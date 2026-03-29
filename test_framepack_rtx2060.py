#!/usr/bin/env python3
"""FramePack I2V test on RTX 2060 6GB using robot_source.png"""
import gc, os, sys, time
os.environ['HF_HOME'] = '/home/jet/hf_download'
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['TRANSFORMERS_OFFLINE'] = '0'
os.environ['HF_HUB_OFFLINE'] = '0'
sys.path.insert(0, '/home/jet/FramePack')

import torch
import numpy as np
from PIL import Image
from diffusers import AutoencoderKLHunyuanVideo
from transformers import LlamaModel, CLIPTextModel, LlamaTokenizerFast, CLIPTokenizer
from diffusers_helper.models.hunyuan_video_packed import HunyuanVideoTransformer3DModelPacked
from diffusers_helper.hunyuan import encode_prompt_conds, vae_decode, vae_encode
from diffusers_helper.memory import get_cuda_free_memory_gb, gpu
from diffusers_helper.bucket_tools import find_nearest_bucket
from diffusers_helper.utils import resize_and_center_crop, save_bcthw_as_mp4

torch.cuda.empty_cache()
gc.collect()

print(f"=== FramePack I2V Test on RTX 2060 ===")
print(f"Free VRAM: {get_cuda_free_memory_gb(gpu):.2f} GB")

SOURCE_IMAGE = '/home/jet/视频/robot_source.png'
OUTPUT_VIDEO = '/home/jet/视频/framepack_test.mp4'
IMAGE_DIR = '/home/jet/视频'
PROMPT = "The robot dances energetically, leaping mid-air with fluid arm swings and quick footwork, dynamic motion."

# Step 1: Load source image
print("\n[1] Loading source image...")
image = Image.open(SOURCE_IMAGE).convert('RGB')
# Resize to bucket for FramePack
W, H = 512, 512
image = image.resize((W, H), Image.LANCZOS)
print(f"Image size: {image.size}")

# Step 2: Load text encoder
print("\n[2] Loading text_encoder...")
text_encoder = LlamaModel.from_pretrained(
    "hunyuanvideo-community/HunyuanVideo",
    subfolder='text_encoder',
    torch_dtype=torch.float16,
    local_files_only=True
).to(gpu)
print(f"VRAM after text_encoder: {get_cuda_free_memory_gb(gpu):.2f} GB")

# Step 3: Load text_encoder_2
print("\n[3] Loading text_encoder_2...")
text_encoder_2 = CLIPTextModel.from_pretrained(
    "hunyuanvideo-community/HunyuanVideo",
    subfolder='text_encoder_2',
    torch_dtype=torch.float16,
    local_files_only=True
).to(gpu)
print(f"VRAM after text_encoder_2: {get_cuda_free_memory_gb(gpu):.2f} GB")

# Step 4: Load tokenizer
print("\n[4] Loading tokenizer...")
tokenizer = LlamaTokenizerFast.from_pretrained(
    "hunyuanvideo-community/HunyuanVideo",
    subfolder='tokenizer',
    local_files_only=True
)
tokenizer_2 = CLIPTokenizer.from_pretrained(
    "hunyuanvideo-community/HunyuanVideo",
    subfolder='tokenizer_2',
    local_files_only=True
)

# Step 5: Load VAE
print("\n[5] Loading VAE...")
vae = AutoencoderKLHunyuanVideo.from_pretrained(
    "hunyuanvideo-community/HunyuanVideo",
    subfolder='vae',
    torch_dtype=torch.float16,
    local_files_only=True
).to(gpu)
vae.enable_slicing()
vae.enable_tiling()
print(f"VRAM after vae: {get_cuda_free_memory_gb(gpu):.2f} GB")

# Step 6: Load image_encoder (flux_redux_bfl)
print("\n[6] Loading image_encoder (flux_redux_bfl)...")
from transformers import SiglipImageProcessor, SiglipVisionModel
from diffusers_helper.clip_vision import hf_clip_vision_encode
feature_extractor = SiglipImageProcessor.from_pretrained("lllyasviel/flux_redux_bfl", subfolder='feature_extractor', local_files_only=True)
image_encoder = SiglipVisionModel.from_pretrained("lllyasviel/flux_redux_bfl", subfolder='image_encoder', torch_dtype=torch.float16, local_files_only=True).to(gpu)
print(f"VRAM after image_encoder: {get_cuda_free_memory_gb(gpu):.2f} GB")

# Step 7: Load transformer (FramePackI2V_HY)
print("\n[7] Loading transformer (FramePackI2V_HY)...")
transformer = HunyuanVideoTransformer3DModelPacked.from_pretrained(
    'lllyasviel/FramePackI2V_HY',
    torch_dtype=torch.bfloat16,
    local_files_only=True
).to(gpu)
print(f"VRAM after transformer: {get_cuda_free_memory_gb(gpu):.2f} GB")

vae.eval()
text_encoder.eval()
text_encoder_2.eval()
image_encoder.eval()
transformer.eval()

print("\n=== All models loaded successfully! ===")
print(f"Final free VRAM: {get_cuda_free_memory_gb(gpu):.2f} GB")

# Cleanup
del text_encoder, text_encoder_2, vae, image_encoder, transformer
torch.cuda.empty_cache()
gc.collect()
print(f"After cleanup: {get_cuda_free_memory_gb(gpu):.2f} GB")
print("\n=== TEST PASSED: FramePack loads on RTX 2060 6GB ===")
