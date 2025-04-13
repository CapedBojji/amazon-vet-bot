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

from time_utils import convert_to_military, generate_dates, next_date_of, wait_for_time, convert_time_to_seconds, is_time_between, get_next_week
from O365 import Account, FileSystemTokenBackend

from utils import browser_wait, ensure_directories, get_next_time_epoch_seconds, obfuscate_email 
from utils import resource_path
from printer import logger

ensure_directories(["cookies", "email-tokens"])
dotenv.load_dotenv(dotenv_path=resource_path("builtin.env"))
dotenv.load_dotenv()

def debug(message="", list=None):
    logger.debug(message)
    if list is not None:
        for item in list:
            logger.debug(item)

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
    if browser.current_url == URLS["LOGGED_IN"]:
        debug("Already logged in")
        return True

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
        browser_wait(browser, 10, None)
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
    tabs = {
        "main": browser.current_window_handle,
    }

    for date in dates:
        browser.switch_to.new_window("tab")
        browser.get(URLS["SHIFTS"] + date)

        browser_wait(browser, 3, lambda d: d.execute_script("return document.readyState") == "complete")
        debug(f"Page loaded for {date}")

        tabs[date] = browser.current_window_handle


    
    for date in dates:
        browser.switch_to.window(tabs[date])

        if not EC.url_contains(URLS["SHIFTS"])(browser):
            # debug(f"Shifts page not loaded for {date}")
            continue

        # Grab all rows
        # browser_wait(browser, 1, EC.presence_of_element_located((By.XPATH, "//div[@role='listitem']")))
        # debug(f"Found {len(rows)} rows")

        rows = browser.find_elements(By.XPATH, "//div[@role='listitem']")
        print(f"Found {len(rows)} rows")

        for row in rows:
            try:
                # Grab add shift button, will error if it's not there thus skipping the row
                # browser_wait(browser, 1, EC.presence_of_all_elements_located((By.XPATH, ".//button[@aria-label='Add shift button']")))
                add_shift = row.find_elements(By.XPATH, ".//button[@aria-label='Add shift button']")
                if len(add_shift) == 0:
                    # debug(f"Add shift button not found")
                    continue
                debug(f"Found add shift button")

                # Grab the text element
                textelem = row.find_element(By.XPATH, ".//div[@data-test-component='StencilText']")
                # debug(f"Checking {textelem.text}")

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
                    # if not browser_wait(browser, 1, EC.element_to_be_clickable((By.XPATH, ELEMENTS["OPORTUNITY_ACCEPT"]))):
                    #     # return False
                    #     continue
                    time.sleep(1.5)
                    browser.find_element(By.XPATH, ELEMENTS["OPORTUNITY_ACCEPT"]).click()
            except Exception as e:
                pass

    for handle in tabs:
        if handle != "main":
            browser.switch_to.window(tabs[handle])
            browser.close()

    browser.switch_to.window(tabs["main"])

def process_config(config_file):
    with open(config_file, "r") as file:
        data = toml.load(file)
        name = data["name"]
        days_to_check = data["days_to_check"] or 9
        email = data["email"]
        start_time = data["start_time"]
        manual_login = data["manual_login"]
        ignore_start_time = data["ignore_start_time"]
        password = os.getenv("PASSWORD") or data["password"]
        working_hours = {key: [] for key in generate_dates(0, 9)}
        for rule, times in data["rules"].items():
            if rule.title() in list(calendar.day_name) or rule.title() in list(calendar.day_abbr):
                is_sun_or_mon = rule.lower() in ["sunday", "monday"]
                offset_map = {
                    "sunday": 0,
                    "monday": 1,
                    "tuesday": 2,
                    "wednesday": 3,
                    "thursday": 4,
                    "friday": 5,
                    "saturday": 6
                }
                date = datetime.strptime(next_date_of(day_of_week="sunday", use_today_if_same=True), "%Y-%m-%d")
                date += timedelta(days=offset_map[rule.lower()])
                date = date.strftime("%Y-%m-%d")

                if is_sun_or_mon and rule.lower() == "sunday":
                    date = [date]
                    next_date = next_date_of(date=date[0], offset=7)
                    date.append(next_date)

                if type(date) is not list:
                    date = [date]
                for time in times:
                    for d in date:
                        _start_time, end_time = time["start_time"], time["end_time"]
                        _start_time, end_time = convert_time_to_seconds(_start_time), convert_time_to_seconds(end_time)
                        if _start_time > end_time:
                            next_date = next_date_of(date=d, offset=1)
                            working_hours[d].append((_start_time, 86399))
                            working_hours[next_date].append((0, end_time))
                        else:
                            working_hours[d].append((_start_time, end_time))
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
        return days_to_check, start_time, manual_login, ignore_start_time, name, email, password, working_hours
                    
                        



def main():
    config_file = os.getenv("CONFIG_FILE") or input("Enter config file: ")
    if not os.path.exists(config_file):
        raise Exception(f"Config file {config_file} does not exist")
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    duration = int(os.getenv("DURATION")) * 60 or int(input("Enter duration in minutes: ")) * 60
    days_to_check, start_time, manual_login, ignore_start_time, name, email, password, working_hours = process_config(config_file) 
    DEBUG = bool(input("Debug mode? (y/n): ").lower() == "y") or False

    debug(f"Starting for {name}\nStart Time: {start_time}\nManual Login: {manual_login}\nIgnore Start Time: {ignore_start_time}\nEmail: {email}\nWorking Hours: {working_hours}\n")

    start_time = get_next_time_epoch_seconds(start_time)
    account = Account((client_id, client_secret), token_backend=FileSystemTokenBackend(token_path="email-tokens", token_filename=f"{name}.secret"))

    if not account.is_authenticated and not account.authenticate(scopes=['basic', 'mailbox']):
        raise Exception("Failed to authenticate with O365")
    logger.info("Authenticated with O365")

    while True:
        browser = None
        try:
            browser = Chrome(headless=True if not DEBUG and not manual_login else False)
            load_cookies(browser, f"cookies/{name}.pkl")
            if manual_login:
                browser.get(URLS["LOGIN_1"])
                input("Press Enter to when done...")
                if not browser_wait(browser, 10, EC.url_contains(URLS["LOGGED_IN"])):
                    raise Exception("Failed to login")
                logger.info("Logged in successfully")
            else:
                if not login(browser, name, password, email, account):
                    raise Exception("Failed to login")
            save_cookies(browser, f"cookies/{name}.pkl")
            # if not sign_out(browser):
            #     logger.error(f"Failed to sign out for {name}")
            #     return False

            # browser.quit()
            if not ignore_start_time:
                wait_for_time(epoch_seconds=start_time - 120)

            # browser = Chrome()
            load_cookies(browser, f"cookies/{name}.pkl")
            if not login(browser, name, password, email, account):
                raise Exception("Failed to login")
            save_cookies(browser, f"cookies/{name}.pkl")
            browser.quit()
            time.sleep(5)
            browser = Chrome(headless=True)
            # browser = Chrome(port=port)
            load_cookies(browser, f"cookies/{name}.pkl")
            while time.time() < start_time + 300 + duration:
                time.sleep(5)
                if not login(browser, name, password, email, account):
                    raise Exception("Failed to login")
                pick_shifts(browser, working_hours, days_to_check)
            save_cookies(browser, f"cookies/{name}.pkl")

            browser.quit()
            logger.info(f"Finished for {name}\n")
            return True
        except Exception as e:
            browser.quit()
            debug(f"Error in main: {e}")
            continue
        
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