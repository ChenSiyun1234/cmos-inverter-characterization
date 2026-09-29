"""Tests for analyze.py on synthetic transfer curves with known answers."""

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import analyze as az  # noqa: E402

VDD = 5.0
CODE = 0.01974  # scope code size in the lab captures (V)


# --------------------------------------------------------------------------
# Synthetic curves


def tanh_vtc(vin, center=2.5, gain=4.0):
    """Smooth inverter-like curve that falls from VDD to 0 around `center`."""
    return VDD / 2 * (1 - np.tanh(gain * (np.asarray(vin, float) - center)))


def tanh_unity_points(center, gain):
    """Exact inputs where the tanh curve has slope -1."""
    u = np.arccosh(np.sqrt(VDD / 2 * gain)) / gain
    return center - u, center + u


def tanh_vm(center, gain):
    """Exact input where the tanh curve crosses Vout = Vin (bisection)."""
    lo, hi = 0.0, VDD
    for _ in range(100):
        mid = (lo + hi) / 2
        if tanh_vtc(mid, center, gain) > mid:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def quantize(v, code=CODE):
    return np.round(np.asarray(v, float) / code) * code


def lab_levels(fine_lo=2.2, fine_hi=3.2):
    """Step plan like the baseline capture: 0.5 V steps far out, 50 mV steps near the switch."""
    coarse_lo = np.arange(0.0, fine_lo - 0.01, 0.5)
    fine = np.arange(fine_lo, fine_hi + 1e-9, 0.05)
    coarse_hi = np.arange(3.5, VDD + 1e-9, 0.5)
    return np.r_[coarse_lo, fine, coarse_hi]


def staircase_record(levels, center=2.5, gain=4.0, dwell=100, repeats=3, start_step=0):
    """Fake 1 kS/s scope record of a repeating staircase, quantized like the ADALM2000."""
    seq = np.tile(levels, repeats)[start_step:]
    vin = np.repeat(seq, dwell)
    return quantize(vin), quantize(tanh_vtc(vin, center, gain))


def write_scopy_csv(path, ch1, ch2, rate=1000):
    """Write a file laid out like a Scopy oscilloscope export."""
    header = [
        b";Scopy version,3d4c582",
        # The date line in the real files is in the PC locale, not UTF-8.
        b";Exported on,\xd0\xc7\xc6\xda\xcb\xc4 \xce\xe5\xd4\xc2 07/05/2026",
        b";Device,M2K",
        f";Nr of samples,{len(ch1)}".encode(),
        f";Sample rate,{rate}".encode(),
        b";Tool,Oscilloscope",
        b";Additional Information,",
        b"Sample,Time(S),CH1(V),CH2(V)",
    ]
    t0 = -len(ch1) / rate
    rows = [f"{i},{t0 + i / rate:g},{a:.6g},{b:.6g}".encode() for i, (a, b) in enumerate(zip(ch1, ch2))]
    path.write_bytes(b"\n".join(header + rows) + b"\n")


# --------------------------------------------------------------------------
# Steps and sweeps


def test_find_steps_recovers_every_level():
    levels = lab_levels()
    vin, vout = staircase_record(levels, repeats=2)
    steps = az.find_steps(vin, vout, rate=1000)
    assert len(steps) == 2 * len(levels)
    assert np.allclose([s.vin for s in steps], quantize(np.tile(levels, 2)), atol=1e-9)
    assert np.allclose([s.vout for s in steps], quantize(tanh_vtc(np.tile(levels, 2))), atol=1e-9)


def test_find_steps_ignores_flicker_and_spikes():
    levels = np.array([0.0, 0.5, 1.0, 1.05, 1.10, 2.0])
    vin = np.repeat(levels, 100)
    rng = np.random.default_rng(1)
    measured = quantize(vin) + rng.choice([-1, 0, 1], size=vin.size, p=[0.1, 0.8, 0.1]) * CODE
    measured[100::100] += 0.3  # one-sample overshoot at each edge
    measured[250] -= 0.2  # lone spike inside a step
    steps = az.find_steps(measured, VDD - vin, rate=1000)
    assert len(steps) == len(levels)
    assert np.allclose([s.vin for s in steps], quantize(levels), atol=CODE)


def test_only_full_sweeps_are_kept():
    levels = lab_levels()
    vin, vout = staircase_record(levels, repeats=3, start_step=12)  # starts mid-sweep
    steps = az.find_steps(vin, vout, rate=1000)
    assert len(az.split_sweeps(steps)) == 3
    full = az.full_sweeps(steps)
    assert len(full) == 2
    assert all(len(sweep) == len(levels) for sweep in full)


# --------------------------------------------------------------------------
# Transfer-curve points


def test_switching_point_of_a_symmetric_curve():
    x = np.arange(0, 5.0001, 0.05)
    assert az.switching_point(x, tanh_vtc(x)) == pytest.approx(2.5, abs=1e-9)


@pytest.mark.parametrize("center,gain", [(2.3, 3.0), (2.7, 6.0)])
def test_switching_point_of_shifted_curves(center, gain):
    x = np.arange(0, 5.0001, 0.01)
    assert az.switching_point(x, tanh_vtc(x, center, gain)) == pytest.approx(tanh_vm(center, gain), abs=2e-3)


