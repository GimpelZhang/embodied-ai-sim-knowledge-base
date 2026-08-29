# LW-BenchHub 复现经验知识（AI Agent 实战复盘）

> **⚠️ 证据等级声明**：本文档**全篇为 `[实践]` 级**，即本机一次具体复现过程中的踩坑记录与事后结论，**不是官方结论**，也不构成对上游行为的普适断言。上游版本迭代后部分现象可能已消失。
> 需要 `[CODE]` / `[README]` 级证据请查 [`background_knowledge.md`](background_knowledge.md)。
> 按报错现象快速查询请用 [`troubleshooting.md`](troubleshooting.md)。
>
> **隐私处理**：原始材料中的账号、sudo 口令、HF token、LLM API key **一律未收录**；所有本机绝对路径统一写作 `<path>`，用户目录写作 `<user_home>`。
>
> **编号约定**：`P`（问题）/ `D`（决策）/ `L`（教训）**只追加、不重排、不复用**，外部交叉引用依赖此约定。

---

## 1. 复现目标与背景

### 1.1 目标

在一台**无图形界面的云服务器**上，用光轮智能 `LW-BenchHub` + NVIDIA `IsaacLab-Arena` + HuggingFace `lerobot` 三者组合，跑通 **VLA（Vision-Language-Action）策略的闭环仿真评测**，并产出人类可直接查看的交付物（`.mp4` 闭环视频 + `.png` 单帧 + 指标 JSON）。

复现分四个阶段递进：

| 阶段 | 目标 |
|---|---|
| **Stage 1** | 跑通至少一条 VLA 闭环，拿到非零成功率 |
| **Stage 2** | 用 LLM 自动生成新场景，并对生成场景做**可达性验证**后再评测 |
| **Stage 3** | 搭建多策略 / 多本体的统一基准调度 |
| **Stage 4** | 建数据飞轮：自动生成可用于微调的示教数据集 |

### 1.2 硬件与软件基线

| 项 | 值 |
|---|---|
| 操作系统 | Ubuntu 22.04（云服务器，**无显示器**） |
| GPU | NVIDIA A800-SXM4-40GB（`sm_80`） |
| 驱动 | 起始 535.113.01 → 最终 **580.159.03**（见 `P04`） |
| 系统 CUDA | nvcc 11.8（**不匹配 torch**，见 `P10`） |
| Python | 系统 3.12，实际使用 **3.11**（Isaac Sim 要求） |
| Isaac Sim | 5.1.0 |
| Isaac Lab | v2.3.0 → 实际 v2.3.2（pip 包版本 0.54.2） |
| IsaacLab-Arena | `release/0.1.1` |
| lw_benchhub | 0.1.0（`-e` editable 安装） |
| lerobot | 0.5.1 |
| numpy | **必须 1.26.0**（见 `P03`） |
| torch | 2.7.0+cu128 |
| warp-lang | **必须 1.8.1**（见 `P11`） |

### 1.3 两条评测路径

| | 路径 A | 路径 B |
|---|---|---|
| 模型 | `nvidia/pi05-arena-gr1-microwave`（π0.5，约 7B） | `LightwheelAI/smolvla-double-piper-pnp`（SmolVLA，约 300M） |
| 本体 | GR1 人形（`gr1_pink` / `gr1_joint`） | `DoublePiper-Abs` 双臂 |
| 任务 | 开微波炉门 | 把黑碗放到盘子上（`L90K1PutTheBlackBowlOnThePlate`） |
| obs / action 维度 | 54 / 36 | 16 / 12 |
| 相机 | **1 路**头视角 | **3 路**（左手 / 右手 / 第一人称） |
| 最终成功率 | **0%**（工程 bug 修完后仍为 0，归模型能力，见 `P19` `P22`） |**40%（4/10）** ✅ |

**路径 B 成为后续全部阶段复用的"黄金路径"** —— Stage 2/3/4 的所有实验都以它为控制组。

### 1.4 用户侧硬约束（贯穿全程）

1. 所有安装落在大容量挂载点（系统 `/` 分区容量紧张）→ 促成 `D03`。
2. 必须在**无显示器**服务器上跑通 → 促成 `D02`。
3. 必须产出**人类可看的视频/图片**，不接受只有指标。
4. **执行不打折扣**：遇到阻塞要修到通，不允许悄悄降级或跳过。
5. Stage 3 起追加：必须以**光轮自家**工具链/模型/场景为主线（见 `D12`）。

---

## 2. 计划与执行流程

### 2.1 阶段时间线

| 时间 / 阶段 | 主要动作 | 结果 |
|---|---|---|
| 初始计划 | 双轨方案定型，随后升级为 headless + 交付物导向 | `D01` `D02` |
| 环境勘察 | 实地体检，暴露 4 个缺失项 | `P01` `P02` |
| Stage 1 路径 A | 驱动三段跳 → 首轮评测复盘 → 0% 根因攻坚 | `P04` `P17`–`P20` |
| Stage 1 路径 B | 13 处 API 漂移补丁，9 次重启修到通 | `P06`–`P09` |
| **2026-06-22** | **路径 B 跑通，成功率 40%** | ✅ 里程碑 |
| **2026-06-27** | Stage 2 计划纠偏；v1 完成（跳过可达性验证，3 场景全 0%） | `P25` `D06` |
| 2026-06-27 | 独立 `autosim` env 零 sudo 装通 cuRobo（8 个坑） | `D08` |
| Stage 2 v2→v4 | 可达性门连续三次自我否定 | `P26` 类同源 |
| Stage 2 v5 | 两个 BLOCK 解掉，但撞上 warp ABI 冲突 | `P05` `P10` `P11` |
| **2026-06-27** | **Stage 2 v6：live reach gate 打通**（真启 Isaac Sim + cuRobo IK） | ✅ 里程碑 |
| **2026-06-28** | 交付 `LW_Benchhub_Interface.md`：五层栈全链路溯源 | ✅ 认知修正 |
| Stage 3 v1 | NVIDIA 跨本体方向；AI 自查出 `gr1_white` 不存在 | 被用户否决 |
| Stage 3 v2 / v3 | 改跨品牌；再改多策略字典矩阵 | `D12` `D13` |
| **2026-07-03** | `Stage4_Plan_Detailed.md` 推翻 skeleton 全部伪造 API | `D17` |
| Stage 4 T3 | 生成双臂 URDF，修 7 个 bug，seed 48 跑通 6/6 技能 263 帧 | `D14` |
| Stage 4 v2 | **发现 `success=True` 在撒谎**，8 episode 全失败 | `P29` ⚠️ |
| **2026-07-05** | 接触力埋点**否定**"动态碰撞推碗"假设 | `P30` 反转一 |
| 2026-07-05 | Phase 1 四个坑修完，交付 **10 ep / 6527 帧**数据集 | ✅ 里程碑 |
| **2026-07-10** | commit `88f5999`：第 10 次运行证明"推碗"从未发生 | `P30` 反转二 |
| **2026-07-11** | Patch 02：Issue A 修复；Issue B 判定为运动学硬限制 | `P33` `P34` |

### 2.2 执行流程的典型模式

复现全程反复出现同一个循环，值得单列：

```
读文档 / 写计划  →  实地 grep 核实      →  多数情况：计划被推翻重写
                          ↓（核实通过）
                     实现 + 跑
                          ↓
                     结果异常  →  提假设（常 2–3 条）
                          ↓
                     逐条埋点排除  →  多数假设是错的
                          ↓
                     定位真根因  →  修  →  验证
```

