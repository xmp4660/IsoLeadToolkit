"""Smoke tests for selection and tooltip use cases."""

from application.use_cases.selection_interaction import SelectionInteractionUseCase
from application.use_cases.tooltip_content import TooltipContentUseCase


def test_selection_rectangle_and_toggle_plan() -> None:
    use_case = SelectionInteractionUseCase()
    coordinates = {
        1: (0.0, 0.0),
        2: (1.0, 1.0),
        3: (3.0, 3.0),
    }

    selected = use_case.rectangle_indices(
        coordinates,
        x_min=-0.1,
        x_max=1.5,
        y_min=-0.1,
        y_max=1.5,
    )
    plan = use_case.plan_toggle({1}, selected)

    assert selected == [1, 2]
    assert plan.action == "add"
    assert plan.indices == [1, 2]


def test_tooltip_content_fallback_to_id() -> None:
    use_case = TooltipContentUseCase()
    row = {"Name": "Demo"}

    text = use_case.build_text(
        row=row,
        df_columns=["Name"],
        sample_idx=42,
        tooltip_columns=["MissingColumn"],
        selected=True,
        selected_status_label="Selected",
    )

    assert "ID: 42" in text
    assert "Selected" in text
