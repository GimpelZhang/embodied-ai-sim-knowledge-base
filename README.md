# embodied-ai-sim-knowledge-base

![具身智能仿真工具链知识库](images/main.png)

> **一句话定位**：这是一个**给 AI coding agent（尤其是 Claude Code）常驻挂载的参考层**，不是软件项目，也不是一堆随手记的笔记。它把「从零复现一套具身智能仿真工具链」这件事里真正贵的东西——踩过的坑、试错走过的弯路、上游文档不写的静默失效——固化成可被精准检索的结构化知识。

目前收录 **4 个工具链**、**32 篇文档**、约 **19,600 行**，全部来自本人在真机上的实战复现，每条结论都带证据等级标注。

---

## 目录

- [为什么需要这个库](#为什么需要这个库)
- [快速开始](#快速开始)
- [知识架构：两层 × 五层](#知识架构两层--五层)
- [已收录的工具链](#已收录的工具链)
- [全局层：跨项目综合](#全局层跨项目综合)
- [怎么查：按处境路由](#怎么查按处境路由)
- [证据等级约定](#证据等级约定)
- [如何扩展新项目](#如何扩展新项目)
- [维护约定](#维护约定)
- [License](#license)

---

## 为什么需要这个库

复现一套具身智能仿真工具链，真正的成本不在敲命令，而在三件事：

1. **本领域头号失败形态是「静默无效」，不是报错** —— 配置照收、日志照刷、行为不变。四个项目累计记录了 **40+ 条静默失效路径**（YAML 静默覆盖命令行参数、改的是另一份 vendored 副本、常量在两处各写一遍、兜底路径吞掉动作……），这些东西上游文档一个字都不会写。
2. **同一个坑会在不同工具链里反复出现** —— 所以有了 🌐 全局层：把四个项目**独立**得出的同一条教训标上 🔁，收敛度越高越该当纪律遵守。
3. **踩过的坑如果只留在聊天记录里，等于没留** —— 所以每条问题、决策、教训、FAQ 都有**永久稳定的编号**（`Pxx`/`Dxx`/`Lxx`/`Qxx`，只追加不重排），可以被跨文档、跨项目、跨会话稳定引用。

一个具体例子：本库最值得模仿的一次决策是 `genesis_world` 的 `D18`——OpenVLA 抓取闭环在本机 0/8，先把「当前目标不可达」证明到机制层面（末端恒收敛同一点、夹爪输出恒 0.0、换同本体微调模型仍不收敛），再显式征得同意后止损；反面教材是同项目的 `D08`——放宽判定口径掩盖失败，制造了一个假阳性结论。**这类东西才是这个库存在的理由。**

---

## 快速开始

### 给 Claude Code / AI agent 用（主要用法）

```bash
git clone https://github.com/GimpelZhang/embodied-ai-sim-knowledge-base.git
```

把它放在你的工作目录旁边，或直接在其中启动 agent。仓库根目录的 [`CLAUDE.md`](CLAUDE.md) 就是**写给 agent 的检索协议**：它规定了先查哪层、什么时候不许整篇读、缺证据怎么标。agent 读完它就知道怎么用这个库。

检索入口固定为一个文件：

**➡️ [`knowledge/00-index.md`](knowledge/00-index.md)**

### 给人用

按顺序读三个文件即可建立全貌：

1. [`knowledge/00-index.md`](knowledge/00-index.md) — 总索引，判断该查全局层还是某个项目
2. [`knowledge/global/00-index.md`](knowledge/global/00-index.md) — 全局层索引，含全景目录树与思维导图
3. [`knowledge/projects/00-index.md`](knowledge/projects/00-index.md) — 项目花名册，含选型对照与标签

### ⚠️ 一条重要的使用纪律

**不要整篇读 `background_knowledge.md`（可达 1700 行）或 `code_knowledge.md`（可达 1250 行）。** 先在项目级 `00-index.md` 拿到章节行号，再用带 `offset`/`limit` 的读取方式精准取那几十行。行号表是这个库的核心索引设施——它会漂，读到不符时用 `grep -n '^#\{2,3\} '` 重新定位并**顺手修正索引**。

---

## 知识架构：两层 × 五层

```
knowledge/00-index.md                        ← 唯一入口：判断查全局层还是某个项目
    │
    ├─ 🌐 全局层 knowledge/global/            ← 新工具链 / 通用报错 / 选型 / 术语 / 立纪律
    │      ├── common_reproduction_guide.md   通用复现流程（六阶段）
    │      ├── common_issues_solutions.md     问题分类与解法（A–M 十三类）
    │      ├── toolchain_comparison.md        横向对比与选型（含反向选型）
    │      ├── best_practices.md              最佳实践 32 条（🔁 标收敛度）
    │      └── terminology_mapping.md         术语对照表（同名不同义警告）
    │
    └─ 项目层 knowledge/projects/<slug>/      ← 已锁定某个已收录项目
           ├── quickstart.md            【速查层】⭐ 动手前先读：最短路径 + 自检清单
           ├── background_knowledge.md  【原理层】是什么、怎么设计、API 与限制（固定 9 章）
           ├── ai_knowledge.md          【经验层】实战踩坑、决策复盘、可复用教训（固定 8 章）
           ├── troubleshooting.md       【排障层】按报错现象查的 Q&A（带快速症状索引）
           └── code_knowledge.md        【代码层】代码在哪、怎么启动、改哪个文件（固定 8 章）
```

**五层之间的关系，四条要点：**

| 要点 | 说明 |
|---|---|
| **速查层是派生层** | 从其余四层挑出可直接执行的部分，不新增结论。**冲突时以被引用的那一层为准。** |
| **排障层 ↔ 经验层是同一批事实的两个视图** | `Qxx` 与 `Pxx` 一一对应，不必两边都读。**带逐字报错时优先排障层**（可 `Ctrl-F` 原文）。 |
| **代码层是独立视角** | 它描述的是**本机复现仓库 `<project>_tour`**，不是上游本体；并为排障层的现象提供 `[CODE]` 级机制解释。 |
| **全局层不新增事实** | 每条结论都能回指到某项目的 `Pxx`/`Dxx`/`Lxx`/`Qxx`。这条可追溯性是全局层的全部价值所在（现有 207 处带编号引用，已脚本校验 0 处悬空）。 |

**⚠️ 注意版本落差**：原理层描述的可能是比经验层/代码层更新的 release（如 `genesis_world` 原理层核对 v1.3.3、其余四层实测 v1.2.2）。**API 写法不可跨版本套用，能力边界结论可以。** 每个项目的落差表在其经验层与代码层中显式列出。

---

## 已收录的工具链

四个项目**均已五层齐备**。每个都有一个对应的**实战复现仓库**（命名约定 `<project>_tour`），它是代码层的描述对象：

| 项目 | 上游 / 开发方 | 范式定位 | 知识文档 | 🔧 实战复现仓库 |
|---|---|---|---|---|
| **genie_sim_v3** | `AgibotTech/genie_sim` · 智元机器人 | 物理仿真 + **评测平台**（OpenUSD / Isaac Sim 5.1，**三套并存的栈**） | [五层文档](knowledge/projects/genie_sim_v3/00-index.md) · 4,597 行 | [genie_sim_v3_tour](https://github.com/GimpelZhang/genie_sim_v3_tour) |
| **lw_benchhub** | `LightwheelAI/LW-BenchHub` · 光轮智能 | **薄组合层**（叠在 Isaac Lab / IsaacLab-Arena 之上，272 任务 / 28 本体） | [五层文档](knowledge/projects/lw_benchhub/00-index.md) · 4,470 行 | [lw_benchhub_tour](https://github.com/GimpelZhang/lw_benchhub_tour) |
| **genesis_world** | `Genesis-Embodied-AI/genesis-world` | **通用物理引擎**（8 类求解器同场景、3 种可换耦合器、可微仿真） | [五层文档](knowledge/projects/genesis_world/00-index.md) · 3,634 行 | [genesis-world-tour](https://github.com/GimpelZhang/genesis-world-tour) |
| **ge_sim_v2** | `AgibotTech/GE-Sim-V2` · 智元机器人 | ⚠️ **不是物理仿真器** —— 动作条件**视频生成式世界模型** | [五层文档](knowledge/projects/ge_sim_v2/00-index.md) · 4,001 行 | [GE-Sim-V2-tour](https://github.com/GimpelZhang/GE-Sim-V2-tour) |

> ⚠️ **这四个不是同类产品**，选型前务必先读 [`toolchain_comparison.md`](knowledge/global/toolchain_comparison.md) 的开头——把「通用物理引擎」和「视频生成世界模型」放在同一张表里比性能是没有意义的。该文 §5 是**反向选型**：说明什么情况下四个都不合适。

**每个项目最贵的一条结论**（不查文档也该知道）：

- **`genie_sim_v3`** — Isaac Sim 5.1 要求硬件 RT cores（Compute Capability ≥ 7.5），V100 的 7.0 会让渲染器**静默失败**、benchmark 永久挂起；且 CUDA 架构错配会**伪装成显存问题**（极小张量报 OOM）。
- **`lw_benchhub`** — 8 个入口脚本都在 `parse_args()` 之后执行 `args_cli.__dict__.update(yaml_args.__dict__)`，**YAML 静默覆盖命令行参数**（含 `--device`），所以 `--device cuda:0` 实际仍跑 CPU，表现为「莫名奇妙地慢」。要改这类值就改 YAML。
- **`genesis_world`** — 官方宣传的「四层栈」有一半不在 pip 包里（Nyx 在 `genesis/**/*.py` 中 grep 零命中，是独立包）；且**传感器缺陷参数默认全为 `0.0`**——默认即理想真值，相机连噪声字段都没有。
- **`ge_sim_v2`** — 两套 16 维状态布局不同（世界模型侧 `[L臂, L夹爪, R臂, R夹爪]` vs 策略侧 `[L臂, R臂, L夹爪, R夹爪]`），**用错不报错、只是行为错**；且实测吞吐 0.88 帧/s ≈ 0.055× 实时，直接判死「用它做在线 RL 数据引擎」。

---

## 全局层：跨项目综合

📍 索引：[`knowledge/global/00-index.md`](knowledge/global/00-index.md)

| 文档 | 用途 | 适合什么时候读 |
|---|---|---|
| [`common_reproduction_guide.md`](knowledge/global/common_reproduction_guide.md) | 通用复现流程六阶段：准备 / 安装 / 调试 / 调优 / 验收 / 记录 | **要复现的工具链本库还没收录** —— 先读 §0 三条与 §7 一页动作序列 |
| [`common_issues_solutions.md`](knowledge/global/common_issues_solutions.md) | 问题分类与解法库，A–M 十三类，跨项目重复者带 🔁 | 有报错但项目层排障层查不到 |
| [`toolchain_comparison.md`](knowledge/global/toolchain_comparison.md) | 横向对比 + 选型建议 + **反向选型** | 该用哪个工具链 / 这个栈能不能干这件事 |
| [`best_practices.md`](knowledge/global/best_practices.md) | 32 条最佳实践，按主题分类，🔁 标独立收敛度 | 开工前立规矩 / 复盘对照 / 给 agent 写执行协议 |
| [`terminology_mapping.md`](knowledge/global/terminology_mapping.md) | 术语对照表，§9 是**同名不同义**警告表 | 一个词不确定在这个栈里指什么 |

**两条最高价值的跨项目纪律**（来自代价最大的两次教训）：

1. **动手「修复 X」之前，先量化「X 是否真的发生」。** 曾为一个根本不存在的现象修了三轮。**若修复改变了变量而结果分毫不变，说明变量没起作用或问题不存在**——此时应质疑问题本身，而不是提出第 N 个假设。
2. **任何写进配置或计划的键 / 字段 / ID，落笔前必须 grep 到它的定义处或读取处。** 此类错误单个项目内复发 ≥5 次，且失败形态是**静默无效**。

**跑出 0 分或分数不合理时，⛔ 先别改模型**，先跑 [`best_practices.md`](knowledge/global/best_practices.md) §5.3 的**审计四件套**：回退计数 / 动作非退化 / 帧数对账 / 输入侧量纲。本库最贵的一次错判就是把管道故障读成了模型能力。

---

## 怎么查：按处境路由

| 手上有什么 | 去哪 |
|---|---|
| 要动手跑 / 想不起命令怎么敲 | ⭐ 项目层 `quickstart.md` |
| 一条具体报错 / 日志异常 | 项目层 `troubleshooting.md` 顶部「快速症状索引」→ 查不到再去全局层 `common_issues_solutions.md` |
| 要改代码 / 找某个类、函数、参数在哪个文件 | 项目层 `code_knowledge.md` §2 入口点、§3 核心模块、§4 配置系统、§7 硬编码陷阱 |
| 想知道为什么会这样、试过哪些无效方法 | 项目层 `ai_knowledge.md` §4（含「无效尝试」列） |
| 查 API / 参数 / 设计原理 / 能力边界 | 项目层 `background_knowledge.md` |
| 估工作量 / 避免重复踩坑 | 项目层 `ai_knowledge.md` §2 时间线 + §3 决策表 + §6 教训 |
| 🌐 要复现的工具链本库还没收录 | 全局层 `common_reproduction_guide.md` |
| 🌐 「改了没生效」 | 全局层 `common_issues_solutions.md` §I ＋ `best_practices.md` §4 |
| 🌐 想放宽判定口径 / 降低目标 | 全局层 `best_practices.md` §6.2 —— 必须先把「原目标不可达」证明到机制层面并显式征得同意 |

---

## 证据等级约定

**每条结论都带证据标注**，这是本库可信度的基础。做工程决策时只信 `[CODE]`：

| 标注 | 含义 |
|---|---|
| `[CODE]` | 可在上游仓库逐行验证，附相对路径（必要时带行号）—— **工程决策只信这一级** |
| `[PAPER]` / `[README]` | 论文宣称值 / 仓库文档说法 |
| `[官网]` / `[文章]` | 官方博客或发布页的宣称值（**未开源可复现验证脚本**）/ 第三方分析，二手 |
| `[实践]` | 本机踩坑记录，**不是官方结论**（经验层与排障层全篇为此级） |
| `[推断]` | 证据不足以定论（仅代码层使用） |
| `未提及` | 资料中无证据。**不推测、不编造**，且已 grep 确认并收进项目索引的「未提及」清单 |

> 💡 **先查「未提及」清单能省最多时间**：项目级索引集中列出了已确认无证据的方向，命中清单就别再搜了。

---

## 如何扩展新项目

本库的结构是为持续扩展设计的——章号跨项目稳定、编号只追加不重排、索引三处同步，因此**加第 5、第 6 个项目不需要重构任何已有内容**。

### 新增一个项目的完整流程

1. **准备源料** —— 在 `sources/<slug>/` 下放 `background.txt`（URL 清单）并 `git clone` 上游仓库。`[CODE]` 级证据必须在这里核实，**不许猜**。
2. **建目录** —— `knowledge/projects/<slug>/`，slug 用小写下划线。
3. **按顺序写五层**（推荐顺序，后者依赖前者）：
   - `background_knowledge.md` — **固定 9 章**（项目概述 / 核心原理 / 架构与模块 / 关键特性 / 安装与依赖 / 基本使用流程 / 常用 API / 已知问题与限制 / 参考资源）。**章号跨项目稳定是行号表能通用的前提，不要自创章节。**
   - `ai_knowledge.md` — **固定 8 章**，全篇 `[实践]` 级，须在文档头声明「不是官方结论」。
   - `troubleshooting.md` — 由经验层 §4 按**故障类别**重排的 Q&A，顶部必须有「快速症状索引」表。
   - `code_knowledge.md` — **固定 8 章**，描述对象是 `<project>_tour` 复现仓库，文档头必须声明这一点。
   - `quickstart.md` — 最后写，从其余四层提炼，**不新增结论**。
4. **建项目级 `00-index.md`** —— 带行号的章节地图 + 「未提及」清单。行号用脚本核验，**不要靠算**。
5. **三处索引同步** —— `knowledge/00-index.md` 的花名册与路由表、`knowledge/projects/00-index.md` 的总表与项目条目、以及该项目自己的 `00-index.md`。
6. **🌐 回灌全局层**（**必做，清单见 [`knowledge/global/00-index.md`](knowledge/global/00-index.md) §6**）：
   - `toolchain_comparison.md` 加一列 + §4 加一节
   - `common_issues_solutions.md` 的 🔁 重复度**重算**
   - `best_practices.md` §9 溯源表加行 + 🔁 **重算**
   - `terminology_mapping.md` §9 检查是否产生新的**同名不同义**
   - `common_reproduction_guide.md` 仅在出现**新类型的阶段性坑**时才改
   - ⚠️ **🔁 的分母是当前已收录项目数（现为 4）**，加项目时已有标记必须重新核对，**不能只加不改**。
7. **更新根目录 [`CLAUDE.md`](CLAUDE.md) 的检索协议**与本 README 的项目表。

### 编号规则（跨项目一致）

`P`（问题）/ `D`（决策）/ `L`（教训）/ `Q`（FAQ）/ `E`（事件）—— **只追加、不重排、不复用**，外部交叉引用依赖此约定。每个项目独立编号，引用时带项目名消歧。

---

## 维护约定

| 约定 | 说明 |
|---|---|
| **禁密钥、禁绝对路径** | 不得出现账号、密码、密钥、access token。示例中的本地路径写 `<your_path>` / `<user_home>` / `<path>`，主机地址写 `<INFER_IP>:<PORT>`，复现仓库根写 `<repo_root>`。 |
| **缺证据就标 `未提及`** | 不推测、不编造，同时补进项目索引的「未提及」清单。 |
| **双向交叉引用** | 新增经验层/排障层后必须回头在 `background_knowledge.md` 加指回链接；原理层的建议若被实践推翻，要**就地标注冲突**并说明以哪层为准。 |
| **分批写入** | 单篇文档每次写 100–200 行，用哨兵注释追加，避免超长写入失败。 |
| **只有 `knowledge/**` 与根目录文件入库** | `sources/`（原始资料与上游克隆）与 `*_tour/`（各自是独立仓库）已 gitignore，**索引中引用它们的路径仅在本机有效**。 |

---

## License

[Apache License 2.0](LICENSE)

本库为个人实战复现记录的整理，所述各上游工具链的著作权归其各自作者所有，许可证以其仓库声明为准。文中 `[实践]` 级内容是本机环境下的观测结果，**不构成任何官方结论**。
