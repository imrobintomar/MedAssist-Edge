#!/usr/bin/env python3
"""
Download MedGemma 1.5 weight shards only.
Run: python3 scripts/download_weights.py

Reads token from HF_TOKEN environment variable.
Never paste your token into this file or into chat.

  export HF_TOKEN=hf_...          # set in terminal
  python3 scripts/download_weights.py
"""

import os
import sys
from pathlib import Path

LOCAL_DIR = Path("/media/drprabudh/m2/MedGemma/model/medgemma-1.5-4b-it")
REPO_ID   = "google/medgemma-1.5-4b-it"
SHARDS    = [
    "model-00001-of-00002.safetensors",
    "model-00002-of-00002.safetensors",
]

token = os.environ.get("HF_TOKEN")
if not token:
    print("ERROR: HF_TOKEN environment variable is not set.")
    print("Run:  export HF_TOKEN=hf_...")
    sys.exit(1)

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("Installing huggingface_hub ...")
    os.system(f"{sys.executable} -m pip install -q huggingface_hub")
    from huggingface_hub import hf_hub_download

LOCAL_DIR.mkdir(parents=True, exist_ok=True)
print(f"Downloading {len(SHARDS)} weight shards → {LOCAL_DIR}")
print("Total size: ~8.6 GB\n")

for shard in SHARDS:
    dest = LOCAL_DIR / shard
    if dest.exists() and dest.stat().st_size > 1_000_000:
        print(f"  ✓ Already exists: {shard} ({dest.stat().st_size/1e9:.2f} GB)")
        continue
    print(f"  Downloading: {shard} ...")
    hf_hub_download(
        repo_id=REPO_ID,
        filename=shard,
        local_dir=str(LOCAL_DIR),
        token=token,
    )
    size_gb = (LOCAL_DIR / shard).stat().st_size / 1e9
    print(f"  ✓ Done: {shard} ({size_gb:.2f} GB)")

print("\n✓ All shards downloaded.")
print(f"  Path: {LOCAL_DIR}")
print("\nNext steps:")
print("  python3 scripts/setup_rag.py")
print("  python3 backend/main.py")
