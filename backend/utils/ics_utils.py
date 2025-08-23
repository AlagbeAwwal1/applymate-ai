from datetime import datetime, timedelta, timezone

def simple_ics(summary: str, due_date: datetime) -> str:
        # Minimal .ics string (UTC)
        dt = due_date.astimezone(timezone.utc)
        stamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
        dtstr = dt.strftime('%Y%m%dT%H%M%SZ')
        ics = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//ApplyMate AI//EN
BEGIN:VEVENT
UID:{stamp}-applymate@example.com
DTSTAMP:{stamp}
DTSTART:{dtstr}
SUMMARY:{summary}
END:VEVENT
END:VCALENDAR"""
        return ics
