# genesis_world 代码层知识：`genesis-world-tour` 复现仓库

> **描述对象声明**
> 本文档描述的是**本机复现仓库 `genesis-world-tour`**（下称 `<repo_root>`），**不是上游本体 `Genesis-Embodied-AI/Genesis`**。
> 上游库的原理、API 与能力边界见 **[原理层 `background_knowledge.md`](./background_knowledge.md)**（描述 genesis-world **1.3.3**）。
>
> ⚠️ **版本落差**：本仓库运行在 **genesis-world 1.2.2**，原理层描述 **1.3.3**。
> 本文档中的**具体 API 写法**（`gs.morphs.*` 签名、`Camera.render()` 返回值、`inverse_kinematics()` 返回长度等）**只对 1.2.2 成立**，不可直接套用到 1.3.3；而**能力边界类结论**（IPC 需额外安装、FEM 无 IPC 不做刚-柔接触、相机无噪声模型）两个版本一致。
>
> 🔒 **已替换敏感信息**：仓库源码中存在 **12 个文件、49 行**主机绝对路径（`/mnt/...`、`/home/<user>/...`）。本文档一律写为 `<repo_root>` / `<path>` / `<user_home>` / `<conda_env>`，**并在 §7.1 集中列出它们的位置与用途**，便于换机部署时逐一替换。文档内不含任何账号、密码、密钥、token。
>
> **证据等级**：`[CODE]` = 可在 `<repo_root>` 内逐行核实（附 `文件:行号`）；`[README]` = 来自仓库 `README.md` / 仓库内 `CLAUDE.md`；`[推断]` = 证据不足以定论。**无法判定某处是「本地改的」还是「上游本来就没有」的，一律标 `[推断]`，不计入本次改动。**

---

## 摘要（≤200 字，用于索引）

`genesis-world-tour` 是一个**四阶段递进的 Genesis 能力探针仓库**（16 个 Python 文件 / 5608 行，无包结构、无 `setup.py`、无测试框架），三个最关键特征：

1. **「一次性演示脚本 + 独立客观验证门」的成对结构**。每个 Stage 都配一个 `verify_stageN.py`，用 `ffprobe` + `cv2` 像素统计 + JSON 数值断言做**无需看图**的硬门禁，失败 `sys.exit(1)`。
2. **把 1.2.2 的 API 陷阱固化进代码**。`gs.morphs.Franka` 不存在、IK 返回完整 `qpos(16,)`、`render()` 返回 4-tuple、相机必须在 `build()` 前添加、rsl-rl 0-based checkpoint 编号——每一条都在源码里以注释 + 防御性分支写死。
3. **进程隔离与降级回退是架构主线**。Stage 3 用 `subprocess.run` 让每个阶段独占一次 `gs.init()`；Stage 4 用 `try IPC / except ImportError → PBD` 在能力缺失时自动降级，并把降级事实写进产物 JSON。

---

## 1. 代码结构总览

### 1.1 目录树 `[CODE]`

```
<repo_root>/
├── CLAUDE.md                     414 行  ← 仓库自带的 agent 指南，本层最富信息的单一来源
├── README.md                     109 行  ← 四阶段总览 + 快速开始
├── LICENSE
├── .gitignore                     25 行  ← 忽略全部运行产物目录
├── images/                        9 个文件（8 GIF + 1 PNG，各 Stage 的成果动图）
│
├── scene_factory.py              411 行  【Stage 2】配置驱动的场景工厂
├── vla_closed_loop_demo.py       626 行  【Stage 1】VLA 单场景闭环主脚本
├── batch_eval_vla.py             616 行  【Stage 2】8 场景批量评测
├── verify_stage2.py              193 行  【Stage 2】无图像客观验证门
├── classical_demo.py             383 行  【对照组】纯经典控制（无 VLA）
├── hybrid_vla_demo.py            410 行  【对照组】VLA 理解 + 经典 IK 执行
│
├── stage3/                       【Stage 3】Go2 四足 RL 训练与可视化
│   ├── go2_env.py                308 行  并行环境封装（Genesis ↔ rsl-rl 适配）
│   ├── go2_train.py              178 行  官方风格训练脚本 + 全部超参
│   ├── train_subprocess.py       252 行  训练子进程（绝对目标迭代数契约）
│   ├── eval_subprocess.py        149 行  评测/录像子进程
│   ├── run_orchestrator.py       155 行  5 阶段主调度器
│   ├── verify_stage3.py          158 行  MP4 / checkpoint / tensorboard 三重门
│   ├── run_in_env.sh              10 行  conda + 环境变量包装器
│   └── gradient_test.sh           42 行  num_envs 梯度 OOM 测试
│
└── stage4/                       【Stage 4】刚-柔 / 刚-流耦合
    ├── cloth_grasp_demo.py       416 行  PBD.Cloth 布料形变
    ├── sponge_squeeze_demo.py    474 行  PBD.Elastic 体积软体挤压
    ├── glass_water_demo.py       528 行  SPH.Liquid 刚-流耦合打翻水杯
    ├── verify_stage4.py          351 行  三个 demo 的统一验证门
    ├── glass_cup.urdf             11 行  单 link / 5 个 box 碰撞体的水杯
    └── meshes/cloth.obj          706 行  16×16 布料网格（脚本可自动生成）
```

**规模**：16 个 `.py` 文件、**5608 行**；`git log` 共 **39 次提交** `[CODE]`。

### 1.2 各部分职责

| 部分 | 目标能力 | 结论 |
|---|---|---|
| Stage 1（`vla_closed_loop_demo.py`） | 单场景 VLA 闭环 pick-and-lift | ❌ 未达成，见 `ai_knowledge.md` §4.4 |
| Stage 2（`scene_factory.py` + `batch_eval_vla.py` + `verify_stage2.py`） | 8 场景泛化评测 | ❌ **0/8**，全部失败 |
| 对照组（`classical_demo.py` / `hybrid_vla_demo.py`） | 证明「问题在 VLA 而非仿真器」 | 用于归因，非交付物 |
| Stage 3（`stage3/`） | Go2 四足并行 RL 训练 | ✅ 达成，151,839 steps·s⁻¹ |
| Stage 4（`stage4/`） | 刚-柔 / 刚-流耦合 | ✅ 三个 demo 全部通过验证门 |

### 1.3 三条贯穿全仓库的结构约定 `[CODE]`

1. **无包结构、无 `__init__.py`、无 `setup.py`、无 `requirements.txt`、无测试框架**。所有脚本靠**同目录相对 import** 互相引用（`batch_eval_vla.py:28` `from scene_factory import ...`；`stage3/train_subprocess.py:32` `from go2_env import Go2Env`），因此**必须 `cd` 到脚本所在目录再运行**。
2. **`demo` + `verify` 成对**。`verify_stage2.py` / `stage3/verify_stage3.py` / `stage4/verify_stage4.py` 都不依赖人眼看图，只用 `ffprobe` 读视频元数据、`cv2` 做像素掩膜统计、读产物 JSON 做数值断言，全部通过才 `sys.exit(0)`。
3. **全部运行产物被 gitignore**。`.gitignore` 忽略 `stage1_*/`、`stage2_*/`、`classical_*/`、`hybrid_*/`、`stage3/logs/`、`stage3/rl_visualizations/`、`stage4/diagnostics{,_sponge,_glass}/` `[CODE]` —— 仓库里**只有代码，没有任何 checkpoint、视频或日志**，克隆后需要自己重新跑出来。

---

## 2. 入口点与运行方式

> 所有命令都假定已激活 conda 环境（见 §5）。**路径一律相对 `<repo_root>`**。

### 2.1 入口点总表 `[CODE]`

