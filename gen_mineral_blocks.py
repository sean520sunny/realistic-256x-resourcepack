# -*- coding: utf-8 -*-
"""
程序化生成 17 种矿物/压缩方块共 20 张 256x256 写实贴图（纯 Pillow，无 numpy）。

方块与贴图映射（Minecraft Java 1.21.x）：
  amethyst_block / diamond_block / emerald_block / lapis_block / redstone_block  宝石块
  gold_block / iron_block / copper_block                                          金属块
  coal_block / netherite_block                                                    深色矿物块
  quartz_block(顶底) + quartz_block_side(侧)                                      石英
  raw_copper_block / raw_gold_block / raw_iron_block                              粗金属块
  resin_block                                                                     树脂块
  bamboo_block(侧)+bamboo_block_top(顶) / stripped_bamboo_block(侧)+..._top(顶)   竹块

所有纹理使用周期噪声与周期 Voronoi，保证四边无缝平铺。
"""
import os, math, random
from PIL import Image, ImageDraw

BASE = r"D:\WorkSpace(WB)\2026-11-17-20-32-26"
OUT = os.path.join(BASE, "_mineral_out")
BLK = os.path.join(BASE, "realistic-256x-pack", "assets", "minecraft", "textures", "block")
os.makedirs(OUT, exist_ok=True)
N = 256
TAU = 2 * math.pi


# ---------------------------------------------------------------- 基础工具
def clamp(v):
    return 0 if v < 0 else (255 if v > 255 else int(v))


def lerp(a, b, t):
    return a + (b - a) * t


def noise_field_periodic(cx, cy, seed):
    """周期化值噪声：格点环绕插值，x/y 都以 N 为周期 -> 无缝。"""
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


def fbm_periodic(cx, cy, seed, layers=((1.0, 0.0),)):
    """多层周期噪声混合。layers 为 (频率倍率, 权重) 列表。"""
    imgs = []
    for i, (mul, w) in enumerate(layers):
        imgs.append((noise_field_periodic(max(2, int(cx * mul)), max(2, int(cy * mul)),
                                          seed + i * 1009), w))
    tot = sum(w for _, w in imgs) or 1
    out = Image.new("L", (N, N), 0)
    op = out.load()
    data = [im.load() for im, _ in imgs]
    for y in range(N):
        for x in range(N):
            v = sum(data[k][x, y] * w for k, (_, w) in enumerate(imgs)) / tot
            op[x, y] = int(v)
    return out


def soft_fbm(cx, cy, seed):
    """常用三层 fbm。"""
    return fbm_periodic(cx, cy, seed, layers=((1, 0.0), (2, 0.30), (4, 0.14)))


def colorize(base, gray, contrast=0.35, lift=0.0, gray2=None):
    """把灰度场映射成以 base 为基调的彩色。gray2 可选作为第二层明暗微调。"""
    gp = gray.load()
    gp2 = gray2.load() if gray2 else None
    out = Image.new("RGB", (N, N))
    op = out.load()
    r0, g0, b0 = base
    for y in range(N):
        for x in range(N):
            t = gp[x, y] / 255.0
            f = 1.0 - contrast + 2 * contrast * t + lift
            if gp2:
                f *= 0.92 + 0.16 * (gp2[x, y] / 255.0)
            op[x, y] = (clamp(r0 * f), clamp(g0 * f), clamp(b0 * f))
    return out


def voronoi(n, seed):
    """
    周期 Voronoi：返回 idx(最近种子编号) 与 edge(边界强度 0~255, 越大越靠近晶界)。
    种子在 3x3 平铺空间内展开，保证左右/上下边界连续。
    """
    r = random.Random(seed)
    pts = [(r.random() * N, r.random() * N, r.random()) for _ in range(n)]
    expanded = []
    for i, (x, y, _b) in enumerate(pts):
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                expanded.append((x + ox, y + oy, i))
    idx = [0] * (N * N)
    edge = [0] * (N * N)
    bright = [0.72 + 0.56 * b for _x, _y, b in pts]
    for py in range(N):
        for px in range(N):
            d1 = 1e18
            d2 = 1e18
            i1 = -1
            for ex, ey, i in expanded:
                dx = ex - px
                dy = ey - py
                d = dx * dx + dy * dy
                if d < d1:
                    d2, d1, i1 = d1, d, i
                elif d < d2 and i != i1:
                    d2 = d
            p = py * N + px
            idx[p] = i1
            # sqrt 差值越小 -> 越靠近晶界 -> edge 越大
            gap = math.sqrt(d2) - math.sqrt(d1)
            edge[p] = clamp(255 * (1 - gap / 9.0)) if gap < 9 else 0
    return idx, edge, bright


