# 仓库说明（给 Claude Code）

这是一个**具身智能仿真工具链知识库**，不是软件工程项目。它的存在目的是给你（Claude Code）提供常驻参考层，服务两类任务：

1. **复现** — 从零部署某个具身智能仿真工具链（装环境、跑通闭环、排障）
2. **使用** — 在已复现的工具链上做新的仿真测试任务（评测、采数、场景生成、RL 训练）

---

## 检索协议（回答本领域问题前先走这一步）

**入口固定**：[`knowledge/00-index.md`](knowledge/00-index.md)

```
knowledge/00-index.md                        判断该查哪个项目
    ↓
knowledge/projects/00-index.md               项目花名册 / 标签 / 选型对照表
    ↓
knowledge/projects/<项目>/00-index.md        章节地图（带行号）+ 未提及清单
    ↓
    ├── background_knowledge.md   【原理层】是什么、怎么设计、API 与限制（固定 9 章）
    ├── ai_knowledge.md           【经验层】实战踩坑、决策复盘、可复用教训
    └── troubleshooting.md        【排障层】按报错现象查的 Q&A
          三者都用 offset/limit 只读那几十行
```

**先选对文档层次**（选错最浪费时间）：

| 手上有什么 | 去哪 |
|---|---|
| **一条具体报错 / 日志异常** | **`troubleshooting.md` 顶部「快速症状索引」** → 按现象查到 `Qxx`。**带报错时这是最快路径，优先于经验层。** |
| 想知道**为什么会这样、试过哪些无效方法** | `ai_knowledge.md` §4 问题表（含"无效尝试"列） |
| 查 API / 参数 / 设计原理 / 能力边界 | `background_knowledge.md` |
| 估工作量、避免重复踩坑 | `ai_knowledge.md` §2 时间线 + §3 决策表 + §6 教训 |

排障层与经验层是**同一批事实的两个视图**（`Qxx` ↔ `Pxx` 一一对应），不必两边都读。

**规则：**

- **不要整篇读 `background_knowledge.md`**（单篇可达 1600+ 行）。先在项目级 `00-index.md` 拿到行号，再用 `Read` 的 `offset`/`limit` 精准读取。
- **先查 `未提及` 清单**。项目级索引集中列出了已 grep 确认"资料中无证据"的方向。命中清单就别再搜了，直接说明缺证据，或去读上游仓库源码。
- **认证据等级**：`[CODE]` 可在上游仓库验证 → 工程决策只信这一级；`[PAPER]` 是论文宣称值；`[README]` 来自仓库文档；`[实践]` 是本机踩坑记录，**不是官方结论**。`ai_knowledge.md` 与 `troubleshooting.md` **全篇均为 `[实践]` 级**。
- **注意版本落差**。原理层描述的可能是比实践记录更新的 release（如 genie_sim_v3：原理层是 v3.2.0 的 `geniesim` CLI，实践记录是 3.0 时期的 `app/app.py`）。**经验层的命令不可直接套用**，先看该文 §7.1 的落差表。
- **原理层里的修复建议可能已被实践推翻**。若两层冲突，以经验层的事后结论为准（例：`background_knowledge.md` §8.4 建议用 `primvars:displayColor` 补色，已被 `D10` 自我否定）。
- **行号会漂**。若读到的内容与索引描述不符，用 `grep -n '^#\{2,3\} '` 重新定位，并顺手修正索引。
- 已收录项目见 `knowledge/projects/00-index.md`。目前仅 `genie_sim_v3` 完成（三层齐备），其余三个（`genesis_world` / `ge_sim_v2` / `lw_benchhub`）源料就绪、待编写。

---

## 写入约定（新增或修改知识文档时）

| 约定 | 说明 |
|---|---|
| 固定 9 章结构 | **仅 `background_knowledge.md`**：项目概述 / 核心原理 / 架构与模块 / 关键特性 / 安装与依赖 / 基本使用流程 / 常用 API 接口 / 已知问题与限制 / 参考资源。**章号跨项目稳定**，是索引行号表能通用的前提。 |
| 经验层固定 8 章 | **仅 `ai_knowledge.md`**：复现目标与背景 / 计划与执行流程 / 关键决策与原因 / **遇到的问题与解决方案（核心章）** / AI Agent 表现评估 / 可复用的经验教训 / 关联的 background 类知识 / 附录原始材料索引。 |
| 排障层由经验层派生 | `troubleshooting.md` 是 `ai_knowledge.md` §4 按**故障类别**重排的 Q&A，不是新事实来源。每条含 `**Q**` 现象／`**A**` 步骤／**❌ 无效尝试**／回指 `Pxx`·`Lxx` 的「相关经验」。顶部必须有「快速症状索引」表（现象 → `Qxx`）。 |
| 编号永久稳定 | `P`（问题）/`D`（决策）/`L`（教训）/`Q`（FAQ）/`E`（事件）**只追加、不重排、不复用**，外部交叉引用依赖此约定。 |
| 双向交叉引用 | 新增经验层或排障层后，**必须回头在 `background_knowledge.md` 的对应章节加指回链接**（§5 安装、§6 使用流程、§8 已知问题至少各一处）。原理层的建议若被实践推翻，要在原理层就地标注冲突并给出以哪层为准。 |
| 禁密钥禁绝对路径 | 不得出现账号、密码、密钥、access token。示例里的本地路径写 `<your_path>` 或 `<path>`/`<user_home>`，主机地址写 `<INFER_IP>:<PORT>`。 |
| 缺证据就标 `未提及` | **不推测、不编造**。同时把该项补进项目级索引的 `未提及` 清单。 |
| 每条结论带证据标注 | `[CODE]` 附仓库相对路径（必要时带行号）。经验层/排障层全篇 `[实践]`，须在文档头声明"不是官方结论"。 |
| 分批写入 | 每次约 100–200 行，避免单次超长写入失败。用哨兵注释（如 `<!-- CHUNK_MARKER -->`）追加，最后一批删除哨兵。 |
| 三处索引同步更新 | 完成/修改一篇文档后，同步 `knowledge/00-index.md` 的花名册表与「常见任务」路由、`knowledge/projects/00-index.md` 的总表与项目条目（含摘要）、以及该项目 `00-index.md` 的行号表与章节地图。**新增文档类型时还要更新本文件的检索协议。** |
| 标签复用词表 | 见 `knowledge/projects/00-index.md` 末尾的标签词表，**勿造同义词**。 |

---

## 目录结构

```
simulation-knowledge/
├── CLAUDE.md                  ← 本文件
├── knowledge/                 ← ✅ 唯一纳入 git 跟踪的知识层
│   ├── 00-index.md
│   └── projects/
│       ├── 00-index.md
│       └── <project_slug>/
│           ├── 00-index.md
│           ├── background_knowledge.md   ← 原理层（固定 9 章，必备）
│           ├── ai_knowledge.md           ← 经验层（复现复盘，有实战记录才写）
│           └── troubleshooting.md        ← 排障层（由经验层 §4 派生的 Q&A）
├── sources/                   ← ⚠️ gitignore，仅本机存在
│   └── <project_slug>/
│       ├── background.txt     ← 源料 URL 清单
│       ├── *.md / *.txt       ← 抓取的原始资料
│       └── <upstream_repo>/   ← git clone 的上游仓库
└── <project>_tour/            ← ⚠️ gitignore，本人的实战复现仓库
```

`sources/` 与 `*_tour/` 已 gitignore：索引中引用它们的路径**仅在本机有效**，换机器需重新 clone。上游仓库源码是 `[CODE]` 级证据的来源——需要核实细节时读 `sources/<slug>/<repo>/`，而不是猜。
