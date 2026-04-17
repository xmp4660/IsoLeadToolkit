"""Tests for geochem model age line helper functions."""

from __future__ import annotations

import numpy as np

from visualization.plotting.geochem import model_age_lines


class _FakeGeochemistry:
    @staticmethod
    def calculate_two_stage_age(_pb206, _pb207, params=None):
        return np.array([100.0, np.nan], dtype=float)

    @staticmethod
    def calculate_single_stage_age(_pb206, _pb207, params=None):
        return np.array([200.0, 300.0], dtype=float)


def test_resolve_model_age_single_stage_uses_cdt_and_t2(monkeypatch) -> None:
    monkeypatch.setattr(model_age_lines, "_lazy_import_geochemistry", lambda: (_FakeGeochemistry(), None))

    t_model, t1_override = model_age_lines._resolve_model_age(
        pb206=np.array([1.0, 2.0], dtype=float),
        pb207=np.array([3.0, 4.0], dtype=float),
        params={"Tsec": 0.0, "T2": 4_500_000_000.0, "T1": 4_430_000_000.0},
    )

    np.testing.assert_allclose(t_model, np.array([200.0, 300.0], dtype=float), rtol=0.0, atol=1e-12)
    assert t1_override == 4_500_000_000.0


def test_resolve_model_age_two_stage_prefers_finite_sk_age(monkeypatch) -> None:
    monkeypatch.setattr(model_age_lines, "_lazy_import_geochemistry", lambda: (_FakeGeochemistry(), None))

    t_model, t1_override = model_age_lines._resolve_model_age(
        pb206=np.array([1.0, 2.0], dtype=float),
        pb207=np.array([3.0, 4.0], dtype=float),
        params={"Tsec": 3_700_000_000.0, "T2": 4_500_000_000.0, "T1": 4_430_000_000.0},
    )

    np.testing.assert_allclose(t_model, np.array([100.0, 300.0], dtype=float), rtol=0.0, atol=1e-12)
    assert t1_override == 3_700_000_000.0
