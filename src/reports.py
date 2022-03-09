# import json
# import secrets

from .api import get_sftp_reports_list, get_sftp_report
from flask import Blueprint, render_template, url_for

bp = Blueprint("reports", __name__, url_prefix="/reports")


@bp.route("/")
def reports():
    reports_list = get_sftp_reports_list()

    cols = ["Report", "Link"]
    rows = [
        (report_name, url_for("reports.report", report_name=report_name))
        for report_name in reports_list
    ]

    return render_template("table.html", cols=cols, rows=rows)


def remove_empty_cols(cols, rows):
    cols_new = []
    rows_new = [[] for _ in rows]
    for (col_header, *col) in zip(cols, *rows):
        if any(col):
            cols_new.append(col_header)
            for row_idx, entry in enumerate(col):
                rows_new[row_idx].append(entry)
    return cols_new, rows_new


@bp.route("/<report_name>")
def report(report_name):
    cols, rows = get_sftp_report(report_name)
    cols, rows = remove_empty_cols(cols, rows)
    return render_template("table.html", cols=cols, rows=rows)
