# genesis_world 复现经验知识（AI Knowledge）

> **文档性质**：本篇**全文为 `[实践]` 级**——记录的是本机一次完整复现过程中的实测现象、决策与教训，**不是 Genesis World 的官方结论**。凡与原理层 [`background_knowledge.md`](background_knowledge.md) 冲突处，须注意两者的版本落差（见 §1.3）。
> **脱敏声明**：原始材料中的本机绝对路径已统一替换为 `<user_home>`（用户家目录）与 `<path>`（大容量挂载点），主机名替换为 `<host>`。文中不含任何账号、密码、密钥或 token。
> **编号约定**：`Pxx`（问题）/ `Dxx`（决策）/ `Lxx`（教训）**只追加、不重排、不复用**。排障层 [`troubleshooting.md`](troubleshooting.md) 的 `Qxx` 与本篇 §4 的 `Pxx` **一一对应**。
> **事件索引**：`Exx` 指向 `sources/genesis_world/key_events_summary.md`（仅本机存在，已 gitignore）中的编号事件。

---

## 1. 复现目标与背景

### 1.1 项目目标

在**单卡、无显示器的云服务器**上，用 Genesis World 走通四条互相独立的具身智能仿真路线，每条都要求产出**可客观验证**的交付物（MP4 + JSON 指标 + 自动化验证脚本 exit 0）：

| 路线 | 阶段 | 目标 | 结果 |
|---|---|---|---|
| VLA 闭环操作（Franka + OpenVLA） | Stage 1 / Stage 2 | 视觉语言模型驱动机械臂抓取方块，并在 8 个扰动场景下批量评估 | ❌ **Stage 2 0/8**，从未成功抓取 |
| VLA 换本体换模型（Unitree G1 + PI0 / Pi0.5） | Patch 01 / Patch 02 | 换人形本体与流匹配策略以消除本体不匹配 | ⚠️ **仅有计划，全文无执行记录** |
| 强化学习（Go2 四足 PPO） | Stage 3 | 2048 并行环境训练四足行走，录制三阶段对比视频 | ✅ **完全成功** |
| 刚柔 / 刚流耦合 | Stage 4 | 布料、体积柔性体、流体与刚体机械臂的交互演示 | ✅ 三 demo 交付（IPC 路径不可达，降级 PBD） |

**贯穿全程的一条硬约束**：执行方（AI Agent）**没有读图能力**。因此"机器人是否真的动了/抓到了/走起来了"不能靠看视频判断，必须转化为**可机器判定的数值证据**——这条约束反过来塑造了本项目最有价值的一批方法论（见 `L03`）。

### 1.2 环境条件

| 项 | 值 | 说明 |
|---|---|---|
| GPU | NVIDIA A800-SXM4-40GB × 1 | 单卡；40GB 显存是 2048 并行环境与 8B VLA 模型能共存的前提 |
| 驱动 | 580.159.03 | |
| CUDA Toolkit | 11.8 | `CUDA_HOME=/usr/local/cuda-11.8`；与 PyTorch 的 cu128 wheel 并存（见 `P01`） |
| OS | Ubuntu 22.04，**headless 云服务器** | 无 X server，所有渲染走 `show_viewer=False` + 离屏相机 |
| Python | 3.12.13 | conda 环境（本文记为 `<env>`）；此版本与 OpenPI 要求的 3.11 冲突（见 `P37`） |
| PyTorch | 2.10.0+cu128 | Genesis **不把 PyTorch 列入依赖**，需自行安装并自行保证与 CUDA 匹配 |
| genesis-world | **1.2.2** | ⚠️ 与原理层描述的 1.3.3 有落差，见 §1.3 |
| gs-nyx | 0.1.3 | Nyx 渲染器为**独立 out-of-tree 包** |
| rsl-rl-lib | 5.0.1 | Stage 3 的 PPO 实现；其 0-based 迭代编号是本阶段最致命的坑（`P19`） |
| transformers | 4.57.6 → 降级至 4.53.2 | Stage 1 V3 的微调模型硬性要求 `>=4.40,<4.50`（`P12`） |

### 1.3 ⚠️ 版本落差提示（阅读本篇前必读）

**本篇记录的是 genesis-world 1.2.2 时期的实践，原理层 [`background_knowledge.md`](background_knowledge.md) 描述的是 1.3.3。**两者之间存在 API 与能力差异，因此：

- **本篇给出的具体 API 写法与命令不可直接套用到 1.3.x**，需先核对上游 CHANGELOG。
- 反过来，**本篇里的若干"不存在/不可达"结论可能已在新版本被修复**（例如 IPC 耦合器的可安装性、`examples/` 是否随包分发）。凡涉及"某功能不存在"的判断，在新版本上部署前请重新验证。
- 但**方法论层面的教训（§6）与工程纪律是跨版本有效的**——它们描述的是如何工作，而非某个 API 长什么样。

---

## 2. 计划与执行流程

### 2.1 阶段时间线

材料中带明确日期标记的节点有限，以下时间线**以阶段推进顺序为主、绝对日期为辅**：

| 阶段 | 时间 | 计划要点 | 实际发生了什么 | 计划变更 |
|---|---|---|---|---|
| **A 立项 + Stage 1 计划** | 初期 | OpenVLA-7B + Franka，复用现有 conda 环境，bfloat16 加载，headless 用 OpenCV 写 MP4；产出九步闭环链路与 8 类故障预判表 | 计划书里的 Genesis API **几乎全是"想当然"写法**（`E03`），执行阶段被逐条证伪 | — |
| **B Stage 1 执行** | 初期 | 按计划实现闭环 | 连撞五类踩坑（`P02`–`P08`）；`pos_scale` 五点扫描后把方块搬到模型收敛点，拿到 "PARTIAL SUCCESS" | **重大变更**：从"让模型适应场景"改为"**让场景迁就模型**"（`D07`） |
| **C Stage 2 v1.0 + 根因分析** | 2026-07-12 | 3 场景扰动评估 | 复盘认定 Stage 1 的 SUCCESS 是**假阳性**（`P09`）；定位四条根因；六次尝试中前三次改控制器全败、第四次改场景才"成功" | 输出短/中/长三级方案，直接催生后续三次自救 |
| **D Patch 01 / 02** | 2026-07-12 / 07-17 | 换本体（G1）换模型（PI0 → Pi0.5 + WebSocket 服务） | 调研极其详尽（含 10 条跨项目迁移检查清单），但**tour.md 全文没有任何执行记录** | ⚠️ 计划完成即搁置 |
| **E Stage 1 V3** | 2026-07-19 | 换用 Franka 微调模型 `openvla-mcx-card`，宣称"无 embodiment mismatch" | 仍不收敛（18–36cm），根因只是**从 embodiment mismatch 换成了 sim-to-sim gap**（`P13`） | 成功判定从"抬起 5cm"下调为"触碰 <3.5cm"（`D08`） |
| **F 双相机增补** | 2026-07-25 | 加宽视角人类视图 | 新增 render-only `wide_cam`，**VLA 相机一行不动**；用像素统计客观验证 | — |
| **G Stage 2 v2.0** | — | 8 场景 × 1000 步批量评估 + 41 项自动化验证门 | 41/41 验证 PASS，但业务结果 **0/8 全失败**；两个反直觉发现（`P14`） | — |
| **H Stage 3** | — | 放弃 VLA，转 Go2 四足 PPO；进程隔离架构 | 环境探针推翻计划书六项假设；五处 API 缺陷全部被 smoke test 提前捕获；**完全成功** | **战略转向**：从操作任务转为运动控制任务（`D14`） |
| **I Stage 4** | — | IPC 耦合器 + FEM 布料做"零穿透"演示 | IPC 本机不可达且安装会摧毁主环境（`P26`）→ 降级 PBD；13 次探针后判定抓取提拉物理不可达 → 转向形变演示 | **两次降级**：IPC→PBD（`D17`）、抓取→形变（`D18`） |
| **J 仓库交付** | 收尾 | — | README 固化 "Critical API Gotchas" 清单与三种运行方式 | — |

