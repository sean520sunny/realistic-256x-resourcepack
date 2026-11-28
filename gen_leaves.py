# -*- coding: utf-8 -*-
"""
由 AI 写实树叶底图生成 Minecraft 树叶贴图（纯 Pillow，无 numpy）。

核心思路（对应要求：透明必须来自真实叶片间隙，而不是在叶片上抠洞）：
1. 裁右下角 AI 水印。
2. 边缘渐变融合做无缝（树叶随机簇状，不能镜像，否则对称太明显）。
3. 用亮度生成「叶片掩膜」：
   - 叶片（亮）置白，间隙（暗）置黑；
   - 做**闭运算**（先膨胀后腐蚀）把叶片内部的阴影小斑填平，叶片本体保持实心，
     绝不会被抠出洞；
   - 只有叶片丛之间真正的大间隙，闭运算也填不平，才会透光。
4. 间隙里再随机保留少量小叶块（低频噪声控制），其余留空白透明。
5. 颜色：Java 版树叶是灰度图 + 生物群系染色，故用「AI 亮度层次 + 中性绿基调」，
   避免游戏染色后过暗。
"""
import os
from PIL import Image, ImageDraw, ImageFilter

BASE = r"D:\WorkSpace(WB)\2026-11-17-20-32-26"
SRC = os.path.join(BASE, "_tex_source", "leaves_ai")
OUT = os.path.join(BASE, "_leaves_out")
os.makedirs(OUT, exist_ok=True)
N = 256


def crop_nomark(im):
    """裁掉右下角水印：取左上 88% 方形。"""
    w, h = im.size
    side = int(min(w, h) * 0.88)
    return im.crop((0, 0, side, side))