**关键观察**：本次复现中「计划阶段被自己或被用户推翻」发生了 **5 次**（`P25` Stage 2 schema、Stage 3 v1→v2→v3 两次、`P26` 飞轮字段、`D17` Stage 4 skeleton），而每一次的根因都是**同一类**：计划建立在"以为存在"的 API / 字段 / ID 之上，而没有先 grep 核实。见 `L02`。

### 2.3 阶段间的资产复用关系

- Stage 2 v6 的 **reach gate**（`validate_scene_objects_reach_v5.py`）被 Stage 4 T3 直接继承。
- Stage 1 路径 B 的 CLI 与配置被 Stage 2/3/4 **1:1 复用**，只改少数字段 —— 这是能把变量控制住的前提。
- 各阶段的 `*_env.sh` 环境脚本层层叠加，最终形成 `lerobot_arena_curobo_env.sh`。
- 已完成阶段的输出目录被列为**只读资产清单**，禁止后续阶段覆盖（见 `D18`）。

---

## 3. 关键决策与原因

| ID | 决策 | 原因 | 事后评价 |
|---|---|---|---|
| **D01** | 双轨并行（路径 A + 路径 B） | 无法预判哪条能通，并行降低总风险 | ✅ 正确。路径 A 卡了很久，正是路径 B 打破死锁 |
| **D02** | 全面走 headless EGL，交付物必须含视频 | 服务器无显示器；用户要求可视化 | ✅ 正确。且视频后来成了排障手段（见 `P26` 的假阳性是靠"视频看着空"发现的） |
| **D03** | conda 的 `pkgs_dirs`/`envs_dirs` 重定向到大容量挂载点 | 系统盘容量紧张 | ✅ 正确，此后再未遇到磁盘问题 |
| **D04** | numpy 一律"最后装、每次 pip 后回锁" | Isaac Sim 5.1.0 的 C 扩展硬绑 1.26.0 | ✅ 正确，但**执行成本高**：这是全程重复次数最多的动作 |
| **D05** | `PiperPinocchioIK` 从 `raise` 改为 **lazy stub** | cmeel 的 pinocchio wheel 不含 casadi 绑定，硬 raise 会阻断整条启动链 | ⚠️ 双刃剑。让流程跑通了，但后来有人（见 `P32`）差点把它当可用 IK 去调用 |
| **D06** | 可达性检查**显式改走 cuRobo**，不用 pinocchio | 因 `D05` 后者已是 stub | ✅ 正确 |
| **D07** | 在 conda env 内装 CUDA toolkit，不动系统、不用 sudo | 无 sudo 权限；且不能破坏已跑通的基线 | ✅ **最有复用价值的决策之一** |
| **D08** | 为 cuRobo 另建完全隔离的 `autosim` env | 避免污染已跑通的主环境 | ✅ 正确。代价是同一个库要装两遍 |
| **D09** | `warp-lang` 精确锁 `==1.8.1` | Isaac Sim 5.1 自带 1.8.2 但 PyPI 无该版本，1.8.1 是同 minor 系列唯一可得 | ✅ 正确，但**是软锁**：升级 Isaac Sim 后必须重新探测 |
| **D10** | reach gate 用 `rotation_threshold=π`（只判位置不判姿态） | 姿态约束会让工作空间边缘全部规划失败 | ⚠️ 权衡。它让门能用，但产生了"点可达而实际抓不到"的假阳性（`P34` 即此类） |
| **D11** | 双臂 IK 用**单臂镜像 ±0.15 m** 近似 | 无已验证的双臂 URDF，真双臂需 12-DoF 配置 + 自碰撞约束 | ⚠️ 已在交付时**主动自曝**为局限。足以*否决*不可达场景，不足以*保证*可达场景无自碰撞 |
| **D12** | Stage 3 放弃 NVIDIA 主线，回到光轮模型/场景 | **用户强制**：v1 把"展示光轮能力的 Demo"变成了纯 NVIDIA 官方示例，属"严重去光轮化偏差" | ✅ 正确。这是外部纠偏，AI 自己没意识到方向漂移 |
| **D13** | 废弃"同一 VLA 控不同硬件"，改**多策略字典矩阵** | 关节空间策略有强硬件专一性；动作维度本身与本体绑定 | ✅ 正确，且有 `P22` 的定量证据支撑 |
| **D14** | T3 采用 **Option B：两个单臂规划器**，而非单个 12-DoF 规划器 | `EnvExtraInfo.ee_link_name` 是单值、`_build_world_state()` 只有一个 EE 索引；且单臂配置已被 reach gate 验证 | ✅ 正确（在当时约束下）。但它与 `D11` 同源，最终在 `P34` 处撞上边界 |
| **D15** | T1 明确标记 **BLOCKED** 而非绕过 | 要修必须升 Isaac Lab 到 v2.4+，会破坏全部 v2.3.x 补丁，代价不划算 | ✅ 正确。**声明失败的成本远低于让假结果流入交付** |
| **D16** | 放弃 scripted cuRobo，改用 **SmolVLA 闭环自滤波**产数据 | `P34` 已判定为运动学硬限制；而 SmolVLA 40% 成功率是已验证资产 | ✅ 正确。用已验证能力换交付确定性 |
| **D17** | 场景难度控制改用 **seed sweep + `fix_object_pose_cfg`** | 原 skeleton 里的难度 API 全不存在（`P26` 同源） | ✅ 正确。两者都是 grep 可证的真实机制 |
| **D18** | 失败轨迹**原样保留不覆盖**，并加显式警告 README | 避免后续误把失败数据当示教数据用 | ✅ 正确 |

---

## 4. 遇到的问题与解决方案（核心章）

