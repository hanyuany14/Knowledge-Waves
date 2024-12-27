from datetime import datetime
from google.api_core.exceptions import Conflict

import src.backend.utils as utils
import src.backend.configs as configs


class GCSOperation:
    def __init__(self):
        self.yesterday, self.today = utils.get_time_range()
        self.__datetime_str = self.today.strftime("%Y-%m-%d")
        self.__create_bucket()

    def upload(
        self,
        crawl_results: dict[str, list[dict[str, str | list[str] | datetime]]],
    ) -> bool:
        """Uploads content to the bucket as a .txt file with nested folders.

        Args:
            source (str): The source of the article (second-level folder: 'github', 'medium', 'csdn').
            article_content (str): The content to save and upload.
            destination_blob_name (str): The name of the file to save in the bucket (without extension).

        Returns:
            bool: True if upload succeeds, False otherwise.
        """
        print(f"\nNow uploading content to GCS...")

        for source, articles in crawl_results.items():
            for article in articles:
                try:
                    file_path = f"{self.__datetime_str}/{source}/{article['title']}.txt"
                    bucket = utils.GCS_CLIENT.bucket(configs.GCS_BUCKET_ID)

                    blob = bucket.blob(file_path)
                    blob.upload_from_string(article["content"], content_type="text/plain")
                    print(f"Content uploaded to {file_path} in bucket {configs.GCS_BUCKET_ID}.")
                except Exception as e:
                    print(f"Failed to upload content to GCS: {e}")

        return True

    def fetch_articles_by_title(
        self, source_and_titles_and_url: dict[str, list[tuple[str, str, int, str]]]
    ) -> dict[str, list[tuple[str, str]]]:
        """Fetches articles from the bucket based on source and titles.

        Args:
            source_and_titles (dict[str, list[tuple[str, str]]]): A dictionary where the key is the source
                                                     (e.g., 'github', 'medium', 'csdn')
                                                     and the value is a list of article titles.

        Returns:
            dict[str, list[tuple[str, str]]]: A dictionary where the key is the source and the value is a list of
                                              tuples containing the title and its content.

                                              e.g., {
                                                    "github": [("title1", "content1"), ("title2", "content2")],
                                                    "medium": [("title3", "content3"), ("title4", "content4")],
                                                    "csdn": [("title5", "content5"), ("title6", "content6")]
                                                }
        """
        article_titles_and_contents = {}

        try:
            for source, titles_and_urls in source_and_titles_and_url.items():
                article_titles_and_contents[source] = []
                print(f"titles_and_urls: {titles_and_urls}")
                for title, url, _, _ in titles_and_urls:
                    file_path = f"{self.__datetime_str}/{source}/{title}.txt"

                    bucket = utils.GCS_CLIENT.bucket(configs.GCS_BUCKET_ID)
                    blob = bucket.blob(file_path)

                    if blob.exists():
                        content = blob.download_as_text()
                        article_titles_and_contents[source].append((title, content))
                        print(f"Successfully fetched content for {file_path}.")
                    else:
                        print(f"File {file_path} does not exist in the bucket.")
        except Exception as e:
            raise Exception(f"Failed to fetch articles from GCS: {e}")

        return article_titles_and_contents

    def __create_bucket(self):
        try:
            bucket = utils.GCS_CLIENT.lookup_bucket(bucket_name=configs.GCS_BUCKET_ID)
            if bucket:
                print(f"\n\n    Bucket {configs.GCS_BUCKET_ID} already exists.")
            else:
                utils.GCS_CLIENT.create_bucket(configs.GCS_BUCKET_ID)
                print(f"Bucket {configs.GCS_BUCKET_ID} created successfully.")
        except Conflict as e:
            print(f"Bucket {configs.GCS_BUCKET_ID} already exists (Conflict error): {e}")
        except Exception as e:
            print(f"Failed to create bucket: {e}")
