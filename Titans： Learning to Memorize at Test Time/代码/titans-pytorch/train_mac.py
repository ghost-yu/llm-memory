import random
import tqdm
import gzip
import numpy as np

import torch
from torch import nn, Tensor
from torch.nn import functional as F
from torch.utils.data import DataLoader, Dataset

from adam_atan2_pytorch import AdoptAtan2

from titans_pytorch import (
    MemoryAsContextTransformer,
    MemoryMLP,
    MemoryAttention
)

# constants

NUM_BATCHES = int(1e5)  # Full training
# NUM_BATCHES = 10  # Quick test (uncomment for testing)
BATCH_SIZE = 24  # Increased for GH200 480GB (was 4)
GRADIENT_ACCUMULATE_EVERY = 2  # Reduced since batch is bigger (was 4)
LEARNING_RATE = 2e-4
VALIDATE_EVERY  = 100  # Full training
GENERATE_EVERY  = 500  # Full training
SAVE_EVERY = 5000  # Save checkpoint every N batches
# VALIDATE_EVERY  = 5  # Quick test
# GENERATE_EVERY  = 5  # Quick test
PRIME_LENGTH = 100
GENERATE_LENGTH = 512
SHOULD_GENERATE = True
SEQ_LEN = 512  # Increased for longer context (was 512)

# neural memory related

NEURAL_MEMORY_DEPTH = 2
NUM_PERSIST_MEM = 4
NUM_LONGTERM_MEM = 4
NEURAL_MEM_LAYERS = (2, 4, 6)                   # layers 2, 4, 6 have neural memory, can add more
NEURAL_MEM_GATE_ATTN_OUTPUT = False
NEURAL_MEM_MOMENTUM = True
NEURAL_MEM_MOMENTUM_ORDER = 1
NEURAL_MEM_QK_NORM = True
NEURAL_MEM_MAX_LR = 1e-1
USE_MEM_ATTENTION_MODEL = False
WINDOW_SIZE = 32
NEURAL_MEM_SEGMENT_LEN = 4                      # set smaller for more granularity for learning rate / momentum etc
NEURAL_MEM_BATCH_SIZE = 128                     # set smaller to update the neural memory weights more often as it traverses the sequence
SLIDING_WINDOWS = True
STORE_ATTN_POOL_CHUNKS = True                   # whether to use attention pooling for chunk derived momentum, per-layer lr mod, decay
MEMORY_MODEL_PER_LAYER_LEARNED_LR = True
NEURAL_MEM_WEIGHT_RESIDUAL = True               # learning to accept contributions from the weights of the previous neural mem layer brings about significant improvements. this was improvised and not in the paper, but inspired by the value residual learning free lunch paper
NEURAL_MEM_QKV_RECEIVES_DIFF_VIEW = True        # will allow the neural memory to select what layers from which to derive queries / keys / values, effectively allowing it to graft itself to the transformer in any way to be beneficial. this is to address an issue from a phd student who noted that the mem network is learning nothing more than wk @ wv. this also generalizes all possible ways to connect the neural memory to a transformer, a sort of NAS
NEURAL_MEM_SPEC_NORM_SURPRISES = True           # applying lessons from Muon optimizer to surprise updates, by spectral norming the surprises

# experiment related

PROJECT_NAME = 'titans-mac-transformer'
RUN_NAME = f'mac - {NUM_LONGTERM_MEM} longterm mems, layers {NEURAL_MEM_LAYERS}'
WANDB_ONLINE = False # turn this on to pipe experiment to cloud

# device detection

device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
print(f'Using device: {device}')

# perf related

USE_ACCELERATED_SCAN = True if device == 'cuda' else False  # Triton only works on CUDA
USE_FLEX_ATTN = True
USE_FAST_INFERENCE = False

# wandb experiment tracker

import wandb
wandb.init(project = PROJECT_NAME, mode = 'disabled' if not WANDB_ONLINE else 'online')
wandb.run.name = RUN_NAME
wandb.run.save()

# helpers

def cycle(loader):
    while True:
        for data in loader:
            yield data

def decode_token(token):
    return str(chr(max(32, token)))

def decode_tokens(tokens):
    return ''.join(list(map(decode_token, tokens)))

# memory model

if USE_MEM_ATTENTION_MODEL:
    neural_memory_model = MemoryAttention(
        dim = 64
    )
else:
    neural_memory_model = MemoryMLP(
        dim = 64,
        depth = NEURAL_MEMORY_DEPTH
    )

# instantiate memory-as-context transformer

