# lw_benchhub（光轮 LW-BenchHub）· 项目索引

> 更新日期：2026-08-29
> 上游仓库：`github.com/LightwheelAI/LW-BenchHub`
> 本机源料：`sources/lw_benchhub/`（已 gitignore；含 `LW-BenchHub/`、`IsaacLab-Arena/`、`AutoDataGen/` 三个 clone）

---

## 一句话定位

**LW-BenchHub 是 Lightwheel（光轮智能）基于 Isaac Lab + IsaacLab-Arena 的"薄组合层"机器人操作 benchmark**：自身不含仿真器、不含管理器系统、不含 RL 算法，核心机制是把 scene / robot / task / rl 四类 id 通过 Gymnasium 注册表做四路组合。

## 三点摘要（选型时先看这个）

1. **本质是组合层，不是仿真器。** 四路 id 组合 → `IsaacLabArenaEnvironment` → `LwEnvBuilder`；对 isaaclab 打了 **9 处 monkey patch**，其中一处是给上游已删除的 API 做"生命维持"——**升级 isaaclab 会直接破坏本仓库**。
2. **传感器仿真只做配置层组装，无任何自研模型。** 9 种相机全部只输出 RGB；深度 / 激光 / IMU / 触觉 / 6 维力矩 / 关节力矩观测与**传感器噪声模型**均经 grep 确认缺失（`enable_corruption=True` 是空转的假开关）。唯一非平凡耦合：**开启逐环境相机内参随机化会静默关闭 tiled rendering**，并行渲染吞吐大幅下降。
3. **README 宣称的规模需按实测校准。** 任务实为 **272**（非 268）、机器人变体 **28**（非 27）、layout id 可达 **62**（非"100 组合"）、**rsl-rl 只注册不执行**；且 272 个任务中**只有 6 个 RL 配置且全部挂在 `LiftObj` 上**。资产运行时通过 `lightwheel_sdk` 联网拉取，**离线环境不可用**。

## 关键标签

`Isaac Sim` `Isaac Lab` `IsaacLab-Arena` `机器人操作benchmark` `遥操作数据采集` `强化学习训练` `VLA评测` `LeRobot生态` `RoboCasa` `LIBERO` `场景随机化` `解耦式策略API` `sim2real` `云端资产分发`

---

## 文档层次现状

| 层 | 文件 | 行数 | 状态 |
|---|---|---|---|
| 【速查层】 | `quickstart.md` | — | ⏳ 待编写 |
| 【原理层】 | [`background_knowledge.md`](background_knowledge.md) | **1442** | ✅ 已完成（9 章齐备，含 §2.6 传感器仿真 13 小节） |
| 【经验层】 | `ai_knowledge.md` | — | ⏳ 待编写 |
| 【排障层】 | `troubleshooting.md` | — | ⏳ 待编写 |
| 【代码层】 | `code_knowledge.md` | — | ⏳ 待编写（对应本机 `lw_benchhub_tour/`） |

---

## `background_knowledge.md` 章节地图（带行号，用 `Read` 的 `offset`/`limit` 精准读取）

> ⚠️ **行号是 2026-08-29 快照。** 若读到的内容与描述不符，用 `grep -n '^#\{2,4\} ' knowledge/projects/lw_benchhub/background_knowledge.md` 重新定位并顺手更新本表。

### 高频入口（先看这四处）

| 想知道什么 | 直接读 |
|---|---|
| **这东西是什么、值不值得用** | L127–134（§1.6 三个最值得注意的点）+ L779–791（§4.2 规模实测校准） |
| **传感器出的数能不能用** | L481–507（§2.6.13 能力边界一览表，21 行） |
| **全流程怎么串起来的** | L530–568（§3.2 端到端接线图，**排障主索引**） |
| **能力有没有 / 别再搜了** | L1354–1377（§8.7 未找到清单） |

### 逐章行号

