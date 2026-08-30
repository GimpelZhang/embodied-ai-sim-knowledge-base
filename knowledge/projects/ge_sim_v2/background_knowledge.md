# GE-Sim 2.0 原理层知识（background_knowledge）

> **文档定位**：本文是 `ge_sim_v2` 项目的**原理层**，回答"是什么、怎么设计、API 与能力边界"。
> 动手跑之前请先读 [`quickstart.md`](quickstart.md)；带着报错来的请直接去 [`troubleshooting.md`](troubleshooting.md)。
>
> **证据等级**（本文逐条标注，请按等级采信）：
> - `[PAPER]` —— 出自 arXiv:2605.27491v1 论文正文/附录，**是作者宣称值，未经本机复现**。
> - `[CODE]` —— 可在上游开源仓库 `AgibotTech/GE-Sim-V2` 中验证，附相对路径（必要时带行号）。**工程决策只信这一级。**
> - `[README]` —— 出自该仓库的 README / docs 目录。
> - `[官网]` —— 出自项目主页 `ge-sim-v2.github.io`，**无可复现验证脚本**。
> - `[文章]` —— 第三方或官方公众号宣传文章，二手，**宣传口径与论文口径存在实证冲突，见 §8.2**。
> - `[SKILL]` —— 出自 RoboColiseum 官方发布的 Claude Code skill 包（`challenge-*`），描述的是线上服务的**契约**而非本地代码。
>
> **版本对齐**：论文为 **v1（2026-05-26）**；开源仓库快照见 §5.1 的 commit 记录。**二者不是同一交付物** —— 论文描述完整训练体系，仓库只交付推理侧客户端，落差见 §5.2 与 §8.4。

---

## 1. 项目概述

### 1.1 名称与身份

| 项 | 内容 | 证据 |
|---|---|---|
| 正式名称 | **GE-Sim 2.0**（Genie Envisioner World Simulator 2.0） | `[PAPER]` 标题 |
| 论文标题 | *GE-Sim 2.0: A Roadmap Towards Comprehensive Closed-loop Video World Simulators for Robotic Manipulation* | `[PAPER]` |
| arXiv | **arXiv:2605.27491v1 [cs.RO]**，2026-05-26 提交，DOI `10.48550/arXiv.2605.27491` | `[PAPER]` |
| 主页 | `https://ge-sim-v2.github.io/`（页脚 © 2026 GE-Sim2） | `[官网]` |
| 代码 | `https://github.com/AgibotTech/GE-Sim-V2` | `[CODE]` |
| 中文宣传名 | "Genie Envisioner 2.0"、"GE-Sim 2.0"，公众号称其为"具身智能的物理进化引擎" | `[文章]` |

**开发者**：`[PAPER]` 署名 15 人 —— Boxiang Qiu、Liliang Chen、Yue Liao（通讯）、Nan Wang、Lintao Wang、Jiayi Luo、Wenzhi Zhao、Shengcong Chen、Di Chen、Ye Li、Chen Gao、Shuicheng Yan、Si Liu、Maoqing Yao、Guanghui Ren。
**署名机构**：**AgiBot（智元机器人）· BUAA（北航）· LV-NUS Lab（新加坡国立）· TJU（天津大学）**，以 AgiBot 为主导。

### 1.2 一句话定位

> GE-Sim 2.0 是一个**面向机器人操作（manipulation）的闭环视频世界模拟器**：给定初始多视角观测和一段动作轨迹，它用**生成模型直接"演"出机器人执行该轨迹的多视角视频**，同时解码出本体感觉状态、并对该 rollout 自动打分。

**必须先建立的认知：它不是仿真器，是"生成器"。** `[PAPER]` §1 明确把这条路线称作 "a neural world simulator for manipulation"，其核心主张是 **"By replacing hand-built physics and rendering with a data-driven generative process"** —— **用数据驱动的生成过程替换掉手工物理与渲染**。因此：

- **没有物理引擎**。没有刚体求解器、没有碰撞检测、没有接触力计算、没有摩擦系数。物体"为什么这样动"完全由训练数据里的视觉统计规律决定。
- **没有渲染器**。没有光栅化、没有光追、没有材质/BRDF、没有光源配置。像素直接由 VAE 解码得到。
- **没有场景文件**。没有 USD / MJCF / URDF 场景描述可编辑。"场景"就是你喂进去的那张初始观测图，**你无法在其中增删一个物体**。
- **不能自由造场景**。传统仿真器的"搭个新场景 → 跑"在这里不成立；GE-Sim 2.0 只能从**真实拍到的一帧**出发向前推演。

选型时这条是分水岭 —— 详见 §4.3 的能力边界与 §8.3。

### 1.3 主要用途

`[官网]` 列出三类应用场景（原文为三个并列标题，**无解释性正文**）：

1. **Evaluation in the world simulator** —— 在世界模型里评测策略（论文的主线，实验最充分）。
2. **Teleoperation in the world simulator** —— 在世界模型里做遥操作。
3. **Close-loop Learning in the world simulator** —— 闭环学习。

> ⚠️ **口径差异（重要）**：`[官网]` 用的词是 **"Close-loop Learning"**，而 `[文章]` 公众号称"**可以完成强化学习（RL in World Model）**"。但 `[PAPER]` §6「Looking Forward」把 RL 明确列为**尚未完成的future work**："A natural continuation is **online policy learning and reinforcement learning inside the simulator**"。论文实际做到的只是**离线的 filtered BC**（§4.4）。**三方口径不一致，以论文为准，详见 §8.2。**

论文自身给出的定位落点（`[PAPER]` 摘要末句）：

> "establishing GE-Sim 2.0 as a practical platform for **scalable evaluation** and **closed-loop learning** of manipulation policies."

### 1.4 适用 / 不适用场景

| 场景 | 是否适用 | 理由 |
|---|---|---|
| 已有真机数据分布内，想**大批量重复评测** VLA 策略、省真机工时 | ✅ 最契合 | 这是论文的主战场；`[PAPER]` §4.2 报 episode 级一致性 acc 0.81 |
| 想要**免人工判定**的成功/失败信号 | ✅ | World Judge，WM 模式 acc 0.79（`[PAPER]` Table 3） |
| 想用生成 rollout **筛数据回灌训练**（filtered BC） | ✅ 已验证 | 三任务真机平均 +15pp（`[PAPER]` §4.4） |
| 想在模型世界里做**在线 RL** | ❌ 未实现 | `[PAPER]` §6 明确列为 future work，见 §8.2 |
| 想**新建场景 / 换物体 / 改光照**做泛化测试 | ❌ 做不到 | 无场景表示，只能从真实初始帧出发（§1.2） |
| 需要**深度图 / 点云 / LiDAR / IMU / 力矩 / 触觉** | ❌ 全部缺失 | 只产出 RGB + 16 维关节态，详见 §2.7 |
| 需要**物理正确性**（力、摩擦、质量、稳定性） | ❌ 无保证 | 无物理解算；视觉合理 ≠ 物理合理，见 §8.3 |
| **换本体**（单臂 / 四足 / 人形 / 移动底盘） | ❌ 未支持 | 训练数据为固定双臂本体，`[PAPER]` §6 自述为 future work |
| 想**离线自建全流程** | ⚠️ 受限 | 开源仓库不含训练代码与权重，见 §5.2 |

### 1.5 家族谱系（理解 GE-Sim 2.0 的由来）

`[文章]` + `[PAPER]` §2 共同勾勒出智元世界模型的两条主线：

```
                    ┌─ World Action Model（WAM，建模"动作"）
                    │     EnerVerse ──► GE-Base / GE-Act ──► Act2Goal
世界模型（Genie Envisioner）
                    │
                    └─ World Simulator（建模"可交互世界"）
                          EnerVerse-AC ──► GE-Sim 1.0 ──► **GE-Sim 2.0**
                                              │
                                    EWMBench（评估世界模型能力）
```

周边配套项目（本项目源料一并收录，详见 §9）：

- **WorldArena**（arXiv:2602.08971）—— 世界模型统一评测基准。GE-Sim 2.0 宣称登顶其榜单，**但存在自评疑虑，见 §8.2**。
- **Real2Edit2Real**（arXiv:2512.19402）—— 真实演示数据的编辑扩增流水线，与 GE-Sim 共享 AgiBot 数据生态。
- **RoboColiseum**（`robocoliseum.ai`）—— 线上挑战赛/评测平台，是 GE-Sim 系世界模型的**托管服务化出口**，见 §6.4。

---
## 2. 核心原理

### 2.1 范式：把"仿真"换成"条件视频生成"

传统仿真器的回路是：

```
状态 s_t ──[物理求解器]──► 状态 s_{t+1} ──[渲染器]──► 图像 o_{t+1}
```

GE-Sim 2.0 的回路是（`[PAPER]` §1、§3.1）：

```
初始观测 x_0 + 稀疏记忆 m + 动作轨迹 A ──[多视角扩散 DiT]──► 未来视频块 x̂
                                                              │
                                                              ├─[状态专家]──► 本体感觉 ŝ（16 维）
                                                              └─[World Judge]──► 成功信号 r̂
```

**没有中间"状态"这一层**。模型直接从"像素 + 动作"映射到"像素"，物理规律以隐式方式编码在扩散模型权重里。论文对这么做的理由说得很直接（`[PAPER]` §1）：现有仿真器在**接触动力学、可变形物体、细粒度视觉外观、乃至机器人自身的驱动特性**上都吃力，"where effects such as **harmonic-drive compliance** are routinely abstracted away"（谐波减速器的柔顺性通常被直接抽象掉）。而生成模型在网络级视频上训练，能覆盖手工仿真器难以复现的长尾外观与交互。

### 2.2 底座：GE-Base 多视角视频世界基础模型

`[PAPER]` §2.1。GE-Sim 2.0 继承 GE-Base 的全部骨架，四个要点：

**(1) 分块自回归生成（chunk-wise autoregressive）**
设相机集合 `V = {h, l, r}`（head 头部、left wrist 左腕、right wrist 右腕）。在第 `t` 个自回归步，世界模型 `W` 预测下一块 `N` 帧多视角画面：

```
x^t_{1:N} = W(x_0, m_{0:t-1}, T(q))          … 式(1)
```

- `x_0`：初始多视角观测
- `m_{0:t-1}`：**长时稀疏记忆**，由之前已生成的各块中**稀疏采样关键帧**构成
- `T(·)`：冻结的 **T5 文本编码器**（此为 GE-Base；到 GE-Sim 这一项被动作条件替换）

> **稀疏记忆是长时程能力的关键**：它让时间上下文远超当前块，同时把输入长度控制在可算范围内。这是 GE-Sim 2.0 能做"分钟级"推演的机制根源。

**(2) 多视角编码**
每个视角独立过共享视频编码器 `E`，token 再叠加 **3D 旋转位置编码（RoPE）** 与**可学习的视角嵌入** `e^i_view`：

```
ṽ^i = RoPE(t,h,w) + v^i + e^i_view          … 式(2)
```

单视角输入序列为 `u^i = [ṽ^i_0 ‖ ṽ^i_m ‖ z^i]`（`z^i` 为该视角的噪声图）。

**(3) 跨视角一致性靠"部分层跨视角注意力"**
所有视角 token 拼接后送入**视频扩散 Transformer（DiT）**。**只有一部分 DiT block 做跨视角注意力**（在合并后的多视角序列上），其余 block 各视角独立处理以省算力。这是**质量与效率的显式折中** —— 跨视角一致性不是硬约束，而是靠注意力"软"实现的。

**(4) 骨干与训练目标**
- 骨干：**Cosmos-Predict2-2B-Video2World DiT**（NVIDIA），即 **2B 参数**。`[PAPER]` 反复强调"仅 2B"却登顶 WorldArena。
- 目标：**隐空间 flow matching**。给定目标块的 VAE 隐变量 `l` 与加噪隐变量 `l̃ = (1-σ_τ)l + σ_τ ε`，模型预测去噪速度 `v_θ`，并用条件掩码 `M` 只在待预测帧上算损失：

```
L_video = w(τ) · ‖ (v_θ − (ε − l)) ⊙ (1 − M) ‖²₂          … 式(3)
```

### 2.3 动作条件注入：Pose2Image + Raymap（本项目最有辨识度的设计）

这是 GE-Sim 系列的招牌机制，也是 `[官网]` 所称 "control-signal injection mechanism"。

**问题**：低维控制信号（14 维末端位姿）和高维视频隐空间之间如何对齐？直接当成一个全局条件向量喂进去，模型学不到"末端应该出现在画面哪个像素"。

**解法**：把动作**渲染成与画面像素网格对齐的图**，再按通道拼接。`[PAPER]` §2.2、§3.2。

#### 2.3.1 动作表示（14 维）

双臂系统每个控制步编码为 14 维向量，即左右臂各 7 维末端状态拼接（`[PAPER]` 式(4)）：

```
a_i = [ x,y,z, r,p,y, o  |  x,y,z, r,p,y, o ] ∈ R^14
        └── 左臂 ──┘      └── 右臂 ──┘
```

其中 `(x,y,z)` 为末端位置，`(r,p,y)` 为 roll-pitch-yaw 姿态，`o` 为**夹爪开合度**。`K` 步轨迹记作 `A ∈ R^{K×14}`。

> ⚠️ **注意维度对不上是常见困惑点**：**动作是 14 维末端空间（EE space）**，而**状态专家输出的是 16 维关节空间**（§2.4）。二者不是同一套表示，不要混用。

#### 2.3.2 EE Pose Map（3 通道）—— 把动作画成图

对每个时间步、每个视角，渲染分三步（`[PAPER]` §3.2）：

1. **位姿投影**：把每只手的夹爪位姿表示为世界系下的 4×4 变换，经**固定的 wrist-to-EE 修正**变换到相机系，然后把 **EE 原点 + 三个坐标轴各一个关键点**投影到像素平面，得到位置与朝向的像素坐标。
2. **深度感知渲染**：在画布上以 EE 原点为心画**实心圆**，半径随"相机到 EE 的距离"单调递减 —— **离相机越近圆越大**（`[PAPER]` 式(8)）：

```
r = clamp( 1 − (‖x_EE − x_cam‖ − d_min) / (d_max − d_min), 0, 1 ) · r_max
```

姿态则画成从原点连到三个投影轴关键点的**彩色线段**，左右臂用不同配色。

3. **夹爪开合度编码**：圆的**填充色**用连续 colormap 表示开合度 —— **由闭到开，颜色由深到浅**，左右臂用不同色系。论文特别说明这么做的动机：夹爪状态"binary in nature yet carries a continuous degree"（本质二值但带连续程度），用连续色带能在**单一稳定通道**里同时表达两者。

> **训练与推理用同一个 renderer**，以保证输入分布对齐（`[PAPER]` §3.2 原文点名强调）。这条对复现很关键：**自己实现 renderer 时任何细节偏差都会造成分布漂移**。

#### 2.3.3 Camera Raymap（6 通道）—— 把相机几何显式告诉模型

对每个像素 `(u,v)`，由内参 `K` 与相机到世界外参 `T_i` 构造一条世界系射线，取**射线原点 `o_i ∈ R³`（相机中心）** 与**单位方向 `d_i ∈ R³`**，沿通道堆叠得 6 通道 raymap `R_i ∈ R^{6×H×W}`。

**为什么必须要它**（`[PAPER]` §3.2，这段是理解本设计的关键）：

> 头部相机和腕部相机**都装在会动的机器人上**，腕部视角尤其随手臂大幅移动。Raymap 让模型能把"**视点运动造成的画面变化**"与"**场景中物体运动造成的画面变化**"区分开。
> 对腕部相机而言更是如此 —— 末端相对相机几乎静止，**手臂的运动学信号主要就承载在 raymap 里**。

#### 2.3.4 隐空间融合

`P_i` 与 `R_i` 双线性下采样到隐空间分辨率，与含噪视频隐变量沿**通道维**拼接（`[PAPER]` 式(5)、式(7)）。GE-Sim 2.0 的完整条件输入为：

```
z_cond = [ z_noisy ; R_ray ; M_pose ; m_cond ]          … 式(7)
          16 通道    6 通道   3 通道    1 通道
```

