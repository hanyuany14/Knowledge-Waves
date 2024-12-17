from datetime import datetime

from langchain_google_community.bigquery import BigQueryLoader
from langchain_google_vertexai import VertexAIEmbeddings
from langchain_google_community import BigQueryVectorStore


import src.backend.configs as configs
import src.backend.utils as utils


class VectorStore:
    def __init__(self):
        self.__embedding_obj = self.__get_embeddings_obj()
        self.__vectorstore_obj = self.__get_vectorestore_obj()

        today_date = datetime.now().strftime("%Y%m%d")
        self.__table_name = f"{configs.VECTORSTORE_TABLE_ID}_{today_date}"

    def embedding_and_upload(self, today_tags: dict[str, set[str]]) -> bool:

        all_texts = set()
        for source, tags in today_tags.items():
            all_texts = all_texts.union(tags)
            metadatas = [{"source": source} for _ in tags]

        self.__vectorstore_obj.add_texts(texts=list(all_texts), metadatas=metadatas)
        return True

    def search_similar_tags(self, query: str, sources: list[str] | None) -> list[(str)]:
        """Searches for similar tags based on the query.

        Args:
            query (str): The query to search for. e.g. "Give me some information about NLP."
            sources (list[str], optional): The sources selected by user to search. Defaults to None.
                                            e.g. ["github", "medium"]

        Returns:
            list[(str)]: A list of similar tags. e.g. ["NLP", "Natural Language Processing"]
        """
        interested_tags = []
        sources = sources if sources else ["github", "medium", "csdn"]

        for source in sources:
            docs_for_tags = self.__vectorstore_obj.similarity_search(
                query=query,
                filter=[{"source": source}],
                k=10,
            )
            for doc in docs_for_tags:
                interested_tags.append((doc.page_content, doc.metadata["source"]))

        return interested_tags

    def __get_embeddings_obj(self):
        return VertexAIEmbeddings(
            model_name="textembedding-gecko@latest", project=configs.PROJECT_ID, credentials=utils.CREDENTIAL_OBJ
        )

    def __get_vectorestore_obj(self):
        return BigQueryVectorStore(
            project_id=configs.PROJECT_ID,
            dataset_name=configs.DATASET_ID,
            table_name=self.__table_name,
            location=configs.VECTORSTORE_REGION,
            embedding=self.__embedding_obj,
            credentials=utils.CREDENTIAL_OBJ,
            distance_type="COSINE",  # 'COSINE', 'EUCLIDEAN', 'DOT_PRODUCT'
        )