### 2.2 计划变更点小结

全程共有 **5 次实质性方向变更**，其中 4 次是"目标向能力妥协"，只有 1 次（Stage 3）是主动换赛道：

1. **场景迁就模型**（`D07`）——把方块搬到模型的固定收敛点，本质上是承认模型不受控。
2. **成功判定放宽**（`D08`）——从"抬起 5cm"到"触碰 <3.5cm"。⚠️ 根因分析明确指出，Stage 1 六次尝试中通过率的提升**完全来自判定口径变更，而非能力提升**（`E14`）。
3. **换微调模型**（`D12`）——寄望换模型解决根因，实测只是换了根因的名字。
4. **放弃 VLA 转 RL**（`D14`）——唯一成功的路线。
5. **Stage 4 双降级**（`D17`/`D18`）——IPC→PBD，抓取→形变。

> **这条脉络本身就是最重要的经验**：当连续三次"换个组件就能解决"的假设都失败后，真正奏效的是**换问题**（从需要预训练策略泛化的操作任务，换成可以在仿真内自监督训练的运动控制任务）。详见 `L07`。

---

## 3. 关键决策与原因

> 决策来源分三类：**[AI]** = Agent 主动提出并被采纳；**[人]** = 用户判断或批准；**[外]** = 来自外部资料（上游文档、跨项目调研）。

| ID | 决策 | 原因 | 来源 | 事后评价 |
|---|---|---|---|---|
| `D01` | 复用已有 conda 环境而非新建 | 依赖（PyTorch/CUDA/transformers）已装好且验证可用，新建环境的收益不抵风险 | [AI] | ✅ 正确。后续 Stage 3 明确"**禁止执行任何 `pip install`**"，同一纪律 |
| `D02` | OpenVLA-7B 用 **bfloat16** 加载（~14GB） | fp32 需 ~28GB，与仿真渲染争抢 40GB 显存 | [AI] | ✅ 正确，显存全程无压力 |
| `D03` | headless：`show_viewer=False` + 离屏相机 + OpenCV 写 MP4 | 云服务器无 X server | [AI] | ✅ 正确，但埋下 `P24`（mp4v/mpeg4 fourcc）的伏笔 |
| `D04` | **VLA 模型必须先于 `gs.init()` 加载** | 实测顺序颠倒会引发 CUDA 上下文冲突（`P06`） | [AI]→实测 | ✅ 关键契约，后续所有脚本沿用 |
| `D05` | 用独立的 `GripperController` 四态状态机接管夹爪，不信任 VLA 的夹爪输出 | VLA 夹爪维度**恒为 0.0**，且抬升 PD 增益（kp=2000 / kv=200）后才夹得住 | [AI]→实测 | ⚠️ 治标。它把"模型不会用夹爪"这个根因掩盖了，直接导致 `P09` 假阳性 |
| `D06` | `pos_scale` 用五点扫描确定为 **0.08**（相对基准 0.05，等效放大 1.6×） | 网格搜索而非猜测 | [AI] | ✅ 方法正确，但调的是无关变量（见 `L02`） |
| `D07` | **把方块搬到模型的固定收敛点** | 模型无论目标在哪都收敛到 ~(0.575, −0.081, 0.244)，与其修控制器不如迁就 | [AI] | ⚠️ 工程上有效、认识上有害——它让 Stage 1 看起来成功了 |
| `D08` | 成功判定从"抬起 5cm"下调为"夹爪触碰方块 <3.5cm" | 抬起从未达成 | [AI] | ❌ **危险决策**。根因分析自己指出：六次尝试的通过率提升**完全来自口径变更** |
| `D09` | 输出短期/中期/长期三级方案 | 承认短期方案是权宜之计，把根本解法（微调 / 换模型 / 换框架）显式写出 | [AI] | ✅ 优秀。诚实标注了自己方案的层级 |
| `D10` | Patch 01：换 Unitree G1 + PI0（3.5B 流匹配 + 动作分块） | 同时消除 embodiment mismatch（G1 左臂同为 7-DOF）与单步预测抖动；**关节空间 8D 控制可绕开 IK 振荡**；VRAM 降到 8–12GB | [AI] | ⚠️ 推理链条完整，但**从未执行**，价值仅停留在分析 |
| `D11` | Patch 02：调研 genie_sim_v3，改用 **Pi0.5 + WebSocket 策略服务器 + action chunk FIFO 消费** | 该项目实测 90% 成功率，是已验证的参照系；FIFO 消费能把 300–500ms 推理开销摊薄到 1.67s | [外] | ⚠️ 调研质量极高（`E17`），同样**从未执行**；且唯一被标 ⚠️ 未验证的 Docker 恰恰是方案命脉 |
| `D12` | Stage 1 V3 换 `tshiamor/openvla-mcx-card`（Isaac Sim 中用 Franka 数据微调） | 模型卡片宣称"核心优势：无 Embodiment Mismatch" | [外] | ❌ 无效。只是把根因换成 sim-to-sim gap（`P13`）；还附赠 transformers 跨大版本降级（`P12`） |
| `D13` | 双相机：**新增** render-only `wide_cam`，**VLA 相机一行不动** | 已实测相机哪怕只做 Y 方向平移，模型收敛点就从 27cm 漂到 35cm | [AI]→实测 | ✅ **本项目最漂亮的决策之一**。改需求而不改敏感输入 |
| `D14` | 放弃 VLA，转 Go2 四足 PPO；**进程隔离**架构（orchestrator + subprocess） | 三次自救全败；RL 可在仿真内自监督训练，不依赖外部策略的泛化能力。进程隔离规避训练与渲染的 CUDA 上下文冲突 | [AI] | ✅ 唯一完全成功的路线 |
| `D15` | 从 GitHub v1.2.2 tag **vendoring** 官方 `go2_env.py` / `go2_train.py` | pip 包内没有 `examples/`（`P16`）；且 URDF 路径**必须保持相对**，改绝对反而失败 | [AI]→实测 | ✅ 正确，同时保留了官方实现的可追溯性 |
| `D16` | 直接用 **2048 并行环境**，不做保守回退 | 先跑 256/512/1024/2048 各 2 iter 的显存梯度测试，四档全 OK 且吞吐近线性（18,891 → 151,839 steps/sec） | [AI] | ✅ 用 2 分钟的加压测试换掉一个大风险假设 |
| `D17` | Stage 4 从 IPC 耦合器降级到 **PBD** | `pip install pyuipc` 会拉入 numpy 2.5.1 → numba ImportError → `import genesis` 失败，**整个主环境报废**（`P26`）；且 `IPCCouplerOptions` 的三个计划字段全不存在 | [AI]→实测 | ✅ 及时止损；PBD 是本机唯一 smoke-test 通过的刚柔耦合路径 |
| `D18` | Stage 4 目标从"抓取提拉布料 ≥10cm"改为"**布料形变演示**" | 13 次探针证明 panda_bullet 夹爪闭合是"前+侧+上扫动"而非平行对夹，该 URDF + IK 约束下**物理不可达** | [AI]→**[人] 批准** | ✅ 正确。且这次是**先证明不可达再改目标**，与 `D08` 的"先改口径"性质完全不同 |
| `D19` | **一进程一场景**（或子进程隔离） | 同一 quat 在单场景进程收敛、在多场景进程发散，IK/PD 状态会跨场景污染（`P31`） | [AI]→实测 | ✅ 与 `D14` 的进程隔离同源 |
| `D20` | 宣称口径主动降级：不说"数学零穿透"，只说"所有帧实测最小间距 ≥ −thickness，**未检测到穿透事件**" | 用 `torch.cdist` 采样 36 个指尖顶点，分辨率有限，不足以支撑 IPC 级别的强宣称 | [AI] | ✅ 罕见的**对自己结论强度主动降级**，值得作为范例 |

