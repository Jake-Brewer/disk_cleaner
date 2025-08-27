"""Tests for Configuration Manager module."""

import pytest
from pathlib import Path
from typing import Dict, Any


class TestConfigurationManager:
    """Test suite for Configuration Manager functionality."""

    @pytest.mark.unit
    def test_default_configuration_generation(self):
        """Test that default configuration can be generated successfully."""
        # This test will fail initially - RED phase
        from disk_cleaner.src.disk_cleaner.config import ConfigurationManager

        config_manager = ConfigurationManager()
        default_config = config_manager.get_default_configuration()

        # Assert that default configuration is generated
        assert default_config is not None
        assert isinstance(default_config, dict)

        # Assert required top-level sections exist
        required_sections = ['scan', 'performance', 'classification', 'ui']
        for section in required_sections:
            assert section in default_config
            assert isinstance(default_config[section], dict)

    @pytest.mark.unit
    def test_default_scan_paths_are_windows_specific(self):
        """Test that default scan paths are appropriate for Windows."""
        from disk_cleaner.src.disk_cleaner.config import ConfigurationManager

        config_manager = ConfigurationManager()
        default_config = config_manager.get_default_configuration()

        scan_config = default_config['scan']
        assert 'paths' in scan_config

        paths = scan_config['paths']
        assert isinstance(paths, list)
        assert len(paths) > 0

        # Check that paths contain Windows-specific directories
        path_strings = [str(path) for path in paths]
        windows_paths = [p for p in path_strings if 'Users' in p or 'Documents' in p]
        assert len(windows_paths) > 0

    @pytest.mark.unit
    def test_default_performance_settings_are_reasonable(self):
        """Test that default performance settings are within reasonable bounds."""
        from disk_cleaner.src.disk_cleaner.config import ConfigurationManager

        config_manager = ConfigurationManager()
        default_config = config_manager.get_default_configuration()

        perf_config = default_config['performance']
        assert 'mode' in perf_config
        assert perf_config['mode'] in ['background', 'foreground']

        assert 'max_threads' in perf_config
        assert isinstance(perf_config['max_threads'], int)
        assert 1 <= perf_config['max_threads'] <= 16

        assert 'memory_limit_mb' in perf_config
        assert isinstance(perf_config['memory_limit_mb'], int)
        assert perf_config['memory_limit_mb'] > 0

    @pytest.mark.unit
    def test_configuration_is_serializable(self):
        """Test that default configuration can be serialized to YAML."""
        import yaml
        from disk_cleaner.src.disk_cleaner.config import ConfigurationManager

        config_manager = ConfigurationManager()
        default_config = config_manager.get_default_configuration()

        # Should be able to serialize without errors
        yaml_str = yaml.dump(default_config, default_flow_style=False)
        assert isinstance(yaml_str, str)
        assert len(yaml_str) > 0

        # Should be able to deserialize back
        deserialized = yaml.safe_load(yaml_str)
        assert deserialized == default_config
