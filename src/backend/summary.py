import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

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
        """根據用戶查詢總結文章。

        Args:
            query (str): 查詢內容，例如 "Give me some information about NLP."
            sources (list[str], optional): 用戶選擇的來源，例如 ["github", "medium"]。默認為 None。

        Returns:
            tuple[list[str], str, dict[str, list[tuple[str, str, int, str | None]]]]:
                - tags(list[str]): 類似的標籤列表。
                - summary(str): 總結的內容。
                - articles(dict[str, list[tuple[str, str, int, str | None]]]): 來源到文章的映射。
        """
        tags = VectorStore().search_similar_tags(query=query, sources=sources)
        print(f"tags: {tags}")
        articles = BigQueryOperation().fetch_articles_by_tags(interested_tags=tags, sources=sources)
        print("articles success")
        article_titles_and_contents = GCSOperation().fetch_articles_by_title_and_url(source_and_titles_and_url=articles)
        print("content success")

        # 組合文章的標題、URL 和內容
        combined_articles = {}
        for source, articles_list in articles.items():
            combined_articles[source] = []
            contents = article_titles_and_contents.get(source, [])
            for article_tuple, content_tuple in zip(articles_list, contents):
                title, url, _, _ = article_tuple
                title_content, content = content_tuple
                combined_articles[source].append({"title": title, "url": url, "content": content})

        summary = self.llm_summary(combined_articles)
        print("summary success")
        interested_tags = [tag[0] for tag in tags]

        print(f"\n\ninterested_tags: \n\n{interested_tags}")
        print(f"\n\nsummary: \n\n{summary}")
        print(f"\n\narticles: \n\n{articles}")

        return interested_tags, summary, articles

    def do_select_tag_summary(
        self, selected_tags: list[str], sources: list[str] | None = None
    ) -> tuple[list[str], str, dict[str, list[tuple[str, str, int, str | None]]]]:
        """根據選擇的標籤總結文章。

        Args:
            selected_tags (list[str]): 選擇的標籤列表。
            sources (list[str], optional): 用戶選擇的來源，例如 ["github", "medium"]。默認為 None。

        Returns:
            tuple[list[str], str, dict[str, list[tuple[str, str, int, str | None]]]]:
                - tags(list[str]): 類似的標籤列表。
                - summary(str): 總結的內容。
                - articles(dict[str, list[tuple[str, str, int, str | None]]]): 來源到文章的映射。
        """
        articles = BigQueryOperation().fetch_articles_by_tags(interested_tags=selected_tags, sources=sources)
        print("articles success")
        article_titles_and_contents = GCSOperation().fetch_articles_by_title_and_url(source_and_titles_and_url=articles)
        print("content success")

        # 組合文章的標題、URL 和內容
        combined_articles = {}
        for source, articles_list in articles.items():
            combined_articles[source] = []
            contents = article_titles_and_contents.get(source, [])
            for article_tuple, content_tuple in zip(articles_list, contents):
                title, url, _, _ = article_tuple
                title_content, content = content_tuple
                combined_articles[source].append({"title": title, "url": url, "content": content})

        summary = self.llm_summary(combined_articles)
        print("summary success")

        print(f"\n\nselected_tags: \n\n{selected_tags}")
        print(f"\n\nsummary: \n\n{summary}")
        print(f"\n\narticles: \n\n{articles}")

        return selected_tags, summary, articles


    def llm_summary(self, target_articles: dict[str, list[dict[str, str]]]) -> str:
        # 第一層提示：對每篇文章進行摘要，使用白話且列點
        prompt_1 = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "你是一個友善的學者，負責將文章總結成有意義且重點的段落。請使用繁體中文回覆，並以列點的方式呈現。請將摘要控制在 2-3 句話內。",
                ),
                ("human", "{content}"),
            ]
        )

        # 第二層提示：將每篇文章的摘要整合成來源級別的總結，並將標題轉換為超連結，使用白話且列點
        prompt_2 = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    '你需要將每一篇文章的摘要整合成一段敘述，並使用列點的方式呈現。請將標題（repo 標題或是文章標題）轉換為 <a href="URL">title</a> 的格式插入。最後，請為這些文章撰寫一個總結。請使用繁體中文並保持白話易懂。',
                ),
                ("human", "{summaries}"),
            ]
        )

        chain_1 = prompt_1 | self.llm | StrOutputParser()
        chain_2 = prompt_2 | self.llm | StrOutputParser()

        source_summaries = {}

        for source, articles in target_articles.items():
            per_article_summaries = []
            print(f"articles: {articles}")
            for article in articles:
                print(f"article: {article}")
                title = article["title"]
                url = article["url"]
                content = article["content"]

                # 第一層摘要
                response = chain_1.invoke({"content": content})
                article_summary = response.strip()
                # 格式化每篇文章的摘要，保留標題和 URL
                formatted_summary = f'"{title}": {article_summary} <a href="{url}">{title}</a>'
                per_article_summaries.append(formatted_summary)

            # 將所有文章的摘要整合為一個字符串，供第二層使用
            summaries_input = "\n".join(per_article_summaries)

            # 第二層摘要，生成來源級別的總結
            response = chain_2.invoke({"summaries": summaries_input})
            source_summary = response.strip()
            source_summaries[source] = source_summary

        # 將所有來源的總結組合成最終的總結字符串
        final_summary = "\n\n".join([f"{source}:\n{summary}" for source, summary in source_summaries.items()])

        return final_summary
