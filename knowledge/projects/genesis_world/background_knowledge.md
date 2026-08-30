# Genesis World 原理层知识（background）

> **本文是什么** — 具身智能仿真平台 **Genesis World**（Genesis AI）的**原理层**参考：它是什么、怎么设计、有哪些 API、能力边界在哪。按仓库约定固定 9 章，章号跨项目稳定。
>
> **本文不是什么** — 不是踩坑记录，不是操作手册。要动手跑请走同目录 [`quickstart.md`](quickstart.md)；手上有报错请走 [`troubleshooting.md`](troubleshooting.md)；想知道复现时为什么那么选请走 [`ai_knowledge.md`](ai_knowledge.md)；想找代码实体请走 [`code_knowledge.md`](code_knowledge.md)。
>
> **证据等级** — 每条结论都标注来源：
> - `[CODE]` 上游仓库源码，附仓库相对路径（必要时带行号），**工程决策只信这一级**
> - `[README]` 上游仓库文档（README / RELEASE / doc 目录）声明
> - `[官网]` Genesis AI 官方博客的宣称值，**未经代码验证**
> - `[文章]` 第三方解读文章，二手转述，可信度低于 `[官网]`
> - `[推断]` 由前述证据推导，**证据不足以定论**
>
> **引用的上游仓库**（本机位于 `sources/genesis_world/genesis-upstream/`，换机器需重新 clone）：
> - `github.com/Genesis-Embodied-AI/genesis-world` — 本体，**本文所有 `[CODE]` 默认指它**
> - 快照版本 `1.3.3`，HEAD `19f56d6`（2026-08-30）`[CODE]` `genesis/version.py`
>
> **⚠️ 三个必须先知道的落差（读之前先看）**
>
> 1. **Nyx 和 Quadrants 不在本仓库里** —— README 把它们画进"Genesis World 四层"，但二者是**独立仓库**（`genesis-nyx`、`quadrants`），本仓库只是依赖它们。想读渲染器或编译器源码，本仓库里找不到。见 §3.1。
> 2. **博客写的是 "Genesis World 1.0"，pip 包版本号是 `1.3.3`** —— 二者不是同一套编号。博客（2026-05）描述的是平台代际，仓库版本号是发布序列。**博客里的性能数字（0.8996 相关性、103× IPC 加速、4 ms/帧）全部是 `[官网]` 级，本仓库中没有可复现的基准脚本佐证**，详见 §8.1。
> 3. **本项目名曾是 "Genesis"** —— 2024-12 作为学术项目起步，现由 Genesis AI 官方支持并更名 `Genesis World`。旧教程、旧论文、旧 issue 里的 `Genesis` 指的是同一个东西；但 PyPI 包名一直是 `genesis-world`，`import` 名一直是 `genesis`。`[README]` `README.md:16`

---

## 1. 项目概述

### 1.1 身份与定位

| 项 | 值 | 证据 |
|---|---|---|
| 名称 | **Genesis World**（旧名 Genesis） | `[README]` `README.md:3,16` |
| 开发方 | **Genesis AI**（`genesis.ai`）；2024-12 起源于学术项目，现由公司官方支持 | `[README]` `README.md:16` |
| 仓库 | `github.com/Genesis-Embodied-AI/genesis-world` | `[README]` `README.md:8` |
| PyPI 包名 | `genesis-world`（import 名 `genesis`，惯用别名 `gs`） | `[README]` `README.md:5` |
| 本文快照版本 | `1.3.3` | `[CODE]` `genesis/version.py`、`pyproject.toml` |
| 许可 | Apache License 2.0 | `[CODE]` `LICENSE:1-3` |
| 官方文档 | `genesis-world.readthedocs.io` | `[README]` `README.md:44` |
| 一句话定位 | "a simulation platform for physical AI developments" —— 把**统一多物理引擎 + 照片级渲染器（Nyx）+ 跨平台编译器（Quadrants）** 装在一个 Pythonic 接口后面 | `[README]` `README.md:14` |
| 设计目标 | "scale from a single laptop kernel to datacenter-grade GPUs, while remaining easy to read, extend, and embed in research code" | `[README]` `README.md:14` |
| 引用条目 | `@article{genesis2026genesisworld}`（2026-05 博客）+ `@misc{Genesis}`（2024-12 原始项目） | `[README]` `README.md:206-226` |

### 1.2 它解决什么问题

Genesis World 的自我定位**不是"仿真数据生成器"，而是"机器人基础模型的评测与迭代引擎"** —— 这是理解它全部设计取舍的前提。`[官网]`

官方博客给出的问题陈述：具身智能领域公认的瓶颈是数据，但还有一个同样关键却长期被忽视的瓶颈是**模型开发周期本身慢**。当每个 ablation、每个 checkpoint 比较、每次数据配方调整都必须靠真机验证时，研发节奏被真实世界的 1× 时间锁死。`[官网]` `Genesis_world_02.txt:39-41`

Genesis 给出的具体量级对比 `[官网]` `Genesis_world_02.txt:86-92`：

| 维度 | 真机评测 | 仿真评测 |
|---|---|---|
| 一轮完整评测（数百任务 × 数百 episode） | 一名操作员 + 一台机器人工位连续 **200+ 小时** | **< 0.5 小时** |
| 人工/硬件介入 | 必需 | 无 |
| 重跑一致性 | 有标定漂移、磨损、操作员差异 | **位级一致（bit-level）** |

> ⚠️ 上表全部是官方宣称。**仓库里没有能复现这些 sim-real 相关性数字的评测套件**（14 任务 × 200 episodes 的真机对照实验不在开源范围内），工程估算请按 `[官网]` 级对待。
> 但**速度类基准是有的** `[CODE]`：`examples/speed_benchmark/`（`anymal_c.py`、`franka.py`、`timers.py`）与 `tests/benchmarks/` —— 想自测吞吐可以直接跑这两处。

### 1.3 为什么"先做评测，再做数据生成"

这是 Genesis 路线图上最反直觉、也最值得注意的一个决策，官方给了三条理由 `[官网]` `Genesis_world_02.txt:46-53`：

1. **评测是绕不过去的前置瓶颈**：无论目标是评测、数据生成还是 post-training RL，仿真行为必须先在系统层面与真实行为对齐。可信仿真是其他一切的前提。
2. **短期内真机数据采集在经济上仍可行**，足以支撑所需规模与多样性、揭示早期 scaling 行为 —— 这就腾出了时间窗口，可以先把 sim-to-real gap 收敛干净，再让仿真数据进训练。
3. **仿真只提供数据生成的"环境"**，要产出有用数据还需要任务生成、奖励规约、TAMP/RL 采样等一整套管线；产出数据有意义，但让其分布对齐部署分布仍需大量额外工作。

配套的方法论约束是 **zero-shot real-to-sim**：被评测的策略**只在真机数据上训练**，训练流与评测流完全解耦。理由是若训练和评测共享同一份仿真分布，性能提升既可能是"模型真的更好"，也可能只是"对仿真器动力学拟合得更紧"。`[官网]` `Genesis_world_02.txt:58`

### 1.4 主要用途与适用场景

| 场景 | 说明 | 证据 |
|---|---|---|
| **闭环策略评测** | 首要用途。沿视觉/行为/语义等约 10 条扰动轴系统扫描策略鲁棒性，见 §4.3 | `[官网]` `Genesis_world_02.txt:99,243-252` |
| **大规模并行 RL** | GPU 并行刚体求解，单卡可拉起数千并发环境 | `[README]` `README.md:60`（`examples/` 有并行环境示例） |
| **多物理场耦合仿真** | 刚体 + FEM + MPM + SPH + PBD 共享同一场景与同一状态 | `[README]` `README.md:40` |
| **可微仿真** | 反向模式自动微分在各后端均为一等公民 | `[官网]` `Genesis_world_02.txt:205` |
| **跨形态机器人研究** | MJCF / URDF / USD 资产，覆盖机械臂、灵巧手、夹爪、人形、四足 | `[官网]` `Genesis_world_02.txt:161` |
| **数字孪生与资产重建** | 摄影测量管线 + Gaussian splats，同时供渲染与物理使用 | `[官网]` `Genesis_world_02.txt:218` |

### 1.5 不适用 / 需谨慎的场景

- **需要开箱即用的任务基准套件** —— Genesis World 是**平台**不是 benchmark 套件。它不自带成套的标准任务、成功判据与 leaderboard（对比 LIBERO / `lw_benchhub`）。博客里的"14 个任务 × 200 episode"评测集**未开源**。`[推断]`（基于 `examples/` 只有单点 demo，无任务注册表）
- **需要传感器噪声建模** —— 见 §8.3，本版本传感器噪声支持有限，详见 §2.5。
- **需要博客宣称的 Nyx 渲染真实感** —— Nyx 在独立仓库，需额外安装，见 §5.4。

---

## 2. 核心原理

### 2.1 统一多物理：一个场景，一个状态

Genesis 与传统单一物理引擎拉开差距的地方在 Physics 层。它把多种**建模方法**（不是多个独立仿真器）放进**同一个场景、同一份状态**里。`[README]` `README.md:40`

本版本实际落地的求解器 `[CODE]` `genesis/engine/solvers/`：

| 求解器 | 文件 | 适用对象 | 原理要点 |
|---|---|---|---|
| **Rigid** | `rigid/`（子包） | 机器人本体、机械臂、夹爪、桌面、盒子、工具 | 形变可忽略的对象；URDF/MJCF/USD 资产大多落到这一类 |
| **FEM** | `fem_solver.py` | 弹性体、软体、布料 | 有限元，保留连续形变，能表达"被抓住后局部变形"、"接触处拉伸压缩" |
| **MPM** | `mpm_solver.py` | 颗粒、沙子、弹塑性材料 | 粒子携带材料状态 + 背景网格更新动量；适合大形变、破碎、流动、堆积 |
| **SPH** | `sph_solver.py` | 流体 | 光滑粒子流体力学，通过粒子邻域估计密度与压力 |
| **PBD** | `pbd_solver.py` | 快速布料、位置约束类液体 | 基于位置的动力学；求稳定快速可控，不追求最严格物理精度 |
| **SF**（Stable Fluid） | `sf_solver.py` | 烟雾等欧拉场流体 | `examples/fluid/smoke.py` |
| **Kinematic** | `kinematic_solver.py` | 纯运动学驱动对象 | 不参与动力学求解 |
| **Tool** | `tool_solver.py` | 工具类实体 | — |

> **为什么这件事对具身智能重要**：真实操作任务很少只涉及一种物理。刚体机器人、柔性物体、布料、颗粒、液体、接触摩擦、传感器反馈往往混在一起。传统做法是每种物理现象各建一个仿真环境，Genesis 的取舍是让它们在同一状态里一起跑。`[文章]` `Genesis_world_01.txt:97`
>
> **一条依赖链上的判断**：如果刚体动力学本身不稳，后面的视觉和语言评测再精细也没有意义。`[文章]` `Genesis_world_01.txt:99`

### 2.2 三种可互换的耦合器（coupler）

**coupler ≠ solver。** 耦合器负责把不同物体、运动学树、接触模型和物理求解过程**耦合到同一个批量仿真环境**里。`[文章]` `Genesis_world_01.txt:23`

本版本实际存在**三个**耦合器，与官方宣称一致 `[CODE]` `genesis/engine/couplers/`：

| 耦合器 | 类 | 文件 | 定位 |
|---|---|---|---|
| **Legacy**（快速通用） | `LegacyCoupler` | `legacy_coupler.py:22` | **默认值**；快速、通用、显式耦合 |
| **SAP**（Drake 风格半解析原-对偶） | `SAPCoupler` | `sap_coupler.py:141` | 配合 hydroelastic 接触；偏刚体接触场景中高效稳定的约束求解 |
| **IPC** | `ipc_coupler/coupler.py` | `ipc_coupler/` | 面向精细可变形体，强调**无相交接触**（penetration-free） |

