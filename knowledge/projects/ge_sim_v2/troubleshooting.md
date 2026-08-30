# GE-Sim 2.0（`ge_sim_v2`）常见问题与解决方案

> **本文档来源**：由本项目经验层 [`ai_knowledge.md`](ai_knowledge.md) §4「遇到的问题与解决方案」按**故障类别**重排而成，**不是新的事实来源**。
>
> **证据等级：全篇 `[实践]`** —— 来自 2026 年 7–8 月一次五阶段本机复现的踩坑记录，**不是官方结论**。上游行为可能已变，动手前请对照 [`background_knowledge.md`](background_knowledge.md) 与上游源码。
>
> **编号约定**：`Qxx` 与经验层 `Pxx` **一一对应**（`Q13` ↔ `P13`），只追加、不重排、不复用。想知道"为什么会这样"、"还试过哪些无效方法"，按每条末尾的「相关经验」回查经验层。
>
> **隐私**：全篇已脱敏，本机绝对路径写作 `<repo_root>` / `<user_home>` / `<path>`，主机地址写作 `<INFER_IP>:<PORT>`。原始材料中的凭据**从未被引用**。

---

## 快速症状索引

**带着报错来的话，从这张表进。**

| 你看到的现象 | 去 |
|---|---|
| pip / HF / pytorch.org 极慢或直接超时 | [`Q01`](#q01) |
| 权重"下完了"但体积不对 / 加载时报文件损坏 | [`Q02`](#q02) ⭐ |
| 杀了下载进程但流量还在 / 两个下载器互相覆写 | [`Q03`](#q03) |
| `LocalEntryNotFoundError`（`hf download`） | [`Q04`](#q04) |
| ModelScope 下载量远超预期（下了几百个文件） | [`Q05`](#q05) |
| 长调用被挂死 / 连 `127.0.0.1` 都 503 | [`Q06`](#q06) |
| `Connect call failed ('127.0.0.1', 10900)` / 隧道拨号失败 | [`Q07`](#q07) ⭐ |
| 服务启动即 500：`ImportError: liger-kernel is required` | [`Q08`](#q08) |
| `ModuleNotFoundError: No module named 'spas_sage_attn'` | [`Q09`](#q09) ⭐ |
| `git submodule` 报 "needs a separate revision" | [`Q10`](#q10) |
| lerobot API 不匹配 / numpy 被顶成 2.x / `No matching distribution found for regex` | [`Q11`](#q11) |
| conda 求解极慢 / 装完 CUDA 从 12.1 变成 13.x | [`Q12`](#q12) |
| `from pkg_resources import ...` 导入期崩溃 | [`Q13`](#q13) ⭐ |
| GroundingDINO 起不来 / 仓库 403 | [`Q14`](#q14) |
| `ModuleNotFoundError: h5py` / `matplotlib`（明明装过） | [`Q15`](#q15) |
| 显存突然只剩四分之一 | [`Q16`](#q16) |
| `env.step()` 解包报错 / 帧数组形状不对 / 视角取错 | [`Q17`](#q17) ⭐ |
| VLM 返回 HTTP 200 但 content 是空的 | [`Q18`](#q18) |
| 任务抛 `NotImplementedError` | [`Q19`](#q19) |
| 图像编辑 API 调用 socket hang | [`Q20`](#q20) |
| `conditioning="action"` 下仍报缺 `.npy` 文件 | [`Q21`](#q21) |
| 从 H5 读出来的数值量级完全不对 | [`Q22`](#q22) |
| `ModuleNotFoundError: No module named 'scripts'` / import 成功但拿到空壳 | [`Q23`](#q23) |
| 想做 LoRA 微调但接不上 | [`Q24`](#q24) |
| 想算策略梯度但没有概率密度 | [`Q25`](#q25) |
| 梯度传不回策略 | [`Q26`](#q26) |
| 执行 `pkill` 后当前 shell 自己死了（exit 144） | [`Q27`](#q27) |
| 服务"杀掉了"但显存仍占十几 GB | [`Q28`](#q28) ⭐ |
| 启动编排脚本整体 hang 到超时 | [`Q29`](#q29) |
| 后台任务日志文件长时间是空的 | [`Q30`](#q30) |
| 渲染跑到第几个片段就被 OOM-kill | [`Q31`](#q31) |
| 进程消失、日志停在某一行、**没有任何 Traceback** | [`Q32`](#q32) ⭐ |
| 盘写满 / 输出落在错误的盘 | [`Q33`](#q33) |
| 平台侧进度冻结，重连成功但网关不发数据 | [`Q34`](#q34) |
| 成功率 0 %，但怀疑不是模型的问题 | [`Q35`](#q35) ⭐ |
| 手臂抖动 / 夹爪不动 / 左右臂互换，但**不报错** | [`Q36`](#q36) ⭐ |
| 对端解析崩 / 会话静默失败（msgpack） | [`Q37`](#q37) |
| 一连上就异常断线 / 轮询把在跑的 job 判成终态 | [`Q38`](#q38) |
| 报告小节全空 / 首帧日志把图像形状打成 `[]` | [`Q39`](#q39) |
| 跨机型评测得 0 分 | [`Q40`](#q40) |
| Stage 1 三个 demo 动作雷同 | [`Q41`](#q41) ⚠️ **未解决** |
| 榜单 `total` 与文档写的算法对不上（说是求和、数字像均值） | [`Q42`](#q42) |
| 计划里的任务数 / 拆分 / 成功率与平台实际不符 | [`Q43`](#q43) ⭐ |
| `GET .../job/<uuid>/result` 返回 500 `invalid job_id` | [`Q44`](#q44) |
| 计划中的"Z 轴 / 桌高泛化曲线"画不出来（自变量方差为 0） | [`Q45`](#q45) |

⭐ = 最容易重复踩的；⚠️ = 未解决。

**分类速览**：[A 网络与下载](#a-类网络下载与代理q01q07) · [B 安装与依赖](#b-类安装依赖与环境q08q16) · [C 源码契约与接口误用](#c-类源码契约与接口误用q17q26) · [D 进程与资源](#d-类进程资源与稳定性q27q34) · [E 正确性与假阴性](#e-类正确性与假阴性q35q41) · [F 平台契约与判分口径](#f-类平台契约与判分口径q42q45)

---

## A 类·网络、下载与代理（`Q01`–`Q07`）

<a id="q01"></a>
### `Q01` pip / pytorch.org / HuggingFace 全部阻断或极慢

**Q**：安装依赖、下载权重时速度只有几十 KB/s，或直接超时。

**A**：
1. pip 换清华 TUNA 镜像。
2. HuggingFace 走 `hf-mirror` 镜像端点。
3. 实测提速 **38 KB/s → 9.9 MB/s（约 250×）**。

**❌ 无效尝试**：直连反复重试 —— 这不是网络抖动，是稳定阻断，重试到天亮也一样。

**相关经验**：[`ai_knowledge.md` §4.1 · `P01`](ai_knowledge.md)

---

<a id="q02"></a>
### `Q02` ⭐ 权重下载"成功"但文件是截断损坏的

**Q**：下载结束、没有任何报错，但文件体积不对（实测 1703 MB → 1042 MB、1405 MB → 1220 MB），加载时才报损坏。

**A**：根因是 `curl -C -` 对**会 302 跳转的镜像**做续传时，CDN **间歇性返回 200 而不是 206**；curl 收到 200 就从字节 0 开始重写，于是文件被截断。自研分块下载器，四条都要有：

```
① 8 MB 定长 Range 分块请求
② 只在 HTTP 206 时写盘 —— 收到 200 直接 raise，绝不写
③ 续传偏移取 dest.stat().st_size，不依赖 curl 的状态
④ 遇 403 重新解析直链（预签名过期）
```

启动方式用 `nohup … &` **独占**运行，不接管道。

**❌ 无效尝试**：反复 `curl -C -` 重试 —— **每次都"成功"、每次都坏**，这正是它危险的地方。

> 💡 通用教训：**为"成功"设一个可断言的判据，而不是以"没报错"为成功**（[`L05`](ai_knowledge.md)）。

**相关经验**：[`ai_knowledge.md` §4.1 · `P02`](ai_knowledge.md)、决策 `D03`、教训 `L05`

---

<a id="q03"></a>
### `Q03` 杀掉下载进程后仍在下载，且两个下载器互相覆写同一文件

**Q**：`kill` 之后流量不减；文件体积忽大忽小。

**A**：
1. `kill <bash-pid>` 杀掉的是 shell，**fork 出来的 python 子进程还活着**。用 `ps` 找到真实 PID 再杀。
2. 确认同一时刻**只有一个**下载器在写目标文件。
3. 下载器用 `nohup … &` 独占启动，不接管道。

**❌ 无效尝试**：杀父 shell；把输出接给 `tail`（会让进程随管道存活状态不定）。

**相关经验**：[`ai_knowledge.md` §4.1 · `P03`](ai_knowledge.md)

---

<a id="q04"></a>
### `Q04` `hf download` 对某些文件报 `LocalEntryNotFoundError`

**Q**：同一个仓库里大部分文件能下，个别文件必失败。

**A**：这些文件走 **xet 后端**，国内不可达。改用 `aria2c` 直接请求镜像的 `/resolve/main/<file>` 路径，带上 Authorization 头。

**❌ 无效尝试**：重试 `hf download`；只改 endpoint 环境变量 —— 后端选择不受它控制。

**相关经验**：[`ai_knowledge.md` §4.1 · `P04`](ai_knowledge.md)

---

<a id="q05"></a>
### `Q05` ModelScope 下载量远超预期

**Q**：本以为下十几个文件，结果下了几百个、几十 GB。

**A**：
1. `--include "checkpoints/*"` 是通配，会匹配整棵树（实测 **936 个文件**，含其它 baseline）。**精确到 board 子目录**：`checkpoints/<name>/**`。
2. **匿名即可下载，不需要登录。**
3. 下载前先用 API 查一次文件数与总体积，对不上就说明 include 写宽了。

**相关经验**：[`ai_knowledge.md` §4.1 · `P05`](ai_knowledge.md)

---

<a id="q06"></a>
### `Q06` 长连接被本地代理挂死，甚至连 `127.0.0.1` 都返回 503

**Q**：本机服务之间互调也失败。

**A**（适用于**离线批处理**场景）：
```
no_proxy="*"
unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY all_proxy
HF_HUB_OFFLINE=1
```

**⚠️ 注意**：这条配置**只适用于不需要出网的阶段**。需要连外网隧道时请看 [`Q07`](#q07) —— **两者方向相反**。

**相关经验**：[`ai_knowledge.md` §4.1 · `P06`](ai_knowledge.md)

---

<a id="q07"></a>
### `Q07` ⭐ 隧道拨号失败：`Connect call failed ('127.0.0.1', 10900)`

**Q**：明明要连的是外网网关，报错里却出现 `127.0.0.1` 和本地代理端口；重连几秒内烧完配额。

**A**：本地代理劫持了 websockets 的拨号。**这里的正确配置与 [`Q06`](#q06) 恰好相反**：网关在外网、要直连，而 localhost 上的策略服务器又必须绕开代理。

```
no_proxy="localhost,127.0.0.1,::1"      # 精确值，不是 "*"
```
并在 websockets 拨号处**显式传 `proxy=None`**。若用第三方/官方 agent 代码，启动前 unset 全部代理变量。

**❌ 无效尝试**：照搬前几个阶段的 `no_proxy="*"` 肌肉记忆。

> ⚠️ **此坑会在换用别人的代码时复发**：官方 `tunnel_agent.py` 的拨号处**没有 `proxy=None`**（我们自己的适配层有，所以没炸）。**别人的代码不会带着你踩过坑之后加的防御。**

**相关经验**：[`ai_knowledge.md` §4.1 · `P07`](ai_knowledge.md)、教训 `L03`
---

## B 类·安装、依赖与环境（`Q08`–`Q16`）

> 📌 本类问题的根源是**上游依赖除 `torch>=2.0` 外全部未锁版本**（见 [`background_knowledge.md` §5.3](background_knowledge.md)）。装依赖时**顺序本身就是坑**，不要照 requirements 从上到下装。

<a id="q08"></a>
### `Q08` 世界模型服务启动即 500：`ImportError: liger-kernel is required`

**Q**：服务能起，第一个请求就 500。

**A**：配置默认开着 liger 系加速内核。二选一：
1. `pip install liger-kernel`（实测 0.8.1 可用）；
2. **推荐**：直接在 `configs/gesim_v2.yaml` 里关掉开关 —— 见 [`Q09`](#q09)。

**相关经验**：[`ai_knowledge.md` §4.2 · `P08`](ai_knowledge.md)

---

<a id="q09"></a>
### `Q09` ⭐ `ModuleNotFoundError: No module named 'spas_sage_attn'`

**Q**：pip 装不上，试了各种名字变体都说找不到包。

**A**：**SpargeAttn 根本不在 PyPI 上**，只能源码编译。上游明确说过没有这些内核也能跑，所以**首次部署应把四个加速内核开关全部关掉**：

```yaml
# configs/gesim_v2.yaml
liger_norm:        false
liger_layernorm:   false
triton_rope:       false
sparge_attention:  false
```

注意力回落到 SDPA，功能无损（实测跑完五个阶段）。

**❌ 无效尝试**：`pip install` 各种名字变体 —— **这个包在 PyPI 上不存在**，换名字没有意义。

> 💡 **这条应当成为所有新部署的默认动作**，不要等报错了才关。

**相关经验**：[`ai_knowledge.md` §4.2 · `P09`](ai_knowledge.md)、决策 `D02`；原理层 [`background_knowledge.md` §5.4](background_knowledge.md)

---

<a id="q10"></a>
### `Q10` 子模块报 "needs a separate revision"

**Q**：`git submodule update --init` 失败。

**A**：`third_party/openpi` 是**嵌套**子模块，且 pin 在具体 commit 上。浅克隆后按 sha 取：

```bash
git fetch --depth 1 origin <sha>
git checkout FETCH_HEAD
```

另外：**主仓库 clone 必须带 `--recursive`**，且 `openpi-client` 需要单独 `pip install -e third_party/openpi/packages/openpi-client`。

**❌ 无效尝试**：普通 `git submodule update --init`。

**相关经验**：[`ai_knowledge.md` §4.2 · `P10`](ai_knowledge.md)；原理层 [`background_knowledge.md` §8.5](background_knowledge.md)

---

<a id="q11"></a>
### `Q11` openpi 依赖地狱（三个症状连着来）

**Q**：① lerobot 的 API 与代码对不上；② numpy 被顶成 2.x；③ 装 torch 时报 `No matching distribution found for regex!=2019.12.17`。

**A**：**按这个顺序**装：

```
① 先装 regex          ← 否则 torch 装不上
② 按 commit 装 git 源码版 lerobot 0.1.0   ← PyPI 的 0.3.3 API 与代码不符
③ 装完把 numpy 回锁到 1.26.4（numpy<2）   ← lerobot 会拖入 numpy 2.4.6
```

每次 pip 操作后都复查一遍 `numpy.__version__`。

**❌ 无效尝试**：按 requirements 从上到下顺序安装。

**相关经验**：[`ai_knowledge.md` §4.2 · `P11`](ai_knowledge.md)

---

<a id="q12"></a>
### `Q12` conda 求解极慢，且装完 CUDA 从 12.1 变成 13.x

**Q**：求解 8 分钟；本来配好的 CUDA 12.1 被悄悄升级，编译链随之失效。

**A**：
1. `conda config --set solver libmamba`（求解慢的解法）。
2. **坚持系统 gcc 11.4，绝不装 conda 的 gcc** —— conda-forge gcc 的传递依赖会把 CUDA 顶高。
3. cuda-toolkit 装好一次后，**把该环境当只读**，不再往里装编译器类包。
4. 编译 wrapper 里显式 pin：`CUDA_HOME=$CONDA_PREFIX`、`CC=/usr/bin/gcc`。

**❌ 无效尝试**：`--freeze-installed` —— **明确无效**，拦不住这条传递依赖。

**相关经验**：[`ai_knowledge.md` §4.2 · `P12`](ai_knowledge.md)

---

<a id="q13"></a>
### `Q13` ⭐ 导入期直接崩：`from pkg_resources import ...`

**Q**：脚本还没跑到业务逻辑就崩了。

**A**：setuptools 83 移除了 `pkg_resources`，而 `imageio-ffmpeg 0.4.7` 在**模块加载期**就 import 它。降 setuptools：

```bash
pip install --no-deps "setuptools<81"
```

完整触发链：推理脚本 → trainer → dataset → `moviepy.editor` → `moviepy.config` → `imageio_ffmpeg._utils`。

**❌ 无效尝试**：设 `IMAGEIO_FFMPEG_EXE` —— **根本救不了**。该变量是在 `get_ffmpeg_exe()` 函数内部才读取的，而崩溃发生在更早的**模块加载期**，代码永远执行不到那里。

> 💡 通用判据：**报错发生在 import 期，就不要指望任何运行期开关**。

**相关经验**：[`ai_knowledge.md` §4.2 · `P13`](ai_knowledge.md)

---

<a id="q14"></a>
### `Q14` GroundingDINO 起不来 / 仓库 403

**Q**：两个不同的症状。

**A**：
- **起不来**：离线环境缺 bert tokenizer 的 `vocab.txt`，用 `aria2c` 从镜像单独拉一份放到缓存目录。
- **403**：这是 gated 仓库，需要先到模型页面接受许可，之后才能下载。

**相关经验**：[`ai_knowledge.md` §4.2 · `P14`](ai_knowledge.md)

---

<a id="q15"></a>
### `Q15` `ModuleNotFoundError: h5py` / `matplotlib`（明明装过）

**Q**：确认装过，还是报找不到。

**A**：本项目是**双 conda 环境**（世界模型侧 / 策略侧）。包装在 A 环境，脚本跑在 B 环境。用 `pip install --no-deps <pkg>` 补进**实际运行脚本的那个环境**。

**❌ 无效尝试**：假设"装过了" —— **多环境项目里"装过"必须问清楚是哪个环境**。排查时先 `which python` 确认身份。

**相关经验**：[`ai_knowledge.md` §4.2 · `P15`](ai_knowledge.md)

---

<a id="q16"></a>
### `Q16` 显存突然只剩四分之一

**Q**：什么模型都还没加载，`nvidia-smi` 已经显示占了约 30 GB。

**A**：`import jax` 默认预占约 75 % 显存。**强制项**：

```bash
export XLA_PYTHON_CLIENT_PREALLOCATE=false
```

必须在 import jax **之前**生效。

**相关经验**：[`ai_knowledge.md` §4.2 · `P16`](ai_knowledge.md)
---

## C 类·源码契约与接口误用（`Q17`–`Q26`）

> 📌 **本类是本项目问题数量最多的一类**，全部源于"按接口名望文生义"。
> **最有效的对策不是排障，是前置核验**：Stage 4 在写码前花约 2 小时逐条核对源码，一次性抓出 9 条致命错误，执行期做到 0 error / 0 abort。详见教训 [`L02`](ai_knowledge.md)。

<a id="q17"></a>
### `Q17` ⭐ `env.step()` 解包报错 / 帧数组形状不对 / 取到的不是想要的视角

**Q**：按 gym 惯例写的代码全线出错。

**A**：四条真实契约（都与"合理推断"不同）：

| 你可能以为 | 实际 |
|---|---|
| `step()` 返回 5 元组带 `done` | 返回 **4 元组 `obs, reward, state, info`，没有 `done`** |
| `frames[:, 0]` 取第一个视角 | `frames` 是 `(T, 3, V, H, W)` float32，`[:, 0]` 取到的是 **RGB 通道轴**。要取头部视角用 `head_view_frames()`，得 `(T, H, W, 3) uint8` |
| `RewardResult` 是 NamedTuple | 是 `@dataclass(frozen=True)`，**不能改字段** |
| 用 `--model_path` 指定检查点 | **没有这个参数**，检查点写在 YAML 的 `checkpoint:` 字段 |

**❌ 无效尝试**：按接口名望文生义 —— gym 风格的 `step` 在这里**就是没有 `done`**。

**相关经验**：[`ai_knowledge.md` §4.3 · `P17`](ai_knowledge.md)；原理层 [`background_knowledge.md` §7.1](background_knowledge.md)（`WorldModelEnv`）、[§7.2](background_knowledge.md)（`types.py` 数据契约）

---

<a id="q18"></a>
### `Q18` VLM 返回 HTTP 200，但 content 是空的

**Q**：请求成功、无报错，`content` 就是空字符串。

**A**：推理型模型（实测 `mimo-v2.5`）会**先吐约 462 token 的思维链 `reasoning_content`**，把 `max_tokens: 256` 的预算吃光，真正的 JSON 永远出不来。

```yaml
max_tokens: 2048   # 从 256 提上来
```
并在代码里留注释固化原因，否则下一个人还会调回去。

**❌ 无效尝试**：当成网络抖动重试；改 prompt —— **问题不在 prompt，在 token 预算**。

**相关经验**：[`ai_knowledge.md` §4.3 · `P18`](ai_knowledge.md)

---

<a id="q19"></a>
### `Q19` 任务抛 `NotImplementedError`

**Q**：某个任务名跑不起来。

**A**：实测 `mug_to_basket` 缺 `preprocess_seededit` 提示词，上游未实现。换成有完整实现的任务（本次全流程改用 `lift_box`）。

> ⚠️ **换任务是影响面很大的决定**：它会让"评测任务"与"策略训练任务"分离，后续所有成功率数字都变成**跨任务迁移**测量。本项目就因为没有把这件事贯彻到判分标准里，产生了 [`Q35`](#q35) 那个假阴性。**换任务时，务必同时检查所有消费任务名/任务文本的地方。**

**相关经验**：[`ai_knowledge.md` §4.3 · `P19`](ai_knowledge.md)、决策 `D04`

---

<a id="q20"></a>
### `Q20` 图像编辑 API 调用 socket hang

**Q**：请求发出去就卡住，不返回也不报错。

**A**：两个叠加的原因：
1. 上游代码用的模型**已下架**，换成在线可用的新模型。
2. 默认 `response_format="url"` 返回的是 CDN 链接，**国内不可达**。

修复要点（缺一不可）：
```
response_format="b64_json"   ← 内联返回，绕开 CDN
SIGALRM 150 s 硬超时         ← socket 层超时不一定生效
6 次重试
输出尺寸下限（实测 960×960）
```
把这些做成**幂等的 marker patch**，重复执行安全（本次固化为 226 行 patch，12/12 零重试通过）。

**❌ 无效尝试**：加长超时 —— **hang 的是 CDN 不可达，等多久都没用**。

**相关经验**：[`ai_knowledge.md` §4.3 · `P20`](ai_knowledge.md)、决策 `D05`

---

<a id="q21"></a>
### `Q21` `conditioning="action"` 下仍报缺 `.npy` 文件

**Q**：文档/推断都说动作条件模式不需要录制轨迹，但它还是要读文件。

**A**：**这个推断是错的**。渲染器初始化时仍会调 `load_bundle_cache()` 从磁盘读 4 个 `.npy`（相机内参 / 对齐外参 / 头腰常量 / 腕部锚点）。解法是**现合成**这几个约 1 KB 的小文件：

```python
build_bundle(staging_dir=...)   # 从 H5 + 相机 JSON 生成 4 个 .npy
```

**❌ 无效尝试**：传 `None`；按接口语义推断"不该需要它"。

> 💡 通用教训：**否定式断言（"不需要 X"、"不消费 Y"）必须验证到源码的读取处**。它比肯定式断言更容易错 —— 因为没人会主动去证明一件事不发生。

**相关经验**：[`ai_knowledge.md` §4.3 · `P21`](ai_knowledge.md)、决策 `D09`、[§3.1 两条被证伪的思路](ai_knowledge.md)

---

<a id="q22"></a>
### `Q22` 从 H5 读出来的数值量级完全不对

**Q**：读到的夹爪值离谱。

**A**：两处：
1. **H5 是嵌套 schema，不是扁平 `(T, 16)`**，按嵌套路径读。
2. 夹爪必须取 **`/action/{left,right}_effector/position[0,0]`**（归一化指令值）；**绝不能取 `/state/*_effector/position`**（原始编码器计数，量级完全不同）。

**❌ 无效尝试**：假设扁平布局；取 `/state/` 下的同名字段 —— **名字像，含义不同**。

**相关经验**：[`ai_knowledge.md` §4.3 · `P22`](ai_knowledge.md)

---

<a id="q23"></a>
### `Q23` `ModuleNotFoundError: No module named 'scripts'` / import 成功但拿到的是空壳

**Q**：两个相关症状。

**A**：
1. `python scripts/foo.py` 会把 **`scripts/` 而不是仓库根**放进 `sys.path[0]`。在脚本头 bootstrap 仓库根路径。
2. 目录名与包名相同时，会形成**命名空间包假阳性** —— `import` 成功，但导入的是空壳。加断言：

```python
assert module.__file__ and "<expected>" in module.__file__, module.__file__
```

**❌ 无效尝试**：只看"import 没报错" —— **能 import 不等于装对了**。

**相关经验**：[`ai_knowledge.md` §4.3 · `P23`](ai_knowledge.md)、教训 `L05`

---

<a id="q24"></a>
### `Q24` 想给策略做 LoRA 微调，但整条路线接不上

**Q**：peft 套不上去。

**A**：**这条路线本身不成立**，四个原因：peft 没装；openpi 的 LoRA 实现是 **JAX-only**；模型是朴素 `nn.Module`（没有 peft 期望的结构）；计划里写的 `action_head` **根本不存在**。

可行替代：**冻结主干，只解冻 4 个真实存在的 Linear 层**，实测共 **2,165,792** 个可训练参数，配 AdamW + 梯度裁剪 1.0。

**❌ 无效尝试**：`pip install peft` 然后套 `get_peft_model` —— **装上了也没用**。

**相关经验**：[`ai_knowledge.md` §4.3 · `P24`](ai_knowledge.md)、决策 `D13`；原理层 [`background_knowledge.md` §8.4](background_knowledge.md)（论文与开源交付的落差）

---

<a id="q25"></a>
### `Q25` 无法计算策略梯度：没有可用的概率密度

**Q**：想做 policy gradient，找不到 `log_prob`。

**A**：**流匹配模型没有闭式概率密度** —— `forward()` 是速度场的 MSE，采样是 `@torch.no_grad` 的 10 步 Euler 积分。

可行替代：**RWR（Reward-Weighted Regression）**，直接在原生可微损失上加权，不需要密度：

```
w    = softmax((R − b) / temp)        # b 为 EMA 基线：b ← 0.9b + 0.1R
loss = Σ wₜ · forward(obsₜ, aₜ).mean()
```

实测 60 iters，loss 2.055 → 1.080（最低 0.710，−47 %），留出集 OSR 30 % → 80 %。

**❌ 无效尝试**：套高斯 `log_prob` + REINFORCE —— **没有可用的密度可取对数**。

**相关经验**：[`ai_knowledge.md` §4.3 · `P25`](ai_knowledge.md)、决策 `D11`

---

<a id="q26"></a>
### `Q26` 梯度传不回策略

**Q**：跨服务调用后 loss 没有梯度。

**A**：`Policy.infer()` 末尾是 `np.asarray(x.detach().cpu())`，这是一道**硬 numpy 屏障**。放弃跨服务反传，改成**进程内加载策略**。

**❌ 无效尝试**：想办法"穿过" WebSocket 反传 —— `detach()` 之后再转 numpy，已经没有任何东西可穿。

**相关经验**：[`ai_knowledge.md` §4.3 · `P26`](ai_knowledge.md)、决策 `D12`
---

## D 类·进程、资源与稳定性（`Q27`–`Q34`）

> 📌 **本类的共同特征是「失败没有报错」** —— 日志干净、进程消失、显存不还。
> **靠读应用日志排查不出来**，必须外部观测：`nvidia-smi` 看显存、`dmesg` 看内核、`ps` 看真实 PID。

<a id="q27"></a>
### `Q27` 执行 `pkill` / `kill` 之后当前 shell 自己死了（exit 144）

**Q**：退出码 144 = 128 + 16（SIGTERM）。

**A**：`pkill` 的匹配模式把自己也匹配进去了。
1. 服务用 `setsid … &` 启动，脱离当前会话。
2. 按 pid 文件里的**精确 PID** 杀，不用模式匹配。

**❌ 无效尝试**：宽松的 `pkill` 模式。

**相关经验**：[`ai_knowledge.md` §4.4 · `P27`](ai_knowledge.md)

---

<a id="q28"></a>
### `Q28` ⭐ 服务"已经杀掉了"，但显存仍占十几 GB

**Q**：pid 文件里的进程已经不存在，`nvidia-smi` 还显示占用约 18 GB。

**A**：**pid 文件记的是 `conda run` 包装进程，不是真正的子进程**。杀包装进程只会让真进程变成孤儿，继续持有显存。

```bash
ps -ef | grep -E '<real-process-name>'   # 找真实子 PID
kill <real-pid>
nvidia-smi                               # 必须确认归零（空闲约 4 MiB）
```

**根治**：pid 文件里直接写真实子进程 PID，或干脆不用 `conda run` 包装（改为先 activate 再启动）。

**❌ 无效尝试**：只杀 pid 文件里的进程；只看应用日志判断是否退出。

> ⚠️ **此坑在本项目复发过一次**（Stage 3 踩过，Stage 5 原样再踩）。**文档拦不住复发** —— 要么写进启动/停止脚本的固定动作，要么写进单测（教训 [`L03`](ai_knowledge.md)）。

**相关经验**：[`ai_knowledge.md` §4.4 · `P28`](ai_knowledge.md)、教训 `L03` `L07`

---

<a id="q29"></a>
### `Q29` 启动编排脚本整体 hang 到超时（实测满 600 s）

**Q**：卡死在启动阶段，看不出卡在哪。

**A**：探活函数用的接口**没有设短超时**，而且在服务真正起来**之前**就被调用，于是探针自己 hang 住。
1. 手动分步起服务，先单独查世界模型的健康端点（`GET /healthz`）。
2. 探针必须带短超时 + 重试，而不是一次长阻塞调用。
3. 实测更省事的做法：编排脚本里干脆不用探针，改为固定等待 + 显式健康检查。

**❌ 无效尝试**：加长总超时 —— **hang 的是探针本身**，总超时给多久都会用满。

**相关经验**：[`ai_knowledge.md` §4.4 · `P29`](ai_knowledge.md)

---

<a id="q30"></a>
### `Q30` 后台任务日志文件长时间是空的，看不出死活

**Q**：`cat` 日志什么都没有，不知道是没跑还是卡了。

**A**：Python 的 stdout 在重定向到文件时是**块缓冲**的。一律加 `-u`：

```bash
nohup python3 -u train.py > run.log 2>&1 &
```

**❌ 无效尝试**：反复 `cat` 等它出现 —— 缓冲区没满就一直不会出现。

> 💡 这属于**开跑前就该铺好的可观测性**，事后补不回来（教训 [`L07`](ai_knowledge.md)）。

**相关经验**：[`ai_knowledge.md` §4.4 · `P30`](ai_knowledge.md)、教训 `L07`

---

<a id="q31"></a>
### `Q31` 渲染跑到第几个片段就被 OOM-kill

**Q**：实测跑到第 ~6 个 clip 挂掉。

**A**：进程 RSS **跨 clip 单调增长**。解法是**每个 clip 起一个独立子进程**，让操作系统在进程退出时回收全部内存。

**❌ 无效尝试**：进程内 `gc.collect()` —— **试过，明确无效**。它只能缓解跨条目的累积，解决不了单条目内的峰值。

**相关经验**：[`ai_knowledge.md` §4.4 · `P31`](ai_knowledge.md)、决策 `D08`、[§3.1 两条被证伪的思路](ai_knowledge.md)

---

<a id="q32"></a>
### `Q32` ⭐ 进程消失、日志停在某一行、**没有任何 Traceback**

**Q**：实测日志停在 `Restoring checkpoint` 就再无输出，进程不在了，应用日志里找不到任何线索。

**A**：**是内核 OOM killer 发的 SIGKILL，应用层捕获不到，所以永远不会有 Traceback。**

```bash
dmesg -T | grep -i -E 'oom|killed process'    # 唯一的证据在这里
```

实测场景：每个 jax 进程 restore 阶段峰值约 11–12 GB RSS，4 个并发就超过 47 GB 宿主内存。解法是**错峰启动**（实测间隔 120 s 即可，4 个 agent 全部 RUNNING，GPU 27.4 GB，宿主仍余 26 GB+）。

**❌ 无效尝试**：翻应用日志找原因 —— **应用日志里什么都不会有**。

> 💡 **排查纪律**：凡是"进程消失且无 Traceback"，第一动作就是 `dmesg`，不要先加假设。

**相关经验**：[`ai_knowledge.md` §4.4 · `P32`](ai_knowledge.md)、决策 `D19`、教训 `L05` `L07`

---

<a id="q33"></a>
### `Q33` 盘写满 / 输出落在错误的盘

**Q**：目标盘只剩几 G，而输出路径硬编码在上游代码里。

**A**：
1. **逐文件符号链接**做影子树（实测每 episode 12 个链接）。
2. 长期方案是整体改道到空间充足的目录。

**❌ 无效尝试**：**目录级软链** —— 上游会往目录里写**新**文件，目录级软链在这里不管用。

**相关经验**：[`ai_knowledge.md` §4.4 · `P33`](ai_knowledge.md)、决策 `D07`

---

<a id="q34"></a>
### `Q34` 平台侧进度冻结：重连成功，但网关 20+ 分钟一个字节不发

**Q**：agent 自动重连后 TCP 已 ESTABLISHED，但没有 warmup、没有数据帧，进度完全不动。

**A**：网关的会话管理器**卡死在已死 session 的句柄上**。关键点：**用同一个 `agent_id` 重连不会触发重新派发**。

```
1. 杀掉该 job 的全部 agent
2. 用全新 agent_id 错峰重启（间隔见 Q32）
3. 网关随即重新 warmup 并派发 pending case
```
实测 17:42 重启 → 17:46 重新派发 → 17:58 该 case 完成 → 17:59 正常收尾。

**判据**（用来区分"还在跑"和"卡死了"）：重连后 TCP ESTABLISHED **但长时间既无 warmup 帧也无数据帧**，即为卡死。

**❌ 无效尝试**：等待自动重连恢复 —— **连上了也没用**，问题在对端的会话状态。

**相关经验**：[`ai_knowledge.md` §4.4 · `P34`](ai_knowledge.md)
---

## E 类·正确性与假阴性（`Q35`–`Q41`）

> 📌 **本类最贵**：程序不报错、流程看着正常，但**结论是错的**。
> 排查它靠的不是读日志，而是**审计四件套**（教训 [`L01`](ai_knowledge.md)）：
> ```
> ① 回退计数    —— 兜底路径触发了几次？（要求 0，且触发必被记录）
> ② 动作非退化  —— 动作 std、关节位移、夹爪开合，是不是在输出常数？
> ③ 帧数对账    —— 落盘帧数 = 元数据行数 = 各日志帧计数之和？
> ④ 输入侧测量  —— 观测的量纲、分位、静息位形，是否落在训练分布内？
> ```
> **先证明管道是通的，再讨论模型行不行。**

<a id="q35"></a>
### `Q35` ⭐ 成功率 0 %，但怀疑不是模型的问题

**Q**：批量评测跑完全部失败，看起来像泛化彻底失败。

**A**：**先查判分标准是否与被测任务一致**。本次的真实原因是：

> 一个常量 `SOURCE_TASK_TEXT` **被三方消费** —— 策略的 prompt、世界模型的 `set_task`、VLM 判分器的评分标准。它被留成了上一阶段的"水壶"文本（因为检查点的 `DEFAULT_PROMPT` 就是水壶），而数据其实是 `lift_box`。判词直白得刺眼：**"画面里既没有水壶也没有杯子"**。

三处统一改成正确任务文本后重跑，从 0 % 变成 6.5 %。

排查步骤：
```
1. 把判分器的原始判词打出来读一遍 ← 最快，本次就是这一步露的马脚
2. grep 出任务文本常量的全部消费者，逐个确认取到的值
3. 再做审计四件套的 ①②③
4. 以上都干净，才可以把数字当成模型能力结论
```

**❌ 无效尝试**：把 0 % 直接当成模型能力结论 —— **这是本项目最接近"发布错误结论"的一次**，是人工复核（"评判标准要换成新任务"）拦下来的。

**相关经验**：[`ai_knowledge.md` §4.5 · `P35`](ai_knowledge.md)、教训 `L01` `L06`

---

<a id="q36"></a>
### `Q36` ⭐ 手臂抖动 / 夹爪不动 / 左右臂互换，但**不报错**

**Q**：动作数组维度对得上，程序正常运行，行为就是不对。

**A**：**16 维关节布局有多套并存**，用错不报错、只是行为错。本次实测撞到**三套**：

| 位置 | 布局 |
|---|---|
| 模型输入 | grip-last：`[L7臂, R7臂, L夹爪, R夹爪]` |
| 策略服务器输出 | WM 交错：`[L7臂, L夹爪, R7臂, R夹爪]` |
| 平台包络切片基准 | grip-last |

正确做法：
1. 转换走官方的 `wm_state_to_policy_state()`（见 [`background_knowledge.md` §7.2](background_knowledge.md)），不要手抄下标。
2. 自己写的重排**必须配单测**：构造 `wm[j] = j` 的模式数组，**逐位断言**转换结果。

**❌ 无效尝试**：目测数组"长得对" —— **16 个数排错顺序，肉眼分不出来**。

> 💡 本次靠这条单测，线上 8994 帧零协议错误。**这就是"写进单测比写进文档可靠"的实例**（教训 [`L03`](ai_knowledge.md)）。

**相关经验**：[`ai_knowledge.md` §4.5 · `P36`](ai_knowledge.md)、教训 `L03`

---

<a id="q37"></a>
### `Q37` 对端解析崩 / 会话静默失败（msgpack）

**Q**：本地测试正常，发到对端就崩，或者会话无声无息断掉。

**A**：对端用的是**普通 msgpack**（不是 `msgpack_numpy`），任何 numpy ndarray 都会被编成 ext 类型，对端解不开。

1. 包络里所有数组 `.tolist()`，只用纯 Python 容器。
2. 加 round-trip 断言：
```python
assert msgpack.unpackb(msgpack.packb(env)) == env   # 且确认无 ext 类型
```

**❌ 无效尝试**：假设两端 msgpack 变体一致。

**相关经验**：[`ai_knowledge.md` §4.5 · `P37`](ai_knowledge.md)、教训 `L04`

---

<a id="q38"></a>
### `Q38` 一连上就异常断线 / 轮询把在跑的 job 判成终态

**Q**：两个都是"按文档写代码"导致的。

**A**：
1. **空帧**：网关的 `warmup` 控制帧会以 `("", b"")` 调用 handler。handler 首行判空直接返回，不要往下走业务逻辑。
2. **状态机**：平台实际比文档**多一个 `evaluating` 状态**。把它加进"进行中"集合，否则轮询会把在跑的 job 当成结束。

**❌ 无效尝试**：完全照文档写状态机。

> 💡 通用方法论：**第三方文档管协议，实测管 API**。本次实测出 6 处 HTTP API 与文档不符（登录方法、地址、SDK 路径是否存在、配额数字、id 形态、状态机）。分诊启发式：**4xx 是语义拒绝，改请求而不是重试；5xx 先怀疑自己再怀疑平台**（教训 [`L04`](ai_knowledge.md)）。

**相关经验**：[`ai_knowledge.md` §4.5 · `P38`](ai_knowledge.md)、教训 `L04`

---

<a id="q39"></a>
### `Q39` 报告小节全空 / 首帧日志把图像形状打成 `[]`

**Q**：两个独立的小坑。

**A**：
1. **报告空**：结果文件名 `final_<tag>.json` 的 tag 在轮询脚本与报告脚本里**各硬编码了一遍，且不一致**。**跨脚本的文件名约定只定义一次**，从同一个源导入。
2. **形状打成 `[]`**：对 dict 做 `np.asarray(...).shape` 得到的是 `()`。改为记录结构化的 `image_specs`，逐键记形状与 dtype。

**相关经验**：[`ai_knowledge.md` §4.5 · `P39`](ai_knowledge.md)、教训 `L06`

---

<a id="q40"></a>
### `Q40` 跨机型评测得 0 分

**Q**：同一条链路在本机型好用，换目标机型全零。

**A**：**先做审计四件套确认不是管道问题**，再判定为真实测量。本次的审计结论：

```
① 回退计数 0                                    → 没有走兜底
② 动作非退化：std ≈ 0.27、约 2 rad 关节位移、夹爪有开合  → 不是输出常数
③ 帧数对账：8994 = JPEG 数 = 元数据行数 = 各日志计数之和  → 没有丢帧
④ 输入侧测量：目标机型静息位形大部分落在训练分位（q01–q99）之外；
   夹爪量纲 −0.735 vs 训练分布 0..119.8，归一化后直接削顶到 0
```
→ 结论：**不是 bug，是真实的跨机型迁移失败**。

**处理原则：记录在案，不做静默矫正**，并在报告里写明定位（跨任务域 + 跨机型）。

> ✅ 事后验证：同一条链路换成官方 baseline 权重，得到 0.745 / 0.604 的正常分数 —— **反过来证明了这个 0 分是真实测量，而不是管道故障**。

**❌ 无效尝试**：悄悄做量纲对齐把分数抬上去 —— 那测的就不是零样本迁移了（教训 [`L08`](ai_knowledge.md)）。

**相关经验**：[`ai_knowledge.md` §4.5 · `P40`](ai_knowledge.md)、决策 `D17`、教训 `L01` `L08`

---

<a id="q41"></a>
### `Q41` ⚠️ Stage 1 三个 demo 里机器人的动作雷同

**Q**：人工查看输出视频，发现三个不同任务的 demo 里机器人做的都像是"拿水壶倒水"。

**A**：**未解决，建议参考详细记录。**

原始材料里只有"到 `debug-stage1` 分支核查三个 demo 是否共用同一 prompt、找出各自正确的 prompt 后重跑"这条指令，**没有任何执行纪要或结论**。

材料内部还存在张力：
- Stage 1 报告里三个 demo 的 prompt 文本**是各不相同的**；
- VLM 判词也分别针对洗面奶（"抓成了薯片袋"）和毛巾（"抓起了毛巾但没有擦拭"）；
- 这与"三个视频动作雷同"的观察**对不上**。

**证据不足以判断**是 prompt 传递有 bug，还是策略在三个任务上行为坍缩到了同一个模式 —— 后者若成立，反而是关于被测策略的一个重要发现。

**引用 Stage 1 相关结论前请注意这个未决项。** 若要复查，建议的第一步是给每个 demo 的 prompt 加落盘记录，从数据而非视频侧确认三者是否真的不同。

> 💡 附带教训：这个问题**只可能由人发现** —— 执行方没有读图能力，视觉层面的错误对它是结构性盲区。这类项目里"让人定期看一眼输出"不是可选项，是补盲。

**相关经验**：[`ai_knowledge.md` §4.5 · `P41`](ai_knowledge.md)、[§5.3 用户介入的价值](ai_knowledge.md)

---

## F 类·平台契约与判分口径（`Q42`–`Q45`）

这一类**不是"程序崩了"，而是"我们把外部契约或自己的数字读错了"**。共同特征：**照文档写、照计划写就会错**，而且错了之后程序照跑、日志照打，只有对着实测数字算一遍才会发现。四条全部来自 R2E2R 数据生成（Stage 2）与 RoboColiseum 在线评测（Stage 5）。

<a id="q42"></a>
### `Q42` 榜单 `total` 与文档写的算法对不上（说是求和，数字像均值）

**Q**：平台文档描述 board 总分为各任务得分之**和**，但拉回来的 `total` 明显小于分项之和。

**A**：**实测口径是算术平均，不是求和。以实测为准。**

1. 从 `/result` 拉回逐任务分数与 `total`，**手算一遍**：
   - Stage 5b manipulation：10 个任务分数之和 `6.04`，`total = 0.604` → 恰为 `6.04 / 10`；
   - Stage 5b instruction：和 `7.46`，`total = 0.745` → 误差 ≤ 0.001。
2. 结论：**`total` 应按均值读**。因此 **board 之间的 `total` 不可直接横向比较**（任务数不同、任务难度不同）。
3. 报告里写分数时同时落盘逐任务分数快照，别只存 `total`。

**❌ 无效尝试**：按文档把 `total` 当求和解释 —— 会得出"平均分只有十分之一"的错误结论，并连带把 instruction board 的 0 误读成"部分任务有分但被拉低"。实际上那是 **10 个任务全 0 → 均值 0** 的干净 0。

**相关经验**：[`ai_knowledge.md` §4.6 · `P42`](ai_knowledge.md)、原理层 [`background_knowledge.md` §9.3.4](background_knowledge.md)

<a id="q43"></a>
### `Q43` ⭐ 计划里的任务数 / 拆分 / 成功率与平台实际不符

**Q**：执行计划写着"共 78 个任务、四个 board 各 20/20/20/18"，报告模板里甚至预填了"综合平均成功率 62.5 %"和几条行业基线；上线一拉发现全不对。

**A**：**计划作者没有访问过平台，这些数字是想象出来的。**

1. **任务数从平台实测**：`GET /api/challenge/job/<id>/result` 的 `tasks` 键数量即为该 board 的任务数 —— 实测 instruction 与 manipulation **各 10 个**。
2. **总数 78 本身可以被独立佐证**，但**不能引计划**：见姊妹项目 [`genie_sim_v3` 原理层 §3.5](../genie_sim_v3/background_knowledge.md) 的 `[CODE]` 级 board 表（instruction 10 + robust 50 + manip 10 + spatial 8 = 78）。**错的是"20/20/20/18"这个拆分**。
3. 本次的处置：在报告里显式声明勘误"78 是未经验证数字"，并立一条硬规矩 —— **报告中不存在任何无法溯源到 `results/` 快照的数字**。

**❌ 无效尝试**：把占位数字留在报告模板里"等实测回来再填" —— 模板里的数字比正文里的更危险，因为它看起来像结论、且极容易漏改。

**相关经验**：[`ai_knowledge.md` §4.6 · `P43`](ai_knowledge.md)、`L09`

<a id="q44"></a>
### `Q44` `GET .../job/<uuid>/result` 返回 500 `invalid job_id`

**Q**：手上有 job 的 uuid，拼进 result 接口却拿到 HTTP 500，报文里写 `invalid job_id`。

**A**：**该接口要的是数字自增 id，不是 uuid。**

1. 先 `GET /api/challenge/jobs` 列出全部 job —— **注意响应里的列表键名是 `items`，不是 `jobs`**。
2. 用返回结果建一张 `job_uuid → id` 的映射表。
3. 再用数字 id 请求 `/api/challenge/job/<id>/result`。

**❌ 无效尝试**：把 500 当成平台故障去等它自己好 —— 参见教训 `L04`：**5xx 先怀疑自己**（本项目里 5xx 多次是自己传错参数或 token 问题；反过来 **4xx 从来不是网络抖动**）。

**相关经验**：[`ai_knowledge.md` §4.6 · `P44`](ai_knowledge.md)、原理层 [`background_knowledge.md` §9.3.5 文档漂移表](background_knowledge.md)

<a id="q45"></a>
### `Q45` 计划中的"Z 轴 / 桌高泛化曲线"画不出来（自变量方差为 0）

**Q**：想按计划分析生成数据的 Z 向（桌高）泛化衰减，却发现所有 episode 的 Z 位移都一样。

**A**：**生成配置本身把 Z 钉死了，这条分析维度不成立。**

1. 查生成配置的 `trans_range.generate.object` —— Z 分量上下界**都是 `0.0`**。
2. 统计 46 个 episode 的 `meta_info.json` —— `dz` **实测全部为 0.000**。
3. 同批数据还有两个易误读的分布特征：
   - `dx` **恒为负**（平移只朝一个方向采样）；
   - `obj_rot_angle` **未做 `mod 2π` 归约**，分布展开到约 ±1000°，直接画直方图会得到无意义长尾。
4. 正确处置：**删掉该分析维度**，并在报告里补一条"Z 轴声明" —— 本批数据是**平面内平移 + 绕 Z 旋转**的分布，**Z 向泛化未被覆盖**，避免下游误以为"测过且通过"。

**❌ 无效尝试**：在自变量零方差的情况下硬凑曲线（例如改用别的量冒充 Z、或把噪声当信号解释）。

**相关经验**：[`ai_knowledge.md` §4.6 · `P45`](ai_knowledge.md)、教训 `L09`

---

## 贡献指南

**追加新条目前先读这一节**，编号约定是外部交叉引用的基础。

### 编号规则

- `Qxx` 与经验层 [`ai_knowledge.md`](ai_knowledge.md) §4 的 `Pxx` **严格一一对应**。
- **只追加、不重排、不复用**。即使某条已经过期或被推翻，也保留编号，在正文标注"已过期 / 已被 `Qyy` 取代"。
- 新增排障条目的正确顺序是：**先在 `ai_knowledge.md` §4 的对应类别表里加 `Pxx`，再在本文档加同号 `Qxx`**。不要只加一边。

### 条目模板

```markdown
<a id="qNN"></a>
### `QNN` 一句话症状（用**你会在终端里看到的东西**当标题）

**Q**：现象描述，尽量带上原始报错文本或可观测的数字。

**A**：
1. 步骤清晰、可直接执行。
2. 命令与代码片段用 fenced code block。
3. 本机路径写 `<repo_root>` / `<user_home>` / `<path>`，主机地址写 `<INFER_IP>:<PORT>`。

**❌ 无效尝试**：已经确认走不通的路（**这一项最有价值，不要省略**）。

**相关经验**：[`ai_knowledge.md` §4.x · `PNN`](ai_knowledge.md)、决策 `Dxx`、教训 `Lxx`
```

### 三条硬要求

1. **必须同步「快速症状索引」表** —— 新增 `Qxx` 后在顶部表格加一行，用**用户实际看到的现象**做索引词，不要用根因做索引词（用户排障时手上只有现象）。
2. **必须填「❌ 无效尝试」** —— 这是本文档区别于普通 FAQ 的核心价值：记录**已经花过时间确认走不通**的路。没有无效尝试就写"—"，不要删掉这一栏。
3. **禁密钥、禁绝对路径** —— 不得出现账号、密码、密钥、access token。示例中的本机路径统一替换为占位符。

### 未解决条目的写法

没有明确解决方案时，`**A**` 的第一行写 **"未解决，建议参考详细记录。"**，然后：
- 说明**已知什么、缺什么证据**；
- 如实记录材料内部的矛盾（不要为了好看而挑一种解释）；
- 给出"若要复查，建议的第一步"；
- 在快速症状索引里用 ⚠️ 标注。

参照 [`Q41`](#q41) 的写法。

### 分层纪律

本文档是**排障视图**，与 [`ai_knowledge.md`](ai_knowledge.md) §4 是**同一批事实的两个视图**：

| 你想知道 | 去哪 |
|---|---|
| 遇到 X 报错怎么办 | **本文档** |
| 为什么会这样 / 还试过哪些无效方法 / 当时怎么决策的 | `ai_knowledge.md` §3 §4 |
| 设计原理、API 契约、能力边界 | [`background_knowledge.md`](background_knowledge.md) |
| 代码在哪、改哪个文件 | [`code_knowledge.md`](code_knowledge.md) |
| 只想赶紧把它跑起来 | [`quickstart.md`](quickstart.md) |

**不要在本文档新增只有这里才有的事实** —— 那属于经验层。本文档只做重排与检索。
