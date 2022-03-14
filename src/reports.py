import csv
import paramiko

from flask import Blueprint, current_app, render_template, url_for

bp = Blueprint("reports", __name__, url_prefix="/reports")


def get_sftp_client(hostname=None):
    if hostname is None:
        hostname = current_app.config["SFTP_HOSTNAME"]

    username = current_app.config["SFTP_USERNAME"]
    password = current_app.config["SFTP_PASSWORD"]

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname, username=username, password=password, port=22)

    return client.open_sftp()


def get_sftp_reports_list():
    """Get the list of reports from the SFTP server.

    Docs: https://developer.paypal.com/docs/reports/sftp-reports/access-sftp-reports/
    """
    reports_dir = "/ppreports/outgoing"
    sftp_client = get_sftp_client()

    reports_lst = sorted(sftp_client.listdir(reports_dir))

    for report in sorted(
        sftp_client.listdir_attr(path=reports_dir), key=lambda x: x.st_size
    ):
        current_app.logger.debug(report)

    sftp_client.close()
    return reports_lst


def get_sftp_report(report_name):
    """Download the report with the given name from the SFTP server.

    Docs: https://developer.paypal.com/docs/reports/sftp-reports/access-sftp-reports/
    """
    reports_dir = "/ppreports/outgoing"
    sftp_client = get_sftp_client()

    with sftp_client.file(f"{reports_dir}/{report_name}", "r") as f:
        reader = csv.reader(f)
        rows = []
        for r in reader:
            if r[0] == "CH":
                # CH stands for Column Header
                cols = r[1:]
                cols_str = "".join(f"\n\t{col}" for col in cols)
                current_app.logger.debug(f"Column headers are:\n\t{cols_str}")
            elif r[0] == "SB":
                # SB stands for Section Body
                row = r[1:]
                rows.append(row)

    sftp_client.close()
    return cols, rows


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
    """Return the table with its empty columns removed."""
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
