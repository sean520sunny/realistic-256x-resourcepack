# 更新日志 / Changelog

面向 Minecraft Java 版 1.21.11 的写实 256X 材质包。本文件记录各版本的主要变更。
A realistic 256X resource pack for Minecraft Java Edition 1.21.11. This file records notable changes per version.

---

## v1.2.1 — 修复床贴图 / Bed Texture Fix

修复 v1.2.0 中床贴图缺失白色枕头的问题，按原版 UV 布局重建 16 色床贴图。

Fixes the missing white pillow in v1.2.0 beds; all 16 bed textures rebuilt with the vanilla UV layout.

- **白色枕头**：床头上半部补上原版式白枕（白底 + 浅灰中央凹块 + 枕套边框），固定白色不参与染色
- **木质床架**：补上原版木架与横向板缝（复用橡木木板纹理）
- **正确 UV**：原版床贴图实为 64×64（非 64×32），改为 512×512（8 倍），按原版分区：白枕 + 染色床单 + 木架，仅床单染色
- **White pillow**: vanilla-style pillow on the head half (white base + light-gray center + border), kept white and excluded from dyeing
- **Wooden frame**: restored the vanilla wooden bed frame with plank seams (reused oak planks texture)
- **Correct UV**: vanilla bed texture is 64×64 (not 64×32); rebuilt at 512×512 (8×) with the proper UV layout — only the sheet is dyed

## v1.2.0 — 织物与 1.21.11 / Fabric & 1.21.11

- 新增 16 色羊毛、床、旗帜共 48 张织物贴图（AI 写实底图 + 标准色板染色，无缝）
- 材质包版本锁定 1.21.11（`pack_format: 75`，`supported_formats: [75, 75]`）
- Added 48 fabric textures — 16-color wool, beds and banners (AI realistic base + standard palette dyeing, seamless)
- Locked the pack to Minecraft 1.21.11 (`pack_format: 75`, `supported_formats: [75, 75]`)

## v1.1.0 — 矿物与压缩方块 / Mineral & Compressed Blocks

- 新增 17 种矿物/压缩方块共 20 张程序化贴图：宝石块、金属块、深色矿物、石英、粗金属、树脂、竹块/去皮竹块
- Added 20 procedural textures for 17 mineral/compressed blocks: gems, metals, dark minerals, quartz, raw metals, resin, bamboo/stripped bamboo

## v1.0.0 — 首个 GitHub 正式版 / First GitHub Release

- 地形（草/泥土/沙/砂砾）、石材（圆石/石头/花岗岩/闪长岩/玄武岩/砂岩/土径及衍生）、木材/木板/菌核动画
- Terrain, stone, wood/planks and flowing Nether-stem animations

## 0.8 — 初始版本 / Initial Release

- 材质包首个上传版本，包含草方块、泥土、沙子等基础地形贴图
- The first uploaded version, with basic terrain textures: grass block, dirt, sand, etc.
