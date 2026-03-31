"""Event handlers for user interactions (hover, click, legend)."""
from __future__ import annotations

import logging
from typing import Any

import pandas as pd
from matplotlib.widgets import RectangleSelector, LassoSelector

from application import (
    RenderPlotUseCase,
    SelectedIsochronUseCase,
    SelectionInteractionUseCase,
    TooltipContentUseCase,
)
from core import app_state, state_gateway, translate
from visualization.selection_overlay import refresh_selection_overlay_state
from visualization.plotting.isochron import resolve_isochron_errors as _resolve_isochron_errors

logger = logging.getLogger(__name__)

# Minimum box size to register a rectangle selection (data units)
_SELECTION_MIN_SPAN = 1e-9
# Maximum distance (data units) for hover nearest-neighbor lookup
_HOVER_DISTANCE_THRESHOLD = 0.15
_ASYNC_EMBEDDING_ALGORITHMS = {'UMAP', 'tSNE', 'PCA', 'RobustPCA'}

_SELECTION_USE_CASE = SelectionInteractionUseCase(
    hover_distance_threshold=_HOVER_DISTANCE_THRESHOLD,
)
_SELECTED_ISOCHRON_USE_CASE = SelectedIsochronUseCase()
_TOOLTIP_CONTENT_USE_CASE = TooltipContentUseCase()


def _data_state() -> Any:
    """Return layered data state when available, otherwise fallback to app_state."""
    return getattr(app_state, 'data', app_state)


def _df_global() -> Any:
    return getattr(_data_state(), 'df_global', app_state.df_global)


def _data_cols() -> list[str]:
    return getattr(_data_state(), 'data_cols', app_state.data_cols)


def _group_cols() -> list[str]:
    return getattr(_data_state(), 'group_cols', app_state.group_cols)

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

        indices_in_box = _SELECTION_USE_CASE.rectangle_indices(
            app_state.sample_coordinates,
            x_min=x_min,
            x_max=x_max,
            y_min=y_min,
            y_max=y_max,
        )

        if not indices_in_box:
            return

        plan = _SELECTION_USE_CASE.plan_toggle(app_state.selected_indices, indices_in_box)
        if plan.action == 'remove':
            state_gateway.remove_selected_indices(plan.indices)
            logger.info("Deselected %d samples via box selection.", len(indices_in_box))
        elif plan.action == 'add':
            state_gateway.add_selected_indices(plan.indices)
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

        indices_in_shape = _SELECTION_USE_CASE.lasso_indices(
            app_state.sample_coordinates,
            vertices,
        )

        if not indices_in_shape:
            return

        plan = _SELECTION_USE_CASE.plan_toggle(app_state.selected_indices, indices_in_shape)
        if plan.action == 'remove':
            state_gateway.remove_selected_indices(plan.indices)
            logger.info("Deselected %d samples via custom shape.", len(indices_in_shape))
        elif plan.action == 'add':
            state_gateway.add_selected_indices(plan.indices)
            logger.info("Selected %d samples via custom shape.", len(indices_in_shape))

        refresh_selection_overlay()
        _notify_selection_ui()
        _refresh_isochron_after_selection()
    except Exception as err:
        logger.warning("Custom shape selection failed: %s", err)


def refresh_selection_overlay() -> None:
    """Update selection overlay scatter to highlight chosen points."""
    refresh_selection_overlay_state(
        state=app_state,
        state_write=state_gateway,
        notify_selection_ui=_notify_selection_ui,
    )


def calculate_selected_isochron() -> None:
    """Calculate isochron age for selected data points."""
    try:
        from data.geochemistry import york_regression, calculate_pbpb_age_from_ratio, engine

        payload = _SELECTED_ISOCHRON_USE_CASE.execute(
            df=_df_global(),
            selected_indices=list(app_state.selected_indices),
            render_mode=app_state.render_mode,
            resolve_errors=_resolve_isochron_errors,
            york_regression=york_regression,
            calculate_age=calculate_pbpb_age_from_ratio,
            get_engine_parameters=engine.get_parameters,
        )

        if payload is None:
            logger.warning("Isochron calculation did not produce a valid result.")
            state_gateway.set_selected_isochron_data(None)
            return

        state_gateway.set_selected_isochron_data(payload)
        logger.info(
            "Isochron calculated: Age = %.1f Ma, n = %d, R² = %.4f",
            payload.get('age', 0.0),
            payload.get('n_points', 0),
            payload.get('r_squared', 0.0),
        )
        logger.info(
            "Slope = %.6f, Intercept = %.6f",
            payload.get('slope', 0.0),
            payload.get('intercept', 0.0),
        )

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
            return _SELECTION_USE_CASE.nearest_sample_index(
                app_state.sample_coordinates,
                x=float(event.xdata),
                y=float(event.ydata),
            )
    except Exception:
        return None
    return None


def toggle_selection_mode(tool_type: str = 'export') -> None:
    """
    Toggle interactive selection mode.
    tool_type: 'export', 'lasso', or 'isochron'
    """
    try:
        try:
            new_tool = _SELECTION_USE_CASE.resolve_next_tool(
                app_state.selection_tool,
                tool_type,
                app_state.render_mode,
            )
        except ValueError:
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

                txt = _TOOLTIP_CONTENT_USE_CASE.build_text(
                    row=row,
                    df_columns=df.columns,
                    sample_idx=sample_idx,
                    tooltip_columns=getattr(app_state, 'tooltip_columns', None),
                    selected=sample_idx in app_state.selected_indices,
                    selected_status_label=translate("Status: Selected"),
                )

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

                            visible_groups = _SELECTION_USE_CASE.next_visible_groups(
                                current_visible_groups=(
                                    list(app_state.visible_groups)
                                    if app_state.visible_groups is not None
                                    else None
                                ),
                                all_groups=list(app_state.current_groups),
                                target_group=label,
                                target_visible=new_visible,
                            )
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
