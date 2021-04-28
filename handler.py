import csv
from datetime import date, datetime, timedelta
from typing import Any, Dict, Union, OrderedDict

grade_columns = {
    0: None,
    1: '1年個別予定',
    2: '2',
    3: '3',
    4: '4',
    5: '5',
    6: '専1',
    7: '専2'
} # type: Dict[int, Union[None, str]]

class CalendarManager:
    def __init__(self, grade: int):
        self.grade = grade
        grade_text = f"{grade}年"
        if grade == 6:
            grade_text = "専1"
        elif grade == 7:
            grade_text = "専2"
        else:
            grade_text = "全学年"

        self.grade_text = grade_text

        self.text = (
            "BEGIN:VCALENDAR\n" +
            "VERSION:2.0\n" +
            "PRODID:-//jugyobot//q55mehqs//KadaiCalendar//JP\n" +
            f"X-WR-CALNAME:仙台高専 年間行事予定 ({grade_text})" +
            "X-WR-TIMEZONE:JST" +
            f"X-WR-CALDESC:仙台高専 {grade_text}の年間行事予定")

    def add_data(self, schedule):
        f = '%Y%m%d'
        stdate = datetime.strptime(schedule['開始日'], "%Y-%m-%d")
        endate = datetime.strptime(schedule['開始日'], "%Y-%m-%d") if not schedule['終了日'] else stdate + timedelta(days=1)

        summary = self.make_summary(schedule)

        self.text += (
            "BEGIN:VEVENT\n" +
                f"DTSTART;TZID=Asia/Tokyo;VALUE=DATE:{datetime.strftime(stdate, f)}\n" +
                f"DTEND;TZID=Asia/Tokyo;VALUE=DATE:{datetime.strftime(endate, f)}\n" +
                f"SUMMARY:{summary}\n" +
                f"DESCRIPTION:{summary}\n" +
            "END:VEVENT\n"
        )

    def make_summary(self, schedule: Dict[str, str]) -> str:
        text = []
        if schedule['全学年予定']:
            text.append(schedule['全学年予定'])

        column = grade_columns[self.grade]
        if column is None:
            return text[0]

        if schedule[column]:
            text.append(f'({self.grade_text}) {schedule[column]}')

        return ', '.join(text)

    def get_cal(self):
        return self.text + "END:VCALENDAR"

def now_year():
    today = date.today()
    return today.year if today.month < 4 else today.year - 1

def handler(event: Dict[str, Any], context):
    grade = event['grade'] if 'grade' in event else 0 # type: int
    manager = CalendarManager(grade)

    with open(f'SnctSchedules/{now_year}.csv', 'r', encoding='utf-8', newline="") as f:
        ds = csv.DictReader(f)

        for d in ds:
            manager.add_data(d)

    return {
        'statusCode': 200,
        'headers': {
            "Content-Type": "text/calendar"
        },
        'body': manager.get_cal()
    }
