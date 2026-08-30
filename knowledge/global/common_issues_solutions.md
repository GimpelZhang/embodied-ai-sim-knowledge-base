# 跨项目常见问题分类与解决方案库

> **这是什么**：把本知识库 4 个项目的排障层（**共 145 条 `Qxx`**）按**故障类别**重排的跨项目视图。
> `genie_sim_v3` `Q01`–`Q29` · `lw_benchhub` `Q01`–`Q38` · `genesis_world` `Q01`–`Q37` · `ge_sim_v2` `Q01`–`Q41`
>
> **怎么用**：
> 1. **手上有具体报错** → 先看 §0 的「重复问题榜」，命中就直接照那条办；没命中再按类别（A–M）查。
> 2. **确认类别后** → 去对应项目的 `troubleshooting.md`，用 `grep -n 'Qxx'` 定位原文（含 **❌ 无效尝试**栏，能省掉重走死路的时间）。
> 3. **想知道流程该怎么走**（而不是查某条报错）→ 去 [`common_reproduction_guide.md`](common_reproduction_guide.md)。
>
> **证据等级**：全篇 `[实践]` 级（本机踩坑记录），**不是官方结论**。四个项目的软硬件基线各不相同，套用前先核对版本。
>
> **本库最重要的一句**：**四个项目里代价最大的问题全部不报错。** 所以 §I（配置静默失效）与 §J（正确性假象）虽然排在后面，却是最该先读的两节。

---

## 0. 跨项目重复问题榜 🔁

**在 ≥2 个项目中独立出现过的问题。这些是"下一个项目也几乎必然会遇到"的，优先固化成检查项。**

| # | 问题 | 出现项目 | **最有效的解决方案** |
|---|---|---|---|
| 🔁**1** | **配置/修复改了，但完全没生效，且不报错** | **4 / 4** | 把"**输出是否随输入变化**"当成独立健全性检查；配置键必须 grep 到**读取它的代码**；**一个常量有几个消费者就 grep 出全部消费者**（`ge_sim_v2 Q35`：三方消费漏改一处 → 全 0 %）。见 §I |
| 🔁**2** | **管线自报成功，实际是失败（假阳性）／实际成功却报 0（假阴性）** | **4 / 4** | 成功判定只取**环境返回的信号**；下结论前跑**审计四件套**。见 §J |
| 🔁**3** | **进程无声死亡或永久挂起，没有 traceback** | **4 / 4** | 设**独立于日志的存活判据** + 外部 wall-clock 超时；查 `dmesg`；`python3 -u`。见 §H |
| 🔁**4** | **照文档/模型卡片/计划写的 API 名、字段名、关节名不存在** | **4 / 4** | 落笔前 `grep -rn "<名字>" <上游源码>`，找不到就当它不存在。**源码才是契约**。见 §F |
| 🔁**5** | **`nvcc` 路径查找失败，报错路径带前导冒号** | `lw_benchhub Q01` · `genesis_world Q01` | 根因是 `CUDA_HOME` 为空导致拼出 `:/bin/nvcc`。**两个项目一模一样** → 先 `echo $CUDA_HOME` 再编译 |
| 🔁**6** | **装一个包，把整个环境搞坏（传递依赖冲突）** | `lw_benchhub`(numpy) · `genesis_world Q26`(pyuipc→numpy 2.5.1) · `ge_sim_v2 Q12`(conda 把 CUDA 从 12.1 换成 13.x) | 高风险依赖先 `pip install --dry-run`；**装进独立环境验证**；`--target` 隔离**不够**。见 §A |
| 🔁**7** | **CUDA / 架构 / ABI 版本不匹配，报错指向错误方向** | `genie_sim_v3 Q12`·`Q13` · `lw_benchhub Q10`·`Q11`·`Q13` | **显存数字荒谬 = 架构问题，不是容量问题**；换卡必重编译所有扩展。见 §B |
| 🔁**8** | **LLM / VLM 返回 HTTP 200，但内容为空或用的不是请求的模型** | `lw_benchhub Q27` · `ge_sim_v2 Q18` | **回读响应体的 `model` 字段**并断言非空；不要以状态码为成功。见 §L |
| 🔁**9** | **相机/渲染返回空、全黑或 shape 异常** | `genie_sim_v3 Q10`·`Q22` · `lw_benchhub Q02`·`Q04` · `genesis_world Q18` | 先分清是**渲染库缺失**、**驱动/RTX 能力不足**还是**返回值结构理解错**（`cam.render()` 可能是 4 元组）。见 §C |
| 🔁**10** | **checkpoint / 权重加载 key 不匹配，只打 warning 就静默随机初始化** | `lw_benchhub Q18` · `genesis_world Q20`·`Q22` | 加载后**断言权重非随机**（比对某层 norm）；`load()` 返回值可能是 `None` |
| 🔁**11** | **磁盘写满 / 输出落到错误的盘** | `ge_sim_v2 Q33` · `lw_benchhub D03` | 准备阶段就把 conda `pkgs_dirs`/`envs_dirs` 与输出目录重定向到大盘。输出路径若硬编码在上游，用**逐文件软链**搭影子目录 |
| 🔁**12** | **Python / transformers 等版本窗口互斥** | `genesis_world Q12`·`Q37` · `ge_sim_v2 Q11` · `genie_sim_v3 Q04` | 版本需求**正面冲突时立刻隔离环境**，不要找第三个版本。见 §A |
| 🔁**13** | **`import` 成功，但拿到的是空壳 / 不是你以为的那份代码** | `ge_sim_v2 Q13`·`Q23` · `lw_benchhub`（两份 vendored IsaacLab） | `import` 后**查 `__file__`**；有多份同名依赖时先判定"pip 装的是哪一份" |
| 🔁**14** | **降低目标 / 放宽判定口径来"解决"问题** | `genesis_world D08`(❌) vs `D18`(✅) · `ge_sim_v2 D17`(✅) · `genie_sim_v3 L8`(❌×2) | **先把"当前目标不可达"证明到机制层面，再显式征得决策者同意**。见 §J.4 |

---

## A. 依赖与版本冲突

### 常见表现形式

- 一连串 `ModuleNotFoundError`，装了一个又缺下一个。
- 明明装过的包 `import` 报找不到（装到了另一个 env / 另一个 Python）。
- 装 B 包之后 A 包不能用了；`import` 主库直接崩。
- 版本求解极慢，或解出来的 CUDA / numpy 大版本被悄悄换掉。
- 同一个库的两个消费者要求互斥版本。

### 跨项目实例

