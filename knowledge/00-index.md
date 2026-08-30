# 具身智能仿真工具链知识库 · 总索引

> 更新日期：2026-08-30
> 本知识库用途：作为 **Claude Code 的常驻参考层**，服务两类任务——
> 1. **复现**：从零部署某个具身智能仿真工具链（装环境、跑通闭环、排障）
> 2. **使用**：在已复现的工具链上完成新的仿真测试任务（评测、采数、场景生成、RL 训练）
>
> 知识分两层：**[全局层 `knowledge/global/`](global/00-index.md)** 是跨项目综合（通用流程 / 问题分类 / 选型 / 最佳实践 / 术语），**项目层 `knowledge/projects/<项目>/`** 是单项目五层文档。**有对应项目就直接进项目层；面对本库还没有的新工具链，全局层是唯一入口。**

---

## 全局层速览（跨项目，不针对某一个工具链）

入口：[`global/00-index.md`](global/00-index.md)。五篇共 2211 行，是四个项目五层文档（约 12 000 行）的横向提炼。**它是派生层，不新增事实；与项目层冲突时以被引用的那一层为准。**

| 文档 | 行数 | 什么时候读它 |
|---|---|---|
| ⭐⭐ [`common_reproduction_guide.md`](global/common_reproduction_guide.md) | 539 | **要复现一个本库还没有的新工具链** —— 准备 / 安装 / 运行调试 / 调优 / 验收 / 记录六阶段；先读 §0 三条 + §7 一页动作序列 |
| ⭐⭐ [`common_issues_solutions.md`](global/common_issues_solutions.md) | 759 | **有报错但项目层症状索引查不到** —— A–M 共 13 类；先读 §N 定位顺序。⚠️ 两节最高价值：**§I 改了没生效**、**§J 假阳性与假阴性** |
| ⭐ [`toolchain_comparison.md`](global/toolchain_comparison.md) | 282 | **选型 / 判断某个栈能不能干这件事** —— 必先读开头「⚠️ 这 4 个不是同类产品」；§5 是**反向选型**（这 4 个都不合适的情况） |
| ⭐ [`best_practices.md`](global/best_practices.md) | 390 | **开工前立规矩 / 复盘对照 / 给 Agent 写执行协议** —— 32 条教训按 8 主题重组，🔁 标记表示有几个项目**独立**得出同一条 |
| [`terminology_mapping.md`](global/terminology_mapping.md) | 241 | **词义不确定**，尤其时间频率与关节控制 —— §0 九组易混概念、§9 同名不同义警告表 |

**三条最高频的全局层用法：**

1. **「跑出 0 分 / 成功率不合理」⛔ 先别改模型** → [`best_practices.md` §5.3 审计四件套](global/best_practices.md)（回退计数 / 动作非退化 / 帧数对账 / 输入侧量纲）。本库最贵的一次错判就是把管道故障读成了模型能力。
2. **「我改了代码或配置，但完全没生效」** → [`common_issues_solutions.md` §I](global/common_issues_solutions.md) + [`best_practices.md` §4](global/best_practices.md)。这是本领域头号失败形态：**静默无效**，不报错。
3. **「想降低目标 / 放宽判定口径」** → [`best_practices.md` §6.2](global/best_practices.md)：必须先把「原目标不可达」证明到机制层面并显式征得同意。反面教材是放宽口径制造假阳性。

---

## 给 Claude Code 的使用约定（先读这一节）

**检索顺序（逐层收窄，不要一上来就读正文）：**

```
knowledge/00-index.md            ← 你在这里。判断「查全局层还是某个项目」
        │
        ├── 新工具链 / 通用问题 / 选型 / 术语
        │       ↓
        │   knowledge/global/00-index.md      ← 全局层索引（5 篇跨项目文档 + 行号表）
        │
        └── 已锁定某个已收录项目
                ↓
            knowledge/projects/00-index.md   ← 项目花名册 + 标签 + 选型对照表
                ↓
            knowledge/projects/<项目>/00-index.md   ← 章节地图，定位到具体小节
                ↓
                ├── quickstart.md             ← 【速查层】⭐ 要动手就先读这个：最短路径 + 自检清单
                ├── background_knowledge.md   ← 【原理层】是什么、怎么设计、API 与限制
                ├── ai_knowledge.md           ← 【经验层】实战踩坑、决策复盘、可复用教训
                ├── troubleshooting.md        ← 【排障层】按报错现象查的 Q&A（带报错时最快路径）
                └── code_knowledge.md         ← 【代码层】代码在哪、怎么启动、改哪个文件、硬编码陷阱
                      后四者都只读需要的那几十行；quickstart 可整篇读（约 385 行）
```

**先选对文档层次**（这一步选错会浪费很多时间）：

