from datetime import datetime
from backend.crawl.main import Crawl

"""
2. 資料層：爬蟲、embedding、上傳資料
每天早上 7:00 執行
- 爬蟲：爬取三個網站的文章內容
    - 包含：文章標題、文章內容、tags、文章網址、文章時間
- 上傳到 BigQuery：將爬取的資料上傳到 BigQuery
    - 包含：文章標題、tags、文章網址、文章時間、文章來源
- 上傳到 GCS：將爬取的資料上傳到 GCS
    - 包含：文章內容
- Embedding 上傳到 vectorestore：將 tags 進行 embedding 並存在 google vectorestore
    - 包含：tags、embedding
"""


class Prepare:
    def __init__(self):
        self.crawl_results: dict[str, list[dict[str, str | list[str] | datetime]]] = {}

    def prepare(self):
        self.crawl_results, today_tags = self.__do_crawl()

        self.__do_embedding_and_upload(today_tags)
        self.__upload_to_bigquery()
        self.__upload_to_gcs()

        return True

    def __do_crawl(self) -> tuple[
        dict[str, list[dict[str, str | list[str] | datetime]]],
        dict[str, set[str]],
    ]:
        crawl_results, today_tags = Crawl().crawl()
        return crawl_results, today_tags

    def __do_embedding_and_upload(self, today_tags: dict[str, set[str]]) -> bool:
        """Embedding 上傳到 vectorestore：將 tags 進行 embedding 並存在 google vectorestore
        - 包含：tags、embedding
        """
        return True

    def __upload_to_bigquery(self):
        """上傳到 BigQuery：將爬取的資料上傳到 BigQuery
        - 包含：文章標題、tags、文章網址、文章時間、文章來源

        文章來源 就是 crawl_results 的 key
        """
        return True

    def __upload_to_gcs(self):
        """上傳到 GCS：將爬取的資料上傳到 GCS
        - 包含：文章內容

        文章來源 就是 crawl_results 的 key
        """
        return True
