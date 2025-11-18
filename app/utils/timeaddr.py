"""
Timezone and address utilities
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, Optional

import pytz
from dateutil import parser

# Load timezone mapping data
_timezone_mapping: Optional[list] = None


def _load_timezone_mapping() -> list:
    """(Lazy) Load timezone mapping from JSON file"""
    global _timezone_mapping
    if _timezone_mapping is None:
        current_dir = os.path.dirname(__file__)
        json_path = os.path.join(current_dir, "timezone_mapper.json")
        with open(json_path, "r") as f:
            _timezone_mapping = json.load(f)
    return _timezone_mapping


class TimezoneEntry:
    """Timezone mapping entry"""

    def __init__(self, data: Dict[str, Any]):
        self.state_code = data["stateCode"]
        self.state = data["state"]
        self.zipcode_start = data["zipcodeStart"]
        self.zipcode_end = data["zipcodeEnd"]
        self.timezone_id = data["timezoneId"]


def get_datetime_by_address(date_str: str, time_str: str, address: str) -> datetime:
    """
    Get datetime object from date string, time string, and address

    Args:
        date_str: Date in "Month Day, Year" format
        time_str: Time in "HH:mm" format
        address: Address string to extract timezone from

    Returns:
        datetime object in the appropriate timezone

    Raises:
        ValueError: If timezone cannot be determined from address
    """
    timezone_id = get_timezone_id_by_address(address)
    if not timezone_id:
        raise ValueError(f'Could not get timezone ID for: "{address}".')

    return get_datetime_by_timezone_id(date_str, time_str, timezone_id)


def get_datetime_by_timezone_id(
    date_str: str, time_str: str, timezone_id: str
) -> datetime:
    """
    Create datetime from date string, time string, and timezone id

    Args:
        date_str: Date string in any format
        time_str: Time string in any format
        timezone_id: Timezone identifier (e.g., "America/New_York")

    Returns:
        datetime object in UTC

    Raises:
        ValueError: If date/time parsing fails
    """
    try:
        # Parse date string
        date_part = parser.parse(date_str)
        if not date_part:
            raise ValueError(f'Invalid dateStr: "{date_str}".')

        time_part = parser.parse(time_str)
        if not time_part:
            raise ValueError(f'Invalid timeStr: "{time_str}".')

        # print(date_part)
        # print(time_part)

        # Create timezone-aware datetime
        tz = pytz.timezone(timezone_id)

        # Combine date and time
        local_dt = tz.localize(
            datetime(
                year=date_part.year,
                month=date_part.month,
                day=date_part.day,
                hour=time_part.hour,
                minute=time_part.minute,
                second=0,
            )
        )

        # print(local_dt)

        return local_dt

    except Exception as e:
        raise ValueError(
            f'Error creating datetime for "{date_str} {time_str}" in timezone "{timezone_id}": {str(e)}'
        )


def get_timezone_id_by_address(address: str) -> Optional[str]:
    """
    Extract timezone from address by looking up zipcode

    Args:
        address: Address string

    Returns:
        Timezone ID or None if not found
    """
    # Extract zipcode from address (last part)
    address_parts = address.split(" ")
    zipcode = address_parts[-1]
    return get_timezone_id_by_zipcode(zipcode)


def format_full_address_line(street: str, city: str, zipcode: str) -> str:
    """
    Format full address line with lookup state code

    Args:
        street: Street address
        city: City name
        zipcode: ZIP code

    Returns:
        Formatted address string
    """
    state_code = _get_state_code(zipcode)
    if state_code:
        return f"{street}, {city}, {state_code} {zipcode}"
    return f"{street}, {city}, {zipcode}"


def to_12hr(time: datetime) -> str:
    """Convert datetime to 12-hour format string"""
    return time.strftime("%I:%M %p")


def to_24hr(time: datetime) -> str:
    """Convert datetime to 24-hour format string"""
    return time.strftime("%H:%M")


def get_timezone_id_by_zipcode(zipcode: str) -> Optional[str]:
    """
    Get timezone ID from zipcode

    Args:
        zipcode: ZIP code string

    Returns:
        Timezone ID or None if not found
    """
    entry = _lookup_zipcode(zipcode)
    if entry:
        return entry.timezone_id
    return None


def _get_state_code(zipcode: str) -> Optional[str]:
    """
    Get state code from zipcode

    Args:
        zipcode: ZIP code string

    Returns:
        State code or None if not found
    """
    entry = _lookup_zipcode(zipcode)
    if entry:
        return entry.state_code
    return None


def _lookup_zipcode(zipcode_str: str) -> Optional[TimezoneEntry]:
    """
    Look up zipcode in timezone mapping

    Args:
        zipcode_str: ZIP code string

    Returns:
        TimezoneEntry or None if not found
    """
    try:
        zipcode = int(zipcode_str)
    except (ValueError, TypeError):
        return None

    mapping = _load_timezone_mapping()
    for entry_data in mapping:
        entry = TimezoneEntry(entry_data)
        if entry.zipcode_start <= zipcode <= entry.zipcode_end:
            return entry

    return None