| 我的问题是 | 查哪层 |
|---|---|
| **我要复现的工具链本库还没收录** | 🌐 **全局层** [`global/common_reproduction_guide.md`](global/common_reproduction_guide.md) —— 六阶段通用流程；配合 [`best_practices.md`](global/best_practices.md) 立纪律、[`common_issues_solutions.md`](global/common_issues_solutions.md) 预判坑的形状 |
| **我手上有一条具体报错 / 日志异常，现在怎么办？** | **排障层** `troubleshooting.md` —— 直接看顶部「快速症状索引」，按现象查到 `Qxx`。**带报错时这是最快路径，优先于经验层。** 查不到再回 🌐 [`global/common_issues_solutions.md`](global/common_issues_solutions.md) 按类别定位 |
| **我要动代码 / 要跑起来 / 找某个类或参数在哪个文件？** | **代码层** `code_knowledge.md` —— §2 入口点与完整命令、§3 核心模块、§4 配置系统、§7 硬编码陷阱 |
| 这个报错**为什么**会这样？当时试过哪些无效方法？ | **经验层** `ai_knowledge.md` §4（问题表含"无效尝试"列，可直接排除错误路径） |
| 这个仿真器怎么设计的？有什么 API / 配置项 / 能力边界？ | **原理层** `background_knowledge.md` |
| 复现这东西大概要多久、会踩几个坑、哪些决策容易做错？ | **经验层** §2 时间线 + §3 决策表 + §6 教训；跨项目汇总见 🌐 [`global/best_practices.md`](global/best_practices.md) |
| **该用哪个工具链？这个栈能不能干这件事？** | 🌐 **全局层** [`global/toolchain_comparison.md`](global/toolchain_comparison.md) —— 对比矩阵 + 选型建议 + 适用边界 + **反向选型**；细节再回项目层原理层 §4/§8 |
| **这个词在这个工具链里到底指什么？** | 🌐 **全局层** [`global/terminology_mapping.md`](global/terminology_mapping.md) —— §0 九组易混、§9 同名不同义 |

> 排障层与经验层是**同一批事实的两个视图**（`Qxx` ↔ `Pxx` 一一对应），不是互相补充 —— 不必两边都读。
> **代码层是独立视角**：它描述**具体某个复现仓库的代码实体**（不是上游本体），并为排障层的现象提供 `[CODE]` 级机制解释。四层的关联映射见各项目 `code_knowledge.md` §8。

**硬性规则：**

| 规则 | 说明 |
|---|---|
| 按需读取 | `background_knowledge.md` 单文件可达 1600+ 行。**永远先读该项目的 `00-index.md` 拿到行号，再用 `Read` 的 `offset`/`limit` 精准读取**，不要整篇载入。 |
| 认证据等级 | 正文每条结论带 `[CODE]` / `[PAPER]` / `[README]` / `[官网]` / `[文章]` / `[实践]` / `[推断]` 标注。**做工程决策只信 `[CODE]`**（可在上游仓库当场验证）；`[PAPER]` / `[官网]` 是论文或官方博客的宣称值，`[README]` 来自仓库文档，`[文章]` 是第三方分析（二手），`[实践]` 是本地踩坑记录、不等于官方结论；`[推断]` 表示证据不足以定论（代码层与 genesis_world 原理层使用）。<br>⚠️ `[官网]` / `[文章]` 两级由 `genesis_world` 引入 —— 该项目源料含大量**无法复现的官方性能宣称**（如 103× / 4.6× / Pearson 0.8996），已在 `background_knowledge.md` §8.3 集中隔离。 |
| 不补空白 | 标注 `未提及` 的地方表示三方资料均无证据。**不要据此推测**，需要就去读上游仓库源码，读到后回写本库。 |
| 无密钥无绝对路径 | 本库所有文档禁止出现账号、密码、密钥、access token；示例中的本地路径统一写作 `<your_path>`、主机地址写作 `<INFER_IP>:<PORT>`。**新增内容时沿用此约定。** |
| 行号会漂 | 索引里的行号是编写时快照。若 `Read` 到的内容与索引描述不符，用 `grep -n '^## '` 重新定位并**顺手更新索引**。 |
| 分批写入 | 新建或大改 `background_knowledge.md` 时，每次写入约 100–200 行，避免单次超长写入失败。 |

---

## 目录结构与命名约定