| 项目 | 问题摘要 | 条目 |
|---|---|---|
| `lw_benchhub` | **`numpy==1.26.0` 被 Isaac Sim 的 C 扩展硬绑** —— 必须最后装，且**每次 pip 操作后重新锁回**；否则出现随机 `ImportError` 或 Segfault | `Q03` ⭐ `D04` |
| `lw_benchhub` | `warp-lang` 必须精确锁 `==1.8.1`（Isaac Sim 5.1 自带 1.8.2 但 PyPI 无此版本）→ 否则 `AttributeError: module 'warp.types' has no attribute 'array'` | `Q11` ⭐ `D09` |
| `lw_benchhub` | `curobo` 装不上：`setuptools-scm was unable to detect version` | `Q12` |
| `lw_benchhub` | 一连串 `ModuleNotFoundError`；`ImportError: cannot import name 'CONFIGS_PATH'` / `DEVICE_MAP` / `ENDPOINT` | `Q05` `Q06` `Q08` |
| `genesis_world` | **`pip install pyuipc` 拉入 numpy 2.5.1 → `Numba needs NumPy 2.4 or less` → `import genesis` 失败 → 前三个 Stage 成果全部不可运行** | `Q26` ⚠️ `L06` |
| `genesis_world` | 模型要求 `transformers>=4.40,<4.50`，环境是 4.57.6；降级会跨大版本 | `Q12` |
| `genesis_world` | OpenPI 要求 Python 3.11，现有环境是 3.12 | `Q37` |
| `genesis_world` | **PyTorch 不在依赖里**，必须先单独装；Python 窗口 `>=3.10,<3.14`；**6 处依赖带界/排除 pin** 各对应一个已知上游破坏 | `code_knowledge.md §5` |
| `ge_sim_v2` | **openpi 依赖地狱（三个症状连着来）** | `Q11` |
| `ge_sim_v2` | conda 求解极慢，且**装完 CUDA 从 12.1 变成 13.x** | `Q12` |
| `ge_sim_v2` | `from pkg_resources import ...` 导入期直接崩（setuptools 新版移除） | `Q13` ⭐ |
| `ge_sim_v2` | `h5py` / `matplotlib` 明明装过却 `ModuleNotFoundError`（装错 env） | `Q15` |
| `ge_sim_v2` | 依赖**除 `torch>=2.0` 外全无版本约束** —— 不同时间点装出的环境完全不同 | `code_knowledge.md §5.2` |
| `genie_sim_v3` | **`pycolmap` 版本连锁**：`UnicodeDecodeError` → `SceneManager` 不存在 → `OverflowError`（两个工具需求正面互斥） | `Q04` `L5` |

### 通用解决策略 / 检查清单

```
□ 先找出「硬绑版本」的包（通常是被 C 扩展绑定的 numpy / warp / CUDA runtime）
    → 写成锁定清单，规定它「最后装」，并在每次 pip 操作后回读断言版本
□ 装任何新包前评估传递依赖：pip install --dry-run 或 pip download 看解析结果
    → 高风险依赖装进独立环境验证。⚠️ --target 隔离不够，运行时仍会冲突
□ 版本需求正面互斥 → 立刻隔离成两个 env，用文件在磁盘上交接
    → 不要尝试寻找「同时满足两者的第三个版本」，那是版本连锁的入口
□ 装完就断言装上了：import 后查 __file__、关键包回读 __version__
□ torch 依赖型扩展一律加 --no-build-isolation（PEP 517 隔离看不到已装的 torch）
□ 注意 conda activate 不把 env 的 bin 传给子进程 PATH（torch 的 shutil.which 会误报）
□ 多份同名依赖并存时，先判定「pip 实际装的是哪一份」再改代码
```

**详细方案**：[`lw_benchhub/troubleshooting.md`](../projects/lw_benchhub/troubleshooting.md) §A ·
[`genesis_world/troubleshooting.md`](../projects/genesis_world/troubleshooting.md) §A ·
[`ge_sim_v2/troubleshooting.md`](../projects/ge_sim_v2/troubleshooting.md) B 类 ·
[`genie_sim_v3/troubleshooting.md`](../projects/genie_sim_v3/troubleshooting.md) §一

---

## B. 编译错误与 CUDA 工具链

### 常见表现形式

- `nvcc` 找不到，且报错路径开头多一个冒号。
- `Ninja is required`，但 ninja 明明已经装了。
- 扩展编译**通过**，但运行时 kernel crash 或抛晦涩 CUDA 错误。
- **极小张量报 out of memory**，或请求 56 GiB / 130000 GiB 这类荒谬数字。
- 编译期 OOM、`cuda.h not found`、`CXXABI_1.3.15 not found`。
- `import` 某个编译型库直接 segfault。

### 跨项目实例

| 项目 | 问题摘要 | 条目 |
|---|---|---|
| `lw_benchhub` + `genesis_world` | 🔁 **`nvcc` 路径带前导冒号**（`CUDA_HOME` 为空导致拼出 `:/bin/nvcc`）—— **两个项目同一现象** | `lw Q01` · `genesis Q01` |
| `genie_sim_v3` | **同一根因（CUDA 架构不匹配）以三种面貌出现**：运行时 kernel crash / 100 元素张量报 OOM / 请求 56 GiB。浪费数小时，修复只需**重编译 5 分钟** | `Q12` `Q13` `L1` |
| `genie_sim_v3` | `Ninja is required` 但 ninja 已装（`conda activate` 未传 PATH 给子进程） | `Q03` |
| `genie_sim_v3` | `fused-ssim` 等扩展 PyPI 找不到 / PEP 517 构建看不到已装的 torch | `Q14` |
| `lw_benchhub` | `CUDA mismatch 11.8 vs 12.8` / `import curobo` 直接 segfault | `Q10` |
| `lw_benchhub` | cuRobo 编译报 `cuda.h not found` / 编译期 OOM / `CXXABI_1.3.15 not found` | `Q13` |
| `ge_sim_v2` | `spas_sage_attn` **根本不在 PyPI 上**，须源码编译；上游明说没有它也能跑 → 应直接关掉该内核开关 | `Q09` ⭐ `D02` |
| `ge_sim_v2` | 世界模型服务启动即 500：`ImportError: liger-kernel is required` | `Q08` |

### 通用解决策略 / 检查清单

```
□ 第 0 步：nvidia-smi --query-gpu=name,compute_cap
    → 把值显式写进 TORCH_CUDA_ARCH_LIST，不要让构建系统猜
□ 编译前 echo $CUDA_HOME；为空就先设好（🔁5 的根因）
□ 换 GPU 之后必须重编译所有 CUDA 扩展 —— 不要假设 .so 是为当前卡编译的
□ ⭐ 判据：显存请求数字荒谬（极小张量报 OOM / 远超物理显存）= 架构不匹配，不是容量问题
    → 驱动返回 cudaErrorNoBinaryForGpu 后，上层框架回落 CPU dispatcher 并错算内存需求
□ 加速内核类可选依赖（sparse attention、liger kernel 等）：
    上游若声明「没有它也能跑」→ 首次部署一律先关掉，不要为了它去编译
□ torch 扩展加 --no-build-isolation；编译 OOM 就降 MAX_JOBS
```

**详细方案**：[`genie_sim_v3/troubleshooting.md`](../projects/genie_sim_v3/troubleshooting.md) §四 ·
[`lw_benchhub/troubleshooting.md`](../projects/lw_benchhub/troubleshooting.md) `Q01` `Q10` `Q13` ·
[`ge_sim_v2/troubleshooting.md`](../projects/ge_sim_v2/troubleshooting.md) `Q08` `Q09`

---

## C. 驱动、GPU 与渲染硬门槛

### 常见表现形式

- 仿真器拒绝启动：`ERROR_INCOMPATIBLE_DRIVER`。
- Vulkan 初始化失败 / GPU PhysX 或 RTX 渲染器异常。
- 相机返回 `shape=(0,)` 或全黑（mean=0.00），但帧率与分辨率都"正常"。
- 日志出现 `Your GPUs do not support RayTracing`，**之后任务永久挂起**。
- `cudaErrorIllegalAddress`（在分配 USD 纹理时）。

### 跨项目实例

