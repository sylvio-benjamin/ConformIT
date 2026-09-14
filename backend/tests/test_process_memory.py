import importlib

import pytest


def test_process_memory_module_removed():
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("app.etat_analyses")


def test_config_has_no_shared_api_master_key():
    import app.config as config

    assert not hasattr(config, "API_KEY_ATTENDUE")
    assert hasattr(config, "MAKE_WEBHOOK_URL")
