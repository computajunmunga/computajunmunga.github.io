"""Pantry + model-stats -> repo CSV hourly refresh. stdlib only."""
import csv
import io
import json
import os
import urllib.request

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "assets", "data")

PANTRY_PUBLIC = "https://getpantry.cloud/apiv1/public/4e838a05450f87530fe0450439d6a382"
SYMBOLS_PUBLIC = "https://getpantry.cloud/apiv1/public/4a8477043869bbc5a9736316cf3d123f"


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def refresh_rsi():
    basket = get_json(PANTRY_PUBLIC)
    rows = basket.get("rsi", [])
    if not rows:
        print("rsi 비어있음 → 기존 파일 유지")
        return
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["ts", "rsi15m", "rsi1h", "rsi4h", "rsi1d"])
    for o in rows:
        w.writerow([o.get("ts"), o.get("a"), o.get("b"), o.get("c"), o.get("d")])
    path = os.path.join(DATA, "rsi.csv")
    os.makedirs(DATA, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())
    print(f"rsi.csv: {len(rows)} rows")


def refresh_daily():
    # 서버 내부망 API 대신 Pantry basket의 daily 배열을 그대로 CSV로 옮긴다.
    # daily 배열은 서버/노트북의 push_daily_to_pantry()가 채운다.
    basket = get_json(PANTRY_PUBLIC)
    rows = basket.get("daily", [])
    if not rows:
        print("daily 비어있음 → 기존 파일 유지")
        return
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["day", "model", "n", "acc"])
    for o in rows:
        day = o.get("day")
        for model, key in (("model1", "m1"), ("model2", "m2")):
            if o.get(key) is None:
                continue
            w.writerow([day, model, o.get("n", 0), o.get(key)])
    path = os.path.join(DATA, "model_daily.csv")
    os.makedirs(DATA, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())
    print(f"model_daily.csv: {len(rows)} days")


def refresh_symbols():
    # 심볼별 최신 RSI (산점도용). Coinsimbolrsi 바스켓 symbols 배열 그대로 저장.
    basket = get_json(SYMBOLS_PUBLIC)
    rows = basket.get("symbols", []) if isinstance(basket, dict) else []
    rows = [o for o in rows if isinstance(o, dict) and o.get("symbol")]
    if not rows:
        print("symbols 비어있음 → 기존 파일 유지")
        return
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["symbol", "rsi15m", "rsi1h", "rsi4h", "rsi1d"])
    for o in sorted(rows, key=lambda x: x["symbol"]):
        w.writerow([o.get("symbol"), o.get("rsi15m"), o.get("rsi1h"),
                    o.get("rsi4h"), o.get("rsi1d")])
    path = os.path.join(DATA, "rsi_latest.csv")
    os.makedirs(DATA, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())
    print(f"rsi_latest.csv: {len(rows)} symbols")


if __name__ == "__main__":
    refresh_rsi()
    refresh_daily()
    refresh_symbols()
