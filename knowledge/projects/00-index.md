# 项目花名册 · 索引

> 更新日期：2026-08-30 ｜ 上级：[`../00-index.md`](../00-index.md)
>
> 本文件是**选型与定位层**：先在这里确定「查哪个项目」，再进入该项目的 `00-index.md` 定位章节。
>
> 🌐 **跨项目内容不在这里**：横向对比与选型建议见 [`../global/toolchain_comparison.md`](../global/toolchain_comparison.md)（含适用边界与**反向选型**），通用复现流程 / 问题分类 / 最佳实践 / 术语对照见 [`../global/00-index.md`](../global/00-index.md)。**本库还没收录的新工具链，从全局层开始。**

---

## 总表

| 项目 slug | 名称 / 上游 | 开发方 | 状态 | ⭐ quickstart（速查层） | background（原理层） | ai_knowledge（经验层） | troubleshooting（排障层） | code_knowledge（代码层） | 项目内索引 |
|---|---|---|---|---|---|---|---|---|---|
| `genie_sim_v3` | Genie Sim 3.x (`AgibotTech/genie_sim`) | 智元机器人 AgiBot | ✅ 已完成 | [`quickstart.md`](genie_sim_v3/quickstart.md) | [`background_knowledge.md`](genie_sim_v3/background_knowledge.md) | [`ai_knowledge.md`](genie_sim_v3/ai_knowledge.md) | [`troubleshooting.md`](genie_sim_v3/troubleshooting.md) | [`code_knowledge.md`](genie_sim_v3/code_knowledge.md) | [`00-index.md`](genie_sim_v3/00-index.md) |
| `genesis_world` | Genesis World (`Genesis-Embodied-AI/genesis-world`) | Genesis Embodied AI | ✅ 已完成（五层齐备） | [`quickstart.md`](genesis_world/quickstart.md) | [`background_knowledge.md`](genesis_world/background_knowledge.md) | [`ai_knowledge.md`](genesis_world/ai_knowledge.md) | [`troubleshooting.md`](genesis_world/troubleshooting.md) | [`code_knowledge.md`](genesis_world/code_knowledge.md) | [`00-index.md`](genesis_world/00-index.md) |
| `ge_sim_v2` | GE-Sim-V2 (`AgibotTech/GE-Sim-V2`) | 智元机器人 AgiBot | ✅ 已完成（五层齐备） | [`quickstart.md`](ge_sim_v2/quickstart.md) | [`background_knowledge.md`](ge_sim_v2/background_knowledge.md) | [`ai_knowledge.md`](ge_sim_v2/ai_knowledge.md) | [`troubleshooting.md`](ge_sim_v2/troubleshooting.md) | [`code_knowledge.md`](ge_sim_v2/code_knowledge.md) | [`00-index.md`](ge_sim_v2/00-index.md) |
| `lw_benchhub` | LW-BenchHub (`LightwheelAI/LW-BenchHub`) | 光轮智能 Lightwheel | ✅ 已完成（五层齐备） | [`quickstart.md`](lw_benchhub/quickstart.md) | [`background_knowledge.md`](lw_benchhub/background_knowledge.md) | [`ai_knowledge.md`](lw_benchhub/ai_knowledge.md) | [`troubleshooting.md`](lw_benchhub/troubleshooting.md) | [`code_knowledge.md`](lw_benchhub/code_knowledge.md) | [`00-index.md`](lw_benchhub/00-index.md) |

**四类文档的分工**（按"手上有什么"选）：

| 你现在的处境 | 去哪 | 层次 |
|---|---|---|
| **手上有一条报错 / 异常现象** | `troubleshooting.md` 顶部「快速症状索引」 | **排障层**，Q&A，`[实践]` 级 |
| **要跑起来 / 要改代码 / 找某个类或参数在哪个文件** | `code_knowledge.md` §2 入口点、§3 核心模块、§4 配置系统 | **代码层**，`[CODE]`/`[实践]`/`[推断]` 级 |
| 想知道**为什么会这样、当时试错走过哪些弯路** | `ai_knowledge.md` §4（含"无效尝试"列） | **经验层**，全篇 `[实践]` 级 |
| 查 **API / 参数 / 设计原理 / 版本能力** | `background_knowledge.md`（固定 9 章） | **原理层**，多为 `[CODE]`/`[PAPER]` 级 |

> ⚠️ **代码层描述的是本机实战复现仓库 `<project>_tour`，不是上游本体**，可能落后于上游版本；跨版本迁移前先读该文的版本落差说明。

---

## 1. genie_sim_v3 — Genie Sim 3.x

- **开发方**：智元机器人（AgiBot / AgibotTech）
- **版本**：v3.2.0（发布 2026-06-25），许可证 MPL-2.0
- **background 文档**：[`genie_sim_v3/background_knowledge.md`](genie_sim_v3/background_knowledge.md)（1694 行，9 章齐备）
- **ai_knowledge 文档**：[`genie_sim_v3/ai_knowledge.md`](genie_sim_v3/ai_knowledge.md)（393 行，复现实战复盘，`[实践]` 级）
- **troubleshooting 文档**：[`genie_sim_v3/troubleshooting.md`](genie_sim_v3/troubleshooting.md)（605 行，`Q01`–`Q29` FAQ，按现象检索，`[实践]` 级）
- **code_knowledge 文档**：[`genie_sim_v3/code_knowledge.md`](genie_sim_v3/code_knowledge.md)（1251 行，8 章，对应复现仓库 `genie_sim_v3_tour`，`[CODE]`/`[实践]`/`[推断]` 级）
- ⭐ **quickstart 速查卡**：[`genie_sim_v3/quickstart.md`](genie_sim_v3/quickstart.md)（385 行，环境准备 / 3 个运行示例 / 改参数 / 9 个常见代码问题 / 一分钟自检清单）——**要动手先读这个**
- **项目内索引**：[`genie_sim_v3/00-index.md`](genie_sim_v3/00-index.md) ← **先读这个拿行号**

