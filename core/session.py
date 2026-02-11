import logging
logger = logging.getLogger(__name__)
"""
Session Management - Save and Load Algorithm Parameters
Handles persistence of last used parameters across program sessions
"""
import json
from .config import CONFIG


def save_session_params(algorithm, umap_params, tsne_params, point_size, group_col,
                        group_cols=None, data_cols=None, file_path=None, sheet_name=None,
                        render_mode='UMAP', selected_2d_cols=None, selected_3d_cols=None,
                        language=None, tooltip_columns=None, ui_theme=None):
    """
    Save current session parameters to temporary file
    """
    try:
        session_data = {
            'session_version': CONFIG.get('session_version', 1),
            'algorithm': algorithm,
            'umap_params': umap_params,
            'tsne_params': tsne_params,
            'point_size': point_size,
            'group_col': group_col,
            'group_cols': group_cols,
            'data_cols': data_cols,
            'file_path': file_path,
            'sheet_name': sheet_name,
            'render_mode': render_mode,
            'selected_2d_cols': selected_2d_cols or [],
            'selected_3d_cols': selected_3d_cols or [],
            'language': language,
            'tooltip_columns': tooltip_columns,
            'ui_theme': ui_theme
        }
        
        logger.debug(f"[DEBUG] Saving session params. Tooltip columns: {tooltip_columns}")

        with open(CONFIG['params_temp_file'], 'w', encoding='utf-8') as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"[INFO] Session parameters saved to {CONFIG['params_temp_file']}")
        return True
    except Exception as e:
        logger.exception(f"[WARN] Failed to save session parameters: {e}")
        return False


def load_session_params():
    """
    Load last session parameters from temporary file
    
    Returns:
        dict with keys: algorithm, umap_params, tsne_params, point_size, group_col
        or None if file doesn't exist or load fails
    """
    try:
        params_file = CONFIG['params_temp_file']
        legacy_params_file = CONFIG.get('legacy_params_temp_file')

        if not params_file.exists():
            if legacy_params_file is not None and legacy_params_file.exists():
                params_file = legacy_params_file
            else:
                logger.info("[INFO] No previous session found")
                return None

        with open(params_file, 'r', encoding='utf-8') as f:
            session_data = json.load(f)

        version = int(session_data.get('session_version', 1))
        current_version = int(CONFIG.get('session_version', 1))
        if version < current_version:
            logger.info(f"[INFO] Session data version {version} -> {current_version}")
            session_data['session_version'] = current_version

        if legacy_params_file and params_file == legacy_params_file:
            # Migrate to preferred location for faster future loads.
            try:
                with open(CONFIG['params_temp_file'], 'w', encoding='utf-8') as out:
                    json.dump(session_data, out, indent=2, ensure_ascii=False)
                logger.info(f"[INFO] Migrated session parameters to {CONFIG['params_temp_file']}")
            except Exception:
                pass
        
        logger.info(f"[INFO] Session parameters loaded from {params_file}")
        logger.info(f"[INFO] Previous algorithm: {session_data.get('algorithm', 'UMAP')}")
        logger.info(f"[INFO] Previous group: {session_data.get('group_col', 'Province')}")
        return session_data
    except Exception as e:
        logger.exception(f"[WARN] Failed to load session parameters: {e}")
        return None


def clear_session_params():
    """Clear saved session parameters"""
    try:
        params_file = CONFIG['params_temp_file']
        if params_file.exists():
            params_file.unlink()
            logger.info("[INFO] Session parameters cleared")
            return True
    except Exception as e:
        logger.exception(f"[WARN] Failed to clear session parameters: {e}")
    return False


def get_temp_dir_size():
    """Get size of temp directory in MB"""
    try:
        total_size = 0
        for item in CONFIG['temp_dir'].iterdir():
            if item.is_file():
                total_size += item.stat().st_size
        return total_size / (1024 * 1024)  # Convert to MB
    except Exception:
        return 0
