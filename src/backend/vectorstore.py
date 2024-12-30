import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(project_root)

from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

from langchain_google_vertexai import VertexAIEmbeddings
from langchain_google_community import BigQueryVectorStore

import src.backend.configs as configs
import src.backend.utils as utils
from src.backend.configs import GOOGLE_API_KEY


class VectorStore:
    def __init__(self):

        self.yesterday, self.today = utils.get_time_range()

        today_date = self.today.strftime("%Y%m%d")
        self.__table_name = f"{configs.VECTORSTORE_TABLE_ID}_{today_date}"
        print(f"table_name: {self.__table_name}")

    def embedding_and_upload(self, today_tags: dict[str, set[str]]) -> bool:

        print(f"\n\nNow embedding and uploading tags to vectorestore...")

        self.__delete_existed_vectorstore_table()
        self.__vectorstore_obj = self.__get_vectorestore_obj()

        all_tags = set()
        all_metadatas = []
        for source, tags in today_tags.items():
            all_tags = all_tags.union(tags)
            all_metadatas.extend([{"source": source} for _ in tags])

        print(f"    all_tags: {all_tags}")
        print(f"    all_metadatas: {all_metadatas}\n\n")

        all_tags = list(all_tags)
        self.__vectorstore_obj.add_texts(all_tags, metadatas=all_metadatas)
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
        self.__vectorstore_obj = self.__get_vectorestore_obj()

        interested_tags = []
        sources = sources if sources else ["github", "medium", "csdn"]

        filter = " OR ".join([f"source = '{source}'" for source in sources])

        represented_query = self._represent_query(query)
        # represented_query = [query]

        print(f"\nBefore representing: {query}")
        print(f"After representing: {represented_query}")

        docs_for_tags = self.__vectorstore_obj.batch_search(
            queries=represented_query,
            filter=f"({filter})",
            k=5,
        )

        interested_tags = []
        for result in docs_for_tags:
            query_predictions = []
            for doc in result:
                query_predictions.append({"content": doc[0].page_content, "similarity": doc[1]})
            interested_tags.extend(query_predictions)

        top_5_tags_with_score = sorted(interested_tags, key=lambda x: x["similarity"], reverse=True)[:5]
        top_5_tags = [tag["content"] for tag in top_5_tags_with_score]
        return top_5_tags

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
            embedding=self.__get_embeddings_obj(),
            credentials=utils.CREDENTIAL_OBJ,
            distance_type="COSINE",  # 'COSINE', 'EUCLIDEAN', 'DOT_PRODUCT'
        )

    def __delete_existed_vectorstore_table(self):
        utils.BQ_CLIENT.delete_table(
            f"{configs.PROJECT_ID}.{configs.DATASET_ID}.{self.__table_name}", not_found_ok=True
        )
        print(f"Table  `{self.__table_name}` deleted successfully.")

    def _represent_query(self, query: str) -> list[str]:

        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-8b",
            temperature=0,
            max_tokens=None,
            timeout=None,
            max_retries=2,
            api_key=GOOGLE_API_KEY,  # type: ignore
        )

        tags_parser = StructuredOutputParser.from_response_schemas(
            response_schemas=[
                ResponseSchema(
                    name="tags",
                    description=(
                        "Provide a list of topics in English that accurately represent the key themes or subjects "
                        "discussed in the query. The topics should be concise, relevant, and capture the essence of "
                        "what the query is about."
                    ),
                    type="List[str]",
                ),
            ]
        )
        prompt_template = """
        You are an intelligent assistant that helps identify key topics or tags from natural language queries. Your task is to analyze the user's input and provide a concise, relevant list of English tags that represent the main themes or subjects mentioned or implied in the query.

        Guidelines:
        1. Focus on extracting key topics that best describe the content of the query.
        2. Use clear and specific tags that are relevant to the query's context.
        3. Avoid using vague or overly broad tags; ensure each tag is meaningful.
        4. Return the tags as a list of strings in English.
        5. you have to follow the format to response: {format_instructions}

        Example 1:
        Query: "What are the best tools for building scalable distributed systems?"
        Tags: ["distributed", "Distributed Locks", "http", "reverse-proxy"]

        Example 2:
        Query: "How does psychology influence technology adoption in society?"
        Tags: ["psychology", "technology", "society", "lifestyle"]

        Now, analyze the following query and provide the relevant tags:
        {task_content}
        """

        chat_prompt = PromptTemplate(
            input_variables=["task_content"],
            partial_variables={
                "format_instructions": tags_parser.get_format_instructions(),
            },
            template=prompt_template,
            output_parser=tags_parser,
        )

        chain = chat_prompt | llm | tags_parser
        response = chain.invoke({"task_content": query})

        return response["tags"]


if __name__ == "__main__":
    result = VectorStore().search_similar_tags(
        query="我想知道今天深度學習與分散式系統部署的文章內容",
        sources=None,
    )
    print(f"Retrival result: {result}")
