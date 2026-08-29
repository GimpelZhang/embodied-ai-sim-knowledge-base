# genie_sim_v3 快速上手指南（quickstart）

> **本文是速查卡，不是教程。** 只放"照着敲就能跑"的最短路径与最常撞的坑。
> 每条都给出深读入口——**要理解原理/看完整证据，去对应文档**，本文不重复解释：
>
> | 想知道 | 去哪 |
> |---|---|
> | 代码在哪、为什么这么写 | [`code_knowledge.md`](code_knowledge.md)（1251 行，用 §号跳） |
> | 一条具体报错怎么修 | [`troubleshooting.md`](troubleshooting.md) 顶部「快速症状索引」 |
> | 为什么当初这么选、试过哪些无效 | [`ai_knowledge.md`](ai_knowledge.md) §4 问题表 |
> | API / 设计原理 / 能力边界 | [`background_knowledge.md`](background_knowledge.md) |
>
> **证据等级**：`[CODE]` 可在仓库核实 ｜ `[实践]` 本机踩坑记录，**不是官方结论**。
> **已替换敏感信息**：全文不含账号/口令/密钥/token/本机绝对路径。宿主机路径写 `<repo_root>`、`<path>`；主机地址写 `<INFER_IP>:<PORT>`；密钥写 `<your_key>`。
> 文中形如 `/geniesim/main`、`/isaac-sim/...` 的路径**是容器内路径，照抄即可**（见 §0）。

---

## 0. 先记住三件事（否则后面全看不懂）

`[CODE]`

1. **一次闭环要三个容器，没有 compose 编排，全手工起**：仿真容器 `genie_sim_benchmark`、π0 推理容器 `docker-openpi_server-1`（监听 **9001**）、重建容器（只在 Stage 3 用）。
2. **宿主机 `<repo_root>` 被 bind-mount 成容器内 `/geniesim/main`**，工作目录也钉在那里。所以脚本里的 `/geniesim/main/...` 不是本机路径。
   > 好处：**改宿主机上的 `.py` 立即生效，不用重启容器**。
3. **容器里有 4 个互相隔离的 Python，选错就 `ModuleNotFoundError`**：

   | 解释器 | 用来跑 |
   |---|---|
   | `/isaac-sim/python.sh` | ★ 仿真主进程、benchmark、**所有用 `pxr` 的脚本** |
   | `/geniesim/generator_env/bin/python` | 场景 DSL 生成器 |
   | `/geniesim/record_env/bin/python` | 解 `.mcap`（锁 `numpy<2.0`） |
   | `/geniesim/teleop_env/bin/python` | 遥操作 |

   **拿不准就用 `python.sh`**——除了生成器和解 mcap，其余都是它。

---

## 1. 环境准备

### 1.1 前置条件

`[CODE]` / `[实践]`

| 项 | 要求 | 不满足会怎样 |
|---|---|---|
| GPU | NVIDIA，**先查 compute capability**（`nvidia-smi --query-gpu=compute_cap --format=csv`） | 重建镜像编译期架构写死，装不上或 kernel image 报错 |
| 驱动 | 宿主机需能提供 Vulkan/GL 库 | headless 渲染全盘失败 |
| Docker | 支持 `--gpus all`、`--privileged`、`--network=host` | 无法启动 |
| 磁盘 | 仿真镜像 + π0 镜像（约 19 GB）+ 资产，**预留 100 GB 以上** | 构建中途失败 |
| 本仓库 | ⚠️ **`genie_sim_v3_tour` 是覆盖层，不能独立跑通** | 见下 §1.2 |

### 1.2 ★ 组装工作目录（最容易忽略的一步）

`[CODE]` 本覆盖层**缺 `entrypoint.sh`、`patch/*.patch`、生成器主体、`assets/`、`openpi/`**，必须先叠上游：

