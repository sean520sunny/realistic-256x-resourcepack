# -*- coding: utf-8 -*-
"""
由 2 张 AI 白色写实底图，程序化染色生成 16 色混凝土 + 16 色混凝土粉末（纯 Pillow）。
流程同羊毛：裁水印 -> 边缘渐变融合无缝 -> Minecraft 标准 16 色板染色 -> 亮度归一压淡杂质斑点。

输出：
  block/<color>_concrete.png        256x256  (16)
  block/<color>_concrete_powder.png 256x256  (16)
"""
import os
from PIL import Image, ImageDraw

BASE = r"D:\WorkSpace(WB)\2026-11-17-20-32-26"
SRC = os.path.join(BASE, "_tex_source", "concrete_ai")
OUT = os.path.join(BASE, "_concrete_final")
os.makedirs(OUT, exist_ok=True)

# 两张底图（按质感对应：粗颗粒=粉末，细密=混凝土）
F_CONCRETE = os.path.join(SRC, "A_seamless_tileable_top_down_f_2026-11-21T10-19-37.png")
F_POWDER   = os.path.join(SRC, "A_seamless_tileable_top_down_f_2026-11-21T10-19-34.png")

# Minecraft 标准 16 色「混凝土」色板（wiki 值）
COLORS = [
    ("white",      (237, 237, 237), "白色"),
    ("light_gray", (157, 162, 165), "淡灰色"),
    ("gray",       (85, 89, 97),    "灰色"),
    ("black",      (20, 22, 30),    "黑色"),
    ("brown",      (115, 77, 46),   "棕色"),
    ("red",        (160, 39, 41),   "红色"),
    ("orange",     (215, 106, 19),  "橙色"),
    ("yellow",     (244, 193, 28),  "黄色"),
    ("lime",       (97, 193, 34),   "黄绿色"),
    ("green",      (50, 124, 48),   "绿色"),
    ("cyan",       (27, 133, 149),  "青色"),
    ("light_blue", (66, 151, 214),  "淡蓝色"),
    ("blue",       (43, 66, 157),   "蓝色"),
    ("purple",     (114, 50, 155),  "紫色"),
    ("magenta",    (171, 45, 137),  "品红色"),
    ("pink",       (212, 112, 141), "粉红色"),
]


def crop_nomark(path):
    """裁掉右下角水印，取左上 88% 方形。"""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    side = int(min(w, h) * 0.88)
    return im.crop((0, 0, side, side))


def seamless_blend(im, border=40):
    """边缘渐变融合：左右/上下边缘渐变拉向对边均值，无对称花纹。"""
    px = im.load(); w, h = im.size
    b = min(border, w // 4, h // 4)
    for i in range(b):
        t = 1.0 - i / b
        for y in range(h):
            l = px[i, y]; r = px[w - 1 - i, y]
            px[i, y] = tuple(int((l[c]+r[c])/2*t + l[c]*(1-t)) for c in range(3))
            px[w-1-i, y] = tuple(int((l[c]+r[c])/2*t + r[c]*(1-t)) for c in range(3))
    for i in range(b):
        t = 1.0 - i / b
        for x in range(w):
            a = px[x, i]; d = px[x, h-1-i]
            px[x, i] = tuple(int((a[c]+d[c])/2*t + a[c]*(1-t)) for c in range(3))
            px[x, h-1-i] = tuple(int((a[c]+d[c])/2*t + d[c]*(1-t)) for c in range(3))
    return im


def gen_layer(path, size=256, strength=1.6, clip=0.18):
    """
    返回 (灰度织物场, strength)。
    灰度做对比度压缩与亮部归一：把 AI 图的深色杂质斑点压淡，避免染色后显脏。
    """
    im = crop_nomark(path).resize((size, size), Image.LANCZOS)
    im = seamless_blend(im)
    g = im.convert("L")
    gp = g.load()
    hist = g.histogram()
    mean = sum(i*hist[i] for i in range(256)) / (size*size)
    # 相对起伏限制在 ±clip，压掉极端暗点与亮斑
    out = Image.new("L", (size, size))
    op = out.load()
    for y in range(size):
        for x in range(size):
            delta = max(-clip, min(clip, (gp[x, y]-mean)/mean))
            op[x, y] = max(0, min(255, int(mean*(1+delta))))
    return out, strength


def tint(gray, strength, base):
    """把灰度场染成 base 色，保留明暗起伏。"""
    gp = gray.load(); w, h = gray.size
    hist = gray.histogram()
    mean = sum(i*hist[i] for i in range(256))/(w*h) or 1
    out = Image.new("RGB", (w, h)); op = out.load()
    r0, g0, b0 = base
    for y in range(h):
        for x in range(w):
            delta = (gp[x, y]-mean)/mean
            f = max(0.45, min(1.45, 1.0 + strength*delta))
            op[x, y] = (min(255,int(r0*f)), min(255,int(g0*f)), min(255,int(b0*f)))
    return out


def seam_diff(path):
    im = Image.open(path).convert("RGB"); p = im.load(); w, h = im.size
    dl = dt = 0
    for i in range(h):
        a, b = p[0,i], p[w-1,i]
        dl += abs(a[0]-b[0])+abs(a[1]-b[1])+abs(a[2]-b[2])
    for i in range(w):
        a, b = p[i,0], p[i,h-1]
        dt += abs(a[0]-b[0])+abs(a[1]-b[1])+abs(a[2]-b[2])
    return dl/h/3, dt/w/3


if __name__ == "__main__":
    print("Preparing seamless grayscale bases ...")
    g_conc, s_conc = gen_layer(F_CONCRETE, strength=1.5, clip=0.15)
    g_pow,  s_pow  = gen_layer(F_POWDER,   strength=1.9, clip=0.20)

    for name, base, cn in COLORS:
        tint(g_conc, s_conc, base).save(os.path.join(OUT, f"{name}_concrete.png"))
        tint(g_pow, s_pow, base).save(os.path.join(OUT, f"{name}_concrete_powder.png"))
        print(f"  {name:11s} {cn}")

    for fn in ("white_concrete.png", "red_concrete.png", "white_concrete_powder.png"):
        l, t = seam_diff(os.path.join(OUT, fn))
        print(f"  seam {fn:26s} L={l:4.1f} T={t:4.1f}")

    # 预览：混凝土 4x4 + 粉末 4x4
    cw, ch = 100, 100
    # 画布高度贴合内容：4 行色块 + 底部标签，不留大片空白
    prev = Image.new("RGB", (4*cw*2+30, 4*ch+40), (28,28,32))
    d = ImageDraw.Draw(prev)
    ox, oy = 10, 10
    for i, (name, _b, _cn) in enumerate(COLORS):
        r, c = divmod(i, 4)
        prev.paste(Image.open(os.path.join(OUT, f"{name}_concrete.png")).resize((cw,ch)), (ox+c*cw, oy+r*ch))
        prev.paste(Image.open(os.path.join(OUT, f"{name}_concrete_powder.png")).resize((cw,ch)), (ox+4*cw+10+c*cw, oy+r*ch))
    d.text((ox, oy+4*ch+3), "CONCRETE (left)   |   CONCRETE POWDER (right)", fill=(235,235,235))
    p = os.path.join(OUT, "_preview.png")
    prev.save(p)
    print("preview:", p)
    print("DONE ->", OUT)
