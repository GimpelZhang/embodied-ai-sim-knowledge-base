#!/usr/bin/env python3
"""Q2 物理光学天气材质模型的零付费确定性测试（不依赖 Carla/容器）。

Task0b 从 sim-praxis tests/milestone1/test_q2_optics_model.py 逐断言迁入；
导入面由 conftest.py 的平目录夹具桥接，断言一字未放水。
"""
from __future__ import annotations

import numpy as np
import pytest

from optics_model import (
    QBACK_DEFAULT,
    OpticsParams,
    WeatherSpec,
    apply_optics,
    extinction_coefficients,
)
import optics_model as om


def _frame(n: int = 400, seed: int = 0):
    """沿 +x 方向 n 条射线、距离 1–50m 的合成表面点云。"""
    rng = np.random.default_rng(seed)
    r = rng.uniform(1.0, 50.0, size=n)
    pts = np.stack([r, np.zeros(n), np.zeros(n)], axis=1)
    inten = rng.uniform(0.2, 1.0, size=n)
    tags = np.array(["road"] * n)
    return pts, inten, tags


def test_clear_is_identity():
    pts, inten, tags = _frame()
    rng = np.random.default_rng(1)
    out = apply_optics(
        pts, inten, WeatherSpec("clear"), rng, surface_tag=tags,
        params=OpticsParams(shot_noise_rel=0.0, detect_i_min=0.0))
    assert out["alpha_per_m"] == 0.0 and out["beta_pi_per_m_sr"] == 0.0
    assert out["n_weather_false"] == 0
    assert np.array_equal(out["points"], pts)
    assert np.allclose(out["intensity"], inten)
    assert out["transmission_mean"] == 1.0


def test_extinction_monotonic_rain_and_snow():
    alphas = [extinction_coefficients(WeatherSpec("rain", rate_mmh=r))["alpha"]
              for r in (2.5, 10, 50, 100)]
    assert alphas == sorted(alphas) and alphas[0] > 0
    # 同水当量下雪的截面更大（大而密的雪花谱）
    a_rain = extinction_coefficients(WeatherSpec("rain", rate_mmh=10))["alpha"]
    a_snow = extinction_coefficients(WeatherSpec("snow", rate_mmh=10))["alpha"]
    assert a_snow > a_rain


def test_rain_dsd_matches_empirical_band():
    # Rasshofer 2011: a_R=1.075·R^0.68 dB/km；滴谱积分（Qext=2）须在 ×1.5 内
    for rate in (2.5, 10, 50, 100):
        a = extinction_coefficients(WeatherSpec("rain", rate_mmh=rate))["alpha"]
        db_km = 4.343 * a * 1000.0
        emp = om.RAIN_EMP_K * rate ** om.RAIN_EMP_EXP
        assert 0.66 * emp <= db_km <= om.RAIN_DSD_VS_EMPIRIC_TOL * emp


def test_fog_koschmieder_band():
    a = extinction_coefficients(WeatherSpec("fog", visibility_m=50.0))["alpha"]
    assert 50.0 / 1000.0 <= a <= 120.0 / 1000.0
    assert abs(a - 3.912 / 50.0) < 1e-12


def test_attenuation_and_detection_drop():
    pts, inten, _ = _frame()
    rng = np.random.default_rng(2)
    dense_fog = WeatherSpec("fog", visibility_m=6.0, wetness=True)
    out = apply_optics(pts, inten, dense_fog, rng,
                       params=OpticsParams(shot_noise_rel=0.0))
    assert out["transmission_mean"] < 0.1
    assert out["detect_drop_mask"].sum() > 0
    assert out["n_surface_kept"] < out["n_input"]


def test_wet_material_darkens_road():
    pts, inten, tags = _frame(n=10)
    dry = apply_optics(pts, inten, WeatherSpec("clear"), np.random.default_rng(3),
                       surface_tag=tags,
                       params=OpticsParams(shot_noise_rel=0.0, detect_i_min=0.0))
    rain = WeatherSpec("rain", rate_mmh=2.5, wetness=True)
    wet = apply_optics(pts, inten, rain, np.random.default_rng(3),
                       surface_tag=tags,
                       params=OpticsParams(shot_noise_rel=0.0, detect_i_min=0.0))
    assert wet["intensity"].mean() < dry["intensity"].mean()


def test_weather_false_returns_scale_with_backscatter():
    # 距离门积分模型：β 大（强降水）时近场 bloom 命中数单调增加
    pts, _, _ = _frame(n=4000)
    inten = np.full(4000, 0.9)
    quiet = OpticsParams(shot_noise_rel=0.0, detect_i_min=0.0)
    n50 = apply_optics(pts, inten, WeatherSpec("rain", rate_mmh=50),
                       np.random.default_rng(4), params=quiet)["n_weather_false"]
    n100 = apply_optics(pts, inten, WeatherSpec("rain", rate_mmh=100),
                        np.random.default_rng(4), params=quiet)["n_weather_false"]
    assert n100 > n50 > 0


