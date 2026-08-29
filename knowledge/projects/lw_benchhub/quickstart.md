# lw_benchhub 快速上手指南（quickstart）

> **本文是速查卡，不是教程。** 只放"照着敲就能跑"的最短路径与最常撞的坑。
> 每条都给出深读入口——**要理解原理 / 看完整证据，去对应文档**，本文不重复解释：
>
> | 想知道 | 去哪 |
> |---|---|
> | 代码在哪、哪些是本地改的、有哪些静默失效 | [`code_knowledge.md`](code_knowledge.md)（952 行，用 §号跳） |
> | 一条具体报错怎么修 | [`troubleshooting.md`](troubleshooting.md) 顶部「快速症状索引」（`Q01`–`Q38`） |
> | 为什么当初这么选、试过哪些无效 | [`ai_knowledge.md`](ai_knowledge.md) §4 问题表（`P01`–`P38`） |
> | API / 设计原理 / 能力边界 | [`background_knowledge.md`](background_knowledge.md)（1478 行） |
>
> **证据等级**：`[CODE]` 可在仓库核实 ｜ `[实践]` 本机踩坑记录，**不是官方结论**。
> **本文是派生层**：与被引用的那一层冲突时，**以那一层为准**（尤其代码细节以 `code_knowledge.md` 为准）。
> **已替换敏感信息**：全文不含账号 / 口令 / 密钥 / token / 本机绝对路径。仓库根写 `<repo_root>`，原复现机挂载点写 `<orig_root>`，家目录写 `<user_home>`。

---

## 0. 先记住四件事（否则后面全看不懂）

`[CODE]`

1. **这个仓库开箱跑不了。** 79 个文件、**326 处**硬编码了原复现机的挂载点 `<orig_root>`，且三个含密钥的 `*_env.sh` 只在仓库里留了 `.example` 模板。**先做 §1.2 和 §1.3，否则第一条命令就失败。**
2. **它是 vendored 单仓，不是覆盖层。** 5679 个 tracked 文件里 5552 个是 5 个上游仓库的整体拷贝。"仓库里有某文件" ≠ "这文件是本次改的"（真正改过的只有 10 个，见 `code_knowledge.md` §6.2）。
3. **唯一跑通的评测是"路径 B"，成功率 40%（4/10）。** 用 `LightwheelAI/smolvla-double-piper-pnp`。另一条路径（pi0.5 / GR1）是 **0%**，不要照它排查。
4. **"双臂"是假的**：单臂 URDF + 写死 `ARM_LATERAL_OFFSET = 0.15` m 侧移近似出来的；可达闸门**不查碰撞**、**不管姿态**（`rotation_threshold = π`）。用它的结论时要知道边界（`code_knowledge.md` §4.3）。

---

## 1. 环境准备

### 1.1 前置条件

`[实践]` 缺任何一项都会在很后面才炸，先一次性备齐：

