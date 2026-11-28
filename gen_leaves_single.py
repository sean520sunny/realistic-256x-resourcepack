# -*- coding: utf-8 -*-
"""
单层叶片版树叶贴图（纯 Pillow，无 numpy）。

源图特点：AI 直接生成的「单层叶片、互不重叠、纯黑背景」平铺图，
实测平铺周期正好 256px（自相关匹配率 99.5%），黑背景与叶片亮度分界干净。

流程：
1. 取无水印的 256×256 区块（水印在右下 (3,3) 块，故取 (0,0) 块）。
   因为周期=256，取任一完整周期块都能无缝平铺。
2. 按亮度抠掉黑背景 -> alpha（带窄过渡，边缘不硬）。
3. 颜色：Java 版树叶是灰度+生物群系染色，故收敛到中性绿基调，避免染色后过暗。
"""
import os
from PIL import Image, ImageDraw, ImageFilter

BASE = r"D:\WorkSpace(WB)\2026-11-17-20-32-26"
SRC = os.path.join(BASE, "_tex_source", "leaves_ai")
OUT = os.path.join(BASE, "_leaves_out")
os.makedirs(OUT, exist_ok=True)
N = 256


def build_single_layer_leaves(src_path, base_color, sat_keep=0.92,
                              bg_hi=46, fade=18, ox=0, oy=0):
    """
    bg_hi: 亮度 <= bg_hi 视为背景（全透明）
    fade:  bg_hi ~ bg_hi+fade 之间做渐变过渡，让叶缘柔和
    """
    im = Image.open(src_path).convert("RGB")
    tile = im.crop((ox, oy, ox + N, oy + N))

    gray = tile.convert("L")
    gp = gray.load(); sp = tile.load()

    out = Image.new("RGBA", (N, N)); op = out.load()
    br, bgc, bb = base_color
    for y in range(N):
        for x in range(N):
            g = gp[x, y]
            if g <= bg_hi:
                op[x, y] = (0, 0, 0, 0)
                continue
            if g < bg_hi + fade:
                a = int(255 * (g - bg_hi) / fade)
            else:
                a = 255
            sr, sg, sb = sp[x, y]
            lum = g / 255.0
            mix_r = sr * sat_keep + br * (1 - sat_keep)
            mix_g = sg * sat_keep + bgc * (1 - sat_keep)
            mix_b = sb * sat_keep + bb * (1 - sat_keep)
            f = 0.66 + 0.72 * lum
            avg = (mix_r + mix_g + mix_b) / 3
            mix_r = avg + (mix_r - avg) * 1.40
            mix_g = avg + (mix_g - avg) * 1.40
            mix_b = avg + (mix_b - avg) * 1.40
            r = max(0, min(255, int(mix_r * f)))
            gg = max(0, min(255, int(mix_g * f)))
            b = max(0, min(255, int(mix_b * f)))
            op[x, y] = (r, gg, b, a)
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
    src = os.path.join(SRC, "A_seamless_tileable_top_down_f_2026-11-21T13-52-15.png")
    oak = build_single_layer_leaves(src, (96, 132, 62), sat_keep=0.92,
                                    bg_hi=46, fade=18, ox=0, oy=0)
    p = os.path.join(OUT, "oak_leaves.png"); oak.save(p)
    a = oak.split()[3]; px = list(a.getdata())
    print("saved", p, oak.size, "| 透明比例 %.0f%%" % (100 * sum(1 for v in px if v == 0) / len(px)))
    showcase(oak, os.path.join(OUT, "_oak_showcase.png"))
    print("showcase saved")
