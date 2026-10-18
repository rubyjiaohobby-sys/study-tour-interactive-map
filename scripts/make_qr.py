#!/usr/bin/env python3
"""生成二维码：把部署后的网址生成 PNG 二维码，贴到海报/手册上，扫码即开研学地图。

用法：
  uv run --with segno python make_qr.py "https://你的网址" -o 二维码.png
依赖 segno（纯 Python，无 PIL 依赖）。
"""
import argparse
import segno


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url", help="部署后的完整网址（要 https:// 开头）")
    ap.add_argument("-o", "--out", default="二维码.png")
    ap.add_argument("--scale", type=int, default=10, help="每个码点像素，10 约 500px 宽")
    ap.add_argument("--dark", default="#b93a2b", help="码点颜色（默认朱红，配国潮）")
    ap.add_argument("--light", default="#fffdf8", help="背景色（默认米白）")
    args = ap.parse_args()

    qr = segno.make(args.url, error="m")
    qr.save(args.out, scale=args.scale, border=2, dark=args.dark, light=args.light)
    print(f"二维码 → {args.out}（扫码打开 {args.url}）")


if __name__ == "__main__":
    main()
