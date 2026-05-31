import json
import os
import time

for key in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ.pop(key, None)

import akshare as ak
import requests

CHECKS = []


def add(name, capability, provider, ok, detail):
    CHECKS.append({
        "name": name,
        "capability": capability,
        "provider": provider,
        "ok": ok,
        "detail": detail,
    })
    print(f"[{'OK' if ok else 'FAIL'}] {capability} / {name} ({provider}): {detail}")


def df_check(name, capability, provider, func):
    start = time.time()
    try:
        df = func()
        rows = len(df)
        cols = list(df.columns)[:8]
        add(name, capability, provider, rows > 0, f"rows={rows}, cols={cols}, elapsed={round(time.time()-start, 2)}s")
    except Exception as e:
        add(name, capability, provider, False, f"{type(e).__name__}: {e}; elapsed={round(time.time()-start, 2)}s")


probe_date = "20260529"

# Machine tasks: scan + leader/sentiment inputs.
df_check("涨停池", "涨停生态", "AKShare/EastMoney", lambda: ak.stock_zt_pool_em(date=probe_date))
df_check("炸板池", "涨停生态", "AKShare/EastMoney", lambda: ak.stock_zt_pool_zbgc_em(date=probe_date))
df_check("跌停池", "涨停生态", "AKShare/EastMoney", lambda: ak.stock_zt_pool_dtgc_em(date=probe_date))
df_check("昨日涨停池", "涨停生态", "AKShare/EastMoney", lambda: ak.stock_zt_pool_previous_em(date=probe_date))
df_check("强势股池", "涨停生态", "AKShare/EastMoney", lambda: ak.stock_zt_pool_strong_em(date=probe_date))

df_check("龙虎榜-东方财富", "龙虎榜", "AKShare/EastMoney", lambda: ak.stock_lhb_detail_em(start_date=probe_date, end_date=probe_date))
df_check("龙虎榜-新浪", "龙虎榜", "AKShare/Sina", lambda: ak.stock_lhb_detail_daily_sina(date=probe_date))

# Sector/theme: EastMoney names fail locally, THS fallback works.
df_check("同花顺行业列表", "题材/板块", "AKShare/THS", ak.stock_board_industry_name_ths)
df_check("同花顺概念列表", "题材/板块", "AKShare/THS", ak.stock_board_concept_name_ths)
df_check("同花顺行业摘要", "板块强度/资金替代", "AKShare/THS", ak.stock_board_industry_summary_ths)
df_check("同花顺概念摘要", "题材驱动事件", "AKShare/THS", ak.stock_board_concept_summary_ths)
df_check("东方财富板块异动", "板块异动/主力净流入替代", "AKShare/EastMoney", ak.stock_board_change_em)

# Social/hotness.
df_check("东方财富人气榜", "社交/热度", "AKShare/EastMoney", ak.stock_hot_rank_em)
df_check("百度热搜股票", "社交/热度", "AKShare/Baidu", lambda: ak.stock_hot_search_baidu(symbol="A股", date="20260601", time="今日"))
df_check("微博股票报告", "社交/热度", "AKShare/Weibo", ak.stock_js_weibo_report)

# Text inputs.
df_check("财新资讯", "新闻", "AKShare/Caixin", ak.stock_news_main_cx)
df_check("全市场公告", "公告", "AKShare/EastMoney", lambda: ak.stock_notice_report(symbol="全部", date="20260601"))
df_check("个股公告", "公告", "AKShare/EastMoney", lambda: ak.stock_individual_notice_report(security="600000", symbol="全部", begin_date="20260501", end_date="20260601"))
df_check("个股研报", "研报", "AKShare/EastMoney", lambda: ak.stock_research_report_em(symbol="600000"))
df_check("新闻联播", "宏观新闻", "AKShare/CCTV", lambda: ak.news_cctv(date="20260529"))

# Northbound.
df_check("沪深港通资金流摘要", "北向资金", "AKShare/EastMoney", ak.stock_hsgt_fund_flow_summary_em)
df_check("沪深港通历史", "北向资金", "AKShare/EastMoney", ak.stock_hsgt_hist_em)

# Realtime quote.
start = time.time()
try:
    r = requests.get("http://qt.gtimg.cn/q=sh600000", timeout=10)
    ok = r.status_code == 200 and "v_sh600000" in r.text
    add("腾讯实时行情", "实时行情", "Tencent", ok, f"status={r.status_code}, len={len(r.text)}, elapsed={round(time.time()-start, 2)}s")
except Exception as e:
    add("腾讯实时行情", "实时行情", "Tencent", False, f"{type(e).__name__}: {e}; elapsed={round(time.time()-start, 2)}s")

required_capabilities = {
    "涨停生态",
    "龙虎榜",
    "题材/板块",
    "板块强度/资金替代",
    "题材驱动事件",
    "板块异动/主力净流入替代",
    "社交/热度",
    "新闻",
    "公告",
    "研报",
    "宏观新闻",
    "北向资金",
    "实时行情",
}
covered_capabilities = {item["capability"] for item in CHECKS if item["ok"]}
missing_capabilities = sorted(required_capabilities - covered_capabilities)
failed_optional = [item for item in CHECKS if not item["ok"]]
summary = {
    "total_checks": len(CHECKS),
    "passed_checks": len(CHECKS) - len(failed_optional),
    "failed_optional_checks": len(failed_optional),
    "required_capabilities": sorted(required_capabilities),
    "covered_capabilities": sorted(covered_capabilities),
    "missing_capabilities": missing_capabilities,
    "failed_optional_items": failed_optional,
}
print("SUMMARY=" + json.dumps(summary, ensure_ascii=False))
if missing_capabilities:
    raise SystemExit(1)
