import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from config import load_config
from bot import Bot
import os

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    # load all variables from devo.conf to environmental variables
    load_config()

    telegram_token = os.environ['TELEGRAM_BOT_TOKEN']

    db_user = os.environ['POSTGRES_USER']
    db_password = os.environ['POSTGRES_PASSWORD']
    db_name = os.environ['POSTGRES_DB']

    # SQLAlchemy setup
    engine = create_engine(f'postgresql://{db_user}:{db_password}@localhost/{db_name}')
    Base = declarative_base()
    Base.metadata.create_all(engine)
    session = Session(engine)

    telegram_token = os.environ['TELEGRAM_BOT_TOKEN']

    bot = Bot(session, telegram_token)
    bot.run()
