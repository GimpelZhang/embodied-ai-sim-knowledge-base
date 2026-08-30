# 具身智能仿真工具链横向对比与选型指南

> **对比对象**：本知识库已完成五层收录的 4 个工具链。
> **数据来源**：各项目 `background_knowledge.md`（原理层，`[CODE]`/`[PAPER]`/`[README]`/`[官网]` 级）+ `code_knowledge.md`（代码层）；使用体验类结论来自 `ai_knowledge.md`（经验层，`[实践]` 级，**不是官方结论**）。
> **结论力度声明**：性能数字凡标 `[官网]`/`[PAPER]` 的均为**宣称值**，多数无可复现脚本；标 `[实践]` 的是**单机单次实测**，不构成基准。

## ⚠️ 读这张表之前必须知道的一件事

**这 4 个不是同类产品，不能按同一把尺子排名。**

| | 它是什么 | 一句话 |
|---|---|---|
| `genesis_world` | **通用物理仿真平台** | 6 类求解器同场景共存 + 可换耦合器；最接近"传统仿真器"的那个 |
| `genie_sim_v3` | **工具链 + 评测体系**（含 3 套并存的仿真栈） | 底座是 Isaac Sim；真值源是 OpenUSD stage；ROS 2 原生 |
| `lw_benchhub` | **评测框架 / 薄组合层** | 自身不含仿真器，靠四路组合把 Isaac Lab / Arena 的能力拼成 benchmark |
| `ge_sim_v2` | ⚠️ **动作条件视频生成世界模型** | **无物理引擎、无渲染器、无场景文件** —— 它不解算物理，它"演"物理 |

**因此**：
- 问「哪个物理更准」→ 只在 `genesis_world` / `genie_sim_v3` / `lw_benchhub` 三者间有意义，`ge_sim_v2` 不参与（它没有物理解算）。
- 问「哪个画面更真」→ `ge_sim_v2` 反而占优，但那是**因为它的画面本来就是真机域**，不是渲染得好。这两件事不可混谈（见 §3.1）。
- 问「哪个能开箱评测」→ `lw_benchhub` / `genie_sim_v3` 有成套任务与判据，`genesis_world` **明确不是 benchmark 套件**。

---

## 1. 定位速览

| 工具链 | 类型 | 底座 | 许可 | 核对版本 |
|---|---|---|---|---|
| **`genesis_world`** | 物理仿真平台 | 自研多物理栈（Quadrants 编译器 + 8 求解器） | Apache-2.0 | 原理层 **v1.3.3** / 实测 **v1.2.2** |
| **`genie_sim_v3`** | 工具链 + 评测体系 | Isaac Sim 5.1（+ Newton / MuJoCo） | MPL-2.0（部分组件更严） | 原理层 **v3.2.0** / 实测 **3.0 时期** |
| **`lw_benchhub`** | 评测框架（薄组合层） | Isaac Sim 5.0/5.1 + Isaac Lab + IsaacLab-Arena | Apache-2.0 | `main` @ `b2bcb2d` |
| **`ge_sim_v2`** | 视频生成世界模型 | Cosmos-Predict2-2B DiT（**2B 参数**） | 权重在 HF | 论文 v1 ≠ 权重 `community v2.0.1` ⚠️ |

⚠️ **本库内部的版本落差**：`genesis_world` 与 `genie_sim_v3` 的原理层比实测层新。**API 写法不可跨版本套用；能力边界类结论可以。**

---

## 2. 主对比矩阵

> 为了可读，把维度放在行、工具链放在列（9 个请求维度全部覆盖）。

### 2.1 领域与引擎

| 维度 | `genesis_world` | `genie_sim_v3` | `lw_benchhub` | `ge_sim_v2` |
|---|---|---|---|---|
| **主要仿真领域** | 刚体 + 软体 + 流体 + 颗粒；桌面操作、四足/人形移动、软体/流体交互、数字孪生 | 人形/双臂 **loco-manipulation**；覆盖零售/工业/餐饮/家庭/办公五类真实作业场景 | **厨房操作**（kitchen manipulation）+ loco-manipulation + 长时序组合任务 | **双臂桌面 manipulation**；擅长长尾外观（液体、可变形物、接触细节、真实材质） |
| **领域反向边界** | 不自带任务基准 | 无 GPU 向量化多环境物理 | **非厨房域（工业装配、户外、驾驶）不适用** | 分布外场景/物体/任务不可靠 |
| **核心物理引擎** | **自研统一多物理栈**，8 求解器：Rigid / FEM / MPM / SPH / PBD / Stable-Fluid / Kinematic / Tool；刚体以 `mujoco>=3.2.5` 为参考实现 | **三后端可切**：`isaac_physx`（PhysX 5，默认）/ `isaac_newton`（🧪 UNSTABLE，仅刚体）/ `newton_standalone`（唯一支持布料/软体） | **PhysX（GPU）** via Isaac Sim；Arena 另带实验性 Newton / MuJoCo-Warp | ❌ **无物理引擎** —— 无刚体求解器、无碰撞检测、无接触力、无摩擦系数 |
| **跨物理耦合** | ⭐ **三种可换耦合器**：`LegacyCoupler`（默认）/ `SAPCoupler`（Drake 式 + hydroelastic）/ `IPCCoupler`（无相交接触，需 `pyuipc`） | 布料求解器四种（VBD 默认 / XPBD / Style3D / AVBD），仅 `newton_standalone` 路径 | 未提及（`PhysxCfg()` 留在 Isaac Lab 默认值，`contact_offset`/`rest_offset` 两仓库均未设置） | 不适用 |
| **核心渲染引擎** | 包内自带 **LuisaCompute（光追）+ PyRender（光栅）+ gs-madrona（批渲染）**；⚠️ 宣传里的 **Nyx 不在 pip 包内**（独立包 `gs-nyx`） | **OVRtx**（NVIDIA 独立 C-API RTX 库，脱离 Omniverse Kit，硬钉 `0.3.x`）；Benchmark 栈走 Kit RTX | **Omniverse RTX 实时渲染器**（光栅 + 光追）；`PathTracing` / `rendering_mode` **均未提及** ⇒ 不跑路径追踪 | ❌ **无渲染器** —— 无光栅化/光追/材质/光源；像素由 **VAE 解码**得到 |
| **渲染模式档位** | `Rasterizer` / `RayTracer` / `BatchRenderer` 三类 | 三档：`RaytracedLighting`（默认）/ `RealTimePathTracing`（`rt_subframes=8`）/ `PathTracing`（离线最准）；⚠️ **全栈无 AA/denoiser/DLSS** | 仅实时；相机分辨率跨度 84×84 → 720×1280 | 固定 **384×512**、三视角，不可改 |