### 3.1 决策质量的一个观察

把 `D08`（放宽判定口径）与 `D18`（改变演示目标）并列看，能提炼出一条判据：

- `D08` 是**先改口径、后解释**——"抬起做不到，那就算触碰"，此时并没有证据表明抬起不可达，只是还没做到。结果是掩盖了失败。
- `D18` 是**先证明不可达、再经用户批准改目标**——13 次探针 + 明确的物理机制解释（夹爪运动学）。结果是止损。

> **判据**：降低目标之前，必须先把"当前目标不可达"证明到机制层面，并且这个降级要显式征得决策者同意。否则降级会变成对失败的隐藏。

---

## 4. 遇到的问题与解决方案（核心章）

> 本章共 **37 条**（`P01`–`P37`），按发生阶段分组。每条含**现象 / 排查 / 无效尝试 / 最终方案**。
> 按**报错现象**反查请用排障层 [`troubleshooting.md`](troubleshooting.md)，其 `Qxx` 与本章 `Pxx` 一一对应。
> 全部为 genesis-world **1.2.2** 上的实测，新版本请重新验证。

### 4.1 环境与安装（P01, P12, P26, P37）

| ID | 现象 | 排查过程 | ❌ 无效尝试 | ✅ 最终方案 |
|---|---|---|---|---|
| `P01` | 编译期报 `error: [Errno 2] No such file or directory: ':/usr/local/cuda-11.8/bin/nvcc'` —— 路径**开头多一个冒号** | 路径本身存在，问题在字符串。定位到环境脚本里用 `CUDA_HOME=$CUDA_HOME:/usr/local/cuda-11.8` 形式拼接，而 `CUDA_HOME` 原本为空，于是拼出 `:/usr/...` | 检查 CUDA 安装完整性、重装 toolkit（方向完全错误——文件是在的） | `CUDA_HOME` 是**单值变量不是 PATH 列表**，直接赋值 `CUDA_HOME=/usr/local/cuda-11.8`，不要用冒号拼接 |
| `P12` | Stage 1 V3 的微调模型硬性要求 `transformers>=4.40,<4.50`，环境是 **4.57.6**，属跨大版本降级 | 读模型卡片的依赖声明 | 直接在 4.57.6 上加载（行为不可预期） | 降级到 **4.53.2**——实测只报告警告、不影响推理。⚠️ 注意这是"擦边"方案，严格满足约束应降到 <4.50 |
| `P26` | `import uipc` → `ModuleNotFoundError`；而 **`pip install pyuipc` 会拉入 numpy 2.5.1，触发 `ImportError: Numba needs NumPy 2.4 or less`，进而使 `import genesis` 失败——Stage 1/2/3 全部报废** | 在**装之前**先做依赖传递性评估，发现 pyuipc 与 genesis 的 numpy 约束不相容 | 用 `pip install --target` 隔离安装：装是装上了，但运行时 numpy 冲突仍使 IPC 的 `scene.build()` 失败 | **放弃 IPC 路径，降级到 PBD**（`D17`）。教训见 `L06` |
| `P37` | OpenPI 要求 **Python 3.11 + uv**，现有环境是 3.12.13 | 读 OpenPI 安装文档 | — | 计划中的对策是另建 3.11 环境或用 uv 隔离，并额外把 `transformers_replace/*` 补丁复制进 site-packages。⚠️ **该计划从未执行，方案未经验证** |

### 4.2 Genesis API 陷阱（P02–P05, P15, P16, P18）

这一组是**计划书 API 写法被证伪**的集中体现——它们全部来自"看起来应该这么写"，而非查证。

| ID | 现象 | 排查过程 | ❌ 无效尝试 | ✅ 最终方案 |
|---|---|---|---|---|
| `P02` | `AttributeError: module 'genesis.options.morphs' has no attribute 'Franka'` | 计划书写 `gs.morphs.Franka()`，实际不存在这个便捷类 | 换大小写、查 `gs.morphs` 其它别名 | 用 URDF 加载：`gs.morphs.URDF(file=os.path.join(os.path.dirname(gs.__file__), "assets", "urdf", "panda_bullet", "panda.urdf"))`。**注意 Franka 的 `n_dofs=15`**（7 臂 + 2 指 + 其余） |
| `P03` | `Validation error for <gs.morphs.Box>: Unrecognized attribute 'surface'` | `surface` 被写进了 morph 的构造参数 | 尝试 `gs.morphs.Box(surface=...)` 的各种变体 | `surface` 属于 **`scene.add_entity()`** 而不是 morph：`scene.add_entity(morph=gs.morphs.Box(...), surface=gs.surfaces.Plastic(color=(0,0,1)))` |
| `P04` | `Link not found for name: hand.` | 计划书假设末端执行器链接叫 `"hand"` | 试 `"panda_hand"`、`"ee_link"` 等常见命名 | panda_bullet URDF 里末端是 **`"panda_link7"`**。⚠️ 通用做法是**运行时枚举链接名**而不是硬编码猜测 |
| `P05` | `Invalid input shape: (14,). Dimension 0 consistent with required size 7` | IK 求解返回值被 `[:-2]` 切片（意图是"去掉两个夹爪自由度"） | 各种切片写法 | **IK 返回的是完整 qpos `(16,)`**，不是臂部 7 维。必须用显式索引 `motors_dof = np.arange(7)`，`qpos[motors_dof]`。`[:-2]` 得到 `(14,)` 是错的 |
| `P15` | 批量评估中第二次调用 `gs.init(backend=gs.gpu)` 直接 Segfault 或抛 Taichi error；且找不到 `scene.destroy()` | Taichi 的 CUDA 初始化是**进程级**的 | 在循环内反复 `gs.init()`；找场景销毁 API（**不存在**） | ① `gs.init()` 提到场景循环外，全进程只调一次；② 每个场景的构建与运行封进独立函数，靠作用域退出 + GC 回收；③ 更彻底的做法是 Stage 3 采用的**进程隔离**——每个 subprocess 各自 `gs.init()` 拿独立 CUDA 上下文（`D19`） |
| `P16` | `from examples.locomotion.go2_env import Go2Env` → `ModuleNotFoundError` | pip 安装的 `genesis-world` 包内**没有 `examples/` 目录**，它只存在于 GitHub 仓库 | 找 site-packages 下的各种子路径 | 从 GitHub **v1.2.2 tag** 把 `go2_env.py`（304 行）/ `go2_train.py`（178 行）vendoring 进本仓库（`D15`）。⚠️ 其中的 URDF 路径**必须保持相对**，改成绝对路径反而失败 |
| `P18` | `cam.render(rgb=True)` 的返回值直接当 ndarray 用 → 后续 numpy 操作报类型错 | 打印返回值 | 假设它返回单个数组 | **返回 4 元组 `(rgb, depth, seg, normal)`**，须解包取第 0 项 |

