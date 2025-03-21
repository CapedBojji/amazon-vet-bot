
from datetime import datetime, timedelta
from time import time, sleep


def convert_to_military(time_str: str) -> str:
    # Parse the input string which is in the format "6:15pm" or "06:15 PM"
    dt = datetime.strptime(time_str.strip().lower(), "%I:%M%p")
    return dt.strftime("%H:%M")

def generate_dates(offset = 0, amount = 1, offset_from_today=False, format="%Y-%m-%d", use_today_if_sunday=True):
    today = datetime.today().date()
    if today.weekday() == 6:
        if use_today_if_sunday:
            start = today + timedelta(days=offset) if offset_from_today else today
        else:
            start = today + timedelta(days=7) + timedelta(days=offset) if offset_from_today else today + timedelta(days=7)
    else:
        start = today + timedelta(days=offset) if offset_from_today else today + timedelta(days=(6 - today.weekday()))

    dates = []
    for i in range(amount):
        dates.append((start + timedelta(days=i)).strftime(format))

    return dates


def next_date_of(date=None, offset=0, day_of_week="monday", use_today_if_same=True, format="%Y-%m-%d"):
    if date is not None:
        return (datetime.strptime(date, format) + timedelta(days=offset)).strftime(format)

    today = datetime.today().date()
    day_of_week = day_of_week.lower()

    days_map = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6
    }

    if day_of_week not in days_map:
        raise ValueError("Invalid day of week.")
    
    target_day = days_map[day_of_week]

    delta_days = (target_day - today.weekday() + 7) % 7
    if delta_days == 0 and not use_today_if_same:
        delta_days = 7
    return (today + timedelta(days=delta_days)).strftime(format)

def get_next_week(day_of_week, format="%Y-%m-%d"):
    # Get sunday
    today = datetime.today().date()
    next_sunday = today + timedelta(days=(6 - today.weekday()))
    days_map = {
        "sunday": 0,
        "monday": 1,
        "tuesday": 2,
        "wednesday": 3,
        "thursday": 4,
        "friday": 5,
        "saturday": 6
    }

    if day_of_week is not None and day_of_week in days_map:
        target_day = days_map[day_of_week]
        return (next_sunday + timedelta(days=target_day)).strftime(format)
    
    raise NotImplementedError("Use case not implemented.")


def wait_for_time(epoch_seconds=0):
    if epoch_seconds:
        while True:
            if time() >= epoch_seconds:
                break
            sleep(1)

def convert_time_to_seconds(time: str):
    hours, minutes = time.split(":")
    return int(hours) * 3600 + int(minutes) * 60

def is_time_between(start_time: int, end_time: int, other_start_time: int, other_end_time: int):
    return start_time <= other_start_time < end_time and start_time < other_end_time <= end_time