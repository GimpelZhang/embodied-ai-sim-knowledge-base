# 跨工具链术语对照表

> **用途**：读某个项目文档时撞到不认识的术语，或**同一个词在两个工具链里含义不同**时查这里。
> **来源**：4 个项目 `background_knowledge.md` 与 `code_knowledge.md`，逐条可回溯到项目文档章节。
> **不做什么**：本文**不解释通用学术概念**（什么是 PPO、什么是扩散模型），只解释**这四个工具链里的具体所指**与**它们之间的差异**。

**项目缩写**（本文全篇使用）：

| 缩写 | 项目 | 范式 |
|---|---|---|
| **GW** | [`genesis_world`](../projects/genesis_world/background_knowledge.md) | 物理仿真平台 |
| **GS3** | [`genie_sim_v3`](../projects/genie_sim_v3/background_knowledge.md) | 工具链 + 评测体系（Isaac Sim 底座） |
| **LW** | [`lw_benchhub`](../projects/lw_benchhub/background_knowledge.md) | 评测框架（Isaac Lab / Arena 薄组合层） |
| **GE2** | [`ge_sim_v2`](../projects/ge_sim_v2/background_knowledge.md) | ⚠️ 视频生成世界模型（**无物理、无渲染**） |

---

## 0. 最容易混的九组概念

> 每一组都是"两个词长得像 / 名字一样，但不是一回事"。这一节是本文的核心。

| # | 容易混的一对 | 区别 | 混淆代价 |
|---|---|---|---|
| **1** | **物理步长**用「秒」还是「Hz」表示 | **GW `dt`（秒，默认 `1e-2`）** ↔ **GS3 `physics_hz`（Hz，默认 `100.0`）** ↔ **LW `sim.dt`（秒）**。三者是**同一个量的倒数关系** | 抄参数时把 `100` 当成秒或把 `0.01` 当成 Hz，量级差 10⁴ |
| **2** | **`substeps`（求解器子步）** vs **`decimation`（控制降采样）** | **不是同一个轴。** `substeps`(GW) / `substep`(GS3) 是**一个物理步内部**的求解细分，为数值稳定；`decimation`(LW) 是**一个环境步里跑几个物理步**，决定**控制频率** | 想提高稳定性却改了控制率，或反之 |
| **3** | **`set_dofs_position`** vs **`control_dofs_position`**（GW） | 前者**硬置位、瞬移、绕过动力学**（只用于初始化 / hard reset）；后者是**位置指令**，交给内部 PD 控制器走完整动力学 | GW 原文明说这两条"**最容易混**"；用错的表现是机器人不受力地穿模 |
| **4** | **`solver`（求解器）** vs **`coupler`（耦合器）**（GW） | `solver` 是**建模方法**（8 个，Rigid/FEM/MPM/SPH/PBD/SF/Kinematic/Tool）；`coupler` 是**把不同求解器的物体耦合到同一批量环境**的模块（3 个，Legacy/SAP/IPC） | 换 coupler ≠ 换 solver；且**换 coupler 不是行为中性的** |
| **5** | **物理 `material`** vs **外观 `surface`/`texture`**（GW） | `material` 决定实体**路由到哪个 solver**（`gs.materials.PBD.Cloth()`）；`surface`/`texture` 只管外观 | 传错对象是 GW 复现里实际发生过的错误 |
| **6** | **`n_envs=0`** vs **`n_envs=1`**（GW） | **语义不同**：`0` 的状态张量**无 batch 维**，`1` 有长度为 1 的 batch 维 | 索引全错，且报错信息不指向根因 |
| **7** | **渲染频率**有几个旋钮（LW） | LW **有两个且互不相等**：`render_interval`（每几个物理子步渲染一次，任务基类 4 ⇒ **25 Hz**）与 `update_period`（相机采样周期，LW 侧全 **0.05 s = 20 Hz**、Arena 侧全 `0.0` = 每 step）。而控制是 **50 Hz** | "图像看起来滞后"**是正常现象不是 bug**（LW 原文） |
| **8** | **两套 16 维关节布局**（GE2） | 世界模型侧 `[L7臂, L夹爪, R7臂, R夹爪]`；策略侧 `[L7臂, R7臂, L夹爪, R夹爪]` —— **两个夹爪维的位置不同** | ⚠️ **用错不报错，只是行为错**。必须走 `wm_state_to_policy_state()` |
| **9** | **「帧数」vs「覆盖跨度」**（GE2） | 实际生成 **25 帧**；配 4× 跳帧后**覆盖**约 100 帧的时间跨度 | 论文把前者写成 "100-frame rollout"，导致外界高估吞吐 4× |

---

## 1. 时间、频率与步进 ★ 最高频的混淆源

