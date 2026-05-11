from datetime import datetime
import re
import uuid

def format_datetime(dt: datetime, format: str = "%Y-%m-%d %H:%M:%S") -> str:
    return dt.strftime(format)

def validate_email(email: str) -> bool:
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email))

def generate_session_id() -> str:
    return str(uuid.uuid4())

def parse_date(date_str: str) -> datetime:
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {date_str}")