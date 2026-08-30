# genesis_world 速查（quickstart）

> **本文是派生层，不是新事实来源。** 它从 [`code_knowledge.md`](./code_knowledge.md)、[`background_knowledge.md`](./background_knowledge.md)、[`ai_knowledge.md`](./ai_knowledge.md)、[`troubleshooting.md`](./troubleshooting.md) 中挑出**可直接执行**的部分，不重复解释、不新增结论。与被引用的那一层冲突时，**以那一层为准**。
>
> **描述对象**：本机复现仓库 `genesis-world-tour`（根目录记作 `<repo_root>`），跑的是 **genesis-world 1.2.2**。原理层写的是 **1.3.3**，**API 写法不可互换**。
>
> 🔒 **已替换敏感信息**：所有本机绝对路径写作 `<path>` / `<user_home>` / `<conda_env>`。

**先读这张表，再往下翻：**

| 我现在想干什么 | 去哪一节 |
|---|---|
| 从零把环境搭起来 | §1 环境准备 |
| 跑一个能出视频的最小例子 | §2.1 Stage 4 单 demo（最快，不需要 VLA 模型） |
| 跑 VLA 抓取闭环 | §2.2 Stage 1 / Stage 2 |
| 跑 RL 训练全流程 | §2.3 Stage 3 |
| 改分辨率 / 步数 / 阈值 / 超参 | §3 改关键参数 |
| 报错了 | §4 常见问题（只列高频）→ 更全的看 [`troubleshooting.md`](./troubleshooting.md) 顶部「快速症状索引」 |
| 交付前自查 | §5 自检清单 |

---

## 1. 环境准备

### 1.1 前置条件

| 项 | 要求 |
|---|---|
| GPU | 单卡 NVIDIA，显存 ≥ 40 GB（Stage 2 的 VLA 模型 bfloat16 约 15 GB；Stage 3 用 2048 个并行环境） |
| CUDA | 11.8（与驱动匹配即可，**不要为了跑通去动驱动**） |
| Python | 3.12 |
| 显示 | 不需要。全程 headless，所有脚本都是 `show_viewer=False` |
| 系统工具 | `ffmpeg` / `ffprobe`（三个 `verify_*.py` 都靠 `ffprobe` 读视频元数据） |

### 1.2 装依赖

**仓库里没有 `requirements.txt` / `setup.py` / `environment.yml`** —— 得手动装。版本锁定的那几个是硬要求：

```bash
conda create -n <conda_env> python=3.12 -y
conda activate <conda_env>

# 版本锁定项（这三个装错会直接失败或静默走错分支）
pip install genesis-world==1.2.2          # 全仓库 API 写法基于 1.2.2
pip install rsl-rl-lib==5.0.1             # train_subprocess.py 有硬版本门，<5 直接 raise
pip install numpy==1.26.4                 # 与 Genesis 的 C 扩展绑定

# 常规依赖
pip install torch torchvision             # 实测 2.10.0+cu128
pip install transformers tensordict opencv-python
pip install pysplashsurf                  # 仅 Stage 4 水面重建需要
# pip install flash-attn                  # 可选，缺了会自动退回 eager 注意力
```

⚠️ **不要装 `pyuipc` / IPC**。装它会破坏环境（`L06`），本仓库全部软体结果都建立在 **PBD 路径**上，Stage 4 的布料/海绵 demo 已内置 `try IPCCouplerOptions() / except ImportError → PBD` 降级。
⚠️ **不是 `splashsurf`，也不是 `openvdb`**（后者只支持 Python 3.9）。

### 1.3 环境变量

绝大多数变量**不需要你在 shell 里设**——脚本自己写死或 `setdefault`：

| 变量 | 谁设的 | 你要不要管 |
|---|---|---|
| `HF_HOME` / `TRANSFORMERS_CACHE` | Stage 1/2 的四个脚本在 `import torch` **之前**用 `os.environ[...] = ...` **硬写死** | ✅ **换机必改脚本**，改环境变量没用（详见 `code_knowledge.md` §2.3、§7.1） |
| `GSPATH` / `GS_HOME` | Stage 4 三个 demo 用 `os.environ.setdefault(...)` | 外部已设则不覆盖，一般不用管 |
| `TMPDIR` | `stage3/run_in_env.sh` 设到大盘 | 不用管 |

### 1.4 VLA 模型（只有 Stage 1/2 需要）

模型是**本地目录**，加载全部带 `local_files_only=True`，**运行时不联网**。默认路径写死在脚本里（`--model_path` 的 default），换机要么改脚本要么每次显式传 `--model_path <path>/openvla-mcx-card`。