### 2.2 本体、语言与 API

| 维度 | `genesis_world` | `genie_sim_v3` | `lw_benchhub` | `ge_sim_v2` |
|---|---|---|---|---|
| **支持的机器人类型** | 机械臂 / 灵巧手 / 夹爪 / 人形 / 四足 / **无人机（带螺旋桨模型）**；内置 Franka、Go2 等资产 | 一等支持 AgiBot **Genie G2** 系列；另提供 Franka / UR5 / Aloha / ARX / Agilex 参考 URDF；Benchmark 侧 5 个前缀 | **实测 28 个** `Robocasa-Robot-*` 变体（README 说 27，不准）；7 个厂商：Unitree G1 / Agilex Piper / ARX X7S / Franka Panda(+Omron) / LeRobot / 双臂组合 | ⚠️ **仅 Genie-01 + OmniPicker 双臂**，单一本体 |
| **能否换本体** | ✅ URDF / MJCF / USD / Mesh / xacro / Terrain 均可 | ✅ 支持 xacro 接入；硬约束：**URDF 根 link 必须零质量** | ✅ 但注册散落各厂商子包 | ❌ **不能** —— FK 以预编译 `_g01_fk.so` 发布，官方明确"no URDF or robot geometry is published"，**换本体=换那个 `.so`，而你没有源码** |
| **编程语言** | 纯 Python（`import genesis as gs`） | Python + **ROS 2 (C++/Python colcon)** + gRPC | 纯 Python（Isaac Lab manager-based 范式） | Python |
| **主 API 形态** | **声明式 options**，全部是 **Pydantic 模型**带 `model_post_init` 校验 ⇒ **配置错误在 `Scene()` 构造时就报错** | **统一 CLI `geniesim`**（15 命令模块）+ Python `ParameterServer`/`APICore`（约 70 方法）+ ROS 2 topics + gRPC(24 RPC) + 策略侧 WebSocket+msgpack | **shell 包装器 + `--task_config=<stem>` YAML**（8 个入口脚本）；接自研策略唯一入口是实现 `BasePolicy` 4 个抽象方法 | **gym 风格 SDK** `WorldModelEnv`（`reset`/`step`）；三进程拓扑：客户端 ←HTTP:9000→ 世界模型 ←WS:8000→ π0.5 策略 |
| **API 稳定性** | 版本演进快，1.2.2↔1.3.3 写法已有差异 | 演进约每季一版；`geniesim2` 已 E.O.L.、`geniesim4` 标 "not implemented" | ⚠️ **底座自称 alpha** —— Arena README 写 "APIs will break without deprecation warnings … Do not use this in production" | ⚠️ 反直觉点多：`step()` 返回 **4 元组且无 `done`**；`frames` 是 `(T,3,V,H,W)`，`[:,0]` 取到**通道轴不是视角** |
| **稳定 Python 评测 API** | 不适用（不是 benchmark） | ✅ 有（`BenchmarkVecEnv` / `VecEnvAdapter`） | ❌ **缺失** —— 上游 issue #45 未关闭；只能走 `BasePolicy` + shell | ✅ `WorldModelEnv` 即是 |
| **上手成本** | 最小程序 **6 个动作**、顺序强制；`examples/` **122 个 `.py`** / 18 子目录 | 高：三套栈语义不同、`benchmark` 与 `ros` 两条栈**场景格式不得混用** | 中：核心是「四路组合」；绝大多数故障是"组合没解析对"而非"仿真算错" | 低（API 面小）但**陷阱密度高** |

### 2.3 典型应用场景支持度

**图例**：✅ 开箱支持 · ⚠️ 支持但有明显限制 · ❌ 不支持 / 未提及

