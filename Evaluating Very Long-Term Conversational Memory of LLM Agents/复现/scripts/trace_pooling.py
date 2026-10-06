"""Original mean_pooling on existing CPU PyTorch, without embedding models."""
import ast,hashlib,inspect,json,sys
from pathlib import Path
import torch
P=Path(__file__).resolve().parents[2];source=P/'代码/locomo-official/task_eval/rag_utils.py'
node=next(n for n in ast.parse(source.read_text(encoding='utf8')).body if getattr(n,'name',None)=='mean_pooling')
ns={};exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),ns)
pool=ns['mean_pooling'];torch.set_num_threads(1)
x=torch.tensor([[[2.,4.],[4.,6.],[100.,100.]],[[1.,2.],[3.,4.],[5.,6.]],[[2.,4.],[4.,6.],[100.,100.]]])
mask=torch.tensor([[1,1,0],[0,0,0],[2,1,0]])
before=x.clone();result=pool(x,mask)
checks={'binary_mask_average':torch.allclose(result[0],torch.tensor([3.,5.])),
'all_masked_row_NaN':bool(torch.isnan(result[1]).all()),
'nonbinary_mask_changes_denominator':torch.allclose(result[2],torch.tensor([2.,10/3])),
'input_tensor_unchanged':torch.equal(x,before)}
grad_input=x[:1].clone().requires_grad_();pool(grad_input,mask[:1]).sum().backward()
checks['autograd_and_masked_token_zero']=torch.allclose(grad_input.grad,torch.tensor([[[.5,.5],[.5,.5],[0.,0.]]]))
assert all(checks.values()),checks
output={'scope':'Original mean_pooling function, real CPU torch tensors; no tokenizer, encoder/model, or rag_utils whole-package import',
'source':str(source.relative_to(P)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
'signature':str(inspect.signature(pool)),'checks_passed':checks,'input_shape':list(x.shape),'mask_shape':list(mask.shape),'output_shape':list(result.shape),
'observations':{'binary_result':result[0].tolist(),'all_masked_is_nan':bool(torch.isnan(result[1]).all()),'nonbinary_result':result[2].tolist(),'gradient':grad_input.grad.tolist()},
'python':sys.version,'torch':torch.__version__,'device':'cpu'}
(P/'复现/outputs/pooling_trace.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf8')
print('PASS: 5 original mean_pooling tensor checks')