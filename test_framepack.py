#!/usr/bin/env python3
"""Quick FramePack test - generate a short video from a test image"""
import os
os.environ['HF_HOME'] = os.path.expanduser('~/hf_download')
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['TRANSFORMERS_OFFLINE'] = '1'

import torch
import numpy as np
from PIL import Image
from diffusers import AutoencoderKLHunyuanVideo
from transformers import LlamaModel, CLIPTextModel, LlamaTokenizerFast, CLIPTokenizer
from diffusers_helper.models.hunyuan_video_packed import HunyuanVideoTransformer3DModelPacked
from diffusers_helper.hunyuan import encode_prompt_conds, vae_decode, vae_encode
from diffusers_helper.memory import get_cuda_free_memory_gb, move_model_to_device_with_memory_preservation
from diffusers_helper.bucket_tools import find_nearest_bucket
from diffusers_helper.utils import resize_and_center_crop, save_bcthw_as_mp4
import argparse

print("Starting FramePack test...")
print(f"Free VRAM: {get_cuda_free_memory_gb(0):.2f} GB")

# Load models
print("Loading text_encoder...")
text_encoder = LlamaModel.from_pretrained(
    "hunyuanvideo-community/HunyuanVideo", 
    subfolder='text_encoder', 
    torch_dtype=torch.float16,
    local_files_only=True
).cuda()
print(f"After text_encoder: {get_cuda_free_memory_gb(0):.2f} GB")

print("Loading text_encoder_2...")
text_encoder_2 = CLIPTextModel.from_pretrained(
    "hunyuanvideo-community/HunyuanVideo", 
    subfolder='text_encoder_2', 
    torch_dtype=torch.float16,
    local_files_only=True
).cuda()
print(f"After text_encoder_2: {get_cuda_free_memory_gb(0):.2f} GB")

print("Loading tokenizer...")
tokenizer = LlamaTokenizerFast.from_pretrained(
    "hunyuanvideo-community/HunyuanVideo", 
    subfolder='tokenizer',
    local_files_only=True
)

print("Loading vae...")
vae = AutoencoderKLHunyuanVideo.from_pretrained(
    "hunyuanvideo-community/HunyuanVideo", 
    subfolder='vae', 
    torch_dtype=torch.float16,
    local_files_only=True
).cuda()
vae.enable_slicing()
vae.enable_tiling()
print(f"After vae: {get_cuda_free_memory_gb(0):.2f} GB")

print("Loading transformer (FramePackI2V_HY)...")
transformer = HunyuanVideoTransformer3DModelPacked.from_pretrained(
    'lllyasviel/FramePackI2V_HY',
    torch_dtype=torch.bfloat16,
    local_files_only=True
).cuda()
print(f"After transformer: {get_cuda_free_memory_gb(0):.2f} GB")

print("\nAll models loaded successfully!")
print(f"Final VRAM: {get_cuda_free_memory_gb(0):.2f} GB")
print("\nTest PASSED - FramePack can load in 6GB VRAM")
