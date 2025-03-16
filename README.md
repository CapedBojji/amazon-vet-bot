# AtoZBot - Automated Shift Picking for Amazon A to Z

AtoZBot is a Python-based automation tool designed to help Amazon employees automatically pick shifts on the A to Z platform based on your preferred working hours and availability.

## Overview

AtoZBot automatically:
- Logs into your Amazon A to Z account
- Navigates to the shift selection page
- Monitors for available shifts that match your preferred working hours
- Automatically selects shifts that fit your criteria
- Handles the two-factor authentication process via email
- Runs headlessly in the background

## Requirements

- Python 3.8 or higher
- Chrome browser installed
- Microsoft 365 email account for 2FA code retrieval

## Configuration

### Environment Variables

The application expects the following environment variables in a `.env` file:

```.env
CLIENT_ID=your_microsoft_365_app_client_id
CLIENT_SECRET=your_microsoft_365_app_client_secret
DAYS_TO_CHECK=9
DURATION=10
CONFIG_FILE=config.toml
PASSWORD=your_amazon_password
```

- **CLIENT_ID/CLIENT_SECRET**: Required for Microsoft Graph API to access your email for 2FA codes
- **DAYS_TO_CHECK**: Number of days to look ahead for shifts (default: 9)
- **DURATION**: How long to run the script in minutes (default: 10)
- **CONFIG_FILE**: Path to your configuration file (default: config.toml)
- **PASSWORD**: Your Amazon login password

### Microsoft Graph API Setup

To set up access to your Microsoft email account:
1. Visit the [O365-Python GitHub repository](https://github.com/O365/python-o365) for detailed instructions
2. Follow their guide to register an application with Microsoft
3. Make sure to request the appropriate permissions (`basic`, `mailbox`)
4. Use the provided Client ID and Secret in your `builtin.env` file

### config.toml Configuration

The `config.toml` file contains your personal preferences for shift selection:

```toml
name = "your_amazon_username"
email = "your_email@example.com"
start_time = "21:00"  # When to start checking for shifts (24h format)
manual_login = false  # Set to true if you want to log in manually
ignore_start_time = false  # Set to true to start immediately

[rules]
# Day-based rules (can use full day names or abbreviations)
Monday = [
    { start_time = "6:15am", end_time = "4:45pm" }
]
Tuesday = [
    { start_time = "6:15am", end_time = "4:45pm" }
]
# Date-specific rules override day-based rules
"2025-04-01" = [
    { start_time = "6:15am", end_time = "12:15pm" }
]
```

- **name**: Your Amazon login username
- **email**: Email address used for 2FA
- **start_time**: When to begin checking for shifts (24-hour format)
- **manual_login**: Enable if you want to authenticate manually
- **ignore_start_time**: Start immediately, regardless of start_time setting

The `[rules]` section lets you specify when you're available to work. You can set:
- **Day-based rules**: Apply to specific days of the week
- **Date-specific rules**: Apply to specific calendar dates (override day rules)

Each rule contains a start and end time for your availability window.

## How It Works

1. The application initializes a Chrome browser instance
2. It loads saved cookies to attempt a quick login
3. If cookies are invalid, it performs a full login with 2FA:
   - Enters username and password
   - Retrieves verification code from your email
   - Submits the code to complete authentication
4. At the specified start time, it begins checking for shifts
5. For each available shift, it checks if the shift time falls within your specified working hours
6. When a matching shift is found, it automatically accepts it
7. The process continues until the specified duration has elapsed

## Running the Application

### Using the Executable

The simplest way to run AtoZBot is using the provided executable:

```
AtoZBot_win.exe
```

### Running from Source

To run from source code:

```
python app.py
```

## Building from Source

A build script is included to package the application as an executable:
When building from source, application expects the builtin.env file to be present in the root directory.
and it should contain the following environment variables:
```
CLIENT_ID=your_microsoft_365_app_client_id
CLIENT_SECRET=your_microsoft_365_app_client_secret
```
To build the application, run:

```
python build.py
```

This will create an executable for your current platform in the dist directory.

## Notes

- The application uses "undetected_chromedriver" to minimize detection by Amazon's bot protection
- Cookies are saved between sessions to improve login speed
- Email tokens are stored in the "email-tokens" directory for Microsoft Graph API authentication
- All sensitive information is stored locally and not transmitted elsewhere

## Disclaimer

This tool is for educational purposes only. Use at your own risk and in compliance with Amazon's terms of service.