# 项目花名册 · 索引

> 更新日期：2026-08-29 ｜ 上级：[`../00-index.md`](../00-index.md)
>
> 本文件是**选型与定位层**：先在这里确定「查哪个项目」，再进入该项目的 `00-index.md` 定位章节。

---

## 总表

| 项目 slug | 名称 / 上游 | 开发方 | 状态 | background（原理层） | ai_knowledge（经验层） | troubleshooting（排障层） | code_knowledge（代码层） | 项目内索引 |
|---|---|---|---|---|---|---|---|---|
| `genie_sim_v3` | Genie Sim 3.x (`AgibotTech/genie_sim`) | 智元机器人 AgiBot | ✅ 已完成 | [`background_knowledge.md`](genie_sim_v3/background_knowledge.md) | [`ai_knowledge.md`](genie_sim_v3/ai_knowledge.md) | [`troubleshooting.md`](genie_sim_v3/troubleshooting.md) | [`code_knowledge.md`](genie_sim_v3/code_knowledge.md) | [`00-index.md`](genie_sim_v3/00-index.md) |
| `genesis_world` | Genesis World (`Genesis-Embodied-AI/genesis-world`) | Genesis Embodied AI | ⏳ 待编写 | — | — | — | — | — |
| `ge_sim_v2` | GE-Sim-V2 (`AgibotTech/GE-Sim-V2`) | 智元机器人 AgiBot | ⏳ 待编写 | — | — | — | — | — |
| `lw_benchhub` | LW-BenchHub (`LightwheelAI/LW-BenchHub`) | 光轮智能 Lightwheel | 🚧 四层已完成（缺速查层） | [`background_knowledge.md`](lw_benchhub/background_knowledge.md) | [`ai_knowledge.md`](lw_benchhub/ai_knowledge.md) | [`troubleshooting.md`](lw_benchhub/troubleshooting.md) | ⏳ 待编写 | [`00-index.md`](lw_benchhub/00-index.md) |

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
- **background 文档**：[`lw_benchhub/background_knowledge.md`](lw_benchhub/background_knowledge.md)（1459 行，9 章齐备，含 §2.6 传感器仿真 13 小节）
- **ai_knowledge 文档**：[`lw_benchhub/ai_knowledge.md`](lw_benchhub/ai_knowledge.md)（411 行，8 章齐备，`P01`–`P38` / `D01`–`D18` / `L01`–`L08`，`[实践]` 级）
- **troubleshooting 文档**：[`lw_benchhub/troubleshooting.md`](lw_benchhub/troubleshooting.md)（862 行，`Q01`–`Q38` 分 5 组，顶部带**快速症状索引**，`[实践]` 级）
- **code_knowledge 文档**：⏳ 待编写（对应 `lw_benchhub_tour/`）
- **项目内索引**：[`lw_benchhub/00-index.md`](lw_benchhub/00-index.md) ← **先读这个拿行号**

**复现经验摘要**（经验层 + 排障层）
一次跨约 3 周、分四阶段的本机复现：① 装通 5 层技术栈（Isaac Sim 5.1.0 / Isaac Lab 2.3.2 / IsaacLab-Arena 0.1.1 / lw_benchhub 0.1.0 / lerobot 0.5.1）并跑通 VLA 评测 —— **π0.5 路线 0%，换 SmolVLA + DoublePiper 后取得 40%（4/10）**，此路径成为后续全部阶段复用的"黄金路径"；② LLM 驱动场景生成做课程难度分级；③ 策略接入接口梳理；④ scripted cuRobo 管线自动产数据集 —— **未达成**，卡在规划器 EE link 与仿真 TCP link 相差 **0.30 m**。
**最高价值的三条教训**：⚠️ **动手"修复 X"之前先量化"X 是否真的发生"**（本次为一个根本不存在的"物体被推开 0.109 m"修了三轮，是最大的一笔时间浪费）；⚠️ **任何写进配置或计划的键 / 字段 / ID，落笔前必须 grep 到它的定义处或读取处**（此类错误复发 ≥5 次）；⚠️ **成功判定只能信环境返回的信号** —— 管线自报的 `success=True` 会把失败轨迹标成成功、污染数据集。
**四条本次未解决**：`Q34` EE/TCP 0.30 m 偏差（5 种修法逐一被阻断）、`Q31` 同进程多次批量规划触发 cuRobo 内部 shape mismatch、`Q36` 数据集 PNG 导出约 40 分钟（三条优化思路已验证无效）、`Q24` 某 layout 在 boot 阶段无限挂起。

