#!/usr/bin/env python3
"""Minimal FramePack model loading test - no network calls"""
import gc, os, sys
os.environ['HF_HOME'] = '/home/jet/hf_download'
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
sys.path.insert(0, '/home/jet/FramePack')

import torch
from diffusers_helper.memory import get_cuda_free_memory_gb, gpu

gc.collect()
torch.cuda.empty_cache()
print(f"=== FramePack Model Loading Test ===")
print(f"Free VRAM before: {get_cuda_free_memory_gb(gpu):.2f} GB")

# Test 1: Load VAE to GPU
print("\n[TEST 1] Loading VAE to GPU...")
from diffusers import AutoencoderKLHunyuanVideo
vae = AutoencoderKLHunyuanVideo.from_pretrained(
    "hunyuanvideo-community/HunyuanVideo",
    subfolder='vae',
    torch_dtype=torch.float16,
    local_files_only=True
).to(gpu)
print(f"After VAE: {get_cuda_free_memory_gb(gpu):.2f} GB")
del vae
gc.collect()
torch.cuda.empty_cache()
print(f"After cleanup: {get_cuda_free_memory_gb(gpu):.2f} GB")

# Test 2: Load transformer to GPU
print("\n[TEST 2] Loading FramePackI2V_HY transformer to GPU...")
from diffusers_helper.models.hunyuan_video_packed import HunyuanVideoTransformer3DModelPacked
transformer = HunyuanVideoTransformer3DModelPacked.from_pretrained(
    'lllyasviel/FramePackI2V_HY',
    torch_dtype=torch.bfloat16,
    local_files_only=True
).to(gpu)
print(f"After transformer: {get_cuda_free_memory_gb(gpu):.2f} GB")
del transformer
gc.collect()
torch.cuda.empty_cache()
print(f"After cleanup: {get_cuda_free_memory_gb(gpu):.2f} GB")

print("\n=== TEST PASSED ===")
print("FramePack models CAN load on RTX 2060 6GB")
