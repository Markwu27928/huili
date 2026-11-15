#!/usr/bin/env python3
"""
永豐金-匯立（9A81）分點進出每日整理

每次執行：
  1. 抓取 MoneyDJ 系統「分點明細」頁（近一日，金額＋張數）
  2. 存成 data/9A81/YYYYMMDD.csv（同一資料日期已存在就略過，假日不會重複）
  3. 依累積歷史資料產生 reports/YYYY-MM-DD.md 與 reports/latest.md

用法：
  python huili_tracker.py          # 一般執行
  python huili_tracker.py --force  # 同日資料已存在也重抓覆蓋
"""
from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

import requests

BRANCH_NAME = "永豐金-匯立"
BROKER = "9A00"
BRANCH = "9A81"
BRANCH_HEX = "".join(f"{ord(c):04X}" for c in BRANCH)  # 0039004100380031

# 同一套 DJ 系統的多個鏡像站，第一個失敗就換下一個
HOSTS = [
    "https://fubon-ebrokerdj.fbs.com.tw",
    "https://5850web.moneydj.com",
    "https://concords.moneydj.com",
    "https://stockchannelnew.sinotrade.com.tw",
    "https://jsjustweb.jihsun.com.tw",
]
PAGE_PATH = "/z/zg/zgb/zgb0.djhtm"
UNITS_PARAM = "&c=B"  # 張數模式

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / BRANCH
REPORT_DIR = ROOT / "reports"

TOP_N = 20          # 報告中買超、賣超各列幾檔
CUM_DAYS = 5        # 累計天數
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/129.0 Safari/537.36"
    )
}
FIELDS = ["date", "code", "name", "buy_amt", "sell_amt", "diff_amt",
          "buy_lots", "sell_lots", "diff_lots"]

RE_DATE = re.compile(r"資料日期[：:]\s*(\d{8})")
RE_GENLINK = re.compile(
    r"GenLink2stk\(\s*'[A-Za-z]*([0-9][0-9A-Za-z]*)'\s*,\s*'([^']*)'\s*\)")
RE_LINK = re.compile(
    r"Link2Stk\(\s*'([0-9][0-9A-Za-z]*)'\s*\)[^>]*>\s*([^<]*?)\s*<", re.I)
RE_NUM_TD = re.compile(r"<td[^>]*>\s*(-?[\d,]+)\s*</td>", re.I)


# ---------------------------------------------------------------- 抓取與解析
def fetch_page(extra: str = "", session=None) -> tuple[str, str]:
    """依序嘗試各鏡像站，回傳 (html, host)。"""
    s = session or requests
    errors = []
    for host in HOSTS:
        url = f"{host}{PAGE_PATH}?a={BROKER}&b={BRANCH_HEX}{extra}"
        try:
            r = s.get(url, headers=HEADERS, timeout=25)
            r.raise_for_status()
            html = r.content.decode("cp950", errors="replace")
            if "資料日期" in html and ("GenLink2stk" in html or "Link2Stk" in html):
                return html, host
            errors.append(f"{host}：頁面格式不符")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{host}：{e}")
    raise RuntimeError("所有來源都抓取失敗：\n  " + "\n  ".join(errors))


def parse_page(html: str) -> tuple[str, list[dict]]:
    """回傳 (資料日期 YYYYMMDD, 各股列表)。數值單位依頁面（仟元或張）。"""
    m = RE_DATE.search(html)
    if not m:
        raise ValueError("找不到資料日期")
    date = m.group(1)

    rows, seen = [], set()
    for chunk in re.split(r"</tr>", html, flags=re.I):
        stock = None
        g = RE_GENLINK.search(chunk)
        if g:
            stock = (g.group(1), g.group(2).strip())
        else:
            l = RE_LINK.search(chunk)
            if l:
                code, name = l.group(1), l.group(2).strip()
                if name.startswith(code):
                    name = name[len(code):].strip()
                stock = (code, name)
        if not stock or stock[0] in seen:
            continue
        nums = [int(x.replace(",", "")) for x in RE_NUM_TD.findall(chunk)]
        if len(nums) < 3:
            continue
        buy, sell, diff = nums[-3:]
        if buy - sell != diff or diff == 0:   # 檢核：買進－賣出＝差額
            continue
        seen.add(stock[0])
        rows.append({"code": stock[0], "name": stock[1],
                     "buy": buy, "sell": sell, "diff": diff})
    if not rows:
        raise ValueError("頁面中沒有解析到任何個股")
    return date, rows


