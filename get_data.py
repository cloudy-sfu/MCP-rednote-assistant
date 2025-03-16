import json
import logging
import time

import pandas as pd
from bs4 import BeautifulSoup
from requests import Session

from xhshow.config import replacements
from xhshow.encrypt.misc_encrypt import x_b3_traceid, x_xray_traceid, search_id
from xhshow.encrypt.xs_encrypt import encrypt_xs
from xhshow.encrypt.xsc_encrypt import encrypt_xsc
from xhshow.extractor.extract_initial_state import extract_initial_state

with open("headers/explore.json", "r") as f:
    header_explore = json.load(f)
with open("headers/homefeed.json", "r") as f:
    header_homefeed = json.load(f)


class Feed:
    def __init__(self, cookies: dict):
        self.session = Session()
        self.cookies = cookies
        self.header = header_homefeed.copy()
        self.refresh_type = 1
        self.note_index = None
        self.initial_timestamp = None
        self.cursor_score = ""

    def init(self):
        """
        Initialize a "xiaohongshu" thread and get first page of posts.
        :return: pd.DataFrame table of posts' meta.
        """
        response = self.session.get(
            url="https://www.xiaohongshu.com/explore",
            headers=header_explore,
            cookies=self.cookies,
        )
        assert response.status_code == 200, "Fail to fetch home page of xiaohongshu."
        self.initial_timestamp = round(time.time() * 1000)
        initial_state = extract_initial_state(response.text, replacements)
        posts = []
        for feed in initial_state['feed']['feeds']:
            post = {
                "id": feed['id'],
                "xsec_token": feed['xsecToken'],
                # no title is possible
                "title": feed['noteCard'].get('displayTitle', ''),
                # resolution: blur, median, original (not available in feed)
                "cover_median_url": feed['noteCard']['cover']['urlDefault'],
                'user_id': feed['noteCard']['user']['userId'],
                'user_name': feed['noteCard']['user']['nickName'],
                'user_xsec_token': feed['noteCard']['user']['xsecToken'],
            }
            posts.append(post)
        posts = pd.DataFrame(posts)
        self.note_index = posts.shape[0]
        return posts

    def more(self, n):
        """
        After initialized the information thread, get more posts.
        :param n: The number of more posts to get.
        :return: pd.DataFrame table of posts' meta.
        """
        if not (self.initial_timestamp and self.note_index):
            logging.error("Run Feed.init function first.")
            return
        payload = {
            "category": "homefeed_recommend",
            "cursor_score": self.cursor_score,
            "image_formats": ["jpg", "webp", "avif"],
            "need_num": n - 25,
            "note_index": self.note_index,
            "num": n,
            "refresh_type": self.refresh_type,
            "search_key": "",
            "unread_begin_note_id": "",
            "unread_end_note_id": "",
            "unread_note_count": 0,
            "need_filter_image": False,
        }
        payload_str = json.dumps(payload, separators=(',', ':'))
        logging.info(f"POST --URL /api/sns/web/v1/homefeed --Payload {payload_str}")
        current_timestamp = round(time.time() * 1000)
        sc = round((current_timestamp - self.initial_timestamp) / 30000)
        x_t = str(current_timestamp)
        x_b3_trace_id = x_b3_traceid()
        x_s = encrypt_xs(
            url="/api/sns/web/v1/homefeed" + payload_str,
            a1=self.cookies['a1'],
            ts=x_t,
            platform=self.cookies['xsecappid'],
        )
        x_s_common = encrypt_xsc(
            xs=x_s,
            xt=x_t,
            platform=self.cookies['xsecappid'],
            a1=self.cookies['a1'],
            x4=self.cookies['webBuild'],
            sc=sc,
        )
        self.header['content-length'] = str(len(payload_str))
        self.header['x-b3-traceid'] = x_b3_trace_id
        self.header['x-s'] = x_s
        self.header['x-s-common'] = x_s_common
        self.header['x-t'] = x_t
        self.header['x-xray-traceid'] = x_xray_traceid(x_b3_trace_id)
        response = self.session.post(
            url="https://edith.xiaohongshu.com/api/sns/web/v1/homefeed",
            data=payload_str,
            cookies=self.cookies,
            headers=self.header,
        )
        assert response.status_code == 200, "Fail to fetch subsequent xiaohongshu thread."
        self.refresh_type = 3
        self.note_index += n
        response_json = response.json()
        assert response_json['success'] == True, (f"Fail to fetch, website's message: "
                                                  f"{response_json['msg']}.")
        self.cursor_score = response_json['data']['cursor_score']
        posts = []
        for item in response_json['data']['items']:
            post = {
                'id': item['id'],
                'xsec_token': item['xsec_token'],
                'title': item['note_card'].get('display_title', ''),
                'cover_median_url': item['note_card']['cover']['url_default'],
                'user_id': item['note_card']['user']['user_id'],
                'user_name': item['note_card']['user']['nick_name'],
                'user_xsec_token': item['note_card']['user']['xsec_token'],
            }
            posts.append(post)
        posts = pd.DataFrame(posts)
        return posts


