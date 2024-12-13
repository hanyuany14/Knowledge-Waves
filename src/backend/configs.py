from dotenv import load_dotenv
import os

load_dotenv(".env.local")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CREDENTIAL_PATH = "final-project-vectorestore_credentials.json"

PROJECT_ID = "final-project-1-444506"
DATASET_ID = "final_project_poc"

# Vectorstore
VECTORSTORE_REGION = "US"
VECTORSTORE_TABLE = "doc_and_vectors"

# Medium
MEDIUM_TAG_BASE_URL = "https://medium.com/feed/tag/"