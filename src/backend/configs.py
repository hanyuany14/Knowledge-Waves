from dotenv import load_dotenv
import os

load_dotenv(".env.local")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CREDENTIAL_PATH = "final-project-vectorestore_credentials.json"

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
# BigQuery
PROJECT_ID = "final-project-1-444506"
DATASET_ID = "final_project_poc"
ARTICLE_INFO_TABLE_ID = "article_collection"
BIGQUERY_REGION = "US"

# GCS
GCS_BUCKET_ID = "article-collection-storage"

# Vectorstore
VECTORSTORE_REGION = "US"
VECTORSTORE_TABLE_ID = "doc_and_vectors"

# Medium
MEDIUM_TAG_BASE_URL = "https://medium.com/feed/tag/"