```
simulation-knowledge/
├── knowledge/                       ← ✅ 唯一纳入 git 跟踪的知识层
│   ├── 00-index.md                  ← 总索引（本文件）
│   ├── global/                      ← 🌐 全局层：跨项目综合，不针对某一个工具链
│   │   ├── 00-index.md              ← 全局层索引（含五篇的行号表 + 思维导图）
│   │   ├── common_reproduction_guide.md   ← 通用复现流程（六阶段）
│   │   ├── common_issues_solutions.md     ← 问题分类与解决方案库（A–M）
│   │   ├── toolchain_comparison.md        ← 横向对比与选型指南
│   │   ├── best_practices.md              ← 最佳实践 32 条（按主题）
│   │   └── terminology_mapping.md         ← 跨工具链术语对照表
│   └── projects/
│       ├── 00-index.md              ← 项目花名册
│       └── <project_slug>/
│           ├── 00-index.md          ← 项目内章节地图（五篇文档都在这里定位行号）
│           ├── quickstart.md             ← 速查层（派生自其余四层，不含新事实）
│           ├── background_knowledge.md   ← 原理层主文档（固定 9 章结构）
│           ├── ai_knowledge.md           ← 经验层文档（复现实战复盘，可选）
│           ├── troubleshooting.md        ← 排障层文档（由经验层 §4 改写为 Q&A，可选）
│           └── code_knowledge.md         ← 代码层文档（对应 <project>_tour 复现仓库，可选）
├── sources/                         ← ⚠️ 已 gitignore，仅本地存在
│   └── <project_slug>/
│       ├── background.txt           ← 该项目的源料 URL 清单
│       ├── *.md / *.txt             ← 抓取或导出的原始资料
│       └── <upstream_repo>/         ← git clone 下来的上游仓库
└── <project>_tour/                  ← ⚠️ 已 gitignore，本人的实战复现仓库
```

**约定：**
- `00-index.md` 前缀 `00-` 保证在任何目录列表中排最前，便于第一眼命中。
- 项目 slug 与 `sources/` 下的目录名保持一致，便于双向跳转。
- `background_knowledge.md` 必须固定为 9 章：项目概述 / 核心原理 / 架构与模块 / 关键特性 / 安装与依赖 / 基本使用流程 / 常用 API 接口 / 已知问题与限制 / 参考资源。章号稳定 ⇒ 跨项目可用同一套定位习惯。
- **`global/` 是派生层，不新增事实**：每条结论必须能回指到某个项目的 `Pxx`/`Dxx`/`Lxx`/`Qxx` 或原理层章节。**新增项目后必须回灌全局层**（对比表加列、🔁 重复度重算、教训溯源表加行），清单见 [`global/00-index.md`](global/00-index.md) §6。
- `sources/` 与 `*_tour/` 不入库，**索引里引用它们的路径仅在本机有效**；换机器需重新 clone。

---

## 项目花名册（速览）

详表见 [`projects/00-index.md`](projects/00-index.md)。

| 项目 | 定位一句话 | 速查层 | 原理层文档 | 经验层文档 | 排障层文档 | 代码层文档 |
|---|---|---|---|---|---|---|
| **genie_sim_v3** | 智元 Genie Sim 3.x，OpenUSD + Isaac Sim 的评测/采集/RL 三栈仿真平台 | ⭐ [速查卡](projects/genie_sim_v3/quickstart.md) | ✅ [已完成](projects/genie_sim_v3/background_knowledge.md) | ✅ [已完成](projects/genie_sim_v3/ai_knowledge.md) | ✅ [Q01–Q29](projects/genie_sim_v3/troubleshooting.md) | ✅ [已完成](projects/genie_sim_v3/code_knowledge.md) |
| **genesis_world** | Genesis World 通用物理平台，8 类求解器 + 3 种可换耦合器，单卡大规模并行、可微仿真、传感器缺陷建模 | ⭐ [速查卡](projects/genesis_world/quickstart.md) | ✅ [已完成](projects/genesis_world/background_knowledge.md)（v1.3.3） | ✅ [已完成](projects/genesis_world/ai_knowledge.md)（v1.2.2） | ✅ [Q01–Q37](projects/genesis_world/troubleshooting.md) | ✅ [已完成](projects/genesis_world/code_knowledge.md)（v1.2.2） |
| **ge_sim_v2** | 智元 GE-Sim-V2，**动作条件视频生成式世界模型**（⚠️ 非物理仿真：无引擎、无渲染器、无场景文件，只出 RGB） | ⭐ [速查卡](projects/ge_sim_v2/quickstart.md) | ✅ [已完成](projects/ge_sim_v2/background_knowledge.md)（论文 v1 / 权重 v2.0.1） | ✅ [已完成](projects/ge_sim_v2/ai_knowledge.md) | ✅ [Q01–Q45](projects/ge_sim_v2/troubleshooting.md) | ✅ [已完成](projects/ge_sim_v2/code_knowledge.md) |
| **lw_benchhub** | 光轮 LW-BenchHub，架在 Isaac Lab + IsaacLab-Arena 之上的**薄组合层**操作 benchmark | ⭐ [速查卡](projects/lw_benchhub/quickstart.md) | ✅ [已完成](projects/lw_benchhub/background_knowledge.md) | ✅ [已完成](projects/lw_benchhub/ai_knowledge.md) | ✅ [Q01–Q38](projects/lw_benchhub/troubleshooting.md) | ✅ [已完成](projects/lw_benchhub/code_knowledge.md) |