### 4.3 生命周期与调用顺序（P06, P17）

| ID | 现象 | 排查过程 | ❌ 无效尝试 | ✅ 最终方案 |
|---|---|---|---|---|
| `P06` | 【CRITICAL】在 `gs.init()` 之后加载 OpenVLA，出现 CUDA 上下文冲突，典型报错 `RuntimeError: can't convert cuda:0 device type tensor to numpy` | 交换加载顺序做 A/B 对比 | 加 `.cpu()`、`.detach()` 之类的局部补丁（治标，问题会在别处复现） | **VLA 模型必须先于 `gs.init()` 完成加载**（`D04`）。这是一条硬顺序契约，所有脚本沿用 |
| `P17` | `genesis.GenesisException: Scene is already built.` —— 在 `Go2Env` 构造后调用 `add_camera` | 读 `go2_env.py` 发现 **`Go2Env.__init__` 内部已经调了 `scene.build()`** | 在 env 构造后补 `add_camera`（必然失败） | `scene.add_camera` 带 `@gs.assert_unbuilt` 装饰器，**相机必须在 build 之前添加**。解法是给 `Go2Env` 加 `camera_cfg=` 构造参数，把相机添加挪进 build 之前。<br>⚠️ 与之互补的一条：**PD 增益 `set_dofs_kp/kv` 与 `get_link()` 必须排在 build 之后** |

### 4.4 VLA 闭环的根因链（P07–P11, P13, P14）

> 这一组不是孤立 bug，而是**一条根因链**：表层是"抓不住"，深层是本体不匹配，再深层是仿真器间的 sim-to-sim gap。

| ID | 现象 | 排查过程 | ❌ 无效尝试 | ✅ 最终方案 / 结论 |
|---|---|---|---|---|
| `P07` | 模型卡片描述的 API 与实际不符；`predict_action` 的返回类型在不同调用下漂移 | 直接打印返回对象的 type 与 shape | 照模型卡片写 | 以实测类型为准做防御性解包。⚠️ 一般教训：**模型卡片是文档不是契约** |
| `P08` | 夹爪合上了却夹不住方块，物体从指间滑出 | 检查接触力与关节实际位置 | 调闭合行程、调 friction | Franka 夹爪默认 PD 增益太低，撑不住。设 **kp=2000 / kv=200**（build 之后设置），并用 `GripperController` 四态状态机管理开合时序（`D05`） |
| `P09` | Stage 1 报出 "PARTIAL SUCCESS"，复盘认定是**假阳性** | 逐条核对成功判定：方块本就放在模型收敛点、判定口径已放宽到"触碰"、夹爪由外部状态机接管 | —— | 结论：所谓成功是**三重外部辅助叠加**的结果，模型本身没有完成任务。**六次尝试中通过率的提升完全来自判定口径变更**（`E14`） |
| `P10` | OpenVLA-7B 无论目标方块放在哪，末端都收敛到 **~(0.575, −0.081, 0.244)**（相对目标偏置 X +7.6cm / Y −8.1cm / Z +2.4cm）；夹爪维度**恒为 0.0** | 五点扫描 `pos_scale`、变更目标位置做对照 | 改 `pos_scale`、改控制器增益、改动作缩放——**三次改控制器全部失败** | 根因是 **embodiment mismatch**：`openvla/openvla-7b` 是在 WidowX 数据上预训练的，与 Franka Panda 的运动学不匹配。短期只能迁就（`D07`），根本解法是微调或换模型 |
| `P11` | IK 目标用 `panda_link7`，但实际夹持发生在指尖，两者有偏移 | 测量 link7 与指尖的相对位置 | 用固定偏移量补偿 | 偏移是**姿态相关的**（实测某构型下 ΔX +12.8cm / ΔY +10.5cm），常数补偿无效。中期方案是把 IK 目标改成手指链接（需处理叶子链接的数值不稳定） |
| `P13` | 换用 Franka 微调模型 `openvla-mcx-card` 后，末端仍距方块 **18–36cm 且不向方块收敛**；夹爪仍恒 0.0；模型倾向从**上方**接近，手指落在方块顶部而非两侧 | 与 Stage 1 结果做对照 | 换模型本身就是那次尝试 | 根因从 embodiment mismatch 变成 **sim-to-sim gap**——模型在 Isaac Sim 训练、在 Genesis 推理，物理引擎 / 渲染器 / 相机模型全不同。<br>❌ **"从上方接近"一条文档明写"目前无根本解决方案，需要重新训练模型或使用混合控制策略"** |
| `P14` | 8 场景批量评估 **0/8 全失败**，但出现两个反直觉现象：相机抬高 +0.35m 的 scene 7 反而**更接近**方块（14.89cm vs 无扰动基线 34.6–35.6cm）；目标移开收敛点的 scene 4 **发散到 267.36cm** | 对照 8 组扰动的最终距离 | —— | 结论：**模型对场景内容（干扰物 / 杂乱 / 强光）鲁棒，但对相机外参高度敏感**。⚠️ 收敛点的漂移方向**不可预测**，因此 scene 7 的"更近"不能算作改善，也不能作为调参方向 |

### 4.5 Stage 3 训练链路（P19–P23）

> 这五条的共同点：**全部由小规模 smoke test 在正式运行之前捕获**，没有一条是在多小时训练跑完后才暴露的。这是本项目方法论上最大的胜利（`L01`）。

