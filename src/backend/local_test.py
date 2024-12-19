"""This module is used to run the backend locally for testing purposes.
And need to be ignored in the github.
"""

from datetime import datetime

from main import Main

if __name__ == "__main__":

    main = Main()
    # print("Start preparing news...")
    # main.prepare_news()
    # print("Done!")

    # TODO: 佑，上面的程式碼是初始化，每天要記得用一下，下面的程式碼是用來測試的，可以去修改 main 把不需要的程式碼註解掉

    query = "我想要找生成式ai"
    print(query)
    sources = ["github", "medium", "csdn"]
    tags, summary, articles = main.do_summarize(query=query, sources=sources)
    print(f"tags: {tags}")

    # articles = BigQueryOperation().fetch_articles_by_tags(interested_tags=tags)
    # article_titles_and_contents = GCSOperation().fetch_articles_by_title(source_and_titles_and_url=articles)
    # print('articles:',articles)
    # print('contents:',article_titles_and_contents)
