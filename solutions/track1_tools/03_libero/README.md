# Track1 #4 — LIBERO 官方 MuJoCo 栈最小闭环（libero_spatial 十任务，EGL 无头）

- 冻结输入：`inputs/tracks/track_1_samples.txt` 第 4 条工具（track1 / index=4，LIBERO）
- 仿真引擎：LIBERO 官方栈（robosuite 1.4.0 + MuJoCo；隔离 venv 内 mujoco 钉
  **3.1.6**——robosuite 1.4.0 与 mujoco 3.15 存在结构性 MjData API 断裂
  `d.qM`→`d.M` 与关节类型断言墙，经用户裁决降版，Phase 1 主 venv 3.15 不动）
- 用途：Phase 2 Task7 LIBERO Stage1 实跑（第五平台 track）；Gate2 真人验收
  载体（2026-10-27 14:47:24 approve，批注要求的「夹爪抓起物体→移动→放下
  完整成功 demo」由本脚本 servo 控制器产出）

## 运行面

```bash
# 容器内隔离 venv（宿主零安装）；ulimit -n 65535 防 task8 env 构造 EMFILE
ulimit -n 65535
MUJOCO_GL=egl PYOPENGL_PLATFORM=egl \
  /home/agent/runs/phase2/venvs/libero/bin/python stage1_minimal.py \
  --out-dir <workdir> --run-id <run_id>
```

`--out-dir` 必填（编排器注入）；`--run-id` 默认 `run`。需
`LIBERO_CONFIG_PATH` 指向含 `.libero` 资产的目录（官方 BDDL/init_states）。

产物：`results.json`（schema `simpraxis.task7.libero_results.v1`，官方判分
`judge=libero_official`）+ `telemetry.json`（逐 episode 摘要）+ `video.mp4`
+ `cover.png` + `manifest.json`。

## 控制器要点（Gate2 质量线的机器真值来源）

10 任务 × 2 局；每局：settle → hover → **指轴 z 对齐**（finger spread 轴 init
沿 ±y，须空中绕 z 转腕至径向）→ 垂直下探 → 闭爪壁咬（qpos ~[0.005,−0.005]）
→ 抬升 → **拖尾补偿放置**（碗 trails eef ~0.047m，指令 eef=plate_xy+trail；
分轴运输 + 反应式下放 + 开爪与上提同步）。BDDL goal 解析兼容大写
`On`/`Inside` 谓词与 `(:obj_of_interest …)` 兜底。

判分时刻：`env.check_success()`（官方）；本套件遥测为逐 episode 摘要，
无逐帧 ee/penetration 数组，Rung1–3 规则判定结构性不可判（学习回写按
核验级 rung=1 落表）。

## 溯源

正本 = Gate2 真人 accept 的 run 副本
`@runs/phase2/task7_libero/stage1_spatial/run_t7-libero-stage1-20261026e_2/stage1_minimal.py`
（sha256 `a9619eca…`，18741B，575 行）；仓内版逐字节复制。Task7 攒批战役
（run2k reject#1 → 攢批82/84 facts 注入 → r26 一次通过）产物，Gate2 后按
计划 L166 回收。
