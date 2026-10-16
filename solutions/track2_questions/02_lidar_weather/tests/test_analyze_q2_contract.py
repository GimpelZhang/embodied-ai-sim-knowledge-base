#!/usr/bin/env python3
"""analyze_q2.write_summary 阴性对照契约（L-10）+ load_frame 缺帧/缺键错误（S-7）。

Task0b 从 sim-praxis 迁入：
- tests/milestone1/test_q2_optics_model.py 的两条 write_summary 契约断言；
- tests/milestone2/test_task0_debt.py 的 S-7（FrameDataError/load_frame）。
导入面由 conftest.py 平目录夹具桥接，断言一字未放水。
"""
from __future__ import annotations

import json

import numpy as np

from analyze_q2 import FrameDataError, load_frame, write_summary
import pytest


# ---------------------------------------------------------------------------
# L-10：阴性对照缺采时 SUMMARY 必须显式写「未采集」，绝不伪造对照 z
# ---------------------------------------------------------------------------

def _summary_fixture(tmp_path):
    """构造 write_summary 所需最小 check/rec 结构（无 Carla/无真实数据）。"""
    root = tmp_path / "q2root"
    out = tmp_path / "q2out"
    root.mkdir()
    out.mkdir()
    checks = {
        "geo_count_z_vs_clear": {"rain_hard": 1.23, "fog_dense": -0.45},
        "semantic_geometry_bit_identical":
            {"comparisons": 90, "failures": 0},
        "geo_count_preset_stats": {
            k: {"mean": 3000.0, "std": 12.0}
            for k in ("clear", "rain_hard", "fog_dense")},
        "survivor_intensity_identity": [
            {"preset": "rain_hard", "max_abs_dI": 1.0e-7},
            {"preset": "fog_dense", "max_abs_dI": 2.0e-7}],
    }
    rec = lambda name, kept=0.9, nfalse=0.0, blind=0.0, tr=1.0: {  # noqa: E731
        "condition": name, "frac_surface_kept_mean": kept,
        "n_weather_false_mean": nfalse, "n_near_blind_mean": blind,
        "transmission_mean_mean": tr}
    recs = [rec("clear"), rec("rain_100", .82, 120.0, 4.0, .61),
            rec("snow_100", .70, 260.0, 4.0, .52),
            rec("fog_v6", .35, tr=.08)]
    meta = {"server_version": "0.10.0-fixture", "map": "Town10HD_Opt",
            "vehicle": "vehicle.lincoln.mkz"}
    return write_summary, root, out, checks, recs, meta


def test_missing_negative_control_is_explicit_never_fabricated(tmp_path):
    write_summary, root, out, checks, recs, meta = _summary_fixture(tmp_path)
    write_summary(out, root, checks, recs, meta, {"analysis_wall_s": 0.1})
    text = (out / "SUMMARY.md").read_text(encoding="utf-8")
    # 主实验 z 如实写出
    assert "跨天气 z = +1.23 / -0.45" in text
    # 缺采显式声明（两处：结论行 + 证据行），范围降为三重复
    assert "阴性对照：未采集（本批次不做天气因果证伪）" in text
    assert "阴性对照：未采集（无 control/ 目录" in text
    assert "（三重复）" in text and "（三重复+阴性对照）" not in text
    # 不得出现伪造的对照 z 数值行（主实验行格式为「跨天气 z =」）
    assert "阴性对照（三段物理上全部下发 clear" not in text


def test_present_negative_control_values_are_rendered(tmp_path):
    write_summary, root, out, checks, recs, meta = _summary_fixture(tmp_path)
    ctrl_dir = root / "control" / "analysis"
    ctrl_dir.mkdir(parents=True)
    (ctrl_dir / "invariance_checks.json").write_text(json.dumps({
        "geo_count_z_vs_clear": {"rain_hard": 0.82, "fog_dense": -0.77}}),
        encoding="utf-8")
    write_summary(out, root, checks, recs, meta, {"analysis_wall_s": 0.1})
    text = (out / "SUMMARY.md").read_text(encoding="utf-8")
    assert "阴性对照（三段物理上全部下发 clear，仅段位置不同）z = " \
           "+0.82 / -0.77" in text
    assert "（三重复+阴性对照）" in text
    assert "未采集" not in text


# ---------------------------------------------------------------------------
# S-7：analyze_q2 缺帧/缺键显式错误（兼容旧 except KeyError 调用面）
# ---------------------------------------------------------------------------

def test_s7_load_frame_missing_file_and_key(tmp_path):
    root = tmp_path / "collect"
    # 文件缺失
    with pytest.raises(FrameDataError) as ei:
        load_frame(root, 1, "clear", 0)
    msg = str(ei.value)
    assert "frames_rep1.npz" in msg and "rep=1" in msg and "frame=0" in msg
    assert isinstance(ei.value, KeyError)  # 兼容旧 except KeyError 调用面

    # 文件在但键缺失：错误列出槽位现存键与总键数，不再裸抛键名
    d = root / "collect_rep1"
    d.mkdir(parents=True)
    np.savez(d / "frames_rep1.npz",
             **{"clear__0__geo": np.zeros(2),
                "clear__0__sem_xyz": np.zeros(2)})  # 缺 sem_tag
    with pytest.raises(FrameDataError) as ei2:
        load_frame(root, 1, "clear", 0)
    m2 = str(ei2.value)
    assert "clear__0__sem_tag" in m2
    assert "clear__0__geo" in m2 and "全部键数=2" in m2
