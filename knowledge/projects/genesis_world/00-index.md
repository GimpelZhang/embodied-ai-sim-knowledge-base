# genesis_world（Genesis World）· 项目索引

> 更新日期：2026-08-29
> 上游仓库：`github.com/Genesis-Embodied-AI/genesis-world`
> 核对版本：**v1.3.3**（HEAD `19f56d6`，2026-08-30，Apache 2.0）
> 本机源料：`sources/genesis_world/`（已 gitignore；含 `genesis-upstream/` clone 与三份源料）

---

## 一句话定位

**Genesis World 是 Genesis AI 出品的通用具身智能仿真平台**：把刚体 / FEM / MPM / SPH / PBD / Stable-Fluid 六类求解器放进**同一个场景、同一份状态**，用**可互换的耦合器**处理跨物理交互，配一套**带硬件缺陷建模的传感器子系统**，主打"仿真评测能可靠预测真机性能"。

## 三点摘要（选型时先看这个）

1. **官方宣传的"四层栈"有一半不在这个包里。** Render 层的 **Nyx** 在 `genesis/**/*.py` 中 **grep 零命中** —— 它是独立包 `gs-nyx`，按**插件**装；Compiler 层的 **Quadrants** 是独立包（`import quadrants as qd`，硬依赖 `quadrants==1.3.0` 精确 pin）。**默认 `pip install genesis-world` 装出来的是 LegacyCoupler + PyRender/Luisa/Madrona，没有 Nyx。** 另：博客称 "Genesis World **1.0**"，pip 上是 **1.3.3**，两套编号别混引。

2. **多物理与耦合器是真本事，但切换不是行为中性的。** 8 个 solver 在树内（`rigid/` `fem` `mpm` `sph` `pbd` `sf` `kinematic` `tool`）；三种耦合器 **Legacy（默认）/ SAP（Drake 式半解析 + hydroelastic）/ IPC**，改一行 `coupler_options=` 即可切换 —— 但 `sap_coupler.py` 里有 **20 个物料对专用的接触 handler**，换耦合器后**必须重新验证你那组材料组合**。且 **IPC 支需额外 `pip install pyuipc`，仅 Linux/Windows x86 + NVIDIA**。

3. **传感器子系统完整，但"默认即理想真值"。** 两层缺陷继承：`SensorOptions` 给全部传感器 `delay`/`jitter`/`history_length`，`SimpleSensorOptions` 追加 `resolution`/`bias`/`noise`/`random_walk`（含 IMU 的 3 轴 × 5 类完整矩阵）。**但所有缺陷参数默认都是 `0.0`**，不显式配就是理想值；**相机直接派生自 `Sensor`，根本没有这层噪声字段** —— 视觉策略的鲁棒性测试要自己在图像上加扰动。

## 关键标签

`通用物理引擎` `多物理耦合` `可微分仿真` `大规模并行环境` `强化学习训练` `VLA评测` `传感器仿真` `触觉仿真` `激光雷达` `IPC接触` `光线追踪渲染` `GaussianSplat` `跨平台GPU` `sim2real` `数字孪生` `USD` `MJCF` `URDF`

---

## 文档层次现状

| 层 | 文件 | 行数 | 状态 |
|---|---|---|---|
| 【速查层】 | `quickstart.md` | — | ⏳ 待编写（Task10） |
| 【原理层】 | [`background_knowledge.md`](background_knowledge.md) | **1197** | ✅ 已完成（9 章齐备，含 §2.5 传感器仿真 7 小节） |
| 【经验层】 | `ai_knowledge.md` | — | ⏳ 待编写（Task5） |
| 【排障层】 | `troubleshooting.md` | — | ⏳ 待编写（Task6） |
| 【代码层】 | `code_knowledge.md` | — | ⏳ 待编写（Task9，对象是本机 `genesis-world-tour/`） |

> ⏳ **目前只有原理层。** 其余四层完成后本表与下方章节地图需同步更新（见项目 `CLAUDE.md` 的「三处索引同步更新」约定）。
> ⚠️ `background_knowledge.md` 中已存在指向 `quickstart.md` / `ai_knowledge.md` / `troubleshooting.md` / `code_knowledge.md` 的**前向链接（暂为死链）**，位于 L730 / L887 / L902 / L904 / L1114 与 §9.5。四层补齐后要回头核对这几处。

### 该读哪一层

