# -*- coding: utf-8 -*-
"""
由 3 张 AI 写实织物底图，程序化染色生成 16 色羊毛 / 床 / 旗帜贴图（纯 Pillow）。
- 底图右下角有浅水印 -> 裁掉
- 用镜像拼贴法做无缝（随机织物纹理，对称不明显，接缝为 0）
- 用 Minecraft 标准 16 色羊毛色板染色，保留织物明暗起伏

输出：
  block/<color>_wool.png        256x256  (16)
  entity/bed/<color>.png        512x256  (16)  原版 64x32 的 8 倍，保持 2:1
  entity/banner/<color>_banner.png 256x256 (16)
"""
import os, glob, math
from PIL import Image, ImageDraw

BASE = r"D:\WorkSpace(WB)\2026-11-17-20-32-26"
SRC = os.path.join(BASE, "_tex_source", "wool_ai")
OUT = os.path.join(BASE, "_wool_final")
os.makedirs(OUT, exist_ok=True)

# 3 张底图（按时间戳对应：羊毛绒 / 旗帜帆布 / 床品细织）
F_WOOL   = os.path.join(SRC, "A_seamless_tileable_top_down_f_2026-11-21T06-15-33.png")
F_BANNER = os.path.join(SRC, "A_seamless_tileable_top_down_f_2026-11-21T06-16-01.png")
F_BED    = os.path.join(SRC, "A_seamless_tileable_top_down_f_2026-11-21T06-16-04.png")

# Minecraft 标准 16 色羊毛色板（wiki 值）
COLORS = [
    ("white",      (249, 255, 254), "白色"),
    ("light_gray", (157, 157, 151), "淡灰色"),
    ("gray",       (71, 79, 82),    "灰色"),
    ("black",      (29, 29, 33),    "黑色"),
    ("brown",      (131, 84, 50),   "棕色"),
    ("red",        (176, 46, 38),   "红色"),
    ("orange",     (249, 128, 29),  "橙色"),
    ("yellow",     (254, 216, 61),  "黄色"),
    ("lime",       (128, 199, 31),  "黄绿色"),
    ("green",      (59, 177, 54),   "绿色"),
    ("cyan",       (22, 156, 156),  "青色"),
    ("light_blue", (58, 179, 218),  "淡蓝色"),
    ("blue",       (60, 68, 170),   "蓝色"),
    ("purple",     (137, 50, 184),  "紫色"),
    ("magenta",    (199, 78, 189),  "品红色"),
    ("pink",       (243, 139, 170), "粉红色"),
]


def crop_nomark(path, ratio=(1, 1)):
    """裁掉右下角水印，并按目标宽高比取区域。"""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    rw, rh = ratio
    # 先按目标比例取最大居中偏上的矩形，再向内缩到 88% 去水印
    if rw / rh > w / h:
        ch = int(w * rh / rw)
        box = (0, 0, w, ch)
    else:
        cw = int(h * rw / rh)
        box = (0, 0, cw, h)
    x0, y0, x1, y1 = box
    iw, ih = x1 - x0, y1 - y0
    m = int(min(iw, ih) * 0.06)
    return im.crop((x0, y0, x1 - m, y1 - m))