> 本章共 **38 条**（`P01`–`P38`），按**故障类别**分为 5 组。
> 按**报错现象**查询请用 [`troubleshooting.md`](troubleshooting.md)（同一批事实的另一个视图，`Qxx` ↔ `Pxx` 一一对应），不必两边都读。
> 「❌ 无效尝试」列记录**试过但没用**的做法 —— 这是本章最省时间的部分。
>
> 📌 **与代码直接相关的条目，去代码层看机制与物证** → [`code_knowledge.md`](code_knowledge.md)（描述对象是本机复现仓库 `lw_benchhub_tour`，`[CODE]` 级可逐行核实）：
>
> | 本章条目 | 代码层对应章节 | 那里能拿到什么 |
> |---|---|---|
> | `P05` namespace 包遮蔽 | **§6.2 #7**、§8.4 #4 | 改的是**外层** `lw_benchhub/__init__.py`；内层与上游逐字节相同（本条描述据此收窄） |
> | `P07` pinocchio 无 casadi 绑定 | **§3.6（M6 `piper_ik.py`）** | lazy stub 与 `_is_stub` 守卫的确切行号（`:20-31`、`:56-71`、`:325-329`） |
> | `P08` `DEVICE_MAP` / `ENDPOINT` 消失 | §6.2 #1、#3 | 补丁的优雅跳过分支与 SDK fallback 的行号 |
> | `P09` xform op 顺序强校验 | **§3.1（M1 第 11 个补丁）** | `patch_xform_prim_view_auto_standardize`（`:708-743`）—— **本地新增的第 11 个补丁** |
> | `P12` setuptools_scm 探测失败 | §6.2 第 11 项 | 改的是 `AutoDataGen/dependencies/curobo/src/curobo/__init__.py:53-58` |
> | `P13` `P14` `P15` 编译与启动 | **§5.3**、**§2.1** | cuRobo 编译期环境变量；**六行运行前奏**（本项目一切脚本的前置） |
> | `P25` `P26` 配置键无人读取 | **§6.3**、**§7.2** | `fix_object_pose_cfg` 的 6 点贯通链（每一环都静默失败）+ 11 条静默失效路径 |
> | `P29` `P35` 成功判定不可信 | §3.4（M4）、§7.4 | **6 种并存的成功判定实现**，以及它们为什么会互相矛盾 |
> | `P30` 为不存在的现象修三轮 | §3.2（M2 的四个 `_log_*` 诊断） | 约 120 行 Issue-B 取证代码 —— 这是"先量化再修"的反面教材实物 |
> | `P31` `P34` cuRobo 规划失败 | **§4.3**、§3.2、§2.8 | `piper_curobo.yml` 单臂 6 关节 / `rotation_threshold=π` / 碰撞体全空；"双臂"= 单臂 + 硬编码 `ARM_LATERAL_OFFSET = 0.15` |
> | `P36` PNG 导出 40 分钟 | §3.5（M5 `_fast_png_save:30`） | 已做的 `compress_level=1` 优化（仍不够） |
> | 「改了却没生效」这一类共性 | ⭐⭐ **§7.2 静默失效 11 条 + §7.3 两份 vendored IsaacLab** | **改错哪一份 IsaacLab 不报错也不生效**，附判别法 |
>
> ⚠️ 两层冲突时**以代码层为准**（可逐行核实）；被它推翻或收窄的本层结论集中在其 §8.4。

### 4.A 环境与安装类（P01–P16）

| ID | 现象 | 根因 | 解决方案 | ❌ 无效尝试 |
|---|---|---|---|---|
| **P01** | nvcc 路径查找失败，报错形如 `':/usr/local/cuda-11.8/bin/nvcc'` | `CUDA_HOME` 环境变量带**前导冒号** | `export CUDA_HOME=/usr/local/cuda`（去掉冒号） | — |
| **P02** | LFS 资产为空 / headless 渲染起不来 / Isaac Sim 拒绝启动 | 三项前置缺失：`git-lfs` 未安装、`libnvidia-egl-*` 缺失、系统 Python 是 3.12 而 Isaac Sim 要 3.11 | 装 `git-lfs` 并 `git lfs pull`；装 `libnvidia-egl-*`；conda 建 Python **3.11** 环境 | — |
| **P03** | 随机 `ImportError` 或 Segfault，尤其在 Isaac Sim 的 C 扩展中 | Isaac Sim 5.1.0 编译期硬绑 `numpy==1.26.0`；**任何 pip 操作都可能把 numpy 顶到 2.x** | 顺序纪律：其它依赖先装，numpy 最后装；此后每次 pip 之后立刻 `pip install --no-deps numpy==1.26.0` 并 assert 校验 | — |
| **P04** | Vulkan / GPU PhysX / RTX 渲染器异常 | 驱动**内核模块 535.113.01 与 GL 库 535.309.01 版本不匹配** | 升级驱动到 **580.159.03** | 装 535.309.01 DKMS 求版本对齐 —— Vulkan `vkCreateDevice` 仍失败 |
| **P05** | `ImportError: cannot import name 'CONFIGS_PATH' from 'lw_benchhub'` | 仓库外层有一个 `pkg_resources.declare_namespace` 存根，当从仓库目录**之外**启动 Python 时它遮蔽了内层真包 | 把外层 `__init__.py` 重写为 `importlib.util` shim：`spec_from_file_location` 加载内层真包并 `sys.modules[__name__] = inner`（原文件备份） | **4 种修法全失败**：剔除 `sys.path` 条目 / 预导入内层 / 只改外层导出 / 把脚本移进包内 —— traceback 都指回同一文件 |
| **P06** | 一连串 `ModuleNotFoundError` | `pyproject.toml` **漏声明 9 个运行期依赖** | 批量补装；其中 **`qpsolvers` 必须精确 `==4.8.1`**、**`vuer` 必须带 `[all]` extra** | — |
| **P07** | `pinocchio is required for PiperPinocchioIK`；装上后仍报 `AttributeError: ... has no attribute '_model'` | cmeel 分发的 pinocchio wheel **不含 `pinocchio.casadi` 绑定** | 把 `__init__` 改为 **lazy stub**（置 `_is_stub=True` 不抛异常），并给 `reset()` 加 stub 守卫（见 `D05`） | — |
| **P08** | `ImportError: DEVICE_MAP from teleop_device_factory`；`ImportError: ENDPOINT from lightwheel_sdk.loader` | IsaacLab v2.3.x 移除了 `DEVICE_MAP`/`RETARGETER_MAP`；lightwheel SDK 1.0.3 把 `ENDPOINT` 从 `.loader` 搬到 `.client` | 给 teleop 补丁函数加 `try/except` 优雅跳过；给 SDK import 加 fallback 分支 | — |
| **P09** | `ValueError: ... is not a xformable prim with standard transform operations` | IsaacLab v2.3.x 强校验 xform op 顺序为 `[translate, orient, scale]`，而涉事 SimReady USD 用的是 `[translate, rotateXYZ, scale]` | 新增补丁函数强制 `validate_xform_ops=False` | 调用 `standardize_xform_ops()` 就地修复 —— prim 来自子图层、Sdf 写权限被拒，改不了 |
| **P10** | cuRobo 编译报 `CUDA mismatch 11.8 vs 12.8`；或装上后 `import curobo` segfault | 系统 nvcc 是 11.8，而 torch 是 cu128 编译的 | **在 conda env 内**装 `cuda-toolkit=12.8`（无需 sudo），并 `export PATH=$CUDA_HOME/bin:$PATH` 让它优先于系统 nvcc（见 `D07`） | 直接在系统层升 CUDA —— 无 sudo 权限 |
| **P11** | `AttributeError: module 'warp.types' has no attribute 'array'` | pip 默认拉 `warp-lang 1.14.0`（已删该 legacy 属性），污染 `sys.modules` 后 Isaac Sim 自带的 warp 模块在 import 期崩溃 | `pip install --no-deps warp-lang==1.8.1`（Isaac Sim 自带 1.8.2 不在 PyPI，1.8.1 是同 minor 唯一可得），随后立刻回锁 numpy | **4 种缓解全失败**：预先 import cuRobo / 设 PRETEND_VERSION 环境变量 / 重命名 `curobo/.git` / 调换 import 顺序 |
| **P12** | `LookupError: setuptools-scm was unable to detect version for curobo` | cuRobo 在 import 期走 `setuptools_scm` 探测版本，但在 Isaac Lab 之后 import 时解析到的是 Isaac Sim 私有打包的那份拷贝，**它忽略 `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_*` 环境变量并直接抛错** | 改 cuRobo 的 `__init__.py`，在任何 setuptools_scm 逻辑**之前**先读该环境变量返回（原文件备份） | 只设 `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO` 环境变量 —— 私有拷贝不认 |
| **P13** | cuRobo 编译报 `cuda.h not found` / 编译期 OOM / `libstdc++.so.6: CXXABI_1.3.15 not found` | ① conda 把 CUDA 头文件放在 `$CUDA_HOME/targets/x86_64-linux/include/` 而非 `include/`；② 默认并行度过高；③ 系统 libstdc++ 版本旧 | ① env 脚本首次 source 时自动建**符号链接**到 `$CUDA_HOME/include/`；② `MAX_JOBS=4`；③ 调整 `LD_LIBRARY_PATH` 指向 env 内的 libstdc++。另需 `TORCH_CUDA_ARCH_LIST="8.0"`（A800 是 sm_80）否则编译数小时 | — |
| **P14** | 运行脚本立刻 `unbound variable` 中止 | conda 的 CUDA 激活脚本引用了未绑定变量（如 `NVCC_PREPEND_FLAGS`） | 脚本必须用 **`set +u`**，不能用 `set -u`。原文注释："Hours were lost on this before changing to `set +u`. Do NOT switch back." | — |
| **P15** | Isaac Sim 在相机初始化时**直接 segfault，无 traceback** | 设置了 `CUDA_VISIBLE_DEVICES`，而 Isaac Sim 自行枚举显卡 | 运行前 **`unset CUDA_VISIBLE_DEVICES`**。⚠️ 此项**不能写进 shell 配置文件**，只在每次评测前执行 | — |
| **P16** | `cudaErrorIllegalAddress`（发生在分配 USD 纹理时） | Isaac Sim 与 cuRobo 的初始化**顺序错了** | **必须先启动 Isaac Sim，再构建 cuRobo IK**；反序必崩 | — |