| 术语 | 定义 / 解释 | 出现的项目 | 备注（跨工具链差异） |
|---|---|---|---|
| **物理步长** | 每推进一次物理所对应的仿真时长 | 全部（GE2 除外） | **表示方式不统一**：GW 用周期 `dt`（秒），GS3 用频率 `physics_hz`（Hz），LW 用周期 `sim.dt`（秒）。互为倒数，抄参数时务必换算 |
| `dt` | GW：每个 `scene.step()` 推进的物理时长（秒） | GW | `SimOptions.dt` 默认 **`1e-2`**；⚠️ **solver options 里同名给值会覆盖 `SimOptions`** |
| `physics_hz` | GS3：物理步进频率（Hz） | GS3 | 默认 **`100.0`** |
| `sim.dt` | LW：物理步长（秒） | LW | **同一仓库内三个值**：任务基类 `1/100`、RL 基类 `0.01`、G1 覆盖为 `1/200`。⚠️ `g1.py` 有一处**注释写 100 Hz 而代码是 200 Hz** |
| `substeps` | GW：一个 `scene.step()` **内部**的求解子步数 | GW | 默认 **`1`**；耗时最坏线性、实践次线性 |
| `substep` / `sim_dt` | GS3：求解器内部子步（外层 tick 内细分） | GS3 | 例：10 substep / 10 ms 外层 ⇒ `dt_solver = 1 ms`。**提子步而非提 `physics_hz`** 是官方给的稳定性调法 |
| `substeps_local` | GW：GPU 显存里保留的子步数 | GW | 非可微模式**强制为 1** 省显存；**仅可微模式有意义**，显存随它**线性增长** |
| `decimation` | LW：**一个环境步内跑几个物理子步** | LW | ⚠️ **与 `substeps` 不是同一个轴**（见 §0 第 2 组）。任务基类 **2** / RL 基类 **5** / Arena 基类 **8** |
| **控制频率 / 控制率** | 策略下发一次动作的频率 | 全部 | **四种完全不同的确定方式**：GW **无独立参数**，= `1/dt`（每 `step` 下一次指令）；GS3 proprioception **100 Hz 且滞后一拍**；LW **`1/(sim.dt × decimation)`** ⇒ **RL 20 Hz、遥操作/回放 50 Hz、Arena 基类 15 Hz**（LW 原文：**本项目最常见的对不齐来源**）；GE2 参照系是 **fps 16** |
| **渲染帧率** | 每秒出图数 | 全部 | **四种口径**：GW **没有全局参数** —— 由你调 `cam.render()` 的次数决定；GS3 `render_hz` / `render_target_hz`；LW **两个旋钮**（`render_interval` + `update_period`，见 §0 第 7 组）；GE2 固定 25 帧/chunk |
| `render_hz` / `render_target_hz` | GS3：渲染频率 | GS3 | ⚠️ **`render_hz=0.0` 是"未提供"哨兵**，回落到 `render_target_hz=30.0`。不是"关闭渲染" |
| `render_interval` | LW：每几个**物理子步**渲染一次 | LW | 任务基类 **4** ⇒ 25 Hz。⚠️ 渲染**只在有 GUI 或有 RTX 传感器时**才真的发生 |
| `update_period` | LW：相机**采样**周期（秒） | LW | LW 侧全部 **0.05（20 Hz）**，Arena 侧全部 **0.0（每 step 刷新）**。⇒ LW 侧图像与 50 Hz 控制**解耦** |
| `skipped(budget)` vs `skipped(period)` | GS3：丢渲染帧的两种原因 | GS3 | 前者 = **预算不足主动丢帧**，后者 = 还没到渲染时刻。⇒ **渲染帧率不保证、相机时间戳非均匀** |
| `episode_length_s` | 一个 episode 的时长上限（秒） | LW | 唯一生效的 YAML 键在 `configs/envhub/example.yml`（20.0）；其余**硬编码**：任务 8.0 / RL 3.2 / 遥操作禁用 ⇒ **episode 时长基本改不动** |
| `fps` / `× 实时` | 吞吐口径 | GE2 | 实测 **0.88 帧/s ≈ 0.055× 实时**（参照系 fps 16）；论文 25 帧 / 2.3 s ≈ **10.9 帧/s** —— **差一个数量级，引用时必须说清是哪一个** |
| **跳帧（frame skip / random-stride）** | GE2：训练时随机时间步长采样，使推理时可跳帧 | GE2 | **最多 4×**：用同样帧数覆盖至多 4 倍时间跨度 |
| **覆盖跨度 vs 帧数** | GE2：生成 25 帧 ↔ 覆盖约 100 帧跨度 | GE2 | ⚠️ 见 §0 第 9 组。正确写法：「2.3 s 生成 25 帧，配 4× 跳帧可覆盖约 100 帧跨度」 |
| **蒸馏步数** | GE2：DMD2 蒸馏后的推理去噪步数 | GE2 | 目标 **4 步**（训练时在 1–4 随机化）；YAML 写死 `num_inference_steps: 4` |

---

## 2. 关节、动作与控制模式 ★ 第二高频混淆源

