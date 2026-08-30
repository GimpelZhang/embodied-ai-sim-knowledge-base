# Genesis World 常见问题与解决方案

> **文档来源**：本篇由 [`ai_knowledge.md`](ai_knowledge.md) §4「遇到的问题与解决方案」**按故障类别重排**而成，**不是新的事实来源**。每条 `Qxx` 与该章的 `Pxx` **一一对应、编号永久稳定**（只追加、不重排、不复用）。
> **证据等级**：全篇为 **`[实践]`** 级——记录的是本机一次复现中的实测现象与解法，**不是 Genesis World 的官方结论**。
> **版本**：全部实测于 **genesis-world 1.2.2 + gs-nyx 0.1.3**（Python 3.12.13 / PyTorch 2.10.0+cu128 / CUDA 11.8 / A800-40GB / Ubuntu 22.04 headless）。原理层 [`background_knowledge.md`](background_knowledge.md) 描述的是 **1.3.3**，**本篇的具体写法不可直接套用到新版本**。
> **脱敏**：本机绝对路径已替换为 `<user_home>` / `<path>`，主机名替换为 `<host>`。全篇无账号、密码、密钥、token。

---

## 快速症状索引

**带着报错来的，直接在这张表里搜关键字。**

| 症状 / 报错关键字 | 条目 |
|---|---|
| `No such file or directory: ':/usr/local/cuda-11.8/bin/nvcc'`（路径开头多冒号） | [`Q01`](#q01) |
| `transformers` 版本不满足模型要求（`>=4.40,<4.50`） | [`Q12`](#q12) |
| `ImportError: Numba needs NumPy 2.4 or less` / 装完某包后 `import genesis` 就崩 | [`Q26`](#q26) |
| OpenPI 要 Python 3.11，环境是 3.12 | [`Q37`](#q37) |
| `AttributeError: module 'genesis.options.morphs' has no attribute 'Franka'` | [`Q02`](#q02) |
| `Validation error for <gs.morphs.Box>: Unrecognized attribute 'surface'` | [`Q03`](#q03) |
| `Link not found for name: hand.` | [`Q04`](#q04) |
| `Invalid input shape: (14,). Dimension 0 consistent with required size 7` | [`Q05`](#q05) |
| 第二次 `gs.init()` 就 Segfault / Taichi error；找不到 `scene.destroy()` | [`Q15`](#q15) |
| `ModuleNotFoundError: examples.locomotion.go2_env` | [`Q16`](#q16) |
| `cam.render()` 的返回值当数组用报类型错 | [`Q18`](#q18) |
| `RuntimeError: can't convert cuda:0 device type tensor to numpy` | [`Q06`](#q06) |
| `genesis.GenesisException: Scene is already built.` | [`Q17`](#q17) |
| `predict_action` 返回类型不稳定 / 模型卡片 API 与实际不符 | [`Q07`](#q07) |
| 夹爪合上了却夹不住，物体从指间滑出 | [`Q08`](#q08) |
| 评测报了 SUCCESS，但怀疑是假阳性 | [`Q09`](#q09) |
| VLA 末端无论目标在哪都收敛到同一点；夹爪输出恒 0.0 | [`Q10`](#q10) |
| IK 目标用 `panda_link7`，但夹持发生在指尖，对不准 | [`Q11`](#q11) |
| 换了微调模型仍不收敛（末端距目标 18–36cm） | [`Q13`](#q13) |
| 相机位置一动，模型行为就变 | [`Q14`](#q14) |
| `learn(50)` 之后 `model_50.pt` 不存在，只有 `model_49.pt` | [`Q19`](#q19) |
| `OnPolicyRunner.load()` 返回 `None` | [`Q20`](#q20) |
| `policy(obs["policy"])` 形状报错 | [`Q21`](#q21) |
| resume 训练时之前的 checkpoint 被删了 | [`Q22`](#q22) |
| 后台 bash 任务秒退、无输出、无进程 | [`Q23`](#q23) |
| 正常的 MP4 被验证脚本判 FAIL（编码名对不上） | [`Q24`](#q24) |
| 像素验证误报"目标不可见" | [`Q25`](#q25) |
| `IPCCouplerOptions` 的字段不存在 / `set_ipc_link_filter` 找不到 | [`Q27`](#q27) |
| `AttributeError: 'PBD2DEntity' object has no attribute 'geom_start'` | [`Q28`](#q28) |
| PBD 布料 / 柔性体一放上去就掉下去 | [`Q29`](#q29) |
| IK 解发散到几十米外（如 `[5.67, -250, -140]`） | [`Q30`](#q30) |
| 同一段代码单场景收敛、多场景循环就发散 | [`Q31`](#q31) |
| 夹爪闭合后物体留在原地 / 被压穿桌面 | [`Q32`](#q32) |
| FEM 柔性体被手指直接穿过 | [`Q33`](#q33) |
| SPH 流体"炸开" | [`Q34`](#q34) |
| `g1_29dof.urdf` 里找不到夹爪关节 | [`Q35`](#q35) |
| 从 Isaac Sim 抄来的链接名在 Genesis 里 `get_link()` 找不到 | [`Q36`](#q36) |

**按类别浏览**：[A 安装与依赖](#a-安装与依赖) · [B API 用法错误](#b-api-用法错误) · [C 生命周期与调用顺序](#c-生命周期与调用顺序) · [D VLA 闭环行为异常](#d-vla-闭环行为异常) · [E 训练链路（RL）](#e-训练链路rl) · [F 验证与交付](#f-验证与交付) · [G 刚柔 / 刚流耦合](#g-刚柔--刚流耦合) · [H 跨项目资产迁移](#h-跨项目资产迁移)

---

## A 安装与依赖

<a id="q01"></a>
### Q01 · 编译报错说 nvcc 不存在，但路径开头多了一个冒号

**Q**：`error: [Errno 2] No such file or directory: ':/usr/local/cuda-11.8/bin/nvcc'` —— 去看这个文件明明存在。

**A**：问题不在 CUDA 安装，在**环境变量的字符串**。

1. 打印确认：`echo "[$CUDA_HOME]"`，若输出形如 `[:/usr/local/cuda-11.8]`，即命中。
2. 根因是环境脚本里用了 PATH 式拼接 `CUDA_HOME=$CUDA_HOME:/usr/local/cuda-11.8`，而 `CUDA_HOME` 原本为空，于是拼出前导冒号。
3. **`CUDA_HOME` 是单值变量，不是 PATH 列表**，直接赋值：
   ```bash
   export CUDA_HOME=/usr/local/cuda-11.8
   export PATH=$CUDA_HOME/bin:$PATH          # 只有 PATH 才用冒号拼接
   ```

❌ **无效尝试**：检查 CUDA 安装完整性、重装 toolkit —— 方向完全错误，文件一直都在。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.1 `P01`

---

<a id="q12"></a>
### Q12 · 模型要求 `transformers>=4.40,<4.50`，环境是 4.57.6

**Q**：加载 Franka 微调模型时提示 transformers 版本不满足，属于跨大版本降级，怕影响其它组件。

**A**：

1. 先确认约束来源（模型卡片的依赖声明），不要凭报错猜。
2. 本次降级到 **4.53.2**，实测**只报告警告、不影响推理**。
3. ⚠️ 注意这是"擦边"方案——严格满足声明应降到 `<4.50`。若出现推理行为异常，先把这条列为嫌疑。
4. 降级前后都要复跑一次最小推理用例做回归。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.1 `P12`

---

<a id="q26"></a>
### Q26 · 装了某个可选包之后，`import genesis` 直接崩了

**Q**：为启用 IPC 耦合器执行 `pip install pyuipc`，之后 `import genesis` 报 `ImportError: Numba needs NumPy 2.4 or less`，此前所有能跑的脚本全部失效。

**A**：这是**依赖传递性摧毁主环境**的典型案例，处理分两步。

*已经踩了 —— 恢复：*
1. 把 numpy 锁回 genesis 可接受的版本（本机为 numpy < 2.5），重新验证 `import genesis` 与 `import numba`。
2. 复跑一个最小仿真用例确认恢复。

*还没踩 —— 预防（推荐）：*
1. **装之前**先看解析结果，不要直接装：
   ```bash
   pip install --dry-run pyuipc     # 只看它会动哪些包
   ```
2. 高风险依赖装进**完全独立的环境**验证。
3. ⚠️ **`pip install --target` 的隔离不够**：本次用 `--target` 装上了，但运行时 numpy 仍然冲突，IPC 的 `scene.build()` 依旧失败。

*本次结论*：**IPC 路径在本机不可达，降级到 PBD**（PBD 是本机唯一 smoke-test 通过的刚柔耦合路径）。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.1 `P26` · 教训 `L06`

---

<a id="q37"></a>
### Q37 · OpenPI 要求 Python 3.11，现有环境是 3.12

**Q**：想接入 OpenPI 的 PI0 策略，但它要求 Python 3.11 + uv，而工作环境是 3.12.13。

**A**：**⚠️ 未解决，建议参考详细记录** —— 该方案（Patch 01）**从未实际执行**，以下对策**未经验证**：

1. 另建 Python 3.11 环境，或用 uv 做隔离。
2. 安装后**必须**把 OpenPI 的 `transformers_replace/*` 补丁复制进 site-packages（易漏步骤）。
3. 由于仿真侧（3.12）与推理侧（3.11）分处两个环境，两者需通过进程间通信衔接——参考 Patch 02 采用的 WebSocket 策略服务器方案。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.1 `P37`

---

## B API 用法错误

> 这一组的共同点：**它们都来自"看起来应该这么写"，而不是查证过的写法**。落笔任何 API 名之前先 grep 到定义处，可以一次性避掉整组。

<a id="q02"></a>
### Q02 · `gs.morphs.Franka` 不存在

**Q**：`AttributeError: module 'genesis.options.morphs' has no attribute 'Franka'`

**A**：Genesis 没有这种"机器人便捷类"，要走 URDF 加载。

```python
import os, genesis as gs

franka = scene.add_entity(
    gs.morphs.URDF(
        file=os.path.join(os.path.dirname(gs.__file__),
                          "assets", "urdf", "panda_bullet", "panda.urdf"),
        fixed=True,
    )
)
```

⚠️ 加载后请注意 **Franka 的 `n_dofs=15`**（7 臂 + 2 指 + 其余），后续索引不要假设是 7 或 9。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.2 `P02`

---

<a id="q03"></a>
### Q03 · `surface` 参数不被 morph 接受

**Q**：`Validation error for <gs.morphs.Box>: Unrecognized attribute 'surface'`

**A**：`surface` 属于 **`scene.add_entity()`**，不属于 morph。

```python
# ❌ 错
scene.add_entity(gs.morphs.Box(size=(0.04,)*3, surface=gs.surfaces.Plastic(color=(0,0,1))))

# ✅ 对
scene.add_entity(
    morph=gs.morphs.Box(size=(0.04,)*3, pos=(0.5, 0.0, 0.02)),
    surface=gs.surfaces.Plastic(color=(0, 0, 1)),
)
```

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.2 `P03`

---

<a id="q04"></a>
### Q04 · `get_link("hand")` 报 Link not found

**Q**：`Link not found for name: hand.`

**A**：panda_bullet URDF 的末端链接叫 **`panda_link7`**，不是 `hand` / `panda_hand` / `ee_link`。

```python
ee = franka.get_link("panda_link7")
```

**更通用的做法是运行时枚举，不要硬编码猜测**：

```python
print([l.name for l in franka.links])   # 先看清楚有哪些链接
```

⚠️ 注意 `get_link()` 必须在 `scene.build()` **之后**调用（见 [`Q17`](#q17)）。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.2 `P04` · 同类问题 [`Q36`](#q36)

---

<a id="q05"></a>
### Q05 · IK 结果传给控制接口时形状不对

**Q**：`Invalid input shape: (14,). Dimension 0 consistent with required size 7`

**A**：**IK 返回的是完整 qpos `(16,)`，不是臂部 7 维**。用 `[:-2]`（意图是"去掉两个夹爪自由度"）会得到 `(14,)`，是错的。

```python
motors_dof = np.arange(7)              # 显式索引臂部 7 个自由度

qpos = franka.inverse_kinematics(link=ee, pos=target_pos, quat=ee.get_quat())
franka.control_dofs_position(qpos[motors_dof], motors_dof)
```

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.2 `P05`

---

<a id="q18"></a>
### Q18 · `cam.render()` 的返回值不能直接当图像用

**Q**：把 `cam.render(rgb=True)` 的结果传给 numpy / OpenCV 时报类型错。

**A**：它返回 **4 元组 `(rgb, depth, seg, normal)`**，必须解包。

```python
rgb, depth, seg, normal = cam.render(rgb=True)
# 或
rgb = cam.render(rgb=True)[0]
```

⚠️ 另外 `fov` 是**垂直**视场角，默认 30° 对全身取景过窄；宽视图建议 45°。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.2 `P18`

---

<a id="q16"></a>
### Q16 · `from examples.locomotion.go2_env import Go2Env` 找不到模块

**Q**：`ModuleNotFoundError` —— 官方教程里的 `examples.*` 导入不了。

**A**：**pip 安装的 `genesis-world` 包里没有 `examples/` 目录**，它只存在于 GitHub 仓库。

1. 到 GitHub 上**与本机 genesis 版本完全一致的 tag**（本次为 `v1.2.2`）取文件。
2. 把 `go2_env.py`（304 行）/ `go2_train.py`（178 行）等 vendoring 进自己的仓库，纳入版本管理。
3. ⚠️ **其中的 URDF 路径必须保持相对**——本次实测改成绝对路径反而失败。
4. vendoring 后建议在文件头注明来源 tag，便于后续对齐上游。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.2 `P16`

---

## C 生命周期与调用顺序

> **一句话记住整组**：**模型加载 → `gs.init()` → 添加实体与相机 → `scene.build()` → 设 PD 增益 / `get_link()` → 开始 step**。顺序错了就是本组的各种报错。

<a id="q06"></a>
### Q06 · 【CRITICAL】加载深度学习模型后出现 CUDA 上下文冲突

**Q**：`RuntimeError: can't convert cuda:0 device type tensor to numpy`，或其它形式的 CUDA 上下文异常。

**A**：**深度学习模型（VLA / 策略网络）必须先于 `gs.init()` 完成加载。**

```python
# ✅ 正确顺序
model = load_vla_model(...)      # 1. 先加载模型（本次为 bfloat16，约 14GB）
gs.init(backend=gs.gpu)          # 2. 再初始化 Genesis
scene = gs.Scene(...)            # 3. 然后构建场景
```

❌ **无效尝试**：在报错处加 `.cpu()` / `.detach()` —— 治标，问题会在别处以其它形态复现。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.3 `P06`（决策 `D04`）

---

<a id="q17"></a>
### Q17 · `Scene is already built.`

**Q**：`genesis.GenesisException: Scene is already built.` —— 在构造完环境对象后调用 `scene.add_camera`。

**A**：`scene.add_camera` 带 `@gs.assert_unbuilt` 装饰器，**相机必须在 `scene.build()` 之前添加**。

若使用第三方 / vendored 的 Env 类（如 `Go2Env`），先确认它**是否在 `__init__` 内部就调用了 `scene.build()`**（本次即是）：

1. 读 `Go2Env.__init__`，定位 `scene.build()` 的位置。
2. 给它加一个 `camera_cfg=` 构造参数，把相机添加挪到 build **之前**。
3. 不要试图在 env 构造完之后补相机——必然失败。

⚠️ **与之互补的一条（方向相反）**：**PD 增益 `set_dofs_kp` / `set_dofs_kv` 与 `get_link()` 必须排在 `build()` 之后。**

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.3 `P17`

---

<a id="q15"></a>
### Q15 · 循环里第二次 `gs.init()` 就 Segfault；找不到销毁场景的 API

**Q**：批量评估要在一个进程里连跑多个场景，第二次 `gs.init(backend=gs.gpu)` 直接 Segfault 或抛 Taichi error；也找不到 `scene.destroy()` / `cleanup()`。

**A**：Taichi 的 CUDA 初始化是**进程级**的，而 Genesis **没有场景销毁 API**。

*方案一（同进程多场景，够用即可）：*
1. 把 `gs.init()` 提到场景循环**之外**，全进程只调一次。
2. 每个场景的构建与运行封进**独立函数**，靠作用域退出 + GC 回收。
   ```python
   gs.init(backend=gs.gpu)          # 只调一次
   for cfg in scene_configs:
       run_single_scene(cfg)        # 场景对象在函数返回后被回收
   ```

*方案二（推荐，更彻底）：*
**进程隔离** —— orchestrator 用 subprocess 串行调度，每个子进程各自 `gs.init()`、各自拿独立 CUDA 上下文。这也顺带规避了训练与渲染争抢上下文的问题，以及 [`Q31`](#q31) 的跨场景状态污染。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.2 `P15`（决策 `D19`）

---

## D VLA 闭环行为异常

> ⚠️ 这一组**不是孤立 bug，而是一条根因链**：表层"抓不住" → 本体不匹配（embodiment mismatch）→ 仿真器间的 sim-to-sim gap。
> **本项目最终 8 场景评测 0/8，该链路未走通。** 若你在做同类任务，建议按 [`Q09`](#q09) 先自查判定口径，再往下读。

<a id="q07"></a>
### Q07 · 模型卡片写的 API 和实际对不上；返回类型还会漂移

**Q**：按模型卡片写的调用报错；`predict_action` 在不同调用下返回类型不一致。

**A**：

1. **不要照模型卡片写**——先直接打印实际返回对象：
   ```python
   out = model.predict_action(...)
   print(type(out), getattr(out, "shape", None))
   ```
2. 按实测类型写**防御性解包**（兼容 ndarray / tuple / dict 等形态）。
3. ⚠️ 一般教训：**模型卡片是文档不是契约**，源码和实测才是。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.4 `P07`

---

<a id="q08"></a>
### Q08 · 夹爪合上了，物体还是从指间滑出去

**Q**：夹爪闭合动作执行了，接触也有，但夹不住方块。

**A**：Franka 夹爪的**默认 PD 增益太低**，撑不住物体重量。

1. 在 `scene.build()` **之后**提高夹爪增益：
   ```python
   fingers_dof = np.arange(7, 9)
   franka.set_dofs_kp(np.array([2000, 2000]), fingers_dof)
   franka.set_dofs_kv(np.array([200, 200]),  fingers_dof)
   ```
2. 用状态机管理开合时序（本次为 `GripperController` 四态：`OPEN → CLOSING → HOLDING → RELEASING`），不要每步直接下发目标。

❌ **无效尝试**：调闭合行程、调 friction —— 增益不够时这些都补不上。

⚠️ 若增益调高后仍然抓不住、且物体是**布料 / 柔性体**，问题可能不在增益而在夹爪运动学，见 [`Q32`](#q32)。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.4 `P08`（决策 `D05`）

---

<a id="q09"></a>
### Q09 · 评测报了 SUCCESS，但怀疑是假阳性

**Q**：闭环评测输出 "PARTIAL SUCCESS"，但直觉上模型并没有真的完成任务。

**A**：**这个怀疑通常是对的。**逐条核对下面五项，任何一项成立都要给结论打折：

1. **目标物体是不是被挪到了模型的固定收敛点？**（即"场景迁就模型"）
2. **成功判定口径是不是被放宽过？**（如从"抬起 5cm"降为"触碰 <3.5cm"）
3. **有没有外部控制器接管了模型本该输出的维度？**（如夹爪由状态机接管，而模型输出恒 0）
4. **通过率的提升，是来自能力变化还是来自口径变化？** —— 本次六次尝试中，提升**完全来自口径变更**。
5. **换一个目标位置重跑，结果还成立吗？** 这是最快的证伪实验。

*本次结论*：所谓成功是**三重外部辅助叠加**的结果，模型本身没有完成任务。

⚠️ 一般纪律：**降低目标之前，必须先把"原目标不可达"证明到机制层面并显式征得批准**，否则降级会变成对失败的隐藏。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.4 `P09` · 教训 `L04`

---

<a id="q10"></a>
### Q10 · VLA 末端无论目标放哪都收敛到同一点，夹爪输出恒 0.0

**Q**：`openvla/openvla-7b` 驱动 Franka 时，末端总是收敛到 **~(0.575, −0.081, 0.244)**（相对目标偏置 X +7.6cm / Y −8.1cm / Z +2.4cm），且动作向量的夹爪维度**恒为 0.0**。

**A**：根因是 **embodiment mismatch** —— 该模型在 **WidowX** 数据上预训练，与 Franka Panda 的运动学不匹配。**这不是控制器问题。**

*诊断（30 秒确认）*：把目标物体挪到另一个位置重跑，若末端仍收敛到**原来那个点**，即确诊。

❌ **无效尝试（本次连试三轮全败）**：调 `pos_scale`、调 PD 增益、调动作缩放。
> ⚠️ **重要信号**：如果你改了变量而结果分毫不变，说明该变量根本没参与因果链——此时应质疑问题定义，而不是提第 N+1 个假设。

*可选路径*：
- **短期（治标）**：把目标搬到模型收敛点 + 用独立控制器接管夹爪。⚠️ 会制造假阳性，见 [`Q09`](#q09)。
- **中期**：把 IK 目标改成手指链接（见 [`Q11`](#q11)）；VLA 只做感知、经典控制器做执行。
- **长期（根本）**：用 50–100 个 Franka 示范 episode 做 LoRA 微调；或换 Octo / Diffusion Policy / SmolVLA；或迁到 LeRobot 框架。
  ⚠️ 但注意 [`Q13`](#q13) —— **换成 Franka 微调模型本次并未奏效**。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.4 `P10` · 教训 `L02`

---

<a id="q11"></a>
### Q11 · IK 目标是 `panda_link7`，但实际夹持发生在指尖

**Q**：末端链接与真正的夹持点之间有偏移，导致定位系统性偏差。

**A**：**这个偏移是姿态相关的，常数补偿无效。**

1. 实测某构型下偏移为 ΔX +12.8cm / ΔY +10.5cm，换个姿态就变。
2. ❌ **无效尝试**：用固定偏移量补偿。
3. **可行方向**：把 IK 目标直接改成手指链接。⚠️ 需处理叶子链接的数值不稳定问题。
4. 折中做法（本次采用）：手工调整工作点 X 使张开的手指落在物体正确一侧，实测可达 `dist=0.024`。仅适用于固定姿态场景。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.4 `P11`

---

<a id="q13"></a>
### Q13 · 换成同本体的微调模型，仍然不收敛

**Q**：改用在 Isaac Sim 中用 Franka 数据微调的模型（卡片宣称"无 Embodiment Mismatch"），末端仍距目标 **18–36cm 且不向目标收敛**，夹爪仍恒 0.0，且模型倾向从**上方**接近、手指落在物体顶部而非两侧。

**A**：**⚠️ 部分未解决。**根因只是从 embodiment mismatch 换成了 **sim-to-sim gap** —— 模型在 Isaac Sim 训练、在 Genesis 推理，**物理引擎、渲染器、相机模型全不同**。

- 前两条现象有临时绕过（挪目标到收敛点 + 外部夹爪控制器），但同样制造假阳性。
- **第三条"从上方接近"目前无根本解决方案**，原始记录明确写道"需要重新训练模型或使用混合控制策略"。

⚠️ 一般教训：**"换个更好的组件"往往只是换了根因的名字。**换之前先问一句"如果换了还不行，下一个解释会是什么"——如果能立刻说出下一个借口，说明根因没有定到底。真正奏效的往往是**换问题**（本次是转向可在仿真内自监督训练的 RL 任务）。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.4 `P13` · 教训 `L07`

---

<a id="q14"></a>
### Q14 · 相机位置一动，模型行为就变

**Q**：8 场景批量评估 0/8 全失败，但出现两个反直觉现象：相机抬高 +0.35m 的场景反而**更接近**目标（14.89cm，无扰动基线是 34.6–35.6cm）；把目标移开收敛点的场景则**发散到 267.36cm**。

**A**：结论是 **模型对场景内容（干扰物 / 杂乱 / 强光）鲁棒，但对相机外参高度敏感**。

**实践准则**：
1. **已经调通的 VLA 输入相机，一个参数都不要动**——本次实测哪怕只做 Y 方向平移，收敛点就从 27cm 漂到 35cm。
2. 需要额外视角（如人类视图 / 录像取景）时，**新增一台 render-only 相机作为旁路**，不要移动原相机：
   ```python
   cam      = scene.add_camera(res=(224, 224), fov=30)   # VLA 输入，锁死不动
   wide_cam = scene.add_camera(res=(640, 480), fov=45)   # 仅渲染，人类视图
   ```
3. 用 **grep 推理路径**验证不变量：确认 `wide_cam` / `wide_img` 只出现在渲染、保存、日志三处，**绝不出现在 `processor` / `predict_action` 的参数里**。
4. 改动后做**轨迹回归**（本次比对 500 步轨迹与此前记录完全一致）。
5. ⚠️ **收敛点的漂移方向不可预测**——"相机一抬反而更近"不能算改善，更不能作为调参方向。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.4 `P14`（决策 `D13`）

---

## E 训练链路（RL）

> 本组五条**全部由小规模 smoke test 在正式运行之前捕获**，没有一条是在多小时训练跑完后才暴露的。
> **建议做法**：把正式参数按 1/100 缩小（iterations / envs / steps），**完整跑通全部阶段**（尤其是产物交接处），再放大。

<a id="q19"></a>
### Q19 · 【最致命】`learn(50)` 之后 `model_50.pt` 不存在，只有 `model_49.pt`

**Q**：训练脚本跑完，下游阶段报 `FileNotFoundError: model_50.pt`。

**A**：**rsl-rl-lib 5.0.1 使用 0-based 迭代索引**（见 `rsl_rl/runners/on_policy_runner.py` L77–161）。

训练结束后显式对齐编号再保存：

```python
runner.learn(num_learning_iterations=args.max_iterations)
runner.current_learning_iteration = args.max_iterations   # 对齐为 1-based 语义
runner.save(os.path.join(log_dir, f"model_{args.max_iterations}.pt"))
```

⚠️ **为什么必须提前发现**：若不修，会等到 orchestrator 的第 3 阶段才报错，**前面数小时训练时间全部浪费**。这是本项目 smoke test 价值最高的一次拦截。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.5 `P19` · 教训 `L01`

---

<a id="q20"></a>
### Q20 · `OnPolicyRunner.load()` 返回 `None`

**Q**：把 `load()` 的返回值当模型字典使用，拿到 `None`。

**A**：`load()` 返回的是 `loaded_dict["infos"]`（此处为 `None`），**不是 state_dict**。

要读迭代数请直接读 checkpoint：

```python
ckpt = torch.load(ckpt_path, weights_only=False)
start_iter = ckpt["iter"]
```

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.5 `P20`

---

<a id="q21"></a>
### Q21 · `policy(obs["policy"])` 形状报错

**Q**：推理时给策略传观测报形状错误。

**A**：策略要接收**完整 TensorDict**，传 `obs["policy"]` 等于**索引了两遍**。

```python
# ❌ 错
action = policy(obs["policy"])
# ✅ 对
action = policy(obs)
```

⚠️ 同一处容易连带踩到的两条：
- **`Go2Env.step()` 返回 4 元组**（不是 gym 惯例的 5 元组）。
- `reset()` 返回的是键为 `"policy"` 的 TensorDict。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.5 `P21`

---

<a id="q22"></a>
### Q22 · resume 训练时，之前存好的 checkpoint 被删了

**Q**：带 `--resume` 重启训练后，`model_50.pt` 消失。

**A**：官方 `go2_train.py` **无条件执行 `shutil.rmtree(log_dir)`**。vendoring 之后必须改两处：

```python
# 1) 仅在非 resume 时清空日志目录
if not args.resume and os.path.exists(log_dir):
    shutil.rmtree(log_dir)

# 2) save_interval 从 100 改到 50，否则拿不到中间 checkpoint
train_cfg["save_interval"] = 50
```

*验证 resume 无 off-by-one*：本次实测 phase 2 产出 `model_50.pt`（内部 `iter=50`），phase 4 加载后 `delta=50`、跑 iters 50..99、产出 `model_100.pt`，正确。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.5 `P22`

---

<a id="q23"></a>
### Q23 · 后台任务秒退，无输出、无进程、无报错

**Q**：同一条命令前台跑正常，放到后台就立刻结束，什么也不留下。

**A**：**后台 / 非交互 bash 不继承 conda 环境**（不 source profile）。

写一个显式 source 一切的 wrapper（本次为 `run_in_env.sh`）：

```bash
#!/usr/bin/env bash
set +u                                    # 注意：不要用 set -u
source <user_home>/miniconda3/etc/profile.d/conda.sh
conda activate <env>
source <path>/<project>_env.sh            # 项目环境脚本（CUDA_HOME 等）
exec "$@"
```

调用：`./run_in_env.sh python train_subprocess.py --max_iterations 100`

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.5 `P23`

---

## F 验证与交付

> 前提约束：本项目执行方**无读图能力**，所有视觉结论必须转成可机器判定的数值断言。这两条是该协议自身的坑。

<a id="q24"></a>
### Q24 · 正常的 MP4 被验证脚本判 FAIL

**Q**：视频能播、也没损坏，但自动化验证判定编码不合法。

**A**：**OpenCV 用 `mp4v` fourcc 写出的文件，ffprobe 报告的 `codec_name` 是 `mpeg4`。**

编码白名单必须同时包含两者：

```python
ALLOWED_CODECS = {"mp4v", "mpeg4"}       # 两个都要
```

先手工确认实际值再写断言：

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=codec_name,width,height,nb_frames -of default=nw=1 out.mp4
```

⚠️ 这个坑在本项目 Stage 3 与 Stage 4 **各踩了一次**——项目级 gotcha 应在首次踩到时就沉淀。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.6 `P24`

---

<a id="q25"></a>
### Q25 · 像素验证误报"目标不可见"

**Q**：用像素统计验证"目标物体在画面中"，部分场景误报失败，但相机参数看起来没问题。

**A**：**不是相机问题，是比较基准帧选错了时刻。**

本次用的是 step-500 的中段关键帧，而此时**已经发散的机械臂在近距离视图里正好挡住了目标**。

1. 改用 **step-0 关键帧**作为比较基准（此时场景处于已知的初始状态，无遮挡）。
2. 一般原则：像素基准帧应取自**状态确定、无动态遮挡**的时刻，不要取中段。
3. 误报时先做这个判别：把该帧存出来做像素统计，看是"目标像素为 0"还是"目标像素被其它物体覆盖"。

*可复用的验证手段*（本项目 41 项验证门的构成）：ffprobe 查分辨率 / 编码 / 帧数、颜色掩码统计目标占比、帧差定位运动像素分布、JSON 指标字段完整性。原则是"**永不在没有像素证据的情况下声称视觉成功**"，同时**明确写出该协议不能证明什么**。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.6 `P25` · 教训 `L03`

---

## G 刚柔 / 刚流耦合

> **本组开篇先看这条**：IPC 耦合器在本机**不可达**（[`Q26`](#q26)），因此以下所有解法都建立在 **PBD** 路径上。若你的环境能装上 pyuipc，本组多条结论需要重新验证。

<a id="q27"></a>
### Q27 · `IPCCouplerOptions` 的字段不存在；`set_ipc_link_filter` 找不到

**Q**：按计划 / 教程写 `IPCCouplerOptions(dt=..., ipc_constraint_strength=..., contact_friction_mu=...)` 报字段不存在；文档提到的"重要优化" `set_ipc_link_filter` 在源码里搜不到。

**A**：**这三个字段与该方法在 genesis 1.2.2 中都不存在。**

1. 不要按二手材料写 API 名，**直接 grep 上游源码**：
   ```bash
   grep -rn "class IPCCouplerOptions" -A 40 <genesis_src>/
   grep -rn "set_ipc_link_filter"      <genesis_src>/    # 本次：零命中
   ```
2. 用 Python 直接内省真实字段：
   ```python
   import genesis as gs
   print(gs.options.IPCCouplerOptions.model_fields.keys())   # Pydantic 声明式配置
   ```
3. ⚠️ 一般教训：**任何写进代码或配置的 API 名、字段名，落笔前必须 grep 到它的定义处。** 计划书、文档、模型卡片都不是契约，源码才是。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.7 `P27` · 教训 `L05`

---

<a id="q28"></a>
### Q28 · `get_contacts()` 对 PBD 实体抛 AttributeError

**Q**：`franka.get_contacts(with_entity=cloth)` → `AttributeError: 'PBD2DEntity' object has no attribute 'geom_start'`

**A**：**`get_contacts` 属于 rigid-rigid 接触管线，而 PBD 布料内部是粒子系统，根本不参与该管线。**换参数形式反复调用没有用。

改用几何距离法（GPU 上算）：

```python
import torch

finger_verts = finger.get_verts()            # 左右指尖碰撞网格顶点，(36, 3)
cloth_parts  = cloth.get_particles_pos()     # 布料粒子位置
min_dist = torch.cdist(finger_verts, cloth_parts).min()
```

⚠️ **顶点采样稀疏是已知局限**，因此宣称口径也要相应降级：只说"所有帧实测最小间距 ≥ −thickness，**未检测到穿透事件**"，**不要说 IPC 级别的"数学零穿透"**。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.7 `P28`（决策 `D20`）

---

<a id="q29"></a>
### Q29 · PBD 布料 / 柔性体一放上去就掉下去

**Q**：布料按坐标放好，机械臂还没碰到就已经"掉桌"（粒子 `zmin` 落到 ~0.005）。

**A**：**PBD 柔性体无支撑就立即受重力下落**，它不会自己悬空。

加一个固定的支撑面，并把柔性体贴其上方：

```python
table = scene.add_entity(gs.morphs.Box(size=(0.6, 0.6, 0.40),
                                       pos=(0.5, 0.0, 0.20), fixed=True))   # 桌顶 Z=0.40
cloth = scene.add_entity(gs.morphs.Cloth(pos=(0.5, 0.0, 0.41), ...))        # 贴桌面
```

诊断手段：每步打印 `cloth.get_particles_pos()[:, 2].min()`，看它是否在接触前就单调下降。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.7 `P29`

---

<a id="q30"></a>
### Q30 · IK 解发散到几十米外

**Q**：对桌面高度的目标求 IK，末端飞到 `[5.67, −250, −140]`。

**A**：**不要用固定 quat 做增量式 IK。**

```python
# ❌ 错：固定姿态
qpos = franka.inverse_kinematics(link=ee, pos=target, quat=np.array([1, 0, 0, 0]))

# ✅ 对：每一步重新读取当前姿态
qpos = franka.inverse_kinematics(link=ee, pos=target, quat=ee.get_quat())
```

关键发现：本项目 Stage 1 之所以能工作，正是因为它**每一步重读 `ee.get_quat()`** 做增量移动；改用 evolving quat 后 XY 才能准确到位。

⚠️ 若改成 evolving quat 后**仍然**发散，看 [`Q31`](#q31)。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.7 `P30`

---

<a id="q31"></a>
### Q31 · 同一段代码，单场景收敛、多场景循环就发散

**Q**：同一个 quat、同一套参数，在单场景进程里 IK 正常，在同进程循环建多个 `gs.Scene` 时发散。

**A**：**IK / PD 状态会跨场景污染。**在多场景进程里怎么调参数都不对——这不是参数问题。

**结论：一进程一场景 / 子进程隔离。** 批量任务用 orchestrator + subprocess 串行调度（同 [`Q15`](#q15) 方案二）。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.7 `P31`（决策 `D19`）

---

<a id="q32"></a>
### Q32 · 夹爪闭合后物体留在原地，或被直接压穿桌面

**Q**：夹爪闭合了，但布料 `lift = −0.50cm`（没抬起来）；改用更轻的布料 + 更慢的闭合速度反而更糟——布料被压下桌面。

**A**：**⚠️ 本次判定为物理不可达，未解决。**

*诊断方法（关键）*：打印闭合前后的**指尖世界坐标**。

本次实测：从 `[0.479, 0.016, 0.392]` 跳到 `[0.72, −0.145, 0.505]` —— **panda_bullet 的夹爪闭合是"向前 + 向侧 + 向上扫动"，不是平行对夹**。物体不是被夹住，是被扫开了。

❌ **无效尝试（13 次探针全部无效）**：调 friction、调 rho、调 dt、调闭合速度、调 EEF 偏移。

*结论*：**"从上方捏取平铺布料并提拉 ≥10cm"在该 URDF + IK 约束下物理不可达。** 经决策者批准后改为**形变演示**（按压 + 横扫，正好利用张开手指的运动特性），布料 Z-range 从 0 变为 14.45cm，交付成功。

⚠️ 注意这次改目标与 [`Q09`](#q09) 里的"放宽口径"性质**完全不同**：这里是**先证明不可达（机制层面）、再经批准改目标**。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.7 `P32`（决策 `D18`）· 教训 `L04`

---

<a id="q33"></a>
### Q33 · FEM 柔性体被手指直接穿过

**Q**：用 `FEM.Elastic` 做三维体积柔性体（如海绵），刚体手指直接穿过去，调材料参数无效。

**A**：**只有耦合器是 `IPCCoupler` 时，FEM 才由 IPC 处理接触；否则 FEM 只积分内部力、完全不做刚-柔接触解算。**

- 证据：`genesis/engine/solvers/fem_solver.py` L975 附近的 `isinstance(self.sim._coupler, IPCCoupler)` 分支。
- 调 FEM 材料参数与接触无关，改不出结果。

*解法*：IPC 不可达时（[`Q26`](#q26)），**`PBD.Elastic` 是本机唯一的体积柔性体路径**：

```python
sponge = scene.add_entity(
    morph=gs.morphs.Box(size=(0.08, 0.08, 0.05), pos=(0.5, 0.0, 0.43)),
    material=gs.materials.PBD.Elastic(),      # 经 TetGen 四面体化，本次约 806 粒子
)
```

⚠️ 一般教训：验证"某功能是否真的生效"时，要找到它的**执行路径**（哪个分支、什么条件下才走到），而不是看它的**配置项是否存在**——**配置项存在但空转的假开关很常见**。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.7 `P33` · 教训 `L08`

---

<a id="q34"></a>
### Q34 · SPH 流体"炸开"

**Q**：SPH 流体在仿真开始后粒子迅速四散。

**A**：**时间步长过大。SPH 稳定步长 `dt ≤ 4e-4`**（本次在 `dt=2e-3` 下必炸）。

```python
scene = gs.Scene(sim_options=gs.options.SimOptions(dt=4e-4))
```

❌ **无效尝试**：调粒子半径、调粘度 —— 步长不稳时这些都救不回来。

*参考*：玻璃杯盛半杯水被机械臂撞倒的 demo，最终倾角 ≈175°、洒出 ≈71%，全程稳定。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.7 `P34`

---

## H 跨项目资产迁移

> ⚠️ 本组两条来自**计划阶段的资产核对**（读了 URDF 原文，标注为 Verified），但**所属方案从未执行**，因此"解决方案"一栏**未经运行验证**。

<a id="q35"></a>
### Q35 · `g1_29dof.urdf` 里找不到夹爪关节

**Q**：计划中要控制 `gripper_l_joint` / `gripper_r_joint`，URDF 里搜不到。

**A**：**`g1_29dof.urdf` 根本没有夹爪关节。**它只有 29 个 revolute 关节（腿 12 + 腰 3 + 双臂 14）；手是通过 `right_hand_palm_joint`（`type="fixed"`）连到 `right_rubber_hand` 的**固定链接**，不可驱动。

1. 先核对实际关节清单：
   ```bash
   grep -n '<joint' g1_29dof.urdf | grep -v 'type="fixed"'
   ```
2. 需要可驱动手部时改用 **43-DOF 带手 URDF**，做 Omnipicker 式三指协调控制。
3. ⚠️ **未验证**：PI0 类策略通常是用 1–2 DOF 的 omnipicker 训练的，映射到多指手只是近似。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.8 `P35`

---

<a id="q36"></a>
### Q36 · 从 Isaac Sim 抄来的链接名在 Genesis 里找不到

**Q**：`head_link2` / `gripper_l_base_link` / `gripper_r_base_link` 在 Genesis 里 `get_link()` 全部报找不到。

**A**：**这些是 Isaac Sim USD 的 prim 路径片段，不是 URDF 链接名。**两者命名体系不同，不能直接照抄。

1. 用 URDF 里真实存在的名字替换，本次对应关系为：
   | Isaac Sim（USD prim） | Genesis（URDF link） |
   |---|---|
   | `head_link2` | `head_link` |
   | `gripper_l_base_link` | `left_wrist_yaw_link` |
   | `gripper_r_base_link` | `right_wrist_yaw_link` |
2. 通用做法是**运行时枚举**而非硬编码（同 [`Q04`](#q04)）：
   ```python
   print([l.name for l in robot.links])
   ```

### 附：Isaac Sim → Genesis 迁移检查清单（10 条）

本项目唯一可跨项目复用的产物。⚠️ **整体未经执行验证。**

1. 资产用 **URDF** 替代 USD。
2. 固定基座用 `fixed=True` 替代浮动基座 + 锚定约束。
3. **运行时发现 DOF 索引**，不要硬编码。
4. 控制用 `control_dofs_position()` 替代 `set_joint_positions()`。
5. **Genesis 必须显式 `set_dofs_kp` / `set_dofs_kv`**（PhysX 的 joint drive 增益不会自动带过来）。
6. 相机是**场景级**的，**不能挂到链接上**，需手动每步跟踪链接位姿。
7. 深度图是浮点米，按需自行转整数。
8. `render()` **返回元组**（见 [`Q18`](#q18)）。
9. 用 `links_to_keep` 保留挂载用的链接，避免被合并优化掉。
10. 步进用 `scene.step()` 替代 `world.step()`。

**相关经验**：[`ai_knowledge.md`](ai_knowledge.md) §4.8 `P36` · 教训 `L05`

---

## 贡献指南

### 什么时候该往这里加一条

满足**任意一条**即值得记录：

- 报错信息**无法直接搜到答案**，或搜到的答案是错的。
- 排查耗时**超过 30 分钟**。
- 现象是**静默失效**（不报错、日志正常，但行为不对）——这类最值钱。
- 你试过的某个方案**看起来很合理但无效**——"无效尝试"和正确答案同样重要。

### 怎么加

1. **先在 [`ai_knowledge.md`](ai_knowledge.md) §4 追加 `Pxx`**（本篇是派生层，**不是新事实来源**）。取当前最大编号 +1，**只追加、不重排、不复用编号**。
2. 回到本篇，用**相同数字**追加 `Qxx`（`Qxx` ↔ `Pxx` 永久一一对应）。
3. 放进合适的类别（A–H）；若都不合适，新开一节并在文首「按类别浏览」加入。
4. **在顶部「快速症状索引」表加一行**——带着报错来的人只看这张表。索引项要写**用户实际会看到的字符串**（报错原文关键字 / 现象描述），不要写你的诊断结论。
5. 加锚点 `<a id="qxx"></a>`，与索引表的链接对应。

### 每条必须包含

| 字段 | 要求 |
|---|---|
| **Q** | 现象，一两句。写**观察到什么**，不写**你以为是什么**。 |
| **A** | 可执行的步骤 / 代码。多方案时标明推荐哪个、各自适用场景。 |
| **❌ 无效尝试** | 试过但没用的方向。**这一项经常比答案更省时间。** |
| **相关经验** | 回指 [`ai_knowledge.md`](ai_knowledge.md) 的 `Pxx`，有对应教训则一并标 `Lxx`。 |

### 三条硬约束

- **无解就直说**：写「**未解决，建议参考详细记录**」，并说明卡在哪里、已排除了什么。**不要编造解法**。
- **脱敏**：不得出现账号、密码、密钥、token；本机路径写 `<user_home>` / `<path>`，主机地址写 `<host>` 或 `<INFER_IP>:<PORT>`。
- **标版本**：新条目若不是在 genesis-world 1.2.2 上实测的，**必须在条目内注明实测版本**——本篇的默认版本前提见文首。

### 同步更新

修改本篇后，请同步项目索引 [`00-index.md`](00-index.md) 的行号表与条目计数（行号会随内容漂移，建议用脚本重算 `grep -n '^#\{2,3\} '` 而非手工推算）。