| 应用场景 | `genesis_world` | `genie_sim_v3` | `lw_benchhub` | `ge_sim_v2` |
|---|---|---|---|---|
| **大规模并行 RL 训练** | ✅ **最强** —— `scene.build(n_envs=N)` GPU 并行，单卡数千环境；实测 **2048 envs → 151,839 steps/s** | ⚠️ **仅 RLinf 栈**（CPU MuJoCo 多进程，SAC+BC 正则）；❌ **无 Isaac Lab 式 GPU 向量化物理** | ⚠️ **面极窄** —— 272 任务只有 **6 个 RL 配置且全挂在 `LiftObj`**；skrl 是唯一真被实例化的库，**rsl-rl 只注册不执行** | ❌ 在线 RL 论文列为 future work；实测须自搭（**流匹配无闭式概率密度 ⇒ 无法做 policy gradient**，最终用 RWR 才跑通） |
| **VLA / 策略闭环评测** | ✅ **官方首要用途**，约 10 条扰动轴扫描鲁棒性 | ✅ **成建制** —— RoboColiseum 5 榜 + ADER 规则化判据 | ✅ 核心用途（成功率评测） | ✅ **论文主战场**（分布内批量重复评测） |
| **运动规划** | ✅ `RigidEntity` 自带 IK + 规划 API | ✅ `genie_sim_moveit`（MoveIt 2 + 3 IK 插件 + RRT-Connect + TOPP-RA）；采集侧 cuRobo GPU 规划 + GraspNet | ⚠️ **不在本体内** —— cuRobo 走 `autosim` 插件，而**该包源码不在仓库、也未在 `pyproject.toml` 声明**（装完仍 ImportError） | ❌ |
| **多机器人 / 多智能体** | ❌ 未提及 | ❌ 未提及（RT Engine 单环境单机器人） | ❌ 未提及（有双臂本体但不是多智能体） | ❌ |
| **ROS / ROS 2 集成** | ❌ **未提及**（已 grep 确认无证据） | ✅ ⭐ **唯一 ROS 2 原生**：Jazzy，10 个 colcon 包，`/clock`·`/joint_states`·`/joint_command`·`/tf`·`/odom`+相机 topics；RMW 固定 `rmw_cyclonedds_cpp` | ❌ 未提及 | ❌ |
| **软体 / 流体 / 颗粒** | ✅ **最强** —— FEM/MPM/SPH/PBD/SF 五类 + `hybrid_entity`（同一物体不同部分不同求解器） | ⚠️ **只有一条路径**（`launcher_newton_*` 的 VBD/XPBD，自标实验性；PhysX 布料 "not actively maintained"） | ❌ 未提及 | ❌ |
| **可微仿真** | ✅ `SimOptions.requires_grad` + `scene.backward(loss)`，反向 AD 已是各后端一等公民；⚠️ 易 OOM，显存随 `substeps_local` 线性增长 | ❌ 未提及 | ❌ 未提及 | ❌（无闭式密度） |
| **遥操作采数** | ❌ 未提及 | ✅ VR/Pico | ✅ 键盘 / VR（Vision Pro、PICO、Quest）/ 主从臂；含 **`action_delay_*` 真动作延迟注入**与 M/N/B/R 存档读档键 | ⚠️ 官网列 "Teleoperation in WM"，未见实证 |
| **合成数据生产** | ⚠️ 官方明确**先做评测再做数据生成**（路线图取舍） | ✅ 10,000+ 小时合成数据，**含 error-recovery 轨迹** | ✅ LeRobot 数据集导出 + `lerobot-eval` 桥接 | ⚠️ 已验证 **filtered BC**（三任务真机平均 **+15 pp**）；但❌无法新建场景 |
| **数字孪生 / real2sim** | ✅ 摄影测量 + Gaussian splats，**同时供渲染与物理使用** | ⚠️ 3DGS 管线存在，但**USD handoff 在仓库之外**（无 mesh 提取/TSDF/USD writer） | ⚠️ 数字孪生 + RGB 叠加（语义掩膜保前景、其余像素换真实照片） | ✅ 天然真机域（**无 sim-to-real 视觉 gap**） |
| **开箱任务基准** | ❌ **明确不是 benchmark 套件**（无标准任务/判据/leaderboard） | ✅ 200+ 任务 / 100,000+ 场景 / 5,140 sim-ready 资产 | ✅ **实测 272 任务**（LIBERO 131 + RoboCasa 141；README 说 268，不准） | ❌ 开箱无自动评测（World Judge 未开源，`reward`/`progress` **恒 `None`**） |

### 2.4 传感器与噪声建模（选型中最容易被忽略、代价最大的一栏）

| 传感器 | `genesis_world` | `genie_sim_v3` | `lw_benchhub` | `ge_sim_v2` |
|---|---|---|---|---|
| RGB | ✅ | ✅ | ✅ | ✅（唯一输出） |
| 深度 | ✅ 两条独立路径（相机 depth + `RaycasterOptions`） | ✅ 但是 **z-depth 几何真值**，无噪声/无空洞 | ❌ 未提及 | ❌ 未提及 |
| 分割 | ✅ 语义 + 实例 | ⚠️ **仅语义**，实例分割未提及 | ❌ 未提及 | ❌ 未提及 |
| 法线 | ✅ | 未提及 | ❌ | ❌ |
| LiDAR | ✅ `RaycasterOptions` | ✅ `instantLidar` + de-skew | ❌ 未提及 | ❌ 未提及 |
| IMU | ✅ 三合一（acc + gyro + mag） | ⚠️ 有，但**无噪声模型**（几何真值） | ❌ 未提及 | ❌ 未提及 |
| 关节力矩 | ✅ `JointTorqueSensor` | ✅ `effort` 14 维 | ❌ 未提及 | ❌ 未提及 |
| 接触力 | ✅ `RigidContactForceSensor`（⚠️ `get_contacts()` 属 rigid-rigid 管线，**对 PBD 粒子实体直接 `AttributeError`**） | 未提及 | ❌ 未提及 | ❌ |
| 触觉 | ✅ 两条路线（`ElastomerTaxel` + `TactileSensor`）⚠️ 前者非真 FEM 变形 | ❌ **未提及** | ❌ 未提及 | ❌ 未提及 |
| 温度场 | ✅（`Tool` 求解器族） | ❌ | ❌ | ❌ |
| 本体感觉 | ✅ | ✅ | ✅ | ✅ 16 维 |
| **噪声建模** | ⭐ **机制最完整**：两层继承 —— `SensorOptions` 给 `delay`/`jitter`/`history_length`，`SimpleSensorOptions` 追加 `resolution`/`bias`/`noise`/`random_walk`。⚠️ **但所有参数默认 `0.0`，且相机直接派生自 `Sensor`、根本没有噪声字段** | ⭐ **RGB 噪声实际启用**（全库唯一）：7 个 Warp kernel，实启 5 种（高斯/椒盐/散粒/条带/暗电流）+ ISP 链。**但深度/IMU/LiDAR 全是几何真值** | ❌ **`enable_corruption=True` 是空转的假开关** —— 全仓库无任何 `ObsTerm` 传 `noise=`；⇒ **所有鲁棒性结论都是"无传感器噪声条件下"的** | ⚠️ **无任何显式噪声参数，但输出也不是理想真值** —— 生成伪影（物体消失、抓取穿模、纹理漂移）是内生的，**不可参数化、不可关闭** |
| **域随机化** | ✅ 视觉 + 材质属性 + 地形 + 外部扰动 | ✅ **11 类已实现**（光照/材质/纹理/相机/物体位姿·尺度/摩擦·质量/初始位形/…） | ⚠️ 靠 Arena `variations` **8 类**（光照/相机/物体位姿·缩放/关节初值/物理材质/…）；**纹理与材质外观随机化未提及** | ❌ 不可控 |

