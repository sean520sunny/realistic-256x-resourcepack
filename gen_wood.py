# -*- coding: utf-8 -*-
"""
程序化生成写实木头/木板/菌核贴图（纯 Pillow，无 numpy）。
思路：可缩放的多层值噪声(fBm) + 纵向/横向拉伸 -> 木纹/树皮；
年轮用径向距离 + 噪声扰动；再做颜色映射与特征色。
"""
import os, math, random, sys
from PIL import Image, ImageDraw

BASE = r"D:\WorkSpace(WB)\2026-11-17-20-32-26"
OUT = os.path.join(BASE, "_wood_out")
SAMPLE_DIR = os.path.join(BASE, "_tex_source", "wood_samples")
os.makedirs(OUT, exist_ok=True)
os.makedirs(SAMPLE_DIR, exist_ok=True)
N = 256


def clamp(v):
    return 0 if v < 0 else (255 if v > 255 else int(v))


def noise_field(cx, cy, seed):
    """低分辨率随机格点 -> 双三次放大，得到平滑噪声场(L)。"""
    r = random.Random(seed)
    small = Image.new("L", (cx, cy))
    small.putdata([r.randint(0, 255) for _ in range(cx * cy)])
    return small.resize((N, N), Image.BICUBIC)


def fbm(cx, cy, seed):
    """三层噪声混合，模拟自然纹理的多尺度细节。"""
    a = noise_field(cx, cy, seed)
    b = noise_field(cx * 3, cy * 3, seed + 101)
    c = noise_field(cx * 7, cy * 7, seed + 202)
    n = Image.blend(a, b, 0.32)
    n = Image.blend(n, c, 0.16)
    return n


def noise_field_periodic(cx, cy, seed):
    """
    周期化噪声场：随机格点 + 环绕插值，x/y 方向都以 N 为周期。
    用于需要无缝平铺的原木侧面——普通 noise_field 的双三次放大在边界
    不接，接缝色差能到 150，事后任何缝合都会留痕。
    """
    r = random.Random(seed)
    grid = [[r.randint(0, 255) for _ in range(cx)] for _ in range(cy)]
    out = Image.new("L", (N, N))
    px = out.load()
    for y in range(N):
        fy = y * cy / N
        y0 = int(fy)
        ty = fy - y0
        y1 = (y0 + 1) % cy
        ty = ty * ty * (3 - 2 * ty)
        gy0, gy1 = grid[y0 % cy], grid[y1]
        for x in range(N):
            fx = x * cx / N
            x0 = int(fx)
            tx = fx - x0
            x1 = (x0 + 1) % cx
            tx = tx * tx * (3 - 2 * tx)
            top = gy0[x0 % cx] * (1 - tx) + gy0[x1] * tx
            bot = gy1[x0 % cx] * (1 - tx) + gy1[x1] * tx
            px[x, y] = int(top * (1 - ty) + bot * ty)
    return out


def fbm_periodic(cx, cy, seed):
    """周期版 fbm，三层环绕噪声混合。"""
    a = noise_field_periodic(cx, cy, seed)
    b = noise_field_periodic(cx * 2, cy * 2, seed + 101)
    c = noise_field_periodic(cx * 4, cy * 4, seed + 202)
    n = Image.blend(a, b, 0.30)
    n = Image.blend(n, c, 0.14)
    return n


def colorize(base, gray, contrast=0.40, lift=0.0):
    """把灰度纹理映射成以 base 为基调的彩色，带明暗起伏。"""
    gp = gray.load()
    out = Image.new("RGB", (N, N))
    op = out.load()
    r0, g0, b0 = base
    for y in range(N):
        for x in range(N):
            t = gp[x, y] / 255.0
            f = 1.0 - contrast + 2 * contrast * t + lift
            op[x, y] = (clamp(r0 * f), clamp(g0 * f), clamp(b0 * f))
    return out


