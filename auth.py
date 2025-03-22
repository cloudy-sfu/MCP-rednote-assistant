import os
import time

import pandas as pd


def dump_cookies(cookies_dict, output_path):
    cookies = pd.DataFrame(cookies_dict['cookies'])
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cookies.to_csv(output_path, index=False)


def load_cookies(cookies_path):
    cookies = pd.read_csv(cookies_path)
    cookies = {row['name']: row['value'] for _, row in cookies.iterrows()}
    return cookies


def check_cookies(cookies_path):
    if not os.path.isfile(cookies_path):
        return False
    cookies = pd.read_csv(cookies_path)
    expiry_datetime = cookies['expirationDate'].min() + 86400
    if time.time() > expiry_datetime:  # np.False_ is not False
        return False
    return True