def seamless_blend(im, border=40):
    """
    边缘渐变融合无缝：把左右/上下边缘按到边界的距离渐变拉向对边均值。
    相比镜像拼贴法，不会在随机织物上产生对称花纹（羊毛/布料本无对称结构）。
    """
    px = im.load()
    w, h = im.size
    b = min(border, w // 4, h // 4)
    for i in range(b):
        t = 1.0 - i / b  # 边缘 i=0 时权重 1（完全取均值），向内递减
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


def gen_layer(src_path, size, strength=1.7):
    """返回 (灰度基准图 L) —— 无缝化后的织物明暗，供多色复用。"""
    im = crop_nomark(src_path, ratio=(size[0] / size[1], 1))
    im = im.resize(size, Image.LANCZOS)
    im = seamless_blend(im)
    return im.convert("L"), strength


def tint(gray, strength, base):
    """把灰度织物场染成 base 色：以 base 为中间调，按相对明暗起伏上下浮动。"""
    gp = gray.load()
    w, h = gray.size
    # 统计均值用于相对起伏
    hist = gray.histogram()
    mean = sum(i * hist[i] for i in range(256)) / (w * h)
    if mean < 1:
        mean = 1
    out = Image.new("RGB", (w, h))
    op = out.load()
    r0, g0, b0 = base
    for y in range(h):
        for x in range(w):
            delta = (gp[x, y] - mean) / mean          # 相对起伏，通常 ±0.15
            f = max(0.45, min(1.55, 1.0 + strength * delta))
            op[x, y] = (min(255, int(r0 * f)),
                        min(255, int(g0 * f)),
                        min(255, int(b0 * f)))
    return out


def seam_diff(path):
    im = Image.open(path).convert("RGB")
    p = im.load(); w, h = im.size
    dl = dt = 0
    for i in range(h):
        a, b = p[0, i], p[w - 1, i]
        dl += abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2])
    for i in range(w):
        a, b = p[i, 0], p[i, h - 1]
        dt += abs(a[0]-b[0]) + abs(a[1]-b[1]) + abs(a[2]-b[2])
    return dl / h / 3, dt / w / 3


if __name__ == "__main__":
    print("Preparing seamless grayscale bases ...")
    g_wool, s_wool = gen_layer(F_WOOL, (256, 256), strength=2.0)
    g_banner, s_banner = gen_layer(F_BANNER, (256, 256), strength=1.5)
    g_bed, s_bed = gen_layer(F_BED, (512, 256), strength=1.4)

    for name, base, cn in COLORS:
        tint(g_wool, s_wool, base).save(os.path.join(OUT, f"{name}_wool.png"))
        tint(g_banner, s_banner, base).save(os.path.join(OUT, f"{name}_banner.png"))
        tint(g_bed, s_bed, base).save(os.path.join(OUT, f"{name}_bed.png"))
        print(f"  {name:11s} {cn}")

    # 接缝抽检
    for fn in ("white_wool.png", "red_wool.png", "white_banner.png", "white_bed.png"):
        l, t = seam_diff(os.path.join(OUT, fn))
        print(f"  seam {fn:20s} L={l:4.1f} T={t:4.1f}")

    # 预览：羊毛 16 色 4x4 + 床 + 旗帜 各一行缩略
    cw, ch = 96, 96
    prev = Image.new("RGB", (4 * cw * 3 + 40, 4 * ch + 3 * (ch // 2 + 24) + 40), (28, 28, 32))
    d = ImageDraw.Draw(prev)
    ox, oy = 10, 10
    # 羊毛区 4x4
    for i, (name, _b, _cn) in enumerate(COLORS):
        r, c = divmod(i, 4)
        im = Image.open(os.path.join(OUT, f"{name}_wool.png")).resize((cw, ch))
        prev.paste(im, (ox + c * cw, oy + r * ch))
    d.text((ox, oy + 4 * ch + 2), "WOOL x16", fill=(235, 235, 235))
    # 床区 8x2
    by = oy + 4 * ch + 20
    for i, (name, _b, _cn) in enumerate(COLORS):
        r, c = divmod(i, 8)
        im = Image.open(os.path.join(OUT, f"{name}_bed.png")).resize((cw, ch // 2))
        prev.paste(im, (ox + c * cw, by + r * (ch // 2 + 2)))
    d.text((ox, by + 2 * (ch // 2 + 2) + 2), "BED x16 (2:1)", fill=(235, 235, 235))
    # 旗帜区 8x2
    fy = by + 2 * (ch // 2 + 2) + 18
    for i, (name, _b, _cn) in enumerate(COLORS):
        r, c = divmod(i, 8)
        im = Image.open(os.path.join(OUT, f"{name}_banner.png")).resize((cw, ch // 2))
        prev.paste(im, (ox + c * cw, fy + r * (ch // 2 + 2)))
    d.text((ox, fy + 2 * (ch // 2 + 2) + 2), "BANNER x16", fill=(235, 235, 235))
    p = os.path.join(OUT, "_preview.png")
    prev.save(p)
    print("preview:", p)
    print("DONE ->", OUT)
