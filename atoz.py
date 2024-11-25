from dotenv import load_dotenv
from undetected_chromedriver import By
from browser import Browser
import os

from utils import obfuscate_email

ATOZ_URLS = {
    "LOGIN": "https://atoz-login.amazon.work/",
}
ATOZ_ACTIONS = {
    "LOGIN_ONE": [
        {"action": "TYPE", "element": '//*[@id="associate-login-input"]'},
        {"action": "CLICK", "element": '//*[@id="login-form-login-btn"]'},
    ],
    "LOGIN_TWO": [
        {"action": "TYPE", "element": '//*[@id="password"]'},
        {"action": "CLICK", "element": '//*[@id="buttonLogin"]'},
    ],
}


class AtoZClient:
    def __init__(self, username, password, browser: Browser, cookies_file="") -> None:
        self.__username = username
        self.__password = password
        self.__browser = browser
        self.__cookies_file = cookies_file

    def authenticate(
        self, verification_handler, verification_email=None, save_cookies=True
    ):
        browser = self.__browser
        browser.load_cookies(self.__cookies_file)
        browser.new_tab()
        browser.go_to(ATOZ_URLS["LOGIN"])
        if not browser.get_driver().current_url == ATOZ_URLS["LOGIN"]:
            if save_cookies:
                browser.save_cookies(self.__cookies_file)
            print("Already authenticated")
            return 0
        browser.perform_actionset(ATOZ_ACTIONS["LOGIN_ONE"], self.__username)
        browser.wait_for_url(
            "^https://idp.amazon.work/idp/profile/SAML2/Unsolicited/SSO?"
        )
        browser.perform_actionset(ATOZ_ACTIONS["LOGIN_TWO"], self.__password)
        if browser.wait_for_url(
            r"^https:\/\/idp.amazon.work\/idp\/enter\?sif_profile=amazon-passport"
        ):
            if verification_email is not None:
                obfuscated = obfuscate_email(verification_email)
                label = browser.find_element(
                    f"//label[normalize-space()='{obfuscated}']"
                )
                input_element = label.find_element(By.TAG_NAME, "input")
                browser.click_element(input_element)
                browser.click_element(selector_value='//*[@id="buttonContinue"]')
                code = verification_handler()
        else:
            print("Url not found")


def verification_handler():
    code = input("Enter login code")
    return code


def main():
    load_dotenv()
    binary_location = "/home/freren/.local/share/flatpak/exports/bin/com.brave.Browser"
    browser = Browser(binary_location)
    username = os.getenv("AMAZON_USERNAME")
    password = os.getenv("AMAZON_PASSWORD")
    email = os.getenv("AMAZON_VERIFICATION_EMAIL")

    atoz_client = AtoZClient(username, password, browser)
    atoz_client.authenticate(verification_handler, email)

    browser.wait_for_browser_close()


if __name__ == "__main__":
    main()
