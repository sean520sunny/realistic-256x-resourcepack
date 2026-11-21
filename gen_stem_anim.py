# -*- coding: utf-8 -*-
"""
绯红菌核 / 诡异菌核 侧面 -> 流动动画

格式要点：
  1. 动画贴图是"纵向堆叠的 sprite sheet"，每帧高 = 宽，游戏按宽度推断帧高；
     元数据文件名 = 完整贴图名 + ".mcmeta"，即 crimson_stem.png.mcmeta。
  2. .mcmeta 的 frametime 以 tick 计（20 tick = 1 秒），interpolate 让帧间交叉淡化。

实现路线（三个坑都踩过，记在这里）：
  A. 最初想"整张纵向滚动"，但静态源图上下边界不匹配 -> 接缝线被滚过整个方块表面。
     所以先用 gradient_compensation 做周期化：把边界色差线性摊到全图，
     纹理结构不动、不产生模糊带，两端差值归零。
  B. 接着用"按行偏移"制造流动，结果把横向瘤状条纹扭成规则锯齿竖条，很假。
     改用双周期正弦涡旋，又出现规则 W 波纹。
  C. 最终方案 = 无缝源图 + 整张滚动（有明确流向）+ 双周期噪声形变（打散机械感）。
     噪声场在 x/y 上周期为 W/H，滚动量为 H 的整数倍 -> 全程无缝且完美循环。
"""
import os, math, json, random
from PIL import Image, ImageEnhance

BASE = r"D:\WorkSpace(WB)\2026-11-17-20-32-26"
BLK = os.path.join(BASE, "realistic-256x-pack", "assets", "minecraft", "textures", "block")
STATIC = os.path.join(BASE, "_stem_static")

W = H = 256

ANIM = {
    # 绯红：血肉组织，幅度大一点，向上"涌"
    "crimson_stem.png": dict(frames=8, frametime=4, amp_x=7.0, amp_y=8.0, seed=11),
    # 诡异：黏液菌丝，形变更碎、更快
    "warped_stem.png":  dict(frames=8, frametime=3, amp_x=6.0, amp_y=9.0, seed=47),
}


# ---------- 周期噪声 ----------
def periodic_noise(freq, seed):
    """生成 x/y 双向周期的值噪声，返回 list[y][x] 归一化到 -1..1。"""
    rnd = random.Random(seed)
    g = [[rnd.uniform(-1.0, 1.0) for _ in range(freq)] for _ in range(freq)]
    out = [[0.0] * W for _ in range(H)]
    for y in range(H):
        fy = y * freq / H
        y0 = int(fy) % freq
        ty = fy - int(fy)
        ty = ty * ty * (3 - 2 * ty)          # smoothstep，避免线性插值的棱角
        y1 = (y0 + 1) % freq
        g0, g1 = g[y0], g[y1]
        row = out[y]
        for x in range(W):
            fx = x * freq / W
            x0 = int(fx) % freq
            tx = fx - int(fx)
            tx = tx * tx * (3 - 2 * tx)
            x1 = (x0 + 1) % freq
            top = g0[x0] * (1 - tx) + g0[x1] * tx
            bot = g1[x0] * (1 - tx) + g1[x1] * tx
            row[x] = top * (1 - ty) + bot * ty
    return out


def combined_noise(seed):
    """
    只用低频涡：位移场频率过高会在噪声格点处形成固定的错位线，
    看起来像竖格砖墙（freq=13 时尤其明显）。低频 + 小幅细层最自然。
    """
    acc = [[0.0] * W for _ in range(H)]
    for i, (fq, wt) in enumerate(((2, 1.0), (5, 0.32))):
        n = periodic_noise(fq, seed + i * 131)
        for y in range(H):
            r, nr = acc[y], n[y]
            for x in range(W):
                r[x] += nr[x] * wt
    peak = max(max(abs(v) for v in row) for row in acc) or 1.0
    k = 1.0 / peak
    for y in range(H):
        row = acc[y]
        for x in range(W):
            row[x] *= k
    return acc


