# 写实地形、石材、木材、矿物、织物、混凝土与花卉 256X 材质包

这是一个给 Minecraft Java 版用的高清写实材质包。原版 16×16 的方块贴图被放大到 256×256，
细节多了 16 倍。草、石头、木头、矿物、织物、混凝土和花都按真实质感重做，但方块的形状和辨识度
保持原样，不会出现认不出是什么方块的情况。

只支持 1.21.11，pack_format 75，覆盖 1.21.11-pre1 到正式版。更早的游戏版本加载不了。

## 为什么做这个包
原版贴图分辨率低，直接放大就糊了，还容易出现一块一块的色块。所以我按七类方块重画了一遍：
地形、石材、木材、矿物和压缩方块、织物（羊毛、床、旗帜）、混凝土和混凝土粉末，
以及全部 17 种小型花和 5 种大型花。

模型和方块的对应关系没有动。台阶、楼梯、墙、压力板这些形状变体不用单独做贴图，
游戏自己会调用基础方块的贴图。

## 具体做法
- 木纹是纯程序算出来的，没用 AI。用 Pillow 写了可缩放的值噪声（fBm），加上径向年轮和
  树种配色，白桦的横皮孔、金合欢的橙红、樱花木的粉色都是单独调的。
- 矿物方块同样是程序生成。宝石用周期 Voronoi 做晶面，金属是拉丝配错缝的锭板倒角，
  粗金属则是岩石底上嵌矿粒。17 种方块一共 20 张贴图，四边都能无缝拼。
- 羊毛、床、旗帜这类织物，底图是 AI 生成的，之后做无缝化和染色。按 Minecraft 标准的
  16 色板调色，一共 48 张，颜色准，接缝也处理掉了。
- 混凝土和粉末用了 2 张 AI 底图，一张致密水泥、一张松散粉粒。把亮度归一化压掉杂质以后
  再染成 16 色，32 张放一起质感区分很清楚。
- 花一共 22 种（17 小 + 5 大）。AI 画写实花，抠掉黑底，同形态的花共用一张底图染色，
  比如四种郁金香、三种蓝花都是从一张底图变出来的。大花拆成上下两片，对应原版的 top/bottom。
- 草地边缘原来有一圈素材自带的白框，已经修掉了，平铺看不出网格。
- 原木侧面的树皮和裂纹改成周期噪声生成，接缝在生成的时候就不存在，不是事后补的。
- 绯红和诡异菌核的侧面做成了流动动画。纵向 sprite sheet 配 .png.mcmeta，用 interpolate
  过渡，循环起来看不出接缝。

最终一共 190 张贴图，外加 2 个动画元数据文件。

## 主要贴图清单
- grass_block_top.png 草方块顶部（写实草地，去掉了素材边缘的白框，平铺没有网格轮廓）
- grass_block_side.png 草方块侧面（草皮到泥土的过渡）
- grass_block_side_overlay.png 草皮覆盖层（支持生物群系染色）
- dirt.png 泥土（草方块底部）
- sand.png 沙子
- gravel.png 砂砾（碎石加鹅卵石）
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

## 木材与木板（23 种，木纹全部程序生成）
- 原木侧 + 顶：oak / spruce / birch / jungle / acacia / dark_oak / mangrove / cherry / pale_oak
  （各 `_log.png` + `_log_top.png`）
  * 原木侧面无缝，树皮和裂纹都用周期噪声生成，平铺找不到接缝和方块轮廓；白桦保留了细横疤皮孔
- 菌核侧 + 顶：crimson / warped（各 `_stem.png` + `_stem_top.png`）
- 菌核侧面是流动动画：`crimson_stem.png` / `warped_stem.png` 做成了 8 帧纵向 sprite sheet（256×2048），
  配套 `crimson_stem.png.mcmeta` / `warped_stem.png.mcmeta` 控制播放。
  绯红 frametime=4，诡异 frametime=3，都开了 interpolate，一轮大约 1.2 到 1.6 秒
- 木板：橡木 / 云杉 / 白桦 / 丛林 / 金合欢 / 深色橡木 / 红树 / 樱花 / 苍白橡木 / 竹 / 绯红 / 诡异（各 `_planks.png`）
- 杨木和杨木木板暂时没有，1.21.11 里还没有杨树更新