**这一栏的三条选型硬结论**：
1. **要依赖深度/激光/触觉做任务 → 只有 `genesis_world` 与 `genie_sim_v3` 进入候选**；`lw_benchhub` 与 `ge_sim_v2` 需自行扩展。
2. **`genesis_world` 与 `ge_sim_v2` 是两个极端**：前者机制完整但**默认全 0（理想真值）**，后者**根本没有旋钮但输出天然带噪**。前者要你主动开噪声，后者不允许你关噪声。
3. **默认即理想真值是三个仿真项目的共同状态** ⇒ 任何"策略抗噪"的结论都必须先确认噪声真的开了（见 [`common_issues_solutions.md` §J](common_issues_solutions.md)）。

### 2.5 安装难度（基于原理层 §5 评估）

| 工具链 | 难度 | 关键卡点 | 离线可用 |
|---|---|---|---|
| **`genesis_world`** | ★★☆☆☆ | `pip install genesis-world` 真的能装上。① **PyTorch 不在依赖里，必须先单独装**；② Python 窗口窄 `>=3.10,<3.14`；③ **6 处带界/排除 pin**（`trimesh`/`libigl`/`pyglet`/`z3-solver`/`Pillow`/`pygltflib`）各对应一个已知上游破坏；④ 装 `[dev]` 会把 mujoco 从 `>=3.2.5` 收紧到 `>=3.10,<3.11` ⇒ **建议单独开环境**；⑤ IPC 支需 `pip install pyuipc`（仅 Linux/Windows x86 + NVIDIA），批渲染 `gs-madrona` 仅 Linux x86_64 | ✅ 基本可（首次跑 example 会拉资产） |
| **`ge_sim_v2`** | ★★★★☆ | ① **仓库内无任何依赖清单**（无 `requirements.txt`/`setup.py`/`environment.yml`），**除 `torch>=2.0` 外全无版本约束** ⇒ 版本组合全靠自己试；② `clone` **必须带 `--recursive`**，`openpi-client` 要单独 `pip install -e third_party/openpi/packages/openpi-client`；③ 三个 conda 环境隔离，逐 Stage 代理策略相反；④ `configs/gesim_v2.yaml` **默认把四个加速内核开关全开**但它们需源码编译（上游明说"没有也能跑"）；⑤ 权重需单卡 **≥48 GB 显存** | ⚠️ 权重需从 HF 拉 |
| **`genie_sim_v3`** | ★★★★★ | ① **只走容器**（Ubuntu 24.04 镜像），宿主只装驱动 + Docker + NVIDIA Container Toolkit；② **`compute_cap >= 7.5` 是硬门槛 —— V100(7.0) 完全不可用**；③ 驱动需 580+（apt 安装）；④ 3DGS 管线是**第二个独立镜像**，`pycolmap` 编译链长；⑤ 多架构镜像构建可超 1 小时；⑥ Python `>=3.10,<3.13` | ⚠️ 镜像大，资产需下载 |
| **`lw_benchhub`** | ★★★★★ | ① **两条互不可混的安装路径**（`install.sh` 用 torch 2.7.0+cu128；docker `environment.yml` 用 torch 2.5.1）；② **`numpy==1.26.0` 必须最后装，每次 pip 操作后重新锁回**（Isaac Sim C 扩展硬绑）；③ `-e` 不能省（`CONFIGS_PATH` 依赖源码树）；④ `flatdict==4.0.1` 装不上需 `sed` 改版本；⑤ Arena 子模块是 **SSH URL**（无 key 直接失败）；⑥ 当前 `Dockerfile` 必然失败（`COPY` 了不存在的 `AutoDataGen`）；⑦ **显存/磁盘/Python 版本官方全未声明** | ❌ **不可** —— 厨房资产运行时经 `lightwheel_sdk` 从云端拉取，**`import` 阶段就调 `list_registry()`** |

> **难度评分口径**：★ 数反映"从零到跑通第一个官方 example"的**卡点数量与不可绕性**，不含硬件采购。两个 ★★★★★ 项目的共性是：**依赖不是 pip 能解决的**（一个要容器 + 特定 compute capability，一个要云端资产 + 手工锁 numpy）。

### 2.6 性能特点

