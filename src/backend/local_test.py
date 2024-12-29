import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.append(project_root)

from src.backend.bigquery_operation import BigQueryOperation
from src.backend.gcs_operation import GCSOperation
from src.backend.main import Main

if __name__ == "__main__":

    main = Main()

    # print("Start preparing news...")
    # main.prepare_news()
    # print("Done!")

    # query = "我想要找生成式ai"
    # print(query)
    # sources = ["github", "medium"]
    # tags, summary, articles = main.do_text_search_summary(query=query, sources=sources)

    selected_tags = ["react", "python"]
    print(selected_tags)
    sources = ["github", "medium"]
    tags, summary, articles = main.do_select_tag_summary(selected_tags=selected_tags, sources=sources)

    print(f"\n\ntags: {tags}")
    print(f"\n\narticles: {articles}")
    print(f"\n\nsummary: {summary}")

# tags = [
#     ("目标跟踪", "github"),
#     ("正则表达式", "github"),
#     ("计算机网络", "github"),
#     ("模块", "github"),
#     ("多目标算法", "github"),
#     ("微软", "github"),
#     ("杂谈", "github"),
#     ("图论", "github"),
#     ("分布式", "github"),
#     ("智慧园区", "github"),
#     ("前端", "medium"),
#     ("学习", "medium"),
#     ("编辑器", "medium"),
#     ("炼丹师", "medium"),
#     ("音视频", "medium"),
#     ("运维", "medium"),
#     ("账号与门户管理工具", "medium"),
#     ("大数据", "medium"),
#     ("网络", "medium"),
#     ("算法", "medium"),
# ]

# articles = BigQueryOperation().fetch_articles_by_tags(interested_tags=tags)
# article_titles_and_contents = GCSOperation().fetch_articles_by_title_and_url(source_and_titles_and_url=articles)
# print("articles:", articles)
# print("contents:", article_titles_and_contents)