## 矿物与压缩方块（17 种，程序生成）
- 宝石块（周期 Voronoi 晶面，带切面反光）：amethyst_block 紫水晶 / diamond_block 钻石 /
  emerald_block 绿宝石 / lapis_block 青金石 / redstone_block 红石
- 金属块（金属拉丝，错缝锭板倒角）：gold_block 金 / iron_block 铁 / copper_block 铜
- 深色矿物块：coal_block 煤炭（带树脂光泽）/ netherite_block 下界合金（暗红余烬斑）
- 石英：`quartz_block.png` 顶底（乳白晶质）/ `quartz_block_side.png` 侧面（菱形浮雕）
- 粗金属块（岩石底嵌矿粒）：raw_copper_block 粗铜 / raw_gold_block 粗金 / raw_iron_block 粗铁
- 树脂块：`resin_block.png`（琥珀橙红，蜂巢六边纹，1.21.4+）
- 竹块：`bamboo_block.png` + `bamboo_block_top.png`（侧面竹条竹节，顶面是横截面）
- 去皮竹块：`stripped_bamboo_block.png` + `stripped_bamboo_block_top.png`（偏亮黄绿）

## 织物：羊毛、床与旗帜（16 色，AI 底图 + 染色）
- 羊毛：`block/<color>_wool.png` ×16（蓬松羊毛绒，AI 写实素材染色，边缘做了融合）
- 床：`entity/bed/<color>.png` ×16（512×512，按原版 UV 分区做：白色枕头、染色床单、木质床架）
- 旗帜：`entity/banner/<color>_banner.png` ×16（粗帆布织纹，256×256）
- 16 色：white / light_gray / gray / black / brown / red / orange / yellow / lime / green /
  cyan / light_blue / blue / purple / magenta / pink，走的是 Minecraft 标准羊毛色板
- 地毯、羊毛台阶、羊毛楼梯没有单独的贴图，游戏会自动用对应颜色的羊毛贴图
- 挽具（1.21.4+）这次没做

## 混凝土与混凝土粉末（16 色，AI 底图 + 染色）
- 混凝土：`block/<color>_concrete.png` ×16（致密水泥表面，有细孔和骨料，AI 底图染色）
- 混凝土粉末：`block/<color>_concrete_powder.png` ×16（松散颗粒和团块的质感，AI 底图染色）
- 16 色用的是 Minecraft 标准混凝土色板，比羊毛更饱和一些。两张白色底图先做亮度归一化，
  把杂质斑点压淡，再程序染成 16 色，四边无缝

## 花（17 种小型 + 5 种大型，AI 底图 + 染色）
- 小型花：`block/<name>.png` ×17 —— 蒲公英、金蒲公英、虞美人、兰花、绒球葱、蓝花美耳草、
  滨菊、矢车菊、铃兰、凋灵玫瑰、火把花、闭合眼眸花、张开眼眸花，以及红/橙/白/粉四种郁金香
- 大型花：`block/<name>_top.png` + `block/<name>_bottom.png` ×5 —— 向日葵、丁香、玫瑰丛、牡丹、瓶子草
- 都是 AI 写实底图抠黑底做成，256×256 透明背景；四种郁金香共用一张白花底图染色，
  大花按原版拆成上下两片

台阶、楼梯、墙、压力板、按钮这些形状变体不用单独做贴图，游戏会自动调用上面这些原方块贴图。

除了菌核侧面的动画 sprite sheet（256×2048，8 帧纵向排列）和床贴图，其它都是 256×256。
床是 512×512，原版 64×64 的 8 倍，按原版 UV 分区做的。錾制方块是整面居中浮雕，
和游戏原版一致，不做平铺。

## 使用方式
1. 打开游戏目录 .minecraft/resourcepacks
   （Windows 运行框里输入 %appdata%/.minecraft/resourcepacks）
2. 把文件夹或者 zip 放进去
3. 进游戏：选项 → 资源包 → 选上这个包；换完贴图按 `F3 + T` 重载