| 工具链 | 官方宣称 | 本机实测（`[实践]`，单机单次） | 怎么读这些数字 |
|---|---|---|---|
| **`genesis_world`** | `[官网]` 无相交接触**快 103×**；Quadrants 运行时 **4.6×**、启动 **>10×**；1080p 渲染 **4 ms**；评测 200+ 小时 → **<0.5 小时**；sim-real Pearson **0.8996** | Go2 PPO，A800，**2048 envs → 151,839 steps/s** | ⚠️ **sim-real 评测套件未开源**，0.8996 不可复现。**速度类可自测**：`examples/speed_benchmark/` + `tests/benchmarks/` |
| **`genie_sim_v3`** | 默认 **100 Hz 物理 / 30 Hz 渲染**；官方 `perf.md` Render mean **28.40 ms**（渲染 tick ≈ 非渲染的 5 倍）；`[PAPER]` sim2real **R²=0.931** | **3DGS 点云是主导开销**：600K 点 → **0.25 Hz**；100K → **~4 Hz**；无点云 → **~18 Hz**。100K vs 600K 平均像素差仅 **1.13** ⇒ **降点云几乎免费** | R²=0.931 **仓库无评测脚本**。⇒ 优化第一刀砍点云规模，不是砍渲染质量 |
| **`lw_benchhub`** | ❌ **官方无任何 FPS / 吞吐数字**；仅 CI 阈值 `success_rate>=0.7`；数据集侧 219 任务 / 21,500 episodes / 20,537,015 帧 | 唯一成功闭环 **SmolVLA 40%（4/10）**；π0.5 **0%**；scripted cuRobo **8/8 全失败**（EE 与 TCP 差 **0.30 m**，未解决） | ⚠️ **性能不可预估** —— 且有个隐形陷阱：**开逐环境相机内参随机化会静默关闭 tiled rendering**（表现为"莫名奇妙地慢"）；`teleop_base.yml` 默认 `device: cpu` 且 **YAML 静默覆盖 `--device`** |
| **`ge_sim_v2`** | `[PAPER]` H100 4 步 **2.3 秒生成 25 帧**（≈10.9 帧/s） | **0.88 帧/s ≈ 0.055× 实时**（对照：纯仿真 + VLA 约 3.2 帧/s） | ⚠️ **不要引用"100 帧/2.3 秒"** —— 那是 25 帧 × 4× 跳帧的**覆盖跨度**。实测 0.88 帧/s **直接判死"在线 RL 数据引擎"**，只适合离线批量 rollout。落盘 `keep_frames=True` 约 **7 MB/帧** |

**跨项目的性能规律（3 条）**：
1. **瓶颈几乎从不在物理求解器**，而在渲染/生成/资产 I/O。`genie_sim_v3` 是点云，`lw_benchhub` 是渲染路径被静默降级，`ge_sim_v2` 是扩散采样。
2. **先降数据量，再优化实现** —— `genie_sim_v3` 点云 600K→100K 换来 16× 吞吐、像素差 1.13，这类"几乎免费"的量级调整应先做完。
3. **"莫名奇妙地慢"通常是配置被静默改写**，不是算力不够（`lw_benchhub` 的 CPU 回落是典型）。诊断顺序见 [`common_issues_solutions.md` §K](common_issues_solutions.md)。

### 2.7 社区活跃度与可依赖性

| 工具链 | 迭代节奏 | 文档 | Issue / 社区 | 论文 | 可依赖性判断 |
|---|---|---|---|---|---|
| **`genesis_world`** | 活跃，**v1.3.3**（HEAD `19f56d6`），公司支持（Genesis AI） | readthedocs + **122 个 `.py` 示例** / 18 子目录（最好的一份） | 上游血缘清晰（Taichi / MuJoCo / libccd / libuipc / FluidLab / LuisaCompute / PyRender 等均在文档致谢） | 有官方博客与技术报告 | ⭐ **最高**。但⚠️ **版本编号混乱三处**：博客称 "Genesis World **1.0**" 而 pip 是 **1.3.3**；旧名 "Genesis"；包名 `genesis-world` / `import genesis` / 别名 `gs` |
| **`genie_sim_v3`** | 约**每季一版**，v3.2.0（2026-06-25） | 分层文档 + `perf.md` | 未提及 star/issue 数 | arXiv **2601.02078 v4** | 高，但**组件版本硬钉多**（OVRtx `0.3.x`）；旧 CLI（`geniesim2`）会 E.O.L. |
| **`lw_benchhub`** | `main` @ `b2bcb2d` | 有独立文档站 + HF 数据集 | **5 个未关闭 / 6 个已关闭 issue**（含关键的 #45 缺 Python API） | 未提及 | ⚠️ **最低** —— 不是它本身不活跃，而是**它的行为由 Isaac Lab / Arena 决定，而 Arena 自称 alpha 且"APIs will break without deprecation warnings"**。⇒ **不要升级 isaaclab 或 Arena 子模块**（monkey patch 按 pin 住的版本写死：上游 10 处、复现仓库 11 处） |
| **`ge_sim_v2`** | 权重发布于 HF | 有 README 与技术报告 | 上游社区规模未提及 | arXiv **2605.27491** | ⚠️ **"可用的推理发行版，不是可复现的研究发行版"** —— 未发布：训练/蒸馏代码、非蒸馏权重、**World Judge 实现与权重**、URDF/FK 源码。⚠️ **论文 v1 与发布权重 `community v2.0.1` 不是同一交付物** |

---

## 3. 选型建议

### 3.1 「要高保真渲染」

**先分清两件被混为一谈的事**：

| 你实际想要的 | 术语 | 推荐 |
|---|---|---|
| 光照/材质/阴影/折射**物理正确**（做视觉算法、标定、光度一致性） | **渲染保真度** | **`genie_sim_v3`** ⭐ |
| 图像**看起来像真机拍的**（喂 VLA、缩小视觉 sim2real gap） | **视觉真实感 / 域一致性** | **`ge_sim_v2`** ⭐ 或 `lw_benchhub` 的真实照片叠加 |

