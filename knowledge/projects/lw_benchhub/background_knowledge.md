# LW-BenchHub 原理层知识（background）

> **本文是什么** — 具身智能仿真工具链 **LW-BenchHub**（光轮智能 Lightwheel AI）的**原理层**参考：它是什么、怎么设计、有哪些 API、能力边界在哪。按仓库约定固定 9 章，章号跨项目稳定。
>
> **本文不是什么** — 不是踩坑记录，不是操作手册。要动手跑请走同目录 [`quickstart.md`](quickstart.md)；手上有报错请走 [`troubleshooting.md`](troubleshooting.md)；想知道复现时为什么那么选请走 [`ai_knowledge.md`](ai_knowledge.md)。
>
> **证据等级** — 每条结论都标注来源：
> - `[CODE]` 上游仓库源码，附仓库相对路径（必要时带行号），**工程决策只信这一级**
> - `[README]` 上游仓库文档（README / CITATION / docs）声明
> - `[官网]` 厂商官网市场材料，宣称值，未经代码验证
> - `[ISSUE]` 上游 GitHub issue 中用户报告的现象
> - `[推断]` 由前述证据推导，**证据不足以定论**
>
> **引用的三个上游仓库**（本机位于 `sources/lw_benchhub/`，换机器需重新 clone）：
> - `LW-BenchHub/` — 本体，`github.com/LightwheelAI/LW-BenchHub`
> - `IsaacLab-Arena/` — 上游依赖，`github.com/isaac-sim/IsaacLab-Arena`
> - `AutoDataGen/` — 配套自动数据生成管线，`github.com/LightwheelAI/AutoDataGen`
>
> 本文引用路径时用 `LW-BenchHub:` / `Arena:` / `AutoDataGen:` 前缀区分是哪个仓库。**未标前缀的默认是 LW-BenchHub。**
>
> **⚠️ 版本落差警告（读之前先看）** — 本文描述的是 LW-BenchHub `main`（commit `b2bcb2d`）与它**实际锁定的** Arena 版本，而不是 Arena 上游最新版。两者差了一个大版本，详见 §1.4。照抄 Arena 官方文档的命令**会失败**。

---

## 1. 项目概述

### 1.1 身份与定位

| 项 | 值 | 证据 |
|---|---|---|
| 名称 | **LW-BenchHub**（仓库名 `lw_benchhub`） | `[README]` `README.md:1` |
| 开发方 | **Lightwheel Team**（光轮智能，Lightwheel AI） | `[README]` `README.md:25`、`README.md:178` |
| 许可 | Apache License 2.0，Copyright 2025 Lightwheel Team | `[README]` `README.md:176-178` |
| 一句话定位 | "an end-to-end robotics simulation benchmark platform … specifically designed for evaluating robots in kitchen manipulation and loco-manipulation tasks" | `[README]` `README.md:25` |
| 建构基础 | NVIDIA **Isaac Lab-Arena**（作为 git submodule 置于 `third_party/`） | `[CODE]` `.gitmodules` |
| 官方文档 | `docs.lightwheel.net/lw_benchhub` | `[README]` `README.md:13` |
| 数据集 | Hugging Face `LightwheelAI/datasets` | `[README]` `README.md:17` |
| 引用条目 | `@software{Lightwheel_Team_LW-BenchHub_...}`，title "LW-BenchHub: Lightwheel's End-to-End Embodied AI Simulation Platform" | `[README]` `README.md:166-171` |

### 1.2 它解决什么问题

LW-BenchHub 的定位不是"又一个仿真器"，而是**评测集散地（benchmark hub）**。它自己不实现物理与渲染 —— 物理交给 PhysX、渲染交给 Isaac Sim 的 RTX，环境组装交给 Arena。它提供的是这四件被拼在一起、单独拿出来都不够用的东西：

1. **统一接口**（consistent interfaces）—— 让 7 类机器人、268 个任务共用同一套观测/动作/成功判定协议 `[README]` `README.md:7,29,32`
2. **成规模的真实场景** —— 10 布局 × 10 风格 = 100 套厨房配置，资产经 Lightwheel SDK 拉取 `[README]` `README.md:30`
3. **从遥操作到策略部署的完整数据链路** `[README]` `README.md:33`
4. **开箱即跑的大规模评测**（ready-to-run large-scale evaluation）`[README]` `README.md:7`

换句话说：它把"评测一个具身大模型"这件事从**每次都要自己搭**变成**改一个配置名**。这也是它把自己叫 hub 而不是 framework 的原因。

### 1.3 适用场景与不适用场景

**适用**（有直接证据支撑）：

| 场景 | 依据 |
|---|---|
| 评测通用操作策略（VLA / 模仿学习）在厨房操作任务上的成功率 | `[README]` `README.md:25,32` |
| 遥操作采集示教数据（键盘 / VR / 主从臂） | `[README]` `README.md:31,73-86` |
| 强化学习训练与评估（对接 rsl-rl、skrl） | `[README]` `README.md:34,109-131` |
| 复用已发布的大规模厨房操作数据集（21,500 episodes / 20,537,015 frames） | `[README]` `README.md:35` |
| loco-manipulation（移动+操作，如 Unitree G1、PandaOmron 底盘臂） | `[README]` `README.md:25,29` |
| 长时序组合任务（long-horizon compositional tasks） | `[README]` `README.md:32` |

**不适用 / 需要额外工作**：

| 场景 | 原因 | 依据 |
|---|---|---|
| Windows / macOS 开发 | 仅主要支持 Linux | `[README]` `README.md:42` |
| 无独立 NVIDIA GPU 的机器 | 硬性要求 NVIDIA GPU；光追效果依赖 RTX | `[README]` `README.md:42,46` |
| 非厨房域（工业装配、户外、驾驶） | 场景资产与任务库都围绕厨房构建 | `[README]` `README.md:25,30,32` |
| 需要稳定 API 的生产环境 | 底座 Arena 自我声明处于 **alpha**，"APIs will break … Do not use this in production" | `[README]` `Arena:README.md:23,212-221` |
| 需要 Python ≠ 3.11 | 上游按 3.11 装 | `[README]` `README.md:43,52` |

### 1.4 版本坐标与关键落差 ⚠️

这是使用本项目**最容易踩的第一个坑**，且不写清楚会导致后面每一章都被误读。

**LW-BenchHub 自己声明的环境** `[README]` `README.md:9-11,42-46`：

| 项 | 声明值 |
|---|---|
| Python | 3.11 |
| CUDA | 12.8（推荐） |
| NVIDIA 驱动 | 570.133.07（推荐） |
| badge 写的 "Isaac Lab" | **5.0.0** |

**但 `install.sh` 实际装的是** `[CODE]` `install.sh:1-25`：

```bash
uv pip install torch==2.7.0 torchvision==0.22.0 --index-url .../cu128
conda install pinocchio -c conda-forge -y
uv pip install "isaacsim[all,extscache]==5.0.0" --extra-index-url https://pypi.nvidia.com
```

**落差 1：README badge 的 "Isaac Lab 5.0.0" 是笔误，实际是 Isaac Sim 5.0.0。** `[推断]` 依据：Isaac Lab 的版本号序列是 1.x–3.x，从不存在 5.0.0；而 `install.sh:7` 装的 `isaacsim==5.0.0` 恰好是 5.0.0。Isaac Lab 本体由 `isaaclab.sh --install` 从 submodule 源码装，版本由 submodule 的 commit 决定，不由 pip 版本号决定 `[CODE]` `install.sh:12-17`。

**落差 2（更要紧）：本项目锁定的 Arena 是 v0.1.0 时代，不是 Arena 现在的 v0.2.x。**

| | LW-BenchHub 锁定的 Arena | Arena 上游 `main`（2026-08 抓取时） |
|---|---|---|
| commit | `c7b70779`（"Update docs link in the README. (#270)"） | `4357457` |
| 自称版本 | v0.1.0 时代 | **v0.2.x** |
| Isaac Lab | 2.3.0 | **3.0.0** |
| Isaac Sim | 5.0.0 | **6.0.0** |
| Python | ≥ 3.10（`py_version = 310`） | **≥ 3.12** |

证据：`[CODE]` `.gitmodules` 声明 submodule；`git ls-tree HEAD third_party/` 得到 pin `160000 commit c7b70779…`；`Arena:README.md:203-210` 的版本兼容表给出各分支对应关系；pin 处 `Arena:pyproject.toml` 的 `[tool.isort] py_version = 310`。

**这意味着：**

- Arena 官方文档站（`isaac-sim.github.io/IsaacLab-Arena/main/`）描述的是 0.2.x，**它的安装命令、`uv sync`、`policy_runner.py --viz kit` 这些在本项目里不一定存在或不一定同名**。要查 Arena 的 API，读 pin 住的那个 commit，别读官网。
- Arena 现在的 README 里那些标 "New" 的特性（Sequential Task Chaining、Natural Language Object Placement、异构并行评测）`[README]` `Arena:README.md:57-61`，**不能假设 LW-BenchHub 已经有**。是否存在要逐个到 pin 版本里 grep 验证。
- 反过来，Arena `main` 已把 `extension.toml` 的 `version` 留在 `0.1.0` 没跟着改 `[CODE]` `Arena:extension.toml:4` —— **判断 Arena 版本要看 README badge，不要看 `extension.toml`**。这是一个会误导人的陷阱。

### 1.5 生态位置

Arena 官方 README 把 LW-BenchHub 列为已发布基准之一，且明确说 Arena 的"评测与任务层是与 Lightwheel 紧密合作设计的" `[README]` `Arena:README.md:230-232,292`：

- **Lightwheel RoboCasa Tasks** — "138+ open-source tasks, 50 datasets per task, 7+ robots"
- **Lightwheel LIBERO Tasks** — "Adapted LIBERO benchmarks"
- **Lightwheel RoboFinals** — 高保真工业基准（另一个仓库）

也就是说 LW-BenchHub 与 Arena 不是单纯的"下游用上游"，而是**共同设计**关系。这解释了为什么 LW-BenchHub 能把 Arena 的 `third_party/` 原样保留（"preserved in their original form as much as possible"）还能跑通 `[README]` `README.md:146`。

配套还有 **AutoDataGen**（`github.com/LightwheelAI/AutoDataGen`）：LLM 任务分解 + cuRobo 运动规划 + 导航，把"Isaac Lab 里的一个任务"自动变成可执行技能序列并产出轨迹数据 `[README]` `AutoDataGen:README.md:3-16`。它在 LW-BenchHub 里以 `lw_benchhub/autosim/` 的形式出现 `[README]` `AutoDataGen:README.md:148-162`。

### 1.6 三个最值得注意的点（索引用摘要）

1. **它是评测集散地而非仿真器**。物理/渲染全部下沉给 Isaac Sim + PhysX，Arena 负责环境组装，LW-BenchHub 贡献的是统一接口、268 个厨房任务、100 套场景配置和 21,500 条示教数据 —— 价值在"标准化"而不在"仿真能力"。
2. **版本落差是第一坑**。README badge 的 "Isaac Lab 5.0.0" 实为 Isaac Sim 5.0.0；且它锁定的 Arena 是 v0.1.0 时代（Isaac Lab 2.3 / Python≥3.10），与 Arena 上游 v0.2.x（Isaac Lab 3.0 / Python≥3.12）差一个大版本，**照抄 Arena 官网命令会失败**。
3. **底座自称 alpha**。Arena 明确写 "APIs will break without deprecation warnings … Do not use this in production"，所以任何基于本工具链的长期工程都要预留接口漂移的成本。

---

## 2. 核心原理

### 2.1 一句话机制

> LW-BenchHub 把 **Gymnasium 的注册表当成"组件注册表"** 用：场景、机器人、任务、RL 配置各自注册成独立的 gym id，运行时按 `场景 × 机器人 × 任务 × RL` 四路组合解析成一个 `IsaacLabArenaEnvironment`，再交给 Arena 的构建器产出标准的 `ManagerBasedRLEnvCfg`。所有仿真行为本身由 Isaac Lab / Isaac Sim 执行，本仓库只负责**组装与接线**。

它不实现仿真器、不实现 manager 系统、不实现 RL 算法 `[CODE]` `lw_benchhub/utils/env.py:73-157`。理解这一层是理解全部报错的前提：**绝大多数故障不在"仿真算错了"，而在"组合没解析对"**。

### 2.2 四路组合的解析流程

核心函数是 `parse_env_cfg()` `[CODE]` `lw_benchhub/utils/env.py:169`，它做五件事，顺序固定：

| 步骤 | 位置 | 做什么 |
|---|---|---|
| 1 | `lw_benchhub/utils/env.py:224-258` | 把 CLI + YAML 的所有选项灌进全局单例 `Context` |
| 2 | `lw_benchhub/utils/env.py:259` | `discover_and_import_lw_benchhub_modules()` — 强制 import 所有注册模块，触发 339 次 `gym.register` |
| 3 | `lw_benchhub/utils/env.py:266-278` | 4 次 `load_cfg_cls_from_registry()`，把名字换成配置类 |
| 4 | `lw_benchhub/utils/env.py:286-292` | 组装 `IsaacLabArenaEnvironment` |
| 5 | `lw_benchhub/utils/env.py:298-299` | `LwEnvBuilder(...).build_registered()` 产出 `(env_name, cfg)` |

组合的那几行是全仓库最值得记住的代码 `[CODE]` `lw_benchhub/utils/env.py:286-299`：

```python
isaaclab_arena_environment = IsaacLabArenaEnvironment(
    name=task_name,
    embodiment=robot(enable_cameras=enable_cameras),
    scene=scene(),
    task=task(),
    orchestrator=LwBaseOrchestrator(),
    teleop_device=teleop_device,
)
arena_builder = LwEnvBuilder(isaaclab_arena_environment, args, rl() if rl else rl)
env_name, cfg = arena_builder.build_registered()
```

**组件 id 的构造公式**是 `{Backend}-{Type}-{Name}` `[CODE]` `lw_benchhub/utils/env.py:111-113`：

```python
assert cfg_type in ["scene", "task", "robot", "rl"]
cfg_name = f"{backend.capitalize()}-{cfg_type.capitalize()}-{cfg_name}"
cfg_entry_point = gym.spec(cfg_name).kwargs.get(entry_point_key)
```

所以 `Robocasa-Robot-G1-Hand`、`Robocasa-Scene-Libero`、`Robocasa-Task-LiftObj`、`Robocasa-Rl-LeRobotLiftObjStateRL` 都是合法 id。**注意 `.capitalize()` 只大写首字母并把其余字母小写**，这是 `--task`/`--robot` 传参大小写敏感问题的根源。

组件被发现的契约写在 `pyproject.toml` 里 `[CODE]` `pyproject.toml:39-43`：

```toml
[project.entry-points.lw_benchhub_modules]
lw_benchhub_scences = "lw_benchhub.core.scenes"     # [sic] 拼写为 scences
lw_benchhub_robots  = "lw_benchhub.core.robots"
lw_benchhub_tasks   = "lw_benchhub_tasks"
lw_benchhub_rl      = "lw_benchhub_rl"
```

**第二层注册**：每个入口脚本在运行时另外合成并注册一个复合 id，公式 `Robocasa-{task}-{robot}-v0`，全部指向 `entry_point="isaaclab.envs:ManagerBasedRLEnv"` `[CODE]` `lw_benchhub/scripts/rl/train.py:111-113`、`lw_benchhub/scripts/env_server.py:87-89`、`lw_benchhub/scripts/rl/play.py:105-109`。

一个容易踩的分支：`env_server.py` 与 `maniskill_ppo/train.py` 会检查 `"-" in cfg.task` —— **任务名里带短横线就绕过 LW-BenchHub 自己的 `parse_env_cfg`，直接交给上游 `isaaclab_tasks.utils.parse_env_cfg`** `[CODE]` `lw_benchhub/scripts/env_server.py:55`、`lw_benchhub/scripts/maniskill_ppo/train.py:58-67`。

### 2.3 全局可变单例 `Context`

所有跨模块的运行时选项走一个 `@dataclass Context` `[CODE]` `lw_benchhub/core/context.py:25`，约 35 个字段（`scene_name`、`robot_name`、`execute_mode`、`enable_cameras`、`add_camera_to_observation`、`num_envs`、`device`、`use_fabric`、`replay_cfgs`、`max_scene_retry=5`、`max_object_placement_retry=3` 等），模块级变量 `CURRENT_CONTEXT` `[CODE]` `lw_benchhub/core/context.py:21`，由 `get_context()` 懒创建 `[CODE]` `lw_benchhub/core/context.py:59`。

这是**设计上的单一真相源，也是并发与可复现性的薄弱点**：任何模块都能在任何时刻改它，谁最后写谁生效。已确认的两处后果 `[CODE]`：

- `device` 字段**声明了两次**（`lw_benchhub/core/context.py:32` 与 `:51`），后者胜出，默认 `"cpu"`。
- `parse_env_cfg` 会写 `context.enable_global_illumination` 与 `context.enable_full_local_scene` `[CODE]` `lw_benchhub/utils/env.py:250-251`，但这两个**不是 `Context` 的声明字段**。dataclass 不阻止动态赋值，所以不报错，只是无法从类定义看出它们存在。

上游 issue #29（`cfg.headless` 被 `AppLauncher` 默认值静默覆盖）在结构上就是这个模式的产物 —— 详见 §8。

### 2.4 `ExecuteMode`：同一套配置的 9 种运行语义

`ExecuteMode` 枚举 `[CODE]` `lw_benchhub/utils/env.py:46`：`TRAIN=0, EVAL=1, TELEOP=2, REPLAY_JOINT_TARGETS=3, REPLAY_ACTION=4, REPLAY_STATE=5, TEST_OBJECT=6, TEST_FIXTURE=7, REPLAY_TELEOP=8`。字符串转换函数 `str_to_execute_mode()` 会规范化大小写和下划线，**匹配不上时默认回落到 `TELEOP`** `[CODE]` `lw_benchhub/utils/env.py:60` —— 拼错模式名不会报错，而是静默进了遥操作模式。

