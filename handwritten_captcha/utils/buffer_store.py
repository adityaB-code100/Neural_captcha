import time
import threading

# Thread-safe global buffer for session storage
# Structure:
# {
#   "session_id": {
#       "session_id": "session_id",
#       "expected_text": "text",
#       "total_processed": 0,
#       "correct": 0,
#       "failed": 0,
#       "final_decision": "Pending", # Pending, Pass, Fail
#       "images": {
#           0: {
#               "image_number": 0,
#               "image_data": "base64...",
#               "predicted_text": None,
#               "confidence": 0.0,
#               "is_correct": False,
#               "status": "Queued", # Queued, Processing, Completed, Failed
#               "processing_time": 0.0,
#               "created_at": time.time()
#           },
#           ...
#       },
#       "created_at": time.time()
#   }
# }
_SESSION_BUFFER = {}
_BUFFER_LOCK = threading.Lock()

def create_session(session_id, expected_text):
    with _BUFFER_LOCK:
        _SESSION_BUFFER[session_id] = {
            "session_id": session_id,
            "expected_text": expected_text,
            "total_processed": 0,
            "correct": 0,
            "failed": 0,
            "final_decision": "Pending",
            "images": {},
            "created_at": time.time()
        }
        return _SESSION_BUFFER[session_id]

def get_session(session_id):
    with _BUFFER_LOCK:
        return _SESSION_BUFFER.get(session_id)

def add_image_to_session(session_id, image_number, image_data):
    with _BUFFER_LOCK:
        session = _SESSION_BUFFER.get(session_id)
        if not session:
            return False
            
        if image_number in session["images"]:
            # Prevent duplicate processing
            return False
            
        session["images"][image_number] = {
            "image_number": image_number,
            "image_data": image_data,
            "predicted_text": None,
            "confidence": 0.0,
            "is_correct": False,
            "status": "Queued",
            "processing_time": 0.0,
            "created_at": time.time()
        }
        return True

def update_image_status(session_id, image_number, status, result=None):
    with _BUFFER_LOCK:
        session = _SESSION_BUFFER.get(session_id)
        if not session:
            return False
            
        image = session["images"].get(image_number)
        if not image:
            return False
            
        image["status"] = status
        
        if result and status == "Completed":
            image["predicted_text"] = result.get("predicted_text")
            image["confidence"] = result.get("confidence")
            image["is_correct"] = result.get("is_correct")
            image["processing_time"] = result.get("processing_time")
            
            session["total_processed"] += 1
            if image["is_correct"]:
                session["correct"] += 1
            else:
                session["failed"] += 1
                
            # If all 10 are processed, make the final decision
            if session["total_processed"] == len(session["expected_text"]):
                if session["correct"] >= 8:
                    session["final_decision"] = "Pass"
                else:
                    session["final_decision"] = "Fail"
                    
        return True
