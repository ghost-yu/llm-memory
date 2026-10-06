# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an unofficial PyTorch implementation of **Titans: Learning to Memorize at Test Time** (arXiv:2501.00663). The architecture implements a neural long-term memory module that learns to memorize historical context during inference, using gradient-based updates with momentum and weight decay.

## Key Concepts

### Three-Tier Memory System
The architecture combines three distinct memory types:
1. **Short-term Memory**: Sliding window attention for current context
2. **Long-term Memory**: Neural memory module that learns via test-time gradient updates
3. **Persistent Memory**: Learnable data-independent parameters for task knowledge

### Memory as Context (MAC) Architecture
The MAC variant (`MemoryAsContextTransformer`) treats long-term memory as context:
- Sequences are chunked into segments
- Neural memory retrieves relevant historical information for each segment
- Attention operates over concatenated [persistent_memory || retrieved_memory || current_segment]

### Neural Memory Learning Mechanism
The neural memory (`NeuralMemory`) learns at test time by:
- Computing "surprise" via gradients on associative memory loss: `||M(k_t) - v_t||²`
- Using momentum to track surprise flow across tokens (not just momentary surprise)
- Applying adaptive forgetting via weight decay (data-dependent gating)
- Updating parameters through parallelized mini-batch gradient descent

## Development Commands

### Setup
```bash
# Install base dependencies
pip install -e .

# Install with training examples
pip install -e .[examples]

# Install with testing
pip install -e .[test]
```

### Training
```bash
# Train MAC transformer on enwik8
python train_mac.py

# The script saves checkpoints:
# - titans_enwik8_best.pt: Best validation loss
# - checkpoint_batch_N.pt: Regular checkpoints every 5000 batches
# - titans_enwik8.pt: Final model after training
```

### Testing
```bash
# Run full test suite
pytest tests/test_titans.py

# Run specific test
pytest tests/test_titans.py::test_mac -v

# Test memory learning behavior
python test_memory_simple.py
```

## Architecture Components

### Core Files

**`titans_pytorch/neural_memory.py`** - The neural long-term memory module
- `NeuralMemory`: Main memory class implementing test-time learning
- Uses `AssocScan` for parallel associative scans (momentum computation)
- Supports both parallel training and sequential inference
- Key parameters:
  - `chunk_size`: Granularity of gradient updates (smaller = more frequent updates)
  - `batch_size`: Controls how many chunks to process before weight update
  - `momentum`: Enable surprise flow tracking across tokens
  - `qk_rmsnorm`: RMSNorm for query/key stability

**`titans_pytorch/mac_transformer.py`** - Full transformer with memory
- `MemoryAsContextTransformer`: Complete language model with MAC architecture
- `SegmentedAttention`: Attention over [persist_mem || longterm_mem || segment]
- Uses FlexAttention (PyTorch 2.5+) for efficient block-diagonal attention patterns
- Supports autoregressive generation with caching

**`titans_pytorch/memory_models.py`** - Memory network architectures
- `MemoryMLP`: Default 1-4 layer MLP for memory network
- `MemoryAttention`: Alternative attention-based memory
- `MemorySwiGluMLP`: SwiGLU variant

### Training Configuration

The `train_mac.py` script has extensive hyperparameters controlling:

**Neural Memory Behavior:**
- `NEURAL_MEMORY_DEPTH`: Memory network depth (1-4 layer MLP, default: 2)
- `NEURAL_MEM_SEGMENT_LEN`: Chunk size for gradient computation (default: 4)
- `NEURAL_MEM_BATCH_SIZE`: Mini-batch size for weight updates (default: 128)
- `NEURAL_MEM_MOMENTUM`: Enable momentum-based surprise tracking
- `NEURAL_MEM_MAX_LR`: Maximum learning rate for adaptive step size

**Memory Integration:**
- `NEURAL_MEM_LAYERS`: Which transformer layers get neural memory (e.g., `(2, 4, 6)`)
- `NEURAL_MEM_WEIGHT_RESIDUAL`: Learn to mix weights from previous memory layer
- `NEURAL_MEM_QKV_RECEIVES_DIFF_VIEW`: Allow memory to select input layers for Q/K/V

**Architecture:**
- `NUM_PERSIST_MEM`: Number of persistent memory tokens (default: 4)
- `NUM_LONGTERM_MEM`: Number of long-term memory tokens (default: 4)
- `WINDOW_SIZE`: Local attention window (default: 32)
- `SLIDING_WINDOWS`: Use sliding window vs block-diagonal attention

## Important Implementation Details

### Parallel vs Sequential Processing
The neural memory supports both modes:
- **Parallel (training)**: Entire sequence processed at once using tensorized gradient descent
- **Sequential (inference)**: One token at a time, maintaining `NeuralMemState`
- State includes: `(seq_index, weights, cache_store_segment, states, updates)`

### Memory State Management
When chaining forward passes or doing autoregressive generation:
```python
retrieved, state = neural_memory(seq)
next_retrieved, state = neural_memory(next_seq, state=state)
```

Use `mem_state_detach()` to prevent backprop through memory updates when needed.

### Flex Attention (CUDA only)
The MAC architecture uses PyTorch's FlexAttention for efficient custom attention masks:
- Automatically generates block masks for segmented + sliding window patterns
- Falls back to manual masking on non-CUDA devices
- Enable/disable via `use_flex_attn` parameter

### Accelerated Scan (Triton)
Momentum computation uses associative scan:
- `use_accelerated_scan=True` uses Triton kernel (CUDA only)
- Falls back to PyTorch implementation on CPU/MPS

## Model Checkpoints

Checkpoint structure:
```python
{
    'batch': int,                    # Training iteration
    'model_state_dict': OrderedDict, # Model weights
    'optimizer_state_dict': dict,    # Optimizer state
    'val_loss': float,               # Validation loss
    'config': dict                   # Model hyperparameters
}
```

The neural memory weights are stored in layers with keys like:
- `layers.N.X.memory_model.*` - The memory network itself
- `layers.N.X.to_queries.*`, `to_keys.*`, `to_values.*` - Q/K/V projections
- `layers.N.X.to_adaptive_step.*` - Learned learning rate modulation
- `layers.N.X.to_momentum.*` - Momentum gating
- `layers.N.X.to_decay_factor.*` - Forgetting mechanism

## Testing Patterns

Tests validate critical properties:
1. **Shape consistency**: Output matches input shape
2. **Parallel-sequential equivalence**: Same results whether processing full sequence or token-by-token
3. **State chaining**: Proper state propagation across forward passes
4. **Gradient flow**: Memory learning works correctly
5. **Caching correctness**: Autoregressive generation with/without cache matches

## Common Pitfalls

1. **Chunk size too large**: Memory updates infrequent, learning slow
2. **Batch size too small**: Weight updates too frequent, unstable training
3. **Missing accelerated_scan**: 10x slower momentum computation on long sequences
4. **FlexAttention on CPU**: Will crash, disable `use_flex_attn` for non-CUDA devices
5. **Memory depth > 2**: Diminishing returns vs computational cost, not in original paper

## Performance Optimization

- Use CUDA for Triton kernels (accelerated_scan) and FlexAttention
- Increase `BATCH_SIZE` for high-memory GPUs (24 on GH200)
- Reduce `GRADIENT_ACCUMULATE_EVERY` when batch size is large
- Set `chunk_size` based on sequence length: smaller for short sequences
- Enable `USE_FAST_INFERENCE` for autoregressive generation with caching