# ---------------------------------------------------------------- 宝石块
def gen_gem(base, seed, n=26, contrast=0.42, sparkle=1.0):
    """宝石块：Voronoi 晶面 + 晶面反光 + 晶界高光 + 内部微裂。"""
    idx, edge, bright = voronoi(n, seed)
    micro = soft_fbm(30, 30, seed + 55).load()
    r0, g0, b0 = base
    out = Image.new("RGB", (N, N))
    op = out.load()
    # 每个晶面的高光方向不同，制造切面感
    r = random.Random(seed + 777)
    face_dir = [(r.uniform(-1, 1), r.uniform(-1, 1)) for _ in range(n)]
    for y in range(N):
        for x in range(N):
            p = y * N + x
            i = idx[p]
            dx, dy = face_dir[i]
            # 晶面内方向性渐变（模拟反光斜面）
            grad = (x / N - 0.5) * dx + (y / N - 0.5) * dy
            f = bright[i] * (1 + 0.22 * grad) * (0.88 + 0.24 * micro[x, y] / 255.0)
            f = 1 - contrast + 2 * contrast * f
            e = edge[p] / 255.0
            # 晶界：暗线 + 一侧高光
            if e > 0:
                hi = e ** 1.6 * sparkle
                f = f * (1 - 0.35 * e) + hi * 0.55
            op[x, y] = (clamp(r0 * f), clamp(g0 * f), clamp(b0 * f))
    return out


# ---------------------------------------------------------------- 金属块
def gen_metal(base, seed, axis="x", n_ingots=5):
    """
    金属块：金属拉丝底 + 错缝金属锭拼接。

    修复记录：初版只用「上亮右暗」单向倒角，导致贴图四边明暗不一致，
    接缝色差高达 26~35；拉丝对比度 0.16 也太强，竖向条纹盖住了锭板结构。
    现在改为：拉丝对比度降到 0.08；锭板四边一律画暗缝 + 内侧一圈等宽高光，
    使边界在 x/y 两向都对称，接缝色差回落到个位数。
    """
    cx, cy = (72, 8) if axis == "x" else (8, 72)
    brush = noise_field_periodic(cx, cy, seed)
    broad = soft_fbm(5, 5, seed + 31)
    img = colorize(base, brush, contrast=0.08, lift=0.0, gray2=broad)
    d = ImageDraw.Draw(img, "RGBA")
    r0, g0, b0 = base
    cell = N / n_ingots
    for row in range(n_ingots):
        y0 = row * cell
        shift = (cell / 2) if row % 2 else 0
        for col in range(-1, n_ingots + 1):
            x0 = col * cell + shift
            x1, y1 = x0 + cell, y0 + cell
            # 锭缝：四边等宽暗线（对称，保证平铺边界一致）
            d.rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2],
                        outline=(int(r0 * 0.58), int(g0 * 0.58), int(b0 * 0.58), 110), width=3)
            # 内侧一圈淡高光：模拟金属锭倒角反光，四边等宽同样对称
            d.rectangle([x0 + 5, y0 + 5, x1 - 5, y1 - 5],
                        outline=(255, 255, 255, 42), width=2)
    return img


