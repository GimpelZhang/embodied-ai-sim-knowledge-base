# Genie Sim v3 — 具身智能仿真工具链知识文档

> 文档整理日期：2026-08-29
> 覆盖版本：**v3.2.0**（仓库 `VERSION` 文件，发布日期 2026-06-25）
>
> **证据等级标注**（全文通用）：
> - `[CODE]` — 在开源仓库代码中可直接验证，附仓库相对路径（必要时带行号）
> - `[PAPER]` — 来自 arXiv:2601.02078 论文
> - `[README]` — 来自仓库 README / 模块文档
> - `未提及` — 在论文、代码、官方文档中均未找到证据，**不做推测**
>
> **官方文档站说明**：`agibot-world.com/sim-evaluation/docs/#/v3` 为纯 JavaScript 渲染的 SPA，抓取仅得到标题 "Genie Sim User Guide"，正文无法获取。因此本文技术结论以 `[CODE]` 为主、`[PAPER]` 为辅。
>
> 仓库路径缩写（下文统一使用，均为仓库相对路径）：
> | 缩写 | 实际路径 |
> |---|---|
> | `ENG/` | `source/geniesim_ros/src/ros_ws/src/genie_sim_engine/` |
> | `RENDER/` | `source/geniesim_ros/src/ros_ws/src/genie_sim_render/` |
> | `BRINGUP/` | `source/geniesim_ros/src/ros_ws/src/genie_sim_bringup/` |
> | `BENCH/` | `source/geniesim_benchmark/src/geniesim_benchmark/` |
> | `DC/` | `source/data_collection/` |

---

## 索引总结（3 个要点）

1. **不是单一仿真器，而是三套共存的仿真栈**：RT Engine（ROS 2 原生实时闭环）、Benchmark/Data-collection（直连 Isaac Sim，用于评测与采集）、RLinf（CPU MuJoCo 多进程 + 共享内存，用于 RL 训练）。三栈的物理、渲染、传感器路径完全不同，不可混谈。
2. **以 OpenUSD 为唯一真值源、三物理后端可切换**：PhysX（默认稳定）、Isaac Newton（实验，仅刚体）、Newton-standalone（唯一支持布料/软体）。跨引擎一致性靠 USD 属性而非代码分支保证。
3. **评测体系是其核心竞争力**：200+ 任务、10 万+ 场景、5,140 个资产、10,000+ 小时合成数据，配合 LLM 生成任务与 VLM 自动打分，并作为 RoboColiseum 竞赛引擎；论文称仿真与真机成功率线性拟合 R²=0.931。传感器侧仅 RGB 有噪声模型，深度/IMU/LiDAR 均为几何真值，是 sim2real 的明确缺口。

---

## 1. 项目概述

| 项目 | 内容 |
|---|---|
| **官方名称** | **Genie Sim**（核心评测模块名为 **Genie Sim Benchmark**） |
| **论文题名** | *Genie Sim 3.0: A High-Fidelity Comprehensive Simulation Platform for Humanoid Robot* |
| **开发者** | **AgiBot（智元机器人）** — 原文："Genie Sim is the simulation platform from AgiBot." GitHub 组织 `AgibotTech` |
| **版本** | **3.2.0**（`VERSION`；发布 2026-06-25） |
| **许可证** | `source/geniesim_*` 与 `source/data_collection` 为 **Mozilla Public License 2.0**；`source/scene_reconstruction` 为多许可证混合；cuRobo 受 NVIDIA cuRobo 许可约束（**仅限非商业研究/评估**） |
| **论文** | arXiv **2601.02078**（v1 提交 2026-01-05，当前 v4，最后修订 2026-08-14），cs.RO |
| **作者** | 19 人，第一作者 Chenghao Yin，通讯/末位 Maoqing Yao |

### 1.1 主要用途

`[README]` 官方定位原文：

> "It provides developers with a complete toolchain for *environment reconstruction*, *scene generalization*, *data collection*, and *automated evaluation*. Its core module, **Genie Sim Benchmark** is a standardized tool dedicated to establishing the most accurate and authoritative evaluation for embodied intelligence."

即四大用途：**环境重建 → 场景泛化 → 数据采集 → 自动化评测**。

### 1.2 规模数字

`[README]` / `[PAPER]`

- 评测体系覆盖 **200+ 任务**、**100,000+ 场景**
- 开放 **10,000+ 小时**合成数据（含真实机器人操作场景）
- **5,140** 个经验证的 sim-ready 3D 资产
- 声称仿真与真机测试结果差异 **< 10%**；论文给出线性拟合 **R² = 0.931、斜率 ≈ 1.023**
- 资产、数据集、代码**全部开源**

### 1.3 适用场景

- **本体类型**：人形 / 双臂机器人的 loco-manipulation（移动操作）。一等支持 AgiBot **Genie G2** 系列（`arm × gripper` 矩阵）；另提供 Franka、UR5、Aloha、ARX、Agilex 的参考 URDF；支持通过 xacro 接入自定义机器人
- **资产领域**：覆盖五大真实作业场景 — **零售（retail）、工业（industry）、餐饮（catering）、家庭（home）、办公（office）**
- **典型工作流**：VLA / VLM 策略的闭环评测与排行榜竞赛（RoboColiseum）、合成数据生产、真实场景 3DGS 重建复刻、强化学习训练、VR 遥操作采集

### 1.4 论文要解决的三个瓶颈

`[PAPER]`

1. **真机数据采集成本高** — 人力、时间、硬件损耗
2. **现有仿真 benchmark 碎片化** — 各家任务/资产/评测互不兼容，难以横向比较
3. **保真度不足** — 仿真训练的策略难以零样本迁移到真机

---

## 2. 核心原理

### 2.1 仿真方法

#### 2.1.1 OpenUSD 作为唯一真值源

`[CODE]` 整个工具链的中枢不是某个仿真器 API，而是 **OpenUSD stage**。所有信息——几何、材质、灯光、物理属性、关节驱动增益、相机光学参数、LiDAR profile、渲染模式——都被 author 成 USD 属性，再由不同消费者（PhysX 的 USD parser、Newton 的 `add_usd`、OVRtx 的 Fabric、Replicator 的 render product）各自解析。

使用的 schema：

- `UsdPhysics`（`RigidBodyAPI`、`CollisionAPI`、`MeshCollisionAPI`、`ArticulationRootAPI`、`DriveAPI`、`MassAPI`）
- `PhysxSchema`（`PhysxJointAPI:armature`、`PhysxMimicJointAPI`、`PhysxRigidBodyAPI`）
- `NewtonMimicAPI`
- `UsdGeom.Camera`、`UsdLux.DomeLight`
- 自定义命名空间：`mjc:damping` / `mjc:frictionloss`（MuJoCo 侧被动关节物理）、`mujoco:geom_solimp`（接触柔度）、`omni:sensor:Core:*`（LiDAR）、`omni:rtx:rendermode`（渲染模式）、`omni:lensdistortion:opencvFisheye:*`（镜头畸变）

**设计后果**（`ENG/config/physics_params.yaml` 头部注释）：同一份 USD 被"任何解析 stage 的消费者"读取，因此 USD 上的驱动增益既是 PhysX 的初始增益，又通过 Newton 的 `add_usd` 变成 `model.joint_target_ke/kd`，再变成 dump 出的 MJCF 里的 `actuator gainprm/biasprm`。**跨引擎一致性靠 USD 而不是靠代码分支保证。**

#### 2.1.2 三阶段装配链

`[CODE]` `ENG/scripts/assemble_scene.py`（1103 行）、`ENG/scripts/assemble_robot.py`

场景不是直接加载，而是先"装配"：

1. **assemble_robot** — 从 URDF 导入 → 写 `robot.usda` → author 碰撞近似策略、驱动增益（Layer 1）、mimic 约束、被动关节物理
2. **assemble_scene** — 组合场景 USD + 机器人 USD → 生成 `render_layer.usda`（相机、LiDAR、RenderProduct、RenderVar、渲染模式）+ `manifest.json`（进程间契约）
3. **launch** — 引擎进程与渲染进程各自读 `manifest.json`，前者建物理，后者建渲染

装配结果带缓存（由 `manifest.json` 门控），避免每次启动重复导入。`assemble_robot.py` 在首次写出 `robot.usda` 后即为**只读**。

`manifest.json` 是**物理进程与渲染进程唯一的静态契约**（动态部分走 `/tf_render`），字段：`scene_usda` / `usd_path`、`robot_usda`、`render_layer_usda`、`robot_prefix`、`free_cam_prim_path`、`base_path`、`cameras[]`。

**兜底场景** `ENG/scripts/assemble_scene.py:420-466`：找不到场景时生成 `scene_empty.usda` — Z-up、`metersPerUnit=1.0`、50×50 m 灰色地面、单个 `UsdLux.DomeLight`（`intensity=1000.0`）。这间接确认全栈单位约定为**米**、上方向为 **+Z**。

#### 2.1.3 AS3 资产布局

`[CODE]` 资产按 AS3（AgiBot Sim Asset Spec 3）组织，物理属性以 **payload** 分层挂载：

```
payloads/Physics/physics.usda    ← 通用 UsdPhysics 层
payloads/Physics/physx.usda      ← PhysX 专属层
payloads/Physics/mujoco.usda     ← MuJoCo/Newton 专属层
```

机制价值：同一份几何资产按目标引擎**选择性 payload**，引擎无关部分只写一次，引擎特有调参互不污染。这是"三后端共存"能落地的资产层前提。

#### 2.1.4 三套共存的仿真栈（理解本项目最关键的一点）

`[CODE]`

| | **RT Engine** | **Benchmark / Data-collection** | **RLinf** |
|---|---|---|---|
| 代码位置 | `source/geniesim_ros/` | `source/geniesim_benchmark/`、`source/data_collection/` | `source/rlinf_geniesim/` |
| 用途 | 实时闭环仿真（ROS 2 机器人栈） | 数据采集 + benchmark 评测 | RL 训练 |
| 物理 | PhysX / Isaac Newton / Newton-standalone（三选一） | Isaac Sim PhysX | **CPU MuJoCo**，每 env 一进程 |
| 渲染 | OVRtx（Kit-free C-API，硬钉 0.3.x） | Kit RTX `RealTimePathTracing` | 单个 Isaac Sim 进程 + `GridCloner` |
| 进程模型 | 物理进程 + 渲染进程（`/tf_render` 解耦），或 inline OVRtx 单进程 | 单进程 Kit | N 个 MuJoCo 进程 + 1 个渲染进程 |
| 传输 | ROS 2 topics | ROS 2 + gRPC + WebSocket/HTTP | 共享内存（SHM） |
| 时间步 | 100 Hz 物理 / 30 Hz 渲染（默认） | Replicator `delta_time=0.0` 逐步驱动 | MuJoCo 步 + `steps_per_step` |

> ⚠️ `source/AGENTS.md` 明确声明：`geniesim_benchmark` 与 `geniesim_ros` 是**两条互相独立的并行栈**，场景格式与 launch 图不得混用。路线图计划把 benchmark 重构为 `geniesim_ros` 之上的一层，**目前尚未完成**。

**两个 Isaac Sim 版本共存** `[CODE]` `docker/AGENTS.md`、`docker/Dockerfile.5.1`：Isaac Sim **5.1** 位于基础镜像 `/isaac-sim`，通过 `omni_python` 调用；Isaac Sim **6.0** pip 安装进系统 python3.12，通过 `python3` 调用（Newton 后端需要）；ROS 2 发行版为 **Jazzy**。

---

### 2.2 物理引擎

#### 2.2.1 两层抽象与三个后端

`[CODE]` `ENG/scripts/engine/base.py`、`ENG/docs/engines.md`

```
PhysicsEngine (ABC)            ← 引擎级：生命周期、stage 管理、step、tick_extras
   ├─ IsaacPhysXEngine
   ├─ IsaacNewtonEngine
   └─ NewtonHeadlessEngine
          └─ SolverAdapter (ABC)   ← 求解器级：仅存在于 newton-standalone 内
                 ├─ MuJoCoWarpAdapter   (SolverMuJoCo)
                 ├─ FeatherstoneAdapter (SolverFeatherstone)
                 └─ AVBDAdapter         (SolverVBD)
```

| `physics_engine` | 类 | 文件 | 说明 |
|---|---|---|---|
| `isaac_physx`（默认） | `IsaacPhysXEngine` | `ENG/scripts/kit/isaac_physx.py` | PhysX 5 via `omni.physx`，稳定参考路径 |
| `isaac_newton` | `IsaacNewtonEngine` | `ENG/scripts/kit/isaac_newton.py` | `isaacsim.physics.newton` 包装器，仅 MuJoCo-Warp 刚体，**不支持布料** |
| `newton` | `NewtonHeadlessEngine` | `ENG/scripts/engine/newton/` | Newton 直连、Kit-free，**唯一支持布料/软体** |

规范引擎 id 为 `isaac_physx` / `isaac_newton` / `newton_standalone`；裸写 `physx` / `newton` 会被 `runtime.bootstrap._validate_engine_id` 拒绝。

`SolverAdapter` 的核心契约是一个**可被 CUDA graph 捕获的 `substep`**：substep 循环内不得有任何 host 侧分支或分配，才能用 `wp.ScopedCapture` 录制一次、之后每步 `wp.capture_launch` 重放。这是 newton-standalone 性能的来源。

#### 2.2.2 时间步、子步与频率

`[CODE]` `ENG/scripts/common/params.py`

```python
physics_hz: float = 100.0                     # 默认物理频率
render_hz:  float = 0.0                       # 0.0 = 哨兵，回落到 render_target_hz
render_target_hz = 30.0                       # 默认渲染频率
physics_solver: str = ""                      # "" = 引擎自选默认
physics_solver_substep: int = 0                # 0 = 引擎默认
physics_solver_iterations: int = 0             # 0 = 引擎默认
physics_solver_mass_matrix_interval: int = 0   # 0 = 引擎默认(= sim_substeps)
```

各 launcher 实测配置（`BRINGUP/config/launcher_*.yaml`）：

| launcher | `physics_engine` | `physics_solver` | physics_hz | substep | ⇒ sim_dt | render_hz |
|---|---|---|---|---|---|---|
| `launcher_ovrtx_isaac_physx` | `isaac_physx` | — | — | — | — | — |
| `launcher_ovrtx_isaac_newton` | `isaac_newton` | `mujoco-warp` | 100 | 10 | **1 ms** | 30 |
| `launcher_newton_mjwarp` | `newton` | `mujoco-warp` | 100 | 10 ★ | **1 ms** | 30 |
| `launcher_newton_mjvbd` | `newton` | `mjvbd` | 60 | 10 | 1.67 ms | 40 |
| `launcher_newton_mjxpbd` | `newton` | `mjxpbd` | 60 | FEM 场景 24 | — | 30 |
| `launcher_newton_avbd` | `newton` | `avbd` | 60 | — | — | 10 |
| `launcher_newton_fsvbd` | `newton` | `fsvbd` | 60 | — | — | 10 |

**核心权衡**（`launcher_ovrtx_isaac_newton.yaml` 注释）：不提高 `physics_hz`，而在求解器内部细分子步——

> "10 mjwarp substeps per 10 ms outer frame → dt_solver = 1 ms … Cranking `physics_hz` instead would pay Kit/USD update cost (~9 ms) on every outer tick; substepping [avoids it]."

即外层 tick 要付约 **9 ms** 的 Kit/USD 更新固定开销，把细分放进求解器可以免掉这笔重复成本。

**重力**：`未提及`（代码未显式 author 重力向量，使用引擎默认 −9.81 m/s² 沿 −Z）。

#### 2.2.3 接触与摩擦模型

`[CODE]` `ENG/scripts/common/object_classification.py:183-206`