| 手上有什么 | 去哪 |
|---|---|
| 查 API / 参数 / 设计原理 / 能力边界 | [`background_knowledge.md`](background_knowledge.md)（**用下方行号表精准读，勿整篇读 1197 行**） |
| **要动手跑** | ⏳ 速查层未就绪 → 暂用原理层 **§6 基本使用流程（L734–907）** + **§5.6 装完第一件事（L718）** |
| **一条具体报错** | ⏳ 排障层未就绪 → 暂用原理层 **§8 已知问题与限制（L1052–1117）** |
| **要改代码** | ⏳ 代码层未就绪 → 暂用原理层 **§3 架构与模块（L393–550）** + **§7 常用 API（L908–1051）** |

---

## `background_knowledge.md` 章节地图（原理层，1197 行；带行号，用 `Read` 的 `offset`/`limit` 精准读取）

> ⚠️ **行号是 2026-08-29 快照。** 若读到的内容与描述不符，用
> `grep -n '^#\{2,3\} ' knowledge/projects/genesis_world/background_knowledge.md`
> 重新定位并**顺手更新本表**。

### 高频入口（先看这五处）

| 想知道什么 | 直接读 |
|---|---|
| **这东西是什么、值不值得用** | L1–25（文档头**三条落差警告**）+ L81–88（§1.5 不适用场景） |
| **Nyx / Quadrants 到底在不在包里** | ⭐⭐ **L395–424（§3.1 四层栈对照表 + grep 证据）** |
| **传感器出的数能不能用** | ⭐⭐ **L186–313（§2.5 全章）**，尤其 L305–313（§2.5.7「默认理想化」） |
| **装之前要知道的坑** | L659–733（§5 全章），尤其 **L682–701（§5.3 依赖 pin 表）** |
| **能力有没有 / 别再搜了** | ⭐ **L1100–1117（§8.4 未提及清单）** |

### 逐章行号