- **首选 `genie_sim_v3`** —— 唯一提供**三档渲染模式**（实时光追 / 实时路径追踪 / 离线 `PathTracing`）且带**真实启用的 RGB 传感器噪声链**（5 种噪声 + ISP，全库唯一）。⚠️ 两个代价：**全栈无 AA/denoiser/DLSS**（离线模式要靠加采样降噪，慢）；**3DGS 点云会主导开销**（600K 点 → 0.25 Hz，务必先降到 ~100K，像素差仅 1.13）。
- **次选 `genesis_world`** —— 包内自带 `RayTracer`（LuisaCompute），`[官网]` 称 1080p 4 ms；胜在**渲染与物理共享同一份 Gaussian splats 资产**。⚠️ 但宣传里的 **Nyx 不在 pip 包内**，别按博客的能力清单做规划。
- ⚠️ **`lw_benchhub` 不适合**：只跑 Omniverse RTX 实时，`PathTracing` 未提及；且**开逐环境相机内参随机化会静默关闭 tiled rendering**。
- ⚠️ **`ge_sim_v2` 是另一条路，不是"渲染得更好"**：它的画面天然在真机域（**无视觉 sim2real gap**），代价是**没有任何可控旋钮** —— 不能改相机、不能改光照、分辨率锁定 384×512、三视角固定，且生成伪影不可关闭。

**训评一致性纪律（`genesis_world` 明示）**：**渲染路径必须训评一致** —— 用 `Rasterizer` 训的策略拿 `RayTracer` 评，掉分不能归因于策略。

### 3.2 「要快速 RL 训练」

- **首选 `genesis_world`，且优势是压倒性的** —— `scene.build(n_envs=N)` 单卡数千环境 GPU 并行，实测 **2048 envs → 151,839 steps/s**。另有可微仿真（`scene.backward(loss)`）作为 RL 之外的第二条优化路径。
  ⚠️ 三个前置认知：① `n_envs=0` 与 `n_envs=1` **张量形状不同**（前者无 batch 维）；② `build()` 之后场景结构**不可再增删实体**，域随机化只能改属性；③ rsl-rl 的 checkpoint 编号是 **0-based**（`learn(50)` 只产出 `model_49.pt`）。
- **其余三个都不推荐做 RL 主力**：
  - `genie_sim_v3` —— RL 只在 **RLinf 栈**（**CPU MuJoCo 多进程**），且 `newton` 后端非力矩控制、`isaac_newton` 的 `snapshot_joint_states` 返全零。**没有 GPU 向量化物理**。
  - `lw_benchhub` —— **272 个任务只有 6 个 RL 配置，且全挂在 `LiftObj` 一个任务上**；**`rsl-rl` 只注册不执行**，ManiSkill PPO 不读 YAML，课程学习是空壳。⇒ 它是**评测框架，不是训练框架**。
  - `ge_sim_v2` —— 实测 **0.88 帧/s ≈ 0.055× 实时**，这个数字直接判死在线 RL；且**流匹配无闭式概率密度 ⇒ 无法直接做 policy gradient**（复现中最终用 RWR 绕过）。"可做 RL" 的说法只见于公众号，论文列为 future work。

### 3.3 「要 ROS / ROS 2 集成」

- **只有一个答案：`genie_sim_v3`** —— ROS 2 **Jazzy** 原生，10 个 colcon 包，标准 topic 面（`/clock`、`/joint_states`、`/joint_command`、`/tf`、`/odom` + 相机），并自带 `genie_sim_moveit`（MoveIt 2 + 3 个 IK 插件 + RRT-Connect + TOPP-RA）。⚠️ 硬约束：**RMW 固定 `rmw_cyclonedds_cpp`**；**`benchmark` 栈与 `ros` 栈是两条独立管线，场景格式不得混用**。
- 其余三个：`genesis_world` **未提及**（已 grep 确认无证据）、`lw_benchhub` **未提及**、`ge_sim_v2` 不适用。若必须在 `genesis_world` 上接 ROS，**需自行写桥接层，且没有可参考的官方实现**。

### 3.4 其他常见需求的路由

| 你的需求 | 首选 | 理由 / 注意 |
|---|---|---|
| **软体 / 流体 / 颗粒 / 多物理耦合** | `genesis_world`（唯一选择） | 5 类求解器 + `hybrid_entity` + 三种可换耦合器。⚠️ 换耦合器**不是行为中性的**（`sap_coupler.py` 有 20 个物料对专用 handler），换完必须重验你那组材料 |
| **开箱就有成套任务与判据** | `lw_benchhub`（272 任务）或 `genie_sim_v3`（200+ 任务 + 5 榜 + ADER 判据） | `genesis_world` **明确不是 benchmark 套件** |
| **厨房场景长时序操作** | `lw_benchhub` | 这是它的主场；⚠️ 非厨房域不适用 |
| **人形 loco-manipulation** | `genie_sim_v3` | Genie G2 一等支持；`genesis_world` 有人形资产但无成套任务 |
| **大规模合成数据（含失败恢复轨迹）** | `genie_sim_v3` | 10,000+ 小时，含 error-recovery；`genesis_world` 官方明示先评测后数据生成 |
| **只想快速看"策略会怎么动"，且分布内** | `ge_sim_v2` | 无需建场景/无需调物理；⚠️ 只能回答"看起来会怎么动"，**不能回答"物理上会不会成功"** |
| **缩小视觉 sim2real gap 的离线 BC** | `ge_sim_v2` | 已验证 filtered BC 三任务真机平均 **+15 pp** |
| **可微仿真 / 基于梯度的优化** | `genesis_world`（唯一） | ⚠️ 易 OOM，显存随 `substeps_local` 线性增长 |
| **完全离线 / 内网环境** | `genesis_world` 或 `genie_sim_v3`（预拉镜像与资产） | ❌ **`lw_benchhub` 不可** —— 厨房资产运行时从云端拉取，`import` 阶段即调 `list_registry()` |
| **旧卡（V100 / compute_cap < 7.5）** | `genesis_world` | ❌ **`genie_sim_v3` 完全不可用**（硬门槛 7.5）；`ge_sim_v2` 需 ≥48 GB 单卡 |