```bash
# ① 先 clone 上游本体
git clone <上游 genie_sim 仓库> <repo_root>

# ② 把本覆盖层的文件叠进去（覆盖同名文件）
#    覆盖层提供：config/*.yaml、scene_recon_scripts/、stage2_generate_scenes*.py、docs/ 等

# ③ 备好资产目录 assets/（被 .gitignore 忽略，需另行获取）

# ④ π0 策略侧另需 clone 到 <repo_root>/openpi（分支 genie_sim）
git clone -b genie_sim https://github.com/AgibotTech/ACoT-VLA.git <repo_root>/openpi
```

> ⚠️ 上游是 **v3.2.0**，而本覆盖层是 **3.0 布局**。两者目录结构不同（`source/geniesim/` ↔ `source/geniesim_benchmark/src/geniesim_benchmark/`），环境变量也改了名。**直接叠会有落差**，先读 `code_knowledge.md` §6.4。

### 1.3 构建镜像

```bash
# 仿真镜像（在 <repo_root> 下）
docker build -f ./scripts/dockerfile \
  -t registry.agibot.com/genie-sim/open_source:latest .

# 需要代理时
docker build -f ./scripts/dockerfile \
  --build-arg http_proxy=http://<INFER_IP>:<PORT> \
  --build-arg https_proxy=http://<INFER_IP>:<PORT> \
  --network=host \
  -t registry.agibot.com/genie-sim/open_source:latest .
```

**重建镜像（只有做 Stage 3 才需要，约 30–60 分钟）**：

```bash
# ★ 先按你的显卡改 source/scene_reconstruction/Dockerfile:8
#   上游原值 8.9（RTX 4090/L40）｜ 本仓库已改成 8.0（A100/A30）
#   3090/A10 → 8.6 ｜ H100 → 9.0    改完必须重编
docker build -f source/scene_reconstruction/Dockerfile -t scene_recon:latest .
```

> ⚠️ 该 Dockerfile `:140` 有个**上游自带的 typo** `pip install e .`（少横线，应为 `-e .`），会导致 hloc 装不上。自建镜像时顺手修掉。详见 `code_knowledge.md` §7.4。

### 1.4 启动仿真容器

```bash
bash scripts/start_headless.sh
```

这一个脚本就够了。它内部做两件必须的事：预建 8 个缓存目录并 `chown` 到容器 UID **1234:1234**（与宿主机 UID 不同），然后 `docker run` 挂上 GPU、宿主机 GL 库和工作目录，最后 `sleep infinity`——**容器只挂着不干活，后续全靠 `docker exec`**。

> ⚠️⚠️ 两个高频翻车点 `[实践]`：
> - **`/tmp/nvidia-libs` 在 tmpfs 上，重启即失**。补完库后**必须重建容器**，旧容器挂载已失效。
> - 那个 `chown` 少做一次，容器会因写不进缓存而以各种间接症状失败（`troubleshooting.md` §二 Q05–Q08）。

### 1.5 环境变量：最小必需集

`[CODE]` 跑仿真主进程时**这几个必须设**（完整表见 `code_knowledge.md` §2.8）：

```bash
export ALIEN_HEADLESS=1                    # ★ 无头必设，否则 Lula IK 求解器报错
export SIM_REPO_ROOT=/geniesim/main        # v3.2.0 已改名 GENIESIM_REPO_PATH（旧名仍兼容）
export ROS_DISTRO=jazzy
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export VK_ICD_FILENAMES=/usr/local/nvidia/glx/vulkan/nvidia_icd.json
export LD_LIBRARY_PATH=/isaac-sim/exts/isaacsim.ros2.bridge/jazzy/lib:/usr/local/nvidia/glx
export PYTHONPATH=/isaac-sim/exts/isaacsim.ros2.bridge/jazzy/rclpy:$PYTHONPATH
source /isaac-sim/setup_ros_env.sh
```

**只跑生成器时**换成 `PYTHONPATH=/geniesim/main/source`，且 `cwd` 必须是 `/geniesim/main`。

**LLM 凭据一律走环境变量，绝不写进代码**：`API_KEY` / `BASE_URL` / `MODEL`。
> ⚠️ 本仓库 `stage2_generate_scenes_r2.py:12` 有过明文硬编码（key 已吊销）——**别照抄那种写法**，第一版脚本 `stage2_generate_scenes.py:186` 才是对的。见 `code_knowledge.md` §7.3。