- `z_noisy`：**16 通道**含噪视频隐变量
- `R_ray`：**6 通道**逐像素射线图
- `M_pose`：**3 通道** EE 位姿图
- `m_cond`：**1 通道**二值掩码，区分"记忆帧"与"待预测帧"

> `[PAPER]` §3.2 特别交代了一条工程细节：**所有视觉输入从 `[0,1]` 归一化到 `[-1,1]`，两张条件图也遵循同样的 `[-1,1]` 约定**，使视频通道与条件通道数值对齐，"diffusion training is not destabilized by scale mismatch"。**自行接入时这是最容易踩的坑之一。**

通道级拼接的好处：在 DiT 的**每一层**都保持动作条件、相机几何、视频 token 三者的空间对齐。

#### 2.3.5 从 TI2V 到动作条件仿真

把式(1) 中的语言条件 `T(q)` 换成动作轨迹 `A`，其余骨架不变，得到（`[PAPER]` 式(6)）：

```
x^t_{1:N} = S(x_0, m_{0:t-1}, A^t)
```

`[PAPER]` §3.1 明确：模拟器**对动作来源不可知（agnostic）** —— 待评策略、遥操作日志、运动规划器、手写轨迹都可以。

### 2.4 本体感觉状态专家（Proprioceptive State Expert）

`[PAPER]` §3.3。这是 GE-Sim 2.0 相对 1.0 的**第一个新增模块**，也是 Table 1 中**唯一一个只有它有的能力**。

**要解决的缺口**：策略模型做 next-chunk 预测时需要**本体感觉状态**，但视觉专家只生成画面，画面里并不直接暴露关节角。以往做法是**拿下发的动作指令当状态的代理**，而 `[PAPER]` §1 指出这是 "a noisy proxy that **drifts from the arm's actual motion**"（会偏离手臂实际运动的噪声代理）—— 真机上因**柔顺性与接触力**，实际关节态和指令并不相等。

**状态表示（16 维，关节空间）**（`[PAPER]` 式(9)）：

```
s_t = [ θ^L (7 维关节角), g^L (夹爪), θ^R (7 维关节角), g^R (夹爪) ] ∈ R^16
```

夹爪开合度**线性归一化到 [0,1]**，与 EE pose map 的约定一致。

**输入构成**：除待预测的 `T_fut` 未来帧外，还含 `n_prev` 个历史帧的本体感觉状态 + 对齐的历史与未来动作，共 **`2·n_prev + 2·T_fut` 个 token**，其中**只有未来状态 token 被加噪**。

**如何取用视觉信息**（设计上值得注意）：状态专家与视觉专家**不是逐层对齐**的。视觉专家先跑完全部 `L` 个 block，各层输出 `h^video_l` 用**可学习标量权重 `α_l`**（初始化为 1）加权求和后过一次 LayerNorm（`[PAPER]` 式(10)）：

```
H_fuse = LayerNorm( Σ_{l=1..L} α_l · h^video_l )
```

状态专家的**所有 block 共享同一个 `H_fuse` 作为 cross-attention 的 K/V**。多视角下 `H_fuse` 重排为 `B × (V·L_tok) × d`，即**一次性 attend 到所有视角**的视觉特征。

**结构**：`L` 个轻量 transformer block，**隐藏维远小于视觉专家**。每块 = 沿状态时间轴的 RoPE 自注意力 + 对 `H_fuse` 的交叉注意力 + FFN；扩散时间步经 **AdaLN-single** 注入，且**与视觉专家共用同一个扩散时间步**。

**训练**：**冻结视觉专家**，只更新状态专家，同样用 flow matching（`[PAPER]` 式(11)）。

**历史状态增强（History-state augmentation）—— 一个很实在的闭环工程考量**：
训练时历史状态几乎总是**无噪的精确读数**，但闭环推理时部分历史状态来自状态专家**上一块自己的预测**，是带误差的。不做处理的话模型会"过度依赖完美历史"。因此训练时对历史段施加两种扰动（各以概率 0.5 独立施加，`[PAPER]` §8.2）：

1. **时间索引扰动（delta-index shift）**：整体平移 `Δ ~ Uniform{-3..-1, 1..3}` 并裁剪到有效范围，模拟策略与模拟器之间 1–3 帧的时间错位。
2. **历史轨迹重采样**：`n_prev → n_prev−1` 下采样再线性插值回 `n_prev`（式(12)），等效于**低通失真** —— 保留长期趋势、抹掉单帧高频细节。

两者在**验证时关闭**。

### 2.5 World Judge（世界评判器）

`[PAPER]` §3.4。**第二个新增模块**，把 rollout 变成机器可验证的信号。

- **来源**：设计基于 **Robometer**（Liang et al., 2026）这一通用视觉语言奖励模型，改造到闭环场景并**只训练单一 success 目标**。
- **骨干**：VLM。**冻结视觉编码器**，只训练语言模型与下游预测头。
- **逐帧表示**：rollout 的每一帧**单独作为一张图**送入（**不沿时间轴平均**，以保住逐帧判别粒度）。每帧图后追加一个专用 per-frame token，取其 hidden state 作为该帧表示 `f_i`。
- **文本条件的关键细节**：条件**不是完整任务指令，而是与当前 chunk 匹配的子任务 caption**，使判断针对"这一块本应完成什么"。

**为什么只做 success、不做 progress**（`[PAPER]` §3.4 的论证值得记住）：
Robometer 原本是 progress + preference 双目标，但 GE-Sim 2.0 **刻意砍掉 progress**，理由有二：

1. 稀疏成功信号对闭环评测与下游 RL 已经够用，且是操作类基准的主流指标。
2. **progress 监督在真机数据上本就不可靠** —— 真实采集的轨迹常含"有意或无意的纠错行为"（绕路、重试、在最终成功前暂时倒退）。在这种**非单调执行**下，标量 progress 标签噪声大，甚至不再对应真实的任务完成过程。

**监督构造**：每条轨迹有人工标注的成功帧 `i_succ`，该帧及其之后标 1，之前标 0；整体失败或无标注的轨迹**全部标 0**（式(13)）：

```
y_i = 1[ i ≥ i_succ ]
```

**损失**：正负帧极不平衡，故用**类别平衡 BCE**，按批内正负帧数 `N₊/N₋` 的倒数给少数类加权（式(14)）。

**闭环集成**：rollout 过程中 World Judge 对生成帧持续输出成功信号，形成一条**成功曲线**，既作评测的自动裁决，也作 reward-driven learning 的反馈。

### 2.6 加速：DMD2 步数蒸馏 + 随机步长训练

`[PAPER]` §3.5、§8.3。**第三个新增模块**。大规模并行评测下，多步扩散推理是吞吐瓶颈。两个方向：

**(1) 步数蒸馏（DMD2）**
用 **DMD2**（Yin et al., 2024）的分布匹配框架，把多步扩散蒸馏成少步学生模型。三个角色：

- **teacher**：主训练阶段的世界模型，全程**冻结**
- **student**：待蒸馏的少步模型
- **fake-score critic**：估计学生输出分布的分数

每步学生生成一个样本，重新加噪后分别由 teacher 与 critic 去噪，得到 `x_0^teacher` 与 `x_0^fake`，其差构成分布匹配梯度（式(15)）：

```
∇_DMD = ( x_0^fake − x_0^teacher ) / ‖ x_0^student − x_0^teacher ‖
```

分母做逐样本梯度幅值归一化。学生与 critic **交替优化**。适配 GE-Sim 2.0 的三点改动：teacher/student/critic **共用同一动作图条件**；**记忆帧全程保持为干净的真值隐变量**；学生的**去噪步数在训练时随机化**，从而推理时支持 1–4 步灵活配置。

超参（`[PAPER]` §8.3）：student 目标 **4 步推理**，训练时步数在 1–4 随机；**每 5 步更新一次 student、其余 4 步更新 critic**，首次 student 更新前有单步 warmup；critic 损失按 `1/σ²` 加权；student 用固定 sigma 调度 `[1.0, 0.9375, 0.8333, 0.625]`（集中在高噪端）；generator 更新时 sigma 分布 shift=3，critic 更新时 shift=5；student 用 AdamW（β₂=0.999、weight decay 0.01、100 步 warmup），critic 学习率 `2e-6`、β₁=0、β₂=0.999、weight decay 0.01；**学生不加辅助 flow-matching 损失**。

**(2) 随机步长训练（random-stride）**
训练时对每块的帧做**随机时间步长采样**，让模型见过不同时间密度的轨迹，从而推理时可**跳帧**，用同样帧数覆盖最多 **4×** 的时间跨度。长时程任务下这能显著减少所需的自回归块数，论文称"no noticeable loss in spatial-temporal consistency"。

**⚠️ 速度数字自相矛盾（重要，见 §8.2）**：
- `[PAPER]` **摘要**：a **25-frame** rollout in **2.3 seconds** on a single H100
- `[PAPER]` **§3.5 正文**：generates a **100-frame** rollout in about **2.3 seconds** on a single H100 with only four inference steps

**同一篇论文里同一个 2.3 秒对应了 25 帧和 100 帧两个说法，相差 4×**。合理猜测是正文把"随机步长 4× 跳帧后等效覆盖 100 帧"与"实际生成 25 帧"混写了，但**论文未作说明**。引用此数字时务必注明出处段落。

### 2.7 传感器仿真原理（专项详解）

> 本节回答"GE-Sim 2.0 的传感器是怎么仿真的"。**结论先行：它不做传统意义上的传感器仿真** —— 没有传感器模型、没有噪声模型、没有成像管线。理解这一点比理解任何细节都重要。

#### 2.7.1 与传统仿真器的根本差异

| 环节 | 传统仿真器（Isaac Sim / Genesis / MuJoCo） | GE-Sim 2.0 |
|---|---|---|
| 相机成像 | 场景几何 → 光栅化/光追 → 图像；可配内参、畸变、曝光、噪声 | **图像本身就是模型的生成目标**，无成像管线 |
| 相机外参 | 显式设定，可任意摆放新相机 | **仅编码为 raymap 条件**；视角受限于训练时的三目布置 |
| 深度图 | 免费副产物（z-buffer） | **不产出**（§2.7.4） |
| IMU / 力矩 / 触觉 | 由物理量导出 + 可选噪声模型 | **不产出** |
| 本体感觉 | 由关节状态直接读出（真值） | **由视频隐变量"解码"出来**（§2.4），是**估计值不是真值** |
| 传感器噪声 | 显式参数（bias / random walk / 高斯噪声等） | **无任何显式噪声参数**；真实感来自训练数据分布 |

#### 2.7.2 相机配置：固定三目，不可增删

`[PAPER]` §2.1 定义 `V = {h, l, r}` —— **头部相机 + 左腕相机 + 右腕相机**，共 **3 个视角**。

- 每个视角有**可学习的视角嵌入 `e^i_view`**（式(2)）。这意味着视角是**枚举量而非连续参数** —— 想加第 4 个相机，需要新的视角嵌入，**不能在推理时凭空增加**。
- 视角一致性由**部分 DiT 层的跨视角注意力**保证（§2.2），是软约束。`[官网]` 给的定性例证：毛巾演示中"左视角盲区里被遮挡的物体，随手臂移动后出现，且与主视角保持一致"，镜面反射也一并生成。

#### 2.7.3 相机几何如何进入模型：Raymap 就是"相机模型"

GE-Sim 2.0 唯一的"相机模型"就是 **6 通道 raymap**（§2.3.3）：由**每帧的相机内参与外参**构造逐像素的（射线原点，单位方向）。

它承担了传统渲染管线中"相机"的全部职责，但方式完全不同 —— 它不去**计算**这个相机会看到什么，而是**告诉网络"你现在是从这个位姿、这套内参在看"**，由网络自己生成相应画面。

**三点工程含义**：

1. **内外参必须准**。整套条件依赖标定，`[官网]` 称之为把异构动作空间"calibrated into a unified control space"。标定误差直接表现为动作跟随不准。
2. **相机随本体运动是被显式建模的**。这是论文强调 raymap 必要性的原因（§2.3.3）—— 腕部相机的运动学信号主要就在 raymap 里。
3. **不支持自由视角合成**。raymap 只在训练分布覆盖的位姿附近可信；把相机挪到训练中没出现过的位置，没有任何机制保证结果正确。

#### 2.7.4 只有 RGB —— 缺失的传感器清单

经论文全文核对，GE-Sim 2.0 **产出**只有两类：

- **RGB 多视角视频**（3 视角，由 VAE 解码）
- **16 维本体感觉状态**（双臂关节角 + 夹爪，由状态专家解码）

以下在论文中**未提及**，视为不支持：

| 传感器 | 状态 |
|---|---|
| 深度图 / 点云 | **未提及**。注意：EE pose map 里那个"离相机越近圆越大"的半径编码（式(8)）是**给模型的输入条件**，不是输出的深度 |
| LiDAR | **未提及** |
| IMU / 加速度计 / 陀螺仪 | **未提及** |
| 关节力矩 / 六维力 | **未提及** |
| 触觉 / 接触传感 | **未提及**。接触只以**视觉形式**呈现，无接触量输出 |
| 音频 | **未提及** |
| 分割 / 法线 / 光流等辅助通道 | **未提及** |

#### 2.7.5 "传感器噪声"在这套范式里意味着什么

传统仿真器里，噪声是**加在干净真值上的显式模型**（bias、random walk、高斯噪声……）。GE-Sim 2.0 **没有这一层**，但这不等于输出是"理想真值"——恰恰相反：

- **输出天然带有生成模型的伪影与误差**，且这些误差**不可参数化、不可关闭、不可复现控制**。
- 论文把这类误差当作**要对抗的东西**，而不是要建模的特性。两处针对性设计都是为此：
  - **记忆帧增强**（§2.3 训练段、`[PAPER]` §8.1）：训练时对记忆帧隐变量注入扰动，逼近推理时自生成记忆帧的误差分布。具体：外层激活概率 0.8；**渐进噪声混合**（逐帧激活概率 0.5、扰动尺度 `σ_mem=0.2`，另有概率 0.2、尺度 `σ_first=0.5` 的首帧扰动）；**局部高斯模糊**（概率 0.5，kernel ∈ [1,5]，σ ∈ [0.1,1.3]，限制在覆盖约 **20%** 画面的连通域掩码内）；**多视角同步色彩抖动**（概率 0.3，**所有视角共享同一抖动**以保持跨视角光照与色彩统计一致）。
  - **历史状态增强**（§2.4）：对抗状态专家自身预测误差的累积。

> **给复现者的提示**：如果你的下游任务依赖"可控的传感器噪声"（例如测策略对噪声的鲁棒性），GE-Sim 2.0 **给不了** —— 它的噪声既无法调大也无法调小。这与 `genesis_world` 恰好相反：后者有完整的两层缺陷模型但默认全 `0.0`（详见 `../genesis_world/background_knowledge.md`）。

#### 2.7.6 本体感觉：是"解码"不是"读取"

最后强调一个容易误解的点。传统仿真器里关节角是**状态变量本身**，读出来就是真值。GE-Sim 2.0 里关节角是**从视频隐变量里回归出来的估计量**（§2.4），它：

- 有误差，且误差会在自回归中累积（论文为此专门做了历史状态增强）；
- 但**恰恰因此更贴近真机** —— 论文的论证是，真机上因**柔顺性与接触力**，实际关节态本就偏离下发指令，用指令当代理反而更不准（`[PAPER]` §1、§4.5）。
- 消融证据（`[PAPER]` §4.5）：去掉状态专家，episode 级一致性 **acc 0.81 → 0.74**、**recall 0.82 → 0.67**，precision 基本不变。收益集中在**需要跨多个动作块精确跟踪状态**的任务（Fold towels、Borrow flame、Clean mirror stains）。

---
## 3. 架构与模块

> **本章要点**：GE-Sim 2.0 有**两套需要分开看的架构** —— 论文描述的**模型内部架构**（§3.2），和开源仓库交付的**工程运行架构**（§3.3–§3.6）。二者不是同一层次的东西，混读会得出错误结论。本章 §3.3 起全部为 `[CODE]` 级，读自仓库快照 `AgibotTech/GE-Sim-V2`。

### 3.1 先分清两层架构

