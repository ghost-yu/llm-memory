"""Titans synthetic associative-memory demo using the pinned third-party module.
No pretrained weights, language translation, API calls, or paper benchmark claims.
"""
from pathlib import Path
import argparse
import json
import math
import sys
import time
import subprocess

BASE = Path(__file__).resolve().parents[2]
REPO = BASE / '代码' / 'titans-pytorch'
sys.path.insert(0, str(REPO))
import torch
from torch.nn import functional as F
from titans_pytorch import NeuralMemory, MemoryMLP

K = 8
DIM = K * 2
COMMIT = 'ce7da9e9a7909e95c8249ceece7c88000bc2c0b9'

def make_memory(depth, linear=False):
    model = MemoryMLP(DIM, depth=depth, expansion_factor=2.)
    if linear:
        with torch.no_grad():
            for p in model.parameters(): p.zero_()
    mem = NeuralMemory(dim=DIM, model=model, chunk_size=1, batch_size=K,
        momentum=not linear, pre_rmsnorm=False, post_rmsnorm=False,
        mem_model_norm_add_residual=False, default_step_transform_max_lr=16. if linear else 1.,
        init_adaptive_step_bias=0., init_decay_bias=-20. if linear else -8.,
        init_momentum_bias=None if linear else -4.)
    # Fixed, visible encoding: address in the first half; value in the second.
    with torch.no_grad():
        for branch in (mem.to_queries, mem.to_keys, mem.to_values):
            proj = branch if hasattr(branch, "weight") else branch[0]
            proj.weight.zero_()
        eye = torch.eye(K)
        mem.to_queries.weight[:K, :K].copy_(eye)
        mem.to_keys.weight[:K, :K].copy_(eye)
        mem.to_values.weight[:K, K:].copy_(eye)
    for proj in (mem.to_queries, mem.to_keys, mem.to_values):
        for p in proj.parameters(): p.requires_grad_(False)
    return mem

def episode(batch, generator):
    targets = torch.stack([torch.randperm(K, generator=generator) for _ in range(batch)])
    order = torch.stack([torch.randperm(K, generator=generator) for _ in range(batch)])
    selected = targets.gather(1, order)
    writes = torch.cat((F.one_hot(order, K), F.one_hot(selected, K)), dim=-1).float()
    queries = torch.zeros(batch, K, DIM)
    queries[:, :, :K] = torch.eye(K)
    return writes, queries, targets

def read_all(mem, queries, weights):
    batch, count, _ = queries.shape
    # One frozen final state per query. The query contains NO target value.
    repeated = {name: value.repeat_interleave(count, dim=0).unsqueeze(1)
                for name, value in weights.items()}
    result = mem.retrieve_memories(queries.reshape(batch*count, 1, DIM), repeated)
    return result.reshape(batch, count, DIM)[..., :K]

def final_state(mem, writes):
    _, state = mem(writes)
    return state

def metric(logits, targets):
    return float((logits.argmax(-1) == targets).float().mean())

def evaluate(mem, batch=256, seed=101):
    mem.eval()
    gen = torch.Generator().manual_seed(seed)
    with torch.no_grad():
        writes, queries, targets = episode(batch, gen)
        state = final_state(mem, writes)
        normal = read_all(mem, queries, state.states[0])
        initial = mem.init_weights(batch)
        reset = read_all(mem, queries, initial)
        # Identical queries, independent fresh random values: detects answer leakage.
        other_writes, _, other_targets = episode(batch, gen)
        other_state = final_state(mem, other_writes)
        other = read_all(mem, queries, other_state.states[0])
        # Update address zero to a different class; preserve the other targets.
        changed_targets = targets.clone()
        changed_targets[:, 0] = (targets[:, 0] + 1) % K
        update = torch.zeros(batch, 1, DIM)
        update[:, 0, 0] = 1.
        update[torch.arange(batch), 0, K + changed_targets[:, 0]] = 1.
        # batch boundary one: evaluate a real update, not an incomplete cached segment.
        _, new_state = mem(update, state=state, ttt_batch_size=1)
        updated = read_all(mem, queries, new_state.states[0])
        return {
            'episodes': batch, 'queries': batch*K, 'chance_accuracy': 1/K,
            'written_accuracy': metric(normal, targets),
            'reset_accuracy': metric(reset, targets),
            'changed_context_accuracy': metric(other, other_targets),
            'changed_key_accuracy': metric(updated[:, :1], changed_targets[:, :1]),
            'untouched_keys_accuracy': metric(updated[:, 1:], targets[:, 1:]),
            'initial_vs_written_max_difference': float((normal-reset).abs().max()),
            'examples': [
                {'key': f'key_{key}', 'target': int(targets[0, key]),
                 'read': int(normal[0, key].argmax()),
                 'after_reset': int(reset[0, key].argmax()),
                 'updated_target': int(changed_targets[0, key]),
                 'after_update': int(updated[0, key].argmax())}
                for key in range(K)],
        }