_NCACHE = {}


def noises(seed):
    if seed not in _NCACHE:
        # 4 张互不相关的噪声：dx 用前两张、dy 用后两张，避免整体同向平移
        _NCACHE[seed] = tuple(combined_noise(seed + i * 977) for i in range(4))
    return _NCACHE[seed]


# ---------- 周期化 ----------
def smooth_series(seq, win=11):
    """对补偿量做循环移动平均。不平滑的话，逐列/逐行不同的补偿量会变成细竖条纹。"""
    n = len(seq)
    half = win // 2
    ch = len(seq[0])
    out = []
    for i in range(n):
        s = [0.0] * ch
        for k in range(-half, half + 1):
            v = seq[(i + k) % n]
            for c in range(ch):
                s[c] += v[c]
        out.append(tuple(x / win for x in s))
    return out


def gradient_compensation(im, iters=2):
    """
    把边界色差（top vs bottom、left vs right）线性摊到整张贴图。
    只给每个像素加一个平滑常数场，纹理结构不变、不糊，但两端被拉平。

    关键：补偿量必须先做循环平滑。直接逐列用原始差值，
    会在图上留下等间距的细竖条纹（原图是噪声，逐列差值也是噪声）。
    """
    px = im.load()
    ch = len(px[0, 0])
    for _ in range(iters):
        # 纵向：每列的 bottom-top 差值，平滑后沿 y 摊掉
        dlist = [[px[x, H - 1][i] - px[x, 0][i] for i in range(ch)] for x in range(W)]
        dlist = smooth_series([tuple(d) for d in dlist])
        for x in range(W):
            d = dlist[x]
            if max(abs(v) for v in d) < 0.5:
                continue
            for y in range(H):
                t = y / (H - 1) - 0.5
                c = px[x, y]
                px[x, y] = tuple(
                    max(0, min(255, int(round(c[i] - d[i] * t)))) for i in range(ch))
        # 横向：每行的 right-left 差值
        dlist = [[px[W - 1, y][i] - px[0, y][i] for i in range(ch)] for y in range(H)]
        dlist = smooth_series([tuple(d) for d in dlist])
        for y in range(H):
            d = dlist[y]
            if max(abs(v) for v in d) < 0.5:
                continue
            for x in range(W):
                t = x / (W - 1) - 0.5
                c = px[x, y]
                px[x, y] = tuple(
                    max(0, min(255, int(round(c[i] - d[i] * t)))) for i in range(ch))
    return im


# ---------- 采样 ----------
def bilinear(px, x, y):
    """双线性采样，坐标按贴图尺寸循环包裹；位移为 0 时精确还原原像素。"""
    x0 = int(math.floor(x))
    y0 = int(math.floor(y))
    fx = x - x0
    fy = y - y0
    x0 %= W
    y0 %= H
    x1 = (x0 + 1) % W
    y1 = (y0 + 1) % H
    a, b = px[x0, y0], px[x1, y0]
    c, d = px[x0, y1], px[x1, y1]
    w00 = (1.0 - fx) * (1.0 - fy)
    w10 = fx * (1.0 - fy)
    w01 = (1.0 - fx) * fy
    w11 = fx * fy
    return (
        int(a[0] * w00 + b[0] * w10 + c[0] * w01 + d[0] * w11),
        int(a[1] * w00 + b[1] * w10 + c[1] * w01 + d[1] * w11),
        int(a[2] * w00 + b[2] * w10 + c[2] * w01 + d[2] * w11),
    )