**简短总结**
Lightwheel 出品的机器人操作 benchmark，本质是**架在 Isaac Lab + IsaacLab-Arena 之上的"薄组合层"**：自身不含仿真器、不含管理器系统、不含 RL 算法，核心机制是把 scene / robot / task / rl 四类 id 经 Gymnasium 注册表做**四路组合**，并对 isaaclab 打 **9 处 monkey patch**（其中一处在给上游已删除的 API 做生命维持 ⇒ **升级 isaaclab 会直接破坏它**）。任务库分两族且设计哲学相反：LIBERO 系钉死 USD 资产与坐标（低方差，适合基线），RoboCasa 系按类别采样 + 干扰物（高方差，适合泛化评测）。⚠️ **README 的规模宣称需按实测校准**：任务实为 **272**（非 268）、机器人变体 **28**（非 27）、layout id 可达 **62**（非"100 组合"）、**rsl-rl 只注册不执行**；且 272 个任务里**只有 6 个 RL 配置且全挂在 `LiftObj` 上**。**已知短板**：传感器只做配置层组装、无任何自研模型 —— 9 种相机全部仅输出 RGB，深度 / 激光 / IMU / 触觉 / 6 维力矩 / 关节力矩与**噪声模型**均经 grep 确认缺失（`enable_corruption=True` 是空转的假开关）；资产**运行时联网**从 Lightwheel 云端拉取，离线不可用。

**关键标签**
`物理仿真` `IsaacSim` `IsaacLab` `lerobot生态` `双臂操作` `VLA闭环` `评测基准` `场景生成-LLM驱动` `数据飞轮` `课程学习` `运动规划-cuRobo` `数据采集` `遥操作` `传感器仿真` `容器化部署`

**三个"别踩"提醒**（详见项目内索引末尾）
① 别升级 isaaclab 或 Arena 子模块（Arena 被 pin 在 `c7b70779`，9 处 patch 按该版本写死）；② 别相信 README 数字，也别相信注释（`g1.py:997` 注释写 100Hz 而代码是 200Hz）；③ 别以为 `enable_corruption=True` 就有观测噪声。另有 **15 项已验证代码缺陷**（含 `teleop_device` 被硬编码成 `None`、配置键拼错成 `remote_protocal`、`rl_on` 断言形同虚设）与 **8 条安装部署限制**（含 torch 2.7.0 vs 2.5.1 冲突、`docker/Dockerfile` 当前就会失败、Arena 子模块用 SSH URL）见 `background_knowledge.md` §8.3 / §8.5。

**本机相关资源**（均已 gitignore，仅本地有效）
  - 源料：`sources/lw_benchhub/background.txt`（LightwheelAI 组织 + LW-BenchHub + 平台主页 + IsaacLab-Arena + AutoDataGen）
  - 上游仓库克隆：`sources/lw_benchhub/LW-BenchHub/`、`IsaacLab-Arena/`、`AutoDataGen/` ← **`[CODE]` 级证据在这里核实**
  - 复现原始日志：`sources/lw_benchhub/lw_benchhub_tour.md`（**混合流水日志与已完成文档，不是纯时间序**）
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
| **传感器保真度**要求高（深度/LiDAR/IMU 噪声） | ⚠️ 四者都要先查缺口 | genie_sim_v3 已确认仅 RGB 有噪声模型；**`lw_benchhub` 已确认最弱 —— 只有 RGB，且无任何噪声模型**；其余两者未核验 |
| **多本体横向对比**（同任务换机器人） | `lw_benchhub` | 28 个机器人变体 × 272 个任务的组合注册表；但**位姿需查 `layout_task_mapping.csv`**（§4.5） |
| **离线 / 内网环境**部署 | ⚠️ 避开 `lw_benchhub` | 场景与物体资产运行时联网从 Lightwheel 云端拉取，无独立下载脚本（§4.10） |

---

## 标签词表（新增项目时请复用，勿造同义词）

- **范式**：`物理仿真` `世界模型` `视频扩散` `非物理引擎`
- **底座 / 生态**：`OpenUSD` `IsaacSim` `IsaacLab` `MuJoCo` `lerobot生态` `ROS2集成`
- **能力**：`VLA闭环` `强化学习训练` `数据采集` `评测基准` `场景生成` `场景生成-LLM驱动` `数据飞轮` `课程学习` `遥操作` `运动规划-cuRobo` `传感器仿真` `Real2Sim` `Real2Sim-3DGS` `大规模并行` `软体与流体` `多物理场耦合` `线上榜单盲测`
- **形态**：`双臂操作` `四足机器人` `人形机器人` `移动操作`
- **工程**：`容器化部署` `Headless渲染`