### 1.5 后台跑长任务

后台 bash 任务**不继承 conda / profile**，直接 `python xxx.py &` 会秒退且无输出（`Q23`）。用仓库自带的包装器：

```bash
cd <repo_root>/stage3
bash run_in_env.sh train_subprocess.py --num_envs 2048 --max_iterations 50 --exp_name go2-walking
```

---

## 2. 运行示例

> 所有命令都假定已 `conda activate <conda_env>`。**注意工作目录**：Stage 1/2 在 `<repo_root>`，Stage 3 在 `<repo_root>/stage3`，Stage 4 在 `<repo_root>/stage4`。走错目录会找不到相对路径产物。

### 2.1 最快的冒烟测试：Stage 4 布料抓取（不需要 VLA 模型）

```bash
cd <repo_root>/stage4
python cloth_grasp_demo.py --steps 200 --output_dir diagnostics
python verify_stage4.py --demo cloth
```

**预期输出**：
- `diagnostics/` 下出现一个 MP4（编码可能是 `mp4v` 或 `mpeg4`，都算正常）+ 一份 JSON 报告；
- 控制台打印每帧的**穿透距离**（`torch.cdist(finger_verts, cloth_particles)` 的最小值）与**形变幅度**；
- `verify_stage4.py` 打印 PASS/FAIL 列表并以 `exit 0`（全过）或 `exit 1` 结束。判据：形变范围 > `0.03`、无穿透、视频编码在白名单内。

另外两个 Stage 4 demo（注意**水杯用 `--frames` 不是 `--steps`**）：

```bash
python sponge_squeeze_demo.py --steps 180  --output_dir diagnostics_sponge
python glass_water_demo.py    --frames 180 --output_dir diagnostics_glass
python verify_stage4.py --demo all
```

> 水杯 demo 是三者里最慢的：SPH 时间步被锁在 `4e-4`（再大水会炸开，`Q34`），每帧走 28 个子步。

### 2.2 VLA 抓取闭环：Stage 1 单场景 / Stage 2 批量

```bash
cd <repo_root>

# Stage 1：单场景，最快看到闭环行为
python vla_closed_loop_demo.py \
    --task "Pick up the blue block and place it on the target" \
    --steps 300 --output_dir stage1_eval --pos_scale 0.03

# Stage 2：8 个场景批量评测 + 独立验证门
python batch_eval_vla.py --output_dir stage2_eval --steps 1000 --pos_scale 0.03
python verify_stage2.py  --output_dir stage2_eval     # ← 必须显式传，见下方警告
```

⚠️ **两个默认值不一致**：`batch_eval_vla.py` 默认写到 `stage2_eval`，而 `verify_stage2.py` 默认读 `stage2_eval_8scene`。**验证时必须显式传 `--output_dir`**，否则会以"找不到场景"失败。

只跑指定场景（`--scenes` 是 `nargs="*"`，不传 = 全部 8 个）：

```bash
python batch_eval_vla.py --scenes eval_scene_1_blue_target eval_scene_4_target_shift
```

**预期输出**（每个场景一个子目录）：
- 两路视频：宽视角 640×480 + VLA 输入视角 224×224；
- `trajectory.json`：**逐步**记录 `ee_pos` / `finger_center` / `block_pos` / `finger_dist` / `raw_action` / `delta_pos` —— 这份逐步数值是判断"模型到底在不在动、往哪动"的唯一可靠依据（`L02`）；
- `run_log.json`：含 `success` / `success_type`（`gripper_touch` / `z_lift` / `none`）。

> 📌 **对预期结果要有正确心理预期**：Stage 2 的实测结果是 **0/8 成功**。这是被记录在案的结论，不是你装错了环境。原因分析见 `ai_knowledge.md` §4。仓库里的 `classical_demo.py` / `hybrid_vla_demo.py` 就是为定位"问题在模型还是在仿真器"而写的对照组。

### 2.3 RL 训练全流程：Stage 3

```bash
cd <repo_root>/stage3
python run_orchestrator.py --dry-run    # 先看它要跑哪 5 个阶段，不执行
python run_orchestrator.py              # 真跑：0→50→100 两段训练 + 3 段录像
python verify_stage3.py
```

调度器串行跑 5 个**独立子进程**（各自持有自己的 `gs.init()` 与 CUDA 上下文——这是绕开"一个进程内不能二次 `gs.init()`"的手段，`Q15`）：