---

## 2. 运行示例

### 示例 A ★ 最常用：跑一次完整闭环评测（Stage 1）

**第 1 步 —— 先起 π0 服务，否则仿真会永久挂死。**

`[CODE]` `compose.yml` **没有 `command` 字段**，`docker compose up -d` 只让容器空转，服务并没起来：

```bash
sudo docker exec -d docker-openpi_server-1 bash -c \
  'cd /openpi && bash scripts/server.sh 0 9001 S2R_PACK_IN_SUPERMARKET'
```

**预期输出**：日志出现 `server listening on 0.0.0.0:9001`。**这才是就绪判据。**

> ⚠️ `docker ps` 显示 `Up` ≠ 服务就绪；端口 LISTEN 而无 ESTABLISHED 也不算。

**第 2 步 —— 起仿真。**

```bash
sudo docker exec genie_sim_benchmark bash -c '
export ALIEN_HEADLESS=1
export SIM_REPO_ROOT=/geniesim/main
export ROS_DISTRO=jazzy
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export LD_LIBRARY_PATH=/isaac-sim/exts/isaacsim.ros2.bridge/jazzy/lib:/usr/local/nvidia/glx
export VK_ICD_FILENAMES=/usr/local/nvidia/glx/vulkan/nvidia_icd.json
export PYTHONPATH=/isaac-sim/exts/isaacsim.ros2.bridge/jazzy/rclpy:$PYTHONPATH
source /isaac-sim/setup_ros_env.sh

/isaac-sim/python.sh source/geniesim/app/app.py \
  --config source/geniesim/config/s2r_pack_in_supermarket.yaml \
  --benchmark.infer_host=localhost:9001
'
```

**预期输出与判据**：

| 阶段 | 应该看到 | 不对的话 |
|---|---|---|
| 启动 | Isaac Sim 加载日志、场景 prim 构建 | 卡在加载 → 查资产路径 |
| 物理初始化 | 进入 physics/render 循环 | ★ 只见 `[Physics Callback]` 刷屏（~18 Hz）+ 99% CPU **但策略侧收不到 `infer`** → 见 §4 问题 ①|
| 推理 | π0 容器日志出现 `infer` 请求 | 一直没有 → `infer_host` 配错（默认是 8999，不是 9001） |
| 结束 | `output/` 下有 episode 产物；开了 `record` 则有 `.mcap` | `.mcap` 为空 → 见 §4 问题 ③ |

**Stage 3 的 real2sim 任务只换 `--config`**：

```bash
  --config source/geniesim/config/s2r_real2sim_custom.yaml \
  --benchmark.infer_host=localhost:9001
```

### 示例 B ★ 排障首选：不接策略的空跑

`[实践]` **这是本仓库最值得抄的做法**——把"场景/资产对不对"和"策略行不行"两个问题拆开：

```bash
# 同上环境变量，只换 config
/isaac-sim/python.sh source/geniesim/app/app.py \
  --config source/geniesim/config/s2r_real2sim_dummy.yaml
```

该配置用 `DummyEnv` + `DemoPolicy`（`model_arc: ""`），**不需要起 π0 容器**。

**预期输出**：场景正常加载、机器人按假策略动、无推理请求。
**判读**：这一步跑通 → 问题在策略侧/网络；这一步就挂 → 问题在场景/资产/渲染。

### 示例 C 渲染自检（怀疑相机全黑时最先跑）

`[CODE]` 四个只读自检脚本，**按"从便宜到贵"排**，都不改状态：

```bash
# ① 最便宜：纯 USD 查材质链，不起 Isaac Sim
/isaac-sim/python.sh scene_recon_scripts/g4_texture_chain_probe.py
#    预期：ALL_TEXTURED_OK（失败 exit 1）

# ② 真渲一帧，输出可断言的数字
/isaac-sim/python.sh render_validation.py
#    预期：CAPTURE_OK + 像素均值/标准差/唯一色数
#    ★ 均值 0.00 = 全黑，见 §4 问题 ②

# ③ 摆一台头部相机渲合成场景
/isaac-sim/python.sh scene_recon_scripts/g4b_render_head_camera.py
#    预期：RENDER_OK … roi_std=…
```

