import base64
import hashlib
import json
import struct
from itertools import zip_longest

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

from xhshow.config import xn, xn64


def encrypt_md5(url: str) -> str:
    """
    根据传入的url和params生成MD5摘要
    
    Args:
        url: API的url
    Returns:
        MD5摘要
    """
    md5_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    return md5_hash


def encrypt_text(text: str) -> str:
    """
    根据传入的text生成AES加密后的内容，并将其转为base64编码

    Args:
        text: 需要加密的字符串
    Returns:
        加密后的base64编码字符串
    """
    text_encoded = base64.b64encode(text.encode())
    key_bytes = b''.join(struct.pack('>I', word)
                         for word in [929260340, 1633971297, 895580464, 925905270])
    iv = b'4uzjr7mbsibcaldp'
    cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(text_encoded, AES.block_size))
    ciphertext_base64 = base64.b64encode(ciphertext).decode()
    return ciphertext_base64


def base64_to_hex(encoded_data):
    """
    把加密后的payload转为16进制

    Args:
        encoded_data: 加密后的payload
    Returns:

    """
    decoded_data = base64.b64decode(encoded_data)
    hex_string = ''.join([format(byte, '02x') for byte in decoded_data])
    return hex_string



def encrypt_payload(payload: str, platform: str) -> str:
    """
    把小红书加密参数payload转16进制 再使用base64编码

    Args:
        payload: 要加密处理的payload内容
        platform: 登录平台
    Returns:
        加密后并进行base64编码的字符串
    """
    obj = {
        "signSvn": "56",
        "signType": "x2",
        "appId": platform,
        "signVersion": "1",
        "payload": base64_to_hex(payload)
    }
    return base64.b64encode(json.dumps(obj, separators=(',', ':')).encode()).decode()



def encrypt_xs(url: str, a1: str, ts: str, platform: str) -> str:
    """
    将传入的参数加密为小红书的xs

    Args: url: API请求的URL
        a1: 签名参数a1
        ts: 时间戳
        platform: 登录平台 默认为xhs-pc-web
    Returns:
        最终的加密签名字符串，前缀为“XYW_”
    """
    text = (f'x1={encrypt_md5(url="url="+url)};'
            f'x2=0|0|0|1|0|0|1|0|0|0|1|0|0|0|0|1|0|0|0;'
            f'x3={a1};'
            f'x4={ts};')
    return 'XYW_' + encrypt_payload(encrypt_text(text), platform=platform)



def encrypt_sign(ts: str, payload: dict) -> str:
    """
    小红书验证码签名
    Args:
        ts: xt
        payload: 请求参数
    Returns:
        加密后的字符串
    """
    url = f"{ts}test/api/redcaptcha/v2/captcha/register{json.dumps(
        payload, separators=(',', ':'), ensure_ascii=False)}"

    result = ''
    md5_ascii = [ord(char) for char in encrypt_md5(url)]
    chunks = zip_longest(md5_ascii[::3], md5_ascii[1::3], md5_ascii[2::3], fillvalue=0)

    for u, c, s in chunks:
        l = u >> 2
        f = ((u & 3) << 4) | (c >> 4)
        p = ((c & 15) << 2) | (s >> 6) if c else 64
        d = s & 63 if s else 64

        result += xn[l] + xn[f] + (xn[p] if p < 64 else xn64) + (xn[d] if d < 64 else xn64)
    return result


if __name__ == '__main__':
    x_s = encrypt_xs(
        url='/api/sns/web/v1/homefeed{"cursor_score":"","num":39,"refresh_type":1,"note_'
            'index":35,"unread_begin_note_id":"","unread_end_note_id":"","unread_note_co'
            'unt":0,"category":"homefeed_recommend","search_key":"","need_num":14,"image'
            '_formats":["jpg","webp","avif"],"need_filter_image":false}',
        a1='1947369ced9g07o90xrwmhqzjfzpsgrlfc20baiaj50000474757',
        ts='1738852912404',
        platform='xhs-pc-web'
    )
    print(x_s)
    answer = ("XYW_eyJzaWduU3ZuIjoiNTYiLCJzaWduVHlwZSI6IngyIiwiYXBwSWQiOiJ4aHMtcGMtd2ViIiw"
              "ic2lnblZlcnNpb24iOiIxIiwicGF5bG9hZCI6IjA2NTkyNDhhMTdmMTk1OGY5YmM0MGI5MTcxZ"
              "DgxZGQ4YzIxNjBhNTI4YzU5NDhjNTJlOGI2Y2ZjZDFiNmJhZmRhNjJiMjBjY2I4YzM1NjJkZTN"
              "lNzg3NmI1ZTI0YTcyZWIyY2U2MTg5ZGE2ZTY4MzRlZmRmMzIxY2M0MzEwZWE2NWI2NzAwMTEzM"
              "zIwMDZhMDc0ZTI4NWY2YTg0ZWE2NmIyYzBhZmE0MDJjNzZmZDUzZDYxOWRkYjJlMTA0ZmFmNWNm"
              "NGI1N2Q4YzhkNzMxZDMwNTNmMTlhNWM1YzI0Mjc4ZWUyZTAwMGQyY2RiNTYyOWE3ZDI2NjRmZTI"
              "1ZDA5ZjliYmQ0Yjg0ZjU0ODg3ZjYyNGZmM2RhNGVhOTJmMDIzMGI1OTAyYzU3M2JlMjM5M2NhO"
              "GQ0ZDhlNGFmNzBiYWNhYzQ1YjIwNTkyMDA1Y2NkMzRiMzY2N2RhZDk5N2M5ZmExMGVjYTg4ODU"
              "1OTNkMjFhZjJmYjI3M2I5NGM5YTdhZmYxMjU0YjY4YzVkNDU1NjZhYTIyNmUyNDIwNmJjNGRmI"
              "n0=")
    print(answer)
    assert x_s == answer