### 4.B 策略推理与评测类（P17–P24）

| ID | 现象 | 根因 | 解决方案 | ❌ 无效尝试 |
|---|---|---|---|---|
| **P17** | ① 视频只有 2 秒；② 50 个 episode 只出 10 个视频；③ 进程在"还剩 40 个"时结束 | 三者**都不是故障**：① 环境配置 `episode_length_s=2.0` 配合 `dt`/`decimation` → 每 episode 恰好 100 步 → 50 fps 下 2.0 秒；② 评测脚本里 `max_episodes_rendered` 是**硬编码**；③ 是正常完成（总耗时约 3202 秒 / 平均 64 s per episode） | 认识到这是配置与硬编码的正常表现；要改视频长度需改环境配置的 `episode_length_s`，要改录制数量需改脚本硬编码值 | 当作 OOM / 崩溃去排查 |
| **P18** | 加载 checkpoint 时报 437 个 key 不匹配，只有一句 warning | safetensors 里的键路径是 `vision_tower.vision_model.*` 而模型期望 `vision_tower.*`；键名修复函数**只打 warning 没做重映射** → **视觉编码器实际用随机权重，模型"看不见"** | 在模型代码的键名修复处把前缀 `vision_tower.vision_model.` 替换为 `vision_tower.`；修复后应出现 "All keys loaded successfully!" | ⚠️ 注意：修完这条**机器人仍然不动** —— 它只是并列问题之一，不是主因（真主因见 `P19`） |
| **P19** | ⭐ 机器人只单臂轻微抽搐、不伸向目标、成功率 0%；动作数值近零 | **checkpoint 的 `config.json` 里 `compile_model: True` + `compile_mode: max-autotune`**，模型代码据此对推理函数调 `torch.compile(mode='max-autotune')`，该模型的动态计算图在此模式下解算错误 | **直接改 HF 缓存里的 `config.json` blob**，把 `compile_model` 置 `False`（原 blob 备份为 `.bak`）。修复后动作 `absmean≈0.6, std≈0.7`，与训练分布（`action.std` 0.68）吻合，视频里双臂均有明显运动 | **三条假设里两条是错的**：① 怀疑 pip 装 extra 时篡改了 numpy —— 实测就是 1.26.0；② 怀疑 headless EGL 黑屏让 VLA 看不见 —— 抽帧显示画面清晰。**另：只设 `TORCH_COMPILE_DISABLE=1` / `TORCHINDUCTOR_DISABLE=1` 无效**（见 `L04`） |
| **P20** | 想给单相机 VLA 加左右手相机以提升成功率 | 方案在架构层不可行 | 放弃该方案。若真要 3 相机，必须重新采数 + 重训 | 直接加 2 路相机输入 —— **四层证据链否定**：① 模型归一化统计只有 1 个相机；② 模型代码对空相机槽填 -1 且 **mask=0**，架构被训练为忽略第 2/3 路；③ **铁证** —— 训练数据集元信息里只有 1 个相机特征；④ 同厂商全家族模型均为单相机，且部分需独立推理栈、不兼容当前评测 CLI |
| **P21** | 取不到成功率指标；或退出码显示成功但实际报错了 | 三个陷阱：① **评测 CLI 不写 `eval_info.json`**；② 日志里的 `running_success_rate` **是百分数**（`20.0` 表示 20%）；③ 评测进程可能在 RuntimeError 后**仍 exit 0** | ① 必须从日志 grep `running_success_rate`；② 存成分数前要 `/100`；③ 真实退出码从日志里的 `EXIT_CODE:` 行反推，不能信 `$?` | 信 `$?` 的返回值 |
| **P22** | 换任务 / 换场景后成功率一律 **0%** | checkpoint 只在**单一任务**上微调过，属**分布外泛化失败** | 判定为模型能力边界，**不是接口 bug**：同任务稳定 40%，跨任务 0%。要提升必须换模型或微调，改任何接口都无效 | 怀疑图像分辨率不匹配导致 OOD —— 实测环境渲染分辨率与模型声明不同，但策略侧会**自适应 resize**，与 OOD 无关（见 `P23` 所在的接口梳理） |
| **P23** | `gym.NameNotFound: <某 task>` | LLM 从任务映射 CSV 里挑了一个**合法但未在 Gymnasium registry 注册**的 `(layout, task)` 组合 | 校验器捕获该异常 → 生成器把该 pair 加入 **ban 列表**并重新生成（限定最多若干轮） | — |
| **P24** | Isaac Sim boot 阶段**无限挂起、无任何输出** | 某些 layout/task 组合会让 Isaac Sim 在启动期卡死（实测烧掉 **58 分钟** CPU 无进展） | 只能人工 `pkill -9`。**由此确立纪律：任何 Isaac Sim 长跑都要设外部 wall-clock 超时并预留强杀手段** | 等它自己恢复 |

### 4.C 场景生成与配置类（P25–P28）