def seamless_blend(im, border=48):
    """边缘渐变融合：左右/上下边缘按距离渐变拉向对边均值，避免对称花纹。"""
    px = im.load(); w, h = im.size
    b = min(border, w // 4, h // 4)
    for i in range(b):
        t = 1.0 - i / b
        for y in range(h):
            l = px[i, y]; r = px[w - 1 - i, y]
            px[i, y] = tuple(int((l[c] + r[c]) / 2 * t + l[c] * (1 - t)) for c in range(3))
            px[w - 1 - i, y] = tuple(int((l[c] + r[c]) / 2 * t + r[c] * (1 - t)) for c in range(3))
    for i in range(b):
        t = 1.0 - i / b
        for x in range(w):
            a = px[x, i]; d = px[x, h - 1 - i]
            px[x, i] = tuple(int((a[c] + d[c]) / 2 * t + a[c] * (1 - t)) for c in range(3))
            px[x, h - 1 - i] = tuple(int((a[c] + d[c]) / 2 * t + d[c] * (1 - t)) for c in range(3))
    return im


def noise_periodic(cx, cy, seed):
    """周期化值噪声（环绕取样，保证无缝）。"""
    import random
    r = random.Random(seed)
    grid = [[r.randint(0, 255) for _ in range(cx)] for _ in range(cy)]
    out = Image.new("L", (N, N)); px = out.load()
    for y in range(N):
        fy = y * cy / N; y0 = int(fy); ty = fy - y0; ty = ty * ty * (3 - 2 * ty)
        gy0, gy1 = grid[y0 % cy], grid[(y0 + 1) % cy]
        for x in range(N):
            fx = x * cx / N; x0 = int(fx); tx = fx - x0; tx = tx * tx * (3 - 2 * tx)
            top = gy0[x0 % cx] * (1 - tx) + gy0[(x0 + 1) % cx] * tx
            bot = gy1[x0 % cx] * (1 - tx) + gy1[(x0 + 1) % cx] * tx
            px[x, y] = int(top * (1 - ty) + bot * ty)
    return out


def build_leaf_mask(gray, thresh=100, close=9, patch_noise=None, keep_ratio=0.0,
                    seed_t=None, open_k=7):
    """
    生成叶片 alpha 掩膜（分层剥离版）：
      seed_t   取「亮部」当种子阈值（较高）。上层叶片受光更足、更亮，用它当种子
      close    闭运算核：把种子的叶片内部补实成完整叶片
      open_k   开运算核：把叶片之间粘在一起的部分切开、去掉下层露出的碎块
      thresh   保底阈值（未用 seed_t 时按此二值化）
    """
    base = seed_t if seed_t is not None else thresh
    leaf = gray.point(lambda v: 255 if v >= base else 0)
    # 闭运算补齐成完整叶片（上层叶片受光 -> 整个叶面被填实）
    leaf = leaf.filter(ImageFilter.MaxFilter(close))
    leaf = leaf.filter(ImageFilter.MinFilter(close))
    # 开运算：切开叶片之间的粘连、抹掉下层露出的小碎块 -> 只留最上层完整叶片
    leaf = leaf.filter(ImageFilter.MinFilter(open_k))
    leaf = leaf.filter(ImageFilter.MaxFilter(open_k))
    # 模糊磨圆边缘
    leaf = leaf.filter(ImageFilter.GaussianBlur(2.0))
    leaf = leaf.point(lambda v: 255 if v >= 128 else 0)

    if patch_noise is not None and keep_ratio > 0:
        cut = int(255 * keep_ratio)
        cover = patch_noise.point(lambda v: 255 if v < cut else 0)
        cover = cover.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
        cover = cover.filter(ImageFilter.GaussianBlur(1.2))
        cover = cover.point(lambda v: 255 if v >= 128 else 0)
        merged = Image.new("L", (N, N)); mp = merged.load()
        lp = leaf.load(); cp = cover.load()
        for y in range(N):
            for x in range(N):
                mp[x, y] = max(lp[x, y], cp[x, y])
        leaf = merged
    return leaf


def build_leaves(src_path, base_color, sat_keep=0.78, thresh=100, close=9,
                 gap_keep_ratio=0.16, seed_t=None, open_k=7):
    im = crop_nomark(Image.open(src_path).convert("RGB"))
    im = im.resize((N, N), Image.LANCZOS)
    im = seamless_blend(im)

    gray = im.convert("L")
    src = im.load(); gp = gray.load()

    patch_noise = noise_periodic(7, 7, 4242)
    mask = build_leaf_mask(gray, thresh=thresh, close=close,
                           patch_noise=patch_noise, keep_ratio=gap_keep_ratio,
                           seed_t=seed_t, open_k=open_k)
    mpx = mask.load()

    out = Image.new("RGBA", (N, N)); op = out.load()
    br, bg, bb = base_color
    for y in range(N):
        for x in range(N):
            g = gp[x, y]
            sr, sg, sb = src[x, y]
            if mpx[x, y] == 0:
                op[x, y] = (0, 0, 0, 0)
                continue
            lum = g / 255.0
            mix_r = sr * sat_keep + br * (1 - sat_keep)
            mix_g = sg * sat_keep + bg * (1 - sat_keep)
            mix_b = sb * sat_keep + bb * (1 - sat_keep)
            f = 0.52 + 0.82 * lum
            avg = (mix_r + mix_g + mix_b) / 3
            mix_r = avg + (mix_r - avg) * 1.28
            mix_g = avg + (mix_g - avg) * 1.28
            mix_b = avg + (mix_b - avg) * 1.28
            r = max(0, min(255, int(mix_r * f)))
            gg = max(0, min(255, int(mix_g * f)))
            b = max(0, min(255, int(mix_b * f)))
            op[x, y] = (r, gg, b, 255)
    return out


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
    # A 方案 + 分层剥离：只保留最上层完整叶片，下层露出部分扣除
    src = os.path.join(SRC, "A_seamless_tileable_top_down_f_2026-11-21T13-44-09.png")
    oak = build_leaves(src, (96, 132, 62), sat_keep=0.85, close=9,
                       gap_keep_ratio=0.0, seed_t=128, open_k=7)
    p = os.path.join(OUT, "oak_leaves.png"); oak.save(p)
    a = oak.split()[3]; px = list(a.getdata())
    print("saved", p, oak.size, "| 透明比例 %.0f%%" % (100 * sum(1 for v in px if v == 0) / len(px)))
    showcase(oak, os.path.join(OUT, "_oak_showcase.png"))
    print("showcase saved")