**简短总结**
以 OpenUSD 为唯一真值源、构建在 Isaac Sim 5.1 之上的具身智能仿真与**评测**平台。最反直觉的一点是它不是单一仿真器，而是**三套共存的栈**：RT Engine（ROS 2 原生实时闭环）、Benchmark/Data-collection（直连 Isaac Sim，跑评测与采集）、RLinf（CPU MuJoCo 多进程，跑 RL 训练）——三者的物理、渲染、传感器通路完全不同，排障时不可混谈。物理侧三后端可切换（PhysX 默认 / Isaac Newton 实验仅刚体 / Newton-standalone 唯一支持布料软体）。真正的护城河是评测体系：200+ 任务、10 万+ 场景、5140 资产、10000+ 小时合成数据，并作为 RoboColiseum 竞赛引擎。**已知短板**：传感器仅 RGB 有噪声模型，深度/IMU/LiDAR 全为几何真值，是 sim2real 的明确缺口。

**关键标签**
`物理仿真` `OpenUSD` `IsaacSim` `ROS2集成` `评测基准` `数据采集` `VLA闭环` `传感器仿真` `强化学习训练` `Real2Sim-3DGS` `遥操作` `容器化部署` `Headless渲染` `运动规划-cuRobo`

**复现经验摘要**（详见 `ai_knowledge.md`）
一次五阶段实战（环境搭建 → LLM 场景生成 → 3DGS 重建 → USD 物理注入 → 资产规范化）的三条最高价值结论：① **Isaac Sim 5.1 要求硬件 RT cores（Compute Capability ≥ 7.5）**，V100 的 7.0 会导致渲染器静默失败、benchmark 永久挂起，软件光追不被接受；② **CUDA 架构错配会伪装成显存问题**（极小张量报 OOM、请求 56 GiB），换卡后必须重编译所有 CUDA 扩展；③ **"日志在刷 ≠ 任务在跑"**，需用 GPU 利用率、端口 ESTABLISHED、日志明确标记等独立判据。另有 18 条带"无效尝试"记录的问题条目可直接用于排障；已改写为 [`troubleshooting.md`](genie_sim_v3/troubleshooting.md) 的 29 条 Q&A，**带报错就直接查那里的「快速症状索引」**。

**代码层摘要**（详见 `code_knowledge.md`）
描述对象是复现仓库 `genie_sim_v3_tour`（91 个已跟踪文件 / 约 15.7K 行 / 仅 4 个提交）。三个最关键特征：① **它是叠在上游之上的覆盖层，不能独立跑通** —— 无任何 `requirements.txt`/`setup.py`，`entrypoint.sh`、`patch/*.patch`、生成器主体、`assets/`、`openpi/` 全部缺失。② **工作量在"新写"而非"改上游"** —— 经逐文件复核站得住的上游改动仅三类（`enable_cameras` 涉 2 文件、`api_core.py:429` `timeout=600`、重建 `Dockerfile:8` `TORCH_CUDA_ARCH_LIST` `8.9→8.0`），而新写约 1800 行 Python：Real2Sim USD 编写工具箱（三层 prim 树 + 材质图接线）、绕开 WebUI 的 CLI 场景生成、G1–G4 数值门禁。③ **陷阱集中在硬编码与平台假设** —— 容器路径 `/geniesim/main`、`TORCH_CUDA_ARCH_LIST`（本仓库 `8.0`／上游 `8.9`，换卡必重编）、带哈希的 extscache 路径、`:latest` 镜像 tag、Real2Sim 对齐常数只存在于源码。该文 §8.3 还为 `Q15`/`Q16`/`Q22`/`Q17` 等排障条目补上了 `[CODE]` 级机制解释，§6.4 指出 v3.2.0 已上游修掉整条"相机全黑"故障链，但 `timeout=600` 是唯一一条**必须带到新版本**的改动。⚠️ §7.3 记录两类明文凭据曾进入公开仓库（LLM API key 3 文件 + 宿主机 sudo 口令 2 文件共 36 处），已于 2026-08-29 吊销/改密，明文串清理待做。

**本机相关资源**（均已 gitignore，仅本地有效）
- 源料清单：`sources/genie_sim_v3/background.txt`（上游仓库 + arXiv:2601.02078 + 官方文档站）
- 上游仓库克隆：`sources/genie_sim_v3/genie_sim/`
- 实战复现仓库：`genie_sim_v3_tour/`（Stage 1 容器化闭环 / Stage 2 LLM 场景生成 / Stage 3 3DGS 实采重建导入）—— **代码结构已提炼进 `code_knowledge.md`，查代码优先读文档**

---

## 2. genesis_world — Genesis World

