# -*- coding: utf-8 -*-
import logging
import os
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QGroupBox, QComboBox, QLineEdit, QDoubleSpinBox, QSpinBox, QRadioButton,
    QTextEdit, QFileDialog, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import numpy as np
import pandas as pd

from core import app_state, translate, CONFIG

logger = logging.getLogger(__name__)


def show_provenance_ml(parent=None):
    dialog = ProvenanceMLDialog(parent)
    dialog.exec_()


class ProvenanceMLDialog(QDialog):
    """Provenance ML dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(translate("Provenance ML"))
        self.setMinimumWidth(760)
        self.setMinimumHeight(700)

        self._training_df = None
        self._result = None
        self._selected_original_indices = None
        self._ml_params = getattr(app_state, 'ml_params', CONFIG.get('ml_params', {})).copy()
        self._default_training_file = self._resolve_default_training_file()

        self._setup_ui()
        self._refresh_prediction_columns()

        if self._default_training_file:
            self.train_file_edit.setText(self._default_training_file)
            self._populate_training_sheets(self._default_training_file)
            self._load_training_data()

    def _resolve_default_training_file(self):
        base_dir = Path(__file__).resolve().parents[2]
        default_path = base_dir / 'reference' / '18343221' / 'Database - ore lead signatures.xlsx'
        return str(default_path) if default_path.exists() else ''

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel(translate("Provenance ML"))
        title_font = QFont(title.font())
        title_font.setPointSize(title_font.pointSize() + 2)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Training data group
        train_group = QGroupBox(translate("Training Data"))
        train_layout = QVBoxLayout()

        file_row = QHBoxLayout()
        file_row.addWidget(QLabel(translate("Training File:")))
        self.train_file_edit = QLineEdit()
        self.train_file_edit.setReadOnly(True)
        file_row.addWidget(self.train_file_edit, 1)

        browse_btn = QPushButton(translate("Browse..."))
        browse_btn.clicked.connect(self._browse_training_file)
        file_row.addWidget(browse_btn)
        train_layout.addLayout(file_row)

        sheet_row = QHBoxLayout()
        sheet_row.addWidget(QLabel(translate("Training Sheet:")))
        self.train_sheet_combo = QComboBox()
        self.train_sheet_combo.currentIndexChanged.connect(self._on_training_sheet_change)
        sheet_row.addWidget(self.train_sheet_combo, 1)

        load_btn = QPushButton(translate("Load Training File"))
        load_btn.clicked.connect(self._load_training_data)
        sheet_row.addWidget(load_btn)
        train_layout.addLayout(sheet_row)

        self.train_status_label = QLabel("")
        self.train_status_label.setWordWrap(True)
        train_layout.addWidget(self.train_status_label)

        # Training columns
        cols_group = QGroupBox(translate("Training Columns"))
        cols_layout = QVBoxLayout()

        region_row = QHBoxLayout()
        region_row.addWidget(QLabel(translate("Region Column:")))
        self.train_region_combo = QComboBox()
        region_row.addWidget(self.train_region_combo, 1)
        cols_layout.addLayout(region_row)

        self.train_206_combo = QComboBox()
        self.train_207_combo = QComboBox()
        self.train_208_combo = QComboBox()

        pb_row1 = QHBoxLayout()
        pb_row1.addWidget(QLabel("206Pb/204Pb:"))
        pb_row1.addWidget(self.train_206_combo, 1)
        cols_layout.addLayout(pb_row1)

        pb_row2 = QHBoxLayout()
        pb_row2.addWidget(QLabel("207Pb/204Pb:"))
        pb_row2.addWidget(self.train_207_combo, 1)
        cols_layout.addLayout(pb_row2)

        pb_row3 = QHBoxLayout()
        pb_row3.addWidget(QLabel("208Pb/204Pb:"))
        pb_row3.addWidget(self.train_208_combo, 1)
        cols_layout.addLayout(pb_row3)

        cols_group.setLayout(cols_layout)
        train_layout.addWidget(cols_group)

        train_group.setLayout(train_layout)
        layout.addWidget(train_group)

        # Prediction data group
        pred_group = QGroupBox(translate("Prediction Data"))
        pred_layout = QVBoxLayout()

        scope_group = QGroupBox(translate("Data Scope"))
        scope_layout = QVBoxLayout()
        self.radio_all = QRadioButton(translate("All data"))
        self.radio_selected = QRadioButton(translate("Selected data only"))

        selected_count = len(getattr(app_state, 'selected_indices', set()))
        total_count = len(app_state.df_global) if app_state.df_global is not None else 0

        if selected_count > 0:
            self.radio_selected.setText(
                translate("Selected data only") + f" ({selected_count}/{total_count})")
            self.radio_selected.setChecked(True)
        else:
            self.radio_all.setChecked(True)
            self.radio_selected.setEnabled(False)
            self.radio_selected.setText(
                translate("Selected data only") + f" ({translate('no selection')})")

        scope_layout.addWidget(self.radio_all)
        scope_layout.addWidget(self.radio_selected)
        scope_group.setLayout(scope_layout)
        pred_layout.addWidget(scope_group)

        pred_cols_group = QGroupBox(translate("Prediction Columns"))
        pred_cols_layout = QVBoxLayout()

        self.pred_206_combo = QComboBox()
        self.pred_207_combo = QComboBox()
        self.pred_208_combo = QComboBox()

        pred_row1 = QHBoxLayout()
        pred_row1.addWidget(QLabel("206Pb/204Pb:"))
        pred_row1.addWidget(self.pred_206_combo, 1)
        pred_cols_layout.addLayout(pred_row1)

        pred_row2 = QHBoxLayout()
        pred_row2.addWidget(QLabel("207Pb/204Pb:"))
        pred_row2.addWidget(self.pred_207_combo, 1)
        pred_cols_layout.addLayout(pred_row2)

        pred_row3 = QHBoxLayout()
        pred_row3.addWidget(QLabel("208Pb/204Pb:"))
        pred_row3.addWidget(self.pred_208_combo, 1)
        pred_cols_layout.addLayout(pred_row3)

        pred_cols_group.setLayout(pred_cols_layout)
        pred_layout.addWidget(pred_cols_group)

        pred_group.setLayout(pred_layout)
        layout.addWidget(pred_group)

        # Parameters
        param_group = QGroupBox(translate("Parameters"))
        param_layout = QVBoxLayout()

        db_row = QHBoxLayout()
        db_row.addWidget(QLabel(translate("DBSCAN eps:")))
        self.eps_spin = QDoubleSpinBox()
        self.eps_spin.setRange(0.01, 2.0)
        self.eps_spin.setDecimals(3)
        self.eps_spin.setSingleStep(0.01)
        self.eps_spin.setValue(self._ml_params.get('dbscan_eps', 0.18))
        db_row.addWidget(self.eps_spin)
        param_layout.addLayout(db_row)

        ratio_row = QHBoxLayout()
        ratio_row.addWidget(QLabel(translate("DBSCAN min sample ratio:")))
        self.min_samples_ratio_spin = QDoubleSpinBox()
        self.min_samples_ratio_spin.setRange(0.01, 0.5)
        self.min_samples_ratio_spin.setDecimals(2)
        self.min_samples_ratio_spin.setSingleStep(0.01)
        self.min_samples_ratio_spin.setValue(self._ml_params.get('dbscan_min_samples_ratio', 0.1))
        ratio_row.addWidget(self.min_samples_ratio_spin)
        param_layout.addLayout(ratio_row)

        min_region_row = QHBoxLayout()
        min_region_row.addWidget(QLabel(translate("Min region samples:")))
        self.min_region_spin = QSpinBox()
        self.min_region_spin.setRange(3, 1000)
        self.min_region_spin.setValue(self._ml_params.get('min_region_samples', 5))
        min_region_row.addWidget(self.min_region_spin)
        param_layout.addLayout(min_region_row)

        db_min_region_row = QHBoxLayout()
        db_min_region_row.addWidget(QLabel(translate("DBSCAN min region samples:")))
        self.dbscan_min_region_spin = QSpinBox()
        self.dbscan_min_region_spin.setRange(5, 1000)
        self.dbscan_min_region_spin.setValue(self._ml_params.get('dbscan_min_region_samples', 20))
        db_min_region_row.addWidget(self.dbscan_min_region_spin)
        param_layout.addLayout(db_min_region_row)

        smote_row = QHBoxLayout()
        smote_row.addWidget(QLabel(translate("SMOTE k-neighbors:")))
        self.smote_k_spin = QSpinBox()
        self.smote_k_spin.setRange(1, 20)
        self.smote_k_spin.setValue(self._ml_params.get('smote_k_neighbors', 3))
        smote_row.addWidget(self.smote_k_spin)
        param_layout.addLayout(smote_row)

        threshold_row = QHBoxLayout()
        threshold_row.addWidget(QLabel(translate("Prediction threshold:")))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.5, 0.99)
        self.threshold_spin.setDecimals(2)
        self.threshold_spin.setSingleStep(0.01)
        self.threshold_spin.setValue(self._ml_params.get('predict_threshold', 0.9))
        threshold_row.addWidget(self.threshold_spin)
        param_layout.addLayout(threshold_row)

        self.smote_check = QCheckBox(translate("Enable SMOTE"))
        self.smote_check.setChecked(self._ml_params.get('smote_enabled', True))
        param_layout.addWidget(self.smote_check)

        self.standardize_check = QCheckBox(translate("Standardize data"))
        self.standardize_check.setChecked(self._ml_params.get('standardize', True))
        param_layout.addWidget(self.standardize_check)

        param_group.setLayout(param_layout)
        layout.addWidget(param_group)

        # Run button
        run_btn = QPushButton(translate("Run Provenance ML"))
        run_btn.setFixedWidth(220)
        run_btn.clicked.connect(self._on_run_ml)
        layout.addWidget(run_btn, 0, Qt.AlignHCenter)

        # Results
        self.result_group = QGroupBox(translate("Results"))
        result_layout = QVBoxLayout()
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        result_layout.addWidget(self.result_text)
        self.result_group.setLayout(result_layout)
        self.result_group.setVisible(False)
        layout.addWidget(self.result_group)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.addStretch()

        self.apply_btn = QPushButton(translate("Apply as Group Column"))
        self.apply_btn.clicked.connect(self._on_apply_group_column)
        self.apply_btn.setEnabled(False)
        button_layout.addWidget(self.apply_btn)

        self.export_btn = QPushButton(translate("Export Results"))
        self.export_btn.clicked.connect(self._on_export_results)
        self.export_btn.setEnabled(False)
        button_layout.addWidget(self.export_btn)

        close_btn = QPushButton(translate("Close"))
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def _browse_training_file(self):
        file_types = ";;".join([
            f"{translate('Excel files')} (*.xlsx *.xls)",
            f"{translate('CSV files')} (*.csv)",
            f"{translate('All files')} (*.*)",
        ])

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            translate("Select Data File"),
            self.train_file_edit.text() or "",
            file_types,
        )

        if file_path:
            self.train_file_edit.setText(file_path)
            self._populate_training_sheets(file_path)
            self._load_training_data()

    def _populate_training_sheets(self, file_path: str):
        self.train_sheet_combo.blockSignals(True)
        self.train_sheet_combo.clear()

        if not file_path or not os.path.exists(file_path):
            self.train_sheet_combo.addItem(translate("No sheet"))
            self.train_sheet_combo.setEnabled(False)
            self.train_sheet_combo.blockSignals(False)
            return

        if file_path.lower().endswith(('.xlsx', '.xls', '.xlsm')):
            try:
                xls = pd.ExcelFile(file_path, engine='calamine')
            except Exception:
                xls = pd.ExcelFile(file_path)

            sheet_names = xls.sheet_names
            self.train_sheet_combo.addItems(sheet_names)
            self.train_sheet_combo.setEnabled(True)
            if 'Directly usable data' in sheet_names:
                self.train_sheet_combo.setCurrentText('Directly usable data')
        else:
            self.train_sheet_combo.addItem(translate("No sheet"))
            self.train_sheet_combo.setEnabled(False)

        self.train_sheet_combo.blockSignals(False)

    def _on_training_sheet_change(self, _index):
        if self.train_sheet_combo.isEnabled():
            self._load_training_data()

    def _read_training_file(self, file_path: str, sheet_name: str | None):
        if file_path.lower().endswith(('.xlsx', '.xls', '.xlsm')):
            try:
                return pd.read_excel(file_path, sheet_name=sheet_name, engine='calamine')
            except Exception:
                return pd.read_excel(file_path, sheet_name=sheet_name)
        return pd.read_csv(file_path)

    def _load_training_data(self):
        file_path = self.train_file_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, translate("Warning"), translate("Please select a file."))
            return
        if not os.path.exists(file_path):
            QMessageBox.warning(
                self, translate("Warning"),
                translate("File not found: {path}").format(path=file_path),
            )
            return

        sheet_name = None
        if self.train_sheet_combo.isEnabled():
            sheet_name = self.train_sheet_combo.currentText()

        try:
            df = self._read_training_file(file_path, sheet_name)
            self._training_df = df
            self._update_training_columns(df)
            self.train_status_label.setText(
                translate("Training data loaded: {rows} rows, {cols} columns.").format(
                    rows=len(df), cols=len(df.columns))
            )
        except Exception as exc:
            logger.error(f"[ERROR] Failed to load training data: {exc}")
            self._training_df = None
            self.train_status_label.setText("")
            QMessageBox.warning(
                self, translate("Error"),
                translate("Training data load failed: {error}").format(error=str(exc)),
            )

    def _update_training_columns(self, df: pd.DataFrame):
        columns = df.columns.astype(str).tolist()

        self.train_region_combo.clear()
        self.train_region_combo.addItems(columns)

        self.train_206_combo.clear()
        self.train_206_combo.addItems(columns)

        self.train_207_combo.clear()
        self.train_207_combo.addItems(columns)

        self.train_208_combo.clear()
        self.train_208_combo.addItems(columns)

        self._auto_detect_region_column(columns)
        self._auto_detect_pb_columns(columns, self.train_206_combo, self.train_207_combo, self.train_208_combo)

    def _refresh_prediction_columns(self):
        self.pred_206_combo.clear()
        self.pred_207_combo.clear()
        self.pred_208_combo.clear()

        if app_state.df_global is None:
            return

        numeric_cols = app_state.df_global.select_dtypes(include=[np.number]).columns.tolist()
        self.pred_206_combo.addItems(numeric_cols)
        self.pred_207_combo.addItems(numeric_cols)
        self.pred_208_combo.addItems(numeric_cols)
        self._auto_detect_pb_columns(numeric_cols, self.pred_206_combo, self.pred_207_combo, self.pred_208_combo)

    def _auto_detect_region_column(self, columns):
        for i, col in enumerate(columns):
            if col.lower().strip() in ('corrected region', 'region', 'corrected_region'):
                self.train_region_combo.setCurrentIndex(i)
                return
        for i, col in enumerate(columns):
            if 'region' in col.lower():
                self.train_region_combo.setCurrentIndex(i)
                return

    def _auto_detect_pb_columns(self, columns, combo_206, combo_207, combo_208):
        patterns = {
            '206': combo_206,
            '207': combo_207,
            '208': combo_208,
        }
        for key, combo in patterns.items():
            for i, col in enumerate(columns):
                col_lower = col.lower().replace(' ', '')
                if key in col_lower and '204' in col_lower:
                    combo.setCurrentIndex(i)
                    break

    def _on_run_ml(self):
        if app_state.df_global is None:
            QMessageBox.warning(self, translate("Warning"), translate("Please load data first."))
            return

        if self._training_df is None:
            QMessageBox.warning(self, translate("Warning"), translate("Please load training data first."))
            return

        region_col = self.train_region_combo.currentText()
        train_cols = [
            self.train_206_combo.currentText(),
            self.train_207_combo.currentText(),
            self.train_208_combo.currentText(),
        ]

        if not region_col or not all(train_cols) or len(set(train_cols)) < 3:
            QMessageBox.warning(self, translate("Warning"), translate("Please select training columns."))
            return

        pred_cols = [
            self.pred_206_combo.currentText(),
            self.pred_207_combo.currentText(),
            self.pred_208_combo.currentText(),
        ]

        if not all(pred_cols) or len(set(pred_cols)) < 3:
            QMessageBox.warning(self, translate("Warning"), translate("Please select Pb columns for prediction."))
            return

        if self.radio_selected.isChecked() and app_state.selected_indices:
            selected = sorted(list(app_state.selected_indices))
            df_pred = app_state.df_global.iloc[selected].reset_index(drop=True)
            self._selected_original_indices = selected
        else:
            df_pred = app_state.df_global
            self._selected_original_indices = None

        params = getattr(app_state, 'ml_params', self._ml_params) or {}
        xgb_params = params.get('xgb_params', {})
        smote_sampling_strategy = params.get('smote_sampling_strategy', 1.0)

        try:
            from ui.dialogs.progress_dialog import ProgressDialog
            progress = ProgressDialog(translate("Provenance ML"), translate("Loading Data"))
        except Exception:
            progress = None

        try:
            if progress:
                progress.update_message(translate("Preparing data..."))

            from data.provenance_ml import run_provenance_pipeline, ProvenanceMLError

            result = run_provenance_pipeline(
                training_df=self._training_df,
                region_col=region_col,
                feature_cols=train_cols,
                target_df=df_pred,
                target_feature_cols=pred_cols,
                min_region_samples=int(self.min_region_spin.value()),
                dbscan_min_region_samples=int(self.dbscan_min_region_spin.value()),
                dbscan_eps=float(self.eps_spin.value()),
                dbscan_min_samples_ratio=float(self.min_samples_ratio_spin.value()),
                standardize=bool(self.standardize_check.isChecked()),
                smote_enabled=bool(self.smote_check.isChecked()),
                smote_k_neighbors=int(self.smote_k_spin.value()),
                smote_sampling_strategy=smote_sampling_strategy,
                xgb_params=xgb_params,
                predict_threshold=float(self.threshold_spin.value()),
            )

            pred = result['predictions']
            valid_mask = pred['valid_mask']
            full_labels = np.full(len(df_pred), 'Unknown', dtype=object)
            full_probs = np.full(len(df_pred), np.nan, dtype=float)

            if pred['labels']:
                full_labels[valid_mask] = np.array(pred['labels'], dtype=object)
                full_probs[valid_mask] = np.array(pred['max_prob'], dtype=float)

            indices = (
                self._selected_original_indices
                if self._selected_original_indices is not None
                else list(range(len(df_pred)))
            )

            pred_df = pd.DataFrame({
                'Index': indices,
                translate("Predicted Region"): full_labels,
                translate("Predicted Probability"): full_probs,
            })

            proba = pred.get('proba')
            label_order = pred.get('label_order', [])
            if proba is not None and len(label_order) > 0:
                for i, label in enumerate(label_order):
                    col = f"P({label})"
                    values = np.full(len(df_pred), np.nan, dtype=float)
                    if proba.size > 0:
                        values[valid_mask] = proba[:, i]
                    pred_df[col] = values

            result['prediction_df'] = pred_df
            result['full_labels'] = full_labels
            result['full_probs'] = full_probs
            result['prediction_count'] = int(len(df_pred))

            self._result = result
            app_state.ml_last_result = result
            app_state.ml_last_model_meta = result.get('model_info')

            self._display_results()
        except ProvenanceMLError as exc:
            QMessageBox.warning(
                self, translate("Error"),
                translate("ML training failed: {error}").format(error=str(exc)),
            )
        except Exception as exc:
            logger.error(f"[ERROR] Provenance ML failed: {exc}")
            QMessageBox.warning(
                self, translate("Error"),
                translate("ML training failed: {error}").format(error=str(exc)),
            )
        finally:
            if progress:
                progress.close()

    def _display_results(self):
        if self._result is None:
            return

        stats = self._result['training']['stats']
        pred_count = self._result.get('prediction_count', 0)
        labels = self._result.get('full_labels', [])
        unique_labels = sorted(set(labels) - {'Unknown', 'None'}) if len(labels) else []

        summary = [
            translate("Training samples: {count}").format(count=stats.get('rows_final', 0)),
            translate("Training labels: {count}").format(count=stats.get('labels_final', 0)),
            translate("Outliers removed: {count}").format(count=stats.get('outliers_removed', 0)),
            translate("Regions dropped: {count}").format(count=len(stats.get('regions_dropped_small', []))),
            translate("Prediction samples: {count}").format(count=pred_count),
            translate("Predicted regions: {count}").format(count=len(unique_labels)),
        ]

        self.result_text.setPlainText("\n".join(summary))
        self.result_group.setVisible(True)
        self.apply_btn.setEnabled(True)
        self.export_btn.setEnabled(True)

    def _on_apply_group_column(self):
        if self._result is None:
            QMessageBox.warning(self, translate("Warning"), translate("No ML results available."))
            return

        if app_state.df_global is None:
            QMessageBox.warning(self, translate("Warning"), translate("Please load data first."))
            return

        col_label = '_ML_Predicted_Region'
        col_prob = '_ML_Predicted_Prob'

        full_labels = np.full(len(app_state.df_global), 'Unknown', dtype=object)
        full_probs = np.full(len(app_state.df_global), np.nan, dtype=float)

        if self._selected_original_indices is not None:
            for i, orig_idx in enumerate(self._selected_original_indices):
                full_labels[orig_idx] = self._result['full_labels'][i]
                full_probs[orig_idx] = self._result['full_probs'][i]
        else:
            full_labels[:] = self._result['full_labels']
            full_probs[:] = self._result['full_probs']

        app_state.df_global[col_label] = full_labels
        app_state.df_global[col_prob] = full_probs

        if col_label not in app_state.group_cols:
            app_state.group_cols.append(col_label)

        app_state.last_group_col = col_label
        app_state.visible_groups = None

        if hasattr(app_state, '_notify_listeners'):
            app_state._notify_listeners()

        QMessageBox.information(
            self, translate("Success"),
            translate("Provenance results applied successfully."))

    def _on_export_results(self):
        if self._result is None:
            QMessageBox.warning(self, translate("Warning"), translate("No ML results available."))
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            translate("Export Results"),
            "",
            ";;".join([
                f"{translate('CSV files')} (*.csv)",
                f"{translate('Excel files')} (*.xlsx)",
                f"{translate('All files')} (*.*)",
            ]),
        )

        if not file_path:
            return

        try:
            df = self._result.get('prediction_df')
            if df is None:
                raise ValueError("No prediction data to export.")

            if file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)
            else:
                df.to_csv(file_path, index=False)

            QMessageBox.information(
                self, translate("Success"),
                translate("Results exported successfully to {file}").format(file=file_path))
        except Exception as exc:
            QMessageBox.warning(
                self, translate("Error"),
                translate("Failed to export results: {error}").format(error=str(exc)))
