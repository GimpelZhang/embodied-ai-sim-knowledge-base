# LW-BenchHub 常见问题与解决方案

> **文档性质**：本文档是 [`ai_knowledge.md`](ai_knowledge.md) 第 4 章按**故障类别**重排的 Q&A 视图，**不是新的事实来源**。两者是同一批事实的两个视图（`Qxx` ↔ `Pxx` **一一对应**），**不必两边都读**：
> - **带着报错来** → 用本文档（顶部「快速症状索引」→ `Qxx`）。
> - **想知道为什么会这样、试过哪些无效方法、当时怎么决策** → 读 `ai_knowledge.md`。
>
> **⚠️ 证据等级**：全篇为 `[实践]` 级，即本机一次具体复现过程中的踩坑记录，**不是官方结论**。上游版本迭代后部分现象可能已消失。需要 `[CODE]` / `[README]` 级证据请查 [`background_knowledge.md`](background_knowledge.md)。
>
> **隐私处理**：本机绝对路径统一写作 `<path>`，用户目录写作 `<user_home>`；不含任何账号、口令、密钥、token。
>
> **环境基线**（现象能否复现取决于此）：Ubuntu 22.04 无显示器 / A800-40GB `sm_80` / 驱动 580.159.03 / Python 3.11 / Isaac Sim 5.1.0 / Isaac Lab v2.3.2 / IsaacLab-Arena `release/0.1.1` / lw_benchhub 0.1.0 (`-e`) / lerobot 0.5.1 / torch 2.7.0+cu128 / numpy **1.26.0** / warp-lang **1.8.1**。

---

## 快速症状索引

**按你看到的报错文本或现象查。** 同一现象可能对应多条，按序号先后排查。

### 安装与启动期