| | 模型架构（论文） | 工程架构（开源仓库） |
|---|---|---|
| 描述对象 | DiT 主干 + 三个条件通路 + 状态专家 + 评判器 | 三进程 C/S 拓扑 + 一套 gym 风格 SDK |
| 证据等级 | `[PAPER]` | `[CODE]` |
| 见 | §3.2（细节在 §2） | §3.3 – §3.6 |
| 交付状态 | 论文全量描述 | **仅推理侧**；训练代码未开源（见 §8.4） |

**一个必须先纠正的常见预判**：开源仓库**不是**一个"只会调远程 API 的瘦客户端"。`src/gesim/models/gesim_v2/` 下有完整的推理侧模型实现（DiT、VAE、调度器、pose expert、raymap），约 **8 200 行**，占全仓 Python 代码（约 **11 400 行**，不含二进制 FK 库）的 **72%**；权重也确实公开在 HuggingFace 上（§5）。真正缺席的是**训练/蒸馏代码与数据管线**，不是模型本身。

### 3.2 模型侧架构（论文视角，细节见 §2）

```
                 任务指令 text ──► 统一 prompt embedding
                                        │
  首帧 (3,V,H,W) ──► VAE encoder ──┐    │
                                   ▼    ▼
  16-D 动作序列 ──► Pose2Image ──► [ Cosmos-Predict2-2B DiT 主干 ]
       │            (EE 位姿带)      │  多视角 RoPE + view embedding
       │                             │  部分跨视角注意力
       └──► FK ──► 相机 raymap ──────┤
                    (6 通道)         │
                                     ├──► VAE decoder ──► (T,3,V,H,W) 视频
                                     │
                                     └──► Pose Expert ──► (T,16) 本体状态
                                                │
   生成的 head 视角视频 ──────────────────► World Judge ──► success / progress
```

四个模块的职责与公式对应关系：

| 模块 | 职责 | 详见 |
|---|---|---|
| GE-Base（DiT 主干） | 分块自回归的多视角视频生成 | §2.2，式 (1)(2)(3) |
| Pose2Image + Raymap | 把 16-D 关节动作变成**像素级**条件 | §2.3，式 (4)(5)(7)(8) |
| Pose Expert（状态专家） | 从隐层解码出 16-D 本体感觉 | §2.4，式 (9)(10)(11)(12) |
| World Judge（评判器） | 逐帧 success 概率 + progress | §2.5，式 (13)(14) |
| DMD2 蒸馏 | 把采样步数压到 4 步 | §2.6，式 (15) |

> **World Judge 在开源仓库里是"接口而非实现"** —— 仓库只给出 `RewardClient` 协议（§3.5），没有附带评判器权重。这条落差是排障层与经验层的高频起点，详见 §8.4。

### 3.3 工程架构：三进程拓扑 `[CODE]`

跑通一次闭环需要**三个独立进程**，其中两个通常在**不同的 conda 环境**里（openpi 与 gesim 依赖冲突）：

```
┌────────────────────────────────┐
│  你的脚本 / examples/closed_loop.py │   进程 A（gesim 环境）
│    WorldModelEnv (gym 风格)      │
└───────┬─────────────────┬──────┘
        │ HTTP            │ WebSocket
        │ :9000           │ :8000
        ▼                 ▼
┌───────────────┐   ┌──────────────────────┐
│ 世界模型服务   │   │ π0.5 策略服务          │  进程 C（openpi 环境）
│ python -m     │   │ openpi_serving/       │
│   gesim.server│   │   serve_pi05.py       │
│ 进程 B (GPU)  │   │ (无 HTTP 健康检查端点) │
└───────────────┘   └──────────────────────┘
```

- 进程 B 启动：`python -m gesim.server --model gesim_v2 --config configs/gesim_v2.yaml --host 0.0.0.0 --port 9000`（`server/__main__.py:53-87`）。`--config` 对 `gesim_v2` **是必填**，缺省会报错退出（`__main__.py:69-70`）。
- 进程 B 另有一个**纯离线预览模式** `--demo`：它会把 `--model` 强制换成 `example` 假模型并注入合成数据（`__main__.py:26-51,67-68`），**不加载任何权重、不需要 GPU**。这是验证"服务框架是否装对"的最省事手段，也是新手最容易误以为"模型已经跑起来了"的地方。
- 进程 C 启动见 `scripts/serve_policy_pi05.sh`，端口/检查点/norm-stats 全部走环境变量（`OPENPI_CKPT`、`PORT`、`ASSET_ID`），并把 `openpi_serving` 塞进 `PYTHONPATH`。openpi 本身是 git submodule（`.gitmodules` → `Physical-Intelligence/openpi`），**脚本明确声明不修改该 submodule**。

### 3.4 仓库目录结构 `[CODE]`

| 路径 | 行数量级 | 作用 |
|---|---|---|
| `src/gesim/env.py` | 208 | **主入口**：`WorldModelEnv`，gym 风格 `reset`/`step` |
| `src/gesim/types.py` | 82 | 三个核心契约：`Observation`／`StepInfo`／布局转换函数 |
| `src/gesim/episode.py` | — | `EpisodeBundle`：加载 `assets/demo_00x/` 那套 npy+png |
| `src/gesim/action_chunk.py` | — | 长动作块压缩（avg-pool，与服务端对齐） |
| `src/gesim/client/{transport,codecs}.py` | — | HTTP 客户端 + 二进制帧编解码 |
| `src/gesim/server/{app,__main__,session,status,dashboard}.py` | 614 | HTTP 服务、会话管理、实时看板 |
| `src/gesim/models/base.py` | 79 | `WorldModel` 抽象类 + 名称注册表 |
| `src/gesim/models/gesim_v2/**` | **8 206** | **推理侧模型实现全量**（见下） |
| `src/gesim/policies/{base,openpi}.py` | 137 | `Policy` 协议 + π0.5 适配 |
| `src/gesim/rewards/base.py` | 30 | `RewardClient` 协议（**只有协议**） |
| `src/gesim/conditioning/{band,kinematics,policy_band}.py` | — | EE 位姿带渲染 + FK |
| `src/gesim/conditioning/_g01_fk.so` | 二进制 | **编译好的 G01 正运动学库**（无源码） |
| `openpi_serving/{pi05_gesim,serve_pi05}.py` | — | π0.5 服务端（在 openpi 环境里跑） |
| `examples/{closed_loop,replay}.py` | — | 两个官方示例 |
| `docs/*.md` | 556 | 6 篇：安装/回放/闭环/加世界模型/加策略/加奖励 |
| `tests/test_*.py` | — | 8 个测试文件 |

`models/gesim_v2/` 内部（这是 §3.2 那张图的代码落点）：

| 文件 | 行数 | 对应原理 |
|---|---|---|
| `model.py` | 834 | `GeSimV2WorldModel`，实现 `WorldModel` 抽象类 |
| `image_processor.py` | 1320 | Pose2Image 位姿带渲染（§2.3） |
| `networks/transformers/transformer_cosmos_multiview_PE.py` | 599 | 多视角 DiT + 位置编码（§2.2） |
| `networks/transformers/transformer_cosmos.py` | 581 | Cosmos 主干 |
| `networks/transformers/pose_expert.py` | 144 | 状态专家（§2.4） |
| `networks/autoencoders/autoencoder_kl_wan.py` | 1089 | VAE |
| `pipelines/pipeline_cosmos_acwm_PE_eff.py` | 895 | 动作条件世界模型推理管线 |
| `pipelines/pipeline_cosmos2_video2world.py` | 814 | 基础 video2world 管线 |
| `schedulers/scheduling_flow_match_euler_discrete.py` | 561 | 流匹配采样器（§2.2 式 3） |
| `raymap.py` | 92 | 相机射线图（§2.3） |
| `networks/transformers/{liger_norms,triton_rope,sparge_attention}.py` | 134/173/205 | 三个可选加速内核 |

> **`[CODE]` 佐证 —— 蒸馏是真的落到代码里的**：`configs/gesim_v2.yaml` 写死 `num_inference_steps: 4`、`distilled_sampling: true`、`distill_sigma_schedule: [1.0, 0.9375, 0.8333, 0.625]`，与 §2.6 论文描述的 DMD2 四步蒸馏完全对得上。这是全文档中少数几处"论文宣称"能被"发布物"直接验证的地方。

> **`[CODE]` 值得注意 —— `pyproject.toml` 主动豁免了一批文件的 lint**：`networks/`、`pipelines/`、`schedulers/`、`utils/`、两个 processor 被 `extend-exclude` 排除，注释自述这些是"从上游 gesim_v2 代码库**逐字搬运**、重构期间验证过字节一致"的数值敏感代码。**改这些文件要格外小心**，它们没有格式化保护网。

### 3.5 三个扩展点（官方支持的二次开发接口）`[CODE]`

仓库把可替换的部分收敛成了三个窄接口，各配一篇 docs：

| 扩展点 | 契约 | 关键约束 |
|---|---|---|
| **世界模型** `models/base.py:29-60` | 抽象类 `WorldModel`：`from_config`／`reset`／`set_camera_params`／`set_episode_data`／`set_episode_traj`／`step`，可选 `set_task` | 类属性 `chunk_size = 25`；需在 `_REGISTRY` 里注册导入路径（`models/base.py:64-67`，现有 `example` 与 `gesim_v2` 两项） |
| **策略** `policies/base.py:12-23` | Protocol `Policy`：`reset()` + `infer(obs) -> (horizon, 16)` | 返回**必须是 WM 布局** `[L7_arm, L_grip, R7_arm, R_grip]` |
| **奖励** `rewards/base.py:24-30` | Protocol `RewardClient`：`evaluate(head_frames, task) -> RewardResult` | 只吃 **head 单视角** `(T,H,W,3)` uint8；返回 `success` 与 `progress` 两个 `(T,)` 数组 |

> **最高频的一类接口错误：两套 16 维布局不同。** `types.py:6-7` 明确写了两种排列：
> - 世界模型侧（动作、`step` 返回的 state）：`[L7_arm, L_grip, R7_arm, R_grip]`
> - 策略输入侧（`Observation.state`）：`[L7_arm, R7_arm, L_grip, R_grip]`
>
> 转换函数是 `wm_state_to_policy_state()`（`types.py:72-82`）。**两个夹爪维的位置不同**，弄反了不会报错，只会让策略收到错误的夹爪状态——典型的静默失效。

### 3.6 一次 `step()` 的完整数据流 `[CODE]`

以闭环模式（`conditioning="action"`）为例，`env.py:114-179`：

1. 校验动作形状必须是 `(L, 16)`（`env.py:141-142`）。
2. **若 `L > chunk_size` 且 `compress_actions=True`（默认）**：把长块 avg-pool 压成**一块** 25 步（`env.py:145-146`）。文档自述这是"每回合只跑一次世界模型推理"的加速手段，**代价是时间分辨率**（`env.py:43-48`）。例如 π0.5 一次输出 50 步动作 → 被压成 25 步。若要保留完整时间分辨率，传 `compress_actions=False`，改为切成多个子块、每块一次推理。
3. 对每个子块：用 `PolicyBandRenderer` 经 FK 渲染 EE 位姿带 + c2w，上传 `set_episode_traj`，再 `client.step(chunk)`（`env.py:150-155`）。
4. 拼接帧与状态；若配了 reward client，则用 **head 视角**帧打分（`env.py:166-169`）。
5. 构造下一步 `Observation`：取**最后一帧**拆成三视角 uint8 图，state 取预测状态最后一行并**转成策略布局**；**若模型没返回 state，则回退用最后一个动作充当状态**（`env.py:171-175`）——这个 fallback 意味着"状态看起来正常"并不能证明状态专家在工作。
6. 返回四元组 `(obs, reward, state, info)`。

> **接口易错点（三条，均 `[CODE]`）**：
> - **`step()` 返回 4 元组且没有 `done`** —— 不是 gym 的 5 元组，世界模型**不会判定回合结束**，终止条件得你自己按 `reward`/`progress` 定。
> - **第 3 个返回值是 `state` 不是 `info`** —— 顺序为 `(obs, reward, state, info)`（`env.py:116`）。
> - **`reward` 与 `progress` 只在配置了 reward client 时才非 None**（`env.py:166-169`），而仓库**不带评判器实现**，所以开箱即用时这两项恒为 `None`。

### 3.7 两种 conditioning 模式（必须先想清楚用哪个）`[CODE]`

`env.reset()` 的 `conditioning` 参数只有两个合法值（`env.py:25,90-93`）：

| 模式 | 行为 | 用途 | 依赖 |
|---|---|---|---|
| `"action"`（默认） | 用**传给 `step()` 的动作**经 FK 实时渲染位姿带 —— **真闭环** | 策略评测、闭环 rollout | 需要 `_g01_fk.so`，**仅 linux x86_64** |
| `"episode"` | 用 bundle 里**录制好的 EE 位姿**一次性渲染整条带 —— 回放 | 复现训练同分布结果、做 sanity check | 不需要 FK |

> **`"episode"` 模式常被误读为"闭环跑通了"**。它是 training-parity 回放：动作轨迹来自录制数据而非策略，**策略即使是随机的，画面也会照着原轨迹走**。判别方法：看 `reset()` 时是走了 `render_band_from_bundle`（episode）还是构造了 `PolicyBandRenderer`（action），见 `env.py:104-109`。

> **`_g01_fk.so` 是本仓库最硬的一处平台约束** `[CODE]`：`conditioning/kinematics.py:1-31` 说明机器人几何、关节布局、动作→关节映射**全部编译进了这个 `.so`**，Python 侧只传 16-D 动作 + 4 个头/腰关节，拿回左右两个 EE 位姿 `[x,y,z,qx,qy,qz,qw]`（scalar-last）。**没有源码**，加载失败时的报错已内建提示"它是为特定平台（linux x86_64）构建的"。这同时意味着：**换机器人本体 = 换这个 `.so`，而你没有它的源码**（呼应 §8.1 的"固定单一本体"限制）。

## 4. 关键特性

### 4.1 论文自评的能力对照表

`[PAPER]` Table 1 把 GE-Sim 2.0 与 9 个同类工作逐项对照。**这是作者自制的表，请按 `[PAPER]` 级采信**：

| 能力 | IRASim | 1XWM | GE-Sim 1.0 | Ctrl-World | DreamDojo | Interactive WM | ABot-PhysWorld | WorldScape | MotuBrain | **GE-Sim 2.0** |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| Long-horizon 长时程 | ✓ | ✗ | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | **✓** |
| Multi-view 多视角 | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✓ | **✓** |
| **Proprioceptive State 本体感觉** | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| Pseudo Real-Time 准实时 | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | ✓ | ✓ | **✓** |
| **Reward 奖励** | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | **✓** |
| Open-source 开源 | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ | **✓** |

**读这张表要抓的两点**：

1. **"Proprioceptive State" 一栏只有 GE-Sim 2.0 打勾** —— 这是全表唯一的独占能力，也是本项目最实质的差异化贡献。
2. **"Reward" 一栏只有 1XWM 和 GE-Sim 2.0 打勾** —— 内置评判能力是第二个稀缺项。

> ⚠️ **"Open-source ✓" 这一格需要打折扣看**：该表把 GE-Sim 2.0 标为开源，但实际开源的仓库**不含训练代码，也不含模型权重**，是一个面向托管服务的客户端。详见 §5.2 与 §8.4 —— **这是本项目最需要提前知道的落差**。

### 4.2 相对 GE-Sim 1.0 的四项升级

`[PAPER]` §1、§3.1 归纳：

| # | 升级项 | 具体内容 | 解决的缺口 |
|---|---|---|---|
| 1 | **数据重训** | 在**数千小时**真机数据上重训，覆盖遥操作、接触密集交互、真机策略部署 rollout，**且含成功与失败轨迹** | 动作跟随保真度、轨迹空间覆盖度 |
| 2 | **本体感觉状态专家** | 从视频隐变量解码 16 维关节态 | 以往只出画面，策略拿不到 state，只能用指令当噪声代理 |
| 3 | **World Judge** | VLM 奖励模型逐帧打分 | 以往"渲染但不评判"，无法规模化评测 |
| 4 | **加速框架** | DMD2 蒸馏 + 随机步长跳帧 | 吞吐远不够 chunk-wise 大规模并行 rollout |

`[PAPER]` §1 把后三项对应到明确的三个 gap，原文值得直引：

