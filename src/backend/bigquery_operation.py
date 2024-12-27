from datetime import datetime, timedelta
from google.cloud import bigquery
import time
import re

from google.cloud import translate_v3 as translate

import src.backend.utils as utils
import src.backend.configs as configs


class BigQueryOperation:
    def __init__(self):
        self.yesterday, self.today = utils.get_time_range()

        self.article_table_ref = f"{configs.PROJECT_ID}.{configs.DATASET_ID}.{configs.ARTICLE_INFO_TABLE_ID}"

        self.__create_dataset_if_not_exists()
        self.translate_client = translate.TranslationServiceClient(credentials=utils.CREDENTIAL_OBJ)
        # self.translate_client = translate.Client(credentials=utils.CREDENTIAL_OBJ)
        self.parent = f"projects/{configs.PROJECT_ID}/locations/{configs.TRANSLATION_LOCATION}"
        self.translation_cache = {}

    def __is_chinese(self, text: str) -> bool:
        """
        檢查字符串中是否包含中文字符。

        Args:
            text (str): 要檢查的字符串。

        Returns:
            bool: 如果包含中文字符，返回 True，否則返回 False。
        """
        # 使用正則表達式檢測中文字符範圍
        return bool(re.search(r"[\u4e00-\u9fff]", text))

    def __translate(self, tags_list: list[str]) -> list[str]:
        translated_tags_list = []
        tags_to_translate = [tag for tag in tags_list if self.__is_chinese(tag) and tag not in self.translation_cache]
        tags_original = [tag for tag in tags_list]

        if tags_to_translate:
            try:
                response = self.translate_client.translate_text(
                    request={
                        "parent": self.parent,
                        "contents": tags_to_translate,
                        "mime_type": "text/plain",
                        "source_language_code": "zh",
                        "target_language_code": "en",
                    }
                )
                for original, translation in zip(tags_to_translate, response.translations):
                    self.translation_cache[original] = translation.translated_text
                    print(f"翻譯標籤: '{original}' -> '{translation.translated_text}'")  # 添加打印語句
            except Exception as e:
                print(f"翻譯標籤時出錯: {e}")
                for tag in tags_to_translate:
                    self.translation_cache[tag] = tag  # 保留原始標籤

        for tag in tags_original:
            if self.__is_chinese(tag):
                translated_tag = self.translation_cache.get(tag, tag)
                translated_tags_list.append(translated_tag)
                print(f"最終標籤: '{tag}' -> '{translated_tag}'")  # 添加打印語句
            else:
                translated_tags_list.append(tag)
                print(f"標籤不需要翻譯: '{tag}'")  # 添加打印語句

        return translated_tags_list

    def upload(self, crawl_results: dict[str, list[dict[str, str | list[str] | datetime]]]) -> bool:
        """
        上傳文章到 BigQuery。

        Args:
            crawl_results (dict): 每個來源對應的一組文章數據。

        Returns:
            bool: 上傳成功返回 True，否則拋出異常。
        """
        self.__create_table()
        print(f"\nNow uploading articles to BigQuery...")
        try:
            for source, articles in crawl_results.items():
                if not articles:
                    print(f"No articles to upload for {source}.")
                    continue
                rows_to_insert = [
                    {
                        "title": article["title"],
                        "tags": self.__translate(article["tags"]),  # 調用翻譯方法
                        "url": article["url"],
                        "publish_date": (
                            article["publish_date"].strftime("%Y-%m-%dT%H:%M:%S")
                            if isinstance(article["publish_date"], datetime)
                            else article["publish_date"]
                        ),
                        "language": article["language"],
                        "likes": article["likes"],
                        "source": source,
                        "created_time": self.today.strftime("%Y-%m-%dT%H:%M:%S"),
                    }
                    for article in articles
                ]

                # 打印即將上傳的數據
                print(f"準備上傳 {len(articles)} 篇文章來自來源: {source}")
                for row in rows_to_insert:
                    print(f"上傳數據: {row}")

                errors = utils.BQ_CLIENT.insert_rows_json(self.article_table_ref, rows_to_insert)
                if errors:
                    print(f"上傳時發生錯誤: {errors}")
                    raise ValueError(f"Failed to upload articles: {errors}")

                print(f"Successfully uploaded {len(articles)} articles to {self.article_table_ref}.")

            return True
        except Exception as e:
            print(f"Failed to upload articles to BQ. {e}")
            raise Exception(f"Failed to upload articles to BQ. {e}")

    def fetch_articles_by_tags(self, interested_tags: list[str]) -> dict[str, list[tuple[str, str, int, str | None]]]:
        """
        Fetches articles from BigQuery based on tags and organizes the results by source.

        Args:
            interested_tags (list[str]): A list of tags to filter articles.

        Returns:
            dict[str, list[tuple[str, str, int, str]]]: A dictionary where the key is the source and the value
                                                        is a list of tuples containing the title, URL, likes, and language
                                                        of matching articles.
                                                        e.g. {
                                                            "github": [("title1", "url1", 15, "en")],
                                                            "medium": [("title3", "url3", 10, "en")],
                                                            "csdn": [("title4", "url4", 18, "ch")]
                                                        }
        """
        try:
            query = f"""
                SELECT source, title, url, likes, language
                FROM `{self.article_table_ref}`
                WHERE EXISTS (
                    SELECT 1 FROM UNNEST(tags) AS tag
                    WHERE tag IN UNNEST(@interested_tags)
                )
                AND publish_date BETWEEN TIMESTAMP('{self.yesterday}') AND TIMESTAMP('{self.today}')
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ArrayQueryParameter("interested_tags", "STRING", interested_tags),
                    bigquery.ScalarQueryParameter("yesterday", "TIMESTAMP", self.yesterday),
                    bigquery.ScalarQueryParameter("today", "TIMESTAMP", self.today),
                ]
            )

            query_job = utils.BQ_CLIENT.query(query, job_config=job_config)

            results = query_job.result()
            articles_by_source = {}
            for row in results:
                source = row["source"]
                title_url_tuple = (row["title"], row["url"], row["likes"], row["language"])
                if source not in articles_by_source:
                    articles_by_source[source] = []
                articles_by_source[source].append(title_url_tuple)

            return articles_by_source

        except Exception as e:
            print(f"Failed to fetch articles by tags: {e}")
            return {}

    def __create_table(self):
        """
        Checks if the table exists in BigQuery. If not, creates the table with the specified schema.
        """

        schema = [
            bigquery.SchemaField("title", "STRING", mode="REQUIRED", description="文章標題"),
            bigquery.SchemaField("source", "STRING", mode="REQUIRED", description="文章來源"),
            bigquery.SchemaField("publish_date", "TIMESTAMP", mode="REQUIRED", description="文章發佈時間"),
            bigquery.SchemaField("tags", "STRING", mode="REPEATED", description="文章種類（多個）"),
            bigquery.SchemaField("url", "STRING", mode="REQUIRED", description="文章網址"),
            bigquery.SchemaField("likes", "INTEGER", mode="NULLABLE", description="文章的點讚數"),
            bigquery.SchemaField("language", "STRING", mode="NULLABLE", description="文章語言"),
            bigquery.SchemaField("created_time", "TIMESTAMP", mode="REQUIRED", description="資料存入的時間"),
        ]

        try:
            table = bigquery.Table(self.article_table_ref, schema=schema)
            utils.BQ_CLIENT.create_table(table, exists_ok=True)
            print(f"Table {self.article_table_ref} created successfully.")
            time.sleep(10)
        except Exception as e:
            print(f"Failed to create table {self.article_table_ref}: {e}")

    def __create_dataset_if_not_exists(self):
        """
        Checks if the dataset exists in BigQuery. If not, creates the dataset.
        """
        dataset_ref = f"{configs.PROJECT_ID}.{configs.DATASET_ID}"

        try:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = configs.BIGQUERY_REGION
            utils.BQ_CLIENT.create_dataset(dataset, exists_ok=False)
            print(f"Dataset {dataset_ref} created successfully.")
        except Exception as e:
            print(f"Failed to create dataset {dataset_ref}: {e}")

    def __delete_existed_table(self):
        try:
            utils.BQ_CLIENT.delete_table(self.article_table_ref, not_found_ok=True)
            time.sleep(5)
            print(f"Table `{self.article_table_ref}` deleted successfully.")
        except Exception as e:
            print(f"Failed to delete table {self.article_table_ref}: {e}")