| 章节 | 行号 | 内容要点 |
|---|---|---|
| 文档头（读法 / 证据等级 / 三条落差警告） | **1–25** | ⚠️ **动手前必读**：Nyx&Quadrants 出树、1.0 vs 1.3.3 编号错位、项目改名史 |
| **§1 项目概述** | **26–88** | |
| ├ 1.1 身份与定位 | 28–42 | Genesis AI 出品；前身是 2024-12 的学术项目 "Genesis" |
| ├ 1.2 它解决什么问题 | 43–59 | 200h 真机 → <0.5h 仿真对照表 `[官网]` |
| ├ 1.3 为什么"先做评测，再做数据生成" | 60–69 | 含 zero-shot real-to-sim |
| ├ 1.4 主要用途与适用场景 | 70–80 | |
| └ 1.5 不适用 / 需谨慎的场景 | 81–88 | ⭐ **选型必读**；含"速度基准有、sim-real 评测套件没有"的更正 |
| **§2 核心原理** | **89–392** | |
| ├ 2.1 统一多物理 | 91–111 | 8 个 solver 总表 |
| ├ **2.2 三种可互换耦合器** | **112–135** | ⭐⭐ `coupler_options=` 一行切换（已核对代码）；⚠️ `[推断]` 物料对支持度可能不同 |
| ├ 2.3 External Articulation Constraint | 136–156 | 把关节动力学嵌进 IPC 优化（含公式） |
| ├ 2.4 Barrier-free Elastodynamics | 157–185 | 增广拉格朗日替换对数壁垒（含公式）；宣称 103× |
| ├ **2.5 传感器仿真原理（重点章节）** | **186–313** | ⭐⭐ 见下方细分表 |
| ├ 2.6 渲染 | 314–339 | Nyx 三条设计原则 · 三条渲染路径 · Gaussian Splat |
| ├ 2.7 Quadrants | 340–364 | 对"调度开销"的四路攻击；fork 自 Taichi **2025-06** |
| └ 2.8 sim-to-real gap 可归因分解 | 365–392 | 三层 gap + 指标表 + ⭐**负面结论：开环指标区分不出模型** |
| **§3 架构与模块** | **393–550** | |
| ├ **3.1 四层栈 vs 仓库实际内容** | **395–424** | ⭐⭐ **本节最重要**：`grep -rn -i nyx genesis/ --include=*.py` → **0 命中** |
| ├ 3.2 顶层包结构 | 425–447 | `genesis/` 13 个子项 |
| ├ 3.3 `genesis/engine/` 仿真核心 | 448–485 | solvers(8) / couplers(3) / entities / materials 全表 |
| ├ 3.4 `genesis/options/` 用户配置面 | 486–504 | ⭐ **写代码接触最多的目录**；各 `gs.*` 命名空间对应文件 |
| ├ 3.5 `genesis/vis/` 渲染 | 505–521 | ⚠️ v1.3.3 只有 `Rasterizer`/`RayTracer`/`BatchRenderer`，**无 Nyx 类** |
| └ **3.6 一次仿真的数据流** | **522–550** | ⭐ 全流程接线图；**`build()` 是不可逆分界线** |
| **§4 关键特性** | **551–658** | |
| ├ 4.1 大规模并行环境 | 553–571 | ⚠️ `n_envs=0` 与 `=1` 张量形状不同；`env_spacing` **只影响可视化** |
| ├ 4.2 跨后端与多平台 | 572–585 | `cpu/gpu/cuda/amdgpu/metal`；**只有 GPU + `n_envs>0` 才吃满并行** |
| ├ 4.3 可微分仿真 | 586–597 | ⚠️ `substeps_local % substeps == 0` 硬约束；显存线性增长 |
| ├ 4.4 声明式配置（Pydantic） | 598–614 | ⭐ **solver options 覆盖 `SimOptions` 同名字段**的规则 |
| ├ 4.5 多格式资产加载 | 615–626 | MJCF/URDF/USD/Mesh/Terrain/Drone |
| ├ 4.6 传感器套件 | 627–630 | 指回 §2.5 |
| ├ 4.7 状态快照与断点续跑 | 631–644 | ⭐ `reset(envs_idx=)` 按环境子集重置 —— RL 关键能力 |
| ├ 4.8 调试可视化 | 645–650 | 12 个 `draw_debug_*` |
| └ 4.9 录制 | 651–658 | camera 录像 vs `scene.start_recording` 通用录制 |
| **§5 安装与依赖** | **659–733** | |
| ├ 5.1 Python 与 PyTorch 前置 | 661–670 | ⚠️ **torch 不在依赖里，必须先装**；Python `>=3.10,<3.14` |
| ├ 5.2 四种安装方式 | 671–681 | pip / git / editable / uv |
| ├ **5.3 核心依赖清单** | **682–701** | ⭐⭐ **6 处带界/排除 pin 的原因逐条列出**；`quadrants==1.3.0` 精确 pin |
| ├ 5.4 可选扩展 | 702–710 | ⚠️ `pyuipc`（IPC，仅 Linux/Win x86+NV）、`gs-nyx`（Nyx）**都不是默认装的** |
| ├ 5.5 `[dev]`/`[docs]` extras | 711–717 | ⚠️ **mujoco 版本冲突**：主依赖 `>=3.2.5` vs dev `>=3.10,<3.11` |
| └ 5.6 装完第一件事 | 718–733 | 三条自检命令 |
| **§6 基本使用流程** | **734–907** | |
| ├ **6.1 最小可运行程序** | **736–764** | ⭐⭐ 6 行代码 + **五步强制顺序图** |
| ├ 6.2 `Scene` 完整构造面 | 765–792 | 全部 17 个参数；⚠️ `show_FPS` 已废弃 |
| ├ **6.3 控制机器人** | **793–827** | ⭐⭐ **`set_dofs_position` vs `control_dofs_position` 的区别**（最容易混） |
| ├ 6.4 并行环境 | 828–849 | ⭐ 用 `gs.device` 建张量；`envs_idx=` 是全库约定 |
| ├ 6.5 加传感器与相机 | 850–869 | `read_sensors()` 返回 **`dict[type[Sensor], Tensor]`**（按类型聚合） |
| ├ 6.6 典型工作流：RL 训练 | 870–888 | 六步骨架 |
| └ 6.7 典型工作流：VLA 闭环评测 | 889–907 | ⭐ 建议用**几何断言**而非看图判定成功 |
| **§7 常用 API 接口** | **908–1051** | |
| ├ 7.1 顶层 `gs.*` | 912–927 | `gs.init` 全部 10 个参数 |
| ├ **7.2 `Scene`** | **928–958** | ⭐ 按「声明期 / 运行期」分表，全部带行号 |
| ├ **7.3 `RigidEntity`** | **959–1015** | ⭐⭐ 控制 / 增益 / 硬置 / 查询 / 结构属性 / IK+规划，全部带行号；⚠️ **IK 三个实用细节** |
| ├ 7.4 `Camera` | 1016–1026 | 四种图；不需要的通道别开 |
| ├ 7.5 传感器 | 1027–1040 | ⚠️ `jitter>delay` **抛异常**；`delay` 非 `dt` 整数倍**静默取整** |
| └ 7.6 API 稳定性提示 | 1041–1051 | 行号只对 v1.3.3 成立 + 核对命令 |
| **§8 已知问题与限制** | **1052–1117** | |
| ├ **8.1 `[CODE]` 级 15 条** | **1056–1075** | ⭐⭐ **可自行验证的硬事实，做决策只信这组** |
| ├ 8.2 `[推断]` 级 3 条 | 1076–1083 | 耦合器非行为中性 · ElastomerTaxel 不是真 FEM · `performance_mode` 代价未知 |
| ├ 8.3 `[官网]`/`[文章]` 级 11 条 | 1084–1099 | 103× / 4.6× / Pearson 0.8996 等**未验证宣称** + 5 条第三方判断 |
| └ **8.4 未提及清单（9 项）** | **1100–1117** | ⭐⭐ **命中就别再搜了** |
| **§9 参考资源** | **1118–1197** | |
| ├ 9.1 官方 | 1120–1131 | 仓库 / 文档站 / 博客 / nyx / quadrants |
| ├ 9.2 仓库内最值得读的位置 | 1132–1145 | ⭐ 按"想知道什么"路由到 `examples/` 各子目录 |
| ├ 9.3 上游技术血缘 | 1146–1164 | ⭐ 各 solver 参考实现是谁（查行为特征时有用） |
| ├ 9.4 引用格式 | 1165–1173 | 两条 BibTeX（平台 vs 2024 原始项目） |
| ├ 9.5 本知识库关联文档 | 1174–1186 | 五层现状 |
| └ 9.6 源料清单 | 1187–1197 | 仅本机有效 |

