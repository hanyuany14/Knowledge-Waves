from datetime import datetime, timedelta

from langchain_google_community.bigquery import BigQueryLoader
from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud import storage

import configs as configs

CREDENTIAL_OBJ = service_account.Credentials.from_service_account_file(filename=configs.CREDENTIAL_PATH)
BQ_CLIENT = bigquery.Client(project=configs.PROJECT_ID, credentials=CREDENTIAL_OBJ)
GCS_CLIENT = storage.Client(project=configs.PROJECT_ID, credentials=CREDENTIAL_OBJ)


def get_time_range():
    """
    返回基於指定時間段（每天早上 8:00）計算的資料範圍。

    Returns:
        tuple: (start_time, end_time) 分別表示資料的開始和結束時間。
    """
    now = datetime.now()
    base_time = now.replace(hour=8, minute=0, second=0, microsecond=0)

    if now < base_time:  # 如果當前時間早於今天 8:00，則查詢前一天的資料範圍
        end_time = base_time
        start_time = base_time - timedelta(days=1)
    else:  # 當前時間晚於或等於今天 8:00
        start_time = base_time
        end_time = base_time + timedelta(days=1)

    return start_time, end_time
