# ge_sim_v2 速查（quickstart）

> **本文是派生层，不是新事实来源。** 它从 [`code_knowledge.md`](./code_knowledge.md)、[`background_knowledge.md`](./background_knowledge.md)、[`ai_knowledge.md`](./ai_knowledge.md)、[`troubleshooting.md`](./troubleshooting.md) 中挑出**可直接执行**的部分，不重复解释、不新增结论。与被引用的那一层冲突时，**以那一层为准**。
>
> **描述对象**：本机复现仓库 `GE-Sim-V2-tour`（根目录记作 `<repo_root>`），上游 GE-Sim 2.0 以 submodule 挂在 `<repo_root>/gesim`。
>
> 🔒 **已替换敏感信息**：所有本机绝对路径写作 `<repo_root>` / `<user_home>` / `<path>`，比赛网关写 `<GATEWAY_IP>`，第三方判分端点写 `<MIMO_BASE_URL>`。密钥只提文件名（`scripts/secrets.env`，已 gitignore），**不给内容**。

**动手前必须知道的三件事**（否则会白跑）：

1. **它不是物理仿真器，是"动作条件视频生成器"** —— 只出 RGB（三视角固定 384×512），无物理引擎/渲染器/场景文件，不能增删物体、换本体、改相机。它回答"策略看起来会怎么动"，**不回答"物理上会不会成功"**。
2. **开箱即用时 `reward` / `progress` 恒为 `None`** —— 论文主打的 World Judge 奖励模型**未开源**，判分要自己接（§2.3 用的就是自建替身）。
3. **最大的风险是"不报错的失败"** —— 判分器无 key 会静默降级、JSON 解析失败伪装成 0 分、两套 16 维动作布局用错也不报错。**下"模型不行"的结论前先跑 §5 的审计四件套。**

**先读这张表，再往下翻：**

| 我现在想干什么 | 去哪一节 |
|---|---|
| 从零把环境搭起来 | §1 环境准备 |
| 跑一个最小的世界模型推理，确认服务活着 | §2.1 Stage 1 单 demo |
| 批量生成/评测轨迹 | §2.2 Stage 2 数据生成 → §2.3 Stage 3 批量评测 |
| 在世界模型里微调策略 | §2.4 Stage 4 RWR 微调 |
| 接线上评测平台 | §2.5 Stage 5 |
| 改分辨率 / 步数 / 阈值 / 超参 | §3 改关键参数 |
| 报错了 | §4 常见问题（只列高频）→ 更全的看 [`troubleshooting.md`](./troubleshooting.md) 顶部「快速症状索引」 |
| 出结论前自查 | §5 自检清单 |

---

## 1. 环境准备

### 1.1 前置条件

| 项 | 要求 | 说明 |
|---|---|---|
| GPU | 单卡 ≥ 48 GB 显存（实测 47 GB 预算） | Stage 4 要 WM 与策略**共卡**，见 §3.1 的 `XLA_PYTHON_CLIENT_MEM_FRACTION` |
| 盘 | 代码盘与产物盘**分开**，产物盘 ≥ 50 GB | Stage 2 渲染每 episode 产 1 个 mp4 + ~1700 张 JPEG，很容易写满代码盘（`Q33`） |
| OS | Linux + CUDA | 上游未声明跨平台；本机是 Linux |
| conda | 必需 | **三个隔离环境**，不要合并（§1.3） |

### 1.2 拉代码与打补丁

```bash
# 1) clone 必须带 --recursive（上游有嵌套 third_party/openpi）
git clone --recursive <上游或本仓库 URL> GE-Sim-V2-tour
cd GE-Sim-V2-tour

# 2) 初始化 gesim submodule 并打上唯一的那一个补丁（幂等，可重复跑）
bash scripts/setup_gesim_submodule.sh
```

`setup_gesim_submodule.sh` 做两件事：`submodule update --init --recursive`，然后把 `gesim/configs/gesim_v2.yaml` 的 `sparge_attention: true` 改成 `false`。