| ID | 现象 | 排查过程 | ❌ 无效尝试 | ✅ 最终方案 |
|---|---|---|---|---|
| `P19` | 【最致命】`runner.learn(50)` 之后期望的 `model_50.pt` 不存在，实际存出的是 **`model_49.pt`** | 读 `rsl_rl/runners/on_policy_runner.py` L77–161，确认 rsl-rl-lib 5.0.1 用 **0-based 迭代索引** | 改 `learn()` 的参数值（治标且易错） | 训练结束后显式对齐编号再存：`runner.current_learning_iteration = args.max_iterations; runner.save(...)`。<br>⚠️ 若不修，会等到 orchestrator 阶段 3 才 `FileNotFoundError`，**前面所有训练时间全部浪费** |
| `P20` | `OnPolicyRunner.load()` 的返回值被当作模型字典使用，实际拿到 `None` | 打印返回值 | 假设它返回 state_dict | `load()` 返回的是 `loaded_dict["infos"]`（此处为 `None`）。要读迭代数须改用 `torch.load(ckpt, weights_only=False)` 再取 `iter` |
| `P21` | 推理时 `policy(obs["policy"])` 报形状错 | 读 `rsl_rl/models/mlp_model.py` | 各种手工 reshape | 策略要接收**完整 TensorDict**，传 `obs["policy"]` 等于**索引了两遍**。直接 `policy(obs)`。<br>⚠️ 相关：`Go2Env.step()` 返回 **4 元组**（不是 gym 惯例的 5 元组），`reset()` 返回键为 `"policy"` 的 TensorDict |
| `P22` | resume 训练时，之前存好的 `model_50.pt` 消失 | 读 vendored `go2_train.py` | —— | 官方脚本**无条件执行 `shutil.rmtree(log_dir)`**。修改为：仅在非 `--resume` 时清空。同时把 `save_interval` 从 100 改到 50，否则中间 checkpoint 拿不到 |
| `P23` | 后台 bash 任务**秒退、无输出、无进程残留** | 手工前台跑同一命令正常 | 反复检查脚本本身的语法 | **后台 bash 不继承 conda 环境**（非交互 shell 不 source profile）。解法是写一个显式 source 一切的 `run_in_env.sh` wrapper（source conda profile → activate env → source 环境脚本 → exec 目标命令） |

### 4.6 无图像环境下的验证（P24, P25）

| ID | 现象 | 排查过程 | ❌ 无效尝试 | ✅ 最终方案 |
|---|---|---|---|---|
| `P24` | 三个正常的 MP4 全部被验证脚本判 FAIL | 手工跑 ffprobe 看实际字段 | 怀疑视频真的损坏 | OpenCV 用 `mp4v` fourcc 写出的文件，**ffprobe 报告的 `codec_name` 是 `mpeg4`**。编码白名单必须同时包含两者。⚠️ 该坑在 Stage 3 与 Stage 4 各踩了一次 |
| `P25` | Stage 2 的像素验证中 scene 7/8 误报失败（"方块不可见"） | 提取被判失败的关键帧做像素统计 | 怀疑相机没拍到方块、调相机参数 | **不是相机问题**：用的是 step-500 的中段关键帧，而此时**已经发散的机械臂在近距离 VLA 视图里正好挡住了方块**。改用 **step-0** 关键帧作比较基准即修复 |

### 4.7 Stage 4 刚柔 / 刚流耦合（P27–P34）

| ID | 现象 | 排查过程 | ❌ 无效尝试 | ✅ 最终方案 |
|---|---|---|---|---|
| `P27` | 计划书写的 `IPCCouplerOptions(dt=..., ipc_constraint_strength=..., contact_friction_mu=...)` —— **三个字段全部不存在**；计划宣称的"重要优化" `set_ipc_link_filter` 在全源码 **grep 零命中** | 直接读 genesis 1.2.2 源码而不是读计划书 | 按计划书写法构造（必然报错） | 与 `P26` 合并处理：整条 IPC 路径放弃。⚠️ 一般教训：**计划书里的 API 名必须先 grep 到定义处再写进代码** |
| `P28` | `franka.get_contacts(with_entity=cloth)` → `AttributeError: 'PBD2DEntity' object has no attribute 'geom_start'` | 读源码确认 `get_contacts` 属于 **rigid-rigid 接触管线**，而 PBD 布料内部是粒子系统，根本不参与该管线 | 换参数形式反复调用 `get_contacts` | 改为几何距离法：取左右指尖碰撞网格顶点（各 18 个，共 `(36,3)`）与布料粒子做 `torch.cdist(...).min()`，全程在 GPU 上算。<br>⚠️ 顶点采样稀疏是已知局限，因此宣称口径主动降级（`D20`） |
| `P29` | 布料按计划放在 `(0.5, 0, 0.15)` 后，机械臂还没碰到就"掉桌"了 | 打印布料粒子 `zmin` | 调 PBD 参数 | PBD 柔性体**无支撑就立即受重力下落**（`zmin` 掉到 0.005）。加一个 `fixed=True` 的抬高桌面 Box（桌顶 Z=0.40），布料贴其上（`CLOTH_POS=(0.5,0,0.41)`） |
| `P30` | 用固定 `quat=[1,0,0,0]` 对桌面级目标求 IK，末端**飞到 `[5.67, −250, −140]`**（几十米外） | 与 Stage 1 的可用实现做对照 | 换初始 qpos、加迭代次数 | 关键发现：Stage 1 之所以能工作，是因为它**每一步重新读取 `ee.get_quat()`** 做增量移动。改用 evolving quat 后 XY 才能准确到位 |
| `P31` | **同一个 quat，在单场景进程里收敛，在多场景循环进程里发散** | 对照两种运行方式 | 反复调 IK 参数（在多场景进程里怎么调都不对） | IK / PD 状态会**跨场景污染**。结论：**一进程一场景 / 子进程隔离**（`D19`） |
| `P32` | 夹爪闭合后布料留在原地，`lift = −0.50cm`；改用轻布料 + 慢闭合更糟——布料被直接**压下桌面** | 打印闭合前后的指尖世界坐标：从 `[0.479, 0.016, 0.392]` 跳到 `[0.72, −0.145, 0.505]` | 调 friction、调 rho、调 dt、调闭合速度、调 EEF 偏移——**13 次探针全部无效** | 根因：**panda_bullet 的夹爪闭合是"向前 + 向侧 + 向上扫动"，不是平行对夹**。判定"从上方捏取平铺布料并提拉 ≥10cm"在该 URDF + IK 约束下**物理不可达**，经用户批准转向形变演示（`D18`） |
| `P33` | 想用物理上更正确的 `FEM.Elastic` 做三维体积柔性体（海绵），但手指**直接穿过** | 读 `genesis/engine/solvers/fem_solver.py`（L975 附近），确认**只有 `isinstance(self.sim._coupler, IPCCoupler)` 时 FEM 才由 IPC 处理接触**，否则 FEM 只积分内部力、完全不做刚-柔接触解算 | 调 FEM 材料参数（与接触无关） | IPC 既不可达（`P26`），**`PBD.Elastic` 就是本机唯一的体积柔性体路径**（`gs.morphs.Box` 经 TetGen 四面体化得约 806 粒子） |
| `P34` | SPH 流体在 `dt=2e-3` 下"炸开" | 逐档缩小 dt | 调粒子半径、调粘度 | **SPH 稳定步长 `dt ≤ 4e-4`**。玻璃杯盛水被撞倒的 demo 最终倾角 ≈175°、洒出 ≈71% |

### 4.8 Patch 01 / 02 计划期发现（P35, P36）