| 入口 | 位置 | 必须的工作目录 | 默认产物目录 |
|---|---|---|---|
| Stage 1 单场景 VLA 闭环 | `vla_closed_loop_demo.py:205` | `<repo_root>` | `stage1_eval/` |
| Stage 2 批量评测 | `batch_eval_vla.py:501` | `<repo_root>` | `stage2_eval/` |
| Stage 2 验证门 | `verify_stage2.py:70` | `<repo_root>` | 只读，`exit 0/1` |
| 经典控制对照 | `classical_demo.py:70` | `<repo_root>` | `classical_eval/` |
| 混合方案对照 | `hybrid_vla_demo.py:128` | `<repo_root>` | `hybrid_eval/` |
| Stage 3 全流程 | `stage3/run_orchestrator.py:71` | `<repo_root>/stage3` | `logs/`、`rl_visualizations/` |
| Stage 3 单独训练 | `stage3/train_subprocess.py:159` | `<repo_root>/stage3` | `logs/go2-walking/` |
| Stage 3 单独录像 | `stage3/eval_subprocess.py:39` | `<repo_root>/stage3` | `--output` 指定 |
| Stage 3 官方风格训练 | `stage3/go2_train.py:142` | `<repo_root>/stage3` | `logs/<exp_name>/` |
| Stage 3 验证门 | `stage3/verify_stage3.py:141` | `<repo_root>/stage3` | 只读 |
| Stage 4 布料 | `stage4/cloth_grasp_demo.py:400` | `<repo_root>/stage4` | `diagnostics/` |
| Stage 4 海绵 | `stage4/sponge_squeeze_demo.py:459` | `<repo_root>/stage4` | `diagnostics_sponge/` |
| Stage 4 水杯 | `stage4/glass_water_demo.py:513` | `<repo_root>/stage4` | `diagnostics_glass/` |
| Stage 4 验证门 | `stage4/verify_stage4.py:324` | `<repo_root>/stage4` | 只读 |

### 2.2 命令与参数

**Stage 1** `[CODE] vla_closed_loop_demo.py:205-220`

```bash
python vla_closed_loop_demo.py \
    --task "Pick up the blue block and place it on the target" \
    --steps 300 \
    --output_dir stage1_eval \
    --pos_scale 0.03 \
    --model_path <path>/openvla-mcx-card \
    --block_pos 0.57 -0.08 0.22 \
    --touch_threshold 0.035
```

`--block_pos` 是 `nargs=3` 的三个浮点数；`--model_path` 默认值是仓库里写死的本地模型目录（**已替换敏感信息**，见 §7.1）。

**Stage 2** `[CODE] batch_eval_vla.py:502-509`

```bash
python batch_eval_vla.py --output_dir stage2_eval --steps 1000 --pos_scale 0.03
python batch_eval_vla.py --scenes eval_scene_1_blue_target eval_scene_4_target_shift   # 只跑指定场景
python verify_stage2.py --output_dir stage2_eval
```

`--scenes` 是 `nargs="*"`，默认 `None` = 跑全部 8 个场景。`verify_stage2.py` 的 `--output_dir` 默认值是 `stage2_eval_8scene`（`verify_stage2.py:72`）而 `batch_eval_vla.py` 默认写到 `stage2_eval`（`batch_eval_vla.py:503`）—— **两个默认值不一致，验证时必须显式传 `--output_dir`**。

**Stage 3** `[CODE] stage3/run_orchestrator.py:78-127`

```bash
cd stage3
python run_orchestrator.py --dry-run     # 只打印 5 个阶段的命令，不执行
python run_orchestrator.py               # 完整跑：0→50→100 两段训练 + 3 段录像
python verify_stage3.py
```

调度器串行执行的 5 个阶段（每阶段一个独立子进程，**各自持有自己的 `gs.init()` 与 CUDA 上下文**）：

1. `eval_subprocess.py --output rl_visualizations/eval_epoch_0_untrained.mp4 --num_steps 400`
2. `train_subprocess.py --num_envs 2048 --max_iterations 50 --exp_name go2-walking`
3. `eval_subprocess.py --checkpoint logs/go2-walking/model_50.pt --output ...eval_epoch_50_mid.mp4 --num_steps 400`
4. `train_subprocess.py --num_envs 2048 --max_iterations 100 --exp_name go2-walking --resume`
5. `eval_subprocess.py --checkpoint logs/go2-walking/model_100.pt --output ...eval_epoch_100_final.mp4 --num_steps 400`

> ⚠️ **`--max_iterations` 是绝对目标迭代数，不是增量** `[CODE] stage3/train_subprocess.py:7-9,229-233`。第 4 阶段传 `100` 而不是 `50`，脚本内部算 `delta = 100 - loaded_iter`。传成增量会训练过头。

**Stage 4** `[CODE]`

```bash
cd stage4
python cloth_grasp_demo.py   --steps 200 --output_dir diagnostics          # :402-404
python sponge_squeeze_demo.py --steps 180 --output_dir diagnostics_sponge  # :461-463
python glass_water_demo.py   --frames 180 --output_dir diagnostics_glass   # :515-517（注意是 --frames 不是 --steps）
python verify_stage4.py --demo all       # choices: cloth|sponge|glass|all  # :326-328
```

### 2.3 环境变量 `[CODE]`

| 变量 | 设置位置 | 作用 |
|---|---|---|
| `HF_HOME` / `TRANSFORMERS_CACHE` | `vla_closed_loop_demo.py:13-14`、`batch_eval_vla.py:16-17`、`classical_demo.py:10`、`hybrid_vla_demo.py:15` | HuggingFace 缓存目录。**在 `import torch/transformers` 之前用 `os.environ[...] = ...` 硬写死**，不读外部环境。换机必改。 |
| `GSPATH` / `GS_HOME` | `stage4/cloth_grasp_demo.py:38-39`、`sponge_squeeze_demo.py:48-49`、`glass_water_demo.py:53-54` | Genesis 资产缓存目录。用 `os.environ.setdefault(...)`，**外部已设则不覆盖**，比上面四个温和。 |
| `TMPDIR` | `stage3/run_in_env.sh:8`、`gradient_test.sh:8` | 临时目录重定向到大盘。 |

`stage3/run_in_env.sh` 是**后台任务专用包装器** `[CODE] stage3/run_in_env.sh:1-10`：后台 bash 任务不继承 conda/profile，所以它显式 `source` conda 初始化脚本、`conda activate <conda_env>`、`source <path>/genesis_vla_env.sh`、设 `TMPDIR`、`cd` 到 stage3 目录，最后 `exec python "$@"`。

---

## 3. 核心模块详解

挑选 **5 个**在「复现 / 改造」时最常被打开的模块。

### 3.1 `scene_factory.py` —— 配置驱动的场景工厂 `[CODE]`

**路径**：`<repo_root>/scene_factory.py`（411 行）
**职责**：把「8 个评测场景」表达成 8 个纯字典，再由一个函数统一构建 Genesis 场景。这是全仓库唯一**声明式**的部分。

| 实体 | 行号 | 说明 |
|---|---|---|
| `SCENE_1` … `SCENE_8` | 42 / 55 / 75 / 95 / 111 / 137 / 153 / 169 | 8 个场景字典 |
| `WIDE_CAMERA_DEFAULT` | 35 | 人视角宽相机默认参数，8 个场景共用 |
| `get_all_scene_configs()` | 194 | 返回 8 个字典组成的列表 |
| `build_scene_from_config(config)` | 201 | 唯一的场景构建函数，返回 13 键字典 |
| `generate_non_overlapping_positions(...)` | 366 | 干扰物无重叠采样 |

**场景字典的字段**：`name`、`task_instruction`、`target`（`pos`/`size`/`color`）、可选 `distractors`、`camera`（`sensor_pos`/`sensor_lookat`）、可选 `lighting`（`ambient_light`/`directional_intensity`），每个场景顶部有一行 `# [axis: ...]` 注释说明它变化的是哪个维度。

**关键设计点**：