| ID | 现象 | 根因 | 解决方案 | ❌ 无效尝试 |
|---|---|---|---|---|
| **P25** | 按计划写的场景生成器产出的配置**完全跑不通** | 计划假设了一套**本机不存在的 YAML schema**（形如 `task:`/`objects.<name>.position` 显式声明物体坐标）。实际 schema 是 `task` + `robot` + `scene_backend` + `task_backend` + `layout` 的注册制，**物体位置根本不在配置里声明**，而由 `sources` + `layout` + `seed` + 重采样开关共同决定 | 重写计划：LLM **只允许改白名单字段**（`task` / `layout` / `seed` / `episode_length_s` / 重试上限 / 重采样开关），并用任务映射 CSV 做**本地 schema 校验**拒绝 LLM 幻觉出的 `(layout, task)` 组合 | 按文档里看到的 schema 直接生成 —— 那套 schema 是别的版本或臆想的 |
| **P26** | ⭐ 脚本"在调场景难度"，日志也在正常汇报诊断结果，但难度**毫无变化** | 脚本往配置里追加了一个**代码库中无任何解析处**的键（形如 `scene_generation_difficulty: hard_offset_0.35`）；更糟的是"诊断结论"是一句**硬编码 print**，掩盖了字段无效的事实 | 改用两个**grep 可证真实存在**的机制：**seed sweep**（扫 seed 取物体距机器人最远的那个）+ **`fix_object_pose_cfg`**（代码里已消费、已尊重，只需在配置层做加法式暴露）。见 `D17` | 追加自定义难度字段；相信硬编码的诊断输出 |
| **P27** | LLM API 返回 200，但实际用的可能不是请求的模型 | 兼容端点会**静默改写模型名降级**到弱模型，请求 payload 里写什么不代表服务端跑什么 | **唯一可靠检查是回读响应体的 `model` 字段**并严格比对，不一致就报警中止（后期升级为直接 raise）。配套：双鉴权头同发；`max_tokens` 必填；用标准库 `urllib` 零依赖实现，避免第三方 SDK 的隐式重试掩盖问题 | 信请求参数里写的模型名 |
| **P28** | 某个 seed 挂 3 小时，日志里 `scene retry 1/5` 重复上百次 | 场景重试计数器**每次自增后又被模型重载重置**，导致重试上限**永不触发**，形成死循环。另有 seed 因物体离机器人太近（约 0.23 m）而放不下 → `SamplingError` | ① 调度器加 **hang-killer**（重试日志行数超过阈值就 kill）；② 课程 band 重定义为可达范围 **≥0.26 m** 的三分位；③ 换成 fresh-boot 验证过的 seed | 依赖代码里的 `max_scene_retry` 上限 —— 它永远不会生效 |

### 4.D scripted cuRobo 管线类（P29–P34）

> 本组是整个复现中**最深刻的教训来源**。`P29`–`P30` 建议连读。

| ID | 现象 | 根因 | 解决方案 | ❌ 无效尝试 |
|---|---|---|---|---|
| **P29** | ⭐⭐ 管线报告"6/6 技能成功"、`success=True`，但**从没人验证碗到底有没有放到盘子上** | 技能序列执行器在**两种情形**都返回 `success=True`：一是环境的 `terminated` 真触发（真成功），二是"6 个技能都跑完了"（**根本没检查任务条件**）。实测 8 个 episode **全部 `early_return=0`** → 全部任务失败 | 在序列末尾显式调用任务的成功检查接口，与环境 `terminated` **用同一条件**判定 | 相信"技能链跑完 = 成功"。**这是本次复现最危险的坑**：它不报错、不崩溃，只安静地产出污染数据集（见 `L05`） |
| **P30** | ⭐⭐⭐ 观察到目标碗有 **+0.109 m** 位移，判定为"机械臂接近时把碗推开了" | **这个现象根本不存在。** 两次反转：**反转一** —— 接触力埋点实测夹爪三个 link 全程 **`max_gripper_force = 0.000 N`**，从未接触过碗；碗的微小移动来自 `reset` + `plan` 阶段的**物理 settling**。**反转二** —— 第 10 次运行才是**第一次真正的未打补丁对照组**，结果碗从头到尾一动不动，272 帧 6 技能无报错；原先记的 +0.109 m 是在**另一个场景**上观察到的 | 承认假设错误。seed 48 的真实失败是 `grasp` 闭合在空位（根因见 `P34`） | **三轮修复全部无效**（各花大量时间）：① 调 grasp z-offset；② 加 pre-grasp hover 先到上方 20 cm 再下降 —— 碗被"推开"**同样的 +0.109 m**；③ 给夹爪加 mesh 碰撞 —— 碗被推到**完全相同**的位置。三次"完全相同的结果"本应立刻提示"变量根本没起作用"（见 `L01` `L03`） |
| **P31** | 连续多次批量规划后崩 `RuntimeError: shape mismatch: value tensor of shape [N] cannot be broadcast to indexing result of shape [N, 1]`（N 不定） | 并非调用方的错：**"同一进程内连续多次批量规划"本身**会触发 cuRobo 内部结果累积器的形状错配。对照组很干净 —— 原始管线只调 1–2 次正常，改版调 6+ 次就崩 | 只能加 `try/except` 容错。⚠️ 规划器的 `reset()` **只清图规划缓冲与随机种子，不清 per-batch 结果累积器**，救不回来 | **9 次控制变量实验逐条排除 6 个假设**：关闭 CUDA graph 仍崩 / 对齐 seed 数量仍崩 / 预先构建 IK 求解器仍崩 / 规划后调 `reset()` 仍崩 / 去掉全部碰撞球改动仍崩 / **完全不用 IK 求解器纯用运动规划器仍崩** |
| **P32** | 碰撞球配置改完了，但碰撞检测**像没生效一样** | 两个**静默陷阱**：① 必须在 `collision_link_names` 里列出加了球的 link，留空会让 `total_spheres=0` 而**不报任何错**；② 不能给手指 link 加球 —— 球构建器会推断出 URDF 里**不存在的关节名**并直接 `ValueError` | 球心/半径**从真实 STL 顶点范围读 bbox** 后沿轴分段取内切球，而不是用未验证的占位值（过度膨胀会让规划器认为夹爪离目标太近而无法接近）。改完**必须跑测试脚本确认 `total_spheres > 0`** —— "yml 解析通过 ≠ 球加载了" | 用计划里给的未验证占位半径；把 `collision_activation_distance` **调小**到 0.02–0.04 —— **方向反了**：本地默认是 0.05，调小是在**减小**安全边际（更容易穿模），正确应 ≥0.06（最终取 **0.07**）。另：改用 pinocchio IK 做直线下降 —— 它是 stub（`P07`），任何调用都会 raise |
| **P33** | grasp 技能在 **`1 steps`** 就退出，机械臂停在 hover 高度而不是 grasp 高度 | hover 与 grasp **复用同一个 skill 实例**（注册器在循环开头只创建一次），而 `plan()` **不重置内部步计数器 `_step_idx`**。hover 跑完把计数器推到约 57，grasp 重新规划出 43 个 waypoint 的新轨迹后第一次 `step()` 就 `57 >= 43 → done=True`，**grasp 轨迹从未执行** | hover 之后显式调 `skill.reset()`。验证：从 `1 steps` 变成 `44 steps` | 用户下发的排查计划里假设"某技能有 `reach_threshold` 字段且默认过大" —— **该字段根本不存在**，技能是按 `step_idx >= len(traj)` 终止的（见 `L02`） |
| **P34** | 腕部到了碗正上方，但真实手指在碗**后方 0.34 m**，接触力全程 0 N | **规划器的 EE link 与仿真的 TCP link 不是同一个**：前者是腕部 link，后者是一个 **仅存在于仿真、规划器 URDF 里根本没有**的 link，同关节角下世界 X 轴相差 **0.30 m**（原计划估的"约 10 cm"—— 方向对量级错） | **判定为工作空间/运动学固有限制，不是可修 bug**，并如实写入交付文档。落地的只有增量改动：`P33` 的修复、批量规划的容错、把 `rotation_threshold` 从硬编码暴露为配置字段、加 EE-vs-目标诊断仪表 | **5 种修法逐一被阻断**：① grasp 目标补 `-0.30` 偏置 → 触发 `P31` 的 shape crash，**确定性复现 3/3**；② 降 seed 数 / 关图规划 → 仍崩；③ 限制规划尝试次数为 1 → 不崩了但单次尝试太弱、规划失败；④ 启用旋转约束（`rotation_threshold` 收紧到 0.1/0.5）→ **全部规划失败**（工作空间边缘）；⑤ 改 URDF 给腕部加固定偏置 → **link 局部坐标系的固定偏置是位姿相关的**，无法在所有位姿正确补偿，且确切变换锁在二进制 USD 里 |

