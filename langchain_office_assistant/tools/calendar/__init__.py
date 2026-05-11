"""Calendar tools module."""

from langchain_core.tools import tool
from typing import List, Optional


class MockCalendarStore:
    """Mock calendar data store."""

    def __init__(self):
        self.meetings = [
            {
                "id": "meet_001",
                "title": "产品评审会议",
                "date": "2025-01-15",
                "time": "10:00",
                "duration": 60,
                "participants": ["zhangsan@company.com", "lisi@company.com"],
                "location": "3号会议室",
                "status": "confirmed"
            },
            {
                "id": "meet_002",
                "title": "团队周会",
                "date": "2025-01-15",
                "time": "14:00",
                "duration": 45,
                "participants": ["team@company.com"],
                "location": "线上会议",
                "status": "confirmed"
            }
        ]
        self.next_id = 3

    def get_meetings(self, date: str) -> List[dict]:
        return [m for m in self.meetings if m["date"] == date]

    def create_meeting(self, data: dict) -> dict:
        meeting = {
            "id": f"meet_{self.next_id:03d}",
            "status": "confirmed",
            **data
        }
        self.meetings.append(meeting)
        self.next_id += 1
        return meeting


_calendar_store = MockCalendarStore()


@tool
def check_calendar(date: str) -> str:
    """Check calendar schedule for a specific date."""
    try:
        meetings = _calendar_store.get_meetings(date)
        if not meetings:
            return f"No meetings scheduled for {date}"

        output = f"📅 Meetings on {date}:\n\n"
        for m in meetings:
            output += (
                f"🕐 {m['time']} - {m['title']}\n"
                f"   Duration: {m['duration']} minutes | Location: {m['location']}\n"
                f"   Attendees: {', '.join(m['participants'])}\n\n"
            )
        return output
    except Exception as e:
        return f"❌ Failed to check calendar: {str(e)}"


@tool
def schedule_meeting(
    title: str,
    date: str,
    time: str,
    duration_minutes: int,
    participants: List[str],
    location: Optional[str] = None,
) -> str:
    """Schedule a new meeting."""
    try:
        meeting = _calendar_store.create_meeting({
            "title": title,
            "date": date,
            "time": time,
            "duration": duration_minutes,
            "participants": participants,
            "location": location or "Online"
        })

        return (
            f"✅ Meeting scheduled successfully!\n\n"
            f"📌 Title: {title}\n"
            f"📅 Date: {date} at {time}\n"
            f"⏱️ Duration: {duration_minutes} minutes\n"
            f"📍 Location: {location or 'Online'}\n"
            f"👥 Attendees: {', '.join(participants)}\n"
            f"🆔 Meeting ID: {meeting['id']}"
        )
    except Exception as e:
        return f"❌ Failed to schedule meeting: {str(e)}"