| 章节 | 行号 | 内容要点 |
|---|---|---|
| **§1 项目概述** | **25–134** | |
| 1.1 身份与定位 | 27–39 | 光轮智能出品；"薄组合层"定性 |
| 1.2 它解决什么问题 | 40–50 | 统一多本体 / 多场景 / 多任务的评测底座 |
| 1.3 适用场景与不适用场景 | 51–73 | ⭐ **选型必读**：适合什么、明确不适合什么 |
| 1.4 版本坐标与关键落差 ⚠️ | 74–114 | README 徽章 "Isaac Lab 5.0.0" 实指 **Isaac Sim 5.0.0**；Arena pin 在 `c7b70779`（v0.1.0 时期）而上游已 v0.2.x |
| 1.5 生态位置 | 115–126 | 与 RoboCasa / LIBERO / LeRobot / ManiSkill 的关系 |
| 1.6 三个最值得注意的点 | 127–134 | 索引用摘要 |
| **§2 核心原理** | **135–507** | |
| 2.1 一句话机制 | 137–142 | |
| 2.2 四路组合的解析流程 | 143–193 | ⭐ id 拼装公式 `f"{backend.capitalize()}-{cfg_type.capitalize()}-{name}"`；**`.capitalize()` 会把首字母外全部小写 → 大小写敏感陷阱**；`pyproject.toml:39-43` 入口点契约（含 `scences` 拼写错误）；`"-" in cfg.task` 旁路分支 |
| 2.3 全局可变单例 `Context` | 194–204 | 两个已验证缺陷：`device` 声明两次；两个未声明字段被运行时写入 |
| 2.4 `ExecuteMode` 9 种运行语义 | 205–217 | ⚠️ `str_to_execute_mode()` 对未知值**静默回落 `TELEOP`** |
| 2.5 对 isaaclab 的 9 处 monkey patch | 218–238 | ⭐ 完整补丁表；`patch_isaaclab_tasks_mdp` = 上游 API 已删除的生命维持 |
| **2.6 传感器仿真原理（详解）** | **239–507** | ⭐⭐ **本章是 Task 要求的重点补充** |
| ├ 2.6.1 总原则：只是"配置层" | 243–255 | |
| ├ 2.6.2 相机：USD 针孔 + RTX 实时渲染 | 256–282 | 9 个相机内参表；A/B 两组系统性差异（`update_period` 20Hz vs 0；`focus_distance` 400 vs 28） |
| ├ 2.6.3 Tiled rendering 与随机化互斥 | 283–295 | ⚠️ **最高价值的隐藏耦合** |
| ├ 2.6.4 相机默认是关的：两道闸门 | 296–317 | 对应上游 issue #33 |
| ├ 2.6.5 只声明 `data_types=["rgb"]` | 318–333 | 唯一例外：运行时追加 `semantic_segmentation` |
| ├ 2.6.6 本体感知：纯运动学查询 | 334–355 | `FrameTransformer` EE 位姿是**精确无误差**的；关节力矩**未提及** |
| ├ 2.6.7 接触力：PhysX 接触上报 | 356–376 | `history_length=1`；仅 Kuka-Allegro 一例把接触作为观测（±20 N） |
| ├ 2.6.8 深度/激光/IMU/触觉全部缺失 | 377–395 | ⚠️ **含 3 个假阳性辨析**（死路径 docstring、RealSense 真机驱动、`IMUKF` 真机滤波） |
| ├ 2.6.9 噪声模型不存在 + 假开关 | 396–411 | ⚠️ **`enable_corruption` 空转** |
| ├ 2.6.10 节拍三元组 | 412–446 | 6 套配置对照；**RL 20Hz vs 遥操作/回放 50Hz 不匹配** |
| ├ 2.6.11 Arena variations 系统 | 447–469 | 8 类真正被随机化的东西；纹理/材质**未提及** |
| ├ 2.6.12 视觉 sim2real 真实策略 | 470–480 | 数字孪生 RGB 叠加，不是传感器建模 |
| └ 2.6.13 能力边界一览表 | 481–507 | ⭐ **21 行，可直接用于技术选型** |
| **§3 架构与模块** | **508–772** | |
| 3.1 顶层目录 | 510–529 | 五个 Python 包 + shell 包装器 |
| **3.2 端到端接线链（一张图）** | **530–568** | ⭐⭐ **声明为"排障的主索引"，不知道从哪查就先看这张图** |
| 3.3 `utils/` 接线层 | 569–591 | `teleop_device = None` 硬编码（带 TODO）；`CONFIGS_PATH` editable 安装要求 |
| 3.4 `core/` 组合原语 | 592–617 | `LwEnvBuilder` 三个覆盖钩子；`filter_action()` EMA + 速度钳制（回放不一致的机制来源）；14 个观测函数 + 7 个奖励函数 |
| 3.5 `lw_benchhub_tasks/` 任务声明 | 618–659 | 339 个 `gym.register` 分布表；28 个机器人 id；`core/robots/__init__.py` 是空的 |
| 3.6 `lw_benchhub_rl/` 与装饰器绑定 | 660–701 | ⚠️ **`rl_on` 绑定是全局的而非逐类，断言形同虚设**；`CurriculumCfg` 整段注释但仍被赋值 |
| 3.7 `distributed/` 解耦式策略 API | 702–728 | ⚠️ **"zero-copy" debunk**（实为 AF_INET TCP）；真正价值是 `detach()` 复用 Isaac Sim 实例 |
| 3.8 `policy/` 策略插件 | 729–738 | `BasePolicy` 4 方法契约；按模型族切换 conda 环境的必要性 |
| 3.9 `autosim/` 自动示教生成 | 739–748 | 插件进一个**未声明的外部包**；9 条管线 |
| 3.10 `data/` 与 `sim2real/` | 749–754 | 13 个 USD、4 个 WBC ONNX；SO100/SO101 真机驱动 |
| 3.11 Arena 侧三个原语 | 755–772 | Scene/Embodiment/Task + 谓词库 + 两项 alpha 警告 |
| **§4 关键特性** | **773–947** | |
| 4.1 六大组件（README 自述） | 775–778 | |
| **4.2 ⚠️ 规模数字实测校准** | **779–791** | ⭐⭐ **选型/估工作量前必读**：272 vs 268、28 vs 27、62 vs 100、rsl-rl 不可运行 |
| 4.3 任务库的两种设计风格 | 792–812 | ⭐ LIBERO（钉死资产、低方差）vs RoboCasa（类别采样、高方差）对照表 + 两个完整实例 + 成功判定管线（**半秒防抖**） |
| 4.4 `layout` 字符串语法 | 813–828 | 5 种写法；排除清单；**训练与评测光照不同** |
| 4.5 硬编码位姿表 | 829–845 | ⚠️ `layout_task_mapping.csv`（581 行）**文件名全仓库无引用**，靠 `rglob("*.csv")` 发现；LIBERO 字典只覆盖 1 个机器人 |
| 4.6 遥操作与数据采集 | 846–868 | ⭐ `teleop_base.yml` 六段全键清单；`action_delay_*` 延迟注入；**M/N/B/R 键盘检查点**（README 未提） |
| 4.7 RL 训练：三套独立 PPO | 869–890 | ⭐ skrl（唯一可用）/ rsl-rl（不执行）/ ManiSkill（硬编码超参）；skrl 全超参；`discount_factor: 0.8` 的短时程含义 |
| 4.8 解耦式 API 的实际价值 | 891–896 | |
| 4.9 LeRobot 桥与数据集 | 897–915 | ⚠️ **观测键会被重命名**；`episode_length_s` 唯一生效处；21500 episode / 20.5M 帧 |
| 4.10 资产运行时联网拉取 | 916–947 | ⚠️ **离线不可用**；7 个 SDK 调用点；**import 阶段就联网**（报错位置有迷惑性） |
| **§5 安装与依赖** | **948–1060** | |
| 5.1 硬件与驱动底线 | 952–964 | 驱动 ≥ 570.169；显存/磁盘/Python 版本均**未声明** |
| 5.2 两条互相独立的安装路径 | 965–982 | ⚠️ **torch 2.7.0 vs 2.5.1 真实冲突**；无 dockerfile 调用 `install.sh` |
| 5.3 `install.sh` 逐行解读 | 983–1016 | ⭐ **三个必知点**：`flatdict` 补丁、**Arena 子模块用 SSH URL**、`-e` 不能省 |
| 5.4 声明依赖清单 | 1017–1034 | `grpcio`/`protobuf`/`zmq` 声明未用 |
| 5.5 `docker/` 路径 | 1035–1046 | ⚠️ **硬编码代理 `127.0.0.1:7897`**；`third_party/robocasa` 不存在 |
| 5.6 依赖拓扑 | 1047–1060 | **不要自行升级 Arena 子模块** |
| **§6 基本使用流程** | **1061–1149** | |
| 6.1 三行范式 | 1065–1082 | ⭐ **理解这三行就理解全部配置流程**；⚠️ stem 冲突静默覆盖，`.yaml` 压 `.yml` |
| 6.2 入口脚本总览 | 1083–1099 | 9 个根目录 shell 包装器 + `ci_run/` |
| 6.3 遥操作采数 | 1100–1109 | |
| 6.4 RL 训练与回放 | 1110–1119 | `play.py` 的三种 checkpoint 解析 |
| 6.5 解耦式评测 | 1120–1134 | ⚠️ `--overrides` 值经 `eval()`；⚠️ 配置键拼错成 `remote_protocal`，**必须照抄** |
| 6.6 改行为的六个诉求 | 1135–1149 | ⭐ 速查表；**episode 时长基本改不了 YAML** |
| **§7 常用 API / 接口** | **1150–1254** | |
| 7.1 环境组合 `utils/env.py` | 1154–1163 | `parse_env_cfg` / `load_cfg_cls_from_registry` / `create_env` |
| 7.2 `rl_on` 装饰器 | 1164–1173 | ⚠️ 断言不可依赖 |
| **7.3 `BasePolicy` 契约** | **1174–1197** | ⭐ **接自研 VLA 的唯一入口**：4 个抽象方法 + `joint_mapping` 动作重排 + 观测合并 |
| 7.4 远程环境服务两种协议 | 1198–1212 | `--ipc_authkey` 默认 `"lightwheel"`，**生产请改** |
| 7.5 LeRobot / envhub 导出 | 1213–1221 | 观测键重命名表 |
| 7.6 autosim 管线注册 | 1222–1231 | |
| 7.7 MDP 函数库 | 1232–1235 | |
| 7.8 CLI 参数总表 | 1236–1254 | ⭐ 10 个专用脚本的完整参数 |
| **§8 已知问题与限制** | **1255–1377** | |
| 8.1 上游 issue 现状 | 1261–1276 | **5 未关闭 / 6 已关闭**（含 #42 K4 场景崩溃、#39 SDK 版本、#32 SSL） |
| 8.2 README 与代码不符 | 1277–1280 | 指回 §4.2 |
| **8.3 已验证的代码缺陷（15 项）** | **1281–1302** | ⭐⭐ 逐条带位置与影响；⚠️ 标记的会实际影响使用 |
| 8.4 传感器能力硬边界 | 1303–1322 | ⭐ 选型最该看的一节 |
| 8.5 安装部署限制 | 1323–1335 | 8 条，含 3 条"当前就会失败" |
| 8.6 设计层面固有约束 | 1336–1353 | 11 条（不是 bug 但会限制你） |
| **8.7 未找到 / 未提及清单** | **1354–1377** | ⭐⭐ **命中此表就别再搜了** |
| **§9 参考资源** | **1378–1442** | |
| 9.1 官方源 | 1380–1390 | 6 个一手来源 |
| 9.2 必须一并读的上游文档 | 1391–1406 | ⭐ 四级追查顺序（BenchHub→Arena→Isaac Lab→Isaac Sim） |
| 9.3 关联学术与生态项目 | 1407–1420 | 9 个 |
| 9.4 本库内关联文档 | 1421–1430 | |
| 9.5 证据等级说明 | 1431–1442 | 标注约定 + 引用前缀（无前缀 / `Arena:` / `AutoDataGen:`） |