- **开发方**：Genesis Embodied AI（Genesis AI）
- **版本**：核对于 **v1.3.3**（HEAD `19f56d6`，2026-08-30），许可证 **Apache 2.0**；PyPI 包名 `genesis-world`，import 名 `genesis`，惯用别名 `gs`
- **background 文档**：[`genesis_world/background_knowledge.md`](genesis_world/background_knowledge.md)（**1205 行**，9 章齐备，含 §2.5 传感器仿真 7 小节）· 核对 **v1.3.3**
- **ai_knowledge 文档**：[`genesis_world/ai_knowledge.md`](genesis_world/ai_knowledge.md)（**362 行**，8 章齐备；`P01`–`P37` / `D01`–`D20` / `L01`–`L08`）· 实测 **v1.2.2**
- **troubleshooting 文档**：[`genesis_world/troubleshooting.md`](genesis_world/troubleshooting.md)（**902 行**，`Q01`–`Q37`，A–H 八类，顶部有 37 行快速症状索引）· 实测 **v1.2.2**
- **code_knowledge 文档**：[`genesis_world/code_knowledge.md`](genesis_world/code_knowledge.md)（**570 行**，8 章齐备）· 对象是本机复现仓库 **`genesis-world-tour/`（不是上游本体）** · 实测 **v1.2.2**
  - 三点特征：① **「一次性演示脚本 + 独立客观验证门」成对结构**（每个 Stage 配一个 `verify_stageN.py`，用 `ffprobe` + `cv2` 像素统计 + JSON 数值断言做无需看图的硬门禁）；② **把 1.2.2 的 API 陷阱固化进代码**（`gs.morphs.Franka` 不存在、IK 返回完整 `qpos(16,)`、`render()` 返回 4-tuple、相机必须在 `build()` 前添加、rsl-rl 0-based checkpoint）；③ **进程隔离 + 降级回退是架构主线**（Stage 3 用 `subprocess.run` 让每阶段独占一次 `gs.init()`；Stage 4 `try IPC / except ImportError → PBD` 并把降级事实写进产物 JSON）
  - 高频入口：**§2 入口点与命令**（14 个入口 × `文件:行号` × 必须的工作目录）· ⭐⭐ **§7.2 静默失效清单（16 行）**「改了没生效」先查这里 · **§7.1 硬编码路径清单（12 文件 / 49 行，已脱敏）** · **§8 与其余四层的四张映射表**
- **quickstart 速查卡**：[`genesis_world/quickstart.md`](genesis_world/quickstart.md)（**260 行**，可整篇读）· 环境准备（三个版本锁定项）/ 3 组运行示例（含预期输出）/ 改参数 / 高频 10 问 / 自检清单 · 实测 **v1.2.2**
- ⚠️ **版本落差**：原理层是 **1.3.3**，经验层/排障层/代码层/速查层均实测于 **1.2.2** —— **API 写法不可跨版本套用，能力边界结论可以**（见 `ai_knowledge.md` §1.3）
- **项目内索引**：[`genesis_world/00-index.md`](genesis_world/00-index.md) ← **先读这个拿行号**

**简短总结**
Genesis AI 出品的通用具身智能仿真平台（前身是 2024-12 的学术项目 "Genesis"）。核心是把 **8 类求解器**（rigid / FEM / MPM / SPH / PBD / stable-fluid / kinematic / tool）放进**同一场景、同一份状态**，用**三种可互换的耦合器**（Legacy 默认 / SAP / IPC，改一行 `coupler_options=` 切换）处理跨物理交互；`scene.build(n_envs=N)` 一键铺开大规模并行；支持可微仿真与 CPU/CUDA/ROCm/Metal 多后端。**⚠️ 官方宣传的"四层栈"有一半不在这个 pip 包里**：Render 层的 **Nyx** 在 `genesis/**/*.py` 中 **grep 零命中**（是独立包 `gs-nyx`，按插件装），Compiler 层的 **Quadrants** 是独立包（硬依赖 `quadrants==1.3.0` 精确 pin）；v1.3.3 的 `gs.renderers` 下只有 `Rasterizer`/`RayTracer`/`BatchRenderer`。另：博客称 "Genesis World **1.0**" 而 pip 上是 **1.3.3**，两套编号勿混引。**传感器子系统是本库四个项目里最完整的**（两层缺陷继承：`SensorOptions` 给全部传感器 `delay`/`jitter`/`history_length`，`SimpleSensorOptions` 追加 `resolution`/`bias`/`noise`/`random_walk`，IMU 有 3 轴×5 类完整矩阵，还有激光雷达 / 深度 / 触觉 / 接触力 / 关节力矩 / 温度栅格），**但所有缺陷参数默认都是 `0.0`（默认即理想真值），且相机直接派生自 `Sensor`、根本没有噪声字段**。

**关键标签**
`物理仿真` `通用物理引擎` `多物理场耦合` `可微分仿真` `大规模并行` `强化学习训练` `软体与流体` `VLA闭环` `场景生成` `传感器仿真` `触觉仿真` `激光雷达` `IPC接触` `光线追踪渲染` `GaussianSplat` `跨平台GPU` `sim2real` `数字孪生` `OpenUSD` `Headless渲染` `四足机器人`

**五个"别踩"提醒**（详见项目内索引末尾）
① **别以为装了 `genesis-world` 就有 Nyx 渲染**（零命中，要 `pip install gs-nyx`）；② **别以为传感器默认带噪声**（全部默认 `0.0`，相机连字段都没有）；③ **别在 `build()` 之后想加实体/传感器/相机**（不可逆分界线）；④ **别凭直觉升级依赖** —— 6 处 pin（`trimesh`/`libigl`/`pyglet`/`z3-solver`/`Pillow`/`pygltflib`）各对应一个已知上游破坏，`quadrants==1.3.0` 是精确 pin，装 `[dev]` 会把 mujoco 从 `>=3.2.5` 收紧到 `>=3.10,<3.11`，**且 PyTorch 不在依赖里必须先单独装**；⑤ **别把博客数字当工程依据**（103× / 4.6× / Pearson 0.8996 全是 `[官网]` 级，sim-real 评测套件未开源；速度类可自测 `examples/speed_benchmark/`、`tests/benchmarks/`）。另有 **15 条 `[CODE]` 级限制**与 **9 项 `未提及` 清单**见 `background_knowledge.md` §8.1 / §8.4。

