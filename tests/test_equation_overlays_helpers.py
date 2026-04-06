"""Tests for equation overlay expression evaluation helpers."""

from __future__ import annotations

import numpy as np
import pytest

from visualization.plotting.geochem.equation_overlays import _safe_eval_expression


def test_safe_eval_expression_supports_basic_arithmetic_and_where() -> None:
    x_vals = np.array([-2.0, -1.0, 0.0, 1.0, 2.0], dtype=float)

    linear = _safe_eval_expression("x * 2 + 1", x_vals)
    conditional = _safe_eval_expression("where(x > 0, x, -x)", x_vals)

    np.testing.assert_allclose(linear, np.array([-3.0, -1.0, 1.0, 3.0, 5.0], dtype=float), rtol=0.0, atol=1e-12)
    np.testing.assert_allclose(conditional, np.array([2.0, 1.0, -0.0, 1.0, 2.0], dtype=float), rtol=0.0, atol=1e-12)


def test_safe_eval_expression_rejects_unknown_symbols() -> None:
    x_vals = np.array([1.0, 2.0], dtype=float)

    with pytest.raises(ValueError):
        _safe_eval_expression("y + 1", x_vals)

    with pytest.raises(ValueError):
        _safe_eval_expression("__import__('os').system('echo bad')", x_vals)