| 项目 | 问题摘要 | 条目 |
|---|---|---|
| `genie_sim_v3` | **V100 缺硬件 RT cores → 一次 1 h 43 min 无声挂死**。光栅化能跑不代表光追能跑；换 A100 才解决 | `Q11` ⚠️ |
| `genie_sim_v3` | Isaac Sim 报 `ERROR_INCOMPATIBLE_DRIVER`；**驱动一律用包管理器升级，禁止 `.run` 手装** | `Q09` `D3` |
| `genie_sim_v3` | 相机返回 `shape=(0,)`（容器内渲染库缺失）；4 路相机 RGB 全黑但帧率正常 | `Q10` `Q22` |
| `genie_sim_v3` | **宿主机重启后之前修好的渲染问题全部复发**（tmpfs 里手工补齐的 GL 库丢失，且重填后还须重建容器） | `Q08` |
| `lw_benchhub` | LFS 资产为空 / headless 渲染起不来 / Isaac Sim 拒绝启动 | `Q02` |
| `lw_benchhub` | Vulkan 失败 / GPU PhysX 或 RTX 渲染器异常 | `Q04` |
| `lw_benchhub` | **Isaac Sim 在相机初始化时直接 segfault、无 traceback** → 运行脚本必须 `set +u` 且 `unset CUDA_VISIBLE_DEVICES` | `Q15` ⭐ |
| `lw_benchhub` | `cudaErrorIllegalAddress`（分配 USD 纹理时）→ **Isaac Sim 必须先启动，再构造 cuRobo IK** | `Q16` |
| `ge_sim_v2` | 显存突然只剩四分之一（其它进程未释放） | `Q16` |

### 通用解决策略 / 检查清单

```
□ 区分三类：驱动版本不合 / 硬件缺能力 / 用户态库缺失 —— 三者报错都可能是「渲染失败」
    · 驱动版本不合 → 包管理器升级，禁止 .run 手装（会造成用户态 GL 与内核模块版本不一致）
    · 硬件缺能力（如无 RT cores）→ 无法绕过，只能换卡或换渲染后端
    · 用户态库缺失 → 补库；注意放在 tmpfs 的补齐文件重启即丢，且重填后须重建容器
□ 渲染健康检查：GPU 利用率仅 1–2 % 且显存占用为 0 → 渲染或初始化已失败（不是在慢慢跑）
□ 相机返回值先打印 shape 与 dtype，再当图像用（可能是 4 元组 rgb/depth/seg/normal）
□ headless 环境：确认 EGL 路径可用；unset CUDA_VISIBLE_DEVICES（否则相机初始化 segfault 无 traceback）
□ 「不支持 RayTracing」这类日志之后如果任务不再推进，视为已死，不要等
```

**详细方案**：[`genie_sim_v3/troubleshooting.md`](../projects/genie_sim_v3/troubleshooting.md) §三 ·
[`lw_benchhub/troubleshooting.md`](../projects/lw_benchhub/troubleshooting.md) `Q02` `Q04` `Q15` `Q16`

---

## D. 容器、权限与文件系统

### 常见表现形式

- 容器启动即退出。
- `PermissionError`（`shutil.copy` 内部 `os.chmod`）/ 宿主侧写文件 `EACCES` / `mv` 被拒。
- 容器内解析不到某个目录（软链接失效）。
- 官方初始化脚本执行后**没有任何输出，永久挂起**。
- 运行脚本立刻 `unbound variable` 中止。

### 跨项目实例

| 项目 | 问题摘要 | 条目 |
|---|---|---|
| `genie_sim_v3` | **容器 UID ≠ 宿主 UID，两侧交替写同一批文件反复 `PermissionError`** —— 同一根因踩了 **3 次**，逐个 `chmod` 治不了新生成的文件 | `Q06` `L4` |
| `genie_sim_v3` | **宿主机创建的软链接存的是宿主机绝对路径，容器内解析不到** | `Q07` |
| `genie_sim_v3` | 容器启动即退出（entrypoint 的 `set -e` + 某步失败） | `Q05` |
| `genie_sim_v3` | **官方初始化脚本含交互式 `read -p`，非交互 shell 直接挂死** | `Q01` |
| `lw_benchhub` | 运行脚本立刻 `unbound variable` 中止 → 必须用 `set +u`（**不是** `set -u`） | `Q14` |
| `ge_sim_v2` | 盘写满 / 输出落在错误的盘（视频输出路径硬编码在上游）→ 用**逐文件**软链搭影子目录（**目录级软链在这里不管用**，上游会往目录里写新文件） | `Q33` `D07` |

### 通用解决策略 / 检查清单

```
□ 决定「宿主预处理 + 容器内运行」时，边界画在目录上，不要画在文件上
    → 要么全程在容器内做，要么全程在宿主机做
□ 开工第一步把共享目录整体 chown 到容器 UID
□ 软链接必须在容器内用容器内路径创建
□ tmpfs 下的手工补齐文件：重启即丢，且重填后须重建容器（旧容器挂的是空目录快照）
□ 上游脚本可能假设「有人坐在终端前」→ 先 grep 有无交互式 read，改手动等价命令
□ 上游脚本的 set -e / set -u 假设可能与你的 wrapper 冲突 → 先确认再套壳
□ 输出路径硬编码在上游且盘不够时，用逐文件软链（不是目录软链）
```

**详细方案**：[`genie_sim_v3/troubleshooting.md`](../projects/genie_sim_v3/troubleshooting.md) §二 ·
[`ge_sim_v2/troubleshooting.md`](../projects/ge_sim_v2/troubleshooting.md) `Q33`

---

## E. 网络、下载与代理

### 常见表现形式

- pip / pytorch.org / HuggingFace 全部阻断或极慢；`GnuTLS recv error (-9)`。
- 权重"下载成功"但文件是**截断损坏**的。
- 杀掉下载进程后仍在下载，且两个下载器互相覆写同一文件。
- 长连接被本地代理挂死，**甚至连 `127.0.0.1` 都返回 503**。
- 上游仓库 403 / 模型已下架 / CDN 国内不可达。

### 跨项目实例

| 项目 | 问题摘要 | 条目 |
|---|---|---|
| `ge_sim_v2` | ⭐ **权重下载"成功"但截断损坏** —— 镜像 302 跳转，CDN 间歇返回 **200 而非 206**，`curl -C -` 的续传语义**静默截断**。对策：自研分块下载器 + 完整性断言（**Stage 1 里回报最高的一次重写**） | `Q02` `D03` |
| `ge_sim_v2` | pip / pytorch.org / HuggingFace 全部阻断或极慢 | `Q01` |
| `ge_sim_v2` | 长连接被本地代理挂死，连 `127.0.0.1` 都返 503；**逐 Stage 代理策略相反**（Stage 1–4 需 `no_proxy=*`，Stage 5 必须走代理） | `Q06` `code_knowledge.md §5.3` |
| `ge_sim_v2` | `hf download` 对某些文件报 `LocalEntryNotFoundError`；ModelScope 下载量远超预期 | `Q04` `Q05` |
| `ge_sim_v2` | GroundingDINO 起不来 / 仓库 403；上游 inpaint 模型**已下架** | `Q14` `D05` |
| `genie_sim_v3` | 拉不到 NGC 镜像 / 装不上系统包 / `uv sync` 报 `GnuTLS recv error (-9)`；**私有 registry 不可达 → 本地构建全部镜像但保留原 tag** | `Q02` `D2` |

### 通用解决策略 / 检查清单

```
□ 大文件下载后校验大小 + 哈希，不以「命令退出码 0」为成功
□ 断点续传要断言 HTTP 206（200 说明服务端没接受 Range，续传会静默截断）
□ 一个文件只允许一个下载器写；杀进程后确认真的停了（可能有子进程）
□ 代理策略按阶段/按域名分别设定，不要全局一套；注意 no_proxy 对 127.0.0.1 的影响
□ 准备阶段就把权重与资产落到本地 —— 上游 registry / 模型仓库随时可能下架或 403
□ 私有 registry 不可达时：本地构建镜像但打成原 tag，避免改 compose 引用
```

