# genie_sim_v3 代码知识层（`genie_sim_v3_tour`）

> **本文档的性质**：这是对**本人的复现仓库 `genie_sim_v3_tour`** 的代码结构说明，供未来"改这套工具链"或"在这套工具链上加新任务"时查阅。
>
> **它不是上游 genie_sim 的代码文档。** `genie_sim_v3_tour` 是一个 **curated overlay（选择性覆盖层）**，只收录复现过程中**被改动或新写**的文件，不是上游仓库的完整 checkout。想看上游完整实现，读 `sources/genie_sim_v3/genie_sim/`（本机 clone，v3.2.0）。
>
> **证据等级**：
> - `[CODE]` — 可在 `genie_sim_v3_tour/` 或上游 clone 中逐行核对，本文绝大多数结论属此级。
> - `[实践]` — 来自 `ai_knowledge.md` / `troubleshooting.md` 的本机踩坑记录，**不是官方结论**。
> - `[推断]` — 由 diff 或代码痕迹推出但**无法证明归因**的，全部显式标注。第六章大量使用此级，原因见 §6.1。
>
> **脱敏声明**：本文已替换敏感信息。仓库根目录一律写 `<repo_root>`；主机路径写 `<user_home>`/`<path>`；主机地址写 `<INFER_IP>:<PORT>`。代码中**确实存在一处明文 API key**，本文只写位置不写值，见 **§7.3（安全红线）**。
>
> **重要版本前提**：`genie_sim_v3_tour` 里的代码对应 genie_sim **3.0 时期**的目录结构（`app/`、`benchmark/`、`generator/` 直挂 `source/geniesim/`）；本机上游 clone 是 **v3.2.0**，目录已重构为 `source/geniesim_benchmark/src/geniesim_benchmark/…`。**两者的命令与 import 路径不能互换**，详见 §6.1 与 §6.4。

**三层知识 → 五层知识**。本文是**代码层**，与其余四层的分工：

| 你现在要做的事 | 去哪 |
|---|---|
| **只想尽快装完跑起来 / 想不起命令怎么敲** | ⭐ [`quickstart.md`](quickstart.md) —— 从本文与其余三层提炼的**最短可执行路径**（篇幅小，可整篇读） |
| 改代码 / 加任务 / 找某个类在哪个文件 | **本文** |
| 查某个原理、API 语义、设计为什么这么设计 | [`background_knowledge.md`](background_knowledge.md) |
| 手上有一条报错 | [`troubleshooting.md`](troubleshooting.md) 顶部「快速症状索引」 |
| 想知道当初为什么这么改、试过哪些无效方案 | [`ai_knowledge.md`](ai_knowledge.md) §3 决策表 / §4 问题表 |

> **本文与 `quickstart.md` 的分工**：quickstart 是**派生层**，只挑「可直接照做的部分」，**不新增结论**；本文是它引用的底本。两者若冲突，**以本文为准**。反过来，本文里凡是"该怎么敲"的段落（§2 入口点、§4.5 注册新任务、§5.3 构建注意）都能在 quickstart 找到压缩版：§2 ↔ quickstart §2、§4 ↔ quickstart §3、§5 ↔ quickstart §1、§7 ↔ quickstart §4。

第八章给出本文与其余各层的**逐条映射**。

---

## 一、代码结构总览

### 1.1 仓库性质与规模

`[CODE]` 全仓库 **91 个已跟踪文件（`git ls-files`）、约 15.7K 行**，其中 markdown 文档 **7232 行**，Python **5918 行**（剔除 `llm_task` 生成实例后 5608 行）（`docs/` 与 `wiki_pages/` 是**互为副本**的同一批 5 篇文档），Python 代码约 5.4K 行。上游 genie_sim 完整仓库是数万行量级——**规模差本身就说明这是覆盖层，不是 fork**。

Git 现状 `[CODE]`：4 个提交（`f859316` initial → `489f568` 主体代码+图片+wiki → `10efc72` docs 备份 → `c23e652` README），remote 为**公开** GitHub 仓库。

### 1.2 目录树

```
<repo_root>/                                  # 容器内 bind-mount 到 /geniesim/main
├── README.md                          101 行  三阶段总览（Stage1 闭环 / Stage2 LLM 场景 / Stage3 Real2Sim）
├── LICENSE                                    上游 MPL-2.0 副本
├── .gitignore                                 ★ 直接沿用上游的，见 §1.4
│
├── docs/                                      wiki 内容备份（与 wiki_pages/ 内容相同）
│   ├── README.md                              页面 ↔ 源文件对照表
│   ├── Complete_Stage1.md            1115 行  Stage1 全流程手册（最长）
│   ├── Complete_Stage2.md             942 行  Stage2 LLM 场景生成手册
│   ├── Complete_Stage3.md             517 行  Stage3 Real2Sim 重建手册
│   ├── Genie_Sim_VLA_interface.md     597 行  VLA↔仿真通信与控制回路剖析
│   └── Install_ROS2.md                384 行  Ubuntu 22.04 编译 ROS 2 Jazzy
├── wiki_pages/                                同上 5 篇的副本（GitHub Wiki 上传源）
├── images/                                    7 个演示素材（5 gif + 1 png + 1 jpg），共约 56 MB
│
├── scripts/                          ★ 环境与容器层
│   ├── dockerfile                      94 行  主仿真镜像（FROM nvcr.io/nvidia/isaac-sim:5.1.0）
│   ├── start_headless.sh               39 行  ★ 唯一的容器启动入口
│   └── align_3dgs_origins.py          160 行  量测 3DGS 资产 AABB，算原点补偿量
│
├── stage2_generate_scenes.py          304 行  ★ Stage2 第一轮：LLM 生成场景 DSL
├── stage2_generate_scenes_r2.py       210 行  ★ Stage2 第二轮（EXEMPLAR 强化版）⚠ 含明文密钥
├── render_validation.py                78 行  离屏渲染自检（viewport → replicator 兜底）
│
├── scene_recon_scripts/              ★ Stage3 USD 资产编写器（全部为新写文件）
│   ├── trackA_author_mesh_usd.py      201 行  物体：Mesh + UV 贴图链
│   ├── trackA_author_uv_usd.py        181 行  物体：同上，读 xatlas 产出的 *_uv.npz
│   ├── trackA_author_tsdf_usd.py      166 行  物体：改走 displayColor 顶点色（不用贴图）
│   ├── trackB_author_room_uv_usd.py   109 行  背景房间：Mesh + UV + 地面碰撞代理
│   ├── trackB_bake_zup.py              67 行  背景：把 +90°X 旋转烘进点云，Y-up→Z-up
│   ├── trackB_package_usdz.py          27 行  背景：USDA → USDZ 打包
│   ├── trackB_yup_wrapper.py           32 行  背景：仿 house_2.usd 的 Y-up 外层包装
│   ├── g4_texture_chain_probe.py       93 行  纯 USD 层校验材质链（不起 Hydra）
│   ├── g4b_render_head_camera.py      101 行  真起 Isaac Sim 渲一帧头部相机
│   └── validate_gates.py               72 行  ★ G1–G4 门禁总校验
│
└── source/                           ★ 上游文件的覆盖层
    ├── geniesim/                              3.0 时期目录结构
    │   ├── app/controllers/api_core.py       2147 行  ★ 仿真侧总控（最大单文件）
    │   ├── app/workflow/app_launcher.py       257 行  ★ SimulationApp 启动封装
    │   ├── config/params.py                   176 行  ★ 全部配置的 dataclass 定义
    │   ├── config/s2r_pack_in_supermarket.yaml 10 行  Stage2 运行配置
    │   ├── config/s2r_real2sim_custom.yaml     11 行  Stage3 运行配置（真跑 π0）
    │   ├── config/s2r_real2sim_dummy.yaml      13 行  Stage3 冒烟配置（DummyEnv）
    │   ├── benchmark/config/task_config_mapping.py  263 行  任务→背景/评测维度 查找表
    │   ├── benchmark/config/robot_init_states.py    384 行  任务→机器人初始位姿 查找表
    │   ├── benchmark/config/eval_tasks/pick_real2sim_object.json 119 行  自建任务配置
    │   ├── benchmark/config/llm_task/pack_in_supermarket/{10..15}/  LLM 生成的 6 个场景实例
    │   ├── benchmark/config/llm_task/pick_real2sim_object/0/        自建 real2sim 场景实例
    │   ├── benchmark/policy/pipolicy.py       161 行  ★ π0 策略客户端
    │   ├── plugins/output_system/eval_utils.py 356 行  ★ 评分与进度归约
    │   └── generator/LLM_RESULT.py             32 行  生成器用的 DSL 模板样例
    └── scene_reconstruction/                  Stage3 重建环境
        ├── Dockerfile                         146 行  ★ COLMAP+PGSR+gsplat+Difix 多阶段镜像
        └── scripts/preprocess_mp4.py           31 行  手机视频按 fps 抽帧
```

`★` = 后续章节会展开的核心文件。

### 1.3 按职责重排：五个功能块

`[CODE]` 把上面的树按"改哪块"重组，这是实际查阅时更有用的视图：

| 功能块 | 涉及文件 | 一句话职责 |
|---|---|---|
| **A. 环境与容器** | `scripts/dockerfile`、`scripts/start_headless.sh`、`source/scene_reconstruction/Dockerfile` | 两套互不相干的镜像：仿真镜像（Isaac Sim 5.1.0 基底）与重建镜像（CUDA 11.8 基底） |
| **B. 仿真运行时** | `source/geniesim/app/controllers/api_core.py`、`app/workflow/app_launcher.py` | 起 Isaac Sim、管 stage、跨线程投递任务、录 rosbag |
| **C. 策略接口** | `source/geniesim/benchmark/policy/pipolicy.py` | 把观测打包发给 π0 推理服务，取回 action chunk |
| **D. 任务与场景定义** | `config/params.py`、`config/s2r_*.yaml`、`benchmark/config/**` | 配置 dataclass + 三张查找表 + 任务 JSON + 场景 DSL 实例 |
| **E. 资产生产线** | `stage2_generate_scenes*.py`、`scene_recon_scripts/**`、`scripts/align_3dgs_origins.py`、`render_validation.py` | 两条产线：LLM 生成场景 DSL；实采视频 → 3DGS/TSDF → USD 资产 |

**A/B/C/D 是"改上游"，E 是"新写的工具"**——这条界线与第六章的归因直接相关。

### 1.4 不在仓库里的东西（查之前先知道）

`[CODE]` 这些被 `.gitignore` 排除或本就不在覆盖层内，**不要在本仓库里找**：

| 缺什么 | 为什么 | 想要就去哪 |
|---|---|---|
| `assets/` 全部 | `.gitignore` 第 7–8 行显式忽略（`assets/` 与 `assets`） | 上游资产包需单独下载；**Stage3 自建的 USD 资产（`Aligned.usd`、`diffuse.jpg`）也一并没进版本库** |
| `requirements.txt`（主镜像用） | `scripts/dockerfile:68` `COPY ./requirements.txt` 引用了它，但覆盖层没收录 | 上游 clone 根目录 |
| `source/teleop/requirements.txt` | 同上，`dockerfile:87` 引用 | 上游 clone |
| `source/geniesim/generator/` 除 `LLM_RESULT.py` 外的全部 | 生成器主体（`app.py`、`helper.py`、DSL 实现）未收录，但 Stage2 脚本调用它 | 上游 clone |
| `patch/*.patch`（3 个） | 重建 Dockerfile 第 80/104/135 行 `git apply ../../patch/{colmap-pcd,pgsr,hloc}.patch`，`patch/` 目录**全仓库不存在** | **未发现**——这三个 patch 内容没有留存，是复现该镜像的硬缺口 |
| `third_party/gsplat` | 重建 Dockerfile 第 127 行 `cd ./third_party/gsplat` 假定已存在 | **未发现**，需自行 clone |
| `.mcap` 录制产物、`output/`、`logs/` | `.gitignore` 忽略 | 只在本机 |

> ⚠️ **由此得出一条结论**：`genie_sim_v3_tour` **不是可自包含复现的仓库**。它是"改动集 + 手册 + 演示素材"，必须叠加在上游 clone 与资产包之上才能跑。第二章的所有命令都以此为前提。

---

## 二、入口点与运行方式

### 2.0 路径约定（先读这段，否则后面所有命令都会看不懂）

`[CODE]` 全套代码里**只有一个路径是硬编码的**，就是容器内的 `/geniesim/main`：

```
宿主机 <repo_root>            ──bind-mount──>   容器内 /geniesim/main
（genie_sim 上游 clone 与本
  覆盖层叠加后的工作目录）
```

映射由 `scripts/start_headless.sh:36` 的 `-v $CURRENT_DIR:/geniesim/main:rw` 建立，`-w /geniesim/main` 把工作目录也钉在那里。

**因此**：`scene_recon_scripts/*.py`、`render_validation.py`、`stage2_generate_scenes*.py` 里出现的 `/geniesim/main/...` **不是本机路径，是容器内路径**，照抄即可；但它们**假定容器就叫这个挂载点**，换挂载点必须改代码（见 §7.1）。

### 2.1 运行栈总览：三个容器

`[CODE]` 一次完整闭环需要三个互不相同的容器，**没有 compose 把它们编在一起**，全部手工起：