| 术语 | 定义 / 解释 | 出现的项目 | 备注（跨工具链差异） |
|---|---|---|---|
| **DOF / `dofs_idx_local`** | 自由度的**局部**索引，按关节名取 | GW | 取法 `entity.get_joint(name).dofs_idx_local[0]` |
| `qpos` | 关节位形向量 | GW | ⚠️ **v1.2.2 实测：IK 类接口返回的是完整 qpos**（Franka 为 `(16,)`）**而非手臂 7 维** —— GW 复现里最高频的 API 误用之一 |
| **`set_dofs_position`** | **硬置位**：瞬移到该位形，**绕过动力学** | GW | 只用于初始化 / hard reset。见 §0 第 3 组 |
| **`control_dofs_position`** | **位置指令**：交给内部 PD 控制器，走完整动力学 | GW | 官方示例前 150 步用 `set_`、之后切 `control_`。配套 `set_dofs_kp/kv/force_range` 配增益与力矩饱和，⚠️ **必须在 `build()` 之后**调用 |
| **两层 PD 增益授权** | GS3：USD 属性层 vs 运行时 tensor 层 | GS3 | **Layer 1 `usd_drive_api`** 在 `world.reset()` **之前**、持久且跨引擎；**Layer 2 `articulation_view_runtime`** 在**之后**、仅本次运行，且 **`newton_standalone` 读不到** ⇒ 换后端时 Layer 2 的调参会静默失效 |
| `armature` | GS3：关节等效转子惯量（数值稳定裕度） | GS3 | 分层取值：torso **0.1** / wrist **0.02** / 底盘驱动轮 **0.0** |
| `frictionloss` | GS3：关节常量库仑摩擦下限 | GS3 | 默认 **0.3**；`chassis_drive` 例外取 **0.05** —— 0.3 会造成约 **0.03 rad/s 的速度死区** |
| `solref` / `solimp` | GS3：MuJoCo 接触柔度参数 | GS3 | 默认 `solref=(0.002,1.0)`=(timeconst, dampratio)、`solimp=(0.9,0.95,0.001,0.5,2.0)` |
| **ke/kd 反演** | GS3：由目标 `solref` 反算 `kd=2/timeconst`、`ke=(kd/2ζ)²` | GS3 | ⚠️ **绝不直写 `geom_solref`** —— mjwarp **每步会重算覆盖** |
| **mimic joint（主从夹爪）** | GS3：一主 N 从的夹爪耦合约束 | GS3 | master 靠 `HasAPI(DriveAPI)` 识别；**三套实现**（`PhysxMimicJointAPI` / 软件广播 / MuJoCo 等式约束）；master 最优增益 **2e3/200** |
| **`JOINT_ABS` / `EEF_ABS`** | GS3：策略回包的动作 `kind`，即两种**动作空间语义** | GS3 | 由 `_post_process_action()` 分派；`end_pose` 参考系声明为 **`base_link`** |
| **动作空间的规范维度与布局** | — | GS3 | ⚠️ **`未提及`** —— 文档只给两种语义与 effort 14 维，**没有统一的"N 维动作向量逐位布局表"**。跨栈对接时必须自己实测确认 |
| `init_base_pose` / `init_joint_pos` | GS3：场景 YAML 的初始化字段 | GS3 | **非物理 teleport**，在第一个求解器 tick 之前施加。⚠️ **`init_joint_pos` 单位是「度」** —— 全库唯一的非弧度关节量，最容易错 |
| **effort 14 维** | GS3：`/joint_states` 的力矩通道维度 | GS3 | 对应双 7-DOF 臂；proprioception **100 Hz 且滞后一拍** |
| **14 维动作（EE 空间）** | GE2：左右臂各 7 维末端状态 `[x,y,z,r,p,y,o]` 拼接 | GE2 | `o` 是夹爪开合度。⚠️ **与 16 维关节空间不是同一套表示** |
| **两套 16 维布局** | GE2：世界模型侧 vs 策略侧的关节向量排列 | GE2 | ⚠️ 见 §0 第 8 组。转换函数 `wm_state_to_policy_state()`（`types.py:72-82`）。**弄反不报错、只是行为错** —— 本项目最高频的静默错误 |
| **`compress_actions`** | GE2：默认 `True`，50 步动作 avg-pool 压成 1 块 25 | GE2 | 夹爪用**最近邻保时机**、手臂**保端点 + 内部平均池化**；**默认站在"快"那边** |
| `joint_mapping` | LW：策略动作重排用的映射表 | LW | 在 `step_environment()` 里从 `usr_args['joint_mapping']` 取 —— 接自研策略时的必填项 |
| `FrameTransformer` | LW：测末端位姿的**运动学查询** | LW | ⚠️ **不是物理传感器** —— EE 位姿精确无误差，**不存在真机上的标定误差** ⇒ 基于它的精度结论不可外推到真机 |
| **EE link vs TCP link** | 规划器用的末端链接 ≠ 仿真里的工具中心点链接 | LW（实测） | ⚠️ LW 复现里两者同关节角下**世界 X 轴相差 0.30 m**，导致 scripted 抓取 **8/8 全失败且判定为不可修**。跨栈对接时**必须显式核对是哪个 link** |

---

## 3. 场景、资产与实体