| 现象 / 报错文本 | 去哪 |
|---|---|
| `':/usr/local/cuda-11.8/bin/nvcc'` 这种带冒号的路径报错 | [`Q01`](#q01) |
| LFS 资产是空文件 / headless 渲染起不来 / Isaac Sim 拒绝启动 | [`Q02`](#q02) |
| 随机 `ImportError` 或 Segfault，尤其在 Isaac Sim 的 C 扩展里 | [`Q03`](#q03) ⭐ |
| Vulkan `vkCreateDevice` 失败 / GPU PhysX 或 RTX 渲染器异常 | [`Q04`](#q04) |
| `ImportError: cannot import name 'CONFIGS_PATH' from 'lw_benchhub'` | [`Q05`](#q05) |
| 一连串 `ModuleNotFoundError`（`lazy_import`、`tyro`、`casadi` 等） | [`Q06`](#q06) |
| `pinocchio is required for PiperPinocchioIK` | [`Q07`](#q07) |
| `AttributeError: 'PiperPinocchioIK' object has no attribute '_model'` | [`Q07`](#q07) |
| `ImportError: DEVICE_MAP from teleop_device_factory` | [`Q08`](#q08) |
| `ImportError: ENDPOINT from lightwheel_sdk.loader` | [`Q08`](#q08) |
| `ValueError: ... is not a xformable prim with standard transform operations` | [`Q09`](#q09) |
| `CUDA mismatch 11.8 vs 12.8` / `import curobo` 直接 segfault | [`Q10`](#q10) |
| `AttributeError: module 'warp.types' has no attribute 'array'` | [`Q11`](#q11) ⭐ |
| `LookupError: setuptools-scm was unable to detect version for curobo` | [`Q12`](#q12) |
| cuRobo 编译报 `cuda.h not found` / 编译期 OOM / `CXXABI_1.3.15 not found` | [`Q13`](#q13) |
| 运行脚本立刻 `unbound variable` 就中止了 | [`Q14`](#q14) |
| Isaac Sim 在相机初始化时**直接 segfault、无 traceback** | [`Q15`](#q15) ⭐ |
| `cudaErrorIllegalAddress`（在分配 USD 纹理时） | [`Q16`](#q16) |

### 评测与推理期

| 现象 / 报错文本 | 去哪 |
|---|---|
| 视频只有 2 秒 / 50 个 episode 只出 10 个视频 / 进程"提前"结束 | [`Q17`](#q17) |
| 加载 checkpoint 时报几百个 key 不匹配，但只有一句 warning | [`Q18`](#q18) |
| **机器人只轻微抽搐、不伸向目标、成功率 0%，动作数值近零** | [`Q19`](#q19) ⭐⭐ |
| 想给单相机 VLA 加左右手相机 | [`Q20`](#q20) |
| 找不到 `eval_info.json` / 取不到成功率 / 退出码显示成功但其实报错了 | [`Q21`](#q21) |
| 换任务或换场景后成功率一律 **0%** | [`Q22`](#q22) |
| `gym.NameNotFound: <某 task>` | [`Q23`](#q23) |
| Isaac Sim boot 阶段**无限挂起、无任何输出** | [`Q24`](#q24) ⚠️ 未根治 |

### 场景生成与配置期

| 现象 / 报错文本 | 去哪 |
|---|---|
| 按计划/文档写的场景配置完全跑不通 | [`Q25`](#q25) |
| 脚本"在调难度"、日志也在正常汇报，但难度**毫无变化** | [`Q26`](#q26) ⭐ |
| LLM 返回 200，但怀疑用的不是请求的模型 | [`Q27`](#q27) |
| 某个 seed 挂几小时，日志里 `scene retry 1/5` 重复上百次 | [`Q28`](#q28) |
| `SamplingError`（物体放不下） | [`Q28`](#q28) |

### scripted cuRobo 管线期

| 现象 / 报错文本 | 去哪 |
|---|---|
| **管线报告 `success=True` / "6/6 技能成功"，但任务其实没完成** | [`Q29`](#q29) ⭐⭐ |
| 观察到目标物体被"推开"了几厘米到十几厘米 | [`Q30`](#q30) ⭐⭐⭐ |
| `RuntimeError: shape mismatch: value tensor of shape [N] cannot be broadcast to indexing result of shape [N, 1]` | [`Q31`](#q31) ⚠️ 未根治 |
| 碰撞球配置改完了，但碰撞检测像没生效 / `total_spheres=0` | [`Q32`](#q32) |
| 给手指 link 加碰撞球后报"不存在的关节名" `ValueError` | [`Q32`](#q32) |
| 某个技能在 **`1 steps`** 就退出了 | [`Q33`](#q33) |
| 腕部到位了但真实手指差 0.3 m，接触力全程 0 N | [`Q34`](#q34) ⚠️ 未解决 |

### 数据集生成与基础设施

| 现象 / 报错文本 | 去哪 |
|---|---|
| "一 episode 一进程"跑出 0 成功，单进程顺序跑却正常 | [`Q35`](#q35) ⭐ |
| `terminated=True` 的 episode 被判为失败、数据未保存 | [`Q35`](#q35) ⭐ |
| 进程退出了、数据也存了，但日志**缺尾**（无完成标记行） | [`Q35`](#q35) |
| `pkill -9 -f "isaacsim"` 返回 exit 1 且杀不掉 / 把自己的 shell 杀了 | [`Q35`](#q35) |
| 数据集导出崩 `KeyError: observations/qpos` | [`Q35`](#q35) |
| 数据集导出耗时约 40 分钟 | [`Q36`](#q36) ⚠️ 未解决 |
| 长跑管线崩溃只有一行错误摘要，看不到调用栈 | [`Q37`](#q37) |
| LLM API 调用在 Isaac Sim 进程内概率性 segfault、无 traceback | [`Q38`](#q38) |

---

## A. 环境与安装类

<a id="q01"></a>
### Q01 · nvcc 路径查找失败，报错路径带前导冒号

**Q**：编译或调用 nvcc 时报错，路径形如 `':/usr/local/cuda-11.8/bin/nvcc'`（注意开头的冒号）。

**A**：
1. 检查 `echo "$CUDA_HOME"`，若输出以 `:` 开头即命中。
2. 重设为不带冒号的路径：`export CUDA_HOME=/usr/local/cuda`。
3. 若是 shell 配置文件里拼接出来的（形如 `CUDA_HOME=$X:/usr/local/cuda-11.8` 而 `$X` 为空），修掉那处拼接。

**相关经验**：`P01`

---

<a id="q02"></a>
### Q02 · LFS 资产为空 / headless 渲染起不来 / Isaac Sim 拒绝启动

**Q**：三种表现之一：仓库里的 USD、示教资产是几十字节的指针文件；EGL 离屏渲染初始化失败；Isaac Sim 报 Python 版本不符。

**A**：逐项体检三个前置条件（这三项在纯净云主机上**默认都不满足**）：
1. **git-lfs**：`git lfs version` 无输出就装它，然后在仓库内 `git lfs pull`。LW-BenchHub 的 USD / 示教资产全靠 LFS。
2. **EGL 库**：确认 `libnvidia-egl-*` 系列已安装 —— 这是 headless 渲染的关键依赖，缺失时报错往往不直接指向 EGL。
3. **Python 版本**：Isaac Sim 需要 **3.11**。若系统是 3.12，用 conda 单独建 3.11 环境，不要在系统 Python 上装。

**建议顺序**：先解决这三项，再动 Isaac Sim 本身 —— 否则后续报错会互相掩盖。

**相关经验**：`P02`

---

<a id="q03"></a>
### Q03 · ⭐ 随机 `ImportError` 或 Segfault（尤其在 Isaac Sim 的 C 扩展里）

**Q**：明明昨天还能跑，今天装了个包就开始随机崩；或 Isaac Sim 的 C 扩展在 import 期 Segfault。

**A**：**第一件事是查 numpy 版本**。
1. `python -c "import numpy; print(numpy.__version__)"` —— 必须是 **1.26.0**。Isaac Sim 5.1.0 的 C 扩展编译期硬绑该版本。
2. 不是就强制回锁：`pip install --no-deps numpy==1.26.0`。
3. **建立纪律**（这是本次复现中重复次数最多的动作）：
   - 装环境时，其它依赖**先**装，numpy **最后**装；
   - 此后**每一次** `pip install` 之后都立刻回锁一遍 —— 尤其是带 extra 的安装（形如 `pip install -e ".[xxx]"`），它们几乎必然把 numpy 顶到 2.x；
   - 在环境脚本尾部加一句 assert 校验，让不匹配立刻暴露而不是等到运行时 Segfault。

**相关经验**：`P03`、`L06`

---

<a id="q04"></a>
### Q04 · Vulkan 失败 / GPU PhysX 或 RTX 渲染器异常

**Q**：`vkCreateDevice` 报错，或 GPU PhysX、RTX 渲染器无法工作。

**A**：
1. 对比驱动的**内核模块版本**与 **GL 库版本**是否一致（本次遇到的是内核模块 535.113.01 而 GL 库 535.309.01，**两者不匹配**）。
2. 升级驱动到 **580.159.03**（本次实测可用版本）。
3. 顺带确认三个 headless 相关环境变量已设：`DISPLAY`（配合 Xvfb 虚拟显示）、`HDF5_USE_FILE_LOCKING=FALSE`（防 HDF5 文件锁冲突）、`PYTHONUNBUFFERED=1`。

**❌ 无效尝试**：装 535.309.01 的 DKMS 版本求"版本对齐" —— Vulkan `vkCreateDevice` 仍然失败，必须升到 580 系。

**相关经验**：`P04`

---

<a id="q05"></a>
### Q05 · `ImportError: cannot import name 'CONFIGS_PATH' from 'lw_benchhub'`

**Q**：从仓库目录**之外**启动 Python 时，`from lw_benchhub import CONFIGS_PATH` 直接 ImportError；在仓库目录内却正常。

**A**：根因是**包遮蔽** —— 仓库外层有一个 `pkg_resources.declare_namespace` 存根（不含 `CONFIGS_PATH`），内层才是真包；当 `sys.path[0]` 为空（即从别处启动）时，默认 path finder 命中外层存根。
1. 备份外层 `__init__.py`。
2. 把它重写为 `importlib.util` shim：用 `spec_from_file_location` 加载**内层真包**，再 `sys.modules[__name__] = inner` 重新导出。
3. 从**至少 3 个不同 cwd** 验证 `from lw_benchhub import CONFIGS_PATH` 均成功。

**❌ 无效尝试**（4 种全失败，traceback 都指回同一个文件）：从 `sys.path` 里剔除条目 / 预先导入内层包 / 只改外层的导出列表 / 把调用脚本移进包内。

**⚠️ 附带风险**：这是**本地补丁**。`git submodule update --init --recursive --force` 或 pull 会把它抹掉，之后必须重验 import。

**相关经验**：`P05`

---

<a id="q06"></a>
### Q06 · 一连串 `ModuleNotFoundError`

**Q**：启动时接连报缺模块（`lazy_import`、`tyro`、`casadi`、`qpsolvers`、`vuer` 等），装一个又冒一个。

**A**：根因是 `pyproject.toml` **漏声明了 9 个运行期依赖**，只能批量补装。两个必须精确的点：
- **`qpsolvers` 必须精确 `==4.8.1`**（其它版本 API 不兼容）；
- **`vuer` 必须带 `[all]` extra**，否则缺子依赖。

补装完**立刻回锁 numpy**（见 [`Q03`](#q03)）。

**相关经验**：`P06`

---

<a id="q07"></a>
### Q07 · `pinocchio is required for PiperPinocchioIK` / `has no attribute '_model'`

**Q**：报缺 pinocchio；装上之后又报 `AttributeError: 'PiperPinocchioIK' object has no attribute '_model'`。

**A**：根因是 cmeel 分发的 pinocchio wheel **不含 `pinocchio.casadi` 绑定**，所以装上了也用不了。
1. 把该 IK 类的 `__init__` 从"直接 `raise ImportError`"改为 **lazy stub**（置 `_is_stub=True` 而不抛异常），避免硬 raise 阻断整条启动链。
2. 给 `reset()` 补 stub 守卫，修掉 `_model` 缺失的 AttributeError。

**⚠️ 这是双刃剑**：改成 stub 后流程能跑通，但该 IK **实际不可用** —— 任何 `solve_*` 调用都会 raise。**不要在后续开发中把它当可用 IK 去调用**（这个坑真实发生过，见 [`Q32`](#q32) 的无效尝试）。需要 IK 请用 cuRobo 的求解器（已验证残差 <1 cm）。

**相关经验**：`P07`、`L06`

---

<a id="q08"></a>
### Q08 · `ImportError: DEVICE_MAP` / `ImportError: ENDPOINT`

**Q**：报 `ImportError: DEVICE_MAP from teleop_device_factory`，或 `ImportError: ENDPOINT from lightwheel_sdk.loader`。

**A**：两者都是**上游 API 漂移**，不是你装错了：
- IsaacLab v2.3.x **移除了** `DEVICE_MAP` / `RETARGETER_MAP` → 给对应的 teleop 补丁函数加 `try/except`，缺失时**优雅跳过**（本次复现不需要 teleop 设备）。
- lightwheel SDK 1.0.3 把 `ENDPOINT` 从 `.loader` **搬到了 `.client`** → 给该 import 加 fallback 分支，两个位置都试。

**相关经验**：`P08`

---

<a id="q09"></a>
### Q09 · `ValueError: ... is not a xformable prim with standard transform operations`

**Q**：加载某些 SimReady USD 场景资产时报此错，无法启动。

**A**：根因是 IsaacLab v2.3.x **强校验** xform op 顺序为 `[translate, orient, scale]`，而涉事资产用的是 `[translate, rotateXYZ, scale]`。
1. 新增一个补丁函数，强制 `validate_xform_ops=False` 关掉该校验。
2. 在脚本入口**显式调用**该补丁（连同 [`Q08`](#q08) 的 teleop 补丁一起），不要指望它自动生效。

**❌ 无效尝试**：调用 `standardize_xform_ops()` 就地把 op 顺序改标准 —— 涉事 prim 来自**子图层**且 Sdf 写权限被拒，改不了。

**相关经验**：`P09`

---

<a id="q10"></a>
### Q10 · `CUDA mismatch 11.8 vs 12.8` / `import curobo` 直接 segfault

**Q**：编译 cuRobo 时报 CUDA 版本不匹配；或强行装上后 `import curobo` 直接 segfault。

**A**：根因是**系统 nvcc 版本与 torch 编译时的 CUDA 版本不一致**（本次是系统 11.8 vs torch cu128）。**不要动系统、不需要 sudo**：
1. 在 conda 环境内装匹配版本：`conda install -c nvidia/label/cuda-12.8.1 cuda-toolkit`（约 5 GB / 数分钟）。
2. **让它优先于系统 nvcc**：`export CUDA_HOME=<conda_env_root>` 且 `export PATH=$CUDA_HOME/bin:$PATH`。
3. 用 `which nvcc` 确认解析到的是 env 内那个，不是系统的。
4. **装完立刻回锁 numpy**（见 [`Q03`](#q03)）—— conda 装 CUDA 会拉高 numpy。
5. 若同时还报头文件/OOM/ABI 问题，一并看 [`Q13`](#q13)。

**为什么值得这么做**：这条路径既不需要 sudo，也不会破坏已跑通的其它环境 —— 是本次复现中最有复用价值的做法之一。

**相关经验**：`P10`、`D07`

---

<a id="q11"></a>
### Q11 · ⭐ `AttributeError: module 'warp.types' has no attribute 'array'`

**Q**：构建 cuRobo IK 时（或 Isaac Sim import 期）报此错。

**A**：根因是**两个库 pin 了冲突的 warp 版本**：pip 默认拉 `warp-lang 1.14.0`（已删除该 legacy 属性），它污染 `sys.modules` 后，Isaac Sim 自带的 warp 模块在 import 期崩溃。
1. `pip install --no-deps warp-lang==1.8.1`
2. **立刻回锁 numpy**（见 [`Q03`](#q03)）。
3. 验证：先 import isaaclab 再 `from curobo.types.base import TensorDeviceType`，不报错即通。

**为什么是 1.8.1**：Isaac Sim 5.1 自带的是 `omni.warp.core 1.8.2`，但 **1.8.2 不在 PyPI 上**（PyPI 版本从 1.7.2 直接跳到 1.8.0），**1.8.1 是同 minor 系列唯一可得的版本**。

**❌ 无效尝试**（4 种缓解全失败）：预先 import cuRobo 抢占 `sys.modules` / 设 PRETEND_VERSION 环境变量 / 重命名 `curobo/.git` / 调换两者 import 顺序。**同进程内的 ABI 冲突无法靠 import 顺序绕开。**

**⚠️ 这是软锁**：它只针对 Isaac Sim 5.1。升级 Isaac Sim 后必须重新探测自带 warp 版本并重新选 pin。

**相关经验**：`P11`

---

<a id="q12"></a>
### Q12 · `LookupError: setuptools-scm was unable to detect version for curobo`

**Q**：在 Isaac Lab **之后** import cuRobo 时报此错（单独 import cuRobo 却正常）。

**A**：根因是 cuRobo 在 import 期走 `setuptools_scm` 探测版本，而在 Isaac Lab 之后 import 时，Python 解析到的是 **Isaac Sim 私有打包的那份 setuptools_scm 拷贝**，那份拷贝**忽略 `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_*` 环境变量并直接抛错**。
1. 备份 cuRobo 的 `__init__.py`。
2. 改它：在**任何** setuptools_scm 逻辑**之前**先读 `SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO` 环境变量，读到就直接返回。
3. 该环境变量仍需在运行脚本里 export。

**❌ 无效尝试**：只设那个环境变量而不改源码 —— 私有拷贝不认它。

**⚠️ 本地补丁**：submodule 强制更新会抹掉，pull 后需重验（同 [`Q05`](#q05)）。

**相关经验**：`P12`

---

<a id="q13"></a>
### Q13 · cuRobo 编译报 `cuda.h not found` / 编译期 OOM / `CXXABI_1.3.15 not found`

**Q**：cuRobo 源码编译过程中的三类失败。

**A**：分别对应三个独立原因：

| 现象 | 原因 | 处理 |
|---|---|---|
| `cuda.h not found` | conda 把 CUDA 头文件放在 `$CUDA_HOME/targets/x86_64-linux/include/`，而编译器只找 `$CUDA_HOME/include/` | 建**符号链接**把前者的头文件链到后者。建议写进 env 脚本，首次 source 时自动执行 |
| 编译期 OOM | 默认并行度过高 | `export MAX_JOBS=4` |
| `libstdc++.so.6: CXXABI_1.3.15 not found` | 系统 libstdc++ 版本旧于编译产物要求 | 调 `LD_LIBRARY_PATH` 指向 conda env 内较新的 libstdc++ |

**另外必设**：`export TORCH_CUDA_ARCH_LIST="8.0"`（A800 是 `sm_80`）—— **不设会对所有架构编译，耗时数小时**。

**编译耗时参考**：A800 上约 15–25 分钟。

**相关经验**：`P13`

---

<a id="q14"></a>
### Q14 · 运行脚本立刻 `unbound variable` 中止

**Q**：脚本刚启动就报某个变量未绑定（如 `NVCC_PREPEND_FLAGS`）并退出。

**A**：根因是 conda 的 CUDA 激活脚本引用了未绑定变量。
- 运行脚本必须用 **`set +u`**，**不能用 `set -u`**。

**⚠️ 不要"优化"回去**：原始记录里写着 "Hours were lost on this before changing to `set +u`. Do NOT switch back."

**相关经验**：`P14`

---

<a id="q15"></a>
### Q15 · ⭐ Isaac Sim 在相机初始化时直接 segfault、无 traceback

**Q**：启用相机的评测脚本一到相机初始化就 segfault，**没有任何 Python traceback**。

**A**：
1. 运行前 **`unset CUDA_VISIBLE_DEVICES`** —— Isaac Sim 自行枚举显卡，设了该变量会让带相机渲染的脚本直接 Segfault。
2. **⚠️ 该 unset 不能写进 shell 配置文件**（会影响其它工具），只在每次评测前、在运行脚本里执行。
3. 若仍崩，检查 EGL 库是否缺失（见 [`Q02`](#q02)）。

**"无 traceback" 本身就是线索**：Python 级异常会有 traceback，纯 segfault 通常指向底层库的设备/驱动/ABI 问题，而不是你的代码逻辑。

**相关经验**：`P15`

---

<a id="q16"></a>
### Q16 · `cudaErrorIllegalAddress`（在分配 USD 纹理时）

**Q**：同一进程内既用 Isaac Sim 又用 cuRobo，在 Isaac Sim 分配 USD 纹理时崩 `cudaErrorIllegalAddress`。

**A**：**初始化顺序错了。**
- **必须先启动 Isaac Sim，再构建 cuRobo IK / MotionGen。反序必崩。**
- 具体做法：把 `AppLauncher` 的启动放在最前面，cuRobo 的 import 与求解器构建**都**放在其后（注意 import 本身也算，见 [`Q12`](#q12)）。

**相关经验**：`P16`

---

## B. 策略推理与评测类

<a id="q17"></a>
### Q17 · 视频只有 2 秒 / 50 个 episode 只出 10 个视频 / 进程"提前"结束

**Q**：评测跑完，但三个现象看着都像故障。

**A**：**三者都不是故障**，逐条对应：

| 现象 | 真实原因 | 要改就改这里 |
|---|---|---|
| 视频只有 2 秒 | 环境配置 `episode_length_s=2.0`，配合 `dt` / `decimation` → 每 episode 恰好 100 步 → 50 fps 下正好 2.0 秒 | 改环境配置的 `episode_length_s` |
| 50 个 episode 只录 10 个视频 | 评测脚本里 `max_episodes_rendered` 是**硬编码**的 | 改脚本里那个硬编码值 |
| 进程在"还剩 40 个 episode"时结束 | **是正常完成**（本次实测总耗时约 3202 秒 / 平均 64 秒每 episode） | 无需处理 |

**❌ 无效尝试**：当成 OOM 或崩溃去排查。

**⚠️ 相关设计事实**：`episode_length_s` 之外的一些行为参数**确实被写死在代码里** —— 找不到某个配置项，可能是它真的不存在。详见原理层 §6 的"改行为对照表"。

**相关经验**：`P17`

---

<a id="q18"></a>
### Q18 · 加载 checkpoint 时报几百个 key 不匹配，但只有一句 warning

**Q**：日志里有一句 warning 提到几百个 key（本次是 437 个）不匹配，程序照常继续跑。

**A**：**这不是可以忽略的 warning —— 它意味着那部分权重是随机初始化的**（本次是视觉编码器，导致模型实际"看不见"）。
1. 对比 safetensors 里的**实际键路径**与模型**期望的键路径**。本次是实际为 `vision_tower.vision_model.*` 而期望 `vision_tower.*`。
2. 在模型代码的键名修复函数里做**真正的重映射**（本次是去掉多余的 `vision_model.` 一段），而不是只打 warning。
3. 验证：加载日志应出现 "All keys loaded successfully!"。

**⚠️ 重要**：本次修完这条之后**机器人仍然不动** —— 它只是并列问题之一，**不是主因**。主因见 [`Q19`](#q19)。不要因为修了一个真 bug 就认为问题结束了。

**相关经验**：`P18`、`L06`

---

<a id="q19"></a>
### Q19 · ⭐⭐ 机器人只轻微抽搐、不伸向目标、成功率 0%，动作数值近零

**Q**：VLA 闭环能跑完，视频里机器人只有单臂轻微抽搐、完全不朝目标运动，成功率 0%；打印出的动作数值接近 0。

**A**：**优先查 checkpoint 的 `config.json` 里有没有编译开关。**
1. 找到 HF 缓存里该 checkpoint 的 `config.json`，检查是否有 `compile_model: True`（本次还伴随 `compile_mode: max-autotune`）。
2. **备份该 blob**（复制为 `.bak`），然后把 `compile_model` 改为 `False`。
   - ⚠️ 必须改**缓存里那份**。见下方说明。
3. 加动作诊断日志，验证修复：本次修好后动作 `absmean≈0.6, std≈0.7`，与训练数据的 `action.std`（0.68）吻合，视频里双臂均有明显运动。

**根因**：模型代码读到该字段后会对推理函数调 `torch.compile(mode='max-autotune')`，而该模型的动态计算图在此模式下**解算错误**，输出近零动作。

**❌ 无效尝试**：
- **只设 `TORCH_COMPILE_DISABLE=1` / `TORCHINDUCTOR_DISABLE=1` 环境变量 —— 无效。** 环境变量关不掉代码里**显式写死**的 `torch.compile()` 调用（见 `L04`）。
- 怀疑 pip 装 extra 时篡改了 numpy —— 实测就是 1.26.0，假设被排除。
- 怀疑 headless EGL 黑屏让 VLA 看不见 —— 抽帧显示场景画面清晰，假设被排除。

**⚠️ 为什么必须改缓存里那份**：评测栈实际执行的是 **HF 缓存中的副本**，不是你本地仓库里的文件（详见 [`Q22`](#q22) 说明的"双副本"现象）。改本地仓库不生效。

**⚠️ 修完仍是 0% 怎么办**：性质已经不同了 —— 动作有效但精度不够。本次修完后判定剩余 0% 属**模型能力边界**：训练数据本身只有约 2 秒演示（`timestamp.max≈2.02s`），超出工程修复范围。见 [`Q22`](#q22)。

**相关经验**：`P19`、`L04`

---

<a id="q20"></a>
### Q20 · 想给单相机 VLA 加左右手相机来提升成功率

**Q**：模型只用头视角一路相机，想加左右手相机改善表现。

**A**：**先验证模型架构是否支持，再动手 —— 大概率不支持。** 四步核查（本次四步全部指向"不可行"）：
1. 查模型的**归一化统计**里有几个相机键。本次只有 1 个。
2. 查模型代码怎么处理空相机槽。本次是填 -1 且 **mask=0** —— **架构被训练为忽略第 2/3 路**，加了也不看。
3. **铁证：查训练数据集的元信息**（`meta/info.json`）里有几个相机特征。本次只有 1 个 —— 模型从未见过多相机输入。
4. 查同厂商同系列的其它 checkpoint。本次遍历全家族**均为单相机**，且部分还需独立推理栈、不兼容当前评测 CLI。

**结论**：要真用 3 相机，**必须重新采数 + 重训**，不是配置层能解决的。

**❌ 无效尝试**：直接在环境侧加 2 路相机输入 —— 架构层已 mask 掉。

**💡 反向参考**：本次路径 B 用的模型**原生就是 3 路相机**（左手/右手/第一人称）且成功率 40%。**换一个原生多相机的模型，比给单相机模型加相机现实得多。**

**相关经验**：`P20`

---

<a id="q21"></a>
### Q21 · 找不到 `eval_info.json` / 取不到成功率 / 退出码说成功但其实报错了

**Q**：想自动化采集评测指标，但拿不到或拿错。

**A**：三个独立陷阱，**都要处理**：

| 陷阱 | 处理 |
|---|---|
| **评测 CLI 不写 `eval_info.json`** | 必须从**日志**里 grep `running_success_rate` |
| **`running_success_rate` 是百分数**（`20.0` 表示 20%） | 存成分数前必须 **`/100`** |
| **评测进程可能在 RuntimeError 之后仍 exit 0** | 真实退出码要从日志里的 `EXIT_CODE:` 行**反推**，**不能信 `$?`** |

**验证脚本建议**：三项一起断言 —— 取到了成功率、值域在 `[0, 100]`、日志里有 `EXIT_CODE: 0`。

**相关经验**：`P21`、`L06`

---

<a id="q22"></a>
### Q22 · 换任务或换场景后成功率一律 0%

**Q**：某个任务上有正常成功率，换成别的任务/场景就一律 0%。怀疑接口接错了。

**A**：**先判断是 OOD 还是接口 bug。本次的结论是 OOD，不是接口 bug。**

判断依据（本次的核查链，可照做）：
1. **checkpoint 是在哪些任务上微调的？** 本次的模型只在**单一任务**上微调过 → 同任务稳定 40%，跨任务 0%。
2. **观测/动作契约核对**：键名、动作维度、图像分辨率逐项核实。本次全部正确。
   - 关于分辨率：环境渲染分辨率与模型声明的输入尺寸**确实不同**，但策略侧会**自适应 resize** → **与 OOD 无关**，不用改。
3. 若 1 成立而 2 无异常 → **判定为分布外泛化失败，属模型能力边界**。

**⚠️ 未解决（也无需解决）**：这不是可修的 bug。**要提升只能换模型或做微调，改任何接口都无效。**

**💡 顺带一条容易踩的认知**：评测栈并**不直接 import** 本工具链 —— 它下载 HF Hub 上的环境定义文件并在 `trust_remote_code` 下执行，由那份**远端代码**再 import 本地包。因此存在**"双副本"现象**：本地仓库的改动不一定生效，缓存里那份才是运行时真身（这与 [`Q19`](#q19) 必须改缓存 blob 是同一根因）。

**相关经验**：`P22`、`D13`

---

<a id="q23"></a>
### Q23 · `gym.NameNotFound: <某 task>`

**Q**：从任务映射 CSV 里挑的 `(layout, task)` 组合，运行时报找不到该 task。

**A**：根因是**该组合在 CSV 里合法，但对应的 task 并未在 Gymnasium registry 注册**。CSV 与 registry **不是一一对应的**。
1. 生成/选择组合前，先对 registry 做 grep 核实（找 `register(id=...)` 调用处），只用真实注册过的 ID。
2. 自动化生成场景时，让校验器**捕获该异常** → 把该 pair 加入 **ban 列表** → 重新生成（设一个最大轮数上限）。

**相关经验**：`P23`、`L02`

---

<a id="q24"></a>
### Q24 · Isaac Sim boot 阶段无限挂起、无任何输出

**Q**：某些 layout/task 组合下，Isaac Sim 在启动期卡死，无任何输出，CPU 却在跑。

**A**：
1. 确认是挂起而非慢：本次实测烧掉 **58 分钟** CPU 无任何进展。
2. **只能人工 `pkill -9`** 回收（注意用方括号技巧避免自杀，见 [`Q35`](#q35)）。
3. **建立纪律**：任何 Isaac Sim 长跑都必须设**外部 wall-clock 超时**并预留强杀手段 —— 不要指望它自己恢复或自己报错。
4. 自动化流程里，把这类组合加入 ban 列表（同 [`Q23`](#q23)）。

**⚠️ 未根治**：本次没有定位到 boot 挂起的根因，只做了超时兜底。若需深究，建议从该 layout 的 USD 资产加载路径入手。

**相关经验**：`P24`、`L07`

---

## C. 场景生成与配置类

<a id="q25"></a>
### Q25 · 按计划/文档写的场景配置完全跑不通

**Q**：参照某份计划或文档写出的场景 YAML（形如显式声明 `objects.<name>.position`）根本不被识别。

**A**：**那套 schema 在本机不存在。** 先摸清真实结构再写生成器：
1. 实地读一份**能跑通的**示例配置，列出它真实有哪些顶层键。本次的真实 schema 是 `task` + `robot` + `scene_backend` + `task_backend` + `layout` 的**注册制三元组**。
2. **关键认知：物体位置根本不在配置里声明。** 它由 `sources` + `layout` + `seed` + 重采样开关共同决定 —— 所以没有"直接把碗挪到某个坐标"这种配置写法。
3. 让 LLM/生成器**只允许改白名单字段**：`task` / `layout` / `seed` / `episode_length_s` / 重试上限 / 重采样开关。
4. 用任务映射 CSV 做**本地 schema 校验**，拒掉 LLM 幻觉出的 `(layout, task)` 组合（并配合 [`Q23`](#q23) 的 registry 核实）。

**❌ 无效尝试**：按文档里看到的 schema 直接生成 —— 那套 schema 可能属于别的版本，或本就是臆想的。

**相关经验**：`P25`、`L02`

---

<a id="q26"></a>
### Q26 · ⭐ 脚本"在调难度"、日志也在正常汇报，但难度毫无变化

**Q**：脚本往配置里写了难度相关字段，日志还打印了诊断结论，但场景难度实际没有任何变化。

**A**：**大概率你写的键没有任何代码在读它，而"诊断结论"是硬编码的。**
1. **对每个自定义键 grep 它的读取处**：`grep -rn "<你的键名>" <仓库根>`。搜不到 → 它是一行无效注释。本次的 `scene_generation_difficulty: hard_offset_0.35` 就是如此。
2. **检查诊断输出是不是硬编码 print**。本次的"诊断结论"是一句写死的字符串，让日志看起来在正常工作 —— 这比字段无效本身更危险。
3. 改用**确实存在**的机制。本次替换为两个 grep 可证的真实机制：
   - **seed sweep**：扫一批 seed，取物体距机器人最远的那个作为"难"场景；
   - **`fix_object_pose_cfg`**：代码里已消费、已尊重的固定物体位姿机制，只需在配置层做**加法式**暴露。

**❌ 无效尝试**：追加自定义难度字段；相信硬编码的诊断输出。

**⚠️ 这是本次复现中复发至少 5 次的最高频错误类型**（另见 [`Q25`](#q25)、[`Q33`](#q33)）。铁律：**任何写进配置或计划的键 / 字段 / ID，落笔前必须 grep 到它的定义处或读取处。**

**相关经验**：`P26`、`D17`、`L02`

---

<a id="q27"></a>
### Q27 · LLM 返回 200，但怀疑用的不是请求的模型

**Q**：请求里指定了某个模型，HTTP 也返回 200，但输出质量像是弱模型。

**A**：**兼容端点会静默改写模型名降级。请求 payload 里写什么，不代表服务端跑什么。**
1. **唯一可靠的检查是回读响应体的 `model` 字段**并与期望值严格比对，不一致就报警中止（本次后期升级为直接 raise）。
2. 每次调用后打印 `[请求模型: X | 实际响应模型: Y]`，让降级立刻可见。
3. 配套三条实测兼容性处理：
   - 双鉴权头同发（`x-api-key` 与 `Authorization: Bearer`）；
   - `max_tokens` 必填（Anthropic Messages 协议）；
   - 用标准库 `urllib` 零依赖实现，避免第三方 SDK 的隐式重试掩盖问题。
4. 凭据放在权限 600 的独立 env 脚本里，**不入库**。

**❌ 无效尝试**：信请求参数里写的模型名。

**相关经验**：`P27`、`L06`

---

<a id="q28"></a>
### Q28 · 某个 seed 挂几小时，日志里 `scene retry 1/5` 重复上百次 / `SamplingError`

**Q**：两种表现：① 场景重试日志重复上百次、进程挂数小时不退；② 报 `SamplingError`（物体放不下）。

**A**：

**① 重试死循环** —— 根因是**场景重试计数器每次自增后又被模型重载重置**，导致代码里的 `max_scene_retry` 上限**永不触发**。
- 在调度器层加 **hang-killer**：统计日志里重试行的出现次数，超过阈值就直接 kill 该进程。
- **❌ 无效尝试**：依赖代码里的 `max_scene_retry` 配置 —— 它永远不会生效。

**② `SamplingError`** —— 根因是该 seed 采样出的物体离机器人**太近**（本次是约 0.23 m），放不下也够不到。
- 把课程 band 重定义为**可达范围 ≥0.26 m** 的三分位；
- 换成一个 fresh-boot 验证过的 seed。

**💡 通用做法**：任何"自动重试"机制都要在**外层**再加一道基于 wall-clock 或日志行数的兜底 —— 不要只信内层的重试上限（同 [`Q24`](#q24)）。

**相关经验**：`P28`、`L06`

---

## D. scripted cuRobo 管线类

> ⚠️ **本组是整个复现中最深刻的教训来源。动手排查前，强烈建议先读 [`Q29`](#q29) 和 [`Q30`](#q30)** —— 它们能帮你避免把大量时间花在错误的方向上。

<a id="q29"></a>
### Q29 · ⭐⭐ 管线报告 `success=True` / "6/6 技能成功"，但任务其实没完成

**Q**：scripted 管线报告全部技能成功、`success=True`，但没人验证过目标物体到底有没有到位。

**A**：**先假定这个 `success` 在撒谎，然后去证伪它。**
1. 检查技能序列执行器的返回逻辑。本次发现它在**两种情形**都返回 `success=True`：
   - 环境的 `terminated` 真触发（**这才是真成功**）；
   - **"所有技能都跑完了"（根本没检查任务条件）**。
2. 逐 episode 打印区分标志（本次是 `early_return`）。本次实测 **8 个 episode 全部 `early_return=0`** → **全部任务失败**。
3. 修复：在序列末尾**显式调用任务的成功检查接口**，与环境 `terminated` **用同一条件**判定。

**❌ 无效尝试**：相信"技能链跑完 = 成功"。

**⚠️ 为什么这是本次最危险的坑**：它**不报错、不崩溃**，只安静地把失败轨迹标成成功，**污染下游数据集**。任何要产出数据集的管线，成功判定都必须来自环境信号（见 `L05`，并注意 [`Q35`](#q35) 里"反过来也会错"的那种情形）。

**相关经验**：`P29`、`L05`

---

<a id="q30"></a>
### Q30 · ⭐⭐⭐ 观察到目标物体被"推开"了几厘米到十几厘米

**Q**：日志/记忆里记着目标物体在机械臂接近过程中被推开了一段距离（本次是 +0.109 m），准备去修这个"碰撞推挤"。

**A**：**停。先证明这件事真的发生了，再动手修。** 本次这个现象**根本不存在**，为它花掉的时间是整个复现中最大的一笔浪费。

按顺序做三件**便宜**的事：
1. **跑一次未打任何补丁的 baseline**，在**你要修的那个 seed / 那个场景**上，逐技能打印目标物体的世界坐标。
   - 本次第 10 次运行才第一次做了这件事 —— 结果碗从头到尾一动不动，272 帧 6 技能无报错。**原先记的 +0.109 m 是在另一个场景上观察到的。**
2. **埋一次接触力**（读 PhysX 的 `net_contact_forces`），确认夹爪是否真的碰到了物体。
   - 本次实测夹爪三个 link 全程 **`max_gripper_force = 0.000 N`** —— **从未接触**。物体的微小移动来自 `reset` + `plan` 阶段的**物理 settling**，不是碰撞。
3. 只有当 1 和 2 都确认现象存在，才去改碰撞模型。

**❌ 无效尝试**（三轮修复，各花大量时间，全部无效）：
- 调 grasp 的 z-offset；
- 加 pre-grasp hover（先到物体上方 20 cm 再下降）→ 物体被"推开"**同样的 +0.109 m**；
- 给夹爪加 mesh 碰撞 → 物体被推到**完全相同**的位置。

**⚠️ 三次"完全相同的结果"本身就是最强的警告信号**：如果你的修复改变了变量，结果却分毫不变，那么**变量根本没起作用**，或者**你修的问题不存在**。此时应停下来质疑问题本身，而不是提第 N 个假设（见 `L01` `L03`）。

**💡 本次 seed 48 的真实失败原因**是 grasp 闭合在空位 —— 根因见 [`Q34`](#q34)，与"推物体"毫无关系。

**相关经验**：`P30`、`L01`、`L03`

---

<a id="q31"></a>
### Q31 · `RuntimeError: shape mismatch: value tensor of shape [N] cannot be broadcast to indexing result of shape [N, 1]`

**Q**：在同一进程内做了多次批量规划之后崩此错，`N` 每次还不一样。

**A**：**这不是你的调用写错了。** 根因是"**同一进程内连续多次批量规划**"本身会触发 cuRobo 内部结果累积器的形状错配。
- 对照组很干净：原始管线只调 1–2 次批量规划**正常**，改版调 6+ 次就崩。
- **规划器的 `reset()` 救不回来** —— 它只清图规划缓冲与随机种子，**不清 per-batch 结果累积器**。

**处理（只能缓解，不能根治）**：
1. 给批量规划调用加 `try/except` 容错，让单次失败不炸掉整条管线。
2. **尽量减少同进程内的批量规划次数**（这是本次唯一真正有效的规避方式）。
3. 排查时**必须先打完整 traceback**，否则定位不到（见 [`Q37`](#q37)）。

**❌ 无效尝试**（9 次控制变量实验逐条排除 6 个假设）：关闭 CUDA graph 仍崩 / 对齐 seed 数量仍崩 / 预先构建 IK 求解器仍崩 / 规划后调 `reset()` 仍崩 / 去掉全部碰撞球改动仍崩 / **完全不用 IK 求解器、纯用运动规划器仍崩**。

**⚠️ 未根治**：本次判定为 cuRobo 内部行为，未提交上游修复。**建议参考 `ai_knowledge.md` 的 `P31` 详细记录**再决定是否深究。

**💡 方法论**：这 9 次实验之所以有效，是因为**严格一次只改一个变量**。Isaac Sim 每次启动约 3 分钟，多变量同改会让结果完全无法归因（见 `L07`）。

**相关经验**：`P31`、`L07`、`L08`

---

<a id="q32"></a>
### Q32 · 碰撞球配置改完了，但碰撞检测像没生效 / 给手指加球后报不存在的关节名

**Q**：两种表现：① 碰撞球配置写好了、YAML 也解析通过了，但行为完全没变；② 给手指 link 加球后报 `ValueError`，提到一个 URDF 里根本没有的关节名。

**A**：

**① 静默失效** —— **必须在 `collision_link_names` 里列出加了球的 link**。留空会让 `total_spheres=0` 而**不报任何错**，球定义被静默忽略。
- **改完必须跑验证脚本断言 `total_spheres > 0`。"YAML 解析通过 ≠ 球加载了。"**

**② 不存在的关节名** —— **不要给手指 link 加球**。球构建器会从 link 名推断关节名，推出 URDF 里不存在的名字后直接 `ValueError`。只给腕部/掌部 link 加。

**球心与半径怎么定**：**从真实 STL 的顶点范围读 bbox**，沿某轴分段取内切球。
- ❌ 不要用计划里给的未验证占位值 —— **过度膨胀会让规划器认为夹爪离目标太近而无法接近**，产生新的规划失败。

**⚠️ 另一个方向性错误（务必注意）**：`collision_activation_distance` **不要调小**。
- 本地默认是 **0.05**（不是 0.005）。调到 0.02–0.04 是在**减小**安全边际 → **更容易穿模**，方向完全相反。
- **该值越大，规划越保守、离障碍越远。** 正确方向是 **≥0.06**，本次最终取 **0.07**。

**❌ 另一个无效尝试**：改用 pinocchio IK 做直线下降 —— 它是 **stub**（见 [`Q07`](#q07)），任何调用都会 raise。需要 IK 用 cuRobo 的求解器。

**相关经验**：`P32`、`L06`

---

<a id="q33"></a>
### Q33 · 某个技能在 `1 steps` 就退出了

**Q**：某个技能（本次是 grasp）刚开始就报完成，只跑了 1 步，机械臂停在上一个技能的位姿。

**A**：**查是不是复用了同一个技能实例，而它的内部步计数器没被重置。**
1. 检查技能实例是在**循环内**创建还是**循环外**创建一次后复用。本次是后者：hover 与 grasp **共用同一实例**。
2. 检查 `plan()` 是否重置内部步计数器。本次**不重置** —— hover 跑完把计数器推到约 57，grasp 重新规划出 43 个 waypoint 的新轨迹后，第一次 `step()` 就 `57 >= 43 → done=True`，**grasp 轨迹从未执行**。
3. **修复：在复用前显式调 `skill.reset()`。** 验证：本次从 `1 steps` 变成 `44 steps`。

**❌ 无效尝试**：按"某技能有 `reach_threshold` 字段且默认值过大"的假设去改 —— **该字段根本不存在**，技能是按 `step_idx >= len(traj)` 终止的（这是"写修复计划前必须 grep 验证字段存在"的又一次印证，见 `L02`）。

**💡 通用规则**：**复用任何有状态实例前，先 `inspect.getsource()` 看它的 `reset()` / `plan()` 到底重置了什么。** 这种隐式状态耦合从代码表面看不出来（同 [`Q31`](#q31) 的累积器问题，见 `L08`）。

**相关经验**：`P33`、`L02`、`L08`

---

<a id="q34"></a>
### Q34 · 腕部到位了但真实手指差 0.3 m，接触力全程 0 N

**Q**：规划报告末端已到达目标上方，但实测真实手指在目标后方约 0.3 m，接触力全程 0 N，抓取必然落空。

**A**：**根因是规划器的 EE link 与仿真的 TCP link 不是同一个。**
1. 打印**同一关节角下**两个 link 的世界坐标做对比。本次：规划器用的是腕部 link，仿真 TCP 是一个**仅存在于仿真、规划器 URDF 里根本没有**的 link，世界 X 轴相差 **0.30 m**（原计划估的"约 10 cm"—— 方向对但量级错）。
2. 加诊断仪表常态化打印"规划 EE 位置 vs 仿真 TCP 位置 vs 目标位置"三者，避免下次再靠猜。

**⚠️ 未解决 —— 本次判定为工作空间/运动学固有限制，不是可修的 bug。建议参考 `ai_knowledge.md` 的 `P34` 详细记录。**

本次实际落地的只有增量改动：[`Q33`](#q33) 的修复、批量规划容错、把 `rotation_threshold` 从硬编码暴露为配置字段、加上述诊断仪表。

**❌ 无效尝试（5 种修法逐一被阻断）**：

| 尝试 | 结果 |
|---|---|
| 给 grasp 目标补 `-0.30` 偏置 | 触发 [`Q31`](#q31) 的 shape crash，**确定性复现 3/3** |
| 降 seed 数 / 关闭图规划 | 仍崩 |
| 限制规划尝试次数为 1 | 不崩了，但单次尝试太弱、规划失败 |
| 启用旋转约束（`rotation_threshold` 收紧到 0.1 / 0.5） | **全部规划失败** —— 目标在工作空间边缘 |
| 改 URDF 给腕部加固定偏置 | **link 局部坐标系的固定偏置是位姿相关的**，无法在所有位姿正确补偿；且确切变换锁在二进制 USD 里 |

**💡 若要继续 scripted 路线的建议**：**先换一个目标物体不在工作空间边缘的 seed** —— 用可达性门的 IK 残差判断能否以**约束朝向**（而非仅位置）到达目标上方，再谈修偏置。
- ⚠️ 注意：可达性门默认 `rotation_threshold=π` 意味着**完全不检查朝向**，"点可达"不等于"抓得到"。本条 Q34 正是这类假阳性的后果。

**相关经验**：`P34`、`D10`、`D11`、`D14`、`D16`

---

## E. 数据集生成与工程基础设施类

<a id="q35"></a>
### Q35 · ⭐ 数据集生成阶段的五个环环相扣的坑

**Q**：五种表现，实践中会接连撞上：① 改成"一 episode 一进程"后成功率掉到 **0/3**，而同一批 seed 在单进程内顺序跑是 40%；② 一个 `terminated=True` 的**真成功 episode 被判为失败、数据未保存**；③ 进程退出了、数据也存了，但日志**缺尾**（没有完成标记行）；④ `pkill -9 -f "isaacsim"` 返回 exit 1 且杀不掉，还把自己的 shell 杀了；⑤ 数据集导出崩 `KeyError: observations/qpos`。

**A**：五条互不相干，逐条对号入座。

**① 一进程一 episode → 0 成功**
根因：配置开了物体/机器人**重采样**，放置用的是 **env 的 RNG**，而该 RNG 在**进程内跨 episode 累积**。`env.reset(seed=N)` 只设置 reset seed，**不重置放置 RNG 的累积状态** —— 所以新进程里每个 episode 都从同一个"第一次采样"开始。
- 解决：改回 **N 个 episode 在同一进程内顺序跑**，每 episode 只重置策略 + `env.reset(seed=base+i)`，**env 跨 episode 保持存活**。
- **❌ 无效尝试**：以为"固定 seed 就能复现 40%"。**这是误解** —— 在开了重采样的环境里固定 seed = 固定放置 = 要么 0% 要么 100%；那个 40% 来自**基准 seed 加 per-episode 递增**。

**② 真成功 episode 被丢弃**
根因：向量环境包装器在 `terminated` 后会**自动 reset**（gymnasium 标准行为），所以循环外再去查 raw env，读到的是**下一 episode 的初始状态**。
- 解决：**在 `step()` 返回的瞬间捕获 `terminated`**（`task_success = last_terminated`）。事后查询只能用于打印诊断，且必须在日志里标注"该位置是 auto-reset 之后的状态、不是 episode 末态"。
- ⚠️ 与 [`Q29`](#q29) 构成**一对镜像错误**：`Q29` 是把失败当成功，这里是把成功当失败。两者都源于**成功判定没统一到环境信号的正确采样时刻**。

**③ 日志缺尾**
根因：`os._exit(0)` **跳过 stdio flush**。
- 解决：`os._exit(0)` 前**显式 flush stdout/stderr**。

**④ `pkill -f` 杀不掉还自杀**
根因：`pkill -f` 用整条命令行匹配，**匹配到了 pkill 自己那条命令**，于是杀掉父 shell。
- 解决：用**方括号技巧** `pkill -9 -f "[i]saacsim"` 规避自匹配。

**⑤ 导出崩 `KeyError`**
根因：失败的 episode 留下了**空 HDF5** 文件，导出时按 key 取数据直接 KeyError。
- 解决：导出前按 summary 的 `success` 字段**过滤，并清理空文件**。

**相关经验**：`P35`、`L05`、`L08`

---

<a id="q36"></a>
### Q36 · 数据集导出耗时约 40 分钟

**Q**：仿真部分已经跑完，但把 episode 导出成数据集要约 40 分钟，批量产数时不可接受。

**A**：先认清瓶颈在哪 —— **是 PNG 编码，不是仿真、也不是压缩级别**。
1. 算清数据量：本次 10 episode × 约 652 帧 × **3 相机** ≈ **1.8 万张 PNG**，单核约 **2 fps**，40 分钟符合预期，不是哪里卡住了。
2. 因此优化方向只能落在**减少 PNG 张数**（降相机数 / 降帧率 / 降分辨率）或**换编码路径**上 —— 但下面三条常见思路本次都已验证无效。

**❌ 无效尝试（三条，均已核实）**：

| 尝试 | 为什么不行 |
|---|---|
| 换成 video 格式存储 | **不可行** —— 策略训练的 schema 要求图像类型、明确禁用 video（已对照数据集元信息与模型配置核实） |
| 调低 PNG 压缩级别 | 几乎无效（2.2 → 2.3 fps）。**瓶颈在 PNG filter，不在压缩级别** |
| 打开数据集库的并行编码开关 | 该开关**只对 video 生效**，对 PNG 路径无作用 |

**⚠️ 未解决 —— 本次接受该瓶颈并如实记录，未做进一步优化。建议参考 `ai_knowledge.md` 的 `P36` 详细记录**，再结合自己的相机数与帧率预算决定取舍。

**相关经验**：`P36`

---

<a id="q37"></a>
### Q37 · 长跑管线崩溃只有一行错误摘要，看不到调用栈

**Q**：长跑管线崩了，日志里只有一行错误摘要，没有 traceback，无法定位到出错代码。

**A**：**根因几乎总是异常处理只存了 `repr(e)`。**
1. `grep -rn "except Exception" <相关模块>`，找形如 `except Exception as e: err = repr(e)` 的写法 —— 它把栈信息整条丢掉了。
2. 补上 `traceback.print_exc()`（或把 `traceback.format_exc()` 写进错误记录），重跑即可拿到具体行号。本次正是这样定位到根因的。
3. **硬规则：长跑 pipeline 的异常处理必须打完整 traceback。** 一次长跑动辄数十分钟，靠 `repr(e)` 猜根因等于把整次运行作废 —— 本次因此白烧了两次运行。

**❌ 无效尝试**：靠一行 `repr(e)` 判断根因。[`Q31`](#q31) 的 shape mismatch 也是补全 traceback 之后才定位到的。

**相关经验**：`P37`、`L06`

---

<a id="q38"></a>
### Q38 · LLM API 调用在 Isaac Sim 进程内概率性 segfault、无 traceback

**Q**：在 Isaac Sim 进程内调用 LLM API，约 **40% 概率** segfault，日志停在"生成中"就没有下文，**没有任何 traceback**。

**A**：**不要在 Isaac Sim 进程内发起 LLM/网络调用。** 疑为 Isaac Sim 进程内的 **SSL / 网络栈冲突**（本次未进一步定位到具体库）。
1. 本次的实际解法：**给全部 seed 预填任务分解缓存**。该任务分解是**确定性的**，可以直接复用先前已验证过的结果、只改任务名 → **运行期零 API 调用、零崩溃**。
2. 若你的调用结果不是确定性的、无法预填，就把 LLM 调用**放到 Isaac Sim 之外的独立进程**，通过文件交换数据（先生成、再启动仿真消费）。

**❌ 无效尝试**：加重试 —— 这是**进程级 segfault**，进程已经死了，重试逻辑根本不会在同一进程内被执行到。

**💡 通用原则**：Isaac Sim 进程应尽量**只做仿真**。配置/任务分解生成、结果分析等都放到进程外，既避开这类冲突，也让失败可归因。

**相关经验**：`P38`、`D18`

---

## 贡献指南

本文档是**派生层**，不是新事实来源。修改时请遵守以下约定，以保证与其余四层的引用关系不断裂。

### 什么情况下改这里

| 你遇到的情况 | 应该改哪 |
|---|---|
| 踩到一个**全新**的坑 | **先**在 `ai_knowledge.md` §4 追加一条 `Pxx`，**再**在本文档追加对应的 `Qxx` |
| 已有 `Qxx` 的**解决步骤有更新**（找到更好的解法） | 直接改本文档的 `**A**`，并回头同步 `ai_knowledge.md` 对应 `Pxx` 的"解决方案"列 |
| 试了某个方法**没用** | 补进对应 `Qxx` 的 **❌ 无效尝试**（这是本文档最有价值的部分，请不要省略） |
| 某个 `⚠️ 未解决` 项被解决了 | 改 `**A**`、去掉 `⚠️` 标记、更新快速症状索引里的标记 |
| 只是想解释**为什么**会这样 | 改 `ai_knowledge.md`（经验层），本文档只放**可执行步骤** |

### 追加一条 Qxx 的清单

1. **编号只追加，不重排、不复用。** 当前最大编号为 `Q38`，下一条从 `Q39` 起。外部文档依赖此约定做交叉引用。
2. **保持 `Qxx` ↔ `Pxx` 一一对应。** 新增 `Qxx` 必须能指回一条 `Pxx`；不要把两条 `Pxx` 合并成一条 `Qxx`。
3. **归入已有的 A–E 分组**（环境与安装 / 策略推理与评测 / 场景生成与配置 / scripted cuRobo 管线 / 数据集生成与工程基础设施）。确实放不进去再新开分组，并同步在快速症状索引里加一张子表。
4. **同步更新顶部「快速症状索引」**：症状一栏尽量写**逐字的报错原文**（不是抽象归类），这样 `Ctrl-F` / `grep` 能直接命中。
5. **锚点格式固定**为 `<a id="qNN"></a>`，与索引里的 `[QNN](#qnn)` 对应（**锚点全小写**）。
6. **必备四件套**：`**Q**` 现象 / `**A**` 编号步骤 / `❌ 无效尝试`（有就写）/ `**相关经验**：Pxx`（可附 `Lxx`）。

### 内容纪律

- **本文档全篇为 `[实践]` 级**，是本机复现记录，**不是官方结论**。不要在这里写官方 API 语义或设计原理 —— 那属于 `background_knowledge.md`。
- **未解决的条目要如实标 `⚠️ 未解决` / `⚠️ 未根治`**，并写明"建议参考 `ai_knowledge.md` 的 `Pxx` 详细记录"。**不要为了让文档看起来完整而编造解法。**
- **不得出现**账号、密码、密钥、access token。本地绝对路径统一写 `<path>` / `<user_home>` / `<仓库根>`，主机地址写 `<INFER_IP>:<PORT>`。
- 涉及版本相关的结论，**写明当时的版本基线**（见文档头「环境基线」），不要让读者误以为结论跨版本通用。

### 改完之后

1. 检查新增/修改的锚点在索引里都能点到（锚点小写、无重复）。
2. 若新增了 `Qxx`，同步 `knowledge/projects/lw_benchhub/00-index.md` 的行号表与条目数。
3. 若章节位置发生较大移动导致索引行号漂移，用 `grep -n '^#\{2,3\} '` 重新定位并顺手修正索引。