- **双相机**：`cam` 是喂给 VLA 的 224×224 相机（每个场景可自定义 `sensor_pos`/`sensor_lookat`），`wide_cam` 是 640×480 / fov 45 的人视角相机，**8 个场景完全相同**（`scene_factory.py:35`），只用于录像，不进入模型输入。两个相机**都在 `scene.build()`（:319）之前添加**（:298-316）—— `Scene.add_camera` 带 `@gs.assert_unbuilt` 装饰器，build 后再加会抛异常。
- **PD 增益必须在 build 之后设**（:323-336）：`set_dofs_kp/kv` 手臂 7 轴 `[4500,4500,3500,3500,2000,2000,2000]` / `[450,450,350,350,200,200,200]`，手指 2 轴 `kp=2000, kv=200`，并用 `set_dofs_force_range(±20N)` 限幅。
- **Franka 用 URDF 加载，不是 `gs.morphs.Franka`**（:266-272）：`os.path.join(os.path.dirname(gs.__file__), "assets","urdf","panda_bullet","panda.urdf")`。末端 link 名是 `panda_link7`（**不是 `hand`**），手指是 `panda_leftfinger` / `panda_rightfinger`。
- **`surface` / `color` 传给 `add_entity()`，不传给 morph 构造器**（docstring `:212-216` 明确列了这三条 1.2.2 注意事项）。
- **`vis_options` 只在场景带 `lighting` 字段时才构造**，用 `gs.options.VisOptions(ambient_light=..., lights=[DirectionalLight(...)])`，`DirectionalLight` 从 `genesis.options.vis` 导入（:19）。
- **收敛点**：场景 1/2/3/5/6/7/8 的目标块都在 `(0.57, -0.08, 0.22)`，只有场景 4 移到 `(0.65, 0.05, 0.22)`——这正是它偏差 267 cm 而其余场景都稳定在 ~35 cm 的原因（见 `ai_knowledge.md` §4.4）。
- `generate_non_overlapping_positions` 的采样约束（:366+）：X∈[0.4, 0.75]、Y∈[−0.3, 0.3]、距目标 >0.15 m、距机械臂基座 >0.35 m、干扰物两两 >0.12 m，最多重试 100 次。

**调用关系**：`batch_eval_vla.py:28` 导入 `build_scene_from_config` / `get_all_scene_configs` / `WIDE_CAMERA_DEFAULT`。Stage 1 的 `vla_closed_loop_demo.py` **不**用这个工厂，它自己内联建场景——两边的建场景逻辑是**重复代码**。

### 3.2 `vla_closed_loop_demo.py` / `batch_eval_vla.py` —— VLA 闭环 `[CODE]`

**路径**：`<repo_root>/vla_closed_loop_demo.py`（626 行）、`<repo_root>/batch_eval_vla.py`（616 行）
**职责**：Stage 1 单场景 / Stage 2 批量的 OpenVLA 闭环控制。两者**共享同一套控制逻辑，且是复制粘贴而非抽取共用模块**——`ActionDenormalizer`、`GripperController`、`compute_target_quat`、`check_gripper_touch_block` 在两个文件里各有一份（`batch_eval_vla.py:33/52/113/128`）。**改一处必须同步改另一处。**

**闭环单步的固定顺序**（`batch_eval_vla.py:217-318`，Stage 1 同构）：

1. `cam.render(rgb=True)` → **`if isinstance(img, tuple): img = img[0]`**（:219-221）——1.2.2 的 `render()` 返回 `(rgb, depth, seg, normal)` 四元组。
2. 浮点图转 uint8；`wide_cam` 同样渲染一帧存录像（:229-236）。
3. 构造 prompt `f"In: {instruction}\nOut:"`，`processor(prompt, pil_img)`，**浮点张量转 `bfloat16` 上 cuda，整型张量只上 cuda**（:243-246）。
4. `model.predict_action(input_ids, unnorm_key="bridge_orig", do_sample=False, pixel_values=...)`（:249-254）；返回值**可能是 Tensor 也可能是 numpy**，两种都处理（:257-260）。
5. `delta_pos = raw_action[:3] * (pos_scale / 0.05)`（:265）——`predict_action` 已按 `bridge_orig` 反归一化过，这里是二次缩放。
6. **LIFT/HOLD 状态下冻结手臂位姿**（:275-277），否则 `target = current + delta`。
7. `franka.inverse_kinematics(link=, pos=, quat=)` → **返回完整 `qpos`（16 维），必须用 `motors_dof=np.arange(7)` 切片**（:284-287）；异常时回退到 `franka.get_qpos()[motors_dof]`（:288-291）。
8. `GripperController.update()` 给出 `finger_targets` 与 `lift_offset`；有抬升时**再解一次 IK**（:303-311）。
9. `control_dofs_position()` 分别下发手臂与手指目标（:314-315），`scene.step()`。
10. 记录轨迹；**发散检测**：`qpos` 出现 NaN/Inf 立即 break（:342-344）。

**`GripperController` 状态机**（`batch_eval_vla.py:52-110`）：常量 `APPROACH=0, GRASP=1, HOLD=2, LIFT=3`。
⚠️ **两个文件的状态转移顺序不同**：`batch_eval_vla.py` 是 `APPROACH → GRASP → LIFT → HOLD`（:97 在 GRASP 里直接跳 LIFT，:106 在 LIFT 结束跳 HOLD），常量名 `HOLD=2` 与它在流程中的实际位置（最后）**不一致**，读代码时容易误判。
⚠️ **构造器默认值与实际调用值不同**：默认 `grasp_dist=0.06, grasp_patience=5, hold_steps=80, lift_height=0.15, lift_steps=100`（:67），但实际实例化用的是 `grasp_patience=3, hold_steps=150, lift_height=0.10, lift_steps=80`（`batch_eval_vla.py:198-201`；`vla_closed_loop_demo.py:342` 同）。**改行为要改调用处，不是改默认值。**

**模型必须在 Genesis 之前加载** `[CODE] batch_eval_vla.py:513-560`：注释原文 `# CRITICAL: 必须在 Genesis 初始化之前加载`，`gs.init(backend=gs.gpu)` 在 `:560`，且**整批 8 个场景只 `gs.init()` 一次**（:559 注释 `gs.init() must be called once, before all scenes`）。场景对象靠 GC 回收，注释明确写了 `Genesis has no explicit scene.destroy() method`（:576）。

**模型加载参数**（:519-540）：`AutoProcessor` / `AutoModelForVision2Seq` 均 `trust_remote_code=True, local_files_only=True`；`torch_dtype=torch.bfloat16`；`device_map="auto"`；`attn_implementation` 先试 `flash_attention_2`，`ImportError` 则退 `eager`（:524-530）。

**产物**（`batch_eval_vla.py:440-482`）：每场景一个目录，含宽视角 MP4、VLA 视角 MP4、5 组双视角关键帧 PNG、`trajectory.json`、`run_log.json`；顶层再写 `eval_summary.json`（:594），含 `overall_success_rate`。

### 3.3 `stage3/go2_env.py` —— Genesis ↔ rsl-rl 并行环境适配层 `[CODE]`

**路径**：`<repo_root>/stage3/go2_env.py`（308 行）
**职责**：把 Genesis 的批量刚体仿真包装成 rsl-rl 5.x 能吃的 `Env` 接口。它是**唯一被两个子进程共同 import 的模块**（`train_subprocess.py:32`、`eval_subprocess.py`）。

| 成员 | 行号 | 说明 |
|---|---|---|
| `gs_rand(lower, upper, batch_shape)` | 10 | 批量均匀采样工具 |
| `Go2Env.__init__` | 16 | 建场景 → 加机器人 → **可选相机** → `scene.build(n_envs=)` |
| `Go2Env.step(actions)` | 160 | **返回 4-tuple**（`obs, rew, reset_buf, extras`），不是 gym 的 5-tuple |
| `Go2Env.get_observations()` | 211 | 返回 `TensorDict`，键为 `"policy"` |
| `Go2Env._reset_idx` / `_update_observation` / `reset` | 214 / 265 / 278 | |
| 6 个 `_reward_*` 方法 | 284–307 | `tracking_lin_vel` / `tracking_ang_vel` / `lin_vel_z` / `action_rate` / `similar_to_default` / `base_height` |

**关键设计点**：

