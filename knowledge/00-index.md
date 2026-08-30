# 具身智能仿真工具链知识库 · 总索引

> 更新日期：2026-08-29
> 本知识库用途：作为 **Claude Code 的常驻参考层**，服务两类任务——
> 1. **复现**：从零部署某个具身智能仿真工具链（装环境、跑通闭环、排障）
> 2. **使用**：在已复现的工具链上完成新的仿真测试任务（评测、采数、场景生成、RL 训练）

---

## 给 Claude Code 的使用约定（先读这一节）

**检索顺序（三级索引，逐层收窄，不要一上来就读正文）：**

```
knowledge/00-index.md            ← 你在这里。判断"该查哪个项目"
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
| **我手上有一条具体报错 / 日志异常，现在怎么办？** | **排障层** `troubleshooting.md` —— 直接看顶部「快速症状索引」，按现象查到 `Qxx`。**带报错时这是最快路径，优先于经验层。** |
| **我要动代码 / 要跑起来 / 找某个类或参数在哪个文件？** | **代码层** `code_knowledge.md` —— §2 入口点与完整命令、§3 核心模块、§4 配置系统、§7 硬编码陷阱 |
| 这个报错**为什么**会这样？当时试过哪些无效方法？ | **经验层** `ai_knowledge.md` §4（问题表含"无效尝试"列，可直接排除错误路径） |
| 这个仿真器怎么设计的？有什么 API / 配置项 / 能力边界？ | **原理层** `background_knowledge.md` |
| 复现这东西大概要多久、会踩几个坑、哪些决策容易做错？ | **经验层** §2 时间线 + §3 决策表 + §6 教训 |

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
│   └── projects/
│       ├── 00-index.md              ← 项目花名册
│       └── <project_slug>/
│           ├── 00-index.md          ← 项目内章节地图（四篇文档都在这里定位行号）
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
- `sources/` 与 `*_tour/` 不入库，**索引里引用它们的路径仅在本机有效**；换机器需重新 clone。

---

## 项目花名册（速览）

详表见 [`projects/00-index.md`](projects/00-index.md)。

| 项目 | 定位一句话 | 速查层 | 原理层文档 | 经验层文档 | 排障层文档 | 代码层文档 |
|---|---|---|---|---|---|---|
| **genie_sim_v3** | 智元 Genie Sim 3.x，OpenUSD + Isaac Sim 的评测/采集/RL 三栈仿真平台 | ⭐ [速查卡](projects/genie_sim_v3/quickstart.md) | ✅ [已完成](projects/genie_sim_v3/background_knowledge.md) | ✅ [已完成](projects/genie_sim_v3/ai_knowledge.md) | ✅ [Q01–Q29](projects/genie_sim_v3/troubleshooting.md) | ✅ [已完成](projects/genie_sim_v3/code_knowledge.md) |
| **genesis_world** | Genesis World 通用物理平台，8 类求解器 + 3 种可换耦合器，单卡大规模并行、可微仿真、传感器缺陷建模 | ⏳ 待编写 | ✅ [已完成](projects/genesis_world/background_knowledge.md)（v1.3.3） | ✅ [已完成](projects/genesis_world/ai_knowledge.md)（v1.2.2） | ✅ [Q01–Q37](projects/genesis_world/troubleshooting.md) | ⏳ 待编写 |
| **ge_sim_v2** | 智元 GE-Sim-V2，视频扩散**生成式世界模型**（非传统物理仿真） | ⏳ 待编写 | ⏳ 待编写 | ⏳ 待编写 | ⏳ 待编写 | ⏳ 待编写 |
| **lw_benchhub** | 光轮 LW-BenchHub，架在 Isaac Lab + IsaacLab-Arena 之上的**薄组合层**操作 benchmark | ⭐ [速查卡](projects/lw_benchhub/quickstart.md) | ✅ [已完成](projects/lw_benchhub/background_knowledge.md) | ✅ [已完成](projects/lw_benchhub/ai_knowledge.md) | ✅ [Q01–Q38](projects/lw_benchhub/troubleshooting.md) | ✅ [已完成](projects/lw_benchhub/code_knowledge.md) |

---

## 常见任务 → 去哪查

| 我要做的事 | 建议路径 |
|---|---|
| **手上有一条报错，先判断是不是已知坑** | ⭐ **`troubleshooting.md` 顶部「快速症状索引」** —— 按现象直接查到 `Qxx`（genie_sim_v3 有 **29** 条；lw_benchhub 有 **38** 条；**genesis_world 有 37 条，分 A–H 八类**。索引栏写的都是**逐字报错原文**，可直接 `Ctrl-F`） |
| **把某个已复现的工具链跑起来（完整命令）** | ⭐⭐ **先看 `quickstart.md`**（若该项目有）—— 最短路径 + 自检清单；不够细再进 **`code_knowledge.md` §2「入口点与运行方式」**（容器启动、逐条 `docker exec`、环境变量总表） |
| **改代码 / 加新任务 / 改配置项** | ⭐ **`code_knowledge.md` §3 核心模块 + §4 配置系统**（含"注册新任务必改的 6 处"） |
| **换机器或换显卡前的兼容性检查** | **`code_knowledge.md` §7.5 平台假设 + §5.5 版本约束** —— 编译期写死的 GPU 架构是最常见的坑。**lw_benchhub 额外必看 §7.1** —— 硬编码主机绝对路径散布 79 文件 326 处，换机不改则开箱不可运行 |
| **"我改了代码 / 配置，但完全没生效"** | ⭐ **`code_knowledge.md` §7「代码中的注意事项」** —— 这类失败的共同形态是**静默无效**（配置照收、日志照打、行为不变）。lw_benchhub 有 **11 条已知静默失效路径**（§7.2），且仓库内**存在两份 vendored IsaacLab**，改错那份不报错也不生效（§7.3 给了判别法） |
| 装某个仿真器 / 排装机报错 | `troubleshooting.md` §一~§三 → 详因见 `ai_knowledge.md` §4（含无效尝试）→ 再看 `background_knowledge.md` 第 5 章（安装与依赖）+ 第 8 章（已知问题） |
| **进程像在跑但没有产出** | `troubleshooting.md` §五「看起来在跑类假象」→ 教训 `L2`（独立存活判据） |
| **CUDA 报错 / 显存数字不合理** | `troubleshooting.md` §四（`Q12`–`Q13`）→ `ai_knowledge.md` `P08` + `L1` —— 优先怀疑 compute capability 架构不匹配，而非显存容量 |
| **某个问题至今没解决？** | `troubleshooting.md` §九「未解决 / 仅部分解决」—— 避免在已知死路上重复投入。genesis_world 的三条明确未解见 `Q13` / `Q32` / `Q37` |
| **在 Genesis 上跑 VLA 抓取闭环，值不值得做** | ⚠️ 先读 `genesis_world/ai_knowledge.md` §4.4（`P07`–`P14`）与 §3.1 —— 本机一次完整尝试的结果是 **0/8**，并已把"当前目标不可达"证明到机制层面（`D18`）。**别重跑这条路，除非换掉根因层级**（`L07`） |
| **在 Genesis 上做四足 / 轮足 RL 训练** | ✅ 有完整成功记录：`genesis_world/ai_knowledge.md` §4.5（`P19`–`P23`）+ 排障层 E 类（`Q19`–`Q23`）。⚠️ 头号坑：**rsl-rl 的 checkpoint 编号是 0-based**（`learn(50)` 只产出 `model_49.pt`） |
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
| 跨工具链选型 | [`projects/00-index.md`](projects/00-index.md) 的「选型对照表」 |

---

## 知识库现状

- **已完成（五层齐备）**：**2 个项目**
  - **genie_sim_v3** —— 原理层 1694 行（9 章齐备，含传感器仿真深挖）＋ 经验层 393 行（五阶段复现复盘，18 个问题条目 / 10 个决策 / 8 条教训）＋ 排障层 605 行（`Q01`–`Q29` FAQ，按现象检索）＋ **代码层 1251 行**（对应复现仓库 `genie_sim_v3_tour`，8 章：结构 / 入口 / 核心模块 / 配置 / 依赖 / 修改点 / 注意事项 / 四层关联）＋ **速查层 385 行**
  - **lw_benchhub** —— 原理层 1478 行（9 章齐备，含 §2.6 传感器仿真 13 小节、§4.2 规模数字实测校准、§8.3 十六项已验证代码缺陷、§8.7 未找到清单）＋ 经验层 432 行（`P01`–`P38` / `D01`–`D18` / `L01`–`L08`）＋ 排障层 864 行（`Q01`–`Q38`，5 组，带快速症状索引与贡献指南）＋ **代码层 952 行**（对应复现仓库 `lw_benchhub_tour`；`[CODE]`×72 / `[实践]`×15 / `[推断]`×8；含 **11 处 monkey patch 全表**（上游 10 + 本地新增 1）、**两份 vendored IsaacLab 的判别法**、**11 条静默失效路径**、22 行 `Qxx`→机制映射）＋ **速查层 403 行**（3 个带预期输出的运行示例）
- **编写中**：**1 个项目**
  - **genesis_world** —— **原理层 1202 行**（9 章齐备，核对上游 v1.3.3 / HEAD `19f56d6`；含 §2.5 传感器仿真 7 小节、§3.1「四层栈 vs 仓库实际内容」的 Nyx 零命中证据、§5.3 六处依赖 pin 逐条溯因、§8.1 十五条 `[CODE]` 级限制、§8.4 九项未提及清单）＋ **经验层 347 行**（`P01`–`P37` / `D01`–`D20` / `L01`–`L08`；四条技术路线：VLA 闭环 ❌ 0/8、G1+PI0 ⚠️ 仅计划、Go2 PPO ✅、多物理耦合 ✅）＋ **排障层 901 行**（`Q01`–`Q37`，A–H 八类，带 37 行快速症状索引与贡献指南）。**速查层 / 代码层待编写**（Task9/Task10），原理层 L730 / L902 与 §9.5 中指向这两层的**前向链接暂为死链**。
    ⚠️ **版本落差**：原理层核对 **1.3.3**，经验层与排障层实测于 **1.2.2** —— 后两层的 API 写法不可直接套用到新版本，但能力边界结论（IPC 需额外装 `pyuipc`、无 IPC 时 FEM 不做刚-柔接触、相机无噪声字段、`build()` 不可逆）两边一致
- **源料就绪、待编写**：1 个项目（ge_sim_v2），`sources/ge_sim_v2/` 下已有 URL 清单与原始资料，且本机有对应的实战仓库可交叉验证
- **下一步建议**：先补齐 genesis_world 的**代码层 / 速查层**（对象是本机复现仓库 `genesis-world-tour/`），再按同一五层模板处理 ge_sim_v2。每篇完成后同步更新本文件、`projects/00-index.md` 与该项目 `00-index.md` 三处