### §2.5 传感器仿真章 细分行号（L186–313）

| 小节 | 行号 | 要点 |
|---|---|---|
| 2.5.1 子系统组织 | 192–197 | `SensorManager` + 15 个传感器文件 |
| **2.5.2 已实现传感器清单**（对照宣称逐条核实） | **198–214** | ⭐⭐ **逐条核对宣传 vs 代码**，含"宣称之外还有"的额外项 |
| **2.5.3 硬件缺陷两层继承** | **215–245** | ⭐⭐ `SensorOptions`(4 字段) → `SimpleSensorOptions`(+4 字段)；⚠️ **相机不在噪声层** |
| 2.5.4 IMU（建模最完整的传感器） | 246–260 | acc/gyro/mag × resolution/cross_axis/noise/bias/random_walk |
| 2.5.5 触觉：两条技术路线 | 261–294 | Kinematic taxel vs **HydroShear 弹性体**（SDF 驱动，非真 FEM） |
| 2.5.6 激光雷达 / 深度射线投射 | 295–307 | ⚠️ **`no_hit_value` 默认等于 `max_range` 的歧义陷阱** |
| **2.5.7「默认理想化」** | **308–313** | ⭐⭐ **本章头号结论：所有缺陷参数默认 0.0** |

> 精确重定位：`grep -n '^#\{4\} 2\.5' knowledge/projects/genesis_world/background_knowledge.md`

---

## 五个"别踩"提醒（给未来的自己）

1. **别以为装了 `genesis-world` 就有 Nyx 渲染。** `nyx` 在 `genesis/**/*.py` 里零命中，要 `pip install gs-nyx`。v1.3.3 的 `gs.renderers` 下只有 `Rasterizer`/`RayTracer`/`BatchRenderer`（§3.1、§3.5）。
2. **别以为传感器默认带噪声。** 缺陷参数全部默认 `0.0`，相机连字段都没有 —— 不显式配置，你测的是理想真值（§2.5.7、§8.1 #3/#4）。
3. **别在 `build()` 之后想加东西。** `add_entity`/`add_sensor`/`add_camera` 都必须在 `build()` 之前（§3.6、§8.1 #11）。
4. **别凭直觉升级依赖。** 6 处 pin 各对应一个已知上游破坏，`quadrants==1.3.0` 是精确 pin，`[dev]` 会把 mujoco 收紧到 3.10.x（§5.3、§5.5、§8.1 #6/#7/#8）。
5. **别把博客数字当工程依据。** 103× / 4.6× / Pearson 0.8996 全是 `[官网]` 级，评测套件未开源。速度类倒是可以自测：`examples/speed_benchmark/`、`tests/benchmarks/`（§8.3、§1.5）。

---

## 本机源料位置（**仅在本机有效**）

| 内容 | 路径 | 证据等级 |
|---|---|---|
| 源料 URL 清单（3 条） | `sources/genesis_world/background.txt` | — |
| 第三方技术分析（136 行） | `sources/genesis_world/Genesis_world_01.txt` | `[文章]` |
| 官方博客译文（292 行） | `sources/genesis_world/Genesis_world_02.txt` | `[官网]` |
| **上游仓库 clone** | `sources/genesis_world/genesis-upstream/` ← **`[CODE]` 级证据都在这里核实** | `[CODE]` |
| 复现过程原始记录（16471 行） | `sources/genesis_world/genesis-world-tour.md` | `[实践]` |
| 本机复现仓库（33 文件） | `genesis-world-tour/`（代码层的描述对象） | `[CODE]` |

⚠️ `sources/` 与 `genesis-world-tour/` 均已 gitignore，换机器需重新 clone。
