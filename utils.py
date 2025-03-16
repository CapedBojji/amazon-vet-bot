import calendar
from datetime import datetime, timedelta
import unittest

def get_next_day_date(target_day: str) -> str:
    # Map day names/abbreviations to an index, with Sunday as 0.
    days = {
        'sunday': 0, 'sun': 0,
        'monday': 1, 'mon': 1,
        'tuesday': 2, 'tue': 2,
        'wednesday': 3, 'wed': 3,
        'thursday': 4, 'thu': 4,
        'friday': 5, 'fri': 5,
        'saturday': 6, 'sat': 6
    }
    
    # Normalize input and retrieve the target day's index.
    target_index = days[target_day.lower()]
    
    # Get today's date.
    today = datetime.today().date()
    
    # Calculate days until the next Sunday.
    # Python's weekday() returns 0 for Monday ... 6 for Sunday.
    if today.weekday() == 6:  # Today is Sunday.
        days_until_sunday = 7  # Force "next" Sunday.
    else:
        days_until_sunday = 6 - today.weekday()
    
    next_sunday = today + timedelta(days=days_until_sunday)
    
    # Get the date for the target day in the week starting from next Sunday.
    target_date = next_sunday + timedelta(days=target_index)
    
    # Return the date in "YYYY-MM-DD" format.
    return target_date.strftime("%Y-%m-%d")

def convert_to_year_mon_day(date_str: str) -> tuple:
    # List of common date formats to try.
    date_formats = [
        "%Y-%m-%d",    # e.g., 2023-03-21
        "%m/%d/%Y",    # e.g., 03/21/2023
        "%B %d, %Y",   # e.g., March 21, 2023
        "%b %d, %Y",   # e.g., Mar 21, 2023
        "%d-%b-%Y",    # e.g., 21-Mar-2023
        "%d %B %Y",    # e.g., 21 March 2023
    ]
    
    # Try each format until one matches.
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            # Return a tuple with success flag and formatted date.
            return (True, parsed_date.strftime("%Y-%m-%d"))
        except ValueError:
            continue  # Try the next format.
    
    # If no format matches, return False with None.
    return (False, None)

def split_interval_seconds(start_sec: int, end_sec: int, date_str: str) -> list:
    """
    Given a start and end time in seconds and a date (YYYY-MM-DD),
    returns a list of one or two tuples. Each tuple is:
      (date, start_seconds, end_seconds)
    
    - If the interval is within one day, returns one tuple.
    - If the interval spans midnight, returns two tuples: one for the starting day
      and one for the next day.
    
    It's assumed that the interval spans at most two days.
    """
    # Convert the input date string to a datetime.date object.
    start_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    
    # Check if the interval does NOT cross midnight.
    if start_sec <= end_sec:
        return [(start_date.strftime("%Y-%m-%d"), start_sec, end_sec)]
    
    # Otherwise, the interval crosses midnight.
    # For the first day, the interval is from start_sec to 86399 (i.e. 23:59:59).
    first_interval = (start_date.strftime("%Y-%m-%d"), start_sec, 86399)
    
    # For the next day, the interval is from 0 to end_sec.
    next_date = start_date + timedelta(days=1)
    second_interval = (next_date.strftime("%Y-%m-%d"), 0, end_sec)
    
    return [first_interval, second_interval]

def convert_time_to_seconds(time: str):
    hours, minutes = time.split(":")
    return int(hours) * 3600 + int(minutes) * 60

def is_time_between(start_time: int, end_time: int, other_start_time: int, other_end_time: int):
    return start_time <= other_start_time < end_time and start_time < other_end_time <= end_time

def generate_dates(start: int, end: int, offset: int = 0): 
    today = datetime.today().date()
    dates = []
    for i in range(start, end + 1):
        dates.append((today + timedelta(days=i + offset)).strftime("%Y-%m-%d"))
    return dates

def is_valid_day(day_str):
    # Normalize to lowercase for comparison.
    day_lower = day_str.lower()
    # Generate lists of valid full and abbreviated day names.
    valid_full = [day.lower() for day in calendar.day_name]
    valid_abbr = [day.lower() for day in calendar.day_abbr]
    return day_lower in valid_full or day_lower in valid_abbr

def time_to_seconds(time_str):
    hours, minutes = time_str.split(":")
    return int(hours) * 3600 + int(minutes) * 60


# def get_current_time_seconds():
#     now = datetime.now()
#     midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
#     seconds_since_midnight = (now - midnight).total_seconds()
#     return int(seconds_since_midnight)

def get_next_time_in_seconds(time_str):
    target_time = time_to_seconds(time_str)
    current_time = get_current_time_seconds()
    if current_time < target_time:
        return target_time
    return target_time + 86400


def get_current_time_seconds():
    now = datetime.now()
    return now.hour * 3600 + now.minute * 60 + now.second


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
