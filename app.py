import calendar
import pickle
import sys
import os
import toml
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException
import dotenv
from undetected_chromedriver import Chrome

import time
import re
from datetime import datetime, timedelta
import logging
from multiprocessing import Pool

from time_utils import generate_dates, next_date_of, wait_for_time, convert_time_to_seconds, is_time_between
from O365 import Account, FileSystemTokenBackend

from utils import get_next_time_epoch_seconds


# Create a logger
logger = logging.getLogger("AtoZBot")
logger.setLevel(logging.DEBUG)

# Create file handler
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Create console handler (optional)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Show only INFO and above in console
console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))

# Add handlers to logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def convert_to_military(time_str: str) -> str:
    # Parse the input string which is in the format "6:15pm" or "06:15 PM"
    dt = datetime.strptime(time_str.strip().lower(), "%I:%M%p")
    return dt.strftime("%H:%M")

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

def ensure_directories():
    """Create necessary directories if they don't exist"""
    os.makedirs("email-tokens", exist_ok=True)
    os.makedirs("cookies", exist_ok=True)
    return True

def obfuscate_email(email: str):
    # Replace everything between the first character and the '@' with '*'
    return re.sub(r'(?<=.).*(?=@)', lambda m: '*' * len(m.group()), email)


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

URLS = {
    "LOGIN_1": "https://atoz-login.amazon.work/",
    "LOGIN_2": "https://idp.amazon.work/idp/profile/SAML2/Unsolicited/SSO?",
    "LOGIN_3": "https://idp.amazon.work/idp/enter?sif_profile=amazon-passport",
    "LOGGED_IN": "https://atoz.amazon.work/shifts",
    "SHIFTS": "https://atoz.amazon.work/shifts/schedule/find?ref=hm_fs_qklink&date=",
    "SIGN_OUT": "https://atoz-login.amazon.work/logout"
}

ELEMENTS = {
    "USERNAME_BOX_1": "//*[@id='associate-login-input']",
    "SUBMIT_BUTTON_1": "//*[@id='login-form-login-btn']",
    "USERNAME_BOX_2": "//*[@id='login']",
    "PASSWORD_BOX_2": "//*[@id='password']",
    "SUBMIT_BUTTON_2": "//*[@id='buttonLogin']",
    "SUBMIT_BUTTON_3": "/html/body/div[1]/div/div[2]/form/div[2]/button",
    "CODE_BOX": "/html/body/div[1]/div/div[2]/form/div[1]/input",
    "TRUST_DEVICE": "/html/body/div[1]/div/div[2]/form/label",
    "SUBMIT_BUTTON_4": "/html/body/div[1]/div/div[2]/form/div[2]/button",
    "OPORTUNITY_ACCEPT": "//button[@data-test-id='AddOpportunityModalSuccessDoneButton']",
}

