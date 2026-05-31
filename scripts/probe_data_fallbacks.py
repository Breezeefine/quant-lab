import json
import os
import time

for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ.pop(key, None)

import akshare as ak

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


run_df("sector_theme_fallback", "stock_board_industry_name_ths", ak.stock_board_industry_name_ths)
run_df("sector_theme_fallback", "stock_board_concept_name_ths", ak.stock_board_concept_name_ths)
run_df("sector_theme_fallback", "stock_board_industry_summary_ths", ak.stock_board_industry_summary_ths)
run_df("sector_theme_fallback", "stock_board_concept_summary_ths", ak.stock_board_concept_summary_ths)
run_df("sector_theme_fallback", "stock_board_industry_info_ths[半导体]", lambda: ak.stock_board_industry_info_ths(symbol="半导体"))
run_df("sector_theme_fallback", "stock_board_concept_info_ths[人工智能]", lambda: ak.stock_board_concept_info_ths(symbol="人工智能"))

run_df("text_fallback", "stock_news_main_cx", ak.stock_news_main_cx)
run_df("text_fallback", "stock_individual_notice_report[600000]", lambda: ak.stock_individual_notice_report(security="600000", symbol="全部", begin_date="20260501", end_date="20260601"))
run_df("text_fallback", "news_cctv", lambda: ak.news_cctv(date="20260529"))
run_df("text_fallback", "news_economic_baidu", lambda: ak.news_economic_baidu(date="20260601"))

print("JSON_RESULT=" + json.dumps(RESULTS, ensure_ascii=False))
