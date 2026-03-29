#!/usr/bin/env python3
"""Direct model loading test - bypass HuggingFace metadata API"""
import gc, os, sys
sys.path.insert(0, '/home/jet/FramePack')

import torch
import safetensors.torch as sf
from diffusers_helper.memory import get_cuda_free_memory_gb, gpu

gc.collect()
torch.cuda.empty_cache()
print(f"=== Direct Model Loading Test ===")
print(f"Free VRAM: {get_cuda_free_memory_gb(gpu):.2f} GB")

# Test 1: Load VAE from safetensors directly
print("\n[TEST 1] Loading VAE from safetensors...")
vae_path = "/home/jet/hf_download/models--hunyuanvideo-community--HunyuanVideo/snapshots/e8c2aaa66fe3742a32c11a6766aecbf07c56e773/vae/diffusion_pytorch_model.safetensors"
state_dict = sf.load_file(vae_path)
print(f"VAE state_dict keys: {len(state_dict)}, dtype: {next(iter(state_dict.values())).dtype}")
# Move to GPU
vae_state = {k: v.half().cuda() for k, v in state_dict.items()}
print(f"After VAE to GPU: {get_cuda_free_memory_gb(gpu):.2f} GB")
del vae_state, state_dict
gc.collect()
torch.cuda.empty_cache()
print(f"After VAE cleanup: {get_cuda_free_memory_gb(gpu):.2f} GB")

# Test 2: Load FramePackI2V_HY transformer from safetensors
print("\n[TEST 2] Loading FramePackI2V_HY transformer...")
fp_path = "/home/jet/hf_download/lllyasviel/FramePackI2V_HY"
import json
with open(f"{fp_path}/config.json") as f:
    config = json.load(f)
print(f"Transformer config: {config.get('model_type', 'unknown')}")

# Load safetensors shards
shards = sorted([f for f in os.listdir(fp_path) if f.endswith('.safetensors') and not f.endswith('.index.json')])
print(f"Shards: {shards}")
total_params = 0
for shard in shards:
    sd = sf.load_file(f"{fp_path}/{shard}")
    print(f"  {shard}: {len(sd)} tensors, moving to GPU...")
    sd_gpu = {k: v.bfloat16().cuda() for k, v in sd.items()}
    total_params += len(sd)
    current_vram = get_cuda_free_memory_gb(gpu)
    print(f"  After shard: {current_vram:.2f} GB free")
    del sd, sd_gpu
    gc.collect()
    torch.cuda.empty_cache()
print(f"Total params: {total_params}")

print(f"\n=== RESULT ===")
print(f"FramePackI2V_HY has multiple safetensors shards.")
print(f"VRAM at end: {get_cuda_free_memory_gb(gpu):.2f} GB")
print("\n=== CONCLUSION ===")
print("VAE loaded OK (fits in VRAM)")
print("Transformer is sharded - needs sequential loading with CPU offload")