def add_grain_lines(img, seed, axis="x", count=26, dark=0.30, length=0.7):
    """
    叠加细长的深浅木纹线。axis=x 表示线沿水平方向延伸。

    修复记录：横向木纹线原本是"两点一直线"，最长能横跨 217px，
    在浅色木板（尤其白桦）上就像用尺子划出的横疤。
    现在改成多段轻微起伏的曲线 + 更短 + 更淡 + 颜色更暖，
    让它融进 fbm 木纹本身，而不是浮在表面的一道墨线。
    原木侧面(axis=y)保留直裂纹——树皮纤维本来就是竖向直的，不改。
    """
    r = random.Random(seed)
    dr = ImageDraw.Draw(img, "RGBA")
    col = (46, 30, 18)  # 从近黑 (20,12,8) 调暖调淡，避免白木板上像墨线
    for _ in range(count):
        if axis == "x":
            y0 = r.randint(0, N - 1)
            x0 = r.randint(0, int(N * (1 - length)))
            x1 = x0 + int(N * length * r.uniform(0.5, 1.0))
            pts = []
            x = x0
            while x < x1:
                pts.append((x, y0 + r.randint(-2, 2)))
                x += r.randint(12, 26)   # 每小段换一个高度，形成自然起伏
            pts.append((x1, y0 + r.randint(-2, 2)))
            dr.line(pts, fill=(col[0], col[1], col[2], int(255 * dark)),
                    width=r.choice([1, 1, 2]))
        else:
            x0 = r.randint(0, N - 1)
            y0 = r.randint(0, int(N * (1 - length)))
            y1 = y0 + int(N * length * r.uniform(0.5, 1.0))
            wob = r.randint(-3, 3)
            dr.line([(x0, y0), (x0 + wob, y1)],
                    fill=(20, 12, 8, int(255 * dark)), width=r.choice([1, 1, 2]))
    return img


def make_planks(base, seed, kind="normal"):
    """横向木板：沿水平的木纹 + 板缝 + 每板色差 + 结疤。"""
    g = fbm(4, 46, seed)          # x 低频、y 高频 -> 水平木纹
    img = colorize(base, g, 0.34)
    # 板缝：4 块板，每块 64px
    p = img.load()
    for y in range(N):
        board = y // 64
        shift = (-6, 4, -2, 6)[board]
        for x in range(N):
            if y % 64 < 2:  # 缝隙
                p[x, y] = (clamp(p[x, y][0] * 0.62), clamp(p[x, y][1] * 0.62), clamp(p[x, y][2] * 0.62))
            else:
                p[x, y] = (clamp(p[x, y][0] + shift), clamp(p[x, y][1] + shift), clamp(p[x, y][2] + shift))
    # 木纹线：短、淡、弯曲。白桦原版就是干净的浅色木纹，进一步压低
    if kind == "birch":
        add_grain_lines(img, seed + 7, "x", count=16, dark=0.09, length=0.42)
    else:
        add_grain_lines(img, seed + 7, "x", count=28, dark=0.15, length=0.56)

    # 木节：带缺口的不规则弧，不再是规整同心扁椭圆（三圈叠起来像几道横线）
    # 白桦木板保持干净，不加木节；黑斑只属于白桦原木树皮
    if kind != "birch":
        r = random.Random(seed + 55)
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(2):
            kx, ky = r.randint(38, N - 38), r.randint(30, N - 30)
            rx = r.randint(9, 15)
            ry = int(rx * r.uniform(0.62, 0.88))   # 不再压成 2:1 的扁椭圆
            tilt = r.uniform(-0.28, 0.28)
            ct, st = math.cos(tilt), math.sin(tilt)
            for ring in range(2):
                rr = 1.0 + ring * 0.58
                start = r.uniform(0, 2 * math.pi)
                span = r.uniform(3.6, 5.2)          # 留缺口，弧不闭合
                pts = []
                for k in range(30):
                    a = start + span * k / 29
                    wob = 1.0 + 0.13 * math.sin(a * 4 + ring * 2)
                    ex = rx * rr * wob * math.cos(a)
                    ey = ry * rr * wob * math.sin(a)
                    pts.append((kx + ex * ct - ey * st, ky + ex * st + ey * ct))
                d.line(pts, fill=(66, 42, 22, 72), width=1)
            d.ellipse([kx - 2, ky - 2, kx + 2, ky + 2], fill=(66, 42, 22, 88))
    return img


