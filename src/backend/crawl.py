from datetime import datetime


class Crawl:
    def __init__(self) -> None:
        self.yesterday = datetime.now().replace(day=datetime.now().day - 1)

    def crawl(
        self,
    ) -> tuple[
        dict[str, list[dict[str, str | list[str] | datetime]]],
        set[str],
    ]:
        """
        爬蟲：爬取三個網站的文章內容
        """
        github_result = self.__crawl_from_github()
        medium_result = self.__crawl_from_medium()
        csdn_result = self.__crawl_from_csdn()

        today_tags = self.__get_tags(github_result + medium_result + csdn_result)

        crawl_results = {
            "github": github_result,
            "medium": medium_result,
            "csdn": csdn_result,
        }
        return crawl_results, today_tags

    def __crawl_from_github(self) -> list[dict[str, str | list[str] | datetime]]:
        """ """
        result_list = [
            {
                "title": "title",
                "subtitle": "subtitle",
                "content": "content",
                "tags": ["tag1", "tag2"],
                "url": "url",
                "publish_time": datetime,
            }
        ]

        return result_list

    def __crawl_from_medium(self) -> list[dict[str, str | list[str] | datetime]]:
        """ """
        result_list = [
            {
                "title": "title",
                "subtitle": "subtitle",
                "content": "content",
                "tags": ["tag1", "tag2"],
                "url": "url",
                "publish_time": datetime,
            }
        ]

        return result_list

    def __crawl_from_csdn(self) -> list[dict[str, str | list[str] | datetime]]:
        """ """
        result_list = [
            {
                "title": "title",
                "subtitle": "subtitle",
                "content": "content",
                "tags": ["tag1", "tag2"],
                "url": "url",
                "publish_time": datetime,
            }
        ]

        return result_list

    def __get_tags(self, parse_result: list[dict]) -> set[str]:
        tags = [tag for result in parse_result for tag in result["tags"]]
        return set(tags)
