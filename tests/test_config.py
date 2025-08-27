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

    @pytest.mark.unit
    def test_yaml_configuration_parsing(self):
        """Test that YAML configuration files can be parsed correctly."""
        from disk_cleaner.src.disk_cleaner.config import ConfigurationManager
        import tempfile
        from pathlib import Path

        config_manager = ConfigurationManager()

        # Test valid YAML parsing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
scan:
  paths:
    - C:\\Test\\Path
    - D:\\Another\\Path
  max_depth: 5
performance:
  mode: background
  max_threads: 8
""")
            temp_path = Path(f.name)

        try:
            config_data = config_manager._read_config_file(temp_path)
            assert isinstance(config_data, dict)
            assert 'scan' in config_data
            assert 'performance' in config_data
            assert config_data['scan']['max_depth'] == 5
            assert config_data['performance']['mode'] == 'background'
            assert len(config_data['scan']['paths']) == 2
        finally:
            temp_path.unlink()

    @pytest.mark.unit
    def test_malformed_yaml_handling(self):
        """Test that malformed YAML files are handled gracefully."""
        from disk_cleaner.src.disk_cleaner.config import ConfigurationManager
        import tempfile
        from pathlib import Path

        config_manager = ConfigurationManager()

        # Test malformed YAML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
scan:
  paths:
    - C:\\Test\\Path
  invalid_yaml: [missing closing bracket
performance:
  mode: background
""")
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Cannot parse configuration file"):
                config_manager._read_config_file(temp_path)
        finally:
            temp_path.unlink()

    @pytest.mark.unit
    def test_yaml_anchors_and_references(self):
        """Test that YAML anchors and references are supported."""
        from disk_cleaner.src.disk_cleaner.config import ConfigurationManager
        import tempfile
        from pathlib import Path

        config_manager = ConfigurationManager()

        # Test YAML with anchors and references
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("""
defaults: &defaults
  max_depth: 10
  follow_symlinks: false

scan:
  <<: *defaults
  paths:
    - C:\\Test\\Path
performance:
  <<: *defaults
  mode: background
  max_threads: 4
""")
            temp_path = Path(f.name)

        try:
            config_data = config_manager._read_config_file(temp_path)
            assert config_data['scan']['max_depth'] == 10
            assert config_data['scan']['follow_symlinks'] is False
            assert config_data['performance']['max_depth'] == 10
            assert config_data['performance']['follow_symlinks'] is False
            assert config_data['performance']['mode'] == 'background'
        finally:
            temp_path.unlink()

    @pytest.mark.unit
    def test_json_configuration_parsing(self):
        """Test that JSON configuration files can be parsed correctly."""
        from disk_cleaner.src.disk_cleaner.config import ConfigurationManager
        import tempfile
        from pathlib import Path
        import json

        config_manager = ConfigurationManager()

        # Test JSON parsing
        config_dict = {
            'scan': {
                'paths': ['C:\\Test\\Path'],
                'max_depth': 5
            },
            'performance': {
                'mode': 'background',
                'max_threads': 8
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_dict, f)
            temp_path = Path(f.name)

            config_data = config_manager._read_config_file(temp_path)
            assert isinstance(config_data, dict)
            assert config_data == config_dict
        finally:
            temp_path.unlink()

    @pytest.mark.unit
    def test_configuration_schema_validation(self):
        """Test that configuration schema validation works correctly."""
        from disk_cleaner.src.disk_cleaner.config import ConfigurationManager, BasicConfigurationValidator
        import pytest

        validator = BasicConfigurationValidator()
        config_manager = ConfigurationManager()

        # Test valid configuration
        valid_config = config_manager.get_default_configuration()
        validator.validate(valid_config)  # Should not raise

        # Test missing required section
        invalid_config = valid_config.copy()
        del invalid_config['scan']
        with pytest.raises(ValueError, match="Missing required configuration section: scan"):
            validator.validate(invalid_config)

        # Test invalid section type
        invalid_config = valid_config.copy()
        invalid_config['scan'] = "invalid_string_instead_of_dict"
        with pytest.raises(ValueError, match="Configuration section 'scan' must be a dictionary"):
            validator.validate(invalid_config)

    @pytest.mark.unit
    def test_performance_settings_validation(self):
        """Test that performance settings are validated correctly."""
        from disk_cleaner.src.disk_cleaner.config import BasicConfigurationValidator
        import pytest

        validator = BasicConfigurationValidator()

        # Test valid performance settings
        valid_config = {
            'scan': {'paths': []},
            'performance': {
                'mode': 'background',
                'max_threads': 8,
                'memory_limit_mb': 1024,
                'cpu_limit_percent': 80
            },
            'classification': {'temp_file_age_days': 30},
            'ui': {'theme': 'auto'}
        }
        validator.validate(valid_config)  # Should not raise

        # Test invalid max_threads
        invalid_config = valid_config.copy()
        invalid_config['performance']['max_threads'] = 20  # Too high
        with pytest.raises(ValueError, match="max_threads must be an integer between 1 and 16"):
            validator.validate(invalid_config)

        invalid_config['performance']['max_threads'] = 0  # Too low
        with pytest.raises(ValueError, match="max_threads must be an integer between 1 and 16"):
            validator.validate(invalid_config)

        # Test invalid memory_limit_mb
        invalid_config = valid_config.copy()
        invalid_config['performance']['max_threads'] = 8  # Reset to valid
        invalid_config['performance']['memory_limit_mb'] = 0  # Invalid
        with pytest.raises(ValueError, match="memory_limit_mb must be a positive integer"):
            validator.validate(invalid_config)

    @pytest.mark.unit
    def test_configuration_manager_integration(self):
        """Test that ConfigurationManager integrates validation correctly."""
        from disk_cleaner.src.disk_cleaner.config import ConfigurationManager, BasicConfigurationValidator
        import pytest

        # Test with valid validator
        config_manager = ConfigurationManager()
        config = config_manager.get_default_configuration()
        assert isinstance(config, dict)
        assert 'scan' in config

        # Test with custom validator that always fails
        class FailingValidator(BasicConfigurationValidator):
            def validate(self, config):
                raise ValueError("Custom validation error")

        config_manager = ConfigurationManager(validator=FailingValidator())
        with pytest.raises(ValueError, match="Custom validation error"):
            config_manager.get_default_configuration()