### 3.5 组合使用（比单选更常见的真实答案）

这 4 个的能力**互补性大于竞争性**，实际项目里常见两种组合：

1. **`genesis_world`（训）+ `genie_sim_v3` 或 `lw_benchhub`（评）** —— 用前者的 GPU 并行做 RL / 大规模训练，用后者成建制的任务与判据做标准化评测。⚠️ 两侧的观测量纲、控制模式、渲染路径必须显式对齐。
2. **物理仿真器（判成败）+ `ge_sim_v2`（判外观泛化）** —— 前者回答"物理上成不成"，后者回答"长尾外观下策略还认不认"。**这正是 `ge_sim_v2` 的正确站位**：补充而非替代。

---

## 4. 已知限制与适用边界

> 每个项目的完整边界清单见其 `background_knowledge.md` §8。此处只列**会改变选型决定**的条目。

### 4.1 `genesis_world`

- `scene.build()` 是**不可逆分界线**：`add_entity` / `add_sensor` / `add_camera` 必须在它之前；之后场景结构静态。
- **传感器默认全是理想真值**（噪声参数默认 `0.0`，相机连噪声字段都没有）⇒ 抗噪结论必须先确认噪声真开了。
- **可微仿真易 OOM**；`ElastomerTaxel` **不是真 FEM 变形**。
- **开环指标不可用于选模型**；**渲染路径必须训评一致**；**IPC 耦合器不是无条件保险**。
- **不自带任务基准套件** —— 要标准化评测需自建或借用他家。
- 宣传与包内容有落差：**Nyx 不在 pip 包内**（独立包 `gs-nyx`）、**Quadrants 是独立包且硬依赖精确 pin `quadrants==1.3.0`**。
- `未提及` 9 项，含 **多 GPU / 分布式** 与 **ROS 集成**。
- 本库落差：原理层 **1.3.3** vs 其余四层 **1.2.2**，**API 写法不可跨版本套用**。
- 实测三条高频 API 误用：`get_dofs_position` 式 IK 返回**完整 qpos 而非手臂 7 维**；`cam.render()` 返回 **4 元组** `(rgb, depth, seg, normal)`；`get_contacts()` **对 PBD 粒子实体直接抛 `AttributeError`**。
- ⛔ **止损结论**：OpenVLA 抓取闭环本机 **0/8 且已证明到机制层面不可达**（末端恒收敛同一点、夹爪输出恒 0.0、换同本体微调模型仍不收敛）—— 别重复投入。

### 4.2 `genie_sim_v3`

- ⛔ **`compute_cap >= 7.5` 硬门槛，V100(7.0) 完全不可用** —— 这一条能直接排除整个方案。
- **无 GPU 向量化多环境物理** ⇒ 不做大规模并行 RL。
- `isaac_newton` 后端 🧪 **UNSTABLE 且仅刚体**；其 `snapshot_joint_states` **返全零**；newton 路径**非力矩控制**。
- **布料/软体只有一条路径**（`newton_standalone`），PhysX 布料上游 "not actively maintained"。
- **深度 / IMU / LiDAR 全是几何真值**（无噪声）；**触觉未提及**。
- **`benchmark` 与 `ros` 两条栈独立，场景格式不得混用**。
- **3DGS → USD handoff 在仓库之外**（无 mesh 提取 / TSDF / USD writer）⇒ 数字孪生管线不完整。
- **无确定性（determinism）保证**；**多机器人未提及**。
- `[PAPER]` sim2real **R²=0.931 仓库无评测脚本**，不可复现。
- **LiDAR `fireTimeNs` 钳制 26000 ns，超窗静默返零点** —— 静默失效，不报错。
- 本库落差：原理层是 v3.2.0 的 `geniesim` CLI，经验层/代码层是 3.0 时期的 `app/app.py`，**命令不可直接套用**。

### 4.3 `lw_benchhub`

- ⛔ **离线不可用** —— 厨房资产运行时经 `lightwheel_sdk` 从云端拉取，**`import` 阶段就调 `list_registry()`**。内网/断网环境直接排除。
- ⚠️ **底座自称 alpha**：Arena README 明写 "APIs will break without deprecation warnings … **Do not use this in production**"。⇒ **不要升级 isaaclab 或 Arena 子模块**（monkey patch 按 pin 住版本写死：上游 10 处、复现仓库 11 处）。
- **README 规模数字有 4 处与代码不符**：任务 **272**（非 268）、机器人 **28**（非 27）、layout 至 **62**（非 100）、**rsl-rl 只注册不执行**。估工作量以 `background_knowledge.md` §4.2 为准。
- **只有 RGB，且无任何噪声模型**（`enable_corruption=True` 是假开关）⇒ **一切鲁棒性结论都带"无传感器噪声"这个前提**。
- **无稳定 Python 评测 API**（issue #45 未关闭）；**一个进程内只能有一套配置**（全局单例 `Context`）。
- **YAML 静默覆盖命令行参数**（含 AppLauncher 的 `--device`）—— 8 个入口脚本都在 `parse_args()` 之后执行 `args_cli.__dict__.update(yaml_args.__dict__)`，**命令行显式传的值被无声丢弃**；`teleop_base.yml:6` 是 `device: cpu`，所以 `--device cuda:0` 实际仍跑 CPU。**要改这类值就改 YAML。**
- **cuRobo 走 `autosim` 插件，而该包源码不在仓库、也未在 `pyproject.toml` 声明**（装完仍 ImportError）⇒ 运动规划能力不在本体内。
- **episode 时长基本改不动**；RL 面极窄（6 配置全在 `LiftObj`）；课程学习是空壳。
- **官方无任何 FPS 数字** ⇒ 性能不可预估。
- 复现层三条硬约束：`numpy==1.26.0` 必须最后装并每次 pip 后锁回；运行脚本用 `set +u`（**不是** `set -u`）且必须 `unset CUDA_VISIBLE_DEVICES`（否则相机初始化 segfault 且无 traceback）；**Isaac Sim 必须先启动再构造 cuRobo IK**（顺序颠倒会在 USD 纹理分配时 `cudaErrorIllegalAddress`）。