```python
_DEFAULT_SOLREF   = (0.002, 1.0)                  # (timeconst, dampratio)
_DEFAULT_SOLIMP   = (0.9, 0.95, 0.001, 0.5, 2.0)  # (d_min, d_max, width, midpoint, power)
_DEFAULT_FRICTION = (1.0, 0.005, 0.0001)          # (滑动, 扭转, 滚动)
```

物体分为 robot / floor / passive / static_prop / other 五类，但**当前五类使用完全相同的参数**——分类结构已就位，尚未分化调参。

**solref ↔ ke/kd 反演（关键机制）** `ENG/scripts/engine/newton/mjc_contact.py:62-105`：MuJoCo-Warp 不允许直接写 `geom_solref`——它每步从 `shape_material_ke` / `shape_material_kd` 通过内部 `convert_solref` 重算。因此要设定期望 solref，必须反演出 ke/kd：

```python
kd = 2.0 / timeconst
ke = (kd / (2.0 * dampratio)) ** 2
```

文件注释强调：**所有调用点都用反演形式，绝不直写 `geom_solref`**。

**solref 与子步数的耦合校验** `mjc_contact.py:150-167`：取全场景最紧的 `solref[0]`，推算所需最小子步数，不满足则报错要求"提高 substep 或放宽 solref timeconst"。机制上，接触刚度的时间常数必须显著大于 `sim_dt` 才稳定，这段代码把隐式约束变成了启动期硬检查。

**碰撞近似策略（选择性碰撞）** `ENG/scripts/assemble_robot.py:1262-1386`：

- 夹爪 visual mesh 用 **SDF**（`gripper_visual_sdf`）——代价高，但对薄壁/凹形夹爪指是唯一能产生正确接触面的近似
- 轮子用 **convexHull**（`wheel_convex_hull`）——只需外轮廓
- 其余非接触 link **禁用碰撞**——机械臂中段极少参与接触，直接关闭省下大量 contact pair

`ENG/docs/perf.md` 把该策略列为求解器性能第一梯队手段，并警告 `MeshCollisionAPI` 近似**不可用 `meshSimplification`**（PhysX 会推迟到求解时才网格化）。

**PhysX 求解器细节**（迭代次数、solver type、CCD、GPU pipeline）：`未提及` — grep 确认代码中**未显式设置**。`ENG/docs/perf.md` 仅给出一段待核实的建议片段，并注明 7-DOF 臂 @100 Hz 时 CPU 求解 3–8 ms vs GPU <1 ms。

#### 2.2.4 关节、驱动与抓取

**两层 PD 授权（本仓最容易搞错的机制）** `[CODE]` `ENG/config/physics_params.yaml` 头部长注释：

| | **Layer 1 — `usd_drive_api`** | **Layer 2 — `articulation_view_runtime`** |
|---|---|---|
| 写到哪 | `UsdPhysics.DriveAPI` 属性 → `robot.usda` | `ArticulationView.set_dof_stiffnesses/dampings/max_forces` |
| 何时 | 装配/启动时，`world.reset()` **之前** | `world.reset()` **之后** |
| 持久性 | 持久，粘在 USD 资产上，跨引擎 | 仅本次运行 |
| 谁能读到 | 任何解析 stage 的消费者（PhysX USD parser、Newton `add_usd` → `joint_target_ke/kd` → MJCF `actuator gainprm`） | PhysX、`isaac_newton`（tensor setter） |
| 谁读不到 | — | **newton-standalone 完全读不到**（从不实例化 `ArticulationView`） |
| 独有能力 | 关节限位、`physxJoint:armature`、`PhysxMimicJointAPI:*:naturalFrequency` | 运行时权威（存在 `ArticulationRootAPI` 时覆盖 Layer 1） |

两层都必须存在的两个具体故障（`ENG/docs/engines.md`）：

1. **PhysX 启动种子** — `World.reset()` 会跑约 5 个 init tick，无种子时 PhysX 用 URDF importer 默认值（夹爪 kp=625、kd=0），夹爪**下垂约 80 ms**
2. **Newton actuator 存在性种子** — Newton USD importer 在 `ModelBuilder.finalize()` 依 `stiffness/damping` 决定是否分配 POSITION actuator；`stiffness=0, damping=0` 会落入 `EFFORT` 模式 → **没有位置 actuator** → `apply_action` 的 `joint_target_pos` 无处施力。URDF→USD 转换会把夹爪 mimic follower 留在 `stiffness=0`，故需 Newton-only 的 DriveAPI 种子

**增益表（Layer 1）** `[CODE]` 单位为 PhysX 单位（旋转 N/rad、N·s/rad）：

| 关节类 | stiffness | damping | max_force | `dof_frictionloss` | `armature` |
|---|---|---|---|---|---|
| `chassis_drive_joint`（自由滚轮） | 0.0 | 1.0e6（兜底种子） | 1.0e7 | **0.05** | **0.0** |
| `chassis_steer_joint` | 1.0e5 | 5.0e3 | 5.0e3 | 0.3 | 0.05 |
| `default_revolute`（body/arm/head） | 5.0e4 | 5.0e3 | 5.0e3 | 0.3 | 0.05 |
| `body`（torso 链，7–20 kg） | ↑ | ↑ | ↑ | 0.3 | **0.1** |
| `arm_wrist`（joint6-7，0.3–0.8 kg） | ↑ | ↑ | ↑ | 0.3 | **0.02** |
| `default_prismatic` | 5.0e4 | 5.0e3 | **5.0e4** | — | — |
| `gripper` master | **2000.0** | **200.0** | 0.0（保留 URDF `<limit effort>`） | 0.3 | 0.1 |

被动关节物理采用 x2_31dof_hand 约定：统一 `armature≈0.03 / frictionloss=0.3 / damping=0`。心智模型是"纯力矩"——actuator 的 PD 提供恢复力，关节只加常量库仑摩擦下限（数值鲁棒性）与极小转子惯量（kp/dt² 稳定裕度）；**不加粘性阻尼 = 不依赖隐式速度反馈**，调参更简单。`armature` 分层理由：torso link 重，0.1 转子惯量 <1% M_eff 不可见；wrist link 轻，0.1 会把等效惯量抬高 30–100% 并可见地拖慢跟踪，故取 0.02（"能在 1 ms 子步上平滑 stick-slip 的最小值"）。`chassis_drive` 的两个例外：`frictionloss=0.05`（fl=0.3 会造成约 0.03 rad/s 速度死区）、`armature=0`（否则底盘"发黏"）。

**夹爪主从与 mimic** `[CODE]` master 识别仅靠 `HasAPI(DriveAPI)`——Robotiq 风格拓扑里它是唯一带 drive 的关节，故该判据对 2F-85 / 2F-140 及任意"一主 N 从"夹爪通用；仅当机器人由 URDF 构建时施加，手写 legacy USD 保留手工调参。

master 增益的调参史（值得完整保留）：`1e4/10`（参考 G2 MJCF）静态抓取可用，但与 mimic 等式约束在臂运动下**耦合恶化**——高 PD 与等式求解器相互作用并放大 follower 摆动（0.5 rad / 0.5 Hz 臂扫下 follower 幅值 0.06 rad、漂移 0.01 rad）。扫参最优点 `2e3/200`：follower 漂移降 **30×**（0.01 → 0.0003 rad）、幅值降约 33%，且**不损失夹持力**——在 0.025 rad 指令误差处 master 就撞上 `actfrcrange=±50 N·m`，峰值力矩与旧配置相同。

三套 mimic 实现：`isaac_physx` 用 `PhysxMimicJointAPI`（C++ 求解器层刚性约束，`naturalFrequency=0`/`dampingRatio=0` 即刚性）；`isaac_newton` 与 `newton` 共享软件广播 `engine/_mimic.expand_targets`；mjwarp 路径额外用 MuJoCo 等式约束（`mimic_eq_solref: [-10000, -100]`，负值 = 刚性直接模式；注释警告**比 `[-50000, -500]` 更硬会在典型 2 ms 子步下炸**）。follower 两层增益均 kp=0/kd=0（由约束驱动而非 PD 驱动）。

> ✅ **没有作弊式抓取** `[CODE]`（grep 确认）：**不存在 adhesion / sticky-grasp / 吸附约束 / 抓取时动态创建 fixed joint**。抓取完全依赖接触摩擦 + SDF 碰撞 + 夹爪力矩，这是一个正面的保真度事实。

**三种控制律** `[CODE]` `ENG/docs/engines.md`：

| | `isaac_physx` | `isaac_newton` | `newton` |
|---|---|---|---|
| 控制律 | PhysX 力模式 PD `τ = kp·(q⋆−q) + kd·(q̇⋆−q̇)` | Newton wrapper **加速度模式** PD | **速度注入** `joint_qd ← q⋆−q` |
| 指令路径 | `articulation.apply_action(ArticulationAction(...))` | 同调用面，`_view_input` 包成 `wp.array` | `_target_joint_pos.assign(numpy)`（GPU 原地 memcpy） |

> ⚠️ **`newton` 后端的速度注入是运动学式的**：直接把关节速度设为位置误差，不通过力/力矩。该后端**不产生真实关节力矩**，接触力的物理性也随之改变。选它做 RL 训练或力控研究前必须知道这一点。

#### 2.2.5 可变形体（布料）

`[CODE]` `ENG/scripts/engine/newton/cloth.py`、`engine_base.py:134-152`

**仅 `physics_engine:=newton` 支持**（`isaac_physx` / `isaac_newton` 均 not supported）。默认参数：

```python
_PARTICLE_RADIUS = 0.008   # 0.8 cm
_TRI_KE  = 1e4             # 面内拉伸
_TRI_KA  = 1e4             # 面积保持
_TRI_KD  = 1.5e-6          # 面内阻尼
_EDGE_KE = 5.0             # 弯曲刚度
_DENSITY = 0.02
```

经 `builder.add_cloth_mesh(...)` 注入，逐项可被 sidecar 条目覆盖。**单位强制检查**：布料 USD 必须按米制 author（可用 `tools/usd/bake_cloth_meters.py` 预烘），加载后记录 `bbox(m)`，**超过 5 m 直接告警**——防止把厘米制资产误当米制加载。存在布料条目时 `physics_solver` 必须是 `{vbd, xpbd, style3d}` 之一；连同 AVBD，实际布料求解器有四种：**VBD（默认）、XPBD、Style3D、AVBD**。

Fabric 回写：`isaac_physx` / `isaac_newton` 由 wrapper extension 自动完成；`newton` 每 tick 用专用 kernel 手工回写 cloth points + body transforms（对应 `perf.md` 中 `Extras` 字段"对 newton 非零"）。

#### 2.2.6 确定性、并行与 Warp

`[CODE]`

- newton-standalone 全程 **NVIDIA Warp** 数组；`wp.ScopedCapture` / `wp.capture_launch` 做 CUDA graph 捕获重放，`wp.record_event` 做跨流握手
- 主机侧 pinned-host `AsyncMirror` 双缓冲把 GPU 状态异步搬到 CPU，避免 publish 阻塞物理线程
- OVRtx inline visualizer 用独立 Python 线程 + 独立 CUDA stream；物理线程每步只 `record` 一个 `physics_step_event`，渲染线程的 Warp stream 在每帧同步前 wait 该 event —— **物理线程从不 CPU 阻塞**，物理与渲染 GPU 工作重叠（`ENG/docs/ovrtx_sync.md`）
- mjwarp 约束预分配：`_DEFAULT_NJMAX = 1024`（约束 Jacobian 最大行数 = 接触 + 限位 + 等式）、`_DEFAULT_NCONMAX = 512`（最大活跃接触对）。超市场景峰值 njmax 约 750；**欠分配会刷 `nefc overflow` / `nconmax overflow`**
- 积分器：`implicitfast`（在超过标称阻尼比时仍稳定）
- **确定性保证**：`未提及`（无 seed 固定、无跨运行 bit-wise 复现声明）
- **多环境并行**：RT Engine 单环境；Benchmark 用共享相机 teleport；RLinf 用 N 进程 MuJoCo + GridCloner。**没有 GPU 向量化多环境物理**（无 Isaac Lab 风格的 `num_envs` 张量化）

#### 2.2.7 性能诊断

`[CODE]` `ENG/docs/perf.md` — 引擎每约 1 秒打一次性能摘要（`stats_interval_s` 控制）：

| 症状 | 根因 |
|---|---|
| `Solver mean` >5 ms @100 Hz | 求解器 CPU/GPU 饱和 |
| `render-tick step mean` ≫ `non-render step mean` | RTX 帧预算溢出 |
| `Spin mean` ≈ 0 且 `Budget worst` >100% 且频繁 overrun | 循环撑不住墙钟 |
| `Publish mean` >1 ms | ROS 序列化开销 |
| `GPU-sync max` >2 ms | 显式 GPU 同步阻塞 CPU（仅 `GENIESIM_RENDER_SYNC=1` 时非零） |
| `Interval jitter (std)` >0.5 ms 而 Solver/Spin 正常 | OS 调度抢占 |
| `skipped(budget)` 高而 `skipped(period)` 低 | `render_safety_ms` 过紧 |

`Solver` 字段是**后端无关**的 `sim.step(dt)` 耗时，可直接跨三引擎比较。

### 2.3 渲染技术

#### 2.3.1 OVRtx：脱离 Kit 的 C-API RTX 渲染库

`[CODE]` `ENG/docs/ovrtx_sync.md`

**OVRtx = NVIDIA 独立的 C-API RTX 渲染库**，不依赖 Omniverse Kit。版本**硬钉 0.3.x**（`OVRTX_VERSION_MAJOR=0, MINOR=3`），代码用 `RuntimeError` 做版本守卫。

两条**运行时互斥**的使用臂：

1. **跨进程** — `genie_sim_render` 独立 ROS 2 节点（`RENDER/src/render_node.cpp`），由 `/tf_render` 驱动。位姿路径：Newton GPU → 物理 CPU → `tf2_msgs::TFMessage` 序列化 → ROS 中间件 → 反序列化 → `ovrtx_set_xform_mat`（内部 `ovrtx_write_attribute` + `OVRTX_DATA_ACCESS_SYNC`，**每次调用一次 CPU→GPU 拷贝**）。这个成本是跨进程设计固有的。
2. **进程内** — `physics_engine_visualizer:=ovrtx`（`InlineOvrtxVisualizer`）。**零拷贝**：Warp kernel 经 `binding.map(device=Device.CUDA)` 直接写进 OVRtx 内部 Fabric buffer。

两条臂不互相替代：newton-standalone 的 launcher 都保持 `launcher.renders: []`，是 inline 路径的天然归属；跨进程臂保留给需要 GPU 隔离 / 独立故障域 / 一个渲染器驱动多物理源的场景。

变换约定：属性名 `"omni:xform"`，语义 `Semantic.XFORM_MAT4x4`，**USD 行向量约定**（平移在最后一行 `[3][0..2]`），**仅 float64**。

#### 2.3.2 渲染模式（两处设定，不要混淆）

`[CODE]`

**(a) USDA 里硬编码**（`ENG/scripts/assemble_scene.py:683,709`）：

```python
rp_prim.CreateAttribute("omni:rtx:rendermode",
                        Sdf.ValueTypeNames.Token).Set("RealTimePathTracing")
```

即装配出的 `render_layer.usda` 中 RenderProduct 一律为 `RealTimePathTracing`。

**(b) Kit 侧启动参数映射**（`ENG/scripts/kit/bootstrap.py:47-53`）：

```python
RENDER_MODE_MAP = {
    "raster":    ("rtx", "RaytracedLighting"),    # 默认
    "pathtrace": ("rtx", "RealTimePathTracing"),
    "offline":   ("rtx", "PathTracing"),
}
```

