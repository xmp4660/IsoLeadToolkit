"""Tests for data.geochemistry.engine parameter management helpers."""

from __future__ import annotations

import pytest

from data.geochemistry.engine import (
    E1_CUMMING_RICHARDS,
    E2_CUMMING_RICHARDS,
    GeochemistryEngine,
    PRESET_MODELS,
    T_SK_STAGE2,
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
