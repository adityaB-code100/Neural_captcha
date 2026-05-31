import time

class CustomLogger:
    """
    Highly styled visual console logger for AI predictions, 
    ensemble decisions, and security alerts.
    """
    
    # ANSI escape colors
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'
    
    @staticmethod
    def info(msg):
        print(f"{CustomLogger.BLUE}[INFO]{CustomLogger.END} {msg}")
        
    @staticmethod
    def success(msg):
        print(f"{CustomLogger.GREEN}[SUCCESS]{CustomLogger.END} {CustomLogger.BOLD}{msg}{CustomLogger.END}")
        
    @staticmethod
    def warning(msg):
        print(f"{CustomLogger.YELLOW}[WARNING]{CustomLogger.END} {msg}")
        
    @staticmethod
    def error(msg):
        print(f"{CustomLogger.RED}[ERROR]{CustomLogger.END} {CustomLogger.BOLD}{msg}{CustomLogger.END}")
        
    @staticmethod
    def security(msg):
        print(f"{CustomLogger.RED}{CustomLogger.BOLD}[SECURITY-ALERT]{CustomLogger.END} {msg}")

    @staticmethod
    def log_prediction(char_idx, target_char, cnn_pred, cnn_conf, ocr_pred, ocr_conf, final_pred, is_correct, elapsed_time):
        """
        Prints a structured table in the console for each character prediction.
        """
        color = CustomLogger.GREEN if is_correct else CustomLogger.RED
        status = "✓ MATCHED" if is_correct else "✗ MISMATCH"
        
        print("\n" + "="*70)
        print(f"{CustomLogger.BOLD}{CustomLogger.CYAN}CHARACTER DRAWING #{char_idx + 1} AUDIT REPORT{CustomLogger.END}")
        print("-"*70)
        print(f"Target Character : {CustomLogger.BOLD}{target_char}{CustomLogger.END}")
        print(f"predicted: '{final_pred}'")
        print(f"Verification     : {color}{CustomLogger.BOLD}{status}{CustomLogger.END}")
        print("="*70 )