---

## `未提及` / `未找到` 清单（**命中就别再搜了**）

以下方向已 grep 确认**资料中无证据**。需要就去读上游源码 `sources/lw_benchhub/LW-BenchHub/`，读到后回写本库。完整版见 `background_knowledge.md` L1354–1377。

**传感器类**：深度图 · 激光雷达 / ray caster · IMU · 触觉 · 6 维力矩 · 关节力矩(effort)观测 · 传感器噪声模型 · 镜头畸变 · 卷帘快门 · 曝光模型

**渲染类**：路径追踪渲染 · 抗锯齿模式 · 纹理与材质随机化

**代码实体类**：零拷贝 / 共享内存 / CUDA-IPC 传输 · gRPC 使用 · ZMQ 使用 · `autosim` 包源码 · `gr00t` 包源码 · `interact_api.py` 的调用者 · `core/robots/__init__.py` 里的机器人注册 · `third_party/` 下除 Arena 外的子模块 · `configs/rl/rsl_rl/` 目录 · 独立资产下载脚本 · `task.csv`

**环境需求类**：显存需求 · 磁盘空间需求 · Python 版本要求（`pyproject.toml` 无 `requires-python`）

**物理类**：`contact_offset` / `rest_offset` 的显式设置（用 PhysX 默认值）

