# -*- coding: utf-8 -*-
"""
由 1 张 AI 白色郁金香底图，生成 4 色郁金香（红/橙/白/粉）写实贴图（纯 Pillow）。

关键：
- 抠掉黑背景 -> alpha。
- 花瓣与茎叶分离：花瓣饱和度低且亮（sat<0.35, lum>100），茎叶饱和高偏绿。
  只给花瓣染色，茎叶保持绿色。
- 避开右下角水印（提取时忽略 x>W*0.8 且 y>H*0.9 的区域）。
- 输出 256×256 RGBA，供 block/<color>_tulip.png 使用。
"""
import os
from PIL import Image, ImageDraw

BASE = r"D:\WorkSpace(WB)\2026-11-17-20-32-26"
SRC = os.path.join(BASE, "_tex_source", "tulip_ai")
OUT = os.path.join(BASE, "_tulips_out")
os.makedirs(OUT, exist_ok=True)
N = 256
SRC_FILE = os.path.join(SRC, "A_single_photorealistic_white__2026-11-28T01-54-03.png")

# 四种花瓣目标色（不含茎叶）
PETALS = {
    "red":    (206, 46, 42),
    "orange": (238, 133, 35),
    "white":  (245, 243, 236),
    "pink":   (232, 138, 186),
}


def prepare(im, out_size=N):
    """裁水印、抠黑底、按包围盒居中缩放，返回 RGBA 植物图。"""
    W, H = im.size
    wm_x, wm_y = int(W * 0.80), int(H * 0.90)
    px = im.load()
    # 找主体包围盒（排除水印区）
    minx = miny = 10**9; maxx = maxy = -1
    for y in range(0, H, 2):
        for x in range(0, W, 2):
            if x > wm_x and y > wm_y:
                continue
            r, g, b = px[x, y]
            if max(r, g, b) > 42:
                minx = min(minx, x); maxx = max(maxx, x)
                miny = min(miny, y); maxy = max(maxy, y)
    # 留一点边距
    pad = 12
    minx = max(0, minx - pad); miny = max(0, miny - pad)
    maxx = min(W - 1, maxx + pad); maxy = min(H - 1, maxy + pad)
    crop = im.crop((minx, miny, maxx + 1, maxy + 1)).convert("RGBA")
    cp = crop.load()
    # 抠黑底：按亮度做 alpha
    g = crop.convert("L"); gp = g.load()
    for y in range(crop.height):
        for x in range(crop.width):
            lum = gp[x, y]
            if lum <= 24:
                a = 0
            elif lum < 56:
                a = int(255 * (lum - 24) / 32)
            else:
                a = 255
            r, gg, b, _ = cp[x, y]
            cp[x, y] = (r, gg, b, a)
    # 等比缩放居中到画布
    iw, ih = crop.size
    scale = min((out_size - 4) / iw, (out_size - 4) / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    crop = crop.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (out_size, out_size), (0, 0, 0, 0))
    canvas.paste(crop, ((out_size - nw) // 2, (out_size - nh) // 2), crop)
    return canvas


def find_flower_split(base):
    """找花头底部 y：从上往下扫，花头下方会出现一小段几乎全黑的细茎。"""
    a = base.split()[3]; ap = a.load()
    rows=[]
    for y in range(N):
        rows.append(sum(1 for x in range(N) if ap[x,y]>128))
    # 花头是连续的宽行；花头结束处宽度骤降。找第一个从宽变窄的位置
    for y in range(20, N-10):
        if rows[y] > 20 and rows[y+3] < rows[y]*0.5:
            return y+3
    return int(N*0.36)

def is_petal(r, g, b, y, split):
    """花瓣：位于花头区域(y<split) 且低饱和高亮；叶尖高光不再误判。"""
    if y >= split:
        return False
    mx = max(r, g, b); mn = min(r, g, b)
    sat = (mx - mn) / mx if mx else 0
    lum = (r + g + b) / 3
    return sat < 0.40 and lum > 95


def dye(base_rgba, color, split):
    """只给花瓣染色，保留明暗层次与茎叶。"""
    out = base_rgba.copy(); p = out.load()
    tr, tg, tb = color
    for y in range(N):
        for x in range(N):
            r, g, b, a = p[x, y]
            if a == 0 or not is_petal(r, g, b, y, split):
                continue
            lum = (r + g + b) / 3 / 255.0
            # 用亮度调制目标色，保留花瓣阴影/高光
            f = 0.52 + 0.85 * lum
            p[x, y] = (max(0, min(255, int(tr * f))),
                       max(0, min(255, int(tg * f))),
                       max(0, min(255, int(tb * f))), a)
    return out


def make_preview(imgs):
    names = list(imgs.keys())
    cw = N
    prev = Image.new("RGB", (cw * 4 + 50, cw + 50), (244, 244, 246)); d = ImageDraw.Draw(prev)
    checker = Image.new("RGB", (cw, cw), (255, 255, 255)); dc = ImageDraw.Draw(checker)
    for yy in range(0, cw, 16):
        for xx in range(0, cw, 16):
            if (xx // 16 + yy // 16) % 2:
                dc.rectangle([xx, yy, xx + 15, yy + 15], fill=(228, 228, 232))
    for i, name in enumerate(names):
        tile = checker.copy(); tile.paste(imgs[name], (0, 0), imgs[name])
        prev.paste(tile, (10 + i * (cw + 10), 34))
        d.text((10 + i * (cw + 10), 12), name + " tulip", fill=(40, 40, 40))
    prev.save(os.path.join(OUT, "_tulips_preview.png"))


if __name__ == "__main__":
    im = Image.open(SRC_FILE).convert("RGB")
    base = prepare(im)
    split = find_flower_split(base)
    print('花头底部 y =', split)
    imgs = {}
    for name, color in PETALS.items():
        dyed = base if name == "white" else dye(base, color, split)
        p = os.path.join(OUT, f"{name}_tulip.png")
        dyed.save(p)
        imgs[name] = dyed
        a = dyed.split()[3]; px = list(a.getdata())
        print(name, "->", p, "| 不透明 %.0f%%" % (100 * sum(1 for v in px if v > 128) / len(px)))
    make_preview(imgs)
    print("preview saved")
