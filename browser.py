from typing import List
from selenium.webdriver import ActionChains
from undetected_chromedriver import By, Chrome, WebElement, webelement
from undetected_chromedriver.options import ChromeOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import re
import time
import pickle


class Browser:
    def __init__(self, binary_location: str | None = None, headless=False) -> None:
        options = ChromeOptions()
        if binary_location:
            options.binary_location = binary_location
        self.__driver = Chrome(headless=headless, options=options)
        self.__action_chain = ActionChains(self.__driver)

    def go_to(
        self,
        url: str,
        wait_for_page_load=None,
        wait_for_elements: list[str] | None = None,
    ) -> None:
        self.__driver.get(url)
        if wait_for_page_load is not None:
            self.wait_for_page_load(
                wait_for_page_load, full_page=True, elements=wait_for_elements
            )

    def new_tab(self) -> str:
        self.__driver.switch_to.new_window("tab")
        tab_id = self.__driver.current_window_handle
        return tab_id

    def click_on(self, xpath, index=0) -> int:
        elements = self.__driver.find_elements(By.XPATH, xpath)
        if elements is None or len(elements) == 0:
            return 0
        if len(elements) - 1 < index:
            return 0
        element = elements[index]

        element.click()
        return 1

    def get_driver(self):
        return self.__driver

    def url_match(self, regex) -> bool:
        return re.search(regex, self.__driver.current_url) is not None

    def save_cookies(self, file_path):
        pickle.dump(self.__driver.get_cookies(), open(file_path, "rb"))

    def load_cookies(self, file_path):
        if os.path.exists(file_path) and os.path.isfile(file_path):
            cookies = pickle.load(open(file_path, "rb"))

            # Enables network tracking so we may use Network.setCookie method
            self.__driver.execute_cdp_cmd("Network.enable", {})

            # Iterate through pickle dict and add all the cookies
            for cookie in cookies:
                # Fix issue Chrome exports 'expiry' key but expects 'expire' on import
                if "expiry" in cookie:
                    cookie["expires"] = cookie["expiry"]
                    del cookie["expiry"]

                # Set the actual cookie
                self.__driver.execute_cdp_cmd("Network.setCookie", cookie)

            # Disable network tracking
            self.__driver.execute_cdp_cmd("Network.disable", {})
            return 1

        return 0

    def perform_actionset(self, actionset: list, *args) -> bool:
        for index, action in enumerate(actionset):
            if action.get("action") == "TYPE":
                if not self.perform_type_action(action, args[index]):
                    return False
            elif action.get("action") == "CLICK":
                if not self.perform_click_action(action):
                    return False
        return True

    def perform_click_action(self, action) -> bool:
        if "element" not in action:
            return False

        xpath = action["element"]
        try:
            self.wait_for_element(xpath)
            element = self.__driver.find_element(By.XPATH, xpath)
            element.click()
            return True
        except Exception as e:
            print(e)
            return False

    def perform_type_action(self, action, value) -> bool:
        if value is None:
            print("[Error] expected value to be string, got None: perform_type_action")
            return False
        if "element" not in action:
            return False
        xpath = action["element"]
        try:
            self.wait_for_element(xpath)
            element = self.__driver.find_element(By.XPATH, xpath)
            element.send_keys(value)
            print(f"Sent keys {value} to element {xpath}")
            return True
        except Exception as e:
            print(e)
            return False

    def wait_for_element(self, selector_value, timeout=10, selector_type=By.XPATH):
        WebDriverWait(self.__driver, timeout).until(
            EC.presence_of_element_located((selector_type, selector_value))
        )
        WebDriverWait(self.__driver, timeout).until(
            lambda d: d.find_element(selector_type, selector_value)
        )

    def wait_for_url(self, url_pattern, timeout=10):
        try:
            # Wait until the URL matches the regex pattern
            WebDriverWait(self.__driver, timeout).until(
                lambda d: re.search(url_pattern, d.current_url)
            )
        except Exception as error:
            print(
                f"An error occured waiting for url {url_pattern}. \n Details: {error}"
            )
            return False
        return True

    def wait_for_browser_close(self, check_interval=0.5):
        try:
            while len(self.__driver.window_handles) > 0:
                time.sleep(check_interval)  # Check every 0.5 seconds by default
        except Exception as e:
            print(f"Exception occurred: {e}")

    def find_elements(self, selector_type, selector_value):
        return self.__driver.find_elements(selector_type, selector_value)

    def find_element(self, selector_value, selector_type=By.XPATH):
        return self.__driver.find_element(selector_type, selector_value)

    def click_element(self, element=None, selector_value=None, selector_type=By.XPATH):
        if element is None and selector_value is None:
            raise Exception(
                "You must provided either an element or selector to click on"
            )
        if selector_value is not None:
            element = self.find_element(selector_value, selector_type)
        assert element is not None, "Expected value, but got None: element"
        self.__action_chain.move_to_element(element)
        element.click()


def main():
    print("Reached")
    binary_location = "/home/freren/.local/share/flatpak/exports/bin/com.brave.Browser"
    browser = Browser(binary_location)
    browser.go_to("https://nowsecure.nl")

    browser.go_to("https://www.youtube.com/shorts/T_B2d4EAjgc")
    browser.wait_for_page_load(
        "^https://www.youtube.com/shorts/T_B2d4EAjgc$", full_page=True
    )
    browser.wait_for_browser_close()


if __name__ == "__main__":
    main()