> ⚠️⚠️ **`validate_gates.py` 的 `ALL GATES PASSED` 不可信**：G2 失败时它只打印 `FAIL` 就继续往下跑，末行仍无条件打印通过标记，**退出码是 0**。别拿它当 CI 判据。详见 `code_knowledge.md` §7.4。

> `[实践]` 这几个脚本的存在本身是条教训：**headless 下看不到 viewport，唯一办法是把"渲得对不对"变成可断言的数字**。

---

## 3. 修改关键参数

### 3.1 三层配置，后者覆盖前者

`[CODE]` 由 `source/geniesim/config/params.py` 实现，**没有第四层**（没有"环境变量注入配置"的机制）：

```
① dataclass 默认值  →  ② YAML（--config）  →  ③ 命令行点号覆盖（优先级最高）
```

> ★ **最省事的调试入口**：`override_from_cli()` 为**每个已声明字段**自动生成 `--<dotted.key>` 参数。
> 所以**任何 dataclass 字段都能直接从命令行改，YAML 里没写也行**。

```bash
--app.headless=true            # 切无头（默认 False，是有界面的！）
--benchmark.num_episode=5      # 多跑几个 episode
--benchmark.preview=true       # ★ 存策略输入图，headless 调试神器
--benchmark.fps=15             # 降控制频率
--app.enable_ros=false         # 关 ROS（省 20–25% 渲染负载）
```

### 3.2 按代价从低到高，四种改法

| 想干什么 | 怎么做 | 代价 |
|---|---|---|
| 只调**一次运行** | 命令行 `--xxx.yyy=…`，不动文件 | 最低 |
| 固定**一组设置** | 复制一份 `s2r_*.yaml`，改 `task_name`/`sub_task_name` | 低 |
| **换任务** | 改 6 处，见 §3.4 | 中 |
| 换资产**位姿/尺度** | ⚠️ **只能改 Python 源码里的硬编码常数**（`ALIGN` 字典、`SCALE`/`TRANSLATE`/`QUAT`），**没有配置文件** | 高，见 §4 问题 ⑤ |

### 3.3 最常改的字段

`[CODE]` 完整表见 `code_knowledge.md` §4.2。**注意几个反直觉的默认值**：

| 字段 | 默认 | ⚠️ 注意 |
|---|---|---|
| `app.headless` | `False` | **默认有界面**，无头必须显式设 `true` |
| `app.enable_cameras` | `True` | 关掉则相机 buffer 全空 |
| `app.enable_rate_limit` | `False` | **不开则仿真跑得比策略快** |
| `app.enable_ros` | `False` | `.mcap` 录制的前提；**开了会加 20–25% 渲染负载** |
| `app.physics_step` / `rendering_step` | `120` / `60` | 物理 120 Hz、渲染 60 Hz |
| `benchmark.infer_host` | `"localhost:8999"` | ★★ **默认 8999，实际部署用 9001**——所以命令行**永远**要带这个 |
| `benchmark.policy_class` | `"DemoPolicy"` | ⚠️ **默认是假策略**；要跑 π0 得配 `model_arc: pi` |
| `benchmark.env_class` | `"DummyEnv"` | ⚠️ 同上，默认空环境 |
| `benchmark.preview` | `False` | 调试时开 |

### 3.4 注册一个新任务：必须改 6 处

`[CODE]` **少一处就报"任务未定义"或静默用错资产**：

| # | 文件 | 改什么 |
|---|---|---|
| 1 | `benchmark/config/task_config_mapping.py` | 加 `background` + `eval_dims` |
| 2 | `benchmark/config/robot_init_states.py` | 加机器人初始关节状态 |
| 3 | `plugins/output_system/eval_utils.py` | 在 `TASK_STEPS` 加有序步骤 |
| 4 | `benchmark/config/eval_tasks/<task>.json` | 新建任务定义（相机/机器人/物体） |
| 5 | `benchmark/config/llm_task/<task>/<idx>/LLM_RESULT.py` | 新建场景 DSL 实例 |
| 6 | `config/<name>.yaml` | 新建运行配置，填两级任务名 |

