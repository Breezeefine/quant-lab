import json
import os
import time

# Reduce proxy/DNS interference for this probe.
for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ.pop(key, None)

results = []


def record(name, ok, detail):
    results.append({"name": name, "ok": ok, "detail": detail})
    print(f"[{'OK' if ok else 'FAIL'}] {name}: {detail}")


import akshare as ak
record("akshare_version", True, getattr(ak, "__version__", "unknown"))

dates = ["20260529", "20260601"]
for probe_date in dates:
    probes = [
        (f"stock_zt_pool_em[{probe_date}]", lambda d=probe_date: ak.stock_zt_pool_em(date=d)),
        (f"stock_zt_pool_zbgc_em[{probe_date}]", lambda d=probe_date: ak.stock_zt_pool_zbgc_em(date=d)),
        (f"stock_zt_pool_dtgc_em[{probe_date}]", lambda d=probe_date: ak.stock_zt_pool_dtgc_em(date=d)),
        (f"stock_lhb_detail_em[{probe_date}]", lambda d=probe_date: ak.stock_lhb_detail_em(start_date=d, end_date=d)),
    ]
    for name, func in probes:
        start = time.time()
        try:
            df = func()
            record(name, True, f"rows={len(df)}, cols={list(df.columns)[:10]}, elapsed={round(time.time() - start, 2)}s")
        except Exception as e:
            record(name, False, f"{type(e).__name__}: {e}; elapsed={round(time.time() - start, 2)}s")

for indicator in ["今日", "5日", "10日"]:
    start = time.time()
    try:
        df = ak.stock_sector_fund_flow_rank(indicator=indicator)
        record(f"stock_sector_fund_flow_rank[{indicator}]", True, f"rows={len(df)}, cols={list(df.columns)[:10]}, elapsed={round(time.time() - start, 2)}s")
    except Exception as e:
        record(f"stock_sector_fund_flow_rank[{indicator}]", False, f"{type(e).__name__}: {e}; elapsed={round(time.time() - start, 2)}s")

print("JSON_RESULT=" + json.dumps(results, ensure_ascii=False))