def login(browser, username, password, email, account):
    browser.get(URLS["LOGGED_IN"])
    if browser_wait(browser, 10, EC.url_contains(URLS["LOGGED_IN"])):
        logger.debug("Already logged in")
        return True

    # Check if already logged in
    browser.get(URLS["LOGIN_1"])
    if browser_wait(browser, 10, EC.url_contains(URLS["LOGGED_IN"])):
        logger.debug("Logged in after first redirect")
        return True
    # Login page 1
    if not browser_wait(browser, 10, EC.element_to_be_clickable((By.XPATH, ELEMENTS["USERNAME_BOX_1"]))):
        logger.debug("Failed to find username box")
        return False
    browser.find_element(By.XPATH, ELEMENTS["USERNAME_BOX_1"]).send_keys(username)
    browser.find_element(By.XPATH, ELEMENTS["SUBMIT_BUTTON_1"]).click()
    # Wait for redirect
    browser_wait(browser, 5, None)
    # If we are still on the login page 1, then the cookies expired
    if browser_wait(browser, 10, EC.url_contains(URLS["LOGIN_1"])):
        logger.debug("Cookies expired")
        browser.find_element(By.XPATH, ELEMENTS["USERNAME_BOX_1"]).send_keys(username)
        browser.find_element(By.XPATH, ELEMENTS["SUBMIT_BUTTON_1"]).click()
    # Check if logged in
    if browser_wait(browser, 10, EC.url_contains(URLS["LOGGED_IN"])):
        logger.debug("Logged in after second redirect")
        return True
    # Login page 2 
    if not browser_wait(browser, 10, EC.url_contains(URLS["LOGIN_2"])):
        logger.debug("Failed to find login page 2")
        return False
    if not browser_wait(browser, 10, EC.element_to_be_clickable((By.XPATH, ELEMENTS["USERNAME_BOX_2"]))):
        logger.debug("Failed to find username box 2")
        return False
    browser.find_element(By.XPATH, ELEMENTS["USERNAME_BOX_2"]).clear()
    browser.find_element(By.XPATH, ELEMENTS["USERNAME_BOX_2"]).send_keys(username)
    if not browser_wait(browser, 10, EC.element_to_be_clickable((By.XPATH, ELEMENTS["PASSWORD_BOX_2"]))):
        logger.debug("Failed to find password box 2")
        return False
    browser.find_element(By.XPATH, ELEMENTS["PASSWORD_BOX_2"]).clear()
    browser.find_element(By.XPATH, ELEMENTS["PASSWORD_BOX_2"]).send_keys(password)
    if not browser_wait(browser, 10, EC.element_to_be_clickable((By.XPATH, ELEMENTS["SUBMIT_BUTTON_2"]))):
        logger.debug("Failed to find submit button 2")
        return False
    browser.find_element(By.XPATH, ELEMENTS["SUBMIT_BUTTON_2"]).click()
    # Check if logged in
    if browser_wait(browser, 10, EC.url_contains(URLS["LOGGED_IN"])):
        logger.debug("Logged in after second redirect")
        return True
    # Perform 2FA
    if not browser_wait(browser, 10, EC.url_contains(URLS["LOGIN_3"])):
        logger.debug("Failed to get to 2FA page")
        return False
    if not browser_wait(browser, 10, EC.element_to_be_clickable((By.XPATH, f"//label[normalize-space()='{obfuscate_email(email)}']"))):
        logger.debug("Failed to find email label")
        return False
    browser_wait(browser, 5, None)
    browser.find_element(By.XPATH, f"//label[normalize-space()='{obfuscate_email(email)}']").click()
    if not browser_wait(browser, 10, EC.element_to_be_clickable((By.XPATH, ELEMENTS["SUBMIT_BUTTON_3"]))):
        logger.debug("Failed to find 2FA method submit button")
        return False
    browser.find_element(By.XPATH, ELEMENTS["SUBMIT_BUTTON_3"]).click()

    if not browser_wait(browser, 10, EC.element_to_be_clickable((By.XPATH, ELEMENTS["CODE_BOX"]))):
        logger.debug("Failed to find 2FA code box")
        return False
    # Wait for email
    browser_wait(browser, 60, None)
    code = retrieve_code(account)
    if code == None:
        logger.debug("Failed to retrieve 2FA code")
        return False
    browser.find_element(By.XPATH, ELEMENTS["CODE_BOX"]).clear()
    browser.find_element(By.XPATH, ELEMENTS["CODE_BOX"]).send_keys(code)
    if not browser_wait(browser, 10, EC.element_to_be_clickable((By.XPATH, ELEMENTS["TRUST_DEVICE"]))):
        logger.debug("Failed to find trust device checkbox")
        return False
    browser.find_element(By.XPATH, ELEMENTS["TRUST_DEVICE"]).click()
    if not browser_wait(browser, 10, EC.element_to_be_clickable((By.XPATH, ELEMENTS["SUBMIT_BUTTON_4"]))):
        logger.debug("Failed to find 2FA submit button")
        return False
    browser.find_element(By.XPATH, ELEMENTS["SUBMIT_BUTTON_4"]).click()
    # Check if logged in
    if browser_wait(browser, 10, EC.url_contains(URLS["LOGGED_IN"])):
        logger.debug("Logged in after 2FA")
        return True
    else:
        logger.debug("Robot detected")
        # Robot detected
        return False
    
def sign_out(browser):
    browser.get(URLS["SIGN_OUT"])
    if not browser_wait(browser, 10, EC.url_contains(URLS["LOGIN_1"])):
        return False
    return True

def pick_shifts(browser, working_hours, days_to_check):
    dates = generate_dates(0, days_to_check, use_today_if_sunday=True)
    for date in dates:
        browser.get(URLS["SHIFTS"] + date)

        if not browser_wait(browser, 2, EC.url_contains(URLS["SHIFTS"])):
            return False
        # Wait for shifts to load
        if not browser_wait(browser, 2, EC.presence_of_element_located((By.XPATH, "//div[@role='listitem']"))):
            return False
        
        for row in browser.find_elements(By.XPATH, "//div[@role='listitem']"):
            # Grab add shift button, will error if it's not there thus skipping the row
            add_shift = row.find_elements(By.XPATH, ".//button[@aria-label='Add shift button']")
            if len(add_shift) == 0:
                continue
            # Grab the text element
            textelem = row.find_element(By.XPATH, ".//div[@data-test-component='StencilText']")
            # Grab the text
            hours = textelem.text
            # Grab the time
            parts = hours.split(" ")
            start, end = parts[0].split("-")
            # Check if date goes through next day
            next_day = False
            if "pm" in start and "am" in end:
                next_day = True
            # Convert start and end to seconds
            start_time = convert_time_to_seconds(convert_to_military(start))
            end_time = convert_time_to_seconds(convert_to_military(end))
            times = []
            # If next day, create a tuple of start, 11:59pm and 12:00am, end
            if next_day:
                times.append((start_time, convert_time_to_seconds("23:59")))
                times.append((convert_time_to_seconds("00:00"), end_time))
            else:
                times.append((start_time, end_time))
            # Check if any of the times are in non_working_hours

            for t in times:
                found = False
                for working_hour in working_hours[date]:
                    if is_time_between(working_hour[0], working_hour[1], t[0], t[1]):
                        found = True
            if found:
                add_shift[0].click()
                if not browser_wait(browser, 1, EC.element_to_be_clickable((By.XPATH, ELEMENTS["OPORTUNITY_ACCEPT"]))):
                    return False
                browser.find_element(By.XPATH, ELEMENTS["OPORTUNITY_ACCEPT"]).click()

            browser_wait(browser, 0.5, None)


