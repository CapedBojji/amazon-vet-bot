import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from requests.models import HTTPError

from datetime import datetime


class GmailClient:
    def __init__(self, credentials_file, scopes, token_file=None) -> None:
        self.__token_file = token_file
        self.__credentials_file = credentials_file
        self.__scopes = scopes
        self.__service = None
        self.__creds = None

    def authenticate(self, save_token=True):
        if self.__service is not None:
            return 1

        if self.__token_file is not None and os.path.exists(self.__token_file):
            self.__creds = Credentials.from_authorized_user_file(
                self.__token_file,
            )

        if not self.__creds or not self.__creds.valid:
            if self.__creds and self.__creds.expired and self.__creds.refresh_token:
                self.__creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", self.__scopes
                )
                self.__creds = flow.run_local_server(port=0)

            if save_token:
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(self.__creds.to_json())

        try:
            self.__service = build("gmail", "v1", credentials=self.__creds)
        except HTTPError as error:
            print(f"An error occurred could not authenticate: {error}")
            return 1

        return 0

    def search_emails(self, sender=None, start_date=None):
        """
        Search emails by sender and/or start date.

        Args:
            sender (str): The email address of the sender.
            start_date (str): The start date in format YYYY/MM/DD.

        Returns:
            list: A list of email IDs that match the search criteria.
        """
        # Ensure authenticated
        if self.__service is None:
            print("[ERROR] cannot search emails not authenticated")
            return []

        query = ""
        if sender:
            query += f"from:{sender} "
        if start_date:
            query += f"after:{start_date} "

        try:
            results = (
                self.__service.users()
                .messages()
                .list(userId="me", q=query.strip())
                .execute()
            )
            messages = results.get("messages", [])
            return [msg["id"] for msg in messages]

        except HttpError as error:
            print(f"An error occurred: {error}")
            return []

    def read_email(self, message_id):
        """
        Read the content of an email by its ID.

        Args:
            message_id (str): The ID of the email to retrieve.

        Returns:
            dict: A dictionary containing the email subject and body snippet.
        """
        # Ensure authenticated
        if self.__service is None:
            print("[ERROR] cannot search emails not authenticated")
            return []

        try:
            message = (
                self.__service.users()
                .messages()
                .get(userId="me", id=message_id)
                .execute()
            )
            subject = next(
                header["value"]
                for header in message["payload"]["headers"]
                if header["name"] == "Subject"
            )
            snippet = message["snippet"]
            return {"subject": subject, "snippet": snippet}

        except HttpError as error:
            print(f"An error occurred: {error}")
            return None


def main():
    scopes = ["https://www.googleapis.com/auth/gmail.readonly"]
    gmail_client = GmailClient("credentials.json", scopes, "token.json")

    gmail_client.authenticate()

    # Search for emails from a specific sender after a given date
    email_ids = gmail_client.search_emails(
        sender="capedbojji@gmail.com", start_date=datetime.today().strftime("%Y/%m/%d")
    )
    print("Found email IDs:", email_ids)

    # Read the content of the first email found
    if email_ids:
        email_content = gmail_client.read_email(email_ids[0])
        print("Email Content:", email_content)


if __name__ == "__main__":
    main()
