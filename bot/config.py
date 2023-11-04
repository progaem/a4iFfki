import os
import configparser

def load_config():
    config = configparser.ConfigParser()
    config.read('../devo.conf')

    database_section = config['database']
    s3_section = config['s3']
    telegram_section = config['telegram']

    # Set telegram environmental variables
    os.environ['TELEGRAM_BOT_TOKEN'] = telegram_section['TELEGRAM_BOT_TOKEN']

    # Set database environmental variables
    os.environ['DB_HOST'] = database_section['DB_HOST']
    os.environ['DB_USER'] = database_section['DB_USER']
    os.environ['DB_PASSWORD'] = database_section['DB_PASSWORD']
    os.environ['DB_NAME'] = database_section['DB_NAME']

    # Set S3 environmental variables
    os.environ['S3_ENDPOINT'] = s3_section['S3_ENDPOINT']
    os.environ['S3_ACCESS_KEY'] = s3_section['S3_ACCESS_KEY']
    os.environ['S3_SECRET_KEY'] = s3_section['S3_SECRET_KEY']