### 4.4 `ge_sim_v2`

- ⛔ **它不是物理仿真器** —— 无物理引擎、无渲染器、无场景文件。**不能增删物体、不能换本体、不能改相机**；三视角（head / left_wrist / right_wrist）与 384×512 固定；**只出 RGB**。
- ⛔ **不能换本体** —— FK 以预编译 `_g01_fk.so`（仅 linux x86_64）发布，官方明确不发 URDF 与机器人几何。
- ⚠️ **开源是"可用的推理发行版"而非"可复现的研究发行版"** —— 未发布训练/蒸馏代码、非蒸馏权重、**World Judge 奖励模型**、URDF/FK 源码。**直接后果：开箱即用时 `reward` 与 `progress` 恒为 `None`**，论文主打的"自带可验证奖励"要自己补。
- ⚠️ **论文 v1 与发布权重 `community v2.0.1` 不是同一交付物**。
- **三处宣传口径必须打折**（详见 `background_knowledge.md` §8.2）：① "100 帧 / 2.3 秒" 实为 **25 帧 × 4× 跳帧的覆盖跨度**（应写"25 帧 / 2.3 s，配合 4× 跳帧可覆盖约 100 帧跨度"）；② "可做 RL" 只见于公众号，论文列为 future work、正文只演示离线过滤式 BC；③ "登顶 WorldArena" 指**活榜而非那篇基准论文**（其正文 grep `GE-Sim` **命中 0**），且该基准作者自述 **EWMScore 与动作规划仅 r=0.36 弱相关**。
- **两套 16 维布局不同**：世界模型侧 `[L7臂, L夹爪, R7臂, R夹爪]`，策略侧 `[L7臂, R7臂, L夹爪, R夹爪]` —— **用错不报错、只是行为错**，务必走 `types.py` 的 `wm_state_to_policy_state()`。这是本项目最高频的静默错误。
- **实测吞吐 0.88 帧/s ≈ 0.055× 实时** ⇒ 只适合**离线批量 rollout**；估预算按此数字算，不要按论文的 2.3 秒算。落盘 `keep_frames=True` 约 **7 MB/帧**，**代码盘与产物盘必须分开，产物盘 ≥50 GB**。
- **分布外不可靠**：新场景/新物体/新任务、以及需要精确物理判定（力、摩擦、稳定性）的问题都不在能力范围内。
- ⚠️ **`Q41` / `P41` 明确"未解决"** —— 源料内部记录自相矛盾且未收口，引用前先读原文。

---

## 5. 反向选型：这 4 个都不合适的情况

| 你的需求 | 现状 | 建议 |
|---|---|---|
| **多机器人 / 多智能体协作** | 4 个项目**全部未提及**（`lw_benchhub` 有双臂本体，但那不是多智能体） | 需另选工具链或自行扩展；**别指望这 4 个开箱支持** |
| **多 GPU / 分布式训练** | `genesis_world` 列在 `未提及` 清单；其余三个亦无证据 | 单机单卡规划；`genesis_world` 单卡并行度已很高，先压满单卡 |
| **驾驶 / 户外 / 大场景导航** | 都是桌面或室内 manipulation 域 | 不适用 |
| **工业装配等高精度接触** | `genesis_world` 的 IPC 耦合器最接近，但"**不是无条件保险**" | 需自行验证你那组材料与接触参数 |
| **需要 bit-level 确定性复现** | `genie_sim_v3` 明确**无确定性保证**；其余未声明 | 用固定种子 + 多次重复取统计量，不要指望逐帧一致 |
| **音频 / 触觉为主的任务** | 触觉只有 `genesis_world` 有（且 `ElastomerTaxel` 非真 FEM）；音频 4 个全无 | 不适用 |

---

## 6. 关联文档

| 文档 | 什么时候用 |
|---|---|
| [`common_reproduction_guide.md`](common_reproduction_guide.md) | 选定工具链之后 —— 通用复现流程（准备 / 安装 / 运行调试 / 调优 / 验收 / 记录） |
| [`common_issues_solutions.md`](common_issues_solutions.md) | 装或跑的过程中撞墙 —— 跨项目问题分类库（A–M 类 + 14 条重复问题榜 + 9 步排障流程） |
| [`best_practices.md`](best_practices.md) | 想避免已知代价 —— 四个项目 §6 教训的主题化汇总 |
| [`terminology_mapping.md`](terminology_mapping.md) | 读到看不懂或跨项目含义不同的术语 |
| [`../projects/00-index.md`](../projects/00-index.md) | 选定后进入项目级五层文档；先读该项目的 `quickstart.md` |

**各项目原理层 §4（关键特性）/ §8（已知限制）直达**：
[`genesis_world`](../projects/genesis_world/background_knowledge.md) · [`genie_sim_v3`](../projects/genie_sim_v3/background_knowledge.md) · [`lw_benchhub`](../projects/lw_benchhub/background_knowledge.md) · [`ge_sim_v2`](../projects/ge_sim_v2/background_knowledge.md)


