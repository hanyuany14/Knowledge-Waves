import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(project_root)

import schedule
import time
from datetime import datetime

from src.backend.main import Main


def job():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"Now is {current_time}...")
    main = Main()
    main.prepare_news()


# 排程每天早上 7:00 執行
schedule.every().day.at("7:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
