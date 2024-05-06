#!/usr/bin/env python3
import json
import sqlite3
import sys

from datetime import datetime, timezone, timedelta


def get_cols():
    return {
        "date_time": "timestamp",
        "week": "TEXT",
        "remote_address": "TEXT",
        "referer": "TEXT",
        "method": "TEXT",
        "url_path": "TEXT",
        "status": "INTEGER",
        "user_agent": "TEXT",
        "request_time_in_seconds": "REAL",
    }


def format_timestamp(timestamp):
    month_dict = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12,
    }
    timestamp = timestamp.removeprefix("[")
    timestamp = timestamp.removesuffix("]")
    day, month, year_and_time = timestamp.split("/")
    year, hour, minute, second_and_offset = year_and_time.split(":")
    second, offset = second_and_offset.split(" ")

    offset_hours, offset_minutes = offset[:-2], offset[-2:]
    offset = timezone(
        timedelta(
            hours=int(offset_hours),
            minutes=int(offset_minutes),
        )
    )

    kwargs = dict(
        year=int(year),
        month=month_dict[month],
        day=int(day),
        hour=int(hour),
        minute=int(minute),
        second=int(second),
        tzinfo=offset,
    )
    my_datetime = datetime(**kwargs)
    return datetime.fromtimestamp(my_datetime.timestamp(), tz=timezone.utc)


def create_table(con):
    cols = ", ".join([f"{key} {val}" for key, val in get_cols().items()])
    con.execute(f"CREATE TABLE access({cols})")


def format_result(result, col_names):
    max_widths = []
    for col in zip(col_names, *result):
        max_widths.append(max([len(str(val)) for val in col]))

    rows_out = [
        " | ".join(
            [
                f"{col_name:<{max_width}}"
                for col_name, max_width in zip(col_names, max_widths)
            ]
        ),
        "-+-".join("-" * max_width for max_width in max_widths),
    ]
    for row in result:
        rows_out.append(
            " | ".join(
                [f"{val:>{max_width}}" for val, max_width in zip(row, max_widths)]
            )
        )
    return rows_out


def insert_logs_into_table(con, logs):
    cols = get_cols().keys()
    rows = [tuple(log[col_name] for col_name in cols) for log in logs]
    with con:
        con.executemany("INSERT INTO access VALUES (?,?,?,?,?,?,?,?,?)", rows)


def list_data(con):
    cols = {
        "date_time": "Access time",
        "remote_address": "IP Address",
        "referer": "Referer",
        "method": "Method",
        "url_path": "Route",
        "status": "Status",
        # "request_time_in_seconds": "Request time",
    }
    with con:
        res = con.execute(
            f"""
            SELECT
                {', '.join(cols.keys())}
            FROM
                access
            ORDER BY
                date_time DESC
        """
        )
    result = list(res.fetchall())
    formatted_results = format_result(
        result,
        col_names=cols.values(),
    )
    print("\n".join(formatted_results))


def inspect_data_by_week(con):
    cols = {
        "week": "WeekNumber",
        "count(*)": "Count",
    }
    with con:
        res = con.execute(
            f"""
            SELECT
                {', '.join(cols.keys())}
            FROM
                access
            GROUP BY
                week
            ORDER BY
                week desc
        """
        )
    result = list(res.fetchall())
    formatted_results = format_result(result, col_names=cols.values())
    print("\n".join(formatted_results))


def inspect_data_by_date(con):
    cols = {
        "DATE(date_time)": "Date",
        "count(*)": "Count",
    }
    with con:
        res = con.execute(
            f"""
            SELECT
                {', '.join(cols.keys())}
            FROM
                access
            GROUP BY
                DATE(date_time)
            ORDER BY
                date_time DESC
        """
        )
    result = list(res.fetchall())
    formatted_results = format_result(result, col_names=cols.values())
    print("\n".join(formatted_results))


def inspect_data_by_time(con, date="now"):
    cols = {
        "strftime('%H:%M', date_time)": "Time",
        # "date_time": "Access time",
        # "remote_address": "IP Address",
        "referer": "Referer",
        "method": "Method",
        "url_path": "Route",
        "status": "Status",
        "user_agent": "User Agent",
    }
    with con:
        res = con.execute(
            f"""
            SELECT
                {', '.join(cols.keys())}
            FROM
                access
            WHERE
                DATE(date_time) = DATE('{date}')
            ORDER BY
                date_time DESC
        """
        )
    result = list(res.fetchall())
    formatted_results = format_result(result, col_names=cols.values())
    print("\n".join(formatted_results))


def inspect_data_by_user_agent(con):
    cols = {
        "user_agent": "User Agent",
        "count(*)": "Count",
    }
    with con:
        res = con.execute(
            f"""
            SELECT
                {', '.join(cols.keys())}
            FROM
                access
            GROUP BY
                user_agent
            ORDER BY
                count(*) DESC
        """
        )
    result = list(res.fetchall())
    formatted_results = format_result(result, col_names=cols.values())
    print("\n".join(formatted_results))


def load_logs(con, log_file):
    with open(log_file, "r") as f:
        logs = f.readlines()

    logs_as_dicts = []
    for log in logs:
        if not log:
            continue

        log = log.replace('\\"', "'")
        log = log.replace("\\", "")
        try:
            log = json.loads(log)
        except json.decoder.JSONDecodeError:
            print(f"JSONDecodeError loading {log}")
            continue

        if (
            log["user_agent"]
            == "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)"
            or "Nessus" in log["user_agent"]
            or "nessus" in log["user_agent"]
        ):
            continue

        log["referer"] = log["referer"].removeprefix(
            "http://partnertools.dev51-test-apps-gpstam.dev51.cbf.dev.paypalinc.com:8000"
        )
        date_time = format_timestamp(log["date_time"])
        log["date_time"] = date_time
        isocalendar = date_time.isocalendar()
        log["week"] = f"Y{isocalendar.year}-W{isocalendar.week:02}"
        logs_as_dicts.append(log)

    create_table(con)
    insert_logs_into_table(con, logs_as_dicts)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        log_file = "access_log.log"

    # db_file = "access_log.db"
    db_file = ":memory:"
    con = sqlite3.connect(db_file)

    load_logs(con, log_file)
    # list_data(con)
    # inspect_data_by_user_agent(con)
    # inspect_data_by_date(con)
    inspect_data_by_week(con)
    # inspect_data_by_time(con)
