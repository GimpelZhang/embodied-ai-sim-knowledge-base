# lw_benchhub 代码知识层（`lw_benchhub_tour`）

> **本文档的性质**：这是对**本人的复现仓库 `lw_benchhub_tour`** 的代码结构说明，供未来"改这套工具链"或"在这套工具链上加新的仿真测试任务"时查阅。
>
> **它不是上游 lw_benchhub 的代码文档。** 上游本体的原理、API、设计意图请读 [`background_knowledge.md`](background_knowledge.md)。本文描述的是**本机这一份能跑起来的快照**：改了什么、入口在哪、配置怎么串、坑在哪一行。
>
> **与 genie_sim_v3 代码层的形态差异（重要）**：`genie_sim_v3_tour` 是**选择性覆盖层**（只收改过的文件）；`lw_benchhub_tour` 相反，是一个**整体 vendored monorepo** —— 5 个上游仓库（`lw_benchhub` / `IsaacLab` / `IsaacLab-Arena` / `AutoDataGen` / `lerobot`）以**普通目录**而非 git submodule 的形式直接提交进来，共 **5679 个跟踪文件**。因此"仓库里有某文件"**不等于**"这文件是本次改的"，两者必须靠 git 历史区分，见 §6.1。
>
> **证据等级**：
> - `[CODE]` — 可在 `lw_benchhub_tour/` 内逐行核对（本文给出仓库相对路径，必要时带行号），本文绝大多数结论属此级。
> - `[实践]` — 来自 [`ai_knowledge.md`](ai_knowledge.md) / [`troubleshooting.md`](troubleshooting.md) 的本机踩坑记录，**不是官方结论**。
> - `[推断]` — 由代码痕迹或 diff 推出但**无法证明归因**的（尤其"这是本地改的还是上游本来就这样"），全部显式标注。按仓库写入约定，**`[推断]` 级的改动不计入 §6 的本次改动清单**。
>
> **脱敏声明**：**本文已替换敏感信息。** 仓库根目录一律写 `<repo_root>`；主机绝对路径写 `<orig_root>` / `<user_home>` / `<path>`；conda 前缀写 `<conda_prefix>`；模型仓库缓存写 `<hf_cache>`。凡涉及 API key / token 的，本文**只写变量名与所在文件，不写值**，见 §5.4 与 §7.6。

**五层知识里本文的位置**：

| 你现在要做的事 | 去哪 |
|---|---|
| **只想尽快装完跑起来 / 想不起命令怎么敲** | ⭐ [`quickstart.md`](quickstart.md) —— 从本文与其余三层提炼的**最短可执行路径**（篇幅小，可整篇读） |
| 改代码 / 加场景 / 找某个类、函数、参数在哪个文件 | **本文** |
| 查某个原理、API 语义、能力边界、为什么这么设计 | [`background_knowledge.md`](background_knowledge.md) |
| 手上有一条报错 | [`troubleshooting.md`](troubleshooting.md) 顶部「快速症状索引」 |
| 想知道当初为什么这么改、试过哪些无效方案 | [`ai_knowledge.md`](ai_knowledge.md) §3 决策表 / §4 问题表 |

> **本文与 `quickstart.md` 的分工**：quickstart 是**派生层**，只挑「可直接照做的部分」，**不新增结论**；本文是它引用的底本。两者若冲突，**以本文为准**。

第八章给出本文与其余各层的**逐条映射表**。

---

## 一、代码结构总览

### 1.1 仓库性质与规模

`[CODE]` `git ls-files | wc -l` = **5679** 个跟踪文件。顶层分布：

| 顶层目录 | 跟踪文件数 | 性质 |
|---|---|---|
| `AutoDataGen/` | 2491 | **vendored 上游** —— 自动示教生成框架，内含 `dependencies/curobo/`（可编辑安装的 cuRobo 0.7.7） |
| `IsaacLab/` | 1362 | **vendored 上游** —— Isaac Lab v2.3.2 |
| `lw_benchhub/` | 847 | **vendored 上游 + 本次改动集中地**（5 个补丁文件全在这里，见 §6.2） |
| `lerobot/` | 605 | **vendored 上游** —— lerobot 0.5.1，评测 CLI 与数据集库 |
| `IsaacLab-Arena/` | 243 | **vendored 上游** —— `release/0.1.1`，任务/技能原语 |
| `stage4_flywheel/` | 100 | **本人新写** —— 数据飞轮（Stage 4）全部脚本、配置、URDF、指标 |
| `(root)` | 17 | **本人新写** —— 4 个 Stage 2/3 主脚本 + 4 个环境脚本 + Docker + 文档 |
| `stage2_logs/` | 7 | **本人新写** —— Stage 2 调度脚本 + 可达性报告 + manifest |
| `images/` | 4 | README 用的 banner / GIF |
| `pathB_logs/` | 3 | **本人新写** —— 路径 B（SmolVLA 评测，"黄金路径"）的运行脚本 |

**读法上的直接推论 `[CODE]`**：本次复现真正**新写**的代码只有 **`stage4_flywheel/` + 根目录 + `stage2_logs/` + `pathB_logs/`，共约 127 个文件**；剩下 5552 个文件是 vendored 上游，其中**只有 6 个被改过**（§6.2）。**先看这 127 个，不要从 5679 个里找起。**

`[CODE]` Git 现状：**10 个提交，单一分支 `main`**（`feature-flywheel` 已经 PR #1 合并进 main 并删除本地分支）。时间序：

```
32a1751  Initial monorepo commit: lw_benchhub_tour
dc63eca  Add CLAUDE.md                                  ← 交接文档（562 行）
c5233b1  Stage 2/4 regression fix: verify_stage4_v2.sh protected paths
525a4f1  Remove _v1-_v6 iteration suffixes from committed project files   ← 迭代后缀清理，见 §6.5
80a77c2  Remove unused files
5aa8b5f  Add LICENSE
88f5999  Stage 4 Phase 2 方案二: gripper collision spheres + activation_distance
5163560  Stage 4 Patch 02: fix skill.reset (Issue A) + plan_batch crash resilience + rotation_threshold config
6179df7  docs: add Stage 4 data-flywheel experience to CLAUDE.md
951f239  Merge pull request #1 from GimpelZhang/feature-flywheel
e88ba35  docs: rewrite README (Chinese project intro + stage banners) + images/
```

⚠️ `[CODE]` **remote 是公开 GitHub 仓库**。因此 `.gitignore` 的排除项不只是"减小体积"，还是**唯一的凭据隔离机制** —— 见 §1.3 与 §7.6。

### 1.2 目录树（只展开本人新写的部分）

```
<repo_root>/
├── CLAUDE.md                        ← 562 行交接文档，本文的主要一手依据
├── README.md                        ← 119 行中文项目介绍 + 阶段 banner
├── .gitignore                       ← ⚠️ 凭据隔离机制，见 §1.3
│
├── 【环境脚本：source 之后才能跑任何东西】
├── autosim_env.sh                   ← AutoDataGen / autosim 侧环境
├── lerobot_arena_curobo_env.sh      ← ⭐ cuRobo 脚本管线用（Stage 2 / Stage 4 T3）
├── headless_env.sh.example          ← 无头渲染变量模板（真文件被 gitignore）
├── llm_env.sh.example               ← LLM 端点/密钥模板（真文件被 gitignore）
├── deepseek_v4pro_env.sh.example    ← 同上，v4-pro 端点
│
├── 【Stage 2/3 主脚本】
├── generate_scenes_with_live_reach.py   ← LLM 场景生成 + 在线可达性闭环（v6）
├── validate_scene_objects_reach.py      ← 可达性验证器（被上者 in-process import）
├── verify_stage2.py                     ← Stage 2 产物自检
├── auto_stage3_benchmark.py             ← 31 KB，Stage 3 批量评测调度器
├── deepseek_v4_pro.py                   ← LLM 调用薄封装（零第三方依赖）
├── piper_curobo.yml                     ← 可达性验证用的 cuRobo 机器人配置
│
├── 【容器化评测】
├── Dockerfile.eval
├── run_eval_docker.sh
│
├── stage2_logs/                     ← Stage 2 调度与产物
│   ├── run_stage2_all.sh / run_stage2_scene.sh
│   ├── final_manifest.json          ← 被接受的场景清单
│   ├── smoketest.json
│   └── scene_reach_reports/scene_{1,2,3}_reach.json
│
├── pathB_logs/                      ← ⭐ 路径 B「黄金路径」：40% 成功率那次
│   ├── run_pathB.sh                 ← 完整评测命令，见 §2.3
│   └── run_stage2_all.sh / run_stage2_scene.sh
│
├── stage4_flywheel/                 ← 数据飞轮，100 文件
│   ├── scripts/                     ← 19 个脚本，核心是 generate_policy_demos.py
│   ├── curobo/                      ← 双臂 URDF + 左右臂 cuRobo 配置（含碰撞球）
│   ├── curriculum/                  ← 21 个按难度 band × seed 的场景 YAML
│   ├── configs/                     ← 4 个场景配置（easy/medium/hard/_probe_seed）
│   ├── llm/                         ← 课程生成的 prompt / response / 审计 JSON
│   ├── metrics/                     ← baseline / curriculum 指标与关节表
│   ├── demos/hard_scene/            ← 演示产物
│   ├── generate_pnp_curriculum_v4pro.py
│   └── report_v2_draft.md
│
└── 【vendored 上游，共 5552 文件，只有 6 个被改过（§6.2）】
    ├── lw_benchhub/                 ← 847（含 lw_benchhub/ 472、lw_benchhub_tasks/ 252、configs/ 46）
    ├── IsaacLab/                    ← 1362
    ├── IsaacLab-Arena/              ← 243
    ├── AutoDataGen/                 ← 2491（含 dependencies/curobo/）
    └── lerobot/                     ← 605
```

### 1.3 `.gitignore` 是本仓库的安全边界（务必先读）

`[CODE]` `<repo_root>/.gitignore` 的排除项分四类，**第一类是安全性的、不可放松**：

| 类别 | 排除项 | 为什么 |
|---|---|---|
| **① 凭据（安全）** | `.gitignore:7-14`：`headless_env.sh`、`llm_env.sh`、`deepseek_v4pro_env.sh`、`*.env.sh`、`genesis_vla_env.sh` —— 但用 `!` **保留** 4 个 `*.example` | 真文件里含 LLM API key / HF token。原注释写得很直白：`NEVER commit; .example templates are tracked`。**模板进仓库，真值不进**。新机部署时 `cp *.example` 去掉后缀再填值 |
| ② 大产物 | `models/`、`conda/`、`.cache/`、`stage4_flywheel/datasets/`、`eval_outputs_*/`、`*.mp4`、`*.hdf5`、`*.h5`、`*.tar.gz` | 数据集与视频体积大；`policy_demos_v3_lerobot`（10 ep / 6527 帧）**不在仓库里**，需按 §2.4 重新生成 |
| ③ 运行时噪声 | `*.log`、`*.pid`、`*.stdout`、`.omc/`、`__pycache__/`、`*.so`、各 `*_install_logs/`、`stage3_logs/`、`stage4_flywheel/logs/` | — |
| ④ 迭代残留与安全备份 | `*.bak_patch01`、`*.bak_patch01_descend`、`*.bak_patch02`、`pathB_logs_v{2,3,4,5}/`、`_legacy/`、`_git_backups/`、`docs/`、各 `regress_*/` | `.bak_patch0*` 的原注释是 `restore points, not source` —— 它们是 Stage 4 Phase 2 / Patch 02 的**本地回滚点**。另见 §6.5：`_v1`–`_v6` 迭代后缀在提交前被统一清理 |
| ⑤ 嵌套 `.git` 兜底 | `*/.git/`、`*/*/.git/`（注释：`safety; should not exist`） | vendored 时 5 个上游仓库的 `.git/` 已被吸收删除；这两行是防回归 |

