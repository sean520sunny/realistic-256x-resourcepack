# -*- coding: utf-8 -*-
"""
由 AI 写实花卉底图生成 Minecraft 花贴图（纯 Pillow，无 numpy）。

小型花 13 种（郁金香 4 种另由 gen_tulips.py 产出）：
  dandelion, golden_dandelion, poppy, blue_orchid, allium, azure_bluet,
  oxeye_daisy, cornflower, lily_of_the_valley, wither_rose, torchflower,
  closed_eyeblossom, open_eyeblossom
大型花 5 种（top/bottom 两片）：
  sunflower, lilac, rose_bush, peony, pitcher_plant

工艺：
  1. 抠黑底 -> alpha（避开右下角水印）
  2. 按包围盒居中缩放到 256
  3. 花瓣染色（复用「低饱和高亮 + 花头位置」判定），茎叶保持绿
  4. 大型花：取底图上半部(花)做 top，下半部(茎叶)做 bottom，各自居中放大
"""
import os
from PIL import Image, ImageDraw

BASE = r"D:\WorkSpace(WB)\2026-11-17-20-32-26"
SRC = os.path.join(BASE, "_tex_source", "flowers_ai")
OUT = os.path.join(BASE, "_flowers_out")
os.makedirs(OUT, exist_ok=True)
N = 256

# 底图文件
S = {
    "yellow": "A_single_photorealistic_yellow_2026-11-28T02-04-45.png",
    "daisy":  "A_single_photorealistic_white__2026-11-28T02-04-44.png",
    "poppy":  "A_single_photorealistic_red_po_2026-11-28T02-04-47.png",
    "allium": "A_single_photorealistic_purple_2026-11-28T02-04-43.png",
    "lily":   "A_single_photorealistic_lily_o_2026-11-28T02-05-29.png",
    "torch":  "A_single_photorealistic_torchf_2026-11-28T02-05-31.png",
    "eye":    "A_single_photorealistic_open_e_2026-11-28T02-05-32.png",
    "sun":    "A_single_photorealistic_sunflo_2026-11-28T02-05-29.png",
    "lilac":  "A_photorealistic_lilac_flower__2026-11-28T02-05-52.png",
    "rose":   "A_photorealistic_rose_bush__se_2026-11-28T02-05-58.png",
    "peony":  "A_photorealistic_peony_flower__2026-11-28T02-05-53.png",
}

# 小型花：(底图, 花瓣目标色 或 None=不染色, 花头位置比例)
SMALL = {
    "dandelion":        ("yellow", (250, 214, 46), 0.42),
    "golden_dandelion": ("yellow", (232, 174, 20), 0.42),
    "poppy":            ("poppy",  None, 0.40),
    "wither_rose":      ("poppy",  (46, 40, 52), 0.40),   # 虞美人底染成暗紫黑
    "allium":           ("allium", None, 0.42),
    "azure_bluet":      ("daisy",  (110, 155, 232), 0.32),
    "cornflower":       ("daisy",  (48, 92, 210), 0.32),
    "blue_orchid":      ("daisy",  (158, 96, 214), 0.32),
    "oxeye_daisy":      ("daisy",  None, 0.42),
    "lily_of_the_valley": ("lily", None, 0.75),  # 铃铛串贯穿，不按花头位置染
    "torchflower":      ("torch",  None, 0.45),
    "open_eyeblossom":  ("eye",    None, 0.45),
    "closed_eyeblossom":("eye",    (170, 168, 160), 0.45),  # 张开花去橙心+压灰=闭合
}

# 大型花：底图 -> 花头分界比例（上半=花 top，下半=茎 bottom）
TALL = {
    "sunflower":     ("sun",   0.45),
    "lilac":         ("lilac", 0.62),
    "rose_bush":     ("rose",  0.58),
    "peony":         ("peony", 0.60),
    "pitcher_plant": ("lily",  0.55),  # 暂无独立底图，用铃兰近似（捕虫囊形态差异待补）
}


def crop_nomark(im):
    """裁掉右下角水印：取主体包围盒，排除水印区。"""
    W, H = im.size
    wm_x, wm_y = int(W * 0.78), int(H * 0.78)
    px = im.load()
    minx = miny = 10**9; maxx = maxy = -1
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            if x > wm_x and y > wm_y:
                continue
            if max(px[x, y]) > 42:
                minx = min(minx, x); maxx = max(maxx, x)
                miny = min(miny, y); maxy = max(maxy, y)
    # 直接抹掉右下水印区，杜绝被当成植物像素
    im = im.copy(); ip = im.load()
    for y in range(wm_y, H):
        for x in range(wm_x, W):
            ip[x, y] = (0, 0, 0)
    pad = 10
    minx = max(0, minx - pad); miny = max(0, miny - pad)
    maxx = min(W - 1, maxx + pad); maxy = min(H - 1, maxy + pad)
    return im.crop((minx, miny, maxx + 1, maxy + 1)).convert("RGBA")


