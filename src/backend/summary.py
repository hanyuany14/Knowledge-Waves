
class Summarization:
    def __init__(self, text):
        self.text = text

    def do_summary(self, query: str):
        tags = VectorStore.search_similar_tags(query, None)
        articles = BigQueryOpeartion.search_articles_by_tags(tags)
        articles_content = GCSOperation.search_articles_by_title(articles)
        summary = self.llm_summary(articles_content)

        return tags, summary, articles

    def llm_summary(self):
        pass