1. 未训练策略录像 → `rl_visualizations/eval_epoch_0_untrained.mp4`
2. 训练到第 50 迭代
3. 中期录像 → `eval_epoch_50_mid.mp4`
4. 训练到第 **100** 迭代（`--resume`）
5. 最终录像 → `eval_epoch_100_final.mp4`

**预期输出**：三段 MP4 肉眼可见的行为差异（乱抖 → 站住 → 前进）、`logs/go2-walking/model_50.pt` 与 `model_100.pt`、tensorboard 事件文件。`verify_stage3.py` 检查三个视频存在且时长/编码合法、两个 checkpoint 存在、`Train/mean_reward` 单调改善。

⚠️ **`--max_iterations` 是绝对目标迭代数，不是增量**。第 4 阶段传 `100` 而不是 `50`，脚本内部算 `delta = 100 - loaded_iter`。传成增量会训练过头。

**先探显存再开长跑**（`L01`）：仓库自带梯度测试脚本，用 256/512/1024/2048 个环境各跑 2 个迭代探 OOM 边界：

```bash
bash gradient_test.sh
```

---

## 3. 改关键参数

> **本仓库没有任何 YAML / JSON 配置文件**，全部配置是 argparse + 模块级常量 + Python 字典。好处是没有静默覆盖，坏处是**改参数必须改源码**。完整说明见 `code_knowledge.md` §4。

### 3.1 能用命令行改的（优先走这条）

| 想改 | 参数 | 在哪个入口 |
|---|---|---|
| 闭环步数 | `--steps` | Stage 1 / 2 / Stage 4 布料·海绵 |
| 渲染帧数 | `--frames` | **仅** Stage 4 水杯 demo |
| 动作位移尺度 | `--pos_scale`（默认 `0.03`） | Stage 1 / 2 |
| 产物目录 | `--output_dir` | 全部 |
| 跑哪些场景 | `--scenes`（`nargs="*"`） | Stage 2 |
| 模型路径 | `--model_path` | Stage 1 / 2 |
| 方块初始位置 | `--block_pos x y z`（`nargs=3`） | Stage 1 |
| 接触判定阈值 | `--touch_threshold`（默认 `0.035`） | Stage 1 |
| 并行环境数 / 目标迭代 | `--num_envs` / `--max_iterations` | Stage 3 训练 |
| 只验哪个 demo | `--demo cloth\|sponge\|glass\|all` | Stage 4 验证门 |

### 3.2 必须改源码的（附「改哪一份」的坑）

| 想改 | 改哪里 | ⚠️ 陷阱 |
|---|---|---|
| **RL 超参**（学习率、网络、奖励权重…） | `stage3/train_subprocess.py` 里的 `get_train_cfg` / `get_cfgs` | **`train_subprocess.py` 自带一份副本，不 import `go2_train`**。只改 `go2_train.py` 对编排流程**完全无效**（静默） |
| **新增 Stage 2 场景** | `scene_factory.py` 复制一个场景字典 → 加进 `get_all_scene_configs()` | 必须**同步**改 `verify_stage2.py` 的 `EXPECTED_SCENES` 列表和 `len(scenes) != 8` 断言，否则验证门 FAIL |
| **Stage 4 判定阈值** | demo 顶部大写常量 | **同一批数值在 `verify_stage4.py` 的 `DEMOS` 字典里又写了一遍**。只改一边会出现「demo 自认为通过、verify 判 FAIL」 |
| **HuggingFace 缓存目录** | Stage 1/2 四个脚本顶部的 `os.environ[...] = ...` | 它在 `import torch` **之前硬写死**，在 shell 里 export 无效 |
| **相机分辨率 / 视角** | 场景字典的 `camera` 段；Stage 3 在 `eval_subprocess.py` 的 `camera_cfg` | Stage 3 的相机**必须在 `scene.build()` 之前**加，所以只能通过 `Go2Env(camera_cfg=...)` 注入，不能事后 `add_camera` |
| **训练/评测配置一致性** | 不用管 | 训练时配置会 pickle 到 `logs/<exp_name>/cfgs.pkl`，评测子进程优先读它 |

### 3.3 几个改之前要知道的数值现状

- Stage 3 的三个 command 区间**都退化成常量**（`lin_vel_x` 固定 `0.5`，y 与角速度固定 `0`）——当前只训练「以 0.5 m/s 直行」这一个命令。想训练转向要先把区间放开。
- `base_height` 奖励权重是 **−50.0**，比其它项高一到两个量级，是主导项。
- Stage 3 训练里 `save_interval` 被设成 **50**（不是官方的 100），这是为了让 `model_50.pt` 和 `model_100.pt` 都能落盘给编排器用。

