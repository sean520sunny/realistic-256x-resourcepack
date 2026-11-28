# -*- coding: utf-8 -*-
"""
树叶贴图：把每片叶子抠出来，随机旋转 + 随机落位重排，打散 AI 图的规整网格。
平铺无缝靠「环绕绘制」保证（贴在 x±N / y±N 九个位置各画一次）。

源图：AI 生成的单层橡树叶 + 纯黑背景（叶尖首尾相接串成竖列，需腐蚀断开）。
"""
import os
import random
from collections import deque
from PIL import Image, ImageFilter, ImageDraw

BASE = r"D:\WorkSpace(WB)\2026-11-17-20-32-26"
SRC = os.path.join(BASE, "_tex_source", "leaves_ai")
OUT = os.path.join(BASE, "_leaves_out")
os.makedirs(OUT, exist_ok=True)
N = 256


def extract_leaf_sprites(src_path, analyze_size=512, thresh=60, erode=5, min_area=600,
                         src_crop=(0, 0, 780, 800)):
    """从黑底图里抠出每片叶子，返回 RGBA sprite 列表。
    src_crop: 先裁掉水印区域（水印在右下角 880,930 起）。
    """
    im = Image.open(src_path).convert("RGB")
    im = im.crop(src_crop)  # 避开右下角水印
    work = im.resize((analyze_size, analyze_size), Image.LANCZOS)
    g = work.convert("L")
    binary = g.point(lambda v: 255 if v > thresh else 0)

    # 腐蚀断开细连接
    er = binary.filter(ImageFilter.MinFilter(erode))
    W, H = er.size
    ep = er.load()
    seen = [[0] * W for _ in range(H)]
    labels = []
    for y in range(H):
        for x in range(W):
            if ep[x, y] > 128 and seen[y][x] == 0:
                q = deque([(x, y)]); seen[y][x] = 1
                pts = []; area = 0
                while q:
                    cx, cy = q.popleft(); area += 1; pts.append((cx, cy))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = cx + dx, cy + dy
                        if 0 <= nx < W and 0 <= ny < H and seen[ny][nx] == 0 and ep[nx, ny] > 128:
                            seen[ny][nx] = 1; q.append((nx, ny))
                if area >= min_area:
                    labels.append(pts)

    bp = binary.load()
    spans = []
    for pts in labels:
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        # 把腐蚀后的点扩回去（膨胀同核尺寸），恢复叶片原先的完整轮廓
        pad = erode + 2
        bx0, bx1 = max(0, x0 - pad), min(W - 1, x1 + pad)
        by0, by1 = max(0, y0 - pad), min(H - 1, y1 + pad)
        w, h = bx1 - bx0 + 1, by1 - by0 + 1
        sprite = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        sp = sprite.load()
        ptset = set(pts)
        # 以「腐蚀点为中心」把附近属于原二值的像素收进来
        for (px, py) in pts:
            for dy in range(-pad, pad + 1):
                for dx in range(-pad, pad + 1):
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < W and 0 <= ny < H and bp[nx, ny] > 128:
                        # 距离约束，避免把别的叶子拉进来
                        if dx * dx + dy * dy <= pad * pad:
                            r, gg, b = work.getpixel((nx, ny))
                            sp[nx - bx0, ny - by0] = (r, gg, b, 255)
        spans.append(sprite)
    return spans


def tint_neutral(img, base=(96, 132, 62), sat_keep=0.92, sat_boost=1.40, lo=0.66, span=0.72):
    """中性绿基调 + 提饱和，避免游戏染色后过暗。"""
    px = img.load(); w, h = img.size
    br, bg, bb = base
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255.0
            mr = r * sat_keep + br * (1 - sat_keep)
            mg = g * sat_keep + bg * (1 - sat_keep)
            mb = b * sat_keep + bb * (1 - sat_keep)
            f = lo + span * lum
            avg = (mr + mg + mb) / 3
            mr = avg + (mr - avg) * sat_boost
            mg = avg + (mg - avg) * sat_boost
            mb = avg + (mb - avg) * sat_boost
            px[x, y] = (max(0, min(255, int(mr * f))),
                        max(0, min(255, int(mg * f))),
                        max(0, min(255, int(mb * f))), a)
    return img


def paste_wrap(canvas, sprite, x, y):
    """环绕绘制：跨边界部分在对侧同时画出，保证平铺无缝。"""
    for ox in (-N, 0, N):
        for oy in (-N, 0, N):
            canvas.paste(sprite, (x + ox, y + oy), sprite)