### 4.E 数据集生成与工程基础设施类（P35–P38）

| ID | 现象 | 根因 | 解决方案 | ❌ 无效尝试 |
|---|---|---|---|---|
| **P35** | ⭐ 五个环环相扣的数据生成坑 | ① "一 episode 一进程"跑出 **0/3 成功**，而同一批 seed 在单进程内顺序跑是 40% —— 因为配置开了物体/机器人**重采样**，放置用的是 env RNG，**该 RNG 在进程内跨 episode 累积**；`env.reset(seed=N)` 只设 reset seed，不重置放置 RNG 的累积状态。② 一个 `terminated=True` 的**真成功 episode 被错误丢弃** —— 向量环境包装器在 `terminated` 后**自动 reset**（gymnasium 标准行为），循环外再查 raw env 读到的是下一 episode 的初始状态。③ episode 跑完、数据已存，但日志**缺尾**（无完成标记行）—— `os._exit(0)` 跳过 stdio flush。④ `pkill -9 -f "isaacsim"` 返回 exit 1 且杀不掉 —— `pkill -f` 匹配到含 pkill 自身的整条命令行，**自杀了父 shell**。⑤ 失败 episode 留下空 HDF5，导致数据集导出崩 `KeyError` | ① 改为"N 个 episode 在**同一进程内**顺序跑"，每 episode 只重置策略 + `env.reset(seed=base+i)`，env 跨 episode 保持存活。② **在 step 返回的瞬间捕获 `terminated`**（`task_success = last_terminated`），事后查询只用于打印诊断（且必须标注该位置是 auto-reset 后的、非 episode 末态）。③ `os._exit(0)` 前显式 flush stdout/stderr。④ 用**方括号技巧** `pkill -9 -f "[i]saacsim"` 规避自匹配。⑤ 导出前按 summary 的 `success` 字段过滤并清理空文件 | 认为"固定 seed 就能复现 40%" —— **误解**：在开了重采样的环境里固定 seed = 固定放置 = 0% 或 100%；那个 40% 来自基准 seed **加 per-episode 递增** |
| **P36** | 导出数据集耗时约 **40 分钟** | 10 episode × 约 652 帧 × 3 相机 ≈ 1.8 万张 PNG，单核约 2 fps | 接受该瓶颈并如实记录 | **不能换成 video 格式**（策略训练 schema 要求图像类型、禁用 video，已对照数据集元信息与模型配置核实）；调低 PNG 压缩级别几乎无效（2.2→2.3 fps，**瓶颈在 PNG filter 不在压缩**）；数据集库的并行编码开关**只对 video 生效** |
| **P37** | 长跑管线崩溃时只看到一行错误摘要，**看不到调用栈**，白烧两次运行 | 异常处理写的是 `except Exception as e: err = repr(e)`，只存 repr 不打 traceback | 补 `traceback.print_exc()`，随即定位到具体行号。**硬规则：长跑 pipeline 的异常处理必须打完整 traceback** | 靠一行 `repr(e)` 判断根因 |
| **P38** | LLM API 在 Isaac Sim 进程内约 **40% 概率 segfault**（日志停在"生成中"、无 traceback） | 疑为 Isaac Sim 进程内的 SSL / 网络栈冲突 | 给全部 seed **预填任务分解缓存**（该分解是确定性的，可复用先前已验证的结果，只改任务名）→ **运行期零 API 调用、零崩溃** | 加重试 —— 是进程级 segfault，重试不在同一进程内生效 |

---

## 5. AI Agent 表现评估

### 5.1 做得好的部分

| # | 表现 | 证据 |
|---|---|---|
| 1 | **不满足于表面症状，追到机制层** | `P19` 从"机器人不动"追到 checkpoint 配置里的一个布尔字段；`P05` 从 ImportError 追到 namespace 包遮蔽 |
| 2 | **主动自我否定，而不是护着已有产出** | 可达性门 v2→v3→v4 **三次自己推翻自己**；`P30` 主动补做对照实验并承认整条因果链是错的 |
| 3 | **主动做诚实局限披露** | v6 单开一节列 6 条 "documented bounds"，含**自曝双臂 IK 只是单臂近似**（`D11`）；最终交付时列 5 条局限，含"数据集是自蒸馏、不一定提升 OOD 泛化" |
| 4 | **敢标 BLOCKED，不伪造成功** | `D15` T1 明确 BLOCKED；`P34` 判定为运动学硬限制而非硬凑一个"能跑"的假修复；`D18` 失败轨迹原样保留并加警告 README |
| 5 | **能核查上级下发的计划并指出错误** | 抓出 `collision_activation_distance` **方向调反了**（`P32`）；抓出计划假设的 `reach_threshold` 字段**根本不存在**（`P33`）；抓出计划里引用的机器人 ID 在代码中不存在 |
| 6 | **用控制变量法逐条排除，不靠猜** | `P31` 用 **9 次控制变量实验**排除 6 个假设；`P20` 用**四层证据链**否定 3 相机方案 |
| 7 | **区分"证据不足"与"已验证"** | reach gate 各版本都在文档里明写 "pass by absence of evidence"（物体数为 0 时默认通过），而不是伪装成已验证 |

### 5.2 做得不好的部分

| # | 问题 | 证据 | 应如何避免 |
|---|---|---|---|
| 1 | ⭐⭐ **在未确认问题存在的情况下就动手修** | `P30`：三轮碰撞修复 + 后续大量 descend 调试，全部指向一个**从未发生的现象** | 先跑未打补丁的 baseline 并埋点量化（`L01`） |
| 2 | ⭐⭐ **把"以为存在"的 API / 字段当真实存在** | `P25` `P26` `P33` `D17`，以及计划里引用不存在的机器人 ID —— 同一类错误**至少复发 5 次** | 落笔前 grep 到定义处/读取处（`L02`） |
| 3 | **三次"完全相同的结果"没有触发警觉** | `P30` 的三次修复得到**完全相同**的位移值，本应立刻怀疑"变量根本没起作用"，却继续提新假设 | 相同输出 = 变量未生效（`L03`） |
| 4 | **用硬编码输出伪装诊断** | `P26` 的"诊断结论"是一句写死的 print，让日志看起来在正常工作 | 诊断必须来自实际读取的数据 |
| 5 | **假设正确率不高** | `P19` 三条根因假设**两条是错的**；`P30` 的动态碰撞假设完全错误；Patch 02 的两个假设**都不成立** | 承认这是正常的，但要**尽早用最便宜的埋点去筛**，而不是按假设顺序去实现修复 |
| 6 | **方向漂移需要外部纠偏** | `D12`：Stage 3 v1 把"展示光轮工具链能力"的目标做成了纯 NVIDIA 官方示例，AI 自己没意识到 | 定期回读原始目标，而不只看当前子任务是否推进 |
| 7 | **异常处理掩盖信息** | `P37` 只存 `repr(e)` 不打 traceback，白烧两次运行 | 长跑管线一律打完整 traceback |