> "(i) existing simulators predict only visual states, leaving unmodeled the **proprioceptive state**...; (ii) they render rollouts but **do not score them**...; (iii) their **rendering throughput** is far below what chunk-wise, parallel rollout across many tasks and seeds demands."

### 4.3 独特优势（相对传统物理仿真器）

| 优势 | 说明 | 证据 |
|---|---|---|
| **覆盖长尾外观与交互** | 液体、可变形物体、接触细节、真实材质，都是手工仿真器最吃力而生成模型相对擅长的 | `[PAPER]` §1 |
| **不需要建模** | 无需 USD/URDF 资产、无需调物理参数、无需标定摩擦系数 | 范式使然 |
| **自带真机外观** | 视觉域天然就是真机域，**没有 sim-to-real 视觉 gap** | 范式使然 |
| **建模了驱动柔顺性** | 谐波减速器柔顺性等被传统仿真器"抽象掉"的效应，隐含在真机数据里 | `[PAPER]` §1 |
| **本体感觉贴近真机** | 解码的是**实际**关节态而非下发指令，天然含柔顺/接触导致的偏差 | `[PAPER]` §1、§4.5 |
| **长时程稳定性好** | 头视角 50 秒 rollout 内 PSNR 仅从 24.84 降到 21.08 dB（<4 dB），且**第一段之后趋于平缓**；基线持续劣化 | `[PAPER]` §4.1、Figure 6 |
| **小模型高效** | 仅 **2B** 参数即登顶 WorldArena，胜过闭源大模型 Sora / Veo | `[PAPER]` §4.1（⚠️ 自评疑虑见 §8.2） |

### 4.4 需要同时记住的代价

上表每一条优势都有对应代价，**不能只记优势**：

| 优势 | 对应代价 |
|---|---|
| 不需要建模 | → **也无法建模**：不能新建场景、增删物体、改光照材质（§1.2） |
| 自带真机外观 | → **只能在训练数据分布内可信**；OOD 场景无保证 |
| 覆盖长尾交互 | → **无物理正确性保证**：视觉合理 ≠ 力学合理（§8.3） |
| 本体感觉贴近真机 | → 它是**估计值**，有误差且会累积（§2.7.6） |
| 小模型高效 | → 2B 的容量上限也限制了泛化，论文自述"foundation backbone 是通向通用具身仿真的核心瓶颈"（§6） |

---
## 5. 安装与依赖

> 本章全部 `[CODE]` 级，读自仓库 `docs/installation.md` 与 `pyproject.toml`。
> ⭐ **动手装之前请先读速查层 [`quickstart.md`](quickstart.md) §1 环境准备（L30–102）** —— 那里给的是**实测跑通过的**版本锁定项、三个 conda 环境的分工、以及"必须在 import 之前设"的环境变量。本章给出处与原理，速查层给可直接敲的命令。
> 复现仓库侧的依赖现状见代码层 [`code_knowledge.md`](code_knowledge.md) **§5（L427–475）**，其中 **§5.1 明确 `未发现` 任何依赖清单文件**（`requirements.txt` / `setup.py` / `pyproject.toml` / `environment.yml` 全无），换机只能手装。
>
> ⚠️ **本章给的是"应该怎么装"，不是"实际会撞到什么"。** 本项目依赖除 `torch>=2.0` 外**全无版本约束**（§5.3），实测装依赖时**顺序本身就是坑**。真正踩过的 9 个安装/环境问题见排障层 [`troubleshooting.md`](troubleshooting.md) **B 类 `Q08`–`Q16`**，其中最容易撞的三条：
> - `Q09` —— `spas_sage_attn` **根本不在 PyPI 上**，§5.4 那四个加速内核开关**首次部署应全部关掉**；
>   ⚠️ **但一次实测给出了更省事的结论**：复现仓库**只关了 `sparge_attention` 这一个**、另三个保持 `true`，五个 Stage 全部跑通（[`code_knowledge.md`](code_knowledge.md) §6.1 / §8.4）。装不上任何内核时才需要按本章"四个全关"。
> - `Q11` —— openpi 依赖地狱，**`regex` 必须在 torch 之前装**，且 lerobot 会把 numpy 顶成 2.x，装完要回锁 1.26.4；
> - `Q12` —— **绝不要装 conda 的 gcc**，它的传递依赖会把 CUDA 12.1 顶成 13.x（`--freeze-installed` **明确无效**）。

### 5.1 硬性前提

| 项 | 要求 | 出处 |
|---|---|---|
| Python | **>= 3.10**（未声明上界） | `pyproject.toml` `requires-python` |
| GPU | **仅世界模型服务端需要 CUDA GPU**；客户端（`WorldModelEnv`、策略、奖励）可在纯 CPU 机器与 CI 上跑 | `docs/installation.md` |
| 操作系统 | 闭环模式实际被 `_g01_fk.so` 限定为 **linux x86_64** | `conditioning/kinematics.py:23-27` |
| 克隆方式 | **必须 `--recursive`**，否则没有 openpi submodule | `docs/installation.md` |

```bash
git clone --recursive <repo-url> gesim
cd gesim
```

> **忘了 `--recursive` 是第一个坑**：`third_party/openpi/` 会是空目录，闭环的策略侧整条链路都装不起来。补救：`git submodule update --init --recursive`。

### 5.2 三种安装档位

```bash
pip install -e ".[server]"   # 世界模型服务端（需 GPU）：+diffusers/transformers/accelerate/safetensors/sentencepiece/protobuf/torchvision
pip install -e .             # 仅客户端（哪都能跑）
pip install -e ".[dev]"      # 开发：+pytest/ruff
```

策略客户端是**独立的一个轻量包**，来自 submodule，需单独装：

```bash
pip install -e third_party/openpi/packages/openpi-client
```

> 漏装它的表现是构造 `OpenPIPolicy` 时抛 `ImportError: openpi-client is not installed`（`docs/closed_loop.md` 自带这条排障）。

### 5.3 依赖清单（`pyproject.toml`，**全部未锁版本**）

| 档位 | 依赖 |
|---|---|
| 基础 | `numpy`、`requests`、`pillow`、`opencv-python-headless`、`torch>=2.0`、`einops`、`scipy`、`matplotlib`、`pyyaml`、`huggingface_hub`、**`pin`** |
| `[server]` | `diffusers`、`transformers`、`accelerate`、`safetensors`、`sentencepiece`、`protobuf`、`torchvision` |
| `[dev]` | `pytest`、`ruff` |

> **两处值得警惕的依赖事实**：
> 1. **除 `torch>=2.0` 外没有任何版本约束**（无上界、无 pin）。这与 `genesis_world` 那种"6 处带界 pin 各对应一个已知上游破坏"的风格相反 —— 不是因为兼容性好，而是**没有做过兼容性收敛**。`diffusers`/`transformers` 这类高速迭代包一旦升级出现破坏，这里没有任何保护。**建议自己冻结一份 `requirements.txt` 并单独开环境。**
> 2. **`pin` 是 pinocchio**（刚体动力学库），是**基础依赖而非可选**，因为闭环位姿带渲染要用它做正运动学。它在部分平台上 pip 安装并不顺利，是环境阶段的常见卡点。

### 5.4 PyTorch 与加速内核

**PyTorch 需要自己按驱动装 CUDA 版**（官方文档给的是 cu126 示例）：

```bash
pip install torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 \
    --index-url https://download.pytorch.org/whl/cu126
```

四个加速项**全部可选**，各自对应 `configs/gesim_v2.yaml` 里的一个开关，置 `false` 即可不用：

| 配置开关 | 需要的包 / 源码编译 | 说明 |
|---|---|---|
| （无开关，隐式） | **Flash-Attention**（源码编译，`MAX_JOBS=4 python setup.py install`） | 官方标注"推荐，达到全速" |
| `sparge_attention` | **SpargeAttn**（源码编译，`MAX_JOBS=16`） | 可选 |
| `liger_norm`、`liger_layernorm` | `liger-kernel` | 可选，缺失时回退融合内核 |
| `triton_rope` | `triton` | 可选 |
| （FK 工具） | **PyTorch3D**（源码编译） | 官方标注"部分 FK 工具用到" |

> **关键结论：世界模型服务端在不装任何加速内核的情况下也能跑**（`docs/installation.md` 明确写了 "runs without any of the kernels below"）。**首次部署应当先把四个开关全关跑通，再逐个打开**——三个内核都要源码编译 CUDA 扩展，是环境阶段耗时与失败率的主要来源。注意仓库自带的 `configs/gesim_v2.yaml` **默认四个开关全是 `true`**，照抄即用会直接撞上编译依赖。
>
> ⚠️ **一次实测把这条放宽了**：复现仓库 `GE-Sim-V2-tour` **只关了 `sparge_attention`**（唯一装不上的那个，`spas_sage_attn` 不在 PyPI），`liger_norm` / `liger_layernorm` / `triton_rope` 保持 `true` 并跑通了全部五个 Stage —— 完整 diff 见代码层 [`code_knowledge.md`](code_knowledge.md) **§6.1（L478–501）**，落差说明见其 **§8.4**。
> **以哪层为准**：本节仍是更保守、更省事的默认建议；`liger-kernel` / `triton` 装得上就照实测只关一个，装不上再全关。实测踩坑见 [`troubleshooting.md`](troubleshooting.md) `Q08`（liger 缺失即 500）与 `Q09`（`spas_sage_attn`）。

### 5.5 权重下载

发布的权重在 HuggingFace：**`agibot-world/Genie-Envisioner-Sim-v2.0`**

```bash
huggingface-cli download agibot-world/Genie-Envisioner-Sim-v2.0 \
    --include "checkpoints/**" --local-dir .
```

会取到**两个**检查点：

| 检查点 | 内容 |
|---|---|
| `checkpoints/gesim_community_v2.0.1_g01op_distill_2B` | 世界模型（视频主干 + pose expert，已合并） |
| `checkpoints/pi05_gesim_g01op_test` | π0.5 策略（闭环示例用） |

世界模型检查点目录是**自包含**的，内含 `model.safetensors`、`prompt_embeds.pt`、`norm_stats.json`、`vae/`、`scheduler/`（`configs/gesim_v2.yaml` 头部注释）。配置里只需指一个路径：

```yaml
checkpoint: checkpoints/gesim_community_v2.0.1_g01op_distill_2B
```

命名规范 `gesim_<channel>_v<version>_<robot+gripper>_<variant>_<size>`：上例 = community 发布、v2.0.1、Genie-01 + OmniPicker、蒸馏版、2B 主干。

> **注意 `community` 与 `v2.0.1` 两个词**：发布的是**社区版**，且版本号 `2.0.1` 与论文 v1 不是同一个交付物（见文档头「版本对齐」与 §8.4）。**没有发布非蒸馏版权重**，因此论文里"非蒸馏 vs 蒸馏"的质量对比无法在本地复现。

### 5.6 机器人模型：没有 URDF

闭环所需的 G01 运动学以**预编译库** `gesim/conditioning/_g01_fk.so` 随包发布，官方明确声明 **"no URDF or robot geometry is published"**。好处是闭环免配置；代价见 §3.7 与 §8.1 —— **无法换本体，也无法审计运动学**。回放模式（`conditioning="episode"`）完全不需要机器人模型。

---

## 6. 基本使用流程

> 本章 `[CODE]` 级。命令均为仓库根目录下的相对路径，**不含任何本机绝对路径**。
> ⭐ **只想赶紧跑起来的话，直接去速查层 [`quickstart.md`](quickstart.md) §2 运行示例（L103–197）** —— 五个 Stage 各给一条命令、预期输出、以及"结果长这样该怎么判读"。本章讲的是上游原生流程与设计意图；速查层讲的是复现仓库封装好的一键路径。要改参数则看 [`quickstart.md`](quickstart.md) §3（L198）与代码层 [`code_knowledge.md`](code_knowledge.md) §4 配置系统（L344）。
> 遇到报错请优先查排障层 [`troubleshooting.md`](troubleshooting.md) **顶部的「快速症状索引」**（按现象查到 `Qxx`，比顺序读快得多）。
>
> ⚠️ **本章的接口写法有四处最容易"按 gym 惯例想当然"而出错**，实测详见 [`troubleshooting.md`](troubleshooting.md) `Q17`：`step()` 返回 **4 元组无 `done`**；`frames` 是 `(T,3,V,H,W)`，`[:,0]` 取到的是**通道轴不是视角**（要用 `head_view_frames()`）；`RewardResult` 是 **frozen dataclass**；**没有 `--model_path` 参数**（检查点写在 YAML 的 `checkpoint:`）。
> 另外：`conditioning="action"` 下**仍会从磁盘读 4 个 `.npy`**（"闭环不消费录制轨迹"这个推断是错的），见 `Q21`。

### 6.1 三条上手路径（按投入从小到大）

| 路径 | 需要 GPU | 需要权重 | 目的 |
|---|---|---|---|
| **A. 看板预览** `python -m gesim.server --demo` | ❌ | ❌ | 验证服务框架装对了；浏览器开 `http://localhost:9000` |
| **B. CPU 冒烟** `python -m gesim.server --model example` | ❌ | ❌ | 用假模型返回**形状正确**的合成帧，跑通客户端全链路 |
| **C. 真回放 / 真闭环** | ✅ | ✅ | 见 §6.3 / §6.4 |

> **强烈建议按 A → B → C 顺序推进。** A 和 B 能把"环境问题"与"模型问题"彻底分离开 —— 这是本项目最省时间的一条工程纪律。注意 **`--demo` 会强制把 `--model` 换成 `example` 假模型**（`server/__main__.py:67-68`），看到画面动了**不代表世界模型在工作**。

### 6.2 数据格式：Episode Bundle

一切都从一个 episode bundle 目录开始（仓库自带完整样例 `assets/demo_000`）：

| 文件 | 形状 / 类型 | 用途 |
|---|---|---|
| `intrinsic.npy` | `(V, 3, 3)` | 各视角针孔内参，**烘焙在 512×384 分辨率上** |
| `extrinsic_alignstate_0.npy` | `(V, T, 4, 4)` | 逐帧 camera-to-world |
| `cur_head.png` / `cur_left.png` / `cur_right.png` | RGB | 三个相机的首帧图像 |
| `task.txt` | 文本 | 自然语言任务指令 |
| `actions_0.npy` | `(T, 16)` | 录制的**绝对关节**动作（回放用） |
| `eef_poses_0.npy` | `(T, 14)` | 动作-FK 末端位姿（**回放**条件用） |
| `state_joints_0.npy` | `(T, 20)` | 关节 `[L7, R7, L_grip, R_grip, head2, waist2]` |
| `state_eef_poses_0.npy` | `(T, 14)` | 状态-FK 末端位姿（**闭环**条件用） |

固定量：**V = 3** 视角（head / left_wrist / right_wrist）、帧 **384×512**、动作维 **16**。

> **三处易错**：① 动作是**绝对关节角**，不是增量、也不是末端位姿；② `state_joints_0.npy` 是 **20 维**（比 16 维动作多了 head2 + waist2 四个被"held"的关节），FK 就是靠这 4 个补齐的；③ `eef_poses_0.npy` 与 `state_eef_poses_0.npy` **都是 (T,14) 但用途不同**（前者回放、后者闭环），拿错不会报错。

### 6.3 回放（开环评测）

回放用**录制好的动作**驱动世界模型，把预测视频与真实机器人做对照。**不涉及策略**。

```bash
# 终端 1：世界模型服务
MODEL=gesim_v2 CONFIG=configs/gesim_v2.yaml bash scripts/serve_world_model.sh

# 终端 2：回放
python examples/replay.py --server http://localhost:9000 \
    --episode assets/demo_000 --output-dir outputs/replay
```

常用参数：`--max-frames N`（只放前 N 个动作，`0` = 整条）、`--chunk-size 25`、`--fps 16`。

产出：

| 文件 | 内容 |
|---|---|
| `video.mp4` | 完整 rollout，三视角横向拼接 |
| `state.npy` | `(T, 16)` Pose-Expert 预测状态（WM 布局） |
| `reward.npy` | `(T,)` 逐帧成功概率 —— **仅当挂了 reward client 才有** |
| `metrics.json` | 任务、帧数、平均分块耗时、最终 reward |