`_resolve_render_mode` 对**无法识别的值回落到 `raster` 而不抛异常**（注释：避免畸形启动参数崩掉 bringup）。

三种模式语义：`RaytracedLighting`（光栅化 + 光追直接光照，最快，默认）· `RealTimePathTracing`（实时路径追踪，需多 subframe 收敛，Benchmark 栈 `rt_subframes=8`）· `PathTracing`（离线全路径追踪，最慢最准）。

> ⚠️ 所有 newton launcher 的 `render_mode: raster` 都带注释说明**"仅对 kit visualizer 有效；newton GL / ovrtx 路径忽略此项"**。OVRtx 路径的模式由 USDA 里的 `omni:rtx:rendermode` 决定，不由启动参数决定。

渲染耗时实测（`ENG/docs/perf.md`）：`Render: mean=28.40 max=45.20 ms (47 of 500 ticks rendered)`；`render-tick mean=34.20 ms` vs `non-render mean=6.90 ms`——渲染 tick 的总步耗时约为非渲染 tick 的 5 倍。

#### 2.3.3 抗锯齿 / 降噪 / DLSS

**`未提及`** `[CODE]`（grep 确认）：OVRtx 路径上**没有**任何 AA / denoiser / DLSS / TAA 配置。存在旋钮的仅三处：资产里烘进去的 viewport 设置（不影响 render product）、Kit schema 中声明但未使用的键、以及 Benchmark 栈的 `rt_subframes`（默认 8）。**路径追踪噪声靠 subframe 累积压制，而非 AI denoiser。**

#### 2.3.4 材质与光照

`[CODE]`

- **OVRtx 路径无 MDL**：使用 `UsdPreviewSurface`，且实际只消费 **roughness + metallic** 两个通道。无 MDL、无 subsurface、无 clearcoat、无各向异性
- 光照：兜底场景仅单个 `UsdLux.DomeLight`（`intensity=1000.0`）；真实场景的灯光来自场景 USD 自身
- 阴影 / 全局光照由 RTX 模式隐含决定，无独立配置

#### 2.3.5 3DGS Real2Sim 重建流水线

`[CODE]` `source/scene_reconstruction/`

```
MetaCam 手持激光扫描仪   (RGB 全景 + LiDAR 点云)
   ↓ CloudCompare        (点云法向估计)
   ↓ HLoc                (SuperPoint 特征 + LightGlue 匹配)
   ↓ colmap-pcd          (LiDAR 约束的 SfM —— 用点云钉死位姿尺度)
   ↓ gsplat              (3D Gaussian Splatting 训练)
   ↓ Difix3D+            (novel-view 伪影清理)
   ↓ PGSR               (Planar-Gaussian 表面重建)
```

机制要点：

- **LiDAR 约束的 SfM 是关键** — 纯视觉 SfM 只能恢复相对尺度，机器人仿真需要**米制绝对尺度**；`colmap-pcd` 用激光点云把尺度钉死，这是"重建结果可直接用于机器人"的前提
- **Difix3D+ 处理 3DGS 的固有弱点** — 训练视角外的新视角会出现针状/雾状伪影，用扩散式清理
- **PGSR 把高斯变表面** — 3DGS 本身是体渲染基元，没有几何表面、无法参与碰撞；PGSR 用平面约束高斯做表面重建，是通往 mesh 的一步

> ⚠️ **未实现的 handoff** `[CODE]`（grep 确认）：README 声称重建产物会转成 USD 供 Isaac Sim 使用，但仓库内**不存在 mesh 提取、TSDF、USD writer 或 `gs-asset/` 加载器**——这个 handoff 在仓库之外。另有一个死参数：`batch_rec.py --max_depth` 声明后从未被引用。

#### 2.3.6 域随机化（11 种机制）

`[CODE]` `BENCH/utils/generalization_utils.py`、`BENCH/benchmark/envs/base_env.py`、`DC/server/ros_publisher/camera_noiser.py`

已实现：① 物体位置 ② 物体朝向 ③ 干扰物增删 ④ 同类别物体资产替换 ⑤ 材质/纹理 ⑥ 背景/场景 USD ⑦ 光照（强度/方向/HDRI）⑧ 相机**外参** ⑨ 机器人初始位姿 ⑩ 语言指令改写 ⑪ 图像质量（5 种 RGB 噪声，见 §2.4.8）。

grep 确认的**缺失项**（对 sim2real 判断很重要）：相机**内参**随机化 · 质量/摩擦/恢复系数随机化（五类接触同参且不随机）· 延迟/抖动随机化 · 执行器噪声/增益随机化 · 重力/空气阻力随机化——均为 `未提及`。

> ⚠️ 这与论文 Robust 套件结果高度呼应：**语言与纹理扰动退化 ≤0.061，而机器人位姿扰动 Δ≈−0.258、相机位置 Δ≈−0.256**——恰是"已随机化的维度鲁棒、几何/视点维度脆弱"。而内参与动力学参数正是**未被随机化**的两块。

#### 2.3.7 首帧与预热

`[CODE]` OVRtx / RTX 首帧需要 shader 编译预热；装配后调用顺序为 `_build` → `_warmup` → `_setup_usdrt` → `configure_viewport_for_debug(render_mode=...)`。不预热会在第一帧付数秒的 shader 编译代价。

### 2.4 传感器仿真（详细）

> 本节为用户明确要求的重点章节。所有结论均为 `[CODE]`（官方文档站为纯 JS SPA，无正文可抓）。

三套栈的传感器实现路径完全不同，不可混谈：

| 栈 | 渲染 | 传感器机制 | 输出 |
|---|---|---|---|
| **RT Engine** | OVRtx（Kit-free C-API） | USD RenderProduct + RenderVar，C++ 直接取帧 | ROS 2 topics |
| **Benchmark / Data-collection** | Kit RTX 路径追踪 | Omniverse Replicator annotator/writer + OmniGraph | ROS 2 + gRPC + HTTP |
| **RLinf** | 单 Isaac Sim 进程 + GridCloner | 共享相机 annotator | 共享内存帧 |

#### 2.4.1 两套并行机制（核心认知）

Benchmark/Data-collection 栈里传感器数据的产生有**两条并行且不可互换的机制**，这是排查"话题不出图"的第一现场：

| | 机制 A：Replicator annotator / writer | 机制 B：OmniGraph 节点图 |
|---|---|---|
| 入口 | `rep.create.render_product(prim_path, resolution)` + `rep.writers.get(name)` 或 `AnnotatorRegistry.get_annotator(name)` | `og.Controller.edit(graph_path, {...})` 构图 |
| 数据流 | RTX AOV → RenderVar → writer 直接发 ROS，或 `annotator.get_data(device="cuda")` 手取 | RTX AOV / 物理读数 → OG 节点 → `ROS2Publish*` 节点 |
| 限频门控节点 | `<RenderVar>IsaacSimulationGate` | 显式插入的 `IsaacSimulationGate`，或 LiDAR 的 `PostProcessDispatchIsaacSimulationGate` |
| 用于 | RGB、深度、点云、2D/3D bbox | 语义分割、IMU、LiDAR ROS 2 发布 |

**限频统一做法** `[CODE]`：不改渲染帧率，而是把 gate 节点的 `inputs:step` 设为跳帧数——

```python
og.Controller.attribute(gate_path + ".inputs:step").set(step_size)
```

- 相机：`frameSkipCount = freq - 1`
- LiDAR：`step_size = int(60 / freq)` —— 隐含渲染基准 **60 Hz**
- IMU：`step = math.floor(6.0 / approx_freq)` —— **注意是 6.0 而非 60.0**，代码中无注释解释，疑似笔误或另一套基准，是值得复核的点

> ⚠️ 两类 gate 的命名规则不同（`<rv>IsaacSimulationGate` vs `PostProcessDispatchIsaacSimulationGate`），是最容易踩的坑。

#### 2.4.2 内参：自研的 USD 光学参数 ↔ pinhole 双向换算

这是全仓最重要的传感器实现细节之一。仓库**明确注释 Isaac Sim 自带的 `read_camera_info` 不可用**——`isaacsim.ros2.bridge` 的内置节点无法正确计算 cx / cy，因此自己实现了两个方向的换算。

**方向 1：USD → pinhole 内参（运行时发 `camera_info`）** `DC/server/ros_publisher/camera_info.py`：

```python
fx = width  * focalLength / horizontalAperture
fy = height * focalLength / verticalAperture
cx = width  * 0.5 + camera_info["horizontalOffset"] * width  / horizontalAperture
cy = height * 0.5 + camera_info["verticalOffset"]   * height / verticalAperture

camera_info["k"] = np.asarray([[fx, 0.0, cx], [0.0, fy, cy], [0.0, 0.0, 1.0]])
camera_info["r"] = np.eye(3)
camera_info["p"] = np.concatenate((camera_info["k"], np.zeros([3, 1])), axis=1)
```

机制解释：USD `UsdGeom.Camera` 用**物理光学量**描述相机（`focalLength` 焦距、`horizontalAperture` 传感器宽、`horizontalOffset` 主点偏移，单位为 USD 的 tenths-of-scene-unit），而 pinhole 内参用**像素**描述；两者通过"像素密度 = 分辨率 / 传感器物理尺寸"换算。`cx/cy` 之所以是内置实现的痛点：必须先把 `horizontalOffset`（物理长度）除以 aperture 归一化、再乘分辨率，Isaac 内置节点漏了这一步，导致主点永远被钉在图像中心。

`r` 为单位矩阵、`p = [K | 0]` 说明**未建模双目基线/立体校正**——每个相机都是独立单目，无 `Tx` 项。

**方向 2：pinhole 内参 → USD（场景装配时）** `ENG/scripts/assemble_scene.py:627-647`：

```python
h_aperture   = 20.955                   # Isaac Sim 默认值，硬钉
focal_length = fx * h_aperture / width
v_aperture   = h_aperture * (h / w) * (fx / fy)
clippingRange = (min_range, max_range)  # 默认 0.01 / 10000.0
```

`h_aperture` 固定为 20.955 后只剩一个自由度（`focalLength`）来匹配 `fx`，**`fy` 通过反解 `v_aperture` 匹配**。公式中保留 `fx/fy` 项保证了非方形像素（`fx ≠ fy`）也能被 USD 相机精确表达——这是常见实现会丢失的信息（很多实现直接令 `v_aperture = h_aperture·h/w`，等价于强制 `fx == fy`）。

#### 2.4.3 两套共存的畸变模型

`[CODE]` 仓库同时存在**两套互不相同的畸变表达**，取决于走哪条渲染路径：

**(a) `plumb_bob` / OpenCV fisheye（ROS 侧发布用）** — `DC/server/ros_publisher/camera_info.py`
默认 `physicalDistortionModel = "plumb_bob"`，系数默认 `np.zeros((1, 4))`；当 `cameraProjectionType != "pinhole"` 时填充 **19 槽 `cameraFisheyeParams`**：`fthetaWidth/Height/Cx/Cy/MaxFov`、`fthetaPolyA..F`（f-theta 多项式 6 项）、`p0`、`p1`、`s0..s3`、`fisheyeResolutionBudget`、`fisheyeFrontFaceResolutionScale`。即 pinhole 走 5 系数 `plumb_bob`（k1,k2,p1,p2,k3），鱼眼走 f-theta 多项式 + `equidistant`/`opencvFisheye` 4 系数（k1..k4）。

**(b) RTX 镜头畸变 schema（渲染器侧真正弯曲光线）** — `ENG/scripts/assemble_scene.py:69-91`
`OmniLensDistortionOpenCvFisheyeAPI` + `omni:lensdistortion:opencvFisheye:fx/fy/cx/cy/k1/k2/k3/k4/imageSize`。

> ⚠️ **关键机制差异**：(a) 只是把畸变系数**写进 `camera_info` 消息**，图像本身仍是无畸变的针孔投影——下游若按 `camera_info` 去畸变会引入错误；(b) 才是让 RTX 渲染器**真实按鱼眼模型投射光线**。两者用途不同，必须对齐使用，否则 sim2real 时标定链断裂。

#### 2.4.4 相机配置字段（两套 schema）

**RT Engine 场景 YAML**（`BRINGUP/config/scene_*.yaml`）：

```yaml
cameras:
  - prim_path: <USD prim 绝对路径>
    frame_id: <ROS TF frame>
    topic:
      rgb:   <topic 前缀>
      depth: <topic 前缀；留空则不生成深度 RenderVar>
    sensor:   { width, height, freq, min_range, max_range }
    intrinsic: { cx, cy, fx, fy, k1, k2, p1, p2, k3 }
    extrinsic: { xyz: [x,y,z], wxyz: [w,x,y,z] }
lidars: []
```

关键机制 `[CODE]` `assemble_scene.py:676-678`：**深度 RenderVar `DistanceToImagePlaneSD` 仅当 `topic.depth` 非空时才被 author 到 USD**。即深度不是"永远算好待取"，而是按配置条件生成——省的是 RTX AOV 的显存与带宽。

**Benchmark/Data-collection 机器人配置 JSON**（G2 五相机）：

| 相机 | 分辨率 | 挂载 |
|---|---|---|
| `head_front_Camera` | 640 × 400 | 头部 |
| `head_left_Camera` | 1920 × 1536 | 头部 |
| `head_right_Camera` | 1920 × 1536 | 头部 |
| `Left_Camera` | 1280 × 1056 | `gripper_l_base_link` |
| `Right_Camera` | 1280 × 1056 | `gripper_r_base_link` |

同文件另含 7-DOF 双臂、omnipicker 夹爪（`max_force: 10`、`opened_positions: [0.95, 0.95]`、`closed_velocities: [-5, -5]`）、cuRobo 运动规划配置引用、20 个 `lock_joints`。注意这些分辨率的**非方形宽高比**（1920×1536 = 5:4、1280×1056 ≈ 1.212:1、640×400 = 8:5）——正是 §2.4.2 中 `v_aperture` 公式必须保留 `fx/fy` 项的现实原因。

#### 2.4.5 外参处理：`/tf_render` 与"局部位姿"约定

RT Engine 与渲染进程之间靠专用 topic `/tf_render` 传位姿，协议有两条非直觉约定：

1. **`child_frame_id` 是 USD prim 的绝对路径**（不是 ROS frame 名）
2. **transform 是相对"USD 直接父节点"的局部位姿**，不是 world 位姿

局部化由 `_xform_to_xyzwxyz_local` 完成，按 USD 的**行向量约定**计算 `local = world * inverse(parent_world)`。机制解释：渲染器持有的是 USD stage，写位姿必须写 `xformOp:translate` / `xformOp:orient`，而这些 op 天然相对父节点；物理侧算出的是 world 位姿，故必须先"剥掉"父链。行向量约定意味着乘法顺序与常见的列向量形式（`local = parent_world⁻¹ · world`）相反——这是移植时最容易写错的地方。

Topic 清单：`<camera_topic>/image_raw`、`<camera_topic>/depth/image_raw`（`32FC1`，单位**米**）、`<camera_topic>/camera_info`、`<node_ns>/free_cam_pose`、`/tf_render`。

Benchmark 栈的外参则来自机器人 USD 的相机 prim 自身层级（挂在 `gripper_l_base_link` 等 link 下），随 articulation 前向运动学自动更新，**无需显式外参传输**。

#### 2.4.6 RGB 相机

`[CODE]` 三种发布机制并存于 `DC/server/ros_publisher/camera.py`：

1. **Replicator writer 直发** — `rep.writers.get("ROS2PublishImage")` 绑定到 render product，帧数据不经 Python
2. **annotator 手取（噪声路径必需）** — `rep.create.render_product(...)` + `AnnotatorRegistry.get_annotator("rgb")` + `annotator.get_data(device="cuda")`，拿到 GPU 上的 `rgba8`（**4 通道**）后交给 Warp 噪声核，再手工打包 `sensor_msgs/Image` 发布
3. **OmniGraph** — `ROS2CameraHelper` 节点（语义分割走这条）