模式不是标签，它真的改变行为，三个已确认的分支点 `[CODE]`：

| 行为 | 受模式控制的方式 | 位置 |
|---|---|---|
| 哪些相机被实例化 | 每个相机声明自带 `execute_mode` 白名单，`_setup_camera_config()` 只装匹配当前模式的 | `lw_benchhub/core/robots/robot_arena_base.py:204-221` |
| 是否录制 | 仅当模式**不是** TRAIN/EVAL/REPLAY_STATE 时才返回真的 `RecorderManagerCfg()` | `lw_benchhub/core/robots/robot_arena_base.py:222-224` |
| 成功判定是否生效 | 任务的 `_check_success` 在 TRAIN 模式下短路返回全 False（训练走 reward shaping，不走成功信号） | `lw_benchhub_tasks/lightwheel_robocasa_tasks/single_stage/lift_obj.py:85` |
| UI 窗口 | TELEOP 模式下把 `ui_window_class_type` 置空 | `lw_benchhub/core/cfg/__init__.py:21-23` |

### 2.5 对 isaaclab 的 monkey patch（上游 10 处）

> ⚠️ **数字更正（2026-08 复核）**：本节原标题写"9 处"，但下表本身就有 **10 行** —— 上游实为 **10 处**，`monkey_patch.py:681-690` 连续调用 10 个补丁函数 `[CODE]`。
> 本机复现仓库 `lw_benchhub_tour` 里是 **11 处** —— 本地新增了第 11 个补丁 `patch_xform_prim_view_auto_standardize`（`:708-743`，强制 `validate_xform_ops=False`，用于绕过 Isaac Sim 5.1 的 xformOp 顺序硬校验），并因此使本节所有行号在该仓库中下移。
> **要在本机改补丁、或需要带行号的完整补丁表，看代码层** → [`code_knowledge.md`](code_knowledge.md) §3.1（M1 模块，11 行全表）与 §6.2 #1（改动归因）、§6.6／§8.4（本条更正的出处）。

`lw_benchhub/core/__init__.py` 只有一行 `from lw_benchhub.utils import monkey_patch`，因此**只要 import 了 `lw_benchhub.core`，全部补丁就已经打上了**，无法选择性关闭 `[CODE]` `lw_benchhub/utils/monkey_patch.py:681-690`。

| 补丁函数 | 位置 | 改了 isaaclab 的什么 |
|---|---|---|
| `patch_reset` | `:21` | `ManagerBasedRLEnv.reset` |
| `patch_configclass` | `:101` | `isaaclab.utils.configclass._validate` —— 放行非字符串 dict key |
| `patch_recorder_manager_ep_meta` | `:131` | `RecorderManager.export_episodes` |
| `patch_recorder_manager_joint_targets` | `:167` | `RecorderManager.record_pre_physics_step`、`EpisodeData` |
| `patch_step` | `:301` | `ManagerBasedRLEnv.step`，并新增 `reset_to_check_state` |
| `patch_yaml_load` | `:463` | yaml loader |
| `patch_reward_manager` | `:482` | `RewardManager.compute` |
| `patch_create_teleop_device` | `:521` | `teleop_device_factory` 的 `DEVICE_MAP`/`RETARGETER_MAP`，注入自研 VR/键盘/Leader-Arm 设备 |
| `patch_isaaclab_tasks_mdp` | `:579` | 通过替换 `spec.loader.exec_module` **重新注入"已从 isaaclab_tasks 删除但 gr1t2.py 还在用"的函数** `:603` |
| `patch_termination_manager` | `:648` | `TerminationManager.compute` —— 修 per-term `_term_dones` 记账 |

`patch_isaaclab_tasks_mdp` 尤其值得记住：它是**上游 API 已删、本仓库靠补丁续命**的直接证据，也是"换 isaaclab 版本很容易炸"的原因。

其中 `patch_step` 重写了整个环境步进循环 `[CODE]` `lw_benchhub/utils/monkey_patch.py:40-79`，是理解渲染时机的关键，见 §2.6.10。

### 2.6 传感器仿真原理（详解）

> 本节是本文档最长的一节，因为"传感器到底怎么仿真的"决定了这套工具链能做什么样的评测。**结论先行：本工具链没有任何自研传感器模型，也没有任何传感器噪声模型。**

#### 2.6.1 总原则：LW-BenchHub 与 Arena 都只是传感器的"配置层"

两个仓库里**没有一行传感器物理仿真代码**。每一个传感器都是 Isaac Lab 的传感器类（`isaaclab.sensors.*`），从一个配置 dataclass 实例化出来；真正的仿真发生在 **Omniverse RTX（相机）** 与 **PhysX（接触）** 里 `[CODE]`。

两个仓库贡献的是四件事，仅此而已：

1. **有哪些传感器**（相机槽位、接触传感器挂在哪个 link）
2. **装在哪里**（USD prim 路径与位姿）
3. **内参与更新率**（分辨率、焦距、光圈、裁剪面、`update_period`）
4. **输出如何进入 observation 字典**（哪个 obs group、是否拼接、是否过编码器）

因此凡是问"这个工具链的传感器噪声/畸变/延迟模型是怎样的"，答案都是**未提及**——它继承 Isaac Sim 的默认行为。

#### 2.6.2 相机：USD 针孔模型 + RTX 实时渲染

**传感器类**：LW-BenchHub 直接声明 `TiledCameraCfg` `[CODE]` `lw_benchhub/core/robots/agilex/piper.py:52-168`、`lw_benchhub/core/robots/unitree/g1.py:210-460`、`lw_benchhub/core/robots/arx/x7s.py:58-135`；Arena 侧用自己的包装类 `ArenaCameraCfg` `[CODE]` `Arena:isaaclab_arena/utils/cameras.py:24`，它持有 `CameraCfg` 的字段并按需转成 tiled 版本。

**成像模型**：全部内参来自 `sim_utils.PinholeCameraCfg`，即一个**纯 USD 针孔相机**，焦距与光圈用 USD 的"十分之一场景单位"约定 `[CODE]`。**没有配置任何畸变模型、卷帘快门模型或曝光/自动曝光模型** —— 这是整个工具链视觉 sim2real 的硬边界。

已确认的九组相机内参 `[CODE]`：

| 相机 | 位置 | H×W | focal_length | h_aperture | clipping | update_period |
|---|---|---|---|---|---|---|
| Piper（6 路） | `lw_benchhub/core/robots/agilex/piper.py:52-168` | 480×480 | 40.6 | 38.11 | (0.01, 3.0) | 0.05 |
| G1 躯干相机 | `lw_benchhub/core/robots/unitree/g1.py:210-460` | 224×224 | 19.3 / 24.0 | 27.7（注释写"为 60° FOV 调整"） | (0.1, 1.0e5) | 0.05 |
| G1 手部相机 | `lw_benchhub/core/robots/unitree/g1.py:210-460` | 224×224 | 24.0 | 27.7 | (0.01, 50.0) | 0.05 |
| X7S（6 路） | `lw_benchhub/core/robots/arx/x7s.py:58-135` | 224×224 | 19.3 / 24.0 | 未提及 | (0.1, 1.0e5) | 0.05 |
| Arena Franka `wrist_cam` | `Arena:isaaclab_arena/embodiments/franka/franka.py:282-297` | 84×84 | 2.8 | 5.376 / v 3.024 | 默认 | 0.0 |
| Arena GR1T2 `robot_pov_cam` | `Arena:isaaclab_arena/embodiments/gr1t2/gr1t2.py:348-363` | 512×512 | 18.15 | 未提及 | (0.01, 1.0e5) | 0.0 |
| Arena G1 `robot_head_cam` | `Arena:isaaclab_arena/embodiments/g1/g1.py:489-507` | 480×640 | 15 | 未提及 | (0.1, 5) | 0.0 |
| Arena DROID 外部相机 ×2 | `Arena:isaaclab_arena/embodiments/droid/droid.py:487-530` | 720×1280 | 2.1 | 5.376 / v 3.024 | 默认 | 0.0 |
| Arena DROID `wrist_camera` | `Arena:isaaclab_arena/embodiments/droid/droid.py:487-530` | 720×1280 | 2.8 | 5.376 | 默认 | 0.0 |

两处系统性差异值得记住 `[CODE]`：

- **LW-BenchHub 的相机 `update_period=0.05`（20 Hz），Arena 的全是 `0.0`（每个 env step 都刷新）**。LW-BenchHub 的相机节拍因此**与 50 Hz 控制率解耦** —— 一帧图像会被连续多个控制步复用。做 VLA 闭环时这是"图像看起来滞后"的正常来源，不是 bug。
- LW-BenchHub 统一 `focus_distance=400.0` + `lock_camera=True`；Arena 用 `focus_distance=28.0`。Arena 的 DROID/Franka 焦距-光圈组合（2.1 / 5.376×3.024）是**物理镜头参数化**，LW-BenchHub 的（40.6 / 38.11）是**按 FOV 反算的合成值**。两者不可互相套用。

**渲染模式**：`rendering_mode`、`RenderCfg(rendering_mode=...)`、`/rtx/rendermode`、`PathTracing` 在两个仓库中**均未提及**。二者都跑默认的 **RTX 实时渲染器（光栅 + 光追）**，不是路径追踪。

#### 2.6.3 Tiled rendering：默认开启，且与随机化互斥

Arena 的 `ArenaCameraCfg` 有 `_use_tiled_camera: ClassVar[bool] = True` `[CODE]` `Arena:isaaclab_arena/utils/cameras.py:32`，即**平铺渲染是 Arena 所有 embodiment 的默认**；`_as_tiled_camera_cfg()` 把除 `class_type` 外的所有 init 字段拷进一个 `TiledCameraCfg` `[CODE]` `Arena:isaaclab_arena/utils/cameras.py:69`。

机制上的区别：**tiled 相机把所有并行环境渲进同一张大纹理，共享一个 USD sensor prim；untiled 相机每个环境各自 spawn 一个 sensor prim。** 这个区别直接决定了两件事：

1. **吞吐**：几百个并行环境时，tiled 是唯一可行的方案。
2. **随机化不可用**：per-env 改内参会"穿透"到所有 tile —— Arena 源码注释原话是 tiled 相机 "share one USD sensor across envs, so a per-env intrinsic edit would leak across all tiles" `[CODE]` `Arena:isaaclab_arena/variations/camera_intrinsics_variation.py`。

由此产生本工具链**最值得记住的一处隐式耦合**：`CameraIntrinsicsBuildTimeVariation` 的 `_prepare_at_build_time()` 会调 `self._camera_rig.set_use_tiled_camera(False)` `[CODE]` `Arena:isaaclab_arena/variations/camera_intrinsics_variation.py` —— **一旦开启相机内参随机化，平铺渲染被静默关闭**，USD sensor prim 数量从 1 变成 `num_envs`，高并行下渲染开销会直接主导整个仿真。开了随机化又发现吞吐暴跌，原因就在这里。

LW-BenchHub **不使用** `ArenaCameraCfg`，它直接声明 `TiledCameraCfg`，但会借用 Arena 的 `make_camera_observation_cfg` 来接 observation `[CODE]` `lw_benchhub/core/robots/robot_arena_base.py:209`。

#### 2.6.4 相机默认是关的：两道闸门

这是新用户最高频的困惑（对应上游 issue #33，见 §8）。相机要出图，必须同时满足：

```python
if self.enable_cameras and self.camera_config and self.add_camera_to_observation:
```

`[CODE]` `lw_benchhub/core/robots/robot_arena_base.py:205-221`。而 **`enable_cameras` 与 `add_camera_to_observation` 两个开关的默认值都是 `False`** `[CODE]` `lw_benchhub/core/context.py:37`、`lw_benchhub/core/context.py:53`。

打开它们的三条已知路径 `[CODE]`：

| 方式 | 位置 |
|---|---|
| YAML 里写 `enable_cameras: true` | `configs/rl/skrl/lerobot_liftobj_visual.yaml`、`configs/data_collection/teleop/x7s.yaml` |
| 脚本硬编码 `replay_cfgs={"add_camera_to_observation": True}` | `lw_benchhub/scripts/policy/eval_policy.py:121` |
| 由 `--record` 推导 `bool(app_launcher._enable_cameras and args.record)` | `lw_benchhub/scripts/policy/replay_local_scene.py:107` |

另外 `--video` 会隐式把 `enable_cameras` 设成 `True` `[CODE]` `lw_benchhub/scripts/teleop/teleop_main.py:41-42`。回放时分辨率可覆盖：`modify_observation_cameras()` 用 `context.replay_cfgs["render_resolution"]` 改写 `camera_cfg.width/height` `[CODE]` `lw_benchhub/core/robots/robot_arena_base.py:196-202`。

注意区分：`first_person_view` 是**观察视角**开关，不是传感器 `[CODE]` `lw_benchhub/core/context.py:35`。

#### 2.6.5 数据类型：**每一个相机都只声明 `data_types=["rgb"]`**

已在两个仓库的全部 9 组相机上核实 `[CODE]`。唯一例外是绿幕合成时在运行时追加的 `semantic_segmentation` `[CODE]` `lw_benchhub_rl/lift_obj/lift_obj.py:337-339`：

```python
if 'semantic_segmentation' not in camera_cfg.data_types:
    camera_cfg.data_types.append('semantic_segmentation')
camera_cfg.colorize_semantic_segmentation = False
```

标签 id 从 `scene.sensors[cam].data.info['semantic_segmentation']['idToLabels']` 取回，由打过补丁的 reset 每个 episode 调一次 `[CODE]` `lw_benchhub/utils/monkey_patch.py:320-397`。

**observation 侧**：图像项是 `mdp.image`（原始张量）和 `mdp.image_features`（冻结编码器）。Arena 为每个 (相机, data_type) 组合生成一个 obs term，group 名固定为 `camera_obs`，并设 `enable_corruption = False; concatenate_terms = False` `[CODE]` `Arena:isaaclab_arena/utils/cameras.py:104-137`。视频录制器消费的就是这个 key `[CODE]` `Arena:isaaclab_arena/video/camera_observation_video_recorder.py`。

LW-BenchHub 的视觉 RL 配置混用两种：`hand_camera`/`d435_camera` 走 `mdp.image_features` + `resnet18`，`global_camera` 走原始 `mdp.image` `[CODE]` `lw_benchhub_rl/lift_obj/lift_obj.py:64-135`。可选编码器包括 Theia（`theia-tiny/small/base-patch16-224-cddsv/cdiv`）与 ResNet（`resnet18/34/50/101`）`[CODE]` `lw_benchhub_rl/lift_obj/mdp/observations.py`。

#### 2.6.6 本体感知：纯运动学查询，无编码器模型

本体感知就是 Isaac Lab 的标准 MDP observation term，作用在 articulation 上 —— **没有编码器模型、没有量化、没有延迟、没有噪声** `[CODE]`。

已确认存在的量 `[CODE]`：

| 量 | term | 位置 |
|---|---|---|
| 关节位置 | `joint_pos_rel` / `joint_pos` | `Arena:isaaclab_arena/embodiments/franka/franka.py:302-321` 等 |
| 关节速度 | `joint_vel_rel` / `joint_vel` | 同上 |
| 关节目标（下发值） | `get_target_qpos`（读 `robot._data.joint_pos_target`） | `lw_benchhub/core/mdp/observations.py:77` |
| 末端位姿 | `ee_frame_pos`/`ee_frame_quat`/`ee_pos`/`ee_quat`/`ee_pose`/`get_eef_base` | `lw_benchhub/core/mdp/observations.py:46-156` |
| 夹爪开度 | `gripper_pos` | `lw_benchhub/core/mdp/observations.py:106` |
| 指尖位置 | `fingertips_pos` | `lw_benchhub/core/mdp/observations.py:38` |
| 末端-物体距离 | `rel_ee_object_distance` | `lw_benchhub/core/mdp/observations.py:30` |
| 根位姿 / 全 link 状态 | `root_pos_w`、`root_quat_w`、`get_all_robot_link_state` | `Arena:isaaclab_arena/embodiments/gr1t2/gr1t2.py:371-402` |
| 上一步动作 | `last_action` | 同上 |

**关节力矩（effort/torque）作为 observation term：未提及。** 两个仓库都没有 `joint_effort`/`applied_torque`/`computed_torque` 观测项，也没有声明任何关节力矩传感器 `[CODE]`。要做力控或阻抗类研究，这是需要自己补的第一个洞。

末端位姿是用 **`FrameTransformer`** 测的 —— 一个运动学查询，不是物理传感器 `[CODE]` `Arena:isaaclab_arena/embodiments/franka/franka.py:245`。也就是说末端位姿是**精确无误差**的，不存在真实机器人上的标定误差。

#### 2.6.7 接触力：PhysX 接触上报

接触感知是 `isaaclab.sensors.ContactSensorCfg`，即 **PhysX 的接触上报**。消费两个张量 `[CODE]`：

- `data.net_forces_w` —— 传感器 body 上的合力，例 `lw_benchhub/core/robots/arx/x7s.py:606-607`。
- `data.force_matrix_w` —— per-(传感器 body × 被过滤 body) 的力，形状 `(N, B, M, 3)`，例 `Arena:isaaclab_arena/tasks/predicates/spatial.py:195-228`（断言 B=1 且 M=1）。

`force_matrix_w` 要有值，必须给 `filter_prim_paths_expr`；各处声明并不一致 `[CODE]`：

| 传感器 | `filter_prim_paths_expr` | 位置 |
|---|---|---|
| Piper `base_contact` | `[".../Scene/floor*"]` | `lw_benchhub/core/robots/agilex/piper.py:52-168` |
| G1 夹爪接触 | 已设置 | `lw_benchhub/core/robots/unitree/g1.py:254-266` |
| X7S ×4（link12/13/21/22） | `[]` —— **只有合力，没有分项力** | `lw_benchhub/core/robots/arx/x7s.py:176-280` |
| Fixture 自动挂载 `{name}_contact` | `[]` | `lw_benchhub/core/models/fixtures/fixture.py:305-338` |
| Arena Kuka-Allegro 四指尖 | `["{ENV_REGEX_NS}/Object"]` | `Arena:isaaclab_arena/embodiments/kuka_allegro/kuka_allegro.py:37-72` |

