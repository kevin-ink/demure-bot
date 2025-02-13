import logging
import datetime
import os
from dotenv import load_dotenv

# SETUP LOGGING
logger = logging.getLogger("bot")
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s')

# CONSOLE HANDLER
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# FILE HANDLER
file_handler = logging.FileHandler("runtime.log", mode='a')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# INITIALIZE TOKENS
load_dotenv()
itad_auth = os.getenv("ITAD_TOKEN")  # ITAD TOKEN
bot_token = os.getenv("BOT_TOKEN") # BOT TOKEN
db_token = os.getenv("DB_TOKEN") # DATABASE TOKEN

# TIME
time = datetime.time(hour=20)