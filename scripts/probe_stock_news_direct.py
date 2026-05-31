import json
import os
import re
import time

for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ.pop(key, None)

import requests

symbol = "600000"
inner_param = {
    "uid": "",
    "keyword": symbol,
    "type": ["cmsArticleWebOld"],
    "client": "web",
    "clientType": "web",
    "clientVersion": "curr",
    "param": {
        "cmsArticleWebOld": {
            "searchScope": "default",
            "sort": "default",
            "pageIndex": 1,
            "pageSize": 10,
            "preTag": "<em>",
            "postTag": "</em>",
        }
    },
}
params = {"cb": "jQuery35101792940631092459_1764599530165", "param": json.dumps(inner_param, ensure_ascii=False), "_": str(int(time.time() * 1000))}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": f"https://so.eastmoney.com/news/s?keyword={symbol}",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

start = time.time()
try:
    response = requests.get("https://search-api-web.eastmoney.com/search/jsonp", params=params, headers=headers, timeout=15)
    text = response.text.strip()
    match = re.match(r"^[^(]+\((.*)\)\s*;?$", text, re.S)
    payload = match.group(1) if match else text
    data = json.loads(payload)
    result = data.get("result", {})
    print(f"status={response.status_code}, elapsed={round(time.time()-start, 2)}s, result_keys={list(result.keys())}")
    for key, value in result.items():
        if isinstance(value, list):
            print(f"{key}: rows={len(value)}, sample_keys={list(value[0].keys())[:8] if value else []}")
    articles = result.get("cmsArticleWebOld", [])
    ok = len(articles) > 0
    print(f"{'OK' if ok else 'FAIL'} eastmoney_stock_news_direct rows={len(articles)}")
except Exception as e:
    print(f"FAIL {type(e).__name__}: {e}")
