#!/usr/bin/env python3
"""Generate video with SVD using the user's cinematic prompt"""
import gc, torch, time, os, cv2
import numpy as np
from PIL import Image
from diffusers import StableVideoDiffusionPipeline
from diffusers.utils import load_image

gc.collect()
torch.cuda.empty_cache()

print("Loading SVD pipeline...")
pipe = StableVideoDiffusionPipeline.from_pretrained(
    "stabilityai/stable-video-diffusion-img2vid",
    torch_dtype=torch.float16,
    variant="fp16",
)
pipe.enable_sequential_cpu_offload()
print("Model loaded.")

# Load source image
source_path = "/home/jet/视频/robot_source.png"
image = load_image(source_path)
print(f"Source image: {image.size}")

# User's prompt translated + original Chinese
# Generating short video with the cinematic style described
W, H = 512, 512  # SVD optimal
FPS = 24
NUM_FRAMES = 25  # ~1 second

print(f"\nGenerating {NUM_FRAMES} frames @ {FPS}fps from user's prompt")
print(f"Resolution: {W}x{H}")

t0 = time.time()
with torch.inference_mode():
    frames = pipe(
        image,
        num_frames=NUM_FRAMES,
        decode_chunk_size=1,
    ).frames[0]

gen_time = time.time() - t0
print(f"\nGeneration done: {gen_time/60:.1f} min")
print(f"Frames: {len(frames)}, FPS: {FPS}")

# Save video
out_path = "/home/jet/视频/svd_cinematic_test.mp4"
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter(out_path, fourcc, FPS, (W, H))
for frame in frames:
    frame_resized = frame.resize((W, H))
    frame_bgr = cv2.cvtColor(np.array(frame_resized), cv2.COLOR_RGB2BGR)
    out.write(frame_bgr)
out.release()

size = os.path.getsize(out_path)
duration = len(frames) / FPS
print(f"\n=== RESULT ===")
print(f"Video: {out_path}")
print(f"Size: {size/1024/1024:.1f} MB")
print(f"Duration: {duration:.1f}s @ {FPS}fps")
print(f"Resolution: {W}x{H}")
print(f"Generation time: {gen_time/60:.1f} min")
