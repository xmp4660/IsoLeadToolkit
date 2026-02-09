"""Line style utilities for geochemical overlays."""
import tkinter as tk
from tkinter import ttk, colorchooser


def resolve_line_style(app_state, style_key, fallback):
    """Resolve line style with app_state overrides."""
    style = {}
    try:
        style = getattr(app_state, 'line_styles', {}).get(style_key, {}) or {}
    except Exception:
        style = {}

    resolved = dict(fallback)
    for key, value in style.items():
        if key == 'color':
            if value is not None and value != '':
                resolved['color'] = value
        elif value is not None:
            resolved[key] = value
    return resolved


def open_line_style_dialog(parent, translate, app_state, style_key, swatch=None, on_apply=None):
    """Open dialog to edit line styles for geochemical overlays."""
    dialog = tk.Toplevel(parent)
    dialog.title(translate("Edit Line Style"))
    dialog.geometry("420x260")
    dialog.transient(parent)
    dialog.grab_set()

    body = ttk.Frame(dialog, padding=12)
    body.pack(fill=tk.BOTH, expand=True)

    style = getattr(app_state, 'line_styles', {}).get(style_key, {})
    line_color = tk.StringVar(value=style.get('color') or '')
    auto_color_var = tk.BooleanVar(value=style.get('color') in (None, ''))
    line_width = tk.DoubleVar(value=float(style.get('linewidth', 1.0)))
    line_style = tk.StringVar(value=style.get('linestyle', '-'))
    line_alpha = tk.DoubleVar(value=float(style.get('alpha', 0.85)))

    form = ttk.Frame(body, style='CardBody.TFrame')
    form.pack(fill=tk.X)

    color_row = ttk.Frame(form, style='CardBody.TFrame')
    color_row.pack(fill=tk.X, pady=4)
    ttk.Label(color_row, text=translate("Line Color"), style='Body.TLabel').pack(side=tk.LEFT)
    color_swatch = tk.Label(color_row, width=3, height=1, bg=line_color.get() or '#e2e8f0', relief='solid', bd=1)
    color_swatch.pack(side=tk.LEFT, padx=(8, 0))

    def _pick_color():
        chosen = colorchooser.askcolor(initialcolor=line_color.get() or '#e2e8f0', parent=dialog)
        if chosen and chosen[1]:
            line_color.set(chosen[1])
            color_swatch.configure(bg=chosen[1])
            auto_color_var.set(False)

    def _toggle_auto():
        if auto_color_var.get():
            color_swatch.configure(bg='#e2e8f0')

    auto_chk = ttk.Checkbutton(
        color_row,
        text=translate("Auto Color"),
        variable=auto_color_var,
        command=_toggle_auto,
        style='Option.TCheckbutton'
    )
    auto_chk.pack(side=tk.LEFT, padx=(8, 0))
    ttk.Button(
        color_row,
        text=translate("Choose Color"),
        style='Secondary.TButton',
        command=_pick_color
    ).pack(side=tk.LEFT, padx=(8, 0))

    width_row = ttk.Frame(form, style='CardBody.TFrame')
    width_row.pack(fill=tk.X, pady=4)
    ttk.Label(width_row, text=translate("Line Width"), style='Body.TLabel').pack(side=tk.LEFT)
    ttk.Spinbox(width_row, from_=0.2, to=6.0, increment=0.1, textvariable=line_width, width=6).pack(side=tk.LEFT, padx=(8, 0))

    style_row = ttk.Frame(form, style='CardBody.TFrame')
    style_row.pack(fill=tk.X, pady=4)
    ttk.Label(style_row, text=translate("Line Style"), style='Body.TLabel').pack(side=tk.LEFT)
    ttk.Combobox(style_row, textvariable=line_style, values=['-', '--', '-.', ':'], state='readonly', width=6).pack(side=tk.LEFT, padx=(8, 0))

    alpha_row = ttk.Frame(form, style='CardBody.TFrame')
    alpha_row.pack(fill=tk.X, pady=4)
    ttk.Label(alpha_row, text=translate("Opacity"), style='Body.TLabel').pack(side=tk.LEFT)
    ttk.Spinbox(alpha_row, from_=0.1, to=1.0, increment=0.05, textvariable=line_alpha, width=6).pack(side=tk.LEFT, padx=(8, 0))

    btn_row = ttk.Frame(body)
    btn_row.pack(fill=tk.X, pady=(12, 0))
    btn_row.columnconfigure(0, weight=1)

    def _apply():
        if style_key not in getattr(app_state, 'line_styles', {}):
            app_state.line_styles[style_key] = {}
        style_ref = app_state.line_styles[style_key]
        style_ref['color'] = None if auto_color_var.get() else (line_color.get() or '#ef4444')
        style_ref['linewidth'] = float(line_width.get())
        style_ref['linestyle'] = line_style.get() or '-'
        style_ref['alpha'] = float(line_alpha.get())

        if style_key == 'model_curve':
            app_state.model_curve_width = style_ref['linewidth']
        elif style_key == 'paleoisochron':
            app_state.paleoisochron_width = style_ref['linewidth']
        elif style_key == 'model_age_line':
            app_state.model_age_line_width = style_ref['linewidth']
        elif style_key == 'isochron':
            app_state.isochron_line_width = style_ref['linewidth']
        elif style_key == 'selected_isochron':
            app_state.selected_isochron_line_width = style_ref['linewidth']

        if swatch is not None:
            swatch.configure(bg=style_ref['color'] or '#e2e8f0')
        dialog.destroy()
        if callable(on_apply):
            on_apply()

    ttk.Button(btn_row, text=translate("Cancel"), style='Secondary.TButton', command=dialog.destroy).pack(side=tk.RIGHT)
    ttk.Button(btn_row, text=translate("Save"), style='Accent.TButton', command=_apply).pack(side=tk.RIGHT, padx=(0, 8))