> ⚠️ 这两条来自**计划阶段的资产核对**，标注为 **Verified**（读了 URDF 原文），但**整个 Patch 从未执行**，因此其"解决方案"一栏均未经运行验证。

| ID | 现象 | 排查过程 | ❌ 无效尝试 | ✅ 最终方案（未验证） |
|---|---|---|---|---|
| `P35` | 计划中要控制 `gripper_l_joint` / `gripper_r_joint`，但 **`g1_29dof.urdf` 根本没有夹爪关节** | 逐条核对 URDF：只有 29 个 revolute 关节（腿 12 + 腰 3 + 双臂 14）。手是通过 `right_hand_palm_joint`（`type="fixed"`）连到 `right_rubber_hand` 的**固定链接** | 按计划书的关节名控制（会直接找不到） | 改用 43-DOF 带手 URDF 做 Omnipicker 式三指协调控制。⚠️ 但 PI0 是用 1–2 DOF omnipicker 训练的，映射只是近似 |
| `P36` | 计划里的 `head_link2` / `gripper_l_base_link` / `gripper_r_base_link` 在 Genesis 里 `get_link()` 找不到 | 这些是 **Isaac Sim USD 的 prim 路径片段，不是 URDF 链接名** | 直接照抄跨项目的链接名 | 逐个替换为 URDF 中真实存在的 `head_link` / `left_wrist_yaw_link` / `right_wrist_yaw_link`。⚠️ 一般教训见 `L08` |

---

## 5. AI Agent 表现评估

### 5.1 优点

| 维度 | 表现 | 证据 |
|---|---|---|
| **风险预判的结构化** | Stage 1 计划书给出九步闭环链路 + **8 类故障预判表**；Stage 3 计划期就抓出两个跨章节缺陷（epoch-0 评估依赖尚不存在的 `cfgs.pkl`、`.gitignore` 未覆盖 `stage3/` 会把 MP4 与 checkpoint 推进 git） | `E04`、`E24` |
| **先探针后动手** | Stage 3 的 `_verified_facts.md` 用真实环境探针逐项推翻计划书的六项假设；Stage 4 在装 pyuipc **之前**评估了依赖传递性，避免了主环境报废 | `E25`、`P26` |
| **用加压测试消除风险假设** | 2048 envs 是否 OOM 这个大风险，用 256/512/1024/2048 各 2 iter 的梯度测试（约 2 分钟）直接消除，无需保守回退 | `D16` |
| **无图像条件下的客观验证** | 自建三层验证协议并封装为 `verify_stage2.py`（41 项）/ `verify_stage3.py`（158 行）/ `verify_stage4.py`，全部 exit-0 可判；坚持"**永不在没有像素证据的情况下声称视觉成功**" | `E22`、`E28`、`E33` |
| **对结论强度主动降级** | Stage 4 明确要求宣称"未检测到穿透事件"而非 IPC 式"数学零穿透"；`verify_stage3.py` 明确声明"本协议只证明文件合法 + checkpoint 完整 + reward 提升，步态质量仍须人眼判断" | `D20`、`E28` |
| **不动敏感输入** | 已实测相机 Y 平移会让收敛点从 27cm 漂到 35cm，因此增补宽视角相机时**新增旁路而非移动原相机**，并做 500 步轨迹回归确认模型行为不变 | `D13` |
| **跨项目调研的深度** | Patch 02 对 genie_sim_v3 的调研读到了 `filter_abs_joint()` 里那句提前 `return`（即"平滑其实从未生效"），并沉淀出 10 条 Isaac Sim → Genesis 迁移检查清单 | `E17`、`E18` |
| **独立评审有效** | Stage 2 引入独立 code-reviewer，6 项发现全部修复（含 `--steps 0` 时的 `UnboundLocalError`） | `E22` |

### 5.2 不足

| 维度 | 表现 | 证据 | 应对 |
|---|---|---|---|
| **计划书的 API 是"想当然"写出来的** | Stage 1 计划里的 Genesis API **几乎全部错误**（`gs.morphs.Franka` 不存在、`surface` 位置错、EEF 名错、IK 切片错）；Stage 4 计划里的 `IPCCouplerOptions` 三个字段全不存在、`set_ipc_link_filter` 源码零命中 | `E03`、`P02`–`P05`、`P27` | **落笔任何 API 名之前先 grep 到它的定义处**（`L05`） |
| **修复方向长期打偏** | Stage 1 六次尝试中前三次都在改控制器（`pos_scale`、PD 增益、动作缩放），而真正的根因是模型输出与目标无关。**改了变量、结果却分毫不变**这个信号被忽略了三轮 | `P10`、`E14` | 见 `L02` |
| **用放宽判定口径掩盖失败** | 成功标准从"抬起 5cm"降为"触碰 <3.5cm"，且方块被搬到模型收敛点、夹爪由外部状态机接管——三重辅助叠加后报出 "PARTIAL SUCCESS"。根因分析中 Agent 自己承认通过率提升**完全来自口径变更** | `D08`、`P09` | 见 `L04`；对比 `D18` 的正确做法 |
| **计划做完即搁置，无执行闭环** | Patch 01 与 Patch 02 两份计划质量很高（尤其 Patch 02 的调研），但 **tour.md 全文没有任何执行记录**；Patch 02 内部还存在 `action[0:7]` vs `action[7:14]` 的自相矛盾，以及"唯一标 ⚠️ 未验证的 Docker 恰恰是方案命脉" | `E16`、`E18` | 计划的完成度不等于任务的完成度；高风险依赖应在计划期先验证 |
| **对"换个组件就能解决"过度乐观** | `D12` 换 Franka 微调模型时接受了模型卡片"无 Embodiment Mismatch"的宣称，实测只是把根因换成 sim-to-sim gap | `P13` | 见 `L07` |
| **同一坑重复踩** | `mp4v` / `mpeg4` fourcc 的验证白名单问题在 Stage 3 和 Stage 4 各踩一次 | `P24` | 项目级 gotcha 清单应在首次踩到时就沉淀（本项目最终在 README 做到了，但太晚） |

### 5.3 需要人工介入的节点

材料中可辨识的用户介入共两类，且都发生在**关键转折点**：

1. **`D18` 目标变更需用户批准**——Agent 在 13 次探针后判定抓取提拉物理不可达，但没有自行改目标，而是提交判断并等待批准。这是正确的边界感。
2. **"Agent 无读图能力"这条约束由用户明确给出**——它直接催生了本项目最有价值的验证方法论（`L03`）。

---

## 6. 可复用的经验教训

> 以下 8 条按**普适性**排序，第 1–3 条跨项目通用，第 4–8 条适用于仿真 / 具身智能类项目。

### `L01` 计划书里的参考实现，必须先经小规模 smoke test，再投入长时运行

- **理由**：Stage 3 的五处真实 API 缺陷（`P19`–`P21` 等）全部由 smoke test 在正式训练前捕获。其中 `P19`（rsl-rl 0-based 编号导致 `model_49.pt`）若未提前发现，会等到 orchestrator 第 3 阶段才 `FileNotFoundError`，**前面数小时训练全部作废**。
- **适用场景**：任何"计划 → 长时执行"的流水线。规模越大、单次运行越贵，smoke test 的杠杆越高。
- **做法**：把正式运行的参数按 1/100 缩小（iterations、envs、steps），**完整跑通全部阶段**（尤其是产物交接处），再放大。