> **为什么只关这一个**：`spas_sage_attn`（SpargeAttn）不在 PyPI 上、需源码编译（`Q09`）。另三个加速内核（`liger_norm` / `liger_layernorm` / `triton_rope`）**保持 `true` 并已跑通全部五个 Stage** `[实践]`。
> ⚠️ [`background_knowledge.md`](./background_knowledge.md) §5.4 建议首次部署**四个全关**——若你装不上任何内核就照它做；本仓库证明只关装不上的那一个也行。详见 [`code_knowledge.md`](./code_knowledge.md) §6.1。

补丁被**故意留成未提交状态**，所以 `git status` 会长期显示 `gesim` 是 "(modified content)"，这是正常的。

### 1.3 三个 conda 环境（不要合并）

| 环境 | 用途 | 必须单独装的东西 |
|---|---|---|
| `gesim` | 世界模型推理服务（Stage 1/2/3/4 的 WM 侧） | `torch`（先装）、`liger-kernel` |
| `openpi` | 策略侧（π0.5）与 Stage 4 训练器 | `matplotlib` 要**单独补**（`Q15`）；`setuptools` 必须钉 `80.10.2`（`Q13`） |
| `r2e2r` | Real2Edit2Real 数据生成/渲染 | `h5py` 只在这个环境里（`Q15`） |

三个环境里 `h5py` / `matplotlib` "明明装过却 ModuleNotFoundError"，**九成是跑在了错的环境里**。

```bash
# 三个环境各自的装法见 <repo_root>/CLAUDE.md 的环境表；本仓库没有 requirements.txt / setup.py
# （code_knowledge.md §5.1 已确认「未发现」任何依赖清单文件——换机只能照那张表手装）

# 上游 openpi-client 必须单独以 editable 方式装：
pip install -e gesim/third_party/openpi/packages/openpi-client
```

**版本锁定项**（装错会直接崩或静默走错分支）：

```
setuptools==80.10.2     # 83.x 移除了 pkg_resources，导入期直接崩（Q13）
torch>=2.0              # 上游唯一有版本约束的依赖；其余全无约束，自己钉
```

### 1.4 环境变量

```bash
# 判分器（Stage 3/4 要用；不设的话会静默降级为帧差启发式，见 §4）
export MIMO_BASE_URL="<MIMO_BASE_URL>"
export MIMO_API_KEY="<你的 key>"        # 也可放进 scripts/secrets.env（已 gitignore）

# JAX 显存：必须在 import 之前设，写在脚本里而不是交互式设置
export XLA_PYTHON_CLIENT_PREALLOCATE=false
export XLA_PYTHON_CLIENT_MEM_FRACTION=0.20   # 与 WM 共卡时压到 20%

# 代理策略：Stage 3/4 与 Stage 5 是相反的，千万不要互相抄（详见 §4）
export no_proxy="*" NO_PROXY="*"             # ← 仅 Stage 1/2/3/4
```

现成的封装在 `scripts/env.sh`（通用）、`scripts/stage5_env.sh`（Stage 5 专用）、`scripts/r2e2r_env_wrapper.sh`（数据生成）。**优先 source 这些脚本，不要手敲**——它们同时处理了 `PYTHONPATH` 的三段拼接（`Q23`）。

---

## 2. 运行示例

五个 Stage 各有一个一键脚本在 `<repo_root>/scripts/`。**除 Stage 5 外都要求先 `cd <repo_root>`**（只有 `run_stage5.sh` 自己 `cd "$(dirname "$0")"`）。

### 2.1 最小验证：Stage 1 单 demo（先跑这个）

```bash
cd <repo_root>
bash scripts/run_stage1.sh
```

**预期输出**：世界模型服务在 `127.0.0.1:9000` 起来，跑完 3 个 demo，产物落在 `outputs_stage1/`，每个 demo 一段 mp4（三视角 384×512）。日志 `tee` 到带时间戳的文件。

