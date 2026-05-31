import json
import os
import time
from datetime import date

for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ.pop(key, None)

import akshare as ak
import requests

RESULTS = []


def record(category, name, ok, detail):
    RESULTS.append({"category": category, "name": name, "ok": ok, "detail": detail})
    print(f"[{'OK' if ok else 'FAIL'}] {category} / {name}: {detail}")


def run_df(category, name, func):
    start = time.time()
    try:
        df = func()
        rows = len(df)
        cols = list(df.columns)[:10]
        ok = rows > 0
        record(category, name, ok, f"rows={rows}, cols={cols}, elapsed={round(time.time() - start, 2)}s")
    except Exception as e:
        record(category, name, False, f"{type(e).__name__}: {e}; elapsed={round(time.time() - start, 2)}s")


print(f"AKShare={getattr(ak, '__version__', 'unknown')}")
probe_date = "20260529"
today = "20260601"

# 1. Limit-up ecosystem
run_df("limit_ecosystem", "stock_zt_pool_em", lambda: ak.stock_zt_pool_em(date=probe_date))
run_df("limit_ecosystem", "stock_zt_pool_zbgc_em", lambda: ak.stock_zt_pool_zbgc_em(date=probe_date))
run_df("limit_ecosystem", "stock_zt_pool_dtgc_em", lambda: ak.stock_zt_pool_dtgc_em(date=probe_date))
run_df("limit_ecosystem", "stock_zt_pool_previous_em", lambda: ak.stock_zt_pool_previous_em(date=probe_date))
run_df("limit_ecosystem", "stock_zt_pool_strong_em", lambda: ak.stock_zt_pool_strong_em(date=probe_date))

# 2. Dragon tiger list
run_df("dragon_tiger", "stock_lhb_detail_em", lambda: ak.stock_lhb_detail_em(start_date=probe_date, end_date=probe_date))
run_df("dragon_tiger", "stock_lhb_detail_daily_sina", lambda: ak.stock_lhb_detail_daily_sina(date=probe_date))

# 3. Sector/theme and flow alternatives
run_df("sector_theme", "stock_board_industry_name_em", ak.stock_board_industry_name_em)
run_df("sector_theme", "stock_board_concept_name_em", ak.stock_board_concept_name_em)
run_df("sector_theme", "stock_board_change_em", ak.stock_board_change_em)
run_df("sector_flow", "stock_sector_fund_flow_rank", lambda: ak.stock_sector_fund_flow_rank(indicator="今日"))
run_df("sector_flow", "stock_sector_fund_flow_hist", lambda: ak.stock_sector_fund_flow_hist(symbol="汽车服务"))
run_df("sector_flow", "stock_sector_fund_flow_summary", lambda: ak.stock_sector_fund_flow_summary(symbol="汽车服务", indicator="今日"))

# 4. Popularity/social proxies
run_df("hot_social", "stock_hot_rank_em", ak.stock_hot_rank_em)
run_df("hot_social", "stock_hot_search_baidu", lambda: ak.stock_hot_search_baidu(symbol="A股", date=today, time="今日"))
run_df("hot_social", "stock_js_weibo_report", ak.stock_js_weibo_report)

# 5. News/announcements/research
run_df("text_inputs", "stock_news_em", lambda: ak.stock_news_em(symbol="600000"))
run_df("text_inputs", "stock_notice_report", lambda: ak.stock_notice_report(symbol="全部", date=today))
run_df("text_inputs", "stock_research_report_em", lambda: ak.stock_research_report_em(symbol="600000"))

# 6. Northbound funds
run_df("northbound", "stock_hsgt_fund_flow_summary_em", ak.stock_hsgt_fund_flow_summary_em)
run_df("northbound", "stock_hsgt_hist_em", ak.stock_hsgt_hist_em)

# 7. Real-time quote via Tencent
start = time.time()
try:
    r = requests.get("http://qt.gtimg.cn/q=sh600000", timeout=10)
    ok = r.status_code == 200 and "v_sh600000" in r.text
    record("realtime_quote", "tencent_qt_gtimg", ok, f"status={r.status_code}, len={len(r.text)}, elapsed={round(time.time() - start, 2)}s, head={r.text[:80]!r}")
except Exception as e:
    record("realtime_quote", "tencent_qt_gtimg", False, f"{type(e).__name__}: {e}; elapsed={round(time.time() - start, 2)}s")

print("JSON_RESULT=" + json.dumps(RESULTS, ensure_ascii=False))