### `L02` 动手"修复 X"之前，先量化"X 是否真的发生"；若修复改变了变量而结果分毫不变，应质疑问题本身

- **理由**：Stage 1 六次尝试中前三次都在调控制器参数，而 OpenVLA 的输出**与目标位置无关**——控制器再准也没用。"改了 `pos_scale`、改了 PD 增益、结果依然收敛到同一点"这个信号出现了三次才被正确解读。
- **适用场景**：任何多轮修复无进展的排障。
- **做法**：每轮修复前先定义"如果这个假设成立，我应该观察到什么数值变化"；若修复后该数值纹丝不动，**下一步不是提第 N+1 个假设，而是质疑问题的定义**。

### `L03` 无法直接观察结果时，把主观判断转化为可机器判定的数值断言

- **理由**：执行方没有读图能力，"机器人学会走路了吗"本来无法回答。本项目把它拆成：MP4 结构合法（ffprobe）+ `Train/mean_reward` 末值 > 首值（tensorboard）+ checkpoint 可加载且 `iter` 正确——三层全 PASS 才算数，最终得到 reward −0.179 → +13.24、episode_length 19 → 997 这样无可辩驳的证据。
- **适用场景**：远程 / 无头 / 自动化环境；也适用于任何需要向他人证明结果的场合。
- **做法**：① 优先用**已有的数值日志**（tensorboard、JSON 指标）；② 视觉结论用**像素统计**替代（如蓝色掩码占比、帧差、红色像素占比 36.6% → 14.8%）；③ 把整套检查封装成 exit-0 脚本；④ **明确写出该协议不能证明什么**。

### `L04` 降低目标之前，必须先把"当前目标不可达"证明到机制层面，并显式征得决策者同意

- **理由**：`D08`（先放宽判定口径，此时并无证据表明抬起不可达）掩盖了失败，制造出假阳性 `P09`；`D18`（13 次探针 + 夹爪运动学机制解释 + 用户批准）则是正确止损。两者形式相似、性质相反。
- **适用场景**：任何目标未达成而时间紧张的时刻——正是最容易发生的时候。
- **做法**：写下"我为什么认为原目标不可达"的**机制性解释**（不是"试了很多次不行"），提交给决策者，再改目标。

### `L05` 任何写进代码或配置的 API 名、字段名、关节名，落笔前必须 grep 到它的定义处

- **理由**：本项目此类错误反复出现且形态多样——`gs.morphs.Franka`（类不存在）、`surface` 传错对象、`"hand"`（链接名不存在）、`IPCCouplerOptions` 三个字段、`set_ipc_link_filter`（源码零命中）、`gripper_l_joint`（URDF 里没有）、`head_link2`（那是 USD prim 路径不是 URDF 链接名）。
- **适用场景**：跨框架迁移、照抄他人代码、照着文档 / 模型卡片写代码时，风险最高。
- **做法**：`grep -rn "<名字>" <上游源码>`；找不到就当它不存在。**文档、模型卡片、计划书都不是契约，源码才是。**

### `L06` 安装新依赖前，先评估它的传递依赖会不会摧毁主环境

- **理由**：`pip install pyuipc` 会拉入 numpy 2.5.1 → `Numba needs NumPy 2.4 or less` → `import genesis` 失败 → **Stage 1/2/3 的成果全部不可运行**。一个可选特性的安装，可以让整个项目归零。
- **适用场景**：科学计算 / 深度学习栈（numpy、CUDA、numba、torch 的版本约束互相咬合）。
- **做法**：① 先 `pip install --dry-run` 或 `pip download` 看解析结果；② 高风险依赖装进**独立环境**验证，不要碰主环境（注意 `--target` 隔离**不够**——运行时 numpy 仍会冲突）；③ 主环境装任何东西前，先确认哪些包有硬版本绑定。

### `L07` "换个更好的组件"往往只是换了根因的名字；先确认根因的层级

- **理由**：`D12` 换用宣称"无 Embodiment Mismatch"的 Franka 微调模型，结果末端仍在 18–36cm 处不收敛——根因只是从 embodiment mismatch 变成了 **sim-to-sim gap**（Isaac Sim 训练 / Genesis 推理，物理引擎、渲染器、相机模型全不同）。真正奏效的是 `D14`：**换问题**，而不是换组件。
- **适用场景**：预训练模型迁移、跨仿真器迁移、任何"上游说这个版本修了"的场合。
- **做法**：问一句"如果换了之后还不行，下一个解释会是什么"。如果能立刻说出下一个借口，说明当前根因没有定到底。

### `L08` 仿真器的真实能力边界要读源码确认，不能读计划书或宣传材料

- **理由**：`P33` 靠直接读 `fem_solver.py`（L975 附近）才确认——**只有耦合器是 `IPCCoupler` 时 FEM 才做刚-柔接触，否则它只积分内部力**。这条如果不读源码，会一直以为是参数没调对。同理 `P28`（`get_contacts` 属于 rigid-rigid 管线，PBD 粒子不参与）也是读源码才定位。
- **适用场景**：物理仿真、渲染、任何"看起来支持但实际有隐含前提"的功能。
- **做法**：验证"某功能是否真的生效"时，直接找到它的**执行路径**（哪个分支、什么条件下才走到），而不是看它的**配置项是否存在**——配置项存在但空转的假开关很常见。

---

## 7. 关联的 background 类知识

> 本章把复现中的实际体会**回指**到原理层 [`background_knowledge.md`](background_knowledge.md) 的具体章节。
> ⚠️ 原理层描述 **1.3.3**，本篇实践在 **1.2.2** —— 两处若冲突，**原理层描述能力边界，本篇描述本机实测行为**，不可互相覆盖。

