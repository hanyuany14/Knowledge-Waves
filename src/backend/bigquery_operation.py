from datetime import datetime, timedelta
from google.cloud import bigquery

import src.backend.utils as utils
import src.backend.configs as configs


class BigQueryOperation:
    def __init__(self):
        self.today = datetime.now()
        self.yesterday = datetime.now().replace(day=datetime.now().day - 1)

        self.article_table_ref = f"{configs.PROJECT_ID}.{configs.DATASET_ID}.{configs.ARTICLE_INFO_TABLE_ID}"
        self.__create_table()

    def upload(self, crawl_results: dict[str, list[dict[str, str | list[str] | datetime]]]):
        """
        Uploads a list of articles to BigQuery.

        Args:
            articles (list[dict]): A list of dictionaries, each representing an article with keys like
                                'title', 'content', 'tags', 'url', and 'publish_time'.

        Returns:
            bool: True if upload succeeds, False otherwise.
        """
        try:
            for source, articles in crawl_results.items():
                rows_to_insert = [
                    {
                        "title": article["title"],
                        "content": article["content"],
                        "tags": article["tags"],
                        "url": article["url"],
                        "publish_time": article["publish_time"],
                        "source": source,
                    }
                    for article in articles
                ]

                errors = utils.BQ_CLIENT.insert_rows_json(self.article_table_ref, rows_to_insert)
                if errors:
                    raise ValueError(f"Failed to upload articles: {errors}")

                print(f"Successfully uploaded {len(articles)} articles to {self.article_table_ref}.")

            return True
        except Exception as e:
            raise Exception(f"Failed to upload articles to BQ. {e}")

    def fetch_articles_by_tags(self, interested_tags: list[str]) -> dict[str, list[tuple[str, str]]]:
        """
        Fetches articles from BigQuery based on tags and organizes the results by source.

        Args:
            interested_tags (list[str]): A list of tags to filter articles.

        Returns:
            dict[str, list[tuple[str, str]]]: A dictionary where the key is the source and the value
                                            is a list of tuples containing the title and URL of matching articles.
                                            e.g. {
                                                "github": [("title1", "url1"), ("title2", "url2")],
                                                "medium": [("title3", "url3")],
                                                "csdn": [("title4", "url4"), ("title5", "url5")]
                                            }
        """
        try:
            query = f"""
                SELECT source, title, url
                FROM `{self.article_table_ref}`
                WHERE EXISTS (
                    SELECT 1 FROM UNNEST(tags) AS tag
                    WHERE tag IN UNNEST(@interested_tags)
                )
                AND publish_date BETWEEN @yesterday AND @today
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
                title_url_tuple = (row["title"], row["url"])
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
        ]

        try:
            tables = list(utils.BQ_CLIENT.list_tables(configs.DATASET_ID))
            if any(table.table_id == configs.ARTICLE_INFO_TABLE_ID for table in tables):
                print(f"Table {self.article_table_ref} already exists.")
                return

            table = bigquery.Table(self.article_table_ref, schema=schema)
            utils.BQ_CLIENT.create_table(table)
            print(f"Table {self.article_table_ref} created successfully.")
        except Exception as e:
            print(f"Failed to create table {self.article_table_ref}: {e}")
