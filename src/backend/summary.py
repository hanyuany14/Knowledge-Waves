from vectorstore import VectorStore
from bigquery_operation import BigQueryOperation
from gcs_operation import GCSOperation


class Summarization:
    def __init__(self): ...

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
        articles = BigQueryOperation().fetch_articles_by_tags(interested_tags=tags)
        article_titles_and_contents = GCSOperation().fetch_articles_by_title(source_and_titles_and_url=articles)
        summary = self.llm_summary(article_titles_and_contents)

        return tags, summary, articles

    def llm_summary(self, target_articles: dict[str, list[tuple[str, str]]]) -> str:
        # TODO: By 佑
        return "summary"