机制要点：只有走 (2) 才能在发布前介入像素，(1) 最快但不可改。**这解释了为什么噪声只加在 RGB 上——深度/点云走的是 (1)。**

AOV 名：`LdrColor`（低动态范围颜色，即 tonemap 之后的 8-bit 结果）。

#### 2.4.7 深度相机

`[CODE]`

- **AOV / RenderVar**：`DistanceToImagePlaneSD`
- **语义**：到**像平面**的垂直距离（z-depth），**不是**到光心的欧氏射线长（range）。这个区分决定了点云反投影公式 `X = (u-cx)·Z/fx`；若误当作 range 会在图像边缘产生系统性径向误差
- **编码**：`32FC1`，单位**米**，原样发布
- **内参**：与同 prim 的 RGB **共用同一套内参**（同一个 `UsdGeom.Camera`），天然对齐、无需 RGB-D 配准
- **条件生成**：仅当场景 YAML `topic.depth` 非空
- **点云**：`publish_pointcloud_from_depth` 在发布侧由深度图 + 内参反投影

> ⚠️ **已确认的死字段 `depth_scale`** `[CODE]`：从场景 YAML 读入并写进 `manifest.json`（`assemble_scene.py:1056`），但**全仓 grep 找不到任何消费者**。深度在整条渲染链上从未被缩放，始终是 float32 米制。"改 `depth_scale` 能得到毫米整型深度"的假设是错的。

> ⚠️ **深度噪声模型未实现** `[CODE]`（grep 确认）：**不存在任何深度噪声模型**——没有立体匹配失效建模、没有视差量化、没有边缘飞点（flying pixels）、没有反光/透明材质失效、没有 ToF 多径、没有随距离增长的方差。仿真深度是**几何真值**。这是 sim2real 的明确缺口：真实 RealSense/ToF 深度噪声与深度平方成正比且在物体边缘剧烈失效，而仿真深度完美。

#### 2.4.8 RGB 噪声模型库（全仓唯一的传感器噪声实现）

`[CODE]` `DC/server/ros_publisher/camera_noiser.py`（371 行）

共 7 个 Warp kernel，文件 docstring 明确标注 #6 SENSOR NOISE 与 #7 BROWNIAN 为 **"(NOT USED)"**，即**实际启用 5 种**：

| 噪声 | 数学形式 | 采样范围 | 物理对应 |
|---|---|---|---|
| gaussian | `I + σ·N(0,1)`，**逐通道独立种子** | σ ~ 截断\|N(0.15, 0.08)\| ∈ [0.1, 0.4] | 读出噪声 / 热噪声 |
| salt_pepper | 以概率 p 置 0 或 255 | p ~ U(0.002, 0.02)，salt = pepper | 坏点 / 传输误码 |
| poisson | `I + N(0,1)·√I·scale`（高斯近似） | scale ~ U(0.05, 0.3) | 光子散粒噪声 |
| speckle | `I·(1 + σ·N(0,1))`（乘性） | σ ~ U(0.05, 0.2) | 相干成像斑点 |
| quantization | `levels = 2^bits; step = 255/(levels−1)` | bits ~ randint(4, 7)，即 4/5/6 bit | 位深压缩 / 弱 ISP |
| ~~sensor noise~~ | — | — | **NOT USED** |
| ~~brownian~~ | — | — | **NOT USED** |

两个实现细节值得注意 `[CODE]`：

- **gaussian 逐通道独立种子** — `pixel_id + dim_i*dim_j*{0,1,2}`，保证 R/G/B 三通道噪声互相独立（若共用种子会得到灰度噪声，视觉上完全不同）
- **poisson 用高斯近似** — 代码注释自陈 "valid for large counts"。在暗部（低光子数）该近似不成立，真实散粒噪声在暗区是明显偏斜的泊松分布，即**暗场景下噪声保真度有限**

全部核跑在 GPU（Warp），输入是 `annotator.get_data(device="cuda")` 的 `rgba8`，无 GPU→CPU 往返。

#### 2.4.9 语义分割 / 标注类

`[CODE]` 语义分割走 OmniGraph：

```python
og.Controller.edit(..., {
    "isaacsim.ros2.bridge.ROS2CameraHelper": {
        "inputs:type": "semantic_segmentation",
        "inputs:enableSemanticLabels": True,
        "inputs:frameSkipCount": freq - 1,
    }
})
```

**实例分割（instance segmentation）：`未提及`** —— 全仓 grep 无 `instance_segmentation` / `instance_id_segmentation` annotator 使用；只有语义（类别）分割。

**Bounding box**：`publish_bbox2d`（loose 与 tight 两种）、`publish_bbox3d`，均走 Replicator writer。

**gRPC 语义接口**（`sim_camera_service.proto`）整个服务只有一个 RPC：

```
SimCameraService.get_semantic_data(GetSemanticRequest{serial_no})
    → GetSemanticResponse{ serial_no,
          SemanticMask{ name, bytes data },
          repeated SemanticLabel{ label_id, label_name } }
```

即 gRPC 只承载"按需拉一次语义 mask + 标签表"，图像/深度流不走 gRPC。

#### 2.4.10 LiDAR — de-skew 机制（本仓最具技术含量的传感器改造）

`[CODE]` `ENG/scripts/assemble_scene.py:720-800`。README 在 v3.2.0 release log 里把这个特性叫 **"de-skewed rotary lidar"**，实现是四个 USD 属性 + 一个时间钳制：

```python
ref_prim.CreateAttribute("omni:sensor:Core:elementsCoordsType", ...).Set("CARTESIAN")
ref_prim.CreateAttribute("omni:sensor:Core:partialOutputs",     ...).Set(False)
ref_prim.CreateAttribute("omni:sensor:Core:instantLidar",       ...).Set(True)
ref_prim.CreateAttribute("omni:sensor:Core:skipDroppingInvalidPoints", ...).Set(False)
```

**机制拆解**：

1. RTX LiDAR 默认按**真实旋转扫描**建模：一圈 360° 摊到若干渲染步上，每束光线在**不同时刻、不同机器人位姿**下投射。这物理正确（真机就是这样），但机器人运动时输出点云会**扭曲**（直墙变斜墙），因为一帧点云里混了多个位姿
2. `instantLidar=True` **移除时间维度**：整圈 360° 在**单一冻结位姿**下一次性投射完。代价是丢失运动畸变（真机存在），收益是点云与"单位姿光线投射"（注释里对标 `rmagine`）严格一致，可复现、可比对、下游 SLAM/配准不需去畸变
3. `partialOutputs=False`：不吐半圈的部分结果，只在整帧完成时输出——与 (2) 配套，否则下游会收到不完整环
4. `skipDroppingInvalidPoints=False`：保留无效点（未命中射线），点云**保持固定长度/固定角度栅格**，下游可按索引直接反查方位角，无需解析每点角度
5. `elementsCoordsType="CARTESIAN"`：直接输出 xyz 而非距离-方位-俯仰球坐标，省下游一次转换

**`fireTimeNs` 钳制** `[CODE]`：

```python
ft_scale = min(1.0, 26000.0 / ft_max)
```

机制：OVRtx 的发射时间窗约 **27.7 µs**，若 LiDAR profile 声明的最大发射时刻 `ft_max` 超出该窗口，渲染器会**返回零点**（静默失效）。故把所有 `fireTimeNs` 等比压缩到 26000 ns 以内。这是纯工程 workaround，也是移植 LiDAR profile 时必须保留的一步。

**PointCloud RenderVar 通道**：`["Coordinates", "Intensity", "Counts", "TimeOffsetNs", "Flags"]`。注意 `TimeOffsetNs` 通道仍存在（de-skew 的原始信息），但在 `instantLidar=True` 下其内容退化。

**ROS 2 发布**：writer 为 `RtxLidarROS2PublishPointCloudBuffer`（点云）与 `RtxLidarROS2PublishLaserScan`（2D 扫描）；gate 名 `PostProcessDispatchIsaacSimulationGate`（**与相机的 `<rv>IsaacSimulationGate` 不同**）；限频 `step_size = int(60 / freq)`。

**LiDAR 噪声模型：`未提及`** —— 无测距噪声、无强度衰减模型、无雨雾/粉尘建模、无多次回波。

#### 2.4.11 IMU

`[CODE]` OmniGraph 建在 `/World/ImuActionGraph`，`pipeline_stage = GRAPH_PIPELINE_STAGE_SIMULATION`（在物理步内执行，而非渲染后）。节点链：

```
OnPlaybackTick → IsaacSimulationGate(step) → IsaacReadIMU
                     outputs: angVel, linAcc, orientation → ROS2PublishImu
```

- `IsaacReadIMU` 从物理引擎刚体状态**解析求导**得到角速度与线加速度（含重力项），不做数值差分抖动
- 挂在 `GRAPH_PIPELINE_STAGE_SIMULATION` 意味着 IMU 采样与**物理步**对齐而非渲染帧——这是 IMU 与相机**天然不同步**的根源
- 限频 `step = math.floor(6.0 / approx_freq)`（前述 6.0 vs 60.0 疑点）

**IMU 噪声模型：`未提及`** —— 无加计/陀螺 bias、无 bias random walk、无 scale factor error、无轴间不正交、无温度漂移、无量化。输出是物理真值。对需要 VIO / 状态估计的下游任务是显著的 sim2real 缺口。

#### 2.4.12 本体感知（proprioception）

`[CODE]`

- 频率 **100 Hz**（与默认 `physics_hz = 100.0` 一致）
- 内容：`/joint_states`（position / velocity / effort）+ body TF + odom，合并在 `_publish_tick` 内
- **存在一拍延迟**：发布在物理步之后，读到的是本步结束状态，控制器看到的是 t−1 的观测
- **effort 为 14 维**（双 7-DOF 臂）
- ⚠️ **`isaac_newton` 时 `snapshot_joint_states` 返回全零** `[CODE]` `ENG/docs/engines.md`：Newton wrapper 不会把关节状态回写到 PhysX 所写的 USD `state:angular:physics:position` 属性。这是真实功能缺口，不是配置问题

各引擎的关节状态读取源：

| | `isaac_physx` | `isaac_newton` | `newton` |
|---|---|---|---|
| 关节状态源 | USD 属性（PhysX 每 tick 写） | `articulation.get_joint_positions()` 经 `_view_readback` | 直读 `state_0.joint_q`（warp） |
| body 变换 | `_xform_to_xyzwxyz_local` 出的 USD 局部位姿 | 同 PhysX | 世界系 `state_0.body_q`，布局 `(x,y,z,qw,qx,qy,qz)` |
| 张量格式 | numpy / torch | 仅 `wp.array`（`_view_input` 做转换） | 全程 warp array |

**触觉传感器（tactile）：`未提及`** —— 全仓 grep 无触觉实现。
**独立力/力矩传感器（6 轴 F/T）：`未提及`** —— 无对应 prim 或读数接口，只有关节 effort。

#### 2.4.13 多环境并行：共享相机 + teleport 技巧

`[CODE]` `BENCH/app/controllers/api_core.py:500-600`

Benchmark 栈要在一个 Isaac Sim 进程里评测 N 个并行环境，但**每个环境各建一套 render product 会爆显存**。实现的技巧是：

1. 在 `_SHARED_CAM_ROOT` 下建 **N 个共享相机**（N = 每 env 的相机数，而非 env 数），每个配 `rep.create.render_product` + `"rgb"` annotator（外加 `"distance_to_image_plane"`，除非 prim 相对路径含 `"Fisheye"` 或 `"Top"`）
2. 把**所有 env 里的原生 `UsdGeom.Camera` prim 全部 `SetActive(False)`** —— 它们退化为纯粹的"位姿标记"
3. 取某个 env 的观测时 `_teleport_shared_cams_to_env`：读 `XformCache.GetLocalToWorldTransform(native_prim)` → 写 shared_cam 的 `xformOp:translate` / `xformOp:orient`
4. `render_once(n_subframes)`：

```python
rep.orchestrator.step(rt_subframes=n, pause_timeline=False,
                      delta_time=0.0, wait_for_render=True)
```

默认 `shared_cam_render_frames = 8`。

机制解释：`delta_time=0.0` + `pause_timeline=False` 表示**渲染不推进物理时间**——纯粹为了让路径追踪器在新位姿下累积 8 个 subframe 收敛（路径追踪是随机采样，单帧噪声大）。`wait_for_render=True` 强制 CPU 等 GPU，保证 annotator 拿到的是本次位姿的结果而非上一帧。

代价：N 个 env 的观测是**串行**取的（teleport → render → 取帧 → 下一个 env），渲染吞吐随 env 数线性下降。这也是 RLinf 栈选择 GridCloner（把 N 份场景摊在网格里一次渲染）而非 teleport 的原因。

**RLinf 栈的传输** `[CODE]`：ONE Isaac Sim 进程为所有并行环境渲染，GridCloner 把场景复制 N 份成网格布局，每个 clone 订阅 `/env_i/tf_render` 更新 body 位姿，逐 clone 抓帧后经共享内存返回。`shm_layout.py`：`NUM_CAMS = 2`；帧共享内存 `4 + num_envs*num_cams*H*W*3` 字节（**3 通道，无 alpha**）；per-env 控制段含 `state_counter`、`reset_flag`、states、actions、`info_buf`（body 位姿，`BODY_POSE_DIM = 7`）、`mujoco_phase`、`steps_per_step`；全局 step 段含 `step_phase`、`reset_mask`、`actions_all` 及输出 `rewards / terminated / truncated / elapsed_steps / episode_returns / success_once` + `info_body_poses`；`EE_STATE_DIM = 24`。

#### 2.4.14 时序、同步与帧率汇总

`[CODE]`

| 量 | 值 |
|---|---|
| 默认物理频率 | 100 Hz（`physics_hz: float = 100.0`） |
| 默认渲染频率 | 30 Hz（`render_target_hz=30.0`；`render_hz=0.0` 为"未提供"哨兵） |
| 各 launcher 实测 | `newton_mjwarp` / `ovrtx_isaac_newton` 100/30 Hz；`newton_avbd` / `fsvbd` 60/10 Hz；`newton_mjvbd` 60/40 Hz；`newton_mjxpbd` 60/30 Hz |
| LiDAR 限频基准 | 60 Hz（`int(60/freq)`） |
| IMU 限频基准 | 6.0（`floor(6.0/freq)`，疑点） |
| 本体感知 | 100 Hz，滞后一拍 |

**渲染预算削减机制** `[CODE]` `ENG/docs/perf.md`：调度器统计区分 `skipped(period)`（还没到渲染时刻）与 `skipped(budget)`（预算不足主动丢帧以保物理实时性）。即**渲染帧率不保证**——高负载下相机帧会被丢，而物理步不会。这意味着**相机时间戳间隔在仿真中是非均匀的**，下游若假设固定帧间隔会出错。

**跨传感器同步**：

- 相机之间：同一次 `rep.orchestrator.step` / 同一次 render tick 产出的多相机帧共享同一渲染时刻，属**软同步**
- 相机 vs IMU/关节：**不同步**（后者在物理 tick，前者在渲染 tick，比例 100:30 且渲染会丢帧）
- **硬件级同步触发（hardware trigger / strobe）：`未提及`**
- **卷帘快门（rolling shutter）：`未提及`**
- **曝光时间 / 运动模糊：`未提及`**（RTX 有 motion blur 能力，但仓库未配置）

**时间戳源** `[CODE]`：`/clock` 由引擎在 `_publish_tick` 与 `joint_states` / `body_tf` / `odom` 一并发布，全栈使用仿真时间。

#### 2.4.15 观测通路总图