@pytest.mark.parametrize("center,gain", [(2.5, 4.0), (2.3, 3.0), (2.7, 6.0)])
def test_unity_gain_points_on_fine_clean_steps(center, gain):
    x = np.arange(0, 5.0001, 0.01)
    curve = az.analyze_curve(x, tanh_vtc(x, center, gain))
    vil, vih = tanh_unity_points(center, gain)
    assert curve.vil == pytest.approx(vil, abs=0.005)
    assert curve.vih == pytest.approx(vih, abs=0.005)


@pytest.mark.parametrize("offset", [0.0, 0.007, 0.013, 0.021, 0.034, 0.042])
@pytest.mark.parametrize("center,gain", [(2.5, 4.0), (2.4, 2.5), (2.7, 6.0)])
def test_50_mV_steps_with_the_lab_adc_code(center, gain, offset):
    """Same step size and scope code size as the lab captures."""
    x = np.arange(0, VDD + 1e-9, 0.05) + offset
    x = x[x <= VDD]
    curve = az.analyze_curve(quantize(x), quantize(tanh_vtc(x, center, gain)))
    vil, vih = tanh_unity_points(center, gain)
    assert curve.vm == pytest.approx(tanh_vm(center, gain), abs=0.01)
    assert curve.vil == pytest.approx(vil, abs=0.04)
    assert curve.vih == pytest.approx(vih, abs=0.04)
    assert curve.vil_step < az.WIDE_STEP
    assert curve.vih_step < az.WIDE_STEP


def test_point_in_the_wide_steps_is_flagged():
    center, gain = 2.4, 2.5  # VIL near 1.77 V, where this plan steps by 0.5 V
    levels = lab_levels(fine_lo=2.2)
    curve = az.analyze_curve(levels, tanh_vtc(levels, center, gain))
    assert tanh_unity_points(center, gain)[0] < 2.0
    assert curve.vil_step > az.WIDE_STEP
    assert curve.vih_step < az.WIDE_STEP


def test_levels_and_margins_from_steps_in_any_order():
    x = np.arange(0, 5.0001, 0.05)
    y = 0.05 + 4.9 / 2 * (1 - np.tanh(4.0 * (x - 2.5)))
    curve = az.analyze_curve(x[::-1], y[::-1])  # a falling sweep gives the same answer
    u = np.arccosh(np.sqrt(4.9 / 2 * 4.0)) / 4.0  # slope -1 points of this curve
    vil, vih = 2.5 - u, 2.5 + u
    assert curve.voh == pytest.approx(y[0])
    assert curve.vol == pytest.approx(y[-1])
    assert curve.vil == pytest.approx(vil, abs=0.01)
    assert curve.vih == pytest.approx(vih, abs=0.01)
    assert curve.nml == pytest.approx(curve.vil - curve.vol)
    assert curve.nmh == pytest.approx(curve.voh - curve.vih)


def test_curve_without_a_steep_region_gives_nan():
    x = np.linspace(0, 5, 21)
    curve = az.analyze_curve(x, 5 - 0.5 * x)  # slope -0.5 everywhere
    assert np.isnan(curve.vil) and np.isnan(curve.vih)


# --------------------------------------------------------------------------
# Files


def test_load_capture_reads_a_scopy_export(tmp_path):
    path = tmp_path / "capture.csv"
    write_scopy_csv(path, [0.0, 0.5, 1.0], [5.0, 4.9, 4.8])
    cap = az.load_capture(path)
    assert cap.meta["Device"] == "M2K"
    assert cap.rate == 1000
    assert np.allclose(cap.vin, [0.0, 0.5, 1.0])
    assert np.allclose(cap.vout, [5.0, 4.9, 4.8])
    assert np.allclose(np.diff(cap.time), 0.001)


def test_end_to_end_on_a_synthetic_capture(tmp_path):
    center, gain = 2.4, 4.0
    vin, vout = staircase_record(lab_levels(), center, gain, repeats=3, start_step=7)
    path = tmp_path / "Lab3-Part2.4-synthetic.csv"
    write_scopy_csv(path, vin, vout)
    result = az.analyze_capture(az.load_capture(path))
    vil, vih = tanh_unity_points(center, gain)
    assert result.key == "baseline"
    assert len(result.curves) == 2
    assert result.value("vm") == pytest.approx(tanh_vm(center, gain), abs=0.01)
    assert result.value("vih") == pytest.approx(vih, abs=0.04)
    assert result.value("vil") == pytest.approx(vil, abs=0.1)
    assert result.wide("vil") and not result.wide("vih")


def test_lab_captures_split_into_100_ms_steps():
    for path in sorted((ROOT / "data").glob("*.csv")):
        cap = az.load_capture(path)
        steps = az.find_steps(cap.vin, cap.vout, cap.rate)
        lengths = np.array([s.stop - s.start for s in steps[1:-1]])  # ends are cut by the capture window
        assert np.all(np.abs(lengths - 90) <= 10), path.name  # 100 ms minus 5 ms at each end


def test_readme_table_matches_the_data():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    block = az.extract_block(readme)
    assert block is not None, "README has no results block"
    results = az.analyze_files(sorted((ROOT / "data").glob("*.csv")))
    assert block == az.results_markdown(results, az.load_ltspice())
