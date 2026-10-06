"""Small numerical and repository checks, not a paper benchmark reproduction."""
from pathlib import Path
import ast
import json
import platform
import sys
import traceback

BASE = Path(__file__).resolve().parents[2]
REPO = BASE / '代码' / 'titans-pytorch'
OUT = BASE / '复现' / 'outputs'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO))
report = {'python': sys.version, 'os': platform.platform(), 'checks': {}}

def check(name, fn):
    try:
        report['checks'][name] = {'status': 'pass', 'result': fn()}
    except Exception:
        report['checks'][name] = {'status': 'fail', 'traceback': traceback.format_exc()}
    print(name, report['checks'][name]['status'], flush=True)

def syntax():
    paths = list(REPO.rglob('*.py'))
    for path in paths:
        ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    return {'parsed_files': len(paths)}

def scalar():
    # Full squared-error convention from Eq. 12, hence factor two in gradient.
    w, k, v, theta, eta, alpha, s = 1., 2., 6., .05, .5, .1, 0.
    eps = 1e-6
    analytic = 2 * (w * k - v) * k
    finite_diff = (((w+eps)*k-v)**2 - ((w-eps)*k-v)**2) / (2*eps)
    assert abs(analytic-finite_diff) < 1e-7
    rows=[]
    for t in range(1, 3):
        old=w
        g=2*(w*k-v)*k
        s=eta*s-theta*g
        w=(1-alpha)*w+s
        rows.append(dict(t=t, before=old, gradient=g, momentum=s, after=w, loss=(w*k-v)**2))
    assert abs(rows[0]['after']-1.7)<1e-12
    assert abs(rows[1]['after']-2.45)<1e-12
    return dict(analytic=analytic, finite_difference=finite_diff, trajectory=rows)

def scan_algebra():
    # Affine state transitions compose associatively; gradients are held fixed here.
    pairs=[(.2,.7),(.4,-.3),(.8,.1)]
    def compose(left,right):
        a,b=left; c,d=right
        return c*a,c*b+d
    a=compose(compose(pairs[0],pairs[1]),pairs[2])
    b=compose(pairs[0],compose(pairs[1],pairs[2]))
    assert max(abs(x-y) for x,y in zip(a,b))<1e-12
    state=.6
    for c,d in pairs: state=c*state+d
    closed=a[0]*.6+a[1]
    assert abs(state-closed)<1e-12
    return dict(composed=a, sequential=state, composed_result=closed)

def repository_memory():
    import torch
    from titans_pytorch import NeuralMemory
    torch.set_num_threads(2)
    torch.manual_seed(7)
    report['torch']=torch.__version__
    report['cuda_available']=torch.cuda.is_available()
    mem=NeuralMemory(dim=8,chunk_size=2,batch_size=4,
        default_step_transform_max_lr=.01, momentum=True,
        default_model_kwargs=dict(depth=2,expansion_factor=2.))
    seq=torch.randn(2,16,8)
    before={k:v.detach().clone() for k,v in mem.named_parameters()}
    retrieved,state=mem(seq)
    assert retrieved.shape==seq.shape
    assert torch.isfinite(retrieved).all()
    loss=retrieved.square().mean()
    loss.backward()
    grads=[p.grad for p in mem.parameters() if p.grad is not None]
    assert grads and all(torch.isfinite(g).all() for g in grads)
    static_delta=max((p.detach()-before[n]).abs().max().item() for n,p in mem.named_parameters())
    initial=mem.init_weights(2)
    fast_delta=max((state.states[0][n]-initial[n]).abs().max().item() for n in initial.keys())
    assert static_delta==0. and fast_delta>0.
    mem.eval()
    with torch.no_grad():
        fresh,_=mem(seq[:, :4])
        continued,continued_state=mem(seq[:, :4],state=state,detach_mem_state=True)
        fresh_again,_=mem(seq[:, :4])
    assert torch.allclose(fresh,fresh_again)
    diff=(fresh-continued).abs().max().item()
    assert diff>0.
    changed=seq.detach().clone(); changed[:,8:]+=2
    with torch.no_grad():
        original,_=mem(seq); altered,_=mem(changed)
    prefix_diff=(original[:,:8]-altered[:,:8]).abs().max().item()
    assert prefix_diff < 1e-5
    return dict(shape=list(retrieved.shape),loss=loss.item(),finite_grad_tensors=len(grads),
        registered_parameter_delta_without_optimizer=static_delta,
        fast_state_delta=fast_delta, fresh_vs_continued_max_diff=diff,
        suffix_change_prefix_max_diff=prefix_diff, continued_seq_index=continued_state.seq_index)

def repository_mac():
    import torch
    from titans_pytorch import MemoryAsContextTransformer
    torch.manual_seed(11)
    model=MemoryAsContextTransformer(num_tokens=32,dim=16,depth=1,
        segment_len=4,num_persist_mem_tokens=2,num_longterm_mem_tokens=2,
        neural_memory_segment_len=2,neural_memory_batch_size=4,
        dim_head=8,heads=2,num_residual_streams=1,use_flex_attn=False,
        neural_memory_kwargs=dict(default_step_transform_max_lr=.01))
    ids=torch.randint(0,32,(2,13))
    logits=model(ids)
    loss=model(ids,return_loss=True)
    loss.backward()
    assert list(logits.shape)==[2,13,32]
    assert loss.ndim==0 and torch.isfinite(loss)
    assert all(torch.isfinite(p.grad).all() for p in model.parameters() if p.grad is not None)
    return dict(input_shape=list(ids.shape),logits_shape=list(logits.shape),loss=loss.item(),
        parameter_count=sum(p.numel() for p in model.parameters()))

if __name__=='__main__':
    check('syntax',syntax)
    check('scalar_gradient_and_memory_update',scalar)
    check('associative_scan_algebra',scan_algebra)
    check('repository_neural_memory_forward_backward_state_causality',repository_memory)
    check('repository_mac_forward_backward',repository_mac)
    (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    if any(v['status']=='fail' for v in report['checks'].values()): sys.exit(1)