**复现结局速查**（引用经验层前先看这个）：Stage 1/2 **OpenVLA 抓取闭环 ❌ 0/8**，最终在机制层面证明"当前目标不可达"并主动止损；Patch 01/02（G1 + PI0/Pi0.5）⚠️ **只有计划、无任何执行记录**；Stage 3 **Go2 PPO ✅ 完整跑通**（2048 envs / 151,839 steps·s⁻¹ / 100 epoch ≈ 8 min）；Stage 4 **刚柔·刚流耦合 ✅ 三个 demo 全出**。

**本机相关资源**（均已 gitignore，仅本地有效）
- 源料：`sources/genesis_world/background.txt`（上游仓库 + readthedocs 用户指南 + 官方 blog）、`Genesis_world_01.txt`（第三方技术分析，`[文章]` 级）、`Genesis_world_02.txt`（官方博客译文，`[官网]` 级）
- 上游仓库克隆：`sources/genesis_world/genesis-upstream/` ← **`[CODE]` 级证据都在这里核实**
- 复现原始记录：`sources/genesis_world/genesis-world-tour.md`（16471 行）
- 关键事件提炼：`sources/genesis_world/key_events_summary.md`（35 条 `E01`–`E35`，317 行）← 经验层的直接输入
- 实战复现仓库：`genesis-world-tour/`（33 文件 / 16 个 `.py` / 5608 行；Stage1 OpenVLA 闭环 / Stage2 场景工厂+批量评测 / Stage3 Go2 PPO / Stage4 多物理）← **代码层的描述对象；查代码优先读 `code_knowledge.md`，只在需逐行核实时才翻仓库**

---

## 3. ge_sim_v2 — GE-Sim-V2

- **开发方**：智元机器人（AgibotTech）+ 北航 / LV-NUS / 天大（15 作者）
- **版本**：核对于论文 **arXiv:2605.27491v1**（2026-05-26）+ 上游仓库快照 + HF 权重 `agibot-world/Genie-Envisioner-Sim-v2.0`（`community v2.0.1`）。⚠️ **论文 v1 与发布权重不是同一交付物**，论文数字不必然在发布权重上复现
- **background 文档**：[`ge_sim_v2/background_knowledge.md`](ge_sim_v2/background_knowledge.md)（**1414 行**，9 章齐备，含 **§2.7 传感器仿真专项 6 小节**、**§8.2 五条证据矛盾**、**§8.5 18 条实践修正**，以及 **§9.2 Real2Edit2Real 专节**与 **§9.3 RoboColiseum 平台专节（6 小节，含口径漂移表）**）
- **ai_knowledge 文档**：[`ge_sim_v2/ai_knowledge.md`](ge_sim_v2/ai_knowledge.md)（**469 行**，8 章齐备；`P01`–`P45` / `D01`–`D20` / `L01`–`L09`；⭐ 新增 **§4.6 F 类「契约与口径」故障**）
- **troubleshooting 文档**：[`ge_sim_v2/troubleshooting.md`](ge_sim_v2/troubleshooting.md)（**974 行**，`Q01`–`Q45`，A–F **六类**，带 45 行快速症状索引与贡献指南）
- **code_knowledge 文档**：[`ge_sim_v2/code_knowledge.md`](ge_sim_v2/code_knowledge.md)（**743 行**，8 章齐备；描述对象是本机复现仓库 `GE-Sim-V2-tour/`，**不是上游本体**；含 **13 条静默失效路径**、§8 五张跨层映射表，以及 ⭐ **§3.6.1 线上评测隧道的线路层参数** —— 该二进制分帧协议**在平台文档里是 `未提及` 的，本库是唯一成文来源**）
- **quickstart 文档**：⭐ [`ge_sim_v2/quickstart.md`](ge_sim_v2/quickstart.md)（**312 行**，5 章：环境准备 / 五个 Stage 的运行示例 / 改关键参数 / 高频 8 条 / 自检清单；**派生层，不含新事实**）
- **项目内索引**：[`ge_sim_v2/00-index.md`](ge_sim_v2/00-index.md) ← **先读这个拿行号**
- **⚠️ 定位提醒**：**这不是传统物理仿真器**，而是**动作条件视频生成式世界模型**。**没有物理引擎、没有渲染器、没有场景文件**，不能增删物体、不能换本体、不能改相机（三视角 head/left_wrist/right_wrist 固定，384×512）。它用神经网络生成替代了物理解算 + 渲染，与本库其他三个项目属于不同范式，**选型时勿等价对待**。

**简短总结**
给它一张首帧 + 一条动作轨迹，它生成机器人执行该动作的三视角视频（Cosmos-Predict2-2B DiT + 流匹配，分块自回归 + 稀疏记忆），并**额外解码出 16 维本体感觉状态**、**用内置 World Judge 给出成功概率** —— 后两项是它相对同类世界模型近乎独占的能力。关键设计是 **Pose2Image + Camera Raymap 条件化**：把末端位姿渲染成 3 通道图、把相机光线场编码成 6 通道图，在隐空间与噪声潜变量拼接，从而把 TI2V 底座改造成动作条件模型（腕部相机因视角随臂运动，**必须**靠 raymap 才能对齐）。DMD2 蒸馏到 **4 步采样**，单张 H100 上 **25 帧 / 2.3 秒**。**但开源是"可用的推理发行版"而非"可复现的研究发行版"**：推理模型实现（约 8200 行，占全仓 72%）与蒸馏权重已发布，**训练/蒸馏代码、非蒸馏权重、World Judge 奖励模型、机器人 URDF 全部缺席** —— 直接后果是**开箱即用时 `reward` 与 `progress` 恒为 `None`**，论文主打的"自带可验证奖励"需自行补齐（本机实战用小米 MiMo 做替身评判器）。**传感器侧只有 RGB**：深度 / LiDAR / IMU / 力矩 / 触觉 / 音频 / 分割**全部未提及**，也没有任何显式噪声模型 —— 在此范式下噪声是要抑制的**对手**，不是可配置的特性。