| 项 | 要求 | 漏了会怎样 |
|---|---|---|
| Python | **3.11**（conda 环境，名字**必须含 `lerobot-arena`**） | 3.12 → Isaac Sim 拒绝启动（[`Q02`](troubleshooting.md#q02)）；名字不含 → `auto_stage3_benchmark.py` 主动拒跑 |
| NVIDIA 驱动 | **580.159.03**（内核模块与 GL 库版本必须一致） | Vulkan / PhysX / RTX 异常（[`Q04`](troubleshooting.md#q04)） |
| GPU | sm_80（A100/A800 级），**空闲显存 > 20000 MiB** | 脚本硬阈值直接拦 |
| `git-lfs` | 已安装且 `git lfs pull` 过 | 资产为空（[`Q02`](troubleshooting.md#q02)） |
| `libnvidia-egl-*` | 已安装 | headless 渲染起不来 |
| CUDA | **在 conda env 内**装 `cuda-toolkit=12.8`（无需 sudo） | 系统 nvcc 11.8 与 cu128 torch 不匹配（[`Q10`](troubleshooting.md#q10)） |

### 1.2 ★ 对齐硬编码路径（最容易忽略的一步）

`[CODE]` 三选一，**按代价排序**：

```bash
# ① 最省：直接把仓库放到脚本期望的位置
#    仓库根 = <orig_root>，conda env 建在 <orig_root>/conda/envs/
#    conda 初始化脚本期望在 <user_home>/miniconda3/etc/profile.d/conda.sh

# ② 全局替换（先看清规模再动手）
git -C <repo_root> grep -c '<orig_root>' | sort -t: -k2 -rn | head
#    实测 79 文件 / 326 处，最密的是 CLAUDE.md(45)、verify_stage4.sh(12)、run_phase3.sh(12)

# ③ 只改要跑的那一条链路（最快，但易漏）
#    ⚠️ 脚本之间靠"约定的产物路径"通信，改一半会出现"跑通了但读到旧产物"
```

> 详细清单与代价对比：`code_knowledge.md` §2.0 / §7.1。

### 1.3 ★ 建凭据文件（仓库里只有模板）

`[CODE]` 实体文件被 `.gitignore:7-9` 排除，**必须自己 `cp` 一份**：

```bash
cd <repo_root>
cp headless_env.sh.example      headless_env.sh      && chmod 600 headless_env.sh
cp llm_env.sh.example           llm_env.sh           && chmod 600 llm_env.sh
cp deepseek_v4pro_env.sh.example deepseek_v4pro_env.sh && chmod 600 deepseek_v4pro_env.sh
```

然后填入真实值。**需要填的变量名**（本文只列名，不列值）：

| 文件 | 必填 | 其余变量 |
|---|---|---|
| `headless_env.sh` | `HF_TOKEN`、`CUDA_HOME`、`HF_HOME` | `HEADLESS`、`ENABLE_CAMERAS`、`ACCEPT_EULA`、`OMNI_KIT_ACCEPT_EULA`、`OMNI_KIT_ALLOW_ROOT`、`PRIVACY_CONSENT`、`MUJOCO_GL`、`TORCH_COMPILE_DISABLE`、`TORCHINDUCTOR_DISABLE` |
| `llm_env.sh` | `OPENAI_API_KEY`、`OPENAI_BASE_URL` | `LLM_MODEL` |
| `deepseek_v4pro_env.sh` | `DEEPSEEK_API_KEY`、`DEEPSEEK_BASE_URL` | `DEEPSEEK_MODEL` |

> ⚠️ `CUDA_HOME` **不能带前导冒号**，否则 nvcc 路径查找失败（[`Q01`](troubleshooting.md#q01)）。
> ⚠️ 这个仓库的**远端是 public 的**，`.gitignore` 是唯一的凭据隔离机制 —— **不要 `git add -f` 这三个文件**。

### 1.4 四个硬锁版本

`[实践]` 装完任何东西都要回头确认，**特别是 `numpy`**：

```bash
pip install --no-deps numpy==1.26.0        # ★ 每次 pip 操作后都重新执行一遍
pip install --no-deps warp-lang==1.8.1
pip install qpsolvers==4.8.1
pip install 'vuer[all]==0.0.70'
python -c "import numpy; assert numpy.__version__=='1.26.0', numpy.__version__"
```

`numpy` 被顶到 2.x 的症状是**随机 `ImportError` 或 segfault**，且发生在 Isaac Sim 的 C 扩展里，看不出跟 numpy 有关（[`Q03`](troubleshooting.md#q03)）。

编译 cuRobo 前另需（否则编译数小时或 OOM，[`Q13`](troubleshooting.md#q13)）：

```bash
export TORCH_CUDA_ARCH_LIST="8.0"
export MAX_JOBS=4
export SETUPTOOLS_SCM_PRETEND_VERSION_FOR_NVIDIA_CUROBO=<版本号字符串>
```

### 1.5 ★★ 每次跑之前的"六行前奏"（背下来）

`[CODE]` 本仓库**所有**主线脚本都以这几行开头，缺一行就有对应的一种崩法：

```bash
set +u                                    # ① 不能用 set -u
source <user_home>/miniconda3/etc/profile.d/conda.sh
conda activate lerobot-arena
source <repo_root>/headless_env.sh
unset CUDA_VISIBLE_DEVICES                # ② 必须 unset，且不要写进 shell 配置
cd <repo_root>/lw_benchhub                # ③ eval 的 config_path 是相对路径
```

| 行 | 缺了会怎样 |
|---|---|
| `set +u` | 立刻 `unbound variable` 中止（conda 的 CUDA 激活脚本引用了未绑定变量）。[`Q14`](troubleshooting.md#q14) —— 原注释写着 *Hours were lost on this. Do NOT switch back.* |
| `unset CUDA_VISIBLE_DEVICES` | Isaac Sim 在**相机初始化时直接 segfault，无 traceback**。[`Q15`](troubleshooting.md#q15) |
| `cd lw_benchhub` | 找不到场景 YAML |

> ⚠️ 唯一例外：`pathB_logs/run_pathB.sh:2` 用的是 `set -u`。它能跑是因为没走到那些变量，**不要以它为范本**。

---

## 2. 运行示例

### 示例 A ★★ 先跑这个：验证环境的 40% 基准评测

`[CODE]` 这是**唯一跑通的评测路线**（路径 B）。先做完 §1.5 的六行前奏，然后：

```bash
lerobot-eval \
  --policy.path=LightwheelAI/smolvla-double-piper-pnp \
  --env.type=isaaclab_arena \
  --env.hub_path=LightwheelAI/lw_benchhub_env \
  --env.kwargs='{"config_path": "configs/envhub/example.yml"}' \
  --rename_map='{"observation.images.left_hand_camera_rgb":  "observation.images.left_hand",
                 "observation.images.right_hand_camera_rgb": "observation.images.right_hand",
                 "observation.images.first_person_camera_rgb":"observation.images.first_person"}' \
  --trust_remote_code=true \
  --env.state_keys=joint_pos --env.state_dim=16 --env.action_dim=12 \
  --env.camera_keys=left_hand_camera_rgb,right_hand_camera_rgb,first_person_camera_rgb \
  --env.enable_cameras=true --env.headless=true \
  --env.video=true --env.video_length=200 --env.video_interval=1 \
  --policy.device=cuda --eval.batch_size=1 --eval.n_episodes=10 \
  --output_dir=<path>/eval_outputs_pathB_1
```

**预期输出** `[实践]`：

```
约 10 分 39 秒跑完 10 集
日志中最后一次:  running_success_rate: 40.0        ← 是百分数，40.0 表示 40%（4/10）
输出目录:        <path>/eval_outputs_pathB_1/  含 10 个视频
```

**取指标的三个陷阱** —— 直接决定你读到的数字对不对（[`Q21`](troubleshooting.md#q21)）：

```bash
grep -o 'running_success_rate[^,]*' <log> | tail -1   # ① CLI 不写 eval_info.json，只能 grep 日志
# ② 值是百分数，要存成分数请 /100
# ③ 进程可能在 RuntimeError 后仍 exit 0 —— 不要信 $?，从日志的 EXIT_CODE: 行反推
```

> ⚠️ **视频只有 4 秒不是渲染坏了**：`video_length=200` 在 50 Hz 下就是 4 s。要看整集改成 `1100`（§3.2）。
> ⚠️ **换任务 / 换场景成功率会一律变 0%**，这是 checkpoint 单任务微调的 OOD，不是接口 bug（[`Q22`](troubleshooting.md#q22)）。别去查接口。

### 示例 B LLM 生成场景 + 在线可达性闸门（Stage 2）

`[CODE]` 需要 `llm_env.sh` 里的凭据。**两个脚本靠子进程 + JSON 文件串联，不 import 彼此**：

```bash
source <repo_root>/llm_env.sh
python <repo_root>/generate_scenes_with_live_reach.py     # 生成器（内部会调下面那个）

# 也可单独只跑闸门校验某个场景：
python <repo_root>/validate_scene_objects_reach.py --config_path configs/envhub/<scene>.yml
```

**预期输出** `[实践]`：

```
最多 6 轮（MAX_ROUNDS=6）问答；不合法的 (layout, task) 组合进 banned 列表后重问
全通过 → 写出 final_manifest.json
被闸门拒掉的场景会留下形如  scene_variation_3.yml.rejected_by_reach_gate  的文件
```

闸门退出码：**`0`** 通过（⚠️ **含"场景里没有 rigid object → 默认通过"**）、**`1`** 未过闸门、**`≥2`** bug / 环境错误。

> ⚠️ 闸门只保证"位置能到"：**不查碰撞**（碰撞体全空）、**不管姿态**（`rotation_threshold = π`）。别把"过闸门"当成"能抓起来"（`code_knowledge.md` §4.3）。
> ⚠️ 某些 layout/task 组合会让 Isaac Sim 在 boot 期**无限挂起**（实测烧掉 58 分钟无进展）。**长跑一定要设外部 wall-clock 超时并预留 `pkill -9`**（[`Q24`](troubleshooting.md#q24)）。

批量 + 自检：

```bash
N_EPISODES=3 bash <repo_root>/stage2_logs/run_stage2_all.sh
python <repo_root>/verify_stage2.py        # 无参数，产出 stage2_final_deliverables/stage2_summary.md
```

> ⚠️ 自检报告里 `robot_init_pos` / `robot_init_ori` / `task_file` 三列**恒为 `?`** —— 是键名对不上的已知缺陷，不是数据丢了（`code_knowledge.md` §2.5）。

### 示例 C 用 SmolVLA 自过滤采数（Stage 4 Phase 1）

`[CODE]` **这是唯一跑通的采数路线**：让已微调的策略自己跑，只留成功集。

```bash
bash <repo_root>/stage4_flywheel/scripts/run_policy_demo_collection.sh
```

**预期输出** `[实践]`：

```
29 个 episode → 10 个成功（34.5%），共 6527 帧
产出: stage4_flywheel/datasets/policy_demos_v3_lerobot/   （LeRobot v3 格式）
```

打包成数据集（**约 40 分钟**，1.8 万张 PNG 单核约 2 fps，是已知瓶颈、不是卡死，[`Q36`](troubleshooting.md#q36)）：

```bash
python <repo_root>/stage4_flywheel/scripts/build_policy_demos_dataset.py
```

> ⚠️ **Phase 1 故意不 source `lerobot_arena_curobo_env.sh`** —— 这条路线不用 cuRobo，source 它反而引入 CUDA 头文件软链等副作用。这是全仓库唯一绕开统一 env 脚本的主线路径。
> ⚠️ **日志末尾可能缺尾**：收尾用 `os._exit(0)` 硬退（绕过 Isaac Sim 的 atexit 卡死），会跳过 buffer flush。**"日志没写完"≠"挂了"**。
> ❌ **不要跑 `run_one_episode.sh` / `run_all_episodes.sh`**（脚本化 cuRobo PnP）：**已证伪，8/8 全失败**，根因是规划器 `ee_link` 与仿真 TCP 差 0.30 m，不可修（[`Q34`](troubleshooting.md#q34)）。

---

## 3. 修改关键参数

### 3.1 先搞清配置在哪一条轨道上

`[CODE]` 本仓库**没有统一配置框架**，四条轨道互不相通：

| 想改什么 | 改哪 |
|---|---|
| 密钥 / headless / HF 缓存 | `*_env.sh`（§1.3） |
| 场景（layout / task / seed / 时长） | `lw_benchhub/configs/envhub/generated*/`、`stage4_flywheel/{configs,curriculum}/` |
| 机器人运动学 / IK 阈值 | `piper_curobo.yml`、`stage4_flywheel/curobo/piper_curobo_{left,right}.yml` |
| 评测规模 / 相机 / 视频 | 命令行参数（示例 A） |

### 3.2 最常改的几个

| 想要 | 改哪 | 注意 |
|---|---|---|
| 视频录满整集（默认只 4 s） | `--env.video_length=1100` | Stage 2 已改，Stage 1 / Stage 3 仍是 200 |
| 跑更多集 | `--eval.n_episodes=N` | 单集约 64 s，10 集约 10 分半 |
| 换场景 | `--env.kwargs='{"config_path": "configs/envhub/<新场景>.yml"}'` | **相对路径**，必须先 `cd lw_benchhub` |
| 放宽 / 收紧姿态约束 | `AutoDataGen/source/autosim/autosim/capabilities/motion_planning/curobo/curobo_planner_cfg.py:37` | 本地已设 π（= 只管位置）。⚠️ **收紧到 0.1/0.5 会让全部规划失败**（工作空间边缘），已实测 |
| 指定物体初始位姿 | 场景 YAML 的 `fix_object_pose_cfg:` 段 | 这是**代码里真有消费者**的机制（贯通链见 `code_knowledge.md` §6.3） |
| 换本体（改关节数） | **三处同步**：打包脚本的 `assert`、`--policy.*_dim`、SmolVLA 配置 | 少改一处，打包时才炸 |

### 3.3 ❌ 三种改不动的（别浪费时间）

`[实践]`

1. **加自定义难度字段**（如 `scene_generation_difficulty: hard_offset_0.35`）—— **代码库里没有任何解析处**，会静默无效，而"诊断结论"是一句硬编码 print，还会骗你说生效了（[`Q26`](troubleshooting.md#q26)）。要调难度请用 **seed sweep** + **`fix_object_pose_cfg`**。
2. **用环境变量关 `torch.compile`** —— 只设 `TORCH_COMPILE_DISABLE=1` / `TORCHINDUCTOR_DISABLE=1` **无效**，代码里是显式函数调用，必须改配置源头（[`Q19`](troubleshooting.md#q19)、教训 `L04`）。
3. **给单相机 VLA 加左右手相机** —— 四层证据链否定，架构被训练为忽略第 2/3 路。要 3 相机必须重采数 + 重训（[`Q20`](troubleshooting.md#q20)）。

### 3.4 ⚠️⚠️ 改参数前必读：命令行拗不过 YAML

`[CODE]`

8 个入口脚本都有这一行 —— `args_cli.__dict__.update(yaml_args.__dict__)`（`scripts/teleop/teleop_main.py:141` 等）。它在 `parse_args()` 之后、把参数交给 `AppLauncher` 之前执行，**所以 YAML 里的同名键会静默丢弃你在命令行显式传的值，没有任何警告**。

最常中招的一次：`configs/data_collection/teleop/teleop_base.yml:6` 写着 `device: cpu`，于是

```bash
./teleop.sh --task_config double_piper --device cuda:0   # ❌ --device 被丢弃，实际跑在 CPU 上
```

症状是**"莫名奇妙地慢"而不是报错**。同类键：`num_envs`、`enable_cameras`、`headless`。

**规则：要改这些值就去改 YAML（或新建一个 `_base_` 继承它的 YAML），不要加命令行参数。** 完整推导见 [`background_knowledge.md`](background_knowledge.md) §6.1 推论 4 与 §8.3 第 16 条。

---

## 4. 常见代码问题

> 带**具体报错**时请直接查 [`troubleshooting.md`](troubleshooting.md) 顶部的「快速症状索引」，比本节快。本节只列**代码层面**最容易反复踩的。

### ① ★★ 结论是错的但什么都不报错（**最贵的一类**）

`[CODE]` 已定位 **11 条**静默失效路径。读到任何结论前，先确认产生它的代码不在这张表里：

| 现象 | 位置 |
|---|---|
| 自检报告三列恒为 `?` | `verify_stage2.py:121-122,154` 读的键 validator 从不写 |
| 训练集混入黑帧 | `generate_policy_demos.py:100-103` 相机缺帧**零填充**，不报错不计数 |
| 断点续跑永远从头开始 | `run_all_episodes.sh:37` 引用未定义变量 `$EPID_summary` |
| eval 失败却返回 0 | `run_pathB.sh:40` 缺 `exit $EXIT` |
| 真实 100% 被读成 1% | `auto_stage3_benchmark.py:394` 的 `raw_sr > 1.0` 启发式 |
| `--skip-on-failure` 关不掉 | 同上 `:709-716`，声明成 `store_true, default=True`，永真 |
| 镜像"构建成功"但缺包 | `Dockerfile.eval` 有 **3 处 `pip install ... \|\| true`** |
| 位姿配置没生效但不报错 | `fix_object_pose_cfg` 贯通链每环都有兜底 |

> 完整 11 条见 `code_knowledge.md` §7.2。**教训 `L06`：静默失效比报错危险，要主动给它加验证。**

### ② ★★ 补丁"有时生效有时不生效"

`[CODE]` **仓库里 vendored 了两份 IsaacLab**（实测 973 处差异，不是副本）：

| 位置 | 文件数 | 说明 |
|---|---|---|
| `AutoDataGen/dependencies/IsaacLab/` | 1857 | **这份才是 `pip install -e` 装的** |
| `IsaacLab/`（仓库根） | 1362 | Isaac Sim **4.5** 时代遗留，死重量 |

`import isaaclab` 解析到哪一份取决于 `sys.path` 顺序与 cwd。**判据**：根 `IsaacLab/.../curobo_planner_cfg.py:167` 的 `rotation_threshold` 是上游默认 `0.05`（没有本地的 π 改动）—— 若你观察到姿态约束仍在生效，说明 import 到了错的那份。**确认无引用后建议删掉根 `IsaacLab/`。**

### ③ ★ 报 `success=True` 但任务其实没完成

`[实践]` 全仓库有 **6 种不同的成功判定写法**，跨阶段比较成功率会比出假差异。**只信环境返回的信号**：`generate_policy_demos.py:138` 的 `task_success = last_terminated`（在 step 返回**瞬间**捕获，因为向量环境会在 `terminated` 后自动 reset，事后再查读到的是下一集的初始状态）。见 [`Q29`](troubleshooting.md#q29)、[`Q35`](troubleshooting.md#q35)、教训 `L05`。

### ④ `ImportError: cannot import name 'CONFIGS_PATH' from 'lw_benchhub'`

`[CODE]` 从仓库目录**之外**启动 Python 时，**外层** `lw_benchhub/__init__.py` 会遮蔽内层真包。本仓库已把它重写为 `importlib.util` 影子加载。若你在别的 clone 上遇到，改**外层**那个文件（内层的 2 行文件与上游相同，不用动）。[`Q05`](troubleshooting.md#q05)

### ⑤ `pinocchio is required` / `has no attribute '_model'`

`[CODE]` conda 装的 `pin`（cmeel 4.0.0）**不带 `pinocchio.casadi`**。本仓库已把 `piper_ik.py` 改成 lazy stub（import 期不失败，调用期才失败）。**主线评测根本不用它**，只是 import 链会经过。⚠️ 因此**任何"改用 pinocchio IK"的方案都会 raise** —— 它是 stub。[`Q07`](troubleshooting.md#q07)

### ⑥ 长跑挂死 / 一行错误看不到栈

`[实践]` 三条硬规则（教训 `L07`）：

```bash
timeout -k 10 900 <cmd>              # ① 一定给外部 wall-clock 超时
pkill -9 -f "[i]saacsim"             # ② 方括号技巧：否则 pkill -f 会匹配到自己、杀掉父 shell
# ③ 长跑 pipeline 的 except 里必须 traceback.print_exc()，只存 repr(e) 会白烧两次运行
```

⚠️ 挂死检测（`HANG_THRESHOLD=4`）是靠 `grep -c "scene retry"` 数上游日志行，**上游改文案就失效**。另：代码里的 `max_scene_retry` 上限**永远不会触发**（计数器被模型重载重置），别指望它（[`Q28`](troubleshooting.md#q28)）。

### ⑦ 改了模块级 `AppLauncher` 的位置就崩

`[CODE]` `run_dataset_gen.py:18-33` 的 `AppLauncher` **必须留在模块级、在其余 import 之前**。这是 Isaac Sim 的硬要求，不是代码风格问题。

### ⑧ 改了一处不够（重复实现清单）

`[CODE]` 下列语义在仓库里**各有多份、无任何同步机制**：可达性 IK 判断（`reach_gate.py` 与 `validate_scene_objects_reach.py` 三个同名同义函数）、成功判定（6 种）、`state_dim=16`/`action_dim=12`（3 处）、场景 YAML（`generated_stage4/` 与 `stage4_flywheel/` 各一份）、cuRobo 机器人配置（3 份）、IsaacLab（2 份）。详见 `code_knowledge.md` §7.4。

### ⑨ 分不清哪代脚本还有效

`[实践]` `stage4_flywheel/scripts/` 的 48 个脚本有**两代并存**：

- ✅ **有效**：文件名带 `policy_demo` 的（`run_policy_demo_collection.sh`、`generate_policy_demos.py`、`build_policy_demos_dataset.py`）
- ❌ **已废弃 / 探索残留**：带 `patch_`、`_probe`、`descend` 的，以及 4 个 `_` 开头的私有试验脚本

其中三个 `patch_*.py` **在自己的 docstring 里就预言了自己无效** —— 教训 `L01` 最直接的物证。

---

## 5. 一分钟自检清单

动手前逐条打勾，能省掉后面 80% 的排障：

```
环境
[ ] conda env 名字含 lerobot-arena，Python 3.11
[ ] python -c "import numpy; assert numpy.__version__=='1.26.0'"   ← 每次 pip 后都查
[ ] 驱动 580.159.03，内核模块与 GL 库版本一致
[ ] nvidia-smi 空闲显存 > 20000 MiB
[ ] CUDA_HOME 无前导冒号

仓库
[ ] 已处理 <orig_root> 硬编码（§1.2），或仓库就放在该路径下
[ ] headless_env.sh / llm_env.sh / deepseek_v4pro_env.sh 已 cp + chmod 600 + 填值
[ ] 这三个文件没被 git add（远端是 public 仓库）
[ ] 确认走的是 AutoDataGen/dependencies/IsaacLab 那份（不是仓库根的 IsaacLab/）

每次运行前
[ ] set +u（不是 set -u）
[ ] unset CUDA_VISIBLE_DEVICES
[ ] cd <repo_root>/lw_benchhub
[ ] 长跑已套 timeout -k 10 900 并准备好 pkill -9 -f "[i]saacsim"

读结果时
[ ] running_success_rate 是百分数，不是分数
[ ] 不信 $?，从日志 EXIT_CODE: 行反推
[ ] 结论所依赖的代码不在静默失效清单里（§4①）
```

---

## 6. 相关文档

| 文档 | 用途 |
|---|---|
| [`code_knowledge.md`](code_knowledge.md) | 代码层（952 行，8 章）。**本文的所有代码细节以它为准。**§2 入口点 · §3 核心模块 · §4 配置 · §6 修改点 · §7 陷阱 |
| [`troubleshooting.md`](troubleshooting.md) | 排障层（`Q01`–`Q38`）。**带报错时的最快路径**，顶部有「快速症状索引」 |
| [`ai_knowledge.md`](ai_knowledge.md) | 经验层（`P01`–`P38` / `D01`–`D17` / `L01`–`L08`）。想知道**试过哪些无效方法**看 §4 的"无效尝试"列 |
| [`background_knowledge.md`](background_knowledge.md) | 原理层（9 章，1478 行）。API / 设计原理 / 能力边界 |
| [`00-index.md`](00-index.md) | 项目级章节地图与行号表 |

> **本文是派生层**，不引入新事实。与被引用层冲突时以那一层为准。
> **已替换敏感信息**：全文不含账号 / 口令 / 密钥 / token / 本机绝对路径；凡涉及 API key 的只写变量名与所在文件，不写值。