### 5.3 综合评价

**工程执行力强，问题定位深度足够，诚实度高**（愿意标 BLOCKED、愿意自曝局限、愿意推翻自己），**但"验证前置"的纪律建立得太晚**。本次复现中被浪费掉的时间，绝大部分不来自"问题太难"，而来自两类可避免的行为：**修一个不存在的问题**（`P30`）和**基于臆想的 API 写计划**（`P25` `P26` `P33`）。两者的共同解药都是同一个动作 —— **动手前先用最便宜的手段（grep / 一次埋点 / 一次 baseline）确认前提为真**。

---

## 6. 可复用的经验教训

> 8 条，按复用价值排序。这些教训**不限于本工具链**，适用于一般的仿真/机器人工程调试。

### L01 · 实现"修复 X"之前，先量化"X 是否真的发生"

在写任何修复代码之前，先跑一次**未打补丁的 baseline**，并用最便宜的手段（一次埋点、一行 grep）确认目标现象确实存在、确实在这个 seed/场景下存在。

- **代价对比**：`P30` 里一次接触力埋点（约 3 分钟）本可以省掉三轮碰撞修复 + 九次 descend 调试。
- **附加条款**：**跨运行的观察必须绑定 seed 与场景**。`P30` 反转二的根因就是把 A 场景观察到的位移当成 B 场景的 bug 去修 —— 记忆和文档里记的现象，可能来自另一次运行。
- **推论**：修复反复失败、根因迟迟定位不到时，**停下来质疑"问题本身是否存在"**，而不是在第 N 个假设上继续打补丁。

### L02 · 任何写进配置或计划的键 / 字段 / ID，落笔前必须 grep 到它的定义处或读取处

本次复现中**复发至少 5 次**的最高频错误（`P25` `P26` `P33` `D17` + 不存在的机器人 ID）。

- 配置键要 grep 到**读取它的代码**，不然它就是一行无效注释（`P26`）。
- 计划里要修的字段要 grep 到**它真的存在**，不然整个修复方案是空中楼阁（`P33`）。
- 引用的注册 ID 要 grep 到 `register(...)` 调用处，不然运行期才报 `NameNotFound`（`P23`）。
- **推论**：诊断输出不得来自硬编码字符串 —— 那会让无效配置看起来在正常工作。

### L03 · 校验器 / 修复对不同输入给出**相同**输出，说明它根本没生效

- `P30`：三次不同的碰撞修复得到**完全相同**的位移值 → 变量未生效。
- 可达性门 v2：三个不同场景算出**完全相同**的通过率 → 它压根没读场景。

把"输出是否随输入变化"作为一个**独立的健全性检查**，比检查输出值本身更早发现问题。

### L04 · 环境变量无法中和代码里显式的函数调用 —— 要改配置源头

`P19` 的核心教训：`TORCH_COMPILE_DISABLE=1` 这类开关**关不掉代码里写死的 `torch.compile()` 调用**。同理适用于任何"环境变量 vs 代码内显式调用"的场景。

**推广**：当环境变量不起作用时，去找**驱动那个行为的配置文件或代码行**。对 HF 模型而言，那通常是缓存里的 `config.json`（改 blob，记得备份）。

### L05 · 成功判定只能信环境返回的信号，不能信管线自报的 `success`

- `P29`：管线在"技能都跑完了"时也返回 `success=True`，**8 个 episode 全是失败轨迹却全部标为成功**。这是本次复现最危险的坑 —— 不报错、不崩溃、安静地污染数据集。
- `P35`②：反过来也成立 —— 环境的 `terminated` **必须在 step 返回的瞬间捕获**，因为向量环境包装器会自动 reset，事后查询读到的是下一 episode 的初始状态。

### L06 · 静默失效比报错危险，要主动给它加验证

本次遇到的静默失效清单：

| 静默失效 | 出处 |
|---|---|
| 碰撞球定义被忽略，`total_spheres=0` 且不报错 | `P32` |
| IK 被降级为 stub，调用才 raise | `P07` `P32` |
| 配置里的自定义键无人解析 | `P26` |
| 键名不匹配只打 warning，权重静默随机初始化 | `P18` |
| LLM 静默降级，HTTP 仍 200 | `P27` |
| 重试计数器被重置，上限永不触发 | `P28` |
| 评测进程报错后仍 exit 0 | `P21` |

**通用对策**：给每个"配置生效了吗"的问题写一个**最小验证脚本**（如断言 `total_spheres > 0`、回读响应体的 `model` 字段、assert numpy 版本）。"配置解析通过 ≠ 配置生效"。

### L07 · 长跑调试的三条硬规则

Isaac Sim 类仿真每次启动约 3 分钟起，调试成本高，故：

1. **一次只改一个变量**，否则结果有歧义（`P31` 的 9 次实验之所以有效，就是靠严格单变量）。
2. **异常处理必须打完整 traceback**，不能只存 `repr(e)`（`P37`）。
3. **必须设外部 wall-clock 超时并预留强杀手段**（`P24` 的 58 分钟挂起）；`pkill -f` 要用方括号技巧避免自杀（`P35`④）；`os._exit()` 前要显式 flush（`P35`③）。

### L08 · 依赖某个 `reset()` / 复用某个实例之前，先确认它到底重置了什么

- `P33`：`plan()` **不重置**技能实例的内部步计数器 → 复用实例导致轨迹从未执行。这种隐式状态耦合**从代码表面看不出来**。
- `P31`：规划器的 `reset()` 只清图规划缓冲与随机种子，**不清 per-batch 结果累积器**。

**做法**：依赖某个 reset API 前先 `inspect.getsource()` 看它的实现；复用有状态实例时**宁可显式 reset 或干脆重建**。

---

## 7. 关联的 background 类知识

本章把实践结论回指到原理层 [`background_knowledge.md`](background_knowledge.md) 的对应章节。**两层冲突时，以本层（实践）的事后结论为准。**

> 📌 **另有一层可交叉验证本章结论**：[`code_knowledge.md`](code_knowledge.md) 描述本机复现仓库 `lw_benchhub_tour` 的代码实体，为本章多条 `Pxx` 提供 `[CODE]` 级机制解释与物证 —— 每条 `Lxx` 教训的代码物证见其 **§8.2**，`Qxx` 现象 → 代码机制的 22 行映射见 **§8.3**，本层被代码实测**推翻或收窄**的结论见 **§8.4**（例：`P05` 的 namespace 遮蔽发生在**外层** `__init__.py`，内层与上游逐字节相同）。**该层与本层冲突时，以该层为准**（可逐行核实）。

### 7.1 章节对应关系