| 术语 | 定义 / 解释 | 出现的项目 | 备注（跨工具链差异） |
|---|---|---|---|
| **OpenUSD stage** | GS3：全工具链**唯一真值源**，物理/光学/渲染参数都 author 成 USD 属性 | GS3（LW 间接） | 跨引擎一致性**靠 USD 而非代码分支**。这是 GS3 三套仿真栈能共存的根本原因 |
| **AS3** | GS3：AgiBot Sim Asset Spec 3，资产目录规范 | GS3 | 物理属性以 **payload 分层**：`physics.usda` / `physx.usda` / `mujoco.usda` |
| **三阶段装配链** | GS3：`assemble_robot` → `assemble_scene` → `launch` | GS3 | **不是直接 load 场景**，是先"装配"再加载；带缓存 |
| `manifest.json` | GS3：物理进程与渲染进程**唯一的静态契约** | GS3 | 动态部分走 `/tf_render`；也是装配缓存的门控 |
| `entity` | GW：场景中的实体对象，与 solver 一一对应 | GW | 两个特殊类型：**`hybrid_entity`**（同一物体不同部分用不同求解器）、`emitter`（持续产生流体/颗粒） |
| `morph` | GW：**形态 / 几何来源**（程序化几何或资产文件） | GW | `gs.morphs.Box/Sphere/Mesh/MJCF/URDF/USD/Terrain/Drone/Nowhere`；⚠️ **`Nowhere`** = 先注册后定位 |
| `material` | GW：**材料模型**，决定实体路由到哪个 solver | GW | 用法 `gs.materials.<求解器>.<材料>`，如 `gs.materials.PBD.Cloth()`。⚠️ 见 §0 第 5 组 |
| `surface` / `texture` | GW：**外观**材质与贴图（与物理 `material` 分离） | GW | `gs.surfaces.*` / `gs.textures.*` |
| **`solver`** | GW：**建模方法**（求解器），8 个，同场景同状态共存 | GW | `Rigid/FEM/MPM/SPH/PBD/SF/Kinematic/Tool`。⚠️ **≠ coupler** |
| **`coupler`** | GW：把不同物体 / 运动学树 / 接触模型耦合到**同一批量环境**的模块 | GW | 3 个：**Legacy（默认）/ SAP / IPC**；`coupler_options=` 一行切换，`None` 回落 Legacy。⚠️ **换耦合器不是行为中性的**（`sap_coupler.py` 有 20 个物料对专用 handler） |
| **`scene.build()`** | GW：**不可逆分界线** —— 之前是声明期，之后是运行期 | GW | 编译期做 kernel JIT + 内存分配 + 并行环境铺开；之后只能 `step`/`reset`/读写状态。⚠️ `add_entity`/`add_sensor`/`add_camera` **必须在它之前** |
| **四路组合** | LW：`scene × robot × task × rl` 四类 gym id 解析成一个环境 | LW | LW 的核心机制。⚠️ **绝大多数故障是"组合没解析对"而非"仿真算错了"** |
| **组件 id** | LW：格式 `{Backend}-{Type}-{Name}`，如 `Robocasa-Task-LiftObj` | LW | 由 `f"{backend.capitalize()}-{cfg_type.capitalize()}-{name}"` 拼装 ⇒ ⚠️ **`.capitalize()` 把首字母外全部小写，大小写敏感陷阱**。另有第二层"复合 id" `Robocasa-{task}-{robot}-v0`，**两套命名勿混** |
| **`layout`** | ⚠️ **同名不同义**（见 §9） | GS3 / LW | **GS3**：Benchmark 任务 YAML 的三大顶级段之一（与 `app`、`benchmark` 并列），对应 dataclass `LayoutConfig`。**LW**：**场景标识字符串**，按短横线切成 `scene_type-layout-style`，5 种写法（`robocasakitchen-9-8` 全定 / `robocasakitchen-4` style 随机 / `robocasakitchen` 全随机 / `libero-1-1` / `/path/to/scene.usd`） |
| `obj_groups` | LW：RoboCasa 系任务的**类别级**物体采样规格 | LW | ⚠️ 与 LIBERO 系**钉死 USD 资产名**（`asset_name="Plate012.usd"`）**设计哲学相反** —— 前者高方差**适合泛化评测**，后者低方差**适合闭环基线** |
| **Scene Language DSL** | GS3：LLM 生成场景用的领域语言 | GS3 | 流水线：RAG 检索资产（2048 维 embedding，ChromaDB，约 200 ms）→ DSL → 执行建 USD |
| **Episode Bundle** | GE2：驱动一切的输入目录（样例 `assets/demo_000`），8 个文件 | GE2 | ⚠️ `actions_0.npy (T,16)` 是**绝对关节角**；`state_joints_0.npy` 是 **20 维**（多 head2 + waist2）；**两个 `(T,14)` eef 文件用途不同、拿错不报错** |
| **单位与坐标约定** | 长度单位与上方向 | GS3 / GW | GS3：全栈 **米**制、上方向 **+Z**、`metersPerUnit=1.0`，重力 `未提及`（用引擎默认 −9.81 −Z）。GW：`gravity=(0,0,-9.81)` 显式给出。⚠️ **GS3 的 `init_joint_pos` 是「度」，是这套米/弧度约定里的唯一例外** |

---

## 4. 并行环境与批处理

