# Track2 Q1 — 冰面足式 Locomotion DR（Genesis World 1.3.3，humanoid）

- 冻结输入：`inputs/tracks/track_2_samples.txt` 第 1 题（track2 / index=1）
- 仿真引擎：Genesis World（`sim_engine.slug: genesis`）最低版本 1.3.3
  （引擎仓 pins 钉死：genesis-world 1.3.3、torch 2.4.1+cu124、numpy 1.26.4）
- 用途：Phase 1 Task8 Track2 Q1 真实 batch rollout（3 seeds × 3 臂：
  normal / ice_nominal / ice_dr，9 rollout × 8 s），Rung1–4 判定载体；
  阈值真值在引擎仓 `orchestrator/judge/gait_thresholds.py`（公开仓不复制数字）

## 正本溯源（run 执行副本）

本文件正本取 **v1 实际执行副本**（V1 对标线程 `t8-genesis-20261016a`）：

```
$SIMPRAXIS_RUN_DIR/phase1/task8_track2/q1_genesis/
  run_t8-genesis-20261016a_1/genesis_humanoid_dr.py
```

- run 副本 sha256（本文件）：见 manifest `files[]`
- 引擎仓当时仓内版 sha256：见 manifest `provenance.repo_version_sha256`
- 两版约 20 行差异，来自执行后的引擎契约修复（提交 cede4b6 / c3ec0bf）；
  manifest 同时锁两版 sha 与 `v1_run_relpath`，正本以 run 副本为准

## 运行面

```bash
# 单 rollout（Rung4 视频/telemetry 路径）
python genesis_humanoid_dr.py run --params-json <params.json> \
    [--telemetry out.json] [--video out.mp4] [--label ...] [--dur-s 8.0]
# batch（图运行路径，Task8 编排器注入参数）
python genesis_humanoid_dr.py batch --out-dir <workdir> --seeds 3 \
    [--dur-s 8.0] [--calibration-json push_window_calibration.json]
```

`--calibration-json` 指向引擎侧 35N×0.2s 选窗标定件 v2
（`/mnt/caches/simpraxis/genesis_probe/push_window_calibration.json`，
引擎数据/标定资产不随本方案迁移，由编排器 stage 进 workdir）。
无头环境需 `GS_ENABLE_ZEROCOPY=0`（默认 zerocopy int32 gather 抛错的必需
开关）、`PYOPENGL_PLATFORM=egl`。batch 输出
`dr_controls_vs_experimental.csv`（35 列，字段顺序被引擎 AST 测试钉死）。

Task0b（2026-10-17）三层分离时从 sim-praxis 迁入本公开仓。
