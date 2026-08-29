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
        ├── background_knowledge.md   ← 【原理层】是什么、怎么设计、API 与限制
        ├── ai_knowledge.md           ← 【经验层】实战踩坑、决策复盘、可复用教训
        └── troubleshooting.md        ← 【排障层】按报错现象查的 Q&A（最快路径）
              三者都只读需要的那几十行
```

**先选对文档层次**（这一步选错会浪费很多时间）：

| 我的问题是 | 查哪层 |
|---|---|
| **我手上有一条具体报错 / 日志异常，现在怎么办？** | **排障层** `troubleshooting.md` —— 直接看顶部「快速症状索引」，按现象查到 `Qxx`。**带报错时这是最快路径，优先于经验层。** |
| 这个报错**为什么**会这样？当时试过哪些无效方法？ | **经验层** `ai_knowledge.md` §4（问题表含"无效尝试"列，可直接排除错误路径） |
| 这个仿真器怎么设计的？有什么 API / 配置项 / 能力边界？ | **原理层** `background_knowledge.md` |
| 复现这东西大概要多久、会踩几个坑、哪些决策容易做错？ | **经验层** §2 时间线 + §3 决策表 + §6 教训 |

> 排障层与经验层是**同一批事实的两个视图**（`Qxx` ↔ `Pxx` 一一对应），不是互相补充 —— 不必两边都读。

**硬性规则：**

| 规则 | 说明 |
|---|---|
| 按需读取 | `background_knowledge.md` 单文件可达 1600+ 行。**永远先读该项目的 `00-index.md` 拿到行号，再用 `Read` 的 `offset`/`limit` 精准读取**，不要整篇载入。 |
| 认证据等级 | 正文每条结论带 `[CODE]` / `[PAPER]` / `[README]` / `[实践]` 标注。**做工程决策只信 `[CODE]`**；`[PAPER]` 是宣称值，`[实践]` 是本地踩坑记录，不等于官方结论。 |
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
│           ├── 00-index.md          ← 项目内章节地图（三篇文档都在这里定位行号）
│           ├── background_knowledge.md   ← 原理层主文档（固定 9 章结构）
│           ├── ai_knowledge.md           ← 经验层文档（复现实战复盘，可选）
│           └── troubleshooting.md        ← 排障层文档（由经验层 §4 改写为 Q&A，可选）
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

| 项目 | 定位一句话 | 原理层文档 | 经验层文档 | 排障层文档 |
|---|---|---|---|---|
| **genie_sim_v3** | 智元 Genie Sim 3.x，OpenUSD + Isaac Sim 的评测/采集/RL 三栈仿真平台 | ✅ [已完成](projects/genie_sim_v3/background_knowledge.md) | ✅ [已完成](projects/genie_sim_v3/ai_knowledge.md) | ✅ [Q01–Q29](projects/genie_sim_v3/troubleshooting.md) |
| **genesis_world** | Genesis World 物理平台，单卡大规模并行 + 刚柔流多物理场 | ⏳ 待编写 | ⏳ 待编写 | ⏳ 待编写 |
| **ge_sim_v2** | 智元 GE-Sim-V2，视频扩散**生成式世界模型**（非传统物理仿真） | ⏳ 待编写 | ⏳ 待编写 | ⏳ 待编写 |
| **lw_benchhub** | 光轮 LW-BenchHub，IsaacLab-Arena + lerobot 生态的统一物理底座 | ⏳ 待编写 | ⏳ 待编写 | ⏳ 待编写 |

---

## 常见任务 → 去哪查

| 我要做的事 | 建议路径 |
|---|---|
| **手上有一条报错，先判断是不是已知坑** | ⭐ **`troubleshooting.md` 顶部「快速症状索引」** —— 按现象直接查到 `Qxx`（genie_sim_v3 有 29 条） |
| 装某个仿真器 / 排装机报错 | `troubleshooting.md` §一~§三 → 详因见 `ai_knowledge.md` §4（含无效尝试）→ 再看 `background_knowledge.md` 第 5 章（安装与依赖）+ 第 8 章（已知问题） |
| **进程像在跑但没有产出** | `troubleshooting.md` §五「看起来在跑类假象」→ 教训 `L2`（独立存活判据） |
| **CUDA 报错 / 显存数字不合理** | `troubleshooting.md` §四（`Q12`–`Q13`）→ `ai_knowledge.md` `P08` + `L1` —— 优先怀疑 compute capability 架构不匹配，而非显存容量 |
| **某个问题至今没解决？** | `troubleshooting.md` §九「未解决 / 仅部分解决」—— 避免在已知死路上重复投入 |
| 跑一次 VLA 闭环评测 | 第 6 章（基本使用流程）→ 第 7 章（API/配置） |
| 写脚本调用仿真器 | 第 7 章（常用 API / 配置文件结构） |
| 搞清相机/深度/LiDAR/IMU 出的数是不是真值 | 第 2 章「传感器仿真」小节（genie_sim_v3 在 §2.4，含 16 个子节） |
| 选物理后端 / 调接触参数 | 第 2 章「物理引擎」小节 |
| 判断某能力有没有、值不值得投入 | 第 4 章（关键特性）+ 第 8 章（限制），两章对照看 |
| 做 sim2real 或 Real2Sim(3DGS) | 第 2 章渲染 + 第 6 章对应流程 + 第 8 章缺口清单；**实战全流程与踩坑见 `ai_knowledge.md` §2.2 + §4.5** |
| **评估复现工作量 / 避免重复踩坑** | `ai_knowledge.md` §2（时间线与计划变更点）+ §3（决策表）+ §6（8 条可复用教训） |
| 跨工具链选型 | [`projects/00-index.md`](projects/00-index.md) 的「选型对照表」 |

---

## 知识库现状

- **已完成**：1 个项目（genie_sim_v3）—— 原理层 1657 行（9 章齐备，含传感器仿真深挖）＋ 经验层 372 行（五阶段复现复盘，18 个问题条目 / 10 个决策 / 8 条教训）＋ 排障层 600 行（`Q01`–`Q29` FAQ，按现象检索）
- **源料就绪、待编写**：3 个项目（genesis_world / ge_sim_v2 / lw_benchhub），`sources/<slug>/` 下已有 URL 清单与原始资料，且本机均有对应的实战仓库可交叉验证
- **下一步建议**：按同一 9 章模板补齐剩余 3 个项目的原理层；三个项目均有本机实战仓库，可同时产出经验层 `ai_knowledge.md`，再由其 §4 派生排障层 `troubleshooting.md`。每篇完成后同步更新本文件、`projects/00-index.md` 与该项目 `00-index.md` 三处