```
                       ┌──────────────────────────────────┐
                       │  物理步 (100 Hz)                  │
                       │  PhysX / Newton / MuJoCo-Warp    │
                       └────┬────────────────────┬────────┘
        body/joint 状态      │                    │  刚体状态
                            ▼                    ▼
   ┌───────────────────────────────────┐  ┌────────────────────┐
   │ _publish_tick (100 Hz, 滞后一拍)   │  │ OmniGraph          │
   │  /clock                           │  │  SIMULATION stage  │
   │  /joint_states (pos/vel/eff 14)   │  │  IsaacReadIMU      │
   │  body TF, /odom                   │  │   → ROS2PublishImu │
   └───────────────────────────────────┘  └────────────────────┘
                            │
                            │  /tf_render (child_frame_id = USD prim 绝对路径,
                            │              transform = 相对父节点局部位姿)
                            ▼
   ┌──────────────────────────────────────────────────────────────┐
   │  渲染进程 (30 Hz 目标, 预算不足会丢帧)                         │
   │  RT Engine 路径:  OVRtx (Kit-free) ── RenderProduct/RenderVar │
   │  Benchmark 路径:  Kit RTX RealTimePathTracing                 │
   │                                                              │
   │   AOV: LdrColor ──────────────────────────┐                  │
   │        DistanceToImagePlaneSD ────────┐   │                  │
   │        PointCloud[Coordinates,        │   │                  │
   │          Intensity, Counts,           │   │                  │
   │          TimeOffsetNs, Flags] ────┐   │   │                  │
   └───────────────────────────────────┼───┼───┼──────────────────┘
        ┌──────────────────────────────┘   │   └────────────┐
        ▼                                  ▼                ▼
 ┌────────────────┐        ┌──────────────────┐  ┌────────────────────┐
 │ RtxLidar       │        │ writer 直发      │  │ 机制A-2: annotator │
 │ ROS2Publish    │        │ depth/image_raw  │  │  get_data(cuda)    │
 │ PointCloudBuf/ │        │ 32FC1 米, 无缩放 │  │    ↓               │
 │ LaserScan      │        │ (depth_scale 死) │  │  Warp 噪声核 (5种) │
 │ gate: PostProcessDispatch                 │  │    ↓  image_raw    │
 │       IsaacSimulationGate                 │  │ gate: <rv>Isaac    │
 └────────────────┘        └──────────────────┘  │  SimulationGate   │
        │                                        └────────────────────┘
        │      camera_info (自研 K/R/P, plumb_bob 或 19 槽             │
        │                   cameraFisheyeParams)                      │
        └───────────────────────┬────────────────────────────────────┘
                                ▼
              ROS 2 / gRPC(仅语义 mask) / 共享内存(RLinf)
```

#### 2.4.16 传感器建模缺口清单（全部 grep 确认）

这份清单对评估 sim2real 可行性比任何"已实现"列表都重要：

| 缺口 | 状态 | 影响 |
|---|---|---|
| 深度噪声（视差量化、边缘飞点、反光/透明失效、ToF 多径） | `未提及` | 深度为几何真值；依赖深度的策略在真机会遇到未见过的失效模式 |
| IMU 噪声（bias、bias random walk、scale factor、轴不正交） | `未提及` | IMU 为真值；VIO / 状态估计难以在仿真中训练鲁棒 |
| LiDAR 噪声（测距噪声、强度模型、雨雾、多回波） | `未提及` | 点云为几何真值 |
| 相机**内参**随机化 | `未提及`（仅外参随机化） | 论文 Robust 套件"相机位置"扰动 Δ≈−0.256 已是最大失效项之一，内参未覆盖 |
| 卷帘快门 / 曝光 / 运动模糊 | `未提及` | 快速运动下仿真图像过于干净 |
| 跨相机硬同步 / 触发 | `未提及` | 多目时间对齐是软同步 |
| 实例分割 | `未提及` | 仅语义（类别）分割 |
| 触觉传感器 | `未提及` | 接触感知任务无法仿真 |
| 独立 6 轴力/力矩传感器 | `未提及` | 仅关节 effort |
| 立体基线 / 双目校正（`p` 矩阵 `Tx` 项） | `未提及`（`p = [K\|0]`，`r = I`） | 每相机独立单目 |
| 通信延迟 / 抖动随机化 | `未提及` | 真机的观测-动作延迟未建模 |
| `depth_scale` | **死字段**（写入 manifest 无消费者） | 易误以为可配置深度单位 |
| `isaac_newton` 下关节状态 | **返回全零** | 该后端不可用于需要 proprioception 的任务 |

**已实现的传感器保真度亮点**（对照）：

1. 自研内参换算修正了 Isaac 内置节点的 cx/cy bug，且 `v_aperture` 公式保留非方形像素 `[CODE]`
2. LiDAR `instantLidar` de-skew + `fireTimeNs` 钳制，是本仓最扎实的传感器工程 `[CODE]`
3. RGB 噪声库 5 种在 GPU 上零拷贝执行，参数每 episode 重采样 `[CODE]`

---

### 2.5 论文关键思想

`[PAPER]` 《Genie Sim 3.0: A High-Fidelity Comprehensive Simulation Platform for Humanoid Robot》，arXiv:2601.02078（cs.RO，DOI 10.48550/arXiv.2601.02078）。v1 提交 2026-01-05，当前 v4，最后修订 2026-08-14。19 位作者，第一作者 Chenghao Yin；arXiv 页未显式标注机构，代码仓库归属 GitHub 组织 **AgibotTech**。

#### 四个核心特性

**(1) Genie Sim Generator — LLM 驱动的场景构建（四阶段流水线）**

```
自然语言指令
  ↓ ① Assets Index      RAG 检索资产（QWEN text-embedding-v4，2048 维；ChromaDB；约 200 ms）
  ↓ ② DSL Code Generator 生成 "Scene Language" DSL 代码
  ↓ ③ 执行 DSL          构建 USD 场景
  ↓ ④ Results Assembler 组装最终场景 + 任务定义
```

论文称可在"数分钟内生成数千个场景"。

**(2) LLM/VLM 自动评测** — **ADER**（Action Domain Evaluation Rule）规则化动作域评测判据，由 LLM 批量生成评测场景；VLM 判定任务是否完成以替代人工标注。论文自称**首次把 LLM 用于具身评测的自动化**。

**(3) 3DGS Real2Sim 场景重建** — 真实场景扫描 → 3DGS → 高保真仿真场景（代码侧流水线见 §2.3.5；**USD 落地环节代码缺失**）。

**(4) 双模式数据采集 + 解耦闭环评测** — 自动采集用 cuRobo GPU 运动规划 + GraspNet 抓取位姿标签；遥操作采集用 PICO VR 头显；闭环评测中策略与仿真器通过 **HTTP 解耦**，策略侧可独立部署。

#### 关键数字

- 资产 **5,140** 个已验证 3D 资产；数据 **10,000+ 小时**、**200+ 任务**、**100,000+ 场景**
- sim2real 一致性：论文给出 **R² = 0.931、斜率 ≈ 1.023**（仿真成功率 vs 真机成功率线性拟合）；README 另称"仿真与真机测试结果差异小于 10%"
- ⚠️ 上述数字**无法在仓库内复现**——无对应评测脚本或数据

**数据规模缩放（Table I，π0.5 微调，格式 仿真/真机）**

| 训练数据 | Select Color | Recognize Size | Grasp Targets | Organize Objects |
|---|---|---|---|---|
| 200 eps 真机 | 0.45 / 0.53 | 0.50 / 0.56 | 0.34 / 0.39 | 0.25 / 0.30 |
| 500 eps 真机 | 0.75 / 0.73 | 0.75 / 0.75 | 0.54 / 0.58 | 0.45 / 0.40 |
| 500 eps 合成 | 0.53 / 0.60 | 0.50 / 0.63 | 0.29 / 0.33 | 0.39 / 0.35 |
| 1500 eps 合成 | 0.86 / 0.85 | 0.93 / 0.94 | 0.72 / 0.71 | 0.48 / 0.60 |

结论两层：同等规模（500 eps）下**真机数据仍显著占优**（合成数据存在残余 sim2real gap）；但合成数据可廉价放量，扩到 1500 eps 后在真实世界**零样本反超全部真机基线**。论文用这点论证"用生成式流水线换数据量"的性价比，而非声称单条合成轨迹等价于真机轨迹。

**四个 benchmark 套件（Tables III–VI，模型顺序 π0.5 / ACoT-VLA / GR00T-N1.7 / π0）**

| 套件 | π0.5 | ACoT-VLA | GR00T-N1.7 | π0 |
|---|---|---|---|---|
| **Instruction**（10 任务） | 0.75 | **0.76** | 0.65 | 0.37 |
| **Robust**（5 类扰动） | 0.613 | **0.622** | 0.538 | 0.313 |
| **Manipulation**（10 任务） | **0.58** | 0.48 | 0.44 | 0.35 |
| **Spatial**（8 任务） | 0.36 | **0.40** | 0.25 | 0.13 |

- **Instruction** 是当前最饱和的维度（领先模型 0.75+）
- **Robust** 退化极不均衡：机器人初始位姿 Δ=**−0.258**（π0.5）/ −0.217（ACoT-VLA）；相机位置 Δ=**−0.256**（ACoT-VLA）；图像质量 Δ≈−0.15…−0.17；而指令改写与背景替换退化 **≤0.061**，个别略微为正。⇒ 现有 VLA 对语言/纹理鲁棒，对**几何与视点**脆弱
- **Manipulation** 前沿失效任务：`Sorting Packages Continuous` 0.10 / 0.00 / 0.00 / 0.00；`Clean the Desktop` 0.00 / 0.00 / 0.02 / 0.00。⇒ 长时序、需连续重复决策的任务是完全未解决区
- **Spatial** 指代类（referential）任务领先模型可达 0.80–0.81，但四个**构造类**任务（Sort Cubes by Size、Sort Number、Stack Bowls、Stack Three Building Blocks）对所有四个模型均 **≤0.30**。⇒ "识别空间关系"与"主动构造空间结构"之间存在断层

#### 论文声明 vs 代码证据对照

| 论文声明 | 代码侧状态 |
|---|---|
| LLM 驱动的场景/任务生成（Generator + RAG + DSL） | 部分可见：资产索引与 DSL 生成链在 `source/geniesim_world/` 内；ChromaDB / QWEN 嵌入为运行时外部依赖 |
| ADER + VLM 自动评测 | HTTP 解耦闭环评测通路与规则评分入口在 `BENCH/app/controllers/api_core.py`；VLM 评测器权重/端点不在仓库内 |
| 3DGS Real2Sim | 重建流水线完整，**USD 转换缺失** |
| sim2real 差距 <10% / R²=0.931、斜率≈1.023 | 无法在仓库内复现 |
| "de-skewed rotary lidar" | **证据充分**：`instantLidar=True` + `fireTimeNs` 钳制（见 §2.4.10） |
| 传感器噪声建模 | **仅 RGB** 有噪声库（7 实现 / 5 启用）；深度、IMU、LiDAR 均无噪声模型 |
| 高保真物理 | 无作弊抓取是真实优点；但 `newton` 后端用**运动学速度注入**而非力矩控制，`isaac_newton` 后端 proprioception 返回全零 |

**论文本身的缺口**（勿与代码结论混淆）：论文**未点名任何物理引擎**（三后端结构完全来自代码证据）；**未给出任何相机内参、分辨率、帧率或噪声模型**（全部传感器机制为代码证据）；**未给出数据采集吞吐的墙钟数字**。

---

## 3. 架构与模块

### 3.1 整体架构

`[CODE]` `source/README.md`、`source/AGENTS.md`

整体是**一组同级 Python 包（peer packages）+ 若干独立维护模块**，由 `geniesim` CLI 与 Docker 统一编排：

```
                    geniesim CLI  (source/geniesim_cli/)
                          │  单文件 dispatcher，不 import USD/Isaac/MuJoCo
        ┌─────────────────┼─────────────────┬──────────────┬─────────────┐
        ▼                 ▼                 ▼              ▼             ▼
  geniesim_benchmark  geniesim_ros    geniesim_generator  geniesim_   geniesim_
  （legacy 栈，       （RT Engine，    （场景生成）        teleop      world
   直驱 Isaac Sim）    ROS 2 原生）                       (VR/Pico)   (全景→3D)
        │                 │
        │                 └── 10 个 colcon ROS 2 包
        │
  ┌─────┴─────────────┬──────────────────┬─────────────────────┐
  ▼                   ▼                  ▼                     ▼
data_collection   rlinf_geniesim   scene_reconstruction     external/
（gRPC 采集）      （RL 训练）       （3DGS real2sim）        （第三方，仓库内仅 .gitkeep）
```

**双并行栈** ⚠️：`geniesim_benchmark` 直接驱动 Isaac Sim（legacy），`geniesim_ros` 是 ROS 2 原生 RT Engine；两者**场景格式与 launch 图不得混用**。路线图计划把 benchmark 重构为 `geniesim_ros` 之上的一层，**目前尚未完成**。

**分层安装（Tier）** `[CODE]`：

| Tier | 内容 | 安装方式 |
|---|---|---|
| Tier-1（自动安装） | `geniesim_cli`、`geniesim_assets`（带外获取）、`geniesim_benchmark`、`geniesim_ros` | `geniesim bootstrap` / 容器 entrypoint 自动 |
| Tier-2（按需） | `geniesim_teleop`、`geniesim_generator`、`geniesim_world` | `pip install -e "source/geniesim/[teleop\|generator\|world\|all\|full]"` |

**容器镜像变体** `[CODE]` `docker/AGENTS.md`：

| 变体 | Isaac Sim | ROS 2 | 状态 |
|---|---|---|---|
| `geniesim3` | 5.1 | Jazzy | **默认** |
| `geniesim4` | 6.0 | Jazzy | "not implemented" |
| `geniesim2` | 4.5 | Humble | **E.O.L.** |

依赖图可自动生成：`geniesim tool deps-dag`（Python 包依赖）、`geniesim tool ros-dag`（ROS 包依赖）。

### 3.2 各模块通信方式（每栈不同，排障必读）

`[CODE]`

| 模块 | 通信机制 | 关键文件 |
|---|---|---|
| `geniesim_benchmark` → 推理服务 | **WebSocket + msgpack** | `utils/comm/websocket_client.py`；协议在 `benchmark/policy/corobotpolicy.py` |
| `data_collection` | **gRPC** + aimdk protocol | `server/grpc_server.py` |
| `geniesim_ros` | 原生 **ROS 2 topics**，共享同一 `sim_time` | `/joint_command`、`/joint_states`、`/tf`、`/clock`、`/odom`、相机 topics、`/tf_render` |
| `rlinf_geniesim` | **共享内存**（Frame SHM / Ctrl SHM / Step SHM） | `renderer/shm_layout.py` |

RMW 固定为 `rmw_cyclonedds_cpp`，`CYCLONEDDS_URI` 限制在回环地址，关闭组播、peer 固定 `127.0.0.1`。

### 3.3 模块逐一说明

**`geniesim_cli`** — 单文件 dispatcher `src/geniesim_cli/cli.py` + 15 个命令模块；**不 import** USD / Isaac / MuJoCo，故在裸机上也能跑（用于 `docker build` 等前置动作）。唯一依赖 `tomli`。

**`geniesim_benchmark`** — 声明式 YAML 驱动（86 个 task yaml）。入口 `app/app.py`；`app/task_manager.py` 编排 episode；`benchmark/policy/corobotpolicy.py` 是策略侧协议；`evaluator/generators/{auto_score,eval_gen,instruction_gen}.py` + `evaluator/prompts/*` 为 LLM/VLM 评测生成链；`dataset/convert/agibot_to_lerobot.py` 做数据格式转换；`utils/IK-SDK`、`utils/name_utils.py`（`ROBOT_CONFIGS`）；`plugins/{ader,logger,tgs,output_system,sim_control_gui}`；Kit 实验文件 `app/geniesim.exp.kit`。

