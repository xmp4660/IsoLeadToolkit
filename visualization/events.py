"""Event handlers for user interactions (hover, click, legend)."""
from __future__ import annotations

import logging
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import scipy.stats
from matplotlib.patches import Ellipse
from matplotlib.path import Path
from matplotlib.widgets import RectangleSelector, LassoSelector

from application import RenderPlotUseCase
from core import app_state, state_gateway, translate
from visualization.plotting.isochron import resolve_isochron_errors as _resolve_isochron_errors

logger = logging.getLogger(__name__)

# Minimum box size to register a rectangle selection (data units)
_SELECTION_MIN_SPAN = 1e-9
# Maximum distance (data units) for hover nearest-neighbor lookup
_HOVER_DISTANCE_THRESHOLD = 0.15
_ASYNC_EMBEDDING_ALGORITHMS = {'UMAP', 'tSNE', 'PCA', 'RobustPCA'}


def _data_state() -> Any:
    """Return layered data state when available, otherwise fallback to app_state."""
    return getattr(app_state, 'data', app_state)


def _df_global() -> Any:
    return getattr(_data_state(), 'df_global', app_state.df_global)


def _data_cols() -> list[str]:
    return getattr(_data_state(), 'data_cols', app_state.data_cols)


def _group_cols() -> list[str]:
    return getattr(_data_state(), 'group_cols', app_state.group_cols)

def draw_confidence_ellipse(x, y, ax, confidence: float = 0.95, facecolor: str = 'none', **kwargs) -> Ellipse | None:
    """
    Create a plot of the covariance confidence ellipse of *x* and *y*.
    confidence: float, e.g. 0.95 for 95% confidence interval
    """
    if x.size < 2 or y.size < 2:
        return None

    # Calculate n_std based on confidence level for 2D (Chi-squared with 2 DoF)
    # ppf is the inverse of cdf
    chi2_val = scipy.stats.chi2.ppf(confidence, df=2)
    n_std = np.sqrt(chi2_val)

    cov = np.cov(x, y)
    if not np.all(np.isfinite(cov)):
        return None

    var_x = cov[0, 0]
    var_y = cov[1, 1]
    if var_x <= 0 or var_y <= 0:
        return None

    pearson = cov[0, 1] / np.sqrt(var_x * var_y)
    pearson = float(np.clip(pearson, -1.0, 1.0))
    
    ell_radius_x = np.sqrt(1 + pearson)
    ell_radius_y = np.sqrt(1 - pearson)
    
    ellipse = Ellipse((0, 0), width=ell_radius_x * 2, height=ell_radius_y * 2,
                      facecolor=facecolor, **kwargs)

    scale_x = np.sqrt(cov[0, 0]) * n_std
    mean_x = np.mean(x)
    scale_y = np.sqrt(cov[1, 1]) * n_std
    mean_y = np.mean(y)

    theta = 0.5 * np.arctan2(2 * cov[0, 1], var_x - var_y)
    transf = (
        matplotlib.transforms.Affine2D()
        .rotate(theta)
        .scale(scale_x, scale_y)
        .translate(mean_x, mean_y)
    )

    ellipse.set_transform(transf + ax.transData)
    return ax.add_patch(ellipse)


def _notify_selection_ui():
    """Ask the control panel to refresh selection-related widgets."""
    panel = getattr(app_state, 'control_panel_ref', None)
    if panel is None:
        return

    update_fn = getattr(panel, 'update_selection_controls', None)
    if not callable(update_fn):
        return

    try:
        update_fn()
    except Exception as err:
        logger.warning("Unable to update selection controls: %s", err)


def _refresh_isochron_after_selection() -> None:
    """Recalculate isochron if selection changes in Pb evolution mode."""
    if app_state.render_mode != 'PB_EVOL_76':
        return

    is_active = bool(
        getattr(app_state, 'show_isochrons', False)
        or getattr(app_state, 'selected_isochron_data', None)
        or app_state.selection_tool == 'isochron'
    )
    if not is_active:
        return

    had_selected = app_state.selected_isochron_data is not None
    selected = app_state.selected_indices
    if selected and len(selected) >= 2:
        calculate_selected_isochron()
    else:
        state_gateway.set_selected_isochron_data(None)
        if had_selected:
            state_gateway.set_show_isochrons(True)

    if getattr(app_state, 'show_isochrons', False) or app_state.selected_isochron_data is not None or had_selected:
        try:
            from visualization.events import on_slider_change
            on_slider_change()
        except Exception as err:
            logger.warning("Failed to refresh plot after isochron update: %s", err)