**判读**：
- 看到服务 500 报 `liger-kernel is required` → `Q08`，环境装漏了。
- 看到 `No module named 'spas_sage_attn'` → §1.2 的补丁没打上（`Q09`）。
- 脚本整体 hang 到 600 s 超时 → `Q29`，`launch_services.py` 的重试是**无上限**的，说明服务其实没起来，去看服务日志而不是等。
- ⚠️ **已知未解**：三个 demo 的动作可能雷同（`Q41`）。编排层已排查无缺陷，定位需回上游 `gesim/` 源码。**不要把它当成自己环境装错了。**

> 服务活着但想确认干净收尾：**别信 `.pid` 文件**（它记的是 `conda run` 包装进程，`Q28`）。用 `python scripts/launch_stage4_wm.py stop`，它会找真 PID 并用 `nvidia-smi` 校验显存真的释放了。

### 2.2 Stage 2：批量生成数据（R2E2R）

```bash
cd <repo_root>
bash scripts/run_stage2.sh                      # 走 scripts/configs/phase2_batch50.yaml
# 只渲染视频（大产物，走影子目录避免写满代码盘）：
python scripts/render_stage2_videos.py          # 读 scripts/configs/phase2_video_render.yaml
```

**预期输出**：46 个可用 episode（配置里请求 50，通过率不是 100 %）。渲染阶段每 episode 产 1 个 mp4 + ~1700 张 JPEG。

**两个必知**：
- **渲染产物会被写回输入目录**（上游 `input_root = dirname(output_root)`）。`phase2_video_render.yaml` 用「真目录 + 符号链接的影子树」把它们导到大盘上，`render_stage2_videos.py` 负责建这棵树。**换机时这个 YAML 的 `output_root` 必须改**（`Q33`）。
- 渲染会 OOM-kill（原本挂在第 6 个 clip）。仓库的 `r2e2r-video-render-oom-fix.patch` 加了 `--single_clip` + 断点续跑 + 每 clip 显式 `del`/`gc`。**用 `bash scripts/setup_r2e2r_submodule_patch.sh` 打上**（`Q31`、`Q32`）。

### 2.3 Stage 3：批量评测（最常用）

```bash
cd <repo_root>
bash scripts/run_stage3.sh
```

脚本内部：`export no_proxy="*" NO_PROXY="*"` → 探测帧尺寸并按需 `export STAGE3_TARGET_WH="512,384"` → 跑 46 个 episode → 出报告。

**预期输出**：`raw_eval_results.json`（**增量写**，中断也有数据）+ 一份 Markdown 报告。报告里每条含 `judge_source`、`completion_score`、`reasoning`。

⚠️ **看到 0 % 成功率时，先怀疑管道，不要怀疑模型**（`Q35`）。两条静默路径：
1. **没设 `MIMO_API_KEY`** → 判分器降级成"帧间平均绝对差 / 50"的启发式（自述 "explicitly non-semantic"），`judge_source` 会写 `Heuristic-Fallback (No API Key)`。
2. **判分响应 JSON 解析失败** → 直接返 `completion_score=0.0` 且**不改 `judge_source`**，报告里与真正的 0 分**完全无法区分**。唯一线索是 `reasoning` 字段里的 `MiMo response parse error: ...`。

所以第一步永远是 `grep judge_source` 和 `grep 'parse error'`，见 §5。

> 报告里**没有 Z 轴数据是配置决定的，不是模型不泛化**：`phase2_batch50.yaml` 的 `trans_range.generate.object` 上下界 Z 都是 `0.0`，所以全部 46 个 episode 的 `dz ≡ 0`。报告生成器已就地写了声明。

### 2.4 Stage 4：在世界模型里微调策略（RWR）

```bash
cd <repo_root>
bash scripts/run_stage4.sh          # 起 WM + 在 openpi 环境里跑训练器
# 或分开来：
python scripts/launch_stage4_wm.py start     # / status / stop
```

**跨环境的关键技巧**（`run_stage4.sh` 里的写法，抄的时候三段 `PYTHONPATH` 不能少）：

