"""TEST43-P: v6x wall-clock conversion (barMinutes/refMinutes) and TIMING_BRITTLENESS fill delay."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from t43 import v6x  # noqa: E402


def test_wc_conversion():
    assert v6x._wc(88, 3, 3) == 88
    assert v6x._wc(88, 3, 5) == 53          # 264 minutes on 5m bars (52.8 -> 53)
    assert v6x._wc(8, 3, 5) == 5            # 24 minutes -> 4.8 -> 5 bars
    assert v6x._wc(0, 3, 5) == 0            # disabled stays disabled
    assert v6x._wc(1, 3, 15) == 1           # never rounds a live window to zero


def test_defaults_are_native_3m():
    p = v6x.make_params()
    assert p[v6x.P["barMinutes"]] == 3 and p[v6x.P["refMinutes"]] == 3 and p[v6x.P["fillDelayBars"]] == 0
