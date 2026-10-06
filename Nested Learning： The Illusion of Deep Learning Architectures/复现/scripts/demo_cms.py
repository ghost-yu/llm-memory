"""CMS chain and periodic gradient updates, paper eqs 70/71. Not full HOPE."""
import copy,json,platform,time
from pathlib import Path
import torch
from torch import nn
OUT=Path(__file__).resolve().parents[1]/'outputs'

class MemoryBlock(nn.Module):
    def __init__(self,dim=8,hidden=32):
        super().__init__()
        self.net=nn.Sequential(nn.Linear(dim,hidden),nn.GELU(),nn.Linear(hidden,dim))
        nn.init.normal_(self.net[-1].weight,std=.02)
        nn.init.zeros_(self.net[-1].bias)
    def forward(self,x): return x+self.net(x)

class CMS(nn.Module):
    def __init__(self):
        super().__init__()
        self.blocks=nn.ModuleList([MemoryBlock() for _ in range(3)])
    def forward(self,x):
        for block in self.blocks: x=block(x)
        return x

class PeriodicSGD:
    def __init__(self,model,periods,lr=.1):
        self.blocks=model.blocks;self.periods=periods;self.lr=lr;self.steps=0
        self.accum=[[torch.zeros_like(p) for p in b.parameters()] for b in self.blocks]
        self.counts=[0]*len(self.blocks);self.changes=[]
    def update(self,loss):
        # All gradients are evaluated before any block changes this step.
        params=[p for b in self.blocks for p in b.parameters()]
        gradients=torch.autograd.grad(loss,params)
        self.steps+=1; index=0;changed=[]
        with torch.no_grad():
            for j,(block,period) in enumerate(zip(self.blocks,self.periods)):
                group=list(block.parameters())
                before=[p.clone() for p in group]
                for p,buf in zip(group,self.accum[j]):
                    buf.add_(gradients[index]);index+=1
                due=self.steps%period==0
                if due:
                    for p,buf in zip(group,self.accum[j]):
                        # Mean gradient = eq71 summed gradient with eta_i=lr/period.
                        p.add_(buf,alpha=-self.lr/period);buf.zero_()
                    self.counts[j]+=1
                did_change=any(not torch.equal(a,b) for a,b in zip(before,group))
                if not due: assert not did_change, 'Unscheduled parameter mutation'
                changed.append(did_change)
        self.changes.append(changed)

def loss_fn(pred,target): return .5*(pred-target).square().sum(-1).mean()

def evaluate(model,x,a,b,current):
    with torch.no_grad():
        pred=model(x)
        assert torch.isfinite(pred).all()
        return {'mse_current':float((pred-current).square().mean()),'mse_old_A':float((pred-a).square().mean()),'mse_B':float((pred-b).square().mean()),'stable_accuracy':float((pred[:4].argmax(-1)==a[:4].argmax(-1)).float().mean()),'changed_accuracy_current':float((pred[4:].argmax(-1)==current[4:].argmax(-1)).float().mean())}

def run_one(init,periods,x,a,b):
    model=copy.deepcopy(init);scheduler=PeriodicSGD(model,periods)
    initial=[torch.cat([p.detach().flatten() for p in block.parameters()]) for block in model.blocks]
    trace=[];snapshots={}
    for step in range(1,641):
        phase='A_start' if step<=128 else ('B' if step<=384 else 'A_return')
        target=b if phase=='B' else a
        # Read BEFORE writing labels from this step, to preserve causal evaluation.
        metrics=evaluate(model,x,a,b,target)
        metrics.update({'step':step,'phase':phase})
        trace.append(metrics)
        loss=loss_fn(model(x),target);scheduler.update(loss)
        if step in [128,384,640]: snapshots[str(step)]=evaluate(model,x,a,b,target)
    for j,period in enumerate(periods): assert scheduler.counts[j]==640//period
    norms=[float((torch.cat([p.detach().flatten() for p in block.parameters()])-old).norm()) for block,old in zip(model.blocks,initial)]
    def adaptation(start,target):
        points=trace[start:start+256]
        return next((i+1 for i,z in enumerate(points) if z['changed_accuracy_current']==1.),None)
    out={'periods':periods,'parameter_updates_per_block':scheduler.counts,'total_block_updates':sum(scheduler.counts),'drift_norm_final':norms,'snapshots_after_write':snapshots,'first_perfect_changed_key_read_in_B':adaptation(128,b),'first_perfect_changed_key_read_on_A_return':adaptation(384,a),'trace_before_write':trace,'change_log':scheduler.changes}
    return out,model

