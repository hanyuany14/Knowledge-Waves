"""This module is used to run the backend locally for testing purposes.
And need to be ignored in the github.
"""

from datetime import datetime
from bigquery_operation import BigQueryOperation
from gcs_operation import GCSOperation

from main import Main

if __name__ == "__main__":

    main = Main()

    # print("Start preparing news...")
    # main.prepare_news()
    # print("Done!")

    # query = "我想要找生成式ai"
    # print(query)
    # sources = ["github", "medium"]
    # tags, summary, articles = main.do_summarize(query=query, sources=sources)

    # print(f"\n\ntags: {tags}")
    # print(f"\n\narticles: {articles}")
    # print(f"\n\nsummary: {summary}")

    tags = [
        ("目标跟踪", "github"),
        ("正则表达式", "github"),
        ("计算机网络", "github"),
        ("模块", "github"),
        ("多目标算法", "github"),
        ("微软", "github"),
        ("杂谈", "github"),
        ("图论", "github"),
        ("分布式", "github"),
        ("智慧园区", "github"),
        ("前端", "medium"),
        ("学习", "medium"),
        ("编辑器", "medium"),
        ("炼丹师", "medium"),
        ("音视频", "medium"),
        ("运维", "medium"),
        ("账号与门户管理工具", "medium"),
        ("大数据", "medium"),
        ("网络", "medium"),
        ("算法", "medium"),
    ]

    articles = BigQueryOperation().fetch_articles_by_tags(interested_tags=tags)
    article_titles_and_contents = GCSOperation().fetch_articles_by_title(source_and_titles_and_url=articles)
    print("articles:", articles)
    print("contents:", article_titles_and_contents)