| 术语 | 定义 / 解释 | 出现的项目 | 备注（跨工具链差异） |
|---|---|---|---|
| **`n_envs`** | GW：`scene.build(n_envs=N)`，并行化的**唯一开关** | GW | ⚠️ **`0` 与 `1` 语义不同**（见 §0 第 6 组）。⚠️ `env_spacing` / `n_envs_per_row` / `center_envs_at_origin` **只影响可视化**，物理隔离靠 batch 维本身 |
| **`num_envs`** | LW：并行环境数 | LW | `Context` 字段；`DEFAULT_SCENE_CFG = InteractiveSceneCfg(num_envs=4096, env_spacing=30.0)`；ManiSkill PPO 默认 **512**、skrl 配置默认 **10** —— 三处默认值互不相同 |
| `envs_idx=` | GW：只作用于**环境子集**的贯穿全库约定 | GW | `control_dofs_*` / `scene.reset()` / `read_sensors()` / `get_time()` 都接受。RL 的"只重置已结束环境"靠它 |
| **tiled rendering（平铺渲染）** | 所有并行环境渲进**同一张大纹理**、共享一个 USD sensor prim | LW | Arena 默认开（`ArenaCameraCfg._use_tiled_camera=True`）；LW **不用 `ArenaCameraCfg`**、直接声明 `TiledCameraCfg`。⚠️ **与 per-env 相机内参随机化互斥** —— 开了内参随机化会**静默关闭 tiled rendering**，表现为"莫名奇妙地慢" |
| **共享相机 teleport** | GS3：建 N 个共享相机、原生相机 `SetActive(False)` 退化为位姿标记 | GS3 | `shared_cam_render_frames=8`；`delta_time=0.0` 表示**渲染不推进物理时间**；⚠️ N 个 env **串行**取观测 |
| **`GridCloner`** | GS3：RLinf 栈把 N 份场景摊成网格**一次渲染** | GS3 | 与共享相机 teleport **二选一**的另一条并行路线；通道**只有共享内存** |
| `Context` | LW：进程内**全局可变单例** dataclass，约 35 个字段 | LW | 既是唯一真相源也是**并发 / 可复现性弱点** ⇒ **一个进程内只能有一套配置**。⚠️ `device` 字段**声明两次**，后者（默认 `"cpu"`）生效 |
| **`BatchRenderer`** | GW：批量渲染（多环境并行出图） | GW | 靠 `gs-madrona`，⚠️ **仅 Linux + x86_64** |

---

## 5. 渲染

| 术语 | 定义 / 解释 | 出现的项目 | 备注（跨工具链差异） |
|---|---|---|---|
| `Rasterizer` | GW：PyRender 光栅化后端 | GW | 快速调试与基础可视化；能做的域随机化比光追少 `[文章]` |
| `RayTracer` | GW：LuisaCompute 光追后端 | GW | 精度基线路径。⚠️ **渲染路径必须训评一致** —— 用 `Rasterizer` 训的策略拿 `RayTracer` 评，掉分不能归因于策略 |
| **OVRtx** | GS3：NVIDIA 独立 C-API RTX 渲染库，**脱离 Omniverse Kit** | GS3 | 版本**硬钉 `0.3.x`**；变换属性名 `"omni:xform"`、**USD 行向量约定**、**仅 float64** |
| **`render_mode`** | GS3：渲染模式启动参数 | GS3 | 映射：`raster`→`RaytracedLighting`（默认）/ `pathtrace`→`RealTimePathTracing` / `offline`→`PathTracing`。⚠️ **无法识别的值静默回落 `raster`**；⚠️ **OVRtx 路径完全忽略此项**（模式由 USDA 的 `omni:rtx:rendermode` 决定） |
| `rt_subframes` | GS3：路径追踪每帧累积的 subframe 数 | GS3 | Benchmark 栈默认 **8**。⚠️ **全栈无任何 AA / denoiser / DLSS** —— 噪声只能靠加 subframe 压 |
| **AOV / RenderVar** | GS3：渲染输出通道名 | GS3 | RGB = `LdrColor`；深度 = `DistanceToImagePlaneSD`；LiDAR = `PointCloud[Coordinates,Intensity,Counts,TimeOffsetNs,Flags]` |
| **相机内参单位** | `focal_length` / `h_aperture` 用 USD 的"**十分之一场景单位**"约定 | LW | ⚠️ **两套值不可互相套用**：LW 侧（40.6 / 38.11）是**按 FOV 反算的合成值**，Arena 侧（2.1 / 5.376×3.024）是**物理镜头参数化** |
| **`data_types`** | LW：相机输出通道声明 | LW | ⚠️ 9 组相机**全部只有 `["rgb"]`**；唯一例外是绿幕合成运行时追加 `semantic_segmentation` |
| **Camera Raymap** | GE2：6 通道逐像素（射线原点 `o_i`、单位方向 `d_i`） | GE2 | ⚠️ **这是 GE2 唯一的"相机模型"** —— 让模型区分**视点运动**与**物体运动**，腕部相机的运动学信号主要在此 |
| **EE Pose Map** | GE2：3 通道、与像素网格对齐的末端位姿图 | GE2 | 深度感知半径（离相机越近圆越大）+ 夹爪**连续 colormap**。⚠️ **训练与推理必须用同一个 renderer** |
| **三视角命名** | GE2：`V = {h, l, r}` = head / left_wrist / right_wrist | GE2 | 固定 3 个、**不可增删、不可改位姿**；各带可学习 view embedding。⚠️ `frames` 张量是 `(T,3,V,H,W)` —— **`[:,0]` 取到的是通道轴不是视角** |
| **Quadrants** | GW：跨平台编译器层（Taichi fork，LLVM JIT） | GW | ⚠️ **独立包但硬依赖、精确 pin `quadrants==1.3.0`**。四路攻调度开销：kernel graph / 流并行 / launch context 缓存 / 三层编译缓存 |
| **Nyx** | GW 官方博客宣传的 Render 层 | GW | ⚠️ **不在 pip 包内** —— `genesis/**/*.py` 中 grep **零命中**，是独立包 `gs-nyx`，按插件装。**别按博客的能力清单做规划** |