⚠️ **例外白名单**（`!` 规则）：`pathB_logs/run_pathB.sh`、`stage2_logs/run_stage2*.sh`、`final_manifest.json`、`smoketest.json`、`scene_reach_reports/` 被显式保留 —— 这些是**复现所需的最小证据集**，虽然位于被忽略的日志目录下。

> `[实践]` **`docs/` 被 gitignore**。交接文档 `CLAUDE.md` §12.1 引用的 `Stage4_Plan*.md` / `Stage4_Patch_02_report.md` 等**只在本机存在**，换机器后这些引用会失效 —— 它们的结论已被提炼进 [`ai_knowledge.md`](ai_knowledge.md) 与本文，不必回去找。

### 1.4 三条读码路线（按目的选）

| 目的 | 读这几个文件，按顺序 |
|---|---|
| **跑通一次评测** | `pathB_logs/run_pathB.sh` → `lerobot_arena_curobo_env.sh`（只看变量）→ `lw_benchhub/configs/envhub/example.yml` |
| **改场景 / 加难度** | `generate_scenes_with_live_reach.py` → `validate_scene_objects_reach.py` → `stage4_flywheel/curriculum/scene_*.yml` → `piper_curobo.yml` |
| **改数据采集** | `stage4_flywheel/scripts/generate_policy_demos.py` → `build_lerobot_dataset.py` → `stage4_flywheel/configs/hard_scene.yml` |

---

## 二、入口点与运行方式

### 2.0 ⚠️ 先读这条：本仓库的所有脚本在新机上**开箱不可运行**

`[CODE]` **所有**根目录与 `stage2_logs/`、`pathB_logs/` 下的脚本，都把仓库根**硬编码为原复现机的一个挂载点**（本文统一记作 `<orig_root>`），conda 前缀硬编码为 `<orig_root>/conda/envs/{autosim,lerobot-arena}`，conda 初始化脚本硬编码为 `<user_home>/miniconda3/etc/profile.d/conda.sh`。本机 clone 落在 `<repo_root>`，**两者不同**。

三个选项，按代价排序：

| 方案 | 做法 | 代价 |
|---|---|---|
| ① 对齐路径（原样复现时最省） | 把仓库放到 `<orig_root>`，conda env 建在 `<orig_root>/conda/envs/` | 需要该挂载点的写权限 |
| ② 全局替换 | `git grep -l '<orig_root>'` 逐个改 | ⚠️ **实测 79 个文件、326 处**（含交接文档 `CLAUDE.md` 自身 45 处），详见 §7.1 |
| ③ 只改要跑的那一条链路 | 按 §1.4 的三条读码路线，只改用到的 3–5 个文件 | 最快，但易漏（脚本之间靠约定路径通信，见 §4 的 ④ 轨） |

`[CODE]` 另外两个"文件根本不存在"的坑：`generate_scenes_with_live_reach.py:34` source 的 `headless_env.sh`、`deepseek_v4_pro.py:32` 提示的 `deepseek_v4pro_env.sh`，本机**只有 `.example` 模板**（实体被 `.gitignore:7-9` 排除，见 §1.3）。跑之前必须：

```bash
cd <repo_root>
cp headless_env.sh.example headless_env.sh && chmod 600 headless_env.sh
cp llm_env.sh.example      llm_env.sh      && chmod 600 llm_env.sh
# 然后填入真实的 HF_TOKEN / OPENAI_API_KEY —— 模板里全是占位符
```

### 2.1 所有脚本共用的"运行前奏"范式

`[CODE]` 这套六行前奏在 `pathB_logs/run_pathB.sh:2-8`、`stage2_logs/run_stage2_scene.sh:4-19`、`generate_scenes_with_live_reach.py:139-148`（拼成 bash 串）三处重复出现，**是本工具链的运行契约**：

```bash
set +u                                       # ① 不能用 set -u，见下
source <user_home>/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena                 # ② 或 autosim，两个 env 互相独立
source <repo_root>/headless_env.sh           # ③ 无头渲染 + EULA 应答 + HF 缓存
unset CUDA_VISIBLE_DEVICES                   # ④ 设了必段错误
cd <repo_root>/lw_benchhub                   # ⑤ 配置用相对路径，cwd 必须在这里
```

每一行都有对应的踩坑记录 `[实践]`：

