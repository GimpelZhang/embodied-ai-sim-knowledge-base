# genie_sim_v3 常见问题与解决方案（FAQ / Troubleshooting）

> **文档来源** — 本文由同目录 [`ai_knowledge.md`](ai_knowledge.md) 的「§4 遇到的问题与解决方案」（`P01`–`P18`）改写而成，按**故障类别**重排为 Q&A，供快速检索。原始素材是一次真实复现的本机记录（2026-05/06，Genie Sim 3.0 时期 release）。
>
> **证据等级 `[实践]`** — 全文均为本机踩坑记录，**不是官方结论**。上游已迭代到 v3.2.0（统一 `geniesim` CLI），**部分坑位可能已被官方 `doctor` 子命令覆盖，命令形态也已不同**。动手前请先看 `ai_knowledge.md` §7.1 的版本落差表。
>
> **脱敏** — 不含账号、密码、密钥、token。主机路径写作 `<path>`，用户目录写作 `<user_home>`，主机地址写作 `<INFER_IP>:<PORT>`。
>
> **编号稳定** — 问题编号 `Q01`–`Q29` 为永久编号，后续**只追加、不重排、不复用**（见文末贡献指南）。`P`／`L` 编号对应 `ai_knowledge.md`。
>
> **📌 还没跑起来、不是在排障** — 本文假设你已经装好、正在遇到具体报错。如果你是**第一次上手**（还没装完、想不起命令怎么敲），先走 [`quickstart.md`](quickstart.md) **§1 环境准备** 与 **§2 运行示例**；它的 **§5 一分钟自检清单**按"从便宜到贵"排序，能在进本文之前拦掉大半问题。本文的 `Q01`–`Q29` 中最常撞上的九条，也已在 quickstart **§4 常见代码问题**里给了极简修法（认症状 → 根因 → 一行修法 → 回指本文）。
>
> **📌 想知道某个现象的代码级根因** — 同目录 [`code_knowledge.md`](code_knowledge.md) **§8.3** 列出了本文哪些条目已被升级为 `[CODE]` 级机制解释，其中最有价值的四条：`Q15`（录制无声失败 ← `record_rosbag` 的 `stderr=DEVNULL`）、`Q16`（日志刷屏但无推理 ← `run_on_render_loop` 超时抛异常而渲染循环继续 tick）、`Q17`（容器 `Up` 但端口不监听 ← π0 侧 `compose.yml` 无 `command` 字段）、`Q22`（相机全黑 ← Kit 路径 token → LMDB 锁 → shaderdb → 空 buffer，**v3.2.0 已上游修复**，见该文 §6.4）。

---

## 快速症状索引（按你看到的现象查）

