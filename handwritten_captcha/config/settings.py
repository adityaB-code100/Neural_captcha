import os

# Base Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'models')
TEMP_DIR = os.path.join(BASE_DIR, 'temp')

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

# CAPTCHA Rules
CAPTCHA_LENGTH = 10

# Image Preprocessing Settings
CANVAS_SIZE = (224, 224) # Canvas size from frontend (224 x 224)
MODEL_INPUT_SIZE = (64, 64) # Input size for EfficientNet CNN models

# Model Paths
MODEL_PATHS = {
    'digit': os.path.join(MODELS_DIR, 'digit_model.pth'),
    'lowercase': os.path.join(MODELS_DIR, 'lowercase_model.pth'),
    'uppercase': os.path.join(MODELS_DIR, 'uppercase_model.pth')
}

# Decision & Ensemble Settings
CNN_CONFIDENCE_THRESHOLD = 0.40 # Threshold below which CNN prediction is rejected
OCR_CONFIDENCE_THRESHOLD = 0.45 # High priority threshold for OCR results

# Session Keys
SESSION_CAPTCHA_TEXT = 'captcha_text'
SESSION_CAPTCHA_GENERATED = 'captcha_generated'
SESSION_USER_LOGGED_IN = 'user_logged_in'