def check_gradient_accumulation():
    # Linear case at a frozen parameter: compare two accumulated samples to batch SGD.
    w=torch.tensor([1.,-1.],requires_grad=True)
    xs=[torch.tensor([1.,0.]),torch.tensor([0.,1.])];ys=[2.,3.]
    gs=[torch.autograd.grad(.5*(w@x-y).square(),w)[0] for x,y in zip(xs,ys)]
    batch=.5*((torch.stack(xs)@w-torch.tensor(ys)).square()).mean()
    gb,=torch.autograd.grad(batch,w)
    error=float((sum(gs)/2-gb).abs().max());assert error<1e-7
    return error

def main():
    torch.set_num_threads(1)
    start=time.time();x=torch.eye(8);a=torch.eye(8);b=a.clone();b[4:]=a[torch.tensor([5,6,7,4])]
    result={'scope':'CMS periodic-update mechanism; supervised toy stream, no self-referential Titans or outer meta-training','environment':{'python':platform.python_version(),'torch':torch.__version__,'device':'cpu','dtype':'float32'},'config':{'seeds':[31,32,33,34,35],'dim':8,'hidden':32,'blocks':3,'lr':.1,'pretrain_steps':300,'stream_steps':640,'phases':{'A_start':[1,128],'B':[129,384],'A_return':[385,640]},'periods':{'every_step':[1,1,1],'cms':[1,16,64],'all_slow':[64,64,64]}},'checks':{'accumulated_vs_batch_gradient_error':check_gradient_accumulation()},'runs':[]}
    OUT.mkdir(exist_ok=True)
    for seed in result['config']['seeds']:
        torch.manual_seed(seed);init=CMS();opt=torch.optim.SGD(init.parameters(),lr=.1)
        for _ in range(300):
            opt.zero_grad();loss_fn(init(x),a).backward();opt.step()
        entry={'seed':seed,'pretrain_A_mse':evaluate(init,x,a,b,a)['mse_current'],'models':{}}
        states={}
        for name,periods in result['config']['periods'].items():
            report,model=run_one(init,periods,x,a,b);entry['models'][name]=report
            states[name]=model.state_dict()
        result['runs'].append(entry)
        if seed==31:
            torch.save({'seed':seed,'scope':result['scope'],'states':states},OUT/'toy_cms_checkpoint.pt')
            loaded=torch.load(OUT/'toy_cms_checkpoint.pt',weights_only=True)
            for name in states:
                reload_model=CMS();reload_model.load_state_dict(loaded['states'][name])
                for key,value in states[name].items(): assert torch.equal(reload_model.state_dict()[key],value)
            result['checks']['checkpoint_state_reload_exact']=True
    summary={}
    for name in result['config']['periods']:
        reports=[r['models'][name] for r in result['runs']]
        summary[name]={'parameter_count':sum(p.numel() for p in CMS().parameters()),'updates_per_block':reports[0]['parameter_updates_per_block'],'total_block_updates':reports[0]['total_block_updates']}
        for point in ['128','384','640']:
            summary[name]['after_step_'+point]={metric:sum(q['snapshots_after_write'][point][metric] for q in reports)/len(reports) for metric in reports[0]['snapshots_after_write'][point]}
        for key in ['first_perfect_changed_key_read_in_B','first_perfect_changed_key_read_on_A_return']:
            values=[q[key] for q in reports];summary[name][key]={'values':values,'mean_reached':sum(v for v in values if v is not None)/sum(v is not None for v in values) if any(v is not None for v in values) else None}
    result['summary']=summary;result['elapsed_seconds']=time.time()-start
    (OUT/'demo_results.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({'environment':result['environment'],'checks':result['checks'],'summary':summary,'elapsed_seconds':result['elapsed_seconds']},indent=2))
    print('PASS: scheduled updates, frozen blocks, gradient scaling, finite reads, checkpoint reload')
if __name__=='__main__':main()
