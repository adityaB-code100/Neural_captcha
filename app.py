import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS

# Absolute minimum clean imports from our modular package
# Completely encapsulates torch, easyocr, and ML models away from this script
from handwritten_captcha.config import settings
from handwritten_captcha.utils.captcha_logic import init_session_captcha, get_session_captcha, clear_session_captcha
from handwritten_captcha.utils.engine import captcha_test
from handwritten_captcha.utils.logger import CustomLogger

# Initialize Flask with custom paths pointing into the modular folder
app = Flask(
    __name__,
    template_folder='handwritten_captcha/templates',
    static_folder='handwritten_captcha/static'
)

# Enable CORS for secure AJAX calls
CORS(app)

# Encryption key for securing sessions (Production fallback style)
app.secret_key = os.environ.get('SECRET_KEY', 'aethera_secops_quantum_super_key_2026')

@app.route('/')
def index():
    """
    Gateway login gate. Redirects logged in users to the dashboard.
    """
    if session.get(settings.SESSION_USER_LOGGED_IN):
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """
    Futuristic corporate landing page for Aethera Dynamics.
    Secured: Redirects unauthorized users back to gateway login.
    """
    if not session.get(settings.SESSION_USER_LOGGED_IN):
        CustomLogger.security("Blocked unauthorized access attempt to /dashboard.")
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    """
    Session termination route. Logs the user out and wipes credentials.
    """
    session.pop(settings.SESSION_USER_LOGGED_IN, None)
    clear_session_captcha()
    CustomLogger.info("User logged out. Session variables terminated.")
    return redirect(url_for('index'))

@app.route('/api/generate_captcha', methods=['GET'])
def generate_captcha():
    """
    Secured CAPTCHA generation API.
    Generates a 6-character random token, stores it in Flask session as the
    only source of truth, and returns it for visual drawing display.
    """
    try:
        # Generate and save CAPTCHA in session
        captcha_text = init_session_captcha()
        
        # Log challenge generation in the backend for audits
        CustomLogger.info(f"System generated new CAPTCHA challenge target: '{captcha_text}'")
        
        # Split into characters array for the multi-step canvas draw workflow
        chars_list = list(captcha_text)
        
        return jsonify({
            'status': 'success',
            'captcha_chars': chars_list
        })
    except Exception as e:
        CustomLogger.error(f"Failed to generate CAPTCHA: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to initialize verification gate.'
        }), 500

@app.route('/api/verify_captcha', methods=['POST'])
def verify_captcha():
    """
    Secure CAPTCHA verification API.
    Accepts credentials and drawn canvas images. 
    Verifies drawings using the modular captcha_test decision engine
    against the actual CAPTCHA target saved in the server-side session.
    """
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    images = data.get('images', [])
    
    # 1. Credentials Validation (System simulation for credentials verification)
    if not username or not password:
        return jsonify({
            'status': 'error',
            'message': 'Invalid credentials. Access Denied.'
        }), 400
        
    # 2. Session Integrity Check
    actual_text = get_session_captcha()
    if not actual_text:
        CustomLogger.security("Blocked verification request: Expired or uninitialized session.")
        return jsonify({
            'status': 'error',
            'message': 'Session expired. Please regenerate challenge.'
        }), 400
        
    # 3. Validation Image List check
    if len(images) != 10:
        CustomLogger.security("Blocked verification request: Incomplete drawings package.")
        return jsonify({
            'status': 'error',
            'message': 'Incomplete drawings. Ensure all 10 letters are drawn.'
        }), 400
        
    # 4. CAPTCHA verification through modular pipeline
    # The client NEVER sends the target text back. The backend session remains the source of truth!
    try:
        is_verified = captcha_test(images, actual_text)
        
        if is_verified:
            # Wipe CAPTCHA from session on successful verification to prevent reuse attacks
            clear_session_captcha()
            
            # Authorize User session
            session[settings.SESSION_USER_LOGGED_IN] = True
            
            return jsonify({
                'status': 'success',
                'message': 'Authorization granted.',
                'redirect': url_for('dashboard')
            })
        else:
            # Increment attempts or fail-safe regeneration trigger
            clear_session_captcha() # Force regenerations on error to block brute force
            return jsonify({
                'status': 'error',
                'message': 'Neural verification failed. Drawings did not match system expectations.'
            }), 401
            
    except Exception as e:
        CustomLogger.error(f"Server error encountered during API verification: {e}")
        clear_session_captcha()
        return jsonify({
            'status': 'error',
            'message': 'Server encountered an error processing drawings.'
        }), 500

if __name__ == '__main__':
    # Log system initialization status
    CustomLogger.info("Starting SECURE X Portal...")
    CustomLogger.info("Lazy-loading ML engines and initializing models config...")
    
    # Run the secure Flask server locally
    app.run(debug=True, host='0.0.0.0', port=5000)