def _disable_rectangle_selector():
    selector = getattr(app_state, 'rectangle_selector', None)
    if selector is None:
        return
    try:
        selector.set_active(False)
    except Exception:
        pass


def _disable_lasso_selector():
    selector = getattr(app_state, 'lasso_selector', None)
    if selector is None:
        return
    try:
        selector.set_active(False)
    except Exception:
        pass


def _ensure_rectangle_selector():
    if not app_state.selection_mode or app_state.render_mode == '3D':
        _disable_rectangle_selector()
        return

    if app_state.selection_tool == 'lasso':
        _disable_rectangle_selector()
        return

    if app_state.ax is None:
        return

    selector = getattr(app_state, 'rectangle_selector', None)

    if selector is not None:
        try:
            # If the selector is bound to a different axes, rebuild it
            if getattr(selector, 'ax', None) is not app_state.ax:
                try:
                    selector.disconnect_events()
                except Exception:
                    pass
                state_gateway.set_rectangle_selector(None)
                selector = None
            else:
                selector.set_active(True)
        except Exception:
            state_gateway.set_rectangle_selector(None)
            selector = None

    if selector is None:
        try:
            selector = RectangleSelector(
                app_state.ax,
                _handle_rectangle_select,
                useblit=True,
                button=[1],
                spancoords='data',
                interactive=False
            )
            state_gateway.set_rectangle_selector(selector)
        except Exception as err:
            logger.warning("Unable to initialize rectangle selector: %s", err)
            state_gateway.set_rectangle_selector(None)


def _ensure_lasso_selector():
    if not app_state.selection_mode or app_state.render_mode == '3D':
        _disable_lasso_selector()
        return

    if app_state.selection_tool != 'lasso':
        _disable_lasso_selector()
        return

    if app_state.ax is None:
        return

    selector = getattr(app_state, 'lasso_selector', None)

    if selector is not None:
        try:
            if getattr(selector, 'ax', None) is not app_state.ax:
                try:
                    selector.disconnect_events()
                except Exception:
                    pass
                state_gateway.set_lasso_selector(None)
                selector = None
            else:
                selector.set_active(True)
        except Exception:
            state_gateway.set_lasso_selector(None)
            selector = None

    if selector is None:
        try:
            selector = LassoSelector(
                app_state.ax,
                _handle_lasso_select,
                button=[1]
            )
            state_gateway.set_lasso_selector(selector)
        except Exception as err:
            logger.warning("Unable to initialize lasso selector: %s", err)
            state_gateway.set_lasso_selector(None)


def _handle_rectangle_select(eclick, erelease):
    try:
        if not app_state.selection_mode or app_state.render_mode == '3D':
            return

        if any(val is None for val in (eclick.xdata, erelease.xdata, eclick.ydata, erelease.ydata)):
            return

        x_min, x_max = sorted([float(eclick.xdata), float(erelease.xdata)])
        y_min, y_max = sorted([float(eclick.ydata), float(erelease.ydata)])

        if abs(x_max - x_min) < _SELECTION_MIN_SPAN or abs(y_max - y_min) < _SELECTION_MIN_SPAN:
            return

        indices_in_box = [
            idx for idx, (x_val, y_val) in app_state.sample_coordinates.items()
            if x_min <= x_val <= x_max and y_min <= y_val <= y_max
        ]

        if not indices_in_box:
            return

        if all(idx in app_state.selected_indices for idx in indices_in_box):
            state_gateway.remove_selected_indices(indices_in_box)
            logger.info("Deselected %d samples via box selection.", len(indices_in_box))
        else:
            state_gateway.add_selected_indices(indices_in_box)
            logger.info("Selected %d samples via box selection.", len(indices_in_box))

        refresh_selection_overlay()
        _notify_selection_ui()
        _refresh_isochron_after_selection()
    except Exception as err:
        logger.warning("Rectangle selection failed: %s", err)


