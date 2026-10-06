"""MIRAS equations 13, 26, 27 mechanism demo; not a full language model."""
import json, platform
from pathlib import Path
import torch
OUT=Path(__file__).resolve().parents[1]/'outputs'
DT=torch.float64

def write(w,k,v,mode='l2',eta=.2,alpha=1.,delta=.5):
    # w [1,8], k [8], v scalar; scalar output makes Huber variants agree.
    error=(w@k).squeeze()-v
    if mode=='l2': derivative=error
    elif mode=='huber': derivative=error.clamp(-delta,delta)
    else: raise ValueError(mode)
    return alpha*w-eta*derivative*k.unsqueeze(0)

def checks():
    k=torch.tensor([1.,0.],dtype=DT)
    w=torch.tensor([[1.,-1.]],dtype=DT,requires_grad=True)
    errors={}
    for mode,v in [('l2',20.),('huber',20.),('huber',1.1)]:
        e=(w@k).squeeze()-v
        loss=.5*e.square() if mode=='l2' else torch.where(e.abs()<=.5,.5*e.square(),.5*(e.abs()-.25))
        g,=torch.autograd.grad(loss,w)
        inferred=(w.detach()-write(w.detach(),k,v,mode))/.2
        errors[mode+'_'+str(v)]=float((g-inferred).abs().max())
        assert torch.allclose(g,inferred,atol=1e-12)
    assert torch.allclose(write(w.detach(),k,1.,alpha=.98),.98*w.detach())
    state=torch.full((4,4),.25,dtype=DT)
    rng=torch.Generator().manual_seed(77)
    minval=1.; maxerr=0.
    for _ in range(100):
        grad=torch.randn(4,4,generator=rng,dtype=DT)
        state=torch.softmax(.97*state.log()-.1*grad,dim=0)
        minval=min(minval,float(state.min()))
        maxerr=max(maxerr,float((state.sum(0)-1).abs().max()))
    assert minval>0 and maxerr<1e-12
    prior=torch.tensor([.7,.1,.1,.1],dtype=DT)
    flattened=torch.softmax(.5*prior.log(),dim=0)
    entropy=lambda p: float(-(p*p.log()).sum())
    assert entropy(flattened)>entropy(prior)
    return {'analytical_vs_autograd_max_error':errors,'memora_positive_min':minval,'memora_column_sum_max_error':maxerr,'entropy_before':entropy(prior),'entropy_after_zero_gradient_retention':entropy(flattened)}

def corrupted_stream(seed,contamination):
    rng=torch.Generator().manual_seed(seed)
    target=torch.where(torch.arange(8)%2==0,1.,-1.).to(DT)
    keys=torch.randint(8,(500,),generator=rng)
    noise=.05*torch.randn(500,generator=rng,dtype=DT)
    spikes=(torch.rand(500,generator=rng)<contamination)
    sign=torch.where(torch.rand(500,generator=rng)<.5,-1.,1.).to(DT)
    observed=target[keys]+noise+20*sign*spikes
    states={m:torch.zeros(1,8,dtype=DT) for m in ['l2','huber']}
    traces={m:[] for m in states}
    eye=torch.eye(8,dtype=DT)
    for i in range(500):
        for m in states:
            states[m]=write(states[m],eye[keys[i]],observed[i],m)
            traces[m].append(float((states[m].squeeze()-target).abs().mean()))
    return {'final_mae':{m:traces[m][-1] for m in traces},'late_mean_mae':{m:sum(traces[m][250:])/250 for m in traces},'trace':traces,'corruptions':int(spikes.sum())}

def legitimate_shift():
    result={}; k=torch.ones(1,dtype=DT)
    for mode in ['l2','huber']:
        w=torch.ones(1,1,dtype=DT); trace=[]
        for _ in range(50):
            w=write(w,k,3.,mode); trace.append(float(w.item()))
        result[mode]={'trace':trace,'updates_to_abs_error_below_.1':next((i+1 for i,x in enumerate(trace) if abs(x-3)<.1),None)}
    return result

def main():
    torch.set_num_threads(1)
    result={'scope':'linear-memory mechanism demo, not full Moneta/Yaad/Memora','environment':{'python':platform.python_version(),'torch':torch.__version__,'device':'cpu','dtype':'float64'},'config':{'episodes':100,'updates_per_episode':500,'keys':8,'eta':.2,'delta':.5,'alpha':1.,'noise_std':.05,'spike_amplitude':20,'seed_start':2026},'checks':checks(),'experiments':{},'legitimate_shift':legitimate_shift()}
    for name,rate in [('clean',0.),('contaminated',.03)]:
        runs=[corrupted_stream(2026+i,rate) for i in range(100)]
        metrics={}
        for mode in ['l2','huber']:
            x=torch.tensor([r['late_mean_mae'][mode] for r in runs],dtype=DT)
            metrics[mode]={'late_mean_mae':float(x.mean()),'std_across_episodes':float(x.std()),'se_of_mean':float(x.std()/10),'final_mae_mean':sum(r['final_mae'][mode] for r in runs)/100}
        result['experiments'][name]={'contamination_rate':rate,'metrics':metrics,'example':runs[0]}
    assert result['experiments']['contaminated']['metrics']['huber']['late_mean_mae'] < result['experiments']['contaminated']['metrics']['l2']['late_mean_mae']
    assert result['legitimate_shift']['huber']['updates_to_abs_error_below_.1'] > result['legitimate_shift']['l2']['updates_to_abs_error_below_.1']
    OUT.mkdir(exist_ok=True)
    (OUT/'demo_results.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    print(json.dumps({'environment':result['environment'],'checks':result['checks']},indent=2))
    for name,x in result['experiments'].items(): print(name,json.dumps(x['metrics']))
    print('Shift:',{m:x['updates_to_abs_error_below_.1'] for m,x in result['legitimate_shift'].items()})
    print('PASS: gradients, retention, simplex, robustness and adaptation tradeoff')
if __name__=='__main__': main()
