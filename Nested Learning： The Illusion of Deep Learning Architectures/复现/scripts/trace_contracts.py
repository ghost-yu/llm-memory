"""Trace actual CMS teaching code; not a full Hope reproduction."""
import hashlib, importlib.util, inspect, json, platform
from pathlib import Path
import torch
P=Path(__file__).resolve().parents[2];SOURCE=P/'复现/scripts/demo_cms.py'
spec=importlib.util.spec_from_file_location('cms_demo_trace',SOURCE)
demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)
def main():
    torch.set_num_threads(1);torch.manual_seed(31)
    model=demo.CMS();periods=[1,2,4];scheduler=demo.PeriodicSGD(model,periods)
    x=torch.eye(8);a=x.clone();b=a.clone();b[4:]=a[torch.tensor([5,6,7,4])]
    params=[p for block in model.blocks for p in block.parameters()]
    shapes={name:list(p.shape) for name,p in model.named_parameters()}
    assert sum(p.numel() for p in params)==1656
    hook_shapes=[]
    handles=[module.register_forward_hook(lambda m,i,o:hook_shapes.append({'class':type(m).__name__,'input':list(i[0].shape),'output':list(o.shape)})) for module in [model.blocks[0],*model.blocks[0].net]]
    pred=model(x)
    for h in handles:h.remove()
    assert list(pred.shape)==[8,8]
    assert list(demo.loss_fn(pred,a).shape)==[]
    # loss is 0.5 * sum over output channels, mean over examples: 4*MSE at D=8.
    assert torch.allclose(demo.loss_fn(pred,a),4*(pred-a).square().mean())
    records=[];reference=[torch.zeros_like(p) for p in params]
    for step in range(1,5):
        old=[p.detach().clone() for p in params]
        loss=demo.loss_fn(model(x),b)
        gradients=torch.autograd.grad(loss,params,retain_graph=True)
        reference=[s+g.detach() for s,g in zip(reference,gradients)]
        result=scheduler.update(loss);assert result is None
        index=0
        for j,block in enumerate(model.blocks):
            for p in block.parameters():
                due=step%periods[j]==0
                expected=old[index]-.1/periods[j]*reference[index] if due else old[index]
                assert torch.allclose(p,expected,atol=1e-7,rtol=1e-6)
                if due: reference[index].zero_()
                index+=1
        actual=[buf for group in scheduler.accum for buf in group]
        assert all(torch.allclose(s,r) for s,r in zip(actual,reference))
        assert all(not buf.requires_grad for buf in actual)
        assert all(p.grad is None for p in params)
        records.append({'step':step,'counts':list(scheduler.counts),'changed':list(scheduler.changes[-1]),'buffer_norms':[float(torch.cat([q.flatten() for q in group]).norm()) for group in scheduler.accum]})
    assert scheduler.counts==[4,2,1]
    # A frozen block can produce new outputs when its upstream representation changes.
    torch.manual_seed(31);frozen_demo=demo.CMS();s=demo.PeriodicSGD(frozen_demo,[1,16,64])
    slow=frozen_demo.blocks[1];slow_before=[p.detach().clone() for p in slow.parameters()]
    with torch.no_grad(): out_before=slow(frozen_demo.blocks[0](x)).clone()
    s.update(demo.loss_fn(frozen_demo(x),b))
    with torch.no_grad(): out_after=slow(frozen_demo.blocks[0](x)).clone()
    assert all(torch.equal(old,p) for old,p in zip(slow_before,slow.parameters()))
    difference=float((out_after-out_before).abs().max());assert difference>0
    # Existing constructor has no validation of periodic schedule shape/range.
    errors={}
    zero_model=demo.CMS();zero=demo.PeriodicSGD(zero_model,[0,2,4])
    try: zero.update(demo.loss_fn(zero_model(x),a))
    except ZeroDivisionError as exc: errors['zero_period']={'type':type(exc).__name__,'message':str(exc),'steps_after_failure':zero.steps}
    else: raise AssertionError('zero period accepted')
    short_model=demo.CMS();short=demo.PeriodicSGD(short_model,[1]);short.update(demo.loss_fn(short_model(x),a))
    assert short.counts==[1,0,0] and len(short.changes[-1])==1
    # The existing checkpoint contains model tensors, not scheduler restart state.
    checkpoint=torch.load(P/'复现/outputs/toy_cms_checkpoint.pt',weights_only=True)
    assert set(checkpoint)=={'seed','scope','states'}
    checkpoint_checks={}
    saved=json.loads((P/'复现/outputs/demo_results.json').read_text(encoding='utf8'))
    for name,state in checkpoint['states'].items():
        restored=demo.CMS();restored.load_state_dict(state)
        read=demo.evaluate(restored,x,a,b,a)
        expected=saved['runs'][0]['models'][name]['snapshots_after_write']['640']
        error=max(abs(read[k]-expected[k]) for k in read)
        assert error<1e-7;checkpoint_checks[name]=error
    objects=['MemoryBlock.__init__','MemoryBlock.forward','CMS.__init__','CMS.forward','PeriodicSGD.__init__','PeriodicSGD.update','loss_fn','evaluate','run_one','check_gradient_accumulation','main']
    signatures={}
    for path in objects:
        obj=demo
        for attr in path.split('.'):obj=getattr(obj,attr)
        signatures[path]=str(inspect.signature(obj))
    checks=['parameter count','forward shape','scalar loss','loss/MSE scale','update returns None','mean gradient updates','pending buffers','buffers detached','parameter grad untouched','actual update counts','frozen block parameters','frozen block output changes','zero period rejected at runtime','short schedule truncation observed','checkpoint scope','checkpoint predictions']
    result={'scope':'local CMS teaching implementation contracts and limitations; no official Hope',
      'environment':{'python':platform.python_version(),'torch':torch.__version__,'device':'cpu','dtype':'float32'},'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
      'signatures':signatures,'parameter_shapes':shapes,'parameter_count':1656,'forward_hook_shapes':hook_shapes,'schedule':{'periods':periods,'records':records},
      'frozen_parameters_but_changed_output_max_abs':difference,'observed_errors':errors,
      'short_schedule':{'periods':[1],'counts':short.counts,'change_entry_length':len(short.changes[-1])},
      'checkpoint_keys':list(checkpoint),'checkpoint_prediction_max_error':checkpoint_checks,'gradient_accumulation_error':demo.check_gradient_accumulation(),'checks_passed':checks}
    (P/'复现/outputs/contracts_trace.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS:',len(checks),'contract/boundary checks;',len(signatures),'actual signatures')
if __name__=='__main__':main()