> ⚠️ 第 4 步的 `camera_list` 里 prim 路径**必须与机器人 USD 逐字符一致**，写错**不报错**，只静默录不到那一路图像。

---

## 4. 常见代码问题

> 按**撞见频率**排。每条给"怎么认 → 怎么修"，完整证据链见右列。

### ① ★★ 开了 ROS 就"假死"：日志在刷但策略永远收不到请求

- **怎么认**：`[Physics Callback]` 以 ~18 Hz 刷屏、CPU 99%、π0 侧从未收到第一个 `infer`。**看着像卡住，其实渲染循环还在 tick。**
- **根因** `[CODE]`：`run_on_render_loop`/`run_on_physics_loop` 用 `threading.Event().wait(timeout=120)` 后抛 `TimeoutError`，而循环本身不停。开 ROS 会加 20–25% 渲染负载，**120 s 不够用**。
- **修法（一行）**：`api_core.py:429` 给 `_collect_init_physics` 传 `timeout=600`。
- ★ **升级到 v3.2.0 后这一改动仍然要自己做**——上游 `:1118` 至今不传 `timeout`。
- → `code_knowledge.md` §6.2(b)、§3.1；`troubleshooting.md` Q16

### ② ★★ 4 路相机 RGB 全黑（均值 0.00）但帧率分辨率都正常

- **怎么认**：`render_validation.py` 报均值 0.00；下游 `cv2.cvtColor` 抛 `!_src.empty()`。
- **两条路径** `[CODE]`：
  1. `app.enable_cameras=False` → buffer 空。**先查这个，最便宜。**
  2. Kit 的 `omni_*` 路径 token 未锚定（容器只有 `${exe-path}=/isaac-sim/kit`，缺 `{cache,data,logs}` 子目录）→ shaderdb 初始化失败 → 拿不到 SimulationView → buffer 空。
- ⚠️ LMDB `Failed to acquire exclusive lock ... (256>=256)` 是**要 pin token 的动因**，**不是本级联的直接成因**——**没看到它也可能全黑**。
- ★ **v3.2.0 已上游修掉整条链**（`app_launcher.py:190` `_create_app` 内建 token 重定向，认 `GENIESIM_KIT_RUNTIME_DIR`）。**在新版本上部署，3.0 时期那堆手工绕法都不用了。**
- → `code_knowledge.md` §6.4、§3.2；`troubleshooting.md` Q22

### ③ ★ 录制静默失败：`.mcap` 空或缺某一路

- **根因** `[CODE]`：`record_rosbag()` 起 `ros2 bag record` 时 `stdout/stderr/stdin` **全部 `DEVNULL`**——**录制进程报什么错你都看不见**。
- ⚠️ 这是**上游行为，v3.2.0 至今未修**。
- **排查**：临时把 `DEVNULL` 改成文件重定向再跑；同时核对 `camera_list` 的 prim 路径拼写（§3.4）。
- → `code_knowledge.md` §3.1、§7.4；`troubleshooting.md` Q15

### ④ `ModuleNotFoundError` —— 几乎总是解释器/路径选错

`[CODE]` 对照着查：

| 报错 | 原因 | 修法 |
|---|---|---|
| `No module named 'geniesim'` | 用错解释器或漏了两个前提 | generator 必须 `PYTHONPATH=/geniesim/main/source` **且** `cwd=/geniesim/main`，**两个都要** |
| `No module named 'rclpy'` | 漏 ROS 桥路径 | `PYTHONPATH=/isaac-sim/exts/isaacsim.ros2.bridge/jazzy/rclpy:$PYTHONPATH` |
| `pxr` 相关缺失 | 没用 `python.sh` | 所有 USD 脚本一律 `/isaac-sim/python.sh` |
| `numpy` 版本冲突（解 mcap 时） | 用错环境 | 解 `.mcap` 必须用 `record_env`（锁 `numpy<2.0`） |