- **相机必须在 `scene.build()` 之前加**（:76-79）：`if camera_cfg is not None: self.cam = self.scene.add_camera(**camera_cfg)`，紧接着 `:80` 才 `self.scene.build(n_envs=num_envs)`。因为 `Go2Env.__init__` 内部就 build 了，**外部无法在构造后再加相机**——所以录像用的相机是通过构造参数 `camera_cfg=` 传进来的（`eval_subprocess.py:66-81`）。
- **奖励函数用反射注册**：`self.reward_functions[name] = getattr(self, "_reward_" + name)`，并且 `self.reward_scales[name] *= self.dt`（scale 在注册时就乘了 dt）。新增奖励项 = 在 `reward_cfg["reward_scales"]` 加一个键 + 写一个同名 `_reward_<键>` 方法，无需改注册逻辑。
- **关节顺序做了两次映射**：`motors_dof_idx` 按 `env_cfg["joint_names"]` 顺序取 `dof_start`，`actions_dof_idx = torch.argsort(motors_dof_idx)`。注意 `default_joint_angles` 字典的书写顺序（FL/FR/RL/RR）与 `joint_names` 列表顺序（FR/FL/RR/RL）**故意不同**，靠按名查表对齐。
- 固定 `self.dt = 0.02`（50 Hz，:25）与 `simulate_action_latency = True`（:24，模拟真机 1 步延迟），**都是硬编码，不走配置**。
- 资产用 Genesis 内置相对路径：`urdf/plane/plane.urdf`、`urdf/go2/urdf/go2.urdf`。

### 3.4 `stage3/train_subprocess.py` + `run_orchestrator.py` —— 进程隔离 + 检查点契约 `[CODE]`

**路径**：`<repo_root>/stage3/train_subprocess.py`（252 行）、`run_orchestrator.py`（155 行）

**为什么要分进程**：`run_orchestrator.py:3-4` 注释原文——「Sequentially calls eval_subprocess.py and train_subprocess.py via subprocess.run for process isolation (each subprocess owns its own gs.init / CUDA context)」。一个进程里既训练又渲染会撞 CUDA 上下文，所以 5 个阶段是 5 次 `subprocess.run(cmd, cwd=STAGE3_DIR, check=True)`（:32）。

**`train_subprocess.py` 相对官方 `go2_train.py` 的三处关键改造**（注释里都写明了）：

1. **`log_dir` 条件清空**（:173-190）：官方脚本无条件 `rmtree(log_dir)`，resume 阶段会把 `model_50.pt` 删掉。这里只在**非 resume** 时清空；resume 时 `os.makedirs(exist_ok=True)` 保留已有 tensorboard 事件。
2. **绝对目标迭代数契约**（:229-236）：`runner.learn(N)` 是**在当前迭代数上加 N**，所以 `delta = args.max_iterations - loaded_iter`，`delta <= 0` 直接抛 `ValueError`。
3. **规范化检查点命名**（:238-248）：rsl-rl 5.0.1 用 **0-based 迭代编号**，`learn(50)` 跑的是 iter 0..49，自动保存的最后一个文件是 `model_49.pt` 而**不是** `model_50.pt`。这里显式 `runner.current_learning_iteration = args.max_iterations` 后再 `runner.save(f"model_{max_iterations}.pt")`，让**文件名和文件内 `iter` 字段都等于绝对目标**，保证第二段 resume 的 `delta = 100 - 50 = 50` 没有 off-by-one。

**读取 checkpoint 里的 iter 要绕开 `runner.load()`**（:222-227）：rsl-rl 5.0.1 的 `OnPolicyRunner.load()` **返回的是 `loaded_dict["infos"]`（通常为 `None`），不是整个 dict**。想知道加载到第几代，必须自己 `torch.load(checkpoint, weights_only=False, map_location=gs.device)` 再取 `["iter"]`。

**`train_cfg["save_interval"] = 50` 被改了两遍**：一次在自带的 `get_train_cfg()` 里（:72，注释 `# CHANGED from 100 to 50`），一次在 `main()` 里再赋值一遍（:172）。`go2_train.py:56` 原值是 `100`。改成 50 是为了保证 `model_50.pt` 和 `model_100.pt` 都落盘。

**`gs.init` 参数**（:196-202）：`backend=gs.gpu, precision="32", logging_level="warning", seed=args.seed, performance_mode=True`。

**`run_orchestrator.py` 的前置检查**（`preflight()` :45-68）：四个源文件存在性、建输出目录、**检查解释器路径里是否含 `autosim`**（:56-59，不含只是 WARNING 不中断）、可选 `nvidia-smi` 查询。每个阶段执行前还会 `assert_file(checkpoint)` 确认依赖的 checkpoint 已生成（:141-142）。`--dry-run`（:73）只打印命令。

**`eval_subprocess.py` 的两个 rsl-rl 陷阱**（:104-108、:112）：
- 推理策略要吃**完整 TensorDict**：注释原文「rsl-rl 5.0.1 MLPModel indexes obs by obs_group name internally (obs["policy"]), so pass the full TensorDict `obs`, NOT obs["policy"]」。
- `env.step()` 返回 4-tuple，注释显式标注「Go2Env.step returns 4-tuple, NOT 5-tuple」。
- 无 checkpoint 时用零动作跑（:88-89），因此**阶段 1「未训练视频」不需要任何模型文件**；`cfgs.pkl` 不存在时回退到 `from go2_train import get_cfgs`（:57-62）——这让 epoch-0 录像可以在训练之前独立运行。

### 3.5 `stage4/*_demo.py` —— 三个多物理场 demo 的共用骨架 `[CODE]`

**路径**：`<repo_root>/stage4/cloth_grasp_demo.py`（416）、`sponge_squeeze_demo.py`（474）、`glass_water_demo.py`（528）

三个文件**结构高度同构**（同样是复制演化而来，不是共用基类）：

```
模块 docstring（含 "== Implementation reality (probed against genesis 1.2.2) ==" 小节）
常量区（几何、PD 增益、阶段目标位姿、判定阈值）
build_scene()            → gs.init → Scene → 实体 → add_camera → scene.build()
npz(x) / render_frame_bgr(cam)      工具
<度量函数>               clearance / cloth_deform / finger_clearance / sponge_stats / cup_tilt_rad / water_stats
class <XxxDemo>          分阶段执行 + 每阶段一个 cv2.VideoWriter + _finalize() 写 JSON + _report() 写 report.md
run_demo() / main()      argparse 入口
```

**三者的物理配置对照** `[CODE]`：

| | 布料 | 海绵 | 水杯 |
|---|---|---|---|
| 材料 | `gs.materials.PBD.Cloth(rho=4.0, stretch_compliance=1e-7, bending_compliance=1e-5, static_friction=0.5, air_resistance=0.001)`（:120-123） | `gs.materials.PBD.Elastic(rho=200.0, stretch/bending_compliance=1e-5, volume_compliance=1e-4, *_relaxation=0.1, static_friction=0.9, kinetic_friction=0.7)`（:132-138） | `gs.materials.SPH.Liquid(rho=1000.0, stiffness=5000.0, exponent=7.0, mu=0.01, gamma=0.0, sampler="regular")`（:147-150） |
| 形态 | `gs.morphs.Mesh(file=cloth.obj)`，脚本可现生成 16×16 网格（`make_cloth_obj` :64） | `gs.morphs.Box(size=(0.10,0.10,0.07), maxvolume=1e-6)`，由 tetgen 内部四面体化 | `gs.morphs.Box(size=(0.07,0.07,0.10))` 采样出粒子 |
| `dt` | `1e-2`（:95/104） | `5e-3`（:99/108） | **`4e-4`**（`SPH_DT` :99） |
| Coupler | `try IPCCouplerOptions() except ImportError → PBDOptions()`（:91-107） | 同左，PBD 分支带求解器迭代数（:109-113） | `LegacyCouplerOptions(rigid_sph=True)`（:121），**无降级分支** |
| 判定阈值 | `DEFORM_RANGE_THRESHOLD=0.03`、`CLOTH_THICKNESS=0.001`（穿透容差） | `DEFORM_THRESHOLD=0.015`、`PENETRATION_TOLERANCE=0.008` | `SPILL_FRACTION_THRESHOLD=0.20`、`KNOCKOVER_TILT_THRESHOLD=1.2` rad、`SANITY_CUP_Z_MAX=0.60`、`SANITY_WATER_Z_MAX=1.50` |

**水杯 demo 独有的三处工程手法**：