---

## 6. 传感器与噪声建模

| 术语 | 定义 / 解释 | 出现的项目 | 备注（跨工具链差异） |
|---|---|---|---|
| **`SensorOptions`** | GW：**全部**传感器共有的缺陷层 | GW | `delay` / `jitter` / `history_length` / `draw_debug`。⚠️ **相机只到这一层** —— 根本没有噪声字段 |
| **`SimpleSensorOptions`** | GW：`SimpleSensor` 派生传感器**追加**的缺陷层 | GW | `resolution` / `bias` / `noise` / `random_walk`，由 `_apply_hardware_imperfections` 统一施加 |
| `delay` / `jitter` | GW：读取延迟（秒）/ 附加随机延迟（每步在 `[0,jitter)` 均匀采样） | GW | ⚠️ **`jitter > delay` 直接报错**；⚠️ **`delay` 非 `dt` 整数倍只 warning、静默四舍五入**到 `round(delay/dt)*dt` |
| **`enable_corruption`** | Isaac Lab 里"启用 per-term `noise` 配置"的开关 | LW | ⚠️ **在 LW 里是假开关 / 空转** —— 全仓库**没有任何 `ObsTerm` 传 `noise=`**，`True` 出现在 3 处也没用。⇒ **LW 的一切鲁棒性结论都带"无传感器噪声"这个前提** |
| **`instantLidar` / de-skew** | GS3：整圈 360° 在**单一冻结位姿**下一次投射完，移除时间维 | GS3 | v3.2.0 release log 称 "de-skewed rotary lidar"。⚠️ 代价是**丢失真机存在的运动畸变** |
| **`fireTimeNs` 钳制** | GS3：把 LiDAR 发射时刻等比压到 26000 ns 内 | GS3 | OVRtx 发射窗约 **27.7 µs**，⚠️ **超窗渲染器静默返零点** —— 不报错的失效 |
| **`depth_scale`** | GS3：场景 YAML 字段，写进 manifest | GS3 | ⚠️ **死字段，全仓无消费者**。深度恒为 float32 **米**制，**不可配成毫米整型** |
| **域随机化** | 训练/评测时随机化场景属性 | GW / GS3 / LW | **三种规模与命名**：GW 视觉 + 材质属性 + 地形 + 外部扰动（约 10 条扰动轴）；GS3 **11 类已实现**；LW 靠 Arena **`variations`（8 类）**。⚠️ LW 的相机内参随机化**焦距不变、靠改光圈实现**，外参 ±0.005 m，**纹理/材质未提及** |
| **`variations`** | LW：Arena 的域随机化系统 | LW | 分 **build-time**（采样一次）与 **run-time**（每次 reset 重采样）两类 |
| **理想真值（ideal ground truth）** | 传感器输出无噪声、无延迟、无缺失 | GW / GS3 / LW | ⚠️ **这是三个仿真项目的默认状态**：GW 噪声参数全默认 `0.0`；GS3 **深度/IMU/LiDAR 全是几何真值**（仅 RGB 噪声真启用）；LW **完全没有噪声模型**。做抗噪结论前**必须先确认噪声真的开了** |
| **生成伪影（非参数化噪声）** | GE2：物体消失、抓取穿模、纹理漂移 | GE2 | ⚠️ **与上一条恰好相反** —— GE2 没有任何噪声旋钮，但输出**也不是理想真值**；伪影是内生的，**不可参数化、不可关闭** |

---

## 7. 评测、判定与运行模式

