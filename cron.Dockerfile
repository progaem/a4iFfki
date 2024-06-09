FROM python:3.11
RUN apt-get update && apt-get install -y cron
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
RUN echo "0 0 * * * /usr/local/bin/python /app/src/common/log_cleanup.py >> /var/log/cron.log 2>&1" > /etc/cron.d/log-cleanup-cron
RUN crontab /etc/cron.d/log-cleanup-cron
RUN touch /var/log/cron.log
CMD ["sh", "-c", "cron && tail -f /var/log/cron.log"]