---

## 常见任务 → 去哪查

| 我要做的事 | 建议路径 |
|---|---|
| 🌐 **复现一个本库还没收录的新工具链** | ⭐⭐ [`global/common_reproduction_guide.md`](global/common_reproduction_guide.md) §0 三条 + §7 一页动作序列 → 再按阶段读 §1–§6。开跑前先过 [`global/best_practices.md`](global/best_practices.md) §0「如果只记 5 条」 |
| 🌐 **报错在项目层症状索引里查不到** | [`global/common_issues_solutions.md`](global/common_issues_solutions.md) §N 定位顺序 → A–M 十三类。⚠️ 四类被标记 **🔁 4/4**（四个项目全都撞过）：F 源码契约漂移、H 进程稳定性、**I 改了没生效**、**J 假阳性/假阴性** |
| 🌐 **跑出 0 分 / 分数不合理，想改模型或超参** | ⛔ **先别改** → [`global/best_practices.md`](global/best_practices.md) §5.3 **审计四件套**（回退计数 / 动作非退化 / 帧数对账 / 输入侧量纲）。本库最贵的一次错判是把管道故障读成了模型能力 |
| 🌐 **想放宽判定口径 / 降低目标** | [`global/best_practices.md`](global/best_practices.md) §6.2 —— 必须先把「原目标不可达」证明到机制层面并显式征得同意；反面教材是放宽口径制造假阳性 |
| 🌐 **一个词不确定在这个栈里指什么** | [`global/terminology_mapping.md`](global/terminology_mapping.md) §0 九组易混（物理步长秒 vs Hz、`substeps` vs `decimation`、`set_` vs `control_dofs_position`…）+ §9 同名不同义警告表 |
| **手上有一条报错，先判断是不是已知坑** | ⭐ **`troubleshooting.md` 顶部「快速症状索引」** —— 按现象直接查到 `Qxx`（genie_sim_v3 有 **29** 条；lw_benchhub 有 **38** 条；**genesis_world 有 37 条，分 A–H 八类**；**ge_sim_v2 有 45 条，分 A–F 六类**（F 类是「契约与口径」误解，不是程序崩溃）。索引栏写的都是**逐字报错原文**，可直接 `Ctrl-F`） |
| **把某个已复现的工具链跑起来（完整命令）** | ⭐⭐ **先看 `quickstart.md`**（**四个项目均已具备**）—— 最短路径 + 自检清单；不够细再进 **`code_knowledge.md` §2「入口点与运行方式」**（容器启动、逐条 `docker exec`、环境变量总表）。**genesis_world 的入口总表列出 14 个脚本及其「必须的工作目录」——走错目录会找不到相对路径产物** |
| **改代码 / 加新任务 / 改配置项** | ⭐ **`code_knowledge.md` §3 核心模块 + §4 配置系统**（含"注册新任务必改的 6 处"） |
| **换机器或换显卡前的兼容性检查** | **`code_knowledge.md` §7.5 平台假设 + §5.5 版本约束** —— 编译期写死的 GPU 架构是最常见的坑。**lw_benchhub 额外必看 §7.1** —— 硬编码主机绝对路径散布 79 文件 326 处；**genesis_world 见 §7.1（12 文件 49 行）+ §7.3**，其中 `HF_HOME` 是在 `import torch` 之前 `os.environ[...] = ...` **硬写死**的，在 shell 里 export 无效 |
| **"我改了代码 / 配置，但完全没生效"** | ⭐ **`code_knowledge.md` §7「代码中的注意事项」** —— 这类失败的共同形态是**静默无效**（配置照收、日志照打、行为不变）。lw_benchhub 有 **11 条已知静默失效路径**（§7.2），且仓库内**存在两份 vendored IsaacLab**，改错那份不报错也不生效（§7.3 给了判别法）；**genesis_world 见 §7.2（16 行）—— 头号坑是 `train_subprocess.py` 自带一份超参副本，改 `go2_train.py` 完全无效**；**ge_sim_v2 见 §7.2（13 条）+ §8.5 —— 该仓库有 ≥5 组「同一常量写两遍」，改一处另一处照旧生效** |
| 装某个仿真器 / 排装机报错 | `troubleshooting.md` §一~§三 → 详因见 `ai_knowledge.md` §4（含无效尝试）→ 再看 `background_knowledge.md` 第 5 章（安装与依赖）+ 第 8 章（已知问题） |
| **进程像在跑但没有产出** | `troubleshooting.md` §五「看起来在跑类假象」→ 教训 `L2`（独立存活判据） |
| **CUDA 报错 / 显存数字不合理** | `troubleshooting.md` §四（`Q12`–`Q13`）→ `ai_knowledge.md` `P08` + `L1` —— 优先怀疑 compute capability 架构不匹配，而非显存容量 |
| **某个问题至今没解决？** | `troubleshooting.md` §九「未解决 / 仅部分解决」—— 避免在已知死路上重复投入。genesis_world 的三条明确未解见 `Q13` / `Q32` / `Q37` |
| **在 Genesis 上跑 VLA 抓取闭环，值不值得做** | ⚠️ 先读 `genesis_world/ai_knowledge.md` §4.4（`P07`–`P14`）与 §3.1 —— 本机一次完整尝试的结果是 **0/8**，并已把"当前目标不可达"证明到机制层面（`D18`）。**别重跑这条路，除非换掉根因层级**（`L07`） |
| **在 Genesis 上做四足 / 轮足 RL 训练** | ✅ 有完整成功记录：`genesis_world/quickstart.md` §2.3（可直接照抄的 5 阶段编排命令）+ `ai_knowledge.md` §4.5（`P19`–`P23`）+ 排障层 E 类（`Q19`–`Q23`）+ 代码层 §3.4（checkpoint 契约）。⚠️ 两个头号坑：**rsl-rl 的 checkpoint 编号是 0-based**（`learn(50)` 只产出 `model_49.pt`）、**`--max_iterations` 是绝对目标迭代数而非增量** |
| **在 Genesis 上做软体 / 布料 / 流体耦合** | `genesis_world/troubleshooting.md` G 类（`Q27`–`Q34`）—— ⚠️ **IPC 耦合器在本机不可达**（`Q26`），**无 IPC 时 FEM 完全不做刚-柔接触**（`Q33`），本机唯一可用的体积柔性体路径是 `PBD.Elastic` |
| **要把 Isaac Sim 的资产 / 代码迁到 Genesis** | `genesis_world/troubleshooting.md` **H 类 + 10 条迁移检查清单**（`Q35` `Q36`）—— 链接名、关节名一律不可照抄，须先 grep 到定义处（`L05`） |
| 跑一次 VLA 闭环评测 | 第 6 章（基本使用流程）→ 第 7 章（API/配置） |
| 写脚本调用仿真器 | 第 7 章（常用 API / 配置文件结构） |
| 搞清相机/深度/LiDAR/IMU 出的数是不是真值 | 第 2 章「传感器仿真」小节（genie_sim_v3 在 §2.4 含 16 个子节；lw_benchhub 在 §2.6 含 13 个子节，**结论是大量能力缺失，先看 §2.6.13 的 21 行边界表**；**genesis_world 在 §2.5 含 7 个子节 —— 四者中建模最完整，但结论是"默认全部理想化"：所有缺陷参数默认 `0.0`，且相机根本没有噪声层，见 §2.5.7**） |
| **官方/博客宣称的性能数字能不能信** | ⚠️ 先看该项目的证据等级标注。**genesis_world 的 103× / 4.6× / Pearson 0.8996 等全部是 `[官网]` 级、评测套件未开源**（`background_knowledge.md` §8.3）；速度类可自测 `examples/speed_benchmark/`、`tests/benchmarks/` |
| 选物理后端 / 调接触参数 | 第 2 章「物理引擎」小节 |
| 判断某能力有没有、值不值得投入 | 第 4 章（关键特性）+ 第 8 章（限制），两章对照看。**lw_benchhub 额外先看 §4.2「规模数字实测校准」** —— README 有 4 处数字与代码不符 |
| **命中"某能力到底有没有"的反复搜索** | 各项目 `00-index.md` 末尾的 **`未提及` / `未找到` 清单** —— 已 grep 确认无证据的方向，**命中就别再搜了** |
| 做 sim2real 或 Real2Sim(3DGS) | 第 2 章渲染 + 第 6 章对应流程 + 第 8 章缺口清单；**实战全流程与踩坑见 `ai_knowledge.md` §2.2 + §4.5** |
| **评估复现工作量 / 避免重复踩坑** | `ai_knowledge.md` §2（时间线与计划变更点）+ §3（决策表）+ §6（8 条可复用教训） |
| 跨工具链选型 | 🌐 [`global/toolchain_comparison.md`](global/toolchain_comparison.md)（对比矩阵 / 选型建议 / 适用边界 / 反向选型）＋ [`projects/00-index.md`](projects/00-index.md) 的「选型对照表」 |
| **想用世界模型（GE-Sim 2.0）替代物理仿真做闭环评测** | ⚠️ 先读 `ge_sim_v2/background_knowledge.md` **§1.4 适用/不适用表**与 **§8.3 能力边界表** —— 它只回答"策略看起来会怎么动"，**不回答"物理上会不会成功"**；再看 **§8.4 交付落差** —— **开箱即用 `reward`/`progress` 恒为 `None`**（World Judge 未开源），"自带奖励"这一核心卖点要自己补 |
| **要引用 GE-Sim 2.0 的性能 / 榜单数字** | ⭐ **必读 `ge_sim_v2/background_knowledge.md` §8.2 五条证据矛盾** —— "100 帧/2.3 秒"实为 25 帧 × 4× 跳帧的**覆盖跨度**；"可做 RL"只见于公众号（论文列为未来工作）；"登顶 WorldArena"指活榜，且**基准论文正文 grep `GE-Sim` 命中 0**、其作者自述该分数与动作规划仅 **r=0.36** 弱相关 |
| **部署 GE-Sim 2.0 时撞到报错** | ⭐ **`ge_sim_v2/troubleshooting.md` 快速症状索引（45 条 / A–F 六类）** —— A 网络下载、B 安装依赖、C 源码契约、D 进程资源、E 正确性与假阴性、**F 平台契约与判分口径**。三条最高频：**`Q09` 四个加速内核开关首次部署应全关**（`spas_sage_attn` 不在 PyPI）、**`Q11` numpy 会被重装需再锁回**、**`Q17` `WorldModelEnv` 不是 gym 接口**（四条 gym 习惯全落空） |
| **世界模型闭环评测跑出 0 分 / 分数不合理** | ⚠️ **先做管道审计再改模型**：`ge_sim_v2/troubleshooting.md` E 类（`Q35`–`Q41`）+ `ai_knowledge.md` `L01` —— 本项目 Stage 3 的 0 % 是**假阴性**（兜底路径静默吞掉），Stage 5 的 0 才是真实测量。审计四件套：**回退计数 / 动作非退化 / 帧数对账 / 输入侧量纲**。最快一步是**把判分器的原始判词打出来读一遍**（`Q35`） |
| **两套 16 维动作布局用混了** | `ge_sim_v2/troubleshooting.md` `Q36` + `background_knowledge.md` §7.2 —— 世界模型侧是 `[L7臂, L夹爪, R7臂, R夹爪]`，策略侧是 `[L7臂, R7臂, L夹爪, R夹爪]`，**用错不报错、只是行为错**，必须走 `types.py` 的 `wm_state_to_policy_state()`。⚠️ **本机复现仓库绕开了这个函数**、手写了两份逐行相同的重排（`code_knowledge.md` §7.2 `S3`）—— 那是反面教材，**新写代码用上游函数** |
| **要接 RoboColiseum 线上评测平台（盲测榜单）** | ⭐ **`ge_sim_v2/background_knowledge.md` §9.3（6 小节）** —— ⚠️ 两处最容易搞反：① **它的仿真引擎是 GenieSim 3.0**（引擎侧知识在本库 `genie_sim_v3` 项目，不是 `ge_sim_v2`）；② **选手不上传策略**，平台**反向拨号**进你本地跑的 agent（WS 隧道 + 双层令牌：`CHALLENGE_TOKEN` 会过期、逐 job 的 `JOB_TOKEN` 不过期）。§9.3.5 是**六处官方口径漂移表**。线路层的二进制分帧协议在平台文档里是 `未提及` 的，只在 **`code_knowledge.md` §3.6.1** 成文（**本库唯一来源**）。踩坑见 `troubleshooting.md` `Q07`/`Q34`/`Q37`/`Q38` 与 **F 类 `Q42`/`Q44`** |
| **榜单分数 / 报告里的数字对不上** | ⚠️ **`ge_sim_v2/troubleshooting.md` F 类** —— **`Q42`**：榜单 `total` 文档写作「求和」但**实测口径是算术平均**，跨榜单 `total` 不可比；⭐ **`Q43`**：计划文档里的任务数 / 拆分 / 乃至报告模板预填的成功率**没有一个可以凭想象填**，规矩是「报告中不存在任何无法溯源到 `results/` 快照的数字」，且**模板里的数字比正文里的更危险**；**`Q44`**：`4xx/5xx` 先怀疑自己（→ `L04`） |
| **要用 Real2Edit2Real 做数据扩增** | **`ge_sim_v2/background_knowledge.md` §9.2** —— ⚠️ **它的底座是 GE-Sim v1，不是 2.0**（勿把 2.0 的能力算过去）；**`facebook/VGGT-1B` 是 CC-BY-NC-4.0 非商用**且**微调需 80 GB 显存**（40 GB 卡只能做推理/生成）。首跑两坑见 §8.5 第 16 条（三个运行脚本默认指向**不存在的配置文件**、API Key 是占位符且**无读环境变量的路径**）。落盘分布的坑见 `ai_knowledge.md` §7.2 与 **`Q45`**（目录编号**不连续**，`range(50)` 会越界；`dz` 恒 0 → Z 泛化未覆盖，教训 `L09`）|
| **要动手跑 GE-Sim 2.0 的五个 Stage** | ⭐⭐ **`ge_sim_v2/quickstart.md`** —— §1 三个隔离 conda 环境与环境变量（注意 **Stage 1/2/3/4 要 `no_proxy=*`、Stage 5 反过来必须走代理**）、§2 五个 Stage 的可粘命令与预期输出、§5 把 `L01` 审计拆成 4 条 shell 命令。改参数与源码位置再进 **`code_knowledge.md` §4**（本仓库**没有 `requirements.txt`/`setup.py`**，依赖只能照 §5.2 手装） |

