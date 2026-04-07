"""Tests for data.geochemistry.engine parameter management helpers."""

from __future__ import annotations

import numpy as np
import pytest

from data.geochemistry.engine import (
    E1_CUMMING_RICHARDS,
    E2_CUMMING_RICHARDS,
    GeochemistryEngine,
    PRESET_MODELS,
    T_SK_STAGE2,
    _exp_evolution_term,
    _is_zero_like,
)


def test_get_available_models_matches_presets() -> None:
    ge_engine = GeochemistryEngine()

    assert ge_engine.get_available_models() == list(PRESET_MODELS.keys())


def test_load_preset_returns_false_for_unknown_model() -> None:
    ge_engine = GeochemistryEngine()
    baseline = ge_engine.get_parameters()

    assert ge_engine.load_preset("__unknown_model__") is False
    assert ge_engine.get_parameters() == baseline
    assert ge_engine.current_model_name == "Stacey & Kramers (2nd Stage)"


def test_update_parameters_ignores_unknown_and_invalid_values() -> None:
    ge_engine = GeochemistryEngine()

    ge_engine.update_parameters(
        {
            "age_model": "single_stage",
            "mu_M": "10.5",
            "T1": "invalid",
            "unknown_key": 123,
        }
    )

    params = ge_engine.get_parameters()
    assert params["age_model"] == "single_stage"
    assert params["mu_M"] == pytest.approx(10.5)
    assert params["T1"] == pytest.approx(T_SK_STAGE2)
    assert "unknown_key" not in params
    assert params["v_M"] == pytest.approx(float(params["mu_M"]) * float(params["U_ratio"]))


def test_load_cumming_richards_preset_uses_named_evolution_constants() -> None:
    ge_engine = GeochemistryEngine()

    assert ge_engine.load_preset("Cumming & Richards (Model III)") is True

    params = ge_engine.get_parameters()
    assert params["E1"] == pytest.approx(E1_CUMMING_RICHARDS)
    assert params["E2"] == pytest.approx(E2_CUMMING_RICHARDS)


def test_is_zero_like_treats_zero_as_zero_like() -> None:
    assert _is_zero_like(0.0) is True


def test_exp_evolution_term_zero_uses_plain_exponential() -> None:
    lmbda = 1.55125e-10
    t_years = np.array([1.0e6, 2.5e6, 4.0e6], dtype=float)

    result = _exp_evolution_term(lmbda, t_years, E=0.0)
    expected = np.exp(lmbda * t_years)

    np.testing.assert_allclose(result, expected)


def test_exp_evolution_term_nonzero_applies_evolution_factor() -> None:
    lmbda = 9.8485e-10
    t_years = np.array([2.0e6, 3.0e6], dtype=float)
    e_value = 0.145

    result = _exp_evolution_term(lmbda, t_years, E=e_value)
    expected = np.exp(lmbda * t_years) * (1.0 - e_value * (t_years - (1.0 / lmbda)))

    np.testing.assert_allclose(result, expected)