**"改一行配置就能切换"的说法可以在代码中验证** `[CODE]` `genesis/engine/scene.py:105,126`：

```python
scene = gs.Scene(coupler_options=gs.options.SAPCouplerOptions())   # 换成 IPCCouplerOptions() 即切换
```

- `Scene.__init__` 接受 `coupler_options: BaseCouplerOptions | None`，`None` 时回落到 `LegacyCouplerOptions()` `[CODE]` `scene.py:126`
- 三个 Options 类均定义在 `genesis/options/solvers.py:89,123,196`，并从 `gs.options` 导出 `[CODE]` `genesis/options/__init__.py:7,8,12`
- 传入非 `BaseCouplerOptions` 实例会显式报错 `[CODE]` `scene.py:232-233`

> ⚠️ 「切换耦合器**不用改资产、传感器、策略接口**」这半句是 `[官网]` 宣称 `Genesis_world_02.txt:163`，**本文未逐一验证**。SAP 耦合器内部实现了大量按物料对分派的接触处理器（`RigidRigidContactHandler` / `RigidFEMContactHandler` / `FEMSelfTetContactHandler` 等 20+ 个类，`sap_coupler.py:2199-3657`），因此**不同耦合器支持的物料组合大概率不完全相同** —— 换耦合器后跑不起来时先查这里。`[推断]`

### 2.3 External Articulation Constraint：把关节动力学嵌进 IPC 优化

这是官方博客点名的新技术贡献，用于**让 IPC 与铰接机器人紧耦合**。`[官网]` `Genesis_world_02.txt:165-169`

**要解决的问题**：标准做法是刚体关节求解器和接触求解器**分两个阶段交错运行**，关节空间力和接触力不是同时求解的，事后需要对齐。这在机器人操作里会出问题 —— 手指穿过物体、夹爪接触点不稳定、软物体被不合理挤压等失败大多来自接触。`[文章]` `Genesis_world_01.txt:107`

**做法**：Genesis 扩展了 `libuipc`，把关节空间动力学**直接注入 IPC 的优化目标**。对一个有 $m$ 个关节的铰接系统：

1. 刚体求解器先预测关节位移 $\tilde{\delta\theta}$，并计算关节空间**有效质量矩阵** $M^t$；
2. 把"外部铰接动能"作为一项注入 IPC：

$$K = \tfrac{1}{2}\,\bigl(\delta\theta(q, q^t) - \tilde{\delta\theta}\bigr)^{\mathsf T} M^t \bigl(\delta\theta(q, q^t) - \tilde{\delta\theta}\bigr)$$

其中 $q$ 是 IPC 仿射体状态，$q^t$ 是当前时刻状态，$\delta\theta(\cdot)$ 把 IPC 状态映回关节空间位移。

**关键性质**（这是理解它行为的要点）`[官网]` `Genesis_world_02.txt:169`：

- IPC 最小化该项时，**同时**考虑接触壁垒、摩擦、关节约束 —— 不再事后对齐；
- **无接触时**，求解器恢复出与铰接系统预测完全一致的结果（即不引入额外偏差）；
- **有接触时**，只偏离到刚好能解决接触的程度，且偏离量**按有效质量加权** —— 更重的连杆更抗拒被接触修正。

### 2.4 Barrier-free Elastodynamics：用增广拉格朗日替换对数壁垒

这是官方给出的第二项接触求解改进，目标是**加速接触密集场景**。`[官网]` `Genesis_world_02.txt:171-183`

**标准 IPC 的两个痛点**：

1. 用**对数壁垒**强制非穿透 → 紧接触时 Hessian **严重病态**；
2. 带过滤的 line search **拖慢 active set 探索**。

**Genesis 的替换方案**：把对数壁垒换成自定义**增广拉格朗日**。所有由连续碰撞检测（CCD）返回的接触对**立即进入 active set**，约束满足靠**自适应拉格朗日乘子更新**驱动，而不是不断抬高罚刚度。

对每个接触对 $i$，记当前线性化穿透深度为 $c_i(x)$，引入松弛变量 $s_i$ 把不等式 $c_i(x) \ge 0$ 转成等式 $c_i(x) - s_i = 0$，每步目标为：

$$L(x, s, \lambda) = E(x) + \sum_{i \in \mathcal{A}} \psi\bigl(c_i(x),\, s_i,\, \lambda_i,\, \mu\bigr)$$

其中 $E$ 是增量势能，$\mathcal{A}$ 是当前激活的接触约束集合，$\psi$ 是带刚度 $\mu$ 与乘子 $\lambda_i$ 的增广拉格朗日项。原变量求解在两步之间交替：

$$x \leftarrow \arg\min_x L(x, s, \lambda), \qquad s_i \leftarrow \max\bigl(0,\; c_i(x) - \lambda_i/\mu\bigr)$$

随后更新乘子：

$$\lambda_i \leftarrow \lambda_i - \mu\,\bigl(c_i(x) - s_i\bigr)$$

$s_i$ 取 `max(0, ·)` 保证非负，与非穿透约束语义一致；**$s_i$ 本身不对应任何直接物理量**，只是把不等式改写成等式后需要维护的辅助变量。`[文章]` `Genesis_world_01.txt:37`

**宣称效果**：应力增大时 Hessian 仍保持良态；接触密集基准比传统 IPC **快至 103×**，同时仍保证无相交。`[官网]` `Genesis_world_02.txt:183`

> ⚠️ 103× 是官方在自选基准上的数字，**本仓库中未找到可复现该数字的脚本**。`examples/ipc/` 下有 IPC 演示，但不是性能对照实验。`[推断]`

### 2.5 传感器仿真原理（重点章节）

> 本节全部为 `[CODE]` 级，逐条可在 `genesis/engine/sensors/`（实现）与 `genesis/options/sensors/`（配置）中核对。
>
> **一句话结论**：Genesis 的传感器子系统**远比"渲染出图 + 读真值"复杂** —— 它有一套统一的**硬件缺陷（hardware imperfection）建模层**，把量化、偏置、白噪声、随机游走、读取延迟与抖动做成所有传感器共享的基础设施。**但所有缺陷参数默认值都是 `0.0`，即默认输出理想真值** —— 这是最容易踩的坑，见下文"默认理想化"。

#### 2.5.1 子系统组织

- **注册机制**：传感器类通过 `Sensor.__init_subclass__` **自动注册**到其 Options 类，写法是 `class MySensor(Sensor[MyOptions, MyMetadata, MyData])` `[CODE]` `genesis/options/sensors/options.py:73-76`、`genesis/engine/sensors/base_sensor.py:159`
- **统一调度**：`SensorManager` 统一管理所有传感器的采样 `[CODE]` `genesis/engine/sensors/sensor_manager.py:19`
- **用户命名空间**：`_SensorTypesNamespace` 把传感器 Options 暴露给用户 `[CODE]` `genesis/options/sensors/__init__.py:10`

#### 2.5.2 已实现的传感器清单（对照官方宣称逐条核实）

| 宣称的传感器 | 代码中是否存在 | 实现类 / 文件 |
|---|---|---|
| RGB 相机 | ✅ | `RasterizerCameraSensor` / `RaytracerCameraSensor` / `BatchRendererCameraSensor`，`camera.py:395,592,749` |
| 深度 | ✅ **两条独立路径** | ① 相机渲染出深度；② `DepthCameraSensor`（`depth_camera.py:11`）—— **它是 `Raycaster` 的子类**（`options.py:658`），走光线投射而非渲染 |
| 激光雷达 / 测距 | ✅ | `RaycasterSensor`，`raycaster.py:504` |
| 点云触觉 | ✅ | `ProximityTaxelSensor` / `ElastomerTaxelSensor`，`point_cloud_tactile.py:701,1949` |
| 温度场 | ✅ | `TemperatureGridSensor`，`temperature.py:508` |
| 近距离/表面距离 | ✅ | `SurfaceDistanceProbeSensor`，`surface_distance_probe.py:322` |
| FOTS 弹性体位移 | ✅ **但命名不同** | `ElastomerTaxelSensor`，实现的是 **HydroShear 风格**的 marker displacement，非 FOTS 命名 `[CODE]` `options/sensors/tactile.py:407` |
| 磁力计-IMU | ✅ **三合一** | `IMUSensor`（`imu.py:130`）**同时含加速度计 + 陀螺仪 + 磁力计** |
| 接触探针 | ✅ | `ContactProbeSensor` / `ContactDepthProbeSensor`，`kinematic_tactile.py:1110,975` |
| — | ➕ **宣称之外还有** | `ContactForceSensor`（`contact_force.py:250`）、`ContactSensor`（`:147`）、`JointTorqueSensor`（`joint_torque.py:25`）、`KinematicTaxelSensor`（`kinematic_tactile.py:1211`） |

对应的可运行示例在 `examples/sensors/`（10 个脚本：`imu_franka.py`、`lidar_teleop.py`、`tactile_franka.py`、`temperature_grid.py`、`contact_force_go2.py`、`surface_distance_shadowhand.py` 等）`[CODE]`

#### 2.5.3 硬件缺陷建模：两层继承，决定某个传感器能不能加噪

这是本子系统设计上最值得记住的一点 —— **能不能加噪，取决于该传感器的 Options 继承自哪一层**：

**第一层 `SensorOptions`（所有传感器都有）** `[CODE]` `genesis/options/sensors/options.py:69-121`

| 参数 | 默认 | 语义 |
|---|---|---|
| `history_length` | `0` | 保留历史长度，0 = 不保留 |
| `delay` | `0.0` | **读取延迟**（秒）。读到的数据会陈旧这么多 |
| `jitter` | `0.0` | **抖动**（秒），建模为每步在 `[0, jitter)` 上均匀采样的**附加随机延迟** |
| `draw_debug` | `False` | 可视化调试形状 |

两条**运行时校验**值得注意：
- `jitter > delay` 直接报错 `[CODE]` `options.py:102-104`
- `delay` **不是仿真步长 `dt` 的整数倍**时只 **warning 不报错**，实际延迟被四舍五入到 `round(delay/dt)*dt` `[CODE]` `options.py:113-119` —— ⚠️ 这是个静默行为改变，配了非整数倍延迟会得到与预期不同的值

**第二层 `SimpleSensorOptions`（只有 `SimpleSensor` 派生的传感器有）** `[CODE]` `options.py:219-243`

| 参数 | 默认 | 语义 |
|---|---|---|
| `resolution` | `0.0` | **量化步长**（读数最小增量），0 = 不量化 |
| `bias` | `0.0` | 常值加性偏置 |
| `noise` | `0.0` | 加性**白噪声**的标准差 |
| `random_walk` | `0.0` | **随机游走**标准差，作用是**累积偏置漂移** |

这些参数由 `_apply_hardware_imperfections` 在"嵌入式采样器把传感器快照进共享内存"时统一施加 `[CODE]` `options.py:222-224`（原文注释）。

> ⚠️⚠️ **相机不在第二层里**。源码注释明确写道："Camera (deriving from `Sensor` directly) stays on plain `SensorOptions`" `[CODE]` `options.py:224`。
> **含义**：相机可以配 `delay` / `jitter`，但**没有 `noise` / `bias` / `random_walk` / `resolution`** —— 图像层面的传感器噪声（读出噪声、暗电流、坏点、运动模糊）**不由这套机制提供**。要做视觉域随机化得自己在图像上加，或依赖渲染器侧的能力。

#### 2.5.4 IMU：本仓库中建模最完整的传感器

`IMU` 是唯一把缺陷参数**按三个子传感器 × 五个维度**全展开的 `[CODE]` `options.py:474-566`：

| | `resolution` | `cross_axis_coupling` | `noise` | `bias` | `random_walk` |
|---|---|---|---|---|---|
| **加速度计** `acc_*` | ✅ | ✅ | ✅ | ✅ | ✅ |
| **陀螺仪** `gyro_*` | ✅ | ✅ | ✅ | ✅ | ✅ |
| **磁力计** `mag_*` | ✅ | ✅ | ✅ | ✅ | ✅ |

