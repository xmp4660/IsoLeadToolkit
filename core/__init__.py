"""
Core module - Configuration, state, session, and localization
"""
from .config import CONFIG, load_and_merge_config
from .state import AppStateGateway, StateStore, app_state, state_gateway
from .session import clear_session_params, get_temp_dir_size, load_session_params, save_session_params
from .localization import translate, set_language, available_languages, validate_language

__all__ = [
    'CONFIG',
    'load_and_merge_config',
    'app_state',
    'AppStateGateway',
    'StateStore',
    'state_gateway',
    'load_session_params',
    'save_session_params',
    'clear_session_params',
    'get_temp_dir_size',
    'translate',
    'set_language',
    'available_languages',
    'validate_language',
]
