# Track2 Q2 — 固态 LiDAR 雨雪雾物理光学材质模型（Carla 0.10.0）

- 冻结输入：`inputs/tracks/track_2_samples.txt` 第 2 题（track2 / index=2）
- 仿真引擎：Carla client 0.10.0（`pip install carla==0.10.0 --no-deps`；能力矩阵
  尚未注册 carla slug，方案以 `sim_engine.slug: carla` 显式声明）
- 闸门：D9 条件闸门，不经 LangGraph 图、无 Gate1；2026-10-16 真人 Gate2 点验
  `approve`（飞书卡片表单），全程 0 次方舟付费调用（29→29，delta=0）
- 编排件归属：补点验编排 `scripts/milestone1/q2_human_gate.py` 属引擎仓
  sim-praxis，不随本方案迁移；本目录只含题目三件脚本与其物理测试

## 文件与运行面

| 文件 | 职责 | 运行参数 |
| --- | --- | --- |
| `collect_weather_lidar.py` | 容器内对 clear/rain_hard/fog_dense 三预设各 3 重复、每预设 10 帧同步采集 `ray_cast_semantic`（几何+语义+强度） | `--host/--port/--out（必填）/--map/--repeat/--control-all-clear`（阴性对照：三段全部下发 clear） |
| `optics_model.py` | 引擎外物理光学材质层：雨谱/雪谱消光、Koschmieder 雾、湿材质 BRDF、后向散射假点、检测阈值；纯 numpy 确定性（rng 由条件+帧号派生），不依赖 Carla | 库模块；`QBACK_DEFAULT=0.4` 为源码常量（真人闸门读源码核对，不 import） |
| `analyze_q2.py` | outcome（原生不变量）× mechanism（光学扫描）双路分析；产 `invariance_checks.json`/`optics_sweep.csv`/图/SUMMARY；`write_summary` 强制阴性对照缺失即显式声明，禁止编造 | `--root/--out（必填）/--reps/--label/--native-only` |

`tests/` 是从引擎仓迁入的物理数值断言（零付费、不依赖 Carla）：
`conftest.py` 提供平目录导入夹具（逐字脚本的绝对导入
`sandbox.track2.carla_lidar_weather.optics_model` 在测试中以模块别名桥接，
生产脚本一字未改）。

## Task0a 沉淀：Q2 完整光学知识（数字逐项可溯源）

> 本节是 Phase 2 Task0a 声明的 0b 验收前置：全部数值从真人裁决
> `decision.json` 与分析 JSON/CSV 逐项核对后收录，经 solution_chunks 向量化
> 可语义召回；未从计划 prose 转抄。
>
> 溯源根（相对 `$SIMPRAXIS_RUN_DIR`）：
> `phase1/task8_track2/q2_carla/`，thread `t8-q2carla-hitl-20261016`。

### 1. outcome（Carla 原生通道）：天气因果被证伪

- **语义几何逐 bit 相等**：80 组对比 0 失败
  （`invariance_checks.json: semantic_geometry_bit_identical`；
  decision.json `metrics.outcome.bit_identical.comparisons=80, failures=0`），
  其中含跨进程重复采集 20 组 0 失败（`geo_cross_repeat_bit_identical`，
  `cross_repeat=20`）。claim：`ray_cast_semantic` 射线命中逐 bit 相等——
  天气不进几何管线；同步模式 + 固定参数下进程级重复逐 bit 可复现。
- **ray_cast 点数跨天气有约 0.5% 漂移，但天气因果被 z 分数证伪**：
  对 clear 基线的标准化差 z：rain_hard **−1.1159120360389487**、
  fog_dense **−1.0090239099815772**（|z| 均 < 2.0，无检出天气效应）。
- **阴性对照复现同号漂移**：三段全部下发 clear 的 control 数据集，在相同段
  位置给出 z：rain 槽位 **−1.0767449534523499**、fog 槽位
  **−0.9736084636580625**——与天气数据集同号同量级，证明漂移来自天气无关
  的 dropoff RNG（默认 `dropoff_general_rate=0.45`，`noise_seed=0` 随 tick
  推进）造成的段位置伪相关，而不是天气物理通道。
- **共有坐标点强度逐 bit 恒等**：幸存者 max|ΔI| = **4.45e-05**
  （原值 `4.4465065002441406e-05`，float32 舍入量级；rain_hard/fog_dense
  两预设相同），mean|ΔI| 约 3.6e-05。
