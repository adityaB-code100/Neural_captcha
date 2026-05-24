import os
import time
import numpy as np
from handwritten_captcha.config.settings import CNN_CONFIDENCE_THRESHOLD
from handwritten_captcha.utils.logger import CustomLogger
from handwritten_captcha.utils.preprocess import preprocess_canvas_image
from handwritten_captcha.utils.predictor import predict_cnn, get_character_model_type
from handwritten_captcha.utils.helper import easyocr

# Lazy-loaded EasyOCR reader to optimize startup times and memory
_OCR_READER = None

def get_ocr_reader():
    """
    Lazy initializes and returns the EasyOCR Reader.
    """
    global _OCR_READER
    if _OCR_READER is None and easyocr is not None:
        try:
            CustomLogger.info("Initializing Secondary Predictor (CPU mode)...")
            _OCR_READER = easyocr.Reader(['en'], gpu=False)
            CustomLogger.success("Secondary Predictor initialized successfully!")
        except Exception as e:
            CustomLogger.error(f"Failed to initialize Secondary Predictor: {e}")
    return _OCR_READER

def predict_ocr(pil_image, target_char):
    """
    Extracts handwritten character and confidence score using EasyOCR.
    Uses target character semantic category to build highly restrictive allowlists,
    eliminating digit-to-letter and letter-to-digit cross-talk.
    Conforms casing matching to target character.
    """
    reader = get_ocr_reader()
    if reader is None:
        return "", 0.0
        
    try:
        img_np = np.array(pil_image)
        
        # Build strict allowlists dynamically based on the semantic class of the target
        if target_char.isdigit():
            allowlist = '0123456789'
        elif target_char.islower():
            allowlist = 'abcdefghijklmnopqrstuvwxyz'
        elif target_char.isupper():
            allowlist = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        else:
            allowlist = None
            
        results = reader.readtext(img_np, allowlist=allowlist)
        
        if results:
            # Sort detected candidates by confidence
            results = sorted(results, key=lambda x: x[2], reverse=True)
            text = results[0][1].strip()
            conf = float(results[0][2])
            
            if len(text) > 0:
                char = text[0]
                
                # Case-Insensitive Casing Semantics Alignment:
                # If char matches case-insensitively, align the casing to match the target
                if char.lower() == target_char.lower():
                    char = target_char
                    
                return char, conf
        return "", 0.0
    except Exception as e:
        CustomLogger.warning(f"Secondary parsing encountered warning: {e}")
        return "", 0.0

def captcha_test(images, actual_text):
    """
    The main execution function for Handwritten CAPTCHA Authentication.
    Processes all 10 drawn images sequentially, runs the AI model prediction,
    and applies a partial-match decision strategy (passes if >= 8 out of 10 match).
    
    Args:
        images (list of str): 10 Base64-encoded strings representing user drawing canvas images.
        actual_text (str): 10-character string representing the target CAPTCHA challenge.
        
    Returns:
        bool: True if the ensemble correctly verifies at least 8 out of 10 characters, False otherwise.
    """
    start_time = time.time()
    CustomLogger.info(f"Initiating neural CAPTCHA authentication (10 characters, 8/10 partial-match allowed). Target: '{actual_text}'")
    
    if len(images) != 10 or len(actual_text) != 10:
        CustomLogger.security(f"Blocked verification request: Invalid drawing count ({len(images)}) or text length ({len(actual_text)}).")
        return False
        
    temp_files = []
    verified_characters = 0
    
    try:
        for i in range(10):
            step_start = time.time()
            base64_img = images[i]
            target_char = actual_text[i]
            
            # --- 1. PREPROCESSING PIPELINE ---
            # Preprocess to get PyTorch CNN tensor, clean PIL image for EasyOCR, and temp file path
            cnn_tensor, pil_ocr_image, temp_path = preprocess_canvas_image(base64_img, char_index=i, save_temp=True)
            if temp_path:
                temp_files.append(temp_path)
                
            # --- 2. TARGET-CHARACTER-BASED MODEL ROUTING ---
            model_type = get_character_model_type(target_char)
            
            # --- 3. RUN MODEL PREDICTION ---
            cnn_pred, cnn_conf = predict_cnn(cnn_tensor, model_type)
            
            # --- 4. RUN OCR PREDICTION ---
            ocr_pred, ocr_conf = predict_ocr(pil_ocr_image, target_char)
            
            # --- 5. HYBRID ENSEMBLE DECISION LOGIC ---
            if ocr_pred == "":
                final_pred = cnn_pred
                final_conf = cnn_conf
            else:
                if ocr_pred == cnn_pred:
                    final_pred = ocr_pred
                    final_conf = max(ocr_conf, cnn_conf)
                elif ocr_conf > 0.75:
                    final_pred = ocr_pred
                    final_conf = ocr_conf
                elif cnn_conf > 0.85:
                    final_pred = cnn_pred
                    final_conf = cnn_conf
                else:
                    final_pred = ocr_pred
                    final_conf = ocr_conf
            
            # Apply case-sensitivity matching
            is_correct = (final_pred == target_char)
            
            # Reject if confidence is too low to prevent random scribble hacks
            if final_conf < CNN_CONFIDENCE_THRESHOLD:
                is_correct = False
                
            if is_correct:
                verified_characters += 1
                
            # Step timing
            step_elapsed = time.time() - step_start
            
            # --- 6. LOGGING SYSTEM ---
            CustomLogger.log_prediction(
                char_idx=i,
                target_char=target_char,
                cnn_pred=cnn_pred,
                cnn_conf=cnn_conf,
                ocr_pred=ocr_pred if ocr_pred else "N/A",
                ocr_conf=ocr_conf,
                final_pred=final_pred,
                is_correct=is_correct,
                elapsed_time=step_elapsed
            )
            
        # Final result check: Success if at least 8 out of 10 characters verified
        is_success = (verified_characters >= 8)
        total_elapsed = time.time() - start_time
        
        if is_success:
            CustomLogger.success(f"CAPTCHA authentication successful! Verified {verified_characters}/10 characters. (Threshold: >=8). Total time: {total_elapsed:.2f}s")
        else:
            CustomLogger.warning(f"CAPTCHA authentication failed. Verified {verified_characters}/10 characters. (Threshold: >=8). Total time: {total_elapsed:.2f}s")
            
        return is_success
        
    except Exception as e:
        CustomLogger.error(f"Encountered exception during CAPTCHA verification loop: {e}")
        return False
        
    finally:
        # --- 7. AUTOMATIC CLEANUP OF TEMPORARY IMAGES ---
        # This keeps the server filesystem clean and optimized
        time.sleep(0.5) # Small sleep to ensure files are released from PIL/other handles
        for path in temp_files:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as cleanup_err:
                    CustomLogger.warning(f"Failed to delete temp file '{path}': {cleanup_err}")
        CustomLogger.info("Temporary CAPTCHA drawing audit files auto-cleaned successfully.")