---

## 4. 常见问题（高频 10 条）

> 只列最常撞的。**带着具体报错时，直接查 [`troubleshooting.md`](./troubleshooting.md) 顶部的「快速症状索引」表**（37 条现象 → `Qxx`），比这里全。

| 现象 | 一句话处理 | 详见 |
|---|---|---|
| `morphs has no attribute 'Franka'` | 1.2.2 没有这个 morph。从 `gs.__file__` 拼 `panda_bullet/panda.urdf` 用 URDF 加载 | `Q02` |
| `Unrecognized attribute 'surface'` | `surface` / `color` 要传给 `add_entity()`，**不是**传给 morph 构造函数 | `Q03` |
| `Link not found for name: hand` | 末端 link 叫 `panda_link7`，手指是 `panda_leftfinger` / `panda_rightfinger` | `Q04` |
| `Invalid input shape: (14,)` | IK 返回的是完整 `qpos`，控制前必须 `[motors_dof]` 切片 | `Q05` |
| 第二次 `gs.init()` 直接 segfault | **一个进程只能 init 一次**。批量评测全程只 init 一次靠 GC 回收场景；多阶段流程改用**子进程隔离**（Genesis 没有 `scene.destroy()`） | `Q15` |
| `Scene is already built.` | `add_camera` 带 `@assert_unbuilt`，必须在 `scene.build()` 之前加 | `Q17` |
| `render()` 的返回值当数组用就报错 | 1.2.2 的 `render()` 可能返回 tuple，取值前先 `isinstance(x, tuple)` 兜底（仓库里有 10 处这样的守卫） | `Q18` |
| 后台任务秒退、没有任何输出 | 后台 bash 不继承 conda/profile。用 `stage3/run_in_env.sh` 包装 | `Q23` |
| 正常的 MP4 被验证门判 FAIL | 编码名可能是 `mp4v` 也可能是 `mpeg4`，白名单要都收 | `Q24` |
| SPH 水直接炸开 | `dt` 必须 ≤ `4e-4`；`mu` 调大反而更不稳 | `Q34` |

**还有两条不是报错、但最耗时间的坑：**

- **柔性体被手指穿过去**：没有 IPC 时 FEM 求解器**根本不做刚-柔接触**（只积分内力）。别调参数，唯一可行的体积形变路径是 `PBD.Elastic`。→ `Q33`、`L08`
- **PBD 实体没有 `geom_start`、`get_contacts()` 用不了**：改用 `torch.cdist(finger_verts, particles)` 自己算最小距离当穿透量。→ `Q28`

---

## 5. 自检清单

**动手前**

- [ ] `genesis-world==1.2.2`、`rsl-rl-lib==5.0.1`、`numpy==1.26.4` 三个版本锁对了
- [ ] 没有装 `pyuipc`
- [ ] `ffprobe -version` 能跑（三个验证门都要它）
- [ ] 工作目录对：Stage 1/2 在 `<repo_root>`，Stage 3 在 `stage3/`，Stage 4 在 `stage4/`
- [ ] 长跑之前先 `--dry-run` / `gradient_test.sh` 探一遍（`L01`）

**跑完之后**

- [ ] 跑了对应的 `verify_stage2.py` / `verify_stage3.py` / `verify_stage4.py`，看的是 **exit code**，不是"我觉得视频看着还行"（`L03`）
- [ ] Stage 2 的 `verify` 显式传了 `--output_dir`（两边默认值不一致）
- [ ] 改过 Stage 4 阈值的话，demo 常量和 `verify_stage4.py` 的 `DEMOS` 字典**两边都改了**
- [ ] 改过 RL 超参的话，改的是 `train_subprocess.py` 那一份

**排查"改了没生效"时**

- [ ] 先 grep 到这个键/字段/函数名的**定义处或读取处**，确认它真的被读了（`L05`）
- [ ] 先量化"问题是否真的发生"，再动手修（`L02`）——看 `trajectory.json` 的逐步数值，不要看感觉

---

## 相关文档

- 代码在哪、怎么组织、哪里会静默失效 → [`code_knowledge.md`](./code_knowledge.md)
- 原理、API、能力边界（**1.3.3**） → [`background_knowledge.md`](./background_knowledge.md)（先在 [`00-index.md`](./00-index.md) 拿行号）
- 为什么这么做、试过哪些无效方法 → [`ai_knowledge.md`](./ai_knowledge.md)
- 按报错查 → [`troubleshooting.md`](./troubleshooting.md)