**详细方案**：[`ge_sim_v2/troubleshooting.md`](../projects/ge_sim_v2/troubleshooting.md) A 类 ·
[`genie_sim_v3/troubleshooting.md`](../projects/genie_sim_v3/troubleshooting.md) `Q02`

---

## F. API 不兼容与源码契约漂移 🔁4/4

### 常见表现形式

- 按文档 / README / 模型卡片 / 博客写的类名、参数名、字段名、关节名**不存在**。
- `AttributeError` / `TypeError: unexpected keyword argument` / `NameNotFound`。
- 返回值元数不对：解包报错，或拿到的张量维度与预期不符。
- 函数返回的**类型在不同版本间漂移**（tensor ↔ ndarray ↔ dict）。
- 抽象方法未实现：`NotImplementedError`。

### 跨项目实例

| 项目 | 问题摘要 | 条目 |
|---|---|---|
| `genesis_world` | `gs.morphs.Franka` 不存在 / `surface` 参数不接受 / `get_link("hand")` 找不到 —— **照惯例猜名字全错** | `Q02` `Q03` `Q04` |
| `genesis_world` | **IK 返回完整 qpos 而非手臂 7 维**；`cam.render()` 返回 **4 元组** `(rgb, depth, seg, normal)`；`get_contacts()` 属 rigid-rigid 管线，**对 PBD 粒子实体直接抛 `AttributeError`** | `Q05` `Q18` `Q28` |
| `genesis_world` | `IPCCouplerOptions` 字段名不存在（照博客写的） | `Q27` |
| `genesis_world` | **模型卡片给的 API 与实际对不上，且返回类型在版本间漂移** | `Q07` |
| `genesis_world` | 跨项目迁移资产：`g1_29dof.urdf` 里找不到夹爪关节；Isaac Sim 的链接名在 Genesis 里不存在 | `Q35` `Q36` |
| `lw_benchhub` | 按文档写的配置跑不通（文档字段与代码不一致；README 有 **4 处规模数字与代码不符**） | `Q25` `background_knowledge.md §4.2` |
| `lw_benchhub` | `gym.NameNotFound`（任务 ID 拼写/注册路径不对） | `Q23` |
| `lw_benchhub` | `shape mismatch` / 广播成错误维度 | `Q31` |
| `lw_benchhub` | 配置里写的关节名不存在 / 碰撞球配置没生效 | `Q32` |
| `ge_sim_v2` | ⭐ **`env.step()` 返回值解包错、帧形状理解错、取错视角** —— 三个契约误用叠在一条链上 | `Q17` |
| `ge_sim_v2` | `NotImplementedError`（抽象方法未实现）/ `conditioning=action` 仍报缺 `.npy` | `Q19` `Q21` |
| `ge_sim_v2` | **两套 16 维状态布局不同**（世界模型侧 `[L臂,L夹爪,R臂,R夹爪]` vs 策略侧 `[L臂,R臂,L夹爪,R夹爪]`）→ **不报错、只是行为错** | `Q36` ⚠️ |
| `genie_sim_v3` | LLM 生成的 DSL 把**参数顺序调换**，语法合法但语义错 | `Q21` |

### 通用解决策略 / 检查清单

```
□ ⭐ 铁律：任何要写进代码或配置的名字（类名 / 字段 / 关节 / 任务 ID / 配置键），
    落笔前必须 grep 到它的「定义处」或「读取处」。
    → 本库里这类错误在单个项目内复发 ≥5 次，失败形态通常是静默无效
□ 文档 / README / 模型卡片 / 博客都不是契约，源码才是。冲突时以源码为准
□ 每个新 API 第一次调用后：print(type(x)), print(len(x)), print(x.shape)
    → 尤其是 render()、step()、IK 求解器这类多返回值函数
□ 上游函数已提供的转换 / 适配（如状态布局重排）一律直接调用，不要手写副本
    → 手写副本 = 上游改了你不知道，且两份逐行相同的代码必然漂移
□ 跨项目迁移资产时，先 grep URDF/USD 里的实际关节名与链接名，不要沿用旧项目的名字
□ 涉及不同物理表示（rigid / PBD / FEM / SPH）时，确认这个 API 属于哪条管线
```

**详细方案**：[`genesis_world/troubleshooting.md`](../projects/genesis_world/troubleshooting.md) B 类 ·
[`ge_sim_v2/troubleshooting.md`](../projects/ge_sim_v2/troubleshooting.md) C 类 ·
[`lw_benchhub/troubleshooting.md`](../projects/lw_benchhub/troubleshooting.md) `Q25` `Q31` `Q32`

---

## G. 生命周期与调用顺序

### 常见表现形式

- `Scene is already built` / 某个 `add_*` 调用被拒。
- 第二次初始化直接 segfault。
- CUDA 上下文冲突。
- 环境变量在 shell 里 export 了却无效。
- 两个组件的构造顺序颠倒 → 底层内存错误。

### 跨项目实例

| 项目 | 问题摘要 | 条目 |
|---|---|---|
| `genesis_world` | **`scene.build()` 是不可逆分界线** —— `add_entity` / `add_sensor` / `add_camera` 都必须在它之前；之后再加报 `Scene is already built` | `Q17` `code_knowledge.md §3` |
| `genesis_world` | 同进程第二次 `gs.init()` 直接 segfault | `Q15` |
| `genesis_world` | CUDA 上下文冲突（多后端 / 多进程初始化顺序） | `Q06` |
| `genesis_world` | **`HF_HOME` / `TRANSFORMERS_CACHE` 在 `import torch` 之前用 `os.environ[...]` 硬写死** → 在 shell 里 export **无效** | `code_knowledge.md §2.3` `§7.1` |
| `lw_benchhub` | **Isaac Sim 必须先启动，再构造 cuRobo IK**，顺序颠倒会在 USD 纹理分配时 `cudaErrorIllegalAddress` | `Q16` |
| `ge_sim_v2` | `XLA_PYTHON_CLIENT_PREALLOCATE=false` 必须在 `import` **之前**生效 | `code_knowledge.md §5.3` |
| `ge_sim_v2` | 启动编排 hang 满 600 s（依赖服务未就绪就发请求） | `Q29` |

### 通用解决策略 / 检查清单

```
□ 找出该框架的「不可逆分界线」（build / init / launch），把它画在时间线上：
    分界线之前能做什么、之后只能做什么 —— 这是最省时间的一张图
□ 环境变量分三类，处理方式不同：
    · 进程启动前必须设好的（CUDA_VISIBLE_DEVICES、XLA_* 等）→ 在 wrapper 里 export
    · 必须在 import 之前生效的 → 只能写在 Python 文件顶部
    · 已被代码硬写死的 → export 无效，必须改代码
□ n_envs=0 与 n_envs=1 的张量形状可能不同（前者无 batch 维）—— 别混用
□ 一个进程只初始化一次；需要多次就起子进程
□ 服务依赖顺序显式化：先起被依赖方，探活成功后再起调用方，不要靠 sleep
```

**详细方案**：[`genesis_world/troubleshooting.md`](../projects/genesis_world/troubleshooting.md) C 类 ·
[`lw_benchhub/troubleshooting.md`](../projects/lw_benchhub/troubleshooting.md) `Q16`

---

## H. 进程、资源与稳定性 🔁4/4

### 常见表现形式