```bash
PY4="PYTHONPATH=<repo_root>/gesim/openpi_serving:<repo_root>/gesim/src:<repo_root>"
OPENPI_ENV_VARS="env $PY4 XLA_PYTHON_CLIENT_PREALLOCATE=false \
                 XLA_PYTHON_CLIENT_MEM_FRACTION=0.20 no_proxy=* NO_PROXY=*"
conda run -n openpi --no-capture-output $OPENPI_ENV_VARS \
  python scripts/run_stage4_rl_train.py --max_iterations 60 --max_steps 10
```

**预期输出**：`<user_home>/stage4_outputs/` 下的 `rl_training_curve.json`（**连同全部超参一起落盘**）+ 每 20 iter 一个小头 checkpoint（仅 4 个投影模块，2.16 M 参数 / 8.66 MB）。

**三条必须知道的打折**：
- **策略侧只训 4 个模块**（`action_in_proj` / `action_out_proj` / `time_mlp_in` / `time_mlp_out`），不是全量微调。
- **不是真 RL**：flow-matching 不给概率密度、梯度过不了 WebSocket（`Q25` / `Q26`），所以走 RWR；而**单轨迹下 softmax 权重退化为常数**，等价于"按轨迹奖励加权的过滤式 BC"——函数自己的 docstring 就这么写着。别在汇报里说"做了 RL"。
- **LoRA 是自己手写的**（`LoRALinear`，r=16/alpha=32），因为 PEFT 在这套模型上不可用（`Q24`）。

### 2.5 Stage 5：接线上评测平台

```bash
bash scripts/run_stage5.sh      # 唯一自己 cd 的脚本，可从任意目录调用
```

⚠️ **一键脚本的报告步骤是坏的**：`run_stage5.sh` 传 `--tags A,B`，而 poller 写出的文件是 `final_jobA.json` / `final_jobB.json`，于是报告小节全空（`Q39`）。**照 `README.md` 的手工分步命令跑，用 `--tags jobA,jobB`。**

**Stage 5 的代理策略与 Stage 3/4 相反**：它用 `no_proxy="localhost,127.0.0.1,::1"`（**不是 `*`**）配合 `STAGE5_GATEWAY_DIRECT=1`，因为要经隧道出公网到 `<GATEWAY_IP>`。抄错的表现是**挂住而不是报错**（`Q06` / `Q07`）。

其它两条：各榜的 chunk horizon 不同（`manip` 是 30，`instruction`/`spatial`/`robust` 是 50）；**waist 自由度是 documented no-op**（把观测到的腰部值原样铺满整个 chunk）——跨机型得 0 分时先看这两处（`Q40`）。

---

## 3. 改关键参数

**先记一条**：本仓库**没有统一配置系统**。只有 Stage 2 走 YAML，Stage 3/4/5 的超参和路径全是**模块顶部的大写常量**——改参数就是改源码。完整的四种配置形态见 [`code_knowledge.md`](./code_knowledge.md) §4。

### 3.1 能用命令行/环境变量改的（优先走这条）

| 想改什么 | 怎么改 |
|---|---|
| Stage 4 训练轮数 / 每轮步数 | `python scripts/run_stage4_rl_train.py --max_iterations 60 --max_steps 10` |
| Stage 4 显存占比 | `XLA_PYTHON_CLIENT_MEM_FRACTION=0.20`（与 WM 共卡时别调高） |
| Stage 3 目标帧尺寸 | `export STAGE3_TARGET_WH="512,384"`（脚本会按探测结果自动设，一般不用手动） |
| Stage 5 是否直连网关 | `STAGE5_GATEWAY_DIRECT=1`（默认直连；设 `0` 才走代理） |
| 渲染只跑单个片段（防 OOM） | 渲染脚本的 `--single_clip`（由 OOM patch 引入） |
| 启动编排超时 | `launch_services.py --timeout`（默认 600 s） |

### 3.2 必须改源码的（附「改哪一份」的坑）