---

## 知识库现状

- **🌐 全局层（跨项目综合）已建成**：**5 篇 / 2211 行**，入口 [`global/00-index.md`](global/00-index.md)
  - [`common_reproduction_guide.md`](global/common_reproduction_guide.md) 539 行（六阶段 + §7 一页动作序列）
  - [`common_issues_solutions.md`](global/common_issues_solutions.md) 759 行（A–M 十三类 + §0 重复问题榜 + §N 定位顺序；F/H/I/J 四类标记 🔁 4/4）
  - [`toolchain_comparison.md`](global/toolchain_comparison.md) 282 行（9 维对比矩阵 + 选型建议 + 逐项目适用边界 + §5 反向选型）
  - [`best_practices.md`](global/best_practices.md) 390 行（32 条教训按 8 主题重组，🔁 标注收敛度；§9 溯源索引 32 行）
  - [`terminology_mapping.md`](global/terminology_mapping.md) 241 行（按概念族 10 节；§0 九组易混 + §9 同名不同义 10 组）
  - ⚠️ **派生层，不新增事实**；**新增项目后必须回灌**（对比表加列、🔁 重复度重算、教训溯源表加行、检查是否产生新的同名不同义），清单见 [`global/00-index.md`](global/00-index.md) §6
  - **两条 4/4 全部项目独立收敛的教训**：① **任何写进代码或配置的名字，落笔前必须 grep 到它的定义处或读取处**；② **最贵的失败都不报错** —— 本领域的典型失败形态是静默行为错，不是崩溃