统一设置：`update_period=0.0`（每个物理步都更新）、**`history_length=1`（不缓存接触历史）**、`debug_vis=False` `[CODE]`。物体侧还需要把 `_get_spawn_cfg(activate_contact_sensors=...)` 打开 `[CODE]` `Arena:isaaclab_arena/assets/object_base.py:194-200`。

**接触力作为 observation，全仓库只有一处** `[CODE]` `Arena:isaaclab_arena/embodiments/kuka_allegro/kuka_allegro.py:43-47`：四个指尖的 body 系 3 维力，裁剪到 ±20 N（且该 embodiment 完全没有相机）。**其他地方接触力只用于任务判定，不进观测**：`object_on_destination()` 用 `‖force‖ ≥ 1.0 N` 加 `velocity_threshold=0.5` `[CODE]` `Arena:isaaclab_arena/tasks/predicates/spatial.py:195-228`。

#### 2.6.8 深度 / 激光 / IMU / 触觉：**四类传感器全部未提及**

这一小节记录的是**经 grep 确认的缺失**，不是"没找到"。做技术选型时这是最有价值的部分。

**（1）仿真深度：未提及。** 没有任何相机在 `data_types` 里列 `depth`/`distance_to_camera`/`distance_to_image_plane`（全部是 `["rgb"]`）；没有立体相机组、没有视差计算、没有结构光或红外投射器模拟；也没有深度噪声模型（无量化、无空洞/dropout、无随距离变化的方差）`[CODE]`。

两处**看着像深度但不是**的东西，特别标出以免误判：

- `lw_benchhub_rl/lift_obj/mdp/observations.py` 的 docstring 提到 `convert_perspective_to_orthogonal` "仅当 data type 是 `distance_to_camera` 时使用" —— 这是从 Isaac Lab 继承来的参数文档，对应代码路径**从未被执行**，因为同文件的 `overlay_image()` 直接 `assert data_type == "rgb"` `[CODE]`。
- `lw_benchhub/utils/lerobot_common/cameras/realsense/` 是**真实硬件**的 RealSense 驱动，属于 sim2real 栈，不是仿真深度传感器 `[CODE]`。

同理，G1 的 `d435_camera` 这个名字指的是**一台真实 D435 的安装位姿**，该位姿上的仿真传感器是纯 RGB `[CODE]` `lw_benchhub/core/robots/unitree/g1.py:210-460`。

**（2）射线投射器 / 激光雷达：未提及。** 两个仓库都没有 `RayCaster`、`RayCasterCfg`、`RayCasterCamera`、`RayCasterCameraCfg`，也没有任何 `patterns.*` 配置（`GridPatternCfg`、`LidarPatternCfg`、`BpearlPatternCfg`、`PinholeCameraPatternCfg`），没有高度扫描器 `[CODE]`。**因此这套栈里没有激光雷达、没有 raycast 深度、也没有地形高度观测** —— 移动机器人/足式导航方向要另找工具链。

**（3）IMU：未提及。** 没有 `Imu`/`ImuCfg`/`imu` 传感器声明，也没有基座线加速度/角加速度观测项 `[CODE]`。唯一能被 grep 到 "imu" 的是 sim2real 代码里的 `IMUKF(process_noise, measurement_noise)` —— 那是给**真实机器人** IMU 数据流用的卡尔曼滤波器，它的 `process_noise`/`measurement_noise` 是滤波器调参，**不是加在仿真数据上的传感器噪声模型** `[CODE]` `lw_benchhub/sim2real/`。

**（4）触觉阵列 / 六维力矩传感器：未提及。** 两个仓库都搜不到 "tactile"；也没有任何关节或腕部的六轴力矩传感器声明。能拿到的天花板就是夹爪 link 上的 `net_forces_w`（一个求和后的接触力，**没有力矩分量**）`[CODE]`。

#### 2.6.9 传感器噪声模型：**不存在，且有一个假开关**

`NoiseCfg`、`GaussianNoiseCfg`、`UniformNoiseCfg`、`NoiseModelCfg` 在两个仓库中**均未提及**，也没有任何地方从 `isaaclab.utils.noise` import 东西 `[CODE]`。

`enable_corruption`（那个"本应"启用 per-term `noise` 配置的开关）的分布 `[CODE]`：

- Arena 侧**处处为 `False`**：`Arena:isaaclab_arena/utils/cameras.py:126` 等。
- LW-BenchHub 侧 `False`：`lw_benchhub/core/robots/arx/x7s.py:77`。
- LW-BenchHub 侧 `True`：`lw_benchhub/core/tasks/base.py:71`、`lw_benchhub_rl/lift_obj/lift_obj.py:71`、`:113`。

**但为 `True` 的地方它是空转的**：两个仓库里没有任何一个 `ObsTerm` 传了 `noise=` 参数，所以"启用了对一个空集合的扰动"。**净效果：所有观测都是无噪声的理想值。**

再排除一个假阳性：从 LW-BenchHub 引用到的 Isaac Lab Mimic datagen 里的 `action_noise` 是数据生成时注入到**动作空间**的噪声，不是传感器噪声 `[CODE]`。

> **工程含义**：任何基于本工具链得出的"策略鲁棒性"结论，都是在**无传感器噪声**条件下得到的。要做噪声鲁棒性评测，必须自己加 `NoiseCfg`，或在 policy 侧的 `encode_obs` 里注入。

#### 2.6.10 物理与渲染的节拍：三元组 `sim.dt × decimation × render_interval`

传感器的"何时被采样"由这三个数决定，而它们在不同配置里**并不一致** `[CODE]`：

| 配置 | `sim.dt` | `decimation` | 控制率 | `render_interval` | 位置 |
|---|---|---|---|---|---|
| Arena 基类 | 1/120 | 8 | **15 Hz** | 2 | `Arena:isaaclab_arena/environments/isaaclab_arena_manager_based_env_cfg.py` |
| Arena `set_control_rate_50hz()` | 1/200 | 4 | 50 Hz | — | 同上 `:100` |
| Arena 装配预设 | 1/60 | 2 | 30 Hz | 2 | `Arena:isaaclab_arena_environments/mdp/env_callbacks.py:44-72` |
| **LW-BenchHub 任务基类** | 1/100 | 2 | **50 Hz** | 4（**25 Hz 渲染**） | `lw_benchhub/core/tasks/base.py:234-254` |
| **LW-BenchHub RL 基类** | 0.01 | 5 | **20 Hz** | `= decimation` | `lw_benchhub/core/rl/base.py:71-86` |
| LW-BenchHub G1 覆盖 | 1/200 | 4 | 50 Hz | — | `lw_benchhub/core/robots/unitree/g1.py:997-1001` |

注意 **RL 路径的控制率是 20 Hz，遥操作/回放路径是 50 Hz** —— 采数据和训练不在同一节拍上，这是复现时对不齐的常见来源。RL 基类另外设 `episode_length_s = 3.2` `[CODE]` `lw_benchhub/core/rl/base.py:71-86`。

**渲染只在两种情况下发生**，这是被 patch 过的 step 循环决定的 `[CODE]` `lw_benchhub/utils/monkey_patch.py:40-79`：

```python
is_rendering = self.sim.has_gui() or self.sim.has_rtx_sensors()
for _ in range(self.cfg.decimation):
    self._sim_step_counter += 1
    self.action_manager.apply_action(); self.scene.write_data_to_sim()
    self.sim.step(render=False)
    if self._sim_step_counter % self.cfg.sim.render_interval == 0 and is_rendering:
        self.sim.render()
    self.scene.update(dt=self.physics_dt)
```

即：**只有存在 GUI 或存在 RTX 传感器时才渲染，且只在每 `render_interval` 个物理子步渲染一次**。两个相关的补救机制 `[CODE]`：

- `if self.sim.has_rtx_sensors() and self.cfg.rerender_on_reset: self.sim.render()` `lw_benchhub/utils/monkey_patch.py:62`、`:381`、`:445` —— 保证 reset 后第一帧不是上一 episode 的残留。LW-BenchHub 设 `rerender_on_reset = True` `lw_benchhub/core/tasks/base.py:234-254`。
- 纹理加载屏障：`if self.cfg.wait_for_textures and self.sim.has_rtx_sensors(): while SimulationManager.assets_loading(): self.sim.render()` `lw_benchhub/utils/monkey_patch.py:71`。**Arena 默认 `wait_for_textures = False`** —— 这意味着首帧可能拍到还没加载完的材质。

物理引擎方面：默认 **PhysX（GPU）**；Arena 另外带一个实验性的 **Newton / MuJoCo-Warp** 后端，用 `--presets physx|newton` 选 `[CODE]` `Arena:isaaclab_arena/cli/isaaclab_arena_cli.py:89-95`。PhysX 路径上 Arena 基类**把 `PhysxCfg()` 留在 Isaac Lab 默认值**，没有覆盖求解器类型和迭代次数 `[CODE]`。`contact_offset` / `rest_offset` 在两个仓库中**均未设置**，全部沿用 Isaac Lab / USD 资产默认值 `[CODE]`。

#### 2.6.11 真正被随机化的东西：Arena 的 variations 系统

既然没有传感器噪声，那域随机化靠什么？靠 Arena 的 "variations" —— 分 build-time（采样一次，在环境组装前改资产配置）和 run-time（一个 `EventTermCfg`，每次 reset 重采样）`[CODE]` `Arena:docs/pages/concepts/variations/variations.rst:160-200`。

| Variation | 类型 | 默认采样范围 | 位置 |
|---|---|---|---|
| `CameraExtrinsicsVariation` | run-time | `±0.005 m`（三轴，相机 ROS 光学系） | `Arena:isaaclab_arena/variations/camera_extrinsics_variation.py:38-100` |
| `CameraIntrinsics{BuildTime,RunTime}Variation` | 两者 | `±0.1` 的相对 (d_fx, d_fy) | `Arena:isaaclab_arena/variations/camera_intrinsics_variation.py` |
| `HDRImageVariation` | build-time | 在 HDR 库里选一张，挂到 dome light | `Arena:isaaclab_arena/variations/hdr_image_variation.py` |
| `LightIntensityVariation` | build-time | 100.0 – 2000.0 | `Arena:isaaclab_arena/variations/light_intensity_variation.py` |
| `LightColorTemperatureVariation` | build-time | 1000 – 10000 K | `Arena:isaaclab_arena/variations/light_color_temperature_variation.py` |
| `LightColorVariation` | build-time | RGB 各 0.0 – 1.0 | `Arena:isaaclab_arena/variations/light_color_variation.py:26-27` |
| `LightDirectionVariation` | build-time | 方位 ±π，仰角 0° – 80° | `Arena:isaaclab_arena/variations/light_direction_variation.py:54-57` |
| `ObjectMassVariation` | run-time | 0.05 – 2.0 kg | `Arena:isaaclab_arena/variations/object_mass_variation.py:38` |

内参随机化的实现细节值得注意：**焦距保持不变，缩放是通过改光圈实现的** —— 首次调用时快照标称光圈，然后 per env 执行 `GetHorizontalApertureAttr().Set(nominal_h / (1.0 + d_fx))`，再调 `_update_intrinsic_matrices()` `[CODE]` `Arena:isaaclab_arena/variations/camera_intrinsics_variation.py`。外参随机化同样先快照标称变换，避免每次 reset 的偏移**累积**。

自动注册：`add_camera_variations(camera_rig)` 会给 `camera_rig.camera_names()` 里的**每一个**相机同时注册外参和内参 variation `[CODE]` `Arena:isaaclab_arena/embodiments/embodiment_base.py:172-241`。

**未提及的随机化维度：纹理 / 材质外观随机化。** Arena 随机化光照和 HDR 环境贴图，但**不替换物体的 albedo/roughness 贴图** `[CODE]`。

LW-BenchHub 自己这一侧的随机化**几乎是空的**：`EventCfg` 只有 `reset_all = EventTerm(func=mdp.reset_scene_to_default, mode="reset")`，同文件里两段 `randomize_rigid_body_material`（静/动摩擦 0.8–1.25，`num_buckets=16`）是**注释掉的死代码** `[CODE]` `lw_benchhub/core/tasks/base.py:60-80`。

#### 2.6.12 视觉 sim2real 的真实策略：数字孪生 RGB 叠加

既然没有渲染噪声模型，LW-BenchHub 用另一条路提升视觉真实度：**把仿真前景合成到一张真实照片背景上** `[CODE]` `lw_benchhub_rl/lift_obj/lift_obj.py:296-372`。

- `rgb_overlay_mode: "none"|"debug"|"background"`（默认 `"background"`）
- `render_objects = [SceneEntityCfg("object"), SceneEntityCfg("robot")]` —— 只有物体和机器人算前景
- `setup_camera_and_foreground()` 给前景 spawn 打上 `semantic_tags=[("class","foreground")]`，然后追加 `semantic_segmentation` 标注器（见 §2.6.5）
- `overlay_image()` 在 `semantic_mask == semantic_id` 处保留仿真像素，其余替换为载入的真实图，含一次 BGR→RGB 交换 `back_image[..., [2,1,0]]` `[CODE]` `lw_benchhub_rl/lift_obj/mdp/observations.py`

**这就是这套栈实际的视觉 sim2real 手段：用真实背景代替渲染噪声模型。** 理解这一点，才能解释为什么它不需要相机噪声/畸变模型也能训出可迁移的策略 —— 它绕开了背景域差，只让网络看仿真的前景。

#### 2.6.13 传感器能力边界一览（可直接用于技术选型）

| 能力 | 状态 | 依据 |
|---|---|---|
| RGB 相机 | ✅ 有，USD 针孔，RTX 实时渲染 | §2.6.2 |
| 平铺渲染（高并行） | ✅ 有，Arena 侧默认开 | §2.6.3 |
| 语义分割 | ⚠️ 仅绿幕合成路径运行时追加 | §2.6.5 |
| 本体感知（位置/速度/末端位姿） | ✅ 有，且无误差无噪声 | §2.6.6 |
| 接触力（合力） | ✅ 有，PhysX 上报 | §2.6.7 |
| 接触力（分项 / 指尖入观测） | ⚠️ 仅 Arena Kuka-Allegro 一处 | §2.6.7 |
| 深度 | ❌ 未提及 | §2.6.8 |
| 激光雷达 / 射线投射 / 高度图 | ❌ 未提及 | §2.6.8 |
| IMU | ❌ 未提及 | §2.6.8 |
| 触觉阵列 | ❌ 未提及 | §2.6.8 |
| 六维力矩传感器 | ❌ 未提及 | §2.6.8 |
| 关节力矩观测项 | ❌ 未提及 | §2.6.6 |
| 传感器噪声模型 | ❌ 不存在（`enable_corruption` 为空转） | §2.6.9 |
| 相机畸变 / 卷帘 / 曝光模型 | ❌ 未提及 | §2.6.2 |
| 路径追踪 / 抗锯齿模式选择 | ❌ 未提及 | §2.6.2 |
| 光照 & HDR 随机化 | ✅ 有（Arena variations） | §2.6.11 |
| 纹理 / 材质随机化 | ❌ 未提及 | §2.6.11 |
| 物体质量随机化 | ✅ 有 | §2.6.11 |
| 摩擦随机化 | ❌ LW-BenchHub 侧被注释掉 | §2.6.11 |
| 真实背景叠加（数字孪生） | ✅ 有 | §2.6.12 |

---

## 3. 架构与模块

### 3.1 顶层目录：五个 Python 包 + 一批 shell 包装器

仓库根目录 `[CODE]`：

```
LW-BenchHub/
├── lw_benchhub/            核心包：core / utils / scripts / distributed / autosim / data / sim2real
├── lw_benchhub_tasks/      268 个任务的声明与注册（LIBERO 系 + RoboCasa 系）
├── lw_benchhub_rl/         RL 配置（6 个注册 id，全部围绕 LiftObj）
├── policy/                 IL/VLA 策略插件（GR00T / PI）
├── samples/                仅 1 个文件：解耦式 RL 客户端示例
├── configs/                YAML 配置树（带 _base_ 继承）
├── third_party/            仅一个 submodule：IsaacLab-Arena
├── ci_run/                 CI 脚本
├── docker/                 容器构建
└── *.sh                    8 个入口包装脚本 + install.sh + run_ci*.sh
```

`third_party/` 里**只有一个 submodule**（`IsaacLab-Arena`）`[CODE]` `.gitmodules`；IsaacLab 本体由 Arena 的子 submodule 再往下拉。

### 3.2 端到端接线链（一张图看完全流程）

```
*.sh  ──►  scripts/<x>.py  --task_config=<stem>
                │
                ├─ ConfigLoader.load(stem)                   utils/config_loader.py:51
                │     • 按文件名 stem 递归 rglob configs/**    :30
                │     • 递归 _base_ 深度合并                   :58, :92
                └─ 合并进 args_cli.__dict__                    例 rl/train.py:37-38
                        │
                        ▼
          lw_benchhub.utils.env.parse_env_cfg()               utils/env.py:169
                        │
                        ├─ 灌入全局 Context                    :224-258
                        ├─ discover_and_import_...()           :259  → 触发 339 次 gym.register
                        ├─ 4 × load_cfg_cls_from_registry      :266-278   id = {Backend}-{Type}-{Name}
                        ├─ IsaacLabArenaEnvironment(...)       :286-292
                        └─ LwEnvBuilder(...).build_registered() :298-299
                                   │
                                   ├─ orchestrate()       → LwBaseOrchestrator
                                   │     场景 → 任务 → 本体（顺序固定）  orchestrate.py:56-58
                                   │     然后 LwRL.setup_env_config()（rl_on 断言）rl/base.py:50-51
                                   ├─ modify_env_cfg()
                                   └─ compose_manager_cfg()  ← 重建 observations.policy
                        ▼
        gym.register("Robocasa-{task}-{robot}-v0", "isaaclab.envs:ManagerBasedRLEnv")
                        ▼
                     gym.make(...)  →  ManagerBasedRLEnv（已被 9 处 monkey patch）
                        │
       ┌────────────────┼─────────────────────┬──────────────────────────┐
       ▼                ▼                     ▼                          ▼
 SkrlVecEnvWrapper  ManiSkill PPO      IpcDistributedEnvWrapper    envhub 导出
 rl/train.py:196    agent.py:315       distributed/ipc.py:26       envhub_utils.py:116
                                       ↕ BaseManager / TCP          ↕ lerobot-eval
                                       RemoteEnv.make proxy.py:176
```