**关键标签**
`世界模型` `视频扩散` `非物理引擎` `VLA闭环` `评测基准` `线上榜单盲测` `双臂操作`

**三个"别踩"提醒**（详见项目内索引与 `background_knowledge.md` §8）
① **别把它当仿真器问"物理上会不会成功"** —— 它只回答"看起来会怎么动"（§2.1 / §8.3）；② **别直接引用宣传数字** —— "100 帧/2.3 秒"实为 25 帧 × 4× 跳帧的**覆盖跨度**（矛盾 1）、"可做 RL"只见于公众号而论文列为**未来工作**（矛盾 2）、"登顶 WorldArena"指活榜且**基准论文正文 grep `GE-Sim` 命中 0**、该基准作者自述其分数与动作规划仅 **r=0.36** 弱相关（矛盾 5）；③ **别忽略两套 16 维布局** —— 世界模型侧是 `[L7臂, L夹爪, R7臂, R夹爪]`，策略侧是 `[L7臂, R7臂, L夹爪, R夹爪]`，用错**不报错只是行为错**（§7.2，最高频静默错误）。另：配置默认把四个加速内核开关全开，**但内核需源码编译，首次部署应全关**（§5.4）。

**实践层摘要**（`ai_knowledge.md` + `troubleshooting.md`，全篇 `[实践]` 级，**不是官方结论**）
本机一次完整复现走了**五个阶段**：环境部署 → Real2Edit2Real 数据生成（46 个衍生场景）→ 世界模型闭环评测 → 离线过滤式 BC + RWR 训练 → RoboColiseum 线上盲测接入。三条最贵的量化结论：① **推理吞吐 0.88 帧/s ≈ 0.055× 实时**（印证 §8.2 矛盾 1）—— 它做不了在线 RL 的数据引擎，只适合离线批量 rollout；② **Stage 3 的 0 % 成功率是假阴性** —— 兜底路径静默吞掉了动作，Stage 5 的 0 才是真实测量；由此产出本项目最贵的教训 `L01`「下结论前先审计管道」，审计四件套是**回退计数 / 动作非退化 / 帧数对账 / 输入侧量纲**；③ **RWR 把过滤式 BC 从 30 % 拉到 80 %**（在世界模型自采数据上），但**判分器是自行补的 MiMo 替身，不是官方 World Judge**，该分数不可外推。另：**排障层 45 条中有 6 条属「不报错的失败」**（`L05`），这是本范式最贵的失败形态。

⭐ **本轮新增的 F 类（`P42`–`P45` / `Q42`–`Q45`）不是程序故障，而是「把外部契约或自己的数字读错了」** —— 照文档写、照计划写就会错：① **RoboColiseum 榜单 `total` 文档写作「求和」，实测口径是算术平均**（`Q42`，跨榜单 `total` 不可比）；② **计划文档里的任务数 / 拆分 / 乃至报告模板预填的「成功率 62.5 %」没有一个可以凭想象填**（`Q43`，⭐ 最值得读的一条 —— 结论是「报告中不存在任何无法溯源到 `results/` 快照的数字」，且**模板里的数字比正文里的更危险**）；③ **`job/<uuid>/result` 返回 500 是自己的错**（要数字自增 id，且 job 列表键是 `items` 不是 `jobs`，`Q44` → `L04`「5xx 先怀疑自己」）；④ **Z 轴泛化曲线画不出来是配置决定的**（`trans_range` 的 Z 上下界都是 `0.0`，46 个 episode 实测 `dz` 全为 0.000 —— 由此产出教训 `L09`「先验证数据分布，再承诺分析维度」，正确姿势是**删掉该维度并显式声明 Z 泛化未覆盖**，而不是硬凑曲线，`Q45`）。

**代码层摘要**（详见 [`code_knowledge.md`](ge_sim_v2/code_knowledge.md)）
描述对象是复现仓库 `GE-Sim-V2-tour`（约 8.8K 行，**零模型代码**）。三个最关键特征：① **它是薄编排层，不是模型工作** —— 模型侧全部来自 **未 checkout 的 `gesim` 子模块**，对上游的实际改动只有**一行**（关掉 `sparge_attention`），其余全是新写的五阶段编排：数据生成 → 闭环评测 → 过滤式 BC/RWR → 线上接入。② **没有统一配置系统，也 `未发现` 任何依赖清单** —— 仓库内**没有 `requirements.txt`/`setup.py`/`environment.yml`**，依赖只能照 §5.2 手装；三个 conda 环境彼此隔离，且**逐 Stage 的代理策略相反**（Stage 1–4 必须 `no_proxy=*`，Stage 5 反过来必须走代理），跨 env 调用靠 `conda run` + 显式 `PYTHONPATH` 拼接。③ **最大风险是"不报错的失败"** —— §7.2 列出 **13 条静默失效路径**，并统计出 **≥5 组「同一常量写两遍」**；其中 `S1`/`S2`（判分器降级与解析失败都返 `0.0` 且不改 `judge_source`）正是 `Q35` 的机制解释，`S3`（手写两份 16 维重排、绕开上游 `wm_state_to_policy_state()`）是 `Q36` 的机制解释。⚠️ **§8.2 记录了一件反常事**：教训 `L06`（常量必须单点定义）**在产出这条教训的同一个仓库里被违反了至少四次** —— 引用该仓库写法前先读 §8.4「被本层推翻或修正的结论」（含"四个内核必须全关"被实测放宽、"Stage 5 一键脚本可出报告"实为 `--tags` 传参 bug）。