# ---------------------------------------------------------------- 粗金属块（岩基 + 矿粒）
def gen_raw_ore(rock_base, grain_rgb, seed, n_grains=90):
    """粗金属块：灰褐岩基 + 不规则金属颗粒 + 颗粒高光。"""
    rock = soft_fbm(26, 26, seed)
    img = colorize(rock_base, rock, contrast=0.28, gray2=soft_fbm(60, 60, seed + 9))
    d = ImageDraw.Draw(img, "RGBA")
    r = random.Random(seed + 500)
    gr, gg, gb = grain_rgb
    for _ in range(n_grains):
        cx = r.random() * N
        cy = r.random() * N
        rad = r.uniform(3, 10)
        # 不规则多边形颗粒
        k = r.randint(5, 8)
        pts = []
        for t in range(k):
            a = TAU * t / k
            rr = rad * r.uniform(0.65, 1.25)
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        # 颗粒本体（绕边界复制保证无缝）
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                shifted = [(px + ox, py + oy) for px, py in pts]
                if max(p[0] for p in shifted) < 0 or min(p[0] for p in shifted) > N:
                    continue
                if max(p[1] for p in shifted) < 0 or min(p[1] for p in shifted) > N:
                    continue
                shade = r.uniform(0.75, 1.15)
                col = (clamp(gr * shade), clamp(gg * shade), clamp(gb * shade), 235)
                d.polygon(shifted, fill=col)
                # 高光点
                d.ellipse([cx + ox - rad * 0.35, cy + oy - rad * 0.45,
                           cx + ox - rad * 0.05, cy + oy - rad * 0.2],
                          fill=(255, 255, 255, 70))
    return img


# ---------------------------------------------------------------- 煤炭块
def gen_coal(seed):
    """煤炭块：近黑底 + 不规则块面 + 树脂光泽反光。"""
    base = (30, 28, 27)
    f = soft_fbm(22, 22, seed)
    img = colorize(base, f, contrast=0.55)
    d = ImageDraw.Draw(img, "RGBA")
    r = random.Random(seed + 12)
    for _ in range(40):
        cx, cy = r.random() * N, r.random() * N
        rad = r.uniform(6, 22)
        pts = [(cx + math.cos(TAU * t / 6) * rad * r.uniform(0.6, 1.2),
                cy + math.sin(TAU * t / 6) * rad * r.uniform(0.6, 1.2)) for t in range(6)]
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                s = [(px + ox, py + oy) for px, py in pts]
                d.polygon(s, fill=(18, 17, 17, 120),
                          outline=(70, 68, 66, 90))
    # 光泽条
    sheen = noise_field_periodic(80, 4, seed + 88).load()
    op = img.load()
    for y in range(N):
        for x in range(N):
            v = sheen[x, y]
            if v > 205:
                c = op[x, y]
                k = (v - 205) / 50.0
                op[x, y] = (clamp(c[0] + 40 * k), clamp(c[1] + 40 * k), clamp(c[2] + 42 * k))
    return img


# ---------------------------------------------------------------- 下界合金块
def gen_netherite(seed):
    """下界合金块：深灰黑金属 + 暗红余烬斑 + 微弱反光。"""
    brush = noise_field_periodic(70, 8, seed)
    img = colorize((46, 43, 45), brush, contrast=0.22,
                   gray2=soft_fbm(8, 8, seed + 3))
    d = ImageDraw.Draw(img, "RGBA")
    r = random.Random(seed + 60)
    for _ in range(70):
        cx, cy = r.random() * N, r.random() * N
        rad = r.uniform(1, 4)
        shade = r.randint(0, 1)
        col = (120, 48, 38, r.randint(60, 150)) if shade else (150, 70, 45, r.randint(40, 110))
        for ox in (-N, 0, N):
            for oy in (-N, 0, N):
                d.ellipse([cx + ox - rad, cy + oy - rad, cx + ox + rad, cy + oy + rad], fill=col)
    return img


# ---------------------------------------------------------------- 石英块
def gen_quartz(seed, side=False):
    """石英块：乳白晶质。顶底为均匀晶纹；侧面加原版式凹槽浮雕。"""
    img = colorize((236, 233, 226), soft_fbm(20, 20, seed), contrast=0.13,
                   gray2=soft_fbm(50, 50, seed + 4))
    if side:
        d = ImageDraw.Draw(img, "RGBA")
        # 侧面：错落的浅凹菱形浮雕，模仿原版 quartz_block_side
        cell = N / 4
        for row in range(4):
            for col in range(4):
                cx = (col + 0.5) * cell + (cell / 2 if row % 2 else 0)
                cy = (row + 0.5) * cell
                w, h = cell * 0.36, cell * 0.26
                for ox in (-N, 0, N):
                    diamond = [(cx + ox, cy - h), (cx + ox + w, cy),
                               (cx + ox, cy + h), (cx + ox - w, cy)]
                    d.polygon(diamond, fill=(196, 191, 182, 165),
                              outline=(252, 250, 247, 200), width=2)
    return img


