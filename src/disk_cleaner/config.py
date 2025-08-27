"""Configuration Manager module for Disk Cleaner."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Protocol
import os


class ConfigurationSource(Protocol):
    """Protocol for configuration data sources."""

    def load(self) -> Dict[str, Any]:
        """Load configuration data."""
        ...


class DefaultConfigurationSource:
    """Provides default configuration values."""

    def load(self) -> Dict[str, Any]:
        """Generate default configuration for the disk cleaner.

        Returns:
            Dictionary containing default configuration values
        """
        return {
            'scan': {
                'paths': [
                    os.path.expandvars(r'%USERPROFILE%\Documents'),
                    os.path.expandvars(r'%USERPROFILE%\Downloads'),
                    os.path.expandvars(r'%USERPROFILE%\Desktop')
                ],
                'exclude_patterns': [
                    '**/.git/**',
                    '**/__pycache__/**',
                    '**/node_modules/**'
                ],
                'max_depth': 10,
                'follow_symlinks': False
            },
            'performance': {
                'mode': 'background',
                'max_threads': 4,
                'memory_limit_mb': 1024,
                'cpu_limit_percent': 80,
                'io_throttling': True
            },
            'classification': {
                'temp_file_age_days': 30,
                'large_file_threshold_mb': 500,
                'dev_folder_min_size_mb': 50,
                'exclude_extensions': ['.tmp', '.bak', '.old']
            },
            'ui': {
                'theme': 'auto',
                'show_progress': True,
                'verbose_logging': False,
                'color_output': True
            }
        }


class ConfigurationValidator(ABC):
    """Abstract base class for configuration validators."""

    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> None:
        """Validate configuration data.

        Args:
            config: Configuration dictionary to validate

        Raises:
            ValueError: If configuration is invalid
        """
        pass


class BasicConfigurationValidator(ConfigurationValidator):
    """Basic validator for configuration data."""

    def validate(self, config: Dict[str, Any]) -> None:
        """Validate configuration data."""
        required_sections = ['scan', 'performance', 'classification', 'ui']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")

            if not isinstance(config[section], dict):
                raise ValueError(f"Configuration section '{section}' must be a dictionary")

        # Validate performance settings
        perf = config['performance']
        if 'max_threads' in perf:
            if not isinstance(perf['max_threads'], int) or not (1 <= perf['max_threads'] <= 16):
                raise ValueError("max_threads must be an integer between 1 and 16")

        if 'memory_limit_mb' in perf:
            if not isinstance(perf['memory_limit_mb'], int) or perf['memory_limit_mb'] <= 0:
                raise ValueError("memory_limit_mb must be a positive integer")


class ConfigurationManager:
    """Manages configuration loading, validation, and persistence."""

    def __init__(self,
                 config_source: ConfigurationSource = None,
                 validator: ConfigurationValidator = None):
        """Initialize ConfigurationManager.

        Args:
            config_source: Source for configuration data (uses default if None)
            validator: Validator for configuration data (uses default if None)
        """
        self._config_source = config_source or DefaultConfigurationSource()
        self._validator = validator or BasicConfigurationValidator()

    def _discover_config_files(self) -> List[Path]:
        """Discover configuration files in standard locations.

        Returns:
            List of paths to potential configuration files
        """
        from pathlib import Path
        import os

        config_paths = []

        # Standard locations for configuration files
        search_locations = [
            os.path.expandvars(r'%APPDATA%\disk_cleaner'),
            os.path.expandvars(r'%LOCALAPPDATA%\disk_cleaner'),
            Path.cwd(),  # Current working directory
            Path.home() / '.disk_cleaner'  # Home directory
        ]

        # Possible configuration file names
        config_names = ['config.yaml', 'config.yml', 'config.json']

        for location in search_locations:
            location_path = Path(location)
            if location_path.exists():
                for config_name in config_names:
                    config_path = location_path / config_name
                    if config_path.exists():
                        config_paths.append(config_path)

        return config_paths
