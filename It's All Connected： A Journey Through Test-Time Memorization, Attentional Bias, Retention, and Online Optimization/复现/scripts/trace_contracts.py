"""Observe the teaching demo's contracts and boundaries; not official MIRAS."""
import hashlib, importlib.util, inspect, json, platform
from pathlib import Path
import torch
P=Path(__file__).resolve().parents[2]
SOURCE=P/'复现/scripts/demo_miras.py'
spec=importlib.util.spec_from_file_location('miras_demo',SOURCE)
demo=importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)
DT=demo.DT

def main():
    torch.set_num_threads(1)
    def array(x): return x.detach().tolist()
    w=torch.tensor([[1.,-1.]],dtype=DT)
    k=torch.tensor([1.,0.],dtype=DT)
    before=w.clone()
    l2=demo.write(w,k,21.)
    huber=demo.write(w,k,21.,'huber')
    decayed=demo.write(w,k,1.,alpha=.98)
    assert torch.equal(w,before)
    assert torch.allclose(l2,torch.tensor([[5.,-1.]],dtype=DT))
    assert torch.allclose(huber,torch.tensor([[1.1,-1.]],dtype=DT))
    assert torch.allclose(decayed,.98*w)
    errors={}
    for name,args in [('invalid_mode',(w,k,1.,'bad')),('wrong_key_shape',(w,torch.ones(3,dtype=DT),1.))]:
        try: demo.write(*args)
        except (ValueError,RuntimeError) as exc: errors[name]={'type':type(exc).__name__,'message':str(exc)}
        else: raise AssertionError(name+' unexpectedly accepted')
    # Accepted broadcasting is NOT a multi-output associative-memory implementation.
    vector_v=demo.write(w,k,torch.tensor([21.,2.],dtype=DT))
    assert list(vector_v.shape)==[1,2]
    e=torch.tensor([2.,.25],dtype=DT);delta=.5
    element=e.clamp(-delta,delta)
    norm_variant=delta*e/e.norm()
    branch_l1=delta*e.sign()
    assert not torch.allclose(element,norm_variant)
    assert not torch.allclose(element,branch_l1)
    # Formula 20's joint simplex and this demo's column simplices differ.
    logits=torch.tensor([[1.,2.],[3.,4.]],dtype=DT)
    joint=torch.softmax(logits.flatten(),dim=0).reshape(2,2)
    columns=torch.softmax(logits,dim=0)
    assert abs(float(joint.sum())-1)<1e-12
    assert abs(float(columns.sum())-2)<1e-12
    assert torch.allclose(columns.sum(0),torch.ones(2,dtype=DT))
    # Re-evaluate an archived episode, rather than re-running all 100 episodes.
    saved=json.loads((P/'复现/outputs/demo_results.json').read_text(encoding='utf8'))
    stream=demo.corrupted_stream(2026,.03)
    archived=saved['experiments']['contaminated']['example']
    assert stream==archived
    shift=demo.legitimate_shift()
    assert shift==saved['legitimate_shift']
    assert shift['l2']['updates_to_abs_error_below_.1']==14
    assert shift['huber']['updates_to_abs_error_below_.1']==23
    mechanisms=demo.checks()
    assert mechanisms==saved['checks']
    signatures={name:str(inspect.signature(getattr(demo,name))) for name in ['write','checks','corrupted_stream','legitimate_shift','main']}
    result={'scope':'local teaching code contract trace; semantic document review is separate',
      'environment':{'python':platform.python_version(),'torch':torch.__version__,'device':'cpu','dtype':str(DT)},
      'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'signatures':signatures,
      'write':{'input_w':array(w),'w_shape':list(w.shape),'k_shape':list(k.shape),'read_shape':list((w@k).shape),'error_shape':list(((w@k).squeeze()-21.).shape),'key_row_shape':list(k.unsqueeze(0).shape),'l2':array(l2),'huber':array(huber),'zero_gradient_decay':array(decayed),'input_unchanged':True,'vector_v_accepted_but_unsupported':array(vector_v)},
      'observed_errors':errors,'multi_output_huber':{'residual':array(e),'coordinate':array(element),'norm_huber':array(norm_variant),'norm_branch_l1':array(branch_l1)},
      'normalization':{'joint':array(joint),'joint_total':float(joint.sum()),'columns':array(columns),'column_total':float(columns.sum()),'column_sums':array(columns.sum(0))},
      'episode_replay':{'seed':2026,'contamination':.03,'corruptions':stream['corruptions'],'trace_length':{m:len(t) for m,t in stream['trace'].items()},'matches_saved':True},
      'shift_steps':{m:x['updates_to_abs_error_below_.1'] for m,x in shift.items()},'mechanisms':mechanisms,
      'checks_passed':['input immutability','l2 update','scalar Huber update','zero-gradient decay','invalid mode rejected','wrong key dimension rejected','vector target boundary observed','Huber variants differ','joint simplex','column simplex','episode exact replay','shift exact replay','mechanism exact replay']}
    out=P/'复现/outputs/contracts_trace.json'
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS:',len(result['checks_passed']),'contract/boundary checks; original teaching source unchanged')

if __name__=='__main__': main()
