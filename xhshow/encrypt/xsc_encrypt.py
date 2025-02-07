import functools
import json

from xhshow.config import ie, lookup, version_x1
from xhshow.encrypt.misc_encrypt import b64_encode, encode_utf8


def triplet_to_base64(e) -> str:
    """
    将24位整数分成4个6位部分 转换为Base64字符串
    Args:
        e: 需要转换的整数
    Returns:
        Base64字符串
    """
    return (lookup[(e >> 18) & 63] + lookup[(e >> 12) & 63] +
            lookup[(e >> 6) & 63] + lookup[e & 63])


def encode_chunk(e, t, r) -> str:
    """
    将编码后的整数列表分成3字节一组转换为Base64
    Args:
        e: 整数列表
        t: 开始位置
        r: 结束位置
    Returns:
        编码后的Base64字符串
    """
    chunks = []
    for b in range(t, r, 3):
        if b + 2 < len(e):  # 确保有完整的三个字节
            chunk = triplet_to_base64((e[b] << 16) + (e[b + 1] << 8) + e[b + 2])
            chunks.append(chunk)
    return ''.join(chunks)


def mrc(e) -> int:
    """
    使用自定义CRC算法生成校验值
    Args:
        e: 输入字符串
    Returns:
        32位整数校验值
    """
    o = -1

    def unsigned_right_shift(r, n=8):
        return (r + (1 << 32)) >> n & 0xFFFFFFFF if r < 0 else (r >> n) & 0xFFFFFFFF

    def to_js_int(num):
        return (num + 2 ** 31) % 2 ** 32 - 2 ** 31

    for char in e:
        o = to_js_int(ie[(o & 255) ^ ord(char)] ^ unsigned_right_shift(o, 8))
    return to_js_int(~o ^ 3988292384)


def get_b1(ts: str):
    fake_browser_env = {
        'x33': '0',
        'x34': '0',
        'x35': '0',
        'x36': '3',
        'x37': '0|0|0|0|0|0|0|0|0|1|0|0|0|0|0|0|0|0|1|0|0|0|0|0',
        'x38': "0|0|1|0|1|0|0|0|0|0|1|0|1|0|1|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0",
        'x39': '0',
        'x42': version_x1,
        'x43': 'c12c562c',
        'x44': ts,
        'x45': 'connecterror',
        'x46': 'false',
        'x48': '',
        'x49': '{list:[],type:}',
        'x50': '',
        'x51': '',
        'x52': '[]'
    }
    fake_browser_env = json.dumps(fake_browser_env, separators=(',', ':'))
    return b64_encode(encode_utf8(fake_browser_env))


def encrypt_xsc_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        st = func(*args, **kwargs)
        return b64_encode(encode_utf8(st))
    return wrapper


@encrypt_xsc_decorator
def encrypt_xsc(xs: str, xt: str, platform: str, a1: str, x4: str, sc: int):
    b1 = get_b1(xt)
    x9 = mrc(xt + xs + b1)
    st = json.dumps({
        "s0": 5,
        "s1": "",
        "x0": "1",
        "x1": version_x1,
        "x2": "Windows",
        "x3": platform,
        "x4": x4,  # webBuild version
        "x5": a1,  # Browser feature, in cookies
        "x6": int(xt),  # X-T field
        "x7": xs,  # X-S field
        "x8": b1,
        "x9": x9,
        # sessionStorage.sc, every time fetching unread count, +1
        # restored when close the tab,
        # Reference: https://developer.chrome.com/docs/devtools/storage/localstorage
        "x10": sc,
    }, separators=(",", ":"), ensure_ascii=False)
    return st