# ---------------------------------------------------------------- 树脂块
def gen_resin(seed):
    """树脂块（1.21.4+）：琥珀橙红，半透明流动感 + 蜂巢六边纹理。"""
    base = (222, 96, 30)
    img = colorize(base, soft_fbm(16, 16, seed), contrast=0.30,
                   gray2=soft_fbm(40, 40, seed + 6))
    d = ImageDraw.Draw(img, "RGBA")
    r = random.Random(seed + 21)
    # 六边形蜂巢格
    hs = 26
    for row in range(-1, int(N / (hs * 0.86)) + 2):
        cy = row * hs * 0.86
        for col in range(-1, int(N / hs) + 2):
            cx = col * hs + (hs / 2 if row % 2 else 0)
            pts = [(cx + hs * 0.5 * math.cos(TAU * k / 6),
                    cy + hs * 0.5 * math.sin(TAU * k / 6)) for k in range(6)]
            col2 = (clamp(base[0] * r.uniform(0.85, 1.12)),
                    clamp(base[1] * r.uniform(0.8, 1.15)),
                    clamp(base[2] * r.uniform(0.8, 1.2)), 46)
            d.polygon(pts, fill=col2, outline=(255, 170, 70, 70))
    # 高光亮点
    op = img.load()
    hi = noise_field_periodic(60, 60, seed + 91).load()
    for y in range(N):
        for x in range(N):
            if hi[x, y] > 225:
                c = op[x, y]
                op[x, y] = (clamp(c[0] + 20), clamp(c[1] + 35), clamp(c[2] + 20))
    return img


# ---------------------------------------------------------------- 竹块 / 去皮竹块
def gen_bamboo_side(seed, stripped=False):
    """竹块侧面：纵向竹条/纤维。竹块偏绿带节，去皮偏亮黄绿。"""
    if stripped:
        base = (201, 205, 96)
    else:
        base = (150, 172, 62)
    cx, cy = 5, 120  # 纵向纤维（x 低频、y 高频 -> 竖直条纹）
    fiber = noise_field_periodic(cx, cy, seed)
    img = colorize(base, fiber, contrast=0.24,
                   gray2=soft_fbm(18, 18, seed + 7))
    d = ImageDraw.Draw(img, "RGBA")
    r = random.Random(seed + 300)
    # 竹条分界（竖直）
    nb = 12
    for k in range(nb + 1):
        x = k * N / nb + r.uniform(-2, 2)
        d.line([x, 0, x, N], fill=(clamp(base[0] * 0.62),
                                   clamp(base[1] * 0.62),
                                   clamp(base[2] * 0.62), 90), width=2)
        d.line([x + 2, 0, x + 2, N], fill=(255, 255, 210, 34), width=1)
    # 竹块带横向竹节；去皮竹块节更淡
    if not stripped:
        for yy in (48, 156):
            d.line([0, yy, N, yy], fill=(90, 108, 40, 120), width=4)
            d.line([0, yy + 3, N, yy + 3], fill=(205, 220, 110, 90), width=2)
    return img


def gen_bamboo_top(seed, stripped=False):
    """竹块顶面：竹节横截面，同心分区 + 放射纤维。"""
    base = (206, 210, 102) if stripped else (158, 180, 70)
    img = colorize(base, soft_fbm(14, 14, seed), contrast=0.18)
    d = ImageDraw.Draw(img, "RGBA")
    c = N / 2
    r = random.Random(seed + 44)
    # 放射状纤维
    for k in range(36):
        a = TAU * k / 36 + r.uniform(-0.03, 0.03)
        d.line([c + math.cos(a) * 14, c + math.sin(a) * 14,
                c + math.cos(a) * c, c + math.sin(a) * c],
               fill=(clamp(base[0] * 0.7), clamp(base[1] * 0.7),
                     clamp(base[2] * 0.7), 70), width=2)
    # 同心竹节环
    for rad, al in ((30, 90), (66, 70), (100, 80)):
        d.ellipse([c - rad, c - rad, c + rad, c + rad],
                  outline=(clamp(base[0] * 0.6), clamp(base[1] * 0.6),
                           clamp(base[2] * 0.6), al), width=3)
    d.ellipse([c - 14, c - 14, c + 14, c + 14],
              fill=(clamp(base[0] * 0.82), clamp(base[1] * 0.82),
                    clamp(base[2] * 0.82), 120))
    return img


