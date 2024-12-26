import datetime

from summary import Summarization
from vectorstore import VectorStore
from bigquery_operation import BigQueryOperation
from gcs_operation import GCSOperation
from crawl import Crawl


class Main:
    def __init__(self): ...

    def do_summarize(
        self, query: str, sources: list[str] | None = None
    ) -> tuple[list[str], str, dict[str, list[tuple[str, str]]]]:
        """
        使用者層：接收使用者 query 今日有興趣主題
        - 使用者輸入：今日有興趣主題的自然語言
        - 相似性搜尋：挑出使用者輸入相似的 tags
        - 取得 tags 的文章標題：從 BigQuery 取得 tags 包含的所有文章標題
        - 標題取得文章：從 GCS 取得該文章的內容
        - LLM 總結：使用 LLM 將文章內容總結
        - 回傳結果：將總結回傳給使用者

        Returns:
            interested_tags (list[str]): 相似的 tags e.g. ["tag1", "tag2"]
            summaarized_content (str): 總結的文章內容 e.g. "summary"
            article_titles (list[tuple[str, str]]): tags 包含的所有文章標題 e.g. [("title", "url")]
        """

        interested_tags, summaarized_content, article_titles = Summarization().do_summary(query, sources)

        return interested_tags, summaarized_content, article_titles

    def prepare_news(self):
        """
        資料層：爬蟲、embedding、上傳資料
        每天早上固定執行
        - 爬蟲：爬取三個網站的文章內容
            - 包含：文章標題、文章內容、tags、文章網址、文章時間
        - 上傳到 BigQuery：將爬取的資料上傳到 BigQuery
            - 包含：文章標題、tags、文章網址、文章時間、文章來源
        - 上傳到 GCS：將爬取的資料上傳到 GCS
            - 包含：文章內容、文章標題
        - Embedding 上傳到 vectorestore：將 tags 進行 embedding 並存在 google vectorestore
            - 包含：tags、embedding
        """

        crawl_results, today_tags = Crawl().crawl()
        BigQueryOperation().upload(crawl_results=crawl_results)
        GCSOperation().upload(crawl_results=crawl_results)
        VectorStore().embedding_and_upload(today_tags=today_tags)

        return True
