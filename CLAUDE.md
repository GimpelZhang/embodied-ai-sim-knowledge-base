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
    ├── quickstart.md             【速查层】⭐ 动手前先读：最短路径 + 常见问题 + 自检清单
    ├── background_knowledge.md   【原理层】是什么、怎么设计、API 与限制（固定 9 章）
    ├── ai_knowledge.md           【经验层】实战踩坑、决策复盘、可复用教训（固定 8 章）
    ├── troubleshooting.md        【排障层】按报错现象查的 Q&A
    └── code_knowledge.md         【代码层】代码在哪、怎么启动、改哪个文件（固定 8 章）
          后四者都用 offset/limit 只读那几十行；quickstart 篇幅小，可整篇读
```

**先选对文档层次**（选错最浪费时间）：

| 手上有什么 | 去哪 |
|---|---|
| **要动手跑 / 想不起命令怎么敲** | ⭐ **`quickstart.md`**（若该项目有）→ 环境准备、2–3 个运行示例、改参数、常见代码问题、自检清单。**它是从其余四层提炼的最短路径，先读它再往下钻。** |
| **一条具体报错 / 日志异常** | **`troubleshooting.md` 顶部「快速症状索引」** → 按现象查到 `Qxx`。**带报错时这是最快路径，优先于经验层。** |
| **要改代码 / 找某个类、函数、参数在哪个文件** | **`code_knowledge.md`** → §2 入口点与完整命令、§3 核心模块、§4 配置系统、§7 硬编码陷阱 |
| 想知道**为什么会这样、试过哪些无效方法** | `ai_knowledge.md` §4 问题表（含"无效尝试"列） |
| 查 API / 参数 / 设计原理 / 能力边界 | `background_knowledge.md` |
| 估工作量、避免重复踩坑 | `ai_knowledge.md` §2 时间线 + §3 决策表 + §6 教训 |

排障层与经验层是**同一批事实的两个视图**（`Qxx` ↔ `Pxx` 一一对应），不必两边都读。
**代码层是独立视角**：它描述**本机复现仓库 `<project>_tour` 的代码实体**（不是上游本体），并为排障层的现象提供 `[CODE]` 级机制解释；四层的关联映射见 `code_knowledge.md` §8。
**速查层是派生层，不是新事实来源**：它从其余四层挑出可直接执行的部分，**不重复解释、不新增结论**。与其余各层冲突时，**以被引用的那一层为准**（速查层只是入口）。

**规则：**

- **不要整篇读 `background_knowledge.md` 或 `code_knowledge.md`**（前者可达 1600+ 行，后者 1100+ 行）。先在项目级 `00-index.md` 拿到行号，再用 `Read` 的 `offset`/`limit` 精准读取。
- **先查 `未提及` 清单**。项目级索引集中列出了已 grep 确认"资料中无证据"的方向。命中清单就别再搜了，直接说明缺证据，或去读上游仓库源码。
- **认证据等级**：`[CODE]` 可在上游仓库验证 → 工程决策只信这一级；`[PAPER]` 是论文宣称值；`[README]` 来自仓库文档；`[官网]` 是官方博客/发布页的宣称值，**未开源可复现的验证脚本**；`[文章]` 是第三方分析，二手；`[实践]` 是本机踩坑记录，**不是官方结论**；`[推断]` 证据不足以定论（仅代码层使用）。`[官网]`/`[文章]` 由 `genesis_world` 引入，其不可复现的宣称已集中隔离在 `background_knowledge.md` §8.3，勿把该节内容当工程依据。`ai_knowledge.md` 与 `troubleshooting.md` **全篇均为 `[实践]` 级**；`code_knowledge.md` 三级混用，逐条标注。
- **注意版本落差**。原理层描述的可能是比实践记录/代码层更新的 release（如 genie_sim_v3：原理层是 v3.2.0 的 `geniesim` CLI，经验层与代码层都是 3.0 时期的 `app/app.py`）。**经验层与代码层的命令不可直接套用到新版本**，先看 `ai_knowledge.md` §7.1 与 `code_knowledge.md` §6.4 的落差表。
- **原理层里的修复建议可能已被实践推翻**。若两层冲突，以经验层的事后结论为准（例：`background_knowledge.md` §8.4 建议用 `primvars:displayColor` 补色，已被 `D10` 自我否定）。反之，**代码层 §6.4 可能指出某个 3.0 时期的坑已被上游修掉**——若要在新版本上部署，以代码层的上游对比结论为准。
- **行号会漂**。若读到的内容与索引描述不符，用 `grep -n '^#\{2,3\} '` 重新定位，并顺手修正索引。
- 已收录项目见 `knowledge/projects/00-index.md`。目前 **`genie_sim_v3` 与 `lw_benchhub` 均已五层齐备**（lw_benchhub：原理层 1478 + 经验层 432 + 排障层 864 + 代码层 952 + 速查层 403 行；`P01`–`P38` / `D01`–`D18` / `L01`–`L08` / `Q01`–`Q38`）；**`genesis_world` 已有三层**（原理层 1202 行，核对上游 v1.3.3 / HEAD `19f56d6`；经验层 347 行 + 排障层 901 行，实测 v1.2.2；`P01`–`P37` / `D01`–`D20` / `L01`–`L08` / `Q01`–`Q37`），**速查层与代码层编写中**；`ge_sim_v2` 源料就绪、待编写。
- **`genesis_world` 的三条高频提醒**（不查文档也该知道）：① **官方宣传的"四层栈"有一半不在 pip 包里** —— Render 层的 **Nyx** 在 `genesis/**/*.py` 中 **grep 零命中**（是独立包 `gs-nyx`，按插件装），Compiler 层的 **Quadrants** 是独立包（硬依赖 `quadrants==1.3.0` 精确 pin）；v1.3.3 的 `gs.renderers` 下只有 `Rasterizer`/`RayTracer`/`BatchRenderer`。另：博客称 "Genesis World **1.0**" 而 pip 上是 **1.3.3**，两套编号勿混引。② **传感器"默认即理想真值"** —— 缺陷建模两层继承（`SensorOptions` 给 `delay`/`jitter`/`history_length`，`SimpleSensorOptions` 追加 `resolution`/`bias`/`noise`/`random_walk`）虽然完整，但**所有参数默认 `0.0`**，且**相机直接派生自 `Sensor`、根本没有噪声字段**。③ **博客性能数字全是 `[官网]` 级**（103× / 4.6× / Pearson 0.8996），sim-real 评测套件未开源；速度类可自测 `examples/speed_benchmark/` 与 `tests/benchmarks/`。
- **`genesis_world` 动手前必读三条**（`[CODE]` 级）：① **PyTorch 不在依赖里，必须先单独装**，且 Python 窗口窄（`>=3.10,<3.14`）；**6 处依赖带界/排除 pin**（`trimesh`/`libigl`/`pyglet`/`z3-solver`/`Pillow`/`pygltflib`）各对应一个已知上游破坏，装 `[dev]` 还会把 mujoco 从 `>=3.2.5` 收紧到 `>=3.10,<3.11` —— **建议单独开环境**。② **`scene.build()` 是不可逆分界线** —— `add_entity`/`add_sensor`/`add_camera` 都必须在它之前；`n_envs=0` 与 `n_envs=1` 的张量形状不同（前者无 batch 维）。③ **三种耦合器改一行 `coupler_options=` 即可切换，但不是行为中性的** —— `sap_coupler.py` 里有 20 个物料对专用接触 handler，换耦合器后必须重新验证你那组材料组合；且 **IPC 支需额外 `pip install pyuipc`，仅 Linux/Windows x86 + NVIDIA**。
- **`genesis_world` 复现层的三条硬约束**（`[实践]` 级，实测于 **1.2.2**，见 `ai_knowledge.md` / `troubleshooting.md`）：① **版本落差是本项目最大的引用陷阱** —— 原理层是 1.3.3，经验层与排障层是 1.2.2，**API 写法不可跨版本套用，能力边界结论可以**（`ai_knowledge.md` §1.3）；② **`get_dofs_position` 式 IK 返回的是完整 qpos 而非手臂 7 维**、`cam.render()` 返回 **4 元组 `(rgb, depth, seg, normal)`**、`get_contacts()` **属于 rigid-rigid 管线，对 PBD 粒子实体直接抛 `AttributeError`** —— 三条最高频的 API 误用见排障层 B 类；③ **rsl-rl 的 checkpoint 编号是 0-based** —— `learn(50)` 只会产出 `model_49.pt`，等 `model_50.pt` 会永远等不到（`Q19`）。
- **`genesis_world` 的两条"别重复投入"结论**：① **OpenVLA 抓取闭环在本机 0/8 且已证明到机制层面不可达**（末端恒收敛同一点、夹爪输出恒 0.0、换同本体微调模型仍不收敛），止损决策 `D18` 是本库最值得模仿的一次「先证明不可达、再显式征得同意」；反面教材是 `D08`（放宽判定口径掩盖失败，制造了假阳性 `P09`）。② **Patch 01 / 02（G1 人形 + PI0/Pi0.5）只有计划、没有任何执行记录**，其中的 API 写法未经验证，**引用前务必看清**（`ai_knowledge.md` §4.8）。
- **`lw_benchhub` 的三条高频提醒**（不查文档也该知道）：① 它是**薄组合层**，行为大量由 Isaac Lab / IsaacLab-Arena 决定，**不要升级 isaaclab 或 Arena 子模块**（monkey patch 按 pin 住的版本写死 —— **上游 10 处、本机复现仓库 11 处**；原理层旧标题写的"9 处"已更正，全表见 `code_knowledge.md` §3.1）；② **README 的规模数字有 4 处与代码不符**（任务 272 非 268、机器人 28 非 27、layout 至 62 非 100、rsl-rl 只注册不执行），估工作量以 `background_knowledge.md` §4.2 为准；③ **传感器只有 RGB 且无任何噪声模型**（`enable_corruption=True` 是空转的假开关），依赖深度/激光/触觉的任务需自行扩展。
- **`lw_benchhub` 动代码前必读三条**（`[CODE]` 级）：① 复现仓库内有**两份 vendored IsaacLab**（1362 vs 1857 文件、973 处差异），**被 pip 安装的是 `AutoDataGen/dependencies/IsaacLab/`** —— 改错那份不报错也不生效，判别法见 `code_knowledge.md` §7.3；② 已知 **11 条静默失效路径**（§7.2）与 **79 文件 326 处硬编码主机绝对路径**（§7.1）—— "改了没生效"先查这两处，别急着加假设；③ **YAML 静默覆盖命令行参数（含 AppLauncher 的 `--device`）** —— 8 个入口脚本都有 `args_cli.__dict__.update(yaml_args.__dict__)`，它在 `parse_args()` 之后执行，**命令行显式传的值被无声丢弃**；`teleop_base.yml:6` 是 `device: cpu`，所以 `--device cuda:0` 实际仍跑 CPU（表现为"莫名奇妙地慢"）。**要改这类值就改 YAML**，详见 `background_knowledge.md` §6.1 推论 4 与 §8.3 第 16 条。
- **`lw_benchhub` 复现层的三条硬约束**（`[实践]` 级，来自 `ai_knowledge.md`）：① **`numpy==1.26.0` 必须最后装，每次 pip 操作后重新锁回**（Isaac Sim 的 C 扩展硬绑该版本）；② 运行脚本用 `set +u`（**不是** `set -u`）且必须 `unset CUDA_VISIBLE_DEVICES`，否则相机初始化 segfault 且无 traceback；③ **Isaac Sim 必须先启动，再构造 cuRobo IK**，顺序颠倒会在 USD 纹理分配时 `cudaErrorIllegalAddress`。
- **两条跨项目通用的排障纪律**（本次复现代价最大的两个教训，见 `lw_benchhub/ai_knowledge.md` §6）：① **动手"修复 X"之前，先量化"X 是否真的发生"** —— 本次为一个根本不存在的现象修了三轮；**若修复改变了变量而结果分毫不变，说明变量没起作用或问题不存在**，此时应质疑问题本身而非提第 N 个假设。② **任何写进配置或计划的键 / 字段 / ID，落笔前必须 grep 到它的定义处或读取处** —— 此类错误在本次复发 ≥5 次，且失败形态是**静默无效**（配置照收、日志照打，行为不变）。

---

## 写入约定（新增或修改知识文档时）

| 约定 | 说明 |
|---|---|
| 固定 9 章结构 | **仅 `background_knowledge.md`**：项目概述 / 核心原理 / 架构与模块 / 关键特性 / 安装与依赖 / 基本使用流程 / 常用 API 接口 / 已知问题与限制 / 参考资源。**章号跨项目稳定**，是索引行号表能通用的前提。 |
| 经验层固定 8 章 | **仅 `ai_knowledge.md`**：复现目标与背景 / 计划与执行流程 / 关键决策与原因 / **遇到的问题与解决方案（核心章）** / AI Agent 表现评估 / 可复用的经验教训 / 关联的 background 类知识 / 附录原始材料索引。 |
| 排障层由经验层派生 | `troubleshooting.md` 是 `ai_knowledge.md` §4 按**故障类别**重排的 Q&A，不是新事实来源。每条含 `**Q**` 现象／`**A**` 步骤／**❌ 无效尝试**／回指 `Pxx`·`Lxx` 的「相关经验」。顶部必须有「快速症状索引」表（现象 → `Qxx`）。 |
| 代码层固定 8 章 | **仅 `code_knowledge.md`**：代码结构总览 / 入口点与运行方式 / 核心模块详解 / 配置系统 / 依赖与环境 / 复现过程中的修改点 / 代码中的注意事项 / 与其它三层知识的关联。**描述对象是 `<project>_tour` 复现仓库，不是上游本体**，文档头必须声明这一点。仓库根目录写 `<repo_root>`；容器内路径（如 `/geniesim/main`）照写但要说明它是挂载点。**无法判定某处改动是"本地改的"还是"上游删的"时，标 `[推断]`，不要算成本次改动。** |
| 编号永久稳定 | `P`（问题）/`D`（决策）/`L`（教训）/`Q`（FAQ）/`E`（事件）**只追加、不重排、不复用**，外部交叉引用依赖此约定。 |
| 双向交叉引用 | 新增经验层或排障层后，**必须回头在 `background_knowledge.md` 的对应章节加指回链接**（§5 安装、§6 使用流程、§8 已知问题至少各一处）。原理层的建议若被实践推翻，要在原理层就地标注冲突并给出以哪层为准。**新增代码层后，必须写满其第 8 章的关联映射表**（代码↔原理章节、代码↔`Lxx` 教训物证、代码↔`Qxx` 机制解释、被推翻或修正的结论）。 |
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
│           ├── quickstart.md             ← 速查层（派生自其余四层，不含新事实）
│           ├── background_knowledge.md   ← 原理层（固定 9 章，必备）
│           ├── ai_knowledge.md           ← 经验层（复现复盘，有实战记录才写）
│           ├── troubleshooting.md        ← 排障层（由经验层 §4 派生的 Q&A）
│           └── code_knowledge.md         ← 代码层（对应 <project>_tour，固定 8 章）
├── sources/                   ← ⚠️ gitignore，仅本机存在
│   └── <project_slug>/
│       ├── background.txt     ← 源料 URL 清单
│       ├── *.md / *.txt       ← 抓取的原始资料
│       └── <upstream_repo>/   ← git clone 的上游仓库
└── <project>_tour/            ← ⚠️ gitignore，本人的实战复现仓库
```

`sources/` 与 `*_tour/` 已 gitignore：索引中引用它们的路径**仅在本机有效**，换机器需重新 clone。上游仓库源码是 `[CODE]` 级证据的来源——需要核实细节时读 `sources/<slug>/<repo>/`，而不是猜。**`<project>_tour/` 的代码结构已提炼进 `code_knowledge.md`，查代码优先读该文档，只在需要逐行核实时才翻仓库。**
