#!/usr/bin/env python3
"""
產生手機網頁（GitHub Pages）：site/index.html、data.json、manifest、圖示
資料來源：data/9A81/*.csv（由 huili_tracker.py 每日累積）
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "9A81"
SITE = ROOT / "site"
KEEP_DAYS = 120  # 網頁保留最近幾個交易日（完整歷史仍在 CSV）
TW = dt.timezone(dt.timedelta(hours=8))


def _int(v):
    v = str(v).strip()
    return int(v) if v not in ("", "None") else None


def build_data() -> dict:
    names, days = {}, []
    for p in sorted(DATA_DIR.glob("*.csv"))[-KEEP_DAYS:]:
        rows = []
        with p.open(encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                names[r["code"]] = r["name"]
                rows.append([r["code"], _int(r["buy_amt"]), _int(r["sell_amt"]),
                             _int(r["buy_lots"]), _int(r["sell_lots"])])
        days.append({"d": p.stem, "r": rows})
    return {
        "branch": "永豐金-匯立", "code": "9A81",
        "generated": dt.datetime.now(TW).strftime("%Y-%m-%dT%H:%M"),
        "names": names, "days": days,
    }


# ---------------------------------------------------------------- 圖示（純標準庫產生 PNG）
def make_icon(size: int) -> bytes:
    bg, red, green, ink = (246, 247, 249), (200, 16, 46), (11, 127, 74), (27, 31, 39)
    cx, half = size * 0.5, size * 0.068
    bars = [(0.30, 0.34, red), (0.50, -0.26, green), (0.70, 0.18, red)]
    axis_w, ay0, ay1 = size * 0.014, size * 0.17, size * 0.83
    raw = bytearray()
    for y in range(size):
        line = [bg] * size
        for yc, ext, col in bars:
            if abs(y - yc * size) <= half:
                x0, x1 = sorted((cx, cx + ext * size))
                for x in range(int(x0), int(x1) + 1):
                    if 0 <= x < size:
                        line[x] = col
        if ay0 <= y <= ay1:
            for x in range(int(cx - axis_w), int(cx + axis_w) + 1):
                line[x] = ink
        raw.append(0)
        for c in line:
            raw.extend(c)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


MANIFEST = {
    "name": "永豐金-匯立 分點進出",
    "short_name": "匯立分點",
    "lang": "zh-Hant-TW",
    "start_url": ".",
    "scope": ".",
    "display": "standalone",
    "background_color": "#F6F7F9",
    "theme_color": "#F6F7F9",
    "icons": [
        {"src": "icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
        {"src": "icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}

INDEX_HTML = r"""<!doctype html>
<html lang="zh-Hant-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#F6F7F9" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#101318" media="(prefers-color-scheme: dark)">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="匯立分點">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="icon" href="icon-192.png">
<link rel="manifest" href="manifest.webmanifest">
<title>永豐金-匯立 分點進出</title>
<style>
:root{
  --bg:#F6F7F9; --surface:#FFFFFF; --ink:#1B1F27; --muted:#69707D; --line:#E2E5EA;
  --up:#C8102E; --up-soft:#FBE6E9; --down:#0B7F4A; --down-soft:#E1F3E9; --focus:#2F6FEB;
  color-scheme:light;
}
@media (prefers-color-scheme: dark){
  :root{
    --bg:#101318; --surface:#181C23; --ink:#E7E9EE; --muted:#9AA1AD; --line:#2A3039;
    --up:#FF5C5C; --up-soft:#3B1D21; --down:#38C47D; --down-soft:#16301F; --focus:#7AA7FF;
    color-scheme:dark;
  }
}
*{box-sizing:border-box}
[hidden]{display:none !important}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--bg); color:var(--ink);
  font-family:-apple-system,"PingFang TC","Noto Sans TC","Microsoft JhengHei",system-ui,sans-serif;
  font-size:16px; line-height:1.45;
  padding-bottom:calc(env(safe-area-inset-bottom,0px) + 28px);
}
button,select,input{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--focus);outline-offset:2px}
.num{font-variant-numeric:tabular-nums}
.wrap{max-width:560px;margin:0 auto;padding:0 16px}

/* 頂部 */
.top{position:sticky;top:0;z-index:5;background:var(--bg);
  padding-top:env(safe-area-inset-top,0px);border-bottom:1px solid var(--line)}
.title-row{display:flex;align-items:center;justify-content:space-between;padding:12px 0 4px}
h1{font-size:19px;margin:0;font-weight:700;letter-spacing:.02em}
h1 .code{font-weight:500;color:var(--muted);font-size:15px;margin-left:6px}
.icon-btn{width:40px;height:40px;border:0;background:transparent;border-radius:10px;
  display:grid;place-items:center;cursor:pointer}