| 想改什么 | 改哪里 | 坑 |
|---|---|---|
| 任务指令文本 | `openpi_finetune_head.py:56` `LIFT_BOX_PROMPT` | ⚠️ **同一句话在四个文件里各写了一遍**，还有 `LIFT_BOX_TASK` 这个近义常量。只改一处会静默不一致（`code_knowledge.md` §7.2 S4） |
| RWR 超参（学习率、温度、探索噪声、平滑惩罚、baseline 衰减） | `run_stage4_rl_train.py:75–83` 的大写常量 | 都会被写进 `rl_training_curve.json`，改完能追溯 |
| 世界模型服务地址 | `run_stage4_rl_train.py:72` `WM_SERVER = "http://127.0.0.1:9000"` | — |
| 训练产物目录 | `run_stage4_rl_train.py:67` `OUT_DIR` | — |
| 微调哪几个模块 | `openpi_finetune_head.py:65` `FINETUNE_MODULE_NAMES` | 模块名是**核验过源码的**（`action_head`/`out_proj` 这类名字在这套模型里**不存在**），改之前先 grep `PI0Pytorch.__init__` |
| 数据生成的物体位姿范围 / 阈值 / 生成条数 | `scripts/configs/phase2_batch50.yaml` | `trans_range` 的 Z 上下界都是 `0.0`——想要 Z 轴泛化数据必须在这里放开（§2.3） |
| 渲染产物落盘位置 | `scripts/configs/phase2_video_render.yaml` 的 `output_root` | **换机必改**；影子目录方案见 §2.2 |
| 各榜 chunk horizon | `stage5_adapter.py:573` `BOARD_HORIZON` | — |
| 期望 episode 数 / 判分帧数等阈值 | 多处 | ⚠️ **重复定义**：`46`、`36`/`10`、`50` 各在主脚本、YAML、verify 脚本里写了不止一遍（S7）。改一处不生效就去 grep 数字本身 |

### 3.3 改之前要知道的现状值

| 项 | 现状 | 能不能改 |
|---|---|---|
| 相机视角 | head / left_wrist / right_wrist **三个，固定** | **不能** |
| 分辨率 | 384×512 | **不能** |
| 模态 | 只有 RGB | **不能**（深度/LiDAR/IMU/力矩/触觉/分割全部未提及） |
| 本体 / 场景物体 | 固定 | **不能**（无 URDF、无场景文件） |
| 帧数 | 25 帧 / 2.3 s（配 4× 跳帧可覆盖约 100 帧跨度） | 见 `background_knowledge.md` §8.2 —— **不要引用"100 帧"这个口径** |
| 动作维度 | 16 | 两套布局，见 §4 第 1 条 |

---

## 4. 常见问题（高频 8 条）

> 完整 41 条按现象查 [`troubleshooting.md`](./troubleshooting.md) 顶部的「快速症状索引」。这里只列**最容易白花时间**的。

**① 手臂抖动 / 夹爪不动 / 左右臂互换，但不报错**（`Q36`）
两套 16 维布局：世界模型侧是 `[L7臂, L夹爪, R7臂, R夹爪]`，策略侧是 `[L7臂, R7臂, L夹爪, R夹爪]`。**维度相同，用错不报错，只是行为错。**
→ 新写代码请走上游 `src/gesim/types.py` 的 `wm_state_to_policy_state()`。本仓库**没走**，而是在 `openpi_finetune_head.py:215` 和 `stage5_adapter.py:166` 手写了**两份逐行相同**的重排（这正是教训 `L06` 的由来）。

**② 成功率 0 %，但怀疑不是模型的问题**（`Q35`）
两条静默路径见 §2.3。先 `grep judge_source` 与 `grep 'parse error'`，再谈模型。

**③ `ModuleNotFoundError: No module named 'scripts'` / import 成功但拿到空壳**（`Q23`）
`sys.path[0]` 是 `scripts/` 而不是仓库根；且 `gesim` 是 src-layout，必须把 `gesim/src` 也挂上。用三段 `PYTHONPATH`（§2.4）。

**④ `h5py` / `matplotlib` 明明装过却找不到**（`Q15`）
跑在了错的 conda 环境里。`h5py` 只在 `r2e2r`，`matplotlib` 要单独补进 `openpi`。