- `*_noise` / `*_bias` / `*_random_walk` 均为**逐轴 3 向量**，不是标量 `[CODE]` `options.py:534-552`
- `*_cross_axis_coupling` 是 **3×3 轴对齐矩阵**：对角元表示各轴对齐度（0–1），非对角元建模**跨轴失配**。可传标量（统一设非对角元）、3 向量或完整 3×3 矩阵 `[CODE]` `options.py:484-489`
- 磁力计另有 `magnetic_field`，**默认 `(0.0, 0.0, 0.5)`** `[CODE]` `options.py:553` —— 注意这不是任何真实地点的地磁值，要做磁力计实验须自行设定
- `model_post_init` 把三组参数**相加**写入基类的 `resolution`/`bias`/`noise`/`random_walk` 字段，并留有 `FIXME` 注释说这些字段应设为私有以防被直接赋值 `[CODE]` `options.py:562-568`

#### 2.5.5 触觉：两条技术路线，机制完全不同

**路线 A — 运动学/几何触觉** `[CODE]` `genesis/engine/sensors/kinematic_tactile.py`
`ContactProbeSensor`（`:1110`）、`ContactDepthProbeSensor`（`:975`）、`KinematicTaxelSensor`（`:1211`）。基于探针点与被追踪几何的**接触/穿透深度查询**，轻量。

**路线 B — 弹性体标记位移触觉**（重点）`[CODE]` `genesis/engine/sensors/point_cloud_tactile.py:1949`、配置 `genesis/options/sensors/tactile.py:396-470`

`ElastomerTaxel` 实现的是 **HydroShear 风格的 marker displacement，数据来源是 Genesis 的 SDF 查询** —— **不是**跑一个真的 FEM 弹性体。机制拆开是三部分：

1. **膨胀（dilation）**：被追踪几何压入胶层产生的面内隆起。核函数是高斯 `exp(-lambda_d * r^2)`，`lambda_d` 越大越尖锐局部。
2. **剪切（shear）**：被追踪表面采样点的切向位移，用另一个高斯核 `exp(-lambda_s * r^2)` 扩散到邻近探针。
3. **可压缩性混合** `compressibility ∈ [0,1]`（默认 `1`）—— 这是最精妙的一个参数：
   - `1` = **完全可压缩**：只有 `exp(-lambda_d r^2)` 的**局部**集中隆起，无远场影响；
   - `0` = **完全不可压缩**：面内位移是压深场的**逆拉普拉斯的梯度**（`~ r_hat / r`），即**全局体积守恒的拉伸**，影响整个传感器但中心偏软；
   - 中间值把两个核**各自峰值归一化后按权叠加**，同时得到尖锐局部隆起与全局拉伸。

**`elastomer_thickness`（胶层厚度）的物理含义**值得单独记 `[CODE]` `tactile.py:441-451`：底面粘接在刚性背板上（等价于平板 FEM 会用的 Dirichlet 边界条件）。设为 `>0` 且 `compressibility<1` 时，全局面内响应变成**该厚度不可压缩弹性层**的响应，而非自由空间 `1/r`：

- 远小于厚度的压痕特征 → 几乎不产生面内表面运动（不可压缩半空间极限）
- 与厚度可比的波长 → 响应最强
- 长程场 → 恢复 `1/r` 挤压流

**网格布局走 FFT 加速**（精确谱层解），非网格布局走直接路径（把 `1/r` 核在尺度 `h` 上正则化为 `r_hat * r / (r^2 + h^2)` 做近似）。默认 `elastomer_thickness=0` 保留自由空间核，在探针间距处正则化 —— 源码明确说明这**只是数值保护，不是物理尺度**，要物理地控制全局响应就必须显式设厚度。`[CODE]` `tactile.py:449-451`

**一个已在源码中标注的近似**：`probe_gain` 作为后处理线性缩放施加，对切向膨胀与剪切分量精确，但对法向膨胀项**只是近似** —— 后者按 `depth**normal_exponent` 缩放，理想上应按 `gain**normal_exponent` 而非 `gain` 缩放。增益接近 1 时误差小。`[CODE]` `tactile.py:421-426`

**触觉专有的三种传感器伪影**（可选混入，非默认）`[CODE]` `genesis/engine/sensors/tactile_shared.py`、`genesis/options/sensors/tactile.py`：

| 伪影 | 混入类 | 建模内容 |
|---|---|---|
| **粘弹迟滞** | `ViscoelasticHysteresisMixin`（`tactile_shared.py:582`） | 胶层的时间相关响应，加载/卸载不重合 |
| **空间串扰** | `SpatialCrosstalkMixin`（`tactile_shared.py:808`） | 相邻 taxel 之间的信号串扰 |
| **接触迟滞** | `ContactHysteresisOptionsMixin`（`tactile.py:243`） | 接触通断的阈值迟滞 |

#### 2.5.6 激光雷达 / 深度：光线投射路径

`RaycasterSensor` `[CODE]` `raycaster.py:504`，配置 `options.py:610-655`：

- **加速结构**：BVH（`BVHContext`，`raycaster.py:47`；`RaycastContext`，`:93`）
- **三种投射模式** `[CODE]` `genesis/options/sensors/raycaster.py`：`GridPattern`（`:58`）、`SphericalPattern`（`:150`，即典型旋转式 lidar）、`DepthCameraPattern`（`:202`）
- **量程语义**：`min_range` 默认 `0.0`，`max_range` 默认 `20.0` m，`no_hit_value` 未指定时**回落为 `max_range`** —— ⚠️ 意味着"打空"和"打到 20 m 处"在默认配置下**读数无法区分**，需要显式设 `no_hit_value` 才能分辨 `[CODE]` `options.py:639-640`
- `max_range <= min_range` 直接报错 `[CODE]` `options.py:641-645`
- **性能开关**：`return_points=False` 时只算命中距离不返回逐射线命中点，**内存占用与每步开销降到约四分之一** `[CODE]` `options.py:628-630`
- **噪声**：`Raycaster` 继承 `SimpleSensorOptions`，因此**支持** `noise` / `bias` / `random_walk` / `resolution`

**`DepthCamera` 是 `Raycaster` 的子类** `[CODE]` `options.py:658-666` —— 即深度图这条路走的是光线投射而非渲染管线。这一点在选型时要注意：它与相机渲染出的深度**是两套不同实现**，性能特征和产物语义都不同。

#### 2.5.7 「默认理想化」—— 本节最需要记住的一条

**所有硬件缺陷参数的默认值都是 `0.0`**：`delay=0`、`jitter=0`、`noise=0`、`bias=0`、`random_walk=0`、`resolution=0`（不量化）。`[CODE]` `options.py:90-92,241-243`

**含义**：不显式配置时，Genesis 的传感器输出的是**理想真值**。这与 `lw_benchhub` 那种"根本没有噪声模型"不同 —— Genesis **有**完整的机制，只是**不默认开启**。做 sim-to-real 或鲁棒性研究时，**必须自己把这些参数配上**，否则会训出一个只在无噪世界里成立的策略。

### 2.6 渲染：把路径追踪当作精度基线

**设计出发点**：机器人领域从现成工具里拿不到它需要的渲染器 —— 游戏引擎为视觉吸引力优化且重度依赖 baking；离线渲染器物理准确但每帧动辄几分钟。机器人需要的是**几百万帧、看起来像真实相机拍到的、快到能大规模评估策略**。`[官网]` `Genesis_world_02.txt:140`

Nyx 的三条设计准则 `[官网]` `Genesis_world_02.txt:144-157`：

| 准则 | 具体做法 |
|---|---|
| **效率** | 目标：单张高端消费级 GPU 上 **4 ms 内渲出无噪点 1080p 帧**，不做 baking、不做 ghosting。手段：visibility buffer、bindless GPU 驱动架构、MSAA、硬件光线追踪、硬件矩阵核心、视频压缩，全部围绕 GPU 占用率调过 |
| **最小化 sim-to-real gap** | **路径追踪是基线**，只在"不损害下游模型从图像里学到的信号"的地方才用光栅化捷径。多次反弹光照、软阴影、间接光照结构上正确，叠加物理扎实的相机模型。HDRI 管线用**测量的辐照度**打光；资产来自内部扫描与摄影测量，而非手绘替身 |
| **与 Genesis 紧耦合** | Nyx **由批量物理驱动**，而不是逐场景执行 —— 数千个并行 rollout 各有自己的场景、光照、相机轨迹，全走同一条管线。**这一点是把"渲染吞吐量"变成"评估吞吐量"的关键** |

**三条渲染路径**（都以**相机传感器**的形式接进仿真环境）`[README]` `README.md:41`：

| 路径 | 类型 | 定位 |
|---|---|---|
| **Nyx** | 实时路径追踪 | Genesis 自研，面向机器人场景；**独立仓库 `genesis-nyx`**，需单独安装 |
| **Luisa** | DSL 光线追踪 | 更偏光追 |
| **Pyrender** | 光栅化 | 快速调试与基础可视化 |

> **理解要点**：渲染层不是"单独做一张漂亮图片"，而是**直接决定策略看到什么输入**。对主流机器人基础模型来说视觉输入往往就是策略判断任务状态的主要依据，光照、材质反射、阴影、相机位姿、景深、背景纹理都会影响模型输出。`[文章]` `Genesis_world_01.txt:112-114`
>
> **与评测的耦合**：§4.3 的"视觉扰动轴"能不能成立，很大程度取决于渲染层能不能**稳定地批量生成**这些扰动。`[文章]` `Genesis_world_01.txt:116`

**3D Gaussian Splats 的角色**：在网格重建力有不逮的地方，splats 延伸同一原则。官方点名"重点解决的更硬的问题"是**把基于图像的光照和基于 splat 的几何对齐起来**，让捕获资产能正确参与路径追踪的光传输。`[官网]` `Genesis_world_02.txt:149`

### 2.7 Quadrants：跨平台编译器与"调度开销"这个真瓶颈

**它是什么**：约 2025 年年中从 **Taichi fork** 而来（名字保留以体现出身）。kernel 用**纯 Python** 写，经 **LLVM JIT** 编译到 CUDA / ROCm / Apple Metal / Vulkan / x86 / ARM64。`[官网]` `Genesis_world_02.txt:203`；`[README]` `README.md:42`

> ⚠️ **fork 时间点两处材料不一致**：文章 01 写"2025 年 6 月从 Taichi 分叉"`Genesis_world_01.txt:49`，文章 02 写"大约一年前"（相对 2026-05 博客即 2025 年年中）`Genesis_world_02.txt:203`。二者大致吻合，精确月份以官方仓库为准。**Quadrants 是独立仓库，本仓库中无其源码。**

**核心洞察 —— 瓶颈不在单个 kernel，而在调度**：仿真规模变大后，成本从"逐 kernel 计算"转向"**在每个物理步里调度大量小 kernel 的开销**"。机器人仿真里有大量小 kernel：碰撞检测、约束求解、粒子更新、渲染前后数据整理、批量环境状态更新。`[官网]` `Genesis_world_02.txt:207`

四路同时攻这个开销 `[官网]` `Genesis_world_02.txt:207-211`：

1. **内核图（kernel graph）**：每个物理步记录成**单一 kernel graph**，CUDA 上硬件加速（SM90+ 还支持条件循环），其他后端软件实现 → 从每个 top-level 循环里去掉启动延迟；
2. **流并行**：独立 kernel 通过 streams 重叠，在同一块 GPU 上并行而非序列化；
3. **多级 launch context 缓存**：即便许多小 kernel 连续触发，dispatch 开销保持在**亚微秒**；
4. **三层编译产物缓存**：磁盘上的 compiled kernel + PTX + fast-cache 层。**切换场景复用缓存 kernel 而不触发重编译**；CI 与迭代运行几乎瞬时启动 —— 宣称 **>10× 加速，启动时间从分钟压到秒**。

**其他工程点**：