.icon-btn:active{background:var(--line)}
.icon-btn svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:2}
.icon-btn.spin svg{animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.date-row{display:flex;align-items:center;gap:6px;padding:2px 0 10px}
.date-row .icon-btn[disabled]{opacity:.3}
.date-pick{position:relative;flex:1;text-align:center;font-size:17px;font-weight:600;
  padding:8px 0;border-radius:10px;background:var(--surface);border:1px solid var(--line)}
.date-pick select{position:absolute;inset:0;opacity:0;width:100%;cursor:pointer}

/* 當日買賣力道 */
.balance{margin:16px 0 6px}
.bal-nums{display:flex;justify-content:space-between;align-items:baseline}
.bal-nums span{font-size:13px;color:var(--muted);margin-right:6px}
.bal-nums strong{font-size:22px;font-weight:700}
.bal-nums .b strong{color:var(--up)}
.bal-nums .s{text-align:right}
.bal-nums .s strong{color:var(--down)}
.split{display:flex;height:10px;border-radius:5px;overflow:hidden;margin:8px 0 6px;background:var(--line)}
.split i{display:block;height:100%}
.split .b{background:var(--up)}
.split .s{background:var(--down)}
.net{margin:0;font-size:14px;color:var(--muted)}
.net b{color:var(--ink)}

/* 分頁 */
.tabs{display:grid;grid-template-columns:repeat(5,1fr);gap:2px;margin:14px 0 10px;
  background:var(--line);padding:4px;border-radius:12px}
.tabs button{border:0;background:transparent;padding:8px 0;border-radius:9px;font-size:15px;
  font-weight:600;color:var(--muted);cursor:pointer;white-space:nowrap}
.tabs button[aria-selected="true"]{background:var(--surface);color:var(--ink);
  box-shadow:0 1px 2px rgba(0,0,0,.08)}
.tools{display:flex;gap:8px;align-items:center;margin-bottom:6px;flex-wrap:wrap}
.chips{display:flex;gap:6px}
.chips button{border:1px solid var(--line);background:var(--surface);border-radius:999px;
  padding:5px 12px;font-size:14px;cursor:pointer}
.chips button[aria-pressed="true"]{border-color:var(--ink);font-weight:700}
#q{flex:1;min-width:150px;border:1px solid var(--line);background:var(--surface);
  border-radius:10px;padding:8px 12px;font-size:16px}

/* 清單 */
.sec{font-size:14px;color:var(--muted);margin:16px 0 4px;font-weight:600}
.row{display:block;width:100%;text-align:left;border:0;background:transparent;
  padding:12px 0;border-bottom:1px solid var(--line);cursor:pointer}
.row:active{background:var(--line)}
.r1{display:flex;align-items:center;gap:6px}
.nm{font-weight:700;font-size:17px}
.cd{color:var(--muted);font-size:14px}
.tag{font-size:12px;padding:1px 7px;border-radius:6px;font-weight:600;white-space:nowrap}
.tag.up{background:var(--up-soft);color:var(--up)}
.tag.down{background:var(--down-soft);color:var(--down)}
.tag.new{border:1px solid currentColor;background:transparent}
.amt{margin-left:auto;font-weight:700;font-size:17px;white-space:nowrap}
.up-t{color:var(--up)} .down-t{color:var(--down)}
.meter{display:block;height:5px;margin:7px 0 6px;border-radius:3px;background:var(--line);overflow:hidden}
.meter i{display:block;height:100%;border-radius:3px}
.meter i.up{background:var(--up)} .meter i.down{background:var(--down)}
.r3{display:flex;flex-wrap:wrap;justify-content:space-between;gap:2px 12px;font-size:13px;color:var(--muted)}
.r3 .l span{margin-right:10px;white-space:nowrap}
.msg{padding:40px 8px;text-align:center;color:var(--muted)}
.msg b{display:block;color:var(--ink);margin-bottom:6px;font-size:17px}
.foot{font-size:12px;color:var(--muted);margin-top:18px}

/* 每日表、統計表 */
.seg{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 8px}
.seg button{border:1px solid var(--line);background:var(--surface);border-radius:999px;
  padding:5px 12px;font-size:14px;cursor:pointer}
.seg button[aria-pressed="true"]{border-color:var(--ink);font-weight:700}
.tbl-meta{display:flex;justify-content:space-between;align-items:center;gap:10px;
  font-size:13px;color:var(--muted);margin:8px 0 4px}
.link-btn{border:1px solid var(--line);background:var(--surface);border-radius:8px;
  padding:5px 10px;font-size:13px;cursor:pointer;white-space:nowrap}
.link-btn.more{display:block;width:100%;margin-top:12px;padding:10px;font-size:14px}
.stat3{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:6px 0 4px}
.stat3 div{background:var(--surface);border:1px solid var(--line);border-radius:10px;
  padding:8px 4px;text-align:center}
.stat3 span{display:block;font-size:12px;color:var(--muted)}
.stat3 strong{font-size:15px;white-space:nowrap}
.dt{table-layout:fixed;font-size:13px}
.dt th{padding:0;border-bottom:1px solid var(--line)}
.dt th button{width:100%;border:0;background:transparent;padding:8px 0;font-size:12px;
  color:var(--muted);text-align:right;cursor:pointer;white-space:nowrap}