**这张图是排障的主索引**：报错发生在哪一层，决定了该查哪个文件。

### 3.3 `lw_benchhub/utils/` —— 接线层

**`utils/env.py`（319 行）是全仓库的中枢** `[CODE]`：

| 符号 | 行 | 职责 |
|---|---|---|
| `discover_lw_benchhub_modules()` | `:33` | 遍历 `entry_points(group="lw_benchhub_modules")` |
| `discover_and_import_lw_benchhub_modules()` | `:38` | 调 `isaaclab_tasks.utils.import_packages()` 强制 import 所有注册模块 |
| `ExecuteMode` | `:46` | 9 种运行模式，见 §2.4 |
| `load_cfg_cls_from_registry()` | `:73` | 注册表查询，支持 `.yaml` 入口或 `module:Attr` 字符串 |
| `get_scene_type()` | `:159` | `debug_assets` → `"Testasset"`；名字以 `.usd` 结尾 → `"Usd"`；否则取 `scene_name.split("-",1)[0].capitalize()` |
| `parse_env_cfg()` | `:169` | 整条流水线 |

两处硬编码值得记住 `[CODE]`：`teleop_device = None` 被写死并留了 TODO `lw_benchhub/utils/env.py:284`（即便 YAML 里写了 `teleop_device: vr-controller`）；`cfg.warmup_steps = 10` 在 `:318`。

**`utils/config_loader.py`（106 行）—— YAML 继承** `[CODE]`：`_collect_yml_files` `:30` 递归 rglob `CONFIGS_PATH` 下所有 `*.yml`/`*.yaml`，**按文件名 stem 做 key**，所以 `--task_config=g1-controller` 能定位到 `configs/data_collection/teleop/g1-controller.yml`；`load()` `:51` 递归展开 `_base_` 并检测循环引用 `:58-59`，返回 `argparse.Namespace` `:89`；`merge_dicts` `:92` 是递归深度合并；模块级单例 `config_loader = ConfigLoader()` `:106`。

**一个部署陷阱**：`CONFIGS_PATH = Path(__file__).parent.parent / 'configs'` `[CODE]` `lw_benchhub/__init__.py:2` 解析到**仓库根目录的 `configs/`**，而该目录不在安装后的包里 —— 所以**必须用源码检出 + editable 安装**（`pip install -e .`），普通 wheel 安装会找不到配置。

**`utils/monkey_patch.py`（690 行）—— 与 isaaclab 的边界**，9 个补丁已在 §2.5 列表。

其余 20+ 个辅助模块：`common_utils.py`、`csv_loader.py`、`errors.py`、`find_asset.py`、`fixture_utils.py`、`gripper_utils.py`、`hdf5_utils.py`、`lerobot_utils.py`、`log_utils.py`、`object_utils.py`、`opentelevision.py`、`profile_utils.py`、`render_utils.py`、`robocasa_utils.py`、`teleop_utils.py`、`ui_utils.py`、`usd_utils.py`、`video_recorder.py`、`envhub_utils.py`，以及子包 `isaaclab_utils/`、`lerobot_common/`、`math_utils/`、`pinocchio_ik/`、`piper/`、`place_utils/`、`X7S/` `[CODE]`。

### 3.4 `lw_benchhub/core/` —— 组合原语

| 子模块 | 关键类 | 位置 | 作用 |
|---|---|---|---|
| `context.py` | `Context` | `:25` | 全局单例，见 §2.3 |
| `env_builder/` | `LwEnvBuilder(ArenaEnvBuilder)` | `env_builder.py:29` | 覆盖 Arena 三个钩子；`DEFAULT_SCENE_CFG = InteractiveSceneCfg(num_envs=4096, env_spacing=30.0)` `:31` |
| `orchestrate/` | `LwBaseOrchestrator` | `orchestrate.py:39` | **强制 场景→任务→本体 的固定装配顺序** `:56-58` |
| `tasks/base.py` | `LwTaskBase(TaskBase)` | `:163` | 901 行、约 40 个方法，任务的全部生命周期 |
| `robots/robot_arena_base.py` | `LwEmbodimentBase(EmbodimentBase)` | `:168` | 相机装配、录制门控、动作滤波 |
| `cfg/__init__.py` | `LwBaseCfg(ManagerBasedRLEnvCfg)` | `:19` | 最终产出的环境配置类型 |
| `mdp/` | 14 个 observation 函数 + 7 个 reward 函数 + 8 类 action | — | 见下 |
| `checks/` | `BaseChecker` + 9 个具体检查器 | `base_checker.py:15` | 数据质量检查 |
| `devices/` | VR / OpenXR / 键盘 / Leader-Arm | — | 由 `patch_create_teleop_device` 注入 |
| `scenes/`、`models/` | `LocalScene`、`KitchenArena`、`LwScene`、`LiberoEnvCfg`；`fixtures/`（~30 文件） | — | 场景与家具/物体资产 |
| `simulators/` | `Runner_online_real` | `:21` | 真机在线运行器 |

**`LwEnvBuilder` 覆盖的三个 Arena 钩子** `[CODE]` `lw_benchhub/core/env_builder/env_builder.py`：`orchestrate()` `:37` 调 `rl_env.setup_env_config(...)`；`modify_env_cfg()` `:42`；`compose_manager_cfg()` `:48` 把 本体 + 任务 + RL 三方的 policy-observation 配置用 `combine_configclass_instances` 合并，然后**把 `env_cfg.observations.policy` 重建成一个动态生成的 `ObsGroup` 子类** `:57-61` —— 这解释了为什么 observation 的键名在运行时才能确定。

**`LwEmbodimentBase` 的几个关键行为** `[CODE]` `lw_benchhub/core/robots/robot_arena_base.py`：`EmbodimentGeneralObsCfg` 有 7 个 term（`actions`、`joint_pos`、`joint_vel`、`joint_pos_rel`、`joint_vel_rel`、`eef_pos`、`eef_quat`），`concatenate_terms = False` `:142`；`filter_action()` `:238` 对绝对式手臂动作做 **EMA + 速度钳位**（`max_vel 0.05` / `min_vel 0.002`）—— 这会让下发动作与实际执行动作不完全一致，是回放对不齐的一个来源。

**`core/mdp/observations.py` 的 14 个函数** `[CODE]`：`rel_ee_object_distance` `:30`、`fingertips_pos` `:38`、`ee_pos` `:46`、`ee_quat` `:54`、`ee_pose` `:65`、`get_target_qpos` `:77`、`ee_frame_pos` `:92`、`ee_frame_quat` `:99`、`gripper_pos` `:106`、`get_eef_base` `:114`、`get_eef_pos` `:138`、`get_eef_quat` `:156`、`_match_joint_indices` `:169`、`get_robot_joint_state` `:194`。

**`core/mdp/rewards.py` 的 7 个函数全部是"抓把手/开抽屉"类** `[CODE]`：`approach_ee_handle` `:19`、`align_ee_handle` `:44`、`align_grasp_around_handle` `:76`、`approach_gripper_handle` `:95`、`grasp_handle` `:118`、`open_drawer_bonus` `:139`、`multi_stage_open_drawer` `:151`。**换任务类型要自己写 reward**。

**动作空间实现** `[CODE]` `lw_benchhub/core/mdp/actions/`：`JointPositionMapAction`、`LegPositionAction`、`G1DecoupledWBCAction`、`G1Action`、`JointPositionLimitAction`、`RelJointPositionAction`、`DexRetargetingAction`，以及 `pink_action.py`（1100+ 行的 Pink IK：`PinkIKController` `:790`、`PinkAction` `:956`、`PinkActionCfg` `:1101`）。

### 3.5 `lw_benchhub_tasks/` —— 一个任务是怎么声明的

**注册量**：全仓库 339 次 `gym.register`，分布 `[CODE]`：

| 文件 | 数量 |
|---|---|
| `lw_benchhub_tasks/lightwheel_libero_tasks/libero_90/__init__.py` | 90 |
| `lw_benchhub_tasks/lightwheel_robocasa_tasks/multi_stage/__init__.py` | 88 |
| `lw_benchhub_tasks/lightwheel_robocasa_tasks/single_stage/__init__.py` | 53 |
| `libero_goal` / `libero_10` / `libero_object` / `libero_spatial` | 11 / 10 / 10 / 10 |
| `lw_benchhub_rl/__init__.py` | 6 |
| 其余（基础任务、资产检查） | 3 |

非任务 id 共 41 个：**场景 5 个**（`Local-Scene-Usd`、`Robocasa-Scene-Usd`、`Robocasa-Scene-Libero`、`Robocasa-Scene-Robocasakitchen`、`Robocasa-Scene-Testasset`）、**RL 6 个**（见 §3.6）、**机器人 28 个** `[CODE]`：

```
DoublePanda-{Abs,Rel}, DoublePiper-{Abs,Rel,RL},
G1-{Controller, Controller-DecoupledWBC, FullHand, Hand, Loco-Controller, Loco-Hand, RL, WBC-Joint, WBC-Pink},
LeRobot-{RL, AbsJointGripper-RL, BiARM-RL}, LeRobot100-RL,
Panda, Panda-RL, PandaOmron-{Abs,Rel,RL}, Piper-{Abs,RL}, X7S-{Abs,Joint,Rel}
```

注意 `lw_benchhub/core/robots/__init__.py` 是**空文件** —— 机器人注册散落在各厂商子包的 `__init__.py`（`unitree`、`agilex`、`arx`、`franka`、`lerobot`、`g1_arena`、`compositional`），靠 `import_packages` 拉进来 `[CODE]`。

**声明一个任务的标准形状** `[CODE]` `lw_benchhub_tasks/lightwheel_robocasa_tasks/single_stage/lift_obj.py`：

```python
counter_id: FixtureType = FixtureType.COUNTER   # :39  用哪一族家具
task_name: str = "LiftObj"                       # :40  注册表可见的名字

def _setup_kitchen_references(self, scene):      # :47  登记家具引用 + 机器人基座参考
    self.register_fixture_ref("counter", dict(id=self.counter_id, fix_id=2))   # :54
def _get_obj_cfgs(self):                         # :58  物体生成规格（name/obj_groups/graspable/placement）
def _check_success(self, env):                   # :78
    if ... TRAIN: return all-False               # :85  训练模式短路，走 reward shaping
    # 否则：env.scene['object'].data.root_pos_w[:, 2] >= 0.965
```

即：继承 `LwTaskBase` → 设 `task_name` 与家具类型类属性 → 实现 `_setup_kitchen_references` / `_get_obj_cfgs` / `_check_success`（可选 `get_ep_meta`）→ 在包的 `__init__.py` 里加一条 `gym.register(id=f"Robocasa-Task-{Name}", ...)`。

**LIBERO 系的两点差异** `[CODE]` `lw_benchhub_tasks/lightwheel_libero_tasks/libero_90/L90K3_put_the_moka_pot_on_the_stove.py`：继承的是**同族共享基类**（如 `PutOnStoveBase` `:22`）而不是 `LwTaskBase`；并通过 `get_ep_meta` `:33` 提供自然语言目标 `ep_meta["lang"] = "Put the moka pot on the stove."` `:35` —— **这个字符串就是解耦层对外提供的任务描述** `lw_benchhub/distributed/base.py:154`，也是 VLA 策略的 prompt 来源。LIBERO 任务还会钉死具体资产（`asset_name="Pot086.usd"` `:56`），而 RoboCasa 任务用 `obj_groups` 做类别级采样 —— **这是两个 benchmark 在"泛化性"上的根本区别**。

### 3.6 `lw_benchhub_rl/` —— RL 配置与"装饰器绑定机制"

`lw_benchhub_rl/__init__.py` 做 6 次 `gym.register`，每个 id 携带**三个**入口点 `[CODE]` `lw_benchhub_rl/__init__.py:22-24`：

```python
"env_cfg_entry_point":    f"{__name__}.lift_obj.lift_obj:G1LiftObjStateRL",
"skrl_cfg_entry_point":   f"{lift_obj_agents.__name__}:skrl_ppo_cfg.yaml",
"rsl_rl_cfg_entry_point": f"{lift_obj_agents.__name__}.rsl_rl_ppo_cfg:PPORunnerCfg",
```

6 个 id：`Robocasa-Rl-{G1LiftObjStateRL, G1LiftObjVisualRL, LeRobotLiftObjStateRL, LeRobotLiftObjVisualRL, LeRobotLiftObjDigitalTwin, LeRobot100LiftObjStateRL}` `[CODE]`。

> **值得注意的规模落差**：README 宣称 268 个任务，但**开箱可训的 RL 配置只有 6 个，且全部围绕同一个任务 `LiftObj`**。268 是"可遥操作/可回放/可评测"的任务数，不是"可强化学习训练"的任务数。要在其他任务上做 RL，必须自己写 reward 与 RL 配置类。

`lift_obj/agents/` 下备有 `skrl_ppo_cfg.yaml`、`rsl_rl_ppo_cfg.py`、`rl_games_ppo_cfg.yaml`、`sb3_ppo_cfg.yaml`、`robomimic/{bc,bcq}.json` —— **配置层面接了 4 个 RL 库 + robomimic，但只有 skrl 和自带的 ManiSkill PPO 有可运行的入口脚本** `[CODE]`。

**README 提到的"decorator-based binding mechanism"就是 `rl_on`** `[CODE]` `lw_benchhub/utils/decorators.py:15`：

```python
def rl_on(task=None, embodiment=None):
    # 类型校验：task 必须是 LwTaskBase 子类，embodiment 必须是 LwEmbodimentBase 子类
    def wrapper(cls):
        if task:       cls._rl_on_tasks.append(task)
        if embodiment: cls._rl_on_embodiments.append(embodiment)
        return cls
    return wrapper
```

用法是叠加装饰器 `[CODE]` `lw_benchhub_rl/lift_obj/lift_obj.py:214-215`：

```python
@rl_on(task=LiftObj)
@rl_on(embodiment=UnitreeG1HandEnvRLCfg)
class G1LiftObjStateRL(LwRL): ...
```

约束在环境配置时被断言 `[CODE]` `lw_benchhub/core/rl/base.py:50-51`：`assert type(orchestrator.task) in self._rl_on_tasks`。

> **⚠️ 已核实的缺陷**：`_rl_on_tasks` / `_rl_on_embodiments` 只在基类 `LwRL` 上声明了一次 `[CODE]` `lw_benchhub/core/rl/base.py:36-37`，**没有任何子类重新定义它们**。而装饰器执行的是 `cls._rl_on_tasks.append(...)`，所以每次注册都在改**共享的基类列表**。结果：`base.py:50-51` 的断言实际上是**全局兼容性检查，而不是 per-class 绑定** —— 任何已注册的 (任务, 本体) 组合都能通过任何 RL 配置的断言。**不要依赖这个断言来防止错配。**

`LwRL.modify_env_cfg()` `:71` 会强制 `decimation=5`、`episode_length_s=3.2`、`sim.dt=0.01` 并调大 PhysX 容量 `[CODE]`。`CurriculumCfg` `lw_benchhub_rl/lift_obj/lift_obj.py:203` **整段被注释掉**，但仍被赋值进任务 `lw_benchhub/core/rl/base.py:55` —— 即**课程学习目前是空壳** `[CODE]`。

### 3.7 `lw_benchhub/distributed/` —— 解耦式策略 API（Decoupled Policy API）

这是 README 的重点卖点之一，也是**宣称与实现落差最大的一处**，值得单独看。

**架构确实是 server–client**：服务端把整个 Isaac Sim 环境包起来常驻，客户端用一个懒代理按属性路径远程调用。

| 文件 | 关键类 | 作用 |
|---|---|---|
| `distributed/base.py`（185 行） | `BaseDistributedEnv` `:63` | 抽象基类；`attach()` `:124` / `detach()` `:135` |
| `distributed/ipc.py`（93 行） | `IpcDistributedEnvWrapper` `:26` | 默认传输：`multiprocessing.managers.BaseManager` |
| `distributed/proxy.py`（199 行） | `EnvManager` `:20`、`EnvService` `:37`、`_PathView` `:104`、`RemoteEnv` `:174` | 路径路由 RPC |
| `distributed/restful.py`（424 行） | `RestfulEnvWrapper` `:85` | 备选：Flask REST |

**`detach()` 的设计值得记住** `[CODE]` `lw_benchhub/distributed/base.py:135`：它关闭环境、调 `omni.usd.get_context().new_stage()` 并 `gc.collect()` —— 也就是**服务端可以连续换任务/换配置而不重启 Isaac Sim**。这是这套架构真正的价值所在（Isaac Sim 冷启动是分钟级的）。配套地，`env_server.py` 把 `AppLauncher` 做成**懒构造**，Isaac 应用只在第一个客户端 attach 时才启动 `[CODE]` `lw_benchhub/scripts/env_server.py:112`。

**关于 "zero-copy data exchange"** —— README `:36` 宣称 "Built with zero-copy data exchange, the API minimizes memory overhead"。逐行核查的结论是：

