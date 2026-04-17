"""Tests for visualization.plotting.data lazy import helpers."""

from __future__ import annotations

from visualization.plotting import data as plotting_data


def test_lazy_import_geochemistry_loads_once_and_reuses_cache() -> None:
    snapshot = {
        "module": plotting_data._geochemistry,
        "calculate": plotting_data._calculate_all_parameters,
        "checked": plotting_data._geochem_checked,
    }
    try:
        plotting_data._geochemistry = None
        plotting_data._calculate_all_parameters = None
        plotting_data._geochem_checked = False

        module_1, calc_1 = plotting_data._lazy_import_geochemistry()
        module_2, calc_2 = plotting_data._lazy_import_geochemistry()

        assert module_1 is not None
        assert callable(calc_1)
        assert plotting_data._geochem_checked is True
        assert module_2 is module_1
        assert calc_2 is calc_1
    finally:
        plotting_data._geochemistry = snapshot["module"]
        plotting_data._calculate_all_parameters = snapshot["calculate"]
        plotting_data._geochem_checked = bool(snapshot["checked"])