def train(mem, steps, batch):
    mem.train()
    optim = torch.optim.Adam([p for p in mem.parameters() if p.requires_grad], lr=.003)
    gen = torch.Generator().manual_seed(2026)
    history = []
    for step in range(steps):
        writes, queries, targets = episode(batch, gen)
        state = final_state(mem, writes)
        logits = read_all(mem, queries, state.states[0])
        loss = F.cross_entropy((logits*8).reshape(-1,K), targets.reshape(-1))
        if not torch.isfinite(loss): raise RuntimeError('Non-finite meta-training loss')
        optim.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(mem.parameters(), 1.)
        optim.step()
        if step == 0 or (step+1)%50 == 0 or step+1 == steps:
            row = {'step':step+1, 'loss':float(loss.detach()),
                   'training_batch_accuracy':metric(logits.detach(), targets)}
            history.append(row)
            print('train', row, flush=True)
    return history

def write_report_html(report, path):
    # Self-contained local visual generated from measured results.
    import html
    rows=[]
    for name in ('linear_reference','deep_before','deep_after'):
        data=report[name]
        bars=''.join('<tr><td>'+html.escape(label)+'</td><td><div class="bar"><span style="width:'+str(data[key]*100)+'%"></span></div></td><td>'+format(data[key]*100,'.1f')+'%</td></tr>' for key,label in (
            ('written_accuracy','写入后的查询'),('reset_accuracy','重置后查询'),
            ('changed_context_accuracy','换一份记忆再查询'),('changed_key_accuracy','修改一个 key'),
            ('untouched_keys_accuracy','未修改的其他 key')))
        rows.append('<section><h2>'+html.escape(name)+'</h2><table>'+bars+'</table></section>')
    ex=report['deep_after']['examples']
    examples=''.join('<tr>'+''.join('<td>'+html.escape(str(r[k]))+'</td>' for k in ('key','target','read','after_reset','updated_target','after_update'))+'</tr>' for r in ex)
    path.write_text('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Titans 关联记忆 demo</title><style>body{font:16px system-ui;max-width:980px;margin:36px auto;padding:0 20px;color:#17252d;background:#f5f7fa}section{background:white;padding:20px;margin:20px 0;border-radius:12px}table{width:100%;border-collapse:collapse}td,th{padding:8px;border-bottom:1px solid #eee;text-align:left}.bar{width:300px;height:16px;background:#edf1f5;border-radius:5px}.bar span{display:block;height:100%;background:#29867f;border-radius:5px}p{line-height:1.7}</style><h1>Titans：关联记忆小 demo</h1><p>真实调用锁定第三方 NeuralMemory；随机 key–value，8 类，256 个独立测试 episode。线性参考是退化情形；深层模型经过合成任务外层训练，内层依然启用动量和遗忘。查询不包含 value，读取不执行写入。</p><p>这是受控机制演示，不是自然语言理解、原论文指标或 2M 上下文复现。</p>'+''.join(rows)+'<section><h2>深层模型的一组实际查询</h2><table><tr><th>key</th><th>原目标</th><th>读出</th><th>重置后</th><th>更新目标</th><th>更新后读出</th></tr>'+examples+'</table></section><p>完整配置、训练记录和限制见旁边的 JSON 与 demo说明.md。</p></html>',encoding='utf-8')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--steps',type=int,default=400)
    parser.add_argument('--batch',type=int,default=16)
    parser.add_argument('--threads',type=int,default=2)
    args=parser.parse_args()
    actual=subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()
    if actual != COMMIT: raise RuntimeError('Repository commit differs from documented version')
    torch.set_num_threads(args.threads)
    torch.manual_seed(31)
    start=time.perf_counter()
    linear=make_memory(1,linear=True)
    reference=evaluate(linear)
    assert reference['written_accuracy']==1.
    assert reference['changed_key_accuracy']==1.
    assert reference['untouched_keys_accuracy']==1.
    mem=make_memory(2)
    before=evaluate(mem)
    history=train(mem,args.steps,args.batch)
    after=evaluate(mem)
    report={'scope':'Synthetic LMM component demo, not paper benchmark reproduction',
        'commit':actual,'torch':torch.__version__,'device':'cpu',
        'config':{'dim':DIM,'keys':K,'depth':2,'momentum':True,
                  'decay':True,'chunk_size':1,'batch_size':K,
                  'meta_training_steps':args.steps,'meta_batch':args.batch,
                  'learning_rate':.003,'fixed_kqv':True,'test_seed':101},
        'linear_reference':reference,'deep_before':before,'deep_after':after,
        'history':history,'seconds':time.perf_counter()-start}
    out=BASE/'复现'/'outputs'; out.mkdir(exist_ok=True)
    (out/'demo_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    write_report_html(report,out/'demo_report.html')
    torch.save({'state_dict':mem.state_dict(),'config':report['config'],'commit':actual},out/'synthetic_memory_demo.pt')
    print(json.dumps({k:report[k] for k in ('deep_before','deep_after','seconds')},ensure_ascii=False,indent=2))
    if after['written_accuracy'] < .85 or after['written_accuracy'] < after['reset_accuracy']+.5:
        raise RuntimeError('Demo did not meet retrieval criterion; inspect saved report')

if __name__=='__main__': main()
