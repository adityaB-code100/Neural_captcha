import concurrent.futures
from handwritten_captcha.utils.buffer_store import update_image_status, get_session
from handwritten_captcha.utils.logger import CustomLogger

# Create a ThreadPoolExecutor. 
# max_workers can be configured based on system resources.
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def _process_image_task(session_id, image_number):
    """
    Background worker that runs the OCR processing.
    """
    from handwritten_captcha.utils.engine import process_single_image
    
    try:
        # Mark as processing
        update_image_status(session_id, image_number, "Processing")
        CustomLogger.info(f"Task Queue: Processing started for Session {session_id}, Image {image_number}")
        
        # Pull the session to get image_data and target_char
        session = get_session(session_id)
        if not session:
            CustomLogger.warning(f"Task Queue: Session {session_id} not found.")
            return
            
        image = session["images"].get(image_number)
        if not image:
            CustomLogger.warning(f"Task Queue: Image {image_number} not found for Session {session_id}.")
            return
            
        base64_img = image["image_data"]
        
        char_index = int(image_number)
        if char_index < 0 or char_index >= len(session["expected_text"]):
            CustomLogger.error(f"Task Queue: Invalid char_index {char_index} for Session {session_id}")
            update_image_status(session_id, image_number, "Failed")
            return
            
        target_char = session["expected_text"][char_index]
        
        # Run prediction
        result = process_single_image(base64_img, target_char, image_number)
        
        # Update status
        update_image_status(session_id, image_number, "Completed", result)
        CustomLogger.success(f"Task Queue: Processing completed for Session {session_id}, Image {image_number}")
        
    except Exception as e:
        CustomLogger.error(f"Task Queue: Processing failed for Session {session_id}, Image {image_number}: {e}")
        update_image_status(session_id, image_number, "Failed")

def submit_image_task(session_id, image_number):
    """
    Submits an image to the background worker queue.
    """
    _executor.submit(_process_image_task, session_id, image_number)