class Search:
    def __init__(self, cookies: dict, keyword: str):
        self.session = Session()
        self.cookies = cookies
        self.header = header_homefeed.copy()
        self.keyword = keyword
        self.initial_timestamp = round(time.time() * 1000)
        self.has_more = True
        self.page = 1

    def more(self):
        empty_df = pd.DataFrame(columns=['id', 'xsec_token', 'title', 'cover_median_url',
                                         'user_id', 'user_name', 'user_xsec_token'])
        if self.has_more is False:
            logging.info(f"The current page is {self.page} and no more searching results.")
            return empty_df
        current_timestamp = round(time.time() * 1000)
        payload = {
            "ext_flags": [],
            "image_formats": ["jpg", "webp", "avif"],
            "keyword": self.keyword,
            "note_type": 0,
            "page": self.page,
            "page_size": 20,
            "search_id": search_id(current_timestamp),
            "sort": "general",
        }
        payload_str = json.dumps(payload, separators=(',', ':'))
        logging.info(f"POST --URL /api/sns/web/v1/search/notes --Payload {payload_str}")

        # Build the header
        sc = round((current_timestamp - self.initial_timestamp) / 30000)
        x_t = str(current_timestamp)
        x_b3_trace_id = x_b3_traceid()
        x_s = encrypt_xs(
            url="/api/sns/web/v1/search/notes" + payload_str,
            a1=self.cookies['a1'],
            ts=x_t,
            platform=self.cookies['xsecappid'],
        )
        x_s_common = encrypt_xsc(
            xs=x_s,
            xt=x_t,
            platform=self.cookies['xsecappid'],
            a1=self.cookies['a1'],
            x4=self.cookies['webBuild'],
            sc=sc,
        )
        self.header['content-length'] = str(len(payload_str))
        self.header['x-b3-traceid'] = x_b3_trace_id
        self.header['x-s'] = x_s
        self.header['x-s-common'] = x_s_common
        self.header['x-t'] = x_t
        self.header['x-xray-traceid'] = x_xray_traceid(x_b3_trace_id)
        response = self.session.post(
            url="https://edith.xiaohongshu.com/api/sns/web/v1/search/notes",
            data=payload_str,
            cookies=self.cookies,
            headers=self.header,
        )
        assert response.status_code == 200, "Fail to fetch subsequent xiaohongshu thread."
        response_json = response.json()
        assert response_json['success'] == True, (f"Fail to fetch, website's message: "
                                                  f"{response_json['msg']}.")
        if 'items' not in response_json['data'].keys():
            logging.info(f"The current page is {self.page} and no more searching results.")
            return empty_df
        posts = []
        for item in response_json['data']['items']:
            if not item['model_type'] == 'note':
                continue
            post = {
                'id': item['id'],
                'xsec_token': item['xsec_token'],
                # no title is possible
                'title': item['note_card'].get('display_title', ''),
                'cover_median_url': item['note_card']['cover']['url_default'],
                'user_id': item['note_card']['user']['user_id'],
                'user_name': item['note_card']['user']['nick_name'],
                'user_xsec_token': item['note_card']['user']['xsec_token'],
            }
            posts.append(post)
        posts = pd.DataFrame(posts)
        self.has_more = response_json['data']['has_more']
        self.page += 1
        return posts


class Detail:
    def __init__(self, cookies: dict):
        self.session = Session()
        self.cookies = cookies
        self.header = header_explore

    def get(self, id_: str, xsec_token: str):
        url = f"https://www.xiaohongshu.com/explore/{id_}?xsec_token={xsec_token}"
        response = self.session.get(url, cookies=self.cookies, headers=self.header)
        assert response.status_code == 200, \
            f"Fail to fetch the post's detail from xiaohongshu. URL: {url}"
        logging.info(f"GET --URL {url}")
        tree = BeautifulSoup(response.text, "html.parser")
        images = [
            image.get('content')
            for image in tree.find_all('meta', {'name': 'og:image'})
        ]
        description_node = tree.find('meta', {'name': 'description'})
        description = description_node.get('content') if description_node else ''
        title_node = tree.find('div', {'id': 'detail-title'})
        title = title_node.text if title_node else ''
        topic_node = tree.find('meta', {'name': 'keywords'})
        labels = topic_node.get('content') if topic_node else ''
        labels = [s.strip() for s in labels.split(',')]
        return {
            "title": title,
            "description": description,
            "images": images,
            "labels": labels,
        }