- SIMT 原语映射到各后端原生等价物（NVIDIA 32-warp / AMD 64-wave / Metal subgroup）→ 手调的接触求解器可以**不带任何跨平台分支**地跑；`[官网]` `Genesis_world_02.txt:205`
- **反向模式自动微分**从实验特性升级为**每个后端的一等公民**，可微仿真可在与策略部署相同的硬件上跑；`[官网]` `Genesis_world_02.txt:205`
- 提供**纯 Python 后端**，用于调试与系统化覆盖测试；`[官网]` `Genesis_world_02.txt:205`
- 张量两种可互换类型：`field`（峰值运行时吞吐）与 `ndarray`（快启动、短编译）；统一封装可在运行时切换而不改调用代码；`[官网]` `Genesis_world_02.txt:213`
- 与 ML 栈互操作：张量通过 **DLPack** 与 PyTorch 共享设备内存；Metal 上共享同一 command queue 使零拷贝不引入同步开销。`[官网]` `Genesis_world_02.txt:213`

**宣称收益**：在操作与移动基准上最高 **4.6× 运行时加速**。`[官网]` `Genesis_world_02.txt:203`

### 2.8 sim-to-real gap 的**可归因**分解（方法论，非代码）

这是 Genesis 处理 sim-real gap 的方式与多数工作最不同的一点：**强调可归因，而不是只看黑盒指标**。`[文章]` `Genesis_world_01.txt:19`

**gap 的三个来源层** `[官网]` `Genesis_world_02.txt:109-114`：

| 层 | 具体内容 |
|---|---|
| **视觉保真度** | 材质属性、光照模型、相机特性需对齐真机传感链路 |
| **运动学与动力学** | 关节行为、摩擦、接触的精确建模 |
| **底层控制** | 真机控制器要被**一模一样地复刻**，包括时序、延迟、通信特性 |

**定位手段 —— 实时并排测试台**：仿真器与实体机器人**从同一初始状态并行运行**；策略输入（相机帧、本体感受信号）可以**独立选择来源** —— 来自仿真、来自真机、或二者的**可调混合**。**每次只换一层，看哪里开始发散**，就能把 gap 归因到物理 / 渲染 / 通信 / 控制的具体层，而不是坍缩成一个二值成功/失败。`[官网]` `Genesis_world_02.txt:116`

**验证结果**（`[官网]`，14 任务 × 200 episode × 1,000,000 次 bootstrap，三种模型规模 Small/Medium/Large）`Genesis_world_02.txt:125-127`：

| 指标 | 值 | 含义 |
|---|---|---|
| **Pearson 相关系数** | **0.8996**（95% CI `[0.7439, 0.9314]`） | 仿真忠实反映真机性能**趋势** |
| **MMRV**（Mean Maximum Rank Violation，SimplerEnv 提出） | **0.0166**（95% CI `[0.0102, 0.0474]`） | 仿真很好地保留了不同模型之间的**排序** |
| **FID 度量的真机—仿真差距** | 比次优替代仿真器再**小 45%** | 图像分布层面的接近程度 |

**一个值得记住的负面结论**：开环指标（固定数据集上动作预测的 R² 和 MAE）**并不能反映真机性能差异**。它对发现大幅波动和做 sanity check 有用，但一旦落到窄带里，模型之间的差异在开环上就无法分辨 —— **闭环指标信息量显著更大**。`[官网]` `Genesis_world_02.txt:127`

> **"数字孪生"在这里的含义**：不只是把一个工位的 3D 模型搬过来，而是把栈的每一层 —— 从执行器动力学到像素渲染 —— 都忠实复刻一遍。官方的判断是"只要在最底层细节上投入足够工程注意力，sim-to-real gap 可以被压到几乎可以忽略的程度"。`[官网]` `Genesis_world_02.txt:134`

---

## 3. 架构与模块

### 3.1 官方宣传的四层栈 vs 仓库里实际有什么

官方 README 与博客都把 Genesis World 描述为**四层协同设计**的栈。但这四层**并不都在 `genesis-world` 这个 Python 包里** —— 这是读文档最容易被误导的一点，先看这张对照表：

| 宣传层次 | 职责 | 在 `genesis-world` 包里吗？ | 证据 |
|---|---|---|---|
| **Simulation Interface** | 场景搭建、实体/材料/传感器 API、并行环境 | ✅ **在**（`genesis/engine/scene.py`、`options/`） | `[CODE]` |
| **Physics**（统一多物理求解器 + 耦合器） | 刚体 / FEM / MPM / SPH / PBD / SF + 三种耦合器 | ✅ **在**（`genesis/engine/solvers/`、`couplers/`） | `[CODE]` |
| **Render**（Nyx） | 光追渲染、传感器级真实感 | ❌ **不在** —— 独立包 `gs-nyx`，作为**插件**装 | `[CODE]` 见下 |
| **Compiler**（Quadrants） | Python kernel → LLVM JIT → 多后端 | ❌ **不在** —— 独立包 `quadrants`，作为**依赖**导入 | `[CODE]` `genesis/__init__.py:18` |

**Nyx 的确凿证据**（这是本节最重要的一条）`[CODE]`：

```
grep -rn -i "nyx" genesis/ --include=*.py   →  0 处命中
grep -rn -i "luisa"    genesis/ --include=*.py  →  49 处
grep -rn -i "pyrender" genesis/ --include=*.py  → 150 处
```

`nyx` 在整个 v1.3.3 代码库中**只出现在三个非代码位置**：
- `README.md:128` —— 安装表里的一行：`| Nyx renderer | pip install gs-nyx —— 见 genesis-nyx 仓库 |`
- `RELEASE.md:56` —— "This small release fixes support of the Nyx rendering plugin"
- `.github/workflows/nyx_plugin.yml` —— 独立的 CI workflow，在 `:112` 装 `torch --index-url .../cu128`、`:121` 装 `gs-nyx`

也就是说 **Nyx 是"插件"（plugin）而不是"层"**。包内自带的渲染后端是 LuisaCompute（光追）与 PyRender（光栅化）。

**Quadrants 则相反 —— 它是硬依赖**：`genesis/__init__.py:18` 就是 `import quadrants as qd`，`gs.init()` 内部（`:222` / `:264` / `:290`）直接配置它。没有 Quadrants，Genesis 根本 import 不进来。

> ⚠️ **对复现的影响**：如果你按博客的印象以为"装了 `genesis-world` 就有 Nyx 的照片级渲染"，会发现 `gs.renderers` 下根本没有对应的类（见 §3.5）。要用 Nyx 必须**额外** `pip install gs-nyx`，且它有自己的 CUDA 版本要求。

### 3.2 顶层包结构 `[CODE]`

```
genesis/
├── __init__.py        # gs.init()、公开命名空间的汇出点
├── _main.py           # CLI 入口（gs 命令）
├── version.py         # __version__ = "1.3.3"
├── constants.py       # 枚举：backend、integrator、几何类型等
├── datatypes.py       # 张量/数组类型别名
├── typing.py          # 类型注解工具
├── engine/            # ★ 仿真核心（见 §3.3）
├── options/           # ★ 所有用户可见的配置类（见 §3.4）
├── vis/               # ★ 可视化与渲染（见 §3.5）
├── recorders/         # 数据录制（视频、npz、csv…）
├── grad/              # 可微分仿真支持
├── ext/               # 第三方代码 vendoring
├── utils/             # 网格处理、几何、USD/URDF/MJCF 解析、缓存等
├── assets/            # 内置资产（Franka、Go2、地形贴图…）
├── logging/           # 带样式的日志
├── repr_base.py       # 对象的 __repr__ 基类（Genesis 打印很花哨的原因）
└── styles.py          # 终端配色
```

### 3.3 `genesis/engine/` —— 仿真核心 `[CODE]`

```
engine/
├── scene.py             # ★ Scene：用户几乎所有操作的入口
├── simulator.py         # Simulator：被 Scene 持有，真正驱动各 solver 步进
├── interactive_scene.py # 交互式场景（viewer 里可拖拽）
├── solvers/             # 各物理求解器
├── couplers/            # 求解器之间的耦合（见 §2.2）
├── entities/            # 场景中的实体对象
├── materials/           # 材料模型
├── sensors/             # ★ 传感器子系统（见 §2.5）
├── states/              # 状态快照/回放
├── boundaries/          # 边界条件
├── force_fields.py      # 外力场
├── bvh.py               # 层次包围盒（碰撞/光线投射加速）
└── mesh.py              # 网格表示
```

**`solvers/`（8 个）**：`base_solver.py`、`rigid/`（子包，最复杂）、`fem_solver.py`、`mpm_solver.py`、`sph_solver.py`、`pbd_solver.py`、`sf_solver.py`（stable fluid）、`kinematic_solver.py`、`tool_solver.py`

**`couplers/`（3 种）**：`legacy_coupler.py:22 LegacyCoupler`（默认）、`sap_coupler.py:141 SAPCoupler`（另含 20 个物料对专用的接触/约束 handler，位于 `:1799–3657`）、`ipc_coupler/coupler.py`

**`entities/`** —— 与 solver 一一对应，外加两个特殊的：

| 文件 | 对应 |
|---|---|
| `base_entity.py` | 所有实体的基类 |
| `rigid_entity/` | 刚体（子包，含 link / joint / geom / 求解 IK 等） |
| `fem_entity.py` / `mpm_entity.py` / `sph_entity.py` / `pbd_entity.py` / `sf_entity.py` | 各软体/流体求解器的实体 |
| `particle_entity.py` | 粒子类实体的公共基类 |
| `tool_entity/` | 工具（刚性驱动器，用于操作软体） |
| `drone_entity.py` | 无人机（带螺旋桨模型） |
| `hybrid_entity.py` | **混合实体** —— 同一物体的不同部分用不同求解器 |
| `emitter.py` | 发射器（持续产生流体/颗粒） |

**`materials/`** —— 按求解器分子包：`rigid.py`、`kinematic.py`、`tool.py`、`hybrid.py`、`FEM/`、`MPM/`、`PBD/`、`SPH/`、`SF/`。用法是 `gs.materials.<求解器>.<材料>`，例如 `gs.materials.PBD.Cloth()`、`gs.materials.SPH.Liquid()`。

### 3.4 `genesis/options/` —— 用户配置面 `[CODE]`

这是**实际写代码时接触最多的目录**，因为 Genesis 的设计哲学是"所有行为通过 options 对象声明式配置"（Pydantic 模型，带校验）。

| 文件 | 汇出到 | 内容 |
|---|---|---|
| `solvers.py` | `gs.options.*` | `SimOptions:18`、各 solver options、三个 coupler options（`:81` Base / `:89` Legacy / `:123` SAP / `:196` IPC） |
| `morphs.py` | `gs.morphs.*` | 形态：`Box:224`、`Cylinder:319`、`Sphere:383`、`Plane:444`、`Mesh:694`、`MeshSet:859`、`MJCF:868`、`URDF:1005`、`Drone:1156`、`Terrain:1296`、`USD:1508`、`Nowhere:169` |
| `renderers.py` | `gs.renderers.*` | `Rasterizer:51`、`RayTracer:63`、`BatchRenderer:140`、`SphereLight:20` |
| `sensors/` | `gs.sensors.*` | 传感器 options（详见 §2.5） |
| `surfaces.py` / `textures.py` | `gs.surfaces.*` / `gs.textures.*` | 外观材质与贴图 |
| `vis.py` | — | `VisOptions`、`ViewerOptions` |
| `profiling.py` | — | `ProfilingOptions`（`show_FPS` 等） |
| `recorders.py` | `gs.recorders.*` | 录制配置 |
| `misc.py` / `options.py` | — | 公共基类与杂项 |

`gs.init()` 之后可用的顶层命名空间（`genesis/__init__.py:514-527`）：
`morphs`、`sensors`、`renderers`、`surfaces`、`textures`、`states`、`materials`、`force_fields`、`recorders`、`options`，以及 `Mesh`、`Scene` 两个类。