# ---------------------------------------------------------------- 生成全部
JOBS = [
    ("amethyst_block.png",        lambda: gen_gem((150, 86, 200), 101, n=30, sparkle=1.1)),
    ("diamond_block.png",         lambda: gen_gem((58, 190, 185), 202, n=28, sparkle=1.15)),
    ("emerald_block.png",         lambda: gen_gem((48, 172, 96),  303, n=28, sparkle=1.1)),
    ("lapis_block.png",           lambda: gen_gem((34, 64, 178),  404, n=26, sparkle=0.9)),
    ("redstone_block.png",        lambda: gen_gem((226, 38, 30),  505, n=26, contrast=0.5, sparkle=1.2)),
    ("gold_block.png",            lambda: gen_metal((250, 204, 55), 606, axis="x")),
    ("iron_block.png",            lambda: gen_metal((236, 238, 240), 707, axis="x")),
    ("copper_block.png",          lambda: gen_metal((198, 116, 72), 808, axis="y")),
    ("coal_block.png",            lambda: gen_coal(909)),
    ("netherite_block.png",       lambda: gen_netherite(1010)),
    ("quartz_block.png",          lambda: gen_quartz(1111, side=False)),
    ("quartz_block_side.png",     lambda: gen_quartz(1111, side=True)),
    ("raw_copper_block.png",      lambda: gen_raw_ore((126, 110, 92), (198, 112, 66), 1212)),
    ("raw_gold_block.png",        lambda: gen_raw_ore((128, 116, 96), (236, 192, 60), 1313)),
    ("raw_iron_block.png",        lambda: gen_raw_ore((124, 112, 98), (208, 202, 190), 1414)),
    ("resin_block.png",           lambda: gen_resin(1515)),
    ("bamboo_block.png",          lambda: gen_bamboo_side(1616, stripped=False)),
    ("bamboo_block_top.png",      lambda: gen_bamboo_top(1616, stripped=False)),
    ("stripped_bamboo_block.png", lambda: gen_bamboo_side(1717, stripped=True)),
    ("stripped_bamboo_block_top.png", lambda: gen_bamboo_top(1717, stripped=True)),
]


def seam_diff(path):
    """检测左右/上下接缝平均色差（0 为完美无缝）。"""
    im = Image.open(path).convert("RGB")
    p = im.load()
    dl = dg = 0
    for i in range(N):
        a, b = p[0, i], p[N - 1, i]
        dl += abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
        a, b = p[i, 0], p[i, N - 1]
        dg += abs(a[0] - b[0]) + abs(a[1] - b[1]) + abs(a[2] - b[2])
    return (dl / N / 3, dg / N / 3)


if __name__ == "__main__":
    print("Generating mineral/compressed blocks ...")
    for fn, maker in JOBS:
        img = maker()
        img.save(os.path.join(OUT, fn))
        l, t = seam_diff(os.path.join(OUT, fn))
        print(f"  {fn:36s} {img.size}  seam L={l:5.1f} T={t:5.1f}")

    # 预览拼图（5 列，标注英文名）
    cols = 5
    cell, pad, lab = 128, 10, 18
    rows = (len(JOBS) + cols - 1) // cols
    W = cols * (cell + pad) + pad
    H = rows * (cell + pad + lab) + pad
    prev = Image.new("RGB", (W, H), (26, 26, 30))
    d = ImageDraw.Draw(prev)
    for k, (fn, _mk) in enumerate(JOBS):
        r, c = divmod(k, cols)
        x = pad + c * (cell + pad)
        y = pad + r * (cell + pad + lab)
        im = Image.open(os.path.join(OUT, fn)).convert("RGB").resize((cell, cell))
        prev.paste(im, (x, y))
        d.text((x + 2, y + cell + 2), fn.replace(".png", ""), fill=(220, 220, 220))
    pprev = os.path.join(OUT, "_preview.png")
    prev.save(pprev)
    print("preview:", pprev)
    print("DONE ->", OUT)