---

## 三个"别踩"提醒（给未来的自己）

1. **别升级 isaaclab 或 Arena 子模块。** 9 处 monkey patch 按 pin 住的版本写死，其中一处在给上游已删除的 API 做生命维持（§2.5、§5.6）。
2. **别相信 README 的数字，也别相信注释。** 4 处规模宣称与代码不符（§4.2）；`g1.py:997` 的注释写 100Hz 而代码是 200Hz（§8.3 #15）。
3. **别以为 `enable_corruption=True` 就有观测噪声。** 没有任何 `ObsTerm` 传 `noise=`，这个开关是空转的（§2.6.9）。

---

## 本机源料位置（**仅在本机有效**）

| 内容 | 路径 |
|---|---|
| 源料 URL 清单（5 条） | `sources/lw_benchhub/background.txt` |
| 上游主仓库 clone | `sources/lw_benchhub/LW-BenchHub/` ← **`[CODE]` 级证据都在这里核实** |
| Arena 上游 clone | `sources/lw_benchhub/IsaacLab-Arena/` |
| AutoDataGen clone | `sources/lw_benchhub/AutoDataGen/` |
| 复现过程原始日志 | `sources/lw_benchhub/lw_benchhub_tour.md`（约 73 万字符，**混合了流水日志与已完成文档，不是纯时间序**） |
| 本机复现仓库 | `lw_benchhub_tour/`（代码层的描述对象） |

⚠️ `sources/` 与 `lw_benchhub_tour/` 均已 gitignore，换机器需重新 clone。