### 3.5 `genesis/vis/` —— 可视化与渲染 `[CODE]`

```
vis/
├── visualizer.py         # Visualizer：Scene 持有，管理 viewer + 所有 camera
├── viewer.py             # 交互式窗口
├── camera.py             # Camera 对象（render() 出 rgb/depth/segmentation/normal）
├── rasterizer.py         # 光栅化后端（PyRender）
├── rasterizer_context.py # 光栅化上下文
├── raytracer.py          # 光追后端（LuisaCompute）
├── batch_renderer.py     # 批量渲染（多环境并行出图）
├── keybindings.py        # viewer 快捷键
└── viewer_plugins/       # viewer 插件机制
```

> ⚠️ **版本落差提示** `[CODE]`：README 宣传"三条渲染路径"，而 v1.3.3 的 `genesis/options/renderers.py` 里**只有 `Rasterizer` / `RayTracer` / `BatchRenderer` 三个类，没有任何 Nyx 相关的 `RendererOptions` 子类**。若你在文档里看到 `gs.renderers.Nyx(...)` 之类的写法，那要么来自 `gs-nyx` 插件自己注册的入口，要么是更新的版本 —— **以你本机 `python -c "import genesis as gs; print(dir(gs.renderers))"` 的输出为准**。

### 3.6 一次仿真的数据流

```
用户代码
  │
  ├─ gs.init(backend=gs.gpu)                    → 初始化 Quadrants 后端
  │
  ├─ scene = gs.Scene(sim_options=…,            → 构造 Scene，内部 new 一个 Simulator
  │                   coupler_options=…,           各 *_options 分发给对应 solver
  │                   renderer=…)                  renderer 交给 Visualizer
  │
  ├─ scene.add_entity(morph=…, material=…)      → 按 material 类型路由到对应 solver
  ├─ scene.add_sensor(gs.sensors.IMU(…))        → 注册进 SensorManager
  ├─ cam = scene.add_camera(…)                  → 注册进 Visualizer
  │
  ├─ scene.build(n_envs=2048)                   → ★ 编译期：kernel JIT、内存分配、
  │                                                 并行环境铺开。此后不能再 add_*
  │
  └─ while True:
        scene.step()                            → Simulator 依次推进各 solver，
        │                                          再由 coupler 处理跨求解器交互
        scene.read_sensors()                    → 从 SensorManager 取（带延迟/噪声的）读数
        cam.render()                            → Visualizer 出图
```

**关键约束**：`scene.build()` 是一道**不可逆的分界线** —— 之前是声明期（可以 `add_entity` / `add_sensor` / `add_camera`），之后是运行期（只能 `step` / `reset` / 读写状态）。这是 Genesis 能把整个场景编译成 GPU kernel 并同时跑几千个环境的前提。

---

## 4. 关键特性

### 4.1 大规模并行环境 `[CODE]`

`scene.build(n_envs=N)` 是并行化的唯一开关（`genesis/engine/scene.py:864`）：

```python
scene.build(
    n_envs=2048,                  # 0 = 不加 batch 维；>0 = 所有状态张量第 0 维变成 batch
    env_spacing=(1.0, 1.0),       # 仅影响可视化摆放，不改变仿真位姿
    n_envs_per_row=None,          # 默认 sqrt(n_envs)
    center_envs_at_origin=True,   # 仅可视化
)
```

**两个容易踩的点** `[CODE]`：
- `n_envs=0` 与 `n_envs=1` **语义不同** —— 前者返回的状态**没有** batch 维，后者有一个长度为 1 的 batch 维。写通用代码时别混用。
- `env_spacing` / `n_envs_per_row` / `center_envs_at_origin` 三个参数**只影响可视化**，docstring 明确写了 "does not change simulation-related poses"。想让环境之间物理隔离，靠的是 batch 维本身，不是间距。

并行度的实测参考见 §8 与经验层（本机 A800-40GB 上 Go2 训练达到 151,839 steps/sec @ 2048 envs）。

### 4.2 跨后端与多平台 `[CODE]`

`gs.init(backend=…)` 支持的取值（`genesis/constants.py:166-171`）：

| 取值 | 说明 |
|---|---|
| `gs.cpu` | CPU |
| `gs.gpu` | **自动挑选**当前平台可用的 GPU 后端（最常用） |
| `gs.cuda` | 强制 NVIDIA CUDA |
| `gs.amdgpu` | AMD ROCm |
| `gs.metal` | Apple Metal |

并行级别是内部枚举 `PARA_LEVEL`（`constants.py:189-192`）：`NEVER`（CPU）/ `PARTIAL`（GPU + 非批量场景）/ `ALL`（GPU + 批量场景）—— 也就是说**只有 GPU + `n_envs>0` 才吃满并行**。

### 4.3 可微分仿真 `[CODE]`

由 `SimOptions.requires_grad` 开启（`genesis/options/solvers.py:56`，默认 `False`），配合 `scene.backward(loss)`（`scene.py:1021`）。

**开启可微后有一条硬约束**（`solvers.py:71-77`，违反直接 `raise_exception`）：

```
requires_grad=True  ⟹  substeps_local % substeps == 0
```

`substeps_local` 是"在 GPU 显存里保留多少个子步"。非可微模式下它被强制设为 1 以省显存（`:63-68`）；可微模式下它必须能整除到 `substeps`，因为反向传播要沿子步回放。**显存占用随 `substeps_local` 线性增长** —— 这是可微模式最容易 OOM 的地方。

### 4.4 声明式配置（Pydantic）`[CODE]`

所有 options 都是 Pydantic 模型，带类型校验和 `model_post_init` 后置检查。好处是**配置错误在 `Scene()` 构造时就报错，而不是跑到第 500 步才炸**。

`SimOptions` 的核心字段（`solvers.py:54-59`）：

| 字段 | 默认 | 说明 |
|---|---|---|
| `dt` | `1e-2` | 每个 `scene.step()` 的时长（秒） |
| `substeps` | `1` | 每步的子步数；精度/稳定性 ↑，耗时**最坏线性增长、实践中次线性** |
| `substeps_local` | `None`→1 | 仅可微模式有意义（见 §4.3） |
| `gravity` | `(0, 0, -9.81)` | N/kg |
| `floor_height` | `0.0` | 地面高度（米） |
| `requires_grad` | `False` | 可微开关 |

> ⚠️ **`SimOptions` 与各 solver options 的覆盖关系** `[CODE]` `solvers.py:22-27`：同名参数（典型是 `dt`）**在 solver options 里给就覆盖 `SimOptions` 里的值，只对那个 solver 生效**。同时给 `substeps` 和一个隐含不同子步数的 solver `dt` 会**直接抛异常**，不会静默取其一 —— 这点比很多仿真器友好。

### 4.5 多格式资产加载 `[CODE]`

`gs.morphs.*`（`genesis/options/morphs.py`）覆盖：

- **程序化几何**：`Box` `Cylinder` `Sphere` `Plane`（`:224/319/383/444`）
- **机器人描述**：`MJCF`（`:868`）、`URDF`（`:1005`）—— 依赖里带 `xacro`，所以 `.urdf.xacro` 会先被预处理成纯 URDF（`pyproject.toml` 注释）
- **网格**：`Mesh`（`:694`）、`MeshSet`（`:859`）—— 经 trimesh，支持 `.obj/.stl/.dae/.glb`（含 Draco 压缩）
- **USD**：`USD`（`:1508`）
- **地形**：`Terrain`（`:1296`）—— 高度场，靠 `rtree` 做射线投射转换
- **无人机**：`Drone`（`:1156`）—— 带螺旋桨模型
- **占位**：`Nowhere`（`:169`）—— 先注册后定位

### 4.6 传感器套件

见 §2.5（含完整清单、缺陷建模两层继承、以及"默认全部理想化"的重要提醒）。

### 4.7 状态快照与断点续跑 `[CODE]`

`scene.py` 提供一组状态 API：

| 方法 | 行号 | 用途 |
|---|---|---|
| `get_state()` | `:1063` | 取当前 `SimState` |
| `reset(state=None, envs_idx=None)` | `:975` | 整体或**按环境子集**重置；可重置到指定状态 |
| `save_checkpoint(path)` | `:1546` | 存盘 |
| `load_checkpoint(path)` | `:1565` | 读盘 |
| `dump_ckpt_to_numpy()` | `:1524` | 转成 `dict[str, np.ndarray]` |

`reset(envs_idx=…)` 的**按环境子集重置**是 RL 训练的关键能力 —— 只重置已经 terminate 的那些环境，不打断其余的。

### 4.8 调试可视化 `[CODE]`

`scene.py:1116-1385` 一整组 `draw_debug_*`：`line` `arrow` `frame` `frames` `mesh` `sphere` `spheres` `box` `points` `frustum` `trajectory` `path`。配合 `update_debug_objects` / `clear_debug_object(s)`（`:1476-1501`）。

`draw_debug_frustum(camera)` 画相机视锥、`draw_debug_path(qposs, entity)` 画一整条关节轨迹 —— 这两个在调运动规划时特别省事。

### 4.9 录制 `[CODE]`

两条路：
- `camera.start_recording()` / `stop_recording()` —— 靠 `av` 直接流式写视频文件
- `scene.start_recording(data_func, rec_options)`（`scene.py:677`）+ `gs.recorders.*` —— **通用数据录制**，你给一个取数函数，它按配置落盘（视频 / npz / csv 等）

---

## 5. 安装与依赖

### 5.1 Python 与 PyTorch 的前置要求 `[CODE]` `[README]`

```
requires-python = ">=3.10,<3.14"      # pyproject.toml:9
```

