from datetime import date, timedelta
import re


def parse_date(text: str) -> date | None:
    text = text.lower()

    today = date.today()

    if "сегодня" in text:
        return today
    if "завтра" in text:
        return today + timedelta(days=1)
    if "послезавтра" in text:
        return today + timedelta(days=2)

    # 12.01 or 12/01
    m = re.search(r"(\d{1,2})[./](\d{1,2})", text)
    if m:
        day, month = map(int, m.groups())
        return date(today.year, month, day)

    return None
