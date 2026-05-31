import requests
import time
import base64
import uuid
import threading
import os
import psutil
from PIL import Image, ImageDraw
from io import BytesIO

BASE_URL = "http://localhost:5000"

def create_dummy_image_base64():
    img = Image.new('RGB', (100, 100), color = (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10,10), "A", fill=(0,0,0))
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{img_str}"

def test_session_management():
    print("--- Session Management Testing ---")
    resp = requests.get(f"{BASE_URL}/api/generate_captcha")
    data = resp.json()
    assert data['status'] == 'success'
    session_id = data['session_id']
    print(f"Created Session ID: {session_id}")
    
    img_b64 = create_dummy_image_base64()
    for i in range(1, 11):
        payload = {'session_id': session_id, 'image_number': i, 'image': img_b64}
        r = requests.post(f"{BASE_URL}/api/submit_image", json=payload)
        assert r.status_code == 200, f"Failed submitting image {i}"
        
    print("Submitted 10 images successfully.")
    
    status_resp = requests.get(f"{BASE_URL}/api/session_status/{session_id}")
    status_data = status_resp.json()
    assert status_data['status'] == 'success'
    print("Session remains valid and images stored.")

def test_pipeline_and_queue():
    print("--- Pipeline & Queue Testing ---")
    resp = requests.get(f"{BASE_URL}/api/generate_captcha")
    session_id = resp.json()['session_id']
    
    img_b64 = create_dummy_image_base64()
    
    # submit rapidly
    start = time.time()
    threads = []
    for i in range(1, 11):
        def submit(num):
            payload = {'session_id': session_id, 'image_number': num, 'image': img_b64}
            requests.post(f"{BASE_URL}/api/submit_image", json=payload)
        t = threading.Thread(target=submit, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print(f"Submitted 10 images concurrently in {time.time() - start:.2f}s")
    
    # Wait for queue to process
    print("Waiting for queue processing...")
    while True:
        s = requests.get(f"{BASE_URL}/api/session_status/{session_id}").json()
        if s['total_processed'] == 10:
            print("All 10 images processed.")
            break
        time.sleep(1)

def measure_memory_gpu():
    import subprocess
    try:
        output = subprocess.check_output(['nvidia-smi', '--query-gpu=utilization.gpu,memory.used', '--format=csv,noheader,nounits']).decode()
        print(f"GPU Utilization and Memory: {output.strip()}")
    except Exception as e:
        print(f"Could not read nvidia-smi: {e}")

def run_all_tests():
    measure_memory_gpu()
    test_session_management()
    test_pipeline_and_queue()
    measure_memory_gpu()
    print("Testing Complete.")

if __name__ == '__main__':
    run_all_tests()