## 提示
- 256X 对显卡有点要求，低配机器掉帧的话可以换 128X 版本
- 写实纹理在不同光照下看着会不太一样，这是正常的
- 菌核要流动的话，视频设置里的「动画」得开着

---

# Realistic Terrain, Stone, Wood, Minerals, Fabric, Concrete & Flowers 256X Resource Pack

A high-resolution realistic resource pack for Minecraft Java Edition. Vanilla 16×16 block
textures are scaled up to 256×256, which is 16× the detail. Grass, stone, wood, minerals, fabric,
concrete and flowers have all been redone with a more realistic feel, while the shapes and
recognizability of the blocks stay intact, so you can still tell what you are looking at.

Only 1.21.11 is supported. packs format 75, covering 1.21.11-pre1 through the release. Older
versions will not load the pack.

## Why this pack exists
Vanilla textures are low resolution. Enlarge them and they go blurry, and you start seeing visible
blocks of flat color. So I redrew seven categories: terrain, stone, wood, mineral and compressed
blocks, fabric (wool, beds, banners), concrete plus concrete powder, and all 17 small flowers
and 5 tall flowers.

The model and block mappings are untouched. Slabs, stairs, walls and pressure plates need no
separate textures, since the game pulls the base block texture on its own.

## How it is made
- Wood grain is fully procedural, no AI involved. It uses scalable value noise (fBm) written in
  pure Pillow, plus radial growth rings and per-species color mapping. Birch lenticels, acacia's
  orange-red and cherry's pink were each tuned by hand.
- Mineral blocks are procedural as well. Gems use periodic Voronoi for the facets, metals get
  brushed streaks with staggered ingot bevels, and raw metals are ore grains sitting in rock.
  20 textures for 17 blocks, all tileable on all four edges.
- Fabric like wool, beds and banners starts from an AI-generated base, then gets made seamless
  and dyed. Colors follow the standard Minecraft 16-color palette. 48 textures total, accurate
  colors, seams handled.
- Concrete and powder use 2 AI bases, one dense cement and one loose powder. Brightness is
  normalized to soften impurities before dyeing into 16 colors. The 32 textures read quite
  differently side by side.
- There are 22 flowers in all (17 small, 5 tall). AI draws the realistic blooms, the black
  background is cut out, and flowers of the same shape share one base with a different dye —
  the four tulips and three blue flowers each come from a single source. Tall flowers are split
  into top and bottom halves to match the vanilla layout.
- The grass edge used to carry a white halo from the source image. That is cleaned up, so tiling
  shows no grid.
- Log sides now generate bark and cracks from periodic noise. The seam never exists in the first
  place rather than being patched afterwards.
- Crimson and warped stem sides are animated. A vertical sprite sheet with .png.mcmeta, smoothed
  with interpolate, loops without a visible jump.

All in all that is 190 textures plus 2 animation metadata files.

## Main texture list
- grass_block_top.png Grass block top (realistic grass, source halo removed, no grid when tiled)
- grass_block_side.png Grass block side (grass into dirt transition)
- grass_block_side_overlay.png Grass side overlay (supports biome tinting)
- dirt.png Dirt (grass block bottom)
- sand.png Sand
- gravel.png Gravel (broken stone and pebbles)
- cobblestone.png Cobblestone
- stone.png Stone
- granite.png Granite
- diorite.png Diorite
- basalt_side.png / basalt_top.png Basalt (side and top/bottom)
- sandstone_side.png / sandstone_top.png / sandstone_bottom.png Sandstone (side, top, bottom)
- dirt_path.png / dirt_path_side.png Dirt path (top and side)
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

## Wood and planks (23 blocks, all procedural grain)
- Logs, side and top: oak / spruce / birch / jungle / acacia / dark_oak / mangrove / cherry / pale_oak
  (`_log.png` + `_log_top.png` each)
  * Log sides are seamless. Bark and cracks come from periodic noise, so tiling shows no seam and
    no block outline. Birch keeps its thin horizontal lenticels.
- Stems, side and top: crimson / warped (`_stem.png` + `_stem_top.png` each)
- Stem sides are animated: `crimson_stem.png` and `warped_stem.png` are 8-frame vertical sprite
  sheets (256×2048), driven by `crimson_stem.png.mcmeta` and `warped_stem.png.mcmeta`.
  Crimson uses frametime=4, warped frametime=3, both with interpolate, roughly 1.2 to 1.6 s a loop.