> **未提及 / 未证实。** 传输是 `BaseManager` RPC 走**普通 AF_INET TCP** 套接字加 authkey `[CODE]` `lw_benchhub/distributed/ipc.py:37`、`:47`（`socket.fromfd(c._handle, socket.AF_INET, socket.SOCK_STREAM)` —— 是真 TCP，不是 AF_UNIX，也不是共享内存）。全仓库对 `ForkingPickler|share_memory|cuda_ipc|zero_copy|torch.multiprocessing|reduce_tensor` 的 grep **只命中一处**：`lw_benchhub/distributed/ipc.py:81` 的一句裸 import `from torch.multiprocessing import Queue  # noqa: F401`。该 import 的副作用会注册 torch 的 `ForkingPickler` reducer，*理论上*能让跨 pickler 的张量走 CUDA-IPC 句柄，但**没有任何代码显式构造共享存储，意图也无文档**。
>
> 而备选的 RESTful 传输**明确是反 zero-copy 的**：观测以 **base64 编码的 PNG 塞进 JSON** 返回，动作以**空格分隔的字符串**传入 `[CODE]` `lw_benchhub/distributed/restful.py:332`、`:383`。

`multiprocessing.shared_memory` 确实被用了，但**只在遥操作信号和 VR 图像传输里，不在策略 API 里** `[CODE]` `lw_benchhub/scripts/teleop/teleop_main.py:86`、`:1069-1072`、`lw_benchhub/utils/opentelevision.py:72`。

另外 `pyproject.toml` 声明了 `grpcio>1.73`、`protobuf>6`、`zmq`，但 `lw_benchhub/distributed/` 里**没有任何 gRPC 或 ZMQ 用法** `[CODE]` —— 属于声明未用的依赖。

**结论**：把它当作"能常驻复用 Isaac Sim 实例的 RPC 环境服务"来用是准确的；不要指望它的张量传输有零拷贝性能。

### 3.8 `policy/` —— IL / VLA 策略插件

`policy/__init__.py:1-2` 只导出两个：`PIPolicy`、`GR00TPolicy` `[CODE]`。

**`policy/base.py`（173 行）的 `BasePolicy(ABC)` `:26`** 定义了插件契约 `[CODE]`：已实现的 `initialize` `:45`、`get_instruction` `:54`、`add_video_frame` `:58`、`step_environment` `:69`（会应用 `usr_args['joint_mapping']` 做动作重排 `:76-78`）、`encode_obs` `:84`（**把 `observation['policy']` 与 `observation['embodiment_general_obs']` 合并** `:95-96`，并做 HWC→CHW 转置）；待实现的抽象方法 `get_model` `:124`、`get_action` `:137`、`eval` `:144`、`reset_model` `:161`。

**要接入自己的 VLA，只需实现这 4 个抽象方法**，然后 `eval_policy.py` 会按名字从 `policy` 包动态 import 该类 `[CODE]` `lw_benchhub/scripts/policy/eval_policy.py:129-131`。

注意 **`gr00t` 与 PI 运行时都没有写进 `pyproject.toml`** `[CODE]` —— 它们活在各自独立的环境里，这正是 `ci_run/eval_policy.sh:41-58` 要按模型族切换 conda env / venv（`gr00t*` 用 `gr00t_man` 环境、`pi*` 用 `/.venv/bin/python`、`go*` 用 `torch.distributed.run`）的原因。**跨策略族评测天然是多环境的，不要试图装进一个环境。**

### 3.9 `lw_benchhub/autosim/` —— 自动示教生成（插件侧）

**这个模块是一个插件，插进一个不在本仓库、也未在 `pyproject.toml` 声明的外部 `autosim` 包** `[CODE]` `lw_benchhub/autosim/__init__.py:1`（`from autosim import register_pipeline`）。它对应的就是 AutoDataGen 项目（见 §1.5）。

它有自己的注册表，id 形如 `LWBenchhub-Autosim-<Name>Pipeline-v0`，共 9 条 `[CODE]` `lw_benchhub/autosim/__init__.py:4-56`：`CoffeeSetupMug`、`OpenFridge`、`CheesyBread`、`CloseOven`、`KettleBoiling`、`DessertUpgrade`、`OpenToasterOvenDoor`、`CloseDrawer`、`PnPCounterToStove`。

**机器人抽象层** `lw_benchhub/autosim/robot_profiles.py` `[CODE]`：`RobotProfile` `:17` 有 `profile_id`、`robot_name`（转发给 `parse_env_cfg` 的注册名）、`action_adapter_factory`、`motion_planner_robot_config_file`（**cuRobo 规划器配置文件名**）、`robot_base_link_name`、`ee_link_name`；`TaskRobotOverride` `:35` 提供 per-task 覆盖（`object_reach_target_poses`、`extra_target_link_names`、`reach_extra_target_mode`）。`content/` 下放 X7S 的 URDF/mesh 以及 cuRobo 风格的 `configs/robot/x7s*.yml` 与 `spheres/collision_x7s.yml`。

**这条链路是"LLM 分解任务 → cuRobo 规划 → 仿真执行 → 产出轨迹"的落地点**，也是本机复现工作 Stage 2/4 的主战场（见经验层）。

### 3.10 `lw_benchhub/data/` 与 `sim2real/`

**`data/` 是纯数据** `[CODE]`：13 个机器人 `.usd`（含 `g1_29dof_with_hand`、`x7s`、`piper`、`double_piper`、`so100_follower`、`so101_follower`、`omron_franka`、`panda_2`）；4 个全身控制 ONNX 检查点在 `ckpts/nv_wbc_v0828/` 与 `ckpts/nv_wbc_v0904/homie_v2/{stand,walk,slip_walk}.onnx`；以及 dex-retargeting 的 YAML 与 Unitree Dex3 的 URDF/STL。

**`sim2real/` 只有真机驱动** `[CODE]`：`lerobot_follower/{so100_follower.py, so101_follower.py}`，`SO100Follower` / `SO101Follower` 是**普通 Python 类而非 isaaclab 子类**（`:31`），默认 `port='/dev/ttyACM0'`（`:35`）。公开接口包括 `connect`/`disconnect`/`calibrate`/`set_target_qpos`/`send_action`/`get_qpos`/`get_sensor_images` 等。消费者是 `lw_benchhub/scripts/maniskill_ppo/eval_real.py` 与 `eval_real_no_sim.py`。

### 3.11 Arena 侧的三个原语

理解 LW-BenchHub 必须知道 Arena 给了什么。Arena 的核心抽象只有三个可组合原语 `[README]` `Arena:README.md:35-39`：

| 原语 | 含义 |
|---|---|
| **Scene** | 场景/布局，含家具与静态资产 |
| **Embodiment** | 机器人本体，含关节、控制器、传感器挂载 |
| **Task** | 任务，含物体生成规格、成功判定、语言目标 |

三者由 `ArenaEnvBuilder` 组装成标准的 `ManagerBasedRLEnvCfg` `[README]` `Arena:README.md:41`。**LW-BenchHub 做的就是各自派生一层（`LwScene` / `LwEmbodimentBase` / `LwTaskBase`）并换成自己的 `LwEnvBuilder`**。

Arena 还提供任务判定谓词库 `isaaclab_arena/tasks/predicates/`（`object_on_destination`、`contact_force_is_upward_support` 等，见 §2.6.7）和视频录制器（§2.6.5）`[CODE]`。

**Arena 自我定位是 alpha** —— README 两处明确写 "APIs will break without deprecation warnings … Do not use this in production" `[README]` `Arena:README.md:21-23`、`Arena:README.md:212-221`。这一条对任何长期工程都是硬约束。

---

## 4. 关键特性

### 4.1 六大组件（README 自述）

README 把自己拆成 6 块 `[README]` `README.md:143-148`：机器人本体、场景、任务、遥操作、RL 训练、解耦式策略 API。下面按"宣称 → 实测"逐条核对。

### 4.2 ⚠️ 规模数字的实测校准（选型时先看这一节）

**README 的四个核心数字都与代码有出入。** 以下均为对仓库的直接计数 `[CODE]`：

| README 宣称 | 实测 | 差异说明 |
|---|---|---|
| "27 specific robot variants" `README.md:29` | **28 个** `Robocasa-Robot-*` id | 7 个厂商目录确实对得上"7 robot types"，但变体是 28 个 |
| "268 tasks（130 LIBERO + 138 Robocasa）" `README.md:32` | **272 个** `Robocasa-Task-*` id（LIBERO 131 + RoboCasa 141） | 另有 `task_name` 字面量去重后 LIBERO 103 —— LIBERO 有同类复用多 id |
| "10 layouts × 10 styles = 100 configs" `README.md:30` | 映射 CSV 里 layout id **最大到 62**；排除清单枚举到 60 | 100 大概是**精选子集**，代码允许的范围宽得多 |
| "integrates with rsl-rl and skrl" `README.md:34` | **只有 skrl 会被真的实例化** | 见 §4.7 |

**这不是文档笔误层面的问题**，而是"宣称规模 ≠ 可用规模"的典型：272 个任务里能开箱 RL 训练的只有 6 个配置（§3.6），能被 layout CSV 钉好机器人位姿的组合也只是其中一部分（§4.5）。**做工作量估算时以实测为准。**

### 4.3 任务库的两种设计风格（决定泛化性实验怎么做）

272 个任务分两大族，**设计哲学相反**，这是使用这套 benchmark 最需要先想清楚的事 `[CODE]`：

| | **LIBERO 系**（131 个） | **RoboCasa 系**（141 个） |
|---|---|---|
| 目录 | `lw_benchhub_tasks/lightwheel_libero_tasks/{libero_10, libero_90, libero_goal, libero_object, libero_spatial}` | `lw_benchhub_tasks/lightwheel_robocasa_tasks/{single_stage, multi_stage}` |
| 物体指定 | **钉死 USD 资产名**，如 `asset_name="Plate012.usd"`、`"Bowl008.usd"` | 用 **`obj_groups` 类别级采样**（如 `obj_groups="all"`） |
| 位置 | **显式坐标** + `margin=0.02` | **拒绝采样** + 家具类型引用（`FixtureType.OVEN`） |
| 干扰物 | 无 | 有，数量随机 `num_distr = self.rng.integers(1, 4)` |
| 语言目标 | 固定句子，如 `"Pick up the akita black bowl and put it on the plate."` | 从家具自然语言名合成，如 `f"{behavior.capitalize()} the {fxtr.nat_lang} {door_name}"` |
| 方差 | **低**（可复现，适合做闭环基线） | **高**（适合做泛化/鲁棒性评测） |
| 继承 | 同族共享基类（如 `LiberoGoalTasksBase`） | 行为基类链（`ManipulateDoor` → `ManipulateLowerDoor` → `OpenDropDownDoor` → `OpenOven`） |

**两个完整实例，可作为写新任务的模板** `[CODE]`：

- **RoboCasa 风格：`OpenOven`** `lw_benchhub_tasks/lightwheel_robocasa_tasks/single_stage/kitchen_doors.py:341`。继承链见上；`fixture_id = FixtureType.OVEN` `:344`；`EXCLUDE_LAYOUTS = LwTaskBase.OVEN_EXCLUDED_LAYOUTS` `:343`；`_setup_scene` 会**按行为预置状态**（要"开"就先关上、要"关"就先开着）`:71-74`；成功判定直接委托家具 `return self.fxtr.is_open(env=env)` `:89-92`。同目录的 `kitchen_oven.py` 里 `PreheatOven` 的成功判定是 `self.oven.get_state()["temperature"] >= 0.1` `:45` —— **家具是有状态机的**，不只是几何体。
- **LIBERO 风格：`LGPutTheBowlOnThePlate`** `lw_benchhub_tasks/lightwheel_libero_tasks/libero_goal/LG_put_the_bowl_on_the_plate.py:23`。成功判定用通用谓词 `OU.check_place_obj1_on_obj2(env, bowl, plate, th_z_axis_cos=0.95, th_xy_dist=0.25, th_xyz_vel=0.5)` `:114` —— 即**同时约束姿态垂直度、水平距离和速度**（速度约束是为了排除"正在掉下去"的瞬间）。

**成功判定的通用管线** `[CODE]` `lw_benchhub/core/tasks/base.py`：`TerminationsCfg.success` 声明为 `MISSING` `:160`，由 `LwTaskBase` 在 `:204-206` 绑成 `DoneTerm(func=self.check_success_caller)`。`check_success_caller` `:280-300` 有两道防抖：**必须 `episode_length_buf >= 10` 才允许 latch**（`_start_success_check_count = 10` `:179`），且需连续满足 `_success_count` 步（TELEOP 下是 `int(1/sim.dt/2)`，即半秒；其他模式为 1）`:236-238`。**这解释了为什么手动遥操作时"看起来成功了"要等半秒才判定成功。**

### 4.4 场景系统：`layout` 字符串的语法

`layout` 是一个字符串，由 `LwScene._setup_config` 按短横线切分 `[CODE]` `lw_benchhub/core/scenes/kitchen/kitchen.py:77-87`：

| 写法 | 含义 |
|---|---|
| `robocasakitchen-9-8` | scene_type=`robocasakitchen`，layout=9，style=8 —— **完全确定** |
| `robocasakitchen-4` | 只定 layout，style **随机采样** |
| `robocasakitchen` | layout 与 style **都随机采样** |
| `libero-1-1` | 选 LIBERO 场景族 |
| `/path/to/scene.usd` | 走本地 USD 模式（配合 `scene_backend: local`） |

任务级排除在 `kitchen.py:105-106` 强制执行（`raise ValueError(f"Layout {…} is excluded in task {…}")`）—— 排除清单是 `LwTaskBase` 的类属性 `[CODE]` `lw_benchhub/core/tasks/base.py:169-182`：`OVEN_EXCLUDED_LAYOUTS`（45 个 id）、`DOUBLE_CAB_EXCLUDED_LAYOUTS = [32, 41, 59]`、`DINING_COUNTER_EXCLUDED_LAYOUTS`、`ISLAND_EXCLUDED_LAYOUTS`、`STOOL_EXCLUDED_LAYOUT`、`SHELVES_INCLUDED_LAYOUT = [1..10]`、`FREEZER_EXCLUDED_LAYOUTS`、`FOUR_TOASTER_SLOT_EXCLUDE_STYLES`。**换 layout 报 "excluded" 不是 bug，是任务对家具的硬性要求。**

**光照随模式变化** `[CODE]` `lw_benchhub/core/scenes/kitchen/kitchen.py:164-191`：`ExecuteMode.TRAIN` 下场景装一个名为 `room_light` 的 `SphereLightCfg`（强度 50000）加一个 DomeLight（500）；其他模式只有一个 DomeLight（950）。**训练和评测的光照条件不同** —— 这是 sim2sim 差异的一个隐藏来源，也是 RL 的 `randomize_scene_lighting` 事件（强度 50000–60000）能生效的前提。

### 4.5 硬编码位姿表：随机采样失败时的兜底

这是本工具链一个**不在 README 里但非常重要**的机制。

**（1）`configs/layout_task_mapping/layout_task_mapping.csv`（581 行）** `[CODE]`，表头：

```
robot,layout,task,init_robot_base_pos,init_robot_base_ori,object_init_offset
DoublePiper-Abs,robocasakitchen-61-5,PlaceTableware,"[2.37, -2, 0.72]","[0.00, 0.00, -1.57]","[0.0, 0.2]"
```

即**逐 (机器人, layout, 任务) 手调的出生点表**。命中时 `robot_arena_base.py:310-320` 会设 `orchestrator.task.resample_robot_placement_on_reset = False` —— **CSV 的位姿覆盖拒绝采样** `[CODE]`。物体偏移在 `_create_objects()` 之前被读入 `lw_benchhub/core/tasks/base.py:858-860`。

⚠️ **这个文件名在全仓库没有任何引用** `[CODE]`（`grep -rn "layout_task_mapping"` 只命中文件自身）—— 它是被 `CONFIGS_PATH.rglob("*.csv")` 泛化发现的 `lw_benchhub/utils/csv_loader.py:35`。**换句话说：往 `configs/` 下丢任何 `.csv` 都会被扫进来，按 stem 索引。** 要给新的 (机器人, layout, 任务) 组合定位姿，就是往这张表加一行。

**（2）LIBERO 另有一张硬编码字典** `LIBRO_SCENE_ROBOT_STATE` `[CODE]` `lw_benchhub/core/scenes/kitchen/libero.py:18-50`，覆盖 `libero-{1-1, 2-2, 4-4, 5-5, 8-8}`，且**只对 `"LeRobot-AbsJointGripper-RL"` 一个机器人有效**。`LiberoEnvCfg.sample_robot_base` 优先查这个字典，查不到才回落到父类 `:56-61`。**用别的机器人跑 LIBERO 场景，位姿就得自己调。**

### 4.6 遥操作与数据采集

支持的输入设备 `[README]` `README.md:31`：键盘、VR（Vision Pro / PICO / Meta Quest）、Leader-Follower 机械臂。实现在 `lw_benchhub/core/devices/`，通过 `patch_create_teleop_device` 注入 isaaclab 的设备工厂 `[CODE]`（§2.5）。

`configs/data_collection/teleop/teleop_base.yml`（71 行）是**理解全部可调项的最佳单一入口**，六段分组 `[CODE]`：

| 段 | 关键项（默认值） |
|---|---|
| 基础 | `disable_fabric: false`、`num_envs: 1`、`device: cpu`、`sensitivity: 1.0`、`step_hz: 50` |
| 机器人 | `robot: PandaOmron-Rel`、`robot_scale: 1.0` |
| 任务与场景 | `task: RobocasaBaseTask`、`scene_backend/task_backend: robocasa`、`layout: robocasakitchen`、`sources: [objaverse, lightwheel, aigen_objs]`、`usd_simplify: false`、`seed: 0` |
| 数据采集 | `record: false`、`dataset_file: ./datasets/dataset.hdf5`、`num_demos: 1`、`continue_teleop_after_success: false` |
| 遥操作设备 | `teleop_device: keyboard`、`enable_pinocchio: false`、`relative_control: false`、**`action_delay_async`/`action_delay_time_s`/`action_delay_type`/`action_buffer_size`（人为注入延迟）** |
| 视频 | `enable_cameras: false`、`save_video: false`、`video_save_dir: ./videos`、`video_fps: 30` |
| 重试 | `max_scene_retry: 4`、`max_object_placement_retry: 3`、`resample_objects_placement_on_reset: true`、`resample_robot_placement_on_reset: true` |

两点值得单独记住 `[CODE]`：