**`geniesim_ros`（RT Engine）** — 10 包 colcon 工作空间，同时作为 pip wheel 分发（内含 `_ros_install.tar.gz`）。物理 + 渲染 + 机器人栈作为 ROS 2 节点跑在同一 `sim_time` 上。

**`geniesim_generator`** — Scene Language DSL + Open WebUI agent + MCP 工具 + 资产 RAG。⚠️ `src/geniesim_generator/app.py` **必须在包目录内运行**（不能 `python -m`）；**没有 `geniesim generator` CLI 子命令**。

**`geniesim_teleop`** — VR / Pico 遥操作桥。`scripts/autoteleop.sh` 在宿主侧运行（交互式 y=保留 / n=丢弃），`scripts/autoteleop_post_process.sh <SUB_TASK_NAME>` 做后处理。

**`geniesim_world`** — PanoRecon 流水线：ERP 全景 → DA360 深度 → cubemap 6 面 → SHARP 逐面高斯 → 合并 PLY。使用独立 conda 环境；`geniesim_world create -p <pano>.png -o .`；对应 arXiv 2604.07105。

**`data_collection`** — Isaac Sim 5.1 + cuRobo，gRPC 双进程。输出 agibot 格式 episode（`aligned_joints*.h5` + `observations/` + `data_info.json`）。CLI：`geniesim autocollect {list,run,build,up,into}`。⚠️ 授权限定为**非商业研究/评测用途**。

**`rlinf_geniesim`** — MuJoCo **1000 Hz** 物理（每 env 一进程，用 ROS 2 namespace 隔离）+ 单个 Isaac Sim 30 Hz `GridCloner` 渲染，**唯一通道是共享内存**。支持 SpaceMouse 人在环（仅 `env_0`）；算法为 SAC + BC 正则。入口 `run.sh {collect,convert,train,shell}`、`sim_server.py`（`GenieSimVectorEnv`）、`GenieSimShmClient`。

**`scene_reconstruction`** — Docker 化 CUDA 11.8。入口 `third_party/gsplat/examples/real2sim_environment_entrypoint.sh <SCENE> <NVS_FLAG>`，产物为 `gs-asset/`。

**`external/`** — 仓库内只有 `.gitkeep`；使用者需自行 clone `apple/ml-sharp`、`DepthAnything/DA360`（含 `DA360_large.pth`），可选 Real-ESRGAN。

### 3.4 RT Engine 的 10 个 ROS 2 包

`[CODE]` 均位于 `source/geniesim_ros/src/ros_ws/src/`，每个包同时提供 `README.md` 与 `AGENTS.md`（由 `geniesim tool docs --scope ros` 审计）：

| 包 | 职责 |
|---|---|
| `genie_sim_bringup` | launch 编排；scene YAML 与 launcher YAML 配置 |
| `genie_sim_engine` | 物理 + ROS 2 桥接（三后端在此） |
| `genie_sim_render` | 渲染节点（OVRtx C++ / Isaac Python 两种） |
| `genie_sim_robot_model` | xacro/URDF + 预烘 USD + 离线网格工具 → AS3 布局 |
| `genie_sim_rviz_plugins` | RViz 可视化插件 |
| `genie_sim_moveit` | Genie G2 的 MoveIt 2 配置：SRDF、OMPL、ros2_control、WBC launch |
| `genie_sim_moveit_plugins` | 3 个 IK 插件（KDL-coupled / bio_ik-coupled / relaxed-IK）+ RRT-Connect + TOPP-RA |
| `genie_sim_control` | 控制层（内嵌 `genie_sim_ros_control`） |
| `genie_sim_controllers` | 四轮转向底盘伺服 + MPC/OSQP + `ServoBase` |
| `genie_sim_planning` | 规划层 |

执行期依赖：`bringup → {engine, robot_model}`；`moveit → {robot_model, moveit_plugins, control, planning}`。

**RT Engine 的四条不变量（invariants）** `[CODE]`：

1. **scene YAML 与 launcher YAML 是两条正交轴** —— scene 决定机器人 + 任务，launcher 决定物理后端 + 渲染器，可自由组合
2. 规范引擎 id 是 `isaac_physx` / `isaac_newton` / `newton_standalone`，裸写 `physx` / `newton` 会被 `runtime.bootstrap._validate_engine_id` 拒绝
3. `assemble_robot.py` 在首次写出 `robot.usda` 后**只读**，缓存由 `manifest.json` 门控
4. `init_base_pose` / `init_joint_pos` 是**非物理 teleport**，在第一个求解器 tick 之前施加

**Benchmark 栈的不变量** `[CODE]`：

1. 配置命名规则 `<robot>_<category>_<task>.yaml`，CLI 按**第二个 token** 切出 category
2. 机器人前缀：`g2op`、`g290d`、`arxone`、`g1op`、`aloha`
3. `config.yaml` / `template.yaml` / `teleop.yaml` 是模板，被 `list` 过滤掉
4. `--infer-host=H:P` 会被改写为 `--benchmark.infer_host=…`
5. 未知的 `--key=value` 原样转发给 `app/app.py` 的 `ParameterServer`，键空间即 `config/params.py` 里的 `@dataclass` 树
6. `batch` 是逐配置顺序 `subprocess.run`，任一失败则整体非零退出
7. **排行榜表名是对外契约**，不得随意改动

### 3.5 评测榜单结构

`[CODE]` RoboColiseum 共 5 个 board（基线顺序 π0.5 / ACoT-VLA / GR00T-N1.7 / π0）：

| Board | category | 任务数 | 机器人 | 成绩 |
|---|---|---|---|---|
| Instruction | `if` | 10 | g2op | 0.75 / 0.76 / 0.65 / 0.37 |
| Robust | `robust` | 50（5 类扰动 × 10） | g2op | 0.613 / 0.622 / 0.538 / 0.313 |
| Manipulation | `manip` | 10 | g2op | 0.58 / 0.48 / 0.44 / 0.35 |
| Spatial | `spatial` | 8 | g2op | 0.36 / 0.40 / 0.25 / 0.13 |
| Sim2Real（非竞赛） | `s2r` | 8 | g1op | 2×2 设计：sim2sim 0.80 / real2sim 0.75 / sim2real 0.83 / real2real 0.75 |

Robust 的 5 类扰动为：**指令改写、机器人位姿、背景、图像质量、相机位置**。

---

## 4. 关键特性

### 4.1 README 宣称的特性清单

`[README]`

| 特性 | 说明 |
|---|---|
| `geniesim` 统一 CLI | PEP 517/621 wheel 分发，一个入口覆盖 docker / bootstrap / benchmark / autocollect / teleop / ros / dataset |
| Agent-ready SKILLs | `AGENTS.md` 层级 + `skills/<name>/SKILL.md`，文档面向 AI agent 消费而非仅人类 |
| Genie Sim RT Engine | 物理 + 渲染 + 机器人栈作为 ROS 2 节点跑在**同一 `sim_time`** 上；多物理后端可切；Newton 路径支持布料 + 软体 |
| 5,140 个已验证资产 | 覆盖零售、工业、餐饮、家居、办公五类场景 |
| 3DGS 重建流水线 | 真实场景 → 高保真仿真场景 |
| Genie Sim World | **单张全景图 → 3D 世界，数分钟内完成** |
| LLM 驱动场景生成 | 自然语言 → RAG 检索资产 → DSL → USD 场景 |
| 10,000+ 小时合成数据 | 覆盖 200+ 项 loco-manipulation 任务 |
| 合成数据生成工具链 | 含**错误恢复（error-recovery）**轨迹生成 |
| 100,000+ 场景 benchmark | LLM 生成指令与评测配置；宣称 sim-real 差异 **<10%** |
| VLM 自动评测 | 视觉语言模型判定任务完成度 |
| 零样本 sim-to-real 迁移 | 论文 Table I 中 1500 eps 合成数据反超真机基线 |

### 4.2 与其他仿真器相比的独特之处（代码证据支撑）

`[CODE]`

1. **同时支持三个物理后端且用 USD 保证一致性** —— PhysX / Isaac Newton / Newton-standalone 三选一，且跨引擎一致性靠 USD 属性（含 `mjc:*` / `mujoco:*` / `NewtonMimicAPI` 自定义命名空间）而非代码分支。同类项目通常绑定单一引擎（Isaac Lab → PhysX，MuJoCo Playground → MJX，OmniGibson → PhysX）。

2. **Kit-free 渲染路径（OVRtx）** —— 用 NVIDIA 独立 C-API RTX 库直接渲染，绕开 Omniverse Kit 的启动成本与扩展体系；inline 模式下 Warp kernel 通过 `binding.map(device=Device.CUDA)` **零拷贝**写入渲染器 Fabric buffer。这是本仓最少见的工程能力。

3. **物理与渲染进程可分离，且不阻塞物理线程** —— 物理每步只 `record` 一个 CUDA event，渲染线程在自己的 stream 上 wait 该 event；物理线程从不 CPU 阻塞，物理与渲染 GPU 工作重叠。

4. **de-skewed rotary LiDAR** —— `instantLidar=True` + `fireTimeNs` 钳制，把 RTX 旋转扫描 LiDAR 变成单位姿瞬时快照，输出与光线投射严格一致、可复现。这是同类工具链里罕见的传感器级改造。

5. **自研内参换算修正了 Isaac 内置节点的 cx/cy bug**，且 `v_aperture` 公式保留 `fx/fy` 项以精确表达非方形像素——多数实现在这里丢信息。

6. **评测体系本身是最强竞争力** —— 200+ 任务 / 100k+ 场景 / 5 个榜单 + LLM 任务生成 + VLM 自动打分 + RoboColiseum 排行榜引擎 + 单独的 Sim2Real 2×2 保真度设计。多数开源仿真器只提供环境，不提供成建制的评测与榜单。

7. **不作弊的抓取** —— grep 确认全仓**无 adhesion / sticky-grasp / 吸附约束 / 抓取时动态创建 fixed joint**；抓取完全依赖接触摩擦 + SDF 碰撞 + 夹爪力矩。很多仿真 benchmark 为提高成功率会引入吸附，本仓没有。

8. **选择性碰撞近似策略** —— 夹爪 visual mesh 用 SDF（对薄壁/凹形夹爪指是唯一能产生正确接触面的近似）、轮子用 convexHull、其余非接触 link 直接禁用碰撞。这是有针对性的性能/保真权衡而非全局统一设置。

9. **Agent-first 的文档体系** —— `AGENTS.md` 层级 + `SKILL.md`，并有 `geniesim tool docs` 做文档覆盖审计。这在机器人仿真项目中尚不常见。

### 4.3 需要平衡看待的地方

- 传感器噪声**只有 RGB 有模型**（5 种），深度 / IMU / LiDAR 均为几何真值（见 §2.4.16）
- 域随机化覆盖语言 / 纹理 / 相机外参，**未覆盖相机内参与动力学参数**——恰是论文 Robust 榜上最大的两处失效
- **无 GPU 向量化多环境物理**（无 Isaac Lab 式 `num_envs` 张量化）；Benchmark 靠共享相机 teleport 串行取观测，RLinf 靠多进程 MuJoCo
- `newton` 后端用**运动学速度注入**而非力矩控制；`isaac_newton` 后端 proprioception 返回全零
- 三套栈并行导致概念负担较重，且 benchmark 与 ros 的统一尚未完成

---

## 5. 安装与依赖

### 5.1 系统要求

`[CODE]` / `[README]`

| 项 | 要求 |
|---|---|
| 操作系统 | Ubuntu 24.04 (Noble)，容器内 |
| ROS 2 | Jazzy（默认变体） |
| Python | `requires-python = ">=3.10,<3.13"`（所有 peer 包一致） |
| GPU | **必须有 NVIDIA GPU 且支持 RayTracing**——`compute_cap >= 7.5`。V100（7.0）等无 RT core 的卡**完全无法运行**（见 §8.3） |
| 驱动 / CUDA | issue 模板参考环境：NVIDIA-SMI 570.124.04 / CUDA 12.8。实践上建议 **580+ 且用 apt 安装**（见 §8.3） |
| 显存 | pi05 推理 <8 GB/实例（24 GB 卡最多 3 个）；generator 本地 VL 嵌入峰值约 16 GB；RLinf 需 RTX 3090+ / ≥24 GB；`geniesim_world` 在 RTX 5090 / CUDA 12.8 上验证 |
| 内存 / 磁盘 | `未提及` |
| 容器 | Docker + NVIDIA Container Toolkit；容器以 `--gpus all --privileged --network=host` 运行 |

⚠️ `data_collection` 的 cuRobo 默认 `TORCH_CUDA_ARCH_LIST=8.9`（RTX 4090D）；**50 系（SM_120）可能装不上 cuRobo**。架构不匹配会伪装成假 OOM，详见 §8.2。

镜像基于 `nvcr.io/nvidia/isaac-sim:<TAG>`；变体映射表在 `source/geniesim_cli/src/geniesim_cli/commands/docker.py` 的 `_VARIANTS`。

### 5.2 主要依赖

**apt 层**（`docker/Dockerfile.5.1`）：

- 基础工具：`bash wget curl git git-lfs sudo gosu lsb-release unzip xterm build-essential cmake libeigen3-dev ffmpeg jq vim acl locales software-properties-common ca-certificates gnupg`
- Python：`python3 python3-pip python3-venv python3-dev`
- 图形 / Vulkan：`libvulkan1 vulkan-tools libx11-6 libxrandr2 libxss1 libxcursor1 libxi6 libglu1-mesa libgl1 libegl1 libnss3 libxcomposite1 libxdamage1 libxext6`
- 其他：`liburing2 liburing-dev graphviz libgraphviz-dev`
- ROS 2：`ros-jazzy-desktop`、`ros-jazzy-rmw-cyclonedds-cpp`、`ros-jazzy-vision-msgs-rviz-plugins`、`ros-jazzy-joy`、`ros-dev-tools`，随后 `rosdep init && rosdep update` + `rosdep install`

**Isaac Sim**：`pip install "isaacsim[all,extscache]" --extra-index-url https://pypi.nvidia.com`

**逐包 Python 依赖** `[CODE]`：

| 包 | 依赖 |
|---|---|
| `geniesim_cli` | 仅 `tomli` |
| `geniesim_benchmark` | `isaacsim colorama cv-bridge future grasp_nms msgpack openai pyyaml shapely trimesh` |
| `geniesim_ros` | `isaacsim`、`ovrtx>=0.3.0,<0.4.0`、`pyglet>=2.0`、`pydantic<=2.11.10`、`pydantic_core<=2.33.2`、`idna<=3.10`、`numpy<=2.3.1`、`Pillow<=12.1.1`、`typing_extensions<=4.12.2`、`trimesh<=4.11.1`、`mujoco<3.9.0` |
| `geniesim_teleop` | `aiofiles colorama h5py numpy<2.0 open3d opencv-python pynput pytz pyyaml rosbags rosbags-image scipy` |
| `geniesim_generator` | `jaxtyping mitsuba networkx numpy<2.0 pillow pygraphviz scipy tqdm transforms3d usd-core` + extras `mcp` / `rag` / `vl` |
| `geniesim_world` | `setup.py` 中含 `file://` 本地依赖 + `requirements-cu128.txt` |

注意 `ovrtx` 的**上界钉死** `<0.4.0`（对应 §2.3.1 的版本守卫），以及多个包要求 `numpy<2.0` 而 `geniesim_ros` 允许 `numpy<=2.3.1`——跨 Tier-2 混装时需留意。