回放固定用 `conditioning="episode"`（训练同分布的位姿带），这是回放的**正确选择**。

### 6.4 闭环 rollout（策略评测）

策略看当前观测 → 出动作块 → 世界模型渲染下一段画面 → 画面成为新观测。**没有物理机器人参与。**

```bash
# 终端 1：世界模型服务
MODEL=gesim_v2 CONFIG=configs/gesim_v2.yaml bash scripts/serve_world_model.sh

# 终端 2：π0.5 策略服务（在 openpi 环境里）
OPENPI_CKPT=checkpoints/pi05_gesim_g01op_test bash scripts/serve_policy_pi05.sh

# 终端 3：闭环
python examples/closed_loop.py --server http://localhost:9000 \
    --policy ws://localhost:8000 --episode assets/demo_000 --steps 8
```

一轮循环做的事（`docs/closed_loop.md`，代码对应 §3.6）：

1. `policy.infer(obs)` 返回 `(horizon, 16)` 关节空间动作块，**默认 50 行**，布局 `[L7_arm, L_grip, R7_arm, R_grip]` —— **不是末端位姿**。
2. `env.step(actions)` 默认把它压成**一块 25**（或 `compress_actions=False` 时切成多个 25 的子块）。
3. 经 FK 渲染位姿带：**head 相机保持 episode 录制的安装位，两个腕部相机跟随 FK 推出的手臂运动**。
4. 世界模型出 `(T,3,V,H,W)` 帧 + Pose-Expert 状态。
5. 用**最后一帧**和状态构造下一个 `Observation` 喂回策略。

### 6.5 `compress_actions`：一个必须自觉的取舍

| 取值 | 行为 | 每回合 WM 推理次数 | 时间分辨率 |
|---|---|---|---|
| `True`（**默认**） | 50 步动作压成 1 块 25 | **1 次** | 降低（25 帧/回合） |
| `False`（`--no-compress`） | 切成 2 个 25 的子块 | 2 次 | 保留（50 帧/回合） |

压缩不是简单平均：**夹爪维用最近邻采样**（保住开合时机），**手臂维保端点、内部平均池化**，与服务端预处理对齐（`docs/closed_loop.md`）。

> **这是"跑得快"与"看得准"之间的真实取舍**，且默认站在"快"那边。做定量评测、尤其涉及精细操作时序时，应当显式评估 `compress_actions=False` 的差异，而不是默认接受。

### 6.6 奖励：开箱即用时恒为 `None`

`WorldModelEnv(reward=...)` 可挂一个 `RewardClient`，挂上后 `step()` 才会返回逐帧 `success` 与 `progress`。**仓库不附带任何奖励模型实现**（`docs/replay.md`、`docs/closed_loop.md` 都明确写了 "No reward model is bundled"），要自己按 `docs/adding_rewards.md` 接。这意味着论文 §2.5 的 World Judge **在开源交付里是缺席的**，详见 §8.4。

> ⭐ **一份自建替身的完整实现与它的两个陷阱**见代码层 [`code_knowledge.md`](code_knowledge.md) **§3.3.2（L228–246）**：它把外部 VLM 当判分器，但 ① **没设 API key 时会静默降级**为"帧间平均绝对差"的非语义启发式；② **JSON 解析失败时直接返 `0.0` 且不改 `judge_source` 字段**，在报告里与真正的 0 分**完全无法区分**。这是实测中 Stage 3 得 0 % 假阴性的 `[CODE]` 级根因（[`troubleshooting.md`](troubleshooting.md) `Q35`）。**自己接判分器时，务必让"判不出来"和"判为失败"在产物里可区分。**

## 7. 常用 API 接口

> 本章全部 `[CODE]` 级，行号对应仓库快照，**行号可能随上游更新漂移**，核对方法见文末。
> 布局、时序、返回值的**语义**比行号稳定，优先记语义。

### 7.1 主入口：`WorldModelEnv`（`src/gesim/env.py`）

```python
from gesim.env import WorldModelEnv

env = WorldModelEnv("http://localhost:9000")
obs = env.reset("assets/demo_000")                  # -> Observation
obs, reward, state, info = env.step(actions)        # actions: (L, 16) 关节空间
env.save_video("rollout.mp4")
env.close()
```

**构造函数**（`env.py:51-61`）：

| 参数 | 默认 | 说明 |
|---|---|---|
| `server_url` | — | 世界模型服务地址，如 `http://localhost:9000` |
| `reward` | `None` | `RewardClient`，不给则 `reward`/`progress` 恒 `None` |
| `chunk_size` | `25` | 模型分块长度 |
| `keep_frames` | `True` | 在内存里留全部帧供 `save_video`；**约 7 MB/帧**（3×384×512），长 rollout 请设 `False` |
| `compress_actions` | `True` | 见 §6.5 |
| `user_name` | `"gesim"` | 会话标识 |
| `timeout` | `300.0` | 秒 |

**`reset(episode, task=None, *, conditioning="action")`**（`env.py:73-112`）
- `episode`：bundle 目录或已加载的 `EpisodeBundle`
- `task`：缺省取 bundle 里的 `task.txt`
- `conditioning`：只能是 `"action"`（闭环，走 FK）或 `"episode"`（回放），其余值抛 `ValueError`（`env.py:90-93`）
- 返回首个 `Observation`

**`step(actions) -> (obs, reward, state, info)`**（`env.py:114-179`）

| 返回位 | 类型 | 说明 |
|---|---|---|
| `obs` | `Observation` | 由**最后一帧**构造，供下一次策略调用 |
| `reward` | `(T,) float32` 或 `None` | 逐帧成功概率；**无 reward client 时为 `None`** |
| `state` | `(T, 16) float32` 或 `None` | Pose-Expert 预测状态，**WM 布局** |
| `info` | `StepInfo` | `.frames` `(T,3,V,H,W) float32 [0,1]`、`.progress` `(T,)` 或 `None` |

> **三条必须记住的返回值陷阱**（`[CODE]`，均已在 §3.6 出现，此处重申因为最高频）：
> 1. **是 4 元组，没有 `done`** —— 世界模型不判定回合结束，终止条件自定。
> 2. **第 3 位是 `state` 不是 `info`**。
> 3. **`state` 可能是"假的"** —— 模型不返回状态时，`env.py:171-175` 会**回退用最后一个动作**充当状态。所以"state 看起来合理"不能证明状态专家在工作；要确认请检查 `state is not None` 且与动作**不完全相等**。

**其它成员**：`env.frames`（属性，`(T,3,V,H,W)`，`keep_frames=False` 时为空）、`env.save_video(path, fps=16)`（三视角横向拼接 MP4）、`env.close()`，并支持 `with` 上下文管理（`env.py:204-208`）。

### 7.2 数据契约：`src/gesim/types.py`

```python
VIEW_NAMES = ("head", "left_wrist", "right_wrist")   # types.py:16
STATE_DIM = ACTION_DIM = 16                          # types.py:18-19
```

| 类型 | 字段 |
|---|---|
| `Observation`（`types.py:22-35`） | `images: dict[str, np.ndarray]` 各视角 uint8 `(H,W,3)` RGB；`state: (16,) float32`**策略布局**；`task: str` |
| `StepInfo`（`types.py:38-48`） | `frames: (T,3,V,H,W) float32 [0,1]`；`progress: (T,) float32` 或 `None` |

**两套 16 维布局（本仓库最容易静默出错的地方）**，`types.py:6-7`：

```
世界模型侧（动作、step 返回的 state）：[L7_arm, L_grip, R7_arm, R_grip]
策略输入侧（Observation.state）：      [L7_arm, R7_arm, L_grip, R_grip]
```

转换工具函数：

| 函数 | 作用 |
|---|---|
| `wm_state_to_policy_state(state)`（`types.py:72-82`） | WM 布局 → 策略布局；**只有两个夹爪维在动**。⭐ **新写代码请用这个函数，不要手写重排** —— 一次实测的复现仓库**绕开了它**，在两个文件里各手写了一份**逐行相同**的重排（[`code_knowledge.md`](code_knowledge.md) §7.2 `S3` / §8.2），这正是教训 `L06`「一个常量被多方消费必须单点定义」的由来；用错的表现是**不报错、只是行为错**（[`troubleshooting.md`](troubleshooting.md) `Q36`） |
| `frame_to_view_images(frame)`（`types.py:51-60`） | 一帧 `(3,V,H,W)` float → 三个 uint8 HWC 图的 dict |
| `head_view_frames(frames)`（`types.py:63-69`） | `(T,3,V,H,W)` → head 视角 `(T,H,W,3)` uint8（喂奖励模型用） |

### 7.3 三个扩展点

**① 世界模型** —— 继承抽象类 `WorldModel`（`models/base.py:29-60`），并在 `_REGISTRY` 注册（`models/base.py:64-67`）：

```python
class WorldModel(ABC):
    chunk_size: int = 25
    @classmethod
    def from_config(cls, config: dict) -> "WorldModel": ...
    def reset(self) -> None: ...
    def set_camera_params(self, intrinsic, extrinsic=None) -> None: ...   # (V,3,3) / (V,4,4)
    def set_episode_data(self, first_frame) -> None: ...                  # (3,V,H,W) float [0,1]
    def set_episode_traj(self, traj, c2w) -> None: ...                    # (3,V,T,H,W) / (V,T,4,4)
    def set_task(self, task: str) -> None: ...                            # 可选，默认 no-op
    def step(self, actions) -> StepResult: ...                            # (L<=chunk_size, 16)
```
`StepResult`（`models/base.py:16-26`）= `frames (T,3,V,H,W)` + `state (T,D)` 或 `None`。
现有注册项：`example`、`gesim_v2`。查询用 `available_world_models()`。

**② 策略** —— 实现 Protocol `Policy`（`policies/base.py:12-23`）：

```python
class Policy(Protocol):
    def reset(self) -> None: ...
    def infer(self, obs: Observation) -> np.ndarray: ...   # -> (horizon, 16)，WM 布局
```
> 注意**输入 `obs.state` 是策略布局、输出动作要求 WM 布局** —— 一进一出布局不同，是本接口的固有别扭之处。

**③ 奖励** —— 实现 Protocol `RewardClient`（`rewards/base.py:24-30`）：

```python
class RewardClient(Protocol):
    def evaluate(self, head_frames: np.ndarray, task: str) -> RewardResult: ...
```
输入 `(T,H,W,3)` uint8 **仅 head 视角**；`RewardResult`（`rewards/base.py:11-22`）= `success (T,)` + `progress (T,)`。
> **只喂 head 单视角**是硬约束：想用腕部视角做判定，得自己改 `env.py:168` 那行。

