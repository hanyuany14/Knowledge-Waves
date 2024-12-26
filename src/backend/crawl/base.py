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


class CrawlBase:
    def __init__(self):
        self.yesterday = datetime.utcnow() - timedelta(days=1)

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
