# -*- coding: utf-8 -*-
"""写实草地/泥土/沙子素材 -> Minecraft Java 版 256X 材质包（纯 Pillow，无 numpy）"""
import os, json, math, zipfile
from PIL import Image

BASE = r"D:\WorkSpace(WB)\2026-11-17-20-32-26"
SRC = os.path.join(BASE, "_tex_source")
OUT = os.path.join(BASE, "realistic-256x-pack")
BLK = os.path.join(OUT, "assets", "minecraft", "textures", "block")
os.makedirs(BLK, exist_ok=True)

GRASS_SRC  = os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-17T13-02-55.png")
DIRT_SRC   = os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-17T13-03-37.png")
SAND_SRC   = os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-17T13-04-05.png")
GRAVEL_SRC = os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-17T13-28-49.png")
COBBLE_SRC = os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-17T13-33-51.png")
STONE_SRC  = os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-17T13-34-09.png")
GRANITE_SRC= os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-17T13-34-32.png")
BASALT_SRC = os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-17T13-34-55.png")
SANDSTONE_SRC=os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-17T13-35-17.png")
DIRTPATH_SRC= os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-17T13-35-38.png")
DIORITE_SRC= os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-17T13-35-56.png")
# 衍生方块素材
STONEBRICK_SRC = os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-18T06-46-53.png")
CRACKBRICK_SRC = os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-18T06-47-19.png")
MOSSYBRICK_SRC = os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-18T06-47-38.png")
MOSSYCOBBLE_SRC= os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-18T06-47-58.png")
CHISELSTONE_SRC= os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-18T06-48-18.png")
CHISELSAND_SRC= os.path.join(SRC, "Seamless_tileable_top_down_tex_2026-11-18T06-48-46.png")

TARGET = 256
BORDER = 36


def load_crop(path):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    side = int(min(w, h) * 0.88)  # 裁掉右下角水印
    im = im.crop((0, 0, side, side))
    return im.resize((TARGET, TARGET), Image.LANCZOS)


def make_seamless(im, border=BORDER):
    """边缘渐变融合，左右/上下边缘一致，实现无缝平铺。"""
    px = im.load()
    w, h = im.size
    for i in range(border):
        t = 1.0 - i / border
        for y in range(h):
            l = px[i, y]; r = px[w - 1 - i, y]
            for c in range(3):
                avg = (l[c] + r[c]) / 2
                v = int(avg * t + l[c] * (1 - t))
                px[i, y] = px[i, y][:c] + (v,) + px[i, y][c + 1:]
                v2 = int(avg * t + r[c] * (1 - t))
                px[w - 1 - i, y] = px[w - 1 - i, y][:c] + (v2,) + px[w - 1 - i, y][c + 1:]
    for i in range(border):
        t = 1.0 - i / border
        for x in range(w):
            a = px[x, i]; b = px[x, h - 1 - i]
            for c in range(3):
                avg = (a[c] + b[c]) / 2
                v = int(avg * t + a[c] * (1 - t))
                px[x, i] = px[x, i][:c] + (v,) + px[x, i][c + 1:]
                v2 = int(avg * t + b[c] * (1 - t))
                px[x, h - 1 - i] = px[x, h - 1 - i][:c] + (v2,) + px[x, h - 1 - i][c + 1:]
    return im


def polish(im, strength=0.55):
    """抛光：降低颗粒/裂纹对比、轻微提亮，模拟磨制石材的均匀致密表面。"""
    from PIL import ImageFilter, ImageEnhance
    out = im.filter(ImageFilter.GaussianBlur(radius=1.1))
    out = ImageEnhance.Contrast(out).enhance(1.0 - 0.45 * strength)
    out = ImageEnhance.Brightness(out).enhance(1.0 + 0.10 * strength)
    return out