**周边生态摘要**（`background_knowledge.md` §9，本轮补全）
- **Real2Edit2Real（R2E2R，§9.2 L1193–1282）**：真实数据的「编辑式」扩增管线（重建 → 编辑 → 重渲染）。⚠️ **两条硬约束**：① **它的底座是 GE-Sim v1，不是 2.0** —— 版本钉定见 §9.2 开头，勿把 2.0 的能力算到它头上；② **`facebook/VGGT-1B` 是 CC-BY-NC-4.0 非商用**，且**微调需 80 GB 显存**（本机 A800 为 40 GB），故本机只做推理/生成。另：三个运行脚本都默认指向一个**不存在的配置文件**，API Key 是占位符且**没有读环境变量的路径**（首跑必踩，见 §8.5 第 16 条）。
- **RoboColiseum 线上评测平台（§9.3 L1283–1387，6 小节）**：⚠️ **两处最容易搞反的事实** —— ① **它的仿真引擎是 GenieSim 3.0**（不是 GE-Sim 2.0；本库 `genie_sim_v3` 项目即其引擎侧知识）；② **选手不上传策略** —— 平台**反向拨号**进选手本地运行的 agent（WS 隧道 + 双层令牌：`CHALLENGE_TOKEN` JWT 会过期，逐 job 的 `JOB_TOKEN` 永不过期）。§9.3.5 列出**六处官方口径漂移**；线路层的二进制分帧（`[uint32 BE len][session_id][msgpack_numpy]`）在平台文档里是 `未提及` 的，只在 `code_knowledge.md` §3.6.1 成文。**仍缺三项**：评分 rubric 细则、是否返回渲染视频、单帧延迟上限（**代码里的 20 s/10 s 是本地 WS 心跳，不是平台阈值**）。

**本机相关资源**（均已 gitignore，仅本地有效）
- 源料：`sources/ge_sim_v2/background.txt`（8 个 URL：论文 / 项目页 / 上游仓库 / WorldArena 论文与榜单 / Real2Edit2Real 仓库与论文 / RoboColiseum）、`GE-Sim_v2_中文介绍.txt`（公众号，`[文章]` 级，**口径与论文冲突**）
- 论文纯文本：`sources/ge_sim_v2/_web/{2605.27491,2602.08971,2512.19402}.txt`（GE-Sim 2.0 / WorldArena / Real2Edit2Real）
- 上游仓库克隆：`sources/ge_sim_v2/GE-Sim-V2/`（142 文件）← **`[CODE]` 级证据在这里核实**；周边 `sources/ge_sim_v2/Real2Edit2Real/`（121 文件）
- 复现原始记录：`sources/ge_sim_v2/GE-Sim-V2-tour-docs.md`（11917 行）＋派生材料 `key_events_summary.md`（`E01`–`E35`）与四份 extract。🔒 **正文 L1–11756 已确认干净，但尾部 L11757–11917 是追加的原始 prompt 日志，含明文口令与 API Key** —— 该尾部内容**从未、也不得**被引用进 `knowledge/**`；另全文含约 300 处主机绝对路径，摘写时必须脱敏（早前一次"全文无凭据"的判断只扫了结构化章节 —— **部分扫描不等于扫描干净**）
- 实战复现仓库：`GE-Sim-V2-tour/` ← 代码层的描述对象

---

## 4. lw_benchhub — LW-BenchHub

- **开发方**：光轮智能（LightwheelAI）
- **background 文档**：[`lw_benchhub/background_knowledge.md`](lw_benchhub/background_knowledge.md)（1478 行，9 章齐备，含 §2.6 传感器仿真 13 小节）
- **ai_knowledge 文档**：[`lw_benchhub/ai_knowledge.md`](lw_benchhub/ai_knowledge.md)（432 行，8 章齐备，`P01`–`P38` / `D01`–`D18` / `L01`–`L08`，`[实践]` 级）
- **troubleshooting 文档**：[`lw_benchhub/troubleshooting.md`](lw_benchhub/troubleshooting.md)（864 行，`Q01`–`Q38` 分 5 组，顶部带**快速症状索引**，`[实践]` 级）
- **code_knowledge 文档**：[`lw_benchhub/code_knowledge.md`](lw_benchhub/code_knowledge.md)（952 行，8 章齐备，对应复现仓库 `lw_benchhub_tour/`，`[CODE]`×72 / `[实践]`×15 / `[推断]`×8）
- ⭐ **quickstart 速查卡**：[`lw_benchhub/quickstart.md`](lw_benchhub/quickstart.md)（403 行，环境准备 / 3 个带预期输出的运行示例 / 改参数 / 9 个常见代码问题 / 一分钟自检清单）——**要动手先读这个**
- **项目内索引**：[`lw_benchhub/00-index.md`](lw_benchhub/00-index.md) ← **先读这个拿行号**

