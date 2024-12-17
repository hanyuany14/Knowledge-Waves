from langchain_google_community.bigquery import BigQueryLoader
from google.oauth2 import service_account
from google.cloud import bigquery
from google.cloud import storage

import src.backend.configs as configs

CREDENTIAL_OBJ = service_account.Credentials.from_service_account_file(filename=configs.CREDENTIAL_PATH)
BQ_CLIENT = bigquery.Client(project=configs.PROJECT_ID, credentials=CREDENTIAL_OBJ)
GCS_CLIENT = storage.Client(project=configs.PROJECT_ID, credentials=CREDENTIAL_OBJ)
