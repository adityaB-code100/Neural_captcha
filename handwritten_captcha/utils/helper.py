import sys
import os

# Suppress PyTorch/timm/EasyOCR startup warnings to keep terminal beautiful
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

try:
    import torch
    import torch.nn as nn
    import torchvision
    from torchvision import transforms
    import timm
    from PIL import Image, ImageOps
except ImportError as e:
    print(f"[ERROR] Required core ML library missing: {e}", file=sys.stderr)
    raise

try:
    import easyocr
except ImportError:
    easyocr = None
    print("[WARNING] EasyOCR is not available. System will fallback to local CNN predictions.")

# Exposed variables/classes for backend utilization
__all__ = [
    'torch',
    'nn',
    'transforms',
    'timm',
    'Image',
    'ImageOps',
    'easyocr'
]