**复现经验摘要**（经验层 + 排障层）
一次跨约 3 周、分四阶段的本机复现：① 装通 5 层技术栈（Isaac Sim 5.1.0 / Isaac Lab 2.3.2 / IsaacLab-Arena 0.1.1 / lw_benchhub 0.1.0 / lerobot 0.5.1）并跑通 VLA 评测 —— **π0.5 路线 0%，换 SmolVLA + DoublePiper 后取得 40%（4/10）**，此路径成为后续全部阶段复用的"黄金路径"；② LLM 驱动场景生成做课程难度分级；③ 策略接入接口梳理；④ scripted cuRobo 管线自动产数据集 —— **未达成**，卡在规划器 EE link 与仿真 TCP link 相差 **0.30 m**。
**最高价值的三条教训**：⚠️ **动手"修复 X"之前先量化"X 是否真的发生"**（本次为一个根本不存在的"物体被推开 0.109 m"修了三轮，是最大的一笔时间浪费）；⚠️ **任何写进配置或计划的键 / 字段 / ID，落笔前必须 grep 到它的定义处或读取处**（此类错误复发 ≥5 次）；⚠️ **成功判定只能信环境返回的信号** —— 管线自报的 `success=True` 会把失败轨迹标成成功、污染数据集。
**四条本次未解决**：`Q34` EE/TCP 0.30 m 偏差（5 种修法逐一被阻断）、`Q31` 同进程多次批量规划触发 cuRobo 内部 shape mismatch、`Q36` 数据集 PNG 导出约 40 分钟（三条优化思路已验证无效）、`Q24` 某 layout 在 boot 阶段无限挂起。

**代码层摘要**（详见 [`code_knowledge.md`](lw_benchhub/code_knowledge.md)）
`lw_benchhub_tour/` 是 **vendored 单体仓库，不是 overlay**：5679 个跟踪文件里 5552 个为上游 vendored 代码，**实际只改过 10 个文件**（另有约 127 个本地原创文件）。由于全部改动随首个提交一次性进入，git 历史无法用于归因，**唯一可靠方法是 `diff -rq` 对上游 clone**（方法论见 §6.1）。三项最具工程价值的发现：① **monkey patch 实测：上游 10 处、本机 11 处**（第 11 个 `patch_xform_prim_view_auto_standardize` 是本地新增；原理层旧标题写的"9 处"已更正，全表带行号见 §3.1）；② 仓库里有**两份 vendored IsaacLab**（1362 vs 1857 文件、973 处差异），被 pip 安装的是 `AutoDataGen/dependencies/IsaacLab/` —— **改错那份不报错也不生效**，判别法见 §7.3；③ **11 条静默失效路径**（§7.2）与 79 文件 326 处硬编码主机路径（§7.1）是"改了没生效"的机制根源。另：`doublepiper_kitchen_pnp/` 是**本地原创**且"双臂"是假的（单臂 IK + 硬编码 `ARM_LATERAL_OFFSET = 0.15`、`rotation_threshold=π` 使姿态被忽略、碰撞体全空）。§8.3 提供 22 行 `Qxx` → 代码机制映射，§8.4 列出 7 条被实测推翻的旧结论。

**简短总结**
Lightwheel 出品的机器人操作 benchmark，本质是**架在 Isaac Lab + IsaacLab-Arena 之上的"薄组合层"**：自身不含仿真器、不含管理器系统、不含 RL 算法，核心机制是把 scene / robot / task / rl 四类 id 经 Gymnasium 注册表做**四路组合**，并对 isaaclab 打 **10 处 monkey patch**（本机复现仓库再加 1 处 = 11 处；原理层旧标题写的"9 处"已更正）**其中一处在给上游已删除的 API 做生命维持 ⇒ 升级 isaaclab 会直接破坏它**。任务库分两族且设计哲学相反：LIBERO 系钉死 USD 资产与坐标（低方差，适合基线），RoboCasa 系按类别采样 + 干扰物（高方差，适合泛化评测）。⚠️ **README 的规模宣称需按实测校准**：任务实为 **272**（非 268）、机器人变体 **28**（非 27）、layout id 可达 **62**（非"100 组合"）、**rsl-rl 只注册不执行**；且 272 个任务里**只有 6 个 RL 配置且全挂在 `LiftObj` 上**。**已知短板**：传感器只做配置层组装、无任何自研模型 —— 9 种相机全部仅输出 RGB，深度 / 激光 / IMU / 触觉 / 6 维力矩 / 关节力矩与**噪声模型**均经 grep 确认缺失（`enable_corruption=True` 是空转的假开关）；资产**运行时联网**从 Lightwheel 云端拉取，离线不可用。

**关键标签**
`物理仿真` `IsaacSim` `IsaacLab` `lerobot生态` `双臂操作` `VLA闭环` `评测基准` `场景生成-LLM驱动` `数据飞轮` `课程学习` `运动规划-cuRobo` `数据采集` `遥操作` `传感器仿真` `容器化部署`

**四个"别踩"提醒**（详见项目内索引末尾）
① 别升级 isaaclab 或 Arena 子模块（Arena 被 pin 在 `c7b70779`，**10 处（本机 11 处）** patch 按该版本写死）；② 别相信 README 数字，也别相信注释（`g1.py:997` 注释写 100Hz 而代码是 200Hz）；③ 别以为 `enable_corruption=True` 就有观测噪声；④ **别在没确认"改的是哪一份 IsaacLab"之前调参**（仓库内有两份，973 处差异，见 `code_knowledge.md` §7.3）。另有 **16 项已验证代码缺陷**（含 `teleop_device` 被硬编码成 `None`、配置键拼错成 `remote_protocal`、`rl_on` 断言形同虚设、**YAML 静默覆盖命令行含 `--device`**）与 **8 条安装部署限制**（含 torch 2.7.0 vs 2.5.1 冲突、`docker/Dockerfile` 当前就会失败、Arena 子模块用 SSH URL）见 `background_knowledge.md` §8.3 / §8.5。

