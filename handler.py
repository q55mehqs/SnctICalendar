import csv
from datetime import date, datetime, timedelta
from typing import Any, Dict, Union

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

def make_grade_text(grade: int) -> str:
    if grade > 0 and grade < 6:
        return f"{grade}年"
    elif grade == 6:
        return "専1"
    elif grade == 7:
        return "専2"
    else:
        return "全学年"

class CalendarManager:
    def __init__(self, grade: int):
        self.grade = grade
        self.grade_text = make_grade_text(grade)

        self.text = (
            "BEGIN:VCALENDAR\r\n" +
            "PRODID:-//jugyobot//q55mehqs//KadaiCalendar//JP\r\n" +
            "VERSION:2.0\r\n" +
            "CALSCALE:GREGORIAN\r\n" +
            "METHOD:PUBLISH\r\n" +
            f"X-WR-CALNAME:仙台高専 年間行事予定 ({self.grade_text})\r\n" +
            "X-WR-TIMEZONE:Asia/Tokyo\r\n" +
            f"X-WR-CALDESC:仙台高専 {self.grade_text}の年間行事予定\r\n")

    def add_data(self, schedule):
        if self.grade == 0 and not schedule['全学年予定']:
            return

        f = '%Y%m%d'
        stdate = datetime.strptime(schedule['開始日'], "%Y-%m-%d")
        endate = datetime.strptime(schedule['終了日'], "%Y-%m-%d") if schedule['終了日'] else stdate
        endate = endate + timedelta(days=1)

        summary = self.make_summary(schedule)
        if not summary:
            return

        self.text += (
            "BEGIN:VEVENT\r\n" +
                f"DTSTART;VALUE=DATE:{datetime.strftime(stdate, f)}\r\n" +
                f"DTEND;VALUE=DATE:{datetime.strftime(endate, f)}\r\n" +
                f"SUMMARY:{summary}\r\n" +
                f"DESCRIPTION:{summary}\r\n" +
            "END:VEVENT\r\n"
        )

    def make_summary(self, schedule: Dict[str, str]) -> str:
        summary_data = []
        if schedule['全学年予定']:
            summary_data.append(schedule['全学年予定'])

        column = grade_columns[self.grade]
        if column is None:
            for i in range(1,8):
                col = grade_columns[i]
                if col == None:
                    continue

                if schedule[col]:
                    summary_data.append(f'[{make_grade_text(i)}] {schedule[col]}')
            return ', '.join(summary_data)

        if schedule[column]:
            summary_data.append(f'[{self.grade_text}] {schedule[column]}')

        return ', '.join(summary_data)

    def get_cal(self):
        return self.text + "END:VCALENDAR"

def now_year():
    today = date.today()
    return today.year if today.month <= 4 else today.year - 1

def lambda_handler(event: Dict[str, Any], context):
    print(event)
    if event['queryStringParameters']:
        param = event['queryStringParameters']
        year = int(param['year']) if 'year' in param and param['year'].isdigit() else now_year()

        grade = int(param['grade']) if 'grade' in param and param['grade'].isdigit() else 0
    else:
        year = now_year()
        grade = 0

    manager = CalendarManager(grade)

    with open(f'SnctSchedules/{year}.csv', 'r', encoding='utf-8', newline="") as f:
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
