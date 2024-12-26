import requests
import json
import base64
import feedparser
from datetime import datetime, timedelta
from typing import Set, Tuple, List, Dict
from bs4 import BeautifulSoup
import markdown
import re
import time
import random
import logging
from logging.handlers import RotatingFileHandler
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import configs as configs

# 配置日誌
logger = logging.getLogger()
logger.setLevel(logging.ERROR)
handler = RotatingFileHandler("csdn_crawl_errors.log", maxBytes=5 * 1024 * 1024, backupCount=5)
formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class Crawl:
    def __init__(self) -> None:
        self.yesterday = datetime.utcnow() - timedelta(days=1)

        self.__medium_existed_article = set()
        self.__medium_existed_tags = set()

        self.__github_existed_repo = set()

        self.__csdn_existed_article = set()
        self.__csdn_existed_tags = set()

        # CSDN的User-Agent列表
        self.HEADERS = [
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            },
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Safari/605.1.15"
            },
            {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            },
        ]

        self.session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def crawl(
        self,
    ) -> Tuple[
        Dict[str, List[Dict[str, object]]],
        Dict[str, Set[str]],
    ]:
        """
        爬蟲：爬取三個網站的文章內容

        Returns:
            crawl_results (dict): 爬取的文章內容
            today_tags (dict): 今日爬取的標籤
        """
        # 爬取Medium
        try:
            medium_result, medium_tags = self.__crawl_from_medium()
        except Exception as e:
            print(f"Medium爬取失敗：{e}")
            medium_result, medium_tags = [], set()

        # 爬取GitHub
        try:
            github_result, github_tags = self.__crawl_from_github()
        except Exception as e:
            print(f"GitHub爬取失敗：{e}")
            github_result, github_tags = [], set()

        # 爬取CSDN
        try:
            csdn_result, csdn_tags = self.__crawl_from_csdn()
        except Exception as e:
            print(f"CSDN爬取失敗：{e}")
            csdn_result, csdn_tags = [], set()

        crawl_results = {
            "github": github_result,
            "medium": medium_result,
            "csdn": csdn_result,
        }

        today_tags = {
            "github": github_tags,
            "medium": medium_tags,
            "csdn": csdn_tags,
        }

        return crawl_results, today_tags

    def __crawl_from_github(self) -> Tuple[List[Dict[str, object]], Set[str]]:
        """
        爬取GitHub倉庫資訊

        Returns:
            Tuple: (倉庫資訊列表, 標籤集合)
        """
        print("\n現在正在從GitHub爬取\n")
        result_list = []

        try:
            # 使用GitHub API爬取過去24小時內創建的倉庫
            repos = self.fetch_github_repos()
            print(f"從GitHub API抓取了 {len(repos)} 個倉庫。")
        except Exception as e:
            print(f"抓取GitHub倉庫失敗：{e}")
            repos = []

        # 過濾已存在的倉庫
        for repo in repos:
            if repo["url"] in self.__github_existed_repo:
                print(f"倉庫 {repo['title']} 已存在。")
                continue
            result_list.append(repo)
            self.__github_existed_repo.add(repo["url"])

        # 使用BeautifulSoup爬取GitHub Trending頁面
        try:
            trending_repos = self.fetch_github_trending()
            print(f"從GitHub Trending頁面抓取了 {len(trending_repos)} 個熱門倉庫。")
        except Exception as e:
            print(f"抓取GitHub Trending倉庫失敗：{e}")
            trending_repos = []

        for repo in trending_repos:
            if repo["url"] in self.__github_existed_repo:
                print(f"熱門倉庫 {repo['title']} 已存在。")
                continue
            result_list.append(repo)
            self.__github_existed_repo.add(repo["url"])

        # 提取標籤
        tags = self.__get_tags(result_list)

        return result_list, tags

    def fetch_github_repos(self) -> List[Dict[str, object]]:
        """
        使用GitHub API抓取過去24小時內創建的倉庫

        Returns:
            List[Dict]: 包含倉庫資訊的字典列表
        """
        base_url = "https://api.github.com/search/repositories"
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        time_range = yesterday.strftime("%Y-%m-%dT%H:%M:%SZ")

        # 查詢參數：過去24小時內創建的倉庫，按星標降序排序
        query_params = {
            "q": f"created:>{time_range}",
            "sort": "stars",
            "order": "desc",
            "per_page": 100,  # GitHub API每頁最大100
        }

        headers = {
            "Authorization": f"token {configs.GITHUB_PERSONAL_ACCESS_TOKEN}",  # 從configs導入
            "Accept": "application/vnd.github.v3+json",
        }

        response = self.session.get(base_url, headers=headers, params=query_params, timeout=10)
        if response.status_code != 200:
            raise Exception(f"抓取GitHub倉庫失敗：{response.status_code}, {response.json().get('message', '')}")

        repos = response.json().get("items", [])
        result = []
        for repo in repos:
            # 提取倉庫詳情
            title = repo.get("full_name", "無標題")
            repo_url = repo.get("html_url", "無URL")
            description = repo.get("description", "無描述")
            language = repo.get("language", "無語言指定")
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            created_at_str = repo.get("created_at", "無創建日期")
            try:
                created_at = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%SZ")
                publish_date = created_at.isoformat()  # 轉換為字符串
            except ValueError:
                publish_date = self.yesterday.isoformat()  # 如果日期格式不正確，設置為昨天並轉換為字符串

            # 獲取README內容
            readme_content = self.fetch_readme(title, headers)

            # 獲取倉庫主題（topics）
            topics = self.fetch_topics(title, headers)

            repo_data = {
                "title": title,
                "content": f"This is description:\n{description}.\n This is readme of the repo:{readme_content}",
                "tags": topics,  # 使用topics作為tags
                "url": repo_url,
                "publish_date": publish_date,  # 轉換為字符串
                "language": language,
                "likes": stars,
            }

            result.append(repo_data)

        return result

    def fetch_readme(self, repo_full_name: str, headers: Dict[str, str]) -> str:
        """
        獲取倉庫的README內容

        Args:
            repo_full_name (str): 倉庫全名，例如 "owner/repo"
            headers (Dict[str, str]): HTTP請求頭

        Returns:
            str: README內容（前500字符）
        """
        readme_url = f"https://api.github.com/repos/{repo_full_name}/readme"
        response = self.session.get(readme_url, headers=headers, timeout=10)
        if response.status_code == 200:
            readme_data = response.json()
            try:
                readme_content = base64.b64decode(readme_data.get("content", "")).decode("utf-8", errors="ignore")

                if not readme_content.strip():
                    print(f"Readme for {repo_full_name} is empty.")
                    return "README內容為空。"

                # 判斷是否為Markdown格式（簡單判斷是否包含Markdown語法）
                if re.search(r"[#*_\-~]", readme_content):
                    # 將 Markdown 轉換為 HTML
                    readme_html = markdown.markdown(readme_content)
                    # 使用 BeautifulSoup 解析 HTML
                    readme_text = BeautifulSoup(readme_html, "html.parser").get_text()
                else:
                    # 直接解析 HTML
                    readme_text = BeautifulSoup(readme_content, "html.parser").get_text()

                return readme_text[:500] + "..." if len(readme_text) > 500 else readme_text
            except Exception as e:
                print(f"解碼 {repo_full_name} 的README失敗：{e}")
                return "無法解碼README內容。"
        else:
            return "README無法訪問或未找到。"

    def fetch_topics(self, repo_full_name: str, headers: Dict[str, str]) -> List[str]:
        """
        獲取倉庫的主題（topics）

        Args:
            repo_full_name (str): 倉庫全名，例如 "owner/repo"
            headers (Dict[str, str]): HTTP請求頭

        Returns:
            List[str]: 主題列表
        """
        topics_url = f"https://api.github.com/repos/{repo_full_name}/topics"
        topics_headers = {**headers, "Accept": "application/vnd.github.mercy-preview+json"}
        response = self.session.get(topics_url, headers=topics_headers, timeout=10)
        if response.status_code == 200:
            topics_data = response.json()
            return topics_data.get("names", [])
        else:
            return ["無法訪問或未找到主題"]

    def fetch_github_trending(self) -> List[Dict[str, object]]:
        """
        使用BeautifulSoup爬取GitHub Trending頁面

        Returns:
            List[Dict]: 包含Trending倉庫資訊的字典列表
        """
        trending_url = "https://github.com/trending?since=daily"
        response = self.session.get(trending_url, timeout=10)
        if response.status_code != 200:
            raise Exception(f"抓取GitHub Trending頁面失敗：{response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        repo_elements = soup.find_all("article", class_="Box-row")
        trending_repos = []

        headers = {
            "Authorization": f"token {configs.GITHUB_PERSONAL_ACCESS_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }

        for repo in repo_elements:
            # 提取倉庫名稱（格式：owner/repo）
            repo_name_tag = repo.find("h2", class_="h3")
            if not repo_name_tag:
                continue
            repo_name = repo_name_tag.text.strip().replace("\n", "").replace(" ", "")
            if "/" not in repo_name:
                continue
            owner, repo_title = repo_name.split("/")

            # 构建仓库URL
            repo_url = f"https://github.com/{repo_name}"

            # 提取倉庫描述
            repo_description_tag = repo.find("p", class_="col-9 color-fg-muted my-1 pr-4")
            repo_description = repo_description_tag.text.strip() if repo_description_tag else "無描述提供"

            # 提取編程語言
            repo_language_tag = repo.find("span", itemprop="programmingLanguage")
            repo_language = repo_language_tag.text.strip() if repo_language_tag else "無語言指定"

            # 提取星標數量
            star_element = repo.find("a", class_="Link--muted d-inline-block mr-3")
            star_count = star_element.text.strip().replace(",", "") if star_element else "0"
            try:
                star_count = int(star_count)
            except ValueError:
                star_count = 0

            # 獲取倉庫主題（topics）
            topics = self.fetch_topics(repo_name, headers)

            # 獲取README內容
            readme_content = self.fetch_readme(repo_name, headers)

            # 處理 publish_date 為字符串
            publish_date = self.yesterday.isoformat()  # 由於Trending頁面沒有創建日期，設置為昨天並轉換為字符串

            repo_data = {
                "title": repo_name,
                "content": f"This is repo_description:\n{repo_description}.\n This is readme of the repo:{readme_content}",
                "tags": topics,
                "url": repo_url,
                "publish_date": publish_date,
                "language": repo_language,
                "likes": star_count,
            }

            trending_repos.append(repo_data)

        return trending_repos

    def __crawl_from_medium(self) -> Tuple[List[Dict[str, object]], Set[str]]:
        """爬取medium.com的文章

        Returns:
            tuple: (文章列表, 標籤集合)
        """

        print(f"\n現在正在從medium.com爬取\n")

        max_times = 3
        gloabl_medium_result = []
        categories = ["technology"]
        self.__medium_existed_tags = self.__medium_existed_tags.union(categories)
        print(f"已存在的標籤：{self.__medium_existed_tags}")

        for i in range(max_times):
            print(f"\n----------------處理輪次：{i+1}----------------\n")

            categories = categories[:1]  # 用於測試

            print(f"    類別數量：{len(categories)}")

            parse_medium_result, parsed_tags = self.__crawl_medium_24hr_feed_by_categories(categories)

            if parse_medium_result == []:  # 第一個終止條件 - 這一輪查詢沒有出現任何新的文章
                print("parse_medium_result 為空，結束爬蟲")
                break
            else:
                gloabl_medium_result.extend(parse_medium_result)

            if set(parsed_tags).issubset(
                self.__medium_existed_tags
            ):  # 第二個終止條件 - 本輪新的 tags 都已經存在於 existed_tags 中
                print("所有標籤都已經存在於 existed_tags 中，結束爬蟲")
                break
            else:
                categories = [tag for tag in parsed_tags if tag not in self.__medium_existed_tags]
                self.__medium_existed_tags = self.__medium_existed_tags.union(categories)

        print(f"    爬取的文章數量：{len(gloabl_medium_result)}")
        tags = self.__get_tags(gloabl_medium_result)

        return gloabl_medium_result, tags

    def __crawl_from_csdn(self) -> Tuple[List[Dict[str, object]], Set[str]]:
        """爬取CSDN的文章

        Returns:
            tuple: (文章列表, 標籤集合)
        """
        print("\n現在正在從CSDN爬取\n")
        max_pages = 10  # 修改為爬取10頁
        csdn_articles = self.__scrape_csdn_articles(max_pages)

        result_list = []
        tags_set = set()

        for article in csdn_articles:
            publish_time_str = article["publish_time"]
            if self.is_within_24_hours(publish_time_str):
                if article["link"] in self.__csdn_existed_article:
                    print(f"文章 {article['title']} 已存在。")
                    continue
                repo_data = {
                    "title": article["title"],
                    "content": article["content"],
                    "tags": article["tags"],
                    "url": article["link"],
                    "publish_date": self.parse_publish_time(publish_time_str).isoformat(),
                    "likes": article["likes"],
                    # "views": article["views_count"],
                    "language": "ch",
                }
                result_list.append(repo_data)
                self.__csdn_existed_article.add(article["link"])
                tags_set.update(article["tags"])
            else:
                print(f"文章 {article['title']} 不在24小時內，跳過。")

        print(f"    爬取的CSDN文章數量：{len(result_list)}")
        return result_list, tags_set

    def is_within_24_hours(self, publish_time: str) -> bool:
        """
        檢查發布時間是否在過去24小時內

        Args:
            publish_time (str): 發布時間字符串

        Returns:
            bool: 是否在24小時內
        """
        now = datetime.now()
        if "小時前" in publish_time:
            hours = int(re.search(r"(\d+)小時前", publish_time).group(1))
            publish_time_obj = now - timedelta(hours=hours)
        elif "分鐘前" in publish_time:
            minutes = int(re.search(r"(\d+)分鐘前", publish_time).group(1))
            publish_time_obj = now - timedelta(minutes=minutes)
        elif "昨天" in publish_time:
            publish_time_obj = now - timedelta(days=1)
        else:
            # 假設為標準日期格式 "%Y-%m-%d %H:%M:%S"
            try:
                publish_time_obj = datetime.strptime(publish_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                print(f"無法解析的發布時間格式：{publish_time}")
                return False
        return now - publish_time_obj <= timedelta(days=1)

    def parse_publish_time(self, publish_time: str) -> datetime:
        """
        將發布時間字符串轉換為datetime對象

        Args:
            publish_time (str): 發布時間字符串

        Returns:
            datetime: 發布時間的datetime對象
        """
        now = datetime.now()
        if "小時前" in publish_time:
            hours = int(re.search(r"(\d+)小時前", publish_time).group(1))
            return now - timedelta(hours=hours)
        elif "分鐘前" in publish_time:
            minutes = int(re.search(r"(\d+)分鐘前", publish_time).group(1))
            return now - timedelta(minutes=minutes)
        elif "昨天" in publish_time:
            return now - timedelta(days=1)
        else:
            try:
                return datetime.strptime(publish_time, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return self.yesterday  # 返回昨天的時間

    def scrape_article_details(self, url: str) -> Tuple[str, List[str], str, int, int]:
        """
        爬取CSDN文章詳情頁面

        Args:
            url (str): CSDN文章URL

        Returns:
            Tuple[str, List[str], str, int, int]: (發布時間, 標籤列表, 內容, 點讚數, 瀏覽數)
        """
        try:
            response = self.session.get(url, headers=random.choice(self.HEADERS), timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")

                # 嘗試多種選擇器來提取發布時間
                publish_time = "N/A"
                possible_time_selectors = [
                    {"name": "div", "class_": "time-box"},
                    {"name": "span", "class_": "time blog-postTime"},
                    {"name": "meta", "attrs": {"name": "publish-date"}},
                    {"name": "span", "class_": "date"},  # 新增的選擇器範例
                    {"name": "div", "class_": "article-header__publish-time"},  # 另一個可能的選擇器
                    {"name": "span", "class_": "publish-time"},  # 另一個可能的選擇器
                    # 根據實際情況添加更多選擇器
                ]

                for selector in possible_time_selectors:
                    if "attrs" in selector:
                        tag = soup.find(selector["name"], attrs=selector["attrs"])
                    else:
                        tag = soup.find(selector["name"], class_=selector["class_"])
                    if tag:
                        if tag.name == "meta":
                            publish_time = tag.get("content", "N/A")
                        else:
                            publish_time = tag.get_text(strip=True)

                        # 使用正則表達式提取時間
                        match = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", publish_time)
                        if match:
                            publish_time = match.group(1)
                        # 處理相對時間格式，如 "3小時前"
                        elif "小時前" in publish_time or "分鐘前" in publish_time or "昨天" in publish_time:
                            pass  # 保留原始相對時間格式
                        else:
                            publish_time = "N/A"

                        break  # 成功找到發布時間後退出循環

                if publish_time == "N/A":
                    # 嘗試通過正則表達式在整個頁面中搜索日期
                    date_patterns = [
                        r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})",  # 2024-12-23 21:22:43
                        r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})",  # 2024/12/23 21:22:43
                        r"(\d{4}-\d{2}-\d{2})",  # 2024-12-23
                        r"(\d{4}/\d{2}/\d{2})",  # 2024/12/23
                        r"(\d{2}:\d{2}:\d{2})",  # 21:22:43
                        # 添加更多日期格式
                    ]
                    for pattern in date_patterns:
                        match = re.search(pattern, response.text)
                        if match:
                            publish_time = match.group(1)
                            break

                if publish_time == "N/A":
                    logger.error(f"無法解析發布時間的文章 URL: {url}")
                    print(f"無法解析發布時間的文章 URL: {url}")

                # 提取文章標籤
                tags = []
                tag_container = soup.find("div", class_="tags-box artic-tag-box")
                if tag_container:
                    tags = [tag.get_text(strip=True) for tag in tag_container.find_all("a", class_="tag-link")]

                # 提取文章部分內容
                content = ""
                content_container = soup.find("div", id="content_views")
                if content_container:
                    content = content_container.get_text(strip=True)[:200]  # 取前 200 字

                print(f"發布時間: {publish_time}")

                # 提取點讚數
                likes_count = 0
                likes_element = soup.find("span", class_="read-count", id="blog-digg-num")
                if likes_element:
                    likes_text = likes_element.get_text(strip=True)
                    number_match = re.search(r"\d+", likes_text)
                    if number_match:
                        likes_count = int(number_match.group())

                # 提取瀏覽數
                views_count = 0
                views_element = soup.find("span", class_="read-count", id=None)  # 排除點讚數的span
                if views_element:
                    views_text = views_element.get_text(strip=True)
                    number_match = re.search(r"(\d+\.?\d*)([k])?", views_text.lower())
                    if number_match:
                        number = float(number_match.group(1))
                        unit = number_match.group(2)
                        if unit == "k":
                            views_count = int(number * 1000)
                        else:
                            views_count = int(number)

                return publish_time, tags, content, likes_count, views_count
            else:
                print(f"無法獲取文章詳情：{url}, 狀態碼：{response.status_code}")
                logger.error(f"無法獲取文章詳情：{url}, 狀態碼：{response.status_code}")
                return "N/A", [], "N/A", 0, 0
        except Exception as e:
            print(f"抓取文章詳情失敗：{url}, 錯誤：{e}")
            logger.error(f"抓取文章詳情失敗：{url}, 錯誤：{e}")
            return "N/A", [], "N/A", 0, 0

    def __scrape_csdn_articles(self, max_pages: int) -> List[Dict[str, object]]:
        """
        爬取CSDN的文章

        Args:
            max_pages (int): 要爬取的頁數

        Returns:
            List[Dict[str, object]]: 文章列表
        """
        base_url = "https://blog.csdn.net/nav/home?page={}"
        articles = []

        for page in range(1, max_pages + 1):
            url = base_url.format(page)
            print(f"正在爬取CSDN第 {page} 頁...")
            try:
                response = self.session.get(url, headers=random.choice(self.HEADERS), timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    articles_list = soup.find_all("div", class_="Community-item blog")
                    for article in articles_list:
                        try:
                            # 提取標題和連結
                            title_tag = article.find("a", class_="blog")
                            title = (
                                title_tag.find("span", class_="blog-text").get_text(strip=True) if title_tag else None
                            )
                            link = title_tag["href"] if title_tag else None

                            if not title or not link:
                                print(f"跳過無效的文章：{article}")
                                continue

                            # 確保連結是完整 URL
                            if not link.startswith("http"):
                                link = f"https://blog.csdn.net{link}"
                            print(f"正在處理文章：{title} - {link}")

                            # 爬取文章詳情頁面的數據
                            publish_time, tags, content, likes, views = self.scrape_article_details(link)

                            # 檢查發布時間是否為 "N/A"，如果是則跳過
                            if publish_time == "N/A":
                                print(f"文章 {title} 的發布時間無效，跳過。")
                                continue

                            articles.append(
                                {
                                    "title": title,
                                    "link": link,
                                    "publish_time": publish_time,
                                    "tags": tags,
                                    "content": content,
                                    "likes": likes,
                                    "views_count": views,
                                }
                            )
                        except Exception as e:
                            print(f"處理文章時出錯：{e}")
                            logger.error(f"處理文章時出錯：{e}")
                else:
                    print(f"無法獲取CSDN第 {page} 頁，狀態碼：{response.status_code}")
                    logger.error(f"無法獲取CSDN第 {page} 頁，狀態碼：{response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"請求CSDN第 {page} 頁失敗：{e}")
                logger.error(f"請求CSDN第 {page} 頁失敗：{e}")
            except Exception as e:
                print(f"處理CSDN第 {page} 頁時出現未知錯誤：{e}")
                logger.error(f"處理CSDN第 {page} 頁時出現未知錯誤：{e}")
            finally:
                time.sleep(random.uniform(3, 6))  # 隨機休眠以避免被封禁

        return articles

    def __get_tags(self, parse_results_list: List[Dict[str, object]]) -> Set[str]:
        """
        提取所有唯一標籤

        Args:
            parse_results_list (List[Dict]): 解析後的結果列表

        Returns:
            Set[str]: 唯一標籤集合
        """
        tags = [tag for parse_result in parse_results_list for tag in parse_result.get("tags", [])]
        return set(tags)

    def __crawl_medium_url(self, url: str) -> dict:
        """
        獲取Medium文章內容

        Args:
            url (str): Medium文章URL

        Returns:
            Dict[str, str]: 文章內容
        """
        url = f"{url}?format=json"

        response = requests.get(url)
        if response.status_code == 200:
            if response.text.startswith("])}"):
                json_data = response.text[16:]
                data = json.loads(json_data)

                paragraphs = data["payload"]["value"]["content"]["bodyModel"]["paragraphs"]
                clap_count = data["payload"]["value"]["virtuals"]["totalClapCount"]
                language = data["payload"]["value"]["detectedLanguage"]

                return {
                    "likes": clap_count,
                    "language": language,
                    "content": "".join(paragraph["text"] for paragraph in paragraphs),
                }

        else:
            raise Exception(f"無法獲取資料：{response.status_code}")

        return {"content": ""}

    def __crawl_medium_24hr_feed_by_categories(self, categories: List[str]) -> Tuple[List[Dict[str, object]], Set[str]]:
        """
        爬取Medium特定類別的24小時內發布的文章

        Args:
            categories (List[str]): 類別列表

        Returns:
            Tuple: (文章列表, 標籤集合)
        """
        parsed_tags: Set[str] = set()
        parse_medium_result = []

        for category in categories:
            print(f"處理類別：{category}")
            feed = feedparser.parse(f"{configs.MEDIUM_TAG_BASE_URL}{category}")

            for entry in feed.entries:
                # 解析發布時間
                published_time = datetime(*entry.published_parsed[:6])
                publish_date = published_time.isoformat()

                if published_time > self.yesterday:

                    if entry.id in self.__medium_existed_article:
                        print(f"文章 `{entry.title}` 已存在")
                        continue

                    print(f"處理文章：{entry.title}")
                    try:
                        parse_result = self.__crawl_medium_url(entry.id)
                        tags = [tag.term for tag in entry.tags] if "tags" in entry else []

                        parse_result["title"] = entry.title
                        parse_result["url"] = entry.id
                        parse_result["tags"] = tags
                        parse_result["publish_date"] = publish_date

                        parse_medium_result.append(parse_result)
                        self.__medium_existed_article.add(entry.id)
                        parsed_tags = parsed_tags.union(tags)

                    except Exception as e:
                        print(f"解析文章失敗：{e}")
                        # parse_result = "failed"  # 這裡不需要賦值，因為不會被使用

            print(f"類別：{category}, 計數：{len(parse_medium_result)}")

        return parse_medium_result, parsed_tags


if __name__ == "__main__":
    crawl = Crawl()
    crawl_results, today_tags = crawl.crawl()
    print(f"\n\ncrawl_results:\n\n{crawl_results}")
    print(f"\n\ntoday_tags:\n\n{today_tags}")

    # # 合併 crawl_results 和 today_tags 到一個字典中
    # # 將 today_tags 中的 set 轉換為 list，以便 JSON 序列化
    # combined_results = {"crawl_results": crawl_results, "today_tags": {k: list(v) for k, v in today_tags.items()}}

    # # 保存到一個 JSON 文件
    # with open("combined_crawl_results_csdn.json", "w", encoding="utf-8") as f:
    #     json.dump(combined_results, f, ensure_ascii=False, indent=2)
    # print("Combined crawl results 已保存到 combined_crawl_results_csdn.json")

    # # 另外保存CSDN的結果
    # csdn_results = crawl_results.get("csdn", [])
    # # 由於__crawl_from_csdn已經過濾了24小時內的文章，直接保存
    # with open("csdn_crawl_results_24.json", "w", encoding="utf-8") as f:
    #     json.dump(csdn_results, f, ensure_ascii=False, indent=2)
    # print("CSDN crawl results 已保存到 csdn_crawl_results_24.json")
