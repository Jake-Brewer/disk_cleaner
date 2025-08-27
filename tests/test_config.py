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
    def test_configuration_file_discovery(self):
        """Test that configuration files can be discovered in standard locations."""
        from disk_cleaner.src.disk_cleaner.config import ConfigurationManager
        import tempfile
        import os
        from pathlib import Path

        config_manager = ConfigurationManager()

        # Test that config discovery method exists and works
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test config file
            config_path = Path(temp_dir) / "test_config.yaml"
            config_path.write_text("test: value")

            # Mock the config directory discovery
            original_method = getattr(config_manager, '_discover_config_files', None)
            if original_method:
                config_paths = config_manager._discover_config_files()
                assert isinstance(config_paths, list)
            else:
                # If method doesn't exist yet, this test will fail (RED phase)
                pytest.fail("ConfigurationManager._discover_config_files method not implemented")

    @pytest.mark.unit
    def test_configuration_file_reading(self):
        """Test that configuration files can be read and parsed."""
        from disk_cleaner.src.disk_cleaner.config import ConfigurationManager
        import tempfile
        from pathlib import Path

        config_manager = ConfigurationManager()

        # Test YAML file reading
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
scan:
  paths:
    - C:\\Test\\Path
performance:
  mode: foreground
""")
            temp_path = Path(f.name)

        try:
            # This should work if file reading is implemented
            config_data = config_manager._read_config_file(temp_path)
            assert isinstance(config_data, dict)
            assert 'scan' in config_data
            assert 'performance' in config_data
        except AttributeError:
            # If method doesn't exist yet, this test will fail (RED phase)
            pytest.fail("ConfigurationManager._read_config_file method not implemented")
        finally:
            temp_path.unlink()

    @pytest.mark.unit
    def test_environment_variable_expansion(self):
        """Test that environment variables in paths are properly expanded."""
        import os
        from disk_cleaner.src.disk_cleaner.config import DefaultConfigurationSource

        source = DefaultConfigurationSource()
        config = source.load()

        scan_paths = config['scan']['paths']

        # Check that %USERPROFILE% was expanded (not left as literal string)
        for path in scan_paths:
            assert '%USERNAME%' not in path
            assert '%USERPROFILE%' not in str(path)
            # Should contain actual expanded path
            assert 'Users' in path or os.path.exists(path)