def deframe(im, strength=0.9, band=26):
    """
    消除 AI 全景素材的"边缘受光"白框。

    症状：素材四周一圈比内部偏亮（俯视草地尤其明显），平铺后每个方块
    都以亮边收尾，游戏里能清楚读出棋盘格轮廓。

    做法：以"到最近边的距离"分层统计每圈平均色，与中央安全区基准比对，
    再把偏差按 smoothstep 权重从边缘向内部衰减扣掉。
      - 按圈统计而非逐像素，避免草叶细节把偏差估歪
      - 距离取四边最小值，四角天然对称 -> 打平后接缝依旧连续
      - 只动亮度层，不改色相结构，草叶细节完整保留
    强度 0.9 实测把边缘偏差从 (+9,+13,+1) 压到 (+1.2,+0.8,-0.1)；
    1.2 会过冲成暗边，故默认 0.9。
    """
    px = im.load()
    w, h = im.size

    # 中央安全区（距边 >=32）作基准，不受边缘污染
    s = [0, 0, 0]
    c = 0
    for y in range(h):
        for x in range(w):
            if min(x, y, w - 1 - x, h - 1 - y) >= 32:
                q = px[x, y]
                for i in range(3):
                    s[i] += q[i]
                c += 1
    ref = [v / c for v in s]

    # 逐圈平均偏差
    dev = {d: [0, 0, 0] for d in range(band)}
    cnt = {d: 0 for d in range(band)}
    for y in range(h):
        for x in range(w):
            d = min(x, y, w - 1 - x, h - 1 - y)
            if d < band:
                q = px[x, y]
                for i in range(3):
                    dev[d][i] += q[i]
                cnt[d] += 1
    for d in dev:
        if cnt[d]:
            dev[d] = [dev[d][i] / cnt[d] - ref[i] for i in range(3)]

    out = im.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            d = min(x, y, w - 1 - x, h - 1 - y)
            if d < band:
                t = 1.0 - d / band
                wgt = t * t * (3 - 2 * t)  # smoothstep
                q = px[x, y]
                op[x, y] = tuple(
                    max(0, min(255, int(round(q[i] - dev[d][i] * wgt * strength))))
                    for i in range(3))
    return out


# 草地顶面：先无缝融合，再消除 AI 素材边缘受光造成的白框（无边框草地）
grass  = deframe(make_seamless(load_crop(GRASS_SRC)))
dirt   = make_seamless(load_crop(DIRT_SRC))
sand   = make_seamless(load_crop(SAND_SRC))
gravel = make_seamless(load_crop(GRAVEL_SRC))
grass.save(os.path.join(BLK, "grass_block_top.png"))
dirt.save(os.path.join(BLK, "dirt.png"))
sand.save(os.path.join(BLK, "sand.png"))
gravel.save(os.path.join(BLK, "gravel.png"))

# ---- 单面石质方块 ----
cobble  = make_seamless(load_crop(COBBLE_SRC))
stone   = make_seamless(load_crop(STONE_SRC))
granite = make_seamless(load_crop(GRANITE_SRC))
diorite = make_seamless(load_crop(DIORITE_SRC))
cobble.save(os.path.join(BLK, "cobblestone.png"))
stone.save(os.path.join(BLK, "stone.png"))
granite.save(os.path.join(BLK, "granite.png"))
diorite.save(os.path.join(BLK, "diorite.png"))

# ---- 玄武岩：侧面 + 顶/底（顶用同一素材的轻微旋转变体）----
basalt = make_seamless(load_crop(BASALT_SRC))
basalt.save(os.path.join(BLK, "basalt_side.png"))
basalt.rotate(90).save(os.path.join(BLK, "basalt_top.png"))

# ---- 砂岩：侧面（层理水平）+ 顶/底 ----
sandstone = make_seamless(load_crop(SANDSTONE_SRC))
sandstone.save(os.path.join(BLK, "sandstone_side.png"))
sandstone.save(os.path.join(BLK, "sandstone_top.png"))
sandstone.save(os.path.join(BLK, "sandstone_bottom.png"))