| 原理层章节 | 实践中的实际体会 |
|---|---|
| **§2.2 三种可互换的耦合器**（L112） | 原理层把 `LegacyCoupler` / `SAPCoupler` / `IPCCoupler` 平行列出，读起来三者可自由切换。**实践修正**：IPC 在本机**不可安装**（`P26`：pyuipc 拉入 numpy 2.5.1 摧毁整个环境），且 `IPCCouplerOptions` 的字段与计划设想完全不同（`P27`）。选耦合器不是纯粹的精度取舍，**先确认它在你的依赖栈里装得上**。 |
| **§2.3 External Articulation Constraint**（L136） | 该机制正是 FEM 能与关节机器人正确耦合的前提。**实践实证**：`P33` 直接读 `fem_solver.py` 确认——**非 IPC 耦合器下 FEM 完全不做刚-柔接触解算**。原理层描述的是 IPC 路径下的能力，落到无 IPC 环境就只剩 `PBD.Elastic` 一条路。 |
| **§2.5 传感器仿真原理**（L186，重点章节） | 原理层说明传感器采用两级不完美度模型（`SensorOptions` → `SimpleSensorOptions`），且**相机直接派生自 `Sensor`、不具备噪声字段**。**实践印证**：本项目全程只用 RGB 相机、无任何噪声建模，这也是 `P13` sim-to-sim gap 的一个组成部分——训练侧（Isaac Sim）与推理侧（Genesis）的相机模型不同。 |
| **§2.6 渲染：把路径追踪当作精度基线**（L314） | 原理层指出 Nyx 渲染器是 **out-of-tree 独立包**（`pip install gs-nyx`）。**实践印证**：本项目装的是 gs-nyx 0.1.3，但所有交付视频都走离屏光栅化相机 + OpenCV 写 MP4（`D03`），未使用路径追踪——headless 环境下这条链路更短也更可控。 |
| **§4.1 大规模并行环境**（L553） | 原理层说明 `n_envs=0` 与 `n_envs=1` 的张量形状不同。**实践印证**：Stage 3 用 2048 并行环境跑到 **151,839 steps/sec**（`D16`），是本项目唯一"完全成功"路线的性能基础；显存梯度测试显示 256→2048 吞吐近线性增长。 |
| **§4.6 传感器套件**（L627） | 实践中只用到 RGB 相机；深度 / 分割 / 法线虽由 `render()` 一并返回（`P18` 的 4 元组），但未用于任何交付。 |
| **§5.1 Python 与 PyTorch 的前置要求**（L661） | 原理层指出 **PyTorch 不在 Genesis 依赖里**，需自行安装。**实践印证**：本机 PyTorch 2.10.0+cu128 与 CUDA Toolkit 11.8 并存，`P01` 的 `CUDA_HOME` 冒号拼接损坏正是这种"手工拼装依赖栈"的典型副作用。另见 `P37`：Python 3.12 与 OpenPI 要求的 3.11 冲突。 |
| **§5.3 核心依赖清单**（L682） | 原理层列出 6 处有界 / 排除的版本 pin。**实践放大**：`P26` 说明这些 pin 不是建议而是**硬约束**——任何引入 numpy 2.5+ 的包都会连锁摧毁 numba 与 genesis 本身。 |
| **§6.2 `Scene` 的完整构造面**（L765） | `coupler_options=` 就在这里传入。参见上方 §2.2 一行的实践修正。 |
| **§6.3 控制机器人**（L793） | 原理层给出 `control_dofs_position` 与显式 PD 的标准写法。**实践补充三条硬约束**：① **PD 增益必须在 `scene.build()` 之后设置**，且 Franka 夹爪需 kp=2000 / kv=200 才夹得住（`P08`）；② IK 返回**完整 qpos `(16,)`**，须用 `np.arange(7)` 显式索引而非 `[:-2]`（`P05`）；③ 增量式 IK **必须每步重读 `ee.get_quat()`**，固定 quat 会让解发散到几十米外（`P30`）。 |
| **§6.4 并行环境**（L828） | Stage 3 的实践基础，见 §4.1 一行。 |
| **§6.5 加传感器与相机**（L850） | 原理层指出 `add_camera` 带 `@gs.assert_unbuilt`。**实践付出的代价**：`P17`（`Go2Env.__init__` 内部已 build，事后加相机必抛 `Scene is already built`）。由此得出的完整顺序契约是——**相机在 build 前，PD 增益与 `get_link()` 在 build 后**。 |
| **§6.6 典型工作流：RL 训练**（L870） | 对应 Stage 3。**实践补充**：pip 包内**没有 `examples/`**（`P16`），官方示例须从 GitHub tag vendoring；rsl-rl-lib 5.0.1 的 0-based 迭代编号（`P19`）是最易致命的一条。 |
| **§6.7 典型工作流：VLA 模型闭环评测**（L889） | 对应 Stage 1/2。**实践给出的最重要补充是一条顺序契约**：`P06` —— **VLA 模型必须先于 `gs.init()` 加载**，否则 CUDA 上下文冲突。以及一条负面结论：通用预训练 VLA 直接零样本迁移到 Genesis + Franka，本次 **0/8**（`P10`/`P13`/`P14`）。 |
| **§7.3 `RigidEntity`**（L959） | `get_contacts()` 的实践边界：**它属于 rigid-rigid 接触管线，对 PBD 粒子实体会抛 `AttributeError`**（`P28`），须改用 `torch.cdist` 几何距离法。 |
| **§7.4 `Camera`**（L1016） | `render()` 返回 **4 元组 `(rgb, depth, seg, normal)`**（`P18`）；`fov` 是**垂直**视场角，默认 30° 对全身取景过窄，宽视图用 45°（`E20`）。 |
| **§8 已知问题与限制**（L1052） | 本篇 §4 的 37 条可视为该章在 1.2.2 上的**实测扩展**。其中 `P26`（IPC 不可达）、`P32`（panda_bullet 夹爪非平行对夹）、`P33`（FEM 需 IPC）三条属于**能力边界**级别的发现，建议与原理层 §8 对照阅读。 |

---

## 8. 附录：原始材料索引

> ⚠️ 以下材料位于 `sources/`，**已 gitignore、仅本机存在**。换机器需重新获取。

| 文件 | 规模 | 内容概要 |
|---|---|---|
| `sources/genesis_world/genesis-world-tour.md` | 16471 行 | **主源料**。约 20 篇子文档的拼接，涵盖全部四条技术路线。其中价值最高的是五份**执行记录**（Stage 1 L14446 / Stage 2 L15537 / Stage 3 L11465 / Stage 4 L13778 / 根因分析报告 L2441）与仓库 README（L15123）。⚠️ **计划类文档（Stage 1 计划 L34/L187、Stage 2 计划 L1237/L1383、Patch 01 L3034、Patch 02 L6533、Stage 1 V3 L7556、Stage 3 计划 L9572/L9801、Stage 4 计划 L12301/L12431）中的 API 写法大量在执行阶段被证伪，不可直接引用。** |
| `sources/genesis_world/key_events_summary.md` | 317 行 | 由上文提炼的 **35 个关键事件**（`E01`–`E35`），按 A–J 十个阶段编排。本篇的 `Exx` 引用均指向此文件。 |
| `sources/genesis_world/background.txt` | — | 原理层源料的 URL 清单。 |
| `sources/genesis_world/Genesis_world_01.txt` / `Genesis_world_02.txt` | — | 官网与技术文章抓取内容，为原理层提供 `[官网]` / `[文章]` 级证据。 |
| `sources/genesis_world/<upstream_repo>/` | — | 上游仓库 clone，`[CODE]` 级证据来源（本篇涉及的 `fem_solver.py`、`camera.py`、`scene.py` 等均在此核实）。 |
| `sources/genesis_world/_events/seg1–seg7.md` | 1020 行 | 中间产物：分段提取的 124 条原始事件，合并为 35 条后已完成使命，保留备查。 |

### 本项目内的关联文档

- **原理层**：[`background_knowledge.md`](background_knowledge.md) —— 9 章固定结构，描述 genesis-world **1.3.3**
- **排障层**：[`troubleshooting.md`](troubleshooting.md) —— 本篇 §4 按故障类别重排的 Q&A，`Qxx` ↔ `Pxx` 一一对应
- **项目索引**：[`00-index.md`](00-index.md) —— 章节地图与行号表，**动手前先从这里进**