| 容器 | 镜像 | 由谁定义 | 干什么 |
|---|---|---|---|
| `genie_sim_benchmark` | `registry.agibot.com/genie-sim/open_source:latest` | `scripts/dockerfile`（本地构建） | 跑 Isaac Sim + benchmark + generator |
| `docker-openpi_server-1` | `openpi_server` | **不在本仓库**，来自 `ACoT-VLA` 仓库的 `scripts/docker/serve_policy.Dockerfile` | 跑 π0 推理服务，监听 **9001** |
| 重建容器 | 由 `source/scene_reconstruction/Dockerfile` 构建 | 本仓库 | COLMAP / PGSR / gsplat / Difix3D，**只在 Stage3 用** |

> `[实践]` π0 侧仓库是 `https://github.com/AgibotTech/ACoT-VLA.git`（分支 `genie_sim`），clone 到 `<repo_root>/openpi`，且 `.gitignore` 忽略 `openpi/`——所以本覆盖层里看不到它。

### 2.2 构建仿真镜像

`[CODE]` `scripts/dockerfile:2` 自带用法注释：

```bash
# 在 <repo_root> 下执行
docker build -f ./scripts/dockerfile \
  -t registry.agibot.com/genie-sim/open_source:latest .
```

`[CODE]` 需要代理时走 `ARG`→`ENV`（`dockerfile:39-42`）：

```bash
docker build -f ./scripts/dockerfile \
  --build-arg http_proxy=http://<INFER_IP>:<PORT> \
  --build-arg https_proxy=http://<INFER_IP>:<PORT> \
  --network=host \
  -t registry.agibot.com/genie-sim/open_source:latest .
```

**镜像内建了 4 个互相隔离的 Python 环境** `[CODE]`，选错就 `ModuleNotFoundError`：

| 解释器 | 位置 | 用途 | 定义处 |
|---|---|---|---|
| Isaac Sim 内置 | `/isaac-sim/python.sh` | **仿真主进程、benchmark、所有 `pxr` 脚本** | `dockerfile:69-70` |
| generator venv | `/geniesim/generator_env/bin/python` | 场景 DSL 生成器 | `dockerfile:76-79` |
| record venv | `/geniesim/record_env/bin/python` | 解 `.mcap`（`rosbags`、`numpy<2.0`） | `dockerfile:82-84` |
| teleop venv | `/geniesim/teleop_env/bin/python` | 遥操作 | `dockerfile:88-90` |

镜像还整包装了 **ROS 2 Jazzy desktop** + `rmw_cyclonedds_cpp`（`dockerfile:61-65`），这是 `.mcap` 录制的前提。

### 2.3 启动仿真容器 — `scripts/start_headless.sh`

`[CODE]` 这是**整个仓库唯一的容器启动入口**，39 行，直接 `bash scripts/start_headless.sh` 即可。它做两件事：

**① 预建 8 个缓存目录并 chown 到容器 UID**（`start_headless.sh:7-15`）：

```bash
mkdir -p ~/docker/isaac-sim/{cache/main/ov,cache/main/warp,cache/computecache,config,data/documents,data/Kit,logs,pkg}
sudo chown -R 1234:1234 ~/docker/isaac-sim
```

> ⚠️ `1234` 是镜像内 `isaac-sim` 用户的 UID，**和宿主机用户 UID 不同**。这个 `chown` 少一次，容器就会因为写不进缓存而以各种间接方式失败。详见 `troubleshooting.md` §二（Q05–Q08）。

**② `docker run` 的关键 flag**（`start_headless.sh:17-39`），逐个说明为什么必须有：

| flag | 出处 | 为什么必须 |
|---|---|---|
| `--user 1234:1234` | `:19` | 与上面的 chown 配对 |
| `--entrypoint ./scripts/entrypoint.sh` | `:20` | ⚠️ **该脚本不在本覆盖层**，来自上游；内部 `set -e` + `setfacl` |
| `--gpus all` / `--privileged` | `:22,24` | GPU 直通 |
| `--network=host` | `:23` | 让容器内 `localhost:9001` 直接打到 π0 容器 |
| `-e VK_ICD_FILENAMES=/usr/local/nvidia/glx/vulkan/nvidia_icd.json` | `:27` | ★ 指向**挂进来的宿主机 ICD**，不是容器自带的 |
| `-v /tmp/nvidia-libs:/usr/local/nvidia/glx:ro` | `:35` | ★★ **headless 离屏渲染的命门**：把宿主机显卡 GL/Vulkan 库塞进容器 |
| `-v $CURRENT_DIR:/geniesim/main:rw` + `-w /geniesim/main` | `:36-37` | 建立 §2.0 的路径映射 |
| `bash -c "sleep infinity"` | `:39` | 容器**只挂着不干活**，后续全靠 `docker exec` |

> ⚠️⚠️ `/tmp/nvidia-libs` 在 **tmpfs** 上，**重启即失**。而且补完库之后**必须重建容器**（旧容器的挂载已失效）。`[实践]` 见 `troubleshooting.md` §三。

### 2.4 Stage 1 / 3：跑一次闭环评测

`[CODE]` 仿真主入口是 **`source/geniesim/app/app.py`**（该文件本身不在覆盖层内，是上游文件）。完整命令（`docs/Complete_Stage1.md:615-633`）：

```bash
sudo docker exec genie_sim_benchmark bash -c '
export ALIEN_HEADLESS=1
export SIM_REPO_ROOT=/geniesim/main
export ROS_DISTRO=jazzy
export ROS_VERSION=2
export ROS_PYTHON_VERSION=3
export ROS_LOCALHOST_ONLY=1
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

Stage 3 的 real2sim 任务只换 `--config`（`docs/Complete_Stage3.md:490-492`）：

```bash
  --config source/geniesim/config/s2r_real2sim_custom.yaml \
  --benchmark.infer_host=localhost:9001
```

**先起 π0 服务，否则永久挂死** `[CODE]`（`docs/Complete_Stage1.md:806-807`）——`compose.yml` **没有 `command` 字段**，`up -d` 只会让容器空转：

```bash
sudo docker exec -d docker-openpi_server-1 bash -c \
  'cd /openpi && bash scripts/server.sh 0 9001 S2R_PACK_IN_SUPERMARKET'
# 就绪判据：日志出现 server listening on 0.0.0.0:9001
```

> ⚠️ `docker ps` 显示 `Up` **不等于服务就绪**；端口 LISTEN 而无 ESTABLISHED 也不算。`[实践]` 见 `troubleshooting.md` §五（Q15–Q18）。

**`--config` 必须是 YAML 文件路径，不是任务名** `[CODE]`（`docs/Complete_Stage1.md:656-665`）：

```bash
--config s2r_pack_in_supermarket                              # ❌ 任务配置找不到
--config source/geniesim/config/s2r_pack_in_supermarket.yaml  # ✅
```

### 2.5 Stage 2：LLM 生成场景

`[CODE]` 两步，跑在**同一个仿真容器**内但用**不同解释器**：

```bash
# ① LLM 写 DSL 并调生成器落盘（用 Isaac Sim 解释器起脚本）
sudo docker exec genie_sim_benchmark bash -c '
export API_KEY=<your_deepseek_key>          # ★ 只从环境变量传，绝不写进代码
export BASE_URL=https://api.deepseek.com
export MODEL=deepseek-chat
export PYTHONPATH=/geniesim/main/source
/isaac-sim/python.sh /geniesim/main/stage2_generate_scenes.py
'
```

脚本内部再 `subprocess` 调生成器（`stage2_generate_scenes.py:239-249`），**这一步换 generator venv 且必须同时给 `env` 和 `cwd`**：

```bash
/geniesim/generator_env/bin/python \
    source/geniesim/generator/app.py \
    --scene_id pack_in_supermarket \
    --template_path <生成的 LLM_RESULT.py>
# 必须 PYTHONPATH=/geniesim/main/source 且 cwd=/geniesim/main
# 否则 ModuleNotFoundError: No module named 'geniesim'
```

② 生成完直接用 §2.4 的命令评测，通过 `sub_task_name` + 实例目录号找场景。

### 2.6 Stage 3：重建与 USD 编写

`[CODE]` 分两个环境。**重建**在 `source/scene_reconstruction/Dockerfile` 构建的容器里（conda 多环境，见 §5.1）；**USD 编写**必须回到仿真容器，因为要用 Isaac Sim 自带的 `pxr`：

```bash
# 视频抽帧（重建容器）
python source/scene_reconstruction/scripts/preprocess_mp4.py \
    --video_path <path>/room.mp4 --output_dir <path>/images --fps 2

# 编写 USD 资产（仿真容器，必须用 python.sh 才有 pxr）
/isaac-sim/python.sh /geniesim/main/scene_recon_scripts/trackA_author_uv_usd.py
/isaac-sim/python.sh /geniesim/main/scene_recon_scripts/trackB_author_room_uv_usd.py
```

`[CODE]` `trackA_author_uv_usd.py:178` 支持按需只做某几个物体：

```bash
/isaac-sim/python.sh .../trackA_author_uv_usd.py benchmark_cup_000 benchmark_can_000
# 不带参数 = 处理 ALIGN 字典里的全部三个
```

`[CODE]` `trackB_bake_zup.py:6-8` 的 docstring 额外要求预置 `PYTHONPATH`：

```bash
PYTHONPATH=/isaac-sim/extscache/omni.usd.libs-1.0.1+69cbf6ad.lx64.r.cp311:$PYTHONPATH \
/isaac-sim/python.sh /geniesim/main/scene_recon_scripts/trackB_bake_zup.py
```

> ⚠️ 这个 extscache 目录名**带版本号哈希**，Isaac Sim 版本一变就失效。

### 2.7 诊断与门禁脚本（排障时最先跑这几个）

`[CODE]` 四个都是**只读自检**，不改任何状态，按"从便宜到贵"排：

| 脚本 | 解释器 | 起 Isaac Sim？ | 查什么 | 成功标志 |
|---|---|---|---|---|
| `scene_recon_scripts/g4_texture_chain_probe.py` | `python.sh` | ❌ 纯 USD | Mesh/材质绑定/`diffuseColor` 连接/`st` primvar | `ALL_TEXTURED_OK`，失败 `exit 1` |
| `scene_recon_scripts/validate_gates.py` | `python.sh` | ❌ 纯 USD | G1 能否打开 → G2 prim 计数+顶点色方差 → G3 组合场景 → G4 材质链 | ⚠️ `ALL GATES PASSED` **不可信，见 §7.4** —— G2 失败只打印 `FAIL` 后继续往下跑，末行仍无条件打印该标记 |
| `render_validation.py` | `python.sh` | ✅ | 真渲一帧，先 viewport 后 replicator 兜底 | `CAPTURE_OK` + 像素均值/标准差/唯一色数 |
| `scene_recon_scripts/g4b_render_head_camera.py` | `python.sh` | ✅ | 合成背景+场景，摆一台头部相机渲一帧 | `RENDER_OK … roi_std=…` |

> `[实践]` 这四个脚本的存在本身就是一条教训：**headless 下看不到 viewport，唯一办法是把"渲出来的东西对不对"变成可断言的数字**（`roi_std`、`uniq`、`std_avg`）。对应 `ai_knowledge.md` §6 的教训条目。

`[CODE]` 另有 `scripts/align_3dgs_origins.py`，量测 3DGS 资产 AABB 并输出原点补偿量，**用环境变量配置**：

```bash
REAL2SIM_ASSET_DIR=<path>/assets/objects/real2sim \
REAL2SIM_ALIGN_OUTPUT=/tmp/align_3dgs_origins.json \
REAL2SIM_ALIGN_LOG=/tmp/align_3dgs_origins.progress \
/isaac-sim/python.sh scripts/align_3dgs_origins.py
```

### 2.8 环境变量总表

`[CODE]` 按"谁读它"归类：

| 变量 | 值示例 | 读者 | 作用 |
|---|---|---|---|
| `ALIEN_HEADLESS` | `1` | Isaac Sim / Lula IK | ★ 无头必设，否则 **Lula IK 求解器报错** |
| `SIM_REPO_ROOT` | `/geniesim/main` | `pipolicy.py:25`、`system_utils` | 仓库根；**v3.2.0 已改名 `GENIESIM_REPO_PATH`**（旧名仍兼容——上游 `geniesim_cli/_env.py:122` 原话 "Renamed from SIM_REPO_ROOT; legacy name still read as fallback."，`:329` 有 fallback 实现），见 §6.4 |
| `VK_ICD_FILENAMES` | `/usr/local/nvidia/glx/vulkan/nvidia_icd.json` | Vulkan loader | ★ 指向挂进来的宿主机 ICD |
| `LD_LIBRARY_PATH` | `…/ros2.bridge/jazzy/lib:/usr/local/nvidia/glx` | 动态链接器 | ROS 2 桥 + 宿主机 GL 库 |
| `PYTHONPATH` | `…/ros2.bridge/jazzy/rclpy:$PYTHONPATH` | Python | ★ 否则 `rclpy` `ModuleNotFoundError` |
| `PYTHONPATH` | `/geniesim/main/source` | generator | ★ 否则 `No module named 'geniesim'` |
| `ROS_DISTRO` | `jazzy` | `api_core.py:1827` | 拼 `source /opt/ros/$ROS_DISTRO/setup.bash`，默认值就是 `jazzy` |
| `RMW_IMPLEMENTATION` | `rmw_cyclonedds_cpp` | ROS 2 | 与镜像装的 RMW 对齐 |
| `CUDA_HOME` | `/usr/local/cuda` | 编 CUDA 扩展 | 不设会报 `':/usr/local/cuda-11.8/bin/nvcc'` |
| `API_KEY` / `BASE_URL` / `MODEL` | — | `stage2_generate_scenes.py:186-189` | ★ LLM 凭据，**必须走环境变量**（§7.3） |
| `REAL2SIM_ASSET_DIR` / `_ALIGN_OUTPUT` / `_ALIGN_LOG` | — | `align_3dgs_origins.py:20-22` | 对齐脚本的输入/输出 |
| `TORCH_CUDA_ARCH_LIST` | `8.0` | 重建镜像编译期 | ★ 必须等于**实机** SM 版本；⚠️ **`8.0` 是本地改的，上游原值 `8.9`**，见 §6.2(c)、§7.5 |
| `MAX_JOBS` / `QT_QPA_PLATFORM` | `4` / `offscreen` | 重建镜像 | 限并发编译 / 无头 Qt |
| `UV_HTTP_TIMEOUT` | `1800`（默认 600） | π0 镜像构建 | 网络慢时必调大 |

---

## 三、核心模块详解

选 6 个模块。前三个是**上游代码里被本次复现动过或必须理解的**，后三个是**本次复现新写的**。

### 3.1 `APICore` — 仿真侧的中央调度器 ★最重要

| 项 | 内容 |
|---|---|
| 路径 | `source/geniesim/app/controllers/api_core.py`（2147 行） |
| 主类 | `class APICore`，**96 个方法**（`^    def` 计数；含嵌套闭包为 100）。★ 已与上游 v3.2.0 对照：**96 个全部在上游存在，无本覆盖层独有方法** |
| 上游对应 | `source/geniesim_benchmark/src/geniesim_benchmark/app/controllers/api_core.py`（v3.2.0，3107 行） |

**职责**：所有"对仿真世界的操作"都从这里过——加载物体、设关节、读相机、录 rosbag、发 ROS topic。

**核心设计：双队列 + 跨线程同步** `[CODE]`

Isaac Sim 的 USD stage **只能在自己的循环线程里改**，而策略/评测逻辑跑在别的线程。`APICore` 用两条队列把调用搬到正确的线程上：

```python
def run_on_render_loop(self, func, *args, timeout=120, **kwargs):
    done = threading.Event(); result = {}
    def wrapper():
        try:    result["value"] = func(*args, **kwargs)
        except Exception as e: result["error"] = e
        finally: done.set()
    self.task_queue_on_render_loop.put(wrapper)
    if not done.wait(timeout=timeout):
        logger.error(f"run_on_render_loop timed out after {timeout}s for {func.__name__}")
        raise TimeoutError(f"run_on_render_loop: {func.__name__} did not complete within {timeout}s")
