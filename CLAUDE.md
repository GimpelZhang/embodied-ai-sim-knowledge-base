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
knowledge/projects/<项目>/background_knowledge.md    用 offset/limit 只读那几十行
```

**规则：**

- **不要整篇读 `background_knowledge.md`**（单篇可达 1600+ 行）。先在项目级 `00-index.md` 拿到行号，再用 `Read` 的 `offset`/`limit` 精准读取。
- **先查 `未提及` 清单**。项目级索引集中列出了已 grep 确认"资料中无证据"的方向。命中清单就别再搜了，直接说明缺证据，或去读上游仓库源码。
- **认证据等级**：`[CODE]` 可在上游仓库验证 → 工程决策只信这一级；`[PAPER]` 是论文宣称值；`[README]` 来自仓库文档；`[实践]` 是本机踩坑记录，**不是官方结论**。
- **行号会漂**。若读到的内容与索引描述不符，用 `grep -n '^#\{2,3\} '` 重新定位，并顺手修正索引。
- 已收录项目见 `knowledge/projects/00-index.md`。目前仅 `genie_sim_v3` 完成，其余三个（`genesis_world` / `ge_sim_v2` / `lw_benchhub`）源料就绪、待编写。

---

## 写入约定（新增或修改知识文档时）

| 约定 | 说明 |
|---|---|
| 固定 9 章结构 | 项目概述 / 核心原理 / 架构与模块 / 关键特性 / 安装与依赖 / 基本使用流程 / 常用 API 接口 / 已知问题与限制 / 参考资源。**章号跨项目稳定**，是索引行号表能通用的前提。 |
| 禁密钥禁绝对路径 | 不得出现账号、密码、密钥、access token。示例里的本地路径写 `<your_path>`，主机地址写 `<INFER_IP>:<PORT>`。 |
| 缺证据就标 `未提及` | **不推测、不编造**。同时把该项补进项目级索引的 `未提及` 清单。 |
| 每条结论带证据标注 | `[CODE]` 附仓库相对路径（必要时带行号）。 |
| 分批写入 | 每次约 100–200 行，避免单次超长写入失败。用哨兵注释（如 `<!-- CHUNK_MARKER -->`）追加，最后一批删除哨兵。 |
| 三处索引同步更新 | 完成/修改一篇文档后，同步 `knowledge/00-index.md` 的花名册表、`knowledge/projects/00-index.md` 的总表与项目条目、以及该项目 `00-index.md` 的行号表。 |
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
│           └── background_knowledge.md
├── sources/                   ← ⚠️ gitignore，仅本机存在
│   └── <project_slug>/
│       ├── background.txt     ← 源料 URL 清单
│       ├── *.md / *.txt       ← 抓取的原始资料
│       └── <upstream_repo>/   ← git clone 的上游仓库
└── <project>_tour/            ← ⚠️ gitignore，本人的实战复现仓库
```

`sources/` 与 `*_tour/` 已 gitignore：索引中引用它们的路径**仅在本机有效**，换机器需重新 clone。上游仓库源码是 `[CODE]` 级证据的来源——需要核实细节时读 `sources/<slug>/<repo>/`，而不是猜。