`docker/collect_deps.py` 用正则解析各 `pyproject.toml` 汇总依赖（跳过 `geniesim*`、`isaacsim`、`cv_bridge`、`numpy`、`scipy`）；`--peers` 输出 Tier-1 目录名给 entrypoint 使用。

**预编译轮子**：`3rdparty/ik_solver-0.4.3-cp311-cp311-linux_x86_64.whl`（在 `docker/Dockerfile.5.1:189-190` 被引用）。同目录另有一个 cp312 版本但未被引用。

### 5.3 资产 / 数据集 / 权重的获取

`[CODE]`

| 内容 | 来源 |
|---|---|
| 资产（Tier-1，**带外获取**） | ModelScope `agibot_world/GenieSimAssets` 或 HuggingFace `agibot-world/GenieSimAssets` |
| 数据集 / 3DGS 资产 / Pico APK | ModelScope `agibot_world/GenieSim3.0-Dataset` |
| RoboColiseum 训练数据 | LeRobot v2.1 格式，suite 为 `instruction` / `manipulation` / `sim2real`；`download_dataset.sh <suite> [<your_path>]`（需 `pip install modelscope`），输出至 `<LOCAL_DIR>/<suite>/`，规模数十 GB，支持断点续传 |

> ⚠️ **硬性规则** `[CODE]` `.agent/geniesim_cli.md`：**绝不要建议 `pip install geniesim` 或 `pip install geniesim_assets`** —— 这些包不在 PyPI 上，必须 `pip install -e source/<pkg>/`。
>
> `docker/start.sh` 会在找不到资产包的 `pyproject.toml` 时直接退出。

### 5.4 安装步骤

`[README]` / `[CODE]`

```bash
# 0) 资产包（带外下载后可编辑安装）
pip install -e <your_path>/geniesim_assets

# 1) 宿主侧安装 CLI（不依赖 Isaac/USD，裸机可跑）
pip install -e source/geniesim_cli/

# 2) 构建镜像（--china 把 nvcr 换成 DaoCloud、apt/pip 换成 TUNA 源）
geniesim docker build [--china]

# 3) 起容器（--headless 跳过 X11/DISPLAY 与 /dev/input 挂载）
geniesim docker up [--headless]

# 4) 进容器
geniesim docker into

# 5) 容器内自检与初始化
geniesim status
geniesim doctor
geniesim bootstrap

# 6) 可选 Tier-2 组件
pip install -e "source/geniesim/[teleop]"     # 或 generator / world / all / full
```

机制要点 `[CODE]`：

- **自动 bootstrap** —— 除 `bootstrap` / `status` / `doctor` / `version` / `env` / `help` / `completion` / `docker*` / `tool` / `deploy` 之外的任何子命令，首次调用会自动触发 bootstrap。非 TTY 环境下会失败，除非设 `GENIESIM_SKIP_AUTOBOOT=1`
- **entrypoint 每次 `docker up` 都重跑可编辑安装** —— 所以改了 `pyproject.toml` 只需重启容器，不必重建镜像

---

## 6. 基本使用流程

两条栈的入口完全不同，下面各给一条典型流程。

### 6.1 流程 A：Benchmark 评测（加载场景 → 载入机器人 → 跑策略闭环）

`[README]` / `[CODE]`

```bash
# ① 先确认推理服务可达（策略与仿真器解耦，独立部署）
geniesim benchmark check-inference --infer-host=<INFER_IP>:8999

# ② 浏览可用的类别 / 机器人 / 任务
geniesim benchmark categories        # if / zeroshot / s2r / dev / wbc / lp / manip / probe
geniesim benchmark robots
geniesim benchmark list --robot=g2 pick

# ③ 跑单个任务（场景、机器人、相机全部由该 task 的 YAML 声明）
geniesim benchmark run g2op_if_pick_block_color \
    --infer-host=<INFER_IP>:8999 \
    --app.headless=true \
    --benchmark.record=true \
    --benchmark.num_episode=20 \
    --benchmark.seed=0

# ④ 批量跑一整个类别
geniesim benchmark batch --robot=g2 --category=if
```

第 ③ 步实际展开为 `[CODE]`：

```bash
omni_python source/geniesim_benchmark/app/app.py \
    --config source/geniesim_benchmark/src/geniesim_benchmark/config/<task>.yaml \
    --benchmark.infer_host=<INFER_IP>:8999 \
    --app.headless=true
```

解释器选择顺序：`$GENIESIM_PY_CMD` → PATH 上的 `omni_python` → `sys.executable`。

> ⚠️ `--config` 要的是 **YAML 路径**而非任务名；未知的 `--key=value` 会原样转发到 `ParameterServer`，键空间即 `config/params.py` 的 dataclass 树。

### 6.2 流程 B：RT Engine 实时仿真（ROS 2 原生）

`[CODE]`

```bash
# ① 构建 colcon 工作空间（⚠️ 不能在已有的 colcon 树内执行）
geniesim ros build dev

# ② source 环境
source devel/setup.bash

# ③ 启动：scene 决定机器人+任务，launcher 决定物理后端+渲染器（两条正交轴）
ros2 launch genie_sim_bringup app.launch.py \
    scene:=scene_pnp_g2_op \
    launcher_config:=launcher_ovrtx_isaac_physx \
    headless:=false

# ④ 另开终端起 MoveIt 2 / 全身控制
ros2 launch genie_sim_moveit wbc.launch.py arm:=crs gripper:=omnipicker
```

可用的 launcher 变体 `[CODE]`：

```
launcher_ovrtx_isaac_physx     ← 默认稳定路径（PhysX + OVRtx）
launcher_ovrtx_isaac_newton    ← 实验，仅刚体
launcher_newton_mjwarp         ← Newton-standalone + MuJoCo-Warp
launcher_newton_fsvbd          ← Featherstone + VBD
launcher_newton_avbd           ← AVBD
launcher_newton_mjvbd          ← MuJoCo + VBD（布料）
launcher_newton_mjxpbd         ← MuJoCo + XPBD（布料 / FEM）
```

启动后可订阅的主要话题：`/clock`、`/joint_states`、`/tf` + `/tf_static`、`/odom`、各相机的 `image_raw` / `depth/image_raw` / `camera_info`；下发控制走 `/joint_command`。

### 6.3 流程 C：数据采集

`[CODE]`

```bash
geniesim autocollect build      # 构建采集用镜像
geniesim autocollect up
geniesim autocollect into
geniesim autocollect list       # 列出可采集的任务
geniesim autocollect run <task> # 采集（cuRobo 规划 + GraspNet 抓取标签）
```

产出为 agibot 格式 episode：`aligned_joints*.h5` + `observations/` + `data_info.json`。转 LeRobot 格式用 `dataset/convert/agibot_to_lerobot.py`。

遥操作采集（Tier-2）：宿主侧运行 `scripts/autoteleop.sh`（结束时交互确认 `y` 保留 / `n` 丢弃），再跑 `scripts/autoteleop_post_process.sh <SUB_TASK_NAME>`。

### 6.4 流程 D：单张全景图生成 3D 世界

`[CODE]`

```bash
# 需先在独立 conda 环境安装 geniesim_world，并自行 clone external/ 下的
# apple/ml-sharp 与 DepthAnything/DA360（含 DA360_large.pth）
geniesim_world create -p <your_path>/<pano>.png -o .
```

流水线：ERP 全景 → DA360 深度 → cubemap 6 面 → SHARP 逐面高斯 → 合并 PLY。

> ⚠️ 该模块产物**尚未接入 RT Engine**（路线图待办项）。

---

## 7. 常用 API / 接口

### 7.1 CLI 子命令总表

`[CODE]`

| 子命令 | 作用 |
|---|---|
| `geniesim bootstrap` | 初始化环境（安装 Tier-1 包等） |
| `geniesim status` / `doctor` / `version` / `env` | 自检、诊断、版本、环境变量 |
| `geniesim completion` | shell 补全 |
| `geniesim docker build \| up \| into \| down \| logs` | 容器生命周期 |
| `geniesim docker4.5 \| docker5.1 \| docker6.0` | 指定 Isaac Sim 版本变体 |
| `geniesim ros build [dev]` / `ros launch` | 构建 / 启动 RT Engine |
| `geniesim benchmark categories \| robots \| list \| check-inference \| run \| batch` | 评测 |
| `geniesim dataset` | 数据集操作 |
| `geniesim autocollect build \| list \| run` | 自动采集 |
| `geniesim teleop` | 遥操作 |
| `geniesim deploy` | 部署 |
| `geniesim tool` | 工具集（`deps-dag`、`ros-dag`、`docs` 等） |

### 7.2 配置文件结构

**Benchmark 任务 YAML**（`BENCH/config/<robot>_<category>_<task>.yaml`）`[CODE]`：

```yaml
app:
  headless: true
  physics_step: 120
  rendering_step: 60
  render_mode: RaytracedLighting
  on_demand_render: ...
  enable_rate_limit: ...
  enable_ros: ...              # 录 mcap 必须为 true
benchmark:
  task_name: ...
  platform: ...
  sub_task_name: ...
  env_class: DummyEnv          # 见 §7.3 env 层级
  policy_class: DemoPolicy
  model_arc: pi
  infer_host: <INFER_IP>:<PORT>
  instruction_mode: full       # full | subtask
  num_episode: ...
  seed: ...
  record: ...                  # 录 mcap 必须为 true
  enable_vec: ...
  num_instances: ...
layout:
  ...
```

**评测任务 JSON**（`BENCH/config/eval_tasks/*.json`）字段 `[CODE]`：

```
task, problem_instance
robot   { robot_id, robot_cfg, arm, robot_init_pose }
scene   { scene_id, scene_info_dir, scene_usd, function_space_objects }
objects { task_related_objects, extra_objects, fix_objects, constraints }
stages  [ { action, active, passive, extra_params } ]
generalization.material { enable, num }
recording_setting       { camera_list, fps, num_of_episode }
```

**RT Engine 场景 YAML**（`BRINGUP/config/scene_*.yaml`）`[CODE]`：

```yaml
robot:
  robot_source: { arm: ..., body: ..., gripper: ... }
pin_base_to_world: ...
convert_joints_to_fixed: ...
init_base_pose: ...        # 非物理 teleport，第一个求解器 tick 前施加
init_joint_pos: ...        # 单位为「度」
viewer_camera: ...
cameras:
  - { topic: ..., sensor: ..., intrinsic: ..., extrinsic: ... }   # 详见 §2.4.4
lidars: []
scene: ...
```

**RT Engine launcher YAML**（`BRINGUP/config/launcher_*.yaml`）`[CODE]`：

```yaml
launcher:
  physics:
    engine: isaac_physx            # isaac_physx | isaac_newton | newton_standalone
    engines:
      - { package: ..., executable: ..., name: ... }
  renders: []                      # newton-standalone 保持空（inline 可视化）
industrial_bridge: ...
render_ovrtx:
  ros__parameters:
    plugin: ...
```

### 7.3 Benchmark 侧编程接口

`[CODE]`

**参数系统** —— `ParameterServer`：`declare_parameter()` / `set_parameters_from_yaml()` / `override_from_cli()` / `get()` / `as_dict()`；对应 dataclass 树 `AppConfig` / `BenchmarkConfig` / `LayoutConfig` / `Config`（`config/params.py`）。

**主循环**（`app/app.py`）：

```
ParameterServer
  → AppLauncher(cfg.app)
  → 启用 isaacsim.ros2.bridge
  → TaskManager(api_core=APICore(ui_builder, config=cfg),
                benchmark_config=cfg.benchmark)
  → 循环: physics_step() / on_ros_tick() / my_world.step(render=…) / render_step()
  → stop_all_recording() / shutdown_ros()
```

**`APICore`**（`app/controllers/api_core.py`）—— 约 70 个公开方法，是场景/物体/机器人/相机操作的总门面（也是 HTTP 解耦闭环评测的落点）。

**环境类层级**：`AderEnv → BaseEnv → DummyEnv → PiEnv`，另有 `BenchmarkVecEnv` / `VecEnvAdapter` / `VecPolicyWrapper` 用于向量化。Ader 框架为 `AderParams` / `AderEnv` / `AderTask`（`plugins/ader/ader_base.py`）。

**策略接口** —— `CoRobotPolicy(BasePolicy)`：

| 方法 | 作用 |
|---|---|
| `act(obs)` | 主入口 |
| `get_payload()` | 打包 JPEG 图像 + 深度 + 关节状态 + 双帧 `end_pose` + 指令，msgpack 序列化 |
| `infer()` | 通过 `ws://<host>:<port>` WebSocket 请求推理 |
| `_parse_result()` | 用**纯 `msgpack`**（**不是** `msgpack_numpy`）解析回包 |
| `_post_process_action()` | 按 `kind` 分派：`JOINT_ABS` / `EEF_ABS` |
| `need_infer()` / `inference_due()` | 推理节流 |
| `_build_end_pose()` | 声明参考系为 `base_link` |
| `_encode_image_jpeg()` / `_encode_depth()` | 观测编码 |
| `reset()` | episode 重置 |

### 7.4 gRPC 接口（仅 `data_collection`）

`[CODE]` `DC/common/aimdk/protocol/sim/`

| 服务 | RPC 数 |
|---|---|
| `SimObservationService` | 18 |
| `SimObjectService` | 4 |
| `SimCameraService` | 1（`get_semantic_data`，见 §2.4.9） |
| `SimGripperService` | 1 |
| `SimJointService` | — |

### 7.5 ROS 2 话题接口（RT Engine）

`[CODE]`

| 话题 | 方向 | 说明 |
|---|---|---|
| `/clock` | 出 | 仿真时间，全栈时间戳源 |
| `/joint_states` | 出 | position / velocity / effort（effort 14 维），100 Hz，滞后一拍 |
| `/joint_command` | 入 | 关节指令 |
| `/tf`、`/tf_static` | 出 | 标准 TF |
| `/odom` | 出 | 底盘里程计 |
| `<camera_topic>/image_raw` | 出 | RGB |
| `<camera_topic>/depth/image_raw` | 出 | `32FC1`，单位米，无缩放 |
| `<camera_topic>/camera_info` | 出 | 自研 K/R/P（见 §2.4.2） |
| `/tf_render` | 内部 | 物理进程 → 渲染进程；`child_frame_id` 为 USD prim 绝对路径，transform 为父节点局部位姿 |
| `<node_ns>/free_cam_pose` | 内部 | 自由视角相机 |

---

## 8. 已知问题与限制

> 说明：8.1–8.5 中标 `[README]` / `[CODE]` 的是仓库文档明确声明的限制；标 `[实践]` 的来自本地一份完整的安装/调试记录（含自定义 3DGS 流水线与外部 VLA 服务的集成），属使用者踩坑而非官方声明，但复现性高、诊断价值大。

### 8.1 功能性限制（仓库明确声明）

`[CODE]` / `[README]`

