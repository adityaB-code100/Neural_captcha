import os
import uuid
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS

from handwritten_captcha.config import settings
from handwritten_captcha.utils.captcha_logic import init_session_captcha, get_session_captcha, clear_session_captcha
from handwritten_captcha.utils.logger import CustomLogger
from handwritten_captcha.utils.buffer_store import create_session, get_session, add_image_to_session
from handwritten_captcha.utils.task_queue import submit_image_task

# Initialize Flask with custom paths pointing into the modular folder
app = Flask(
    __name__,
    template_folder='handwritten_captcha/templates',
    static_folder='handwritten_captcha/static'
)
app.config['BASE_URL'] = os.getenv("BASE_URL", "")
# Enable CORS for secure AJAX calls
CORS(app, supports_credentials=True)

# Encryption key for securing sessions
app.secret_key = os.environ.get('SECRET_KEY', 'aethera_secops_quantum_super_key_2026')

@app.route('/')
def index():
    if session.get(settings.SESSION_USER_LOGGED_IN):
        return redirect(url_for('dashboard'))
    return render_template('index.html', BASE_URL=app.config['BASE_URL'])

@app.route('/dashboard')
def dashboard():
    if not session.get(settings.SESSION_USER_LOGGED_IN):
        CustomLogger.security("Blocked unauthorized access attempt to /dashboard.")
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/logout')
def logout():
    session.pop(settings.SESSION_USER_LOGGED_IN, None)
    clear_session_captcha()
    CustomLogger.info("User logged out. Session variables terminated.")
    return redirect(url_for('index'))

@app.route('/api/generate_captcha', methods=['GET'])
def generate_captcha():
    try:
        captcha_text = init_session_captcha()
        
        # Create a unique session ID for pipelined processing
        session_id = uuid.uuid4().hex
        create_session(session_id, captcha_text)
        
        CustomLogger.info(f"System generated new CAPTCHA challenge target: '{captcha_text}' with session {session_id}")
        
        chars_list = list(captcha_text)
        
        return jsonify({
            'status': 'success',
            'session_id': session_id,
            'captcha_chars': chars_list
        })
    except Exception as e:
        CustomLogger.error(f"Failed to generate CAPTCHA: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to initialize verification gate.'
        }), 500

@app.route('/api/submit_image', methods=['POST'])
def submit_image():
    """
    Receives a single image and queues it for processing.
    """
    data = request.get_json() or {}
    session_id = data.get('session_id')
    image_number = data.get('image_number')
    image_data = data.get('image')
    
    if not session_id or image_number is None or not image_data:
        return jsonify({'status': 'error', 'message': 'Missing data'}), 400
        
    # Add to buffer and queue
    if add_image_to_session(session_id, image_number, image_data):
        submit_image_task(session_id, image_number)
        return jsonify({'status': 'queued', 'message': f'Image {image_number} queued for processing.'})
    else:
        return jsonify({'status': 'error', 'message': 'Duplicate image or session not found.'}), 400

@app.route('/api/session_status/<session_id>', methods=['GET'])
def session_status(session_id):
    """
    Returns the current status of the session and all its images.
    """
    sess_data = get_session(session_id)
    if not sess_data:
        return jsonify({'status': 'error', 'message': 'Session not found'}), 404
        
    return jsonify({
        'status': 'success',
        'session_id': sess_data['session_id'],
        'total_processed': sess_data['total_processed'],
        'correct': sess_data['correct'],
        'failed': sess_data['failed'],
        'final_decision': sess_data['final_decision'],
        'images': sess_data['images']
    })

@app.route('/api/verify_captcha', methods=['POST'])
def verify_captcha():
    """
    Final authorization gate. Polled or called once the final decision is PASS.
    """
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    session_id = data.get('session_id')
    
    if not username or not password:
        return jsonify({'status': 'error', 'message': 'Invalid credentials. Access Denied.'}), 400
        
    sess_data = get_session(session_id)
    if not sess_data:
        return jsonify({'status': 'error', 'message': 'Session not found or expired.'}), 400
        
    if sess_data['final_decision'] == 'Pending':
        return jsonify({'status': 'pending', 'message': 'Decision is still pending. Wait for OCR jobs.'})
    
    if sess_data['final_decision'] == 'Pass':
        clear_session_captcha()
        session[settings.SESSION_USER_LOGGED_IN] = True
        return jsonify({
            'status': 'success',
            'message': 'Authorization granted.',
            'redirect': url_for('dashboard')
        })
    else:
        clear_session_captcha()
        return jsonify({
            'status': 'error',
            'message': 'Neural verification failed. Drawings did not match system expectations.'
        }), 401

if __name__ == '__main__':
    CustomLogger.info("Starting SECURE X Portal...")
    CustomLogger.info("Lazy-loading ML engines and initializing models config...")
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=5000)