- **Jacobian 伪逆代替 IK**（`glass_water_demo.py:277-294`）：`J = franka.get_jacobian(link=ee)` 形状 `(6, 15)`，取前 3 行线性部分的手臂 7 列，`delta_q = np.linalg.pinv(Jlin_arm) @ delta_ee`。原因写在 docstring `:20-26`：`set_dofs_position()` 是无限刚的运动学推动，会**冻结其它刚体**（杯子永远不倒）；`control_dofs_position()` 才有力传递。`set_dofs_position` 只用于一次性把手臂从 qpos0 奇异位形收敛到接近位姿（`_kin_step` :266）。
- **`requires_jac_and_IK=True`** 必须在加载 URDF 时传（:138），否则拿不到 Jacobian。
- **SPH 水面重建渲染**：`surface=gs.surfaces.Plastic(color=..., vis_mode="recon")`（:151），否则水渲染成一堆粒子球。依赖 `pysplashsurf`（**不是 splashsurf / openvdb**，后者只支持 Py3.9）。

**`glass_cup.urdf`**（11 行）：单 link `glass_link`，`mass=3.0`，惯性原点抬到 `z=0.10`（人为做成头重脚轻好推倒）；5 个 box 碰撞体 = 底板 `0.1×0.1×0.01` + 四面 20 cm 高的墙 —— **全凸盒碰撞，SPH 不会漏水**。

---

## 4. 配置系统

> **本仓库没有任何 YAML / JSON / TOML 配置文件** `[CODE]`。全部配置以三种形式存在：**argparse 命令行**、**模块级常量**、**Python 字典**。这既是它的优点（无隐式覆盖、无静默失效）也是缺点（改参数必须改源码）。

### 4.1 三层配置形态

| 形态 | 典型位置 | 怎么改 |
|---|---|---|
| **argparse** | 每个入口的 `main()` | 命令行传参，见 §2.2 |
| **模块级大写常量** | `stage4/*_demo.py` 顶部、`stage3/verify_stage3.py:20-30`、`stage4/verify_stage4.py:36-95` | 直接改源码常量 |
| **配置字典** | `scene_factory.py:42-190`（场景）、`stage3/go2_train.py:19-140`（训练超参） | 直接改字典字面量 |

### 4.2 Stage 2 场景配置 `[CODE] scene_factory.py`

8 个场景字典是**唯一接近「配置文件」的东西**。新增一个场景 = 复制一个 `SCENE_N` 字典 → 改 `name` / `target` / `distractors` / `camera` / `lighting` → 加进 `get_all_scene_configs()`（:194）的返回列表 → 同步把新名字加进 `verify_stage2.py:26-35` 的 `EXPECTED_SCENES` 和 `:89` 的 `len(scenes) != 8` 断言，否则验证门会 FAIL。

`pos_scale` 不写在场景字典里，而是由 `batch_eval_vla.py:547-548` **在运行时注入每个 config**（`cfg["pos_scale"] = args.pos_scale`）。

### 4.3 Stage 3 训练超参 `[CODE] stage3/go2_train.py`

`get_train_cfg(exp_name)`（:19-61）与 `get_cfgs()`（:64-140）是两个返回硬编码字典的函数：

| 组 | 关键项 |
|---|---|
| `algorithm`（:21-36） | `PPO`，`clip_param=0.2`、`desired_kl=0.01`、`entropy_coef=0.01`、`gamma=0.99`、`lam=0.95`、`learning_rate=0.001`、`schedule="adaptive"`、`num_learning_epochs=5`、`num_mini_batches=4` |
| `actor`/`critic`（:37-53） | `MLPModel`，`hidden_dims=[512,256,128]`，`activation="elu"`，`GaussianDistribution(init_std=1.0, std_type="scalar")` |
| 采样（:55-58） | `num_steps_per_env=24`、`save_interval=100`、`logger="tensorboard"` |
| `env_cfg`（:65-105） | `num_actions=12`、PD `kp=20.0 / kd=0.5`、`action_scale=0.25`、`clip_actions=100.0`、`episode_length_s=20.0`、`resampling_time_s=4.0`、`base_init_pos=[0,0,0.42]`、翻倒终止阈值 roll/pitch **10°** |
| `obs_cfg`（:106-113） | `obs_scales`：`lin_vel=2.0`、`ang_vel=0.25`、`dof_pos=1.0`、`dof_vel=0.05` |
| `reward_cfg`（:114-130） | `tracking_sigma=0.25`、`base_height_target=0.3`；权重 `tracking_lin_vel=1.0`、`tracking_ang_vel=0.2`、`lin_vel_z=-1.0`、**`base_height=-50.0`**、`action_rate=-0.005`、`similar_to_default=-0.1` |
| `command_cfg`（:131-137） | `lin_vel_x_range=[0.5,0.5]`、`lin_vel_y_range=[0,0]`、`ang_vel_range=[0,0]` —— **三个区间都退化成常量**，即只训练「以 0.5 m/s 直行」这一个命令 |

> ⚠️ `train_subprocess.py` **自带一份 `get_train_cfg`/`get_cfgs` 的副本**（:35 / :79），并不 import `go2_train`。**改超参要改 `train_subprocess.py` 里的那一份**，改 `go2_train.py` 对编排流程无效。（`eval_subprocess.py:57-62` 在 `cfgs.pkl` 缺失时才 fallback 到 `go2_train`。）

配置会在训练开始时被 pickle 到 `logs/<exp_name>/cfgs.pkl`（`train_subprocess.py:194-196`），评测子进程优先读它（`eval_subprocess.py:52-56`），以此保证训练/评测配置一致。

### 4.4 Stage 4 阈值常量 `[CODE]`

每个 demo 顶部的常量区就是它的「配置」，且**同一批数值在 `verify_stage4.py:60-95` 的 `DEMOS` 字典里又写了一遍**（`deform_threshold=0.03/0.015`、`spill_threshold=0.20`、`tilt_threshold_deg=70.0`）。**改 demo 的阈值必须同步改验证门的阈值**，否则会出现「demo 自认为通过、verify 判 FAIL」的不一致。

`verify_stage4.py` 的取值顺序是 `summary.get(key) or report.get(key)`（`:216-217`），即优先读 `<output_dir>/*.json` 的 `summary` 段，`report.md` 只作兜底与存在性门。

---

## 5. 依赖与环境

> **仓库内没有 `requirements.txt` / `setup.py` / `pyproject.toml` / `environment.yml`** `[CODE]`。以下依赖从 `import` 语句与仓库 `CLAUDE.md` 的环境表汇总。

### 5.1 运行环境 `[README]`（来自仓库自带 `CLAUDE.md` 环境表）

| 项 | 值 | 备注 |
|---|---|---|
| GPU | NVIDIA A800-SXM4-40GB | 单卡 |
| CUDA / 驱动 | CUDA 11.8 / 驱动 580.159.03 | **不要改动驱动** |
| conda 环境 | `<conda_env>`（名为 `autosim`） | 路径已替换敏感信息 |
| Python | 3.12.13 | |
| 显示 | 无显示器云服务器，**全程 headless** | 所有脚本 `show_viewer=False` |

### 5.2 关键库与版本锁定

| 库 | 版本 | 锁定理由 |
|---|---|---|
| **genesis-world** | **1.2.2** | 本仓库全部 API 写法基于此版本；原理层描述的是 1.3.3，**不可混用** |
| PyTorch | 2.10.0+cu128 | |
| **rsl-rl-lib** | **5.0.1** | `train_subprocess.py:23-27` 有**硬性版本门**：主版本号 `< 5` 直接 `raise ImportError("Please install 'rsl-rl-lib>=5.0.0'.")` `[CODE]` |
| **numpy** | **1.26.4** | 与 Genesis 的 C 扩展绑定 |
| transformers | — | `AutoModelForVision2Seq` + `trust_remote_code=True` |
| tensordict | — | `go2_env.py:4`，观测容器 |
| opencv-python | — | 全部录像与像素统计 |
| **pysplashsurf** | — | 仅 Stage 4 水面重建渲染需要。**不是 `splashsurf`，也不是 `openvdb`**（后者只支持 Py3.9） |
| flash-attn | 可选 | 缺失时自动退 `eager` 注意力（`batch_eval_vla.py:524-530`） |
| tetgen | 随 Genesis | `PBD.Elastic` + `gs.morphs.Box` 的内部四面体化 |
| ffmpeg / ffprobe | 系统级 | 三个 `verify_*.py` 都靠 `ffprobe` 读视频元数据 |