**本机相关资源**（均已 gitignore，仅本地有效）
  - 源料：`sources/lw_benchhub/background.txt`（LightwheelAI 组织 + LW-BenchHub + 平台主页 + IsaacLab-Arena + AutoDataGen）
  - 上游仓库克隆：`sources/lw_benchhub/LW-BenchHub/`、`IsaacLab-Arena/`、`AutoDataGen/` ← **`[CODE]` 级证据在这里核实**
  - 复现原始日志：`sources/lw_benchhub/lw_benchhub_tour.md`（**混合流水日志与已完成文档，不是纯时间序**）
  - 实战复现仓库：`lw_benchhub_tour/`（内含 `lw_benchhub/`、`IsaacLab/`、`IsaacLab-Arena/`、`lerobot/`、`AutoDataGen/` 多个子仓库，以及 stage2/stage4 报告）—— **代码结构已提炼进 `code_knowledge.md`，查代码优先读文档**

---

## 选型对照表（做新任务时先看这张）

| 需求 | 首选 | 理由 |
|---|---|---|
| 标准化任务**评测**、刷榜、要现成任务集 | `genie_sim_v3` | 200+ 任务 / 10 万+ 场景 / RoboColiseum 引擎 |
| 需要 **ROS 2 原生**实时闭环、接真实控制栈 | `genie_sim_v3`（RT Engine 栈） | 10 个 ROS 2 包，话题级接口 |
| **大规模并行 RL**、单卡吞吐优先 | `genesis_world` | `scene.build(n_envs=N)` 一键铺开；`reset(envs_idx=)` 支持只重置已终止的环境。⚠️ **只有 GPU + `n_envs>0` 才吃满并行**（`PARA_LEVEL.ALL`） |
| **软体 / 布料 / 流体**耦合 | `genesis_world`；退而求其次 `genie_sim_v3` 的 Newton-standalone | genesis 有 FEM/MPM/SPH/PBD/SF 五类可耦合求解器 + 三种耦合器；genie_sim 仅该后端支持布料软体，且为实验路径 |
| **可微分仿真**（梯度回传到物理量） | `genesis_world` | 四者中唯一提供 —— `SimOptions(requires_grad=True)` + `scene.backward(loss)`。⚠️ 硬约束 `substeps_local % substeps == 0`，显存随 `substeps_local` 线性增长，很容易 OOM |
| **触觉 / 激光雷达 / IMU 噪声**建模 | `genesis_world` | 四者中唯一有成体系的传感器缺陷层。⚠️ 但**默认全为 `0.0`，必须显式配置**；**相机不在噪声层**（`Camera` 直接派生自 `Sensor`） |
| 已在 **lerobot / IsaacLab** 生态里，想少改代码 | `lw_benchhub` | 直接复用 IsaacLab-Arena + lerobot 数据与策略接口 |
| 想**跳过物理**、只做视觉级泛化与快速衍生 | `ge_sim_v2` | 生成式世界模型，无物理解算；⚠️ 只出 RGB，且**开箱即用无奖励信号**（`reward`/`progress` 恒 `None`） |
| **传感器保真度**要求高（深度/LiDAR/IMU 噪声） | ⚠️ 四者都要先查缺口；相对最好的是 `genesis_world` | **`genesis_world` 有完整的两层缺陷模型**（`delay`/`jitter` + `resolution`/`bias`/`noise`/`random_walk`，IMU 有 3×5 矩阵），**但默认全 `0.0` 且相机无噪声层**；genie_sim_v3 已确认仅 RGB 有噪声模型；**`lw_benchhub` 已确认最弱 —— 只有 RGB，且无任何噪声模型**；**`ge_sim_v2` 已核验：同样只有 RGB**，深度/LiDAR/IMU/力矩/触觉/音频/分割全部未提及，且**范式上就不存在显式噪声模型**（`background_knowledge.md` §2.7.4） |
| **多本体横向对比**（同任务换机器人） | `lw_benchhub` | 28 个机器人变体 × 272 个任务的组合注册表；但**位姿需查 `layout_task_mapping.csv`**（§4.5） |
| **离线 / 内网环境**部署 | ⚠️ 避开 `lw_benchhub` | 场景与物体资产运行时联网从 Lightwheel 云端拉取，无独立下载脚本（§4.10） |

---

## 标签词表（新增项目时请复用，勿造同义词）

- **范式**：`物理仿真` `通用物理引擎` `世界模型` `视频扩散` `非物理引擎`
- **底座 / 生态**：`OpenUSD` `IsaacSim` `IsaacLab` `MuJoCo` `lerobot生态` `ROS2集成` `跨平台GPU`
- **能力**：`VLA闭环` `强化学习训练` `数据采集` `评测基准` `场景生成` `场景生成-LLM驱动` `数据飞轮` `课程学习` `遥操作` `运动规划-cuRobo` `传感器仿真` `触觉仿真` `激光雷达` `Real2Sim` `Real2Sim-3DGS` `大规模并行` `可微分仿真` `软体与流体` `多物理场耦合` `IPC接触` `sim2real` `数字孪生` `线上榜单盲测`
- **渲染**：`Headless渲染` `光线追踪渲染` `GaussianSplat`
- **形态**：`双臂操作` `四足机器人` `人形机器人` `移动操作`
- **工程**：`容器化部署`
