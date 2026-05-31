import json
import math
import os
import time

for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ.pop(key, None)

results = []


def record(name, ok, detail):
    results.append({"name": name, "ok": ok, "detail": detail})
    print(f"[{'OK' if ok else 'FAIL'}] {name}: {detail}")


url = "https://push2.eastmoney.com/api/qt/clist/get"
params = {
    "pn": "1",
    "pz": "100",
    "po": "1",
    "np": "1",
    "ut": "b2884a393a59ad64002292a3e90d46a5",
    "fltt": "2",
    "invt": "2",
    "fid0": "f62",
    "fs": "m:90 t:2",
    "stat": "1",
    "fields": "f12,f14,f2,f3,f62,f184,f66,f69,f72,f75,f78,f81,f84,f87,f204,f205,f124",
    "rt": "52975239",
    "_": int(time.time() * 1000),
}
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Referer": "https://data.eastmoney.com/bkzj/hy.html",
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

import requests
for mode in ["requests_no_headers", "requests_headers", "requests_session_headers"]:
    start = time.time()
    try:
        if mode == "requests_no_headers":
            r = requests.get(url, params=params, timeout=15)
        elif mode == "requests_headers":
            r = requests.get(url, params=params, headers=headers, timeout=15)
        else:
            s = requests.Session()
            s.trust_env = False
            s.headers.update(headers)
            r = s.get(url, params=params, timeout=15)
        data = r.json()
        total = data.get("data", {}).get("total") if isinstance(data.get("data"), dict) else None
        diff_len = len(data.get("data", {}).get("diff", [])) if isinstance(data.get("data"), dict) else None
        record(mode, r.ok and total is not None, f"status={r.status_code}, total={total}, diff_len={diff_len}, elapsed={round(time.time()-start,2)}s")
    except Exception as e:
        record(mode, False, f"{type(e).__name__}: {e}; elapsed={round(time.time()-start,2)}s")

try:
    from curl_cffi import requests as crequests
    start = time.time()
    s = crequests.Session(impersonate="chrome")
    s.headers.update(headers)
    r = s.get(url, params=params, timeout=15)
    data = r.json()
    total = data.get("data", {}).get("total") if isinstance(data.get("data"), dict) else None
    diff_len = len(data.get("data", {}).get("diff", [])) if isinstance(data.get("data"), dict) else None
    record("curl_cffi_headers", r.ok and total is not None, f"status={r.status_code}, total={total}, diff_len={diff_len}, elapsed={round(time.time()-start,2)}s")
except Exception as e:
    record("curl_cffi_headers", False, f"{type(e).__name__}: {e}")

print("JSON_RESULT=" + json.dumps(results, ensure_ascii=False))