- Planks: Oak / Spruce / Birch / Jungle / Acacia / Dark Oak / Mangrove / Cherry / Pale Oak /
  Bamboo / Crimson / Warped (`_planks.png` each)
- Poplar and poplar planks are missing for now, since 1.21.11 has no poplar update.

## Mineral and compressed blocks (17 blocks, procedural)
- Gem blocks (periodic Voronoi facets with reflective faces): amethyst / diamond / emerald /
  lapis lazuli / redstone
- Metal blocks (brushed metal, staggered ingot bevels): gold / iron / copper
- Dark mineral blocks: coal (resinous sheen) / netherite (dark red ember specks)
- Quartz: `quartz_block.png` top and bottom (milky crystalline) / `quartz_block_side.png` side (diamond relief)
- Raw metal blocks (ore grains in rock): raw copper / raw gold / raw iron
- Resin block: `resin_block.png` (amber orange, honeycomb hex pattern, 1.21.4+)
- Bamboo block: `bamboo_block.png` + `bamboo_block_top.png` (strips and nodes on the side, cross-section on top)
- Stripped bamboo block: `stripped_bamboo_block.png` + `stripped_bamboo_block_top.png` (brighter yellow-green)

## Fabric: wool, beds and banners (16 colors, AI base then dyed)
- Wool: `block/<color>_wool.png` ×16 (fluffy fleece, dyed from an AI realistic source, edges blended)
- Bed: `entity/bed/<color>.png` ×16 (512×512, built on the vanilla UV layout: white pillow, dyed sheet, wooden frame)
- Banner: `entity/banner/<color>_banner.png` ×16 (coarse canvas weave, 256×256)
- 16 colors: white / light_gray / gray / black / brown / red / orange / yellow / lime / green /
  cyan / light_blue / blue / purple / magenta / pink, all on the standard Minecraft wool palette
- Carpet, wool slabs and wool stairs have no separate files, the game reuses the matching wool texture
- Harness (1.21.4+) is not included this time

## Concrete and concrete powder (16 colors, AI base then dyed)
- Concrete: `block/<color>_concrete.png` ×16 (dense cement with fine pores and aggregate, dyed from an AI base)
- Concrete powder: `block/<color>_concrete_powder.png` ×16 (loose grains and clumps, dyed from an AI base)
- Colors follow the standard Minecraft concrete palette, a bit more saturated than wool. Both white
  bases are brightness-normalized to soften impurities, then dyed into 16 colors, seamless on all edges.

## Flowers (17 small + 5 tall, AI base then dyed)
- Small flowers: `block/<name>.png` ×17 — dandelion, golden dandelion, poppy, blue orchid, allium,
  azure bluet, oxeye daisy, cornflower, lily of the valley, wither rose, torchflower, closed and
  open eyeblossom, plus red / orange / white / pink tulips
- Tall flowers: `block/<name>_top.png` + `block/<name>_bottom.png` ×5 — sunflower, lilac, rose bush,
  peony, pitcher plant
- All are AI realistic bases with the black background cut out, 256×256 with transparency. The four
  tulips share one white base with different dyes; tall flowers are split into top and bottom halves.

Shape variants like slabs, stairs, walls, pressure plates and buttons need no separate textures.
The game reuses the base block textures listed above.

Apart from the animated stem sprite sheets (256×2048, 8 frames stacked) and the bed textures,
everything is 256×256. Beds are 512×512, 8× the vanilla 64×64, built on the vanilla UV layout.
Chiseled blocks are a single centered relief, same as vanilla, and are not tiled.

## How to use
1. Open `.minecraft/resourcepacks`
   (on Windows, type `%appdata%/.minecraft/resourcepacks` in the Run dialog)
2. Drop the folder or the zip in there
3. In game: Options → Resource Packs → pick this pack. Press `F3 + T` to reload after swapping

## Notes
- 256X leans on the GPU a little. If a low-end machine stutters, use the 128X version instead.
- Realistic textures look different under different lighting, that is expected.
- The stems only animate while the Animation option in video settings stays on.