| 你看到的现象 | 去看 |
|---|---|
| 脚本/命令执行后无输出、永久挂起 | [Q01](#q01) |
| 拉不到镜像 / `apt` 装不上 / `GnuTLS recv error (-9)` | [Q02](#q02) |
| `Ninja is required` 但 ninja 已装 | [Q03](#q03) |
| `pycolmap` 报 `SceneManager` 不存在 / `OverflowError` | [Q04](#q04) |
| 容器启动即退出 | [Q05](#q05) |
| `PermissionError` / `EACCES` / `mv` 被拒 | [Q06](#q06) |
| 容器内找不到 assets 目录（软链接失效） | [Q07](#q07) |
| 重启后昨天修好的渲染问题全部复发 | [Q08](#q08) |
| `ERROR_INCOMPATIBLE_DRIVER` | [Q09](#q09) |
| 相机返回 `shape=(0,)` | [Q10](#q10) |
| `Your GPUs do not support RayTracing` / `HydraEngine rtx failed` | [Q11](#q11) |
| 编译通过但运行时 kernel crash / 晦涩 CUDA 错误 | [Q12](#q12) |
| 极小张量报 out of memory / 请求 56 GiB 等荒谬显存 | [Q13](#q13) |
| `fused-ssim` 在 PyPI 找不到 | [Q14](#q14) |
| 录制开关全开却无文件落盘、且无报错 | [Q15](#q15) |
| 日志刷 `[Physics Callback]`、CPU 99%，但策略服务器收不到请求 | [Q16](#q16) |
| `docker ps` 显示 `Up` 但端口不监听 | [Q17](#q17) |
| 重启服务报 `address already in use` | [Q18](#q18) |
| `asset not found in library` / `Failed to load USD payload` | [Q19](#q19) |
| LLM 生成代码首行 `SyntaxError` | [Q20](#q20) |
| `usd() got an unexpected keyword argument 'shape'` / 参数顺序错 | [Q21](#q21) |
| 4 路相机 RGB 全黑（mean=0.00）但帧率正常 | [Q22](#q22) |
| 背景渲染成稀疏"浮尘" | [Q23](#q23) |
| 前景物体变成灰色金属件 | [Q24](#q24) |
| 物体只有纯色 / 完全不出现 | [Q25](#q25) |
| 验证全 PASS 但 `textures/` 是空的 | [Q26](#q26) |
| UV 烘焙脚本跑 1 小时无输出 | [Q27](#q27) |
| 开 ROS 后仿真变慢、初始化超时 | [Q28](#q28) |
| 点云渲染帧率极低（0.25 Hz） | [Q29](#q29) |

**跨类通用判据**（三条最省时间的）：

1. 装任何需现场编译的 CUDA 扩展前，先跑 `nvidia-smi --query-gpu=name,compute_cap`。**换 GPU 后必须重编译所有扩展。**
2. **日志在刷 ≠ 任务在跑。** GPU 利用率 1–2% 且显存占用 0 → 渲染/初始化早已失败。
3. 报错数字荒谬（极小张量 OOM、请求超物理显存）→ 怀疑**架构不匹配**，不要怀疑显存容量。

---

## 一、安装与依赖

<a id="q01"></a>
### Q01 · 执行官方初始化脚本后没有任何输出，永久挂起

**A**：上游脚本内含交互式 `read -p`，在非交互 shell（CI、`nohup`、后台执行）下既无回显也不会推进。

1. 先 `grep -n 'read ' <脚本>` 确认是否有交互式等待。
2. 放弃脚本，手动执行其等价操作，例如 `git clone -b <branch> <repo_url>`。
3. 大仓库容易传输中断，加缓冲区参数：

```bash
git clone -c http.postBuffer=524288000 -b <branch> <repo_url> <path>
```

**相关经验**：`ai_knowledge.md` §4.1 · **P01**（L154）；通用教训 **L3**「开工第一步是读源码核对计划」（L247）—— 上游脚本常假设有人坐在终端前。

<a id="q02"></a>
### Q02 · 拉不到 NGC 镜像 / 装不上 `ros-jazzy-desktop` / `uv sync` 报 `GnuTLS recv error (-9)`

**A**：这三个症状**看似无关，实为同一根因**：代理在不同层缺失。只配一层只能修好其中一个。**代理必须在三层各配一次**：

1. **systemd drop-in** —— 给 Docker daemon 用（拉镜像走的是 daemon，不读用户 shell 的环境变量）：

```bash
sudo mkdir -p /etc/systemd/system/docker.service.d
# 写入 http-proxy.conf，内含 Environment="HTTP_PROXY=http://<INFER_IP>:<PORT>"
sudo systemctl daemon-reload && sudo systemctl restart docker
```

2. **`~/.docker/config.json`** —— 客户端把代理注入容器运行时环境。
3. **构建期显式环境变量** —— 构建子进程不继承上述两者：

```bash
http_proxy=http://<INFER_IP>:<PORT> https_proxy=http://<INFER_IP>:<PORT> \
  docker build --network=host \
  --build-arg http_proxy=http://<INFER_IP>:<PORT> \
  --build-arg https_proxy=http://<INFER_IP>:<PORT> .
```

补充三点，缺一仍会失败：
- `--network=host` 与 `--build-arg` 代理**要同时给**。
- Dockerfile 里的代理变量须从 `ARG` **提为 `ENV`**，否则 `RUN` 层内的子进程看不到。
- `uv` 拉 git 依赖易超时，`UV_HTTP_TIMEOUT` 由 600 调到 **1800**。

**相关经验**：`ai_knowledge.md` §4.1 · **P02** ★（L155）。

<a id="q03"></a>
### Q03 · 报 `Ninja is required`，但 ninja 明明已经装了

**A**：torch 的 ninja 检查走 `shutil.which`，而 `conda activate` **不把 env 的 bin 目录传给子进程 PATH**。显式前置即可：

```bash
export PATH="$CONDA_PREFIX/bin:$CUDA_HOME/bin:$PATH"
```

同批出现的还有 `CUDA_HOME` 未设导致拼出畸形 nvcc 路径 —— 一并显式导出。

**相关经验**：`ai_knowledge.md` §4.2 · **P10**（L168）；教训 **L5**（L259）。

<a id="q04"></a>
### Q04 · pycolmap 版本连锁：`UnicodeDecodeError` → `SceneManager` 不存在 → `OverflowError`

**A**：这是**依赖需求正面互斥**，不要试图在同一 env 里调和（两个重建工具分别要 legacy 版与官方 `3.11.1`，并连带牵动 numpy 主版本）。

1. 不要自写 COLMAP `images.bin` 二进制解析器（易 `UnicodeDecodeError`），改用 pycolmap 官方 API。
2. `SceneManager` 在 pycolmap 4.x 已移除 —— 需要它就只能装 legacy 版。
3. legacy 版与 numpy 2.x 冲突（`np.uint64(-1)` 触发 `OverflowError`），须锁版本：

```
numpy<2
plyfile<1.1
opencv-python-headless<4.10
```

4. **彻底隔离成两个 conda env**，用磁盘文件交接而非同进程交接。本次为 `scene_recon`(Py3.10/torch2.7.1) 与 `pgsr`(Py3.8/torch2.4.1)。

**相关经验**：`ai_knowledge.md` §4.2 · **P09** ★（L167）；教训 **L5**「依赖互斥直接隔离环境」（L259）。

---

## 二、容器、权限与文件

> 本类问题的总根源：**容器以 UID `1234` 运行，与宿主用户 UID 不同。**

<a id="q05"></a>
### Q05 · 容器启动即退出

**A**：`entrypoint.sh` 开头有 `set -e`，其中的 `setfacl` 若目标目录不存在就返回非零 → 整个容器挂掉。

1. `docker logs <container>` 定位最后一条命令。
2. 读 `entrypoint.sh`，找出 `setfacl` / `chown` 等操作的目标路径。
3. **启动前预创建这些目录**，再重新 `up`。

**相关经验**：`ai_knowledge.md` §4.1 · **P04**（L157）。

<a id="q06"></a>
### Q06 · `PermissionError`（`shutil.copy` 内部 `os.chmod`）／宿主侧写文件 `EACCES`／`mv` 隐藏旧场景被拒

**A**：**同一根因在本次复现踩了 3 次。** 容器 UID 1234 与宿主用户 UID 不同，两侧交替写同一批文件必然冲突。

- ❌ **无效做法**：逐个文件 `chmod` —— 治不了后续**新生成**的文件。
- ✅ 开工第一步就把共享目录**整体** chown 到容器 UID：

```bash
sudo chown -R 1234:1234 <path>/to/shared_dir
```

**原则**：跨容器边界的文件操作，**要么全程在容器内做，要么全程在宿主机做，不要交替**。

**相关经验**：`ai_knowledge.md` §4.1 · **P05** ★（L158）；教训 **L4**（L253）。

<a id="q07"></a>
### Q07 · 容器内解析不到 assets 目录（软链接失效）

**A**：软链接存的是**创建时所在文件系统的绝对路径**。在宿主机建的链接指向宿主机路径，容器内命名空间里不存在。

- ❌ 在宿主机重建软链接 —— 方向错，仍然无效。
- ✅ **进容器内、用容器内路径创建**：

```bash
docker exec -it <container> bash
ln -s /container/side/assets/path /container/side/expected/path
```

**相关经验**：`ai_knowledge.md` §4.1 · **P04**（L157）；教训 **L4**（L253）。

<a id="q08"></a>
### Q08 · 宿主机重启后，之前修好的渲染问题全部复发

**A**：手工补齐的 GL/Vulkan 库被放在 `/tmp` 等 **tmpfs** 目录下，重启即丢。

- ❌ 只重新 cp 库文件 —— **仍然失败**。
- ✅ 重填库文件后**必须重建容器**（旧容器挂载的是那个目录的空快照）：

```bash
docker compose down && docker compose up -d
```

- 长期解法：把库永久迁出 tmpfs，放到持久化目录再挂载。

**相关经验**：`ai_knowledge.md` §4.1 · **P06**（L159）；教训 **L4** 末段（L253）。

---

## 三、GPU、驱动与渲染硬门槛

<a id="q09"></a>
### Q09 · Isaac Sim 报 `ERROR_INCOMPATIBLE_DRIVER`

**A**：本次是**误判**——驱动 `535.288.01` 经 Vulkan 编码后被读成 `535.32`，于是 `>=535.129` 的检查认为它过旧。

- ❌ 用 `.run` 包手装驱动 —— 会导致用户态 GL 库与内核模块版本不一致，引入新问题。
- ✅ 走发行版包管理器升级到高版本（本次升到 `580.126.09`）：

```bash
sudo apt install nvidia-driver-580
```

**相关经验**：`ai_knowledge.md` §4.1 · **P03** ★（L156）。

<a id="q10"></a>
### Q10 · 相机返回 `shape=(0,)`（容器内渲染库缺失）

**A**：NVIDIA container runtime **只注入计算库（CUDA），不注入 GL/Vulkan 渲染库**。headless 容器里跑 RTX 渲染必须手工补齐。

1. 从宿主机复制以下库及 ICD 配置进容器（或以挂载方式提供）：
   - `libGLX_nvidia.so.*`
   - `libEGL_nvidia.so.*`
   - `libnvidia-glcore.so.*`
   - `nvidia_icd.json`
2. 用 `vulkaninfo` 确认容器内能枚举到 NVIDIA 设备。
3. 注意：**放在 tmpfs 下重启会丢，且重填后须重建容器**（见 [Q08](#q08)）。

**相关经验**：`ai_knowledge.md` §4.1 · **P03** ★（L156）。

<a id="q11"></a>
### Q11 · 日志出现 `Your GPUs do not support RayTracing` / `HydraEngine rtx failed creating scene renderer`，之后任务永久挂起

**A**：**这是硬件门槛，软件层无解。耗时最长的一个坑（1h43min）。**

失效表现极具误导性：进程持续运行但毫无进度，评分 JSON 永不出现，`:9001` 只有 LISTEN 没有 ESTABLISHED，同时还在写几 GB 的垃圾 ROS bag，表面像"卡在物理仿真 17 Hz"。完整因果链：

```
HydraEngine 初始化失败
  → 相机 annotator 的 overscan 参数恒为 None
  → 每帧抛 TypeError: unsupported operand type(s) for -: 'NoneType' and 'NoneType'
  → 无 RGB 输出
  → 永不调用策略服务器
  → 永久挂起
```

- ❌ **三条全部无效**：强制 software fallback；切换 renderer；加 Vulkan 软件光追扩展。`vulkaninfo` 虽能看到 ray tracing 扩展（软件实现），但 Isaac Sim 5.1 **显式检查硬件 RT cores，一概拒绝软件实现**。
- ✅ **换硬件**。硬门槛：Turing 及以上，Compute Capability **≥ 7.5**。

```bash
nvidia-smi --query-gpu=name,compute_cap --format=csv
```

| 卡 | 架构 / CC | 能否跑 Isaac Sim 5.1 |
|---|---|---|
| Tesla V100 | Volta 7.0 | ⛔ 不行（无 RT cores） |
| Tesla T4 | Turing 7.5 | ✅ 最低可用 |
| A100 / A800 | Ampere 8.0 | ✅ |

**排查建议**：这类问题的证据全在**启动日志前 30 行**，不在挂起时刻的日志里。挂起后回头翻开头，比盯着当前输出有效得多。

**相关经验**：`ai_knowledge.md` §4.2 · **P07** ★★（L165）；教训 **L2**（L241）。

---

## 四、编译错误（CUDA 扩展）

> 本类的核心结论：**CUDA 架构不匹配的报错几乎从不指向真因。** 同一根因在本次复现里以**三种完全不同的面貌**出现，共浪费数小时，而修复只需重编译 5 分钟。

<a id="q12"></a>
### Q12 · 扩展编译通过，但运行时 kernel crash 或抛晦涩 CUDA 错误

**A**：`.so` 是按错误的 SM 架构编译的。本次 `TORCH_CUDA_ARCH_LIST` 连错两次 —— Dockerfile 原写 `8.9`（RTX 4090），计划阶段误判为 A100 改成 `8.0`，而实测 GPU 实为 V100 SM 7.0。

```bash
# 第 0 步，永远先做这个
nvidia-smi --query-gpu=name,compute_cap --format=csv
# 把实测值显式写进环境变量再编译
export TORCH_CUDA_ARCH_LIST="8.0"
pip install --no-build-isolation -e .
```

**铁律**：**换 GPU 后必须重编译所有 CUDA 扩展**，不要假设已有 `.so` 是为当前卡编译的。

**相关经验**：`ai_knowledge.md` §4.2 · **P08** ★★（L166）；教训 **L1**（L235）。

<a id="q13"></a>
### Q13 · 极小张量报 out of memory，或前向传播请求 56 GiB（甚至约 130000 GiB）这类荒谬数字

**A**：**这不是显存问题，是同一个架构不匹配问题的伪装。** 机理：驱动对错架构的 `.so` 返回 `cudaErrorNoBinaryForGpu`，torch 回落到 CPU dispatcher 后错算内存需求，于是伪装成 OOM。

- ❌ **本次的错误归因**：把它当成"坐标尺度问题"，据此去改 COLMAP normalization **并重新训练，白费约 2 小时**。
- ✅ 按实际 SM 重编译扩展（约 5 分钟），规范流程立刻跑通。

**判据**：显存请求数字不合理时（远超物理显存，或 N=100 的张量报 OOM）= **架构问题**，不是容量问题。

**相关经验**：`ai_knowledge.md` §4.2 · **P08** ★★（L166）；教训 **L1**（L235）。

<a id="q14"></a>
### Q14 · `fused-ssim` 等扩展在 PyPI 找不到 / PEP 517 构建看不到已装的 torch

**A**：从 git 指定 commit 安装，并**必须**加 `--no-build-isolation`（PEP 517 的构建隔离环境里没有 torch）：

```bash
pip install --no-build-isolation "git+<repo_url>@<commit_sha>"
```

此后 **`--no-build-isolation` 成为所有 torch 依赖型 CUDA 扩展的标配**。若同时报缺 ninja，见 [Q03](#q03)。

**相关经验**：`ai_knowledge.md` §4.2 · **P10**（L168）；教训 **L5**（L259）。

---

## 五、运行时"看起来在跑"类假象

> **最贵的一类问题。** 共同特征：进程活着、日志在刷、CPU 占满，但实际产出为零。**日志有输出 ≠ 任务在推进。**

<a id="q15"></a>
### Q15 · 录制开关全开却无任何文件落盘，而且没有报错

**A**：两步确认：

1. 先确认录制走的是 **ROS2 bag（`.mcap`）而非 `.mp4`** —— 需要 `app.enable_ros: true`。
2. 两个开关都开仍无输出，则读上游源码 —— 本次发现 `api_core.py`（约 L1315）中 `self.record_rosbag()` **默认被注释掉了**。打补丁取消该行注释即可。

- ❌ 反复检查配置项拼写与开关组合 —— 配置侧本来就是对的。

**教训**：**配置项齐全但功能静默失效时，去读源码确认调用点是否真的被执行**，而不是继续排列组合配置。

**相关经验**：`ai_knowledge.md` §4.3 · **P11** ★（L174）。

<a id="q16"></a>
### Q16 · 日志以 ~18 Hz 持续刷 `[Physics Callback]`、进程 99% CPU，看起来完全正常，但策略服务器永远收不到第一次推理请求

**A**：**主线程活着，干活的 worker 线程已被静默杀死。** 开 ROS 后渲染循环多担 20–25% 负载，导致初始化物理的调用在默认 **120 s** 超时内跑不完，worker 被 `TimeoutError` 打死，而主线程继续打印回调日志。

✅ 把该调用点的超时显式提高（本次 `api_core.py` 约 L429，`_collect_init_physics` 由 120 s → **600 s**）。

- ❌ 检查 ROS 配置、检查策略服务器连通性 —— 都正常，纯浪费时间。

**诊断判据（本条最有价值的部分）**：

```bash
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv -l 5
```

**GPU 利用率仅 1–2% 且显存占用为 0 时，立刻怀疑渲染/初始化早已失败**，不要相信 CPU 占用率。

**相关经验**：`ai_knowledge.md` §4.3 · **P12** ★★（L175）；教训 **L2**（L241）。
**代码物证** `[CODE]`：`code_knowledge.md` **§6.2(b)** —— 精确到 `api_core.py:428–429`，并已与上游 v3.2.0 对照确认：**上游至今仍不传 `timeout`（默认 120 s），所以升级到 v3.2.0 后这一改动依然要自己做**。这是唯一一条需要带到新版本的代码修改。

<a id="q17"></a>
### Q17 · `docker ps` 显示容器 `Up`，但端口不监听

**A**：openpi 的 `compose.yml` **没有定义 `command`**，`up -d` 只是把容器停在一个空闲 shell 里 —— 服务根本没起。

```bash
# 手动起 server，注意 --env 的变量名必须全大写
docker exec -d <container> bash -lc '<server_start_cmd>'
# 唯一可靠的就绪判据：tail 日志看到明确标记
docker logs -f <container> 2>&1 | grep -m1 'server listening on 0.0.0.0:9001'
```

- ❌ 只看 `docker ps` 状态为 `Up` 就认为服务就绪。
- ❌ 用 `ss` / `nc` 探测端口 —— **最小镜像里两者都不可用**。

**相关经验**：`ai_knowledge.md` §4.3 · **P13** ★（L176）；教训 **L2** 判据③（L241）。

<a id="q18"></a>
### Q18 · 重启服务报 `address already in use`

**A**：上次会话的残留进程还 hold 着端口。起服务前无脑清理一遍：

```bash
docker exec <container> pkill -f '<server_process_pattern>' || true
```

**相关经验**：`ai_knowledge.md` §4.3 · **P13** ★（L176）。

---

## 六、LLM 驱动场景生成（DSL 生成类）

<a id="q19"></a>
### Q19 · `asset not found in library` / `Failed to load USD payload` / 调用报 `NotFoundError`

**A**：三个独立的 LLM 侧故障，分别处理：

1. **模型凭空编造不存在的物体 id**（本项目物体 id 是随机 hash，如 `benchmark_apple_88fa166f`，模型不可能猜对）：
   - 先 `ls` 真实资产目录拿到**白名单注入 prompt**；
   - 在每个场景 spec 里**显式钉死** target / distractor 的 id，不让模型自选；
   - 失败时把上一次的报错反馈回去重试。
2. **计划文档给的模型 id 根本不存在** → 换成该服务商的通用 chat 模型 id。
3. USD payload 加载失败见 [Q25](#q25)。

**相关经验**：`ai_knowledge.md` §4.4 · **P14**（L182）；教训 **L6**（L265）。

<a id="q20"></a>
### Q20 · LLM 生成的代码首行就 `SyntaxError`

**A**：模型习惯用 markdown code fence（```python）包裹代码。**防御必须冗余，两者都做**：

1. system prompt 里显式声明禁用 markdown 围栏；
2. **代码侧仍要用正则强 strip** —— 只靠 prompt，模型仍会偶发违规。

**相关经验**：`ai_knowledge.md` §4.4 · **P14**（L182）；教训 **L6** 动作③（L265）。

<a id="q21"></a>
### Q21 · `TypeError: usd() got an unexpected keyword argument 'shape'` / `AttributeError: 'numpy.ndarray' object has no attribute 'items'`（参数顺序被调换）

**A**：模型对函数签名的"记忆"在复杂度上升后全面失准 —— 本次 Round 2 的 **3 个场景全部因此失败**。两步缺一不可：

1. system prompt 增设 **CRITICAL API RULES** 段，**逐条列出合法签名**（含"shape 在前、matrix 在后"、必须 `@register()` 等硬性约束）；
2. 贴一份**已成功物化场景的完整代码作为 EXEMPLAR**，让模型模仿而非凭记忆写。

加固后一次通过。

- ❌ 在 prompt 里用自然语言描述 API 约束 —— 不足以纠正参数顺序这类细节。

**结论**：**让 LLM 生成 DSL，示例的价值远高于描述。**

**相关经验**：`ai_knowledge.md` §4.4 · **P15** ★★（L183）；教训 **L6**（L265）。

---

## 七、USD 资产与渲染

> 本类是本次复现里迭代轮次最多的一块（六轮返工）。核心架构结论：**3DGS 作视觉层 + 隐形碰撞代理（`purpose="guide"`）作物理层 + 任务物体作叠加层**。

<a id="q22"></a>
### Q22 · 4 路相机 RGB 全黑（mean=0.00），但帧率与分辨率都正常

**A**：**场景文件里没有灯光**，RTX/Hydra 没有可照明对象。任务目录下的 USD **不自带灯光** —— 脚手架容易让人误以为"什么都能塞进场景文件"。

组合规则：`scene_usd` 被载为 `/World`，任务层叠加为 `/Workspace`。解法是新建专用背景层：

- `DomeLight`（本次 `intensity=1500`）
- 点云 / 背景几何
- **X 轴 +90° 旋转**（COLMAP Y-up → Isaac Z-up）
- 不可见地面碰撞代理

- ❌ 调相机参数、曝光、渲染模式 —— 全部无关。

**相关经验**：`ai_knowledge.md` §4.5 · **P16** ★（L189）。

<a id="q23"></a>
### Q23 · 背景渲染成大片白底，或渲染成稀疏的"浮尘"

**A**：按顺序查四项：

1. **DomeLight 没有 HDR 贴图** → 大片近白像素（本次高达 ~89%）。
2. **被引用 USD 无 `defaultPrim`，且 `prepend payload` 缺显式 prim 路径** → 容器 prim 存在但子节点**根本没加载**。
3. **文件实际是二进制 crate 却用了 `.usda` 后缀** → 解析异常。
4. **点宽在缩放后过细** → 稀疏浮尘。原始 bbox 达 36×25×38 时需 `scale≈0.103` 补偿，点宽须跟着反算（见 [Q25](#q25) 第 3 条）。

**相关经验**：`ai_knowledge.md` §4.5 · **P17** ★★（L190）。

<a id="q24"></a>
### Q24 · 前景物体渲染成灰色金属件，并伴随嵌套 rigid body 报错

**A**：可视 mesh 上仍挂着 physics schema，造成嵌套刚体。**重构为三层结构**：

```
<Root>                     ← PhysicsRigidBodyAPI / PhysicsMassAPI
├── Visuals                ← 纯渲染几何（不带任何 physics schema）
└── CollisionProxy         ← 碰撞体，purpose="guide"（渲染时不可见）
```

**相关经验**：`ai_knowledge.md` §4.5 · **P17** ★★（L190）；架构决策见 `ai_knowledge.md` §3 · **D6**。

<a id="q25"></a>
### Q25 · 物体只渲染出纯色，或者完全不出现

**A**：三个独立根因，按可能性排查：

1. **真正的 3DGS 数据（每个 250–300 MB 的 PLY）一直存在，却从未转成 USD。** 转换要点：numpy 直读二进制 PLY → 按 SH 0 阶还原颜色 → 按 opacity 过滤 → 降采样 → 输出带顶点色的 `UsdGeom.Points`。

```python
color = np.clip(0.5 + 0.28209479 * f_dc, 0, 1)   # SH order-0 decode
```

2. **亚像素剔除**：局部点宽 `0.01` 叠加 `scale≈0.001` 后，世界点宽仅 **0.01 mm**，被渲染器直接剔除。反算局部宽度：

```python
local_width = target_world_width / scale_factor
```

3. **嵌套 payload 静默组合失败** —— 当"被引用层的 `defaultPrim` 类型 ≠ 宿主 prim 类型"时，组合会**无声失败**。
   - 诊断：`stage.Traverse()` 遍历，看子节点是否真的存在。
   - ❌ 改用 `references` 替代 `payload` —— **对嵌套组合失败同样无效**。
   - ✅ 把几何**直接 inline** 进宿主层。（旁证：房间点云一直正常，正因为它本来就是 inline 的。）

**相关经验**：`ai_knowledge.md` §4.5 · **P17** ★★（L190）。

<a id="q26"></a>
### Q26 · 验证门全部 PASS，但 `textures/` 目录是空的 / 表面"有 Material"却仍渲染成纯色

**A**：两个问题，第一个是**验证设计的漏洞**：

1. USD 写进了容器中转目录，却忘了 copy 到最终位置 —— 而**验证门只检查 USD 结构，没检查被引用的文件是否真实存在**。
   - ✅ 验证门改为**从 USD 出发解析相对路径，确认文件真实存在且 size > 100 KB**。
2. 材质图连线写反或漏接。完整链路必须齐全：

```
UsdPreviewSurface.diffuseColor  ←  UsdUVTexture.rgb
UsdUVTexture.st                 ←  UsdPrimvarReader_float2.result
mesh 侧还必须存在 st primvar
```

**教训**：**只检查结构不检查产物落地的验证门会放过假绿灯。**

**相关经验**：`ai_knowledge.md` §4.5 · **P18**（L191）；教训 **L7**（L271）。

---

## 八、性能问题

<a id="q27"></a>
### Q27 · UV 烘焙 / 逐三角光栅化脚本跑 1 小时无输出

**A**：本条是**「先降数据量，再优化实现」的教科书案例。** 症状源于在 4K 分辨率 × 165K 面上用 `for tri in faces` 纯 Python 循环做光栅化。

- ❌ **五种加速方案全部失败**：numba、`scipy.griddata`、skimage、逐三角 GPU 调用、nvdiffrast。
- ❌ `xatlas.parametrize` 在 10 万面以上 chart packing 不收敛，CPU 100% 无输出。
- ✅ **正解是先激进抽面把面数降两个量级**，之后连纯 numpy 都够快 —— **5–20 秒完成**（对比：卡了 3 小时）：

```python
import fast_simplification
from scipy.spatial import cKDTree
# 1) 激进抽面（Open3D 抽到 165K 已是其极限，换 fast_simplification）
verts, faces = fast_simplification.simplify(verts, faces, target_reduction=0.95)
# 2) 用 KD-tree 从原始顶点传色
color = orig_colors[cKDTree(orig_verts).query(verts)[1]]
# 3) 纯 numpy 逐三角 bbox 向量化填充，不写 Python 循环
```

**教训**：卡在性能上时，**先问"能不能少算两个量级"，再问"能不能算得更快"**。

**相关经验**：`ai_knowledge.md` §4.5 · **P18**（L191）；教训 **L8**（L277）。

<a id="q28"></a>
### Q28 · 开启 ROS 后仿真明显变慢、初始化阶段超时

**A**：开 ROS 后渲染循环额外承担 **20–25%** 负载，原本能在默认超时内完成的初始化会跑不完，且**失败方式是静默的**（见 [Q16](#q16)）。

- ✅ 把关键初始化调用的超时上限按实际负载放大（本次 120 s → 600 s）。
- ✅ 同时给这类长步骤设"超过预期 2 倍即视为异常"的硬性上限，而不是无限等待。

**相关经验**：`ai_knowledge.md` §4.3 · **P12** ★★（L175）；教训 **L2**（L241）。

<a id="q29"></a>
### Q29 · 点云场景渲染帧率极低（约 0.25 Hz）

**A**：点数直接决定帧率。本次实测两端后定参：

| 点数 | 帧率 | 与 600K 的均值像素差 |
|---|---|---|
| 600K | 0.25 Hz | 基准 |
| **100K** | **4 Hz** | **仅 1.13** |

✅ 降采样到 100K 并**固定随机种子**保证可复现。质量代价可忽略，帧率提升 16 倍。

**方法论**：性能/质量权衡**要实测两端再定参数**，不要凭感觉取中间值。

**相关经验**：`ai_knowledge.md` §3 · **D9**（L139 附近）；§5.1「量化取舍」（L208）。

---

## 九、未解决 / 仅部分解决的问题

| 问题 | 状态 | 说明 |
|---|---|---|
| 端到端闭环验证门 **G5** | ⚠️ **未解决，两次会话均 DEFERRED** | 缺少"资产升级后完整闭环"的端到端证据。建议参考 `ai_knowledge.md` §5.2「回避端到端证明」（L218）的详细记录 |
| 4 个重建模型 PSNR 22.63 / 23.29 / 24.45 / 23.91 dB | ⚠️ **未达自设 >25 dB 线，未返工** | 原因未定位（可能是输入帧数 278–351 偏少、或标定/尺度基准误差）。**未解决，建议参考详细记录** `ai_knowledge.md` §1.1（L25）与 §5.2（L216） |
| 静态背景从未跑过 PGSR 训练 | ⚠️ 已发现、未补做 | 曾误把 gsplat 的输出目录当成 PGSR 输出（两者不同项目，gsplat 不产 mesh）。**判别方法**：查输出目录下有无 PGSR 的 checkpoint 与 `cameras.json`。详见 `ai_knowledge.md` §4.5 末段（L193） |
| 自定义任务策略得分 0/6 与 0 | ✅ **非缺陷** | 判定为 π0 checkpoint 的 OOD 泛化失败，不是环境故障。判据是"评分链在第几段断掉"。与资产质量无关，不应据此否定基础设施成果 |

---

## 十、贡献指南（追加新问题时）

1. **编号只增不改**。新问题从 `Q30` 开始顺序追加，**不复用已删除的编号，不重排已有编号** —— 外部索引（`00-index.md`、其他文档的交叉引用）依赖编号稳定。
2. **归入现有八类**，尽量不新建类别。确需新建时，追加在第八类之后，并同步更新顶部「快速症状索引」。
3. **每条必须包含四要素**：
   - `**Q**`：以**你实际看到的现象**开头（报错原文、日志片段、可观测行为），不要写成"如何配置 X"。
   - `**A**`：可执行的步骤或命令。
   - **❌ 无效尝试**：`ai_knowledge.md` 刻意保留这一项 —— **排除路径的价值不低于正解**，请一并记录。
   - `**相关经验**`：回指 `ai_knowledge.md` 的 `P`／`L` 编号并附行号（便于 `Read` 的 `offset`/`limit` 精读）。
4. **同步顶部索引**：新增条目后，必须在「快速症状索引」表里加一行症状 → `Qxx` 的映射，否则等于没收录。
5. **三处索引同步**（仓库约定）：本文若新增/改名章节，同步更新 `knowledge/projects/genie_sim_v3/00-index.md` 的行号表；若文档定位变化，再同步 `knowledge/projects/00-index.md` 与 `knowledge/00-index.md`。
6. **脱敏红线**：不得出现账号、密码、密钥、token。本地路径写 `<path>` / `<user_home>`，主机地址写 `<INFER_IP>:<PORT>`。
7. **标注证据等级**：本机实测记 `[实践]`；能在上游仓库验证的记 `[CODE]` 并附相对路径。**缺证据就写"未提及"，不要推测**。
8. **行号会漂**。若引用的行号与实际内容不符，用 `grep -n '^#\{2,3\} '` 重新定位，并顺手修正本文与索引。

---

## 参考

- [`ai_knowledge.md`](ai_knowledge.md) —— 本文的来源。含完整排查过程、无效尝试、决策原因（`P01`–`P18`、`D1`–`D10`、`L1`–`L8`）。
- [`background_knowledge.md`](background_knowledge.md) —— 工具链原理层（v3.2.0）。相关章节：§3.1 三套技术栈（约 L900）、§5.4 安装流程与 `doctor`/`bootstrap`（约 L1150）、§7.1 `geniesim` CLI（约 L1301）。
- [`00-index.md`](00-index.md) —— 本项目章节地图与行号表。
