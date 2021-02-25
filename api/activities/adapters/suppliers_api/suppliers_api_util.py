from datetime import date, timedelta

weekdays_map = {
    "MONDAY": 0,
    "TUESDAY": 1,
    "WEDNESDAY": 2,
    "THURSDAY": 3,
    "FRIDAY": 4,
    "SATURDAY": 5,
    "SUNDAY": 6,
}


def expand_schedule(availabilities):
    """Takes availability information, listed with a from_date and to_date,
    along with a list of weekdays the product is available.  Expands to a list
    of dates, and filtered for weekdays the product is available.

    For examples,
    {
      "days": ["MONDAY", "TUESDAY"],
      "from_date": "2021-01-01",
      "to_date": "2021-01-14",
    }

    Expands to a list:
    2021-01-04T12:00 (Mon)
    2020-01-05T12:00 (Tue)
    2020-01-11T12:00 (Mon)
    2020-01-12T12:00 (Tue)
    """

    begin_date = date.fromisoformat(availabilities["from"])
    end_date = date.fromisoformat(availabilities["to"])
    delta = end_date - begin_date
    days_of_week = list(weekdays_map[x] for x in availabilities["days"])

    times = []
    for i in range(delta.days + 1):
        day = begin_date + timedelta(days=i)
        if day.weekday() not in days_of_week:
            continue

        times.append(day)

    return times