| 术语 | 定义 / 解释 | 出现的项目 | 备注（跨工具链差异） |
|---|---|---|---|
| **task / category / sub_task** | GS3：评测组织单位，配置名为 `<robot>_<category>_<task>.yaml` | GS3 | CLI 按**第二个 token** 切 category；category 值如 `if` / `robust` / `manip` / `spatial` / `s2r` |
| **board** | GS3：RoboColiseum 榜单单位，共 **5** 个 | GS3 | Instruction / Robust / Manipulation / Spatial / Sim2Real。⚠️ **表名是对外契约，不得改** |
| **ADER** | GS3：Action Domain Evaluation Rule，规则化动作域评测判据 | GS3 | LLM 批量生成评测场景 + VLM 判完成度；代码在 `plugins/ader/`。⚠️ **VLM 权重与端点不在仓库内** |
| `env_class` / `policy_class` | GS3：Benchmark 的环境与策略插拔点 | GS3 | env 层级 `AderEnv → BaseEnv → DummyEnv → PiEnv`；向量化用 `BenchmarkVecEnv` / `VecEnvAdapter` |
| **`BasePolicy`** | LW：策略插件契约，**4 个待实现抽象方法** | LW | `get_model` / `get_action` / `eval` / `reset_model`。`encode_obs` 合并 `observation['policy']` 与 `['embodiment_general_obs']` 并做 HWC→CHW。⚠️ **这是接自研策略的唯一入口**（LW 无稳定 Python 评测 API，上游 issue #45 未关闭） |
| **`ExecuteMode`** | LW：9 种运行语义 | LW | `TRAIN` / `EVAL` / `TELEOP` / `REPLAY_*4` / `TEST_OBJECT` / `TEST_FIXTURE`。⚠️ **`str_to_execute_mode()` 对未知值静默回落 `TELEOP`**；而模式真的改变行为（装哪些相机、是否录制、成功判定是否生效） |
| **成功判定防抖** | LW：必须 `episode_length_buf >= 10` 才允许 latch，且需连续满足 `_success_count` 步 | LW | `TELEOP` 下是 `int(1/sim.dt/2)` 即**半秒**，其他模式为 1。⇒ 解释了"看起来成功了要等半秒" |
| **`rl_on`** | LW：把 (任务, 本体) 绑定到 RL 配置类的装饰器 | LW | ⚠️ **形同虚设** —— `_rl_on_tasks` 只在基类声明一次，`append` 改的是**共享基类列表**，断言成了全局检查而非 per-class 绑定 |
| **解耦式策略 API / `detach()`** | LW：server–client 远程环境；`detach()` 关环境 + `new_stage()` + `gc.collect()` | LW | ⚠️ **"server–client" 准确，"zero-copy" 未证实**（实为 AF_INET TCP + authkey）。真正价值是**换任务不重启 Isaac Sim**（冷启动是分钟级） |
| **配置 stem** | LW：`configs/` 全树按**文件名主干**扁平化索引 | LW | `--task_config=g1-controller` → `configs/data_collection/teleop/g1-controller.yml`。⚠️ **同名文件静默互相覆盖**，`.yaml` 压 `.yml` |
| **monkey patch** | LW：对 isaaclab 的运行时函数替换 | LW | **上游 10 处 / 本机复现仓库 11 处**；⚠️ `import lw_benchhub.core` 即**全部生效，无法选择性关闭** ⇒ **不要升级 isaaclab 或 Arena 子模块** |
| **`physics_engine` id** | GS3：物理后端选择键 | GS3 | ⚠️ 规范值**只有** `isaac_physx` / `isaac_newton` / `newton_standalone`；裸写 `physx` / `newton` **被拒** |
| **Tier-1 / Tier-2** | GS3：安装分层 | GS3 | Tier-1 自动 bootstrap；Tier-2 按需 pip extras（`teleop`/`generator`/`world`/`all`/`full`） |
| **假阳性 / 假阴性** | 判定结果与真实情况不符的两个方向 | 全部（实测） | ⚠️ **本领域最贵的两类错误**。假阳性例：LW 管线自报 `success=True` 而 **8 个 episode 全是失败轨迹**；假阴性例：GE2 Stage 3 的 0 % 是**判分文本错位**造成的。⇒ 见 [`best_practices.md` §5.3 审计四件套](best_practices.md) |

---

## 8. GE2 专属：世界模型范式的术语

> GE2 不是物理仿真器，它的术语与其余三个**基本不重叠**。放在单独一节，避免与仿真器术语混读。

| 术语 | 定义 / 解释 | 备注 |
|---|---|---|
| **世界模型 / World Simulator** | 用生成模型从「首帧 + 动作」产出未来多视角视频的模块 | 论文自称 "neural world simulator for manipulation"。⚠️ **与"物理求解 + 渲染"回路互斥** —— 不是二者的补充实现，是替代范式 |
| **动作条件视频生成** | 把语言条件 `T(q)` 换成动作轨迹 `A`，DiT 骨架不变 | 论文明确"**对动作来源不可知**" —— 策略 / 遥操 / 规划器 / 手写皆可 |
| **DiT** | 视频扩散 Transformer 主干，Cosmos-Predict2-2B-Video2World | ⚠️ 仅 **2B 参数**；**只有部分 block 做跨视角注意力**（多视角一致性是软约束，不是硬保证） |
| **VAE** | 视频隐空间编解码器，**像素直接由它解码** | `z_noisy` 为 **16 通道**。这是"无渲染器"的具体含义：像素不来自光栅化或光追 |
| **扩散调度 / flow matching** | 隐空间流匹配，预测去噪速度 `v_θ`，掩码 `M` 只在待预测帧算损失 | ⚠️ **无闭式概率密度 ⇒ 无法做 policy gradient**。这是"不能直接做在线 RL"的机制原因 |
| **本体感觉状态专家（Pose Expert）** | 从视频隐层解码 16 维关节态 `[θ^L(7), g^L, θ^R(7), g^R]` | 夹爪线性归一化到 `[0,1]`；冻结视觉专家只训它 |
| **World Judge** | 基于 Robometer 改造的 VLM 奖励模型，逐帧输出 success 概率 | ⚠️ **未开源**（实现与权重都没发）⇒ **开箱即用时 `reward` 与 `progress` 恒为 `None`**。条件是**当前 chunk 的子任务 caption 而非完整指令** |
| **`progress`** | 逐帧任务进度标量 | ⚠️ **被刻意砍掉** —— 真机轨迹含纠错 / 绕路 / 重试，非单调执行下标签噪声大 |
| **`rollout`** | 一次生成序列 | ⚠️ **`conditioning="episode"` 是回放不是闭环**（策略随机、画面照原轨迹走）；**`"action"` 才是闭环** —— 这是最容易搞错的一个开关 |
| **filtered BC / 过滤式 BC** | 用生成 rollout 筛数据回灌训练 | 论文正文**唯一演示**的下游学习方式；三任务真机平均 **+15 pp** |
| **RWR（奖励加权回归）** | 按轨迹奖励 softmax 加权回归 | `[实践]` 留出集 OSR **30 % → 80 %**。⚠️ 单轨迹时权重退化为均匀 ⇒ 实为"奖励加权的过滤式 BC"；⚠️ 判分器是**自补的替身而非官方 World Judge**，该分数**只能内部对比、不可外推** |
| **EWMScore** | WorldArena 评分：6 感知维度、16 项视频质量指标的线性归一化平均 | 与人类主观 **r=0.825** / 数据合成 **0.600** / ⚠️ **动作规划仅 0.360（弱相关）** |
| **WorldArena** | 世界模型统一评测基准（论文）+ 同名在线**活榜** | ⚠️ **论文与活榜是两份不同结果，不可互引**；引用活榜必须带日期。⚠️ 那篇基准论文正文 grep `GE-Sim` **命中 0** |

