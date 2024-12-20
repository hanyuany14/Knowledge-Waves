from vectorstore import VectorStore
from bigquery_operation import BigQueryOperation
from gcs_operation import GCSOperation
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os

os.environ["GOOGLE_API_KEY"] = "AIzaSyBN7sjpwTrMZjdKzVtE5E1jzzZu7__nLT0"


class Summarization:
    def __init__(self): ...

    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash-8b",
        temperature=0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )

    def do_summary(
        self, query: str, sources: list[str] | None = None
    ) -> tuple[list[str], str, dict[str, list[tuple[str, str]]]]:
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
        print('articles success')
        article_titles_and_contents = GCSOperation().fetch_articles_by_title(source_and_titles_and_url=articles)
        print('content success')
        summary = self.llm_summary(article_titles_and_contents)
        print('summary success')
        articles = {}
        return tags, summary, articles

    def llm_summary(self, target_articles: dict[str, list[tuple[str, str]]]) -> str:
        # TODO: By 佑
        prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "你是一個友善的學者，負責將文章總結成有意義且重點的段落。請使用繁體中文回覆。"
        ),
        ("human", "{input}")
        ])

        chain = prompt | self.llm
        summaries = []
        processed_titles = set()  # 用来记录已处理过的标题

        for source, articles in target_articles.items():
            for title, content in articles:
                # 如果这个标题还没处理过，才生成摘要
                if title not in processed_titles:
                    response = chain.invoke({"input": content})
                    summary = f'"{source}" {title}: {response.content}'
                    summaries.append(summary)
                    processed_titles.add(title)  # 添加到已处理集合中

        return "\n\n".join(summaries)