def collect(session=None) -> tuple[str, list[dict], str, bool]:
    """抓金額與張數並合併。回傳 (日期, 列表, 來源, 是否含張數)。"""
    html, host = fetch_page("", session)
    date, amt_rows = parse_page(html)

    lots = {}
    try:
        html_b, _ = fetch_page(UNITS_PARAM, session)
        date_b, lot_rows = parse_page(html_b)
        same_as_amt = all(
            a["code"] == b["code"] and a["diff"] == b["diff"]
            for a, b in zip(amt_rows, lot_rows)
        ) and len(amt_rows) == len(lot_rows)
        if date_b == date and not same_as_amt:
            lots = {r["code"]: r for r in lot_rows}
        else:
            print("⚠ 張數資料異常（與金額頁相同或日期不同），本次只存金額")
    except Exception as e:  # noqa: BLE001
        print(f"⚠ 張數抓取失敗，本次只存金額：{e}")

    out = []
    for r in amt_rows:
        b = lots.get(r["code"])
        out.append({
            "date": date, "code": r["code"], "name": r["name"],
            "buy_amt": r["buy"], "sell_amt": r["sell"], "diff_amt": r["diff"],
            "buy_lots": b["buy"] if b else "",
            "sell_lots": b["sell"] if b else "",
            "diff_lots": b["diff"] if b else "",
        })
    return date, out, host, bool(lots)


# ---------------------------------------------------------------- 存檔與歷史
def save_csv(date: str, rows: list[dict]) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{date}.csv"
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)
    return path


def _int(v):
    return int(v) if str(v).strip() not in ("", "None") else None


def load_history() -> dict[str, dict[str, dict]]:
    """{日期: {代號: 列}}，日期由舊到新。"""
    hist = {}
    for p in sorted(DATA_DIR.glob("*.csv")):
        with p.open(encoding="utf-8-sig") as f:
            day = {}
            for r in csv.DictReader(f):
                for k in FIELDS[3:]:
                    r[k] = _int(r[k])
                day[r["code"]] = r
            hist[p.stem] = day
    return hist


def streak(hist: dict, dates: list[str], code: str, sign: int) -> int:
    """從最新一天往回數，連續同方向（買超或賣超）出現在榜上的天數。"""
    n = 0
    for d in reversed(dates):
        r = hist[d].get(code)
        if r and (r["diff_amt"] > 0) == (sign > 0):
            n += 1
        else:
            break
    return n


def cumulative(hist: dict, dates: list[str], days: int) -> dict[str, dict]:
    recent = dates[-days:]
    acc = {}
    for d in recent:
        for code, r in hist[d].items():
            a = acc.setdefault(code, {"name": r["name"], "diff": 0, "days": 0})
            a["diff"] += r["diff_amt"]
            a["days"] += 1
            a["name"] = r["name"]
    return acc


# ---------------------------------------------------------------- 報告
def wan(x) -> str:
    """仟元 → 萬元字串"""
    return f"{round(x / 10):,}"


def avg_price(amt, lots) -> str:
    if not lots:
        return "—"
    p = amt / lots   # 仟元 ÷ 張 ＝ 元/股
    return f"{p:,.2f}" if p < 100 else f"{p:,.1f}"


