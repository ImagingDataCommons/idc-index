from datetime import datetime
import pytz

def area(location):
    """This function takes in a location as argument, checks the list of locations available and returns the formatted time to the user."""
    location = format_location(location)
    for areas in pytz.all_timezones:
        if location.lower() in areas.lower():
            location = areas
            tz = pytz.timezone(location)
            date_now = datetime.now(tz)
            formatted_date = date_now.strftime("%B %d, %Y %H:%M:%S")
            print(f"{location} time: ", formatted_date)
            break

    else:
        print("This location isn't on the tz database on Wikipedia")

def area_zone(zone):
    """This function takes in a time zone as argument, checks the list of timezones and returns the formatted time to the user."""
    try:
        zone = timezones(zone)
        tz = pytz.timezone(zone)
        date_now = datetime.now(tz)
        formatted_date = date_now.strftime("%B %d, %Y %H:%M:%S")
        print(f"{zone} time: ", formatted_date)

    except Exception:
        print("Timezone is not on the list. Consider using location instead.")

def timezones(zone):
    """This function is used to handle situations of Daylight Saving Time that the standard library can't recognize."""
    zones = {
        "PDT": "PST8PDT",
        "MDT": "MST7MDT",
        "EDT": "EST5EDT",
        "CDT": "CST6CDT",
        "WAT": "Etc/GMT+1",
        "ACT": "Australia/ACT",
        "AST": "Atlantic/Bermuda",
        "CAT": "Africa/Johannesburg",
    }

    try:
        zones[zone]

    except:
        return zone
    return zones[zone]

def format_location(location):
    location = location.replace(" ", "_")
    return location