def test_weather_points_are_labeled_separately():
    pts, inten, _ = _frame(n=4000)
    quiet = OpticsParams(shot_noise_rel=0.0, detect_i_min=0.0)
    out = apply_optics(pts, inten, WeatherSpec("snow", rate_mmh=50),
                       np.random.default_rng(5), params=quiet)
    assert out["is_weather"].sum() > 0
    assert set(out["surface_tag"][out["is_weather"]]) == {"weather"}
    assert set(out["surface_tag"][~out["is_weather"]]) == {"surface"}


def test_determinism_same_seed():
    pts, inten, tags = _frame()
    w = WeatherSpec("rain", rate_mmh=80, wetness=True)
    a = apply_optics(pts, inten, w, np.random.default_rng(7), surface_tag=tags)
    b = apply_optics(pts, inten, w, np.random.default_rng(7), surface_tag=tags)
    np.testing.assert_array_equal(a["points"], b["points"])
    np.testing.assert_array_equal(a["intensity"], b["intensity"])


def test_invalid_weather_rejected():
    with pytest.raises(ValueError):
        WeatherSpec("hail")
    with pytest.raises(ValueError):
        WeatherSpec("rain", rate_mmh=-1)


# ---------------------------------------------------------------------------
# L-9：OpticsParams.qback 真正被积分消费；默认值逐位不变，alpha 与 qback 无关
# ---------------------------------------------------------------------------

def test_qback_default_is_unchanged_and_beta_scales_but_alpha_not():
    assert OpticsParams().qback == QBACK_DEFAULT == 0.4
    for w in (WeatherSpec("rain", rate_mmh=25.0),
              WeatherSpec("snow", rate_mmh=25.0),
              WeatherSpec("fog", visibility_m=30.0)):
        base = extinction_coefficients(w)
        explicit_default = extinction_coefficients(w, qback=QBACK_DEFAULT)
        assert base["beta_pi"] == explicit_default["beta_pi"]
        assert base["alpha"] == explicit_default["alpha"] > 0.0
        hi = extinction_coefficients(w, qback=0.8)
        lo = extinction_coefficients(w, qback=0.2)
        zero = extinction_coefficients(w, qback=0.0)
        # beta 随 qback 线性（雨/雪滴谱积分；雾 β=α·q/Qext）
        assert hi["beta_pi"] == pytest.approx(4.0 * lo["beta_pi"])
        assert zero["beta_pi"] == 0.0
        # 消光通道只认 Qext=2，任何 qback 下 alpha 逐位相同
        for c in (hi, lo, zero):
            assert c["alpha"] == base["alpha"]


def test_qback_consumed_by_apply_optics_integration():
    pts, inten, _ = _frame(n=4000)
    inten = np.full(4000, 0.9)
    rain = WeatherSpec("rain", rate_mmh=50.0)
    quiet = lambda qb: OpticsParams(  # noqa: E731 - 测试局部短件
        qback=qb, shot_noise_rel=0.0, detect_i_min=0.0)

    default_out = apply_optics(pts, inten, rain, np.random.default_rng(11),
                               params=quiet(QBACK_DEFAULT))
    # qback=0：天气注入概率恒 0 → 零伪回波；alpha/透射不受影响
    zero_out = apply_optics(pts, inten, rain, np.random.default_rng(11),
                            params=quiet(0.0))
    assert zero_out["n_weather_false"] == 0
    assert default_out["n_weather_false"] > 0
    assert zero_out["alpha_per_m"] == default_out["alpha_per_m"] > 0.0
    assert zero_out["beta_pi_per_m_sr"] == 0.0
    assert zero_out["transmission_mean"] == default_out["transmission_mean"]

    # qback=1.0（默认的 2.5 倍）：首帧标量 beta 精确 2.5 倍，伪回波更多，
    # alpha/表面透射仍然逐位不变
    hi_out = apply_optics(pts, inten, rain, np.random.default_rng(11),
                          params=quiet(1.0))
    assert hi_out["beta_pi_per_m_sr"] == pytest.approx(
        2.5 * default_out["beta_pi_per_m_sr"])
    assert hi_out["alpha_per_m"] == default_out["alpha_per_m"]
    assert hi_out["transmission_mean"] == default_out["transmission_mean"]
    assert hi_out["n_weather_false"] > default_out["n_weather_false"]


def test_default_params_reproduce_historical_numbers():
    """默认 OpticsParams 必须与显式 qback=QBACK_DEFAULT 全帧一致（结论不变）。"""
    pts, inten, tags = _frame(n=2000, seed=3)
    w = WeatherSpec("snow", rate_mmh=40.0, wetness=True)
    a = apply_optics(pts, inten, w, np.random.default_rng(21),
                     surface_tag=tags)  # 内置默认 OpticsParams()
    b = apply_optics(pts, inten, w, np.random.default_rng(21),
                     surface_tag=tags,
                     params=OpticsParams(qback=QBACK_DEFAULT))
    np.testing.assert_array_equal(a["points"], b["points"])
    np.testing.assert_array_equal(a["intensity"], b["intensity"])
    assert a["beta_pi_per_m_sr"] == b["beta_pi_per_m_sr"]
    assert a["alpha_per_m"] == b["alpha_per_m"]
    assert a["n_weather_false"] == b["n_weather_false"]