- **Carla 0.10.0 原生无雪**：`engine_has_snow=false`——引擎天气通道没有
  雪预设/雪路径；雪只能由引擎外光学层表达。

### 2. mechanism（引擎外光学材质层）：三天气机理数值

10 帧聚合扫描（`analysis/optics_sweep.csv`；输入 clear 原生点云
n=13255.8/帧）。三档裁决卡引用值（decision.json `metrics.mechanism`）：

| 条件 | 消光 α (1/km) | 后向散射 β_π (1/km/sr) | 平均透射 T | 表面点留存 | 天气假点/帧 | 近盲点数/帧 |
| --- | --- | --- | --- | --- | --- | --- |
| rain 100 mm/h（Marshall–Palmer，Λ=4.1R^−0.21） | 6.635723624602269 | 1.327144724920454 | **0.8710712869551477** | **71.73318315501464%** | **6345.5** | **3747.0** |
| snow 100 mm/h 融化当量（Gunn–Marshall，Λ=2.29S^−0.45） | 498.2267282198721 | 99.64534564397442 | **0.02351639238902357** | **1.7185096739776313%** | **8078.5** | **3740.4** |
| fog V=6 m（Koschmieder 1924，α=3.912/V，905nm≈550nm） | 652.0 | 130.4 | **0.012718466098264918** | **10.687424875465549%** | **0（雾只衰减、不产生假点）** | null（检测丢失 11839.1/帧） |

关键量级关系（optics_sweep.csv 全档位）：

- 同水当量下雪截面远大于雨：10 mm/h 时 α_snow=22.25 vs α_rain=1.56；
  100 mm/h 时雪 T=0.0235 远低于雨 T=0.871——雪谱大而密的雪花占主导。
- 雨透射随雨强单调：R=2.5/10/25/50/100 时 α=0.6495/1.5556/2.7707/4.2878/
  6.6357（1/km），T 由 0.9859 降至 0.8711；雨滴谱积分（Qext=2）落在
  Rasshofer 2011 经验式 a_R=1.075·R^0.68 dB/km 的 ×1.5 容差带内。
- 雾走 Koschmieder：V=200/100/50/20/10/6 m 时 α=19.56/39.12/78.24/
  195.6/391.2/652.0（1/km），V=6 m 时表面留存仅 10.69%、检测丢失
  11839.1/帧；雾无后向散射假点（n_weather_false=0），机理是纯衰减。
- 湿沥青 BRDF 变暗路面（QBACK_DEFAULT=0.4 的材质回射率口径），晴好
  identity：clear 时 α=β=0、T=1.0、天气假点 0、点云逐字节不变。

### 3. 预注册方向的结论与未标定残差（禁止翻案）

outcome 与 mechanism 是两条独立证据链：原生 Carla 通道里天气不进几何/
强度（z 证伪 + 阴性对照），雨雪雾效应由引擎外光学材质层以可标定机理表达。

残差声明（decision.json `metrics.residual` 原文）：
> Qback=0.4、湿沥青 BRDF 0.7、905nm 雾消光等参数未用真实天气 LiDAR 数据
> 标定，模型只断言量级与单调性；静态单车/单地图/单 spawn，未引入交通流
> 与多径。

### 4. 证据原件 sha256（decision.json `evidence_sha256`，2026-10-16）

| 件 | sha256 |
| --- | --- |
| human_gate/decision.json | 4764dd469466ea990c6b81abdd0ad8f1bdb684ac629cb220e8e1f72a4596ed0f |
| analysis/invariance_checks.json | 6ff4a1db16009238665fd95714bea2553e01971c757243ffd6bb1e46a39fa889 |
| control/analysis/invariance_checks.json | a2b9bd83cb1d522c12a8b91ac494608edcbe761dca58952274c7ed31d8daf074 |
| analysis/optics_sweep.csv | 340a7c3ade4f610a922e8c0b1ef40f17fe01718f847120e80728e3fbcf581fc5 |
| analysis/SUMMARY.md | 1a4a7937a5e9c1fe600c6e9a77bfee70983819762a35fec5c31835ec9e812f39 |
| q2_overlay.mp4 | 720bc00d174025490a9160b70dbfbce9209a0f2bd435e12e1caae184b797bd95 |

分析元数据：3 重复 × 每预设 10 帧，analysis_wall_s=16.4，
ts 2026-10-16T10:52:07+0800（`analysis_meta.json`）。