- **已完成（五层齐备）**：**4 个项目**
  - **genie_sim_v3** —— 原理层 1694 行（9 章齐备，含传感器仿真深挖）＋ 经验层 393 行（五阶段复现复盘，18 个问题条目 / 10 个决策 / 8 条教训）＋ 排障层 605 行（`Q01`–`Q29` FAQ，按现象检索）＋ **代码层 1251 行**（对应复现仓库 `genie_sim_v3_tour`，8 章：结构 / 入口 / 核心模块 / 配置 / 依赖 / 修改点 / 注意事项 / 四层关联）＋ **速查层 385 行**
  - **lw_benchhub** —— 原理层 1478 行（9 章齐备，含 §2.6 传感器仿真 13 小节、§4.2 规模数字实测校准、§8.3 十六项已验证代码缺陷、§8.7 未找到清单）＋ 经验层 432 行（`P01`–`P38` / `D01`–`D18` / `L01`–`L08`）＋ 排障层 864 行（`Q01`–`Q38`，5 组，带快速症状索引与贡献指南）＋ **代码层 952 行**（对应复现仓库 `lw_benchhub_tour`；`[CODE]`×72 / `[实践]`×15 / `[推断]`×8；含 **11 处 monkey patch 全表**（上游 10 + 本地新增 1）、**两份 vendored IsaacLab 的判别法**、**11 条静默失效路径**、22 行 `Qxx`→机制映射）＋ **速查层 403 行**（3 个带预期输出的运行示例）
  - **genesis_world** —— **原理层 1205 行**（9 章齐备，核对上游 v1.3.3 / HEAD `19f56d6`；含 §2.5 传感器仿真 7 小节、§3.1「四层栈 vs 仓库实际内容」的 Nyx 零命中证据、§5.3 六处依赖 pin 逐条溯因、§8.1 十五条 `[CODE]` 级限制、§8.4 九项未提及清单）＋ **经验层 362 行**（`P01`–`P37` / `D01`–`D20` / `L01`–`L08`；四条技术路线：VLA 闭环 ❌ 0/8、G1+PI0 ⚠️ 仅计划、Go2 PPO ✅、多物理耦合 ✅）＋ **排障层 902 行**（`Q01`–`Q37`，A–H 八类，带 37 行快速症状索引与贡献指南）＋ **代码层 570 行**（对应复现仓库 `genesis-world-tour`，8 章；含 14 个入口的 `文件:行号` 总表、16 行静默失效清单、12 文件/49 行硬编码路径脱敏清单、§8 四张跨层映射表）＋ **速查层 260 行**（3 组带预期输出的运行示例 + 自检清单）。五层交叉引用已闭环。
    ⚠️ **版本落差**：原理层核对 **1.3.3**，其余四层实测于 **1.2.2** —— 后四层的 API 写法不可直接套用到新版本，但能力边界结论（IPC 需额外装 `pyuipc`、无 IPC 时 FEM 不做刚-柔接触、相机无噪声字段、`build()` 不可逆）两边一致
  - **ge_sim_v2** —— **原理层 1414 行**（9 章齐备，核对论文 arXiv:2605.27491v1 + 上游仓库快照 + HF 权重 `community v2.0.1`；含 **§2.7 传感器仿真专项 6 小节**（结论：**只有 RGB**，深度/LiDAR/IMU/力矩/触觉/音频/分割全部未提及，且范式上不存在显式噪声模型）、**§8.2 五条证据矛盾**（宣传口径与论文/代码的逐条比对）、§8.3 能力边界表、§8.4 论文与开源交付落差、§8.5 **十八条**工程注意事项，以及 **§9.2 Real2Edit2Real 专节**与 **§9.3 RoboColiseum 平台专节 6 小节**（含**六处官方口径漂移表**））＋ **经验层 469 行**（`P01`–`P45` / `D01`–`D20` / `L01`–`L09`；五阶段：环境部署 → Real2Edit2Real 数据生成 → 世界模型闭环评测 → 离线过滤式 BC/RWR → RoboColiseum 线上接入；新增 **§4.6 F 类「契约与口径」故障**）＋ **排障层 974 行**（`Q01`–`Q45`，A–F 六类，带 45 行快速症状索引与贡献指南）。⚠️ **论文 v1 与发布权重 v2.0.1 不是同一交付物**；⚠️ **周边两项的常见误认**：**R2E2R 的底座是 GE-Sim v1 而非 2.0**，**RoboColiseum 的引擎是 GenieSim 3.0 且选手不上传策略**（平台反向拨号进本地 agent）。
    **实践层三条最贵的结论**：① **推理吞吐 0.88 帧/s ≈ 0.055× 实时** —— 它做不了在线 RL 的数据引擎，只适合离线批量 rollout；② **Stage 3 的 0 % 成功率是假阴性**（兜底路径静默吞掉动作），`L01`「下结论前先审计管道」是本项目最贵的一条教训；③ **RWR 把过滤式 BC 从 30 % 拉到 80 %**（在世界模型自采数据上），但**判分器是自己补的 MiMo 替身，不是官方 World Judge**。
    **代码层 743 行**（对应复现仓库 `GE-Sim-V2-tour`，8 章；描述对象是**薄编排层**约 8.8 k 行、**零模型代码**，上游 `gesim` 子模块只改一行；含 **13 条静默失效路径**、**≥5 组重复定义常量**、三个隔离 conda 环境与**逐 Stage 相反的代理策略**、§8 五张跨层映射表，以及 ⭐ **§3.6.1 线上评测隧道的线路层参数** —— 该二进制分帧协议**在平台文档里是 `未提及` 的，本库是唯一成文来源**）＋ **速查层 312 行**（5 个 Stage 的运行示例 + 把 `L01` 审计拆成 4 条可直接粘的命令 + 6 条交付口径检查）。五层交叉引用已闭环。
    ⚠️ **代码层最反常的一条**：教训 `L06`（常量必须单点定义）**在产出这条教训的同一个仓库里被违反了至少四次** —— 本知识库少见的「教训与反例同时留档」，见 `code_knowledge.md` §8.2。
    ⚠️ **两处已就地标注的跨层冲突**：① 原理层 §5.4 建议「四个加速内核全关」，实测只关了 `sparge_attention` 一个也能全程跑通（以代码层 §6.1 为准）；② 两套 16 维布局转换请用上游 `wm_state_to_policy_state()`，**不要**照抄本仓库手写的两份重排（以原理层 §7.2 为准）。
- **下一步建议**：四个项目均已五层齐备，全局层五篇已建成。新增项目时按 `CLAUDE.md` 的写入约定推进，每篇完成后同步更新本文件、`projects/00-index.md` 与该项目 `00-index.md` 三处；**项目五层齐备后，还要按 [`global/00-index.md`](global/00-index.md) §6 的清单回灌全局层**
