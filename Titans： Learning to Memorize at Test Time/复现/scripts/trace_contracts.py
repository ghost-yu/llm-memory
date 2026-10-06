"""Observe the pinned original module without changing source or training again."""
from pathlib import Path
import hashlib,inspect,json,subprocess,sys,types
import torch
BASE=Path(__file__).resolve().parents[2];REPO=BASE/'代码/titans-pytorch';OUT=BASE/'复现/outputs'
sys.path.insert(0,str(REPO))
from titans_pytorch import NeuralMemory,MemoryMLP,MemoryAsContextTransformer
from titans_pytorch.neural_memory import mem_state_detach
COMMIT='ce7da9e9a7909e95c8249ceece7c88000bc2c0b9'
assert subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD'],text=True).strip()==COMMIT
assert not subprocess.check_output(['git','-C',str(REPO),'status','--porcelain'],text=True).strip()
torch.set_num_threads(1);torch.manual_seed(47)
def desc(x):
 if torch.is_tensor(x):return dict(shape=list(x.shape),dtype=str(x.dtype),requires_grad=x.requires_grad)
 if isinstance(x,dict) or hasattr(x,'items'):return {str(k):desc(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [desc(v) for v in x]
 return x
def clone_dict(x):return {k:v.detach().clone() for k,v in x.items()}
def delta(x,y):return max(float((x[k].detach()-y[k].detach()).abs().max()) for k in x.keys())
mem=NeuralMemory(dim=8,chunk_size=2,batch_size=4,model=MemoryMLP(8,2,2.),momentum=True,
 pre_rmsnorm=False,mem_model_norm_add_residual=False,default_step_transform_max_lr=.01)
trace=[]
for name in ['store_memories','retrieve_memories']:
 bound=getattr(mem,name)
 def wrap(*args,_name=name,_bound=bound,**kwargs):
  result=_bound(*args,**kwargs);trace.append(dict(method=_name,input=desc(args),kwargs=desc(kwargs),output=desc(result)));return result
 setattr(mem,name,wrap)
seq=torch.randn(2,5,8);registered=clone_dict(dict(mem.named_parameters()))
output,state=mem(seq,return_surprises=True)[:2]
first=dict(output=desc(output),state=desc(state),state_fields=list(state._fields))
assert output.shape==(2,5,8) and state.seq_index==4 and state.cache_store_segment.shape==(2,1,8)
cache_before=state.cache_store_segment.detach().clone();next_input=torch.randn(2,3,8)
try:
 mem(next_input,state=state,detach_mem_state=True)
except RuntimeError as e:
 unaligned_error=dict(type=type(e).__name__,message=str(e),first_length=5,next_length=3,chunk=2,expected='current implementation fails at query/weight time alignment')
else:
 raise AssertionError('Expected observed unaligned continuation failure was not reproduced')
# Store path alone can consume the leftover input; full forward above cannot align reads.
_,cache_consumed,_=mem.store_memories(torch.cat((cache_before,next_input),dim=1),weights=state.weights,past_state=state.states,seq_index=state.seq_index)
assert cache_consumed.seq_index==8 and cache_consumed.cache_store_segment.shape[-2]==0
_,aligned_state=mem(seq[:,:4])
cont,next_state=mem(torch.randn(2,4,8),state=aligned_state,detach_mem_state=True)
assert next_state.seq_index==8 and next_state.cache_store_segment.shape[-2]==0
assert torch.equal(state.cache_store_segment.detach(),cache_before)
# Frozen reads: identical state dictionaries before/after and repeated outputs.
weights={k:v.detach().unsqueeze(1) for k,v in next_state.states[0].items()};before=clone_dict(weights)
query=torch.randn(2,1,8);read1=mem.retrieve_memories(query,weights);read2=mem.retrieve_memories(query,weights)
# A zero loss mask does not freeze decayed weights.
init=mem.init_weights(2);masked_updates,masked_state,_=mem.store_memories(seq[:,:2],weights=init,mask=torch.zeros(2,2,dtype=torch.bool))
masked_delta=delta(masked_state.states[0],init)
# Detach changes graph ownership, not values.
detached=mem_state_detach(state)
assert delta(detached.states[0],state.states[0])==0
for v in detached.states[0].values():assert not v.requires_grad
# Bare MLP forward trace via hooks, original parameter state unchanged.
mlp=MemoryMLP(8,2,2.);mlp_input=torch.randn(2,3,8);mlp_out=mlp(mlp_input)
# MAC actual pipeline: record original submodule boundary shapes.
model=MemoryAsContextTransformer(num_tokens=32,dim=16,depth=1,segment_len=4,
 num_persist_mem_tokens=2,num_longterm_mem_tokens=2,neural_memory_segment_len=2,
 neural_memory_batch_size=4,dim_head=8,heads=2,num_residual_streams=1,use_flex_attn=False,
 neural_memory_kwargs=dict(default_step_transform_max_lr=.01))
mac=[];handles=[];restore=[]
for name,module in model.named_modules():
 if isinstance(module,NeuralMemory):
  original_forward=module.forward;restore.append((module,original_forward))
  def traced_forward(*args,_fn=original_forward,_name=name,**kwargs):
   result=_fn(*args,**kwargs);mac.append(dict(name=_name,owner='NeuralMemory',input=desc(args),kwargs=desc(kwargs),output=desc(result)));return result
  module.forward=traced_forward
 if name in ['token_emb','norm','to_logits'] or isinstance(module,NeuralMemory) or module.__class__.__name__=='SegmentedAttention':
  def hook(mod,args,result,_name=name):mac.append(dict(name=_name,owner=mod.__class__.__name__,input=desc(args),output=desc(result)))
  handles.append(module.register_forward_hook(hook))
ids=torch.randint(0,32,(2,13));logits=model(ids);mac_inference=list(mac);mac.clear();loss=model(ids,return_loss=True)
loss.backward();mac_training=list(mac)
for h in handles:h.remove()
for module,original_forward in restore:module.forward=original_forward
checks=dict(incomplete_chunk_cached=True,store_path_consumes_cache=True,unaligned_continuation_failure_observed=True,aligned_continuation_passed=True,caller_old_cache_unchanged=True,
 frozen_read_no_mutation=delta(weights,before)==0.,repeated_read_equal=torch.equal(read1,read2),
 masked_loss_still_decay=masked_delta>0,registered_parameters_unchanged=delta(dict(mem.named_parameters()),registered)==0.,
 detached_values_unchanged=delta(detached.states[0],state.states[0])==0.,detached_has_no_graph=all(not v.requires_grad for v in detached.states[0].values()),
 mac_memory_observed=any(x['owner']=='NeuralMemory' for x in mac_inference),mac_output_shape=list(logits.shape)==[2,13,32],mac_loss_scalar=loss.ndim==0 and torch.isfinite(loss).item(),
 mac_backward_finite=all(torch.isfinite(p.grad).all().item() for p in model.parameters() if p.grad is not None))
assert all(checks.values())
objects={'MemoryMLP.__init__':MemoryMLP.__init__,'MemoryMLP.forward':MemoryMLP.forward,'NeuralMemory.__init__':NeuralMemory.__init__,
 'NeuralMemory.init_weights':NeuralMemory.init_weights,'NeuralMemory.init_momentum':NeuralMemory.init_momentum,
 'NeuralMemory.store_memories':NeuralMemory.store_memories,'NeuralMemory.retrieve_memories':NeuralMemory.retrieve_memories,'NeuralMemory.forward':NeuralMemory.forward,
 'mem_state_detach':mem_state_detach,'MemoryAsContextTransformer.forward':MemoryAsContextTransformer.forward,'MemoryAsContextTransformer.sample':MemoryAsContextTransformer.sample}
contracts={name:dict(signature=str(inspect.signature(fn)),file=str(Path(inspect.getsourcefile(inspect.unwrap(fn))).relative_to(REPO)),line=inspect.getsourcelines(inspect.unwrap(fn))[1]) for name,fn in objects.items()}
sources={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [REPO/'titans_pytorch/neural_memory.py',REPO/'titans_pytorch/memory_models.py',REPO/'titans_pytorch/mac_transformer.py']}
report=dict(commit=COMMIT,environment=dict(python=sys.version,torch=torch.__version__,device='cpu'),contracts=contracts,
 config=dict(batch=2,sequence=5,dim=8,chunk=2,reference_refresh=4,depth=2,expansion=2.,momentum=True,normalization=False),
 first=first,unaligned_continuation=unaligned_error,store_cache_consumed=desc(cache_consumed),continued=dict(output=desc(cont),state=desc(next_state)),memory_trace=trace,
 mlp=dict(input=desc(mlp_input),weights=desc(list(mlp.weights)),output=desc(mlp_out)),mac_inference=mac_inference,mac_training=mac_training,
 mask_state_delta=masked_delta,checks=checks,sources=sources,scope='contract and shape observations, not paper benchmark')
(OUT/'contracts_trace.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(checks=checks,first_index=state.seq_index,next_index=next_state.seq_index,mask_delta=masked_delta,mac_boundaries=[(x['name'],x['owner']) for x in mac_inference]),ensure_ascii=False))