**⑤ 导入期崩在 `from pkg_resources import ...`**（`Q13`）
`setuptools 83.x` 移除了 `pkg_resources`。`pip install setuptools==80.10.2`。

**⑥ 长连接被本地代理挂死，连 `127.0.0.1` 都 503 / 隧道拨号打到 `127.0.0.1:10900`**（`Q06` / `Q07`）
**两套相反的代理策略，不要互抄**：Stage 1–4 用 `no_proxy="*"`；Stage 5 必须 `no_proxy="localhost,127.0.0.1,::1"` + `STAGE5_GATEWAY_DIRECT=1`。抄错的表现是**挂住而不是报错**。

**⑦ 服务"已经杀掉了"但显存仍占十几 GB**（`Q28`）
`.pid` 记的是 `conda run` 包装进程。用 `python scripts/launch_stage4_wm.py stop`（找真 PID + `nvidia-smi` 校验）。

**⑧ 报告小节全空**（`Q39`）
`run_stage5.sh:104` 的 `--tags A,B` 与产物文件名 `final_jobA.json` 不匹配。用 `--tags jobA,jobB`。

**换机器时"改了没生效"先查这两处**：仓库有 **49 个文件、213 处主机绝对路径**，且存在**两种根目录推导风格**（14 个文件硬编码仓库根、8 个相对推导，`run_stage3_batch_eval.py` 两种都用），另有 **3 处硬编码路径藏在 argparse 的 default 里**。清单见 [`code_knowledge.md`](./code_knowledge.md) §7.1。

---

## 5. 自检清单

**出任何"模型表现如何"的结论前，先跑这四件套**（教训 `L01`，本项目最贵的一次返工就是跳过了它）：

```bash
# ① 判分器到底是谁在判？出现 Heuristic-Fallback 说明 key 没设上
grep -o '"judge_source": "[^"]*"' raw_eval_results.json | sort | uniq -c

# ② 有多少条是「解析失败伪装成 0 分」？
grep -c 'parse error' raw_eval_results.json

# ③ 分数分布是否退化（全 0 / 全同一个值都可疑）
grep -o '"completion_score": [0-9.]*' raw_eval_results.json | sort | uniq -c

# ④ 夹爪读的是哪个字段？必须是 /action/*_effector/position（归一化命令值）
#    读 /state/* 会拿到原始编码器计数，量级完全不对（Q22）
```

**交付/汇报前的口径检查**：

- [ ] 没有把 Stage 4 说成"做了 RL"（单轨迹 RWR 退化为加权 BC，§2.4）
- [ ] 没有引用"100 帧 / 2.3 秒"（正确写法：25 帧 / 2.3 s，配 4× 跳帧覆盖约 100 帧跨度）
- [ ] 没有把"登顶 WorldArena"当成那篇基准论文的结论（指活榜；该基准正文 grep `GE-Sim` 命中 0）
- [ ] 报告里没有 Z 轴数据时，已说明这是 `trans_range` 配置 Z=0 所致，**不是**模型不泛化
- [ ] 结论没有超出"看起来会怎么动"的范围（无物理引擎，回答不了"物理上会不会成功"）
- [ ] `git status` 里 `gesim` 显示 "(modified content)" —— 这是补丁的正常状态，别去 `checkout` 掉

---

## 相关文档

| 文档 | 什么时候看 |
|---|---|
| [`00-index.md`](./00-index.md) | 拿章节行号，用 `Read` 的 `offset`/`limit` 精读 |
| [`background_knowledge.md`](./background_knowledge.md) | 查 API、设计原理、能力边界；§8.4 是部署前必读的"论文与开源交付落差" |
| [`ai_knowledge.md`](./ai_knowledge.md) | 估工作量、看决策复盘、看试过哪些无效方法（§4 问题表带"无效尝试"列） |
| [`troubleshooting.md`](./troubleshooting.md) | **带着报错来的话，先来这里**（顶部快速症状索引 → `Qxx`） |
| [`code_knowledge.md`](./code_knowledge.md) | 要改代码 / 找类函数参数在哪个文件；§7.2 的 13 条静默失效路径值得先读一遍 |