def _handle_lasso_select(vertices):
    try:
        if not app_state.selection_mode or app_state.render_mode == '3D':
            return

        if not vertices:
            return

        path = Path(vertices)

        indices_in_shape = [
            idx for idx, (x_val, y_val) in app_state.sample_coordinates.items()
            if path.contains_point((x_val, y_val))
        ]

        if not indices_in_shape:
            return

        if all(idx in app_state.selected_indices for idx in indices_in_shape):
            state_gateway.remove_selected_indices(indices_in_shape)
            logger.info("Deselected %d samples via custom shape.", len(indices_in_shape))
        else:
            state_gateway.add_selected_indices(indices_in_shape)
            logger.info("Selected %d samples via custom shape.", len(indices_in_shape))

        refresh_selection_overlay()
        _notify_selection_ui()
        _refresh_isochron_after_selection()
    except Exception as err:
        logger.warning("Custom shape selection failed: %s", err)


def refresh_selection_overlay() -> None:
    """Update selection overlay scatter to highlight chosen points."""
    try:
        if app_state.fig is None or app_state.ax is None or app_state.render_mode == '3D':
            if app_state.selection_overlay is not None:
                try:
                    app_state.selection_overlay.remove()
                except Exception:
                    pass
                state_gateway.set_selection_overlay(None)
            _notify_selection_ui()
            return

        if app_state.selection_overlay is not None:
            try:
                app_state.selection_overlay.remove()
            except Exception:
                pass
            state_gateway.set_selection_overlay(None)
        
        # Clear previous selection ellipse
        if app_state.selection_ellipse is not None:
            try:
                app_state.selection_ellipse.remove()
            except Exception:
                pass
            state_gateway.set_selection_ellipse(None)

        valid_indices = [idx for idx in app_state.selected_indices if idx in app_state.sample_coordinates]
        # Do not remove invisible indices from selection state, just don't draw them
        # removed = set(app_state.selected_indices) - set(valid_indices)
        # if removed:
        #     app_state.selected_indices -= removed

        if not valid_indices:
            app_state.fig.canvas.draw_idle()
            _notify_selection_ui()
            return

        # Save current view limits to prevent auto-scaling
        current_xlim = app_state.ax.get_xlim()
        current_ylim = app_state.ax.get_ylim()

        xs = [app_state.sample_coordinates[idx][0] for idx in valid_indices]
        ys = [app_state.sample_coordinates[idx][1] for idx in valid_indices]

        # Only draw highlight rings when a selection tool is active
        if app_state.selection_tool:
            base_marker_size = getattr(app_state, 'plot_marker_size', app_state.point_size)
            highlight_size = max(int(base_marker_size * 1.8), 20)

            overlay = app_state.ax.scatter(
                xs,
                ys,
                s=[highlight_size] * len(xs),
                facecolors='none',
                edgecolors='#f97316',
                linewidths=1.6,
                zorder=6
            )
            state_gateway.set_selection_overlay(overlay)
        
        # Draw confidence ellipse for selected points if enabled
        should_draw_ellipse = app_state.show_ellipses or getattr(app_state, 'draw_selection_ellipse', False)
        
        if should_draw_ellipse and len(xs) >= 3:
            try:
                x_arr = np.array(xs)
                y_arr = np.array(ys)
                # Use a distinct style for the selection ellipse
                ellipse = draw_confidence_ellipse(
                    x_arr, y_arr, app_state.ax, 
                    confidence=app_state.ellipse_confidence,
                    edgecolor='#f97316', linestyle='--', linewidth=2, zorder=5, alpha=0.8
                )
                state_gateway.set_selection_ellipse(ellipse)
                logger.info("Drawn %.0f%% confidence ellipse for %d selected points.", app_state.ellipse_confidence * 100, len(xs))
            except Exception as e:
                logger.warning("Failed to draw selection ellipse: %s", e)

        # Restore view limits
        app_state.ax.set_xlim(current_xlim)
        app_state.ax.set_ylim(current_ylim)

        app_state.fig.canvas.draw_idle()
        _notify_selection_ui()
    except Exception as err:
        logger.warning("Unable to refresh selection overlay: %s", err)