**PyTorch 必须先单独装**，README 明确要求按 [官方指引](https://pytorch.org/get-started/locally/) 选对 CUDA 版本再装 Genesis —— 它**不在** `dependencies` 列表里（`pyproject.toml:11-77` 通读确认无 `torch`）。这是刻意的：让用户自己控制 CUDA 版本。

> ⚠️ 依赖里没有 torch，但代码里到处 `import torch`（`scene.read_sensors()` 的返回类型就是 `dict[type[Sensor], torch.Tensor]`）。**先装 Genesis 再装 torch 是常见的失败顺序** —— 先 torch。

### 5.2 四种安装方式 `[README]`

| 场景 | 命令 |
|---|---|
| **稳定版**（推荐先试这个） | `pip install genesis-world` |
| **跟 main 分支** | `pip install git+https://github.com/Genesis-Embodied-AI/genesis-world.git`（**不会自动更新**，换 HEAD 后要手动重装） |
| **要改代码 / 贡献** | `git clone …` → `cd genesis-world` → `pip install -e ".[dev]"` |
| **uv** | `git clone …` → `uv sync` → `uv pip install torch --index-url …` → `uv run examples/rigid/single_franka.py` |

> `[README]` 原文的一条运维建议：editable 安装下**每次移动 HEAD 之后都应重跑 `pip install -e ".[dev]"`**，以保证依赖与 entrypoint 同步。（这暗示仓库的 entrypoint / Cython 扩展会随 commit 变化 —— `build-system` 里有 `cython>=3.0.0`。）

### 5.3 核心依赖清单 `[CODE]` `pyproject.toml:11-77`

**最需要注意的一条：`quadrants==1.3.0` 是精确 pin**（`:13`）。这是编译器层，版本必须与 `genesis-world` 严格配套 —— 单独升级它极可能直接 import 失败。README 也说明 "Quadrants is bundled with Genesis automatically; no extra install."

按功能分组（注释均来自 `pyproject.toml` 原文）：

| 组 | 包 | 备注 |
|---|---|---|
| **编译器/数值** | `quadrants==1.3.0`、`numpy>=1.26.4`、`numba`、`pydantic>=2.11.0`、`frozendict`、`psutil`、`py-cpuinfo` | quadrants 精确 pin |
| **刚体参考实现** | `mujoco>=3.2.5` | 刚体动力学与碰撞的参考 |
| **网格处理** | `trimesh>=4.8.2`（4.8.2 才修好 `to_color()` 的 linear/sRGB 转换）、`libigl!=2.6.2`（Windows 无预编译轮子）、`pymeshlab`、`tetgen==0.8.2`、`PyGEL3D`、`fast_simplification>=0.1.12`、`coacd`（凸分解）、`rtree` | 精确/排除 pin 较多 |
| **格式解析** | `xacro`、`pycollada`（`.dae`）、`pygltflib==1.16.0`、`DracoPy`（Draco 压缩 glb）、`vtk`、`OpenEXR` | |
| **渲染（光栅化）** | `pyglet>=1.5,!=2.1.8`、`freetype-py`、`PyOpenGL>=3.1.4` | `pyglet` 排除 2.1.8（破坏 headless 窗口） |
| **批渲染** | `gs-madrona==0.0.10`；**仅 Linux + x86_64/AMD64** | 平台条件依赖 |
| **图像/视频** | `Pillow>11.0`（11.0 起 PNG 导出快很多）、`opencv-python`、`scikit-image`、`moviepy>=2.0.0`、`av` | |
| **约束求解** | `z3-solver<4.15.5.0`（≥4.15.5.0 Linux 无预编译轮子）——用于从碰撞排除表反推 `contype`/`conaffinity` 位掩码 | |
| **SPH 表面重建** | `pysplashsurf==0.14.*` | 粒子→表面网格 |

> 💡 **这张表的实用价值**：Genesis 的依赖里有 **6 处带上下界或排除的 pin**（`trimesh` / `libigl` / `pyglet` / `z3-solver` / `Pillow` / `pygltflib`），每条都对应一个已知的上游破坏。**升级这些包之前先看 `pyproject.toml` 里的原文注释**，别凭 "装个新版应该没事" 的直觉动手 —— 这是和 `lw_benchhub` 的 `numpy==1.26.0` 同类的陷阱。

### 5.4 可选扩展 `[README]` `README.md:126-130`

| 扩展 | 命令 | 平台限制 |
|---|---|---|
| **IPC 求解器**（uipc 后端） | `pip install pyuipc` | **Linux / Windows x86 + NVIDIA GPU** |
| **Nyx 渲染器** | `pip install gs-nyx` | 见 [genesis-nyx](https://github.com/Genesis-Embodied-AI/genesis-nyx) |

> ⚠️ **两条都不是默认装的**。§2.2 讲的三种耦合器里，**IPC 那一支需要额外装 `pyuipc` 才能用**；§3.1 讲的 Nyx 渲染层需要额外装 `gs-nyx`。默认 `pip install genesis-world` 装出来的是 **LegacyCoupler + PyRender/Luisa/Madrona**。

### 5.5 `[dev]` 与 `[docs]` extras `[CODE]` `pyproject.toml:79+`

- **`dev`**：`black`、`pytest` + 插件、`syrupy`（快照测试）、`nvidia-ml-py; platform_system != 'Darwin'`、`setproctitle`、`huggingface_hub[hf_xet]`、`wandb`、`ipython`、**`mujoco>=3.10.0,<3.11.0`**、`matplotlib>=3.7.0`、`scipy`、`pre_commit`
- **`docs`**：**`sphinx==6.2.1`**（精确 pin —— sphinx 7 会挂）、`sphinx-autobuild`、`pydata_sphinx_theme`、`sphinxcontrib.spelling`

> ⚠️ **一个真实的版本冲突** `[CODE]`：主依赖要求 `mujoco>=3.2.5`（无上界），而 `dev` extra 要求 `mujoco>=3.10.0,<3.11.0`。装 `[dev]` 会把 mujoco 收紧到 3.10.x。如果你的其它工具链（例如另一个 RL 库）也 pin 了 mujoco，这里会打架 —— **建议 Genesis 单独开 conda/venv 环境**。

### 5.6 装完之后的第一件事

```bash
# 1) 确认版本与后端
python -c "import genesis as gs; print(gs.__version__)"     # 期望 1.3.3（或你装的版本）

# 2) 跑一个最小示例（会开 viewer 窗口）
python examples/rigid/single_franka.py

# 3) 无显示器的机器上，改用无 viewer 的脚本或设 show_viewer=False
```

装不上 / 跑不起来时的排查顺序见 **[排障层 `troubleshooting.md`](./troubleshooting.md)**，动手命令见 **[速查层 `quickstart.md`](./quickstart.md)**。

---

## 6. 基本使用流程

### 6.1 最小可运行程序 `[CODE]` `examples/tutorials/hello_genesis.py`

```python
import genesis as gs

gs.init(backend=gs.cpu)

scene = gs.Scene()
plane  = scene.add_entity(gs.morphs.Plane())
franka = scene.add_entity(gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"))

scene.build()
for i in range(1000):
    scene.step()
```

**只有 6 个动作**，而且顺序是强制的：

```
gs.init()  →  gs.Scene(...)  →  scene.add_*()  →  scene.build()  →  scene.step()
   ①              ②                  ③                 ④                ⑤
```

- ① **全局只能调一次** —— `genesis/__init__.py:70-71` 里 `if _initialized: raise_exception("Genesis already initialized.")`。想换后端必须先 `gs.destroy()`。
- ③ **必须在 `build()` 之前** —— 之后再 `add_entity` 会失败。
- ④ **`build()` 是不可逆分界线**（见 §3.6）。

> 💡 `file="xml/franka_emika_panda/panda.xml"` 是**相对于 `genesis/assets/` 的内置资产路径**，不是你磁盘上的路径。Franka、Go2 等常见机器人都自带，不用自己找模型。

### 6.2 加配置：`Scene` 的完整构造面 `[CODE]` `scene.py:94-111`

```python
scene = gs.Scene(
    sim_options       = gs.options.SimOptions(dt=0.01, substeps=1, gravity=(0,0,-9.81)),
    rigid_options     = gs.options.RigidOptions(...),
    mpm_options       = gs.options.MPMOptions(...),   # 用到哪个 solver 才配哪个
    sph_options       = gs.options.SPHOptions(...),
    fem_options       = gs.options.FEMOptions(...),
    pbd_options       = gs.options.PBDOptions(...),
    sf_options        = gs.options.SFOptions(...),
    tool_options      = gs.options.ToolOptions(...),
    kinematic_options = gs.options.KinematicOptions(...),
    coupler_options   = gs.options.SAPCouplerOptions(),        # ← 换耦合器就这一行（§2.2）
    vis_options       = gs.options.VisOptions(...),
    viewer_options    = gs.options.ViewerOptions(camera_pos=(0,-3.5,2.5),
                                                 camera_lookat=(0,0,0.5),
                                                 camera_fov=30),
    profiling_options = gs.options.ProfilingOptions(...),
    renderer          = gs.renderers.Rasterizer(),             # 或 RayTracer() / BatchRenderer()
    show_viewer       = True,
)
```

**全部参数都可省略**，每个都有默认值（`scene.py:116-130`）。默认组合是：`LegacyCouplerOptions()` + `Rasterizer()`。

> ⚠️ `show_FPS` 参数**已废弃**（`scene.py:111` 注释 `# deprecated, use profiling_options.show_FPS instead`）。

### 6.3 控制机器人 `[CODE]` `examples/tutorials/control_your_robot.py`

标准套路是 **"按名字拿 DOF 索引 → 设增益 → 发指令"**：

```python
scene.build()

# 1) 关节名 → DOF 局部索引
joints_name = ("joint1", ..., "joint7", "finger_joint1", "finger_joint2")
motors_dof_idx = [franka.get_joint(name).dofs_idx_local[0] for name in joints_name]

# 2) 配 PD 增益与力矩上限（都在 build 之后）
franka.set_dofs_kp(kp=np.array([4500,4500,3500,3500,2000,2000,2000,100,100]),
                   dofs_idx_local=motors_dof_idx)
franka.set_dofs_kv(kv=np.array([450,450,350,350,200,200,200,10,10]),
                   dofs_idx_local=motors_dof_idx)
franka.set_dofs_force_range(lower=np.array([-87,-87,-87,-87,-12,-12,-12,-100,-100]),
                            upper=np.array([ 87, 87, 87, 87, 12, 12, 12, 100, 100]),
                            dofs_idx_local=motors_dof_idx)

# 3) 发指令
franka.control_dofs_position(target_qpos, motors_dof_idx)   # 位置控制（走 PD）
scene.step()
```

**三组 API 的区别（最容易混）** `[CODE]`：

| API | 语义 |
|---|---|
| `set_dofs_position(...)` | **硬置位** —— 瞬间瞬移到该位形，**绕过动力学**。只用于初始化 / hard reset |
| `control_dofs_position(...)` | **位置指令** —— 交给内部 PD 控制器，走完整动力学 |
| `set_dofs_kp/kv/force_range(...)` | 配 PD 增益与力矩饱和 |

示例脚本里前 150 步用 `set_dofs_position` 做 hard reset，之后才切到 `control_dofs_position` —— **这个模式值得照抄**。

### 6.4 并行环境 `[CODE]` `examples/tutorials/parallel_simulation.py`

```python
B = 20
scene.build(n_envs=B, env_spacing=(1.0, 1.0))

# 对所有环境下同一个指令
franka.control_dofs_position(
    torch.tile(torch.tensor([0,0,0,-1.0,0,1.0,0,0.02,0.02], device=gs.device), (B, 1))
)

# 只对部分环境下指令，其余保持原目标不变
franka.control_dofs_position(
    torch.zeros(3, 9, device=gs.device),
    envs_idx=torch.tensor([1, 5, 7], device=gs.device),
)
```

**两个要点** `[CODE]`：
- 用 **`gs.device`** 建张量，别硬写 `"cuda:0"` —— 它跟随 `gs.init(backend=…)` 自动解析。
- **`envs_idx=` 是贯穿全库的约定**：`control_dofs_*`、`scene.reset()`、`scene.read_sensors()`、`scene.get_time()` 都接受它，用于**只作用于环境子集**。RL 里"只重置已结束的环境"就靠这个。

### 6.5 加传感器与相机 `[CODE]`

```python
imu = scene.add_sensor(gs.sensors.IMU(entity_idx=robot.idx, ...))   # build 之前
cam = scene.add_camera(res=(640, 480), pos=(1,1,1), lookat=(0,0,0), fov=45, GUI=False)

scene.build()

while True:
    scene.step()
    readings = scene.read_sensors()      # dict[type[Sensor], torch.Tensor]
    rgb, depth, seg, normal = cam.render(depth=True, segmentation=True, normal=True)
```

`scene.read_sensors(envs_idx=None)` 的返回是 **`dict[type[Sensor], torch.Tensor]`**（`scene.py:657`）—— **按传感器类型聚合、堆成一个张量**，不是按实例逐个返回。多个同类型传感器的读数会在同一个张量里。

相机可出四种图（`constants.py:178-182` `IMAGE_TYPE`）：`RGB` / `DEPTH` / `SEGMENTATION` / `NORMAL`。

**再次提醒**（§2.5.7）：传感器的 `noise` / `bias` / `random_walk` / `delay` **默认全是 0**，不显式配就是理想真值；相机则**根本没有这层噪声参数**。

### 6.6 典型工作流：RL 训练

```
① gs.init(backend=gs.gpu)
② 构造 Scene（show_viewer=False，训练时别开窗口）
③ add_entity（地形 + 机器人）、add_sensor
④ scene.build(n_envs=4096)              ← 编译一次，之后反复用
⑤ 训练循环：
     obs = 组装(scene.read_sensors(), entity.get_dofs_position(), …)
     action = policy(obs)
     entity.control_dofs_position(action)
     scene.step()
     done_idx = 判定终止(...)
     scene.reset(envs_idx=done_idx)      ← 只重置结束的环境
⑥ scene.save_checkpoint(path)
```

本机在 A800-40GB 上按此流程跑 Go2 PPO，2048 envs 达到 **151,839 steps/sec**、100 epoch 约 8 分钟 —— 详见 **[经验层 `ai_knowledge.md`](./ai_knowledge.md)**。

### 6.7 典型工作流：VLA 模型闭环评测

```
① 构造 Scene + 相机（相机是策略的输入源）
② scene.build()
③ 闭环循环：
     rgb = cam.render()[0]
     action = vla_model(rgb, instruction)     ← 视觉输入 → 动作
     robot.control_dofs_position(action)
     scene.step()
④ 按几何条件（而非图像）写断言判定成功
```

> 💡 **一条来自实践的建议**：判定"抓取是否成功"用**几何断言**（如 `torch.cdist` 算穿透、物体高度阈值）而不是看图，评测才能无人值守跑批。见经验层与 **[代码层 `code_knowledge.md`](./code_knowledge.md)**。

跑不通时按 **[排障层 `troubleshooting.md`](./troubleshooting.md)** 的「快速症状索引」查。

---

## 7. 常用 API 接口

> 本章行号均对应 v1.3.3。**几乎所有查询/控制 API 都接受 `envs_idx=` 参数**来限定环境子集，下表不再逐条重复。

### 7.1 顶层 `gs.*` `[CODE]` `genesis/__init__.py`

| API | 行号 | 说明 |
|---|---|---|
| `gs.init(backend=, precision=, seed=, debug=, ...)` | `:57` | **全局一次**。关键参数见下 |
| `gs.destroy()` | — | 释放全局状态；换后端前必须调 |
| `gs.Scene(...)` | — | 场景（见 §6.2） |
| `gs.device` | — | 当前后端对应的 torch device，**建张量时用它** |
| `gs.morphs.*` / `gs.materials.*` / `gs.sensors.*` / `gs.renderers.*` / `gs.surfaces.*` / `gs.textures.*` / `gs.options.*` / `gs.recorders.*` / `gs.force_fields.*` / `gs.states.*` | `:514-527` | 各配置命名空间 |
| `gs.Mesh` | `:514-527` | 网格对象 |

`gs.init()` 的完整参数（`:57-69`）：`backend`、`precision`（`"32"`/`"64"`）、`logging_level`、`debug`、`seed`、`eps=1e-15`、`theme`（`dark`/`light`/`dumb`）、`logger_verbose_time`、`performance_mode`、`use_deterministic_algorithms`。

> 💡 `seed=` + `use_deterministic_algorithms=True` 是复现实验的组合；官方博客宣称支持 **bit-level reproducibility** `[官网]`（未在本文档中实测验证）。
> 💡 `performance_mode=True` 值得在长训练里试 —— 但代价（编译时间、调试信息丢失）文档**未提及**。

### 7.2 `Scene` `[CODE]` `genesis/engine/scene.py`

**声明期（`build()` 之前）**

| API | 行号 |
|---|---|
| `add_entity(morph=, material=, surface=, ...)` | `:311/322/333`（三个重载） |
| `add_sensor(sensor_options) -> Sensor` | `:643` |
| `add_camera(res=, pos=, lookat=, fov=, GUI=, ...)` | `:699` |
| `add_light(...)` / `add_mesh_light(...)` | `:601` / `:560` |
| `add_emitter(...)` | `:788` |
| `add_force_field(force_field)` | `:845` |
| `add_stage(...)` | `:513` |
| **`build(n_envs=0, env_spacing=, n_envs_per_row=, center_envs_at_origin=)`** | **`:864`** |

**运行期（`build()` 之后）**

| API | 行号 | 说明 |
|---|---|---|
| `step(update_visualizer=True, refresh_visualizer=True)` | `:1081` | 推进一步；关掉两个 flag 可在无渲染训练里省时间 |
| `reset(state=None, envs_idx=None)` | `:975` | 重置（可按环境子集） |
| `read_sensors(envs_idx=None) -> dict[type[Sensor], torch.Tensor]` | `:657` | **按传感器类型聚合** |
| `render_all_cameras(...)` | `:1432` | 一次渲染所有相机 |
| `get_state()` / `get_time(envs_idx=None)` | `:1063` / `:1625` | |
| `backward(loss, ...)` | `:1021` | 可微模式反向传播 |
| `save_checkpoint(path)` / `load_checkpoint(path)` / `dump_ckpt_to_numpy()` | `:1546` / `:1565` / `:1524` | |
| `start_recording(data_func, rec_options)` / `stop_recording()` | `:677` / `:1108` | |
| `register_pre_step_callback(callback)` | `:1074` | 每步前的钩子 |
| `draw_debug_*(...)` ×12 | `:1116-1385` | 见 §4.8 |
| `destroy()` | `:289` | |

### 7.3 `RigidEntity` `[CODE]` `genesis/engine/entities/rigid_entity/rigid_entity.py`

**控制（走动力学）**

| API | 行号 |
|---|---|
| `control_dofs_position(target, dofs_idx_local=, envs_idx=)` | `:3967` |
| `control_dofs_velocity(...)` | `:3944` |
| `control_dofs_force(...)` | `:3921` |
| `control_dofs_position_velocity(...)` | `:3991` |

**PD 增益与限幅**

| API | 行号 |
|---|---|
| `set_dofs_kp(kp, dofs_idx_local=)` | `:3748` |
| `set_dofs_kv(kv, dofs_idx_local=)` | `:3765` |
| `set_dofs_force_range(lower, upper, dofs_idx_local=)` | `:3820` |

**硬置状态（绕过动力学，只用于初始化/reset）**

| API | 行号 |
|---|---|
| `set_qpos` / `set_dofs_position` / `set_dofs_velocity` | `:2152` / `:2192` / `:2175` |
| `set_pos` / `set_quat` | `:2090` / `:2121` |
| `zero_all_dofs_velocity()` | `:2299` |

**查询**

| API | 行号 | 说明 |
|---|---|---|
| `get_qpos` / `get_dofs_position` / `get_dofs_velocity` | `:2214` / `:2257` / `:2237` | |
| `get_dofs_limit` / `get_dofs_force_range` | `:2277` / `:4127` | |
| `get_dofs_force` / `get_dofs_control_force` | `:4035` / `:4015` | **两者不同**：前者是总广义力，后者只是控制器贡献的那部分 |
| `get_pos` / `get_quat` / `get_vel` / `get_ang` | `:1856` / `:1876` / `:1896` / `:1913` | 整体位姿/速度 |
| `get_links_pos` / `get_links_quat` / `get_links_vel` / `get_links_ang` | `:1930` / `:1953` / `:2049` / `:2069` | 逐 link |
| **`get_links_net_contact_force()`** | `:4365` | **接触力** —— 做接触判定/奖励最常用 |
| `get_vAABB()` / `get_terrain_height()` | `:1976` / `:2012` | |
| `get_joint(name)` / `get_link(name)` | `:1787` / `:1821` | **按名字取对象**，再读 `.dofs_idx_local` |
| `get_jacobian(link)` | `:2580` | |

**结构属性（property）**：`n_qs` `n_links` `n_joints` `n_dofs` `n_vgeoms` `n_vverts` `n_vfaces`、`links` `joints` `base_link` `base_joint` `joints_by_links`、`link_start/end` `joint_start/end` `dof_start/end` `q_start/end`、`init_qpos` `q_limit` `is_built` `is_attached`（`:2324-2547`）

**运动学与规划**

| API | 行号 | 关键默认值 |
|---|---|---|
| `inverse_kinematics(link, pos=, quat=, ...)` | `:2612` | `respect_joint_limit=True`、`max_samples=50`、`max_solver_iters=20`、`damping=0.01`、**`pos_tol=5e-4`（0.5 mm）**、**`rot_tol=5e-3`（0.28°）**、`pos_mask`/`rot_mask` 各 3 个 bool、`return_error=False` |
| `inverse_kinematics_multilink(...)` | `:2722` | 多末端同时求解 |
| `plan_path(qpos_goal, qpos_start=None, ...)` | `:3215` | `planner="RRTConnect"`、`max_nodes=2000`、`resolution=0.05`、`smooth_path=True`、`num_waypoints=300`、`ignore_collision=False`、`return_valid_mask=False` |
| `attach(...)` | `:1441` | 实体间附着 |

> 💡 **IK 的两个实用细节** `[CODE]`：
> - 目标 `pos`/`quat` 是**世界系**（docstring `:2634-2635` 明确说"不施加 morph pose offset"，与 `get_links_pos(relative=False)` 一致）。
> - `pos_mask` / `rot_mask` 允许**只约束部分自由度** —— 例如只管位置不管姿态就传 `rot_mask=[False]*3`，能显著提高求解成功率。
> - `return_error=True` 会一并返回残差，**批量场景下务必用它筛掉没收敛的解**，否则失败的 IK 会静默返回一个坏位形。

### 7.4 `Camera` `[CODE]` `genesis/vis/camera.py`

```python
cam = scene.add_camera(res=(640,480), pos=(1,1,1), lookat=(0,0,0), fov=45, GUI=False)
rgb, depth, seg, normal = cam.render(depth=True, segmentation=True, normal=True)
cam.set_pose(pos=..., lookat=...)      # 运行期改视角
cam.start_recording(); ...; cam.stop_recording(save_to_filename="out.mp4")
```

四种图对应 `IMAGE_TYPE`：`RGB` / `DEPTH` / `SEGMENTATION` / `NORMAL`（`constants.py:178-182`）。**不需要的通道别打开** —— 每个通道都是实打实的渲染开销。

### 7.5 传感器 `[CODE]`

```python
sensor = scene.add_sensor(gs.sensors.IMU(entity_idx=robot.idx, noise=0.01, delay=0.002))
...
all_readings = scene.read_sensors()          # dict[type[Sensor], Tensor]
```

具体各传感器的 options 字段见 **§2.5**。基类 `SensorOptions` 的四个通用字段（`genesis/options/sensors/options.py:69-121`）：`history_length`、`delay`、`jitter`、`draw_debug`（+ `entity_idx`）；`SimpleSensorOptions` 追加（`:219-243`）：`resolution`、`bias`、`noise`、`random_walk`。

**两条校验行为要记住** `[CODE]`：
- `jitter > delay` → **直接抛异常**（`:102-104`）
- `delay` 不是 `scene.sim.dt` 整数倍 → **只 warning，不报错**，静默四舍五入到 `delay_ts * dt`（`:113-119`）。**想要精确延迟就把 `delay` 设成 `dt` 的整数倍。**

### 7.6 API 稳定性提示

Genesis 仍在快速迭代（`RELEASE.md` 里 v1.3.x 就有多次 API 调整）。**本章行号只对 v1.3.3 成立**。核对方法：

```bash
python -c "import genesis as gs; print(gs.__version__)"
python -c "import genesis as gs; print([x for x in dir(gs.sensors) if not x.startswith('_')])"
```

---

## 8. 已知问题与限制

> 本章按**证据等级**分三组。`[CODE]` 组是可在仓库里自行验证的硬事实，做工程决策只信这一组。

### 8.1 `[CODE]` 级 —— 可在仓库中直接验证

| # | 限制 | 证据 | 影响 |
|---|---|---|---|
| **1** | **Nyx 不在本包内** —— `grep -rn -i nyx genesis/ --include=*.py` 命中 **0** 处 | §3.1 | 按 README"四层栈"的印象去找 `gs.renderers.Nyx` 会扑空。要用必须 `pip install gs-nyx` |
| **2** | **IPC 耦合器需额外装 `pyuipc`**，且**仅 Linux / Windows x86 + NVIDIA GPU** | `README.md:127` | macOS / AMD 卡上 §2.2 的三种耦合器实际只有两种可用 |
| **3** | **传感器缺陷参数默认全为 `0.0`** | `options.py:219-243`、`:474-568` | 不显式配置就是**理想真值**，sim-to-real 迁移会被高估 |
| **4** | **相机不支持噪声建模** —— `Camera` 直接派生自 `Sensor`，停留在 `SensorOptions`，没有 `noise`/`bias`/`random_walk`/`resolution` 字段 | `options.py:219-243` docstring 明确写了这点 | 视觉策略的鲁棒性测试要**自己**在图像上加扰动 |
| **5** | **`delay` 不是 `dt` 整数倍时静默四舍五入**（只 warning 不报错） | `options.py:113-119` | 想要精确延迟必须自己对齐到 `dt` |
| **6** | **`mujoco` 版本在主依赖与 `[dev]` extra 之间冲突**：`>=3.2.5`（无上界） vs `>=3.10.0,<3.11.0` | `pyproject.toml` | 装 `[dev]` 会收紧到 3.10.x；与其它 pin 了 mujoco 的库共存会打架，建议**单独环境** |
| **7** | **6 处依赖带上/下界或排除 pin**（`trimesh` / `libigl` / `pyglet` / `z3-solver` / `Pillow` / `pygltflib`），每条都对应一个已知上游破坏 | `pyproject.toml:11-77` 注释 | 凭直觉升级会踩坑，见 §5.3 |
| **8** | **`quadrants==1.3.0` 精确 pin** | `pyproject.toml:13` | 编译器层与本体强绑定，单独升级极可能 import 失败 |
| **9** | **PyTorch 不在依赖里**，须自行先装 | `pyproject.toml:11-77` 无 `torch` | 装反顺序是常见首次失败原因 |
| **10** | **批渲染器 `gs-madrona` 仅 Linux + x86_64/AMD64** | `pyproject.toml` 平台条件依赖 | ARM / macOS 上没有批渲染 |
| **11** | **`build()` 之后不可再增删实体/传感器/相机** | §3.6、`scene.py:864` | 动态场景（运行时生成物体）需在设计阶段就规避 |
| **12** | **可微模式下 `substeps_local % substeps == 0` 是硬约束**，且显存随 `substeps_local` 线性增长 | `solvers.py:71-77` | 可微 + 多子步很容易 OOM |
| **13** | **`n_envs=0` 与 `n_envs=1` 的张量形状不同**（前者无 batch 维） | `scene.py:875-878` docstring | 通用代码里混用会出形状错 |
| **14** | **Python 版本窗口窄**：`>=3.10,<3.14` | `pyproject.toml:9` | |
| **15** | **`show_FPS` 已废弃** | `scene.py:111` | 改用 `profiling_options.show_FPS` |

### 8.2 `[推断]` 级 —— 有代码线索但未定论

| # | 事项 | 线索 | 建议 |
|---|---|---|---|
| **A** | **耦合器切换很可能不是行为中性的**。宣称"改一行配置即可切换"，但 `sap_coupler.py:1799-3657` 里有 **20 个物料对专用的接触/约束 handler** | `[CODE]` 类结构 | 切换耦合器后**必须重新验证**你那组材料组合的行为，别假定结果等价 |
| **B** | **`ElastomerTaxel` 不是真 FEM 弹性体** —— 标记位移由 **SDF 查询**驱动的高斯核近似，`probe_gain` 的 docstring（`tactile.py:421-426`）自己就标注了这是近似 | `[CODE]` | 做触觉 sim-to-real 时，别把它当作可信的接触力学真值 |
| **C** | **`performance_mode=True` 的代价未说明** | `gs.init` 签名有该参数，文档无解释 | 长训练可试，但要 A/B 对比确认没改变数值行为 |

### 8.3 `[官网]` / `[文章]` 级 —— 官方或第三方的说法，**未经本文档验证**

| # | 说法 | 出处 | 注意 |
|---|---|---|---|
| **i** | Barrier-free elastodynamics 相比传统 IPC 快 **103×** | `[官网]` `Genesis_world_02.txt` | 无可复现基准 |
| **ii** | Quadrants 相比 Taichi 运行时 **4.6×**、启动 **>10×** | `[官网]` | 同上 |
| **iii** | Pearson **0.8996** / MMRV **0.0166** / FID 差距再小 45% | `[官网]` §2.8 | 评测套件未开源 |
| **iv** | 200+ 小时真机 → **<0.5 小时**仿真 | `[官网]` | 依赖具体任务与硬件 |
| **v** | **bit-level 可复现** | `[官网]` | 仓库确有 `seed` / `use_deterministic_algorithms` 参数支撑该方向，但**跨机器/跨后端是否成立未验证** |
| **vi** | 增广拉格朗日中的**松弛变量 `sᵢ` 没有物理意义**，纯数值构造 | `[文章]` `Genesis_world_01.txt:37` | 调参时别试图给它赋予物理解释 |
| **vii** | **刚体稳定性是整个栈的依赖下限** —— 刚体不稳，上层多物理与策略评测都不可信 | `[文章]` `Genesis_world_01.txt:99` | 排障时先怀疑刚体层 |
| **viii** | **IPC 也会失败** —— 极端穿透、病态网格下不保证无穿透 | `[文章]` `Genesis_world_01.txt:107` | 别把 IPC 当无条件保险 |
| **ix** | **渲染层决定策略输入分布** —— 换渲染路径等于换了策略的输入域 | `[文章]` `Genesis_world_01.txt:112-114` | 训练与评测**必须用同一条渲染路径** |
| **x** | **视觉扰动的可用维度取决于渲染器** | `[文章]` `Genesis_world_01.txt:116` | 光栅化路径能做的域随机化比光追少 |
| **xi** | 版本号错位：博客称 "Genesis World **1.0**"，pip 上是 **1.3.3** | 见文档头 | 两套编号体系，别混引 |

### 8.4 本知识库尚未覆盖（**未提及**）

以下方向在现有源料（README / 官方博客 / 第三方文章 / v1.3.3 代码浅层遍历）中**没有找到足够证据**，需要时请直接读上游源码或提 Issue，**不要据此推测**：

- **各求解器的精度/稳定性数值边界**（各 solver 的 CFL 条件、推荐 `dt` 区间）
- **不同耦合器支持的完整材料对矩阵**（哪些组合可用、哪些会静默退化）
- **多 GPU / 分布式仿真**是否支持
- **ROS / ROS2 集成**
- **`gs-nyx` 插件的具体 API 与 CUDA 版本要求**（本仓库只有 CI 里的 `cu128` 一条线索）
- **Gaussian Splat 资产的生产流程**（如何从真实场景采集到可用于 Genesis 的 splat）
- **可微仿真的实际收敛表现**与适用任务范围
- **`performance_mode` / `use_deterministic_algorithms` 的具体语义与代价**
- **官方评测套件**（14 任务 × 200 episodes）的组成与获取方式

排障请转 **[`troubleshooting.md`](./troubleshooting.md)**；本机复现踩过的坑见 **[`ai_knowledge.md`](./ai_knowledge.md)**。

---

## 9. 参考资源

### 9.1 官方

| 资源 | 地址 |
|---|---|
| **主仓库** `genesis-world` | https://github.com/Genesis-Embodied-AI/genesis-world |
| **文档站** | https://genesis-world.readthedocs.io/en/latest/user_guide/index.html |
| **官方博客**（本文档 `[官网]` 级证据的唯一来源） | https://www.genesis.ai/blog/the-role-of-simulation-in-scalable-robotics-genesis-world-10-and-the-path-forward |
| **Nyx 渲染插件** `genesis-nyx` | https://github.com/Genesis-Embodied-AI/genesis-nyx |
| **Quadrants 编译器** | https://github.com/Genesis-Embodied-AI/quadrants |
| Issues / Discussions | 主仓库的 `/issues`、`/discussions` |
| 贡献指南 | `.github/contributing/PULL_REQUESTS.md` |

### 9.2 仓库内最值得读的位置 `[CODE]`

| 想知道什么 | 读哪 |
|---|---|
| **上手** | `examples/tutorials/`（18 个脚本，从 `hello_genesis.py` 到 `advanced_hybrid_robot.py`） |
| **传感器怎么用** | `examples/sensors/`（10 个：`imu_franka.py`、`lidar_teleop.py`、`tactile_franka.py`、`tactile_sandbox.py`、`contact_force_go2.py`、`depth_camera_custom_vverts.py`、`surface_distance_shadowhand.py`、`temperature_grid.py`、`camera_as_sensor.py`、`joint_torque_franka.py`） |
| **多物理耦合** | `examples/coupling/`、`examples/sap_coupling/`、`examples/ipc/` |
| **RL 训练** | `examples/locomotion/`、`examples/drone/hover_train.py` |
| **性能自测** | `examples/speed_benchmark/`、`tests/benchmarks/` |
| **所有可配参数** | `genesis/options/`（Pydantic 模型，docstring 就是最准的参数文档） |
| **版本变更** | `RELEASE.md` |

`examples/` 共 **122 个 `.py`**，分布在 18 个子目录：`collision/ coupling/ deformable/ drone/ fluid/ gui/ ipc/ kinematic/ locomotion/ manipulation/ rendering/ rigid/ sap_coupling/ sensors/ speed_benchmark/ tutorials/ usd/ viewer_plugin/`。

### 9.3 上游致谢中透露的技术血缘 `[README]` `README.md:206-226`

这张表对**理解各求解器的行为特征**很有用 —— 知道参考实现是谁，就知道该去查谁的文档：

| 模块 | 参考/依赖 |
|---|---|
| 编译器 | **Taichi**（Quadrants 于 **2025 年 6 月** fork 自此） |
| IPC 后端 | **libuipc** |
| MPM | **FluidLab** |
| SPH | **SPH_Taichi** |
| PBD | **Ten Minute Physics**、**PBF3D** |
| 刚体动力学 | **MuJoCo** |
| 碰撞检测 | **libccd** |
| 光栅化渲染 | **PyRender** |
| 光追渲染 | **LuisaCompute** / **LuisaRender** |
| 批渲染 | **Madrona** / **Madrona-mjx** |

> ⚠️ **一处源料冲突**：`README.md:210` 说 Quadrants **2025 年 6 月** fork 自 Taichi，第三方文章 `Genesis_world_01.txt:49` 也说 6 月。两处一致，采信 **2025-06**。（§2.7 中若出现"年中"的模糊表述，以此为准。）

### 9.4 引用格式 `[README]` `README.md:206-226`

官方给了**两条** BibTeX，用途不同：

- **`genesis2026genesisworld`** —— 引用 Genesis World 平台本身（Genesis AI Blog, 2026-05）
- **`Genesis`** —— 引用 2024 年 12 月的原始 Genesis 项目

**许可证**：Apache 2.0。

### 9.5 本知识库内的关联文档

> 📌 **当前状态**：本项目目前只有**原理层**（本文档）与索引。其余四层正在编写中，下表中标 ⏳ 的文档**尚未存在**，链接暂时是死链。

| 层 | 文档 | 什么时候看 |
|---|---|---|
| ⏳ 速查层 | `quickstart.md` | **要动手跑**，想不起命令 |
| ✅ 原理层 | 本文档 | 查 API / 参数 / 设计原理 / 能力边界 |
| ⏳ 经验层 | `ai_knowledge.md` | 想知道**为什么会这样**、试过哪些无效方法 |
| ⏳ 排障层 | `troubleshooting.md` | **手上有一条具体报错** |
| ⏳ 代码层 | `code_knowledge.md` | 要改**复现仓库 `genesis-world-tour`** 的代码 |
| ✅ 索引 | [`00-index.md`](./00-index.md) | 带行号的章节地图 + `未提及` 清单 |

### 9.6 源料清单（**仅本机有效**，`sources/` 已 gitignore）

| 文件 | 内容 | 证据等级 |
|---|---|---|
| `sources/genesis_world/background.txt` | 三条源 URL | — |
| `sources/genesis_world/Genesis_world_01.txt` | 第三方技术分析（136 行） | `[文章]` |
| `sources/genesis_world/Genesis_world_02.txt` | 官方博客译文（292 行） | `[官网]` |
| `sources/genesis_world/genesis-upstream/` | 上游仓库 clone，**v1.3.3 / HEAD `19f56d6`** | `[CODE]` |
| `sources/genesis_world/genesis-world-tour.md` | 本机复现全程记录 | `[实践]` |