### ⑤ 改了资产位姿却不生效 / 找不到配置项

- **根因** `[CODE]`：Real2Sim 对齐常数（`ALIGN` / `SCALE` / `TRANSLATE` / `QUAT`）**只存在于 Python 源码，没有任何配置文件**，而且是**人工量测后手抄进源码**的。
- **修法**：直接改源码常数；量测可用 `scripts/align_3dgs_origins.py`（走 `REAL2SIM_ASSET_DIR` 等环境变量）。
- → `code_knowledge.md` §7.2、§4.6

### ⑥ 改了函数却不生效（`pipolicy.py`）

- **根因** `[CODE]`：`_encode_depth` 在 `L54–57` 与 `L62–65` **被定义了两遍**，后者静默覆盖前者。**Python 不报错。**
- **修法**：删掉前一个定义。改前先确认自己改的是哪一个。
- → `code_knowledge.md` §7.4

### ⑦ `--config` 传了任务名 → "任务配置找不到"

```bash
--config s2r_pack_in_supermarket                              # ❌
--config source/geniesim/config/s2r_pack_in_supermarket.yaml  # ✅ 必须是文件路径
```

### ⑧ 换机器/换显卡后重建镜像失败或 kernel image 报错

- `TORCH_CUDA_ARCH_LIST` 是**编译期写死**的（`source/scene_reconstruction/Dockerfile:8`）。
- ⚠️ **两个方向都要查**：重新 clone 上游拿到 `8.9`（4090 可直接用，A100 要改 `8.0`）；沿用本仓库拿到 `8.0`（A100 直接用，4090 要改回 `8.9`）。改完必须重编。
- → `code_knowledge.md` §7.5、§6.2(c)

### ⑨ 重启宿主机后 headless 渲染全挂

- `/tmp/nvidia-libs` 在 **tmpfs** 上，**重启即失**。补完库后**必须重建容器**（旧容器挂载已失效），光重启容器没用。
- → `troubleshooting.md` §三

---

## 5. 一分钟自检清单

跑不通时**从上往下过一遍**，每条都比它下面那条便宜：

- [ ] π0 容器日志出现 `server listening on 0.0.0.0:9001`？（不是看 `docker ps` 的 `Up`）
- [ ] 命令行带了 `--benchmark.infer_host=localhost:9001`？（默认值是 8999）
- [ ] `--config` 传的是 **YAML 文件路径**而非任务名？
- [ ] `ALIEN_HEADLESS=1` 设了？（不设 Lula IK 报错）
- [ ] 解释器对不对？（USD/仿真 → `python.sh`；生成器 → `generator_env` + `PYTHONPATH` + `cwd`）
- [ ] `/tmp/nvidia-libs` 还在？宿主机重启过就要重建容器
- [ ] 缓存目录 `chown` 到 `1234:1234` 了？
- [ ] 先用 `s2r_real2sim_dummy.yaml` 空跑，把场景问题和策略问题分开
- [ ] 相机可疑就跑 `render_validation.py` 看均值；**别信 `validate_gates.py` 的 `ALL GATES PASSED`**

---

## 6. 相关文档

| 文档 | 用途 |
|---|---|
| [`00-index.md`](00-index.md) | 本项目章节地图（带行号），**四层文档的总入口** |
| [`code_knowledge.md`](code_knowledge.md) | 代码层详解：结构 / 入口 / 模块 / 配置 / 依赖 / 修改点 / 陷阱 / 四层关联 |
| [`troubleshooting.md`](troubleshooting.md) | 按报错现象查的 `Q01`–`Q29`，顶部有「快速症状索引」 |
| [`ai_knowledge.md`](ai_knowledge.md) | 复现复盘：时间线 / 决策 / 问题表（含**无效尝试**列）/ 教训 |
| [`background_knowledge.md`](background_knowledge.md) | 原理层：设计、API、能力边界 |


