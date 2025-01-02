from datetime import datetime, timedelta

from langchain_google_community.bigquery import BigQueryLoader
from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud import storage

import src.backend.configs as configs

CREDENTIAL_OBJ = service_account.Credentials.from_service_account_file(filename=configs.CREDENTIAL_PATH)
BQ_CLIENT = bigquery.Client(project=configs.PROJECT_ID, credentials=CREDENTIAL_OBJ)
GCS_CLIENT = storage.Client(project=configs.PROJECT_ID, credentials=CREDENTIAL_OBJ)


def get_time_range(base_time=None):
    """
    返回基於每天早上 7:00 計算的資料範圍。
    情境一：如果當前時間在今天 7:00 之前，返回前兩天 7:00 到前一天 7:00；
    情境二：如果當前時間在今天 7:00 之後，返回前一天 7:00 到今天 7:00。

    Args:
        base_time (datetime, optional): 指定的基準時間，默認為當前時間。

    Returns:
        tuple: (start_time, end_time) 分別表示資料的開始和結束時間。
    """
    if base_time is None:
        base_time = datetime.now()

    today_7am = base_time.replace(hour=7, minute=0, second=0, microsecond=0)

    if base_time < today_7am:  # 情境一
        start_time = today_7am - timedelta(days=2)
        end_time = today_7am - timedelta(days=1)
    else:  # 情境二
        start_time = today_7am - timedelta(days=1)
        end_time = today_7am

    print(f"Currrnt Time: {base_time}")
    print(f"Currrnt Time 7 am: {today_7am}")
    print(f"start_time: {start_time}")
    print(f"end_time: {end_time}")

    return start_time, end_time
