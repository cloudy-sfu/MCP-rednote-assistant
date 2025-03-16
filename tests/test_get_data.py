import json
import logging
import sys

import pandas as pd
import pytest

import auth
from get_data import Feed, Search, Detail

logging.basicConfig(level=logging.INFO, format='%(levelname)s | %(message)s',
                    stream=sys.stdout)
cookies_path = "raw/cookies.csv"
if auth.check_cookies_expiry(cookies_path) is False:
    auth.dump_cookies(cookies_path)
cookies = auth.load_cookies(cookies_path)


def test_feed():
    feed = Feed(cookies)
    post_1 = feed.init()
    post_2 = feed.more(15)
    posts = pd.concat([post_1, post_2], axis=0, ignore_index=True)
    posts.to_csv('raw/posts.csv', index=False)


def test_search():
    s = Search(cookies, "ollama")
    post_1 = s.more()
    post_2 = s.more()
    posts = pd.concat([post_1, post_2], axis=0, ignore_index=True)
    posts.to_csv('raw/posts_search.csv', index=False)


def test_detail():
    d = Detail(cookies)
    posts = pd.read_csv('raw/posts_search.csv')
    details = []
    for _, row in posts.iterrows():
        detail = d.get(row['id'], row['xsec_token'])
        details.append(detail)
    with open("raw/details.json", "w") as f:
        json.dump(details, f, indent=4, ensure_ascii=False)


if __name__ == '__main__':
    pytest.main()