```

配套 `run_on_physics_loop` 同构。消费端：

- `render_step()` — 先 `self._on_recording()`、`self._on_playback()`，再**从渲染队列取一个**任务执行
- `physics_step()` — 从物理队列取一个任务执行

**命名约定**：公开方法 `foo()` 只负责 `run_on_*_loop(self._foo, ...)`，真正干活的是 `_foo()`。**改功能要改 `_` 版本，改线程归属才改公开版本。**

> ★★ **这套机制是"假死"现象的根源** `[CODE]`+`[实践]`：队列任务超时 120 s 抛 `TimeoutError`，但**渲染循环本身仍在正常 tick**——于是日志继续刷、进程不退、GPU 占用照旧，看起来"还在跑"，实际那一路调用早已失败。排障时**必须 grep `did not complete within`**，不能只看进程活不活。对应 `troubleshooting.md` Q19 / `ai_knowledge.md` P13。

**ROS bag 录制**（`api_core.py:1823` 起）`[CODE]`：

```python
ros_distro = os.getenv("ROS_DISTRO", "jazzy")
command_str = f"""
unset PYTHONPATH
unset LD_LIBRARY_PATH
source /opt/ros/{ros_distro}/setup.bash
ros2 bag record -o {self.path_to_save_record} {' '.join(self.record_topic_list)}
"""
process = subprocess.Popen(
    command_str, shell=True, executable="/bin/bash",
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
    stdin=subprocess.DEVNULL,
    preexec_fn=os.setsid,
)
```

（多行字符串靠换行分隔命令，不是 `&&` 串接；外层还有 `if self.enable_ros:` 守卫，且会先 `shutil.rmtree` 掉已存在的输出目录。）

三个关键点：① **先 `unset PYTHONPATH/LD_LIBRARY_PATH`**——因为主进程为了 rclpy 把这两个变量指向了 Isaac Sim 内嵌的 ROS，子进程要用系统 ROS；② `preexec_fn=os.setsid` 建新进程组，停止时 `os.killpg(os.getpgid(pid), SIGINT)` 再兜底 `SIGKILL`，保证 bag 正常收尾；③ **三个流全部 `DEVNULL`**（`stdout`/`stderr`/`stdin`）——**录制失败不会有任何报错**，只能靠文件有没有生成来判断。⚠️ 这段代码与上游 v3.2.0 `:2707` **逐字节相同**（上游只多三行注释），所以这个静默陷阱是**上游行为、不是本次复现引入的**，且**在 v3.2.0 上依然没修**（与 §6.4 那些已被上游修掉的坑不同）。

**自动录制触发**：`_on_recording()` 在 `teleop_recording and wait_recording` 时调 `_start_recording(camera_prim_list=self.task_config["recording_setting"]["camera_list"], fps=30, ...)`，并在 `recording_wait_num == 100` 时 `_dump_recording_info()`。

**依赖**：`omni.isaac.core` / `pxr` / `rclpy`（可选）/ `curobo`（`enable_curobo` 时）/ `self.task_config`（来自 `eval_tasks/*.json`）。

### 3.2 `AppLauncher` — Isaac Sim 启动参数装配

| 项 | 内容 |
|---|---|
| 路径 | `source/geniesim/app/workflow/app_launcher.py` |
| 职责 | 把 `AppConfig` 翻译成 `SimulationApp({...})` 的 kwargs |

**唯一入口是 `SimulationApp(...)`，一旦构造完成绝大多数参数不可改**——所以这里错了，后面全错。关键 kwargs `[CODE]`：

```python
SimulationApp({
    "headless":                 self._headless,
    "disable_viewport_updates": self._headless,   # 无头时顺带关 viewport 刷新
    "renderer":                 self._render_mode,
    "enable_cameras":           self._enable_cameras,
    "limit_cpu_threads":        16,
    ...
})
```

`_config_resolution()` 里读 `self._enable_cameras = getattr(app_config, "enable_cameras", True)`——用 `getattr` 兜底，说明这个字段是**后加的**（见 §6.2）。

> ⚠️ `enable_cameras=False` 会让所有相机 buffer 为空，下游 `cv2.cvtColor` 直接 `!_src.empty()` 断言失败。这是 headless 链路上最隐蔽的一环。

### 3.3 `PiPolicy` — π0 策略客户端

| 项 | 内容 |
|---|---|
| 路径 | `source/geniesim/benchmark/policy/pipolicy.py`（161 行） |
| 主类 | `class PiPolicy(BasePolicy)` |
| 上游对应 | **无法对比——该 clone 内不存在 `pipolicy.py`**（`find . -name 'pipolicy*'` 零命中；`git ls-tree -r HEAD` 该目录下只有 `base.py`/`corobotpolicy.py`/`demopolicy.py`）。但上游 CLI 的环境变量登记表 `source/geniesim_cli/src/geniesim_cli/_env.py:129` **明确把 `geniesim_benchmark/benchmark/policy/pipolicy.py` 列为 `GENIESIM_REPO_PATH` 的 consumer**——说明 v3.2.0 有这个文件，**是本 clone 对该路径不完整**。故本节只描述现状，不声称是本地新增。<br>（另注：该 clone **整个 git index 为空**——`git ls-files` 全仓库返回 0、5721 条 staged-deleted——这与 `policy/` 无关，且**不影响按工作树 diff**，其余文件的对比都正常做成了） |

**关键常量** `[CODE]`：

```python
ROOT_DIR    = os.environ.get("SIM_REPO_ROOT")
TIMEOUT_SEC = 30
```

**三个方法的分工**：

1. `get_payload()` — 组请求。`state` 32 维 + `eef{left,right}` + `images{top_head,hand_left,hand_right}`（**转置成 `(2,0,1)` 即 CHW**）+ `depth`（`uint16`，按 1000/10000 缩放）+ `prompt` / `task_name` / `episode_idx`。有 `gen_config` 时先过 `apply_camera_image_augmentation`。
2. `infer()` — 经 `WebsocketClientPolicy(host, port)` 拿一批动作，塞进 **Action Chunking 缓冲**：`self.action_buffer = deque(actions, maxlen=n)`。
3. `act()` — 每步从缓冲弹一个；缓冲空了就重新 `infer`；**若 `TIMEOUT_SEC=30` 内始终取不到动作**：

```python
os.kill(os.getpid(), signal.SIGINT)   # 给自己发 SIGINT，让 Isaac Sim 走正常退出流程
```

> ★ 这解释了 `[实践]` 里"策略侧不通时进程 30 s 后自己 Ctrl-C 掉"的现象——**不是崩溃，是设计的超时自杀**。对应 `troubleshooting.md` Q17。区别于 §3.1 的 120 s `TimeoutError`（那个不退出）。

**Action Chunking 的节奏**：策略一次返回一段动作序列，物理侧按 30 Hz（`BenchmarkConfig.fps`）逐个消费——**推理频率远低于控制频率**，这是 VLA 能在 30 Hz 闭环里跑起来的原因。

**已知代码缺陷** `[CODE]`：`_encode_depth` **被定义了两遍**（L54–57 与 L62–65），后者覆盖前者。另有一行调试输出 `logger.info(f"DEBUG image shapes: head=…")` 留在正式路径上。见 §7.4。

**`preview` 开关**：`BenchmarkConfig.preview=True` 时把三路图存成 `debug_preview/preview_%04d_<ts>_{head,left_hand,right_hand}.png`——**headless 下确认"喂给模型的图到底长什么样"的唯一手段**。

### 3.4 `stage2_generate_scenes.py` / `_r2.py` — LLM 场景生成流水线

| 项 | 内容 |
|---|---|
| 路径 | `<repo_root>/stage2_generate_scenes.py`（304 行）、`stage2_generate_scenes_r2.py`（210 行） |
| 性质 | **本次复现新写**，用来绕开上游的 Gradio WebUI 走纯 CLI |

**四段结构**（两个文件同构，`_r2` 是第二轮，实例 13/14/15）：

| 段 | 干什么 |
|---|---|
| `SYSTEM_PROMPT` + `REFERENCE_LLM_RESULT` / `EXEMPLAR` | 把场景 DSL 的**契约**写进提示词：`@register()` 装饰器、`root_scene() -> Shape` 必须 `concat_shapes`、`library_call("usd", oid=…, keywords=[…])`、`translation_matrix`/`rotation_matrix`/`transform_shape(shape, matrix)` 的参数顺序、**只能用白名单资产** |
| `filtered_assets()` | `from geniesim.assets import ASSETS_INDEX`，按 6 个前缀过滤——**把资产白名单直接喂给 LLM，从源头掐掉幻觉资产名** |
| `ask_deepseek()` | `api_key=os.environ["API_KEY"]`，`BASE_URL` 默认 `https://api.deepseek.com`，`MODEL` 默认 `deepseek-chat`，`temperature=0.4`，返回后剥 markdown 代码围栏 |
| `materialize_scene()` | `subprocess` 调 `generator/app.py`（见 §2.5），`timeout=300`，**用「调用前后目录集合求差」来识别新生成的实例目录** |

**提示词里编码的几何约束** `[CODE]`（这些数字是"物体不穿模、机器人能够到"的经验值）：

```
桌面 Z = 0.86 / 0.92     桌子放在 (0, 0, 0.265)
X ∈ [-0.30, 0.30]        Y ∈ [-0.40, 0.40]
```

> `[实践]` `_r2.py` 的 `SYSTEM_PROMPT` 多了一节编号的 **"CRITICAL API RULES"**（只有 `oid`/`keywords` 合法、**绝不能写 `shape=`**、`transform_shape` 的参数顺序、必须 `@register()`）——这是第一轮 LLM 反复生成非法 DSL 之后**把错误反过来写进约束**的产物，对应 `ai_knowledge.md` 的决策条目。

> ⚠️ **`stage2_generate_scenes_r2.py:12` 存在明文 API key 硬编码**，且已推到公开仓库。**该 key 已于 2026-08-29 吊销**（已非活凭据），但明文串仍在文件与历史中未清理，且这种写法本身不可照抄。详见 §7.3。

### 3.5 `scene_recon_scripts/` — Real2Sim USD 编写工具箱

| 项 | 内容 |
|---|---|
| 路径 | `<repo_root>/scene_recon_scripts/`（9 个脚本，全部**新写**） |
| 依赖 | 只用 `pxr`（USD），**不需要起 Isaac Sim**（除 `g4b_*`） |

**两条 Track**：Track A = 桌面小物体（cup / can / bag），Track B = 房间背景。

**Track A 三个变体，差别只在"颜色从哪来"**：

| 脚本 | 行数 | 颜色来源 |
|---|---|---|
| `trackA_author_uv_usd.py` | 181 | `primvars:st` UV + `textures/diffuse.jpg` 贴图 |
| `trackA_author_tsdf_usd.py` | 166 | **只用 `displayColor`**（PGSR 的 TSDF mesh 自带逐顶点 RGB，不需要贴图） |
| `trackA_author_mesh_usd.py` | 201 | 写到 `assets/real2sim/object_assets/<sem>/<obj>/Aligned.usd` |

**三层 prim 树是本节最该记住的东西** `[CODE]`（`trackA_author_uv_usd.py`）：

```
/World                                    ← defaultPrim
└── /World/<obj>                          ← Xform + RigidBodyAPI + MassAPI   ← 物理在这层
    ├── /Visuals                          ← Xform，扛 translate + scale       ← 视觉在这层
    │   └── Mesh                          primvars:st (TexCoord2f, vertex) + displayColor
    └── /CollisionProxy                   ← Cylinder 或 Cube
                                            purpose="guide"（不渲染）+ CollisionAPI
```

**为什么必须分三层** `[实践]`：重建出来的高模**不能直接当碰撞体**（面数太多、形状破碎）。做法是**视觉用重建高模、碰撞用手摆的简单几何**，靠 `purpose="guide"` 让代理体参与物理但不出现在画面里。

**`ALIGN` 字典是全脚本的配置中心**：每个物体一条 `scale`/`translate`/`size`/`mass`/`proxy_shape`/`proxy_radius`/`proxy_height`/`uv_npz`。scale 值形如 `0.0010107312367600525`（cup）、`0.0012401617708352602`（can）、`0.0018876341714638791`（bag）——**是量测算出来的，不是手调的**（见 `scripts/align_3dgs_origins.py`），但**硬编码在源码里**，换资产必须改代码（§7.2）。

**材质图接线顺序**（漏一环就是纯灰模型）`[CODE]`：

```
UsdPreviewSurface.diffuseColor  ←  UsdUVTexture.rgb
UsdUVTexture.st                 ←  UsdPrimvarReader_float2(varname="st").result
Mesh.primvars:st                 （interpolation = vertex）
```

> ★ **`primvars:st` 必须是 `vertex` 插值**，因为 `xatlas` 展 UV 时会重排顶点；用 faceVarying 会错位。`[实践]`

**Track B（房间）关键常数** `[CODE]`：`trackB_author_room_uv_usd.py` 的 `SCALE=0.103`、`TRANSLATE=(0.049, 0.914, 0.330)`、`QUAT=(0.7071068, 0.7071068, 0, 0)`（= 绕 X 转 90°，Y-up→Z-up），外加 `/World/GroundProxyCollider`（Plane、axis Z、purpose guide）。`trackB_bake_zup.py` 把坐标烘成 `(x, y, z) → (x, -z, y)`；`trackB_package_usdz.py` 用 `UsdUtils.CreateNewUsdzPackage` 打包；`trackB_yup_wrapper.py` 生成 Y-up 包装层。

### 3.6 `eval_utils.py` + 任务注册表 — 评测打分与任务查表

| 项 | 内容 |
|---|---|
| 路径 | `source/geniesim/plugins/output_system/eval_utils.py`、`source/geniesim/benchmark/config/task_config_mapping.py`、`.../robot_init_states.py` |
| 职责 | 把"机器人做到哪一步"翻译成分数 |

`[CODE]` `eval_utils.py` 的 `TASK_STEPS` 给每个任务列出有序步骤：

```python
"pick_real2sim_object": ["Follow", "PickUpOnGripper"]
```

覆盖层侧另有一段 `deque` 驱动的 `progress` 归约 + `SCORE_TEMPLATE`（`:88`）逐步打分逻辑（上游同名文件中没有）；步骤表是 `TASK_STEPS`（`:39`）→ `self.sub_steps`（`:129`），`"STEPS"` 是**输出 JSON 里的键**（`:167`）而非模块常量，**用于把步骤序列折算成阶段分**。

**三张查表**（新增任务必须三处都改，缺一处就报"任务未定义"）：

| 文件 | 位置 | 内容 |
|---|---|---|
| `task_config_mapping.py` | `:214` | `"pick_real2sim_object": {"background": {"G1": "table_task_g1"}, "eval_dims": {"manip": "planar_pick", "cognition": "semantic"}}` |
| `robot_init_states.py` | `:343` | `"pick_real2sim_object": {"G1_omnipicker": G1_DEFAULT_STATES}` |
| `eval_utils.py` | `TASK_STEPS` | 步骤序列 |

（前两者在 `source/geniesim/benchmark/config/`，后者在 `source/geniesim/plugins/output_system/`。）

完整的 6 处注册点见 §4.5。

---

## 四、配置系统

### 4.1 三层配置，后者覆盖前者

`[CODE]` 由 `source/geniesim/config/params.py`（176 行）实现，**没有第四层**（无环境变量注入配置的机制）：

```
① dataclass 默认值        params.py 里的 AppConfig / BenchmarkConfig / LayoutConfig
        ↓ 被覆盖
② YAML 文件               --config source/geniesim/config/<name>.yaml
        ↓ 被覆盖
③ 命令行点号覆盖          --benchmark.infer_host=localhost:9001
```

`ParameterServer` 的三步（`params.py`）：

| 方法 | 作用 |
|---|---|
| `declare_parameter()` | 注册键与默认值（由 `declare_dataclass_params()` 遍历 dataclass 字段自动完成） |
| `set_parameters_from_yaml()` | 读 YAML 覆盖 |
| `override_from_cli()` | **为每个已声明键自动生成一个 `--<dotted.key>` 参数**，bool 走 `_str2bool` |

> ★ 关键推论：**任何 dataclass 字段都能直接从命令行改**，不需要写 YAML。`--app.headless=true`、`--benchmark.num_episode=5`、`--benchmark.preview=true` 都是合法的，即使 YAML 里没写。这是调试时最省事的入口。

### 4.2 三个 dataclass 的关键字段

`[CODE]` `AppConfig`（仿真器本身）：

| 字段 | 默认 | 说明 |
|---|---|---|
| `headless` | `False` | ⚠️ **默认有界面**；无头必须显式 `true` |
| `enable_cameras` | `True` | 关掉则相机 buffer 全空（§3.2） |
| `physics_step` / `rendering_step` | `120` / `60` | 物理 120 Hz、渲染 60 Hz |
| `enable_ros` | `False` | 开 ROS 2 桥；`.mcap` 录制的前提 |
| `enable_rate_limit` | `False` | 限速到实时；**不开则仿真跑得比策略快** |
| `render_mode` | `"RaytracedLighting"` | 渲染管线 |
| `enable_curobo` | `False` | cuRobo 运动规划 |
| `enable_gpu_dynamics` | `False` | GPU 物理 |
| `record_img` / `record_video` | `False` / `False` | 图像/视频落盘 |
| `reset_fallen` / `disable_physics` / `data_convert` / `enable_playback` / `enable_pub_depth_camera` / `livestream` | `False`… / `-1` | 其余开关 |

`[CODE]` `BenchmarkConfig`（评测与策略）：

| 字段 | 默认 | 说明 |
|---|---|---|
| `task_name` / `sub_task_name` | `""` / `""` | ★ 两级任务名，查表用（§4.5） |
| `policy_class` | `"DemoPolicy"` | ⚠️ 默认是**假策略**；要跑 π0 得配 `model_arc: pi` |
| `env_class` | `"DummyEnv"` | ⚠️ 同上，默认空环境 |
| `model_arc` | `"pi"` | 策略架构选择 |
| `infer_host` | `"localhost:8999"` | ⚠️ **默认 8999，但实际部署用 9001**——所以命令行永远要带 `--benchmark.infer_host` |
| `fps` | `30` | 控制频率（§3.3 的动作消费节奏） |
| `num_episode` | `1` | 跑几个 episode |
| `record` | `False` | 录制开关 |
| `output_dir` | `"output"` | 输出目录（已被 `.gitignore` 忽略） |
| `preview` | `False` | ★ 存策略输入图，headless 调试神器 |
| `seed` / `interactive` | `1` / `False` | — |

`[CODE]` `LayoutConfig`（场景布局）：`seed=0`、`autogen_ratio=0.5`、`num_obj=1`。

### 4.3 本次复现自己写的三个 YAML

`[CODE]` 三个都在 `source/geniesim/config/`，**是本次复现新增的**（上游同类文件叫 `g1op_s2r_pack_in_supermarket.yaml`，内容不同，见 §6.2）：

| 文件 | `task_name` | `sub_task_name` | `model_arc` | `env`/`policy` | 用途 |
|---|---|---|---|---|---|
| `s2r_pack_in_supermarket.yaml` | `table_task_g1` | `pack_in_supermarket` | `pi` | 默认 | Stage 1 闭环 |
| `s2r_real2sim_custom.yaml` | `pick_real2sim_object` | `pick_real2sim_object` | `pi` | 默认 | Stage 3 real2sim 闭环 |
| `s2r_real2sim_dummy.yaml` | `pick_real2sim_object` | `pick_real2sim_object` | `""` | `DummyEnv` / `DemoPolicy` | ★ **不接策略的空跑**，用来单独验证场景/资产是否正常 |

共同设置：`app.enable_rate_limit: true`、`app.enable_ros: true`、`benchmark.record: true`、`benchmark.seed: 1`、`num_episode: 1`；两个 real2sim 的还加了 `app.headless: true`。

> ★ **`s2r_real2sim_dummy.yaml` 这个"哑配置"是很值得抄的做法**：把"场景对不对"和"策略行不行"两个问题拆开验证。`[实践]`

**与上游的差异**：上游 `g1op_*` 用 `task_name: table_task_g1_op`、`platform: g1_op`、`model_arc: corobot`、`enable_ros: false`、`record: false`——即**上游默认跑 cuRobo 而非 VLA、不录制、不开 ROS**。

### 4.4 任务定义 JSON

`[CODE]` `source/geniesim/benchmark/config/eval_tasks/pick_real2sim_object.json`（119 行，**新增**）——描述"这个任务的世界长什么样"：

| 段 | 内容 |
|---|---|
| `recording_setting.camera_list` | 三个相机 prim：`/G1/head_link2/Head_Camera`、`/G1/gripper_l_base_link/Left_Camera`、`/G1/gripper_r_base_link/Right_Camera`；`fps: 30` |
| `robot_cfg` | `G1_omnipicker.json` |
| `arm` | `right` |
| 机器人初始位姿 | `(-0.8, 0.0, -0.01)` |
| 场景物体 | `workspace_00` 在 `(0, 0, 0.71)` |

> ⚠️ `camera_list` 里的 prim 路径**必须与机器人 USD 里的实际路径逐字符一致**，写错不会报错，只会静默录不到那一路图像（§3.1 的 `DEVNULL` 特性放大了这个问题）。

配套的 `source/geniesim/benchmark/config/llm_task/pick_real2sim_object/0/LLM_RESULT.py`（104 行）是场景 DSL：

```python
TABLE_HEIGHT = 0.71
invisible_floor()         # 100 × 100 × 0.001 的 cube，type: collision_proxy
invisible_table_proxy()   # 1.2 × 0.8 × 0.02，放在 z = 0.71 - 0.01
real2sim_object()         # 随机 yaw
real2sim_room()           # oid="room_background"，纯视觉、无碰撞
root_scene()              # = room + floor + table + objects
```

> ★ 注意 `real2sim_room()` **只做视觉**，地面/桌面碰撞完全靠两个 invisible proxy——即 §3.5 "视觉高模 + 碰撞简模"策略在场景级的复用。

### 4.5 注册一个新任务：必须改的 6 处

`[CODE]` 少一处就报"任务未定义"或静默用错资产。这也印证了 `ai_knowledge.md` §7.2 的说法：

| # | 文件 | 改什么 |
|---|---|---|
| 1 | `benchmark/config/task_config_mapping.py` | 加 `background` + `eval_dims` 条目 |
| 2 | `benchmark/config/robot_init_states.py` | 加机器人初始关节状态映射 |
| 3 | `plugins/output_system/eval_utils.py` | 在 `TASK_STEPS` 加有序步骤 |
| 4 | `benchmark/config/eval_tasks/<task>.json` | 新建任务定义（相机/机器人/物体） |
| 5 | `benchmark/config/llm_task/<task>/<idx>/LLM_RESULT.py` | 新建场景 DSL 实例目录 |
| 6 | `config/<name>.yaml` | 新建运行配置，填 `task_name`/`sub_task_name` |

### 4.6 怎么改配置（按代价从低到高）

1. **只调一次运行** → 命令行 `--benchmark.xxx=…`，不动文件（§4.1）
2. **固定一组设置** → 复制一份 `s2r_*.yaml` 改 `task_name`/`sub_task_name`
3. **换任务** → 走 §4.5 的 6 处
4. **换资产的位姿/尺度** → ⚠️ 得改 Python 源码里的硬编码常数（`ALIGN` 字典、`SCALE`/`TRANSLATE`/`QUAT`），**没有配置文件**（§7.2）

---

## 五、依赖与环境

### 5.1 ⚠️ 本覆盖层内没有任何依赖清单文件

`[CODE]` 已核实（`git ls-files` + `find` 双查）：仓库内**不存在** `requirements.txt`、`setup.py`、`pyproject.toml`、`environment.yml`。但 `scripts/dockerfile` 却 `COPY` 了三个：

| Dockerfile 行 | COPY 的文件 | 在本覆盖层 |
|---|---|---|
| `:68` | `./requirements.txt` | **未发现** |
| `:76` | `./source/geniesim/generator/requirements.txt` | **未发现** |
| `:87` | `./source/teleop/requirements.txt` | **未发现** |

> ★★ **直接 clone 本仓库无法构建镜像**——必须先叠到上游 genie_sim clone 之上（呼应 §1.4：本仓库不是自包含的）。**具体版本号只能去上游仓库查**，本文档不推测。

### 5.2 仿真镜像的依赖（`scripts/dockerfile`）

`[CODE]` 基础镜像与硬性前提：

```dockerfile
FROM nvcr.io/nvidia/isaac-sim:5.1.0
```

| 类别 | 内容 | 备注 |
|---|---|---|
| 基座 | **Isaac Sim 5.1.0** | 版本强绑定；Python 是 Isaac Sim 内嵌的 **3.11**（见 §2.6 的 `cp311` extscache 路径） |
| apt | `acl`、`liburing2 liburing-dev`、`libvulkan1 vulkan-tools`、`graphviz libgraphviz-dev`、`python3 python3-pip python3-venv` | `acl` 供 entrypoint 的 `setfacl`；`libvulkan1`/`vulkan-tools` 供 headless 渲染排查 |
| ROS 2 | **Jazzy desktop** + `rmw-cyclonedds-cpp`，经 `ros2-apt-source_1.1.0.noble_all.deb` 安装 | 底层 Ubuntu 是 **noble (24.04)** |
| 用户 | `usermod -aG sudo isaac-sim` + NOPASSWD sudoers，`USER 1234:1234` | 与 `start_headless.sh` 的 chown 配对 |
| pip 源 | `-i https://pypi.tuna.tsinghua.edu.cn/simple` **写死在每一条 pip 命令上** | 见 §7.1 |

**唯一的显式版本锁定** `[CODE]`（`dockerfile:84`，record venv）：

```
rosbags pyyaml opencv-python rosbags.image "numpy<2.0"
```

> ★ `numpy<2.0` 是**必须的**：`rosbags` 生态尚未适配 NumPy 2。这也是为什么解 `.mcap` 要单独开一个 venv 而不能用主环境——**主环境和 record 环境的 numpy 大版本不同**。

### 5.3 重建镜像的依赖（`source/scene_reconstruction/Dockerfile`）

`[CODE]` 与仿真镜像**完全独立**，4 个 build stage：

```dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04 as system-builder
ENV TORCH_CUDA_ARCH_LIST="8.0"    MAX_JOBS=4      # ⚠️ 上游原值 8.9，本机改为 8.0（A100），见 §6.2(c)
ENV QT_QPA_PLATFORM=offscreen     CONDA_ALWAYS_YES=true
```

| stage | 装什么 | 版本锁定 |
|---|---|---|
| `system-builder` | CloudCompare `v2.13.2`；colmap-pcd（commit `9cd7d9b…`）；Miniconda3 `py312_24.9.2` | ★ 全部 **pin 到 tag/commit** |
| `pgsr-builder` | PGSR（commit `de24f1a…`），`conda create -n pgsr python=3.8`，torch **cu118**，`pycolmap==3.11.1`，`submodules/diff-plane-rasterization`、`submodules/simple-knn`、`rich`、`laspy` | ★ `pycolmap==3.11.1` 精确锁定 |
| `difix-builder` | Difix3D，`conda create -n difix python=3.8`，`matplotlib scikit-learn plyfile rich` | — |
| `gsplat-builder` | 在 **base env** 里 `pip3 uninstall pycolmap` 后装 `third_party/gsplat` | ★ 见下方冲突说明 |
| （末段） | hloc（commit `e33422…`），用 `/opt/conda/envs/pgsr/bin/python` 安装 | `PYTHONPATH` 指向 hloc 源码目录 |

**三处必须知道的坑** `[CODE]`：

1. ★★ **`TORCH_CUDA_ARCH_LIST` 是编译期写死的**（`Dockerfile:8`）。⚠️ **本仓库的 `8.0` 是本次复现改的，上游原值是 `8.9`**（见 §6.2(c)：全文件 diff 只差这一行）。8.0 = A100/A30，8.9 = RTX 4090/L40。**架构不匹配则 CUDA 扩展要么装不上、要么运行时报 kernel image 错**。
   - **重新部署时先确认你手上是哪张卡，再决定要不要改**：重新 clone 上游拿到的是 `8.9`（4090 可直接用）；A100/A30 要改成 `8.0`；3090/A10 → `8.6`；H100 → `9.0`。改完必须重编。
2. ★ **`pycolmap` 版本冲突是设计好的**：PGSR 要 `3.11.1`，gsplat 要求先卸掉——所以两者**只能分别待在 `pgsr` 和 `base` 两个 conda env 里**，绝不能合并环境。
3. ⚠️ **`patch/{colmap-pcd,pgsr,hloc}.patch` 三个补丁文件在本覆盖层中「未发现」**，但 Dockerfile 的 `git apply` 强依赖它们（`:80`、`:104`、`:135`）。**缺补丁则重建镜像构建必失败**。

### 5.4 π0 策略侧依赖

`[CODE]` 不在本仓库（`.gitignore` 忽略 `openpi/`）：

```bash
git clone -b genie_sim -c http.postBuffer=524288000 \
    https://github.com/AgibotTech/ACoT-VLA.git ./openpi
```

`[实践]` 构建注意：`serve_policy.Dockerfile` 里 `UV_HTTP_TIMEOUT` 需从 `600` 调到 `1800`；`openpi_server` 镜像约 **19.1 GB**，构建约 **30–60 分钟**。

### 5.5 版本约束速查

| 组件 | 版本 | 硬度 |
|---|---|---|
| Isaac Sim | **5.1.0** | 强绑定（extscache 路径带哈希） |
| Python（仿真侧） | 3.11（Isaac Sim 内嵌） | 不可换 |
| ROS 2 | **Jazzy** + CycloneDDS | `api_core.py` 默认 `ros_distro="jazzy"` |
| CUDA（重建侧） | **11.8.0** + cuDNN8 | 与 torch cu118 配套 |
| Python（重建侧） | **3.8**（pgsr / difix env） | conda 显式指定 |
| numpy（record env） | **< 2.0** | 显式锁定 |
| pycolmap | **3.11.1**（pgsr env）/ 卸载（base env） | 显式锁定 + 显式卸载 |
| GPU 架构 | **SM 8.0** | 编译期写死，换卡需改 |
| 宿主机驱动 | 与容器内 Isaac Sim 兼容 + **能提供 Vulkan 库** | `/tmp/nvidia-libs` 手工提取 |

---

## 六、复现过程中的修改点

### 6.1 ⚠️ 先说方法与局限（否则本章会被误读）

`[CODE]` **本仓库不是上游 fork**，只有 4 个提交、无上游历史：

| commit | 日期 | 内容 |
|---|---|---|
| `f859316` | 2026-06-13 | Initial commit（仅 `LICENSE`） |
| `489f568` | 2026-06-14 | 一次性倒入全部代码 + 图片 + 场景实例 |
| `10efc72` | 2026-06-14 | 倒入 `docs/`（**6 个文件**、3577 行；含 `docs/README.md` 21 行） |
| `c23e652` | 2026-06-14 | `README.md` +3 −1 |

> ★★ **所以 git 历史里没有任何"修改"的痕迹**——所有文件都是在 `489f568` 里一次性以最终形态出现的。**无法用 `git log`/`git diff` 恢复改动过程。**

**唯一可行的对比方法**是拿本覆盖层对上游 clone 做文件级 diff，但这里有一个**结构性障碍**：

```
本覆盖层     = genie_sim 3.0 时期布局   source/geniesim/{app,benchmark,config,generator,plugins}
本机上游clone = v3.2.0 布局             source/{geniesim_benchmark/src/geniesim_benchmark,
                                              geniesim_cli,geniesim_generator,geniesim_ros,data_collection}
```

映射关系：本覆盖层 `source/geniesim/<rel>` ↔ 上游 `source/geniesim_benchmark/src/geniesim_benchmark/<rel>`，import 前缀 `geniesim.` → `geniesim_benchmark.`。

**因此 diff 的归因是双向模糊的** `[推断]`：

| diff 侧 | 两种可能含义 |
|---|---|
| `-`（只在上游 v3.2.0） | 上游在 3.0→3.2.0 之间**新增**的 |
| `+`（只在本覆盖层） | ① 本次复现**自己改的**　② 3.0 时期就有、但被 3.2.0 **删掉**的 |

**本章据此分三档**：§6.2 可确认、§6.3 无法归因、§6.4 上游已修。**不把无法归因的算成"我改的"。**

### 6.2 可确认的新增（本次复现自己写的）

判据：文件在上游**任一布局下都不存在**，或内容明显是本项目专有。

| 类别 | 文件 | 行数 | 说明 |
|---|---|---|---|
| **Real2Sim 工具链** | `scene_recon_scripts/`（9 个） | 1049 | ★ 全新。USD 编写（Track A/B）+ Z-up 烘焙 + USDZ 打包 + G1–G4 门禁 |
| **诊断脚本** | `render_validation.py` | 78 | ★ 全新。headless 下唯一的"渲染是否真出图"断言手段 |
| **对齐量测** | `scripts/align_3dgs_origins.py` | 160 | ★ 全新。算 3DGS 资产 AABB 原点补偿量 |
| **CLI 场景生成** | `stage2_generate_scenes.py`、`_r2.py` | 304 + 210 | ★ 全新。绕开 Gradio WebUI 的纯 CLI 链路 |
| **运行配置** | `config/s2r_{pack_in_supermarket,real2sim_custom,real2sim_dummy}.yaml` | — | 上游同类叫 `g1op_s2r_*.yaml`，`task_name`/`platform`/`model_arc` 均不同（§4.3） |
| **新任务定义** | `benchmark/config/eval_tasks/pick_real2sim_object.json` + `llm_task/pick_real2sim_object/0/` | 119 + 104 | ★ 全新任务 `pick_real2sim_object` |
| **生成的场景实例** | `llm_task/pack_in_supermarket/{10..15}/` | — | ★ 6 个实例，正好对应 `stage2_*.py` 的 `VARIANT_SPECS`（10/11/12 来自第一轮，13/14/15 来自 `_r2`） |
| **文档** | `README.md`、`docs/`（5 篇）、`wiki_pages/` | ~7.1K | ★ 全新，`docs/` 与 `wiki_pages/` 互为副本 |

**四处可确认的代码级改动** `[CODE]`（`+` 侧且能与上游 v3.2.0 逐行对照）：

**(a) 相机开关提升为可配置项**（同一改动的两半）

1. `source/geniesim/config/params.py` — 新增 `enable_cameras: bool = True` 字段
2. `source/geniesim/app/workflow/app_launcher.py` — `_config_resolution()` 里
   `self._enable_cameras = getattr(app_config, "enable_cameras", True)`，
   并把 `"enable_cameras": self._enable_cameras` 加进 `SimulationApp({...})` kwargs

> ★ 用 `getattr(..., True)` 兜底而不是直接取属性，是典型的"事后加字段、怕旧配置炸"写法。对应 `[实践]` 里 headless 相机 buffer 为空的排查（§3.2）。

**(b) ★★ `_collect_init_physics` 超时 120 s → 600 s**（本章最高价值的一条）

`source/geniesim/app/controllers/api_core.py:428–429`：

```python
def collect_init_physics(self):
    self.run_on_render_loop(self._collect_init_physics, timeout=600)
```

上游 v3.2.0 对应位置（`.../geniesim_benchmark/app/controllers/api_core.py:1117–1118`）是
`self.run_on_render_loop(self._collect_init_physics)`，**不传 timeout，即用默认 120 s**。
本覆盖层里 `timeout=600` 是**全文件唯一一处非默认 timeout 的调用点**（其余调用点均走 `run_on_render_loop`/`run_on_physics_loop` 的 `timeout=120` 默认值，见 `:153`/`:174`）——这个"唯一性"本身就是它是手工加的证据。

**为什么必须改**：`enable_ros: true` 后渲染循环除 RTX 渲染还要发布 ROS 话题（**+20–25% 负载**，与 `Q28` 实测吻合），`_collect_init_physics` 无法在 120 s 内跑完。

**故障形态极具欺骗性**——worker 线程死了，Isaac kit 主线程仍在渲染，进程永不退出。日志特征：

```
ERROR    [logger.py:76] run_on_render_loop timed out after 120s for _collect_init_physics
TimeoutError: run_on_render_loop: _collect_init_physics did not complete within 120s
Exception in thread Thread-2 (worker):
  File ".../task_benchmark.py", line 153, in evaluate_policy
    self.api_core.collect_init_physics()
```

伴随 `[Physics Callback] xx.xx Hz` 以约 18 Hz 无限刷屏、Python 占 99% CPU、策略服务端**永远收不到第一个 `infer` 请求**、无 `EPISODE FILE` 标记。
→ 这正是 `Q16` / §3.1 描述的"假死"机制的**具体实例与修法**，也是 `L2`（给长任务预设独立超时）的直接物证。

> ⚠️ **归因说明**：这仍是一个 `+` 侧 diff，按 §6.1 的规则严格来说是有歧义的（也可能是 3.0 代码而被 3.2.0 删掉）。但两点让它远强于 §6.3 里的其它条目：① 它是一次**精确针对那个正在卡住的调用**的 120→600 定向加码；② `[实践]` 记录独立描述了同一个故障。**这是本仓库最强的"确属本地改动"候选**，但不是零疑义。
> ⚠️ 只需要改 `_collect_init_physics` 这一处；其它调用点在 120 s 下正常。
> ★ 源码树是 bind-mount 进容器的（`-v $CURRENT_DIR:/geniesim/main:rw`，§2.3），所以**在宿主机改 `api_core.py` 立即生效，不必重启容器**。

**(c) ★ 重建镜像的 GPU 架构 `8.9` → `8.0`（本仓库归因最干净的一处改动）**

`source/scene_reconstruction/Dockerfile:8`。这个文件在上游 v3.2.0 中**同名同路径存在**，因此可以直接整文件 diff——结果是**全文件只差这一行**：

```diff
-ENV TORCH_CUDA_ARCH_LIST="8.9"     # 上游默认：RTX 4090 / L40 (SM 8.9)
+ENV TORCH_CUDA_ARCH_LIST="8.0"     # 本机改为：A100 / A30 (SM 8.0)
```

> ★★ **这是全仓库唯一一处"同名文件整体 diff 只差一行"的改动**，不存在 3.0/3.2.0 布局错位带来的归因歧义——比 §6.2(b) 还干净。
> ⚠️ **换显卡必须改回来并重编**：`TORCH_CUDA_ARCH_LIST` 是编译期写死的，见 §7.5、`L1`。**上游默认值是 `8.9`，不是 `8.0`**——如果你的卡是 4090，直接用上游原值即可。

**(d) ~~打开 `record_rosbag()` 调用~~ —— 此项已被复核推翻，见 §6.3**

`README.md` 自述"取消注释以恢复 `.mcap` 录制"，但**代码里无法确认**：
- 本覆盖层 `api_core.py:1315` 的 `self.record_rosbag()` **是未注释状态**；
- 上游 v3.2.0 对应调用（`:2192`）**同样未注释**；
- 全文件 grep 不到任何被注释掉的调用行（`^\s*#\s*(self\.|call\()` 零命中）。

"两边都没注释"**无法证明**这里发生过改动——它同时兼容"本地取消了注释"和"3.0 本来就没注释"两种解释。按 §6.1 的归因规则，这条降级为 `[推断]`，见 §6.3。

**(e) `[实践]` π0 侧 Dockerfile 的代理与超时修正**（**不在本覆盖层内**，仅见于 `docs/`）

`openpi/scripts/docker/serve_policy.Dockerfile`（`openpi/` 未纳入本仓库，见 §1.4，故**无法 `[CODE]` 验证**）：

```diff
 ARG http_proxy
 ARG https_proxy
 ARG all_proxy
+ENV http_proxy=${http_proxy} \
+    https_proxy=${https_proxy} \
+    all_proxy=${all_proxy}
 ENV UV_LINK_MODE=copy \
     ...
-    UV_HTTP_TIMEOUT=600 \
+    UV_HTTP_TIMEOUT=1800 \
```

- `ARG`→`ENV`：`ARG` 对子进程不可见，`uv sync` 派生的 `git`/`curl` 收不到代理 → `git fetch lerobot` 报 `GnuTLS recv error (-9)`。**与 `Q02`「代理必须三层各配一次」同源。**
- `600`→`1800`：大 wheel（`nvidia-cusparse-cu12`）超 600 s → `Failed to download distribution due to network timeout`。

**其余 `[实践]` 自述、代码里定位不到的**（保持 `[推断]`）：

- 手工提取宿主机 Vulkan 驱动到 `/tmp/nvidia-libs`（**这不是改代码，是改环境**，见 §2.3）

### 6.3 无法归因的差异（可能是本地改、也可能是 3.0 遗留）

`[推断]` 如实列出，**不声称是本次改动**：

| 文件 | `+` 侧内容 | 备注 |
|---|---|---|
| `benchmark/policy/pipolicy.py` | 整个文件（161 行） | **上游 clone 内根本没有这个文件**（`find` 零命中），无从 diff；而上游 `geniesim_cli/_env.py:129` 却把它列为 `GENIESIM_REPO_PATH` 的 consumer，可见 v3.2.0 有此文件、**是本 clone 不完整**。文件内含调试代码与重复函数定义（§7.4），带明显"改过"的气味，但不能据此断言 |
| `app/controllers/api_core.py` | 2147 行 vs 上游 3107 行 | 差 960 行。★ **已做方法名集合 diff：本覆盖层 96 个方法全部存在于上游，零个独有方法**；36 处差异全是上游新增，且干净地聚成 3.2.0 的四组新特性（向量化环境 `fork_for_env`/`is_vec_mode`、共享相机 `_setup_shared_cameras`、LocalRecorder 拆分 `_start_local_recording`、底盘控制 `apply_chassis_action`）。**所以这 960 行是上游生长，不必再在此文件里找隐藏的本地改动**——唯一一处是 §6.2(b) 的 `timeout=600` |
| `app/controllers/api_core.py` `_start_recording()` | 调用顺序不同 | 本覆盖层 `:1315` 在 `if not self.enable_physics:` 块**之前**调 `record_rosbag()`；上游 `:2192` 在该块**之后**调，并多一句 `self.recording_started = True`（本覆盖层完全没有）。`recording_started` 与上游新的 LocalRecorder/rosbag 拆分绑定，**大概率是 3.2.0 重构而非本地改动** |
| `app/controllers/api_core.py` `record_rosbag()` 是否曾被注释 | — | `README.md` 自述取消过注释，但两边都是未注释状态、且本覆盖层零个被注释的调用行，**无法证实也无法证伪**（详见 §6.2(c)）。函数体本身与上游 `:2707` **逐字节相同** |
| `plugins/output_system/eval_utils.py` | `deque` 驱动的 `progress` 归约 + `SCORE_TEMPLATE`（`:88`）/`TASK_STEPS`（`:39`）打分 | 上游同名文件无此段 |
| `app/workflow/app_launcher.py` | NVIDIA 版权头、`geniesim.plugins.logger` import | 大概率是 3.0 原样 |
| `config/params.py` | 上游 v3.2.0 独有字段：`on_demand_render`、`enable_vec`、`shared_cam_render_frames`、`shared_cam_first_render_frames`、`num_instances`、`language_perturbation(_config)`、`instruction_mode`（`"full"`/`"subtask"`） | 这些是 **`-` 侧**，即上游新增，本覆盖层没有 |

### 6.4 ★ 上游 v3.2.0 已修掉的坑（重新部署时最有价值的一节）

`[CODE]` diff 中发现 **v3.2.0 的 `app_launcher.py` 多出一大段 `_create_app` 代码**，本覆盖层没有。这段代码把 Kit 107.3 的路径 token 全部重定向：

```
${data} ${cache} ${logs} ${documents}  以及  ${omni_*} ${shared_documents}
        ↓ 统一锚到
GENIESIM_KIT_RUNTIME_DIR   或   /workspace/.kit
```

**上游为这段代码写了 20 余行注释**（`app_launcher.py` `_create_app` 定义在 `:190`，注释块 `:192–211`，`token_root` 在 `:212`；均已逐行核对）。**注意：上游把这里讲成两件相关但不同的事，不是一条线性因果链**——本文档早先版本把它们串成一条，是转述错误，现更正：

**(甲) 为什么要 pin token —— LMDB 锁损坏的风险**

Kit 107.3 默认把 `${data}/${cache}/${logs}` 锚在 `${exe-path}/<name>`（即 `/isaac-sim/kit/<name>`），**与 `$HOME` 无关**。而 `/isaac-sim/kit` 是 Docker overlay 挂载点，**容易出 LMDB 锁损坏**：

```
"Failed to acquire exclusive lock to data store (256>=256)"
"Unexpected key-value database error"
```

上游特别点出：**以 root 身份能写成功，恰恰掩盖了底层的不稳定**（`root's write success there masks the underlying flakiness`）。所以要把 token 钉到 bind-mount 的 `/workspace` 上。

**(乙) 相机全黑的直接原因 —— `omni_*` 族没被锚定**

需要覆盖的是**两族互不相同的 token**：`${cache}/${data}/${logs}/${documents}`（材质库、cookedmesh 缓存）与 `${omni_cache}/${omni_data}/${omni_logs}`（`omni.datastore`、**`rtx::shaderdb`**、`stage_templates`、`screenshot_page`）。geniesim3.5 容器**只提供 `${exe-path}=/isaac-sim/kit`，却没有 `/isaac-sim/kit/{cache,data,logs}`**，于是：

```
omni_* 族未锚定（目录缺失）
   → shaderdb 初始化失败
   → 拿不到 SimulationView
   → 相机 buffer 为空
   → 下游 cv2.cvtColor 报 !_src.empty()
```

即：**shaderdb 这条级联的成因是 token 目录缺失／未锚定，而不是 (甲) 的 LMDB 报错本身**。两者共同的解法是同一段 token 重定向（`token_root = os.environ.get("GENIESIM_KIT_RUNTIME_DIR") or "/workspace/.kit"`，`:212`），但**排障时不要因为没看到 `(256>=256)` 就排除相机全黑的可能**。

> ★★ **(乙) 这条链正是本次复现在 3.0 上花大力气绕过的**（对应 `troubleshooting.md` 的相机/渲染类条目）。**如果在 v3.2.0 上重新部署，这一串 3.0 时期的手工绕法都不再需要。**

`[CODE]` 另外两处上游已改进：

| 项 | 3.0（本覆盖层） | v3.2.0 |
|---|---|---|
| 仓库根环境变量 | `SIM_REPO_ROOT` | `GENIESIM_REPO_PATH`（旧名作为 fallback 仍可读） |
| 资产路径环境变量 | `SIM_ASSETS` | `GENIESIM_ASSETS_PATH`（同上） |
| 启动入口 | `python.sh source/geniesim/app/app.py --config <yaml>` | `geniesim` CLI（`source/geniesim_cli`） |

> ⚠️ **反例——不要以为上游把什么都修了**：**§6.2(b) 的 `_collect_init_physics` 超时 120 s → 600 s 在 v3.2.0 上仍需自己改**——上游 `:1118` 依旧不传 `timeout`，`run_on_render_loop` 的默认值仍是 120 s。开 ROS 就会复现同一个"假死"。**这是唯一一条需要带到新版本上的代码改动。**

> ⚠️⚠️ **本文档全部命令属于 3.0 时期，不可直接套用到 v3.2.0。** 迁移前先读 `background_knowledge.md`（描述 v3.2.0）与 `ai_knowledge.md` §7.1 的版本落差表。

### 6.5 一句话总结

**"改上游"的部分极少但有两条关键**（能站住的只有三类：`enable_cameras` 涉两个文件、`api_core.py:429` 的 `timeout=600`、重建 `Dockerfile:8` 的 `TORCH_CUDA_ARCH_LIST` `8.9→8.0`；后两者**都需要带到 v3.2.0**——前者上游至今未修，后者取决于你的显卡。`README.md` 自述的"取消注释恢复录制"经复核**无法证实**，见 §6.2(c)），
**"新写的"部分很多**（Real2Sim USD 工具链 + CLI 场景生成 + 诊断门禁，约 1800 行 Python），
**"最费时间的"部分根本不在代码里**（Vulkan 库提取、UID/缓存目录权限、多 Python 环境隔离、π0 服务手工启动）。

---

## 七、代码中的注意事项

### 7.1 硬编码的容器路径（改挂载点必炸）

`[CODE]` 全仓库**没有一个 `TODO`/`FIXME`/`HACK` 注释**（已 grep 确认），但硬编码常量很多。最普遍的是容器路径：

| 硬编码值 | 出现位置 | 后果 |
|---|---|---|
| `/geniesim/main` | `stage2_generate_scenes.py`（`REPO_ROOT`）、`_r2.py`（`REPO`）、`scene_recon_scripts/*`、`render_validation.py`、`g4b_*` | ★ 换挂载点则全部脚本失效（§2.0） |
| `/geniesim/generator_env/bin/python` | `stage2_generate_scenes.py:240`、`_r2.py` | 换 venv 位置即失效 |
| `/isaac-sim/extscache/omni.usd.libs-1.0.1+69cbf6ad.lx64.r.cp311` | `trackB_bake_zup.py` docstring | ★★ **带版本哈希 + `cp311`**，Isaac Sim 一升级就失效 |
| `/usr/local/nvidia/glx` | `start_headless.sh`、所有启动命令 | 与 `/tmp/nvidia-libs` 约定绑定 |
| `https://pypi.tuna.tsinghua.edu.cn/simple` | `scripts/dockerfile` **每一条 pip 命令** | 境外/内网构建需逐条改 |
| `registry.agibot.com/genie-sim/open_source:latest` | `start_headless.sh`、`dockerfile` | 私有 registry + `:latest`（**不可复现的 tag**） |
| `<path>/stage2/scene_{NN}/`（原文为宿主机绝对路径，**已脱敏**） | `stage2_generate_scenes.py:15,19`（docstring 里的输出路径示例） | 仅注释，不影响运行 |

> ⚠️ **`:latest` 标签值得单独提一句**：镜像内容随构建时间漂移，"同一条命令跑出不同结果"的经典来源。要复现请自己打日期 tag。

### 7.2 硬编码的几何常数（换资产必须改源码）

`[CODE]` **Real2Sim 的对齐参数完全没有配置文件**，全在 Python 源码里：

| 常量 | 位置 | 值 |
|---|---|---|
| `ALIGN` 字典（每物体 `scale`/`translate`/`size`/`mass`/`proxy_*`/`uv_npz`） | `trackA_author_uv_usd.py` 等 | cup `scale=0.0010107312367600525`、can `0.0012401617708352602`、bag `0.0018876341714638791` |
| `SCALE` / `TRANSLATE` / `QUAT` | `trackB_author_room_uv_usd.py` | `0.103` / `(0.049, 0.914, 0.330)` / `(0.7071068, 0.7071068, 0, 0)` |
| 默认点云宽度 | `trackB_bake_zup.py` | `0.29126215` |
| `TABLE_HEIGHT` | `llm_task/pick_real2sim_object/0/LLM_RESULT.py` | `0.71` |
| 桌面 Z / 摆放范围 | `stage2_generate_scenes.py` 的 `SYSTEM_PROMPT` | Z `0.86`/`0.92`，X ∈ [-0.30, 0.30]，Y ∈ [-0.40, 0.40] |
| 机器人初始位姿 | `eval_tasks/pick_real2sim_object.json` | `(-0.8, 0.0, -0.01)` |
| 头部相机位姿 | `g4b_render_head_camera.py` | `(-0.8, 0, 1.3)`，RotX −30 / RotY −90，焦距 20，光圈 36，clip `(0.05, 50)` |

> ★ 这些 15 位小数的 scale **是量测算出来的**（`align_3dgs_origins.py`），不是手调。但**结果被手工抄回了源码**——量测与消费之间没有自动通路。要接新资产：先跑对齐脚本拿数，再**手动填进 `ALIGN`**。这是本工具链最明显的可改进点。

### 7.3 ⚠️⚠️ 明文凭据（本文档已脱敏，但仓库本身仍需处置）

**本文档已替换敏感信息**。实际仓库中存在**两类**明文凭据，且均已随 `489f568` / `10efc72` 推送到**公开** GitHub 仓库。

**(1) LLM API key —— 3 个已跟踪文件**

| 文件 | 行 | 形态 |
|---|---|---|
| `stage2_generate_scenes_r2.py` | 12 | `client = OpenAI(api_key="<HARDCODED SECRET REDACTED>", ...)` |
| `docs/Complete_Stage2.md` | 218 | 同一 key 被抄进文档 |
| `wiki_pages/Complete_Stage2.md` | 218 | 同上（`docs/` 的副本） |

**(2) ⚠️ 宿主机 sudo 口令 —— 2 个已跟踪文件、共 36 处**

以 `echo '<REDACTED>' | sudo -S …` 的写法散布在文档正文的可复制命令块里：

| 文件 | 出现行 | 处数 |
|---|---|---|
| `docs/Complete_Stage2.md` | 174, 187, 427, 448, 449, 460, 488, 492, 500, 514, 544, 547, 551, 562, 637, 642, 660, 683 | 18 |
| `wiki_pages/Complete_Stage2.md` | 同上同行号（副本） | 18 |

> ★ **讽刺之处**：同一份 `docs/Complete_Stage2.md` 的第 941 行自己写着
> *"sudo 密码只在执行时用 stdin 注入，**不要写进任何提交到 git 的文件**。本文档里出现的密码请视情况脱敏"*
> —— 纪律写下来了，但从没执行。这是 `L`-级教训的绝佳反面物证：**"最后统一脱敏"等于不脱敏**。

**处置状态（2026-08-29）**：`[实践]` ★ **第 1 步已完成——两类凭据均已由仓库所有者吊销/更换**，因此仓库中的明文串**已不再是活凭据**。但**第 3–5 步仍未做**：明文串本身还留在工作树与 git 历史里，仍应清掉（既是卫生问题，也避免下一个读者误以为可用、或照抄这种写法）。

**处置建议（顺序不能反）**：

1. ✅ **已完成 · 吊销/更换两类凭据** —— LLM key 已在服务商控制台吊销；宿主机口令已改。⚠️ 这一步必须最先做的原因：已公开暴露，改历史无法收回（爬虫/fork/缓存早已可能取走）
2. 签发新 key，**只经环境变量注入**
3. ⬜ **待做**：把 `_r2.py:12` 改成与 `stage2_generate_scenes.py:186` 一致的写法：
   ```python
   api_key = os.environ["API_KEY"]     # ✅ 正确做法，第一版脚本就是这么写的
   ```
4. ⬜ **待做**：清理 `docs/` 与 `wiki_pages/` 里的副本（**两处都要改，它们是互为副本的两个文件**）；sudo 命令统一改为 `sudo -S` 从 stdin 读或直接依赖 `sudoers` 免密
5. ⬜（可选）`git filter-repo` 重写历史 —— **这是善后，不是修复**；凭据已吊销后其紧迫性大幅下降

> ★ 值得注意的是**第一版 `stage2_generate_scenes.py` 写法是正确的**（读环境变量），`_r2.py` 是第二轮赶工时退化的。典型的"迭代中丢掉纪律"。

`[实践]` 另：`docs/Complete_Stage2.md:675` 附近记录了 `sudo: a terminal is required to read the password` 的报错原文——那一处是**报错信息**，不含真实口令；真实口令在上表列出的 18 行里。

### 7.4 代码缺陷（真的会咬人的）

`[CODE]` 四处，均已核实：

| # | 位置 | 问题 |
|---|---|---|
| 1 | `benchmark/policy/pipolicy.py` L54–57 与 L62–65 | ★ **`_encode_depth` 被定义两遍**，后者静默覆盖前者。Python 不报错，但"改了前一个却不生效"会浪费大量时间 |
| 2 | `benchmark/policy/pipolicy.py` | 正式路径上留着 `logger.info(f"DEBUG image shapes: head=…")` |
| 3 | `source/scene_reconstruction/Dockerfile:140` | ★★ **`pip install e .` 少了横线**，应为 `pip install -e .`。实际会去 PyPI 找名为 `e` 的包 → hloc 装不上或装成非 editable。⚠️ **已核实这是上游的 bug**（v3.2.0 同文件 `:140` 一字不差），不是本次复现引入的——但仍然会咬人，自建镜像时请顺手修掉 |
| 4 | `scene_recon_scripts/validate_gates.py` | ★★ **门禁会漏报通过**。全脚本**没有任何 `sys.exit`**：G1（`:15`）与 G3（`:49`）靠裸 `assert` 抛异常才拿到非零退出码，而 **G2 失败只是把 `status` 置成 `"FAIL"` 并打印（`:32-33`），随后继续执行到 `:72` 无条件 `print("\nALL GATES PASSED")`**。→ **G2 挂掉时脚本既打印 `FAIL` 又打印 `ALL GATES PASSED`，退出码仍是 0。** 拿它做 CI 判据会静默放行。修法：G2 也改成 `assert`，或末尾按累积状态 `sys.exit(1)` |

`[CODE]` 另有两处"静默失败"设计，不算 bug 但极易误判：

| 位置 | 行为 |
|---|---|
| `api_core.py:1823` `record_rosbag()` | `stdout`/`stderr`/`stdin` 三个流全 `DEVNULL` → **录制失败无任何提示**，只能看文件有没有生成。⚠️ 已核实这是**上游行为**（与 v3.2.0 `:2707` 逐字节相同），**不是本次复现引入的，且 v3.2.0 也没修** |
| `eval_tasks/*.json` 的 `camera_list` | prim 路径写错**不报错**，静默丢那一路图像 |

### 7.5 平台假设

`[CODE]` 逐条列出，换机器前先对照：

| 假设 | 出处 | 不满足会怎样 |
|---|---|---|
| ★★ **GPU 架构 = SM 8.0**（A100/A30）—— ⚠️ **这是本仓库的本地改动，不是上游的坑**：上游 `Dockerfile:8` 原值 `8.9`（4090/L40），本次复现改成 `8.0`（§6.2(c)） | 重建 `Dockerfile:8` `TORCH_CUDA_ARCH_LIST` | **换机器时两个方向都要查**：重新 clone 上游得到 `8.9`（4090 直接用，A100 要改成 `8.0`）；沿用本仓库得到 `8.0`（A100 直接用，4090 要改回 `8.9`）。**改错则 CUDA 扩展装不上或 kernel image 报错，必须重编** |
| ★★ 宿主机能提供 Vulkan/GL 库并手工提取到 `/tmp/nvidia-libs` | `start_headless.sh:35` | headless 渲染全盘失败；且 **`/tmp` 是 tmpfs，重启即失，补完还必须重建容器** |
| ★ 容器内 UID/GID = `1234:1234`，宿主机 `~/docker/isaac-sim` 已 chown | `start_headless.sh:12-15,19` | 缓存写入失败，以各种间接症状表现 |
| ★ `--network=host` | `start_headless.sh:23` | 容器内 `localhost:9001` 打不到 π0 容器 |
| `--privileged` + `/dev/input` 挂载 | `start_headless.sh:24,34` | 遥操作设备不可用 |
| Linux + bash + `sudo` 可用（NOPASSWD） | 全部脚本 | ⚠️ **Windows/macOS 完全不适用** |
| Ubuntu 24.04 (noble) + ROS 2 Jazzy | `dockerfile:61-65` | 换发行版需换 apt source deb |
| `entrypoint.sh` 存在且可执行 | `start_headless.sh:20` | ⚠️ **该文件不在本覆盖层**，缺它容器起不来 |

### 7.6 仓库不自包含 —— 复现前必须先补齐

`[CODE]` 汇总所有"引用了但仓库里没有"的东西（详见 §1.4、§5.1）：

| 缺失 | 被谁引用 | 从哪补 |
|---|---|---|
| `requirements.txt`（3 个） | `dockerfile:68,76,87` | 上游 genie_sim 仓库 |
| `scripts/entrypoint.sh` | `start_headless.sh:20` | 上游 |
| `patch/{colmap-pcd,pgsr,hloc}.patch` | 重建 `Dockerfile:80,104,135` | ★ **未发现**，来源不明 |
| `third_party/gsplat` | 重建 `Dockerfile:127` | 需自行 clone |
| `source/geniesim/generator/`（生成器主体） | `stage2_*.py` 调 `generator/app.py` | 上游 |
| `assets/`（含自制 real2sim USD） | 所有场景 | ★ 被 `.gitignore` 忽略，**只在原机器上存在** |
| `openpi/`（π0 服务） | 闭环推理 | `AgibotTech/ACoT-VLA` 分支 `genie_sim` |
| `.mcap` / `output/` / `logs/` | 评测产物 | 运行时生成 |

> ★★ **一句话**：本仓库是**覆盖层 + 记录**，不是可独立 clone 跑通的项目。正确用法 = 先 clone 上游 genie_sim（注意版本，§6.4）→ 备好资产包 → 把本仓库的文件叠上去。

---

## 八、与 background / ai_knowledge / troubleshooting 的关联

本章是**四层知识的缝合点**。左列是本文档的代码事实，右列是它印证/落地/推翻了哪条既有知识。

### 8.1 代码实现了 background 的哪些原理与特性

| 本文档 | 代码事实 | `background_knowledge.md` 章节 | 关系 |
|---|---|---|---|
| §3.1 | `APICore` 双队列 + `run_on_render_loop` / `run_on_physics_loop` | §3.1 整体架构、§3.3 模块逐一说明 | **落地**：原理层说的"分层架构"在代码里的具体形态是跨线程任务队列 |
| §3.1 | `record_rosbag()` 拼 `ros2 bag record`，`on_ros_tick` 发仿真时钟 | §3.4 RT Engine 的 10 个 ROS 2 包、§7.5 ROS 2 话题接口 | **落地** |
| §3.2 | `SimulationApp({"headless", "renderer", "enable_cameras", ...})` | §2.3 渲染技术、§5.1 系统要求 | **落地**：`render_mode="RaytracedLighting"` 就是原理层讲的 RTX 管线开关 |
| §3.3 | `PiPolicy` 组 `state(32) + eef + 3×RGB + depth + prompt`，Action Chunking `deque` | §2.4 传感器仿真、§7.3 Benchmark 侧编程接口 | ★ **落地 + 补细节**：原理层讲传感器"能出什么"，代码给出**实际打包格式与 CHW 转置**、depth 的 1000/10000 缩放 |
| §3.5 | 三层 prim 树（RigidBody / Visuals / CollisionProxy `purpose="guide"`）、`UsdPreviewSurface ← UsdUVTexture ← UsdPrimvarReader_float2` | §2.1 仿真方法、§2.3 渲染技术、§8.4 渲染异常速查 | ★ **落地**：原理层讲 USD 与材质，代码给出**能跑通的最小接线图** |
| §3.6 / §4.5 | `TASK_STEPS` + `task_config_mapping` + `robot_init_states` 三张查表 | §3.5 评测榜单结构、§7.2 配置文件结构 | **落地** |
| §4.1 | `ParameterServer` 三层覆盖 + 自动生成 `--<dotted.key>` | ★ §7.2 配置文件结构 | ★ **落地**：原理层描述 YAML 结构，代码解释**为什么任何字段都能从命令行改** |
| §5.2 / §5.3 | Isaac Sim 5.1.0、ROS 2 Jazzy、CUDA 11.8、numpy<2.0、pycolmap 3.11.1 | §5.1 系统要求、§5.2 主要依赖 | **印证并细化**（给出精确 pin 与 commit 号） |
| §2.7 | G1–G4 门禁、`render_validation.py` 的 `roi_std`/`uniq` | §8.4 渲染异常速查 | ★ **把"速查表"变成可执行断言** |

**background 里有、但代码层未涉及**（本覆盖层不含相关文件）：§2.2 物理引擎细节、§2.5 论文关键思想、§4.2 与其他仿真器对比、§6.2 RT Engine 流程、§6.3 数据采集、§6.4 全景图生成 3D 世界、§7.1 CLI 子命令总表（**属 v3.2.0，本覆盖层是 3.0**）、§7.4 gRPC 接口。

### 8.2 代码印证了 ai_knowledge 的哪些教训

| 教训 | 代码里的物证 | 本文档 |
|---|---|---|
| ★★ **L2 · 给每个长任务预设"独立于日志的存活判据"** | `run_on_render_loop` 超时抛 `TimeoutError` 但**渲染循环继续 tick** → 日志照刷、进程不死；**唯一被实际调大的调用点 `api_core.py:429` `timeout=600` 就是这条教训的代码物证**（§6.2(b)）。`record_rosbag` 的 `stderr=DEVNULL` → 失败无声。**这两处代码就是"日志不可信"的机制性证明** | §3.1、§7.4 |
| ★★ **L5 · 依赖需求正面互斥时直接隔离环境** | 仿真镜像开 **4 个 Python 环境**（`numpy<2.0` 只在 record env）；重建镜像里 **pgsr env 要 `pycolmap==3.11.1`、base env 先 `pip3 uninstall pycolmap`** —— 隔离是写进 Dockerfile 的 | §2.2、§5.2、§5.3 |
| ★★ **L7 · 验证要用数值阈值，并且必须校验产物真实落地** | 四个诊断脚本全部输出**可断言的数字**（`roi_std`、`unique_chunks`、`std_avg`、唯一色数）并以 `ALL_TEXTURED_OK` / `ALL GATES PASSED` / `CAPTURE_OK` 为判据，`validate_gates.py` 失败 `assert` | §2.7 ⚠️ **但 `validate_gates.py` 自身把这条教训执行漏了**：G2 失败不中断、末行无条件打印 `ALL GATES PASSED`（见 §7.4）——这是"验证脚本本身需要被验证"的活例子 |
| ★ **L6 · 让 LLM 产出结构化 DSL，示例价值高于描述，且防御必须冗余** | `SYSTEM_PROMPT` + `REFERENCE_LLM_RESULT`/`EXEMPLAR` 完整范例；`filtered_assets()` 把资产白名单直接注入；`_r2.py` 追加编号的 **"CRITICAL API RULES"** | §3.4 |
| ★ **L1 · 装 CUDA 扩展前先查 compute capability** | 重建 `Dockerfile:8` `TORCH_CUDA_ARCH_LIST`：**上游 `8.9` → 本机 `8.0`**。这不是"踩到坑的现场"，而是**教训被正确执行的物证**——复现时先查清 A100 = SM 8.0 才动手改的（§6.2(c) 全文件 diff 只差这一行）。反过来说，**下一个人重新 clone 上游拿到的是 `8.9`，必须自己再判断一次** | §5.3、§6.2(c)、§7.5 |
| **L4 · 跨容器边界的文件操作要么全在容器内、要么全在宿主机** | `stage2_generate_scenes.py` 全程用容器内路径 `/geniesim/main/...` 与容器内解释器，不跨界；`materialize_scene()` 用"目录集合求差"而非猜路径 | §2.0、§3.4 |
| **L3 · 开工第一步是读源码核对计划** | 本文档 §6.1 的存在本身即此教训的产物：`git log` 只有 4 个提交、无上游历史，**不读源码就无法知道改了什么** | §6.1 |
| **L8 · 正确的加速是先降数据量** | `preprocess_mp4.py` 默认 `--fps 2` 抽帧；`fast-simplification` 把 10M 顶点降到 30–50K 面 | §2.6、`README.md` |

**ai_knowledge §4 的问题编号 ↔ 代码**：

| 问题 | 代码物证 | 本文档 |
|---|---|---|
| §4.3 P11–P13「看起来在跑」类假象 | ★ `run_on_render_loop` 120 s `TimeoutError` 不退出；`PiPolicy.act()` 的 `TIMEOUT_SEC=30` → `os.kill(os.getpid(), SIGINT)` **主动自杀**。两者症状相似但机制完全不同 | §3.1、§3.3 |
| §4.1 P01–P06 容器/网络/权限 | `start_headless.sh` 的 `chown -R 1234:1234` + `--user 1234:1234` + `--network=host` + `--privileged` | §2.3 |
| §4.2 P07–P10 GPU 与 CUDA | `TORCH_CUDA_ARCH_LIST="8.0"`、`/tmp/nvidia-libs` 挂载、`VK_ICD_FILENAMES` | §5.3、§7.5 |
| §4.4 P14–P15 LLM 场景生成 | `SYSTEM_PROMPT` 的几何约束与 API 规则、`filtered_assets()` | §3.4 |
| §4.5 P16–P18 USD 资产与渲染 | 三层 prim 树、`primvars:st` 必须 `vertex` 插值、`purpose="guide"`、`ALIGN` 常数 | §3.5、§7.2 |

### 8.3 代码为 troubleshooting 的哪些 Q 提供了机制解释

**这是本文档对排障层最大的增值：把 `[实践]` 级现象升级为 `[CODE]` 级机制。**

| Q | 现象 | 代码机制 | 本文档 |
|---|---|---|---|
| ★★ **Q15** 录制开关全开却无文件落盘且无报错 | **机制找到了**：`record_rosbag()` 用 `stdout=DEVNULL, stderr=DEVNULL` —— 子进程报错被完全丢弃 | §3.1、§7.4 |
| ★★ **Q16** 日志持续刷 `[Physics Callback]`（约 18 Hz）、CPU 99%，但策略服务器收不到第一次推理 | **机制找到了**：`run_on_render_loop` 超时抛 `TimeoutError`，而**渲染/物理循环独立继续 tick** → 回调照刷、CPU 照占。排障应 grep `did not complete within`。★ **具体触发点也定位了**：`collect_init_physics` 走默认 120 s，而开 ROS 后（+20–25% 负载）跑不完；**修法是 `api_core.py:429` 传 `timeout=600`**，且此改动在 v3.2.0 上仍需自己做 | §3.1、**§6.2(b)**、§6.4 |
| ★★ **Q22** 4 路相机 RGB 全黑（mean=0.00）但帧率分辨率正常 | 两条路径：① `enable_cameras=False` → buffer 空；② ★ **v3.2.0 已上游修复**：Kit 的 `omni_*` 路径 token 未锚定（容器缺 `/isaac-sim/kit/{cache,data,logs}`）→ shaderdb 挂 → 无 SimulationView → buffer 空 → `cv2.cvtColor !_src.empty()`。**注意 LMDB `(256>=256)` 是 pin token 的动因，不是本级联的直接成因，没看到它也可能全黑** | §3.2、§6.4 |
| ★ **Q10** 相机返回 `shape=(0,)` | 同上链条 + `/tmp/nvidia-libs` 未挂载 | §2.3、§3.2 |
| ★ **Q17** `docker ps` 显示 `Up` 但端口不监听 | **机制找到了**：π0 侧 `compose.yml` **没有 `command` 字段**，`up -d` 只让容器空转，必须 `docker exec -d … bash scripts/server.sh 0 9001 …` | §2.4 |
| ★ **Q17 的下游** 30 秒后进程自己退出 | `PiPolicy.act()` `TIMEOUT_SEC=30` → `os.kill(os.getpid(), signal.SIGINT)`。**不是崩溃，是设计的超时自杀** | §3.3 |
| ★ **Q08** 宿主机重启后修好的渲染问题全部复发 | `/tmp/nvidia-libs` 在 **tmpfs** 上，重启即失；且补完必须**重建容器**（旧挂载已失效） | §2.3、§7.5 |
| **Q06/Q07** `PermissionError` / 容器内解析不到 assets | `--user 1234:1234` 与宿主机 UID 不同；`chown -R 1234:1234` 是前置步骤；软链接跨容器边界失效（对应 L4） | §2.3、§7.5 |
| **Q12/Q13** kernel crash / 荒谬的显存数字 | `TORCH_CUDA_ARCH_LIST="8.0"` 编译期写死 → 架构不匹配 | §5.3、§7.5 |
| **Q04** pycolmap 版本连锁 | Dockerfile 里 `pycolmap==3.11.1`（pgsr env）与 `pip3 uninstall pycolmap`（base env）**是刻意的环境隔离** | §5.3 |
| **Q19/Q20/Q21** DSL 生成类（资产不存在 / `SyntaxError` / `shape=` 参数错） | `filtered_assets()` 白名单 + markdown 围栏剥离 + `_r2.py` 的 "CRITICAL API RULES"，**三条防御一一对应三个 Q** | §3.4 |
| **Q25/Q26** 只渲染纯色 / 有 Material 但仍纯色 / `textures/` 为空 | 材质图三段接线缺一即纯色；`primvars:st` 必须 `vertex`（xatlas 会重排顶点）；`g4_texture_chain_probe.py` 专为此写 | §2.7、§3.5 |
| **Q24** 前景渲染成灰色金属件 + 嵌套 rigid body 报错 | 三层 prim 树的分工：RigidBodyAPI **只加在 `/World/<obj>`**，代理体用 `purpose="guide"` 而非再套刚体 | §3.5 |
| **Q28** 开 ROS 后仿真变慢、初始化超时 | `enable_ros: true` 时 `on_ros_tick` 每步 spin rclpy 节点并发时钟 | §3.1、§4.3 |

### 8.4 代码推翻或修正了哪些既有结论

| 既有结论 | 代码/上游证据 | 结论 |
|---|---|---|
| ★★ `troubleshooting.md` Q22/Q10 的一系列 3.0 手工绕法 | 上游 v3.2.0 `app_launcher.py:190` `_create_app` 已内建 Kit 路径 token 重定向（`GENIESIM_KIT_RUNTIME_DIR` / `/workspace/.kit`），上游自带注释同时说明 **LMDB `(256>=256)` 的 overlay 风险**与 **`omni_*` 族未锚定 → shaderdb → SimulationView → 空 buffer** 这两件事 | **在 v3.2.0 上重新部署时，这些绕法不再需要**（§6.4） |
| ★ `ai_knowledge.md` §7.1 的版本落差 | 本覆盖层是 3.0 布局（`source/geniesim/app/app.py` + `--config <yaml>`），v3.2.0 是 `geniesim` CLI + `geniesim_benchmark` 包 + `GENIESIM_REPO_PATH`/`GENIESIM_ASSETS_PATH` | **本文档全部命令属 3.0，不可套用 v3.2.0**（§6.4） |
| `ai_knowledge.md` §7.2「上游改了 3 张查表 + 6 个配置文件」 | 逐一核实到具体文件与行号（`task_config_mapping.py:214`、`robot_init_states.py:343`、`eval_utils.py` `TASK_STEPS`） | **印证，并补齐精确位置**（§4.5） |
| `background_knowledge.md` §8.4 建议用 `primvars:displayColor` 补色 | 代码里 `displayColor` 确实存在，但**只作 fallback**；真正出图靠完整材质图。`trackA_author_tsdf_usd.py` 是**唯一**只用 displayColor 的变体，且因为 PGSR TSDF 自带逐顶点 RGB 才成立 | **与 `ai_knowledge.md` D10 的自我否定一致**：displayColor 不是通用解（§3.5） |

### 8.5 本文档独有、其它三层没有的信息

供后续回填时参考：

1. **§4.1 的"任何 dataclass 字段都能当 CLI 参数"** —— 调试成本最低的入口，三层都没写
2. **§4.3 的 `s2r_real2sim_dummy.yaml`「哑配置」模式** —— 把"场景对不对"与"策略行不行"拆开验证
3. **§7.4 的三个代码缺陷** —— 重复 `_encode_depth`、遗留 DEBUG 日志、`pip install e .` 缺横线
4. **§7.2 的量测→硬编码断链** —— `align_3dgs_origins.py` 算出的 scale 需**手抄**回 `ALIGN`，最明显的可改进点
5. **§7.6 的仓库不自包含清单** —— 尤其 `patch/*.patch` **未发现**，直接影响重建镜像能否构建
6. **§7.3 的明文密钥处置流程** —— 需吊销而非仅重写历史（凭据已于 2026-08-29 吊销，明文串清理仍待做）

---

## 参考

- 上游仓库：`AgibotTech/genie_sim`（`[CODE]` 级证据来源）
- π0 策略侧：`AgibotTech/ACoT-VLA`（分支 `genie_sim`）
- 本覆盖层仓库：`GimpelZhang/genie_sim_v3_tour`（4 个提交，见 §6.1）
- 同项目其它知识层：
  - [`background_knowledge.md`](background_knowledge.md) — 原理层（9 章，`[CODE]`/`[PAPER]`）
  - [`ai_knowledge.md`](ai_knowledge.md) — 经验层（8 章，全 `[实践]`）
  - [`troubleshooting.md`](troubleshooting.md) — 排障层（Q01–Q29）
  - [`00-index.md`](00-index.md) — 项目级章节地图与行号表

> **文档内所有敏感信息已替换**：LLM API key → `<HARDCODED SECRET REDACTED>`（§7.3），宿主机路径 → `<repo_root>` / `<path>`，主机地址 → `<INFER_IP>:<PORT>`。






