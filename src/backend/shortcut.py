from datetime import datetime, timedelta
from google.cloud import bigquery
import src.backend.utils as utils
import src.backend.configs as configs
from src.backend.gcs_operation import GCSOperation
from src.backend.summary import Summarization


class ShortcutsUtil:
    """
    提問 1：今天最受歡迎的文章前五篇文章分別為何？
    提問 2：今天內關於「AI」的文章中，點讚數最高的三篇文章標題是什麼？
    提問 3：對所有來源今日的文章關於 LLM Agent 的內容進行介紹
    提問 4：目前資料中來自「medium」的五篇最熱門文章是什麼？
    """

    def __init__(self) -> None:
        self.yesterday, self.today = utils.get_time_range()
        self.article_table_ref = f"{configs.PROJECT_ID}.{configs.DATASET_ID}.{configs.ARTICLE_INFO_TABLE_ID}"
        self.bq_client = utils.BQ_CLIENT

    def __shortcut_summary(self, source_and_titles: list[dict[str, str]]) -> str:
        article_titles_and_contents = GCSOperation().fetch_articles_by_title(source_and_titles=source_and_titles)
        summaarized_content = Summarization().llm_summary(target_articles=article_titles_and_contents)
        return summaarized_content

    def question_1(self) -> tuple[list[dict[str, str]], str]:
        """
        提問 1：今天最受歡迎的文章前五篇文章分別為何？
        """
        query = f"""
        SELECT title, source, likes, url
        FROM {self.article_table_ref}
        WHERE publish_date >= TIMESTAMP('{self.yesterday}')
            AND publish_date < TIMESTAMP('{self.today}')
        ORDER BY likes DESC
        LIMIT 5
        """
        query_job = self.bq_client.query(query)
        results = query_job.result()
        parse_result = [
            {"title": row.title, "source": row.source, "likes": str(row.likes), "url": row.url} for row in results
        ]
        summaarized_content = self.__shortcut_summary(parse_result)

        return parse_result, summaarized_content

    def question_2(self) -> tuple[list[dict[str, str]], str]:
        """
        提問 2：今天內關於「AI」的文章中，點讚數最高的三篇文章標題是什麼？
        """
        query = f"""
        SELECT DISTINCT title, source, likes, url
        FROM `{self.article_table_ref}`,
            UNNEST(tags) AS tag
        WHERE publish_date >= TIMESTAMP('{self.yesterday}')
            AND publish_date < TIMESTAMP('{self.today}')
            AND LOWER(tag) LIKE '%ai%'
        ORDER BY likes DESC
        LIMIT 3
        """
        query_job = self.bq_client.query(query)
        results = query_job.result()
        parse_result = [
            {"title": row.title, "source": row.source, "likes": str(row.likes), "url": row.url} for row in results
        ]
        summaarized_content = self.__shortcut_summary(parse_result)

        return parse_result, summaarized_content

    def question_3(self) -> tuple[list[dict[str, str]], str]:
        """
        提問 3：對所有來源今日的文章關於 LLM RAG 的內容進行介紹
        """
        query = f"""
        SELECT DISTINCT title, source, url
        FROM `{self.article_table_ref}`,
            UNNEST(tags) AS tag
        WHERE publish_date >= TIMESTAMP('{self.yesterday}')
            AND publish_date < TIMESTAMP('{self.today}')
            AND LOWER(tag) LIKE '%rag%'
        """
        query_job = self.bq_client.query(query)
        results = query_job.result()
        parse_result = [{"title": row.title, "source": row.source, "url": row.url} for row in results]
        summaarized_content = self.__shortcut_summary(parse_result)

        return parse_result, summaarized_content

    def question_4(self) -> tuple[list[dict[str, str]], str]:
        """
        提問 4：目前資料中來自「medium」的五篇最熱門文章是什麼？
        """
        query = f"""
        SELECT title, source, url
        FROM `{self.article_table_ref}`
        WHERE source = 'medium'
        ORDER BY likes DESC
        LIMIT 5
        """
        query_job = self.bq_client.query(query)
        results = query_job.result()
        parse_result = [{"title": row.title, "source": row.source, "url": row.url} for row in results]
        summaarized_content = self.__shortcut_summary(parse_result)

        return parse_result, summaarized_content

    def get_today_tags(self) -> list[str]:
        """
        提問：今天內的 tags DISTINCT 是什麼？
        """
        query = f"""
        SELECT DISTINCT tag
        FROM {self.article_table_ref},
            UNNEST(tags) AS tag
        WHERE publish_date >= TIMESTAMP('{self.yesterday}')
            AND publish_date < TIMESTAMP('{self.today}')
        """
        query_job = self.bq_client.query(query)
        results = query_job.result()
        tags = [row.tag for row in results]
        return tags
