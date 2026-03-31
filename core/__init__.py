"""
Core module - Configuration, state, session, and localization
"""
from .config import CONFIG
from .state import app_state
from .state_gateway import AppStateGateway, state_gateway
from .session import load_session_params, save_session_params, clear_session_params, get_temp_dir_size
from .localization import translate, set_language, available_languages, validate_language

__all__ = [
    'CONFIG',
    'app_state',
    'AppStateGateway',
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
