# 项目花名册 · 索引

> 更新日期：2026-08-29 ｜ 上级：[`../00-index.md`](../00-index.md)
>
> 本文件是**选型与定位层**：先在这里确定「查哪个项目」，再进入该项目的 `00-index.md` 定位章节。

---

## 总表

| 项目 slug | 名称 / 上游 | 开发方 | 状态 | background 文档 | 项目内索引 |
|---|---|---|---|---|---|
| `genie_sim_v3` | Genie Sim 3.x (`AgibotTech/genie_sim`) | 智元机器人 AgiBot | ✅ 已完成 | [`genie_sim_v3/background_knowledge.md`](genie_sim_v3/background_knowledge.md) | [`genie_sim_v3/00-index.md`](genie_sim_v3/00-index.md) |
| `genesis_world` | Genesis World (`Genesis-Embodied-AI/genesis-world`) | Genesis Embodied AI | ⏳ 待编写 | — | — |
| `ge_sim_v2` | GE-Sim-V2 (`AgibotTech/GE-Sim-V2`) | 智元机器人 AgiBot | ⏳ 待编写 | — | — |
| `lw_benchhub` | LW-BenchHub (`LightwheelAI/LW-BenchHub`) | 光轮智能 Lightwheel | ⏳ 待编写 | — | — |

---

## 1. genie_sim_v3 — Genie Sim 3.x

- **开发方**：智元机器人（AgiBot / AgibotTech）
- **版本**：v3.2.0（发布 2026-06-25），许可证 MPL-2.0
- **background 文档**：[`genie_sim_v3/background_knowledge.md`](genie_sim_v3/background_knowledge.md)（1657 行，9 章齐备）
- **项目内索引**：[`genie_sim_v3/00-index.md`](genie_sim_v3/00-index.md) ← **先读这个拿行号**

**简短总结**
以 OpenUSD 为唯一真值源、构建在 Isaac Sim 5.1 之上的具身智能仿真与**评测**平台。最反直觉的一点是它不是单一仿真器，而是**三套共存的栈**：RT Engine（ROS 2 原生实时闭环）、Benchmark/Data-collection（直连 Isaac Sim，跑评测与采集）、RLinf（CPU MuJoCo 多进程，跑 RL 训练）——三者的物理、渲染、传感器通路完全不同，排障时不可混谈。物理侧三后端可切换（PhysX 默认 / Isaac Newton 实验仅刚体 / Newton-standalone 唯一支持布料软体）。真正的护城河是评测体系：200+ 任务、10 万+ 场景、5140 资产、10000+ 小时合成数据，并作为 RoboColiseum 竞赛引擎。**已知短板**：传感器仅 RGB 有噪声模型，深度/IMU/LiDAR 全为几何真值，是 sim2real 的明确缺口。

**关键标签**
`物理仿真` `OpenUSD` `IsaacSim` `ROS2集成` `评测基准` `数据采集` `VLA闭环` `传感器仿真` `强化学习训练` `Real2Sim-3DGS` `遥操作` `容器化部署` `Headless渲染` `运动规划-cuRobo`

**本机相关资源**（均已 gitignore，仅本地有效）
- 源料清单：`sources/genie_sim_v3/background.txt`（上游仓库 + arXiv:2601.02078 + 官方文档站）
- 上游仓库克隆：`sources/genie_sim_v3/genie_sim/`
- 实战复现仓库：`genie_sim_v3_tour/`（Stage 1 容器化闭环 / Stage 2 LLM 场景生成 / Stage 3 3DGS 实采重建导入）

---

## 2. genesis_world — Genesis World

- **开发方**：Genesis Embodied AI
- **background 文档**：⏳ 未编写
- **简短总结（来自源料与实战仓库，尚未经 `[CODE]` 级核验）**
  新一代 Python 原生物理仿真平台，卖点是**单卡即可大规模并行**与**多物理场耦合**。本机实战覆盖四个方向：OpenVLA 端到端闭环控制（Franka Panda）、配置驱动的场景程序化生成与批量鲁棒性压测、单卡大规模并发 PPO 强化学习（Unitree Go2 步态）、刚柔/刚流耦合的"无穿透"交互（布料折叠、海绵挤压、含水玻璃杯倒地）。
- **关键标签**
  `物理仿真` `大规模并行` `强化学习训练` `软体与流体` `多物理场耦合` `场景生成` `VLA闭环` `四足机器人` `Headless渲染`
- **本机相关资源**
  - 源料：`sources/genesis_world/background.txt`（上游仓库 + readthedocs 用户指南 + 官方 blog）、`Genesis_world_01.txt`、`Genesis_world_02.txt`
  - 实战复现仓库：`genesis-world-tour/`（含 `CLAUDE.md`、stage3/stage4 产物）

---

## 3. ge_sim_v2 — GE-Sim-V2