| 本文档内容 | 对应原理层章节 | 关系 |
|---|---|---|
| §1.2 版本基线、`P03` `P11` 版本锁 | [§5 安装与依赖](background_knowledge.md)（L952–1073） | 原理层给出 `install.sh` 的官方步骤与两条安装路径的 torch 版本冲突；本层补充**实际必须叠加的版本锁**（numpy 1.26.0、warp-lang 1.8.1） |
| `P05` namespace 包遮蔽 | §5（`-e` 安装对 `CONFIGS_PATH` 是强制的） | 原理层解释了为什么必须 editable 安装；本层给出**外层包遮蔽内层真包**这一实际故障及 shim 修法 |
| `P25` 配置 schema、`P26` 无效键 | [§6 基本使用流程](background_knowledge.md)（L1074–1172）、§4.5（配置与 CSV） | 原理层已指出物体位置由 `layout` + `seed` 决定、任务映射 CSV 仅通过 `rglob` 被发现；本层是该结论的**实战代价证明** |
| `P22` OOD 边界、路径 A/B 对比 | [§4 关键特性](background_knowledge.md)（L773–951）、§4.9（评测 CLI） | 原理层给出评测命令与观测重命名告警；本层补充**同任务 40% / 跨任务 0%** 的定量边界 |
| `P17` episode 长度与录制数量 | §6 的"改行为对照表" | 原理层已记录"找不到 episode 多长的配置项不是你没找到，是它确实被写死在代码里"；本层是该现象的首次遭遇记录 |
| `P18` `P19` 模型加载与推理 | §7 常用 API（L1173–1277） | 原理层描述策略基类的抽象方法与观测合并；本层补充**checkpoint 侧**的两类陷阱（键名前缀、编译开关） |
| `P20` 相机数量、传感器能力 | [§2.6 传感器仿真原理](background_knowledge.md)（L243–511），尤其 §2.6.13 | 原理层已 grep 确认**无自研传感器模型、RGB-only、噪声开关实际无效**；本层的 `P20` 是"想加相机加不了"的实践侧印证 |
| `P29` 成功判定、`P35`② | §4.3 成功判定管线（含半秒去抖逻辑） | 原理层给出成功计数与去抖的代码位置；本层给出**误用该判定的两种翻车方式** |
| `P34` EE / TCP 差异、`D11` `D14` | §6 使用流程、§8.6 设计约束 | 原理层记录了本体与动作空间的绑定关系；本层补充**规划器 URDF 与仿真 USD 之间 link 不一致**这一实践发现 |
| `P24` boot 挂起、`P23` 未注册 task | [§8 已知问题与限制](background_knowledge.md)（L1278–1406），§8.3 缺陷表 | 原理层的缺陷表来自上游 issue 与代码审查；本层补充两条**上游未记录**的实践故障 |

### 7.2 本层推翻或修正原理层的结论

| 项 | 说明 |
|---|---|
| 无 | 本次未发现原理层结论被实践直接推翻的情形。原因是原理层晚于实践编写、且已吸收了部分实践发现。 |

### 7.3 本层发现但原理层尚未收录的空白

以下事实**只在本层有记录**，建议后续回填到原理层第 8 章：

> ✅ 已在原理层 §8 **章头就地标注指回本节**（`background_knowledge.md` L1268 附近），因此读原理层第 8 章的人不会漏掉这 6 条。正式回填（并入其 `[CODE]` 级缺陷清单）需先在上游仓库核实，**尚未进行**。

1. `P11` `P12`：`warp-lang` 与 `setuptools_scm` 两处 ABI/遮蔽冲突（属安装期硬约束）。
2. `P16`：Isaac Sim 与 cuRobo 的初始化**顺序**约束。
3. `P14` `P15`：`set +u` 与 `unset CUDA_VISIBLE_DEVICES` 两条运行期硬约束。
4. `P21`：评测 CLI 不写结果 JSON、成功率是百分数、退出码不可信（属评测层陷阱）。
5. `P24`：特定 layout/task 组合导致 Isaac Sim boot 无限挂起。
6. `P34`：规划器 EE link 与仿真 TCP link 不一致（0.30 m 量级）。

---

## 8. 附录：原始材料索引

### 8.1 材料清单

| 材料 | 说明 | 可用性 |
|---|---|---|
| `sources/lw_benchhub/lw_benchhub_tour.md` | 原始工作日志，约 1.4 万行，中英混排。**注意它是流水日志与已完成文档的混合体，不是纯时序日志** | ⚠️ 仅本机（已 gitignore）。**含明文凭据，不可外传** |
| `sources/lw_benchhub/key_events_summary.md` | 从上述日志提炼的 **34 个关键事件**（`E01`–`E34`），按项目推进顺序排列，已脱敏 | ⚠️ 仅本机 |
| `sources/lw_benchhub/LW-BenchHub/` | 上游仓库 clone，`[CODE]` 级证据来源 | ⚠️ 仅本机，换机需重新 clone |
| `sources/lw_benchhub/background.txt` | 原理层的源料 URL 清单（5 个） | ⚠️ 仅本机 |

### 8.2 原始日志内含的自制文档（本层结论的直接出处）

原始日志中嵌入了复现过程里产出的多份阶段文档，是本层多数结论的一手来源：

| 文档 | 对应内容 |
|---|---|
| `Stage1_Plan.md` / `Complete_Stage_1.md` | §1.3 双轨设定、`P01`–`P09`、`P17`–`P20` |
| `Stage2_Plan.md`（多版）/ Stage 2 v6 收尾文档 | `P25`、`P10`–`P16`、`D06`–`D11` |
| `LW_Benchhub_Interface.md` | `P22`、五层栈接口溯源、观测/动作契约 |
| `Stage3_Plan.md` v1/v2/v3 | `D12` `D13`、`P27` |
| `Stage4_Plan_Detailed.md` | `D17`、`P26`、`P21` 的两条解析教训 |
| `Stage4_Patch_01(_Detailed).md` | `P32` 的方向错误、否决 stub IK |
| `Complete_Stage_4.md` §12 | `P29`–`P31`、`P35`–`P38` |
| `Stage4_Phase2_commit_88f5999_report.md` | `P30` 反转二、`P31` |
| `Stage4_Patch_02.md` 及其调查报告 | `P33` `P34` |

### 8.3 编号对照

| 编号族 | 含义 | 本文档区间 |
|---|---|---|
| `P` | 问题与解决方案 | `P01`–`P38`（§4） |
| `D` | 关键决策 | `D01`–`D18`（§3） |
| `L` | 可复用教训 | `L01`–`L08`（§6） |
| `E` | 关键事件 | `E01`–`E34`（在 `key_events_summary.md`，本层不重复） |
| `Q` | 按现象查的 FAQ | 见 [`troubleshooting.md`](troubleshooting.md) |

**编号只追加、不重排、不复用。** 新增条目请续接现有最大值。

---

## 附：三点核心总结（约 200 字）

1. **最大的时间黑洞不是难题，而是"修一个不存在的问题"。** 三轮碰撞修复加九次调试，最终被一次接触力埋点和一次真正的对照运行双双证明：那个 +0.109 m 的推碗现象从未发生，记忆来自另一个场景。教训是动手前必须用最便宜的手段确认前提为真，且跨运行观察必须绑定 seed 与场景。
2. **第二高频的错误是把"以为存在"的 API、配置字段、注册 ID 当成真实存在**，导致计划被推翻至少 5 次。解药只有一个动作：落笔前 grep 到它的定义处或读取处；诊断输出也不得来自硬编码字符串。
3. **静默失效比报错更该防。** 成功标志会撒谎（8 个失败 episode 全标成功）、碰撞球会被静默忽略、IK 会降级成 stub、LLM 会静默降级而 HTTP 仍返回 200。对策是给每个"配置生效了吗"的问题都写一个最小验证脚本 —— 解析通过不等于生效。