- **`action_delay_*` 四个键是真的动作延迟注入器**，用于研究控制延迟对策略的影响 —— 这是本工具链一个少见的、明确面向 sim2real 的特性。
- **遥操作模式下超时被完全禁用**：`env_cfg.terminations.time_out = None` `lw_benchhub/scripts/teleop/teleop_main.py:667`。所以遥操作不会自己结束，靠 `num_demos` 计数停止 `:1005-1009`。

遥操作时的键盘检查点控制（写在 `teleop_main.py` 的模块 docstring `:15-46`）：**M = 存档，N = 读档，B = 回退 10 帧，R = 重置** `[CODE]` —— 采数据时非常实用，README 里没提。

### 4.7 RL 训练：**三套彼此独立的 PPO**

这是一个容易踩的点：仓库里有三条 RL 路径，**配置方式和默认超参完全不同** `[CODE]`。

| 路径 | 入口 | 超参来源 | 状态 |
|---|---|---|---|
| **skrl** | `train.sh` → `lw_benchhub/scripts/rl/train.py` | gym 注册表拿 `skrl_ppo_cfg.yaml` | ✅ **唯一被真正实例化的库路径** |
| **rsl-rl** | 无入口脚本 | `lw_benchhub_rl/lift_obj/agents/rsl_rl_ppo_cfg.py` | ⚠️ **只注册不执行**（见下） |
| **ManiSkill PPO（自带实现）** | `train_ppo.sh` → `lw_benchhub/scripts/maniskill_ppo/train.py` | 硬编码的 `PPOArgs` dataclass | ✅ 可用，但**不读 YAML 超参** |

**关于 rsl-rl**：6 个 RL env 每个都注册了 `rsl_rl_cfg_entry_point`，`rsl_rl_ppo_cfg.py` 也确实存在，但 `lw_benchhub/scripts/rl/train.py`（221 行）**从未 import `rsl_rl`**，全仓库也没有任何脚本消费 `rsl_rl_cfg_entry_point` `[CODE]` `lw_benchhub/scripts/rl/train.py:51`、`:56`、`:61`。**README 宣称的 rsl-rl 集成目前是声明式的，不可运行。**

**skrl PPO 的实际超参** `[CODE]` `lw_benchhub_rl/lift_obj/agents/skrl_ppo_cfg.yaml`（80 行）：`seed: 42`；策略 `GaussianMixin` + 价值 `DeterministicMixin`，网络均 `[512, 512]` + `elu`；`rollouts: 16`、`learning_epochs: 8`、`mini_batches: 4`、`discount_factor: 0.8`、`lambda: 0.9`、`learning_rate: 3e-4` + `KLAdaptiveLR(kl_threshold=0.01)`、`grad_norm_clip: 0.5`、`ratio_clip: 0.2`、`entropy_loss_scale: 0.0`、`value_loss_scale: 0.5`；`SequentialTrainer`、`timesteps: 72000`；`checkpoint_interval: 5000`。

注意 **`discount_factor: 0.8` 相当低** —— 配合 `episode_length_s = 3.2`（§2.6.10）说明这是**短时程抓取任务**的调参，换长时程任务必须重调。

`--max_iterations` 的语义是重写 trainer 预算：`agent_cfg["trainer"]["timesteps"] = args_cli.max_iterations * agent_cfg["agent"]["rollouts"]` `[CODE]` `lw_benchhub/scripts/rl/train.py:146`。另外 skrl 路径会**强制** `env_cfg.observations.policy.concatenate_terms = True` `:125` —— 这也是 `configs/common/env_server/env_server_base.yml` 里那句注释 "only skrl need to be true" 的由来。

**ManiSkill PPO 的默认值和 skrl 差得很远** `[CODE]` `lw_benchhub/scripts/maniskill_ppo/agent.py:33-103`：`num_envs=512`（skrl 配置默认 10）、`total_timesteps=10_000_000`、`gamma=0.9`、`num_minibatches=32`、`target_kl=0.2`、`action_dim=6`。**CI 用的是这一条路径**（`ci_run/train_ci.sh` 调 `maniskill_ppo/train.py`），并把 `success_rate` 与 `ci_success = success_rate >= 0.7` 写进 `result.json` `[CODE]` `lw_benchhub/scripts/maniskill_ppo/train.py:156-161`。

**奖励项** `[CODE]` `lw_benchhub_rl/lift_obj/lift_obj.py:194`（LeRobot 路径）：`reaching_reward`(1.0)、`grasp_reward`(1.0)、`place_reward`(1.0)、`touching_table`(**-2.0**)；G1 路径 `:161` 另有 `lifting_object`(minimal_height 0.98, w 15.0)、`object_goal_tracking`(w 16.0)、`action_rate`(-1e-4)、`joint_vel`(-1e-4)。

### 4.8 解耦式策略 API 的实际价值

见 §3.7 的完整分析。一句话总结：**"server–client" 准确，"zero-copy" 未证实**。真正的价值是 `detach()` 能换任务而不重启 Isaac Sim，把分钟级冷启动摊薄到一次。

接入自己的 VLA 只需实现 `BasePolicy` 的 4 个抽象方法（`get_model`/`get_action`/`eval`/`reset_model`）`[CODE]` `policy/base.py:124-161`。

### 4.9 LeRobot 桥与数据集

`lerobot_eval.sh` 是把 LeRobot 生态接进来的入口 `[CODE]`：

```bash
lerobot-eval --policy.path=LightwheelAI/smolvla-double-piper-pnp \
  --env.type=isaaclab_arena --env.hub_path=LightwheelAI/lw_benchhub_env \
  --env.kwargs='{"config_path": "configs/envhub/example.yml"}' \
  --env.state_keys=joint_pos --env.action_dim=12 \
  --env.camera_keys=left_hand_camera_rgb,right_hand_camera_rgb,first_person_camera_rgb \
  --eval.batch_size=10 --eval.n_episodes=100
```

接收端 `lw_benchhub/utils/envhub_utils.py`（135 行）做一件关键的事：**`_reorg_observation_for_envhub` 把 `embodiment_general_obs` 改名成 `policy`，把原来的 `policy` 改名成 `camera_obs`** `[CODE]` `:99-113`，以满足 Arena 的 envhub 观测契约。**这个改名是理解"为什么观测键名和你在配置里写的不一样"的答案。**

`configs/envhub/example.yml` 是**唯一一个 `episode_length_s` 作为 YAML 键生效的地方**（20.0）`[CODE]` `:11` + `envhub_utils.py:91`。其他地方全是硬编码：任务基类 8.0（`core/tasks/base.py:241`），RL 先设 4.0 再覆盖成 3.2（`core/rl/base.py:72`、`:81`），遥操作直接禁用。

**数据集** `[README]` `README.md:35`：219 个任务 / 4 种机器人 / **21,500 条 episode / 20,537,015 帧**，每个 (机器人, 任务) 组合 50 条。HDF5 → LeRobotDataset 的转换脚本有两个版本 `[CODE]`：`convert_hdf5_to_lerobot_dataset.py`（默认相机路径 `["obs/first_person_camera_rgb","obs/left_hand_camera_rgb","obs/right_hand_camera_rgb"]`，默认 `--robot_type X7S-Abs`）和 `convert_hdf5_to_lerobot_datasetv3.py`（`--hdf5_name dataset_success.hdf5`、`--skip_frames 5`）。

### 4.10 资产获取：运行时从 Lightwheel 云端拉取

**这是部署时最容易卡住的一环**：厨房场景和物体**不在仓库里，也不在 git-lfs 里，而是运行时通过 `lightwheel_sdk` 从网络注册表拉取** `[CODE]`。

7 个 `lightwheel_sdk` 调用点 `[CODE]`：

| 位置 | API |
|---|---|
| `lw_benchhub/core/scenes/kitchen/kitchen_arena.py:19` | `from lightwheel_sdk.loader import floorplan_loader` |
| `lw_benchhub/core/scenes/kitchen/kitchen.py:213` | `object_loader.acquire_by_registry("fixtures", ...)` |
| `lw_benchhub/core/tasks/base.py:25` | `ENDPOINT`（写进 episode 元数据 `ep_meta["LW_API_ENDPOINT"]` `:886`） |
| `lw_benchhub/utils/place_utils/kitchen_object_utils.py:20` | `acquire_by_file_version` `:133`、`acquire_by_registry` `:145`、`:159` |
| `lw_benchhub/utils/place_utils/kitchen_objects.py:15` | `object_loader.list_registry()` `:31-32` 构建 `OBJ_CATEGORIES` / `FIXTURE_CATEGORIES` |
| `lw_benchhub/scripts/teleop/replay_demos.py:126`、`replay_action_demo.py:203` | `lw_client` |

楼层平面图的获取 `[CODE]` `lw_benchhub/core/scenes/kitchen/kitchen_arena.py:102-126`：

```python
res = floorplan_loader.acquire_usd(backend="robocasa", scene=scene_type,
        layout_id=…, style_id=…, version=…,
        exclude_layout_ids=…, exclude_style_ids=…)
usd_path, self.floorplan_meta = res.result()
```

三个分支分别对应"都不指定 / 只指定 layout / layout+style" `:114`、`:116`、`:118`。

git-lfs 只管仓库内提交的文件（`.gitattributes` 仅 4 行：`*.onnx`、`*.usd`、`*.usda`、`*.usdc`）`[CODE]`。**没有独立的资产下载脚本 —— 未提及。** 这意味着：**离线环境跑不起来**，且网络问题会直接表现为场景加载失败（对应上游 issue #32 的 SSL 错误，见 §8）。

`kitchen_objects.py:31-32` 在 import 时就调 `object_loader.list_registry()` 构建类别表 —— **也就是说注册表不可达时，失败发生在 import 阶段，而不是场景加载阶段**，报错位置会很有迷惑性。

---

## 5. 安装与依赖

