"""Smoke tests for image export use cases."""

from application.use_cases.export_image import (
    DEFAULT_EXPORT_HEIGHT_RATIO,
    MIN_EXPORT_DPI,
    build_image_export_profile,
    normalize_export_target,
    resolve_image_save_options,
)


def test_normalize_export_target_appends_supported_extension() -> None:
    normalized_path, ext = normalize_export_target("figure_output", "svg")

    assert normalized_path.endswith(".svg")
    assert ext == "svg"


def test_normalize_export_target_rewrites_unsupported_extension() -> None:
    normalized_path, ext = normalize_export_target("figure.badext", "png")

    assert normalized_path.endswith(".png")
    assert ext == "png"


def test_resolve_image_save_options_applies_bounds() -> None:
    profile = build_image_export_profile("science_single")

    options = resolve_image_save_options(
        profile=profile,
        dpi_override=50,
        bbox_tight=True,
        transparent=True,
        pad_inches=-0.5,
        default_dpi=300,
    )

    assert options["dpi"] == MIN_EXPORT_DPI
    assert options["bbox_tight"] is True
    assert options["transparent"] is True
    assert options["pad_inches"] == 0.0


def test_export_profiles_use_named_default_height_ratio() -> None:
    science = build_image_export_profile("science_single")
    ieee = build_image_export_profile("ieee_single")

    assert science["height_ratio"] == DEFAULT_EXPORT_HEIGHT_RATIO
    assert ieee["height_ratio"] == DEFAULT_EXPORT_HEIGHT_RATIO