def build_report(hist: dict) -> tuple[str, str]:
    dates = sorted(hist)
    today = dates[-1]
    day = hist[today]
    cum = cumulative(hist, dates, CUM_DAYS)
    has_lots = any(r["buy_lots"] is not None for r in day.values())
    d_fmt = f"{today[:4]}-{today[4:6]}-{today[6:]}"

    buys = sorted((r for r in day.values() if r["diff_amt"] > 0),
                  key=lambda r: -r["diff_amt"])
    sells = sorted((r for r in day.values() if r["diff_amt"] < 0),
                   key=lambda r: r["diff_amt"])
    tot_b = sum(r["diff_amt"] for r in buys)
    tot_s = sum(r["diff_amt"] for r in sells)
    n_cum = min(CUM_DAYS, len(dates))

    L = [f"# {BRANCH_NAME}（{BRANCH}）分點進出日報",
         "",
         f"資料日期：{d_fmt}　金額單位：萬元　累積資料：{len(dates)} 個交易日",
         "",
         "## 當日概況",
         "",
         f"- 買超 {len(buys)} 檔，合計 {wan(tot_b)} 萬",
         f"- 賣超 {len(sells)} 檔，合計 {wan(tot_s)} 萬",
         f"- 榜上淨額：{wan(tot_b + tot_s)} 萬（僅含買賣超各前 50 名）",
         ""]

    def table(title, rows, sign):
        price_col = "買進均價" if sign > 0 else "賣出均價"
        head = ["#", "股票", "買進", "賣出", "差額"]
        if has_lots:
            head += ["張數", price_col]
        head += ["連續", f"{n_cum}日累計"]
        out = [f"## {title}（前 {min(TOP_N, len(rows))} 名）", "",
               "| " + " | ".join(head) + " |",
               "|" + "|".join([":-:"] + [":--"] + ["--:"] * (len(head) - 2)) + "|"]
        for i, r in enumerate(rows[:TOP_N], 1):
            cells = [str(i), f"{r['code']} {r['name']}",
                     wan(r["buy_amt"]), wan(r["sell_amt"]), wan(r["diff_amt"])]
            if has_lots:
                lots = r["diff_lots"]
                cells.append(f"{lots:,}" if lots is not None else "—")
                cells.append(avg_price(r["buy_amt"], r["buy_lots"]) if sign > 0
                             else avg_price(r["sell_amt"], r["sell_lots"]))
            s = streak(hist, dates, r["code"], sign)
            cells.append(f"{s}日" if s > 1 else "新")
            cells.append(wan(cum[r["code"]]["diff"]))
            out.append("| " + " | ".join(cells) + " |")
        return out + [""]

    L += table("買超", buys, +1)
    L += table("賣超", sells, -1)

    if len(dates) >= 2:
        ranked = sorted(cum.items(), key=lambda kv: -kv[1]["diff"])
        L += [f"## 近 {n_cum} 日累計", "",
              "| 方向 | 股票 | 累計差額 | 上榜天數 |",
              "|:-:|:--|--:|:-:|"]
        for code, a in [x for x in ranked if x[1]["diff"] > 0][:10]:
            L.append(f"| 買 | {code} {a['name']} | {wan(a['diff'])} | {a['days']} |")
        for code, a in [x for x in reversed(ranked) if x[1]["diff"] < 0][:10]:
            L.append(f"| 賣 | {code} {a['name']} | {wan(a['diff'])} | {a['days']} |")
        L.append("")

    L += ["---",
          "說明：「連續」為連續同方向進榜天數（掉出前 50 名即中斷），「新」表示今日才進榜。"
          "均價＝金額÷張數，為估算值。資料來源：MoneyDJ 券商分點進出。",
          ""]
    return d_fmt, "\n".join(L)


def write_report(hist: dict) -> Path:
    d_fmt, md = build_report(hist)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"{d_fmt}.md"
    path.write_text(md, encoding="utf-8")
    (REPORT_DIR / "latest.md").write_text(md, encoding="utf-8")
    return path


# ---------------------------------------------------------------- 主程式
def main(argv=None, session=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    force = "--force" in argv

    date, rows, host, has_lots = collect(session)
    target = DATA_DIR / f"{date}.csv"
    if target.exists() and not force:
        print(f"資料日期 {date} 已存在，略過（可能是假日或尚未更新）")
        return 0

    save_csv(date, rows)
    report = write_report(load_history())
    print(f"✔ {date}：{len(rows)} 檔（{'含' if has_lots else '不含'}張數），來源 {host}")
    print(f"✔ 報告：{report.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
