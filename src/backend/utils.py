from langchain_google_community.bigquery import BigQueryLoader
from google.oauth2 import service_account

import src.backend.configs as configs

CREDENTIAL_OBJ = service_account.Credentials.from_service_account_file(filename=configs.CREDENTIAL_PATH)