### 7.4 服务端 HTTP 接口（`src/gesim/server/app.py`）

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/init` | 建会话，返回 `client_id`；**其余接口都要带它**（`app.py:176-179`，未 init 抛 `PermissionError`） |
| POST | `/reset` `/set_task` `/set_camera_params` `/close` | JSON 端点 |
| POST | `/set_episode_data` `/set_episode_traj` | 二进制端点（`set_episode_traj` 客户端侧 timeout 放宽到 **600 s**，`transport.py:105`） |
| POST | `/step` | 二进制，返回帧 + 状态 |
| GET | `/healthz` | 健康检查 → `{"status": "ok"}`（`app.py:203`） |
| GET | `/` `/api/status` `/api/preview.jpg` | 实时看板、状态 JSON、帧预览图 |

启动器 `server/__main__.py`：`--model`（默认 `gesim_v2`）、`--config`（`gesim_v2` **必填**）、`--host`（默认 `0.0.0.0`）、`--port`（默认 **9000**）、`--demo`。

> **π0.5 策略服务没有 HTTP 健康检查端点** —— 它是 WebSocket（默认 **8000**）。想确认它活着，只能尝试连接，不能 `curl /healthz`。这是排查"闭环卡住"时的常见盲区。

### 7.5 正运动学：`CompiledKinematics`（`conditioning/kinematics.py`）

```python
left, right = CompiledKinematics().fk_action(action16, head_waist4)
# 各返回 (7,) = [x, y, z, qx, qy, qz, qw]，scalar-last 四元数
```
- 输入：16-D 动作 + **4 个被 hold 的头/腰关节**；维度不符抛 `ValueError`（`kinematics.py:40-41`）
- 机器人几何、关节布局、动作→关节映射**全部编译在 `_g01_fk.so` 里，无源码**
- 加载失败抛 `OSError`，报错文案已提示"为特定平台（linux x86_64）构建"（`kinematics.py:23-27`）

### 7.6 配置文件字段（`configs/gesim_v2.yaml`）

| 字段 | 示例值 | 说明 |
|---|---|---|
| `checkpoint` | `checkpoints/gesim_community_v2.0.1_g01op_distill_2B` | 自包含检查点目录 |
| `device` | `cuda` | |
| `dtype` | `bfloat16` | |
| `num_inference_steps` | `4` | **蒸馏后的步数**（§2.6） |
| `distilled_sampling` | `true` | |
| `distill_sigma_schedule` | `[1.0, 0.9375, 0.8333, 0.625]` | 四步 sigma 表 |
| `liger_norm` / `liger_layernorm` / `triton_rope` / `sparge_attention` | 均 `true` | **四个加速开关，默认全开**；无对应包时需手动置 `false`（§5.4） |

> **行号核对方法**：本章行号若与实际不符，用 `grep -n 'def step\|def reset\|VIEW_NAMES\|class WorldModel' src/gesim/*.py src/gesim/**/*.py` 重新定位，并顺手修正本节与项目级 `00-index.md` 的行号表。

## 8. 已知问题与限制

> 本章是全文档**工程决策价值最高**的一章。它把三类东西分开：论文自述的限制（§8.1）、我在核对中发现的**证据矛盾**（§8.2）、范式本身决定的能力边界（§8.3）、以及**论文与开源交付之间的落差**（§8.4）。
> 实践中遇到的具体故障请查排障层 [`troubleshooting.md`](troubleshooting.md)（`Q01`–`Q45`，六类，顶部有快速症状索引；**F 类 `Q42`–`Q45` 是「平台契约与判分口径」，不报错但结论会错**）；决策与教训的复盘见经验层 [`ai_knowledge.md`](ai_knowledge.md)（`P01`–`P45` / `D01`–`D20` / `L01`–`L09`）。
>
> 📌 **本章的几条限制已被实践具体量化，引用时建议一并带上实测数字**（全部 `[实践]` 级，来自 2026 年 7–8 月一次五阶段复现）：
>
> | 本章的论断 | 实践给出的数字 | 出处 |
> |---|---|---|
> | §8.2 矛盾 1：帧数口径 | 闭环 wallclock 实测仅 **0.88 帧/s**（约 **0.055× 实时**）；纯仿真 + VLA 约 3.2 帧/s；瓶颈是**世界模型的视频扩散本身** | `ai_knowledge.md` §1.1 |
> | §8.2 矛盾 2：RL 口径 | 论文列为未来工作是对的 —— 实测**必须自己搭**：LoRA 路线整个不成立（`Q24`）、流匹配**没有闭式概率密度**故无法做 policy gradient（`Q25`），最终用 **RWR** 才跑通，留出集 OSR **30 % → 80 %** | `Q24` `Q25`、`ai_knowledge.md` `D11` |
> | §8.4 落差：奖励模型缺席 | 实测用外部 VLM 顶替可行，但要处理"HTTP 200 而 content 为空"（推理型模型的思维链吃光 token 预算，`Q18`）与 `RewardResult` 是 frozen dataclass（`Q17`） | `Q17` `Q18` |
> | §8.4 落差：无训练代码 / 单本体 | **跨机型零样本迁移实测得 0 分**，且已通过审计确认**不是管道故障**（同链路换官方权重得 0.745 / 0.604）—— 根因是目标机型静息位形落在训练分位之外、夹爪量纲错位 | `Q40` |
> | §8.5 第 1 条：两套 16 维布局 | 线上实测存在**三套**（模型输入 / 服务端输出 / 平台包络），用错**不报错只是行为错**，必须用 `wm[j]=j` 单测钉死 | `Q36` |

### 8.1 论文自述的限制 `[PAPER]`

出自论文 "Looking Forward" 一节：

| # | 限制 | 影响 |
|---|---|---|
| 1 | **固定单一本体** —— 只在 Genie-01 + OmniPicker 上训练与验证 | 换机器人 = 重训；且开源侧连 FK 都是编译死的（§5.6） |
| 2 | **评判器是外挂的，未与世界模型统一** | success/progress 与画面生成不共享表征，可能各说各话 |
| 3 | **只做了离线过滤式行为克隆（filtered BC）** | 论文**没有**演示任何在线 RL |
| 4 | **只验证了单一 VLA 策略族**（π0.5 系） | 对其它策略族的适配性未知 |
| 5 | **2B 主干是核心瓶颈** | 画质、长时一致性、指令遵循的上限都受此限 |

### 8.2 证据矛盾与可复现性问题（**核对中发现，请务必知悉**）

这四条是我在交叉核对论文、官网、公众号文章与开源仓库时发现的**实打实的不一致**。引用本项目任何数字前先看这里。

#### 矛盾 1：同一篇论文里"2.3 秒"对应的帧数差 4 倍（**已查清，是措辞问题**）`[PAPER]`

| 出处 | 说法 |
|---|---|
| 摘要 | 单张 H100 上 **25 帧** rollout 耗时 2.3 秒，外加"推理时最多 **4× 跳帧**" |
| §3.5 末段 | 单张 H100 上 **100 帧** rollout 约 2.3 秒，仅需四步推理 |

**结论：不是笔误，也不是两次不同的测量，而是 §3.5 把"覆盖的时间跨度"写成了"帧数"。**

依据是 §3.5 自己的上一段原话：随机步长训练使模型在推理时可以跳帧，**"用同样数量的帧覆盖至多四倍的时间跨度"**（"covering up to four times the time span with the **same number of frames**"）。也就是说：

```
实际生成帧数 = 25   （四步推理，2.3 秒）
4× 跳帧后覆盖的时间跨度 ≈ 100 帧之久
§3.5 末段把后者说成了 "100-frame rollout"
```

> **`[CODE]` 佐证 25 是真实生成帧数**：`models/base.py:32` 的 `chunk_size = 25`、`env.py:58` 默认 `chunk_size=25`、`docs/closed_loop.md` 明确"50 步动作压成一块 25"。
>
> **引用规范**：写 **"单 H100、四步推理、2.3 秒生成 25 帧；配合 4× 跳帧可覆盖约 100 帧的时间跨度"**。**不要单独引用"100 帧 / 2.3 秒"** —— 那会让人以为吞吐是实际的 4 倍。同时注意 4× 跳帧是**牺牲时间分辨率**换来的，论文自称"无明显时空一致性损失"，但这是作者自评，未见独立验证。

#### 矛盾 2：RL 能力三方口径不一致（**最容易被误导的一条**）

| 来源 | 等级 | 说法 |
|---|---|---|
| 公众号中文介绍 | `[文章]` | "内置激励模型……**可以完成强化学习（RL in World Model）**"、"支持 Eval in WM、**RL in WM**、Teleoperation in WM 都可以直接在模型世界中完成" |
| 官方项目页 | `[官网]` | 只提 **"Close-loop Learning"**，**未点名 RL** |
| 论文 | `[PAPER]` | RL 列在**未来工作**里；正文只演示**离线过滤式 BC** |

**以论文为准：RL 在本版本中不是已交付能力。** 公众号是营销材料，把"具备奖励信号"直接讲成了"能做 RL"。若你的计划依赖"在世界模型里跑 RL"，请按**需要自行实现**来估工作量，且注意 §8.4 —— **连奖励模型本身都没开源**。

#### 矛盾 3：Table 1 的 "Open-source ✓" 需要打折 `[PAPER]` vs `[CODE]`

论文 Table 1 把 GE-Sim 2.0 标为开源。核对仓库后的准确表述是**部分开源**：

| 组件 | 是否发布 |
|---|---|
| 推理侧模型实现（DiT / VAE / 调度器 / pose expert / raymap） | ✅ 已发布，约 8 200 行 |
| 世界模型权重（**蒸馏版**，社区版 v2.0.1） | ✅ HuggingFace |
| π0.5 策略检查点 | ✅ HuggingFace |
| 客户端 / 服务端 / 示例 / 文档 / 测试 | ✅ |
| **训练与蒸馏代码、数据管线** | ❌ 未发布 |
| **非蒸馏版权重** | ❌ 未发布（故论文的蒸馏前后对比无法本地复现） |
| **World Judge（奖励模型）实现或权重** | ❌ 未发布，只有 `RewardClient` 协议 |
| **机器人 URDF / 几何** | ❌ 未发布，FK 是编译好的 `.so` |

> 这比我最初的预判要好（仓库**不是**瘦客户端），但离"完全开源"仍有距离。**它是一个可用的推理发行版，不是一个可复现的研究发行版。**

#### 矛盾 4：结论里的 "1 pp" 在实验章找不到出处 `[PAPER]`

**结论段原话**：闭环成功率与真机 **"agree with the real robot within 1 pp"**（相差 1 个百分点以内）。

**但 §4.2 通篇没有这个数字。** §4.2 实际报告的是两件事：

| §4.2 报告的 | 具体内容 |
|---|---|
| 任务级对齐（Figure 8 散点图） | **纯定性描述**："拟合趋势斜率接近 1、带一个小的负偏移" —— **没有给任何数值**，没有给斜率值、截距值或平均绝对偏差 |
| Episode 级一致性（Figure 10 混淆矩阵） | accuracy **0.81**（Ctrl-World 0.63 / 无状态条件 0.74）、recall **0.82**（0.25 / 0.67）；precision 未在正文给数 |

全文 grep `within 1` **仅命中结论段那一处**，`pp` 的其它出现都属于 World Judge 一节（+19 pp、+29 pp、~8 pp）与策略提升（+15 pp），与闭环成功率无关。

> **引用规范**：**不要引用 "1 pp"**。要说明闭环一致性，请引 **episode 级 acc 0.81 / recall 0.82**，并说明任务级对齐只有散点图的定性描述。
> 另需注意 §4.2 自述的局限：**接触敏感任务（拔插头、指令抓取与释放）仍有明显的假阳/假阴**，论文承认"细粒度接触状态与长时状态累积仍然困难"。**这与"1 pp"给人的印象相去甚远。**

#### 矛盾 5：**"登顶 WorldArena 榜首"这句话需要三重限定** `[PAPER]` vs `[PAPER]`

论文摘要、§1、§4.1、结论**四处**宣称 GE-Sim 2.0 "以仅 2B 参数登顶公开 WorldArena 榜单"，击败 Ctrl-World、DreamDojo、GigaWorld、ABot、Sora、Veo。核对 WorldArena 论文（arXiv:2602.08971）后，有三条必须一并知道：

**① WorldArena 论文里根本没有 GE-Sim。** 全文 grep `GE-Sim` **命中 0 次**。该论文评测的 14 个模型中，AgiBot 系只有**前代 Genie Envisioner**，且其人类评测得分"在所有维度上都显著偏低"（原文："earlier text-conditioned embodied models (e.g., Genie Envisioner) receive substantially lower scores across all dimensions"）。
→ 所以 GE-Sim 2.0 的宣称指的是**在线榜单 `world-arena.ai` 的实时排名**，不是那篇基准论文的表格。**两者不是同一份结果，不可互相引用。**

**② 对手名单对不上。** GE-Sim 2.0 列举的击败对象（DreamDojo、ABot、MotuBrain、Sora）**没有一个出现在 WorldArena 论文的评测列表里**；论文列表里的通用视频模型是 CogVideoX / Wan 2.2 / Wan 2.6 / **Veo 3.1**（无 Sora）。这进一步说明榜单在论文之后有过大幅扩充 —— **榜单是活的，名次会变，引用时必须带日期**。

**③ 最关键：WorldArena 作者自己说这个榜单分数不代表下游可用性。** EWMScore 是 6 个感知维度、16 项视频质量指标的线性归一化平均值。该论文报告的相关性是：

| EWMScore 与 | Pearson r | 论文原话 |
|---|---|---|
| 人类主观评价 | **0.825** | 强相关 |
| 数据合成表现 | 0.600 | 中等 |
| **动作规划表现** | **0.360** | **弱相关** |

原文结论：**"感知真实性是获得好评的必要条件，但并不按比例转化为下游具身任务的收益"**，尤其"与动作规划的相关性有限，说明当前合成数据尽管视觉保真度高，仍不足以为复杂具身推理提供强预测或决策信号"。

> **因此"登顶 WorldArena"主要证明的是画面质量，而不是"用它评测策略更准"。** 后一件事在 GE-Sim 2.0 论文里由 §4.2 的闭环一致性实验单独支撑（acc 0.81 / recall 0.82），**引用时不要把两者混为一谈** —— 这是本项目最容易被营销口径带偏的一处。

> **利益冲突核查（结论：无）**：WorldArena 作者单位为清华（主体）、港大、普林斯顿、中科院、中科大、北大、新加坡国立，**无 AgiBot**。基准方与被测方相互独立。

### 8.3 范式决定的能力边界（不是 bug，是"它就不干这个"）

| 你想要 | GE-Sim 2.0 能否 | 原因 |
|---|---|---|
| 物理正确的接触力/摩擦/形变 | ❌ | 没有物理引擎，画面是**学出来的似真**而非解算出来的（§2.1） |
| 新建场景、增删物体、改光照 | ❌ | 没有场景文件；一切由**首帧 + 指令**决定（§1.2） |
| 深度 / 激光 / IMU / 力矩 / 触觉 / 分割 | ❌ | **只出 RGB**；缺失清单见 §2.7.4 |
| 换相机数量或位置 | ❌ | 三视角拓扑固定（head / left_wrist / right_wrist），§2.7.2 |
| 换机器人本体 | ❌ | 单一本体训练 + FK 编译死（§5.6、§8.1） |
| 分布外场景/物体/任务 | ⚠️ 不可靠 | 生成模型只在训练分布内可信；分布外会"编"得很自然但不真 |
| 精确的绝对时间/物理量读数 | ❌ | 本体状态是**解码出的估计值**，不是传感器读数（§2.7.6） |
| 长时一致性（数百帧） | ⚠️ | 受 2B 主干与稀疏记忆限制（§8.1 第 5 条） |

> **最该记住的一句**：它擅长回答"**这个策略在这类场景里看起来会怎么动**"，不擅长回答"**这件事在物理上会不会成功**"。把它当成**策略行为的视觉预演器**，而不是真值来源。

### 8.4 论文与开源交付的落差（部署前必读）

| 论文里有 | 开源仓库里 | 后果 |
|---|---|---|
| World Judge 评判器（§2.5） | **只有 `RewardClient` 协议，无实现无权重** | **开箱即用时 `reward` 与 `progress` 恒为 `None`**；想要成功率判定必须自己接一个模型 |
| 蒸馏前后质量对比（§2.6） | 只发布蒸馏版权重 | 无法本地复现该对比 |
| 训练/微调流程 | 无训练代码 | **无法在自己的数据上训练或微调**；只能推理 |
| 多本体展望 | FK 编译为 `.so`，无 URDF | 无法换本体，也无法审计运动学 |
| 版本 | 论文 v1（2026-05-26）vs 权重 `community v2.0.1` | **不是同一交付物**，论文数字不必然在发布权重上复现 |

> **"没有奖励模型"是本项目最容易低估的一条落差。** 论文把"自带奖励信号"作为相对其它世界模型的**核心差异化能力**（§4.1 Table 1 中 Reward 是近乎独占的一列），但这一列对应的东西**没有随代码发布**。任何"用 GE-Sim 2.0 做自动评测"的计划，都必须把"自己实现或外接一个评判器"算进工作量。

### 8.5 工程侧注意事项汇总 `[CODE]`

按踩坑概率排序，细节见前文对应章节：

| # | 事项 | 见 |
|---|---|---|
| 1 | **两套 16 维布局不同**（夹爪维位置），弄反**静默失效** | §3.5、§7.2 |
| 2 | **依赖除 `torch>=2.0` 外全无版本约束**，建议自行冻结并单独开环境 | §5.3 |
| 3 | **配置默认四个加速开关全开**，但内核需源码编译；首次部署应全关 | §5.4 |
| 4 | `--demo` / `--model example` **是假模型**，画面动了不代表世界模型在工作 | §6.1 |
| 5 | **`conditioning="episode"` 是回放不是闭环**，策略随机画面也照走原轨迹 | §3.7 |
| 6 | `step()` 返回 **4 元组、无 `done`**，第 3 位是 `state` | §7.1 |
| 7 | **`state` 有回退逻辑**（模型无状态时拿动作充数），不能作为状态专家工作的证据 | §7.1 |
| 8 | `compress_actions=True`（默认）**牺牲时间分辨率换速度** | §6.5 |
| 9 | **忘 `--recursive`** → openpi submodule 为空，策略侧全链路装不起来 | §5.1 |
| 10 | `openpi-client` **需单独安装**，否则 `OpenPIPolicy` 抛 `ImportError` | §5.2 |
| 11 | **π0.5 服务是 WebSocket，无 `/healthz`**，排查"闭环卡住"时易成盲区 | §7.4 |
| 12 | `keep_frames=True`（默认）约 **7 MB/帧**，长 rollout 会吃爆内存 | §7.1 |
| 13 | `_g01_fk.so` **仅 linux x86_64**，其它平台闭环直接不可用 | §5.6 |
| 14 | `pin`（pinocchio）是**基础依赖**，部分平台安装不顺 | §5.3 |
| 15 | `networks/`、`pipelines/`、`schedulers/` 等被 **lint 豁免**（逐字搬运的数值敏感代码），改动无格式化保护 | §3.4 |
| 16 | **`Real2Edit2Real` 有两处会当场卡住首次运行**：`tools/preprocess_demo.py` 的 API key 是占位符且无环境变量路径；三个 run 脚本默认指向一个**不存在的 config** | §9.2 |
| 17 | **R2E2R 的 Metric-VGGT 依赖 `facebook/VGGT-1B`（CC-BY-NC-4.0，非商用）**，且按上游脚本微调需 80 GB 级显存 —— 40 GB 卡上**只能做推理与数据生成** | §9.2、`ai_knowledge.md` §7.2 |
| 18 | **RoboColiseum 的引擎是 GenieSim 3.0，不是 GE-Sim 2.0**；且选手**不上传策略**，是平台反向拨号连你的 agent | §9.3.1–§9.3.2 |

> ⚠️ **除了上面这些"设计与文档层面的坑"，还有一类坑只在真跑起来才暴露：外部契约与自己数字的口径错误。** 它们不报错、程序照跑，只有把实测数字重算一遍才会发现 —— 见 [`ai_knowledge.md` §4.6 F 类](ai_knowledge.md)（`P42` 榜单总分是均值不是求和 / `P43` 计划里的任务数与拆分是想象出来的 / `P44` `result` 接口要数字 id / `P45` Z 轴分析维度在配置层面就不成立）与 [`troubleshooting.md` `Q42`–`Q45`](troubleshooting.md)。

## 9. 参考资源

### 9.1 一手资料（本文档的证据来源）

| 资源 | 等级 | 说明 |
|---|---|---|
| 论文 **arXiv:2605.27491v1**《GE-Sim 2.0: A Roadmap Towards Comprehensive Closed-loop Video World Simulators for Robotic Manipulation》 | `[PAPER]` | 本文档 §1–§4、§8.1–§8.2 的主要来源。**注意 v1 与发布权重 v2.0.1 不是同一交付物** |
| 官方仓库 **`github.com/AgibotTech/GE-Sim-V2`** | `[CODE]` | §3、§5、§6、§7 全部来源。含 `docs/` 6 篇、`examples/` 2 个、`tests/` 8 个 |
| 权重 **`huggingface.co/agibot-world/Genie-Envisioner-Sim-v2.0`** | `[CODE]` | 世界模型 + π0.5 策略两个检查点（§5.5） |
| 项目页 **`ge-sim-v2.github.io`** | `[官网]` | 演示视频与宣称；口径与论文有出入处见 §8.2 矛盾 2 |
| 微信公众号《GE-Sim v2 中文介绍》 | `[文章]` | **营销材料，二手**。其"RL in World Model 已可用"的说法**与论文冲突**，见 §8.2 矛盾 2。**不可作为工程依据** |

> **仓库内最值得先读的四篇 docs**：`installation.md`（§5）、`replay.md`（§6.3，含 episode bundle 格式表）、`closed_loop.md`（§6.4，含一轮循环的精确步骤）、`adding_rewards.md`（因为奖励模型必须自己接，见 §8.4）。

### 9.2 周边项目（理解 GE-Sim 2.0 生态位）

#### WorldArena —— 评测它的基准

| 项 | 内容 |
|---|---|
| 论文 | **arXiv:2602.08971**《WorldArena: A Unified Benchmark for Evaluating Perception and Functional Utility of Embodied World Models》 |
| 榜单 | `world-arena.ai`（**活榜，名次会变，引用必须带日期**） |
| 单位 | 清华（主体）、港大、普林斯顿、中科院、中科大、北大、新加坡国立 —— **无 AgiBot，与被测方独立** |
| 构成 | 6 个感知维度、16 项视频质量指标 → 线性归一化后取算术平均 = **EWMScore**（0–100）；另有具身任务评测与人类评测 |
| 六个感知维度 | 视觉质量 / 运动质量 / 内容一致性 / **物理遵从性** / 3D 准确性 / 可控性 |
| 规模 | 评测了 **14 个**代表性具身世界模型 |

**这篇基准论文自己给出的最重要结论，恰恰是对榜单分数的限定**：

| EWMScore 与 | Pearson r |
|---|---|
| 人类主观评价 | **0.825**（强） |
| 数据合成表现 | 0.600（中） |
| **动作规划表现** | **0.360（弱）** |

> 原文：**"感知真实性是获得人类好评的必要条件，但不会按比例转化为下游具身任务的收益"**。
> **⚠️ 该论文正文中 grep `GE-Sim` 命中 0 次** —— 它评测的 AgiBot 系模型是**前代 Genie Envisioner**，且人类评测得分"在所有维度上显著偏低"。GE-Sim 2.0 的"登顶"指的是**在线榜单**而非这篇论文的表格。完整分析见 §8.2 矛盾 5。

#### Real2Edit2Real —— 建立在 GE-Sim **v1** 之上的数据生成器

| 项 | 内容 |
|---|---|
| 论文 | **arXiv:2512.19402v1**《Real2Edit2Real: Generating Robotic Demonstrations via a 3D Control Interface》，**2025-12-22** `[PAPER]` |
| 会议 | **CVPR 2026**（2026-02-21 接收）；代码与权重 **2026-03-10** 释出 `[README]` |
| 仓库 | `github.com/Real2Edit2Real/Real2Edit2Real`（121 文件，含 vendored `vggt/`、`videogen/`、`editing/`） |
| 单位 | 北大 CFCS + **PKU-AgiBot Lab** + **AgiBot**（8 位作者中 4 位是 AgiBot）—— **与 GE-Sim 同源** |
| 定位 | 通过 3D 控制界面**生成机器人演示数据**（不是仿真器，是**数据工厂**） |
| 与 GE-Sim 的关系 | **它微调的是 GE-Sim `v1`（Genie Envisioner，arXiv 2508.05635）的 2B 主干**，不是 2.0 —— 见下方版本钉定 |

##### ⚠️ 版本钉定：它消费的是 GE-Sim **v1**，且 GE-Sim 2.0 **反向零引用**

这一条容易想当然地读成"R2E2R 是 GE-Sim 2.0 生态的一环"，实际方向和版本都要更精确：

| 断言 | 证据 |
|---|---|
| 基座是 **GE-Sim-2B**，即 v1 的主干 | `[PAPER]` 论文 Table 6 `Base Model: GE-Sim-2B`；§4.1 原文"fine-tuning the backbone of GE-Sim [26] (based on Cosmos-Predict-2B)"，其中 `[26]` = Genie Envisioner (2508.05635) |
| 代码里加载的就是 v1 发布的权重 | `[CODE]` `videogen/configs/action_depth_canny_cosmos2.yaml:32` → `ge_sim_cosmos_v0.1.safetensors`，来自 ModelScope `agibot_world/Genie-Envisioner` |
| **时间上不可能引用 2.0** | R2E2R 挂 arXiv 是 **2025-12-22**，GE-Sim 2.0 是 **2026-05-28**（晚 5 个月） |
| **GE-Sim 2.0 也没有反向引用它** | `[CODE]` 在 `GE-Sim-V2/` 全仓库 grep `real2edit|r2e2r|2512.19402` **命中 0 文件** |

> **所以关系是单向的：GE-Sim v1 → R2E2R。** R2E2R 的**产出**是给 VLA 策略（Go-1、π₀.₅）和 Diffusion Policy 当训练数据，**不回流给 GE-Sim**。把它描述成"GE-Sim 2.0 的数据供给方"属于推测，**`未提及`**。

##### 三阶段管线（Real → Edit → Real）

三个阶段与 README 的三条快速开始命令一一对应 `[CODE]`：

| 阶段 | 命令 | 做什么 |
|---|---|---|
| 1 几何重建 | `bash scripts/preprocess_demo.sh --config-path configs/mug_to_basket.yaml` | Metric-VGGT 从三路 RGB 出**米制**深度与相机位姿 |
| 2 空间编辑 | `bash scripts/generate_demo.sh --config-path ...` | 点云上采样 SE(3) 变换、cuRobo 重规划、渲染新深度 |
| 3 视频生成 | `bash scripts/generate_demo_video.sh --config-path ...` | 微调后的 GE-Sim 主干按深度条件合成三视角视频 |

**输入是 1 条真机遥操 demo**（三视角 RGB + 关节角 + 动作 + URDF/相机内参），输出是 N 条换了物体摆放与轨迹的新 demo；**不需要仿真引擎、不需要数字资产、不需要稠密扫描** `[PAPER]`。

1. **Metric-scale 几何重建 —— Metric-VGGT**。在 VGGT-1B 上做**真实 + 仿真混合微调**（10 万真机 + 4 万 AgiBot-DigitalWorld 仿真帧，8×H100 / 150K 步 / **20 小时**）。三项损失的**域分配**是这一步的设计核心 `[PAPER]`：**相机损失只用仿真**（真机手眼标定被机械公差与运动学误差污染，仿真位姿来自标准 URDF 因而精确，故可直接用朴素 L1）；**深度损失两域都用**（真机有真尺度但有噪声，仿真无噪声但尺度分布偏移）；**点图损失只用仿真**。总损失 `L = λ·L_camera + L_depth + L_pointmap`，**λ = 10**。
2. **深度可靠的空间编辑（"3D 控制界面"）**。点云拆成机器人 / 物体 / 背景后采样一个随机 SE(3) 变换 **T**，轨迹按 DemoGen 的思路切成两类段：**motion 段**用 cuRobo 重新运动规划；**skill 段**把**同一个 T** 同时施加到物体**和**末端执行器点云，从而保持机器人—物体相对关系与源 demo 完全一致。三个支撑机制：**深度投影**（腕部相机刚连末端，故 T 也施加到相机位姿）、**机器人位姿校正 RPC**（不能把整个机器人当刚体平移——只有末端该动，其余连杆必须按新关节角**重渲染**，`editing/demo_generation/a2d_solver.py:337 render_link_depth_and_mask`）、**背景深度补全**（用 SeedEdit 3.0 抹掉前景后重建，并按 RANSAC 桌面平面偏移之比 `scale = plane_o[3]/plane_edit[3]` 修正图像编辑带来的尺度漂移）。
3. **3D 可控视频生成**。**从首帧出发**合成整段视频。三个关键设计：**双注意力**（视图内自注意力保细节 + 跨视图自注意力保多视角一致，比每层全局注意力便宜得多）；**深度控制界面**（深度图与图像 latent 拼接后一起进主干，辅以 Canny 边缘 / 动作图 / 光线图）；**平滑物体重定位 SOR**（直接在首帧里挪物体很难，改为在前 30 帧把物体的平移**和旋转**插值过去，把"图像编辑"问题转成"视频生成"问题，`configs/mug_to_basket.yaml:25 parsing_frames.prepare: 30`）。

**条件通道预算**在配置里逐项写明 `[CODE]` `videogen/configs/action_depth_canny_cosmos2.yaml:34`：

```yaml
in_channels: 32  # 16 (vae) + 3 (traj) + 6 (raymap) + 1 (padding mask) + depth (3) + canny (3)
```

**条件 dropout**（`:147–151`，与论文一致）：`depth_dropout: 0.5`、`canny_dropout: 0.5`、`all_dropout: 0.1`，而 `traj`/`rays` 为 0。理由值得记住：深度与 Canny 这类**强度型条件会压制其它控制信号**，而它们恰恰是空间编辑后最容易变脏的两个，故独立高概率丢弃迫使模型依赖互补证据。另：**深度归一化是"一个训练块内跨三视角全局归一"**而非逐图归一，以保证 3D 条件在视图与时间上一致（`videogen/lib/data/agibotworld_dataset.py:231`）。

##### 主结果与两条不要漏读的反例

`[PAPER]` Table 1，每格为 20 次试验的成功次数，Total 为四任务均值：

| 训练集 | Total Go-1 | Total π₀.₅ |
|---|---|---|
| Real 50 | 61.3 % | 61.3 % |
| Real 1 + Gen 200 | **65.0 %** | 57.5 % |
| Real 2 + Gen 200 | **70.0 %** | **70.0 %** |
| Real 5 + Gen 200 | **78.8 %** | **81.3 %** |

论文口径：5 条源 demo 生成的数据可超过 50 条真机 **17.5 / 20 个点**，数据效率提升 **10–50×**。**但表里有两条论文正文没讨论的反例**：

- **Lift Box 任务是例外** —— Real 1 + Gen 200 **反而比 Real 50 差**（Go-1 12 vs 15，π₀.₅ 10 vs 17）。
- **"一条 demo 就够"只对 Go-1 成立** —— π₀.₅ 在 Real 1 + Gen 200 只有 57.5 %，**仍低于 Real 50 的 61.3 %**；它需要 ≥2 条源 demo（或按 Table 8 把生成量堆到 ≥300 条）。

##### 能力边界（引用前必看）

- **抓取只被"搬运"，不被"新生成"** —— skill 段刻意复用源 demo 的机器人—物体相对关系，所以它泛化的是物体**在哪**，不是**怎么抓** `[PAPER]`。
- **编辑范围是有界的** —— 物体平移约 **40 cm × 40 cm** 方形区域内、旋转 **30°–60°** 范围内，工作台本身是 50 cm × 40 cm。
- **腕部相机必须刚连末端** —— 整个深度投影步骤依赖"把物体变换同样施加到相机位姿"。
- **RPC 不是可选项** —— 去掉它深度图在运动学上就是非法的，生成结果模糊且不一致。
- **铰接物体建模不好**（论文自陈的唯一局限），归因于视频生成训练数据里铰接物体太少。
- **四个消融全是定性图，没有一个给出数字** `[PAPER]`。

##### 安装侧最硬的一条约束 `[CODE]`

`requirements.txt` 51 行里 43 行是 `==` 精确 pin，其中**两个硬编码的平台专用 wheel URL** 是整个安装里最不可绕的：`pytorch3d-0.7.8-cp310-cp310-linux_x86_64.whl`（`py310_cu121_pyt251`）与 `torch_scatter-2.1.2+pt25cu121-cp310-...whl`。两者合起来把环境**锁死在 Linux x86_64 + Python 3.10 + CUDA 12.1 + torch 2.5.1**，任何偏离都在安装期失败。

两个 README 没写、但首次运行必然撞上的坑：

1. **`tools/preprocess_demo.py:43` 的图像编辑 API key 是占位串**，且**没有环境变量通路**——预处理第 3 步（SeedEdit 背景 inpaint）要求把凭据**硬写进源文件**。跑不通该服务就只能跳过第 3 步（`--steps 1245678`）另行提供背景。**本次复现正是在这里打了 patch，见 `code_knowledge.md` §6.2.1。**
2. **三个运行脚本的默认 `config_path` 指向一个仓库里不存在的文件**（`configs/mug_to_box_1654490_bs60.yaml`），实际只有 `mug_to_basket` / `pour_water` / `lift_box` / `scan_barcode` 四个，**所以 `--config-path` 实际是必传的**。

##### 其它可复用事实

训练用 AgiBot-World 的 **7K episodes / 64 任务**；硬件为 **AgiBot Genie G1，头部 + 左右腕三个 RGB 相机**（**与 GE-Sim 2.0 完全相同的三视角拓扑**）；训练分辨率 **384×512**、chunk 25、memory 4（**与 GE-Sim 2.0 同规格**）；8×H100 并行下生成一条 20 秒 / 30 FPS 的 episode 约 **48.6 秒**，而**生成管线本身单卡 RTX 4090 即可跑**、训练才需要 80 GB 卡；运动规划用 **cuRobo**（`third-party/curobo` 子模块，pin 在 `d64c4b0`，因 CUDA 编译脆弱而单列一个安装脚本）。

> ⚠️ **论文与随仓脚本的一处矛盾** `[CODE]`：`vggt/train.sh:11–12` 把 `LR` 与 `LR_BACKBONE` **都设成 2e-5**，而论文 Table 5 写的是 LR **2e-4** / backbone 2e-5。**释出的脚本复现不出论文陈述的学习率**；另 `GRAD_WEIGHT=1` 是第四个损失项，论文 Eq. 5 里没有对应物。

> **生态位小结（已按证据修正）**：`Real2Edit2Real` **消费 GE-Sim v1 的主干**来造数据（单向，2.0 未反向引用）；`WorldArena` **评测** GE-Sim 这类模型（但其论文正文 grep `GE-Sim` 命中 0）；`RoboColiseum` 是 **GenieSim 3.0** 的托管评测平台，**与 GE-Sim 2.0 无文档层面的关系**（见 §9.3，该结论已推翻本节旧版"基于 GE-Sim 的盲测平台"的说法）。**三者并不构成一个围绕 GE-Sim 2.0 的闭环** —— 它们只是同一家公司周边、各自独立的三个项目。

### 9.3 RoboColiseum 挑战平台

> ⛔ **本节旧版有两处事实错误，已在此推翻**。旧版写"基于 GE-Sim 世界模型的**线上策略盲测平台**：选手**提交策略**，在**托管的世界模型**里跑闭环并排名"——**引擎错了，架构方向也错了**。正确说法见下两小节。若在别处看到旧表述，**以本节为准**。

#### 9.3.1 它不是 GE-Sim 的平台，而是 GenieSim 3.0 的平台

三条相互独立的证据都指向同一结论：

| 证据 | 内容 |
|---|---|
| 上游 README 明说 | `[README]` `genie_sim/README.md:103`："**The Genie Sim Benchmark is the engine behind RoboColiseum**"；`:105` 列出四个榜单 `instruction`/`robust`/`manip`/`spatial` |
| skill 包里 GE-Sim **零命中** | `[SKILL]` 12 个 `challenge-*` 文件（1516 行）中，`GE-Sim`、`2.0`、`WorldArena`、**`world model`** 全部 **0 次出现**；唯一版本串是 **GenieSim 3.0** |
| skill 包**物理上就住在 genie_sim 仓库里** | `[CODE]` 这批 skill 的可引用副本在 `genie_sim/source/geniesim_benchmark/skills/robocoliseum/`（10 个目录）；对该目录 grep `ge-sim\|gesim\|world.model\|worldarena` **命中 0 文件** |

**推论**：评测过程是一个**仿真器**在步进机器人并吐相机 JPEG，**没有任何学习到的动力学、视频生成或生成式 rollout 参与**。RoboColiseum 与 GE-Sim 2.0 之间**在文档层面不存在关系**，二者的唯一交集是同属 AgiBot 周边。

> **榜单、任务数与基线分数已由 `genie_sim_v3` 项目覆盖**（`knowledge/projects/genie_sim_v3/background_knowledge.md` §3.5，含四榜 + Sim2Real 非竞赛表、任务数、π₀.₅ / ACoT-VLA / GR00T-N1.7 / π₀ 的成功率）。**本节不重复这些事实**，只写本次复现实际消费到的**平台契约**，以及**文档契约与线上实测的偏差**（§9.3.5）。
>
> 顺带收口一个悬案：本次 Stage 5 的计划文本反复出现"**78 个标准化任务**"，复现过程中因无法证实而**把它判为"未经验证数字"并弃用**（`ai_knowledge.md` `P43`）。用 `genie_sim_v3` §3.5 的 `[CODE]` 表回算，四个竞赛榜任务数 **10（instruction）+ 50（robust）+ 10（manip）+ 8（spatial）= 78**，与该数字吻合；而**本次实测 instruction 与 manip 各 10 个任务**，也与该表逐项一致。**所以"78"这个总数本身是对的，错的是计划里"四榜各 20/20/20/18"的拆分**。引用时请以 `genie_sim_v3` §3.5 为出处，不要引用计划文本。

#### 9.3.2 架构是**反向**的：选手不上传模型

这是整套契约里最容易想错的一条 `[SKILL]`：

```
平台侧：跑仿真器（GenieSim 3.0），持有场景与任务
选手侧：在自己的 GPU 上跑自己的策略服务
连接：平台通过 WebSocket 隧道 **反向拨入** 选手的 agent
```

- **提交体里没有模型产物** —— `POST /api/challenge/job` 的 body 是 `{name, config:{board, model_name, description}}`，其中 `model_name` **只是榜单上的一个标签，不是权重引用**（历史上的 `model_path` 字段已被移除）。
- **隧道网关是一个与官网不同的固定主机** —— 默认 `TUNNEL_ENDPOINT = ws://<GATEWAY_IP>/api/challenge/tunnel`。**不要"顺手把它改成官网域名"**，那是本契约里被专门警告过的一种错误修复。
- 并行度由服务端下发（响应里的 `parallelism`），选手按 `K = min(本地 GPU 数, parallelism)` 起 agent。

