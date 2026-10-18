#!/usr/bin/env python3
"""合并 poi + 介绍 + 题目 + 照片 → 单文件研学交互地图 HTML（答题集章版）。

用法：
  python3 build_study_map.py ../examples/shantou --out 汕头研学交互地图.html

目录内：poi.json（gcj02）、intros.json（介绍）、quiz.json（题目/印章）、
photos/{order:02d}.jpg（可选）、route.geojson（可选，有则画路线+距离标签）。

沿用「漫游地图」的高德瓦片 URL（GCJ-02，无需 key）。
"""
import base64, json, math, argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent
TPL = HERE.parent / "template" / "study.html"


def hav(a, b):
    R = 6371000
    p1, p2 = math.radians(a[1]), math.radians(b[1])
    dp = math.radians(b[1] - a[1]); dl = math.radians(b[0] - a[0])
    return 2 * R * math.asin(math.sqrt(math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2))


def point_along(coords, frac=0.5):
    segs = [hav(coords[i], coords[i+1]) for i in range(len(coords)-1)]
    total = sum(segs)
    if total <= 0:
        return coords[len(coords)//2]
    target = total * frac; acc = 0.0
    for i, d in enumerate(segs):
        if acc + d >= target and d > 0:
            t = (target - acc) / d; a, b = coords[i], coords[i+1]
            return [a[0] + (b[0]-a[0])*t, a[1] + (b[1]-a[1])*t]
        acc += d
    return coords[-1]


def fmt_dist(m):
    return f"{m} m" if m < 1000 else f"{m/1000:.2f} km"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    ap.add_argument("--out", default="研学交互地图.html")
    ap.add_argument("--title", default="研学小侦探")
    ap.add_argument("--subtitle", default="点开建筑 · 答题 · 集章")
    ap.add_argument("--seal", default="研学")
    args = ap.parse_args()

    d = Path(args.dir)
    pois = json.loads((d/"poi.json").read_text(encoding="utf-8"))["pois"]
    intros = json.loads((d/"intros.json").read_text(encoding="utf-8"))["intros"]
    quiz = json.loads((d/"quiz.json").read_text(encoding="utf-8"))["quiz"]
    photodir = d/"photos"

    # 照片 base64
    photos = {}
    for p in pois:
        f = photodir / f"{p['order']:02d}.jpg"
        if f.exists():
            photos[p["order"]] = "data:image/jpeg;base64," + base64.b64encode(f.read_bytes()).decode()

    # 路线（可选）
    route = None; labels = []; bounds = None
    rp = d/"route.geojson"
    if rp.exists():
        route = json.loads(rp.read_text(encoding="utf-8"))
        route = {"type": "FeatureCollection", "features": route["features"]}
        labels = []
        for f in route["features"]:
            pr = f["properties"]; mid = point_along(f["geometry"]["coordinates"])
            labels.append({"lng": mid[0], "lat": mid[1], "text": fmt_dist(pr["distance_m"])})
        allc = [c for f in route["features"] for c in f["geometry"]["coordinates"]]
        bounds = [[min(c[0] for c in allc), min(c[1] for c in allc)],
                  [max(c[0] for c in allc), max(c[1] for c in allc)]]
    else:
        bounds = [[min(p["lng"] for p in pois), min(p["lat"] for p in pois)],
                  [max(p["lng"] for p in pois), max(p["lat"] for p in pois)]]

    data_pois = [{"order": p["order"], "name": p["name"], "lng": p["lng"], "lat": p["lat"],
                  "intro": intros.get(p["name"], "")} for p in pois]

    # 校验 quiz 覆盖所有点
    missing = [p["name"] for p in pois if p["name"] not in quiz]
    if missing:
        print("⚠️ 以下点缺题目：", missing)

    roam = {"title": args.title, "pois": data_pois, "photos": photos,
            "quiz": quiz, "route": route or {"type": "FeatureCollection", "features": []},
            "labels": labels, "bounds": bounds}

    html = TPL.read_text(encoding="utf-8")
    html = html.replace("__TITLE__", args.title)
    html = html.replace("__SUBTITLE__", args.subtitle)
    html = html.replace("__SEAL__", args.seal)
    html = html.replace("__NPOI__", str(len(pois)))
    html = html.replace("/*__STUDY_DATA__*/", json.dumps(roam, ensure_ascii=False))

    out = Path(args.out)
    out.write_text(html, encoding="utf-8")
    nq = sum(len(q["questions"]) for q in quiz.values())
    print(f"生成 {out} ({out.stat().st_size/1024/1024:.1f} MB)：{len(pois)} 点 · {nq} 题 · "
          f"{len(photos)} 照片 · 印章 {len(quiz)} 枚")


if __name__ == "__main__":
    main()