> 排障入口：装不上或跑不起来时，先看 [`troubleshooting.md`](troubleshooting.md)，再回来看本章的机制解释。
>
> 📌 **本机实测的安装踩坑集中在 [`troubleshooting.md`](troubleshooting.md) 的 A 组 `Q01`–`Q16`**（L94–354）。本章只给官方声明的依赖，**以下四条实测硬约束本章未涉及、但不满足就装不通**（`[实践]` 级，出处 `ai_knowledge.md` §1.2、§4.A）：
> - **`numpy==1.26.0` 必须最后装，且每次 pip 操作后重新锁回**（Isaac Sim 的 C 扩展硬绑该版本）→ [`Q03`](troubleshooting.md#q03)
> - **`warp-lang==1.8.1`** 是唯一可获得的同 minor 版本 → [`Q11`](troubleshooting.md#q11)
> - 运行脚本必须 `set +u`（不是 `set -u`）→ [`Q14`](troubleshooting.md#q14)
> - 必须 `unset CUDA_VISIBLE_DEVICES`，否则相机初始化 segfault 且无 traceback → [`Q15`](troubleshooting.md#q15)
>
> 📌 **本机实际装成什么样，看代码层** → [`code_knowledge.md`](code_knowledge.md) §5「依赖与环境」：§5.1 全部锁定版本号（Isaac Sim 5.1.0 / Isaac Lab v2.3.2 / Arena `release/0.1.1` / lerobot 0.5.1 / cuRobo 0.7.7 editable）、§5.2 打包文件分布（⚠️ **仓库根目录没有 `requirements.txt` 或 `pyproject.toml`**，本章的"声明依赖"要到各子包里找）、§5.3 cuRobo 的编译期环境变量、§5.4 五个版本耦合点。
> 📌 **要照抄一份可执行的准备步骤** → [`quickstart.md`](quickstart.md) §1（含四个硬锁版本与六行运行前奏）。

### 5.1 硬件与驱动底线

| 项 | 要求 | 来源 |
|---|---|---|
| GPU | NVIDIA RTX（需 RTX 系列，Isaac Sim 要求光追核心） | `[README]` |
| 驱动 | **≥ 570.169** | `[CODE]` `docker/base.dockerfile` `MIN_DRIVER_VERSION=570.169` |
| 显存 | 未提及（RL `num_envs=512` 的显存需求无记录） | — |
| 磁盘 | 未提及 | — |
| 系统 | Ubuntu（容器基镜像 `nvcr.io/nvidia/base/ubuntu:noble-20250619`，即 24.04） | `[CODE]` |
| Python | **未声明** —— `pyproject.toml` 没有 `requires-python` | `[CODE]` |

⚠️ Python 版本没有约束是个真实隐患：实际由 Isaac Sim 5.0/5.1 的内置 Python 决定（3.11），但仓库不会替你把关。

### 5.2 两条互相独立的安装路径（**不是分层关系**）

这是本工具链安装环节最需要先看清的事 `[CODE]`：

```
路径 A：install.sh（宿主机 / 已有 conda 环境）
路径 B：docker/（容器）
        ↑ 二者 torch 版本冲突，且 B 从不调用 A
```

**没有任何 dockerfile 调用 `install.sh`** `[CODE]`（grep 确认）。两条路各自装一遍依赖，且：

| | `install.sh` | `docker/environment.yml` |
|---|---|---|
| torch | **2.7.0** + cu128 | **2.5.1** |

**冲突是真实的。** 选定一条路径后不要混用，尤其不要在容器里再跑一次 `install.sh`。

### 5.3 路径 A：`install.sh` 逐行解读

`install.sh` 只有 23 行，但每一步都有讲究 `[CODE]`：

```bash
# 1. 装 PyTorch（先装，避免被后续依赖降级）
pip install torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128

# 2. 拉子模块
git submodule update --init --recursive

# 3. ⚠️ 打补丁后再装 isaaclab，装完立刻还原
sed -i 's/flatdict==4.0.1/flatdict==4.0.0/' source/isaaclab/setup.py
bash isaaclab.sh --install
git checkout -- source/isaaclab/setup.py

# 4. 以 editable 方式装 Arena 与本仓库
pip install -e third_party/IsaacLab-Arena
pip install -e .
```

**三个必须知道的点：**

1. **`flatdict==4.0.1` 在 PyPI 上不可安装**（4.0.0 是最后一个可用版本），所以脚本用 `sed` 临时改 isaaclab 的 `setup.py`，装完 `git checkout --` 还原，保持子模块工作区干净。**手动安装时如果跳过这一步，`isaaclab.sh --install` 会在依赖解析阶段失败。**

2. ⚠️ **第 2 步在没有 SSH key 的机器上会失败。** `IsaacLab-Arena/.gitmodules` 用的是 **SSH URL** `[CODE]`：
   ```
   git@github.com:isaac-sim/IsaacLab.git
   git@github.com:NVIDIA/Isaac-GR00T.git
   ```
   只配了 HTTPS token 的环境下 `git submodule update --init --recursive` 会报 `Permission denied (publickey)`。绕法：配 SSH key，或用 `git config --global url."https://github.com/".insteadOf "git@github.com:"` 重写协议。

3. ⚠️ **`pip install -e .` 的 `-e` 不能省。** `lw_benchhub/__init__.py:2` 把配置目录定位为 `CONFIGS_PATH = Path(__file__).parent.parent / "configs"` `[CODE]` —— 即**仓库根的 `configs/`，位于安装包之外**。非 editable 安装后 `CONFIGS_PATH` 会指向 site-packages 里一个不存在的目录，所有 `--task_config` 查找立即失败。同理，`configs/` 不能从仓库里移出去。

### 5.4 声明依赖清单

`pyproject.toml` `[CODE]`：

| 类别 | 包 |
|---|---|
| 数值/工具 | `numpy`、`scipy`、`tqdm`、`pyyaml`、`h5py` |
| 视觉 | `opencv-python`、`pillow`、`imageio`、`imageio-ffmpeg` |
| RL | `skrl`、`gymnasium`、`tensorboard` |
| 通信 | `grpcio`、`protobuf`、`pyzmq`、`fastapi`、`uvicorn`、`requests` |
| 机器人 | `pinocchio`、`urdfpy`、`trimesh` |
| Lightwheel | `lightwheel-sdk` |
| extra `[lerobot]` | `lerobot` |

⚠️ **`grpcio` / `protobuf` / `pyzmq` 声明了但代码里没有任何 import** `[CODE]`（grep 确认）—— 是历史遗留或规划中的传输后端。实际 IPC 用 `multiprocessing.connection` + socket，RESTful 用 fastapi/uvicorn（§3.7）。

⚠️ `setup.py` 里 `package_dir` 映射了一个**不存在的目录 `lw_benchhub_policy`** `[CODE]`。目前无害（`pyproject.toml` 优先），但说明 `setup.py` 是过时残留。

### 5.5 路径 B：`docker/`（13 个文件）

关键内容 `[CODE]`：

| 文件 | 要点 |
|---|---|
| `base.dockerfile` | 基镜像 `nvcr.io/nvidia/base/ubuntu:noble-20250619`；`OMNI_SERVER=…/Assets/Isaac/5.1`；`EXPOSE 47998/udp`（Isaac Sim livestream）、`49100/tcp`；强制 `numpy==1.26.4`（**即 numpy 1.x，不是 2.x**）；apt/pip 用 **3 次重试循环** 抗网络抖动 |
| `environment.yml` | conda 环境定义，`torch==2.5.1` —— 与 `install.sh` 冲突（§5.2） |
| `Dockerfile` | 会 `pip install -e third_party/robocasa` —— ⚠️ **该目录在仓库中不存在**，此路径当前会失败 `[CODE]` |

⚠️⚠️ **`base.dockerfile` 里硬编码了一个代理地址 `http://127.0.0.1:7897`** `[CODE]`。这是原作者的本地代理，**在别的机器上构建必然失败或超时**，需要改成自己的代理或删掉。

### 5.6 依赖拓扑：三层 + 一个外部包

```
lw_benchhub
    ├── isaaclab_arena  （pin 在 c7b70779，v0.1.0 时代）
    │       └── isaaclab / Isaac Sim 5.0 或 5.1
    ├── lightwheel_sdk  （闭源，运行时拉资产）
    └── lw_benchhub_autosim → 依赖一个 pyproject 未声明的外部包（§3.8）
```

⚠️ **版本落差提醒**：README 徽章写的 "Isaac Lab 5.0.0" 实际指 **Isaac Sim 5.0.0**（Isaac Lab 本身版本号是 2.x），而 `docker/base.dockerfile` 的 `OMNI_SERVER` 指向 **5.1** 的资产。Arena 被 pin 在 `c7b70779`（v0.1.0 时期），而 Arena 上游已到 v0.2.x —— **不要自行升级 Arena 子模块**，§2.5 的 9 处 monkey patch 是按 pin 住的那个版本写的。

---

## 6. 基本使用流程

> 想直接上手敲命令，先看 [`quickstart.md`](quickstart.md)（若已生成）；本章解释流程背后的机制。
>
> 📌 **本章描述"该怎么跑"，但跑起来之后最容易撞上的三件事本章看不出来**（`[实践]` 级，见 [`troubleshooting.md`](troubleshooting.md) B 组 L355–510）：
> - 成功率 **0%、机器人只轻微抽搐** → HF checkpoint 自带 `compile_model: True`，环境变量关不掉 → [`Q19`](troubleshooting.md#q19)
> - 加载 checkpoint 时**几百个 key 不匹配只报一句 warning**，权重被静默随机初始化 → [`Q18`](troubleshooting.md#q18)
> - **换任务或换场景后成功率一律 0%** —— 是 OOD 而非配置错 → [`Q22`](troubleshooting.md#q22)
>
> 本机跑通的具体命令与配置组合见 [`ai_knowledge.md`](ai_knowledge.md) §1.3（两条评测路径对照）。
>
> 📌 **想直接敲命令** → ⭐ [`quickstart.md`](quickstart.md) §2 三个带**预期输出**的运行示例（示例 A = 唯一成功闭环的 40% 基准评测）；改参数看 §3，动手前过一遍 §5 自检清单。
> 📌 **要完整入口点清单与本机实测数字** → [`code_knowledge.md`](code_knowledge.md) §2：§2.1 六行运行前奏（⚠️ 比本章 §6.1 的"三行范式"多三行，本机缺一行就跑不起来）、§2.2 入口点总表、§2.3 ★路径 B **40%（4/10）/ 10m39s**、§2.7 采数 29 eps → 34.5%、§2.8 scripted PnP **8/8 全失败**。

### 6.1 所有脚本共用的三行范式

**理解这三行，就理解了这个仓库的全部配置流程** `[CODE]` `lw_benchhub/scripts/teleop/teleop_main.py:131`、`:140`、`:141`：

```python
parser.add_argument("--task_config", type=str, default="teleop_base")   # 只给 stem，不给路径
cfg = load_config(args_cli.task_config)                                 # 递归解析 _base_
Context.get_instance().update_from_config(cfg)                          # 灌进全局单例
```

三个推论：

1. **`--task_config` 永远只写文件名主干，不带目录、不带扩展名。** `configs/` 下的整棵树被 `rglob` 扁平化成 stem → 路径的字典 `[CODE]` `lw_benchhub/utils/config_loader.py:31`、`:34`。
2. ⚠️ **stem 冲突是"后写入者胜"**：先 rglob 全部 `.yml`（`:31`），再 rglob 全部 `.yaml`（`:34`）覆盖进同一个 dict。**两个不同目录下的同名文件会静默互相覆盖，且 `.yaml` 一定压过 `.yml`。** 新增配置时先确认 stem 全局唯一。
3. **`_base_` 继承是递归的**，子配置覆盖父配置，最终转成 `argparse.Namespace` `[CODE]` `:66`、`:72`、`:85`、`:88`、`:89`。所以配置对象在脚本里是用 `cfg.xxx` 而不是 `cfg["xxx"]` 访问的。

`configs/` 共 30 个文件，分 6 个子目录；命名约定：`*_base`（可继承的基类）、`ci_*`（CI 用的缩水配置）、`*_play`（评测/回放）。⚠️ **`configs/rl/rsl_rl/` 不存在** —— 与 §4.7 的结论一致。

### 6.2 入口脚本总览

仓库根目录的 shell 包装脚本（每个都只是设好环境变量后转调同名 Python）`[CODE]`：

| 脚本 | 用途 |
|---|---|
| `teleop.sh` | 遥操作 / 数据采集 |
| `train.sh` | skrl PPO 训练 |
| `eval.sh` | 策略评测 |
| `train_ppo.sh` / `eval_ppo.sh` | ManiSkill PPO 训练/评测 |
| `env_server.sh` | 启动环境服务端（解耦模式） |
| `lerobot_eval.sh` | LeRobot 生态评测（§4.9） |
| `install.sh` | 安装（§5.3） |
| `run_ci.sh` / `run_ci_post.sh` | CI 全流程 |

`lw_benchhub/scripts/ci_run/` 下另有 `eval_policy.sh`（getopts 解析，**按模型族切换解释器**）、`replay.sh`、`replay_state_base.sh`、`train_ci.sh`、`replace_floor_plan_image.sh` `[CODE]`。

### 6.3 典型流程一：遥操作采集数据

```bash
./teleop.sh --task_config teleop_base \
  --robot PandaOmron-Rel --layout robocasakitchen-9-8 \
  --record --num_demos 10 --dataset_file ./datasets/my_data.hdf5
```

采集期间键盘：**M 存档 / N 读档 / B 回退 10 帧 / R 重置**（§4.6）。成功判定要连续满足半秒才 latch（§4.3）。

### 6.4 典型流程二：RL 训练与回放

```bash
./train.sh --task_config rl_base --max_iterations 4500   # timesteps = 4500 × rollouts(16)
```

日志落在 `lw_benchhub_logs/skrl/<experiment>/` `[CODE]` `rl/train.py:162`，同时 dump 一份 `agent_cfg.pkl` `:176-177`。

`rl/play.py` 是**唯一参数风格不同的脚本**（只有 5 个参数）`[CODE]` `:29-33`，其 checkpoint 解析有三种方式 `:127-135`：显式 `--checkpoint` / 从 log 目录找最新 / 按 experiment 名找。`--check_success` 是 `store_true` 但**默认已为 True**。

### 6.5 典型流程三：解耦式评测（服务端 + 客户端）

```bash
# 终端 1：环境服务端
./env_server.sh --remote_protocol ipc --ipc_host 127.0.0.1 --ipc_port 50000 --ipc_authkey <key>
# 或 RESTful：--remote_protocol restful --restful_host 0.0.0.0 --restful_port 8000

# 终端 2：策略客户端
./eval.sh --config <policy_config> --save_states --overrides key:subkey=value
```

⚠️ `eval_policy.py` 的 `--overrides` 用 `argparse.REMAINDER` 接收，键名用 `:` 表示嵌套，**值会经过 `eval()`** `[CODE]` `:61`。这既是它能传任意 Python 字面量的原因，也意味着**不要把不受信任的字符串喂给它**。

⚠️ 配置里那个键叫 **`remote_protocal`**（拼写错误，少了 `o`）`[CODE]` `configs/rl/rl_base.yml` —— 写配置时必须照抄这个错拼，否则不生效。

### 6.6 改行为的六个常见诉求（速查）

| 想改什么 | 改哪里 | 证据 |
|---|---|---|
| 并行环境数 | `--num_envs` 或 YAML `num_envs`（RL 家族默认 512 / 200 / 10 / 1，按配置而异） | `[CODE]` |
| 换机器人 | `--robot <id>`，id 见 §3.5 的 28 个 | `[CODE]` |
| 换场景 layout/style | `--layout robocasakitchen-<layout>-<style>`，语法见 §4.4 | `[CODE]` |
| 开启录制 | `--record --dataset_file <path> --num_demos <N>` | `[CODE]` |
| 改相机分辨率 | 改 Arena 侧相机配置（`width`/`height`），**不在 LW-BenchHub 的 YAML 里** | `[CODE]` |
| 改 episode 时长 | ⚠️ **多数情况改不了 YAML** —— 只有 `configs/envhub/example.yml` 的 `episode_length_s` 生效；任务基类硬编码 8.0、RL 硬编码 3.2、遥操作直接禁用超时 | `[CODE]` §4.9 |

**最后一行是最容易浪费时间的一条**：找不到"episode 多长"的配置项不是你没找到，是它确实被写死在代码里。

---

## 7. 常用 API / 接口

> 本章只收**你需要主动调用或实现**的接口。内部实现细节见 §3。

### 7.1 环境组合：`lw_benchhub/utils/env.py`

| 接口 | 签名要点 | 用途 |
|---|---|---|
| `parse_env_cfg(...)` | 见 §3.2 | **最核心的入口**：把 (scene, robot, task, rl) 四个 id 组合成一个可 `gym.make` 的环境配置 |
| `load_cfg_cls_from_registry(cfg_name, cfg_type, backend)` | `cfg_type ∈ {"scene","task","robot","rl"}` | 按 id 规则拼名并从 gym 注册表取配置类；id 拼装规则见 §2.2 |
| `create_env(...)` | — | 组合 + `gym.make` 的便捷封装 |

⚠️ 调用 `load_cfg_cls_from_registry` 时**只传短名**（如 `LiftObj`），前缀由函数自己拼。id 大小写敏感且经过 `.capitalize()`（会把首字母外的全部小写），见 §2.2 的陷阱说明。

### 7.2 RL 配置绑定装饰器：`rl_on`

```python
@rl_on(tasks=["LiftObj"], embodiments=["LeRobot-AbsJointGripper"])
class MyRLCfg(LwRL):
    ...
```

`[CODE]` `lw_benchhub/core/rl/base.py`。⚠️ **已验证缺陷**：`_rl_on_tasks` / `_rl_on_embodiments` 被写在共享基类 `LwRL` 上而非各子类上，因此那句兼容性 `assert` 实际是**全局检查而不是逐类绑定**。**不要依赖这个断言来防止任务/本体错配** —— 它拦不住。

### 7.3 策略插件契约：`BasePolicy`（接自研 VLA 的唯一入口）

`[CODE]` `policy/base.py`（173 行），`class BasePolicy(ABC)` `:26`。

**必须实现的 4 个抽象方法：**

| 方法 | 行号 | 职责 |
|---|---|---|
| `get_model` | `:124` | 加载模型权重，返回模型对象 |
| `get_action` | `:137` | 单步推理：观测 → 动作 |
| `eval` | `:144` | 评测主循环 |
| `reset_model` | `:161` | episode 间重置内部状态（如观测窗口） |

**基类已提供、通常不需要重写的：** `initialize` `:45`、`get_instruction` `:54`、`add_video_frame` `:58`、`step_environment` `:69`、`encode_obs` `:84`、`get_policy_name` `:171`。

两个实现细节会直接影响你的适配代码 `[CODE]`：

- **`step_environment` 会按 `usr_args['joint_mapping']` 重排动作** `:76-78` —— 关节顺序不一致时在配置里给 `joint_mapping`，不用改模型。
- **`encode_obs` 会把 `observation['policy']` 与 `observation['embodiment_general_obs']` 合并**，并做 HWC→CHW 转置 `:95-96`。

两个官方参考实现：`policy/GR00T/gr00t_policy.py`（`class GR00TPolicy` `:45`，另有 `custom_action_mapping` `:141` / `custom_obs_mapping` `:145` 两个可选钩子）和 `policy/PI/pi_policy.py`（`class PIPolicy` `:36`，带 `_build_observation_window` `:65`）。

⚠️ **`gr00t` 和 PI 运行时都没有在 `pyproject.toml` 里声明** `[CODE]` —— 它们活在各自独立的 Python 环境里，这正是 `ci_run/eval_policy.sh:41-58` 要**按模型族切换 conda env / venv** 的原因。**接新策略时按这个模式做，不要试图把所有依赖塞进一个环境。**

### 7.4 远程环境服务：两种协议

服务端 `lw_benchhub/scripts/env_server.py`（144 行），客户端 `lw_benchhub/distributed/` `[CODE]`：

| 协议 | 传输 | 文件 |
|---|---|---|
| `ipc` | **AF_INET TCP**（`multiprocessing.connection` + `socket.fromfd(...)` `ipc.py:47`） | `distributed/ipc.py`（93 行） |
| `restful` | HTTP + JSON（图像 **base64 PNG 内联**） | `distributed/restful.py`（424 行） |

⚠️ **`ipc` 名字容易误导**：它不是共享内存，是本机 TCP。README 的 "zero-copy" 说法未获证实（§3.7）。

服务端参数 `[CODE]` `env_server.py:29-34`：`--remote_protocol`（`ipc`/`restful`）、`--ipc_host`（`127.0.0.1`）、`--ipc_port`（`50000`）、`--ipc_authkey`（默认 `"lightwheel"`，**生产环境请改**）、`--restful_host`（`0.0.0.0`）、`--restful_port`（`8000`）。

远程环境的关键方法是 **`detach()`** `[CODE]`：内部执行 `new_stage()` + `gc.collect()`，让同一个 Isaac Sim 进程能换任务而不重启（§3.7）。这是解耦架构真正的性能来源。

### 7.5 LeRobot / envhub 导出

| 接口 | 位置 | 说明 |
|---|---|---|
| `export_env_for_envhub(...)` | `lw_benchhub/utils/envhub_utils.py:116` | 把 LW-BenchHub 环境包装成 LeRobot 的 `isaaclab_arena` env |
| `_reorg_observation_for_envhub(...)` | `:99-113` | ⚠️ **会重命名观测键**：`embodiment_general_obs` → `policy`，原 `policy` → `camera_obs` |

用法见 §4.9 的 `lerobot_eval.sh` 命令行。

### 7.6 autosim 管线注册

```python
from autosim import register_pipeline   # 注意：autosim 是外部包，未在 pyproject 声明
register_pipeline(id="LWBenchhub-Autosim-<Name>Pipeline-v0",
                  entry_point=..., cfg_entry_point=...)
```

`[CODE]` `lw_benchhub/autosim/__init__.py:4-56`，共 9 条管线。机器人抽象层 `robot_profiles.py` 提供 `get_robot_profile(profile_id)` `:90`、`resolve_robot_settings(profile_id, override)` `:100`、`configure_robot_runtime_settings(...)` `:107`、`build_env_extra_info(...)` `:125`；数据类 `RobotProfile` `:17` / `TaskRobotOverride` `:35` / `ResolvedRobotSettings` `:47`。

### 7.7 MDP 函数库（写新任务时的可复用积木）

`[CODE]` `lw_benchhub/core/mdp/`：14 个观测函数 + 7 个针对家具把手操作的奖励函数（清单与行号见 §3.4）。谓词库在 Arena 侧（`OU.check_place_obj1_on_obj2` 等，见 §4.3、§3.11）。

### 7.8 CLI 参数总表（脚本即接口）

绝大多数脚本**只暴露一个 `--task_config`**，其余全部走 YAML（§6.1）。下表是例外与专用脚本 `[CODE]`：

| 脚本 | 参数 |
|---|---|
| `rl/play.py:29-33` | `--task`、`--robot`（默认 `G1-Hand`）、`--layout`、`--task_config`、`--check_success`（`store_true` 但默认已 True） |
| `teleop/teleop_main.py:131-134` | `--task_config`、`--checkpoint_path`、`--auto_load_checkpoint`、`--batch_name`（默认 `default-batch`） |
| `policy/eval_policy.py:40-42` | `--config`、`--overrides`（`argparse.REMAINDER`，`:` 表嵌套，值经 `eval()`）、`--save_states` |
| `policy/replay_local_scene.py:36-40` | `--dataset_file`（必填）、`--replay_mode`（`action`\|`state`）、`--layout`、`--first_person_view`、`--record` |
| `policy/replay_policy_state.py:32-33` | `--config`、`--state_file`（均必填） |
| `teleop/replay_action_demo.py:38-72` | 13 个，含 `--width`（1920）、`--height`（1080）、`--replay_mode`（`action`\|`joint_target`）、`--demo`（-1 表示全部） |
| `policy/convert_hdf5_to_lerobot_dataset.py:133-138` | `--tgt_repo_id`、`--root_path`、`--only_last_demo`、`--camera_path_in_hdf5`、`--task_description`、`--robot_type`（`X7S-Abs`） |
| `policy/convert_hdf5_to_lerobot_datasetv3.py:244-250` | 同上 + `--hdf5_name`（`dataset_success.hdf5`）、`--skip_frames`（5） |
| `autosim/run_autosim_example.py:11-13` | `--pipeline_id`、`--robot_profile`、`--num_runs` |
| `autosim/reach_plan_sweep.py:8-22` | `--pipeline_id`（必填）、`--num_samples`（64）、`--dx/--dy/--dz`（0.01）、`--yaw_deg`（10.0）、`--seed`（42）、`--top_k`（10） |

---

## 8. 已知问题与限制

> 📌 **按报错现象查解决步骤，去 [`troubleshooting.md`](troubleshooting.md)**（顶部有"快速症状索引"表）。本章是**机制层面的限制清单**，回答"能不能做到"而不是"怎么修"。
>
> 📌 本机复现过程中实际踩到的坑及其无效尝试记录，见 [`ai_knowledge.md`](ai_knowledge.md) §4。
>
> ⚠️ **本章尚未收录 6 处仅由实践发现的限制**（清单见 [`ai_knowledge.md`](ai_knowledge.md) **§7.3**，L371–385）。它们是 `[实践]` 级、未在上游仓库核实，因此**没有并入本章的 `[CODE]` 级清单**；但对"能不能做到"的判断同样重要，评估可行性时请一并读。
>
> 📌 **要"为什么会这样"的代码级机制解释** → [`code_knowledge.md`](code_knowledge.md)：**§7.2 十一条静默失效路径**（改了不报错也不生效——本章多条限制的共同失败形态）、**§7.3 仓库内存在两份 vendored IsaacLab**（973 处差异，改错那份无效，附判别法）、§7.1 硬编码主机路径 79 文件 326 处、**§8.3 22 行 `Qxx` → 代码机制映射**、**§8.4 七条被实测推翻的旧结论**。
>
> ⚠️ **四条本机判定为"未解决"的限制**（`[实践]` 级）：规划器 EE 与仿真 TCP 相差 **0.30 m**（[`Q34`](troubleshooting.md#q34)）；同进程多次批量规划触发 cuRobo 内部 shape mismatch（[`Q31`](troubleshooting.md#q31)）；数据集 PNG 导出约 **40 分钟**且三条优化思路均无效（[`Q36`](troubleshooting.md#q36)）；某 layout 在 boot 阶段无限挂起（[`Q24`](troubleshooting.md#q24)）。

### 8.1 上游 issue 现状（截至 2026-08-29）

**5 个未关闭** `[ISSUE]`：

| # | 标题 | 性质 |
|---|---|---|
| #45 | Provide a stable Python Eval API for bring-your-own-policy evaluation | **能力缺口** —— 目前接自研策略只能走 `BasePolicy` + shell 脚本（§7.3），没有稳定的 Python 评测 API |
| #44 | Broader policy & demo coverage: VLA ckpts + more demos | 资源缺口：VLA 权重未释出 |
| #42 | `ValueError: No bounded region found for object winerack_left_group_1`，K4 场景任务崩溃 | **真实 bug**：物体缺 bounding region，导致环境初始化失败 |
| #40 | PiPER 遥操作采数时 joint_4 被锁定 | 行为疑问，无官方结论 |
| #39 | Bad version of lightwheel_sdk | **装机高频问题**：SDK 版本不兼容（§4.10 依赖它拉资产） |

**6 个已关闭（仍有参考价值，说明这些是常见坑）** `[ISSUE]`：#37（新增本体时如何配每个任务的初始位姿 → 答案就是 §4.5 的 CSV/字典机制）、#33（`Observation key 'global_camera' not found` → 对应 §2.6.7 的相机开关门控）、#32（`/floorplan/v1/registry/get-object` SSL/重试耗尽 → 对应 §4.10 的运行时联网取资产）、#31（Quick Start 里的遥操作跑不起来）、#29（`export_env_for_envhub` 里 `cfg.headless` 被 AppLauncher 默认值静默覆盖 → 对应 §7.5）、#28（`base.dockerfile` 无法从内网 Artifactory 下 Miniconda → 对应 §5.5 的硬编码代理）。

**关闭 ≠ 你不会遇到**：#32/#31/#28 都是环境与网络问题，换机器就可能复现。

### 8.2 README 宣称与代码实测不符（4 项）

完整对照表见 **§4.2**，此处只列结论 `[CODE]`：任务数 **272 而非 268**；机器人变体 **28 而非 27**；layout **可达 62 而非 100 组合**；**rsl-rl 只注册不执行**。

### 8.3 已验证的代码缺陷（15 项）

全部经 grep/读码确认 `[CODE]`。**标 ⚠️ 的会实际影响使用**：

| # | 缺陷 | 位置 | 影响 |
|---|---|---|---|
| 1 | ⚠️ **`rl_on` 绑定是全局的而非逐类** | `utils/decorators.py:29-31` vs `core/rl/base.py:36-37` | 兼容性断言形同虚设，任务/本体错配拦不住（§7.2） |
| 2 | ⚠️ **"zero-copy" 无证据** | `distributed/ipc.py` | 性能预期需下调（§3.7） |
| 3 | `Context.device` 声明两次 | `core/context.py:32` 和 `:51` | 后者（默认 `"cpu"`）生效，前者是死代码 |
| 4 | Context 未声明字段被运行时写入 | `utils/env.py:250-251` 写 `enable_global_illumination`、`enable_full_local_scene` | dataclass 里查不到这两个键，读代码时会困惑 |
| 5 | ⚠️ **`teleop_device` 在 `parse_env_cfg` 里被硬编码成 `None`**（带 TODO） | `utils/env.py:284` | **即使 YAML 写了 `teleop_device: vr-controller`（`configs/data_collection/teleop/g1-controller.yml`）也会被覆盖** |
| 6 | multiprocessing 启动方式不一致 | `"fork"`（`rl/train.py:218-219`、`maniskill_ppo/train.py:181-182`）vs `"spawn"`（`teleop/teleop_main.py:75-76`） | CUDA + fork 组合有已知风险 |
| 7 | 声明未用的依赖 | `grpcio`、`protobuf`、`zmq` | 徒增安装体积（§5.4） |
| 8 | ⚠️ **未声明的硬依赖** | `autosim`（`autosim/__init__.py:1`）、`gr00t`（`policy/GR00T/data_config/data_config.py:15`） | **`pip install` 装完仍然 `ImportError`** |
| 9 | ⚠️ **配置键拼写错误** | `remote_protocal`（`configs/rl/skrl/rl_base.yml`）；`varient: null` 在 `configs/common/env_server/env_server_base.yml` 里重复 | **必须照抄错拼才生效**（§6.5） |
| 10 | `CurriculumCfg` 整段被注释但仍被赋值 | `lw_benchhub_rl/lift_obj/lift_obj.py:203` ← `core/rl/base.py:55` | 课程学习实际不起作用 |
| 11 | ⚠️ **CI 会原地改源码** | `ci_run/replace_floor_plan_image.sh:15-18` 对 `kitchen_arena.py` 做 `sed -i` | **跑完 CI 工作区会脏**，注意 `git status` |
| 12 | `interact_api.py` 是死代码（6 行，无调用者） | `lw_benchhub/interact_api.py` | 无 |
| 13 | ⚠️ **`CONFIGS_PATH` 要求源码签出** | `lw_benchhub/__init__.py:2` | 非 editable 安装直接不可用（§5.3） |
| 14 | `bounce_threshold_velocity` 在三处被重复设置 | `core/tasks/base.py:250-251`、`core/rl/base.py:77-78`、`core/scenes/kitchen/kitchen.py:156-157` | 物理参数的最终值取决于覆盖顺序，不易预测 |
| 15 | 注释与代码矛盾 | `g1.py:997`：`sim.dt = 1/200  # physics frequency: 100Hz` | **注释是错的**，实际 200 Hz。调物理频率时别信注释 |

### 8.4 传感器能力的硬边界（这是选型时最该看的一节）

完整分析见 **§2.6**。**核心结论：LW-BenchHub 没有自研任何传感器模型，只做配置层组装。** 经 grep 确认**缺失**的能力 `[CODE]`：

| 缺失项 | 说明 |
|---|---|
| **深度图** | 全仓库 `data_types` 只有 `["rgb"]`。两处"疑似支持"是**假阳性**：`convert_perspective_to_orthogonal` 的 docstring 挂在一条被 `assert data_type == "rgb"` 守卫的死路径上；另一处是真实硬件的 RealSense 驱动 |
| **激光雷达 / ray caster** | 无任何 `RayCaster` 配置 |
| **IMU** | 无 `ImuCfg`。`IMUKF` 是真机滤波器，不是仿真传感器（假阳性） |
| **触觉 / 6 维力矩** | 无 |
| **关节力矩 / effort 观测** | 未提及 |
| ⚠️ **传感器噪声模型** | **`enable_corruption=True` 是空转的** —— 没有任何 `ObsTerm` 传了 `noise=` 参数。**不要以为开了这个开关就有观测噪声** |
| 镜头畸变 / 卷帘快门 / 曝光 | 未提及 |
| 路径追踪渲染 / 抗锯齿模式 | 未提及 |
| 纹理与材质随机化 | 未提及（Arena 侧有 8 类变化，但不含纹理） |

**唯一非平凡的隐藏耦合** `[CODE]`：**开启逐环境相机内参随机化会静默关闭 tiled rendering**（`set_use_tiled_camera(False)`），而 tiled rendering 是 Arena 的默认开关（`_use_tiled_camera: ClassVar[bool] = True`，`Arena:isaaclab_arena/utils/cameras.py:32`）。**后果是多环境并行渲染吞吐大幅下降** —— 想做内参域随机化就要接受这个代价（§2.6.13）。

**视觉 sim2real 的实际策略不是传感器建模，而是数字孪生 + RGB 叠加**（§2.6.13）。如果你的研究依赖深度/激光/触觉，本工具链需要自己扩展。

### 8.5 安装与部署层面的限制

`[CODE]`，详见 §5：

1. ⚠️ **两条安装路径的 torch 版本冲突**：`install.sh` 装 2.7.0，`docker/environment.yml` 装 2.5.1，且**没有任何 dockerfile 调用 `install.sh`**。二者是平行方案，不可混用。
2. ⚠️ **`docker/Dockerfile` 当前会失败**：它 `pip install -e third_party/robocasa`，**该目录不存在**。
3. ⚠️ **`base.dockerfile` 硬编码了本地代理 `http://127.0.0.1:7897`**，换机器构建必然超时。
4. ⚠️ **Arena 子模块用 SSH URL**，只配 HTTPS token 的环境 `git submodule update --init --recursive` 会 `Permission denied (publickey)`。
5. **没有声明 `requires-python`**，Python 版本无人把关。
6. **`setup.py` 映射了不存在的 `lw_benchhub_policy` 目录**（过时残留）。
7. ⚠️ **必须联网才能跑**：厨房场景与物体在运行时通过 `lightwheel_sdk` 从云端注册表拉取，**没有独立下载脚本，离线环境不可用**。而且 `kitchen_objects.py:31-32` 在 **import 阶段**就调 `list_registry()`，网络不可达时报错位置极具迷惑性（§4.10）。
8. **不要自行升级 Arena 子模块**：它被 pin 在 `c7b70779`（v0.1.0 时期），而 §2.5 的 9 处 monkey patch 是按这个版本写的。Arena 上游已到 v0.2.x。

### 8.6 设计层面的固有约束（不是 bug，但会限制你）

`[CODE]`：

| 约束 | 说明 |
|---|---|
| **全局可变单例 `Context`** | 一个进程内只能有一套配置；`str_to_execute_mode()` 对未知值**静默回落到 `TELEOP`**（`:60`），拼错模式名不会报错（§2.3、§2.4） |
| **9 处 monkey patch isaaclab** | 其中 `patch_isaaclab_tasks_mdp` 是在给上游已删除的 API 做"生命维持"。**升级 isaaclab 会直接破坏本仓库**（§2.5） |
| **episode 时长基本写死** | 只有 `configs/envhub/example.yml` 的 `episode_length_s` 生效；任务基类 8.0、RL 3.2、遥操作禁用超时（§4.9、§6.6） |
| **RL 可训练面极窄** | 272 个任务，**只有 6 个 RL 配置，且全部挂在 `LiftObj` 上**（§3.6） |
| **控制频率不一致** | RL 20 Hz vs 遥操作/回放 50 Hz。**跨模式复用轨迹要先对齐频率**（§2.6.10） |
| **动作滤波会导致回放不一致** | `filter_action()` 做 EMA + 速度钳制（`utils/env.py:238`），是"录下来的动作重放结果不同"的机制来源（§3.2） |
| **训练与评测光照不同** | `ExecuteMode.TRAIN` 多一个强度 50000 的球灯（§4.4） |
| **stem 命名空间扁平且冲突静默** | `configs/` 全树按文件名主干扁平化，`.yaml` 覆盖 `.yml`，同名文件互相静默覆盖（§6.1） |
| **`layout_task_mapping.csv` 文件名无任何代码引用** | 靠 `rglob("*.csv")` 泛化发现，可读性差但也意味着可自由加表（§4.5） |
| **LIBERO 位姿字典只覆盖一个机器人** | `LIBRO_SCENE_ROBOT_STATE` 仅对 `LeRobot-AbsJointGripper-RL` 有效（§4.5） |
| **两项 Arena alpha 警告** | Arena 自身声明处于早期阶段，API 可能变动（§3.11） |

### 8.7 明确的"未找到 / 未提及"清单（**命中此表就别再搜了**）

`[CODE]` grep 确认无证据：

- 零拷贝 / 共享内存 / CUDA-IPC 张量传输 —— **未找到**
- gRPC 使用 —— **未找到**（尽管声明了 `grpcio>1.73`、`protobuf>6`）
- 分布式层的 ZMQ 使用 —— **未找到**
- `autosim` 包源码 —— **未找到**（本仓库只有插件侧）
- `gr00t` 包源码 —— **未找到**（只有适配层）
- `interact_api.py` 的调用者 —— **未找到**
- `core/robots/__init__.py` 里的机器人注册 —— **未找到**（文件为空，注册在各厂商子包里）
- `third_party/` 下除 `IsaacLab-Arena` 外的子模块 —— **未找到**
- `configs/rl/rsl_rl/` 目录 —— **不存在**
- 独立的资产下载脚本 —— **未提及**
- `task.csv`（被 `lift_obj.py:44` 的注释引用）—— **仓库中不存在**
- 显存需求、磁盘空间需求 —— **未提及**
- Python 版本要求 —— **未声明**
- 深度 / 激光 / IMU / 触觉 / 6 维力矩 / 关节力矩观测 —— **未找到**（§8.4）
- 传感器噪声模型、镜头畸变、卷帘快门、曝光模型 —— **未找到**
- 路径追踪渲染、抗锯齿模式、纹理与材质随机化配置 —— **未提及**
- `contact_offset` / `rest_offset` 的显式设置 —— **未找到**（用 PhysX 默认值）

---

## 9. 参考资源

### 9.1 官方源（本文档的全部一手依据）

| 资源 | 地址 | 用途 |
|---|---|---|
| LW-BenchHub 主仓库 | `github.com/LightwheelAI/LW-BenchHub` | **`[CODE]` 级证据的主要来源**；README、`configs/`、`lw_benchhub/`、`lw_benchhub_tasks/`、`lw_benchhub_rl/`、`policy/`、`docker/` |
| Issue 列表 | `github.com/LightwheelAI/LW-BenchHub/issues` | §8.1 的依据；**装机遇阻时先搜这里** |
| IsaacLab-Arena | `github.com/isaac-sim/IsaacLab-Arena` | 上游组合框架。本仓库 pin 在 `c7b70779`（v0.1.0 时期），**引用时注意版本落差** |
| AutoDataGen | `github.com/LightwheelAI/AutoDataGen` | 同组织的自动数据生成项目（与 `lw_benchhub/autosim/` 相关，但 `autosim` 包本体不在 BenchHub 仓库里） |
| Lightwheel 平台 | `lightwheel.ai/lightwheel-platform` | 商业平台介绍；`lightwheel_sdk` 与云端资产注册表的归属方 |
| LightwheelAI 组织 | `github.com/LightwheelAI` | 组织下其他相关仓库 |

### 9.2 必须一并阅读的上游文档

本工具链是**薄组合层**（§2.1），真正的行为大量由上游决定。排查问题时按这个顺序往上追：

```
LW-BenchHub（本文档）
    ↓ 组合原语、tiled rendering、相机内参、谓词库
IsaacLab-Arena 文档
    ↓ Manager-based env、ObsTerm/RewTerm/DoneTerm、EventTerm、AppLauncher
Isaac Lab 文档
    ↓ 物理求解器参数、渲染管线、USD 场景
Isaac Sim / Omniverse 文档
```

⚠️ **README 徽章上的 "Isaac Lab 5.0.0" 实际指 Isaac Sim 5.0.0**（Isaac Lab 自身版本号是 2.x），而 `docker/base.dockerfile` 的 `OMNI_SERVER` 指向 **5.1** 的资产路径 —— 查上游文档时注意别对错版本（§5.6）。

### 9.3 关联的学术与生态项目

| 项目 | 关系 |
|---|---|
| **RoboCasa** | 141 个任务与厨房场景体系的来源；`docker/Dockerfile` 试图安装 `third_party/robocasa`（**该目录不存在**，§8.5） |
| **LIBERO** | 131 个任务的来源（§4.3） |
| **ManiSkill** | `lw_benchhub/scripts/maniskill_ppo/` 是其 PPO 实现的移植（§4.7） |
| **LeRobot** | 数据集格式与评测生态（§4.9）；`lw_benchhub/utils/lerobot_common/` 是 vendored 副本 |
| **skrl** | 唯一被真正实例化的 RL 库（§4.7） |
| **rsl-rl** | 已注册但**从未执行**（§4.7） |
| **NVIDIA Isaac-GR00T** | `policy/GR00T/` 的适配对象；作为 Arena 的子模块出现（SSH URL，§5.3） |
| **Physical Intelligence (PI)** | `policy/PI/` 的适配对象 |
| **cuRobo** | `lw_benchhub/autosim/content/configs/robot/x7s*.yml` 是 cuRobo 风格的运动规划配置（§3.8） |

### 9.4 本知识库内的关联文档

| 文档 | 何时去看 |
|---|---|
| ⭐ [`quickstart.md`](quickstart.md) | **动手前先读**：最短路径命令 + 自检清单 |
| [`troubleshooting.md`](troubleshooting.md) | **手上有一条具体报错时**：顶部"快速症状索引"按现象查 `Qxx` |
| [`ai_knowledge.md`](ai_knowledge.md) | 想知道**为什么会这样、试过哪些无效方法**、估工作量 |
| [`code_knowledge.md`](code_knowledge.md) | 要**改代码 / 找某个类或参数在哪个文件**（描述对象是本机复现仓库 `lw_benchhub_tour`） |
| [`00-index.md`](00-index.md) | 各层的**章节行号表**，用 `Read` 的 `offset`/`limit` 精准读取 |

### 9.5 证据等级说明（本文档内的标注约定）

| 标注 | 含义 |
|---|---|
| `[CODE]` | 可在上游仓库逐行验证。**工程决策只信这一级。** 附相对路径（必要时带行号） |
| `[README]` | 来自仓库 README 或文档的宣称。⚠️ 本项目已发现 4 处与代码不符（§4.2） |
| `[ISSUE]` | 来自 GitHub issue 讨论，非官方结论 |
| `[官网]` | 来自 Lightwheel 官网的市场表述 |
| `[推断]` | 证据不足以定论，仅作阅读线索 |
| **未提及 / 未找到** | 已 grep 确认资料中无证据。**不推测、不编造**（清单见 §8.7） |

**引用前缀约定**：无前缀 = LW-BenchHub 仓库；`Arena:` = IsaacLab-Arena 仓库；`AutoDataGen:` = AutoDataGen 仓库。