# ---- 衍生方块：石砖家族 / 苔藓 / 錾制 ----
stonebrick = make_seamless(load_crop(STONEBRICK_SRC))
crackbrick = make_seamless(load_crop(CRACKBRICK_SRC))
mossybrick = make_seamless(load_crop(MOSSYBRICK_SRC))
mossycoble = make_seamless(load_crop(MOSSYCOBBLE_SRC))
stonebrick.save(os.path.join(BLK, "stone_bricks.png"))
crackbrick.save(os.path.join(BLK, "cracked_stone_bricks.png"))
mossybrick.save(os.path.join(BLK, "mossy_stone_bricks.png"))
mossycoble.save(os.path.join(BLK, "mossy_cobblestone.png"))
# 錾制方块是整面居中浮雕，不做无缝平铺（与游戏原版一致），直接裁水印后缩放
chiselstone = load_crop(CHISELSTONE_SRC)
chiselsand  = load_crop(CHISELSAND_SRC)
chiselstone.save(os.path.join(BLK, "chiseled_stone_bricks.png"))
chiselsand.save(os.path.join(BLK, "chiseled_sandstone.png"))

# ---- 磨制系列：从原石材抛光派生 ----
polish(granite).save(os.path.join(BLK, "polished_granite.png"))
polish(diorite).save(os.path.join(BLK, "polished_diorite.png"))
polish(basalt).save(os.path.join(BLK, "polished_basalt_side.png"))
polish(basalt.rotate(90)).save(os.path.join(BLK, "polished_basalt_top.png"))
# 平滑玄武岩：直接用玄武岩顶面（游戏原版即如此）
basalt.rotate(90).save(os.path.join(BLK, "smooth_basalt.png"))
# 切制砂岩：砂岩顶面均匀化（游戏原版切制砂岩六面用 sandstone_top）
sandstone.save(os.path.join(BLK, "cut_sandstone.png"))

# ---- 土径：顶面 + 侧面（薄草边 + 泥土）----
dirtpath = make_seamless(load_crop(DIRTPATH_SRC))
dirtpath.save(os.path.join(BLK, "dirt_path.png"))
# 侧面：顶部约 1/8 草皮，下方夯土，用正弦叠加做不规则边界
dpd = dirtpath.load(); gpd = grass.load(); dpdirt = dirt.load()
sidep = Image.new("RGB", (TARGET, TARGET)); spp = sidep.load()
w = TARGET
for x in range(w):
    wv = (1.0 * math.sin(2 * math.pi * x / w + 0.6)
          + 0.5 * math.sin(2 * math.pi * 2 * x / w + 2.1)
          + 0.25 * math.sin(2 * math.pi * 4 * x / w + 1.2))
    wv /= 1.75
    by = max(2, min(TARGET - 2, int(0.13 * TARGET + 0.03 * TARGET * wv)))
    for y in range(TARGET):
        if y < by:
            spp[x, y] = gpd[x, y]
        elif y < by + 3:
            t = (y - by) / 3
            a = gpd[x, y]; b = dpd[x, y]
            spp[x, y] = tuple(int(a[c] * (1 - t) + b[c] * t) for c in range(3))
        else:
            spp[x, y] = dpd[x, y]
sidep.save(os.path.join(BLK, "dirt_path_side.png"))

# ---- 草方块侧面：不规则草皮边界 + 上草下土 ----
gp = grass.load(); dp = dirt.load()
w = TARGET
# 整数周期正弦叠加，保证 x=0 与 x=w 连续
boundary = []
for x in range(w):
    wave = (1.0 * math.sin(2 * math.pi * 1 * x / w + 0.3)
            + 0.55 * math.sin(2 * math.pi * 2 * x / w + 1.7)
            + 0.30 * math.sin(2 * math.pi * 3 * x / w + 0.9)
            + 0.16 * math.sin(2 * math.pi * 6 * x / w + 2.4))
    wave /= 2.01
    base = int(0.21 * TARGET); amp = int(0.055 * TARGET)
    boundary.append(max(2, min(TARGET - 2, int(base + amp * wave))))