def process_config(config_file):
    with open(config_file, "r") as file:
        data = toml.load(file)
        name = data["name"]
        email = data["email"]
        start_time = data["start_time"]
        manual_login = data["manual_login"]
        ignore_start_time = data["ignore_start_time"]
        password = os.getenv("PASSWORD")
        working_hours = {key: [] for key in generate_dates(0, 9)}
        for rule, times in data["rules"].items():
            if rule.title() in list(calendar.day_name) or rule.title() in list(calendar.day_abbr):
                date = next_date_of(day_of_week=rule, use_today_if_same=False)
            else:
                date = rule
            for t in times:
                _start_time, end_time = t["start_time"], t["end_time"]
                _start_time, end_time = convert_time_to_seconds(_start_time), convert_time_to_seconds(end_time)
                if _start_time > end_time:
                    next_date = next_date_of(date=date, offset=1)
                    working_hours[date].append((_start_time, 86399))
                    working_hours[next_date].append((0, end_time))
                else:
                    working_hours[date].append((_start_time, end_time))
        return start_time, manual_login, ignore_start_time, name, email, password, working_hours
                        



def main():
    ensure_directories()
    dotenv.load_dotenv(dotenv_path=resource_path("builtin.env"))
    dotenv.load_dotenv(dotenv_path=resource_path(".env"))
    dotenv.load_dotenv()
    config_file = os.getenv("CONFIG_FILE") or "config.toml" 
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    days_to_check = int(os.getenv("DAYS_TO_CHECK")) or 9
    duration = int(os.getenv("DURATION")) * 60 or 600
    start_time, manual_login, ignore_start_time, name, email, password, working_hours = process_config(config_file) 
    browser = Chrome() if manual_login else Chrome(headless=True)

    start_time = get_next_time_epoch_seconds(start_time)
    account = Account((client_id, client_secret), token_backend=FileSystemTokenBackend(token_path="email-tokens", token_filename=f"{name}.secret"))

    if not account.is_authenticated and not account.authenticate(scopes=['basic', 'mailbox']):
        logger.error(f"Failed to authenticate {name}")
        return False
        
    load_cookies(browser, f"cookies/{name}.pkl")
    if manual_login:
        browser.get(URLS["LOGIN_1"])
        input("Press Enter to when done...")
        if not browser_wait(browser, 10, EC.url_contains(URLS["LOGGED_IN"])):
            logger.error(f"Failed to login manually for {name}")
            return False
    else:
        if not login(browser, name, password, email, account):
            logger.error(f"Failed to login for {name}")
            return False
    save_cookies(browser, f"cookies/{name}.pkl")
    if not sign_out(browser):
        logger.error(f"Failed to sign out for {name}")
        return False
        
    if not ignore_start_time:
        wait_for_time(epoch_seconds=start_time - 120)
    browser.quit()
    browser = Chrome(headless=True)
    while time.time() < start_time + 300 + duration:
        time.sleep(5)
        load_cookies(browser, f"cookies/{name}.pkl")
        if not login(browser, name, password, email, account):
            logger.error(f"Failed to login for {name}")
            return False
        pick_shifts(browser, working_hours, days_to_check)
        save_cookies(browser, f"cookies/{name}.pkl")

    browser.quit()
    logger.info(f"Finished for {name}")
    return True


def retrieve_code(account, folder_name="AtoZ"):
    mailbox = account.mailbox()
    folder = mailbox.get_folder(folder_name=folder_name)    
    for message in folder.get_messages(limit=1):
        if "Amazon A to Z login verification code" in message.subject:
            return re.search(r'\d{6}', message.body).group()
    return None


        
def load_cookies(browser, cookie_file):
    browser.get("https://google.com")
    if os.path.exists(cookie_file) and os.path.isfile(cookie_file):
        cookies = pickle.load(open(cookie_file, "rb"))
        browser.execute_cdp_cmd('Network.enable', {})
        for cookie in cookies:
            if 'expiry' in cookie:
                cookie['expires'] = cookie['expiry']
                del cookie['expiry']
            browser.execute_cdp_cmd('Network.setCookie', cookie)
            browser.execute_cdp_cmd('Network.disable', {})

def save_cookies(browser, cookie_file):
    browser.get("https://atoz.amazon.work")
    pickle.dump(browser.get_cookies() , open(cookie_file or "cookies.pkl","wb"))

if __name__ == "__main__":
    main()