- **进程消失，没有 Traceback、没有错误日志。**
- 后台任务秒退且无输出；或后台日志长时间为空。
- 永久挂起：日志停在某一行不再前进。
- 显存/内存被杀掉的服务继续占用。
- `pkill` 之后**自己的 shell 也死了**。
- 随机 segfault，位置不固定。

### 跨项目实例

| 项目 | 问题摘要 | 条目 |
|---|---|---|
| `ge_sim_v2` | ⭐ **进程消失、无 Traceback**（被 OOM killer 杀）→ 查 `dmesg` | `Q32` |
| `ge_sim_v2` | ⭐ 服务已杀但**显存仍被占用**；渲染进程被 OOM-kill | `Q28` `Q31` |
| `ge_sim_v2` | `pkill` 之后 shell 自己死掉（`exit 144`，匹配到自身/父进程） | `Q27` |
| `ge_sim_v2` | 后台日志长时间为空（stdout 缓冲）→ `python3 -u` | `Q30` |
| `ge_sim_v2` | 长跑内存增长 —— **进程内 `gc` 已被实测证明无效**，改为**每片段起独立子进程** | `ai_knowledge.md §4` |
| `ge_sim_v2` | 平台进度冻结（下游服务无响应但不报错） | `Q34` |
| `lw_benchhub` | ⭐ **相机初始化 segfault，无 traceback**；`set +u` + `unset CUDA_VISIBLE_DEVICES` 才能过 | `Q15` |
| `lw_benchhub` | ⭐ **随机 `ImportError` / Segfault，位置不固定** → 根因是 numpy 版本被 pip 换掉 | `Q03` |
| `lw_benchhub` | boot 阶段无限挂起 | `Q24` |
| `lw_benchhub` | **在 Isaac Sim 进程内调 LLM 会概率性 segfault** → 改为进程外调用 | `Q38` |
| `genesis_world` | 后台任务秒退且无任何输出 | `Q23` |
| `genesis_world` | resume 训练时 checkpoint 被删（清理逻辑与续训冲突） | `Q22` |
| `genie_sim_v3` | 18 Hz 刷日志但策略服务器收不到请求（服务在跑，链路是断的） | `Q16` |
| `genie_sim_v3` | `docker ps` 显示 Up 但端口不监听；`address already in use` | `Q17` `Q18` |

### 通用解决策略 / 检查清单

**⭐ 无 traceback 的死亡，按这个顺序排查（本库四个项目都用过）：**

```
1. dmesg | tail -50               → 有没有被 OOM killer 杀（最常见）
2. nvidia-smi                      → 显存是否被别的进程占着 / 是否为 0（说明根本没跑起来）
3. 进程还在吗？ps + /proc/<pid>/status
4. 是不是 C 扩展 segfault？→ 试 faulthandler / gdb / 逐步注释定位
5. stdout 是不是被缓冲了？→ python3 -u 重跑
```

**长跑作业的六条硬规则：**

```
□ 一切长跑必须有「独立于日志的存活判据」（见 common_reproduction_guide.md §3.2）
    → 日志在动 ≠ 在干活；GPU 利用率 1–2 % 且显存 0 = 已死
□ 设外部 wall-clock 超时，超时即视为失败并保留现场，不要无限等
□ 后台进程一律 python3 -u，并把 stdout/stderr 都重定向到文件
□ 内存/显存持续增长时：先测「进程内回收是否有效」，无效就改为每单元起子进程
    → 不要在同一个进程里加更多 gc.collect()
□ pkill 用精确模式并排除自身（pgrep -f 先确认命中集合再杀）
□ 服务杀掉后回读 nvidia-smi 确认显存真的释放，再起下一个
```

**详细方案**：[`ge_sim_v2/troubleshooting.md`](../projects/ge_sim_v2/troubleshooting.md) D 类 ·
[`lw_benchhub/troubleshooting.md`](../projects/lw_benchhub/troubleshooting.md) `Q03` `Q15` `Q24` `Q38` ·
[`genie_sim_v3/troubleshooting.md`](../projects/genie_sim_v3/troubleshooting.md) §五

---

## I. 配置静默失效：改了没生效 🔁4/4 ⚠️ 最高价值一节

### 常见表现形式

**这一类的定义特征：不报错、日志照打、退出码 0，行为完全不变。**

- 改了参数，重跑，结果**分毫不变**。
- 脚本日志说"正在调整难度 / 正在使用 X 配置"，但实际没变化。
- 命令行显式传的参数被无声丢弃。
- 只改了一处，另一处仍是旧值 → 两个组件对同一事实的判断不一致。
- 改的是 A 文件，实际运行的是 B 文件的同名副本。

### 跨项目实例

| 项目 | 问题摘要 | 条目 |
|---|---|---|
| `lw_benchhub` | ⭐ **YAML 静默覆盖命令行参数（含 `--device`）** —— 8 个入口脚本都有 `args_cli.__dict__.update(yaml_args.__dict__)`，执行在 `parse_args()` **之后**；`teleop_base.yml` 里是 `device: cpu`，所以 `--device cuda:0` 实际仍跑 CPU（表现为"莫名奇妙地慢"） | `background_knowledge.md §6.1` 推论 4 |
| `lw_benchhub` | ⭐ 脚本日志声称"在调难度"，实际**无任何变化** | `Q26` |
| `lw_benchhub` | **11 条已知静默失效路径** + **79 文件 326 处硬编码主机绝对路径** | `code_knowledge.md §7.1` `§7.2` |
| `lw_benchhub` | **两份 vendored IsaacLab（1362 vs 1857 文件、973 处差异）** —— 改错那份不报错也不生效 | `code_knowledge.md §7.3` |
| `ge_sim_v2` | ⭐ **两套 16 维状态布局不同，用错不报错只是行为错**；本仓库还**绕开上游转换函数手写了两份逐行相同的副本**（反面教材） | `Q36` `code_knowledge.md §7.2 S3` |
| `ge_sim_v2` | **≥5 组「同一常量写两遍」**；**13 条静默失效路径** | `code_knowledge.md §7.2` |
| `ge_sim_v2` | `configs/gesim_v2.yaml` 默认把 4 个加速内核开关**全开**，而这些内核需源码编译 —— 默认值本身是陷阱 | `code_knowledge.md §5.4` |
| `genesis_world` | **`stage3/train_subprocess.py` 自带一份 `get_train_cfg`/`get_cfgs` 副本，不 import `go2_train`** → 改 `go2_train.py` 的超参**完全无效且不报错** | `code_knowledge.md §4.3` |
| `genesis_world` | **判定阈值在 demo 顶部常量与 `verify_stage4.py` 的 `DEMOS` 字典里各写一遍** → 只改一边 → "demo 自认为通过、verify 判 FAIL" | `code_knowledge.md §4.4` |
| `genesis_world` | `HF_HOME` 硬写死在 `import torch` 之前，shell export 无效 | `code_knowledge.md §2.3` |
| `genie_sim_v3` | 录制开关**全部打开**，但没有文件落盘，也没有任何报错 | `Q15` |
| `genie_sim_v3` | LLM 生成的 DSL 参数顺序被调换 —— 语法合法、能跑、语义错 | `Q21` |

### 通用解决策略 / 检查清单

**⭐ 配置陷阱八问（改任何配置前逐条过）：**