side = Image.new("RGB", (TARGET, TARGET))
sp = side.load()
gray = grass.convert("L")
gr_px = gray.load()
blend_w = 3
for x in range(w):
    by = boundary[x]
    for y in range(TARGET):
        if y < by - blend_w:
            sp[x, y] = gp[x, y]
        elif y <= by:
            t = (y - (by - blend_w)) / blend_w
            a = gp[x, y]; b = dp[x, y]
            sp[x, y] = tuple(int(a[c] * (1 - t) + b[c] * t) for c in range(3))
        else:
            sp[x, y] = dp[x, y]
side.save(os.path.join(BLK, "grass_block_side.png"))

# ---- 侧面覆盖层：草皮灰度提亮 + 透明渐变，用于生物群系染色 ----
ov = Image.new("RGBA", (TARGET, TARGET), (0, 0, 0, 0))
op = ov.load()
for x in range(w):
    by = boundary[x]
    g = min(255, int(gr_px[x, y] * 1.25 + 38)) if False else None
    for y in range(TARGET):
        if y < by - 5:
            alpha = 120
        elif y <= by:
            alpha = int(120 * (by - y) / 5)
        else:
            alpha = 0
        if alpha > 0:
            g = min(255, int(gr_px[x, y] * 1.25 + 38))
            op[x, y] = (g, g, g, alpha)
ov.save(os.path.join(BLK, "grass_block_side_overlay.png"))

# ---- 元数据 ----
meta = {"pack": {
    "description": "写实地形/石材/木材/矿物/织物 256X · 菌核流动动画 · Realistic Terrain, Wood, Minerals & Fabric",
    "pack_format": 75,
    "supported_formats": [75, 75]
}}
with open(os.path.join(OUT, "pack.mcmeta"), "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

# ---- 图标（6x3 布局）----
# 动态读取 block 目录全部贴图，自动拼成图标网格（含后续加入的木头贴图）
import glob as _glob
_all_tex = sorted(os.path.basename(p) for p in _glob.glob(os.path.join(BLK, "*.png")))
_cols = 9
_rows = (len(_all_tex) + _cols - 1) // _cols
_cell = 48
icon = Image.new("RGB", (_cols * _cell, _rows * _cell), (30, 30, 30))
for idx, fn in enumerate(_all_tex):
    t = Image.open(os.path.join(BLK, fn)).convert("RGB")
    if t.height != t.width:
        # 动画贴图是纵向 sprite sheet，取首帧当缩略图，否则会被拉成长条
        t = t.crop((0, 0, t.width, t.width))
    icon.paste(t.resize((_cell, _cell)), ((idx % _cols) * _cell, (idx // _cols) * _cell))
icon.save(os.path.join(OUT, "pack.png"))

# README 文案抽到独立模板文件，改文案只改 README.template.md，无需动脚本
_tpl = os.path.join(BASE, "README.template.md")
with open(_tpl, "r", encoding="utf-8") as _f:
    readme = _f.read()
# 同时写入项目根目录与包内，保证两处 README 同步
for _rp in (os.path.join(BASE, "README.md"), os.path.join(OUT, "README.md")):
    with open(_rp, "w", encoding="utf-8") as f:
        f.write(readme)

# ---- 打包 zip ----
zip_path = os.path.join(BASE, "RealisticStoneTerrain_256x.zip")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(OUT):
        for fn in files:
            fp = os.path.join(root, fn)
            # 关键：相对 OUT 打包，让 pack.mcmeta / assets 直接位于 zip 根目录
            # （若相对 BASE 会多套一层 realistic-256x-pack 文件夹，游戏识别不到）
            z.write(fp, os.path.relpath(fp, OUT))

print("DONE")
for fn in sorted(os.listdir(BLK)):
    if not fn.lower().endswith(".png"):
        continue  # 跳过 .png.mcmeta 这类动画元数据文件
    print(" -", fn, Image.open(os.path.join(BLK, fn)).size)
print("zip:", zip_path)
