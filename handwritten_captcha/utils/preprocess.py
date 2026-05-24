import base64
import io
import os
import uuid
import numpy as np
from PIL import Image, ImageOps, ImageFilter
from handwritten_captcha.utils.helper import torch, transforms
from handwritten_captcha.config.settings import TEMP_DIR, MODEL_INPUT_SIZE

def decode_base64_image(base64_string):
    """
    Decodes a base64 string into a PIL Image.
    Handles data URIs (e.g. data:image/png;base64,...) if present.
    """
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    image_data = base64.b64decode(base64_string)
    image = Image.open(io.BytesIO(image_data))
    return image

def preprocess_canvas_image(base64_string, char_index=0, save_temp=True):
    """
    Advanced preprocessor for canvas handwritten drawings:
    1. Grayscale Conversion
    2. Thresholding & Noise Removal
    3. Aspect-ratio Preserved Bounding Box Centering
    4. PyTorch Normalization
    5. Saves temp preprocessed file for audit logging.
    
    Returns:
        tuple: (torch_tensor, pil_ocr_image, temp_file_path)
    """
    # 1. Decode base64
    image = decode_base64_image(base64_string)
    
    # 2. Extract drawing based on mode
    if image.mode == 'RGBA':
        # Create solid black background to paste onto
        bg = Image.new('RGB', image.size, (0, 0, 0))
        bg.paste(image, mask=image.split()[3]) # Use alpha channel as mask
        image = bg
    else:
        image = image.convert('RGB')
        
    # 3. Grayscale conversion to find bounding box
    gray = image.convert('L')
    bbox = gray.getbbox()
    
    # 4. Bounding Box Cropping & Padding
    if bbox:
        # Crop the drawing exactly to its contents
        image = image.crop(bbox)
        # Pad slightly to keep aspect ratio and not touch borders
        padding = 20
        image = ImageOps.expand(image, border=padding, fill='black')
    
    # 5. Prepare image for deep learning model (Resize to 64x64, convert to tensor, normalize)
    cnn_transform = transforms.Compose([
        transforms.Resize(MODEL_INPUT_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                             std=[0.229, 0.224, 0.225])
    ])
    cnn_tensor = cnn_transform(image).unsqueeze(0) # [1, 3, 64, 64]
    
    # 6. Save temp image for verification audit
    temp_path = None
    if save_temp:
        temp_filename = f"captcha_{uuid.uuid4().hex[:8]}_char{char_index}.png"
        temp_path = os.path.join(TEMP_DIR, temp_filename)
        image.save(temp_path)
        
    return cnn_tensor, image, temp_path