### 5.3 明确**没有**安装的东西 `[CODE]`

- **IPC / pyuipc 未安装**。三个 Stage 4 demo 的 docstring 都写了 `Hard constraints honored: no new env/packages (NO pyuipc)`，布料与海绵 demo 用 `try IPCCouplerOptions() except ImportError` 自动降级到 PBD（`cloth_grasp_demo.py:91-107`）。因此**本仓库的一切软体结果都是 PBD 路径的结果**。
- 模型 **OpenVLA-mcx-card** 是本地目录（bfloat16，约 15 GB），全部加载都带 `local_files_only=True`，**运行时不联网**。

---

## 6. 复现过程中的修改点

**本仓库不是上游 fork。** 它是一个**独立编写的复现/探针仓库**，只有 Stage 3 明确派生自上游示例 `examples/locomotion/go2_env.py` 与 `go2_train.py`。因此「修改点」分两类讨论。

### 6.1 Stage 3：派生自上游示例，改动极小 `[CODE]`

把 `<repo_root>/stage3/go2_env.py` 与上游 `examples/locomotion/go2_env.py`（1.3.3, HEAD `19f56d6`）逐行 diff，**全文只有 20 行差异**，其中真正的功能改动只有一处：

| 改动 | 位置 | 性质 |
|---|---|---|
| `__init__` 新增 `camera_cfg=None` 形参 + `self.cam = None` | `go2_env.py:16,22` | ✅ **本次改动**。用于在 `scene.build()` 之前注入录像相机 |
| build 前的 `if camera_cfg is not None: self.cam = self.scene.add_camera(**camera_cfg)` | `go2_env.py:76-79` | ✅ **本次改动**（配套上一条） |
| `RigidOptions` 里 `tolerance=1e-5` 与 `max_collision_pairs=20` 的先后顺序、`vis_options` 的书写位置、若干注释行（`# create scene` / `# add robot` / `# resample commands` / 奖励函数分隔注释） | 分散 | 🔶 `[推断]` 上游 1.2.2→1.3.3 之间的排版演化，**不计为本次改动** |

`go2_train.py` 与上游只有 **13 行**差异，且全部是 argparse 的命名风格（本仓库 `--exp_name` / `-B` / `--num_envs` / `--max_iterations`，上游 1.3.3 是 `--exp-name` / `-b` / `--num-envs` / `--max-iterations`）与一行注释。🔶 `[推断]` 这是 1.2.2 时期的原样，**不计为本次改动**。

> 结论：**`go2_env.py` / `go2_train.py` 基本未改动**。所有工程增量都落在**新写的四个文件**上：`train_subprocess.py`、`eval_subprocess.py`、`run_orchestrator.py`、`verify_stage3.py`。

### 6.2 Stage 3：新写文件里对官方流程的四处实质性绕行 `[CODE]`

这四条是「用上游示例跑不通、必须自己补」的部分，也是最值得复用的经验：

1. **resume 不能清空 `log_dir`**（`train_subprocess.py:174-176` 注释原文：`Official go2_train.py unconditionally rmtree(log_dir), which would delete model_50.pt during the resume phase. Only wipe when NOT resuming.`）
2. **`--max_iterations` 改成绝对目标语义**（:7-9, :229-236），避免两段式训练的增量/绝对混淆。
3. **手工补一个规范命名的 checkpoint**（:238-248），绕开 rsl-rl 5.0.1 的 0-based 编号。
4. **checkpoint 的 `iter` 自己 `torch.load` 读**（:222-227），因为 `OnPolicyRunner.load()` 的返回值不是 dict。

### 6.3 Stage 1 / 2 / 4：原创代码，「修改点」体现为对 1.2.2 API 的适配 `[CODE]`

这三部分没有上游对应物可比，其「修改」全部是**为绕开 genesis-world 1.2.2 的行为而写进代码的适配层**：

| 适配 | 代码证据 |
|---|---|
| `gs.morphs.Franka` 不存在 → 从 `gs.__file__` 拼 `assets/urdf/panda_bullet/panda.urdf` | 全仓库 **7 处**：`scene_factory.py:270`、`vla_closed_loop_demo.py:283`、`batch_eval_vla.py`（经 scene_factory）、`classical_demo.py:96`、`hybrid_vla_demo.py:159`、`stage4/cloth_grasp_demo.py:112`、`sponge_squeeze_demo.py:121`、`glass_water_demo.py:136` |
| `render()` 返回 4-tuple → 到处 `if isinstance(x, tuple): x = x[0]` | 全仓库 **10 处**：`vla_closed_loop_demo.py:368,378`、`batch_eval_vla.py:220,230`、`classical_demo.py:157`、`hybrid_vla_demo.py:223`、`stage3/eval_subprocess.py:123`、`stage4/cloth_grasp_demo.py:142`、`sponge_squeeze_demo.py:161`、`glass_water_demo.py:171` |
| IK 返回完整 `qpos(16,)` → 一律 `[motors_dof]` 切片 | `batch_eval_vla.py:287,309` |
| `add_camera` 是 `@assert_unbuilt` → 相机全部前置到 `build()` 之前 | `scene_factory.py:298-319`、`go2_env.py:76-80`、三个 Stage 4 demo |
| IPC 不可用 → `try/except ImportError` 降级 PBD | `stage4/cloth_grasp_demo.py:93,101`、`sponge_squeeze_demo.py:97,105`（水杯 demo 无降级分支） |
| `set_dofs_position` 冻结其它刚体 → 改用 Jacobian 伪逆 + `control_dofs_position` | `glass_water_demo.py:20-26,277-294` |
| SPH 在 `dt=2e-3` 爆炸 → 全局 `dt=4e-4` + `STEPS_PER_FRAME=28` | `glass_water_demo.py:99-100` |
| 后台 bash 不继承 conda → 包装脚本 | `stage3/run_in_env.sh` |

---

## 7. 代码中的注意事项

### 7.1 硬编码主机绝对路径清单（**已替换敏感信息**）`[CODE]`

`grep -rn '/mnt/\|/home/'` 命中 **12 个文件、49 行**。下表按「换机部署必须改」的优先级排列，路径一律以占位符表示（`<path>` = 数据盘挂载点、`<user_home>` = 用户家目录、`<docs>` = 外部文档目录、`<repo_root>` = 本仓库根）。

| 优先级 | 位置 | 内容 | 影响 |
|---|---|---|---|
| 🔴 必改 | `vla_closed_loop_demo.py:13,14`、`batch_eval_vla.py:16,17`、`classical_demo.py:10`、`hybrid_vla_demo.py:15` | `os.environ["HF_HOME"/"TRANSFORMERS_CACHE"] = "<path>/.cache/huggingface"` | **硬赋值，覆盖外部环境**；路径不存在会导致模型加载走错缓存 |
| 🔴 必改 | `vla_closed_loop_demo.py:69`、`batch_eval_vla.py:515` | 模型目录 `<path>/models/openvla-mcx-card` | 模型加载直接失败 |
| 🔴 必改 | `stage3/run_in_env.sh:5-9`、`stage3/gradient_test.sh:5-9` | `source <user_home>/miniconda3/...`、`conda activate <path>/conda/envs/autosim`、`source <path>/genesis_vla_env.sh`、`TMPDIR`、`cd <repo_root>/stage3` | 后台任务包装器整体失效 |
| 🟠 应改 | `README.md:95` | `source <path>/genesis_vla_env.sh` | 文档误导 |
| 🟡 可留 | `stage4/cloth_grasp_demo.py:38,39`、`sponge_squeeze_demo.py:48,49`、`glass_water_demo.py:53,54` | `os.environ.setdefault("GSPATH"/"GS_HOME", "<path>/.cache/genesis")` | 用 `setdefault`，**外部已设则不覆盖**，可先在 shell 里导出同名变量绕开 |
| 🟡 可留 | `stage3/gradient_test.sh:11,21,28,31` | 梯度测试的日志落盘路径 `<path>/tmp/...` | 只影响该辅助脚本 |
| 🟢 无害 | `stage3/run_orchestrator.py:59` | WARNING 文案里提到 conda 路径 | 仅提示，不中断 |
| 🟢 无害 | `batch_eval_vla.py:457` | 写进 `run_log.json` 的 `"model"` 字段 | **会把主机路径写进产物 JSON**，分享产物前需清理 |
| 🟢 无害 | `stage4/*_demo.py` docstring、`CLAUDE.md:27-41,383-390` | 计划文档 `<docs>/*.md` 与环境表 | 引用的外部文档**不在仓库内**，克隆后读不到 |