```
□ 1. 这个键 grep 得到「读取它的代码」吗？    grep -rn "your_key" <src>
      → 找不到读取处 = 这个键是死的，配置照收、行为不变
□ 2. 这个值有几个读取者？                    有 2+ 个就必须只定义一次
□ 3. 有没有另一份同名配置/同名函数副本？      有副本时先判定「运行时用的是哪一份」
□ 4. 命令行 vs 配置文件，谁最后写入？         grep args_cli.__dict__.update 之类的合并逻辑
      → 若配置文件后写，命令行传值会被无声丢弃 → 要改就改配置文件
□ 5. 默认值本身是不是陷阱？                   默认开启但需要额外编译的开关，属于此类
□ 6. 这个值是不是已被硬写死在代码里？          是 → export / 传参都无效，只能改代码
□ 7. 这个值必须在 import 之前生效吗？          是 → 只能写在文件顶部，不能在 shell 里 export
□ 8. 改完之后，输出真的变了吗？                ⭐ 见下方判据
```

**⭐ 判据（本库最有价值的一条通用纪律）：**

> **如果一次修改改变了变量，而结果分毫不变，说明这个变量没起作用，或者你要修的问题不存在。**
> 此时应该**质疑问题本身**，而不是提出第 N 个假设。
> —— `lw_benchhub · L01`：为一个**根本不存在的现象**修了三轮。

对应的正向做法：**每次配置改动都配一次"反向验证"** —— 故意把参数设成极端值，确认输出确实向极端方向变了，再设回目标值。

**详细方案**：[`lw_benchhub/code_knowledge.md`](../projects/lw_benchhub/code_knowledge.md) §7.2 ·
[`ge_sim_v2/code_knowledge.md`](../projects/ge_sim_v2/code_knowledge.md) §7.2 ·
[`genesis_world/code_knowledge.md`](../projects/genesis_world/code_knowledge.md) §4.3 §4.4

---

## J. 正确性假象：假阳性与假阴性 🔁4/4 ⚠️ 代价最大一节

### 常见表现形式

- 管线报 `success=True`，实际任务没完成。
- 所有验证门 PASS，但产物目录是空的。
- 报 0 % 成功率，实际是**管线故障**而不是模型不行（**假阴性**）。
- 视频只有 2 秒 / 数量不对 / 提前结束，但没有报错。
- 报告小节全空、图像形状为 `[]`，评分照样出。
- 权重加载 key 不匹配，只 warning，之后用随机初始化跑完全程。

### 跨项目实例

| 项目 | 问题摘要 | 条目 |
|---|---|---|
| `lw_benchhub` | ⭐⭐ **`success=True` 但任务其实没完成** —— 8 个 episode 全部失败却全部标成功 | `Q29` `L05` |
| `lw_benchhub` | ⭐⭐⭐ 目标物体被"**推开**"而不是抓起；腕部到位但手指差 0.3 m、**接触力 0 N** | `Q30` `Q34` |
| `lw_benchhub` | ⭐⭐ 机器人抽搐、成功率 0、动作幅度近零 | `Q19` |
| `lw_benchhub` | **checkpoint 几百个 key 不匹配，只打 warning** → 静默随机初始化 | `Q18` |
| `lw_benchhub` | 找不到 `eval_info.json`；**退出码说成功，其实内部已报错** | `Q21` |
| `ge_sim_v2` | ⚠️ **本项目最贵的一次错判：把管道故障读成了模型能力** —— Stage 3 报 0 % 是**假阴性**（兜底路径静默吞掉动作），Stage 5 的 0 才是真实测量 | `ai_knowledge.md §4` `L01` |
| `ge_sim_v2` | ⭐ **批量评测全 0 %，看起来像泛化彻底失败** —— 真因是常量 `SOURCE_TASK_TEXT` 被**三方消费**（策略 prompt / 世界模型 `set_task` / VLM 判分标准），其中一处留着**上一阶段的旧任务文本** → 判分器在按错任务打分。三处改对后 **0 % → 6.5 %**。**本项目最接近"发布错误结论"的一次，靠人工复核拦下** | `Q35` ⚠️ |
| `ge_sim_v2` | ⭐ 机制层：**判分器降级与解析失败都返 `0.0` 且不改 `judge_source`** → 报告里与"真 0 分"不可区分 | `code_knowledge.md §7.2 S1/S2` |
| `ge_sim_v2` | 报告小节全空 / 图像形状 `[]`，但流程照走 | `Q39` |
| `ge_sim_v2` | 排障层 41 条里 **6 条属"不报错的失败"** —— 本范式的典型失败形态是**静默行为错**而非崩溃 | `L05` |
| `genesis_world` | **`SUCCESS` 假阳性**；正常 MP4 被判 FAIL；像素验证误报 | `Q09` `Q24` `Q25` |
| `genesis_world` | 夹爪合上但物体滑出 / 留在原地 / 压穿桌面；FEM 被手指穿过 | `Q08` `Q32` `Q33` |
| `genesis_world` | ⭐ **`learn(50)` 只产出 `model_49.pt`**（rsl-rl checkpoint 是 0-based）→ 等 `model_50.pt` 会永远等不到 | `Q19` |
| `genie_sim_v3` | **G1–G4 全部 PASS，而纹理目录是空的** | `Q26` |
| `genie_sim_v3` | 录制开关全开、无文件落盘、无报错；18 Hz 刷日志但对端收不到请求 | `Q15` `Q16` |

### J.1 ⭐ 审计四件套（下任何"模型不行"的结论前必跑）

来自 `ge_sim_v2 · L01`，是本库最可复用的一段纪律：

```
1. 回退计数        —— 兜底 / except / default 分支的触发次数必须为 0，
                      且一旦触发必须记录（不能静默返回默认值）
2. 动作非退化      —— 检查动作 std、关节位移、夹爪开合是否恒定
                      （恒定 = 模型没在输出，不是模型输出得不好）
3. 帧数对账        —— 落盘帧数 == 元数据行数 == 各日志计数之和
4. 输入侧量纲      —— 观测分位与静息位形是否落在训练分布内
                      （量纲错 → 模型看到的是噪声 → 表现必然像"不会做")
```

### J.2 成功判定的三条纪律

```
□ 成功只取「环境返回的信号」（接触力、物体位姿变化、任务 flag），
    不取「脚本自己算的判断」，也不取「日志里写的 success」
□ 主观标准必须转成机器可判定的量：
    · 视频有效性 → ffprobe 查时长/帧数/分辨率
    · 训练有效性 → reward 曲线 + ep_len 曲线 + checkpoint 存在性
    · 抓取成功   → 接触力 > 阈值 AND 物体高度变化 > 阈值
□ 验证门必须检查「产物真的落盘了」，不只是「命令退出码 0」
    → 至少查：文件存在、大小非零、数量符合预期、内容能被解析
```

### J.3 假阴性同样要防

假阳性让你以为成功了，**假阴性让你放弃一条其实可行的路** —— `ge_sim_v2` 就为此错判了模型能力。

```
□ 报 0 / 报失败时，先问「管线本身通吗」，再问「模型行不行」
□ ⭐ 有判分器（LLM/VLM/脚本）的，第一步把它的原始判词/中间量打出来读一遍
    → ge_sim_v2 Q35 就是这一步露的马脚：判词写着「画面里既没有水壶也没有杯子」，
      而被测任务是 lift_box —— 判分标准根本不对
□ 用 mock / 恒定假动作跑一遍全链路：如果 mock 也报 0，那是管线问题
    → ge_sim_v2 · D20 用这招验证出 8994 帧零协议错误
□ 检查是否有 except 分支把真实动作替换成了默认值
□ 检查判分器/评测器是否会在降级时返回与「真失败」相同的值（0.0 / False）
    → 若会，就必须给它加一个可区分的来源标记，否则报告不可信
```