def calculate_selected_isochron() -> None:
    """Calculate isochron age for selected data points."""
    try:
        # Check if we have selected points
        if not app_state.selected_indices or len(app_state.selected_indices) < 2:
            logger.warning("Isochron calculation requires at least 2 selected points.")
            state_gateway.set_selected_isochron_data(None)
            return

        # Check if we're in a Pb evolution mode
        if app_state.render_mode != 'PB_EVOL_76':
            logger.warning("Isochron calculation is only available for Pb evolution plot (PB_EVOL_76).")
            state_gateway.set_selected_isochron_data(None)
            return

        # Determine isochron mode
        mode = 'ISOCHRON1'
        x_col = "206Pb/204Pb"
        y_col = "207Pb/204Pb"

        # Get data
        df = _df_global()
        if df is None or x_col not in df.columns or y_col not in df.columns:
            logger.warning("Required columns %s and %s not found in data.", x_col, y_col)
            state_gateway.set_selected_isochron_data(None)
            return

        # Extract selected points
        selected_list = list(app_state.selected_indices)
        df_selected = df.iloc[selected_list]

        x_data = pd.to_numeric(df_selected[x_col], errors='coerce').values
        y_data = pd.to_numeric(df_selected[y_col], errors='coerce').values

        sx_data, sy_data, rxy_data = _resolve_isochron_errors(df_selected, len(x_data))

        # Remove NaN values
        valid = ~np.isnan(x_data) & ~np.isnan(y_data)
        valid = valid & np.isfinite(sx_data) & np.isfinite(sy_data) & np.isfinite(rxy_data)
        valid = valid & (sx_data > 0) & (sy_data > 0) & (np.abs(rxy_data) <= 1)
        x_data = x_data[valid]
        y_data = y_data[valid]
        sx_data = sx_data[valid]
        sy_data = sy_data[valid]
        rxy_data = rxy_data[valid]

        if len(x_data) < 2:
            logger.warning("Not enough valid data points for isochron calculation.")
            state_gateway.set_selected_isochron_data(None)
            return

        # Perform York regression
        try:
            from data.geochemistry import york_regression, calculate_pbpb_age_from_ratio, engine
            fit = york_regression(x_data, sx_data, y_data, sy_data, rxy_data)
            slope = fit['b']
            intercept = fit['a']
            slope_err = fit['sb']
            intercept_err = fit['sa']
            mswd = fit['mswd']
            p_value = fit['p_value']
        except Exception as e:
            logger.warning("Isochron regression failed: %s", e)
            state_gateway.set_selected_isochron_data(None)
            return

        # Calculate R² value
        y_pred = slope * x_data + intercept
        ss_res = np.sum((y_data - y_pred) ** 2)
        ss_tot = np.sum((y_data - np.mean(y_data)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Calculate age from slope
        try:
            params = engine.get_parameters()
            age_ma, age_err = calculate_pbpb_age_from_ratio(slope, slope_err, params)
        except Exception as e:
            logger.warning("Age calculation failed: %s", e)
            age_ma = 0.0
            age_err = None

        # Store results
        x_min, x_max = np.min(x_data), np.max(x_data)
        span = x_max - x_min
        x_range = [x_min - span * 0.1, x_max + span * 0.1]
        y_range = [slope * x_range[0] + intercept, slope * x_range[1] + intercept]

        state_gateway.set_selected_isochron_data({
            'slope': slope,
            'intercept': intercept,
            'slope_err': slope_err,
            'intercept_err': intercept_err,
            'age': age_ma,
            'age_err': age_err,
            'r_squared': r_squared,
            'mswd': mswd,
            'p_value': p_value,
            'n_points': len(x_data),
            'mode': mode,
            'x_range': x_range,
            'y_range': y_range,
            'x_col': x_col,
            'y_col': y_col
        })

        logger.info("Isochron calculated: Age = %.1f Ma, n = %d, R² = %.4f", age_ma, len(x_data), r_squared)
        logger.info("Slope = %.6f, Intercept = %.6f", slope, intercept)

    except Exception as err:
        logger.warning("Isochron calculation failed: %s", err)
        state_gateway.set_selected_isochron_data(None)


def _resolve_sample_index(event):
    """Attempt to map a Matplotlib event to a sample index."""
    try:
        for sc in app_state.scatter_collections:
            if sc is None:
                continue
            try:
                cont, ind = sc.contains(event)
            except Exception:
                continue
            if not cont or 'ind' not in ind or not ind['ind']:
                continue
            idx_in_scatter = int(ind['ind'][0])
            sample_idx = app_state.artist_to_sample.get((id(sc), idx_in_scatter))
            if sample_idx is not None:
                return sample_idx

        if event is not None and event.xdata is not None and event.ydata is not None:
            x_val = float(event.xdata)
            y_val = float(event.ydata)
            best_idx = None
            best_distance = float('inf')
            for idx, (sx, sy) in app_state.sample_coordinates.items():
                distance = ((x_val - sx) ** 2 + (y_val - sy) ** 2) ** 0.5
                if distance < _HOVER_DISTANCE_THRESHOLD and distance < best_distance:
                    best_distance = distance
                    best_idx = idx
            return best_idx
    except Exception:
        return None
    return None


def toggle_selection_mode(tool_type: str = 'export') -> None:
    """
    Toggle interactive selection mode.
    tool_type: 'export', 'lasso', or 'isochron'
    """
    try:
        # If switching to the same tool that is already active, toggle it off
        if app_state.selection_tool == tool_type:
            new_tool = None
        else:
            new_tool = tool_type

        if new_tool and app_state.render_mode == '3D':
            logger.warning('Selection mode is only available for 2D projections.')
            return

        # Disable existing tool if any
        if app_state.selection_tool:
             _disable_rectangle_selector()
             _disable_lasso_selector()
             # Clear selection only if ellipse is not active
             if app_state.selected_indices and not getattr(app_state, 'draw_selection_ellipse', False):
                 state_gateway.clear_selected_indices()
             # Clear isochron data if switching away from isochron tool
             if app_state.selection_tool == 'isochron':
                 state_gateway.set_selected_isochron_data(None)

        state_gateway.set_selection_tool(new_tool)

        if app_state.selection_tool:
            logger.info("Selection tool '%s' enabled.", new_tool)
            if new_tool == 'lasso':
                _ensure_lasso_selector()
            else:
                _ensure_rectangle_selector()

            # Disable Matplotlib toolbar zoom/pan if active
            try:
                if app_state.fig.canvas.toolbar.mode == 'zoom rect':
                    app_state.fig.canvas.toolbar.zoom()
                elif app_state.fig.canvas.toolbar.mode == 'pan/zoom':
                    app_state.fig.canvas.toolbar.pan()
            except Exception:
                pass

        else:
            logger.info("Selection tool disabled.")
            _disable_rectangle_selector()
            _disable_lasso_selector()

        _notify_selection_ui()
        refresh_selection_overlay()

        # If we just disabled isochron tool, refresh plot to remove the isochron line
        if new_tool is None and app_state.selection_tool is None:
            try:
                from visualization.events import on_slider_change
                on_slider_change()
            except Exception as e:
                logger.warning("Failed to refresh plot after disabling selection tool: %s", e)
    except Exception as err:
        logger.warning("Failed to toggle selection mode: %s", err)


def sync_selection_tools() -> None:
    """Ensure selection helpers stay in sync with current axes."""
    if app_state.selection_tool == 'lasso':
        _ensure_lasso_selector()
        _disable_rectangle_selector()
    elif app_state.selection_tool:
        _ensure_rectangle_selector()
        _disable_lasso_selector()
    else:
        _disable_rectangle_selector()
        _disable_lasso_selector()


def on_hover(event) -> None:
    """Handle mouse hover events"""
    try:
        if app_state.render_mode == '3D':
            return

        if event is None or not hasattr(event, 'inaxes'):
            return
        
        if event.inaxes != app_state.ax or app_state.annotation is None:
            return
        if not getattr(app_state, 'show_tooltip', True):
            try:
                app_state.annotation.set_visible(False)
            except Exception:
                pass
            return
        
        visible = False

        for sc in app_state.scatter_collections:
            if sc is None:
                continue

            try:
                cont, ind = sc.contains(event)
                if not cont or not ind or "ind" not in ind or len(ind["ind"]) == 0:
                    continue

                idx_in_scatter = int(ind["ind"][0])
                sample_idx = app_state.artist_to_sample.get((id(sc), idx_in_scatter))
                if sample_idx is None:
                    continue

                offsets = sc.get_offsets()
                if offsets is None or len(offsets) <= idx_in_scatter:
                    continue

                x, y = offsets[idx_in_scatter]
                x, y = float(x), float(y)

                # Use .loc instead of .iloc to ensure we get the correct row by index label
                # sample_idx is the original index label from df_global
                try:
                    df = _df_global()
                    if df is None:
                        continue
                    row = df.loc[sample_idx]
                    # Handle case where index is not unique (returns DataFrame)
                    if isinstance(row, pd.DataFrame):
                        row = row.iloc[0]
                except KeyError:
                    continue

                lines = []
                # Use configured columns if available, otherwise fallback to defaults
                cols_to_show = getattr(app_state, 'tooltip_columns', None)
                if cols_to_show is None:
                    cols_to_show = ['Lab No.', 'Discovery site', 'Period']

                # If user deselected all columns, show at least the ID
                if not cols_to_show:
                     lines.append(f"ID: {sample_idx}")
                else:
                    found_any = False
                    for col in cols_to_show:
                        if col in df.columns:
                            val = row[col]
                            val_str = str(val) if pd.notna(val) else 'N/A'
                            lines.append(f"{col}: {val_str}")
                            found_any = True
                    
                    if not found_any:
                        lines.append(f"ID: {sample_idx}")
                
                txt = "\n".join(lines)
                if sample_idx in app_state.selected_indices:
                    txt += "\n" + translate("Status: Selected")

                app_state.annotation.xy = (x, y)
                app_state.annotation.set_text(txt)
                app_state.annotation.set_visible(True)
                visible = True
                break

            except Exception:
                continue

        if not visible:
            try:
                app_state.annotation.set_visible(False)
            except Exception:
                pass

    except Exception:
        pass


def on_click(event) -> None:
    """Handle mouse click events for interactive selection."""
    try:
        if app_state.render_mode == '3D':
            return

        if event is None or not hasattr(event, 'inaxes'):
            return
        
        if event.inaxes != app_state.ax:
            return
        
        if not hasattr(event, 'button') or event.button != 1:
            return
        
        if app_state.selection_mode:
            if getattr(event, 'dblclick', False):
                sample_idx = _resolve_sample_index(event)
                if sample_idx is None:
                    logger.warning("No point detected for selection.")
                    return

                try:
                    df = _df_global()
                    if df is None:
                        lab_label = str(sample_idx)
                    else:
                        row = df.loc[sample_idx]
                        lab_value = row['Lab No.'] if 'Lab No.' in df.columns else sample_idx
                        if pd.notna(lab_value):
                            lab_label = str(lab_value)
                        else:
                            lab_label = str(sample_idx)
                except Exception:
                    lab_label = str(sample_idx)

                if sample_idx in app_state.selected_indices:
                    state_gateway.remove_selected_indices([sample_idx])
                    logger.info("Deselected sample %s.", lab_label)
                else:
                    state_gateway.add_selected_indices([sample_idx])
                    logger.info("Selected sample %s.", lab_label)

                refresh_selection_overlay()
            return

        logger.info(translate("Click export has been removed. Use the control panel export instead."))
        return
                
    except Exception as e:
        logger.warning("Click handler error: %s", e)


def on_legend_click(event) -> None:
    """Handle legend click events - bring group to front"""
    try:
        if event is None or not hasattr(event, 'inaxes'):
            return
        
        # Skip if not a button press event or wrong button
        if not hasattr(event, 'button') or event.button != 1:
            return
        
        legend = app_state.ax.get_legend()
        if legend is None or not app_state.scatter_collections:
            return
        
        # Check if click is within legend bounds
        try:
            contains, leg_info = legend.contains(event)
            if not contains:
                return
        except Exception:
            return

        # Get all legend labels and their corresponding scatter objects
        leg_texts = legend.get_texts()
        scatter_labels = {sc.get_label(): sc for sc in app_state.scatter_collections if sc}
        
        # Find which legend entry was clicked
        for i, leg_text in enumerate(leg_texts):
            label = leg_text.get_text()
            if label in scatter_labels:
                # Try to detect which legend item was clicked by checking bbox
                try:
                    bbox = leg_text.get_window_extent()
                    if event.x is not None and event.y is not None:
                        if bbox.contains(event.x, event.y):
                            scatter = scatter_labels[label]
                            
                            # Toggle visibility
                            new_visible = not scatter.get_visible()
                            scatter.set_visible(new_visible)
                            
                            # Update legend text alpha
                            leg_text.set_alpha(1.0 if new_visible else 0.5)
                            
                            # Update legend handle alpha
                            if i < len(legend.legendHandles):
                                legend.legendHandles[i].set_alpha(1.0 if new_visible else 0.5)

                            # Update app_state.visible_groups
                            visible_groups = list(app_state.visible_groups) if app_state.visible_groups is not None else None
                            if visible_groups is None:
                                # If None, it means all were visible. Initialize with all.
                                visible_groups = list(app_state.current_groups)
                            
                            if new_visible:
                                if label not in visible_groups:
                                    visible_groups.append(label)
                            else:
                                if label in visible_groups:
                                    visible_groups.remove(label)
                            
                            # If all are visible again, set to None to indicate "all"
                            if len(visible_groups) == len(app_state.current_groups):
                                state_gateway.set_visible_groups(None)
                            else:
                                state_gateway.set_visible_groups(visible_groups)

                            # Notify Control Panel to update checkboxes
                            panel = getattr(app_state, 'control_panel_ref', None)
                            if panel is not None and hasattr(panel, 'sync_legend_ui'):
                                try:
                                    panel.sync_legend_ui()
                                except Exception as e:
                                    logger.warning("Failed to sync legend UI: %s", e)

                            logger.info("Toggled visibility for: %s to %s", label, new_visible)
                            try:
                                app_state.fig.canvas.draw_idle()
                            except Exception:
                                pass
                            return
                except Exception:
                    pass
                
    except Exception as e:
        pass


def _sync_render_mode(render_mode):
    """Update app_state and control panel if render_mode changed."""
    if render_mode == app_state.render_mode:
        return
    logger.debug("Adjusted render mode: %s -> %s", app_state.render_mode, render_mode)
    state_gateway.set_render_mode(render_mode)
    try:
        panel = getattr(app_state, 'control_panel_ref', None)
        if panel is not None and 'render_mode' in panel.radio_vars:
            panel.radio_vars['render_mode'].set(render_mode)
    except Exception as sync_err:
        logger.warning("Unable to sync control panel render mode: %s", sync_err)


def _cancel_embedding_task(reason: str = "") -> None:
    """Request cancellation for any running embedding task."""
    worker = getattr(app_state, 'embedding_worker', None)
    if worker is None:
        return

    try:
        if worker.isRunning():
            worker.request_cancel()
            logger.debug("Requested cancellation of embedding task. reason=%s", reason)
    except Exception as err:
        logger.warning("Failed to cancel embedding task: %s", err)


def _on_embedding_task_progress(task_token: int, percent: int, stage: str) -> None:
    if task_token != getattr(app_state, 'embedding_task_token', -1):
        return
    callback = getattr(app_state, 'embedding_progress_callback', None)
    if callable(callback):
        try:
            callback(percent, stage)
        except Exception:
            pass


def _on_embedding_task_finished(task_token: int, payload: dict, group_col: str) -> None:
    if task_token != getattr(app_state, 'embedding_task_token', -1):
        logger.debug("Ignore stale embedding result token=%s", task_token)
        return

    state_gateway.set_embedding_worker(None, running=False)

    algorithm = payload.get('algorithm', app_state.render_mode)
    if app_state.render_mode != algorithm:
        logger.debug("Ignore embedding result due to render mode change: %s -> %s", algorithm, app_state.render_mode)
        return

    from .plotting import plot_embedding

    render_ok = plot_embedding(
        group_col,
        algorithm,
        umap_params=app_state.umap_params,
        tsne_params=app_state.tsne_params,
        pca_params=app_state.pca_params,
        robust_pca_params=app_state.robust_pca_params,
        size=app_state.point_size,
        precomputed_embedding=payload.get('embedding'),
        precomputed_meta=payload.get('meta', {}),
    )

    if render_ok:
        refresh_selection_overlay()
        sync_selection_tools()
        _notify_selection_ui()
        try:
            app_state.fig.canvas.draw_idle()
        except Exception:
            pass
        state_gateway.set_initial_render_done(True)
        logger.debug("Async embedding render completed for %s", algorithm)
    else:
        logger.warning("Async embedding render failed for %s", algorithm)


def _on_embedding_task_failed(task_token: int, error_message: str) -> None:
    if task_token != getattr(app_state, 'embedding_task_token', -1):
        return

    state_gateway.set_embedding_worker(None, running=False)
    logger.warning("Embedding task failed: %s", error_message)


def _on_embedding_task_cancelled(task_token: int) -> None:
    if task_token != getattr(app_state, 'embedding_task_token', -1):
        return

    state_gateway.set_embedding_worker(None, running=False)
    logger.debug("Embedding task cancelled: token=%s", task_token)


def _start_async_embedding_render(group_col: str) -> bool:
    """Start background embedding computation for heavy algorithms."""
    from .embedding_worker import EmbeddingWorker
    from .plotting.data import _get_analysis_data

    algorithm = app_state.render_mode
    if algorithm not in _ASYNC_EMBEDDING_ALGORITHMS:
        return False

    x_data, _ = _get_analysis_data()
    if x_data is None:
        return False

    params_map = {
        'UMAP': app_state.umap_params,
        'tSNE': app_state.tsne_params,
        'PCA': app_state.pca_params,
        'RobustPCA': app_state.robust_pca_params,
    }
    params = dict(params_map.get(algorithm, {}))

    _cancel_embedding_task(reason='start_new_task')

    task_token = int(getattr(app_state, 'embedding_task_token', 0)) + 1

    worker = EmbeddingWorker(
        task_token=task_token,
        algorithm=algorithm,
        x_data=x_data,
        params=params,
        feature_names=list(_data_cols()),
    )

    worker.progress.connect(_on_embedding_task_progress)
    worker.finished_signal.connect(lambda token, payload: _on_embedding_task_finished(token, payload, group_col))
    worker.failed.connect(_on_embedding_task_failed)
    worker.cancelled.connect(_on_embedding_task_cancelled)

    state_gateway.set_embedding_worker(worker, running=True, task_token=task_token)
    worker.start()
    logger.debug("Started async embedding task token=%s, algorithm=%s", task_token, algorithm)
    return True


def _build_render_use_case() -> RenderPlotUseCase:
    from .plotting import plot_embedding, plot_3d_data, plot_2d_data

    return RenderPlotUseCase(
        state=app_state,
        get_df_global=_df_global,
        get_data_cols=_data_cols,
        get_group_cols=_group_cols,
        sync_render_mode=_sync_render_mode,
        cancel_embedding_task=_cancel_embedding_task,
        start_async_embedding_render=_start_async_embedding_render,
        plot_embedding=plot_embedding,
        plot_2d_data=plot_2d_data,
        plot_3d_data=plot_3d_data,
        refresh_selection_overlay=refresh_selection_overlay,
        sync_selection_tools=sync_selection_tools,
        notify_selection_ui=_notify_selection_ui,
        disable_rectangle_selector=_disable_rectangle_selector,
    )


def on_slider_change(val=None) -> None:
    """Handle slider and radio button changes from the control panel."""
    try:
        logger.debug("on_slider_change called, val=%s", val)
        _build_render_use_case().execute()
    except Exception as e:
        logger.error("on_slider_change error: %s", e)
        import traceback
        traceback.print_exc()
