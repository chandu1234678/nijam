"""
Download HuggingFace model with progress bar
Faster than automatic download during inference
"""

import os
from huggingface_hub import snapshot_download
from tqdm import tqdm

# Your HF token
HF_TOKEN = "your-hf-token"

# Models to download
MODELS = {
    "1": {
        "name": "Bharat2004/deberta-fakenews-detector",
        "size": "738 MB",
        "description": "DeBERTa-v2 (Primary, most popular)"
    },
    "2": {
        "name": "Bharat2004/deberta-factchecker",
        "size": "~700 MB",
        "description": "DeBERTa-v3-base (Alternative)"
    },
    "3": {
        "name": "Bharat2004/out",
        "size": "~250 MB",
        "description": "DistilBERT (Fast, already may be cached)"
    }
}

def download_model(model_id: str):
    """Download model from HuggingFace"""
    print(f"\n{'='*60}")
    print(f"Downloading: {model_id}")
    print(f"{'='*60}\n")
    
    try:
        cache_dir = os.path.expanduser("~/.cache/huggingface/hub")
        
        snapshot_download(
            repo_id=model_id,
            token=HF_TOKEN,
            cache_dir=cache_dir,
            resume_download=True,  # Resume if interrupted
            local_files_only=False
        )
        
        print(f"\n✓ Successfully downloaded: {model_id}")
        print(f"  Cached at: {cache_dir}")
        return True
        
    except Exception as e:
        print(f"\n✗ Download failed: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("HUGGINGFACE MODEL DOWNLOADER")
    print("="*60)
    
    print("\nAvailable models:")
    for key, model in MODELS.items():
        print(f"  {key}. {model['name']}")
        print(f"     Size: {model['size']} - {model['description']}")
    
    print("\n  A. Download all models")
    print("  Q. Quit")
    
    choice = input("\nSelect model to download (1-3, A, or Q): ").strip().upper()
    
    if choice == 'Q':
        print("Cancelled.")
        return
    
    if choice == 'A':
        print("\nDownloading all models...")
        for key, model in MODELS.items():
            download_model(model['name'])
    elif choice in MODELS:
        model_id = MODELS[choice]['name']
        download_model(model_id)
    else:
        print("Invalid choice.")
        return
    
    print("\n" + "="*60)
    print("DOWNLOAD COMPLETE!")
    print("="*60)
    print("\nModels are now cached and will load instantly.")
    print("Restart your backend to use them.")

if __name__ == "__main__":
    main()
