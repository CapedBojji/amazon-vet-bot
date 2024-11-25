import re
import os
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from browser import Browser
from urllib.parse import quote
from dotenv import load_dotenv
import uuid

ACTIONS = {
    "SIGN_IN": [
        {"action": "TYPE", "element": '//*[@id="username"]'},
        {"action": "TYPE", "element": '//*[@id="password"]'},
        {"action": "CLICK", "element": '//*[@id="staySignedIn"]'},
        {
            "action": "CLICK",
            "element": "/html/body/div[1]/div[4]/div[1]/main/div[1]/div[2]/form/button",
        },
    ]
}

URLS = {"SIGN_IN": "https://account.proton.me/mail"}

URL_PATTERNS = {"LOGGED_IN": r"https://mail.proton.me/u/(\d+)"}


class ProtonMailClient:
    __sign_in_url = "https://account.proton.me/mail"

    def __init__(
        self,
        username,
        password,
        browser: Browser | None,
        cookies_file: str | None = None,
    ) -> None:
        if browser is not None:
            self.__browser: Browser = browser
            self.__is_standalone_browser = False
            self.__tab_id = uuid.uuid4()
            self.__tab_handle = browser.new_tab(self.__tab_id)
        else:
            self.__browser = Browser()
            self.__is_standalone_browser = True

        self.__username = username
        self.__password = password
        self.__cookies_file = cookies_file
        self.__setup()
        print(f"""
                Email: {self.__username}
                Password: {self.__password}
                Account number: {self.__account_number}
              """)

    def __setup(self):
        # Load cookies
        if self.__cookies_file is not None:
            if self.__browser.load_cookies(self.__cookies_file):
                print("Cookies file did not load")
        # Check if already authenticated from cookies
        # If not sign in
        if not self.__is_authenticated():
            self.__authenticate()

    def __authenticate(self):
        if not self.__is_standalone_browser:
            self.__browser.new_tab(self.__tab_id)
        self.__browser.go_to(
            self.__sign_in_url,
            wait_for_page_load=f"{self.__sign_in_url}",
            wait_for_elements=[
                '//*[@id="username"]',
                '//*[@id="password"]',
                '//*[@id="staySignedIn"]',
            ],
        )
        self.__browser.perform_actionset(
            ACTIONS["SIGN_IN"], [{"value": self.__username}, {"value": self.__password}]
        )
        self.__browser.wait_for_page_load(URL_PATTERNS["LOGGED_IN"], full_page=True)
        match = re.match(
            r"https://mail.proton.me/u/(\d+)", self.__browser.get_driver().current_url
        )
        if match is not None:
            self.__account_number = match.group(1)

    def __is_authenticated(self) -> bool:
        return self.__browser.url_match(URL_PATTERNS["LOGGED_IN"])

    # def go_to_page(self, page) -> bool:
    #     if page not in pages:
    #         return False
    #     self.__browser.go_to(urls[page])par
    #     self.__browser.wait_for_page_load(url_patterns[page], full_page=True)
    #     return True
    #
    # def perform_actionset(self, actionset: str, args: list) -> bool:
    #     if actionset == "SIGN_IN":
    #         return self.__browser.perform_actionset(sign_in, args)
    #     return False
    #
    def __switch_to_tab(self):
        self.__browser.new_tab(self.__tab_id)

    def search(
        self, start_date: int | None = None, from_email: str | None = None
    ) -> list[str]:
        # The table of ids that is returned at the end of this function
        ids = []
        # Ensure we are in the proton mail tab
        self.__switch_to_tab()
        # Build the search query
        query = f"https://mail.proton.me/u/{self.__account_number}/almost-all-mail#"
        if from_email is not None:
            query = f"{query}from={quote(from_email)}"
        if start_date is not None:
            query = f"{query}&begin={start_date}"
        # Submit query
        self.__browser.go_to(
            query,
            wait_for_page_load=URL_PATTERNS["LOGGED_IN"],
        )
        # Wait for list to load
        self.__browser.wait_for_element("//*[@data-element-id]")
        # Grab all mail list element and map to their id
        elements = [
            element.get_attribute("data-element-id")
            for element in self.__browser.find_elements(
                By.XPATH, "//*[@data-element-id]"
            )
        ]
        # Process each mail list element
        while len(elements) != 0:
            element = elements.pop()
            self.__browser.click_element(
                selector_value=f"//*[@data-element-id='{element}']"
            )
            # Wait for mail page to load
            self.__browser.wait_for_element("//*[@data-testid='message-content:body']")
            # Grab the id from url
            match = re.match(
                r"^https:\/\/mail.proton.me\/u\/\d+\/(?:almost-all-mail\/)?([A-Za-z0-9_-]+={0,2}).+$",
                self.__browser.get_driver().current_url,
            )
            if match is None:
                raise Exception(
                    "URL pattern mismatch: Expected URL structure does not match. Verify that the URL follows 'https://mail.proton.me/u/{user_id}/{optional-path}{id}'."
                )
            id = match.group(1)
            ids.append(id)
            # Click the back_button
            self.__browser.wait_for_element("//*[data-testid='toolbar:back-button']")
            self.__browser.click_element(
                selector_value="//*[data-testid='toolbar:back-button']"
            )
            # Wait for list to load again
            self.__browser.wait_for_element(
                "/html/body/div[1]/div[3]/div/div[2]/div/div[2]/div/div/div/main/div/div/div/div/div/div[3]"
            )

        return ids

    def get_email_content(self, id, text_only=False) -> str:
        self.__switch_to_tab()
        query = f"https://mail.proton.me/u/{self.__account_number}/inbox/{id}"
        print(query)
        self.__browser.go_to(
            query,
            wait_for_page_load=URL_PATTERNS["LOGGED_IN"],
            wait_for_elements=[
                "/html/body/div[1]/div[3]/div/div[2]/div/div[2]/div/div/div/main/div/div/div/div/div/div[2]",
                "//*[@data-testid='content-iframe']",
            ],
        )
        iframe = self.__browser.find_elements(
            By.XPATH, "//*[@data-testid='content-iframe']"
        )
        if iframe is not None:
            raise Exception("Could not find message Iframe")
        self.__browser.get_driver().switch_to.frame(iframe)
        text = self.__browser.get_driver().find_element(By.ID, "proton-root").text
        return text

    def close(self):
        pass


def main():
    load_dotenv()
    binary_location = "/home/freren/.local/share/flatpak/exports/bin/com.brave.Browser"
    browser = Browser(binary_location)
    email = os.getenv("EMAIL")
    password = os.getenv("PASSWORD")
    client = ProtonMailClient(email, password, browser)
    # mails = client.search(from_email="capedbojji@gmail.com")
    # mail = client.get_email_content(mails[0]).strip()
    # print(f"Mail content: {mail}")
    browser.wait_for_browser_close()


if __name__ == "__main__":
    main()