.dt th:first-child button{text-align:left}
.dt th[aria-sort] button{color:var(--ink);font-weight:700}
.dt td{padding:9px 0;vertical-align:middle;white-space:nowrap}
.dt td:first-child{white-space:normal;overflow:hidden}
.dt tbody tr{cursor:pointer}
.dt tbody tr:active{background:var(--line)}
.dt .nm{display:block;font-size:14px}
.dt .cd{display:block;font-size:12px}
.dt tfoot td{font-weight:700;font-size:12px;border-top:2px solid var(--line)}
.star{color:#D9A400;margin-left:3px;font-size:13px}
.wbtn{display:block;width:100%;margin-top:10px;padding:11px;border-radius:12px;
  border:1px solid var(--line);background:transparent;font-weight:600;cursor:pointer}
.wbtn[aria-pressed="true"]{border-color:#D9A400}

/* 個股明細 */
dialog{border:0;padding:0;width:100%;max-width:560px;margin:auto auto 0;
  border-radius:18px 18px 0 0;background:var(--surface);color:var(--ink);max-height:88dvh}
dialog::backdrop{background:rgba(0,0,0,.45)}
dialog[open]{animation:rise .22s ease-out}
@keyframes rise{from{transform:translateY(40px);opacity:.4}}
.sheet-in{padding:6px 18px calc(env(safe-area-inset-bottom,0px) + 18px)}
.grab{width:40px;height:5px;border-radius:3px;background:var(--line);margin:6px auto 4px}
.sheet-head{display:flex;align-items:center;justify-content:space-between}
.sheet-head h2{font-size:20px;margin:6px 0}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:8px 0 12px}
.stats div{background:var(--bg);border-radius:10px;padding:8px 6px;text-align:center}
.stats span{display:block;font-size:12px;color:var(--muted)}
.stats strong{font-size:14px;white-space:nowrap;display:block}
.chart{width:100%;height:auto;display:block}
.chart-cap{display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin:2px 0 10px}
table{width:100%;border-collapse:collapse;font-size:14px}
th{font-weight:500;color:var(--muted);font-size:12px;text-align:right;padding:4px 0}
th:first-child,td:first-child{text-align:left}
td{text-align:right;padding:6px 0;border-top:1px solid var(--line)}
.ext{display:block;text-align:center;margin-top:14px;padding:11px;border-radius:12px;
  border:1px solid var(--line);color:var(--ink);text-decoration:none;font-weight:600}
@media (prefers-reduced-motion: reduce){
  dialog[open],.icon-btn.spin svg{animation:none}
}
</style>
</head>
<body>
<header class="top">
  <div class="wrap">
    <div class="title-row">
      <h1>永豐金-匯立<span class="code">9A81</span></h1>
      <button class="icon-btn" id="refresh" aria-label="重新整理">
        <svg viewBox="0 0 24 24"><path d="M20 11a8 8 0 1 0-2.3 5.7"/><path d="M20 4v7h-7"/></svg>
      </button>
    </div>
    <div class="date-row">
      <button class="icon-btn" id="prev" aria-label="前一個交易日">
        <svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg></button>
      <label class="date-pick num"><span id="dateLabel">讀取中</span>
        <select id="dateSel" aria-label="選擇資料日期"></select></label>
      <button class="icon-btn" id="next" aria-label="下一個交易日">
        <svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg></button>
    </div>
  </div>
</header>

<main class="wrap">
  <section class="balance" id="balance" hidden aria-label="當日買賣超合計">
    <div class="bal-nums num">
      <div class="b"><span>買超</span><strong id="sumBuy"></strong></div>
      <div class="s"><span>賣超</span><strong id="sumSell"></strong></div>
    </div>
    <div class="split" aria-hidden="true"><i class="b" id="splitB"></i><i class="s" id="splitS"></i></div>
    <p class="net num" id="net"></p>
  </section>

  <div class="tabs" role="tablist">
    <button role="tab" data-tab="buy">買超</button>
    <button role="tab" data-tab="sell">賣超</button>
    <button role="tab" data-tab="cum">累計</button>
    <button role="tab" data-tab="daily">每日表</button>
    <button role="tab" data-tab="stats">統計表</button>
  </div>
  <div class="tools">
    <div class="chips" id="chips" hidden>
      <button data-n="5">5 日</button><button data-n="10">10 日</button><button data-n="20">20 日</button>
    </div>
    <input id="q" type="search" placeholder="搜尋代號或名稱" autocomplete="off">
  </div>
  <div id="list"></div>
  <p class="foot" id="foot"></p>
</main>

<dialog id="sheet" aria-labelledby="sheetTitle">
  <div class="sheet-in">
    <div class="grab"></div>
    <div class="sheet-head">
      <h2 id="sheetTitle"></h2>
      <button class="icon-btn" id="close" aria-label="關閉">
        <svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
    </div>
    <div id="sheetBody"></div>
  </div>
</dialog>

<script>
const $ = s => document.querySelector(s);
const S = {names:{}, dates:[], days:[], idx:-1, tab:'buy', n:5, q:'', loadedAt:0, generated:'',
  sp:5, limit:100, watch:new Set(),
  f:{daily:'all', stats:'all'}, sort:{daily:{k:'d', dir:-1}, stats:{k:'sum', dir:-1}}};
try { const t = localStorage.getItem('huili.tab'); if (['buy','sell','cum','daily','stats'].includes(t)) S.tab = t;
      const n = +localStorage.getItem('huili.n'); if ([5,10,20].includes(n)) S.n = n;
      const sp = localStorage.getItem('huili.sp'); if (sp !== null && [0,5,10,20].includes(+sp)) S.sp = +sp;
      const w = JSON.parse(localStorage.getItem('huili.watch') || '[]');
      if (Array.isArray(w)) S.watch = new Set(w.map(String)); } catch(e) {}

const esc = s => String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
// 金額單位：仟元
function money(k, signed){
  const a = Math.abs(k), sg = !signed ? '' : k > 0 ? '+' : k < 0 ? '−' : '';
  if (a >= 100000) return sg + (a / 100000).toFixed(2) + '億';
  return sg + Math.round(a / 10).toLocaleString('zh-TW') + '萬';
}
const lots = v => v == null ? '' : Math.abs(v).toLocaleString('zh-TW');
function price(amt, l){ if (!l) return ''; const p = amt / l; return p < 100 ? p.toFixed(2) : p.toLocaleString('zh-TW', {maximumFractionDigits:1}); }
function fmtDate(d, short){
  const y = +d.slice(0,4), m = +d.slice(4,6), dd = +d.slice(6);
  if (short) return m + '/' + dd;
  const w = '日一二三四五六'[new Date(y, m-1, dd).getDay()];
  return y + '-' + d.slice(4,6) + '-' + d.slice(6) + '（' + w + '）';
}

function streak(code, i, sign){
  let n = 0;
  for (let j = i; j >= 0; j--) { const r = S.days[j].get(code); if (r && (r.d > 0) === (sign > 0)) n++; else break; }
  return n;
}
function cum(i, n){
  const m = new Map();
  for (let j = Math.max(0, i - n + 1); j <= i; j++)
    for (const [c, r] of S.days[j]) { const a = m.get(c) || {sum:0, days:0}; a.sum += r.d; a.days++; m.set(c, a); }
  return m;
}
const match = c => !S.q || c.startsWith(S.q) || (S.names[c] || '').includes(S.q);

function ingest(j){
  S.names = j.names || {};
  S.generated = j.generated || '';
  S.dates = (j.days || []).map(d => d.d);
  S.days = (j.days || []).map(d => {
    const m = new Map();
    for (const [c, b, s, bl, sl] of d.r)
      m.set(c, {b, s, bl, sl, d: b - s, dl: (bl != null && sl != null) ? bl - sl : null});
    return m;
  });
  S.idx = S.dates.length - 1;
  S.loadedAt = Date.now();
}

async function load(){
  const btn = $('#refresh'); btn.classList.add('spin');
  try {
    const r = await fetch('data.json?t=' + Date.now(), {cache:'no-store'});
    if (!r.ok) throw new Error('HTTP ' + r.status);
    ingest(await r.json());
    render();
  } catch (e) {
    if (S.dates.length) render();
    else { $('#dateLabel').textContent = '讀取失敗';
      $('#list').innerHTML = '<div class="msg"><b>資料讀取失敗</b>請確認網路連線後，點右上角重新整理。</div>'; }
  } finally { btn.classList.remove('spin'); }
}

function render(){
  document.querySelectorAll('.tabs button').forEach(b => b.setAttribute('aria-selected', b.dataset.tab === S.tab));
  document.querySelectorAll('#chips button').forEach(b => b.setAttribute('aria-pressed', +b.dataset.n === S.n));
  $('#chips').hidden = S.tab !== 'cum';
  if (!S.dates.length) {
    $('#dateLabel').textContent = '尚無資料';
    $('#balance').hidden = true;
    $('#list').innerHTML = '<div class="msg"><b>還沒有資料</b>到 GitHub 的 Actions 頁面執行「匯立分點日報」一次，完成後回來重新整理。</div>';
    return;
  }
  const d = S.dates[S.idx];
  $('#dateLabel').textContent = fmtDate(d);
  const sel = $('#dateSel');
  if (sel.options.length !== S.dates.length) {
    sel.innerHTML = S.dates.map((x, i) => '<option value="' + i + '">' + fmtDate(x) + '</option>').reverse().join('');
  }
  sel.value = S.idx;
  $('#prev').disabled = S.idx === 0;
  $('#next').disabled = S.idx === S.dates.length - 1;

  const day = S.days[S.idx];
  let sb = 0, ss = 0;
  for (const r of day.values()) { if (r.d > 0) sb += r.d; else ss += r.d; }
  $('#balance').hidden = false;
  $('#sumBuy').textContent = money(sb);
  $('#sumSell').textContent = money(ss);
  const tot = sb - ss || 1;
  $('#splitB').style.width = (sb / tot * 100) + '%';
  $('#splitS').style.width = (-ss / tot * 100) + '%';
  const net = sb + ss;
  $('#net').innerHTML = '榜上淨' + (net >= 0 ? '買超' : '賣超') + ' <b class="' + (net >= 0 ? 'up-t' : 'down-t') + '">' + money(net) + '</b>';

  $('#list').innerHTML = S.tab === 'cum' ? cumHTML() : S.tab === 'daily' ? dailyHTML() :
    S.tab === 'stats' ? statsHTML() : dayHTML(S.tab === 'buy' ? 1 : -1);
  const g = S.generated ? S.generated.replace('T', ' ').slice(5) : '';
  $('#foot').textContent = '資料日期 ' + fmtDate(d) + (g ? '，網頁更新於 ' + g : '') +
    '。只含每日買超、賣超各前 50 名；均價為金額除以張數的估算值。資料來源：MoneyDJ 券商分點進出。';
}

function tagHTML(st, sign){
  const cls = sign > 0 ? 'up' : 'down';
  return st > 1 ? '<span class="tag ' + cls + '">連' + st + '日</span>' : '<span class="tag new ' + cls + '">新</span>';
}

function dayHTML(sign){
  const day = S.days[S.idx];
  const all = [...day.entries()].filter(([, r]) => sign > 0 ? r.d > 0 : r.d < 0)
    .sort((a, b) => sign > 0 ? b[1].d - a[1].d : a[1].d - b[1].d);
  const max = Math.max(1, ...all.map(([, r]) => Math.abs(r.d)));
  const c5 = cum(S.idx, 5);
  const rows = all.filter(([c]) => match(c));
  if (!rows.length) return '<div class="msg">' + (S.q ? '找不到符合的股票' : '這天沒有' + (sign > 0 ? '買超' : '賣超') + '資料') + '</div>';
  const cls = sign > 0 ? 'up' : 'down';
  return rows.map(([c, r]) => {
    const st = streak(c, S.idx, sign);
    const avg = sign > 0 ? price(r.b, r.bl) : price(r.s, r.sl);
    const det = '<span>買進 ' + money(r.b) + '</span><span>賣出 ' + money(r.s) + '</span>' +
      (r.dl != null ? '<span>' + lots(r.dl) + ' 張</span>' : '') + (avg ? '<span>均價 ' + avg + '</span>' : '');
    return '<button class="row" data-code="' + esc(c) + '">' +
      '<span class="r1"><span class="nm">' + esc(S.names[c] || c) + '</span><span class="cd">' + esc(c) + '</span>' +
      tagHTML(st, sign) + '<span class="amt num ' + cls + '-t">' + money(r.d, true) + '</span></span>' +
      '<span class="meter"><i class="' + cls + '" style="width:' + (Math.abs(r.d) / max * 100).toFixed(1) + '%"></i></span>' +
      '<span class="r3 num"><span class="l">' + det + '</span><span>5日 ' + money(c5.get(c).sum, true) + '</span></span></button>';
  }).join('');
}

function cumHTML(){
  const m = cum(S.idx, S.n);
  const have = Math.min(S.n, S.idx + 1);
  const all = [...m.entries()];
  const max = Math.max(1, ...all.map(([, a]) => Math.abs(a.sum)));
  const today = S.days[S.idx];
  const sec = (title, list, sign) => {
    const cls = sign > 0 ? 'up' : 'down';
    const rows = list.filter(([c]) => match(c)).slice(0, S.q ? 999 : 20);
    if (!rows.length) return '';
    return '<p class="sec">' + title + '</p>' + rows.map(([c, a]) => {
      const t = today.get(c);
      return '<button class="row" data-code="' + esc(c) + '">' +
        '<span class="r1"><span class="nm">' + esc(S.names[c] || c) + '</span><span class="cd">' + esc(c) + '</span>' +
        '<span class="tag ' + cls + '">上榜 ' + a.days + '/' + have + ' 天</span>' +
        '<span class="amt num ' + cls + '-t">' + money(a.sum, true) + '</span></span>' +
        '<span class="meter"><i class="' + cls + '" style="width:' + (Math.abs(a.sum) / max * 100).toFixed(1) + '%"></i></span>' +
        '<span class="r3 num"><span class="l"><span>' + (t ? '當日 ' + money(t.d, true) : '當日未進榜') + '</span></span></span></button>';
    }).join('');
  };
  const buys = all.filter(([, a]) => a.sum > 0).sort((a, b) => b[1].sum - a[1].sum);
  const sells = all.filter(([, a]) => a.sum < 0).sort((a, b) => a[1].sum - b[1].sum);
  const note = have < S.n ? '<p class="sec">目前只累積 ' + have + ' 個交易日的資料</p>' : '';
  const html = sec('近 ' + S.n + ' 日累計買超', buys, 1) + sec('近 ' + S.n + ' 日累計賣超', sells, -1);
  return note + (html || '<div class="msg">找不到符合的股票</div>');
}

// ---------- 每日表、統計表
const sum = a => a.reduce((x, y) => x + y, 0);
const moneyOr = v => v ? money(v) : '—';
const slots = v => v == null ? '' : (v > 0 ? '+' : v < 0 ? '−' : '') + Math.abs(v).toLocaleString('zh-TW');
const cmp = (a, b, dir) => a == null && b == null ? 0 : a == null ? 1 : b == null ? -1 : (a < b ? -1 : a > b ? 1 : 0) * dir;
const FILTERS = [['all','全部'], ['buy','買超'], ['sell','賣超'], ['watch','關注']];
const PERIODS = [[5,'5 日'], [10,'10 日'], [20,'20 日'], [0,'全部']];
const watchLabel = c => S.watch.has(c) ? '★ 已關注，再按一次取消' : '☆ 加入關注';
const starHTML = c => S.watch.has(c) ? '<span class="star" aria-label="已關注">★</span>' : '';

function passF(f, code, v){
  if (f === 'buy') return v > 0;
  if (f === 'sell') return v < 0;
  if (f === 'watch') return S.watch.has(code);
  return true;
}
function emptyMsg(f){
  if (S.q) return '<div class="msg">找不到符合的股票</div>';
  if (f === 'watch') return S.watch.size
    ? '<div class="msg"><b>關注的股票都沒有進榜</b>換一天或拉長統計期間看看。</div>'
    : '<div class="msg"><b>還沒有關注的股票</b>點任一檔股票，在明細最下方按「加入關注」。</div>';
  return '<div class="msg">沒有符合的資料</div>';
}
function chipsHTML(attr, items, cur){
  return '<div class="seg">' + items.map(([v, label]) =>
    '<button data-' + attr + '="' + v + '" aria-pressed="' + (String(cur) === String(v)) + '">' + label + '</button>').join('') + '</div>';
}
function thHTML(tab, k, label){
  const s = S.sort[tab], on = s.k === k;
  return '<th' + (on ? ' aria-sort="' + (s.dir > 0 ? 'ascending' : 'descending') + '"' : '') + '><button data-sort="' + k + '">' +
    label + (on ? (s.dir > 0 ? ' ▲' : ' ▼') : '') + '</button></th>';
}
function nameCell(c){
  return '<td><span class="nm">' + esc(S.names[c] || c) + starHTML(c) + '</span><span class="cd">' + esc(c) + '</span></td>';
}
const signCls = v => v > 0 ? 'up-t' : v < 0 ? 'down-t' : '';

function dailyRows(){
  const f = S.f.daily, s = S.sort.daily;
  const key = {name: r => r.c, b: r => r.b, s: r => r.s, d: r => r.d, dl: r => r.dl}[s.k];
  const all = [...S.days[S.idx].entries()].map(([c, r]) => ({c, ...r}));
  const rows = all.filter(r => passF(f, r.c, r.d) && match(r.c))
    .sort((a, b) => cmp(key(a), key(b), s.dir) || b.d - a.d);
  return {all, rows};
}

function dailyHTML(){
  const {all, rows} = dailyRows();
  const nb = all.filter(r => r.d > 0).length;
  let html = chipsHTML('f', FILTERS, S.f.daily) +
    '<div class="tbl-meta"><span>買超 ' + nb + ' 檔　賣超 ' + (all.length - nb) + ' 檔</span>' +
    '<button class="link-btn" data-act="csv">匯出 CSV</button></div>';
  if (!rows.length) return html + emptyMsg(S.f.daily);
  const tb = sum(rows.map(r => r.b)), ts = sum(rows.map(r => r.s)), td = tb - ts;
  const dls = rows.filter(r => r.dl != null);
  const tl = dls.length ? sum(dls.map(r => r.dl)) : null;
  html += '<table class="dt num"><colgroup><col style="width:27%"><col style="width:17%"><col style="width:17%"><col style="width:19%"><col style="width:20%"></colgroup>' +
    '<thead><tr>' + thHTML('daily', 'name', '股票') + thHTML('daily', 'b', '買進') + thHTML('daily', 's', '賣出') +
    thHTML('daily', 'd', '差額') + thHTML('daily', 'dl', '張數') + '</tr></thead><tbody>' +
    rows.map(r => '<tr class="trow" data-code="' + esc(r.c) + '">' + nameCell(r.c) +
      '<td>' + moneyOr(r.b) + '</td><td>' + moneyOr(r.s) + '</td>' +
      '<td class="' + signCls(r.d) + '"><b>' + money(r.d, true) + '</b></td><td>' + slots(r.dl) + '</td></tr>').join('') +
    '</tbody><tfoot><tr><td>合計 ' + rows.length + ' 檔</td><td>' + money(tb) + '</td><td>' + money(ts) + '</td>' +
    '<td class="' + signCls(td) + '">' + money(td, true) + '</td><td>' + slots(tl) + '</td></tr></tfoot></table>';
  return html;
}

function stat(i, n){
  const from = n ? Math.max(0, i - n + 1) : 0;
  const m = new Map();
  for (let j = from; j <= i; j++)
    for (const [c, r] of S.days[j]) {
      const a = m.get(c) || {code:c, sum:0, b:0, s:0, bd:0, sd:0, dl:null};
      a.sum += r.d; a.b += r.b; a.s += r.s;
      if (r.d > 0) a.bd++; else if (r.d < 0) a.sd++;
      if (r.dl != null) a.dl = (a.dl || 0) + r.dl;
      m.set(c, a);
    }
  const today = S.days[i];
  for (const a of m.values()) {
    const t = today.get(a.code);
    a.days = a.bd + a.sd;
    a.streak = !t ? 0 : t.d > 0 ? streak(a.code, i, 1) : -streak(a.code, i, -1);
  }
  return {from, all:[...m.values()]};
}

function statRows(){
  const f = S.f.stats, s = S.sort.stats;
  const key = {name: a => a.code, sum: a => a.sum, days: a => a.days, streak: a => a.streak}[s.k];
  const st = stat(S.idx, S.sp);
  const rows = st.all.filter(a => passF(f, a.code, a.sum) && match(a.code))
    .sort((a, b) => cmp(key(a), key(b), s.dir) || b.sum - a.sum);
  return {...st, rows};
}

function statsHTML(){
  const {from, all, rows} = statRows();
  const buys = all.filter(a => a.sum > 0), sells = all.filter(a => a.sum < 0);
  const nd = S.idx - from + 1;
  let html = chipsHTML('sp', PERIODS, S.sp) + chipsHTML('f', FILTERS, S.f.stats) +
    '<div class="stat3"><div><span>交易日</span><strong class="num">' + nd + ' 日</strong></div>' +
    '<div><span>淨買超 ' + buys.length + ' 檔</span><strong class="num up-t">' + money(sum(buys.map(a => a.sum)), true) + '</strong></div>' +
    '<div><span>淨賣超 ' + sells.length + ' 檔</span><strong class="num down-t">' + money(sum(sells.map(a => a.sum)), true) + '</strong></div></div>' +
    '<div class="tbl-meta"><span>' + fmtDate(S.dates[from], 1) + ' 至 ' + fmtDate(S.dates[S.idx], 1) + '</span>' +
    '<button class="link-btn" data-act="csv">匯出 CSV</button></div>';
  if (!rows.length) return html + emptyMsg(S.f.stats);
  const shown = rows.slice(0, S.limit);
  html += '<table class="dt num"><colgroup><col style="width:34%"><col style="width:26%"><col style="width:20%"><col style="width:20%"></colgroup>' +
    '<thead><tr>' + thHTML('stats', 'name', '股票') + thHTML('stats', 'sum', '累計差額') +
    thHTML('stats', 'days', '買/賣天') + thHTML('stats', 'streak', '連續') + '</tr></thead><tbody>' +
    shown.map(a => '<tr class="trow" data-code="' + esc(a.code) + '">' + nameCell(a.code) +
      '<td class="' + signCls(a.sum) + '"><b>' + money(a.sum, true) + '</b></td>' +
      '<td>' + a.bd + ' / ' + a.sd + '</td>' +
      '<td class="' + signCls(a.streak) + '">' + (a.streak > 0 ? '買' + a.streak + '日' : a.streak < 0 ? '賣' + (-a.streak) + '日' : '—') + '</td></tr>').join('') +
    '</tbody><tfoot><tr><td>合計 ' + rows.length + ' 檔</td><td class="' + signCls(sum(rows.map(a => a.sum))) + '">' +
    money(sum(rows.map(a => a.sum)), true) + '</td><td></td><td></td></tr></tfoot></table>';
  if (rows.length > shown.length)
    html += '<button class="link-btn more" data-act="more">顯示全部 ' + rows.length + ' 檔（目前 ' + shown.length + ' 檔）</button>';
  return html;
}

function csvDownload(name, head, rows){
  const q = v => { v = v == null ? '' : String(v); return /[",\r\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; };
  const text = '﻿' + [head, ...rows].map(r => r.map(q).join(',')).join('\r\n');
  const url = URL.createObjectURL(new Blob([text], {type:'text/csv;charset=utf-8'}));
  const a = document.createElement('a');
  a.href = url; a.download = name;
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 3000);
}
function exportCSV(){
  const d = S.dates[S.idx];
  if (S.tab === 'daily') {
    csvDownload('huili_daily_' + d + '.csv',
      ['代號','名稱','買進金額(仟元)','賣出金額(仟元)','差額(仟元)','買進張數','賣出張數','差額張數'],
      dailyRows().rows.map(r => [r.c, S.names[r.c] || '', r.b, r.s, r.d, r.bl, r.sl, r.dl]));
  } else if (S.tab === 'stats') {
    csvDownload('huili_stats_' + d + '_' + (S.sp || 'all') + '.csv',
      ['代號','名稱','累計差額(仟元)','買進合計(仟元)','賣出合計(仟元)','買超天數','賣超天數','目前連續(正買負賣)','累計張數差'],
      statRows().rows.map(a => [a.code, S.names[a.code] || '', a.sum, a.b, a.s, a.bd, a.sd, a.streak, a.dl]));
  }
}
function toggleWatch(code){
  if (S.watch.has(code)) S.watch.delete(code); else S.watch.add(code);
  try { localStorage.setItem('huili.watch', JSON.stringify([...S.watch])); } catch (_) {}
}
function setSort(k){
  const s = S.sort[S.tab];
  if (s.k === k) s.dir = -s.dir; else { s.k = k; s.dir = k === 'name' ? 1 : -1; }
  render();
}

function openSheet(code){
  const i0 = Math.max(0, S.idx - 19), span = [];
  for (let j = i0; j <= S.idx; j++) span.push([S.dates[j], S.days[j].get(code)]);
  const now = S.days[S.idx].get(code);
  const sign = now ? Math.sign(now.d) : 0;
  const st = sign ? streak(code, S.idx, sign) : 0;
  const cell = (label, v, cls) => '<div><span>' + label + '</span><strong class="num ' + (cls || '') + '">' + v + '</strong></div>';
  const cv = n => { const a = cum(S.idx, n).get(code); return a ? [money(a.sum, true), a.sum > 0 ? 'up-t' : 'down-t'] : ['—', '']; };
  const [c5, k5] = cv(5), [c10, k10] = cv(10), [c20, k20] = cv(20);
  const stTxt = !sign ? '未進榜' : (sign > 0 ? '買' : '賣') + ' ' + st + ' 日';

  // 長條圖
  const W = 320, H = 120, pad = 4, bw = W / span.length;
  const pm = Math.max(0, ...span.map(([, r]) => r && r.d > 0 ? r.d : 0));
  const nm = Math.max(0, ...span.map(([, r]) => r && r.d < 0 ? -r.d : 0));
  const scale = (pm + nm) ? (H - pad * 2) / (pm + nm) : 0;
  const mid = (pm + nm) ? pad + pm * scale : H / 2;
  let bars = '';
  span.forEach(([, r], k) => {
    const x = k * bw + bw * 0.15, w = bw * 0.7;
    if (!r) { bars += '<rect x="' + x + '" y="' + (mid - 1) + '" width="' + w + '" height="2" fill="var(--muted)" opacity=".5"/>'; return; }
    const h = Math.max(2, Math.abs(r.d) * scale);
    bars += '<rect x="' + x + '" y="' + (r.d > 0 ? mid - h : mid) + '" width="' + w + '" height="' + h + '" rx="1.5" fill="var(' + (r.d > 0 ? '--up' : '--down') + ')"/>';
  });
  const svg = '<svg class="chart" viewBox="0 0 ' + W + ' ' + H + '" role="img" aria-label="近 ' + span.length + ' 個交易日買賣超">' +
    '<line x1="0" x2="' + W + '" y1="' + mid + '" y2="' + mid + '" stroke="var(--line)"/>' + bars + '</svg>' +
    '<div class="chart-cap"><span>' + fmtDate(span[0][0], 1) + '</span><span>灰線：當日未進榜</span><span>' + fmtDate(span[span.length - 1][0], 1) + '</span></div>';

  const rows = span.filter(([, r]) => r).reverse().map(([d, r]) =>
    '<tr><td>' + fmtDate(d, 1) + '</td><td class="' + (r.d > 0 ? 'up-t' : 'down-t') + '">' + money(r.d, true) + '</td>' +
    '<td>' + (r.dl != null ? (r.dl > 0 ? '+' : '−') + lots(r.dl) : '') + '</td>' +
    '<td>' + (r.d > 0 ? price(r.b, r.bl) : price(r.s, r.sl)) + '</td></tr>').join('');

  $('#sheetTitle').textContent = (S.names[code] || code) + ' ' + code;
  $('#sheetBody').innerHTML =
    '<div class="stats">' + cell('連續', stTxt, sign > 0 ? 'up-t' : sign < 0 ? 'down-t' : '') +
    cell('5日', c5, k5) + cell('10日', c10, k10) + cell('20日', c20, k20) + '</div>' + svg +
    '<table class="num"><thead><tr><th>日期</th><th>差額</th><th>張數</th><th>均價</th></tr></thead><tbody>' + rows + '</tbody></table>' +
    '<a class="ext" href="https://tw.stock.yahoo.com/quote/' + encodeURIComponent(code) + '" target="_blank" rel="noopener">在 Yahoo 股市查看 ' + esc(code) + '</a>' +
    '<button class="wbtn" data-watch="' + esc(code) + '" aria-pressed="' + S.watch.has(code) + '">' + watchLabel(code) + '</button>';
  const dlg = $('#sheet');
  if (typeof dlg.showModal === 'function') dlg.showModal(); else dlg.setAttribute('open', '');
}

// 事件
document.querySelector('.tabs').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  S.tab = b.dataset.tab; S.limit = 100; try { localStorage.setItem('huili.tab', S.tab); } catch (_) {}
  render();
});
$('#chips').addEventListener('click', e => {
  const b = e.target.closest('button'); if (!b) return;
  S.n = +b.dataset.n; try { localStorage.setItem('huili.n', S.n); } catch (_) {}
  render();
});
$('#q').addEventListener('input', e => { S.q = e.target.value.trim(); S.limit = 100; render(); });
$('#prev').addEventListener('click', () => { if (S.idx > 0) { S.idx--; render(); } });
$('#next').addEventListener('click', () => { if (S.idx < S.dates.length - 1) { S.idx++; render(); } });
$('#dateSel').addEventListener('change', e => { S.idx = +e.target.value; render(); });
$('#refresh').addEventListener('click', load);
$('#list').addEventListener('click', e => {
  const t = e.target;
  const r = t.closest('.row, .trow'); if (r) return openSheet(r.dataset.code);
  const so = t.closest('[data-sort]'); if (so) return setSort(so.dataset.sort);
  const f = t.closest('[data-f]'); if (f) { S.f[S.tab] = f.dataset.f; S.limit = 100; return render(); }
  const sp = t.closest('[data-sp]');
  if (sp) { S.sp = +sp.dataset.sp; S.limit = 100; try { localStorage.setItem('huili.sp', S.sp); } catch (_) {} return render(); }
  const ac = t.closest('[data-act]');
  if (ac && ac.dataset.act === 'csv') exportCSV();
  if (ac && ac.dataset.act === 'more') { S.limit = Infinity; render(); }
});
$('#sheetBody').addEventListener('click', e => {
  const w = e.target.closest('[data-watch]'); if (!w) return;
  toggleWatch(w.dataset.watch);
  w.textContent = watchLabel(w.dataset.watch);
  w.setAttribute('aria-pressed', S.watch.has(w.dataset.watch));
  render();
});
$('#close').addEventListener('click', () => $('#sheet').close());
$('#sheet').addEventListener('click', e => { if (e.target.id === 'sheet') e.target.close(); });
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && Date.now() - S.loadedAt > 10 * 60 * 1000) load();
});
load();
</script>
</body>
</html>
"""


def main() -> int:
    SITE.mkdir(parents=True, exist_ok=True)
    data = build_data()
    (SITE / "data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")),
                                    encoding="utf-8")
    (SITE / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (SITE / "manifest.webmanifest").write_text(json.dumps(MANIFEST, ensure_ascii=False, indent=1),
                                               encoding="utf-8")
    (SITE / "icon-192.png").write_bytes(make_icon(192))
    (SITE / "icon-512.png").write_bytes(make_icon(512))
    (SITE / "apple-touch-icon.png").write_bytes(make_icon(180))
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    print(f"✔ 網頁已產生：{len(data['days'])} 個交易日、{len(data['names'])} 檔股票")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
