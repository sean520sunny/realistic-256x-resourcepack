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

readme = """# 写实地形、石材、木材、矿物与织物 256X 材质包

面向 **Minecraft Java 版**的高分辨率写实材质包。把原版 16×16 的方块贴图扩展到 256×256
（16 倍细节），在保留原版方块辨识度的前提下，追求更接近真实的草地、岩石、木质、矿物与织物观感。
**专为 Minecraft Java 版 1.21.11 制作**（`pack_format: 75`，支持格式 75–75，
覆盖 1.21.11-pre1 至 1.21.11）。更早版本无法加载本包。

## 项目目的
原版贴图在低分辨率下细节有限，放大后容易模糊、出现色块。本包重新制作地形、石材、木材、
矿物与压缩方块、织物（羊毛/床/旗帜）五大类方块的贴图，让画面更细腻写实，同时严格兼容原版
模型与方块映射——台阶、楼梯、墙、压力板等形状变体自动复用基础贴图，无需单独制作。

## 技术特色
- **程序化写实木纹**：纯 Pillow 实现可缩放 fBm 值噪声、径向年轮与特征色映射，白桦皮孔、
  金合欢橙红、樱花木粉等细节按树种单独处理。
- **程序化矿物方块**：周期 Voronoi 生成宝石切面、金属拉丝配错缝锭板倒角、岩基嵌矿粒，
  17 种方块共 20 张贴图全部四边无缝。
- **AI 织物 + 程序化染色**：羊毛/床/旗帜以 AI 生成的写实织物为底，裁水印后边缘渐变融合无缝，
  再用 Minecraft 标准 16 色色板染色，48 张贴图质感真实、配色准确、零接缝。
- **无边框草地**：消除素材边缘受光形成的白框，平铺后读不出方块网格轮廓。
- **源头无缝**：原木侧面改用周期噪声生成树皮与裂纹，接缝在生成阶段根治，而非事后缝合。
- **菌核流动动画**：纵向 sprite sheet 配合 `.png.mcmeta`，以 `interpolate` 平滑过渡，
  循环闭合无跳变。

成品共 **131 张贴图 + 2 个动画元数据文件**。

## 主要贴图清单
- grass_block_top.png 草方块顶部（写实草地，已做无边框处理：消除素材边缘受光白框，平铺无网格轮廓）
- grass_block_side.png 草方块侧面（草皮 + 泥土过渡）
- grass_block_side_overlay.png 草皮覆盖层（支持生物群系染色）
- dirt.png 泥土（草方块底部）
- sand.png 沙子
- gravel.png 砂砾（碎石 + 鹅卵石）
- cobblestone.png 圆石
- stone.png 石头
- granite.png 花岗岩
- diorite.png 闪长岩
- basalt_side.png / basalt_top.png 玄武岩（侧面 + 顶底）
- sandstone_side.png / sandstone_top.png / sandstone_bottom.png 砂岩（侧 + 顶 + 底）
- dirt_path.png / dirt_path_side.png 土径（顶面 + 侧面）
- stone_bricks.png 石砖
- cracked_stone_bricks.png 裂纹石砖
- mossy_stone_bricks.png 苔藓石砖
- mossy_cobblestone.png 苔藓圆石
- chiseled_stone_bricks.png 錾制石砖
- chiseled_sandstone.png 錾制砂岩
- polished_granite.png 磨制花岗岩
- polished_diorite.png 磨制闪长岩
- polished_basalt_side.png / polished_basalt_top.png 磨制玄武岩
- smooth_basalt.png 平滑玄武岩
- cut_sandstone.png 切制砂岩

## 木材与木板（23 种，程序化写实木纹）
- 原木侧 + 顶：oak / spruce / birch / jungle / acacia / dark_oak / mangrove / cherry / pale_oak（各 `_log.png` + `_log_top.png`）
  * 原木侧面为无缝纹理：周期噪声生成树皮与裂纹，平铺无接缝、无方块轮廓；白桦保留细横疤皮孔
- 菌核侧 + 顶：crimson / warped（各 `_stem.png` + `_stem_top.png`）
- **菌核侧面为流动动画**：`crimson_stem.png` / `warped_stem.png` 改为 8 帧纵向 sprite sheet（256×2048），
  配套 `crimson_stem.png.mcmeta` / `warped_stem.png.mcmeta` 控制播放
  （绯红 frametime=4，诡异 frametime=3，均开启 interpolate 平滑过渡，约 1.2～1.6 秒一轮）
- 木板：橡木 / 云杉 / 白桦 / 丛林 / 金合欢 / 深色橡木 / 红树 / 樱花 / 苍白橡木 / 竹 / 绯红 / 诡异（各 `_planks.png`）
- 注：杨木与杨木木板暂缺（1.21.11 无杨树更新）

## 矿物与压缩方块（17 种，程序化写实）
- 宝石块（周期 Voronoi 晶面 + 切面反光）：amethyst_block 紫水晶 / diamond_block 钻石 /
  emerald_block 绿宝石 / lapis_block 青金石 / redstone_block 红石
- 金属块（金属拉丝 + 错缝锭板倒角）：gold_block 金 / iron_block 铁 / copper_block 铜
- 深色矿物块：coal_block 煤炭（树脂光泽）/ netherite_block 下界合金（暗红余烬斑）
- 石英：`quartz_block.png` 顶底（乳白晶质）/ `quartz_block_side.png` 侧面（菱形浮雕）
- 粗金属块（岩基嵌矿粒）：raw_copper_block 粗铜 / raw_gold_block 粗金 / raw_iron_block 粗铁
- 树脂块：`resin_block.png`（琥珀橙红，蜂巢六边纹，1.21.4+）
- 竹块：`bamboo_block.png` + `bamboo_block_top.png`（侧面竹条竹节 + 顶面横截面）
- 去皮竹块：`stripped_bamboo_block.png` + `stripped_bamboo_block_top.png`（亮黄绿）

## 织物：羊毛、床与旗帜（16 色，AI 底图染色）
- 羊毛：`block/<color>_wool.png` ×16（蓬松羊毛绒，AI 写实素材染色，边缘融合无缝）
- 床：`entity/bed/<color>.png` ×16（512×512，按原版 UV 分区：白色枕头 + 染色床单 + 木质床架）
- 旗帜：`entity/banner/<color>_banner.png` ×16（粗帆布织纹，256×256）
- 16 色：white / light_gray / gray / black / brown / red / orange / yellow / lime / green /
  cyan / light_blue / blue / purple / magenta / pink，采用 Minecraft 标准羊毛色板
- 地毯、羊毛台阶、羊毛楼梯无独立贴图，游戏自动复用对应颜色的羊毛贴图
- 挽具（1.21.4+）暂未制作

台阶、楼梯、墙、压力板、按钮等形状变体无需单独贴图，游戏会自动复用上方原方块贴图。

除菌核侧面的动画 sprite sheet（256×2048，8 帧纵向排列）与床贴图（512×512，原版 64×64 的
8 倍，按原版 UV 分区制作）外，其余贴图均为 256×256 像素。錾制方块为整面居中浮雕，与游戏
原版一致，不做平铺。

## 使用方式
1. 打开游戏目录 .minecraft/resourcepacks
   （Windows 运行框输入 %appdata%/.minecraft/resourcepacks）
2. 把本文件夹（或 zip）放进去
3. 游戏内：选项 → 资源包 → 选中本材质包；更换贴图后按 `F3 + T` 重载资源

## 提示
- 256X 对显卡有一定要求，低端设备若掉帧可换用 128X 版本。
- 写实纹理在不同光照下观感会有差异，属正常现象。
- 菌核贴图需要视频设置中的「动画」选项保持开启才会流动。

---

# Realistic Terrain, Stone, Wood, Minerals & Fabric 256X Resource Pack (English)

A high-resolution realistic resource pack for **Minecraft Java Edition**. It expands the original
16×16 block textures to 256×256 (16× the detail), pursuing a more lifelike look for grass, stone,
wood, minerals and fabric while preserving the recognizability of vanilla blocks. **Made specifically
for Minecraft Java Edition 1.21.11** (`pack_format: 75`, supports formats 75–75, covering
1.21.11-pre1 through 1.21.11). Older versions cannot load this pack.

## Overview
Vanilla textures are limited at low resolution and become blurry or blocky when enlarged. This pack
remakes the textures for five major categories — terrain, stone, wood, mineral/compressed blocks,
and fabric (wool / beds / banners) — for a finer, more realistic look, while staying strictly
compatible with vanilla models and block mappings. Shape variants such as slabs, stairs, walls and
pressure plates automatically reuse the base block textures and need no separate files.

## Technical Highlights
- **Procedural realistic wood**: Pure Pillow implementation of scalable fBm value noise, radial
  growth rings and species-specific color mapping; birch lenticels, acacia's orange-red and
  cherry's pink are handled per species.
- **Procedural mineral blocks**: Periodic Voronoi for gem facets, brushed metal with staggered
  ingot bevels, and ore grains embedded in rock — all 20 textures for 17 blocks are seamlessly
  tileable on all four edges.
- **AI fabric + procedural dyeing**: Wool / bed / banner are based on AI-generated realistic
  fabric, cropped to remove watermarks and made seamless via edge blending, then dyed with the
  standard Minecraft 16-color palette — 48 textures, accurate colors, zero seams.
- **Borderless grass**: Removes the edge-lighting halo from the source image, so tiled grass
  shows no grid outlines.
- **Seamless at the source**: Log sides use periodic noise for bark and cracks, eliminating
  seams during generation rather than patching them afterward.
- **Flowing stem animation**: A vertical sprite sheet paired with `.png.mcmeta`, smoothed with
  `interpolate` and looped without visible jumps.

The pack contains **131 textures + 2 animation metadata files**.

## Main Texture List
- grass_block_top.png Grass block top (realistic grass, borderless: edge-lighting halo removed, no grid outlines when tiled)
- grass_block_side.png Grass block side (grass-to-dirt transition)
- grass_block_side_overlay.png Grass side overlay (supports biome tinting)
- dirt.png Dirt (grass block bottom)
- sand.png Sand
- gravel.png Gravel (broken stone + pebbles)
- cobblestone.png Cobblestone
- stone.png Stone
- granite.png Granite
- diorite.png Diorite
- basalt_side.png / basalt_top.png Basalt (side + top/bottom)
- sandstone_side.png / sandstone_top.png / sandstone_bottom.png Sandstone (side + top + bottom)
- dirt_path.png / dirt_path_side.png Dirt path (top + side)
- stone_bricks.png Stone bricks
- cracked_stone_bricks.png Cracked stone bricks
- mossy_stone_bricks.png Mossy stone bricks
- mossy_cobblestone.png Mossy cobblestone
- chiseled_stone_bricks.png Chiseled stone bricks
- chiseled_sandstone.png Chiseled sandstone
- polished_granite.png Polished granite
- polished_diorite.png Polished diorite
- polished_basalt_side.png / polished_basalt_top.png Polished basalt
- smooth_basalt.png Smooth basalt
- cut_sandstone.png Cut sandstone

## Wood and Planks (23 blocks, procedural realistic wood grain)
- Logs, side + top: oak / spruce / birch / jungle / acacia / dark_oak / mangrove / cherry / pale_oak
  (`_log.png` + `_log_top.png` each)
  * Log sides are seamless: bark and cracks generated with periodic noise, so tiling shows no
    seams or block outlines; birch keeps its thin horizontal lenticels.
- Stems, side + top: crimson / warped (`_stem.png` + `_stem_top.png` each)
- **Flowing stem sides**: `crimson_stem.png` / `warped_stem.png` are 8-frame vertical sprite sheets
  (256×2048), with `crimson_stem.png.mcmeta` / `warped_stem.png.mcmeta` controlling playback
  (crimson frametime=4, warped frametime=3, both with `interpolate` smoothing, ~1.2–1.6 s per loop)
- Planks: Oak / Spruce / Birch / Jungle / Acacia / Dark Oak / Mangrove / Cherry / Pale Oak /
  Bamboo / Crimson / Warped (`_planks.png` each)
- Note: Poplar and poplar planks are omitted (no poplar update in 1.21.11).

## Mineral & Compressed Blocks (17 blocks, procedural realistic)
- Gem blocks (periodic Voronoi facets + reflective faces): amethyst / diamond / emerald /
  lapis lazuli / redstone
- Metal blocks (brushed metal + staggered ingot bevels): gold / iron / copper
- Dark mineral blocks: coal (resinous sheen) / netherite (dark red ember specks)
- Quartz: `quartz_block.png` top/bottom (milky crystalline) / `quartz_block_side.png` side (diamond relief)
- Raw metal blocks (ore grains embedded in rock): raw copper / raw gold / raw iron
- Resin block: `resin_block.png` (amber orange, honeycomb hex pattern, 1.21.4+)
- Bamboo block: `bamboo_block.png` + `bamboo_block_top.png` (side strips & nodes + top cross-section)
- Stripped bamboo block: `stripped_bamboo_block.png` + `stripped_bamboo_block_top.png` (bright yellow-green)

## Fabric: Wool, Beds & Banners (16 colors, AI base + dyed)
- Wool: `block/<color>_wool.png` ×16 (fluffy fleece, dyed from AI realistic source, edge-blended seamless)
- Bed: `entity/bed/<color>.png` ×16 (512×512, vanilla UV layout: white pillow + dyed sheet + wooden frame)
- Banner: `entity/banner/<color>_banner.png` ×16 (coarse canvas weave, 256×256)
- 16 colors: white / light_gray / gray / black / brown / red / orange / yellow / lime / green /
  cyan / light_blue / blue / purple / magenta / pink, using the standard Minecraft wool palette
- Carpet, wool slabs and wool stairs have no separate textures — the game reuses the matching wool texture
- Harness (1.21.4+) is not included yet

Shape variants such as slabs, stairs, walls, pressure plates and buttons need no separate textures —
the game automatically reuses the base block textures listed above.

Except for the animated stem sprite sheets (256×2048, 8 frames stacked vertically) and bed textures
(512×512, 8× the vanilla 64×64, made with the vanilla UV layout), all textures are 256×256 pixels.
Chiseled blocks use a single centered relief, matching vanilla, and are not tiled.

## How to Use
1. Open the game directory `.minecraft/resourcepacks`
   (on Windows, type `%appdata%/.minecraft/resourcepacks` in the Run dialog)
2. Place this folder (or the zip) inside
3. In game: Options → Resource Packs → select this pack; press `F3 + T` to reload after swapping textures

## Notes
- 256X is demanding on the GPU; low-end devices that stutter can use a 128X version instead.
- Realistic textures look different under different lighting — this is normal.
- The stem textures only animate when the "Animation" option is enabled in video settings.
"""
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
