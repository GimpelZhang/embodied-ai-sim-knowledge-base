# GE-Sim 2.0 代码知识（复现仓库 `GE-Sim-V2-tour`）

> **本文档描述的对象是本机复现仓库 `GE-Sim-V2-tour`，不是上游本体 `AgibotTech/GE-Sim-V2`。**
> 上游代码在本仓库中以 git submodule `gesim/` 的形式**被引用但不被跟踪**（pin 在某个上游 commit，`git submodule status` 前缀为 `-`，即**未 checkout**）。因此：
> - 凡涉及**上游**实现的结论，证据出自 `sources/ge_sim_v2/GE-Sim-V2/`（另一份独立 clone），或已写在 [`background_knowledge.md`](background_knowledge.md) 中；
> - 凡涉及**编排层**（怎么启动、怎么改参数、怎么落盘、踩过什么坑）的结论，证据出自本仓库自身的 41 个 `.py` / 14 个 `.sh` / 2 个 `.yaml` / 3 个 `.patch`。
>
> **证据等级**：`[CODE]` = 可在本仓库按给出的 `文件:行号` 复核；`[实践]` = 来自复现记录（见 [`ai_knowledge.md`](ai_knowledge.md) / [`troubleshooting.md`](troubleshooting.md)），**不是官方结论**；`[推断]` = 证据不足以定论，已标明理由。
>
> 🔒 **已替换敏感信息**：本文档中仓库根目录一律写 `<repo_root>`（真实值是一个挂载点下的路径），用户家目录写 `<user_home>`，其它主机绝对路径写 `<path>`，比赛网关 IP 写 `<GATEWAY_IP>`，第三方 LLM 端点写 `<MIMO_BASE_URL>`。仓库里确有 **49 个文件、213 处主机绝对路径**（详见 [§7.1](#71-硬编码主机绝对路径49-文件-213-处)），以及一个**已 gitignore 的 `scripts/secrets.env`**（内含 `HF_TOKEN` / `MIMO_API_KEY` / `GITHUB_TOKEN`）——本文档只提文件名，**绝不复制其内容**。

---

## 1. 代码结构总览

### 1.1 一句话定位

本仓库是一个**薄编排层（thin orchestration layer）**：它自己**不含任何模型代码**，全部 ~8.8 k 行都在做「拉起服务 → 喂数据 → 收结果 → 判分 → 出报告 → 自检」，把上游 GE-Sim 2.0 世界模型、openpi/π0.5 策略、Real2Edit2Real 数据生成器和一个外部 VLM 判分器串成 **5 个 Stage 的流水线**。`[CODE]`

| 类别 | 文件数 | 行数 | 说明 |
|---|---|---|---|
| Python (`scripts/*.py`) | 41 | 7830 | 编排、桥接、训练、判分、报告、自检 |
| Shell (`run_stage*.sh` + `scripts/*.sh`) | 14 | 872 | 5 个 Stage 入口 + 3 个环境脚本 + 6 个安装脚本 |
| YAML (`scripts/configs/*.yaml`) | 2 | 149 | 仅 Stage 2 的 R2E2R 批量生成配置 |
| Patch (`patches/*.patch`) | 3 | 332 | 对上游/第三方仓库的 3 处修改（见 [§6](#6-复现过程中的修改点)） |
| 文档 | 2 | 1048 | `README.md` 303 行 + `CLAUDE.md` 745 行 |
| 素材 | 7 | — | `images/overview.png` + 6 个 Stage 演示 GIF |

**没有的东西**（`未发现`，直接影响部署方式，见 [§5](#5-依赖与环境)）：`requirements.txt`、`setup.py`、`pyproject.toml`、`environment.yml`、`Dockerfile`、`tests/`、CI 配置。`[CODE]` 依赖只能照 `CLAUDE.md` 的环境表手装。

### 1.2 目录树

```
<repo_root>/
├── README.md                      # 303 行：五个 Stage 的成果 + 可复制的手工命令
├── CLAUDE.md                      # 745 行：最权威的实现说明书（坑位表 / 协议 / 环境表 / RWR 伪码）
├── LICENSE
├── .gitmodules                    # 唯一子模块：gesim -> github.com/AgibotTech/GE-Sim-V2.git
├── .gitignore                     # 43 行：secrets.env / 重产物 / gesim 内部重路径
│
├── gesim/                         # ⚠️ submodule，pin 在上游某 commit，**本机未 checkout**
│                                  #    Stage 1/3/4/5 全靠 setup_gesim_submodule.sh 初始化并打补丁
│
├── run_stage1.sh   ( 33 行)       # 闭环打通：WM + policy 双服务 → 8 步 rollout → 自检
├── run_stage2.sh   ( 95 行)       # 数据生成：R2E2R 原生批量生成 50 条 lift_box
├── run_stage3.sh   ( 90 行)       # 泛化评测：46 条 episode 批量闭环 + OSR 报告
├── run_stage4.sh   ( 75 行)       # RL 微调：RWR flow-matching 训 π0.5 小头 + 留出集评测
├── run_stage5.sh   (110 行)       # 线上评测：RoboColiseum 反向 WebSocket 隧道 agent
│
├── patches/
│   ├── gesim-disable-sparge-attention.patch   ( 13 行) → 上游 configs/gesim_v2.yaml
│   ├── r2e2r-update-inpaint-model.patch       (226 行) → R2E2R tools/inpaint_utils.py + preprocess_demo.py
│   └── r2e2r-video-render-oom-fix.patch       ( 93 行) → R2E2R videogen/scripts/infer_..._multigpu.py
│
├── images/                        # overview.png + stage1..stage5 六个 GIF（README 引用）
│
└── scripts/                       # 41 .py + 8 .sh，按职责分七组（见下表）
```

### 1.3 `scripts/` 的七组职责

| 组 | 文件 | 作用 |
|---|---|---|
| **环境** | `env.sh` (44)、`r2e2r_env.sh` (25)、`r2e2r_env_wrapper.sh` (76)、`stage5_env.sh` (44) | 路径 / CUDA / conda / 缓存 / 代理策略。**四个脚本的代理策略互相冲突，是本仓库最反直觉的设计**（见 [§7.3](#73-代理策略在-stage-之间是相反的)） |
| **安装** | `setup_gesim_submodule.sh` (44)、`setup_r2e2r.sh` (8)、`setup_r2e2r_env.sh` (108)、`setup_r2e2r_submodule_patch.sh` (51)、`download_checkpoints.py` (61)、`download_checkpoints_v2.py` (146)、`download_r2e2r_weights.py` (112) | 子模块初始化 + 打补丁 + 三个 conda 环境 + 权重下载 |
| **前置检查** | `check_headless.py` (46)、`check_gpu_stage2.py` (129)、`check_r2e2r_env.py` (64)、`check_agibotworld_gate.py` (41)、`preflight_stage2.py` (139) | 无头渲染 / 显存 / 环境包 / HF 门控 |
| **Stage 1–2 主干** | `launch_services.py` (148)、`run_stage1_eval.py` (152)、`run_phase1_debug.py` (207)、`run_phase2_batch.py` (183)、`render_stage2_videos.py` (384) | 双服务拉起 + 闭环 rollout + R2E2R 两阶段生成 + 视频渲染影子目录 |
| **Stage 3 主干** | `convert_r2e2r_to_bundle.py` (389)、`run_stage3_batch_eval.py` (312)、`vlm_reward_client.py` (252) | 数据桥接（含分辨率探测）+ 批量闭环 + 外部 VLM 判分 |
| **Stage 4 主干** | `split_stage4_dataset.py` (204)、`launch_stage4_wm.py` (230)、`openpi_finetune_head.py` (433)、`run_stage4_rl_train.py` (387)、`run_stage4_test_eval.py` (277) | 36/10 划分 + 单服务拉起 + RWR 训练器 + 留出集评测 |
| **Stage 5 主干** | `stage5_adapter.py` (659)、`stage5_policy_client.py` (75)、`stage5_mock_test.py` (218)、`stage5_check_jobs.py` (250)、`stage5_poll_result.py` (107)、`stage5b_submit_jobs.py` (113)、`stage5b_run_agents.sh` (69)、`render_stage5_obs_videos.py` (120) | 反向隧道 agent + 本地策略客户端 + 离线自测 + 作业管理 |
| **报告 / 自检** | `generate_stage3_report.py` (375)、`generate_stage4_report.py` (231)、`generate_stage4_evidence_report.py` (194)、`generate_stage5_report.py` (198)、`generate_stage5b_report.py` (127)、`verify_outputs.py` (60)、`verify_stage2_inputs.py` (257)、`verify_and_report_stage2.py` (205)、`verify_stage3_outputs.py` (114)、`verify_stage4_outputs.py` (93)、`verify_stage5_outputs.py` (84)、`convert_r2e2r_to_bundle.py`(兼) | 每个 Stage 都是「生成报告」+「独立 verify」两步。**verify 脚本里的阈值常与主脚本重复定义**（见 [§7.2](#72-静默失效路径)） |

### 1.4 提交历史形态

`git log --oneline | wc -l` = **21 次提交**，按 Stage 聚簇：从 `8c6a71c`（pin `gesim` 子模块）到 `43baf94`（README 补齐两个 Stage 5 GIF）。`[CODE]` 每个 Stage 大致对应 3–5 次提交（入口脚本 → 主干脚本 → 报告/自检 → README 收尾），**没有分支、没有 tag、没有 revert**。这意味着**无法从 git 历史里读出「失败过哪几版」**——那些信息只在 `CLAUDE.md` 的坑位表和本知识库的 [`ai_knowledge.md`](ai_knowledge.md) 里。`[推断]`

---

## 2. 入口点与运行方式

### 2.1 五个 Stage 入口一览

每个 `run_stageN.sh` 都是**幂等的一键入口**，内部按 `[i/N]` 分步、每步 `tee` 一份日志。**它们不接受任何命令行参数**——要调参就改脚本里的常量或改被调用的 Python 脚本的默认值。`[CODE]`

| 入口 | 步数 | conda 环境 | 依赖的服务 | 主要产物 |
|---|---|---|---|---|
| `run_stage1.sh` | 0–5 | `gesim` | WM `:9000` + policy `:8000` | `outputs_stage1/stage1_eval_report.md` |
| `run_stage2.sh` | 0–6 | `r2e2r` | 无（本地 GPU 推理） | `outputs_stage2/phase2_batch_50/source_0_trans_NNNN/` × 46 |
| `run_stage3.sh` | 0–6 | `gesim` | WM `:9000` + policy `:8000` + 外部 VLM | `<user_home>/stage3_outputs/stage3_generalization_report.md` |
| `run_stage4.sh` | 1–6 | `gesim`（编排）+ `openpi`（训练/评测，用 `conda run`） | **仅** WM `:9000` | `<user_home>/stage4_outputs/stage4_rl_report.md` |
| `run_stage5.sh` | 0–9 | `openpi`（用 `conda run`） | 本地 policy `:8000` + 远端 RoboColiseum 网关 | `<user_home>/stage5_outputs/stage5_robocoliseum_report.md` |

**共同的前两件事**：`set -euo pipefail`，然后 `source scripts/env.sh`（Stage 5 例外，见 §2.4）。Stage 2/3/5 还会先 `bash -n "$0"` 自校验语法。`[CODE]` `run_stage2.sh:10`、`run_stage3.sh:14`

### 2.2 各 Stage 的分步骨架（可直接对照 README 的手工命令）

```bash
# ── Stage 1（33 行）：闭环打通，最短的入口
bash scripts/setup_gesim_submodule.sh          # [0/5] 初始化 submodule + 打 sparge_attention 补丁
conda activate gesim
python scripts/launch_services.py --timeout 600 # [1/5] 拉起 WM(:9000) + policy(:8000)
python scripts/test_mimo_api.py                 # [2/5] 外部 VLM 判分器连通性预检
python scripts/run_stage1_eval.py --steps 8     # [3/5] 8 步闭环 rollout + 评测
# [4/5] kill outputs_stage1/logs/{world_model,policy}.pid
python scripts/verify_outputs.py                # [5/5] 交付物自检

# ── Stage 3（90 行）：批量泛化评测，46 条 episode
export no_proxy="*" NO_PROXY="*"                # ← 载荷性设置，见 §7.3
python scripts/verify_stage2_inputs.py --phase2_dir <repo_root>/outputs_stage2/phase2_batch_50 \
       --out_dir "$OUT_DIR" --expected_count 46
python scripts/launch_services.py --timeout 600
python scripts/convert_r2e2r_to_bundle.py \
       --probe-episode .../source_0_trans_0000 --server http://127.0.0.1:9000   # 分辨率探测
python scripts/run_stage3_batch_eval.py --dataset_dir ... --output_dir "$OUT_DIR" \
       --wm_server http://127.0.0.1:9000 --policy_server ws://127.0.0.1:8000 \
       --max_steps 10 --vis_interval 5 --save_failed_vis
python scripts/generate_stage3_report.py --raw "$OUT_DIR/raw_eval_results.json" --out_dir "$OUT_DIR"
python scripts/verify_stage3_outputs.py --out_dir "$OUT_DIR" --expected_count 46

# ── Stage 4（75 行）：跨环境编排，训练在 openpi 环境里跑
python scripts/split_stage4_dataset.py                        # [1/6] 36 train / 10 test
python scripts/launch_stage4_wm.py start --timeout 240        # [2/6] 只拉 WM，不拉 policy
conda run -n openpi --no-capture-output $OPENPI_ENV_VARS \
  python scripts/run_stage4_rl_train.py --max_iterations 60 --max_steps 10   # [3/6] ~7 min/iter
conda run -n openpi --no-capture-output $OPENPI_ENV_VARS \
  python scripts/run_stage4_test_eval.py --max_steps 10       # [4/6]
python scripts/generate_stage4_report.py                       # [5/6]
python scripts/verify_stage4_outputs.py && python scripts/launch_stage4_wm.py stop   # [6/6]
```

**Stage 4 的跨环境技巧**（本仓库最值得抄的一处工程写法）`[CODE]` `run_stage4.sh:30–33`：世界模型必须在 `gesim` 环境里，π0.5 训练必须在 `openpi` 环境里，两者**不能合并**。做法是把 `PYTHONPATH` 与关键 env var 打包成一个字符串，交给 `conda run ... env <VARS> python ...`：

```bash
PY4="PYTHONPATH=<repo_root>/gesim/openpi_serving:<repo_root>/gesim/src:<repo_root>"
OPENPI_ENV_VARS="env $PY4 XLA_PYTHON_CLIENT_PREALLOCATE=false \
                 XLA_PYTHON_CLIENT_MEM_FRACTION=0.20 no_proxy=* NO_PROXY=*"
```

三段 `PYTHONPATH` 各有用途：`gesim/openpi_serving` 提供 `pi05_gesim`/`openpi`；`gesim/src` 是 `gesim` 包的根（**src-layout**，不加就 `ImportError`，坑 BB）；仓库根让 `scripts.*` 可导入（坑 E）。`[CODE]`

### 2.3 命令行参数（各主干脚本）

| 脚本 | 关键参数（默认值） |
|---|---|
| `launch_services.py` | `--check-only`、`--timeout 600`、`--no-world-model`、`--no-policy` `[CODE]` `:132–135` |
| `run_stage1_eval.py` | `--server http://127.0.0.1:9000`、`--policy ws://127.0.0.1:8000`、`--gesim-dir <硬编码绝对路径>`、`--steps 8`、`--action-horizon 50`、`--fps 16` `[CODE]` `:128–133` |
| `run_phase1_debug.py` | `--output_dir outputs_stage2/phase1_debug`、`--config configs/lift_box.yaml`、`--steps 1234567` `[CODE]` `:104–108` |
| `run_phase2_batch.py` | `--output_dir`、`--config scripts/configs/phase2_batch50.yaml`、`--num_outputs 50` `[CODE]` `:90–94` |
| `run_stage3_batch_eval.py` | `--dataset_dir`、`--output_dir`、`--wm_server`、`--policy_server`、`--vis_interval 5`、`--save_failed_vis/--no-save_failed_vis`（默认 True）、`--max_steps 10`、`--resume`、`--fps 16`、`--action_horizon 50` `[CODE]` `:213–232` |
| `launch_stage4_wm.py` | 子命令 `start --timeout 180` / `stop` / `status` `[CODE]` `:213–218`（**入口脚本传 `--timeout 240`，与默认 180 不一致**） |
| `run_stage4_rl_train.py` | `--max_iterations`、`--max_steps`、`--lr`、`--temp`、`--explore_sigma`、`--smooth_penalty`、`--finetune_mode action_head`、`--resume` `[CODE]` `:242–250`（默认值全在文件顶部 `DEFAULT_*` 常量里，见 [§4.2](#42-python-常量式配置)） |
| `run_stage4_test_eval.py` | `--max_steps`、`--fps`、`--resume`、`--vis_all`、`--out_name` `[CODE]` `:174–179` |
| `stage5_adapter.py` | `--job-uuid`（必填）、`--gateway-url`（回落 `$SIMUBOTIX_GATEWAY_URL`）、`--access-token`（回落 `$CHALLENGE_TOKEN`）、`--agent-id`、`--board instruction|manip`、`--horizon`、`--policy-host 127.0.0.1`、`--policy-port 8000`、`--tag job`、`--out-dir`（回落 `$OUT_STAGE5`）、`--no-record`、`--max-retries 5` `[CODE]` `:582–597` |

### 2.4 环境脚本与环境变量

四个环境脚本，**互不 `source` 对方**（Stage 5 完全不走 `env.sh`）：

| 脚本 | 服务对象 | 关键导出 |
|---|---|---|
| `env.sh` (44) | Stage 1/2/3/4 | `WORK=<repo_root>`、`GESIM_DIR`、`CUDA_HOME=/usr/local/cuda`、`HF_HOME`/`HF_HUB_CACHE`/`TRANSFORMERS_CACHE`/`PIP_CACHE_DIR`/`UV_CACHE_DIR`（全部指向 `<path>/.cache/`）、conda init、`MIMO_BASE_URL=<MIMO_BASE_URL>`、`MIMO_MODEL_NAME`；末尾**可选** `source scripts/secrets.env` |
| `r2e2r_env.sh` (25) | Stage 2 | `R2E2R_DIR=<path>/Real2Edit2Real`、`HF_ENDPOINT=https://hf-mirror.com`、`PYOPENGL_PLATFORM=egl` |
| `r2e2r_env_wrapper.sh` (76) | Stage 2 | 在 `r2e2r` 环境里补 `CC`/`CXX`/`GCC`/`GXX`/`LD_LIBRARY_PATH`/`LIBGL_ALWAYS_SOFTWARE`，供 R2E2R 的 C 扩展与软渲染 |
| `stage5_env.sh` (44) | Stage 5 | `OUT_STAGE5=<user_home>/stage5_outputs`、`STAGE5_ACCESS_FILE=<path>`、`STAGE5_POLICY_WS=ws://127.0.0.1:8000`、`STAGE5_POLICY_HEALTHZ=http://127.0.0.1:8000/healthz`、`STAGE5_POLICY_CKPT=<repo_root>/gesim/checkpoints/pi05_gesim_g01op_test`、`XLA_PYTHON_CLIENT_PREALLOCATE=false`、**`no_proxy="localhost,127.0.0.1,::1"`（注意不是 `*`）** `[CODE]` `stage5_env.sh:29–30` |

Python 侧真正读取的环境变量（按出现次数）`[CODE]`：`OUT_STAGE5`(8)、`CONDA_PREFIX`(4)、`STAGE5_ACCESS_FILE`(3)、`MIMO_API_KEY`(2)、`CUDA_HOME`(2)，其余各 1 次：`WORK`、`STAGE5_GATEWAY_DIRECT`、`STAGE5_BASE_URL`、`STAGE3_TARGET_WH`、`SIMUBOTIX_GATEWAY_URL`、`PYOPENGL_PLATFORM`、`MIMO_TIMEOUT`、`MIMO_MODEL_NAME`、`MIMO_BASE_URL`、`HF_TOKEN_AGIBOT`、`HF_TOKEN`、`CUDA_VISIBLE_DEVICES`、`CHALLENGE_TOKEN`。

**三个"必须在 import 之前设置"的变量**（顺序敏感，设晚了无效）`[CODE]`：
- `XLA_PYTHON_CLIENT_PREALLOCATE=false` —— JAX 默认预占 ~75 % 显存（约 30 G），会把 13 G 的 WM 服务 OOM 掉。`run_stage4.sh:25` 先导出，`run_stage4_rl_train.py:54` 与 `openpi_finetune_head.py:26,39` **再各自兜一次底**，防止有人直接 `python scripts/...` 绕过入口脚本。
- `XLA_PYTHON_CLIENT_MEM_FRACTION=0.20` —— 把 JAX 上限压到 20 %，与 WM 共卡。`run_stage4.sh:26`
- `STAGE3_TARGET_WH` —— 由 `run_stage3.sh:60–63` **根据探测日志动态导出**：若探测发现 518×294 原生分辨率被 WM 拒绝，就 `export STAGE3_TARGET_WH="512,384"`，批量脚本据此在桥接前 resize。这是一个**运行时决定的配置**，不在任何配置文件里。

### 2.5 手工分步运行（README 路径）

`README.md` 给的是**手工命令序列**而不是一键脚本，且**与入口脚本不完全一致**——Stage 5 的报告步在 README 里是 `--tags jobA,jobB`，而 `run_stage5.sh:104` 写的是 `--tags A,B`。**以 README 为准**，原因见 [§7.2](#72-静默失效路径)。`[CODE]`

---

## 3. 核心模块详解

选六个模块，覆盖「拉服务 / 桥数据 / 跑评测 / 判分 / 训模型 / 上线」六件事。

### 3.1 `scripts/launch_services.py`（148 行）— 双服务拉起与就绪探测

**职责**：在 `gesim` 环境里各起一个后台进程——世界模型 HTTP 服务 `:9000` 与 π0.5 策略 WebSocket 服务 `:8000`——然后轮询到就绪为止。Stage 1 与 Stage 3 共用它；**Stage 4 不用它**（见 §3.5）。

| 元素 | 位置 | 说明 |
|---|---|---|
| `WORK` / `GESIM_DIR` / `LOG_DIR` | `:30–32` | **硬编码仓库绝对路径**（`Path("<repo_root>")`），换机必改 `[CODE]` |
| `WM_URL` / `POLICY_URL` | `:33–34` | `http://127.0.0.1:9000` / `ws://127.0.0.1:8000` |
| `WM_CKPT` / `POLICY_CKPT` | `:39–40` | `gesim/checkpoints/gesim_community_v2.0.1_g01op_distill_2B`（**蒸馏权重**）与 `pi05_gesim_g01op_test` |
| `_conda_run(env, cmd, log)` | `:43` | 统一用 `conda run` 起子进程并把 stdout/stderr 重定向到日志 |
| `start_world_model()` / `start_policy()` | `:54` / `:63` | 各自写 `outputs_stage1/logs/{world_model,policy}.pid` |
| `probe_world_model()` / `probe_policy()` | `:80` / `:88` | 前者打 `/healthz`，后者尝试 WS 连接 |
| `wait_ready(timeout, start_wm, start_pol)` | `:99` | 轮询循环；`--timeout` 默认 600 s（模型加载慢） |

**要点**：`.pid` 文件里记录的是 **`conda run` 包装进程的 PID，不是真正的 `gesim.server` 进程**（坑 I）。所以 `run_stage1.sh:26–29` 那段 `kill $(cat *.pid)` **杀不干净显存**——Stage 4 因此专门另写了一个 `launch_stage4_wm.py` 来做真正的进程查找与 GPU 校验。`[CODE]` `launch_stage4_wm.py:11,78,176`

### 3.2 `scripts/convert_r2e2r_to_bundle.py`（389 行）— 数据格式桥 + 分辨率探测

**职责**：把 Stage 2 产出的 R2E2R episode 目录转成世界模型服务能吃的 `EpisodeBundle`（首帧三路 RGB + 相机内外参 + 初始 16 维状态 + 任务文本），并在批量跑之前**探测服务接受哪个分辨率**。

| 元素 | 位置 | 说明 |
|---|---|---|
| `_load_intrinsic` / `_load_extrinsic` | `:87` / `:106` | 读相机参数 |
| `_load_png_chw(path, target_wh)` | `:123` | 读 PNG 并转 CHW；`target_wh=None` 表示保留原生分辨率 |
| `_scale_intrinsic(K, sx, sy)` | `:137` | **resize 后必须同步缩放内参**，否则几何不自洽 |
| `build_bundle(...)` | `:147` | 组装 bundle 主函数 |
| `_assert_bundle_ok(bundle)` | `:278` | 上传前的形状/量纲断言 |
| `_probe(probe_dir, server)` | `:301` | 先试 **518×294**（R2E2R 原生），失败再试 **512×384**（GE-Sim 侧标称分辨率），并在 `:347` 打印一条明确的 NOTE |

**为什么需要探测**：Stage 2 的 R2E2R 渲染出的是 518×294，而 GE-Sim 2.0 的三视角是 **384×512（H×W）**。两者对不上，但**服务端不一定明确报错**，所以这里用「先原生、后回落、把选择写进日志、由入口脚本 `grep` 日志再 `export STAGE3_TARGET_WH`」的方式把结果传给下游（见 §2.4）。`[CODE]`

### 3.3 `scripts/run_stage3_batch_eval.py`（312 行）+ `scripts/vlm_reward_client.py`（252 行）— 批量闭环与判分

#### 3.3.1 批量闭环驱动

| 元素 | 位置 | 说明 |
|---|---|---|
| `_REPO_ROOT` | `:45` | `Path(__file__).resolve().parent.parent` —— **这里用的是相对推导，比 §3.1 的硬编码更健壮**（同一仓库里两种风格并存） |
| `discover_episodes(dataset_dir)` | `:57` | 扫 `source_0_trans_NNNN/`；实际只有 **46** 个且编号**不连续**（R2E2R 有 4 次 cuRobo IK 失败） |
| `run_one_episode(...)` | `:95` | 单条 episode 的完整闭环：bundle → `env.reset` → N × (policy infer → `env.step`) → 判分 |
| `make_error_record(...)` | `:164` | **异常也要落盘成一条记录**，避免"少了几条却说不出为什么" |
| `should_save_visualization(...)` | `:79` | 配合 `--vis_interval 5` 与 `--save_failed_vis`：每 5 条存一次可视化，失败的**一定**存 |
| `parse_wh(s)` | `:204` | 解析 `$STAGE3_TARGET_WH` |
| `_write_results(...)` | `:191` | 每条都增量写 `raw_eval_results.json`，配合 `--resume` 可断点续跑 |

#### 3.3.2 判分客户端（本项目最需要警惕的一段代码）

上游**没有开源 World Judge 奖励模型**，所以 `reward`/`progress` 开箱即 `None`（见 [`background_knowledge.md`](background_knowledge.md) §8）。本仓库自建了一个替身：调用外部 VLM `mimo-v2.5`，让它看 4 帧 head 相机图并返回 JSON `{success, completion_score, reasoning}`。

| 元素 | 位置 | 说明 |
|---|---|---|
| `_NUM_VLM_FRAMES = 4`、`_VLM_TIMEOUT = 45.0` | `:41–42` | 每次调用只送 4 帧、超时 45 s |
| `MiMoRewardClient.__init__` | `:90` | 读 `MIMO_API_KEY` / `MIMO_BASE_URL` / `MIMO_MODEL_NAME` / `MIMO_TIMEOUT` |
| `evaluate(head_frames, task)` | `:99` | 满足上游 `RewardClient` Protocol；**`progress` 是 `np.linspace(0, score, T)` 的人造斜坡，不是真的逐帧进度** `[CODE]` `:110` |
| `evaluate_with_reasoning(...)` | `:117` | 报告用；返回 `judge_source` 字段，取值 `"MiMo-mimo-v2.5 (World Judge)"` 或 `"Heuristic-Fallback (No API Key)"` |
| `_heuristic(...)` | `:217` | **无 key 时的回退**：算相邻帧平均像素差 `avg`，`score = clip(avg/50, 0, 1)`，`success = score >= 0.5`。注释自己写了 "explicitly non-semantic" |
| `_parse_loose_json(text)` | `:235` | 容忍 ```` ``` ```` 代码围栏和多余散文，正则抠出第一个 `{...}` |
| 文件末尾 `assert isinstance(...)` | `:252` | 导入时就校验 Protocol 兼容性 |

⚠️ **两条静默失效路径都在这里**（`[CODE]`，对应 [`troubleshooting.md`](troubleshooting.md) E 类）：

1. **无 API key → 静默降级为帧差**。循环照跑、报告照出，只有 `judge_source` 字段能看出来。这就是 `L01` 审计四件套里"回退计数"那一件必须查的原因。
2. **JSON 解析失败 → 返回 `completion_score=0.0`**（`:209–214`）。这条路径**不改 `judge_source`**，于是"判分器返回了没法解析的东西"与"模型确实做失败了、得 0 分"在报告里**长得一模一样**。Stage 3 一度出现 0 % 假阴性，机制就在这里：**要判断是哪种，唯一办法是把 `reasoning` 原文打出来读一遍**（解析失败时它会是 `"MiMo response parse error: ..."`）。`[CODE]` `:213`

### 3.4 `scripts/openpi_finetune_head.py`（433 行）+ `scripts/run_stage4_rl_train.py`（387 行）— RWR 微调器

上游只发布了**推理**实现，没有训练/蒸馏代码。这两个文件是本仓库最原创的部分：在**不改动上游任何一行**的前提下，用世界模型当环境、用外部 VLM 当奖励，对 π0.5 做 **RWR（Reward-Weighted Regression）**微调。

#### 3.4.1 `openpi_finetune_head.py` —— 模型侧（"怎么算 loss、改哪些参数"）

| 元素 | 位置 | 说明 |
|---|---|---|
| `LIFT_BOX_PROMPT` | `:56` | 任务文本常量，上一行注释写明**绝不能用 `pi05_gesim.DEFAULT_PROMPT`，那仍是 kettle 的文本**（坑 B / 坑 V） |
| `REAL_DIM = 16` / `MODEL_DIM = 32` | `:59–60` | 真实动作 16 维，模型内部 padding 到 32 维——**推理与训练都要对齐这个 padding** |
| `FINETUNE_MODULE_NAMES` | `:65` | `("action_in_proj", "action_out_proj", "time_mlp_in", "time_mlp_out")`；注释说明真实模块名**在 `PI0Pytorch.__init__` 里核对过**，`action_head`/`out_proj` 在动作通路里**根本不存在**（坑 S） |
| `load_pi05_inprocess(...)` | `:71` | **进程内**加载 π0.5，不经 WebSocket——因为梯度过不了 WS（坑 U） |
| `setup_finetune(model, mode)` | `:107` | 冻结全部参数、只解冻上面 4 个模块（默认 `mode="action_head"`）。**可训参数 2.16 M / 8.66 MB** `[实践]` |
| `LoRALinear` + `_inject_lora_action_expert` | `:163` / `:181` | 备选路径：给 action expert 注入 LoRA（`r=16, alpha=32`）。存在是因为 **PEFT 在这套模型上不可用（坑 S）** |
| `_wm_to_model_layout(actions_wm)` | `:215` | 16 维布局重排：WM `[L7, Lg, R7, Rg]` → 模型内部 `[L7, R7, Lg, Rg]`；docstring 注明它是上游 `GesimOutputs.__call__` 的逆 |
| `flow_matching_loss(...)` | `:255` | **核心**：直接调 `model.forward(obs, actions)`，用模型**原生的 flow-matching 回归 loss**，不假设高斯策略（坑 T——所以这不是标准 policy-gradient） |
| `_normalize_actions(...)` | `:341` | 用 checkpoint 自带的 `norm_stats` 归一化（可选分位数） |
| `compute_reward(...)` | `:370` | VLM 分数 + **动作平滑惩罚** |
| `save_small_head_checkpoint` / `load_small_head_checkpoint` | `:407` / `:428` | 只存/只读那 4 个模块（`strict=False`，坑 Y），所以 checkpoint 只有 ~8.7 MB |

#### 3.4.2 `run_stage4_rl_train.py` —— 训练循环侧

顶部常量即默认超参 `[CODE]` `:75–83`：

```python
DEFAULT_MAX_ITERATIONS = 60      DEFAULT_TEMP = 1.0            # RWR softmax 温度
DEFAULT_MAX_STEPS = 10           DEFAULT_EXPLORE_SIGMA = 0.05  # 探索噪声 std（关节空间，WM 布局）
DEFAULT_LR = 2e-4                DEFAULT_SMOOTH_PENALTY = 0.05
CKPT_INTERVAL = 20               BASELINE_DECAY = 0.9          # EMA baseline
GRAD_CLIP = 1.0                  DEVICE = "cuda:0"
```

`rwr_step(...)`（`:182`）的实际算法 `[CODE]`：

```
adv_t   = (R - b) / max(temp, 1e-6)          # 每步共享同一条轨迹的 R
w       = softmax(adv_t)                     # 数值稳定：先减 max
loss    = Σ_t w_t · flow_matching_loss(obs_t, a_t)
backward → clip_grad_norm_(可训参数, 1.0) → optimizer.step()
b       ← 0.9·b + 0.1·R                      # EMA baseline
```

⚠️ **函数自己的 docstring 就承认了一处理论弱点**（`:194–197`，值得引用）："With a single trajectory the softmax is uniform, so this reduces to mean loss × (R−b)"。即**单轨迹时 RWR 权重退化为常数**，softmax 形式只是为了将来支持多轨迹 mini-batch 时能自然推广。所以 Stage 4 观测到的 30 % → 80 % 提升，**在算法上更接近"按轨迹奖励加权的过滤式 BC"，不是完整的 RWR**。`[CODE]` + `[实践]`

其它要点：
- `WM_SERVER = "http://127.0.0.1:9000"`、`OUT_DIR = Path("<user_home>/stage4_outputs")`、`REPO_ROOT = Path("<repo_root>")` 全为**硬编码常量** `[CODE]` `:48,67,72`
- `:42` 有一行注释解释 `sys.path` bootstrap 的原因（坑 E：`python scripts/foo.py` 会把 `scripts/` 而不是仓库根放进 `sys.path[0]`）
- `:265` 在跑之前**断言任务文本必须是 lift_box**（坑 B 的三方对齐：数据集 / 训练器 / 判分器三处的任务文本必须一致）
- `write_curve(...)`（`:222`）把**全部超参连同每轮记录一起写进 `rl_training_curve.json`**——这是本仓库做得最好的一处可复现性设计

### 3.5 `scripts/launch_stage4_wm.py`（230 行）— 为什么要第二个服务启动器

`launch_services.py` 有三个缺陷让它在 Stage 4 不可用，文件头 `:4–18` 逐条写明了 `[CODE]`：

| 问题 | 说明 |
|---|---|
| 会顺带拉起 policy WS 服务 | Stage 4 的 π0.5 是**进程内**加载的（坑 U），多一个 WS 服务只会白占显存 |
| 重试是**无上限** `sleep(5)` 循环、没有 timeout | 服务起不来就永久挂住（坑 C） |
| `.pid` 记的是 `conda run` 包装进程 | `kill` 掉它显存不释放（坑 I） |

对应地它提供 `start` / `stop` / `status` 三个子命令，并做了三件 `launch_services.py` 没做的事：`:62` 显式设 `no_proxy` 绕开本机 `127.0.0.1:10900` 代理；`:78` 用 `_find_real_pids()` 找**真正的 `gesim.server` 子进程**；`:176` 兜底扫一遍残留进程，`stop` 之后还用 `nvidia-smi` 校验显存已释放。`[CODE]`

### 3.6 `scripts/stage5_adapter.py`（659 行）— 反向 WebSocket 隧道 agent

**本层已枚举的脚本里行数最多的一个**（659 行 `[CODE]`；⚠️ 源料并未把"全仓最大单文件"写成结论，只记了各文件行数与"Stage 5 那次提交共 10 文件 1856 行"，故此处只作枚举范围内的比较）。RoboColiseum 评测平台的模型是"平台主动向你的 agent 推观测"，所以本地要跑一个**反向隧道客户端**：连上网关、接收二进制帧、解出观测、问本地策略服务、把动作打包回去。

| 元素 | 位置 | 说明 |
|---|---|---|
| `MAX_SESSION_ID_LEN = 256` | `:77` | 帧头长度上限校验 |
| `encode_data_frame` / `decode_data_frame` | `:80` / `:87` | 私有分帧协议：`[uint32 BE session_id 长度][session_id][msgpack-numpy 载荷]` |
| `_CAMERA_MAP` | `:102` | 平台相机名 → GE-Sim 三视角名（`head` / `hand_left` / `hand_right`） |
| `_decode_image_field(cam)` | `:109` | 解一路图像 |
| `adapt_obs(params)` | `:118` | 平台 JSON-RPC `infer` 参数 → 策略服务输入。`:146` 注释：**prompt 一律透传，绝不在这里塞硬编码 prompt**（T3 / 坑 V） |
| `wm_to_grip_last(wm)` | `:166` | 16 维重排：WM `[L7, Lg, R7, Rg]` → grip-last `[L7, R7, Lg, Rg]` |
| `build_envelope(...)` | `:176` | 打包成平台信封：`left_arm`/`right_arm` 为 `{"kind":"JOINT_ABS","values":[...]}`，`left_effector`/`right_effector` 为一维列表；**全部 `.tolist()`**（T1） |
| `noop_envelope(...)` | `:200` | 出错时的安全回落：不动 |
| `Stage5Handler` | `:218` | 帧处理器；`_record()` 落盘观测帧、`_write_status()` 写状态文件供外部轮询 |
| `State` 枚举 | `:399` | `QUEUED → WARMUP → RUNNING → DRAINING` |
| `TunnelExhausted` | `:406` | 重连次数耗尽（`--max-retries 5`） |
| `TunnelClient` | `:413` | 状态机 + `active_sessions` 集合 + `_inflight` 任务集合（并发多 session） |
| `BOARD_HORIZON` | `:573` | `{"instruction": 50, "spatial": 50, "robust": 50, "manip": 30}` —— **不同榜单的动作 horizon 不同** |
| `WAIST_BOARDS = {"manip"}` | `:574` | 只有 `manip` 榜需要 waist 字段 |

两处值得注意的设计 `[CODE]`：
- **默认直连、显式关代理**（`:437–439`）：`self._proxy = None if os.environ.get("STAGE5_GATEWAY_DIRECT","1") != "0" else True`。注释说明本机 `quickqservice` 代理会干扰长连接（坑 S5-3）。这与 Stage 3/4 的 `no_proxy="*"` 是**同一个问题的两种解法**（见 §7.3）。
- **腰部关节是文档化的 no-op**（`:191–193`）：`g01op` 模型没有 waist 输出，于是把**当前观测到的 waist 值原样 tile 满整个 chunk**。注释直说这是 "documented no-op"。这类"填了值但没有信息"的字段**极易被误读成模型在控腰**。

配套的 `scripts/stage5_policy_client.py`（75 行）只有一个 `Stage5PolicyClient`（`:34`，默认 `127.0.0.1:8000`），其 docstring `:15` 再次强调 **`prompt` 是透传、绝无硬编码回落**（坑 V）——同一条纪律在三个文件里各写了一遍。

#### 3.6.1 线路层参数：**本仓库是这套协议的唯一成文来源**

⚠️ 平台侧的 SKILL 文档**只描述 JSON-RPC 语义，对二进制分帧布局是 `未提及` 的**（见原理层 §9.3.3）。也就是说 `encode_data_frame` / `decode_data_frame` 那套 `[uint32 BE len][session_id][msgpack_numpy payload]` 布局，**在本知识库内只有这份代码可作依据**；换平台版本前必须重新对齐。`[CODE]`

| 参数 | 取值 | 为什么是这个值 |
|---|---|---|
| 隧道 URL | `ws://<GATEWAY_IP>/api/challenge/tunnel?job=<job_uuid>&agent=<agent_id>` | 网关 IP 与网站域名**不是同一个**，不可互换（原理层 §9.3.2） |
| 鉴权头 | `Authorization: Bearer <job_token>` | 双层令牌：`CHALLENGE_TOKEN`（JWT，会过期）换出**按 job 发放且不过期**的 `JOB_TOKEN` |
| `ping_interval` / `ping_timeout` | 20 s / 10 s | 长连接保活；平台侧断线重派有 ~30 s 窗口 |
| `max_size` | `None` | 观测帧带三路图像，默认 1 MB 上限会直接把帧丢掉 |
| 重连 | ≤ 5 次，退避 0.5 s → 30 s | 耗尽抛 `TunnelExhausted`（`:406`） |
| **收到 `drain` 之后不再重连** | 硬规则 | `drain` 是平台宣布本 job 收尾；此后重连会被判成异常连接（坑 S5-2 / `Q38`） |
| 每个 job 挂 2 个 agent | 实测配置 | 平台按 `agent_id` 分派 session；**网关卡死时必须换一个新的 `agent_id` 才会被重新分派**（`P34` / `Q34`） |

> ⚠️ **一处与官方指引相反的取舍** `[实践]`：官方建议"一个进程独占一张 GPU"，本次却让 **4 个 agent 共享同一个 ~10 GB 的策略服务**（省显存、也让 4 条隧道天然共用一份权重）。本次没出问题，但它是**刻意的偏离**，不是照文档做的结果。同一节的 `proxy=None`（`:437–439`）也是这样一条"本地经验覆盖默认行为"的决定——正是它让 Stage 5 免于代理干扰，而 Stage 5b 换用官方 agent 时因为没有这一手而踩了代理坑（`P34` 家族）。

### 3.7 报告 / 自检家族（11 个文件，~1900 行）

每个 Stage 都是**「生成报告」+「独立 verify」两个脚本**，从不合并。这个模式的价值在 Stage 3/4 体现得最清楚：`generate_stage4_evidence_report.py`（194 行）专门产出**可人工复核的证据清单**（含 `:175` 那种直接给出 `vlc <路径>` 的复核命令），而 `verify_stage4_outputs.py`（93 行）只做机器判定。

⚠️ 代价是**阈值在两处各写一遍**——详见 [§7.2](#72-静默失效路径)。

---

## 4. 配置系统

本仓库**没有统一的配置系统**。配置以四种形态散落在四处，优先级和可发现性各不相同——这是使用它时最容易踩空的地方。

### 4.1 形态一：YAML（仅 Stage 2）

只有两个 YAML，都属于 **Real2Edit2Real（R2E2R）**的 Hydra 配置，不是 GE-Sim 的配置：

| 文件 | 行数 | 用途 |
|---|---|---|
| `scripts/configs/phase2_batch50.yaml` | 64 | 驱动 R2E2R 原生批量生成 50 条 `lift_box` |
| `scripts/configs/phase2_video_render.yaml` | 85 | 上者的副本，**只改一个字段**：`output_root` 改成绝对路径 |

`phase2_batch50.yaml` 的关键项 `[CODE]`：

```yaml
_target_: demo_generation.demogen.DemoGen      # Hydra 实例化目标（上游类）
source_name: agibot / task_name: lift_box      # 选 lift_box 是因为它同时有示例数据和 inpaint prompt
confidence_thres: 30
use_manual_parsing_frames: true
parsing_frames:                                # 手工标注的动作分段帧号
  prepare: 30 / right-motion-1: 40 / right-skill-1: 110
  left-motion-1: 250 / left-skill-1: 350 / end: 600
mask_names: {object: box, right_arm: right_arm, left_arm: left_arm, desktop: white desktop}
generation:
  n_gen_per_source: 50      # ← 交付量在这里，不在命令行
  mode: full_random         # R2E2R 原生随机空间增广
  n_grid_obj: 5 / check_multiply: 40
  render_video: false / render_depth: true / render_canny: false
trans_range: {generate: {object: [[-0.2,-0.2,0.0], [0.2,0.2,0.0]]}}   # ← Z 上下界都是 0.0
rot_range:   {generate: {object: [-30, 30]}}                          # 度
relax_thresholds: {object: [0.02,...], desktop_z_thres: 0.02, ee: [0.08,0.08,0.05]}
```

⚠️ **`trans_range` 把 Z 钉死为 0**，所以下游 Stage 3 报告里 **`dz ≡ 0`，Z 轴泛化维度没有任何数据**——`generate_stage3_report.py:204,227` 专门为此写了一段声明。**这不是 bug，是配置决定的**，但很容易被读成"模型在 Z 轴不泛化"。`[CODE]`

`phase2_video_render.yaml` 顶部 25 行注释是一份**完整的问题诊断记录**（本仓库注释质量的代表）：上游 `generate_demo_video.sh:111` 用 `input_root = dirname(output_root)` 推导读路径，而推理脚本会往每个 episode 目录里**回写 mp4 + ~1737 张 JPEG**；渲染时 `/mnt` 只剩 6.6 G，装不下 4–9 G 新产物。解法是把 `output_root` 指向 `<user_home>` 上的**影子目录树**（由 `render_stage2_videos.py` 建成"真目录 + 指向原数据的符号链接"），于是**读走链接、写落新盘**。之所以可行，是因为 `pathlib` 的 `Path(a) / '/abs/b' == '/abs/b'`——**绝对路径操作数赢得 join**。`[CODE]` `phase2_video_render.yaml:1–24`

### 4.2 形态二：Python 常量式配置（Stage 3/4/5 全靠这个）

**没有配置文件**，超参与路径都是模块顶部的大写常量。要改就改源码。主要几处 `[CODE]`：

| 文件:行 | 常量 | 值 |
|---|---|---|
| `run_stage4_rl_train.py:75–83` | `DEFAULT_MAX_ITERATIONS` / `DEFAULT_MAX_STEPS` / `DEFAULT_LR` / `DEFAULT_TEMP` / `DEFAULT_EXPLORE_SIGMA` / `DEFAULT_SMOOTH_PENALTY` / `CKPT_INTERVAL` / `BASELINE_DECAY` / `GRAD_CLIP` | `60` / `10` / `2e-4` / `1.0` / `0.05` / `0.05` / `20` / `0.9` / `1.0` |
| `run_stage4_rl_train.py:48,67,72–73` | `REPO_ROOT` / `OUT_DIR` / `WM_SERVER` / `DEVICE` | 硬编码路径 / `http://127.0.0.1:9000` / `cuda:0` |
| `openpi_finetune_head.py:56,59–60,65,68` | `LIFT_BOX_PROMPT` / `REAL_DIM=16` / `MODEL_DIM=32` / `FINETUNE_MODULE_NAMES` / `DEFAULT_CKPT` | 见 §3.4.1 |
| `split_stage4_dataset.py:37,43` | `LIFT_BOX_TASK` / `TEST_IDS` | **10 个手工指定的测试集 episode ID** |
| `vlm_reward_client.py:41–42` | `_NUM_VLM_FRAMES=4` / `_VLM_TIMEOUT=45.0` | 判分帧数与超时 |
| `stage5_adapter.py:573–574` | `BOARD_HORIZON` / `WAIST_BOARDS` | 各榜单 horizon；只有 `manip` 带 waist |
| `verify_stage3_outputs.py:26–27` | `MIN_VIDEOS=10` / `MIN_VIDEO_BYTES=100*1024` | 自检阈值 |
| `launch_services.py:30–40` | `WORK` / `WM_URL` / `POLICY_URL` / `WM_CKPT` / `POLICY_CKPT` | 硬编码路径与端口 |

⚠️ **`TEST_IDS` 是写死的 10 个 ID，不是随机划分**（`split_stage4_dataset.py:43`）。所以 Stage 4 的"30 % → 80 %"是在**同一组固定留出集**上测的，不同随机种子无从比较。`[CODE]`

### 4.3 形态三：Shell 变量与 env 脚本

见 [§2.4](#24-环境脚本与环境变量)。三条最需要知道的：
- **`EXPECTED_EPS=46` 在 `run_stage3.sh:32`**，通过 `--expected_count` 传下去；但 `verify_stage3_outputs.py:35,91` **自己也写了一个默认 46**（见 §7.2）。
- **`STAGE3_TARGET_WH` 是运行时由日志推导出来的**（`run_stage3.sh:60–63`），任何配置文件里都找不到它。
- **`OUT_STAGE4` / `OUT_STAGE5` 决定产物落在哪**，默认都在 `<user_home>` 而**不是**仓库里（因为挂载盘满了）。所以"跑完了但仓库里什么都没有"是正常现象。

### 4.4 形态四：`scripts/secrets.env`（已 gitignore，本文档不复制其内容）

`.gitignore:1–4` 的第一条规则就是它。`env.sh:3` 有一行注释说明：`MIMO_API_KEY` / `HF_TOKEN` / `GITHUB_TOKEN` **一律不写进 `env.sh`**，而是放在这个被忽略的文件里，由 `env.sh` 末尾或 `run_stage4.sh:22` 显式 `source`。Stage 5 另有一个 `~/.simubotix-challenge.env`（由 `stage5_check_jobs.py` 登录后生成、`run_stage5.sh:61` source），其中的口令**故意不持久化**（`stage5_check_jobs.py:191` 注释）。`[CODE]`

### 4.5 怎么改常见的东西

| 想改什么 | 改哪里 |
|---|---|
| Stage 2 生成条数 | `phase2_batch50.yaml` 的 `generation.n_gen_per_source`，**以及** `run_stage2.sh:79` 的 `--num_outputs`（两处，见 §7.2） |
| 物体扰动范围 / 旋转范围 | `phase2_batch50.yaml` 的 `trans_range` / `rot_range`（**要加 Z 泛化就改 `trans_range` 的第三个分量**） |
| Stage 3 评测多少步 | `run_stage3.sh:71` 的 `--max_steps 10` |
| Stage 3 期望 episode 数 | `run_stage3.sh:32` 的 `EXPECTED_EPS` **和** `verify_stage3_outputs.py:35,91` 的默认值 |
| RL 超参 | `run_stage4_rl_train.py:75–83` 的 `DEFAULT_*`，或运行时传 `--lr/--temp/...` |
| 微调哪些模块 | `openpi_finetune_head.py:65` 的 `FINETUNE_MODULE_NAMES`；或 `--finetune_mode` 切到 LoRA 路径 |
| 训练/测试集划分 | `split_stage4_dataset.py:43` 的 `TEST_IDS` |
| 判分器 / 判分帧数 | `vlm_reward_client.py:41` 与 `MIMO_MODEL_NAME` / `MIMO_BASE_URL` 环境变量 |
| Stage 5 打哪个榜 | `run_stage5.sh:87–88` 的 `run_job jobA instruction _A` / `run_job jobB manip _B`；horizon 由 `stage5_adapter.py:573` 的 `BOARD_HORIZON` 决定 |
| 产物落盘位置 | `stage5_env.sh` 的 `OUT_STAGE5`、`run_stage4.sh:27` 的 `OUT_STAGE4`、`run_stage3.sh:28` 的 `OUT_DIR` |

---

## 5. 依赖与环境

### 5.1 没有依赖清单文件

**`未发现`**：`requirements.txt`、`setup.py`、`pyproject.toml`、`environment.yml`、`Dockerfile`、lock 文件。`[CODE]` 依赖信息**只存在于 `CLAUDE.md` 与 `README.md` 的表格和 `scripts/setup_*.sh` 里**。这意味着换机部署必须照 §5.2 手装，且**没有任何机器可校验的依赖声明**。

### 5.2 三个互相隔离的 conda 环境

| 环境 | Python | 关键版本 | 服务对象 |
|---|---|---|---|
| `gesim` | 3.10 | **torch 2.7.0+cu126**、numpy 1.26.4 | 世界模型服务端 + Stage 1/3 评测编排 `[CODE]` `README.md:283` |
| `openpi` | 3.11 | **torch 2.7.1+cu126**、transformers 4.53.2、jax/flax | π0.5 策略服务 + Stage 4 RWR 训练 `[CODE]` `README.md:284`、`CLAUDE.md:517` |
| `r2e2r` | 3.10 | **CUDA Toolkit 12.1.0（conda nvidia 频道）+ torch 2.5.1+cu121**、cuRobo | Stage 2 的 3D 重建与运动学编辑 `[CODE]` `README.md:285`、`CLAUDE.md:231–236` |

**为什么必须三个而不是一个** `[CODE]` `CLAUDE.md:234–236, 517–522`：
- `r2e2r` 需要 CUDA **12.1**，与系统 CUDA（11.8）和 `gesim` 的 12.6 都不同，靠 conda 频道隔离；
- `openpi` 需要 torch **2.7.1** + jax，而 `gesim` 是 2.7.0；
- Stage 4 的训练器要**同时**用 openpi 的 `create_trained_policy`/`PI0Pytorch` 和 gesim 的 `WorldModelEnv`，解法不是合环境，而是**把 `gesim/src` 挂到 openpi 环境的 `PYTHONPATH` 上**（见 §2.2）。

**`r2e2r` 被显式声明为"创建后只读"** `[CODE]` `CLAUDE.md:234–236`：绝不要往里跑裸 `conda install`（经典 solver 慢到不可用，且 conda-forge 的 gcc 依赖会试图把 CUDA 12.1 升到 13.x）。宿主编译器用**系统 gcc 11.4（`/usr/bin/gcc`）而不是 conda gcc**，这一点写死在 `r2e2r_env_wrapper.sh` 里：`CUDA_HOME=$CONDA_PREFIX`（环境自带的 12.1）+ `CC=/usr/bin/gcc`。

### 5.3 三处 `--no-deps` 补装（每处都对应一个已确诊故障）

这三条是"只读环境"的**唯一三个例外**，每条都是纯 Python 的兼容垫片，**不碰 CUDA/torch** `[CODE]`：

| 环境 | 命令 | 为什么 |
|---|---|---|
| `gesim` | `pip install --no-deps h5py` | `h5py` 只装在 `r2e2r` 里，但 Stage 3 要读 H5（坑 F）。`CLAUDE.md:424–426` 注明"torch 2.7.0+cu126 + numpy 1.26.4 untouched" |
| `openpi` | `pip install --no-deps matplotlib`（+ 其纯 Python 运行依赖 `cycler`/`contourpy`/`kiwisolver`/`pyparsing`/`fonttools`） | gesim 在 import 时就会 `import matplotlib`。`CLAUDE.md:521–523`。**明确不要装 `peft`——坑 S，不可用** |
| `r2e2r` | `pip install --no-deps "setuptools==80.10.2"` | `r2e2r` 自带 `setuptools 83.x`**移除了 `pkg_resources`**，而 `imageio-ffmpeg`（经 `moviepy`）在模块加载时就 `from pkg_resources import resource_filename` → 渲染在**碰到 GPU 之前**就崩（坑 M）。80.10.2 是最后一个带 `pkg_resources` 的版本。`CLAUDE.md:274–276, 315–322` |

### 5.4 系统层前提

- **NVIDIA 驱动绝不动**（`CLAUDE.md:40–41`）：`gesim` 的 torch wheel 自带 CUDA 12.6 运行时，**不依赖系统 CUDA**，所以没有任何理由重装驱动。
- `CUDA_HOME=/usr/local/cuda`（`env.sh`），系统 CUDA 11.8。
- **无头渲染**：`PYOPENGL_PLATFORM=egl`（`r2e2r_env.sh`）、必要时 `LIBGL_ALWAYS_SOFTWARE`（`r2e2r_env_wrapper.sh`）；`check_headless.py` 专门检这个。
- HF 镜像：`HF_ENDPOINT=https://hf-mirror.com`（`r2e2r_env.sh`），缓存统一重定向到 `<path>/.cache/`（`env.sh`）。

### 5.5 子模块与权重

```bash
git clone --recursive <repo>          # gesim 是 submodule，必须 --recursive
bash scripts/setup_gesim_submodule.sh # 幂等：submodule update --init --recursive + 打 sparge_attention 补丁
```

`setup_gesim_submodule.sh:33` 用 `git submodule update --init --recursive`（**`--recursive` 是为了拉 `gesim` 内部嵌套的 `third_party/openpi`**）。权重由三个下载脚本负责：`download_checkpoints.py`(61) / `download_checkpoints_v2.py`(146) / `download_r2e2r_weights.py`(112)。世界模型用的是**蒸馏权重** `gesim_community_v2.0.1_g01op_distill_2B`，策略是 `pi05_gesim_g01op_test`。`[CODE]` `launch_services.py:39–40`

---

## 6. 复现过程中的修改点

### 6.1 上游 GE-Sim 2.0 本体：**只改了一行**

**唯一的上游修改**是 `patches/gesim-disable-sparge-attention.patch`（13 行，其中 4 行是新增注释）`[CODE]`：

```diff
--- a/configs/gesim_v2.yaml
+++ b/configs/gesim_v2.yaml
@@ -23,4 +23,7 @@ distill_sigma_schedule: [1.0, 0.9375, 0.8333, 0.625]
  liger_norm: true
  liger_layernorm: true
  triton_rope: true
-sparge_attention: true
+# sparge_attention requires the spas_sage_attn (SpargeAttn) library which is not
+# on PyPI. Disabled per plan risk #2: the kernel is optional, the model still runs
+# (falling back to F.scaled_dot_product_attention), just slower.
+sparge_attention: false
```

**除此之外，`gesim/` 里的代码基本未改动**——注意本文档的两个证据边界 `[CODE]`：
- 本仓库**不跟踪** `gesim/` 的内容（submodule 未 checkout），所以"没改"这个结论来自**只有一个 patch 文件、且 `setup_gesim_submodule.sh` 只 apply 这一个 patch**；
- **另外三个加速内核开关 `liger_norm` / `liger_layernorm` / `triton_rope` 仍是 `true`**。上游把四个都默认打开，本次复现**只关了一个**（唯一装不上的那个）。这与 [`background_knowledge.md`](background_knowledge.md) §5.4 的建议（首次部署应把四个全关）**不一致**——原理层给的是保守建议，本次实践只关了必须关的那个并跑通了。`[实践]`

patch 被**故意留成未提交状态**（`setup_gesim_submodule.sh:20–22` 注释）：`git status` 会把 `gesim` 显示成 `(modified content)`，这是**预期且正确的**；任何一次裸 `git submodule update` 都会把它冲掉，重跑该脚本即可恢复（幂等：`:37` 先 `grep -q '^sparge_attention: false'`，命中就跳过）。

### 6.2 第三方 Real2Edit2Real：两个 patch

R2E2R 是**普通 clone（不是 submodule）**，放在 `<path>/Real2Edit2Real`。同样用「tracked patch + 幂等 apply 脚本」模式，由 `setup_r2e2r_submodule_patch.sh`（51 行）负责。

#### 6.2.1 `r2e2r-update-inpaint-model.patch`（226 行）— 换掉已下线的图像编辑模型

改 `tools/inpaint_utils.py` 与 `tools/preprocess_demo.py`。核心变更 `[CODE]`：

| 变更 | 说明 |
|---|---|
| 客户端换掉 | 上游用 `volcenginesdk` Ark client + `doubao-seededit-3-0-i2i-250628`（**已废弃**）→ 改用 OpenAI 兼容端点 + `doubao-seedream-5-0-pro-260628` |
| 显式超时与重试 | `OpenAI(timeout=180.0, max_retries=5)`，注释说明"ARK image generation can take ~30-50s…default is no timeout" |
| **分辨率下限适配** | 新模型要求 `size` 写成 `'WIDTHxHEIGHT'`（不接受 `adaptive` 预设）**且面积 ≥ 921600 px（960×960）**。而预处理帧只有 ~518×294，太小 → 按宽高比放大到刚过下限（`scale = (921600/area)**0.5 * 1.05`，取偶数边长），编辑完**再缩回原尺寸**，以保住与 VGGT / 点云的像素对齐 |
| 改用 `b64_json` 而非 `url` | 注释写明：TOS CDN 间歇性不可达（`ConnectionError`/`SSLError`），而 `b64_json` 把图像**内联在 API 响应里**，不需要二次下载。标注 "VERIFIED working" |
| `SIGALRM` 硬超时 + 重试 | 即便如此，ARK API 仍可能挂死，所以额外加一层信号超时 |
| API key 改为读环境变量 | `preprocess_demo.py` 原本是硬编码占位符 → 改成 `os.environ.get("ARK_API_KEY", "")` |

> **patch 的实际效果** `[实践]`：改完之后 **12 次 inpaint 调用全部一次成功、零重试**。四个原始缺陷里，真正的"根因级"修复是 **`b64_json`** —— 它把 CDN 这个外部依赖**整条移除**，而不是给它加重试。凡是能把不可靠依赖去掉的改法，都优于把它包在重试里。
>
> patch 本身**幂等**：靠一个 `doubao-seedream` 标记判断是否已应用，重复 `apply` 不会二次改写。

#### 6.2.2 `r2e2r-video-render-oom-fix.patch`（93 行）— 视频渲染 OOM 修复

改 `videogen/scripts/infer_action_depth_canny_cosmos2_multigpu.py`，四个 hunk `[CODE]`：

| hunk | 内容 |
|---|---|
| `@@ -263` | 新增 `_already_rendered(clip_name)` + `--single_clip`：**断点续跑**（跳过已渲染的 clip）与**单 clip 模式**（配合 `render_stage2_videos.py` 的"每 clip 一个子进程"驱动，让 OS 在进程退出时回收全部内存） |
| `@@ -469` | 在构造 `video_to_save` **之前**显式 `del` 本 clip 的输入张量（`all_depth`/`all_canny`/`all_traj` ~8 GB + `all_c2w`/`all_w2c`/`all_intrinsic` + chunk 循环局部量），然后 `gc.collect()` + `torch.cuda.empty_cache()`。注释算了账：`save_video` 峰值 = `video_list` 4 GB + `rearrange` 拷贝 4 GB + `clamp` 拷贝 4 GB ≈ 12 GB，**叠在那 8 GB 上就会 OOM，即便单 clip、47 GB 预算也不够** |
| `@@ -482` | `del video_list` 后再 `gc.collect()` |
| `@@ -551` | 每个 clip 结束后再清一次，防止 RSS **单调增长**（原本在第 6 个 clip 被 OOM-kill） |

> 注释里有一条值得单独记住的 CPython 细节：**`locals().pop` 对 fast-local 槽位不可靠，必须按名字直接 `del`**，且要用 `try/except NameError` 包住（不同分支上变量可能未赋值）。`[CODE]`

> ⚠️ **这个 patch 的前两版是失败的，值得当反面教材读** `[实践]`：
>
> 1. **第一版**只做「断点续跑 + 保存后 `gc`」—— **在完全相同的位置再次被 SIGKILL**。原因是峰值发生在 `rearrange` 与 `clamp` 的中间拷贝上，那是 `gc` 调用**之前**的事，事后回收救不了。
> 2. **真正生效的是第三版**：在进程内怎么清都不够，改成 **`--single_clip` + 由 `render_stage2_videos.py render_per_clip` 为每个 clip 起一个子进程**，靠 OS 在进程退出时整体回收。代价是**每个 clip 多花约 60 s 重新加载模型**。
>
> 另有两处需要知道的背景：上游把"跳过已存在"那段**注释掉了**（约 `:266`），所以在修好之前**每次重启都会死在同一个 clip 上**；以及本层只能确认 clip `0006` 有完整产出证据，**"46/46 全部渲染成功"在源料中没有直接证据**（`未提及`）。
>
> 教训层面这条对应"内存峰值要按峰值算、不能按稳态算"，以及 `L01` 的审计纪律：**改了之后结果分毫不变 = 变量没起作用**，此时该质疑假设本身而不是加第 N 个补丁。

### 6.3 本仓库自己新增的东西（不是"修改"，是"补齐"）

上游是**推理发行版**：没有训练/蒸馏代码、没有 World Judge 奖励模型、没有评测编排。本仓库补的三块都是净新增：

| 补的东西 | 文件 | 行数 |
|---|---|---|
| **奖励模型替身** —— 用外部 VLM 冒充 World Judge，实现上游的 `RewardClient` Protocol | `vlm_reward_client.py` | 252 |
| **RWR 训练器** —— 在世界模型里对 π0.5 小头做奖励加权回归 | `openpi_finetune_head.py` + `run_stage4_rl_train.py` | 820 |
| **线上评测 agent** —— RoboColiseum 反向 WebSocket 隧道 | `stage5_adapter.py` + 5 个配套脚本 | ~1500 |

### 6.4 与上游 / 与原理层的落差表

| 项 | 原理层（[`background_knowledge.md`](background_knowledge.md)）说法 | 本仓库实际 | 以哪个为准 |
|---|---|---|---|
| 四个加速内核开关 | §5.4 建议**首次部署全部关掉** | **只关了 `sparge_attention`**，另三个保持 `true` 并跑通 | 想省事就按原理层全关；本仓库证明**只关装不上的那个也能跑** `[实践]` |
| `reward` / `progress` | §8 指出开箱即 `None`（World Judge 未开源） | 确认为真，因此自建 VLM 替身 | 一致 |
| 两套 16 维布局 | §7.2 要求走 `types.py` 的 `wm_state_to_policy_state()` | 本仓库**没用上游那个函数**，而是在 `openpi_finetune_head.py:215` 和 `stage5_adapter.py:166` 各自手写了一份重排 | **原理层的做法更稳**；本仓库这样写的代价见 §7.2 |
| 三视角分辨率 384×512 | §2 给出固定值 | Stage 2 数据是 518×294，需要探测 + resize + 同步缩放内参 | 一致（正因固定，才必须桥接） |
| 依赖除 `torch>=2.0` 外无约束 | §5 指出上游几乎不 pin | 本仓库**用三个隔离 conda 环境把版本钉死**（见 §5.2） | 部署照本仓库做 `[实践]` |

---

## 7. 代码中的注意事项

### 7.1 硬编码主机绝对路径（49 文件 213 处）

全仓库（排除 GIF/PNG）**49 个文件、213 处**主机绝对路径 `[CODE]`：

| 路径形态 | 出现次数 | 本文档中的写法 |
|---|---|---|
| `<挂载点>/<仓库名>`（仓库根，位于挂载盘） | 51 | `<repo_root>` |
| `/home/<用户名>/...`（产物目录、`miniconda3`、`r2e2r_videos`） | 95 | `<user_home>` |
| `<挂载点>/<数据盘目录>/...`（conda envs、缓存、`Real2Edit2Real`） | 61 | `<path>` |
| `<挂载点>/<另一个 tour 仓库>/user_access_methods.txt` | 6 | `<path>` |

占比最高的文件：`CLAUDE.md`(41)、`render_stage2_videos.py`(21)、`r2e2r_env_wrapper.sh`(10)、`README.md`(9)、`setup_r2e2r_env.sh`(8)、`phase2_video_render.yaml`(7)、`run_stage3.sh`(7)、`env.sh`(6)、`stage5_env.sh`(5)。

**换机时优先改哪里**：仓库里同时存在**两种**根目录推导风格，且大致按 Stage 分界 `[CODE]`：

| 风格 | 文件数 | 代表 |
|---|---|---|
| ❌ **硬编码常量** `Path("<repo_root>")` | **14 个文件 / 15 处** | `launch_services.py:30`、`run_stage4_rl_train.py:48`、`launch_stage4_wm.py:39`、`run_stage4_test_eval.py:31`、`generate_stage4_report.py:24`、`verify_stage4_outputs.py:24`、`openpi_finetune_head.py:68`、`render_stage2_videos.py:55–56`、`download_checkpoints{,_v2}.py`、`download_r2e2r_weights.py:30`、`run_stage1_eval.py:130`（在 `--gesim-dir` 的**默认值**里）、`verify_stage2_inputs.py:213`、`run_stage3_batch_eval.py:215`（在 `--dataset_dir` 的**默认值**里） |
| ✅ **相对推导** `Path(__file__).resolve().parent.parent` | 8 个文件 | 全部 Stage 5 脚本 + `run_stage3_batch_eval.py:45`、`split_stage4_dataset.py:31` |

⚠️ **`run_stage3_batch_eval.py` 两种风格并存**：`:45` 用相对推导定义 `_REPO_ROOT`，但 `:215` 的 `--dataset_dir` **默认值又写了绝对路径**。所以"改了 `_REPO_ROOT` 就万事大吉"是错的——**argparse 的默认值也是硬编码路径的藏身处**，共 3 处（`run_stage1_eval.py:130`、`verify_stage2_inputs.py:213`、`run_stage3_batch_eval.py:215`）。

四个 env 脚本里还有一处 `run_stage5.sh` 独有的问题：它 `cd "$(dirname "$0")"`（`:17`，**正确做法**），但同一文件 `:38,52,70` 仍硬编码 `<user_home>/miniconda3/bin/conda`，`:41` 硬编码 `<repo_root>/gesim/openpi_serving`。而 `run_stage1/2/3/4.sh` 则是 **`source <repo_root>/scripts/env.sh`** 直接写死绝对路径（`run_stage1.sh:4`、`run_stage2.sh:13`、`run_stage3.sh:17`；`run_stage4.sh:18` 是 `cd <repo_root>` 后再 `source scripts/env.sh`）。`[CODE]`

### 7.2 静默失效路径

**这一节是本文档最该先读的部分**。以下问题的共同形态是：**不报错、日志照打、结果不对**。

| # | 现象 | 机制 | 位置 |
|---|---|---|---|
| **S1** | 判分全 0，看起来"模型完全不行" | 判分器 JSON 解析失败时返回 `completion_score=0.0`，且**不修改 `judge_source`**——与"真的得 0 分"在报告里长得一样。唯一区分办法：读 `reasoning` 原文（会是 `"MiMo response parse error: ..."`） | `vlm_reward_client.py:209–214` `[CODE]` |
| **S2** | 分数是随机的、和任务毫无关系 | **没设 `MIMO_API_KEY` 就静默降级为帧差启发式**（`score = clip(mean_abs_frame_diff/50, 0, 1)`，注释自称 "explicitly non-semantic"）。只有 `judge_source == "Heuristic-Fallback (No API Key)"` 能看出来 | `vlm_reward_client.py:217–232`、`:117–133` `[CODE]` |
| **S3** | **两套 16 维动作布局用混** | 世界模型侧 `[L7臂, L夹爪, R7臂, R夹爪]`；模型内部 / 平台信封侧 `[L7臂, R7臂, L夹爪, R夹爪]`。**用错不报错**（维度一样），只是行为错。本仓库把同一段重排**手写了两遍、名字还不同**：`_wm_to_model_layout()` 与 `wm_to_grip_last()`，逻辑逐行相同 | `openpi_finetune_head.py:215–231`、`stage5_adapter.py:166–174` `[CODE]` |
| **S4** | 任务文本用的是 kettle（水壶）而不是 lift_box | 上游 `pi05_gesim.DEFAULT_PROMPT` **仍是 kettle 文本**（坑 B/V）。仓库在**四处**各写了一遍"绝不要用它"的告警，并把 `lift_box` 文本硬编码成常量——但这个常量本身**又在两个文件里各写了一份**（`LIFT_BOX_PROMPT` vs `LIFT_BOX_TASK`，字符串相同、名字不同），改一处不会同步另一处 | `openpi_finetune_head.py:55–56`、`split_stage4_dataset.py:36–37`、`stage5_adapter.py:146`、`stage5_policy_client.py:15` `[CODE]` |
| **S5** | `kill $(cat *.pid)` 之后显存没释放 | `.pid` 里记的是 **`conda run` 包装进程**的 PID，不是真正的 `gesim.server`（坑 I）。`run_stage1.sh:26–29` 就是这样杀的 | `launch_services.py`、对照 `launch_stage4_wm.py:11,78,176` `[CODE]` |
| **S6** | Stage 5 报告是空的 | `run_stage5.sh:104` 传 `--tags A,B`，而 poller 写出的文件名是 `final_jobA.json`/`final_jobB.json`（`stage5_poll_result.py:95` 用 `--tag`，入口脚本传的是 `jobA`/`jobB`）。报告脚本的 argparse **默认值是正确的 `jobA,jobB`**，README 与 `CLAUDE.md:700` 给的也是 `jobA,jobB`——**只有入口脚本那一行是错的**。**手工分步跑（照 README）没问题，一键跑会拿不到任何 job** | `run_stage5.sh:104` vs `generate_stage5_report.py:97,110`、`stage5_poll_result.py:95` `[CODE]` |
| **S7** | 改了阈值但 verify 判定没变（或反之） | **阈值在主脚本和 verify 脚本里各写一遍**：`46` 在 `run_stage3.sh:32` 与 `verify_stage3_outputs.py:35,91`；`36`/`10` 在 `split_stage4_dataset.py:43`（`TEST_IDS`）与 `verify_stage4_outputs.py:66–67`（写死的 `== 36` / `== 10`）；`50` 在 `phase2_batch50.yaml`（`n_gen_per_source`）、`run_stage2.sh:79`（`--num_outputs`）与 `run_phase2_batch.py:94`（默认值）三处 | 见左栏 `[CODE]` |
| **S8** | `launch_stage4_wm.py` 的超时和你以为的不一样 | argparse 默认 `--timeout 180`，但 `run_stage4.sh:48` 传的是 `240` | `launch_stage4_wm.py:216` vs `run_stage4.sh:48` `[CODE]` |
| **S9** | RL"跑起来了"但权重加权其实是常数 | 单轨迹时 RWR 的 softmax 权重退化为均匀分布，等价于 `mean_loss × (R − b)`——**函数 docstring 自己写明了这一点**。所以观测到的提升更接近"按轨迹奖励加权的过滤式 BC" | `run_stage4_rl_train.py:194–197` `[CODE]` |
| **S10** | 以为模型在控制腰部 | `manip` 榜要求 waist 字段，但 `g01op` 模型**没有 waist 输出**，代码把**当前观测的 waist 值 tile 满整个 chunk**，注释直称 "documented no-op" | `stage5_adapter.py:191–193` `[CODE]` |
| **S11** | Z 轴泛化"看起来是 0" | 数据生成配置把 `trans_range` 的 Z 上下界都设成 `0.0`，**根本没有 Z 方向的样本**。报告脚本为此专门写了声明 | `phase2_batch50.yaml:52–54`、`generate_stage3_report.py:204,227` `[CODE]` |
| **S12** | `python scripts/foo.py` 直接跑就 `ImportError` | `python scripts/foo.py` 把 **`scripts/`** 而不是仓库根放进 `sys.path[0]`（坑 E）。几个脚本自己 bootstrap 了 `sys.path`（`run_stage4_rl_train.py:42`、`stage5b_submit_jobs.py:29`），**没 bootstrap 的必须靠入口脚本设 `PYTHONPATH`** | 见左栏 `[CODE]` |
| **S13** | JAX 把显存吃光、WM 服务 OOM | `XLA_PYTHON_CLIENT_PREALLOCATE` **必须在 `import jax` 之前**设成 `false`（坑 R，默认预占 ~75 % ≈ 30 G）。三处各兜一次底，但**绕过入口脚本直接 `python` 就可能漏掉** | `run_stage4.sh:25`、`run_stage4_rl_train.py:54`、`openpi_finetune_head.py:26,39` `[CODE]` |

> **审计四件套**（对应 [`ai_knowledge.md`](ai_knowledge.md) 的 `L01`）：任何一次"分数很低/为 0"的结论出口前，先查四件事 —— ① **回退计数**（有多少条走了 S1/S2）；② **动作非退化**（输出不是常量）；③ **帧数对账**（实际推理帧数 × episode 数 = 报告里的总帧数）；④ **输入侧量纲**（S3 的布局、夹爪的归一化 vs 原始编码器计数）。这四件事**全部可以从落盘的 JSON 直接算出来**，不需要重跑。

### 7.3 代理策略在 Stage 之间是**相反的**

本机有一个只监听 `127.0.0.1:10900` 的本地代理。它对**直连 localhost 的请求会返回 503**，也可能挂住长调用。于是：

| Stage | 设置 | 位置 | 理由 |
|---|---|---|---|
| 3 / 4 | `export no_proxy="*" NO_PROXY="*"` —— **完全关掉代理** | `run_stage3.sh:26`、`run_stage4.sh:24`、`launch_stage4_wm.py:62` | 只跟 `127.0.0.1` 说话；外部 VLM 走自己的 base URL，本来也不经这个 localhost 代理 |
| 5 | `export no_proxy="localhost,127.0.0.1,::1"` —— **只对本地免代理，外部仍可走代理**；再叠一个 `STAGE5_GATEWAY_DIRECT=1`（默认）**对网关强制直连** | `stage5_env.sh:29–30`、`stage5_adapter.py:437–439` | 要连**远端**比赛网关的长连接 WebSocket，代理会干扰（坑 S5-3）；但又不能像 Stage 3/4 那样一刀切 |

⚠️ **把 Stage 3/4 的 `no_proxy="*"` 抄到 Stage 5，或反过来，都会出问题**，且症状是"连不上/卡住"而不是明确报错。`stage5_env.sh` 里为此写了一整段 WHY 注释——**改这一行之前先读那段**。`[CODE]`

### 7.4 平台与硬件假设

| 假设 | 证据 |
|---|---|
| **Linux + NVIDIA 单机单卡**（`DEVICE = "cuda:0"`、`CUDA_VISIBLE_DEVICES=0`、`nvidia-smi` 校验） | `run_stage4_rl_train.py:73`、`run_stage5.sh:39`、`launch_stage4_wm.py` `[CODE]` |
| **无头环境**（`PYOPENGL_PLATFORM=egl`，必要时软渲染） | `r2e2r_env.sh`、`r2e2r_env_wrapper.sh`、`check_headless.py` `[CODE]` |
| **conda 装在 `<user_home>/miniconda3`** | `env.sh`、`run_stage5.sh:38,52,70` `[CODE]` |
| **系统 gcc 11.4 在 `/usr/bin/gcc`**（不是 conda gcc） | `CLAUDE.md:236`、`r2e2r_env_wrapper.sh` `[CODE]` |
| **产物盘 vs 代码盘分离**：代码在 `/mnt` 挂载点（渲染时只剩 6.6 G），产物落 `<user_home>`（55 G） | `phase2_video_render.yaml:10–15`、`run_stage3.sh:8`、`run_stage4.sh:14` `[CODE]` |
| **需要外网**：HF（可走 `hf-mirror.com`）、外部 VLM 端点、ARK 图像编辑 API、RoboColiseum 网关 | `[CODE]` |
| **`bash`**（`#!/usr/bin/env bash` + `set -euo pipefail` + `PIPESTATUS`），不是 POSIX sh | 五个入口脚本 `[CODE]` |

### 7.5 注释与"坑位"词表

本仓库的注释质量**显著高于平均水平**：几乎每个反直觉的写法上面都有一段"为什么"，而且**带定量的账**（`~12 GB`、`~1737 张 JPEG`、`6.6 G 剩余`、`2.16 M 参数 / 8.66 MB`）。**没有一个 `TODO` / `FIXME` / `HACK`**——全仓库 `grep` 只命中一个 `XXX`，而它是日志模板里的占位符（`generate_stage4_evidence_report.py:175` 的 `ep_source_0_trans_XXXX_FAILED.mp4`）。`[CODE]`

代价是它用了一套**只在仓库内部有定义的编号词表**，注释里直接写"坑 R"、"坑 S5-3"而不解释：

| 词表 | 范围 | 归属 |
|---|---|---|
| 坑 A–J | Stage 3 | A staging 目录 `.npy` / B 任务文本三方对齐 / E `sys.path` / F `h5py` / G 夹爪数据源 / I `conda run` PID |
| 坑 M/N/O | Stage 2 视频渲染 | M `pkg_resources` / N 硬编码输出路径撑爆磁盘 / O 第 6 个 clip OOM-kill |
| 坑 R–CC | Stage 4 | R JAX 预占 / S PEFT 不可用 / T flow-matching 非高斯 / U 梯度过不了 WS / V `DEFAULT_PROMPT` 是水壶 / X 奖励方差 / Y `strict=False` 加载 / Z `ascontiguousarray` 对 0-d / AA `from_dict` 类型检查 / BB `gesim/src` src-layout |
| 坑 S5-1 … S5-17 | Stage 5 / 5b | S5-3 代理劫持长连接 等 |

**这些编号的完整定义只在仓库的 `CLAUDE.md`（745 行）里**，本知识库把它们按故障现象重排进了 [`troubleshooting.md`](troubleshooting.md)（`Q01`–`Q41`）。**看到注释里的"坑 X"而想不起是什么，去查 `troubleshooting.md` 的快速症状索引，不要去猜。**

---

## 8. 与其它三层知识的关联

### 8.1 代码 ↔ 原理层（[`background_knowledge.md`](background_knowledge.md)）

| 本文档 | 原理层章节 | 关系 |
|---|---|---|
| §3.1 双服务拓扑（WM `:9000` + policy `:8000`） | §3.3 工程架构：三进程拓扑 | 代码层是那张拓扑图的**具体实现与端口/权重名** |
| §3.2 `EpisodeBundle` 桥接、内参同步缩放 | §6.2 数据格式：Episode Bundle、§2.7 传感器仿真原理 | 原理层讲字段契约，代码层讲**从别的数据格式怎么造出来** |
| §3.3.2 判分器替身 | §2.5 World Judge、§6.6「奖励开箱即恒为 `None`」 | 原理层说明**为什么必须自建**；代码层是自建的那一份 |
| §3.4 RWR 微调器 | §5.6「没有 URDF」、§8.4 论文与开源交付的落差 | 原理层指出训练代码缺席；代码层是**补上的那部分**（并诚实标出它退化成了什么，见 S9） |
| §3.6 Stage 5 隧道协议 | §9.3.1–§9.3.6 RoboColiseum 托管服务契约 | 原理层给平台契约（含 6 处文档漂移），代码层给**线上协议的实现细节**；⚠️ **二进制分帧布局在平台文档里是 `未提及` 的，本层是唯一成文来源**（§3.6.1） |
| §6.2 Real2Edit2Real 的两个 patch | §9.2 Real2Edit2Real | 原理层讲方法与三阶段流程（基座是 GE-Sim **v1**，不是 2.0），代码层讲**这套代码在本机跑起来还缺什么**：图像编辑模型已下线、视频渲染必然 OOM |
| §4.2 常量式配置、§5.1「没有依赖清单」 | §5.3「依赖清单全部未锁版本」、§7.6 配置文件字段 | 上游不锁版本 → 本仓库用**三个隔离 conda 环境**代偿（§5.2） |
| §6.1 只关了 `sparge_attention` | §5.4 PyTorch 与加速内核 | ⚠️ **两层不一致**：原理层建议首次部署把四个内核开关**全关**；本仓库只关了装不上的那一个并跑通。**保守起见按原理层，想省时间可按本仓库** |
| §7.2 S3 两套 16 维布局 | §7.2 数据契约 `src/gesim/types.py` | ⚠️ **原理层的做法更稳**：它要求走上游 `wm_state_to_policy_state()`；本仓库**没用**，而是手写了两份重排（`openpi_finetune_head.py:215`、`stage5_adapter.py:166`）。**新写代码请用上游函数** |
| §7.4 平台假设 | §5.1 硬性前提 | 一致，代码层补了产物盘/代码盘分离这一条实操约束 |

### 8.2 代码 ↔ 教训层（[`ai_knowledge.md`](ai_knowledge.md) 的 `L01`–`L09`）—— 代码里的物证

| 教训 | 代码物证 |
|---|---|
| **`L01` 下结论前先审计管道** | `run_stage3_batch_eval.py:191` 增量写 `raw_eval_results.json` + `:164` 把异常也落成记录 + `vlm_reward_client.py:117` 的 `judge_source` 字段 + `run_stage4_rl_train.py:222` 把全部超参写进 `rl_training_curve.json`。**审计四件套之所以能"不重跑就算出来"，全靠这几处落盘设计** |
| **`L02` 写码前把假设核验到源码** | `openpi_finetune_head.py:65` 的注释 "Real module names verified in `PI0Pytorch.__init__` (NOT `action_head`/`out_proj` — those don't exist)"——这是**核验到源码**的书面痕迹；反例见 §7.2 S6（`--tags A,B` 从未被任何一次执行验证过） |
| **`L03` 同一个坑会换皮复发** | "绝不要用 `DEFAULT_PROMPT`" 这条纪律在**四个文件**里各写了一遍（S4）；`stage5b_run_agents.sh:48` 注释直接写 "坑 S5-3 (**recurrence**)" |
| **`L04` 第三方文档管协议、实测管 API** | `r2e2r-update-inpaint-model.patch` 里两处标注：`b64_json` 路径写着 "VERIFIED working"、CDN 路径写着"间歇不可达" |
| **`L05` 最贵的失败是不报错的失败** | §7.2 的 13 条**全部**是它的物证；最典型是 S1（解析失败伪装成 0 分）与 S2（无 key 静默降级） |
| **`L06` 一个常量被多方消费时必须单点定义** | ⚠️ **这条教训在代码里被违反了至少四次**：`46`（S7）、`36`/`10`（S7）、`50`（S7）、`LIFT_BOX_PROMPT` vs `LIFT_BOX_TASK`（S4）、以及两份逐行相同的布局重排（S3）。**代码层是这条教训最直接的反面证据——它写在 `ai_knowledge.md` 里，正因为在这份代码里踩到了** |
| **`L07` 长流程的可观测性要开跑前铺好** | 每个 Stage 都 `tee` 日志到带时间戳的文件；`stage5_adapter.py:274` 的 `_write_status()` 让外部能轮询 agent 状态；`launch_stage4_wm.py` 的 `status` 子命令 |
| **`L08` 诚实测量优先于好看分数** | `run_stage4_rl_train.py:194–197` 主动在 docstring 里承认单轨迹 RWR 退化（S9）；`vlm_reward_client.py:219` 的 `_heuristic` docstring 自称 "explicitly non-semantic"；`stage5_adapter.py:192` 自称 "documented no-op" |
| **`L09` 派生分析的可行性受生成配置约束** | §4.1 的 Stage 2 YAML 里 `trans_range.generate.object` 的 Z 分量上下界**都是 `0.0`** —— 计划中的「Z 轴泛化曲线」在配置层面就已不可能。**这就是「配置项的真实取值必须从配置文件读」的物证**（`P45` / `Q45`） |

### 8.3 代码 ↔ 排障层（[`troubleshooting.md`](troubleshooting.md) 的 `Q01`–`Q45`）—— `[CODE]` 级机制解释

| `Qxx` 现象 | 代码层给出的机制 |
|---|---|
| `Q06` 长连接被本地代理挂死，连 `127.0.0.1` 都 503 / `Q07` 隧道拨号打到 `127.0.0.1:10900` | §7.3 —— 本机代理只听 `127.0.0.1:10900`；Stage 3/4 用 `no_proxy="*"`，Stage 5 **必须**改用 `no_proxy="localhost,127.0.0.1,::1"` + `STAGE5_GATEWAY_DIRECT=1`。`run_stage3.sh:21–26`、`stage5_env.sh:29–30`、`stage5_adapter.py:437–439` |
| `Q09` ⭐ `No module named 'spas_sage_attn'` | §6.1 —— 就是那个唯一的上游 patch；`setup_gesim_submodule.sh` 幂等重放它 |
| `Q13` ⭐ 导入期崩在 `from pkg_resources import ...` | §5.3 —— `setuptools 83.x` 移除了 `pkg_resources`，钉回 `80.10.2` |
| `Q15` `h5py` / `matplotlib` 明明装过却 `ModuleNotFoundError` | §5.2 + §5.3 —— **三个环境互相隔离**，`h5py` 只在 `r2e2r`、`matplotlib` 要单独补进 `openpi` |
| `Q16` 显存突然只剩四分之一 | §2.4 —— `XLA_PYTHON_CLIENT_MEM_FRACTION=0.20` 是**故意**把 JAX 压到 20 % 以与 WM 共卡 |
| `Q17` ⭐ `env.step()` 解包报错 / 取到的不是想要的视角 | §3.2 —— 三视角固定 384×512、需要探测与 resize；返回值结构见原理层 §7.1 |
| `Q22` 从 H5 读出来的数值量级完全不对 | §7.2 审计四件套第 ④ 条 —— 夹爪要读 `/action/*_effector/position`（归一化命令值），**不是** `/state/*`（原始编码器计数，坑 G） |
| `Q23` `No module named 'scripts'` / import 到空壳 | §7.2 S12 —— 坑 E（`sys.path[0]` 是 `scripts/`）+ 坑 BB（`gesim` 是 src-layout，必须挂 `gesim/src`）。`run_stage4.sh:30–33` 的三段 `PYTHONPATH` |
| `Q24` LoRA 路线接不上 / `Q25` 没有可用的概率密度 / `Q26` 梯度传不回策略 | §3.4 —— 坑 S（PEFT 不可用 → 自写 `LoRALinear`）、坑 T（**flow-matching 不是高斯策略**，所以走 RWR 而非 policy gradient）、坑 U（**梯度过不了 WebSocket** → 必须进程内加载） |
| `Q28` ⭐ 服务"已经杀掉了"但显存仍占十几 GB | §7.2 S5 —— 坑 I，`.pid` 记的是 `conda run` 包装进程。正解见 `launch_stage4_wm.py:78,176`（找真 PID + `nvidia-smi` 校验） |
| `Q29` 启动编排整体 hang 到超时（满 600 s） | §3.1 —— `launch_services.py` 的重试是**无上限 `sleep(5)`**（坑 C）；`--timeout` 默认 600 |
| `Q31` 渲染跑到第几个片段就被 OOM-kill / `Q33` 盘写满、输出落错盘 | §6.2.2 + §4.1 —— OOM patch 的四个 hunk（`--single_clip` + 显式 `del` + 每 clip `gc`）与 `phase2_video_render.yaml` 的影子目录方案 |
| `Q35` ⭐ 成功率 0 % 但怀疑不是模型的问题 | §7.2 **S1**（解析失败 → `completion_score=0.0` 且不改 `judge_source`）+ **S2**（无 key 静默降级）。**这两条是 `Q35` 的 `[CODE]` 级根因**；`vlm_reward_client.py:209–214, 217–232` |
| `Q36` ⭐ 手臂抖动 / 夹爪不动 / 左右臂互换但不报错 | §7.2 **S3** —— 两套 16 维布局，维度相同所以不报错。`openpi_finetune_head.py:215`、`stage5_adapter.py:166` |
| `Q39` 报告小节全空 | §7.2 **S6** —— `run_stage5.sh:104` 的 `--tags A,B` 与 poller 写出的 `final_jobA.json` 对不上 |
| `Q40` 跨机型评测得 0 分 | §3.6 —— `BOARD_HORIZON` 各榜不同（`manip` 是 30，其余 50）、`WAIST_BOARDS` 只含 `manip`、waist 是 documented no-op（S10） |
| `Q41` ⚠️ Stage 1 三个 demo 动作雷同（**未解决**） | 代码层**无法解释**：`未发现`任何会导致动作退化的编排层缺陷；`vlm_reward_client.py` 的 `progress` 是人造斜坡（§3.3.2）但不影响开环动作。**该现象的定位仍需回到上游 `gesim/` 源码** `[推断]` |
| `Q34` 网关卡死：TCP 还在、20+ 分钟不发数据 | §3.6.1 —— 平台按 `agent_id` 分派 session，**同一个 `agent_id` 重连不会被重新分派**，必须换一个新的；`ping_interval=20 s` 探不出这种「活着但不派活」的状态 |
| `Q38` 一连上就异常断线 | §3.6.1 —— 收到 `drain` 之后**不得再重连**（`TunnelClient` 的状态机 `:399` 把 `DRAINING` 当终态） |
| `Q42` 榜单 `total` 像均值不像求和 / `Q44` `result` 接口对 uuid 返 500 | 代码层**不解释**：这两条属平台侧口径与路由，机制见原理层 §9.3.4 与 §9.3.5 的漂移表。本层只提供实现侧证据（Stage 5 脚本按数字 id 拉结果） |
| `Q45` Z 轴泛化曲线画不出来 | §4.1 —— Stage 2 YAML 的 `trans_range.generate.object` 把 Z 钉为 `0.0`；这是**配置层面就已注定**的结果，不是数据处理 bug |

### 8.4 被本层推翻或修正的结论

| 原结论 | 出处 | 修正 |
|---|---|---|
| "首次部署应把四个加速内核开关全部关掉" | `background_knowledge.md` §5.4 | **不必**——本次实践只关 `sparge_attention`，另三个（`liger_norm`/`liger_layernorm`/`triton_rope`）保持 `true` 并跑通全部五个 Stage。仍建议装不上任何内核时按原理层全关。`[实践]` |
| "Stage 5 一键脚本可直接产出报告" | 仓库 `README.md` 的一键叙述 | **不能**——`run_stage5.sh:104` 的 `--tags A,B` 与 poller 的输出文件名不匹配（S6）。**照 README 的手工分步命令跑**（`--tags jobA,jobB`）。`[CODE]` |
| "Stage 4 做的是 RL / RWR" | 仓库 `CLAUDE.md` 的标题与本知识库早前表述 | **需打折**——单轨迹下 softmax 权重退化为常数，等价于"按轨迹奖励加权的过滤式 BC"（S9，函数 docstring 自述）。这与 [`background_knowledge.md`](background_knowledge.md) §8.2 对"可做 RL"的打折口径**方向一致**。`[CODE]` |
| "`.pid` 文件可用于清理服务" | `run_stage1.sh:26–29` 自身的写法 | **不可靠**——见 S5。用 `launch_stage4_wm.py stop` 的做法（找真 PID + `nvidia-smi` 校验）替代。`[CODE]` |
| ⭐ "Stage 5 上线时命中了坑 `S5-1`/`S5-2`/`S5-3`" | 源料复盘里"全部命中"的笼统措辞 | **措辞不准，应写'预防成功'**——这三条（msgpack numpy 变体 / warmup 空帧 / 16 维布局）**线上一次都没真正发生**：8994 帧零解码失败、两次 warmup 均正常，全部被 `stage5_mock_test.py` 的断言在上线前拦住。⚠️ 这个区别是有工程后果的：**"踩过并修好"与"写代码时就绕开了"对应完全不同的复现风险**，把后者记成前者会让人以为这些坑必然会遇到。同理，**真实 401 与真实配额耗尽都是 `未提及`**（Stage 5b 那句"耗尽"指的是 6 次**重连**用尽，不是配额）|
| "本仓库遵循单点定义原则" | 无（此为默认期待） | **不成立**——至少 5 组常量被重复定义（S3/S4/S7）。这正是 `L06` 的由来。`[CODE]` |

### 8.5 三条最重要的代码层特征（索引用摘要，≤200 字）

> **① 它是薄编排层，不含模型代码**：全部 8.8 k 行都在"拉服务 / 桥数据 / 判分 / 出报告 / 自检"，上游本体以 submodule 引用且**只改了一行**（关 `sparge_attention`）；训练器、判分器、线上 agent 是本仓库净新增的三块。
> **② 配置无统一系统**：只有 Stage 2 有 YAML，Stage 3/4/5 的超参和路径全是模块顶部大写常量，改参数=改源码；**没有 `requirements.txt`/`setup.py`**，依赖只在 `CLAUDE.md` 的三环境表里。
> **③ 最大的风险是"不报错的失败"**：已定位 13 条静默失效路径（判分器无 key 会静默降级为帧差、JSON 解析失败伪装成 0 分、两套 16 维布局用错不报错、Stage 5 一键脚本的 `--tags` 与产物文件名不匹配……），且至少 5 组常量被重复定义。**下任何"模型不行"的结论前，先跑 `L01` 的审计四件套。**

