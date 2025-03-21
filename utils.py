from datetime import datetime, timedelta
import os
import sys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
import time
import re


def get_next_time_epoch_seconds(target_time_str):
    """
    Get the next occurrence of a specific time in seconds since the Unix epoch.
    
    Args:
        target_time_str: String in military time format (HH:MM)
        
    Returns:
        Seconds since Unix epoch for the next occurrence of that time
    """
    # Parse the target time
    hours, minutes = map(int, target_time_str.split(':'))
    
    # Get current time
    now = datetime.now()
    
    # Create datetime object for target time today
    target_time = now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    
    # If target time has already passed today, add a day
    if now >= target_time:
        target_time += timedelta(days=1)
    
    # Convert to seconds since epoch
    return int(target_time.timestamp())

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    # Handle macOS bundle resources
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        if sys.platform == 'darwin' and '.app/Contents/MacOS' in sys.executable:
            # For macOS .app bundles
            resources_path = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'Resources')
            possible_path = os.path.join(resources_path, relative_path)
            if os.path.exists(possible_path):
                return possible_path

    return os.path.join(base_path, relative_path)

def ensure_directories(paths):
    for path in paths:
        os.makedirs(path, exist_ok=True)

def browser_wait(browser, duration, func):
    try:
        if func == None:
            browser.implicitly_wait(duration)
            time.sleep(duration)
            return True
        WebDriverWait(browser, duration, ignored_exceptions=(TimeoutException)).until(func)
    except TimeoutException:
        return False
    return True

def obfuscate_email(email: str):
    # Replace everything between the first character and the '@' with '*'
    return re.sub(r'(?<=.).*(?=@)', lambda m: '*' * len(m.group()), email)