model = MemoryAsContextTransformer(
    num_tokens = 256,
    dim = 384,
    depth = 8,
    segment_len = WINDOW_SIZE,
    num_persist_mem_tokens = NUM_PERSIST_MEM,
    num_longterm_mem_tokens = NUM_LONGTERM_MEM,
    neural_memory_layers = NEURAL_MEM_LAYERS,
    neural_memory_segment_len = NEURAL_MEM_SEGMENT_LEN,
    neural_memory_batch_size = NEURAL_MEM_BATCH_SIZE,
    neural_mem_gate_attn_output = NEURAL_MEM_GATE_ATTN_OUTPUT,
    neural_mem_weight_residual = NEURAL_MEM_WEIGHT_RESIDUAL,
    neural_memory_qkv_receives_diff_views = NEURAL_MEM_QKV_RECEIVES_DIFF_VIEW,
    use_flex_attn = USE_FLEX_ATTN,
    sliding_window_attn = SLIDING_WINDOWS,
    neural_memory_model = neural_memory_model,
    neural_memory_kwargs = dict(
        dim_head = 64,
        heads = 4,
        attn_pool_chunks = STORE_ATTN_POOL_CHUNKS,
        qk_rmsnorm = NEURAL_MEM_QK_NORM,
        momentum = NEURAL_MEM_MOMENTUM,
        momentum_order = NEURAL_MEM_MOMENTUM_ORDER,
        default_step_transform_max_lr = NEURAL_MEM_MAX_LR,
        use_accelerated_scan = USE_ACCELERATED_SCAN,
        per_parameter_lr_modulation = MEMORY_MODEL_PER_LAYER_LEARNED_LR,
        spectral_norm_surprises = NEURAL_MEM_SPEC_NORM_SURPRISES
    )
).to(device)

# prepare enwik8 data

with gzip.open('./data/enwik8.gz') as file:
    data = np.frombuffer(file.read(int(95e6)), dtype = np.uint8).copy()
    data_train, data_val = np.split(data, [int(90e6)])
    data_train, data_val = map(torch.from_numpy, (data_train, data_val))

class TextSamplerDataset(Dataset):
    def __init__(self, data, seq_len):
        super().__init__()
        self.data = data
        self.seq_len = seq_len

    def __getitem__(self, index):
        rand_start = torch.randint(0, self.data.size(0) - self.seq_len, (1,))
        full_seq = self.data[rand_start: rand_start + self.seq_len + 1].long()
        return full_seq.to(device)

    def __len__(self):
        return self.data.size(0) // self.seq_len

train_dataset = TextSamplerDataset(data_train, SEQ_LEN)
val_dataset   = TextSamplerDataset(data_val, SEQ_LEN)
train_loader  = cycle(DataLoader(train_dataset, batch_size = BATCH_SIZE))
val_loader    = cycle(DataLoader(val_dataset, batch_size = BATCH_SIZE))

# optimizer

optim = AdoptAtan2(model.parameters(), lr = LEARNING_RATE)

# training

best_val_loss = float('inf')

for i in tqdm.tqdm(range(NUM_BATCHES), mininterval = 10., desc = 'training'):
    model.train()

    for __ in range(GRADIENT_ACCUMULATE_EVERY):
        loss = model(next(train_loader), return_loss = True)
        loss.backward()

    print(f'training loss: {loss.item()}')
    torch.nn.utils.clip_grad_norm_(model.parameters(), 0.5)
    optim.step()
    optim.zero_grad()
    wandb.log(dict(loss = loss.item()))

    if i % VALIDATE_EVERY == 0:
        model.eval()
        with torch.no_grad():
            val_loss = model(next(val_loader), return_loss = True)
            print(f'validation loss: {val_loss.item()}')

            # Save best model
            if val_loss.item() < best_val_loss:
                best_val_loss = val_loss.item()
                torch.save({
                    'batch': i,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optim.state_dict(),
                    'val_loss': best_val_loss,
                    'config': {
                        'num_tokens': 256,
                        'dim': 384,
                        'depth': 8,
                        'segment_len': WINDOW_SIZE,
                        'num_persist_mem_tokens': NUM_PERSIST_MEM,
                        'num_longterm_mem_tokens': NUM_LONGTERM_MEM,
                        'neural_memory_layers': NEURAL_MEM_LAYERS,
                        'neural_memory_segment_len': NEURAL_MEM_SEGMENT_LEN,
                        'neural_memory_batch_size': NEURAL_MEM_BATCH_SIZE,
                    }
                }, 'titans_enwik8_best.pt')
                print(f'Saved best model at batch {i} with val_loss {best_val_loss:.4f}')

    # Save regular checkpoint
    if i > 0 and i % SAVE_EVERY == 0:
        torch.save({
            'batch': i,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optim.state_dict(),
            'val_loss': best_val_loss,
        }, f'checkpoint_batch_{i}.pt')
        print(f'Saved checkpoint at batch {i}')

    if SHOULD_GENERATE and i % GENERATE_EVERY == 0:
        model.eval()
        inp = random.choice(val_dataset)[:PRIME_LENGTH]
        prime = decode_tokens(inp)
        print(f'%s \n\n %s', (prime, '*' * 100))

        sample = model.sample(inp[None, ...], GENERATE_LENGTH, use_cache = USE_FAST_INFERENCE)
        output_str = decode_tokens(sample[0])
        print(output_str)

# Save model after training
torch.save({
    'model_state_dict': model.state_dict(),
    'config': {
        'num_tokens': 256,
        'dim': 384,
        'depth': 8,
        'segment_len': WINDOW_SIZE,
        'num_persist_mem_tokens': NUM_PERSIST_MEM,
        'num_longterm_mem_tokens': NUM_LONGTERM_MEM,
        'neural_memory_layers': NEURAL_MEM_LAYERS,
        'neural_memory_segment_len': NEURAL_MEM_SEGMENT_LEN,
        'neural_memory_batch_size': NEURAL_MEM_BATCH_SIZE,
    }
}, 'titans_enwik8.pt')
print('Model saved to titans_enwik8.pt!')