def overlap_ratio(canvas_alpha, sprite_alpha, x, y):
    """估算把 sprite 放在 (x,y) 时与已有叶片的 alpha 重叠比例。"""
    sw, sh = sprite_alpha.size
    sp = sprite_alpha.load(); cp = canvas_alpha.load()
    inter = 0; tot = 0
    for yy in range(0, sh, 2):
        for xx in range(0, sw, 2):
            if sp[xx, yy] > 128:
                tot += 1
                cx = (x + xx) % N; cy = (y + yy) % N
                if cp[cx, cy] > 128:
                    inter += 1
    return (inter / tot) if tot else 1.0


def build_scattered(sprites, seed=20261121, target_cov=0.68, max_overlap=0.20,
                    scale_range=(0.45, 0.72)):
    rnd = random.Random(seed)
    canvas = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    occ = Image.new("L", (N, N), 0)  # alpha 占用图
    placed = 0; attempts = 0
    target_px = int(N * N * target_cov)
    covered = 0
    while covered < target_px and attempts < 3000:
        attempts += 1
        sp = rnd.choice(sprites)
        sc = rnd.uniform(*scale_range)
        w = max(8, int(sp.width * sc)); h = max(8, int(sp.height * sc))
        s = sp.resize((w, h), Image.LANCZOS)
        s = s.rotate(rnd.uniform(0, 360), expand=True, resample=Image.BICUBIC)
        x = rnd.randint(0, N - 1); y = rnd.randint(0, N - 1)
        sa = s.split()[3]
        ov = overlap_ratio(occ, sa, x, y)
        if ov > max_overlap:
            continue
        paste_wrap(canvas, s, x, y)
        # 更新占用图（并集）
        tmp = Image.new("L", (N, N), 0)
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                tmp.paste(sa, (x + ox, y + oy))
        op = occ.load(); tp = tmp.load()
        for yy in range(N):
            for xx in range(N):
                if tp[xx, yy] > op[xx, yy]:
                    op[xx, yy] = tp[xx, yy]
        covered = sum(1 for yy in range(N) for xx in range(N) if op[xx, yy] > 128)
        placed += 1
    return canvas, placed, attempts, covered / (N * N)


def showcase(img, path):
    S = 380
    prev = Image.new("RGB", (S * 2 + 60, S + 70), (250, 250, 252)); d = ImageDraw.Draw(prev)
    chk = Image.new("RGB", (S, S), (255, 255, 255)); dc = ImageDraw.Draw(chk)
    for yy in range(0, S, 20):
        for xx in range(0, S, 20):
            if (xx // 20 + yy // 20) % 2:
                dc.rectangle([xx, yy, xx + 19, yy + 19], fill=(226, 226, 230))
    big = img.resize((S, S), Image.LANCZOS); chk.paste(big, (0, 0), big); prev.paste(chk, (15, 45))
    d.text((15, 20), 'oak_leaves.png 256x256 (checker = transparent)', fill=(40, 40, 40))
    tw, th = S // 2, S // 2
    tilebg = Image.new("RGB", (S, S), (70, 110, 55)); t = img.resize((tw, th), Image.LANCZOS)
    for ty in range(2):
        for tx in range(2):
            tilebg.paste(t, (tx * tw, ty * th), t)
    prev.paste(tilebg, (S + 45, 45))
    d.text((S + 45, 20), '2x2 tiled (seamless check)', fill=(40, 40, 40))
    prev.save(path)


if __name__ == "__main__":
    src = os.path.join(SRC, "A_seamless_tileable_top_down_f_2026-11-21T13-52-15.png")
    sprites = extract_leaf_sprites(src)
    print("提取叶片:", len(sprites), "片 | 尺寸范围:",
          min(s.width for s in sprites), "~", max(s.width for s in sprites))
    sprites = [tint_neutral(s) for s in sprites]
    img, placed, attempts, cov = build_scattered(sprites, target_cov=0.68, max_overlap=0.20, scale_range=(0.45, 0.72))
    p = os.path.join(OUT, "oak_leaves.png"); img.save(p)
    a = img.split()[3]; px = list(a.getdata())
    print("saved", p, "| 放置 %d 片(尝试 %d) | 覆盖 %.0f%% | 透明 %.0f%%" %
          (placed, attempts, cov * 100, 100 * sum(1 for v in px if v == 0) / len(px)))
    showcase(img, os.path.join(OUT, "_oak_showcase.png"))
    print("showcase saved")
