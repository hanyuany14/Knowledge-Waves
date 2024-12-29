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

    def llm_summary(self, target_articles: dict[str, list[tuple[str, str]]]) -> str:
        """
        1. 現在總結是對每一個 repo 或是文章做總結，但太長了，現在要改成對一個 source 就做一個總節
        ex.
        github:
        今天關於 rag 資訊有 memory, prompt 層面。例如 abc/rag-memory 提出一個全新的 memory 演算法，加入了短期演算法改善了模型的記憶。

        csdn:
        xxx

        medium:
        xxx

        -> 建議解決方案：現在是一個 for 迴圈，可以再一個 for 迴圈再一次總結，兩個是不同的 prompt


        2. 內容中要如果提到文章內容，要變成超連結型態。
        ex.
        今天關於 rag 資訊有 memory, prompt 層面。例如<a href=""https://github.com"">abc/rag-memory</a>提出一個全新的 memory 演算法，

        -> 所以現在的參數要額外傳入每個文章的 url，並且一起送進去給第一層的 api
        -> 要在第二層 prompt 加入要用超連結的格式指引，可以給他上面的範例。

        兩層迴圈輸入與輸出：
        第一層輸入：
        url: https:////
        content: xxxxx

        url: https:////
        content: xxxxx

        第一層輸出 & 第二層輸入：
        url: https:////
        summay: xxxxx

        url: https:////
        summay: xxxxx

        第二層輸出：
        source_summay: 今天關於 rag 資訊有 memory, prompt 層面。例如<a href=""https://github.com"">abc/rag-memory</a>提出一個全新的 memory 演算法，

        最後就是 return:

        return {
            'github':source_summay,
            'csdn: source_summay,
            "medium": source_summay,
        }


        第一層的 llm 的 prompt 大概可以是「你是一個友善的學者，負責將文章總結成有意義且重點的段落。請使用繁體中文回覆。」
        第二層的 llm 的 prompt 可以是「你需要將每一個文章總結整合成一段敘述，然後標題（repo 標題或是文章標題）要用 <a href> 中間加入 url」

        """
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "你是一個友善的學者，負責將文章總結成有意義且重點的段落。請使用繁體中文回覆。"),
                ("human", "{input}"),
            ]
        )

        chain = prompt | self.llm
        summaries = []
        processed_titles = set()

        for source, articles in target_articles.items():
            for title, content in articles:
                if title not in processed_titles:
                    response = chain.invoke({"input": content})
                    summary = f'"{source}" {title}: {response.content}'
                    summaries.append(summary)
                    processed_titles.add(title)  # 添加到已处理集合中

        return "\n\n".join(summaries)