### J.4 ⭐ 遇到"过不去"时的口径纪律

本库最有对比价值的一组决策：

| 做法 | 案例 | 结果 |
|---|---|---|
| ❌ **放宽判定口径来"通过"** | `genesis_world · D08` | 掩盖了失败，制造出**假阳性** `P09`，后续要花更多时间才发现 |
| ❌ **降低目标当作解决** | `genie_sim_v3 · L8`（复发 2 次） | 交付物看起来完整，实际能力边界未知 |
| ✅ **先证明"当前目标不可达"到机制层面，再显式征得同意后止损** | `genesis_world · D18` | OpenVLA 抓取 0/8，且证明到机制层（末端恒收敛同一点、夹爪输出恒 0.0、换同本体微调模型仍不收敛）—— **本库最值得模仿的一次止损** |
| ✅ **保留原始测量，另建一条自补通路，并声明它不可外推** | `ge_sim_v2 · D17`（RWR + 自补判分器） | 30 % → 80 %，但明确标注"该分数只能内部对比、不可外推" |

**详细方案**：[`lw_benchhub/troubleshooting.md`](../projects/lw_benchhub/troubleshooting.md) D 类 ·
[`ge_sim_v2/troubleshooting.md`](../projects/ge_sim_v2/troubleshooting.md) E 类 ·
[`genesis_world/troubleshooting.md`](../projects/genesis_world/troubleshooting.md) D 类 F 类

---

## K. 性能问题

### 常见表现形式

- 吞吐低到不足以支撑原计划（例如想做在线 RL，实际帧率是实时的百分之几）。
- 某个环节耗时远超预期（数十分钟到数小时），且看不出在做什么。
- 加了某个组件之后整体变慢。
- 长跑内存/显存持续增长。
- "莫名奇妙地慢" —— 实际是在 CPU 上跑。

### 跨项目实例

| 项目 | 问题摘要 | 实测数字 | 条目 |
|---|---|---|---|
| `ge_sim_v2` | **实测吞吐 0.88 帧/s ≈ 0.055× 实时** —— 直接判死"用它做在线 RL 数据引擎"，只适合**离线批量 rollout** | 0.88 帧/s | `ai_knowledge.md §4` |
| `ge_sim_v2` | 4 个加速内核开关默认全开但需源码编译 —— 试图装齐反而卡在编译上 | — | `Q09` `code_knowledge.md §5.4` |
| `ge_sim_v2` | 长跑内存增长；**进程内 `gc` 实测无效**，改为每片段独立子进程 | — | `ai_knowledge.md §4` |
| `genie_sim_v3` | 点云生成 0.25 Hz → **降采样 600 K→100 K 点后约 4 Hz**，平均像素差仅 **1.13** | 0.25 → ~4 Hz | `Q29` |
| `genie_sim_v3` | UV 烘焙跑 1 小时无输出；**五个加速库全部失败**，最后靠**激进网格简化 + 朴素 numpy** 做到 5–20 s | 1 h → 5–20 s | `Q27` |
| `genie_sim_v3` | 接入 ROS 之后整体变慢 | — | `Q28` |
| `lw_benchhub` | **`--device cuda:0` 被 YAML 静默改回 `cpu`** → 表现为"莫名奇妙地慢"（性能问题的根因在 §I） | — | `background_knowledge.md §6.1` |
| `lw_benchhub` | 数据集导出耗时 40 分钟；某些 seed 挂几小时 / `SamplingError` | — | `Q36` `Q28` |
| `genesis_world` | 并行环境规模化收益显著 | 2048 envs：**18,891 → 151,839 steps/s** | `ai_knowledge.md` |
| `genesis_world` | bfloat16 vs fp32 显存：**~14 GB vs ~28 GB** | 2× | `D02` |
| 跨项目 | 服务化调用的网络跳数开销 | WS 跳 **~350 ms** vs 进程内 **~85–100 ms** | — |

### 通用解决策略 / 检查清单

**⭐ 先排除"三类伪装"（它们看起来是性能问题，其实不是）：**

| 表象 | 真实根因 | 判据 |
|---|---|---|
| **OOM / 显存不够** | CUDA 架构不匹配 | 显存请求数字荒谬（极小张量报 OOM）→ 见 §B |
| **慢 / 挂起** | 硬件缺能力（如无 RT cores） | 日志出现能力警告后不再推进 → 见 §C |
| **莫名奇妙地慢** | 实际跑在 CPU 上 | `nvidia-smi` 利用率接近 0 → 见 §I（配置被静默覆盖） |

**优化顺序（本库四个项目一致的经验）：**

```
□ 第 1 步：先量，别猜。分段计时，定位到具体环节，再动手
□ 第 2 步：⭐ 先降数据量，再优化实现
    → genie_sim_v3 的两个案例都是这样解决的：
      点云 600K→100K（像素差 1.13，视觉无损）比换任何加速库都有效
      UV 烘焙先做激进网格简化，朴素 numpy 就够快
    → 五个加速库全部失败，简化数据一次成功
□ 第 3 步：并行度优先于单步优化（并行环境的收益常有一个数量级）
□ 第 4 步：精度换显存（bf16 ≈ fp32 的一半）
□ 第 5 步：减少跨进程/跨网络跳数（服务化的每一跳都是几百毫秒量级）
□ 内存泄漏：先测「进程内回收是否有效」，无效就改成每单元起子进程，
    不要在同一进程里堆 gc.collect()
□ 加速内核 / 可选依赖：上游若说「没有它也能跑」→ 首次部署一律关掉
```

**吞吐先算清再定方案**：`ge_sim_v2` 的 0.88 帧/s 说明——**估算 rollout 预算要按实测数字算，不要按论文宣称的单次耗时算**。

**详细方案**：[`genie_sim_v3/troubleshooting.md`](../projects/genie_sim_v3/troubleshooting.md) §八 ·
[`common_reproduction_guide.md`](common_reproduction_guide.md) §4

---

## L. LLM / VLM 辅助环节

### 常见表现形式

- HTTP **200**，但 `content` 为空。
- HTTP 200，但**用的不是你请求的那个模型**。
- 生成的代码 / DSL 语法合法但语义错（参数顺序被调换）。
- 生成结果首行就 `SyntaxError`（多了 markdown 围栏）。
- 引用了不存在的资产 ID。
- 在仿真器进程内调 LLM → 概率性 segfault。
- 图像编辑类 API socket hang。

### 跨项目实例

| 项目 | 问题摘要 | 条目 |
|---|---|---|
| `lw_benchhub` | 🔁 **LLM 返回 200 但不是请求的模型**（服务端静默降级） | `Q27` |
| `ge_sim_v2` | 🔁 **VLM 返回 200 但 `content` 为空** | `Q18` |
| `ge_sim_v2` | 图像编辑 API socket hang；上游 inpaint 模型已下架 | `Q20` `D05` |
| `lw_benchhub` | **在 Isaac Sim 进程内调 LLM 会概率性 segfault** → 改进程外调用 | `Q38` |
| `genie_sim_v3` | LLM 生成的 DSL 引用不存在的资产（`asset not found` / USD payload 报错） | `Q19` |
| `genie_sim_v3` | 生成结果首行 `SyntaxError`（markdown 围栏没剥） | `Q20` |
| `genie_sim_v3` | ⚠️ **参数顺序被调换 —— 语法合法、能跑、语义错** | `Q21` |

### 通用解决策略 / 检查清单