**八步工作流** `[SKILL]`：下载数据集 → 起基线 → 登录取 JWT → **查配额** → 提交 job → 在自己 GPU 上起 agent 拨隧道 → 轮询结果（2–5 s）→ 看榜单。其中第 4 步不可省：**每次 POST 前都要 `GET /submission/quota`**，因为"没有任何可信的会话内计数器"，返回形如 `{limit:4, used:1, remaining:3}`。

#### 9.3.3 推理协议要点

| 项 | 内容 `[SKILL]` |
|---|---|
| 观测编码 | msgpack JSON-RPC 信封，用 **`msgpack_numpy.unpackb`** 解 |
| 相机 | `head` **400×640**（分辨率最低的那个）、`hand_left` / `hand_right` 各 1056×1280；均为 **JPEG 字节**，需 `cv2.imdecode` 后 **BGR→RGB** |
| 深度 | schema 里有字段但**被注释掉、实际不下发** |
| 机器人 | `G2_omnipicker`：双臂 7+7、腰 5 自由度、双夹爪；**头部关节 0 维** |
| 状态拼装 | `state = concat(arm_joint_states[14], gripper_states[2], waist_joint_states[5])` = **21 维**，顺序 `joint, left_effector, right_effector, waist`；推理期无 `info.json`，故 `state_indices=None`，**必须由 agent 自己交出已排好序的向量** |
| 动作块长度 | **H = 50**（`instruction` / `spatial`）、**H = 30**（`manip`） |
| 动作切片 | `0:7`→左臂，`7:14`→右臂，`14:15`→左夹爪，`15:16`→右夹爪，`16:`→腰（仅当 D>16） |
| 生命周期 | `WARMUP → RUNNING`，**warmup 那一次传的是空帧** —— handler 必须在 `len(frame_bytes)==0` 时短路返回空动作，否则永远卡在 WARMUP |

