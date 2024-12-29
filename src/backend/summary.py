from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os

from src.backend.vectorstore import VectorStore
from src.backend.bigquery_operation import BigQueryOperation
from src.backend.gcs_operation import GCSOperation
from src.backend.configs import GOOGLE_API_KEY


class Summarization:
    def __init__(self): ...

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-8b",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=GOOGLE_API_KEY,  # type: ignore
    )

    def do_text_search_summary(
        self, query: str, sources: list[str] | None = None
    ) -> tuple[list[str], str, dict[str, list[tuple[str, str, int, str | None]]]]:
        """The function to summarize the articles based on the user query.

        Args:
            query (str): The query to search for. e.g. "Give me some information about NLP."
            sources (list[str], optional): The sources selected by user to search. Defaults to None.
                                            e.g. ["github", "medium"]
        Returns:
            tuple[list[str], str, dict[str, list[tuple[str, str]]]]:
                - tags(list[str]): A list of similar tags.
                - summary(str): The summarized content of the articles.
                - articles(dict[str, list[tuple[str, str]]]): A dictionary where the key is the source and the value
                            is a list of tuples containing the title and URL of matching articles.
        """
        tags = VectorStore().search_similar_tags(query=query, sources=sources)
        print(f"tags: {tags}")
        articles = BigQueryOperation().fetch_articles_by_tags(interested_tags=tags)
        print("articles success")
        article_titles_and_contents = GCSOperation().fetch_articles_by_title_and_url(source_and_titles_and_url=articles)
        print("content success")
        summary = self.llm_summary(article_titles_and_contents)
        print("summary success")
        interested_tags = [tag[0] for tag in tags]

        print(f"\n\ninterested_tags: \n\n{interested_tags}")
        print(f"\n\nsummary: \n\n{summary}")
        print(f"\n\narticles: \n\n{articles}")

        return interested_tags, summary, articles

    def do_select_tag_summary(
        self, selected_tags: list[str], sources: list[str] | None = None
    ) -> tuple[list[str], str, dict[str, list[tuple[str, str, int, str | None]]]]:
        """The function to summarize the articles based on the user query.

        Args:
            query (str): The query to search for. e.g. "Give me some information about NLP."
            sources (list[str], optional): The sources selected by user to search. Defaults to None.
                                            e.g. ["github", "medium"]
        Returns:
            tuple[list[str], str, dict[str, list[tuple[str, str]]]]:
                - tags(list[str]): A list of similar tags.
                - summary(str): The summarized content of the articles.
                - articles(dict[str, list[tuple[str, str]]]): A dictionary where the key is the source and the value
                            is a list of tuples containing the title and URL of matching articles.
        """
        articles = BigQueryOperation().fetch_articles_by_tags(interested_tags=selected_tags, sources=sources)
        print("articles success")
        article_titles_and_contents = GCSOperation().fetch_articles_by_title_and_url(source_and_titles_and_url=articles)
        print("content success")
        summary = self.llm_summary(article_titles_and_contents)
        print("summary success")

        print(f"\n\selected_tags: \n\n{selected_tags}")
        print(f"\n\nsummary: \n\n{summary}")
        print(f"\n\narticles: \n\n{articles}")

        return selected_tags, summary, articles

    # def llm_summary(self, target_articles: dict[str, list[tuple[str, str]]]) -> str:
    #     prompt_1 = ChatPromptTemplate.from_messages(
    #         [
    #             ("system", "你是一個友善的學者，負責將文章總結成有意義且重點的段落。請使用繁體中文回覆。"),
    #             ("human", "{input}"),
    #         ]
    #     )

    #     prompt_2 = ChatPromptTemplate.from_messages(
    #         [
    #             (
    #                 "system",
    #                 "你需要將每一個文章總結整合成一段敘述，然後標題（repo 標題或是文章標題）要用 <a href> 中間加入 url",
    #             ),
    #             ("human", "{input}"),
    #         ]
    #     )
    #     chain_1 = prompt_1 | self.llm
    #     chain_2 = prompt_2 | self.llm

    #     summaries = []
    #     processed_titles = set()

    #     for source, articles in target_articles.items():
    #         for title, content in articles:
    #             if title not in processed_titles:
    #                 response = chain_1.invoke({"input": content})
    #                 summary = f'"{source}" {title}: {response.content}'
    #                 summaries.append(summary)
    #                 processed_titles.add(title)

    #     return "\n\n".join(summaries)
    def llm_summary(self, target_articles: dict[str, list[tuple[str, str]]]) -> str:
        """
        將目標文章進行總結，按來源分組，每個來源一個總結，並將文章標題轉為超連結。
        """
        # 第一層提示：對單篇文章進行總結，並將標題轉為超連結，使用列點格式
        prompt_article = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一個友善且簡明的學者，負責將文章總結成有意義且重點的段落。請使用繁體中文並以列點的方式呈現。",
                ),
                ("human", "URL: {url}\n內容: {content}"),
            ]
        )

        # 第二層提示：將同一來源下的所有文章總結整合成一段敘述，並使用超連結格式，使用列點格式
        prompt_source = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    '你需要將每一篇文章的總結整合成一段敘述，並確保文章標題以超連結的格式呈現，使用列點的方式。請使用繁體中文，並以簡單易懂的白話文來描述文章的核心技術。例如：\n- <a href="https://github.com">abc/rag-memory</a> 提出了全新的 memory 演算法，能夠提升系統效能。',
                ),
                ("human", "來源: {source}\n文章總結:\n{summaries}"),
            ]
        )

        chain_article = prompt_article | self.llm
        chain_source = prompt_source | self.llm

        source_summaries = {}
        gcs_operation = GCSOperation()

        for source, articles in target_articles.items():
            article_summaries = []
            for title, content in articles:
                # 重建 URL 基於來源和標題
                url = self.reconstruct_url(source, title)
                if not url:
                    print(f"無法重建 URL 針對來源: {source}, 標題: {title}")
                    continue

                response = chain_article.invoke({"url": url, "content": content})
                # 將標題轉為超連結格式
                linked_title = f'<a href="{url}">{title}</a>'
                # 將標題與摘要結合，並使用列點
                summary = f"- {linked_title}: {response.content}"
                article_summaries.append(summary)
            if not article_summaries:
                continue
            # 將所有文章的總結傳遞給第二層提示
            combined_summaries = "\n".join(article_summaries)
            response_source = chain_source.invoke({"source": source, "summaries": combined_summaries})
            source_summaries[source] = response_source.content

        # 將所有來源的總結組合成一個完整的字符串，使用列點分隔
        final_summary = "\n\n".join([f"{source}:\n{summary}" for source, summary in source_summaries.items()])

        return final_summary

    def reconstruct_url(self, source: str, title: str) -> str | None:
        """
        根據來源和標題重建 URL。
        假設不同來源有不同的 URL 結構。

        Args:
            source (str): 文章來源，例如 'github', 'medium', 'csdn'
            title (str): 文章標題

        Returns:
            str | None: 重建的 URL，如果無法重建則返回 None
        """
        try:
            if source.lower() == "github":
                # 假設 GitHub 標題格式為 'user/repo'
                return f"https://github.com/{title}"
            elif source.lower() == "medium":
                # 假設 Medium 標題是完整的 URL
                return title  # 如果標題已經是 URL
            elif source.lower() == "csdn":
                # 根據實際的 CSDN URL 結構進行調整
                # 假設標題格式為 'username/article-id'
                return f"https://blog.csdn.net/{title}/article/details/{self.extract_article_id(title)}"
            else:
                # 其他來源的處理邏輯
                return None
        except Exception as e:
            print(f"重建 URL 失敗: {e}")
            return None

    def extract_article_id(self, title: str) -> str:
        """
        從標題中提取文章 ID。
        假設標題格式為 'username/article-id'

        Args:
            title (str): 文章標題，例如 'username/article-id'

        Returns:
            str: 提取出的文章 ID
        """
        try:
            parts = title.split("/")
            if len(parts) == 2:
                return parts[1]
            else:
                raise ValueError("標題格式不正確")
        except Exception as e:
            print(f"提取文章 ID 失敗: {e}")
            return "unknown"
