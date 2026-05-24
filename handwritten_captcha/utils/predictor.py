import os
from handwritten_captcha.utils.helper import torch, nn, timm
from handwritten_captcha.config.settings import MODEL_PATHS, CNN_CONFIDENCE_THRESHOLD

# Global caches for models and devices
_LOADED_MODELS = {}
_DEVICES = {}

def build_efficientnet_model(num_classes=26):
    """
    Builds the custom classification head matching the training phase.
    """
    model = timm.create_model('tf_efficientnetv2_b0', pretrained=False, num_classes=0)
    in_features = model.num_features
    model.classifier = nn.Sequential(
        nn.Linear(in_features, 512),
        nn.BatchNorm1d(512),
        nn.ReLU(),
        nn.Dropout(0.4),
        nn.Linear(512, num_classes)
    )
    return model

def get_model(model_type):
    """
    Retrieves a cached model or loads it from disk if not already cached.
    `model_type` can be 'digit', 'lowercase', or 'uppercase'.
    """
    global _LOADED_MODELS, _DEVICES
    
    if model_type not in MODEL_PATHS:
        raise ValueError(f"Unknown model type: {model_type}")
        
    if model_type in _LOADED_MODELS:
        return _LOADED_MODELS[model_type], _DEVICES[model_type]
        
    model_path = MODEL_PATHS[model_type]
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    if not os.path.exists(model_path):
        print(f"[WARNING] Model file '{model_path}' not found! Creating dummy model.")
        # Fallback in case of missing weights: initialize model and save dummy state_dict
        model = build_efficientnet_model(num_classes=26)
        torch.save(model.state_dict(), model_path)
    else:
        model = build_efficientnet_model(num_classes=26)
        try:
            state_dict = torch.load(model_path, map_location=device)
            model.load_state_dict(state_dict)
            print(f"[INFO] Loaded {model_type} model successfully on {device}.")
        except Exception as e:
            print(f"[ERROR] Failed to load model weights for {model_type}: {e}. Initializing randomly.")
            
    model.to(device)
    model.eval()
    
    _LOADED_MODELS[model_type] = model
    _DEVICES[model_type] = device
    
    return model, device

def predict_cnn(image_tensor, model_type):
    """
    Performs inference on a preprocessed image tensor using the specified model.
    Maps output class indexes to character characters based on category:
      - 'digit': class index % 10 (returns str)
      - 'lowercase': class index maps to a-z (chr(97 + class_index))
      - 'uppercase': class index maps to A-Z (chr(65 + class_index))
    
    Returns:
        tuple: (predicted_char, confidence_score)
    """
    model, device = get_model(model_type)
    image_tensor = image_tensor.to(device)
    
    with torch.no_grad():
        output = model(image_tensor)
        probabilities = torch.softmax(output, dim=1)
        predicted_idx = torch.argmax(probabilities, dim=1).item()
        confidence = probabilities[0][predicted_idx].item()
        
    # Map index to character
    if model_type == 'digit':
        # Digits: 0-9
        predicted_char = str(predicted_idx % 10)
    elif model_type == 'lowercase':
        # Lowercase: a-z
        predicted_char = chr(ord('a') + (predicted_idx % 26))
    elif model_type == 'uppercase':
        # Uppercase: A-Z
        predicted_char = chr(ord('A') + (predicted_idx % 26))
    else:
        predicted_char = str(predicted_idx)
        
    return predicted_char, confidence

def get_character_model_type(char):
    """
    Determines which model type a target character belongs to.
    """
    if char.isdigit():
        return 'digit'
    elif char.islower():
        return 'lowercase'
    elif char.isupper():
        return 'uppercase'
    return 'digit' # Fallback