**动作信封有一处结构性不对称，极易写错**：双臂与腰被包成 `{kind, values}`（`kind` 为 `JOINT_ABS` 或 `EEF_ABS`，左右必须一致），而**两个夹爪是裸的嵌套列表、没有 `kind` 包装**。

> 🔥 **本节最高价值的单条事实 —— plain-msgpack 陷阱** `[SKILL]`：**输入用 `msgpack_numpy` 解，输出却必须用 plain `msgpack`（`raw=False`）能解**。genie-sim 侧不是用 `msgpack_numpy` 解包的，所以直接打包 numpy 数组会以 ext 编码抵达、`np.array(values)` 就地崩坏。**打包前必须把每个数组 `.tolist()` 成原生 Python 列表**。注意失败形态：**你这侧不抛异常，是仿真侧静默拿到垃圾**——这正是本范式典型的"不报错的失败"。

#### 9.3.4 提交、评分与配额规则

- **`board` 是四元闭集** `instruction` / `spatial` / `manip` / `robust`，服务端三处校验。传错值返回 `400 invalid board`（或 `400 no task templates for board`）**并照扣配额**；**4xx 是语义拒绝，不要重试**。
- **一次提交 = 一个 board = 一个 job**，所以跑满四个榜要提交四次。
- **配额**：skill 文档写 **4 次/天**、北京时间午夜（UTC+8）重置 `[SKILL]`；但**本次两轮独立实测 `GET /submission/quota` 均返回 `limit: 99` 总量口径** `[实践]`（§9.3.5 漂移表第 4 行）。**以实测为准，但仍按"提交昂贵"操作**。
- **分数语义：skill 文档说是"和"，实测是"均值"** —— 文档写 `task total = 各 episode 之和`、`job total = 各 task total 之和` `[SKILL]`；而实测 manip 十任务分数之和 6.04、平台报 **0.604**，instruction 之和 7.46、平台报 **0.745**，**除以任务数后与平台报数精确吻合（误差 ≤0.001）** `[推算]`（`P42`）—— ⚠️ 这是**从两组数字反推**，平台从未公布算法；且两个样本恰好都是 10 任务，故"除以任务数"与"除以 10"**无法区分**，**不要反向用它还原分项和**（见 `troubleshooting.md` `Q42`）。**引用总分语义时以实测的"均值"为准**；跨 board 比较仍只在同一 board 内有意义。`genie_sim_v3` §3.5 记录的 0–1 成功率与该均值同量纲。
- **榜单按 board 分列、没有全局总榜**，每行是某用户在该 board 上的最好一次 job；**响应里没有 `rank_change` 字段，不要编造排名变化**。
- 状态机：文档写 `Pending / Queued / Running / Finished / Failed / Cancelled` `[SKILL]`，**实测在 agent 连上后还有一个 `evaluating` 态、终态是 `completed`/`failed`** `[实践]`（`P38`）——轮询器的 ACTIVE 集合漏掉 `evaluating` 会**把正在跑的 job 误判为终态**。失败日志是容器 stdout/stderr + exit code，定位顺序为"最终 exit_code → 最后一段完整 Traceback → 周围约 20 行 stderr"。

**两条跨条目的排障启发式** `[SKILL]`，与本库的通用纪律完全同构：

1. **"4xx 从来不是网络抖动"** —— 手上拿着 4xx 结构化错误体时不要接受"可能是网络问题"的解释，重试只会烧配额；只有 curl 层失败和 5xx 才可能是瞬时的。
2. **"5xx 往往是 token 缺失或错误"** —— `curl -fsS` 会把 5xx 折叠并隐藏响应体；排查顺序是确认状态文件已 source → 检查 token 长度非 0 → 检查 JWT 是否三段式 → **去掉 `-f` 看响应体**（常见情况是"用 500 状态码返回的 401 类消息"）。

另有若干专属失效形态：agent 连上就立刻断开 = 撞到并行度上限；job 卡在 Pending = 没有 agent 在线或已掉线超过 **30 秒**重连窗口；**运行中掉线时 SDK 会用同一 `agent_id` 在 30 秒内自动重拨，此时手工重启会与 SDK 竞争**；收到 `drain` 控制帧应让在途请求跑完并**不要重连**；响应里 `parallelism: 0` 是服务端配置错误（**不是配额耗尽**），应停手上报而非硬起 agent。

#### 9.3.5 ⚠️ 文档契约与线上 API 的 6 处漂移

**这是本节最该先读的一张表** `[实践]`。本次复现的结论是一条清晰的分工：**skill 是协议层的权威**（wire 格式、状态字段布局、生命周期——照它写一次通过，线上 8994 帧零协议失败），**但 HTTP API 层必须用 curl 实测校准**。正确姿势是"先读 skill 拿协议，再用两条只读命令（`GET /jobs`、`GET /current-user-info`）实测校准 API，然后才动手写代码"。

| # | skill 文档说法 `[SKILL]` | 线上实测（2026-08）`[实践]` |
|---|---|---|
| 1 | 登录可 `GET` + urlencode | `GET` → **405**；`POST` form → **400**；email 带尾随空白 → `user not found`；**只有 `POST` JSON + `email.strip()` → 200** |
| 2 | `BASE_URL` = `https://robocoliseum.ai` | 实际是 **`http://<GATEWAY_IP>`**（与官网**不同主机**，也不是 https） |
| 3 | 给出两条官方 SDK 启动路径 | **两条都不存在，SDK 未发布** |
| 4 | 配额 4 次/天 | **`limit: 99` 总量**（两轮独立实测） |
| 5 | `/job/<id>/result` 的 `<id>` | 必须传**数字 id**；传 uuid → **500 `invalid job_id`**。须先 `GET /api/challenge/jobs`（响应键是 **`items`**）拿 `items[].id` ← `items[].job_uuid` 的映射 |
| 6 | 状态机 `pending → running` | 多一个 **`evaluating`** 态（agent 连上后进入）；终态是 `completed` / `failed` |

**外加两条与文档口径不同的事实** `[实践]`：**认证是两层**（`CHALLENGE_TOKEN` = email+password 换来的 JWT，查结果/榜单用；`JOB_TOKEN` = 提交时返回、**永不过期**、只用于拨隧道），计划里假设的单一 `ROBOCOLISEUM_API_KEY` **根本不存在**；**WS 二进制帧布局在 skill 侧是 `未提及` 的**，本次从第三方 agent 源码反推出来的布局见 `code_knowledge.md` **§3.6.1**（L336–351）—— 本库这一层的唯一证据来源就是那次实践。

详见 `ai_knowledge.md` §4.6（`P42`–`P45`）与 §6 教训 `L04`，以及 `troubleshooting.md` `Q42`–`Q45`。

#### 9.3.6 命名、证据等级与 `未提及`

平台在文档里有**三个并存的品牌名**：对外域名是 **RoboColiseum**，skill 内部一律自称 **"the Simulation Challenge"**，而状态文件与 SDK 用第三个名字 **simubotix**（`~/.simubotix-challenge.env`，权限 0600；`contestant_sdk/python/simubotix_agent.py`）。三者指同一套服务。权威 schema 出处是 `main/source/geniesim/benchmark/policy/corobotpolicy.py`。

> 该平台是**托管服务**而非本地代码，因此其契约在本知识库中另立 `[SKILL]` 证据等级（见文档头）——它描述的是**线上服务的约定**，既非本地 `[CODE]`，也非论文 `[PAPER]`。**引用时注意**：`robocoliseum.ai/usage` 是一个 1916 字节的 SPA 空壳、**不提供任何文档内容**，所以本节无法与线上文档交叉验证，全部结论仅来自 skill 文件。此外 skill 存在**两份会漂移的副本**（本机 `~/.claude/skills/` 与上游仓库内），行数与 md5 均有差异——**可长期引用的是上游仓库内那份**。

**`未提及` 清单**（已 grep 确认无证据，不要再搜）：

- **单位与量纲**：关节是弧度还是角度、夹爪/effector 的取值范围，全部未说明。
- **`EEF_ABS` 的坐标系**未定义。
- **任何延迟上限 / 超时 / 步进速率 / 控制频率** —— 整套文件里唯一的墙钟常量只有"30 秒网关重连窗口"和"2–5 秒轮询间隔"。
- **评分细则本身**（rubric）未公开。
- **WS 二进制帧布局、`drain` 之外的控制帧词表、传输状态机** —— 这三项本应在 5 个被引用但**并不存在**的文档里（`../user-manual.md`、`../quickstart.md`、`../tunnel-protocol.md` 等）。
- **谁在运营该平台**、数据集分套的规模/episode/任务数、`sim2real` 训练套为何没有对应 board、以及为何没有 `spatial`/`robust` 训练套。

**本次实践对这份清单的增补** `[实践]`：**评分 rubric 仍是 `未提及`**——判分全在平台侧 Isaac Sim 内完成，本地既拿不到也无从干预，**平台也不回传仿真渲染视频**（本地只能录到自己这侧的观测视角）。**"无延迟上限"得到反面印证**：本次单帧推理稳定 **~350 ms**、单个 board 跑了 **3–4.5 小时**，全程未被平台超时中断，故"没有硬性步进速率要求"这一点可按实践理解为真；但**网关侧会停摆**——曾出现 TCP 连着、agent 自认健康、平台进度却冻结 20 分钟以上的情形，且**用同一 `agent_id` 重连不会触发重新派发**（`P34`）。

> ⚠️ **skill 内部有两处自相矛盾**：选榜环境变量在基线 skill 里是 **`PI05_BOARD`**、在推理协议 skill 里是 **`ACOT_BOARD`**；checkpoint 目录名一处带 `_pi05` 后缀一处不带（**以基线 skill 为准**，因为它描述的正是创建这些目录的下载脚本，可用 `PI05_CKPT_DIR` 覆盖）。另外基线仓库地址被 skill 自己标注为"DEBUG/示例值，请替换为官方值"，故该 URL **属临时性质**，勿当权威。

### 9.4 上游与谱系

| 项目 | 关系 |
|---|---|
| **Cosmos-Predict2-2B-Video2World**（NVIDIA） | GE-Sim 2.0 的 DiT 主干来源（§2.2） |
| **Genie Envisioner / GE-Base**（Liao et al., 2025） | 直接前身，提供分块自回归 + 稀疏记忆 + 多视角 DiT 框架 |
| **EnerVerse → EnerVerse-AC → GE-Sim 1.0** | 更早的家族谱系（§1.5） |
| **Robometer**（Liang et al., 2026） | World Judge 的基础（§2.5） |
| **DMD2** | 步数蒸馏方法（§2.6） |
| **π0.5 / openpi**（Physical Intelligence） | 官方闭环示例所用策略；以 git submodule 引入（§3.3） |
| **AgiBot-World / AgiBot-DigitalWorld** | 数据集来源 |

### 9.5 本知识库内的关联文档

| 文档 | 用途 |
|---|---|
| [`quickstart.md`](quickstart.md) | ⭐ **动手前先读**（✅ **已建立**，312 行）：最短路径、五个 Stage 的运行示例与预期输出、改参数、高频 8 问、自检清单 |
| [`ai_knowledge.md`](ai_knowledge.md) | ✅ **已建立**（469 行，8 章）：复现实战复盘、`P01`–`P45` 问题、`D01`–`D20` 决策、`L01`–`L09` 教训（全篇 `[实践]`）。**§4.6 F 类是「平台契约与判分口径」专章** |
| [`troubleshooting.md`](troubleshooting.md) | ✅ **已建立**（975 行）：`Q01`–`Q45` 按报错现象查的 Q&A，顶部有快速症状索引（F 类 `Q42`–`Q45` 是平台契约与判分口径） |
| [`code_knowledge.md`](code_knowledge.md) | ✅ **已建立**（744 行，8 章）：本机复现仓库 `GE-Sim-V2-tour` 的代码视角；**§7.2 十三条静默失效路径**与 **§8 四层关联映射**是本层结论的物证与反例来源 |
| [`00-index.md`](00-index.md) | 本项目章节地图（带行号）+ `未提及` 清单 |

> **原理层与实践层冲突时以哪层为准**：本文件描述的是**上游设计与文档口径**；`ai_knowledge.md` / `troubleshooting.md` 记录的是**某一次具体复现的实测**；`code_knowledge.md` 描述的是**那次复现的编排代码**（不是上游本体）。
> - **API 具体写法**：以经验层/排障层为准（本文件的推断已被实测推翻过，例见 §6 章首的 `Q17` / `Q21`）。
> - **能力边界与设计原理**：以本文件为准（实测只覆盖了它的一部分用法）。
> - **上游被实际怎么改的**：以代码层 §6 为准（本文件 §5.4 "四个内核全关"的建议已被 §6.1 的实测放宽，两处均已就地标注）。
> - ⚠️ **版本落差**：几层核对的不是同一个检出点，**API 写法不保证跨版本通用，能力边界结论可以**。
