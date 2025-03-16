import json
import os
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import pandas as pd

Tk().withdraw()


def dump_cookies(output_path):
    cookies_path = askopenfilename(
        title="Select \"xiaohongshu.com\" cookies file",
        initialdir=r"C:\Users\%USERNAME%\Downloads",
        filetypes=[("J2TEAMS Cookies File", ".json")],
    )
    with open(cookies_path) as f:
        cookies_dict = json.load(f)
    cookies = pd.DataFrame(cookies_dict['cookies'])
    cookies.to_csv(output_path, index=False)


def load_cookies(cookies_path):
    cookies = pd.read_csv(cookies_path)
    cookies = {row['name']: row['value'] for _, row in cookies.iterrows()}
    return cookies


def check_cookies_expiry(cookies_path):
    if not os.path.isfile(cookies_path):
        return False
    cookies = pd.read_csv(cookies_path)
    if time.time() > cookies['expirationDate'].min():  # np.False_ is not False
        return False
    return True