> ⚠️ 仓库自带的 `CLAUDE.md` 引用了 **7 份外部计划文档**（`Stage1_Plan_Detailed.md`、`Complete_Stage_1.md`、`Stage2_Plan.md`、`Stage2_Plan_Detailed.md`、`Genesis_World_Interface.md`、`Stage4_Plan.md`、`Stage4_Plan_Detailed.md`），它们位于仓库之外的目录，**克隆仓库拿不到**。这些内容的可用替代是本知识库的 [`ai_knowledge.md`](./ai_knowledge.md) 与 [`troubleshooting.md`](./troubleshooting.md)。

### 7.2 静默失效与易踩的坑 `[CODE]`

| # | 陷阱 | 位置 | 表现 |
|---|---|---|---|
| 1 | **`verify_stage2.py` 与 `batch_eval_vla.py` 的默认输出目录不一致**（`stage2_eval_8scene` vs `stage2_eval`） | `verify_stage2.py:72` / `batch_eval_vla.py:503` | 直接跑 verify 会报「全部缺失」，其实只是目录名不对 |
| 2 | **`GripperController` 的默认参数与实际调用值不同** | 定义 `batch_eval_vla.py:67`，调用 `:198-201` | 改默认值不生效 |
| 3 | **`HOLD=2` 常量名与它在状态流程中的位置（最后一步）不符** | `batch_eval_vla.py:62-65,97,106` | 读代码时会把执行顺序读反 |
| 4 | **`train_subprocess.py` 自带一份超参副本，不 import `go2_train`** | `train_subprocess.py:35,79` | 改 `go2_train.py` 的超参对编排流程无效 |
| 5 | **`--max_iterations` 是绝对目标不是增量** | `train_subprocess.py:229-236` | 传成增量会训练过头 |
| 6 | **rsl-rl 5.0.1 的 checkpoint 是 0-based**，`learn(50)` 自动存的是 `model_49.pt` | `train_subprocess.py:238-243` 注释 | 直接找 `model_50.pt` 会找不到 |
| 7 | **`OnPolicyRunner.load()` 返回 `infos`（常为 `None`）而非 dict** | `train_subprocess.py:222-224` 注释 | 用返回值取 `iter` 会拿到 `None` |
| 8 | **推理时必须传完整 TensorDict**（`policy(obs)` 而非 `policy(obs["policy"])`） | `eval_subprocess.py:104-108` 注释 | 传子张量会报形状/键错误 |
| 9 | **`Go2Env.step()` 返回 4-tuple 而非 gym 的 5-tuple** | `eval_subprocess.py:112` 注释 | 按 gym 解包会 ValueError |
| 10 | **相机必须在 `scene.build()` 之前添加**（`add_camera` 带 `@assert_unbuilt`），而 `Go2Env.__init__` 内部就 build 了 | `go2_env.py:76-80` | 构造后再加相机必抛异常，只能走 `camera_cfg=` 参数 |
| 11 | **Stage 4 阈值在 demo 与 verify 里各写一遍** | `stage4/*_demo.py` 常量区 vs `verify_stage4.py:60-95` | 只改一边 → demo 自认为通过、verify 判 FAIL |
| 12 | **`set_dofs_position()` 会冻结其它刚体** | `glass_water_demo.py:20-26` docstring | 水杯永远推不倒；必须用 `control_dofs_position()` 才有力传递 |
| 13 | **SPH 在 `dt=2e-3` 会爆炸**，稳定上限 `4e-4` | `glass_water_demo.py:21,99` | 只报 warning 不报错，水直接飞散 |
| 14 | **ffprobe 把 `mp4v` 报成 `mpeg4`** | `verify_stage4.py:36` `CODEC_WHITELIST = ("h264","mp4v","mpeg4")` | 只白名单 `mp4v` 会误判 |
| 15 | **`nb_frames` 在部分 FFmpeg 构建下是 `"N/A"`** | `verify_stage2.py:53-57` 的 `_int()` 兜底 | 不兜底会 ValueError |
| 16 | **后台 bash 任务不继承 conda/profile** | `stage3/run_in_env.sh` | 直接后台 `python xxx.py` 会用错解释器 |

### 7.3 平台与运行假设 `[CODE]`

- **单 GPU、headless**：所有 `gs.init(backend=gs.gpu)`，所有 `show_viewer=False`，没有任何多卡/分布式代码路径。
- **必须 `cd` 到脚本所在目录**：靠同目录相对 import（`from scene_factory import ...`、`from go2_env import Go2Env`），且 `run_orchestrator.py` 用 `cwd=STAGE3_DIR`（:32）执行子进程；`verify_stage3.py:20-21` 的 `LOG_DIR`/`VIS_DIR` 是相对路径。
- **依赖系统 `ffprobe`**：三个 verify 脚本都调它；缺失时 `verify_stage3.py:39-41` 返回失败，`verify_stage2.py:60-61` 吞异常返回 `None` 再判 FAIL。
- **Stage 4 的 `os.environ.setdefault("GSPATH"/"GS_HOME")` 必须在 `import genesis` 之前**，代码里用 `# noqa: E402` 显式压制了 import 顺序告警（`cloth_grasp_demo.py:41-44`）。

### 7.4 注释与代码风格观察 `[CODE]`

- **全仓库没有一处 `TODO` / `FIXME` / `HACK` / `XXX` / `WORKAROUND`**（grep 零命中）。所有「临时方案」都写成了正式注释并解释了原因——这一点很反常，也是它可读性高的原因。
- 反过来，**含 `CRITICAL` 或显式反例（`NOT ...`）的注释有 21 处**，密集分布在 API 陷阱处。读这些脚本时**注释优先级高于代码**：它们记录的是「为什么不能写成另一种更自然的写法」。
- **Stage 4 三个 demo 的 docstring 都有一节 `== Implementation reality (probed against genesis 1.2.2) ==`**，逐条列出探测出的引擎行为与被迫的设计选择。这是全仓库信息密度最高的三段文字，改 Stage 4 之前必读。
- **代码重复是显式选择而非疏漏**：`ActionDenormalizer`/`GripperController` 在 Stage 1 与 Stage 2 各一份；`get_train_cfg`/`get_cfgs` 在 `go2_train.py` 与 `train_subprocess.py` 各一份；三个 Stage 4 demo 是同构复制。**改动时必须先确认要改的是哪一份**。

---

## 8. 与本项目其它知识层的关联

### 8.1 代码 ↔ 原理层 `background_knowledge.md`（1.3.3）

用 `Read` 的 `offset`/`limit` 精读对应行段，**不要整篇读**。

| 本文档章节 | 原理层章节（起始行） | 关系 |
|---|---|---|
| §3.1 场景工厂、§3.5 多物理场 demo | §2 核心原理（L89）、§3 架构与模块（L393） | 代码是原理的最小可运行实例；求解器/耦合器的分层关系看原理层 |
| §3.5 三种材料参数对照 | §4 关键特性（L551） | PBD / FEM / SPH 各自的适用面与代价 |
| §5 依赖与环境 | §5 安装与依赖（L659） | 原理层是 1.3.3 的官方安装口径；本层是 1.2.2 的实机口径 |
| §2 入口点与运行方式 | §6 基本使用流程（L734） | 原理层给「标准写法」，本层给「本仓库实际怎么跑」 |
| §3.2 IK/渲染/控制调用、§6.3 API 适配表 | §7 常用 API 接口（L908） | ⚠️ **签名以版本为准**：原理层 1.3.3，本层 1.2.2 |
| §7.2 静默失效表 | §8 已知问题与限制（L1052） | 原理层列「代码里能查到的限制」，本层列「本仓库怎么绕过去的」 |