---

## 9. ⚠️ 同名不同义警告表

> 这些词在两个以上项目里都出现，但**含义不同**。看到它们时必须先确认是哪个项目的语境。

| 词 | 在 A 项目里 | 在 B 项目里 | 后果 |
|---|---|---|---|
| **`layout`** | **GS3**：任务 YAML 的**顶级配置段**（与 `app`、`benchmark` 并列） | **LW**：**场景标识字符串**，`scene_type-layout-style` | 完全不同的东西，配置抄错方向 |
| **`substeps` / `decimation`** | **GW / GS3 `substeps`**：一个物理步**内部**的求解细分 | **LW `decimation`**：一个环境步里跑**几个物理步**（决定控制率） | 见 §0 第 2 组 —— 想改稳定性却改了控制率 |
| **`material`** | **GW**：**物理**材料模型（决定路由到哪个 solver） | 通用图形学语境 / GS3 USD：**外观**材质 | GW 里传错对象是实际发生过的错误 |
| **`n_envs` / `num_envs`** | **GW `n_envs`**：`0` 与 `1` **语义不同** | **LW `num_envs`**：`Context` 字段，三处默认值互不相同（4096 / 512 / 10） | GW 侧张量形状错；LW 侧"我设的值没生效" |
| **物理步长** | **GW / LW**：周期（**秒**） | **GS3**：频率（**Hz**） | 量级差 10⁴ |
| **关节角单位** | **GW / LW / GE2**：弧度 | **GS3`init_joint_pos`**：**度** | 全库唯一例外，最容易错 |
| **16 维状态** | **GE2 世界模型侧**：`[L7臂, L夹爪, R7臂, R夹爪]` | **GE2 策略侧**：`[L7臂, R7臂, L夹爪, R夹爪]` | ⚠️ **同一项目内部**的两套布局；**用错不报错，只是行为错** |
| **"渲染帧率"** | **GW**：无全局参数，由 `cam.render()` 调用决定 | **GS3**：`render_hz`（`0.0` 是哨兵）；**LW**：`render_interval` + `update_period` 两个旋钮且不相等 | 以为改了一个就控住了帧率 |
| **`solver`** | **GW**：8 种**建模方法**（Rigid/FEM/MPM/…） | **GS3 / LW**：通常指 PhysX / MuJoCo 等**物理引擎后端** | GW 的"换 solver"是换材料路由，不是换引擎 |
| **成功率（success rate）** | **LW / GS3**：环境判定的任务成功比例 | **GE2**：由 **VLM 判分器**给出；且若用自补判分器**不可外推** | 跨项目直接比较成功率数字是无意义的 |

---

## 10. 关联文档

| 文档 | 什么时候用 |
|---|---|
| [`toolchain_comparison.md`](toolchain_comparison.md) | 想知道这些能力在四个工具链间怎么取舍 —— 横向对比与选型 |
| [`common_reproduction_guide.md`](common_reproduction_guide.md) | 通用复现流程（准备 / 安装 / 运行调试 / 调优 / 验收 / 记录） |
| [`common_issues_solutions.md`](common_issues_solutions.md) | 手上有一条报错 —— 按现象查类别与解法 |
| [`best_practices.md`](best_practices.md) | 想避免已知代价 —— 32 条教训的主题化汇总 |
| [`../projects/00-index.md`](../projects/00-index.md) | 进入项目级五层文档；术语原文在各项目 `background_knowledge.md` §2 / §7 |

**术语原文直达**：[`GW`](../projects/genesis_world/background_knowledge.md) · [`GS3`](../projects/genie_sim_v3/background_knowledge.md) · [`LW`](../projects/lw_benchhub/background_knowledge.md) · [`GE2`](../projects/ge_sim_v2/background_knowledge.md)