def crack_field(seed, cx=24, cy=3, floor=0.18, width=0.10, depth=0.65):
    """
    周期噪声取谷底得到尖锐暗裂纹场（灰度 L：255=无裂纹，低值=裂纹）。
    所有裂缝都从周期噪声派生 -> 天生无缝，不存在手绘跨边界断线问题。
    """
    np = noise_field_periodic(cx, cy, seed).load()
    out = Image.new("L", (N, N))
    op = out.load()
    for y in range(N):
        for x in range(N):
            v = np[x, y] / 255.0
            crack = max(0.0, 1.0 - abs(v - floor) / width)
            op[x, y] = int(255 * (1 - crack * depth))
    return out


def draw_lenticels(img, seed, margin=34):
    """
    白桦皮孔：手绘横向短划线，但严格限制在内部安全区（留 margin 边距）。
    皮孔不碰边界 -> 底噪在边界处纯净连续，接缝不受影响。
    试过用周期噪声取窄带生成皮孔，结果变成满屏"小蝌蚪"闭合轮廓，
    完全不是白桦那种细横疤，观感倒退，故回到手绘 + 边距约束。
    """
    r = random.Random(seed)
    d = ImageDraw.Draw(img, "RGBA")
    for _ in range(34):
        by = r.randint(margin, N - 1 - margin)
        x0 = r.randint(margin, N - margin - 30)
        w = r.randint(6, 28)
        pts = [(x0, by + r.randint(-1, 1)),
               (x0 + w // 2, by + r.randint(-2, 2)),
               (x0 + w, by + r.randint(-1, 1))]
        d.line(pts, fill=(42, 40, 36, 165), width=r.choice([1, 1, 2]))
        if r.random() < 0.30:
            d.line([(x0 + w // 4, by - 1), (x0 + 3 * w // 4, by + 1)],
                   fill=(38, 36, 32, 130), width=2)
    return img


def make_log_side(base, seed, kind="normal"):
    """
    原木侧面：垂直树皮纹理 + 纵向裂纹（全周期噪声版，真正无缝）。

    改造记录：旧版用普通 fbm + 随机手绘裂纹/皮孔，接缝色差高达 112~150，
    事后缝合要么留暗带、要么留明暗条带、要么出对称纹，全部失败。
    现在底噪、裂纹、皮孔三层全部从周期噪声派生：
      - fbm_periodic 底噪（x/y 双向环绕）
      - crack_field 谷底裂纹（周期）
      - lenticel_field 白桦皮孔（周期）
    三层叠加天生无缝，且边缘受光用 deframe_log（中位数版）压平。
    """
    g = fbm_periodic(46, 5, seed)          # 垂直树皮底噪，高频竖纹（cx 低会出大斑）
    img = colorize(base, g, 0.42)

    # 细裂纹（浅）与大裂纹（深）两层
    # width 要窄：太宽会把噪声低值区整片压暗成"豹纹大斑"，不是树皮细纹
    crack1 = crack_field(seed + 33, 40, 5, floor=0.16, width=0.035, depth=0.16)
    crack2 = crack_field(seed + 91, 22, 4, floor=0.12, width=0.028, depth=0.30)
    cp = img.load()
    c1, c2 = crack1.load(), crack2.load()
    for y in range(N):
        for x in range(N):
            q = cp[x, y]
            k1 = c1[x, y] / 255.0
            k2 = c2[x, y] / 255.0
            f = k1 * k2
            cp[x, y] = (clamp(q[0] * f), clamp(q[1] * f), clamp(q[2] * f))

    # 白桦皮孔：手绘细横疤，限制在内部安全区（不碰边界，保住无缝）
    if kind == "birch":
        img = draw_lenticels(img, seed + 77)

    return deframe_log(img)


def deframe_log(im, strength=0.9, band=30):
    """
    原木侧面专用去框：按到最近边距离分层，用逐圈中位数估偏差
    （白桦皮孔短线集中在边缘，均值会被带歪），smoothstep 权重向内衰减。
    """
    import statistics
    px = im.load()
    s = [0, 0, 0]
    c = 0
    for y in range(36, N - 36):
        for x in range(36, N - 36):
            q = px[x, y]
            for i in range(3):
                s[i] += q[i]
            c += 1
    ref = [v / c for v in s]
    dev = {}
    for d in range(band):
        cols = [[], [], []]
        for k in range(d, N - d):
            for (x, y) in [(k, d), (k, N - 1 - d), (d, k), (N - 1 - d, k)]:
                q = px[x, y]
                for i in range(3):
                    cols[i].append(q[i])
        dev[d] = [statistics.median(cols[i]) - ref[i] for i in range(3)]
    out = im.copy()
    op = out.load()
    for y in range(N):
        for x in range(N):
            d = min(x, y, N - 1 - x, N - 1 - y)
            if d < band:
                t = 1.0 - d / band
                w = t * t * (3 - 2 * t)
                q = px[x, y]
                op[x, y] = tuple(
                    clamp(q[i] - dev[d][i] * w * strength) for i in range(3))
    return out


def make_log_top(side_base, top_base, seed, kind="normal"):
    """原木顶面：同心年轮 + 外圈树皮。"""
    ng = fbm(9, 9, seed + 5)
    np = ng.load()
    g = Image.new("L", (N, N))
    gp = g.load()
    cx = cy = N / 2 - 0.5
    rings = 15 if kind != "pale" else 11
    for y in range(N):
        for x in range(N):
            dx = (x - cx) / (N / 2)
            dy = (y - cy) / (N / 2)
            rad = math.sqrt(dx * dx + dy * dy)
            wob = (np[x, y] / 255.0 - 0.5) * 0.10
            rr = rad + wob
            ring = 0.5 + 0.5 * math.sin(rr * rings * math.pi * 2)
            if rad > 0.86:  # 树皮外圈
                v = 0.30 + 0.20 * (np[x, y] / 255.0) + 0.10 * ring
            else:
                v = 0.42 + 0.34 * ring + 0.16 * (np[x, y] / 255.0)
                v *= (1.0 - 0.18 * rad)
            gp[x, y] = clamp(v * 255)
    return colorize(top_base, g, 0.36)


def make_stem_side(base, seed, kind):
    """菌核侧面：绯红/诡异的独特纹理。"""
    g = fbm(12, 30, seed)
    img = colorize(base, g, 0.45)
    p = img.load()
    if kind == "crimson":
        r = random.Random(seed + 3)
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(26):
            x, y = r.randint(0, N), r.randint(0, N)
            rad = r.randint(2, 6)
            d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(214, 92, 120, 120))
    else:  # warped
        r = random.Random(seed + 3)
        d = ImageDraw.Draw(img, "RGBA")
        for _ in range(22):
            x, y = r.randint(0, N), r.randint(0, N)
            rad = r.randint(2, 5)
            d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=(120, 230, 214, 110))
    return img


def make_stem_top(base, seed, kind):
    """菌核顶面：漩涡纹。"""
    ng = fbm(10, 10, seed + 5)
    np = ng.load()
    g = Image.new("L", (N, N))
    gp = g.load()
    cx = cy = N / 2 - 0.5
    for y in range(N):
        for x in range(N):
            dx = (x - cx) / (N / 2)
            dy = (y - cy) / (N / 2)
            rad = math.sqrt(dx * dx + dy * dy)
            ang = math.atan2(dy, dx)
            swirl = math.sin(rad * 18 + ang * 3 + (np[x, y] / 255.0 - 0.5) * 3)
            v = 0.45 + 0.30 * swirl + 0.15 * (np[x, y] / 255.0)
            if rad > 0.86:
                v *= 0.72
            gp[x, y] = clamp(v * 255)
    return colorize(base, g, 0.40)


# ---- 颜色表（写实调色，略偏亮以匹配现有包）----
LOGS = {
    "oak":        ((120, 98, 64),  (168, 138, 84), "normal"),
    "spruce":     ((86, 67, 44),   (120, 94, 58),  "normal"),
    "birch":      ((198, 182, 150),(210, 194, 156),"birch"),
    "jungle":     ((104, 78, 47),  (142, 106, 62), "normal"),
    "acacia":     ((132, 80, 48),  (168, 106, 62), "normal"),
    "dark_oak":   ((60, 46, 31),   (86, 66, 42),   "normal"),
    "mangrove":   ((112, 68, 47),  (144, 92, 60),  "normal"),
    "cherry":     ((126, 86, 92),  (166, 116, 122),"normal"),
    "pale_oak":   ((196, 186, 164),(214, 204, 182),"pale"),
    "crimson":    ((92, 44, 56),   (112, 56, 70),  "crimson"),
    "warped":     ((52, 106, 106), (68, 126, 122), "warped"),
}
PLANKS = {
    "oak":        (166, 132, 82),
    "spruce":     (122, 94, 60),
    "birch":      (208, 192, 154),
    "jungle":     (146, 108, 66),
    "acacia":     (170, 108, 64),
    "dark_oak":   (88, 68, 43),
    "mangrove":   (144, 94, 62),
    "cherry":     (172, 122, 126),
    "pale_oak":   (214, 204, 182),
    "bamboo":     (192, 170, 92),
    "crimson":    (124, 64, 76),
    "warped":     (74, 134, 130),
}


def generate(only_sample=False):
    made = []
    # 木板
    for i, (name, color) in enumerate(PLANKS.items()):
        kind = "birch" if name == "birch" else "normal"
        img = make_planks(color, 1000 + i * 13, kind)
        made.append((f"{name}_planks.png", img))
    # 原木
    for i, (name, (side, top, kind)) in enumerate(LOGS.items()):
        if kind in ("crimson", "warped"):
            made.append((f"{name}_stem.png", make_stem_side(side, 3000 + i * 17, kind)))
            made.append((f"{name}_stem_top.png", make_stem_top(top, 3000 + i * 17, kind)))
        else:
            made.append((f"{name}_log.png", make_log_side(side, 2000 + i * 19, kind)))
            made.append((f"{name}_log_top.png", make_log_top(side, top, 2000 + i * 19, kind)))
    # 输出
    target = SAMPLE_DIR if only_sample else OUT
    for fn, img in made:
        img.save(os.path.join(target, fn))
    if only_sample:
        picks = ["oak_planks.png", "birch_planks.png", "cherry_planks.png",
                 "oak_log.png", "oak_log_top.png", "birch_log.png",
                 "crimson_stem.png", "warped_stem.png", "acacia_log_top.png"]
        chosen = [p for f, p in made if f in picks]
        c = Image.new("RGB", (N * 3, N * 3), (35, 35, 35))
        for i, img in enumerate(chosen):
            c.paste(img, ((i % 3) * N, (i // 3) * N))
        c.save(os.path.join(BASE, "_tex_source", "wood_sample_preview.png"))
    print("generated", len(made), "textures ->", target)


if __name__ == "__main__":
    generate(only_sample=("--sample" in sys.argv))