def to_rgba(crop, target=N, region=None):
    """抠黑底 + 可选区域裁切(top/bottom) + 居中缩放。"""
    if region == "top":
        h = crop.height // 2
        crop = crop.crop((0, 0, crop.width, h))
    elif region == "bottom":
        h = crop.height // 2
        crop = crop.crop((0, h, crop.width, crop.height))
    g = crop.convert("L"); gp = g.load(); cp = crop.load()
    for y in range(crop.height):
        for x in range(crop.width):
            lum = gp[x, y]
            a = 0 if lum <= 24 else (int(255 * (lum - 24) / 32) if lum < 56 else 255)
            r, gg, b, _ = cp[x, y]
            cp[x, y] = (r, gg, b, a)
    iw, ih = crop.size
    sc = min((target - 4) / iw, (target - 4) / ih)
    nw, nh = max(1, int(iw * sc)), max(1, int(ih * sc))
    crop = crop.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    canvas.paste(crop, ((target - nw) // 2, (target - nh) // 2), crop)
    return canvas


def is_petal(r, g, b, y, split, mode="white"):
    if y >= split:
        return False
    mx = max(r, g, b); mn = min(r, g, b)
    sat = (mx - mn) / mx if mx else 0
    lum = (r + g + b) / 3
    if mode == "white":
        # 白花底（daisy/tulip）：严格低饱和高亮，避开灰绿叶尖
        return sat < 0.22 and lum > 140
    if mode == "red":
        # 红花底（poppy）：花头区域内全部非黑像素都算花瓣
        return lum > 40
    return sat < 0.35 and lum > 100


def dye(img, color, split, mode="white"):
    out = img.copy(); p = out.load()
    tr, tg, tb = color
    for y in range(N):
        for x in range(N):
            r, g, b, a = p[x, y]
            if a == 0 or not is_petal(r, g, b, y, split, mode):
                continue
            lum = (r + g + b) / 3 / 255.0
            f = 0.50 + 0.88 * lum
            p[x, y] = (max(0, min(255, int(tr * f))),
                       max(0, min(255, int(tg * f))),
                       max(0, min(255, int(tb * f))), a)
    return out


def green_stem(img, split, stem=(92, 138, 58)):
    """把灰白茎叶染成自然绿（daisy 底图的叶子是灰的，需补色）。"""
    out = img.copy(); p = out.load()
    sr, sg, sb = stem
    for y in range(split, N):
        for x in range(N):
            r, g, b, a = p[x, y]
            if a == 0:
                continue
            lum = (r + g + b) / 3 / 255.0
            f = 0.55 + 0.80 * lum
            p[x, y] = (max(0, min(255, int(sr * f))),
                       max(0, min(255, int(sg * f))),
                       max(0, min(255, int(sb * f))), a)
    return out


def build_small(name, spec):
    srckey, color, split_ratio = spec
    im = Image.open(os.path.join(SRC, S[srckey])).convert("RGB")
    crop = crop_nomark(im)
    base = to_rgba(crop)
    split = int(N * split_ratio)
    mode = "red" if srckey == "poppy" else "white"
    if srckey in ("daisy", "eye", "poppy"):
        base = green_stem(base, split)
    return base if color is None else dye(base, color, split, mode)


def build_tall(name, spec):
    srckey, split_ratio = spec
    im = Image.open(os.path.join(SRC, S[srckey])).convert("RGB")
    crop = crop_nomark(im)
    # top = 花，bottom = 茎叶；各自独立居中
    top = to_rgba(crop, region="top")
    bot = to_rgba(crop, region="bottom")
    return top, bot


def preview(imgs):
    items = list(imgs.items())
    cols = 6; cw = 150; ch = 170
    rows = (len(items) + cols - 1) // cols
    prev = Image.new("RGB", (cols * (cw + 8) + 8, rows * (ch + 8) + 8), (244, 244, 246))
    d = ImageDraw.Draw(prev)
    for i, (name, img) in enumerate(items):
        r, c = divmod(i, cols); x = 8 + c * (cw + 8); y = 8 + r * (ch + 8)
        checker = Image.new("RGB", (cw, cw - 20), (255, 255, 255)); dc = ImageDraw.Draw(checker)
        for yy in range(0, cw - 20, 12):
            for xx in range(0, cw, 12):
                if (xx // 12 + yy // 12) % 2:
                    dc.rectangle([xx, yy, xx + 11, yy + 11], fill=(228, 228, 232))
        t = img.resize((cw - 20, cw - 20), Image.LANCZOS)
        checker.paste(t, (0, 0), t)
        prev.paste(checker, (x, y))
        d.text((x, y + cw - 18), name, fill=(30, 30, 30))
    prev.save(os.path.join(OUT, "_flowers_preview.png"))


if __name__ == "__main__":
    imgs = {}
    for name, spec in SMALL.items():
        img = build_small(name, spec)
        p = os.path.join(OUT, f"{name}.png"); img.save(p)
        imgs[name] = img
        a = img.split()[3]; px = list(a.getdata())
        print("small %-22s 不透明 %2.0f%%" % (name, 100 * sum(1 for v in px if v > 128) / len(px)))
    for name, spec in TALL.items():
        top, bot = build_tall(name, spec)
        top.save(os.path.join(OUT, f"{name}_top.png"))
        bot.save(os.path.join(OUT, f"{name}_bottom.png"))
        imgs[name + "_top"] = top; imgs[name + "_bottom"] = bot
        print("tall  %-22s top/bottom 已存" % name)
    preview(imgs)
    print("preview saved ->", OUT)
