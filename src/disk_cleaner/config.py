"""Configuration Manager module for Disk Cleaner."""

from typing import Dict, Any


class ConfigurationManager:
    """Manages configuration loading, validation, and persistence."""

    def get_default_configuration(self) -> Dict[str, Any]:
        """Generate default configuration for the disk cleaner.

        Returns:
            Dictionary containing default configuration values
        """
        return {
            'scan': {
                'paths': [
                    'C:\\Users\\%USERNAME%\\Documents',
                    'C:\\Users\\%USERNAME%\\Downloads',
                    'C:\\Users\\%USERNAME%\\Desktop'
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