### 8.2 代码 ↔ 经验层教训 `L01`–`L08`（物证）

经验层的每条教训在本仓库都有可指认的代码物证：

| 教训 | 代码物证 |
|---|---|
| `L01` 长时运行前先 smoke test | `stage3/gradient_test.sh`（256/512/1024/2048 envs × 2 iters 的 OOM 梯度探测）、`run_orchestrator.py --dry-run`（:73） |
| `L02` 修复前先量化问题是否真的发生 | 每步都记录 `raw_action` / `delta_pos` / `finger_dist` 进 `trajectory.json`（`batch_eval_vla.py:328-339`）——正是这份逐步数值让「输出与目标无关」成为可证伪的事实 |
| `L03` 把主观判断转成机器断言 | 三个 `verify_*.py` 的全部内容；尤其 `verify_stage2.py:64-66` 的蓝色掩膜像素统计与 `:169-175` 的「宽相机块占比应小于 VLA 相机」几何自洽检查 |
| `L04` 降低目标前先证明不可达 | `batch_eval_vla.py:209,356-365` 保留 `success_type`（`gripper_touch` / `z_lift` / `none`）**双判定口径并存且分别记录**，使口径变化在产物里可追溯 |
| `L05` 落笔前 grep 到定义处 | §6.3 全表；`gs.morphs.Franka` 不存在 → 一律走 URDF；末端 link 用 `panda_link7` 而非 `hand` |
| `L06` 装依赖前评估传递依赖 | 三个 Stage 4 demo 的 docstring 都写死 `Hard constraints honored: no new env/packages (NO pyuipc)` |
| `L07` 换组件常常只是换根因名字 | `classical_demo.py` / `hybrid_vla_demo.py` 两个对照组的存在本身——它们用来定位「问题在模型还是在仿真器」，而不是再换一个模型 |
| `L08` 能力边界读源码确认 | `sponge_squeeze_demo.py:17-19` docstring 直接引用上游 `fem_solver.py` L975 的分支条件作为「FEM 无 IPC 不做刚-柔接触」的依据 |

### 8.3 代码 ↔ 排障层 `Qxx`（机制解释）

排障层给「怎么绕过去」，本层给「代码里为什么这么写」：

| `Qxx` | 现象 | 代码层机制 |
|---|---|---|
| `Q02` | `morphs has no attribute 'Franka'` | §6.3；全仓库 7 处都改成从 `gs.__file__` 拼 `panda_bullet/panda.urdf` |
| `Q03` | `Unrecognized attribute 'surface'` | `scene_factory.py:212-216` docstring 与 `cloth_grasp_demo.py:124` 注释：`surface` 属于 `add_entity()` 而非 morph |
| `Q04` | `Link not found for name: hand` | `scene_factory.py` 末端取 `panda_link7`、手指取 `panda_leftfinger`/`panda_rightfinger` |
| `Q05` | `Invalid input shape: (14,)` | §3.2 第 7 步：IK 返回完整 `qpos(16,)`，必须 `[motors_dof]` 切片 |
| `Q15` | 第二次 `gs.init()` segfault、找不到 `scene.destroy()` | `batch_eval_vla.py:559,575-576`：**全批只 init 一次**，场景靠 GC 回收；Stage 3 则改用**进程隔离**（§3.4） |
| `Q17` | `Scene is already built.` | §3.3：`add_camera` 带 `@assert_unbuilt`，`Go2Env` 只能靠 `camera_cfg=` 前置注入 |
| `Q18` | `render()` 返回值当数组用报错 | §6.3；全仓库 10 处 `isinstance(x, tuple)` 兜底 |
| `Q19` | `model_50.pt` 不存在，只有 `model_49.pt` | §3.4 第 3 条：0-based 编号 + 手工规范化保存（`train_subprocess.py:238-248`） |
| `Q20` | `OnPolicyRunner.load()` 返回 `None` | `train_subprocess.py:222-227`：自己 `torch.load` 读 `["iter"]` |
| `Q21` | `policy(obs["policy"])` 形状报错 | `eval_subprocess.py:104-108`：必须传完整 TensorDict |
| `Q22` | resume 时旧 checkpoint 被删 | `train_subprocess.py:174-191`：`log_dir` 条件清空 |
| `Q23` | 后台 bash 任务秒退无输出 | `stage3/run_in_env.sh` |
| `Q24` | 正常 MP4 被判 FAIL（编码名对不上） | `verify_stage4.py:36` 白名单同时收 `mp4v` 与 `mpeg4` |
| `Q25` | 像素验证误报「目标不可见」 | `verify_stage2.py:143-145` 注释：**只用 step-0 关键帧**做对比，因为中途发散的手臂会遮挡目标 |
| `Q28` | `PBD2DEntity` 没有 `geom_start` | Stage 4 全程不用 `get_contacts()`，改用 `torch.cdist(finger_verts, particles)` 算穿透（`cloth_grasp_demo.py:149-154`） |
| `Q32` | 夹爪闭合后物体不动 / 被压穿桌面 | `glass_water_demo.py:20-26`：`set_dofs_position` 冻结其它刚体，必须 `control_dofs_position` |
| `Q33` | FEM 柔性体被手指穿过 | §5.3 + `sponge_squeeze_demo.py:17-21`：无 IPC 时 FEM 不做刚-柔接触，只能走 `PBD.Elastic` |
| `Q34` | SPH 流体炸开 | `glass_water_demo.py:21,99`：`dt` 必须 ≤ `4e-4`；`mu` 越大越不稳 |

### 8.4 被本层修正或补充的结论

| 结论 | 出处 | 本层的修正 |
|---|---|---|
| 「相机必须在 build 前添加」 | `troubleshooting.md` `Q17` | ✅ 一致，且本层补充了**为什么 `Go2Env` 必须走 `camera_cfg=` 参数**：它在 `__init__` 内部就 build 了，外部没有插入时机（`go2_env.py:76-80`） |
| 「Stage 3 是照搬官方示例」 | 经验层的印象性描述 | 🔶 **本层量化**：`go2_env.py` 与上游只差 **20 行**、`go2_train.py` 只差 **13 行**，真正的工程增量在**新写的 4 个文件**里（§6.1、§6.2） |
| 「`--max_iterations` 语义」 | 经验层 `P22` 相关 | ✅ 本层给出确切契约位置：`train_subprocess.py:7-9`（docstring）与 `:229-236`（实现） |
| 原理层 §8 的部分限制 | `background_knowledge.md` §8（L1052） | ⚠️ **版本差**：原理层描述 1.3.3。本仓库跑 1.2.2，**API 具体写法不可互换**；但 IPC 需额外安装、FEM 无 IPC 不做刚-柔接触、相机无噪声模型这三条能力边界，两个版本一致 |
| 「本仓库有完整环境声明」 | —— | ❌ **纠正**：仓库内**没有** `requirements.txt` / `setup.py` / `environment.yml`（§5）。版本信息只存在于仓库自带 `CLAUDE.md` 的环境表与 `train_subprocess.py:23-27` 的 rsl-rl 版本门里 |

### 8.5 阅读顺序建议

1. 只想跑起来 → [`quickstart.md`](./quickstart.md)
2. 带着报错 → [`troubleshooting.md`](./troubleshooting.md) 顶部「快速症状索引」
3. 要改代码 → **本文档** §2（怎么跑）→ §7（哪些地方会静默失效）→ §3（改哪个模块）
4. 想知道为什么这么设计 / 试过哪些无效方法 → [`ai_knowledge.md`](./ai_knowledge.md) §3 决策表 + §4 问题表
5. 查 API 与能力边界 → [`background_knowledge.md`](./background_knowledge.md)（**先在 [`00-index.md`](./00-index.md) 拿行号**）