def warp_frame(src, f, frames, amp_x, amp_y, seed):
    """
    采样点 = (x + 噪声dx, y + 滚动 + 噪声dy)
      - 滚动量 = H*f/frames，滚满整张 -> f=frames 时精确回到 f=0
      - 噪声用 cos/sin 相位混合两张独立噪声场 -> 形变随时间平滑演化且循环闭合
    """
    px = src.load()
    out = Image.new("RGB", (W, H))
    opx = out.load()
    ph = 2.0 * math.pi * f / frames
    c, s = math.cos(ph), math.sin(ph)
    roll = H * f / frames          # 内容向上流动
    n1, n2, n3, n4 = noises(seed)

    for y in range(H):
        r1, r2, r3, r4 = n1[y], n2[y], n3[y], n4[y]
        sy0 = y + roll
        for x in range(W):
            dx = amp_x * (r1[x] * c + r2[x] * s)
            dy = amp_y * (-r3[x] * s + r4[x] * c)
            opx[x, y] = bilinear(px, x + dx, sy0 + dy)

    # 极轻的明暗呼吸，周期与循环一致，强化"活体"感
    return ImageEnhance.Brightness(out).enhance(1.0 + 0.02 * math.sin(ph))


def build(name):
    cfg = ANIM[name]
    raw = Image.open(os.path.join(STATIC, name)).convert("RGB")
    if raw.size != (W, H):
        raw = raw.resize((W, H), Image.LANCZOS)

    src = gradient_compensation(raw.copy())
    src.save(os.path.join(STATIC, name.replace(".png", "_seamless.png")))

    frames = cfg["frames"]
    sheet = Image.new("RGB", (W, H * frames))
    fcs = []
    for f in range(frames):
        fr = warp_frame(src, f, frames, cfg["amp_x"], cfg["amp_y"], cfg["seed"])
        sheet.paste(fr, (0, f * H))
        fcs.append(fr)

    dst = os.path.join(BLK, name)
    sheet.save(dst)
    with open(dst + ".mcmeta", "w", encoding="utf-8") as fh:
        json.dump({"animation": {"frametime": cfg["frametime"], "interpolate": True}},
                  fh, ensure_ascii=False, indent=2)

    # 循环闭合：f=frames 的相位等于 f=0，应与首帧逐像素一致
    loop = warp_frame(src, frames, frames, cfg["amp_x"], cfg["amp_y"], cfg["seed"])
    d = max(abs(a - b) for a, b in zip(
        [c for p in loop.getdata() for c in p],
        [c for p in fcs[0].getdata() for c in p]))

    # 接缝验证：接缝相邻像素差 vs 图内部相邻像素差（比值 <=1 即无可见接缝）
    def rowdiff(im, y1, y2):
        p = im.load()
        return sum(sum(abs(a - b) for a, b in zip(p[x, y1], p[x, y2])) for x in range(W)) / W

    def coldiff(im, x1, x2):
        p = im.load()
        return sum(sum(abs(a - b) for a, b in zip(p[x1, y], p[x2, y])) for y in range(H)) / H

    ratios = []
    for fr in fcs:
        iy = sum(rowdiff(fr, y, y + 1) for y in range(40, 216, 16)) / 11.0
        ix = sum(coldiff(fr, x, x + 1) for x in range(40, 216, 16)) / 11.0
        ratios.append((rowdiff(fr, 0, H - 1) / max(iy, 0.01),
                       coldiff(fr, 0, W - 1) / max(ix, 0.01)))
    wy = max(r[0] for r in ratios)
    wx = max(r[1] for r in ratios)

    print(f"{name}: {W}x{H * frames} | frames={frames} frametime={cfg['frametime']} "
          f"| 循环闭合误差={d} | 接缝/内部差异比 上下={wy:.2f} 左右={wx:.2f}")
    return fcs


if __name__ == "__main__":
    made = {n: build(n) for n in ANIM}
    cell = 96
    canvas = Image.new("RGB", (4 * cell, 4 * cell), (26, 26, 26))
    for i, fr in enumerate(made["crimson_stem.png"]):
        canvas.paste(fr.resize((cell, cell), Image.LANCZOS), ((i % 4) * cell, (i // 4) * cell))
    for i, fr in enumerate(made["warped_stem.png"]):
        canvas.paste(fr.resize((cell, cell), Image.LANCZOS), ((i % 4) * cell, ((i // 4) + 2) * cell))
    canvas.save(os.path.join(BASE, "_tex_source", "stem_anim_preview.png"))
    print("DONE -> _tex_source/stem_anim_preview.png")
