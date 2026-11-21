# 写实地形、石材、木材、矿物、织物与混凝土 256X 材质包

面向 **Minecraft Java 版**的高分辨率写实材质包。把原版 16×16 的方块贴图扩展到 256×256
（16 倍细节），在保留原版方块辨识度的前提下，追求更接近真实的草地、岩石、木质、矿物、织物与混凝土观感。
**专为 Minecraft Java 版 1.21.11 制作**（`pack_format: 75`，支持格式 75–75，
覆盖 1.21.11-pre1 至 1.21.11）。更早版本无法加载本包。

## 项目目的
原版贴图在低分辨率下细节有限，放大后容易模糊、出现色块。本包重新制作地形、石材、木材、
矿物与压缩方块、织物（羊毛/床/旗帜）、混凝土与混凝土粉末六大类方块的贴图，让画面更细腻写实，
同时严格兼容原版模型与方块映射——台阶、楼梯、墙、压力板等形状变体自动复用基础贴图，无需单独制作。

## 技术特色
- **程序化写实木纹**：纯 Pillow 实现可缩放 fBm 值噪声、径向年轮与特征色映射，白桦皮孔、
  金合欢橙红、樱花木粉等细节按树种单独处理。
- **程序化矿物方块**：周期 Voronoi 生成宝石切面、金属拉丝配错缝锭板倒角、岩基嵌矿粒，
  17 种方块共 20 张贴图全部四边无缝。
- **AI 织物 + 程序化染色**：羊毛/床/旗帜以 AI 生成的写实织物为底，裁水印后边缘渐变融合无缝，
  再用 Minecraft 标准 16 色色板染色，48 张贴图质感真实、配色准确、零接缝。
- **混凝土与粉末**：2 张 AI 写实底图（致密水泥 / 松散粉粒）经亮度归一压淡杂质、程序化染色
  成 16 色混凝土 + 16 色粉末，32 张贴图质感区分明显、四边无缝。
- **无边框草地**：消除素材边缘受光形成的白框，平铺后读不出方块网格轮廓。
- **源头无缝**：原木侧面改用周期噪声生成树皮与裂纹，接缝在生成阶段根治，而非事后缝合。
- **菌核流动动画**：纵向 sprite sheet 配合 `.png.mcmeta`，以 `interpolate` 平滑过渡，
  循环闭合无跳变。

成品共 **163 张贴图 + 2 个动画元数据文件**。

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

## 混凝土与混凝土粉末（16 色，AI 底图染色）
- 混凝土：`block/<color>_concrete.png` ×16（致密水泥表面，细孔与骨料，AI 底图染色）
- 混凝土粉末：`block/<color>_concrete_powder.png` ×16（松散颗粒/团块质感，AI 底图染色）
- 16 色采用 Minecraft 标准混凝土色板（比羊毛更饱和）；两张白色底图经亮度归一压淡杂质斑点，
  程序化染成 16 色，四边无缝

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

# Realistic Terrain, Stone, Wood, Minerals, Fabric & Concrete 256X Resource Pack (English)

A high-resolution realistic resource pack for **Minecraft Java Edition**. It expands the original
16×16 block textures to 256×256 (16× the detail), pursuing a more lifelike look for grass, stone,
wood, minerals, fabric and concrete while preserving the recognizability of vanilla blocks. **Made
specifically for Minecraft Java Edition 1.21.11** (`pack_format: 75`, supports formats 75–75, covering
1.21.11-pre1 through 1.21.11). Older versions cannot load this pack.

## Overview
Vanilla textures are limited at low resolution and become blurry or blocky when enlarged. This pack
remakes the textures for six major categories — terrain, stone, wood, mineral/compressed blocks,
fabric (wool / beds / banners), and concrete & concrete powder — for a finer, more realistic look, while staying strictly
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
- **Concrete & powder**: 2 AI realistic bases (dense cement / loose powder) with brightness
  normalization to soften impurities, dyed into 16 concrete + 16 powder textures — distinct
  looks and seamless edges.
- **Borderless grass**: Removes the edge-lighting halo from the source image, so tiled grass
  shows no grid outlines.
- **Seamless at the source**: Log sides use periodic noise for bark and cracks, eliminating
  seams during generation rather than patching them afterward.
- **Flowing stem animation**: A vertical sprite sheet paired with `.png.mcmeta`, smoothed with
  `interpolate` and looped without visible jumps.

The pack contains **163 textures + 2 animation metadata files**.

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

## Concrete & Concrete Powder (16 colors, AI base + dyed)
- Concrete: `block/<color>_concrete.png` ×16 (dense cement surface with fine pores and aggregate)
- Concrete powder: `block/<color>_concrete_powder.png` ×16 (loose granular/clumpy texture)
- 16 colors use the standard Minecraft concrete palette (more saturated than wool); two white AI
  bases are brightness-normalized to soften impurities, then dyed — all seamlessly tileable

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
