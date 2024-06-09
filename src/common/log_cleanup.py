"""Helper script that would manage log files from previous days"""
import glob
import os
from zipfile import ZipFile, ZIP_DEFLATED

from datetime import datetime, timedelta

###                               CAUTION                               ###
#         this script is run separately from the rest of the app          #
#         DON'T add any internal dependencies to this file                #

LOG_DIR = "/app/logs"  # the directory for logs inside docker container
LOG_NAME = "app.log"  # name of the log
DELETE_CADENCE_DAYS = 30  # remove log files older than 30 days 

def zip_and_cleanup_logs():
    """Zips the previous day's logs and deletes logs older than a month"""
    today = datetime.utcnow().date()
    one_month_ago = today - timedelta(days=DELETE_CADENCE_DAYS)

    for log_file in glob.glob(os.path.join(LOG_DIR, LOG_NAME)):
        log_date_str = log_file.split('.')[-1]
        log_date = datetime.strptime(log_date_str, "%Y-%m-%d").date()

        # zip log files older one day
        if log_date < today:
            with ZipFile(f"{log_file}.zip", 'w', ZIP_DEFLATED) as zipped_file:
                zipped_file.write(log_file, os.path.basename(log_file))
            os.remove(log_file)

        # delete zip files older than one month
        if log_date < one_month_ago:
            os.remove(f"{log_file}.zip")

if __name__ == "__main__":
    zip_and_cleanup_logs()
