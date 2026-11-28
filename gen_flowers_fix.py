# -*- coding: utf-8 -*-
"""
重做用户圈出的 7 种花 + 连带重染凋灵玫瑰（共用虞美人底图）。
底图都是单独 AI 生成的正确形态/颜色，这里只做抠黑底 + 居中缩放 + 必要染色。
"""
import os
from PIL import Image, ImageDraw

BASE = r"D:\WorkSpace(WB)\2026-11-17-20-32-26"
SRC = os.path.join(BASE, "_tex_source", "flowers_fix")
OUT = os.path.join(BASE, "_flowers_out")
N = 256

SRC_FILES = {
    "azure_bluet":       "A_single_photorealistic_azure__2026-11-28T02-24-51.png",
    "blue_orchid":       "A_photorealistic_blue_orchid_p_2026-11-28T02-24-52.png",
    "cornflower":        "A_single_photorealistic_cornfl_2026-11-28T02-31-53.png",
    "oxeye_daisy":       "A_single_photorealistic_oxeye__2026-11-28T02-24-52.png",
    "poppy":             "A_single_photorealistic_poppy__2026-11-28T02-25-15.png",
    "closed_eyeblossom": "A_single_photorealistic_closed_2026-11-28T02-25-19.png",
    "open_eyeblossom":   "A_single_photorealistic_open_e_2026-11-28T02-25-17.png",
}


def crop_nomark(im):
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
    im = im.copy(); ip = im.load()
    for y in range(wm_y, H):
        for x in range(wm_x, W):
            ip[x, y] = (0, 0, 0)
    pad = 10
    minx = max(0, minx - pad); miny = max(0, miny - pad)
    maxx = min(W - 1, maxx + pad); maxy = min(H - 1, maxy + pad)
    return im.crop((minx, miny, maxx + 1, maxy + 1)).convert("RGBA")


def to_rgba(crop, target=N, lo=24, hi=56):
    g = crop.convert("L"); gp = g.load(); cp = crop.load()
    for y in range(crop.height):
        for x in range(crop.width):
            lum = gp[x, y]
            a = 0 if lum <= lo else (int(255 * (lum - lo) / (hi - lo)) if lum < hi else 255)
            r, gg, b, _ = cp[x, y]
            cp[x, y] = (r, gg, b, a)
    iw, ih = crop.size
    sc = min((target - 4) / iw, (target - 4) / ih)
    nw, nh = max(1, int(iw * sc)), max(1, int(ih * sc))
    crop = crop.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    canvas.paste(crop, ((target - nw) // 2, (target - nh) // 2), crop)
    return canvas


def fix_cornflower_center(img):
    """矢车菊：只压真正发白的花心像素（三通道接近且极亮），保留蓝花瓣高光。"""
    out = img.copy(); p = out.load()
    cut = int(N * 0.42)
    for y in range(cut):
        for x in range(N):
            r, g, b, a = p[x, y]
            if a == 0:
                continue
            mx = max(r, g, b); mn = min(r, g, b)
            # 真正发白：极亮 + 三通道非常接近（蓝高光是 b 明显大于 r）
            if mx > 185 and (mx - mn) / mx < 0.12:
                p[x, y] = (58, 46, 128, a)
    return out


def dye_dark_stem(img, split=0.42, target=(48, 42, 54)):
    """凋灵玫瑰：花头染暗紫黑，茎叶也压成深灰（原版是深色茎叶）。"""
    out = img.copy(); p = out.load()
    tr, tg, tb = target; cut = int(N * split)
    for y in range(N):
        for x in range(N):
            r, g, b, a = p[x, y]
            if a == 0:
                continue
            lum = (r + g + b) / 3 / 255.0
            f = 0.45 + 0.75 * lum
            if y < cut:
                p[x, y] = (max(0, min(255, int(tr * f))),
                           max(0, min(255, int(tg * f))),
                           max(0, min(255, int(tb * f))), a)
            else:
                # 茎叶压成深灰绿
                p[x, y] = (max(0, min(255, int(52 * f))),
                           max(0, min(255, int(62 * f))),
                           max(0, min(255, int(48 * f))), a)
    return out


def dye_dark(img, split=0.42, target=(48, 42, 54)):
    """虞美人 -> 凋灵玫瑰：花头区域染成暗紫黑。"""
    out = img.copy(); p = out.load()
    tr, tg, tb = target; cut = int(N * split)
    for y in range(N):
        for x in range(N):
            r, g, b, a = p[x, y]
            if a == 0 or y >= cut:
                continue
            lum = (r + g + b) / 3 / 255.0
            f = 0.45 + 0.75 * lum
            p[x, y] = (max(0, min(255, int(tr * f))),
                       max(0, min(255, int(tg * f))),
                       max(0, min(255, int(tb * f))), a)
    return out


def preview(imgs):
    items = list(imgs.items())
    cols = 4; cw = 170; ch = 188
    rows = (len(items) + cols - 1) // cols
    prev = Image.new("RGB", (cols * (cw + 8) + 8, rows * (ch + 8) + 8), (244, 244, 246))
    d = ImageDraw.Draw(prev)
    for i, (name, img) in enumerate(items):
        r, c = divmod(i, cols); x = 8 + c * (cw + 8); y = 8 + r * (ch + 8)
        checker = Image.new("RGB", (cw, cw - 18), (255, 255, 255)); dc = ImageDraw.Draw(checker)
        for yy in range(0, cw - 18, 12):
            for xx in range(0, cw, 12):
                if (xx // 12 + yy // 12) % 2:
                    dc.rectangle([xx, yy, xx + 11, yy + 11], fill=(228, 228, 232))
        t = img.resize((cw - 18, cw - 18), Image.LANCZOS)
        checker.paste(t, (0, 0), t)
        prev.paste(checker, (x, y)); d.text((x, y + cw - 16), name, fill=(30, 30, 30))
    prev.save(os.path.join(OUT, "_fixed_preview.png"))


if __name__ == "__main__":
    imgs = {}
    for name, fn in SRC_FILES.items():
        im = Image.open(os.path.join(SRC, fn)).convert("RGB")
        if name == "blue_orchid":
            base = to_rgba(crop_nomark(im), lo=10, hi=34)
        else:
            base = to_rgba(crop_nomark(im))
        if name == "cornflower":
            base = fix_cornflower_center(base)
        p = os.path.join(OUT, f"{name}.png"); base.save(p)
        imgs[name] = base
        a = base.split()[3]; px = list(a.getdata())
        print("%-20s 不透明 %2.0f%%" % (name, 100 * sum(1 for v in px if v > 128) / len(px)))
    # 凋灵玫瑰：用新虞美人底图重染
    poppy = imgs["poppy"]
    wr = dye_dark_stem(poppy)
    wr.save(os.path.join(OUT, "wither_rose.png"))
    imgs["wither_rose"] = wr
    print("wither_rose 已用新虞美人底图重染")
    preview(imgs)
    print("preview saved")