- **开发方**：智元机器人（AgibotTech）
- **background 文档**：⏳ 未编写
- **⚠️ 定位提醒**：**这不是传统物理仿真器**，而是**视频扩散生成式世界模型（Neural World Model）**。它没有物理引擎、不解算接触力，"仿真"是由模型直接生成下一帧观测。与本库其他三个项目属于不同范式，选型时勿等价对待。
- **简短总结（来自源料与实战仓库，尚未经 `[CODE]` 级核验）**
  以视频扩散世界模型承载 VLA 闭环评测；配合 Real2Edit2Real 的 3D 场景编辑管线做场景衍生与空间泛化评测，可在世界模型内部做 RL 自我进化，并对接 world-arena / RoboColiseum 线上盲测榜单。本机实战覆盖五阶段：单场景闭环（GE-Sim 2.0 + π₀.₅ + MiMo World Judge）、批量数据衍生、大规模空间泛化评测、世界模型内 RL、第三方线上盲测。
- **关键标签**
  `世界模型` `视频扩散` `VLA闭环` `评测基准` `场景编辑生成` `Real2Sim` `强化学习训练` `线上榜单盲测` `非物理引擎`
- **本机相关资源**
  - 源料：`sources/ge_sim_v2/background.txt`（4 篇 arXiv + 项目主页 + 上游仓库 + Real2Edit2Real + world-arena + robocoliseum）、`GE-Sim_v2_中文介绍.txt`
  - 实战复现仓库：`GE-Sim-V2-tour/`

---

## 4. lw_benchhub — LW-BenchHub

- **开发方**：光轮智能（LightwheelAI）
- **background 文档**：⏳ 未编写
- **简短总结（来自源料与实战仓库，尚未经 `[CODE]` 级核验）**
  光轮的统一物理底座，深度集成 NVIDIA **IsaacLab-Arena** 机器人学习框架与 Hugging Face **lerobot** 生态，配套 `AutoDataGen` 数据生成工具。实战路径为双臂 Piper（`DoublePiper-Abs`）在厨房 PnP 任务下的闭环评测基线 → LLM 驱动场景自适应裂变（cuRobo 工作空间 IK 作物理可达性闸门过滤）→ 失败自动诊断 + 课程学习 + VLA 自过滤的数据飞轮。
- **关键标签**
  `物理仿真` `IsaacSim` `IsaacLab` `lerobot生态` `双臂操作` `VLA闭环` `评测基准` `场景生成-LLM驱动` `数据飞轮` `课程学习` `运动规划-cuRobo` `数据采集`
- **本机相关资源**
  - 源料：`sources/lw_benchhub/background.txt`（LightwheelAI 组织 + LW-BenchHub + 平台主页 + IsaacLab-Arena + AutoDataGen）
  - 实战复现仓库：`lw_benchhub_tour/`（内含 `lw_benchhub/`、`IsaacLab/`、`IsaacLab-Arena/`、`lerobot/`、`AutoDataGen/` 多个子仓库，以及 stage2/stage4 报告）

---

## 选型对照表（做新任务时先看这张）

| 需求 | 首选 | 理由 |
|---|---|---|
| 标准化任务**评测**、刷榜、要现成任务集 | `genie_sim_v3` | 200+ 任务 / 10 万+ 场景 / RoboColiseum 引擎 |
| 需要 **ROS 2 原生**实时闭环、接真实控制栈 | `genie_sim_v3`（RT Engine 栈） | 10 个 ROS 2 包，话题级接口 |
| **大规模并行 RL**、单卡吞吐优先 | `genesis_world` | 单卡大规模并发是其核心卖点 |
| **软体 / 布料 / 流体**耦合 | `genesis_world`；退而求其次 `genie_sim_v3` 的 Newton-standalone | genie_sim 仅该后端支持布料软体，且为实验路径 |
| 已在 **lerobot / IsaacLab** 生态里，想少改代码 | `lw_benchhub` | 直接复用 IsaacLab-Arena + lerobot 数据与策略接口 |
| 想**跳过物理**、只做视觉级泛化与快速衍生 | `ge_sim_v2` | 生成式世界模型，无物理解算 |
| **传感器保真度**要求高（深度/LiDAR/IMU 噪声） | ⚠️ 四者都要先查缺口 | genie_sim_v3 已确认仅 RGB 有噪声模型；其余三者未核验 |

---

## 标签词表（新增项目时请复用，勿造同义词）

- **范式**：`物理仿真` `世界模型` `视频扩散` `非物理引擎`
- **底座 / 生态**：`OpenUSD` `IsaacSim` `IsaacLab` `MuJoCo` `lerobot生态` `ROS2集成`
- **能力**：`VLA闭环` `强化学习训练` `数据采集` `评测基准` `场景生成` `场景生成-LLM驱动` `数据飞轮` `课程学习` `遥操作` `运动规划-cuRobo` `传感器仿真` `Real2Sim` `Real2Sim-3DGS` `大规模并行` `软体与流体` `多物理场耦合` `线上榜单盲测`
- **形态**：`双臂操作` `四足机器人` `人形机器人` `移动操作`
- **工程**：`容器化部署` `Headless渲染`