| 限制 | 细节 |
|---|---|
| **布料/软体只有一条路径** | `isaac_physx` 与 `isaac_newton` 均**不支持布料**；仅 `launcher_newton_*` 的 VBD/XPBD 变体支持，且这些变体本身标注为实验性。PhysX 布料"not actively maintained" |
| `isaac_newton` **实验且受限** | 强制 `physics_solver` 为 mujoco-warp，标记 🧪 UNSTABLE，**仅刚体**；且 `snapshot_joint_states` **返回全零**（proprioception 不可用） |
| `newton` 后端**非力矩控制** | 用运动学速度注入 `joint_qd ← q⋆−q`，不产生真实关节力矩 |
| Newton-standalone **无独立渲染进程** | `launcher.renders: []`；`rerun` / `ovrtx` 可视化器为 TODO；headless 下降级为 `none`；`lidars: []` 是**保留但未实现**的字段 |
| **benchmark 与 ros 是两条独立栈** | 场景格式与 launch 图不得混用；统一重构未完成 |
| `geniesim2`（4.5 + Humble）**已 E.O.L.** | `geniesim4`（Isaac Sim 6.0）标注 "not implemented" |
| `geniesim_generator` **无 CLI 子命令** | `app.py` 必须在包目录内运行，不能 `python -m` |
| URDF 根 link 必须零质量 | 否则 KDL 拒绝做运动学求解 |
| `geniesim_world` 有显式 "not yet supported" 清单 | 且产物尚未接入 RT Engine |
| `scene_reconstruction` 构建上下文固定 | 必须是 `source/scene_reconstruction`；`sparse/0/` 为空表示 COLMAP mapper 失败；CloudCompare 需 `xvfb-run` |
| RoboColiseum 内部测试客户端**不可用于竞赛** | 越界动作只告警不拒绝 |
| `data_collection` 授权受限 | 仅**非商业**研究/评测用途 |
| **无 GPU 向量化多环境物理** | 无 Isaac Lab 式 `num_envs` 张量化 |
| 确定性 | `未提及`——无 seed 固定、无跨运行 bit-wise 复现声明 |
| 传感器缺口 | 见 §2.4.16 完整清单（深度/IMU/LiDAR 无噪声模型、无实例分割、无触觉、无 F/T 传感器、`depth_scale` 为死字段等） |

### 8.2 安装期高频问题

**Docker 构建网络失败** `[实践]`
uv 超时 → 把 `UV_HTTP_TIMEOUT` 从 600 提到 1800；代理必须写成 `ENV` 而不是 `ARG`（否则 RUN 层拿不到）；必要时 `docker build --network=host`；遇 dpkg lock 需等待或清理；内部镜像仓库不可达时改为本地构建；`docker` 组权限需重新登录生效。多架构构建耗时超过 1 小时属正常。

**⚠️ `TORCH_CUDA_ARCH_LIST` 不匹配 —— 安装期最大的坑** `[实践]`
现象是**假 OOM**：在 23.56 GiB 的卡上报 `Tried to allocate 56.60 GiB`。根因是驱动返回的 `cudaErrorNoBinaryForGpu` 被上层包装成了显存错误。排查方式是查询 GPU 的 `compute_cap` 并按真实架构重新编译扩展：

| GPU | compute capability |
|---|---|
| V100 | 7.0 |
| T4 | 7.5 |
| A100 | 8.0 |
| RTX 30 系 | 8.6 |
| RTX 40 系 | 8.9 |
| H100 | 9.0 |

**其他环境类问题** `[实践]`

- `CUDA_HOME` 为空 → 拼出 `':/usr/local/cuda-11.8/bin/nvcc'` 这类畸形路径
- **pycolmap 版本地狱** —— 需要两个隔离的 conda 环境：`numpy<2.0.0`、`plyfile<1.1`、`opencv-python-headless<4.10`；PGSR 要 `pycolmap==3.11.1`，gsplat 要 legacy `rmbrualla/pycolmap@cc7ea4b`
- Ninja 不在 PATH；`fused-ssim` / `fused-bilagrid` 必须加 `--no-build-isolation`；`nvdiffrast` 需要 OpenGL 头文件（最终改用 numpy 光栅化器绕过）
- gsplat `--data_factor 2` 需要预先生成 `images_2/`
- 权重加载报 `NOT_FOUND: Error opening "zarr" driver` = 缺 `manifest.ocdbt` 与 `_METADATA`
- **资产软链接必须在容器内部创建**（宿主创建的链接在容器里指向错误路径）
- 容器 UID 1234 vs 宿主 1000 → 需 chown/chmod，且**所有写操作尽量保持在边界的同一侧**
- `entrypoint.sh` 带 `set -e`，对不存在的目录执行 `setfacl` 会直接杀掉容器
- `start_headless.sh` 在容器真正就绪前就返回 —— 需轮询 `docker ps` 确认

### 8.3 运行期问题（Vulkan / 驱动 / GPU 能力）

**⚠️ Vulkan `ERROR_INCOMPATIBLE_DRIVER`、相机数据 shape 为 `(0,)`** `[实践]`
根因：NVIDIA Container Toolkit 默认**只注入 CUDA，不注入 GL/Vulkan**。修复需把 6 个 NVIDIA GL/Vulkan/RT 库与 `nvidia_icd.json` 拷进容器并设置 `VK_ICD_FILENAMES`。两个陷阱：**不要放在 `/tmp`**（tmpfs，重启即失）；**宿主重启后需重建容器**。

**`RTX driver verification failed`（驱动看起来已经很新）** `[实践]`
Vulkan 的 `driverVersion` 是打包编码的：535.288.01 会被解码成 "535.32"，小于要求的 535.129。建议使用 **580+ 驱动，且用 apt 安装而非 `.run` 安装包**。

**⚠️ 无 RT core 的显卡完全无法运行** `[实践]` / `[CODE]`
V100（compute 7.0）上的故障链：`Your GPUs do not support RayTracing` → `HydraEngine rtx failed creating scene renderer` → `annotator_utils.py:454` 处无限刷 `TypeError: unsupported operand type(s) for -: 'NoneType' and 'NoneType'`。伴随症状极具误导性：GPU 利用率仅 1%、端口 9001 处于 LISTEN 但从未 ESTABLISHED、rosbag 一直增长到 4 GB 却始终没有 `evaluate_ret_*.json`。**要求 `compute_cap >= 7.5`**；快速定位方法是 grep 日志前 50 行里的 `HydraEngine rtx failed`。

**Python / 模块问题** `[实践]`

- `ModuleNotFoundError: rclpy` —— Isaac 用 Python 3.11，系统 Jazzy 是 3.12；用 Isaac 自带的 jazzy 路径，或 `docker exec -it … bash -ic`（**必须交互式 shell**）
- `No module named 'pxr'` —— PYTHONPATH 缺 `omni.usd.libs`
- Lula IK 在无头模式需要 `ALIEN_HEADLESS=1`

**Benchmark 卡住 / 不出数据** `[实践]`

- 卡在 `[Physics Callback] ~18 Hz` 且策略从未被调用 —— `run_on_render_loop timed out after 120s for _collect_init_physics`，把超时提到 600
- 没有 `.mcap` 产出 —— 必须同时满足 `app.enable_ros: true` + `benchmark.record: true`，并取消 `record_topic_list` / `record_rosbag()` 的注释
- 自定义 sub_task 必须在**三张表**里都注册
- 策略服务器 `--env` 参数要**大写枚举值**；端口占用（EADDRINUSE）用 `pkill -9 -f serve_policy`；`server.sh` 默认 `CUDA_VISIBLE_DEVICES=1`
- 外部 openpi compose 文件没有 `command`，需手动启动 `serve_policy`（镜像内无 `ss` / `nc`，只能 grep 日志确认就绪；XLA 预热 3–5 分钟）

### 8.4 渲染异常速查

`[实践]`

| 现象 | 根因与修复 |
|---|---|
| RGB 全黑 | 场景 USD 里没有灯光 —— 把 `scene_usd` 指向官方自带灯光的背景 USD |
| RGB 全白 | DomeLight 缺 HDR 贴图；或 payload 缺显式 `</World>` prim 路径；或给二进制 USDC 文件起了 `.usda` 扩展名 |
| 画面像浮尘 | `UsdGeom.Points` 的 widths 在缩放后小于一个像素 |
| 物体呈单一平板色 | 3DGS 的球谐颜色没导入 —— 写 `primvars:displayColor`，用 `clip(0.5 + 0.28209479177387814 * f_dc, 0, 1)`，并过滤 `opacity > 0.02` |
| 点云在合成 stage 里消失 | **嵌套 payload 会丢点云** —— 改为内联 `def Points`（实测高饱和像素占比从 0.9% 提升到 6.0%） |
| 3DGS 物体穿透 | 纯视觉 3DGS 资产没有碰撞体 —— 需注入不可见的 box proxy |

### 8.5 性能瓶颈与实测数字

`[实践]` / `[CODE]`

**离线流水线**：PGSR 训练约 75 分钟（A800）；TSDF 融合约 50 分钟、每个输出 700 MB–1 GB；网格简化约 30 秒；UV 烘焙在简化后为 20–60 秒/物体（未简化时逐三角形的 Python 循环需 >1 小时；xatlas 在 >100K 三角形时不收敛；单靠 numba JIT 需 30 分钟；scipy `griddata` 需数小时）——**必须先简化到 5–10% 再向量化**。Open3D 的二次误差简化在约 165K 面处触底，改用 `fast-simplification`。3DGS 质量参考：PSNR >25 dB 可接受、>30 dB 良好。

**运行期点云规模 → 物理频率**（关键权衡）：

| 内联点数/物体 | 物理回调频率 | 单 episode（200 步）耗时 |
|---|---|---|
| 600K | **0.25 Hz** | 约 1 小时 |
| 100K | **约 4 Hz** | 约 14 分钟 |
| 正常基线（无点云） | 约 18 Hz | — |

100K 与 600K 的视觉差异极小（平均像素差 1.13）——**推荐 100K**。

**其他实测量级**：策略服务器预热 3–5 分钟；单 episode 10–30 分钟；一次成功的 episode = 209 步 / 850 秒墙钟 / 115 MB MCAP。产物大小：动态 `Aligned.usd` 700 KB–2 MB；2K 漫反射贴图 700 KB–1.1 MB；房间背景 1.6 MB + 4K 版 2.4 MB；含 100K 点的 `Aligned_Merged.usda` 6.6–6.7 MB（相比 `Visual_3DGS.usda` 的 40 MB）；最终网格 30K–45K 面。

**引擎侧诊断字段**见 §2.2.7；渲染帧在预算不足时会被主动丢弃（`skipped(budget)`），**渲染帧率不保证、相机时间戳间隔非均匀**。

### 8.6 路线图未完成项

`[README]` "Next" 清单（即当前尚不具备的能力）：

- 全部资产与数据集上传到 HuggingFace
- 更多 benchmark 套件：可变形/软材料、WBC、VLN
- 更多 RLinf 任务与更大模型
- 更多 Newton 求解器
- 把 `geniesim_benchmark` 重构到 `geniesim_ros` 之上
- 数据记录器改进
- 把 `geniesim_world` 产物接入 RT Engine
- 升级到 Isaac Sim 6.0

版本演进：v2.x（2025）→ **v3.0**（2026-01，Isaac Sim 5.1 / Genie G2 / 3DGS）→ **v3.1**（2026-04，Genie Sim World / RLinf）→ **v3.2**（2026-06，统一 CLI / SKILLs / RT Engine）→ Next。

---

## 9. 参考资源

### 9.1 用户提供的三条来源

| URL | 类型 | 说明 |
|---|---|---|
| https://github.com/AgibotTech/genie_sim | **仓库** | 主仓库。本文绝大多数 `[CODE]` 结论出自此处（v3.2.0，MPL-2.0） |
| https://arxiv.org/pdf/2601.02078 | **论文** | 《Genie Sim 3.0: A High-Fidelity Comprehensive Simulation Platform for Humanoid Robot》，cs.RO，DOI 10.48550/arXiv.2601.02078。v1 提交 2026-01-05，当前 v4（2026-08-14 修订） |
| https://agibot-world.com/sim-evaluation/docs/#/v3 | **官方文档** | ⚠️ 为纯 JavaScript SPA，抓取仅得到页面标题 "Genie Sim User Guide"，**无正文可提取**。本文未从该来源取得任何内容 |

### 9.2 资产 / 数据集来源

| URL / 标识 | 类型 | 内容 |
|---|---|---|
| ModelScope `agibot_world/GenieSimAssets` | **仓库（资产）** | 5,140 个已验证 3D 资产（Tier-1，带外获取） |
| HuggingFace `agibot-world/GenieSimAssets` | **仓库（资产）** | 同上的 HF 镜像 |
| ModelScope `agibot_world/GenieSim3.0-Dataset` | **仓库（数据集）** | 合成数据集、3DGS 资产、Pico APK |
| https://agibot-world.com/genie-sim | **官方文档** | 项目主页 |
| https://robocoliseum.ai | **官方文档** | RoboColiseum 评测排行榜 |

### 9.3 基线模型仓库

| 标识 | 类型 | 说明 |
|---|---|---|
| `Anonymous-694/ACoT-VLA @ agibot_world_challenge` | **仓库** | 挑战赛分支 |
| `AgibotTech/ACoT-VLA` | **仓库** | ACoT-VLA 官方 |
| `MiaoMieu/Isaac-GR00T` | **仓库** | GR00T-N1.7 基线 |

论文中另引用 π0 / π0.5（Physical Intelligence）作为基线，仓库内以 `model_arc: pi` + WebSocket 协议对接。

### 9.4 仓库内的关键文档（相对路径）

`[CODE]` 这些是继续深入时最值得先读的文件：

| 路径 | 内容 |
|---|---|
| `README.md` | 特性清单、Quick start、Roadmap、排行榜、引用信息 |
| `source/README.md` | 模块映射表 + 自动生成的 Mermaid 依赖 DAG |
| `source/AGENTS.md` | 双栈并行的权威声明、安装约定 |
| `ENG/docs/engines.md` | 三后端对照表（控制律、mimic、关节状态源），**理解物理层的第一读物** |
| `ENG/docs/newton_quirks.md` | Newton 后端的特殊行为 |
| `ENG/docs/ovrtx_sync.md` | OVRtx 两条使用臂与跨流同步机制 |
| `ENG/docs/perf.md` | 性能字段与瓶颈对应表 |
| `ENG/docs/pipeline.md` | 装配 → 启动流水线 |
| `ENG/docs/asset_consumption.md` | AS3 资产消费方式 |
| `ENG/docs/param_injection_eval.md` | 参数注入评估 |
| `ENG/config/physics_params.yaml` | **两层 PD 授权设计的权威说明**（头部长注释）+ 完整增益表 |
| `docker/AGENTS.md` | 容器变体表 |
| `.agent/geniesim_ros.md`、`.agent/geniesim_benchmark.md`、`.agent/geniesim_cli.md` | 各栈的 agent 导览与硬性规则 |
| 各 ROS 包下的 `README.md` + `AGENTS.md` | 10 个包各自的职责与不变量 |

### 9.5 引用格式

`[README]`

```bibtex
@misc{yin2026geniesim30,
  ...   % 完整条目见仓库 README.md 末尾
}
```

### 9.6 仓库 References 章节列出的第三方项目

`[README]` 共 15 项：PDDL Parser、BDDL、CUROBO、Isaac Lab、OmniGibson、The Scene Language、COAL、OCTOMAP、PINOCCHIO、URDFDOM、LIBCCD、LIBMINIZIP、LIBODE、LIBURING、MuJoCo。

---

## 附：五条最值得记住的结论

1. **本仓不是一个仿真器，而是三套共存的仿真栈**（RT Engine / Benchmark+Data-collection / RLinf），传感器与物理在三栈中路径不同，不可混谈。
2. **USD 是唯一真值源**，跨引擎一致性靠 USD 属性（含 `mjc:*` / `mujoco:*` / `omni:sensor:Core:*` 自定义命名空间）而非代码分支保证。
3. **驱动增益有两层**（USD `DriveAPI` 种子 vs `ArticulationView` 运行时张量），newton-standalone **读不到 Layer 2** —— 这是"改了增益没生效"最常见的原因。
4. **时间步设计的核心权衡**：不提高 `physics_hz`，而用求解器子步（`substep=10` ⇒ `sim_dt=1 ms`），因为外层 tick 要付约 9 ms 的 Kit/USD 更新固定开销。
5. **域随机化覆盖了语言/纹理/相机外参，未覆盖内参与动力学参数** —— 恰好对应论文 Robust 套件中最大的两处失效（机器人位姿 −0.258、相机位置 −0.256）。