| 行 | 为什么必须这样 | 出处 |
|---|---|---|
| ① `set +u` | conda 的 CUDA 激活脚本引用未绑定变量（如 `NVCC_PREPEND_FLAGS`），`set -u` 下脚本立刻 `unbound variable` 中止。原注释：*Hours were lost on this before changing to `set +u`. Do NOT switch back.* | [`Q14`](troubleshooting.md#q14) / `P14` |
| ④ `unset CUDA_VISIBLE_DEVICES` | Isaac Sim 自行枚举显卡；设了该变量会在**相机初始化时直接 segfault、无 traceback**。⚠️ 此项**不能写进 shell 配置文件**，只在每次运行前执行。`headless_env.sh.example:29-30` 专门写了一条反向约束提醒不要在模板里设它 | [`Q15`](troubleshooting.md#q15) / `P15` |
| ⑤ `cd .../lw_benchhub` | `--env.kwargs` 里的 `config_path` 是**相对路径**（`configs/envhub/example.yml`）。`auto_stage3_benchmark.py:44` 的注释把这条写成了硬约束：*yml 用相对路径，cwd 必须是这里* | `[CODE]` |

> ⚠️ `[CODE]` **唯一的例外**：`pathB_logs/run_pathB.sh:2` 用的是 **`set -u`**，与另外三处及 ① 的硬约束冲突。它是较早期的残留 —— 它当时能跑通，说明该 conda env 在那个时点尚未触发未绑定变量路径；**新写脚本一律用 `set +u`**。

### 2.2 入口点总表

`[CODE]` 按"复现阶段"排列。**★ 标记的是最该先跑通的两条。**

| 阶段 | 入口 | 类型 | 一句话 | 详解 |
|---|---|---|---|---|
| **Stage 1 基线** | ★ `pathB_logs/run_pathB.sh` | bash，无参数 | SmolVLA 10 集闭环评测 —— **"黄金路径"，40% 成功率那次** | §2.3 |
| Stage 2 场景生成 | `generate_scenes_with_live_reach.py` | python，**无 argparse** | LLM 产场景 → 在线可达性闸门 → 闭环重试 | §2.4 |
| Stage 2 可达性验证 | `validate_scene_objects_reach.py <scene.yml>` | python，1 位置参数 + 3 flag | 真启 Isaac Sim 读物体位姿 + cuRobo IK 判可达 | §2.4 |
| Stage 2 批量评测 | `stage2_logs/run_stage2_all.sh` | bash，读 `N_EPISODES` 环境变量（默认 3） | glob 所有 `scene_variation_*.yml` 逐个评测 | §2.5 |
| Stage 2 单场景评测 | `stage2_logs/run_stage2_scene.sh <config_rel> <out_dir>` | bash，2 位置参数 | 单场景 `lerobot-eval`，`video_length=1100` | §2.5 |
| Stage 2 自检 | `verify_stage2.py` | python，无参数 | 汇总 reach 报告 + 视频 + 日志 → `stage2_summary.md` | §2.5 |
| Stage 3 跨本体基准 | `auto_stage3_benchmark.py` | python，4 flag | 4 行矩阵逐行评测 + ffmpeg 对比网格 + 报告 | §2.6 |
| **Stage 4 数据飞轮** | ★ `stage4_flywheel/scripts/generate_policy_demos.py` | python | SmolVLA 闭环自过滤，**唯一可微调路线** | §2.7 |
| Stage 4 数据集导出 | `stage4_flywheel/scripts/build_lerobot_dataset.py` | python | HDF5 → LeRobotDataset | §2.7 |
| Stage 4 脚本 PnP（已证伪） | `stage4_flywheel/scripts/generate_dataset.sh` | bash | cuRobo 6 技能链采集 —— **产出的是失败轨迹，不可微调** | §2.8 |
| 容器化评测（旁支） | `run_eval_docker.sh` | bash | pi0.5 + GR1 microwave，**与 lw_benchhub 主线无关** | §2.9 |
| LLM 小工具 | `deepseek_v4_pro.py "<问题>"` | python CLI | 独立工具，不参与仿真链路 | §3.6 |

### 2.3 ★ Stage 1 / 路径 B：跑通那条 40% 的评测（最该先做的事）

`[CODE]` `pathB_logs/run_pathB.sh` 完整命令（路径已脱敏）：

```bash
set -u        # ⚠️ 原文如此；新写脚本请用 set +u（见 §2.1）
source <user_home>/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source <repo_root>/headless_env.sh
unset CUDA_VISIBLE_DEVICES
cd <repo_root>/lw_benchhub          # 相对 configs 路径才能解析

lerobot-eval \
  --policy.path=LightwheelAI/smolvla-double-piper-pnp \
  --env.type=isaaclab_arena \
  --rename_map='{"observation.images.left_hand_camera_rgb":  "observation.images.left_hand",
                 "observation.images.right_hand_camera_rgb": "observation.images.right_hand",
                 "observation.images.first_person_camera_rgb":"observation.images.first_person"}' \
  --env.hub_path=LightwheelAI/lw_benchhub_env \
  --env.kwargs='{"config_path": "configs/envhub/example.yml"}' \
  --trust_remote_code=true \
  --env.state_keys=joint_pos --env.action_dim=12 --env.state_dim=16 \
  --env.camera_keys=left_hand_camera_rgb,right_hand_camera_rgb,first_person_camera_rgb \
  --env.enable_cameras=true --env.headless=true \
  --env.video=true --env.video_length=200 --env.video_interval=1 \
  --policy.device=cuda \
  --eval.batch_size=1 --eval.n_episodes=10 \
  --output_dir=<path>/eval_outputs_pathB_1
```

**必须理解的四组参数** `[CODE]`：

1. **`state_dim=16` / `action_dim=12`** —— DoublePiper-Abs 专用魔数（16 个 sim 关节；12 = 左右臂各 6 关节 + 双夹爪，`joint4` 跳过）。这组数字在**三个文件里各写死一遍**（`run_pathB.sh:26-28`、`run_stage2_scene.sh:39-41`、`auto_stage3_benchmark.py:34-36`），换本体要改三处。见 §7.1。
2. **三路相机 + `rename_map`** —— 环境侧键名带 `_camera_rgb` 后缀，模型侧不带；`rename_map` 是这层翻译。**少一路或键名错都会静默降级**。
3. **`--env.kwargs` 的 `config_path` 是相对路径** —— 所以必须先 `cd lw_benchhub`（§2.1 ⑤）。
4. **`video_length=200`** —— 在 50 Hz 下只有 **4 秒**，视频看起来像空的。Stage 2 已把它改成 **1100**（录满 22 s 整集），但 Stage 1 与 Stage 3 仍是 200，**这是一处已知的跨文件冲突**，见 §7.2。

**预期输出**：约 **10 分 39 秒**跑完 10 集，日志里 `running_success_rate` 最终为 **40.0**（注意是**百分数**，存成分数要 `/100`）。⚠️ 三个取指标的陷阱见 [`Q21`](troubleshooting.md#q21)：评测 CLI **不写** `eval_info.json`；`running_success_rate` 是百分数；**进程可能在 RuntimeError 后仍 exit 0**，真实退出码只能从日志的 `EXIT_CODE:` 行反推。

> ⚠️ `[CODE]` `run_pathB.sh:40` 只 `echo "EXIT_CODE: $?"` 而**不 `exit $EXIT`**，脚本自身退出码恒为 0。`run_stage2_scene.sh:53-56` 修正了这点（先 `EXIT=$?` 再 `exit $EXIT`）。**不要信 `$?`。**

> `[实践]` 换任务 / 换场景后成功率会**一律降到 0%** —— 这不是接口 bug，是 checkpoint 只在单一任务上微调过的分布外泛化失败，见 [`Q22`](troubleshooting.md#q22)。同任务稳定 40%，跨任务 0%。

### 2.4 Stage 2：LLM 场景生成 + 在线可达性闸门

`[CODE]` 这是本仓库**唯一的编排枢纽**，一条命令串起 LLM、配置生成、Isaac Sim 启动、cuRobo IK：

```bash
# 前奏见 §2.1，另需 source llm_env.sh 注入 OPENAI_API_KEY / OPENAI_BASE_URL / LLM_MODEL
python <repo_root>/generate_scenes_with_live_reach.py       # ⚠️ 无任何命令行参数，全靠常量 + 环境变量
```

**闭环机制** `[CODE]` `generate_scenes_with_live_reach.py`：

```
ask_llm(:174)  ──► LLM 产 N_SCENES=3 个场景 override（JSON 模式，temperature = 0.4 + 0.15×轮次）
    ↓
validate_schema(:115)  ──► 三重校验：① key ∈ MUTABLE_FIELDS 白名单（8 个字段）
                                    ② (layout,task) ∈ layout_task_mapping.csv 合法集
                                    ③ 不在 banned 列表
    ↓
merge_and_save(:129)   ──► 浅合并进 example.yml → 写 lw_benchhub/configs/envhub/generated/scene_variation_{N}.yml
    ↓
run_reach(:136)        ──► bash -c 子进程调 validate_scene_objects_reach.py
    ↓  rc==1（未过闸门）→ 把该 (layout,task) 加入 banned，回灌给 LLM 重来（最多 MAX_ROUNDS=6 轮）
    ↓  rc==0 全通过
写 stage2_logs/final_manifest.json
```

**可达性验证器怎么判"够得到"** `[CODE]` `validate_scene_objects_reach.py`：

```bash
python validate_scene_objects_reach.py <scene.yml> \
    --threshold 0.50 --num-seeds 16 --report-json <out.json>
```

1. `_boot_env(:117)` 调 `lw_benchhub.utils.envhub_utils.export_env_for_envhub()` **真启一个 Isaac Sim**，首次 `reset()` 触发完整场景生成（对 SDK 的 SSL/超时错误重试 3 次、间隔 5 s）。
2. `_dump_scene_poses(:152)` 从 `scene.rigid_objects` 读物体世界位，从 `scene.articulations` 里**按名字含 `piper`/`robot`** 找机器人并把四元数转 yaw。
3. `_world_to_arm_local(:64)` 做变换：绕 +Z 的 yaw 旋转 + 侧向偏移 `±ARM_LATERAL_OFFSET`（**0.15 m**）。
4. `_build_ik_solver(:79)` 用 `piper_curobo.yml` 造 `IKSolver`，`num_seeds=16`、`rotation_threshold=π`（**等于放弃姿态约束**）、关自碰撞、`use_cuda_graph=False`。
5. `_evaluate(:192)` 逐物体在左右臂系各解一次位置 IK，残差 < `POSITION_THRESHOLD`（**0.01 m**）算够到；`reach_ratio` ≥ 0.50 则 PASS。

**退出码语义** `[CODE]` `:20-22`：`0`=通过（**含"无 rigid object → 默认通过"**）、`1`=未过闸门、`≥2`=bug/环境错误。

⚠️ **三个必须知道的顺序/几何前提** `[CODE]`：

| 前提 | 位置 | 后果 |
|---|---|---|
| **必须先 boot Isaac Sim，再建 cuRobo IK** | `main(:233)` 的调用顺序 | 反序会 `cudaErrorIllegalAddress`（分配 USD 纹理时），见 [`Q16`](troubleshooting.md#q16) |
| 三个环境变量必须在 import isaaclab/curobo **之前** `setdefault` | `:37-44`：`ISAAC_DISABLE_OFFSCREEN_KIT_SCREENSHOT=1`、`OMNI_KIT_ACCEPT_EULA=Y`、`SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO` | 注释解释：`isaacsim` 的 `pip_prebundle/` 会 shadow 掉真 `setuptools_scm`，见 [`Q12`](troubleshooting.md#q12) |
| **"双臂"是"单臂 URDF + 写死 ±0.15 m 侧向偏移"近似出来的** | `:47` + `piper_curobo.yml:26`（只有 `joint1..joint6`） | 闸门只保证"位置能到"，**不保证抓取姿态可行**（`rotation_threshold=π`），也**不检测碰撞**（`piper_curobo.yml:13-20` 碰撞体全空） |

### 2.5 Stage 2：批量评测与自检

`[CODE]` 三个脚本靠**约定的产物路径**串联，彼此不 import：

```bash
# ① 批量：glob 所有 scene_variation_*.yml 逐个评测
N_EPISODES=3 bash <repo_root>/stage2_logs/run_stage2_all.sh
#    └─ 内部逐个调 run_stage2_scene.sh <config_rel> <out_dir>
#       产出 stage2_logs/run_stage2_scene{N}.log + eval_outputs_stage2_scene{N}/

# ② 自检：汇总 reach 报告 + 视频 + 日志 → markdown
python <repo_root>/verify_stage2.py     # 无参数
#    产出 stage2_final_deliverables/stage2_summary.md
```

`run_stage2_scene.sh` 相对 `run_pathB.sh` 的**三处改进** `[CODE]`：

| 改进 | 行 | 说明 |
|---|---|---|
| `video_length` 200 → **1100** | `:2-3,46` | 以 50 Hz 录满 22 s 整集。原注释：*原来 200 只有 4 秒，看起来是空的* |
| 跑前清残留 Isaac Sim 进程 | `:14-15` | `pkill -9 -f "isaacsim\|lerobot-eval\|kit/python"` + `sleep 2` |
| 正确传播退出码 | `:53-56` | 先 `EXIT=$?` 再 `exit $EXIT`（`run_pathB.sh:40` 没有这一步） |

⚠️ **两处静默失效**（正是 `L02` 的活样本）`[CODE]`：

`verify_stage2.py` 读 `reach.get("robot_init_pos")` / `robot_init_ori`（`:121-122`）与 `reach.get("task_file")`（`:154`），但 `validate_scene_objects_reach.py:179-184` 写出的键是 **`robot_pose{world_pos, yaw_rad}`**，且**从不写 `task_file`**。→ 报告里这三列**恒为 `?`**，表照渲染、不报错。修法：改 verifier 的键名，或让 validator 补写这些键。

`[推断]` 另有一处隐式契约：`verify_stage2.py` 用 `enumerate(sorted(glob(...)), 1)` 的序号去拼 reach 报告名 / eval 目录名 / 日志名（`:112-114,134`），而 `run_stage2_all.sh:11-15` 用自己的 `idx=$((idx+1))` **独立编号**。两处靠"同一 glob 同一排序"巧合一致，**无任何校验** —— glob 顺序一变就错位。

### 2.6 Stage 3：跨本体基准（`auto_stage3_benchmark.py`，764 行）

```bash
python <repo_root>/auto_stage3_benchmark.py [--dry-run] [--only <label>] [--head-only-rerun] [--abort-on-failure]
```

`[CODE]` 流程：`check_environment(:112)` → `apply_lightwheel_patches(:155)` → 按 **4 行写死的 `MATRIX`（`:64-105`）** 逐行 `generate_scene_yml` / `run_eval` / `parse_metrics` → `write_report(:467)` + `build_comparison_grid(:568)`（ffmpeg `drawtext` + `xstack`/`hstack` 拼对比视频）。

**它与 `lw_benchhub/` 的耦合方式很特别** `[CODE]`：**几乎不当库用，只当数据用** ——

- 只在 `check_environment` 里 `from lw_benchhub import CONFIGS_PATH`（`:127`）**探测 namespace shim 是否可用**（即 §6.2 第 7 项那个补丁是否生效）。
- 静态读 `lw_benchhub/lw_benchhub/utils/monkey_patch.py` 源码，只做 `"def <name>" in src_text` 的**文本包含检查**（`:173-180`）—— 上游改名则此检查静默失配。
- 往 `lw_benchhub/configs/envhub/generated_stage3/` **写** `scene_<label>.yml`（`:45`）。
- `generate_scene_yml(:200)` 用 **5 条行锚正则 `re.subn`** 只覆写 `robot`/`layout`/`task`/`seed`/`episode_length_s`，**任一 pattern 命中 0 次即抛错** —— 这是个正面案例：它不允许静默不生效。

**两个前置校验（跑前先满足）** `[CODE]`：`CUDA_VISIBLE_DEVICES` **必须未设置**（`:119`）；`CONDA_PREFIX` 必须含 `lerobot-arena`（`:122`）；`numpy` **强等于 `1.26.0`**，不等即 RuntimeError（`:116-117`）；GPU 空闲显存阈值写死 20000 MiB（`:146`）。

⚠️ **两个读代码才能发现的行为坑** `[推断]`（仓库内无记录）：

- `:394` 成功率归一化启发式是 `raw_sr > 1.0` 就当百分数除 100 —— **真实成功率恰为 1.0（100%）时会被误判成 1%**。
- `:709-716` `--skip-on-failure` 声明为 `action="store_true", default=True`，该 flag **永远为真**，只能靠 `--abort-on-failure` 关掉。

### 2.7 Stage 4 Phase 1：SmolVLA 自过滤采数（**唯一跑通的采数路线**）★

`[CODE]` `stage4_flywheel/` 下 **48 个脚本**（`git ls-files stage4_flywheel/scripts | wc -l` = 48）**没有单一总控**。存在三个"阶段级"聚合脚本，彼此不调用：`run_phase3.sh`、`run_t2_full.sh`、`run_post_baseline.sh`。真正要照抄的是下面这条：

```bash
# Phase 1：让已微调的 SmolVLA 自己跑，只留成功集
bash <repo_root>/stage4_flywheel/scripts/run_policy_demo_collection.sh
#  └─ 内部：conda activate lerobot-arena；逐 episode 调 generate_policy_demos.py
#     产出 stage4_flywheel/datasets/policy_demos_v3_lerobot/（LeRobot v3 格式）
```

⚠️ **Phase 1 明确"不 source `lerobot_arena_curobo_env.sh`"** `[CODE]` `run_policy_demo_collection.sh:32-50` —— 因为这条路线**不用 cuRobo**（策略直接出动作），source 那个脚本反而会引入 CUDA header 软链等副作用（见 §5.3）。这是本仓库里**唯一**一条故意绕开统一 env 脚本的主线路径。

**实测产出** `[实践]`：29 episodes → **10 成功 = 34.5%**，6527 frames。筛选是**两级**的：单集内 `task_success = last_terminated`（`generate_policy_demos.py:138`），集间只保留 `task_success==True` 的目录再打包。

**三处必须知道的实现细节** `[CODE]`：

| 细节 | 位置 | 为什么重要 |
|---|---|---|
| **PRE-step 也录一帧** | `generate_policy_demos.py:119-122` | 首帧是 reset 后的观测，不是第一次动作后的。数据集帧数 = step 数 **+1** |
| 结束用 `os._exit(0)` **硬退** | `:253-260` | 绕过 Isaac Sim 的 atexit（否则 30 s+ 卡死或段错误）。**副作用：Python 层的 buffer flush 被跳过**，日志末尾可能截断 |
| 缺相机帧被**零填充** | `:100-103` | 某相机该 step 没出图时填全零，**不报错不计数** —— 训练集里会混入黑帧而无人知晓。属 `L02` 型缺陷 |

### 2.8 Stage 4 脚本化 cuRobo PnP（**已证伪，只作反面教材**）

```bash
# 单集脚本化抓放（不推荐照跑）
bash <repo_root>/stage4_flywheel/scripts/run_one_episode.sh <episode_id>   # :1-22
bash <repo_root>/stage4_flywheel/scripts/run_all_episodes.sh               # 批量
```

`[实践]` 结论：**8/8 全部 `TASK_SUCCESS=False`**。两个 Issue 的定位见 [`Q3x` 段](troubleshooting.md) 与 `ai_knowledge.md` §4：

- **Issue A**（已修）：skill 链的 `_step_idx` 未推进。
- **Issue B**（**不可修**）：TCP 定义不一致 —— cuRobo 配置里 `ee_link: gripper_base`（腕部），仿真侧实际抓取点是 `hand_link`，**相差 0.30 m**。改 `ee_link` 会连带 URDF 偏移与工作空间边界一起失效。

⚠️ 三个"证明这条路当时就知道走不通"的代码物证 `[CODE]`：`patch_descend_skill_chain.py` / `patch_piper_adapter_descend.py` / `patch_collision_spheres.py` 三个 Phase 2 补丁脚本，**在自己的 docstring 里就预言了自己无效**。这是 `L01`（"先证伪最便宜的假设"）最直接的代码级证据。另：`max_gripper_force` 实测 **0.000 N**，说明"下降不到位"其实是伪问题 —— 夹爪本来就没出力。

⚠️ **`run_all_episodes.sh:37` 引用了未定义变量 `$EPID_summary`** `[CODE]` —— 断点续跑判断因此永远失败，重跑会从头开始。

### 2.9 容器化评测（旁支，非主线）

`[CODE]` `Dockerfile.eval` + `run_eval_docker.sh` 是**路径 A**（`nvidia/pi05-arena-gr1-microwave`，成功率 0%）时期的产物，**不在主线上**，且有两个不该照抄的地方：

- **3 处 `pip install ... || true`**（`Dockerfile.eval`）—— 依赖装失败被吞掉，镜像"构建成功"但运行时缺包。
- 镜像内是 **cu118**，宿主是 **cu128**，torch/CUDA 不匹配。

---

## 三、核心模块详解

选取 **6 个模块**：它们覆盖了"兼容上游 → 定义任务 → 生成场景并过闸门 → 采数 → 打包 → 求 IK"的完整链条。**其中 M2 是本次唯一从零写的任务本体，M1/M6 是改动最密集的兼容层**。

| # | 模块 | 路径（`<repo_root>/` 起） | 行数 | 性质 |
|---|---|---|---|---|
| M1 | monkey patch 兼容层 | `lw_benchhub/lw_benchhub/utils/monkey_patch.py` | 743 | vendored + **本地改 2 处** |
| M2 | DoublePiper 厨房抓放任务 | `AutoDataGen/source/autosim_examples/autosim_examples/autosim/pipelines/doublepiper_kitchen_pnp/` | 917（4 文件） | **本地原创** |
| M3 | Stage 2 场景生成 + 可达闸门 | `generate_scenes_with_live_reach.py` (273) + `validate_scene_objects_reach.py` (325) | 598 | 本地原创 |
| M4 | Stage 4 Phase 1 策略采数 | `stage4_flywheel/scripts/generate_policy_demos.py` | 260 | 本地原创 |
| M5 | LeRobot 数据集打包 | `stage4_flywheel/scripts/build_policy_demos_dataset.py` (198) + `build_lerobot_dataset.py` (187) + `run_dataset_gen.py` (187) | 572 | 本地原创 |
| M6 | Piper IK 适配（懒加载 stub） | `lw_benchhub/lw_benchhub/utils/pinocchio_ik/piper_ik.py` | 390 | vendored + **本地改 3 处** |

### 3.1 M1：`monkey_patch.py` —— 全栈能跑起来的真正原因

⚠️ **纠错**：`background_knowledge.md` §2.5 与本仓库交接文档均称"9 处 monkey patch"，**实测为 11 处** `[CODE]`：`:696-705` 顺序调用 10 个，`:743` 再调第 11 个。以本节为准。

`[CODE]` 模块是**导入即生效**的（文件末尾直接调用，不是提供 `apply()` 让调用方决定），所以**任何 `import lw_benchhub` 都会打全部补丁**——这也是 §2.6 里 Stage 3 脚本用 `from lw_benchhub import CONFIGS_PATH` 当探针的原因。

| 补丁函数 | 行 | 补什么 |
|---|---|---|
| `patch_reset` | `:21` | `ManagerBasedEnv.reset` 支持按 `env_ids` 局部重置 |
| `patch_configclass` | `:101` | configclass 校验放宽：允许**非字符串 dict key**（`:108`） |
| `patch_recorder_manager_ep_meta` | `:131` | 补 `get_ep_meta` / 覆写 `export_episodes` |
| `patch_recorder_manager_joint_targets` | `:167` | **录制 joint target**（上游只录 state），含 `get_next_joint_target`(`:215`)、`EpisodeData.add`(`:255`)、`pre_export`(`:287`) |
| `patch_step` | `:301` | 覆写 `step`（`:304`）+ `reset_to_check_state`（`:401`）——这是 recorder 能对齐动作/观测的关键 |
| `patch_yaml_load` | `:463` | `cached_safe_load`：给 `yaml.safe_load` 加缓存（**性能**补丁，重复读同一 layout YAML 时明显） |
| `patch_reward_manager` | `:482` | `compute(dt)` 签名对齐 |
| `patch_create_teleop_device` | `:521` | **本地改**（`:525-541`）：eval/inference 不用遥操，缺依赖时**打日志后 `return`**，不再抛异常 |
| `patch_isaaclab_tasks_mdp` | `:594` | 遍历已加载模块（`_patch_module` `:608`）批量替换 mdp 函数；`:650` 兼容延迟导入 |
| `patch_termination_manager` | `:663` | `compute()` 行为对齐（Stage 4 的 `task_success = last_terminated` 依赖它） |
| `patch_xform_prim_view_auto_standardize` | `:708` | **本地新增（第 11 个）**：强制 `XFormPrimView.__init__(validate_xform_ops=False)`（`:730`），绕过 Isaac Sim 5.1 对非标准 xformOp 顺序的硬校验。`:724` 有 IsaacLab 尚未可导入时的 skip 分支 |

**依赖调用关系** `[CODE]`：本模块**只被 `lw_benchhub/__init__.py` 间接触发**（见 §6 第 7 项的 namespace shim），自身 import `isaaclab.*` / `isaacsim.*` / `yaml` / `torch`。它**不 import 本仓库任何其他模块**——单向依赖，所以可以独立读。

### 3.2 M2：`doublepiper_kitchen_pnp/` —— 本次唯一原创的任务本体

`[CODE]` 4 个文件：`doublepiper_kitchen_pnp.py`(713) + `reach_gate.py`(136) + `doublepiper_kitchen_pnp_cfg.py`(62) + `__init__.py`(6)。注册名 `AutoSimPipeline-DoublePiperKitchenPnp-v0`（在 `autosim/__init__.py` 注册，见 §6）。

**主类 `DoublePiperKitchenPnpPipeline(AutoSimPipeline)`**（`:44`）—— 生命周期方法按上游 `AutoSimPipeline` 契约实现：

| 分组 | 方法 | 行 |
|---|---|---|
| 生命周期 | `load_env` / `get_env_extra_info` / `initialize` / `reset_env` / `run` | `:90` `:104` `:126` `:181` `:208` |
| 技能执行 | `execute_skill_sequence`（主循环）/ `_execute_single_skill` / `_check_skill_extra_cfg` | `:235` `:476` `:215` |
| **双臂选择** | `_arm_for_object` | `:641` |
| 规划输入 | `_build_world_state` / `_make_pregrasp_goal(goal, hover_z)` | `:601` `:437` |
| 成功判定 | `_check_task_success` | `:450` |
| 录制 | `enable_dataset_recording` / `reset_episode_record` / `get_episode_record` / `_record_dataset_frame` / `_record_head_view_frame` / `_save_head_view_media` / `_normalize_frames` | `:187` `:191` `:198` `:655` `:648` `:673` `:692` |
| **诊断**（占比很高） | `_log_object_positions` / `_log_ee_vs_bowl` / `_log_curobo_ee` / `_log_diag_summary` | `:321` `:333` `:381` `:414` |

⚠️ 注意四个 `_log_*` 方法合计近 120 行 —— 它们是 §2.8 Issue B（TCP 差 0.30 m）定位过程的**遗留物**，不是任务逻辑。读代码时可跳过。

**`reach_gate.py` 是"可达性判断"的唯一真实现** `[CODE]`：`select_arm_per_object`(`:91`) ← `_solve_single`(`:66`) ← `_build_ik_solver(robot_config_file, curobo_config_path, num_seeds)`(`:43`)，坐标变换在 `_world_to_arm_local`(`:24`)，机器人根位姿从环境读取 `_get_robot_root_pose`(`:82`)。

⚠️ **同一套可达性逻辑在仓库里存在两份近乎复制的实现** `[CODE]`：`reach_gate.py` 与 §3.3 的 `validate_scene_objects_reach.py`（`_world_to_arm_local` / `_build_ik_solver` / `_solve_single` 三个私有函数**同名同义**）。**改一处必须同步改另一处**，无任何共享代码或断言把它们绑在一起。

**依赖调用关系**：`doublepiper_kitchen_pnp.py` → `reach_gate.select_arm_per_object` → cuRobo `IKSolver`；→ `piper_adapter.PiperAbsAdapter`（`:16`，`_apply_reach`(`:55`) / `_apply_grasp`(`:81`) / `set_arm_assignment`(`:43`)）把 skill 输出转成绝对关节目标。入口示例 `AutoDataGen/examples/run_doublepiper_pnp.py`(73 行)。

### 3.3 M3：Stage 2 场景生成 + 可达闸门（两脚本一闭环）

`[CODE]` **两者不 import 彼此**，靠 `subprocess` + JSON 文件通信（这正是 §2.4 那张流程图的实体）。

**`generate_scenes_with_live_reach.py`（273 行，LLM 侧）**：

`main`(`:188`) 循环 ≤ `MAX_ROUNDS=6` 轮 → `ask_llm`(`:174`) 拿 overrides → `validate_schema`(`:115`) 用 `load_legal_combinations`(`:53`) 查合法组合、拒 banned → `merge_and_save`(`:129`) 合并进 `load_template`(`:49`) 的模板 → `run_reach`(`:136`) **起子进程跑 M3 的另一半** → 失败项进 banned 列表下一轮重问 → 全通过则写 `final_manifest.json`。`build_user_prompt`(`:93`) 负责把"合法集合 + 已禁清单"塞进 prompt。

**`validate_scene_objects_reach.py`（325 行，仿真侧）**：

`main`(`:233`) → `_ensure_env`(`:54`，三个 `setdefault`，见 §2.4) → `_boot_env(config_path)`(`:117`，**必须先 boot**) → `_dump_scene_poses`(`:152`) → `_build_ik_solver`(`:79`) → `_evaluate(objects, robot_pose, ik_solver, tdtype)`(`:192`) → 写 JSON 报告（`:179-184` 的键名就是 §2.5 那处静默失效的根因）。退出码 `0/1/≥2`。

### 3.4 M4：`generate_policy_demos.py` —— Phase 1 采数主体

`[CODE]` 260 行，4 个函数，靠 LeRobot 的 `EvalPipelineConfig` 驱动（`main(cfg)` `:182`）：

- `run_one_episode(env, policy, preprocessor, postprocessor, env_preprocessor, env_postprocessor, ...)`(`:85`) —— 单集主循环。**PRE-step 先录一帧**(`:119-122`)；每步 `capture_camera_frame`(`:69`) 取 3 路相机；`task_success = last_terminated`(`:138`)。
- `check_task_success(env, env_id=0)`(`:42`) —— 与 `_check_task_success`（M2 `:450`）**是两套判定**，不共享代码。
- 收尾 `os._exit(0)`(`:253-260`)。

⚠️ 全仓库共有 **6 种成功判定写法** `[实践]`（M2 的 `_check_task_success`、本模块的 `check_task_success` 与 `last_terminated`、`verify_stage2.py` 的日志正则、`parse_baseline_metrics.py` 的 `pc_success` 解析、`auto_stage3_benchmark.py:394` 的百分比启发式）。**跨阶段比较成功率前先确认用的是哪一种。**

### 3.5 M5：数据集打包三件套

`[CODE]` 三个脚本形成"跑 → 存 h5 → 转 LeRobot v3"：

| 脚本 | 关键函数 | 说明 |
|---|---|---|
| `run_dataset_gen.py`(187) | `write_scene_config(template_path, seed, out_path)`(`:46`)、`normalize_camera_frame`(`:63`)、`main`(`:77`) | ⚠️ **模块级就 `AppLauncher`**（`:18-33`，在其余 import 之前）—— 这是 Isaac Sim 的硬要求，**不能挪到 `main` 里** |
| `build_lerobot_dataset.py`(187) | `collect_episodes`(`:49`)、`load_episode`(`:73`)、`main`(`:89`) | 脚本化 PnP 时期的版本 |
| `build_policy_demos_dataset.py`(198) | `_fast_png_save`(`:30`)、`collect_episodes`(`:57`)、`load_episode`(`:80`)、`main`(`:97`) | Phase 1 用的版本。**monkey-patch `PIL.Image.save` 成 `compress_level=1`**（`:30`）以换 IO 速度 |

⚠️ **维度断言写死** `[CODE]`：`assert state_dim == 16 and action_dim == 12`。这两个数字在仓库里**至少出现在 3 个文件**（打包脚本、`run_pathB.sh` 的 `--policy.*_dim`、SmolVLA 配置），**改本体必须三处同步**，否则打包时才炸。

### 3.6 M6：`piper_ik.py` —— "缺 `pinocchio.casadi` 也要能 import"

`[CODE]` 390 行。本地改了 3 处，核心思路是**把"import 期硬失败"改成"调用期才失败"**：

| 改动 | 行 | 内容 |
|---|---|---|
| 拆分 try | `:20-31` | 原本 `import pinocchio` 与 `import pinocchio.casadi` 在同一个 try 里；拆开后前者成功即可 |
| 懒加载 stub | `:56-71` | 缺 casadi 时构造 stub 对象并置 `_is_stub` 标志，**import 成功** |
| stub 感知 `reset()` | `:325-329` | 检查 `_is_stub`，是则跳过，不再 `AttributeError` |

**为什么必须这么改** `[实践]`：conda 装的 `pin`（cmeel 4.0.0）**不带 `pinocchio.casadi`**，而 eval 主线（SmolVLA）根本不用 pinocchio IK——只是 import 链路上会经过它。不改就整条链起不来。详见 [`Q1x` 段](troubleshooting.md) 与 `ai_knowledge.md` §4。

---

## 四、配置系统

`[CODE]` 本仓库**没有统一配置框架**。配置分四条互不相通的轨道，且**同一份语义常在多轨道各存一份副本**——这是本仓库最容易踩的结构性坑。

| 轨道 | 载体 | 谁读 | 特点 |
|---|---|---|---|
| ① 环境变量 | 3 个 `*_env.sh`（**仓库里只有 `.example` 模板**）+ `lerobot_arena_curobo_env.sh` + `autosim_env.sh` | `source` 进 shell | 真文件被 `.gitignore:7-9` 排除，见 §1.3 |
| ② 场景 YAML | `lw_benchhub/configs/envhub/generated*/` + `stage4_flywheel/configs/`、`stage4_flywheel/curriculum/` | eval 命令的 `--env.config_path` | **相对路径**，必须先 `cd lw_benchhub` |
| ③ cuRobo 机器人配置 | 根 `piper_curobo.yml`；`stage4_flywheel/curobo/piper_curobo_{left,right}.yml` | `_build_ik_solver`（M2/M3 各一份） | 见下方 ⚠️ |
| ④ 结果/中间态 JSON | `stage4_flywheel/metrics/`（13 个）、`curriculum/curriculum_manifest.json`、`llm/*.json`、Stage 2 的 `final_manifest.json` + reach 报告 | 下游脚本读回来做决策 | **既是产物又是输入**，无 schema 校验 |

### 4.1 环境变量模板（① 轨）

`[CODE]` **必须先 `cp *.example` 去掉后缀并 `chmod 600` 才能跑任何东西**（见 §2.0）。三个模板声明的变量名如下（**本文只列变量名，不写任何值**，已替换敏感信息）：

| 模板 | 变量 |
|---|---|
| `headless_env.sh.example` | `HEADLESS`、`ENABLE_CAMERAS`、`ACCEPT_EULA`、`OMNI_KIT_ACCEPT_EULA`、`OMNI_KIT_ALLOW_ROOT`、`PRIVACY_CONSENT`、`MUJOCO_GL`、`CUDA_HOME`、`PATH`、`HF_HOME`、**`HF_TOKEN`**、`TORCH_COMPILE_DISABLE`、`TORCHINDUCTOR_DISABLE` |
| `llm_env.sh.example` | `OPENAI_BASE_URL`、**`OPENAI_API_KEY`**、`LLM_MODEL` |
| `deepseek_v4pro_env.sh.example` | `DEEPSEEK_BASE_URL`、**`DEEPSEEK_API_KEY`**、`DEEPSEEK_MODEL` |

⚠️ `lerobot_arena_curobo_env.sh`（**已入 git**，因为不含密钥）**会写文件系统**：它用 `ln -sf` 建 CUDA 头文件软链。它不是纯粹的 `export` 脚本，**重复 source 是幂等的，但在不同 conda 环境下 source 会改错目标**。`[CODE]`

⚠️ `autosim_env.sh` **在整个仓库里没有任何脚本 source 它** `[CODE]` —— 疑似遗留，不要以为它会自动生效。

### 4.2 场景 YAML（② 轨）与 reach gate 的痕迹

`[CODE]` 命名即状态，其中一个文件名本身就是证据：

```
lw_benchhub/configs/envhub/generated/scene_variation_3.yml.rejected_by_reach_gate
```

→ Stage 2 的可达闸门**真的拒过场景**（3 个变体里 1 个被拒），闸门不是装饰。另有 `generated_legacy/` 保留了闸门上线**之前**的 3 个变体，可直接 diff 看闸门改变了什么。

`[CODE]` `generated_stage4/` 与 `stage4_flywheel/configs|curriculum/` **内容重复**（`scene_easy.yml` / `scene_medium.yml` / `scene_hard.yml`、`easy_curriculum.yml` / `medium_curriculum.yml` / `hard_scene.yml` 两边各一份）—— 因为 eval 只认 `lw_benchhub/configs/` 下的相对路径，脚本便把自己 `configs/` 里的副本拷过去。**改了一边不同步另一边，跑的就是旧场景，且不报错。**

课程场景共 **19 个 `scene_{easy,medium,hard}_seed*.yml`**（easy 6 / medium 6 / hard 6 + 3 个无 seed 基准），由 `generate_curriculum.py` + `finalize_curriculum.py` 产出，清单在 `curriculum/curriculum_manifest.json`。

### 4.3 cuRobo 机器人配置（③ 轨）—— "双臂"的真相在这里

⚠️ `[CODE]` 根 `piper_curobo.yml` 的五个要点，**每一个都会影响结论可信度**：

| 项 | 值 | 后果 |
|---|---|---|
| 关节列表 | 只有 `joint1..joint6`（`:26`） | **就是单臂**。所谓双臂靠 `ARM_LATERAL_OFFSET = 0.15` m 写死侧移近似 |
| `ee_link` | `gripper_base`（腕部） | 与仿真实际抓取点 `hand_link` **差 0.30 m** → §2.8 Issue B |
| `rotation_threshold` | `π`（在 `curobo_planner_cfg.py:37-41` 本地改成的） | **姿态约束被完全放开**，IK"成功"不代表抓取姿态可行 |
| 碰撞体 | `:13-20` **全为空** | 可达闸门**不做碰撞检查**，"可达"只是运动学位置可达 |
| 与 `stage4_flywheel/curobo/piper_curobo_{left,right}.yml` | 三份并存 | Stage 4 另立左右两份；**根那份与它们不共享**，改哪份取决于哪条路线 |

### 4.4 结果 JSON（④ 轨）：既是产物又是输入

`[CODE]` 13 个 JSON 里，下面这几个会被下游**当输入读回去**，因此"产物"其实是配置：

| 文件 | 生产者 | 消费者 |
|---|---|---|
| `metrics/baseline/seed_probe.json` | `probe_bowl_seed_inprocess.py` | 课程生成挑 seed |
| `metrics/curriculum_gradient.json` | `run_curriculum_eval.sh` / `parse_baseline_metrics.py` | 人读 + `evaluate_phase1_gates.py` |
| `curriculum/curriculum_manifest.json` | `finalize_curriculum.py` | `validate_curriculum_reach.sh`、eval 脚本 |
| `llm/curriculum_response.json` | `deepseek_v4pro_call.py` | `generate_curriculum.py` 复用（省 LLM 调用） |
| `metrics/doublepiper_joints.json` | `verify_doublepiper_joints.py` | 人读 |

⚠️ **`curriculum_gradient.json` 的实测值不单调** `[实践]`（原文即此三行）：

```json
{"hard_scene": {"success_rate_pct": 40.0},
 "easy_curriculum": {"success_rate_pct": 40.0},
 "medium_curriculum": {"success_rate_pct": 0.0}}
```

→ **medium 比 hard 还差**。这说明"难度分级"没有真正成立（种子间方差压过了难度差），**不要把这三个数当课程有效性的证据**。相关教训见 `ai_knowledge.md` §6。

⚠️ **两个必需输入不在 git 里** `[CODE]`：`stage4_flywheel/datasets/seed_plan.json`（被 `.gitignore` 的 `datasets/` 规则排除）与三个真 `*_env.sh`。换机复现必须自己重建这两样。

---

## 五、依赖与环境

### 5.1 关键版本（本机实测组合）

`[实践]` 这是**唯一验证跑通过的组合**。它不是官方推荐清单，但每一项都被下面 §5.4 的耦合点绑住，**不要单独升级其中任何一项**。

| 组件 | 版本 | 安装形态 |
|---|---|---|
| Isaac Sim | 5.1.0 | pip |
| Isaac Lab | v2.3.2 | vendored 于 `AutoDataGen/dependencies/IsaacLab/`，editable |
| IsaacLab-Arena | `release/0.1.1` | vendored，editable |
| lw_benchhub | 0.1.0 | vendored，editable |
| lerobot | 0.5.1 | vendored，editable |
| lightwheel-sdk | 1.0.3 | pip |
| cuRobo | 0.7.7.post1.dev5 | vendored 于 `AutoDataGen/dependencies/curobo/`，editable，**编译为 `sm_80`** |
| pinocchio (`pin`, cmeel) | 4.0.0 | conda，**不含 `pinocchio.casadi`** → 见 §3.6 |
| cuda-toolkit | 12.8.93 | **conda 环境内**（不是系统级） |

**四个硬锁版本** `[实践]`（写错就报错或静默出错）：

| 包 | 锁定 | 为什么 |
|---|---|---|
| `numpy` | **`==1.26.0`** | `auto_stage3_benchmark.py:116-117` 直接 `RuntimeError` 拦。⚠️ **每次 pip 操作后都要重新确认**——很多包会顺手升到 2.x |
| `warp-lang` | `==1.8.1` | Isaac Lab 2.3.2 对应版本 |
| `qpsolvers` | `==4.8.1` | 差异化控制器依赖 |
| `vuer[all]` | `==0.0.70` | 可视化依赖，新版 API 不兼容 |

### 5.2 打包文件在哪（本仓库没有根级 `requirements.txt`）

⚠️ `[CODE]` **仓库根目录既无 `requirements.txt` 也无 `pyproject.toml`** —— 依赖装配**完全靠人按顺序敲命令**，没有一键复现入口。真正的 packaging 文件全在 vendored 子仓里：

```
AutoDataGen/pyproject.toml                       AutoDataGen 主包
AutoDataGen/source/autosim/pyproject.toml        autosim（任务注册在这条链上）
AutoDataGen/source/autosim_examples/pyproject.toml   ← M2 的 doublepiper 任务在此包内
AutoDataGen/dependencies/curobo/{pyproject.toml,setup.py}
AutoDataGen/dependencies/IsaacLab/environment.yml + 13 个子包 pyproject/setup
IsaacLab-Arena/{pyproject.toml,setup.py}
lerobot/{pyproject.toml,setup.py,requirements-ubuntu.txt}
lw_benchhub/{pyproject.toml,setup.py}  +  lw_benchhub/docker/environment.yml
```

### 5.3 cuRobo 编译：三个必须先设的环境变量

`[实践]` cuRobo 是唯一需要本地编译的重依赖，装之前 export：

| 变量 | 值 | 作用 |
|---|---|---|
| `TORCH_CUDA_ARCH_LIST` | `"8.0"` | 只编本机架构（A100/sm_80）。不设会编全架构，耗时数倍 |
| `MAX_JOBS` | `4` | 并行度；过高会 OOM 被 kill |
| `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO` | 版本号字符串 | ⚠️ 因为 `isaacsim` 的 `pip_prebundle/` 会 **shadow 掉真的 `setuptools_scm`**，不设则版本推导失败。`curobo/__init__.py:53-58` 本地加了短路分支配合它，见 §6 |

`lerobot_arena_curobo_env.sh` 会 `ln -sf` 建 CUDA 头文件软链（见 §4.1 警告）—— 这是为了让 nvcc 在 conda 内找到头文件，**它会改文件系统**。

### 5.4 五个依赖耦合点（"为什么不能升级"的代码级证据）

`[CODE]` 下面每一条都是仓库里**实际改过的代码**在替上游版本打补丁。升级上游 = 这些补丁要么失效、要么冲突：

| # | 耦合点 | 代码位置 |
|---|---|---|
| 1 | Isaac Sim 5.1 的 xformOp 顺序硬校验 | `monkey_patch.py:708-743`（第 11 个补丁） |
| 2 | Isaac Lab 2.3.2 的 `RecorderManager` 不录 joint target | `monkey_patch.py:167-300` |
| 3 | Isaac Lab 2.3.2 configclass 拒绝非字符串 dict key | `monkey_patch.py:101-130` |
| 4 | Arena `0.1.1` 的 ENDPOINT 属性名（`.loader` → `.client`） | `core/tasks/base.py:25-29` |
| 5 | `pin` 4.0.0 缺 `pinocchio.casadi` | `piper_ik.py:20-31,56-71,325-329` |

⚠️ **`AutoDataGen/dependencies/IsaacLab/` 是 vendored 副本**，`pip install -e` 装的就是它。**不要在 conda 里另装一份 isaaclab**，否则 import 到哪一份取决于 `sys.path` 顺序，症状是补丁"有时生效有时不生效"。`[实践]`

### 5.5 运行期环境约束（跑之前必须满足）

`[CODE]` 汇总 §2.1 的判据，按"不满足会怎样"排序：

| 约束 | 不满足的症状 | 交叉引用 |
|---|---|---|
| `set +u`（关闭未定义变量报错） | Isaac Sim 的 setup 脚本引用未定义变量直接退出 | [`Q14`](troubleshooting.md#q14) |
| `unset CUDA_VISIBLE_DEVICES` | Isaac Sim 找不到 GPU / cuRobo 设备错配 | [`Q15`](troubleshooting.md#q15) |
| conda env 名含 `lerobot-arena` | `auto_stage3_benchmark.py:122` 直接拒跑 | — |
| GPU 空闲显存 > 20000 MiB | `auto_stage3_benchmark.py:146` 硬阈值拦 | — |
| 先 boot Isaac Sim 再建 cuRobo IK | `cudaErrorIllegalAddress` | [`Q16`](troubleshooting.md#q16) |
| 三个 `setdefault` 早于 import isaaclab/curobo | `setuptools_scm` 被 shadow / EULA 卡住 | [`Q12`](troubleshooting.md#q12) |
| `cd lw_benchhub` 后再跑 eval | `config_path` 是相对路径，找不到场景 | — |

---

## 六、复现过程中的修改点

### 6.1 归属方法论（为什么不能看 git log）

⚠️ `[CODE]` **本仓库的 git 历史无法回答"哪些是本次改的"** —— 所有 vendored 代码连同改动一起进入了**同一个 initial commit `32a1751`**。因此本章的**唯一可靠方法**是：

```
拿 sources/lw_benchhub/{LW-BenchHub, AutoDataGen} 的上游 clone，
对 lw_benchhub_tour 的对应子树跑 diff -rq，再逐文件 diff -u。
```

**判定规则**（对应本文档头声明的三级证据）：

| diff 结果 | 判定 | 证据级 | 是否计入本章 |
|---|---|---|---|
| 两边都有、内容不同 | **本地修改** | `[CODE]` | ✅ 计入 |
| 只在 tour 有 | **本地新增** | `[CODE]` | ✅ 计入（§6.4） |
| 只在上游有 | **无法区分**"本地删了"还是"上游后来加的" | `[推断]` | ❌ **不计入** |
| 上游 clone 缺失/版本差太远 | 不做任何声明 | — | ❌ 不计入 |

**两处上游 clone 不可用，本章据此放弃声明** `[CODE]`：

- `sources/lw_benchhub/AutoDataGen/dependencies/{curobo,IsaacLab}` 是**未初始化的 submodule（空目录）** → 这两棵树无法 diff。
- `sources/lw_benchhub/IsaacLab-Arena` 在 `main`（HEAD 已到 `Drop uv wheel installation from docs (#1159)`），tour 在 `release/0.1.1` → 实测 **149 文件内容不同 + 285 仅上游有 + 33 仅 tour 有**，是**纯版本落差**，`[推断]`，**本章对 Arena 不作任何改动声明**。

**唯一的例外**：代码里有**自述式补丁注释**时可独立定级 `[CODE]`。本仓库的约定是 `# v5 …` / `# v6 patch: …`（`v5`/`v6` 是本次复现自己的迭代编号），出现即是本地改动的自证。

### 6.2 本地修改清单（diff 确证，共 10 个文件）

`[CODE]` `lw_benchhub/` 子树 **7 个文件**，`AutoDataGen/`（除 `dependencies/`）**3 个文件**：

| # | 文件（`<repo_root>/` 起） | 改动 |
|---|---|---|
| 1 | `lw_benchhub/lw_benchhub/utils/monkey_patch.py` | ① `patch_create_teleop_device`（`:521-541`）改为缺依赖时打日志 `return`，日志原文：*Skipping patch_create_teleop_device (eval/inference does not use it).*（`:540`）② **新增第 11 个补丁 `patch_xform_prim_view_auto_standardize`**（`:708-743`），强制 `validate_xform_ops=False` |
| 2 | `lw_benchhub/lw_benchhub/utils/pinocchio_ik/piper_ik.py` | 三处：拆 try（`:20-31`）、懒加载 stub + `_is_stub`（`:56-71`）、stub 感知 `reset()`（`:325-329`）。见 §3.6 |
| 3 | `lw_benchhub/lw_benchhub/core/tasks/base.py` | **三处**：<br>① `:25-29` `ENDPOINT` 导入加 fallback，注释原文 *lightwheel-sdk >=1.0.x moved ENDPOINT from .loader to .client*<br>② `:222-225` 若自身 `fix_object_pose_cfg is None` 则从 `context` 继承<br>③ `:844,846` 给 `["pos"]` / `["rot"]` 套 `tuple()`（YAML 读出来是 list，下游要 tuple） |
| 4 | `lw_benchhub/lw_benchhub/core/context.py` | `:39` 新增字段 `fix_object_pose_cfg: dict \| None = None` |
| 5 | `lw_benchhub/lw_benchhub/utils/env.py` | `:198` 新增形参、`:250` `context.fix_object_pose_cfg = fix_object_pose_cfg` |
| 6 | `lw_benchhub/lw_benchhub/utils/envhub_utils.py` | ① `:74` 透传 `fix_object_pose_cfg=getattr(cfg, ..., None)`（顺手补了上游漏的逗号）② `:117-128` `export_env_for_envhub(config_path, app_launcher=None)` —— **向后兼容式新增参数**：传了就复用并强制 `cfg.enable_cameras = True`，不传则走原分支 |
| 7 | `lw_benchhub/__init__.py`（**外层**，非包内） | 由上游的 `__import__('pkg_resources').declare_namespace(__name__)` **整文件重写**为 `importlib.util` 影子加载：把内层真包 `spec_from_file_location` 后 `sys.modules[__name__] = _module`。自述注释 `# v5 namespace-collision fix` |
| 8 | `lw_benchhub/.gitignore` | 加 `.omc/`（其余仅行序变化） |
| 9 | `AutoDataGen/source/autosim/autosim/capabilities/motion_planning/curobo/curobo_planner_cfg.py` | `:37` `rotation_threshold: float = 3.141592653589793`（= π） |
| 10 | `AutoDataGen/source/autosim/autosim/capabilities/motion_planning/curobo/curobo_planner.py` | `:4` 引入 `math`；`:89` 传 `rotation_threshold=self.cfg.rotation_threshold`，注释原文：*pi = position-only; small = honor orientation* |

**第 11 项（无 diff，靠自述注释定级 `[CODE]`）**：`AutoDataGen/dependencies/curobo/src/curobo/__init__.py:53-58` —— `# v6 patch: honor PRETEND_VERSION env var BEFORE any setuptools_scm work`，在任何 `setuptools_scm` 逻辑之前短路读 `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO`。配合 §5.3。

### 6.3 一条值得单独看的"贯通链"：`fix_object_pose_cfg`

`[CODE]` 上面第 3–6 项其实是**同一个需求**（"让场景 YAML 能指定物体初始位姿"）在 4 个文件 6 个点上的纵向打通，顺序如下：

```
scene_*.yml  的 fix_object_pose_cfg 段
   │
   ├─ utils/env.py:198        新增形参接住
   ├─ utils/env.py:250        写进 context
   ├─ core/context.py:39      context 上开字段
   ├─ utils/envhub_utils.py:74  从 cfg 透传（getattr 兜底，缺了也不炸）
   ├─ core/tasks/base.py:222-225  task 若没设则从 context 继承
   └─ core/tasks/base.py:844,846   list → tuple，交给 Isaac Lab
```

⚠️ **改动机制上的启示**：这条链**每一环缺一个都会"静默不生效"而不是报错**（`getattr` 有默认值、`is None` 有兜底）。这是 `L02`（静默失效比崩溃更贵）在上游代码里的同构样本 —— 想加类似的贯通参数，务必在最下游加一次断言。

### 6.4 本地新增（原创代码，非修改）

`[CODE]` diff 判定为"只在 tour 有"：

| 新增物 | 行数 | 说明 |
|---|---|---|
| `AutoDataGen/.../autosim/pipelines/doublepiper_kitchen_pnp/` | 917（4 文件） | **本次核心原创**，见 §3.2 |
| `AutoDataGen/.../autosim/action_adapters/piper_adapter.py` + `piper_adapter_cfg.py` | 93 + 14 | 绝对关节目标适配器 |
| `AutoDataGen/.../autosim/decomposers/`（`deepseek_v4pro_decomposer.py` + prompts） | — | 换 DeepSeek 做任务分解 |
| `AutoDataGen/examples/run_doublepiper_pnp.py` | 73 | 单集入口示例 |
| `lw_benchhub/configs/envhub/{generated, generated_legacy, generated_stage3, generated_stage4}/` | 16 个 YAML | 见 §4.2 |

另有 `AutoDataGen/.../autosim_examples/autosim/__init__.py` 被改，用途是**注册** `AutoSimPipeline-DoublePiperKitchenPnp-v0`（列入 §6.2 第 9/10 项之外的第 3 个 AutoDataGen 改动）。

⚠️ 本仓库根目录的 ~127 个本地脚本（`stage4_flywheel/` 100 + 根级 8 + `stage2_logs/`、`pathB_logs/` 等）**全部是本地原创**，不在任何上游里 —— 它们不需要 diff 就能定级。

### 6.5 明确不计入的项（`[推断]`）

`[CODE]` 下列"只在上游有"的路径，**无法区分是本地删的还是上游后加的**，按方法论**不计入改动**：`lw_benchhub/core/models`、`third_party/`、`images/`、`.vscode/`（以及上游 clone 自带的 `.git`、`.omc`）。

同样不计入：`IsaacLab-Arena/` 的全部差异（§6.1）；两棵 `dependencies/` 子树除第 11 项外的全部内容。

### 6.6 与交接文档 / 原理层的偏差修正

⚠️ 本次核对发现如下**必须修正的既有表述**：

| 既有表述 | 出处 | 实测（本文为准） |
|---|---|---|
| "9 处 monkey patch" | `background_knowledge.md` §2.5（旧标题）、本仓库 `CLAUDE.md` | **上游 10 处**（`sources/lw_benchhub/LW-BenchHub/.../monkey_patch.py:681-690`，690 行）、**本机 11 处**（`:696-705` 调 10 个 + `:743` 调第 11 个，743 行；第 11 个是本地新增）。原理层 §2.5 已就地更正 |
| `doublepiper_kitchen_pnp/` 是"改的上游任务" | 交接文档 | **本地原创**，上游无此目录 |
| `core/tasks/base.py` "改了一处" | 交接文档 | **三处**（`:25-29`、`:222-225`、`:844,846`） |
| 内层 `lw_benchhub/lw_benchhub/__init__.py` 被改成 importlib shim | 交接文档 | **不对**。内层与上游**逐字节相同**（2 行，只导出 `CONFIGS_PATH`）；被重写的是**外层** `lw_benchhub/__init__.py` |
| `piper_ik.py` 改动是"绕过 pinocchio" | 交接文档 | 更准确是"把 import 期硬失败推迟成调用期失败"，pinocchio 本体仍导入 |
| 只有一份 IsaacLab | 交接文档隐含 | **两份**：根 `IsaacLab/`（1362 文件）与 `AutoDataGen/dependencies/IsaacLab/`（1857 文件），实测 **973 处差异**，且根那份还带 `apps/isaacsim_4_5`（Isaac Sim 4.5 时代）。详见 §7 |
| Arena 有本地改动 | 交接文档 | **不可断言**，见 §6.1 |

---

## 七、代码中的注意事项

按"会不会让你得出错误结论"排序 —— **静默失效排在崩溃前面**，因为崩溃会自己告诉你。

### 7.1 硬编码宿主路径：79 个文件、326 处

⚠️ `[CODE]` 实测（`git grep -l` / `git grep -o` 计数）：**79 个 tracked 文件、共 326 处**写死了同一个宿主绝对路径前缀（本文统一记作 `<orig_root>`，见 §2.0）。密度最高的：

| 文件 | 处数 |
|---|---|
| `CLAUDE.md`（交接文档本身） | 45 |
| `stage4_flywheel/scripts/verify_stage4.sh` | 12 |
| `stage4_flywheel/scripts/run_phase3.sh` | 12 |
| `auto_stage3_benchmark.py` | 11 |
| `stage4_flywheel/scripts/run_baseline_eval.sh` | 9 |
| `generate_scenes_with_live_reach.py` / `generate_curriculum.py` / `autosim_env.sh` | 各 8 / 8 / 7 |

**后果**：§2.0 说的"开箱不可运行"就是这条。**修法只有两种**：把仓库放到同名路径下（最省事），或全量 `sed` 替换（326 处，要连 `CLAUDE.md` 一起改）。**不要只改你眼前那个脚本** —— 脚本之间靠约定路径通信（§4 的 ④ 轨），改一半会出现"脚本跑通了但读到旧产物"。

### 7.2 静默失效清单（**最危险的一类**）

`[CODE]` 这些地方**不抛异常、不打 error、日志看起来正常**，但结论是错的：

| # | 位置 | 症状 |
|---|---|---|
| 1 | `verify_stage2.py:121-122,154` | 读 `robot_init_pos`/`robot_init_ori`/`task_file`，而 validator 写的是 `robot_pose{world_pos,yaw_rad}` 且从不写 `task_file` → 报告三列**恒为 `?`**（§2.5） |
| 2 | `generate_policy_demos.py:100-103` | 相机缺帧**零填充**，不报错不计数 → 训练集混入黑帧（§2.7） |
| 3 | `run_all_episodes.sh:37` | 引用未定义变量 `$EPID_summary` → 断点续跑判断永远失败，静默从头重跑（§2.8） |
| 4 | `run_lerobot_eval_compare.sh:36` | grep 一个**从未被写入**的日志文件 → 对比结果恒空 |
| 5 | `Dockerfile.eval` | **3 处 `pip install ... \|\| true`** → 依赖装失败被吞，镜像"构建成功"但运行时缺包（§2.9） |
| 6 | `run_pathB.sh:40` | 缺 `exit $EXIT` → **eval 失败也返回 0**，上层以为成功（`run_stage2_scene.sh:53-56` 才修对） |
| 7 | `auto_stage3_benchmark.py:394` | `raw_sr > 1.0` 才当百分数 → **真实 100% 会被读成 1%** |
| 8 | `auto_stage3_benchmark.py:709-716` | `--skip-on-failure` 声明为 `store_true, default=True`，**永真** |
| 9 | `auto_stage3_benchmark.py:173-180` | 用 `"def <name>" in src_text` **文本包含**检查补丁是否存在 → 上游改名即静默失配 |
| 10 | `§6.3` 的 `fix_object_pose_cfg` 贯通链 | 每一环都有 `getattr` 默认值 / `is None` 兜底 → 断链只表现为"位姿没生效" |
| 11 | `verify_stage2.py:112-114,134` vs `run_stage2_all.sh:11-15` | 两处**各自独立编号**，靠"同一 glob 同一排序"巧合对齐，无校验（`[推断]`） |

**读到任何一条结论前先问："产生它的那段代码在上表里吗？"**

### 7.3 两份 IsaacLab（结构级陷阱）

⚠️ `[CODE]` 仓库里 **vendored 了两份 IsaacLab**：

| 位置 | tracked 文件数 | 特征 |
|---|---|---|
| `AutoDataGen/dependencies/IsaacLab/` | 1857 | 带 `AGENTS.md` / `CLAUDE.md` / `docker/Dockerfile.overlay`。**这份才是 `pip install -e` 装的** |
| `IsaacLab/`（仓库根） | 1362 | 带 `apps/isaacsim_4_5/`（Isaac Sim **4.5** 时代遗留） |

实测 `diff -rq` **973 处差异** —— 它们是**两个不同版本**，不是副本。

**为什么这很危险**：`import isaaclab` 解析到哪一份取决于 `sys.path` 顺序与 cwd。症状是 **§6.2 的 monkey patch "有时生效有时不生效"**。判据：根 `IsaacLab/.../curobo_planner_cfg.py:167` 的 `rotation_threshold` 是上游默认 `0.05`，**没有**本次的 π 改动 —— 若你观察到姿态约束仍在生效，说明 import 到了错的那份。**建议：确认无引用后删掉根 `IsaacLab/`（1362 文件的死重量）。**

### 7.4 重复实现与"改一处不够"

⚠️ `[CODE]` 下面每组都是**同一语义存在多份，且无任何机制保证同步**：

| 语义 | 副本 | 风险 |
|---|---|---|
| 可达性 IK 判断 | `reach_gate.py`（`_world_to_arm_local`/`_build_ik_solver`/`_solve_single`）与 `validate_scene_objects_reach.py`（**同名同义三函数**） | 改一处，另一处照旧（§3.2） |
| 成功判定 | **6 种写法**（§3.4） | 跨阶段比成功率会比出假差异 |
| `state_dim=16` / `action_dim=12` | 打包脚本 `assert`、`run_pathB.sh` 的 `--policy.*_dim`、SmolVLA 配置 | 改本体要**三处同步**，否则打包时才炸 |
| 场景 YAML | `generated_stage4/` 与 `stage4_flywheel/{configs,curriculum}/` 各一份 | 改一边不同步，**跑的是旧场景且不报错**（§4.2） |
| cuRobo 机器人配置 | 根 `piper_curobo.yml` + `stage4_flywheel/curobo/piper_curobo_{left,right}.yml` | 改哪份取决于走哪条路线（§4.3） |
| IsaacLab | 两份（§7.3） | import 歧义 |

### 7.5 两代脚本并存

`[实践]` `stage4_flywheel/scripts/` 的 48 个脚本里有**明显两代**：脚本化 cuRobo PnP 时期（`run_one_episode.sh`、`run_all_episodes.sh`、`build_lerobot_dataset.py`、`patch_*.py`、`test_curobo_*.py`）与 Phase 1 SmolVLA 时期（`run_policy_demo_collection.sh`、`generate_policy_demos.py`、`build_policy_demos_dataset.py`）。**前一代已证伪**（§2.8），但文件仍在且命名相近。

**辨认方法**：文件名带 `policy_demo` 的是有效那代；带 `patch_`、`_probe`、`descend` 的是探索残留。另有 4 个以 `_` 开头的私有试验脚本（`_probe_inprocess_test.py`、`_probe_one_seed.py` 等）。

### 7.6 其它单点陷阱

`[CODE]`

- **`run_dataset_gen.py:18-33` 的 `AppLauncher` 必须留在模块级**（在其余 import 之前）。挪进 `main()` 会崩 —— 这是 Isaac Sim 的硬要求，不是风格问题。
- **`generate_policy_demos.py:253-260` 用 `os._exit(0)`** 硬退，跳过 atexit 也跳过 buffer flush → **日志末尾可能被截断**，别把"日志没写完"当成挂死。
- **`autosim_env.sh` 没有任何脚本 source 它**（§4.1）。
- **`deepseek_v4_pro.py` 在仓库里没有任何引用者** `[CODE]`。
- **超时/重试参数散落**：`timeout -k 10 900`、挂死检测 `HANG_THRESHOLD=4`（轮询 `grep -c "scene retry"`，字符串来自 `env_utils.py:1119`）、`pkill -9 -f "[r]un_dataset_gen"`。⚠️ **挂死检测依赖上游日志字符串**，上游改文案即失效。
- **`video_length=200`（`run_pathB.sh`）只录 4 秒**，视频看起来是空的 —— 不是渲染坏了。要看整集用 `1100`（§2.5）。
- **`generate_curriculum.py:41-43` 有反降级守卫**（拒绝把模型降级到弱模型），改 LLM 配置时会被它拦。

---

## 八、与其它三层知识的关联

### 8.1 代码 ↔ 原理层（`background_knowledge.md`）

| 本文章节 | 原理层章节（行号） | 关系 |
|---|---|---|
| §1 代码结构总览 | §3 架构与模块（L512） | 原理层讲上游**应有**的分层；本文讲 vendored monorepo **实际**的样子 |
| §2 入口点与运行方式 | §6 基本使用流程（L1074） | 本文给的是**本机实测跑通的命令**，原理层给的是上游文档式流程 |
| §3.1 monkey patch 11 处 | §2 核心原理（L135）、特别是 §2.5 | ⚠️ **本文纠正原理层旧标题的"9 处"：上游 10 处、本机 11 处**（见 §6.6；原理层 §2.5 已就地更正并回指本节） |
| §3.2 DoublePiper 任务 | §4 关键特性（L773） | 本文是"关键特性"在本机的**具体实现物**，且暴露了"双臂是单臂+偏移近似" |
| §4 配置系统 | §7 常用 API / 接口（L1179） | 原理层讲接口签名；本文讲**配置实际由四条互不相通的轨道承载** |
| §5 依赖与环境 | §5 安装与依赖（L952） | 本文补充**五个耦合点**与"没有根级 requirements.txt"这一事实 |
| §7 注意事项 | §8 已知问题与限制（L1284） | 本文提供 11 条**代码级**静默失效清单，是原理层"已知限制"的机制层补充 |

### 8.2 代码 ↔ 教训层（`ai_knowledge.md` §6 的 `L01`–`L08`）

**每条教训在代码里的物证**——这是本文最该被复用的部分：

| 教训 | 代码物证 | 位置 |
|---|---|---|
| **`L01`** 实现"修复 X"前先量化 X 是否真发生 | `patch_descend_skill_chain.py` / `patch_piper_adapter_descend.py` / `patch_collision_spheres.py` **在自己的 docstring 里预言了自己无效**；`max_gripper_force = 0.000 N` 证明"下降不到位"是伪问题 | §2.8 |
| **`L02`** 写进配置的键必须 grep 到定义处 | `verify_stage2.py:121-122,154` 读的三个键 validator 从不写 → 报告三列恒为 `?` | §2.5、§7.2 #1 |
| **`L03`** 校验器对不同输入给相同输出说明没生效 | 反例（正面案例）：`generate_scene_yml` 的 5 条 `re.subn` **任一命中 0 次即抛错** | §2.6 |
| **`L04`** 环境变量无法中和代码里显式的函数调用 | `curobo_planner.py:89` 显式传 `rotation_threshold=self.cfg.rotation_threshold` → 只能改**配置源头** `curobo_planner_cfg.py:37` | §6.2 #9/#10 |
| **`L05`** 成功判定只能信环境返回的信号 | `generate_policy_demos.py:138` `task_success = last_terminated`（**在 step 返回瞬间捕获**）；对照全仓库 **6 种成功判定写法** | §3.4、§7.4 |
| **`L06`** 静默失效比报错危险 | §7.2 的 **11 条清单**；`fix_object_pose_cfg` 贯通链每环都有兜底 | §6.3、§7.2 |
| **`L07`** 长跑调试三条硬规则 | `timeout -k 10 900`；hang-killer `HANG_THRESHOLD=4` 轮询 `grep -c "scene retry"`；`pkill -9 -f "[r]un_dataset_gen"` 的**方括号技巧** | §7.6 |
| **`L08`** 复用实例前先确认 `reset()` 重置了什么 | `piper_ik.py:325-329` stub 感知 `reset()`；`P31` 的 cuRobo `reset()` **不清 per-batch 累积器**；`P33` 的 skill `_step_idx` 不被 `plan()` 重置 | §3.6、§2.8 |

### 8.3 代码 ↔ 排障层（`troubleshooting.md`）：为现象提供机制解释

| 现象 | 代码级机制 | 本文位置 |
|---|---|---|
| [`Q05`](troubleshooting.md#q05) `cannot import name 'CONFIGS_PATH'` | **外层** `lw_benchhub/__init__.py` 用 `importlib.util` 影子加载内层真包（内层与上游逐字节相同） | §6.2 #7、§6.6 |
| [`Q07`](troubleshooting.md#q07) `pinocchio is required` / `no attribute '_model'` | `piper_ik.py:20-31,56-71,325-329` 三处改动 = "import 期失败推迟到调用期" | §3.6 |
| [`Q08`](troubleshooting.md#q08) `ImportError: ENDPOINT` / `DEVICE_MAP` | `base.py:25-29` 的 try/except fallback；`monkey_patch.py:521-541` 的优雅跳过 | §6.2 #1/#3 |
| [`Q09`](troubleshooting.md#q09) `not a xformable prim with standard transform operations` | **第 11 个补丁** `patch_xform_prim_view_auto_standardize`（`:708-743`）强制 `validate_xform_ops=False` | §3.1、§6.2 #1 |
| [`Q12`](troubleshooting.md#q12) `setuptools-scm was unable to detect version` | `curobo/src/curobo/__init__.py:53-58` 的短路 + 三个 `setdefault` 必须早于 import | §5.3、§6.2 第 11 项、§2.4 |
| [`Q13`](troubleshooting.md#q13) `cuda.h not found` / 编译 OOM | `lerobot_arena_curobo_env.sh` 的 `ln -sf` 建头文件软链；`MAX_JOBS=4`、`TORCH_CUDA_ARCH_LIST="8.0"` | §4.1、§5.3 |
| [`Q14`](troubleshooting.md#q14) 立刻 `unbound variable` | 六行前奏里的 `set +u`；⚠️ `run_pathB.sh:2` 是**唯一的 `set -u` 例外** | §2.1 |
| [`Q15`](troubleshooting.md#q15) 相机初始化直接 segfault | `unset CUDA_VISIBLE_DEVICES`；`auto_stage3_benchmark.py:119` 会主动拒跑 | §2.1、§5.5 |
| [`Q16`](troubleshooting.md#q16) `cudaErrorIllegalAddress` | `validate_scene_objects_reach.py` 中 `_boot_env(:117)` **必须早于** `_build_ik_solver(:79)` 的调用顺序 | §2.4、§3.3 |
| [`Q17`](troubleshooting.md#q17) 视频只有 2 秒 / 只出 10 个视频 | `video_length=200` 只够 4 s；`max_episodes_rendered` 是硬编码 → `run_stage2_scene.sh` 改 1100 | §2.3、§2.5、§7.6 |
| [`Q21`](troubleshooting.md#q21) 取不到成功率 / 退出码骗人 | CLI 不写 `eval_info.json` → 只能 grep `running_success_rate`（**是百分数**）；`run_pathB.sh:40` 缺 `exit $EXIT` | §2.3、§7.2 #6 |
| [`Q22`](troubleshooting.md#q22) 换任务后成功率一律 0% | `run_pathB.sh` 里写死的 `libero-1-1` + 单任务 checkpoint = OOD，不是接口 bug | §2.3 |
| [`Q23`](troubleshooting.md#q23) `gym.NameNotFound` | `validate_schema(:115)` 捕获 → banned 列表 → `MAX_ROUNDS=6` 重问；`scene_variation_3.yml.rejected_by_reach_gate` 是闸门生效的实物 | §2.4、§4.2 |
| [`Q26`](troubleshooting.md#q26) 脚本"在调难度"但难度毫无变化 | 无解析处的自定义键 vs **有消费者**的 `fix_object_pose_cfg` —— 后者的 6 点贯通链见 §6.3 | §6.3 |
| [`Q28`](troubleshooting.md#q28) `scene retry 1/5` 重复上百次 | hang-killer 轮询 `grep -c "scene retry"`（字符串源自 `env_utils.py:1119`）；band 边界 0.260/0.287/0.325/0.385 | §7.6 |
| [`Q29`](troubleshooting.md#q29) 报 `success=True` 但任务没完成 | 全仓库 **6 种成功判定**并存；`_check_task_success(:450)` 与 `check_task_success(:42)` 是**两套不共享的实现** | §3.2、§3.4、§7.4 |
| [`Q31`](troubleshooting.md#q31) cuRobo `shape mismatch` | `reset()` 不清 per-batch 累积器（`motion_gen.py:1395` 一带） | §8.2 `L08` |
| [`Q32`](troubleshooting.md#q32) 碰撞球像没生效 | 根 `piper_curobo.yml:13-20` **碰撞体全为空** → 可达闸门本就不做碰撞检查 | §4.3 |
| [`Q33`](troubleshooting.md#q33) 技能在 `1 steps` 就退出 | skill 实例复用 + `plan()` 不重置 `_step_idx` | §2.8 Issue A |
| [`Q34`](troubleshooting.md#q34) 腕部到位但手指差 0.3 m | `piper_curobo.yml` 的 `ee_link: gripper_base`（腕部）vs 仿真 TCP `hand_link`，差 **0.30 m**；`rotation_threshold=π` 让姿态不参与约束 | §4.3、§2.8 Issue B |
| [`Q35`](troubleshooting.md#q35) 数据生成五连坑 | `generate_policy_demos.py`：PRE-step 录帧(`:119-122`)、`last_terminated`(`:138`)、`os._exit(0)`(`:253-260`) 与 flush；`pkill` 方括号技巧 | §2.7、§3.4、§7.6 |
| [`Q36`](troubleshooting.md#q36) 导出耗时 40 分钟 | `build_policy_demos_dataset.py:30` monkey-patch `PIL.Image.save` 成 `compress_level=1`（**实测几乎无效，瓶颈在 PNG filter**） | §3.5 |

### 8.4 本文推翻或修正的既有结论

⚠️ 按仓库约定，冲突时**以本层为准**（因为本层可在代码中逐行核实）：

1. **"9 处 monkey patch" → 上游 10 处、本机 11 处**（`background_knowledge.md` §2.5 旧标题、tour 仓库 `CLAUDE.md`）。判据：上游 `monkey_patch.py:681-690`（690 行）连调 10 个；本机 `:696-705` + `:743`（743 行）连调 11 个，第 11 个 `patch_xform_prim_view_auto_standardize` 是本地新增。原理层 §2.5 已就地更正并回指本节。
2. **`doublepiper_kitchen_pnp/` 不是改的上游任务，而是本地原创 917 行**（上游 clone 中无此目录）。
3. **`core/tasks/base.py` 改了三处，不是一处**。
4. **内层 `lw_benchhub/lw_benchhub/__init__.py` 未被修改**（与上游逐字节相同）；被重写的是**外层** `lw_benchhub/__init__.py`。`Q05`/`P05` 的描述据此收窄。
5. **IsaacLab 在仓库里有两份**（973 处差异），根 `IsaacLab/` 是 Isaac Sim 4.5 时代遗留 —— 这是"补丁有时不生效"的结构性根因，此前未被记录。
6. **对 `IsaacLab-Arena` 的任何改动声明都不成立**（上游 clone 在 `main`，与 tour 的 `release/0.1.1` 差 149+285+33 个文件，纯版本落差）。
7. **`curriculum_gradient.json` 的三个数不构成"课程有效"的证据**（medium 0% < hard 40%，非单调）。

### 8.5 本文未涉及（`未提及`）

- **根 `IsaacLab/`（1362 文件）与 `lerobot/`（605 文件）的内部实现**：未逐文件核查，仅确认根 `IsaacLab/` 未含本次改动。
- **`AutoDataGen/dependencies/{curobo, IsaacLab}` 除自述补丁外的改动**：上游 submodule 为空目录，**无法 diff，不作声明**。
- **48 个 stage4 脚本中未被 §2.7/§2.8/§7.5 点名的那些**（多为一次性探针与已废弃补丁）：未逐个建档。
- **`lw_benchhub_rl/`、`lw_benchhub_tasks/` 的训练侧代码**：本次复现走的是评测与采数，未触及 RL 训练路径。

---

## 参考

- 上游仓库（`[CODE]` 级证据来源，均在本机 `sources/lw_benchhub/` 下）：`LW-BenchHub`、`AutoDataGen`、`IsaacLab-Arena`
- 本复现仓库：`lw_benchhub_tour`（**10 个提交**，5679 个 tracked 文件，见 §1.1；⚠️ **远端是 public 仓库**，`.gitignore` 是唯一的凭据隔离机制，见 §1.3）
- 同项目其它知识层：
  - [`quickstart.md`](quickstart.md) — 速查层（派生自本层与其余三层，冲突时**以本层为准**）
  - [`background_knowledge.md`](background_knowledge.md) — 原理层（9 章，1478 行）
  - [`ai_knowledge.md`](ai_knowledge.md) — 经验层（8 章，全 `[实践]`，`P01`–`P38` / `D01`–`D17` / `L01`–`L08`）
  - [`troubleshooting.md`](troubleshooting.md) — 排障层（`Q01`–`Q38`）
  - [`00-index.md`](00-index.md) — 项目级章节地图与行号表

> **本文所有敏感信息已替换**：宿主绝对路径 → `<repo_root>` / `<user_home>` / `<path>`；conda 前缀 → `<conda_prefix>`；HF 缓存 → `<hf_cache>`。**凡涉及 API key / token 的（`HF_TOKEN`、`OPENAI_API_KEY`、`DEEPSEEK_API_KEY`），本文只写变量名与所在文件，不写任何值。** 仓库 5679 个 tracked 文件已用强模式正则全量扫描，**无真实密钥落盘**；三个含密钥的 `*_env.sh` 被 `.gitignore:7-9` 排除，且 `git log --all` 确认它们**从未进入任何 ref**。
