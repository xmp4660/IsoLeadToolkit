"""Dimensionality reduction visualization and plotting API."""

from .analysis_qt import (
    show_scree_plot,
    show_pca_loadings,
    show_embedding_correlation,
    show_shepard_diagram,
    show_correlation_heatmap,
)
from .style import refresh_plot_style

from .core import (
    _lazy_import_umap,
    _lazy_import_mplot3d,
    _lazy_import_ellipse,
    _ensure_axes,
    get_umap_embedding,
    get_tsne_embedding,
    get_pca_embedding,
    get_robust_pca_embedding,
    get_embedding,
    _build_group_palette,
    _get_subset_dataframe,
    _get_pb_columns,
    _find_age_column,
)
from .geo import (
    _resolve_isochron_errors,
    _draw_model_curves,
    _build_isochron_label,
    _draw_isochron_overlays,
    _draw_selected_isochron,
    _label_angle_for_slope,
    _position_paleo_label,
    _draw_paleoisochrons,
    refresh_paleoisochron_labels,
    _draw_model_age_lines,
    _draw_model_age_lines_86,
    _draw_equation_overlays,
)
from .ternary import (
    _apply_ternary_stretch,
    calculate_auto_ternary_factors,
)
from .render import (
    _notify_legend_panel,
    _build_legend_proxies,
    plot_embedding,
    plot_umap,
    plot_2d_data,
    plot_3d_data,
)

__all__ = [
    'get_umap_embedding',
    'get_tsne_embedding',
    'get_pca_embedding',
    'get_robust_pca_embedding',
    'get_embedding',
    'plot_embedding',
    'plot_umap',
    'plot_2d_data',
    'plot_3d_data',
    'refresh_plot_style',
    'show_scree_plot',
    'show_pca_loadings',
    'show_embedding_correlation',
    'show_shepard_diagram',
    'show_correlation_heatmap',
    'calculate_auto_ternary_factors',
]