```
□ 不以 HTTP 状态码为成功判据。每次调用后断言：
    · response["model"] == 你请求的模型名     （防静默降级）
    · content 非空且长度合理                   （防空返回）
□ 生成代码/DSL 必须过三道机器校验，不要目测：
    1. 剥 markdown 围栏 → 2. 语法解析（ast.parse / yaml.safe_load）
    3. ⭐ 语义校验：所有引用的资产 ID、关节名、参数名都要 grep 到定义处
       （参数顺序错、ID 不存在这两类，语法检查抓不到）
□ 生成结果一律先在最小场景里跑一遍，再进主流程
□ 不要在仿真器进程内发起 LLM 调用（信号/线程与 C 扩展冲突）→ 进程外 + 文件交接
□ 外部模型服务随时可能下架 → 关键依赖尽早本地化
```

**详细方案**：[`genie_sim_v3/troubleshooting.md`](../projects/genie_sim_v3/troubleshooting.md) §六 ·
[`lw_benchhub/troubleshooting.md`](../projects/lw_benchhub/troubleshooting.md) `Q27` `Q38` ·
[`ge_sim_v2/troubleshooting.md`](../projects/ge_sim_v2/troubleshooting.md) `Q18` `Q20`

---

## M. 验证、交付与资产

### 常见表现形式

- 正常产物被判 FAIL；异常产物被判 PASS。
- 像素级验证误报。
- 只拿到一行错误摘要，看不到真实堆栈。
- 跨项目迁移资产：模型能载入但关节名/链接名对不上。
- USD / 材质渲染异常：白底、浮尘、灰色金属件、纯色或不显示。

### 跨项目实例

| 项目 | 问题摘要 | 条目 |
|---|---|---|
| `genesis_world` | 正常 MP4 被判 FAIL；像素验证误报 | `Q24` `Q25` |
| `genesis_world` | 跨项目资产迁移：URDF 找不到夹爪关节；Isaac Sim 链接名在 Genesis 不存在 | `Q35` `Q36` |
| `lw_benchhub` | 只有一行错误摘要，真实堆栈被吞 | `Q37` |
| `genie_sim_v3` | **G1–G4 全部 PASS 而纹理目录为空**（验证门没查产物） | `Q26` |
| `genie_sim_v3` | USD 渲染异常四连：4 路全黑 / 白底浮尘 / 灰色金属件（嵌套 rigid body）/ 纯色或不显示 | `Q22`–`Q25` |
| `genie_sim_v3` | ⚠️ 原理层曾建议用 `primvars:displayColor` 补色，**已被实践中的 `D10` 自我否定** | `background_knowledge.md §8.4` |

### 通用解决策略 / 检查清单

```
□ 验证门至少四问：文件存在？大小非零？数量符合？内容可解析？
    → 「命令退出码 0」不是验证
□ 判定阈值只允许定义一次（见 §I）；demo 与 verify 脚本共用同一常量
□ 像素/图像类验证容易两头误报 → 配一次「已知好样本」与「已知坏样本」回归
□ 保留完整原始观测：本库里一次全量落盘（8994 帧）后来服务了两个当时没预料到的用途
□ 跨项目迁移资产：先 grep 目标格式里的真实关节名/链接名，不要沿用源项目的名字
□ 只拿到一行摘要时，先想办法把真实堆栈捞出来（关掉上层的 except 包装 / 提高日志级别）
□ ⚠️ 原理层的修复建议可能已被实践推翻 —— 两层冲突时以经验层的事后结论为准
```

**详细方案**：[`genie_sim_v3/troubleshooting.md`](../projects/genie_sim_v3/troubleshooting.md) §七 ·
[`genesis_world/troubleshooting.md`](../projects/genesis_world/troubleshooting.md) F 类 H 类

---

## N. 一页速查：拿到一个报错，按这个顺序走

```
1. 报错文本里有具体的名字（类名/字段/关节/任务 ID）？
     → §F。先 grep 上游源码确认它是否存在。文档不是契约，源码才是。

2. 是「装/编译」阶段？
     → 缺包、版本冲突     → §A
     → nvcc / CUDA / ABI  → §B（先 echo $CUDA_HOME；显存数字荒谬 = 架构问题）
     → 下载失败或损坏     → §E（断言 HTTP 206 + 大小/哈希）

3. 是「起不来」阶段？
     → 驱动/渲染/相机空   → §C（分清 驱动版本 / 硬件能力 / 用户态库缺失）
     → 权限/路径/容器     → §D
     → 顺序或生命周期     → §G（找出 build/init 这条不可逆分界线）

4. 进程没了 / 挂住了 / 没日志？
     → §H。固定顺序：dmesg → nvidia-smi → ps → C 扩展 segfault → python3 -u

5. ⭐ 能跑，但「改了没生效」？
     → §I。八问过一遍。判据：改了变量而结果分毫不变 ⇒ 变量没起作用，或问题不存在。

6. ⭐⭐ 能跑，结果可疑（成功率异常高或异常低）？
     → §J。先跑审计四件套（回退计数 / 动作非退化 / 帧数对账 / 输入侧量纲）。
       报 0 先怀疑管线（假阴性），报成功先怀疑判据（假阳性）。

7. 慢 / OOM / 吞吐不够？
     → §K。先排除「三类伪装」，再「先降数据量，后优化实现」。

8. 涉及 LLM/VLM 生成？   → §L（不以 200 为成功；语义校验，不只语法）
9. 验证门或产物问题？     → §M（退出码 0 不是验证）

⛔ 任何时候，动手「修复 X」之前先量化「X 是否真的发生」。
   本库为一个根本不存在的现象修了三轮。
```

---

## O. 关联文档

| 文档 | 用途 |
|---|---|
| [`common_reproduction_guide.md`](common_reproduction_guide.md) | **流程视角** —— 从准备到交付该怎么走（本文是"出问题了怎么查"，那篇是"怎么少出问题"） |
| [`best_practices.md`](best_practices.md) | 四个项目 `ai_knowledge.md §6` 的教训汇总（本文的每条检查清单大多能追溯到那里的某条 `Lxx`） |
| [`toolchain_comparison.md`](toolchain_comparison.md) | 选型对照 —— 选错工具链会导致本文一整类问题根本不必发生 |
| [`terminology_mapping.md`](terminology_mapping.md) | 术语差异 —— 有些"报错"其实源于同一个词在两个工具链里含义不同 |
| [`../00-index.md`](../00-index.md) | 知识库总入口 |
| [`../projects/00-index.md`](../projects/00-index.md) | 项目花名册与选型对照表 |

**四个项目的排障层原文（含 ❌ 无效尝试栏，能省掉重走死路的时间）：**

- [`genie_sim_v3/troubleshooting.md`](../projects/genie_sim_v3/troubleshooting.md) — `Q01`–`Q29`，9 个分类
- [`lw_benchhub/troubleshooting.md`](../projects/lw_benchhub/troubleshooting.md) — `Q01`–`Q38`，A–E 类
- [`genesis_world/troubleshooting.md`](../projects/genesis_world/troubleshooting.md) — `Q01`–`Q37`，A–H 类
- [`ge_sim_v2/troubleshooting.md`](../projects/ge_sim_v2/troubleshooting.md) — `Q01`–`Q41`，A–E 类

**四个项目的速查层（动手前先读）：**
[`genie_sim_v3`](../projects/genie_sim_v3/quickstart.md) ·
[`lw_benchhub`](../projects/lw_benchhub/quickstart.md) ·
[`genesis_world`](../projects/genesis_world/quickstart.md) ·
[`ge_sim_v2`](../projects/ge_sim_v2/quickstart.md)
