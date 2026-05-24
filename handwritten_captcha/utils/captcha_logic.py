import random
import string
from flask import session
from handwritten_captcha.config.settings import CAPTCHA_LENGTH, SESSION_CAPTCHA_TEXT, SESSION_CAPTCHA_GENERATED

def generate_random_captcha():
    """
    Generates a secure, random 6-character CAPTCHA string consisting of
    numbers (0-9), lowercase (a-z), and uppercase (A-Z) characters.
    """
    char_pool = string.ascii_letters + string.digits
    # Keep generating until we have a diverse mix
    while True:
        captcha = "".join(random.choice(char_pool) for _ in range(CAPTCHA_LENGTH))
        
        # Check that we have at least one digit, one lowercase, and one uppercase letter
        has_digit = any(c.isdigit() for c in captcha)
        has_lower = any(c.islower() for c in captcha)
        has_upper = any(c.isupper() for c in captcha)
        
        if has_digit and has_lower and has_upper:
            return captcha

def init_session_captcha():
    """
    Generates a new CAPTCHA and saves it in the user's session.
    Returns:
        str: The generated CAPTCHA string.
    """
    captcha = generate_random_captcha()
    session[SESSION_CAPTCHA_TEXT] = captcha
    session[SESSION_CAPTCHA_GENERATED] = True
    return captcha

def get_session_captcha():
    """
    Retrieves the CAPTCHA stored in the session.
    """
    return session.get(SESSION_CAPTCHA_TEXT, None)

def clear_session_captcha():
    """
    Clears the CAPTCHA from the session.
    """
    session.pop(SESSION_CAPTCHA_TEXT, None)
    session.pop(SESSION_CAPTCHA_GENERATED, None)
