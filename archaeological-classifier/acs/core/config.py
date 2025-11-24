"""
Configuration Storage Module
============================

Persistent storage for user settings like API keys.
"""

import json
import os
from typing import Dict, Optional, Any


class ConfigManager:
    """
    Manages persistent configuration settings.

    Stores settings in a JSON file for persistence across sessions.
    """

    def __init__(self, config_path: str = None):
        """Initialize configuration manager."""
        if config_path is None:
            # Store in user's home directory
            config_dir = os.path.join(os.path.expanduser('~'), '.acs')
            os.makedirs(config_dir, exist_ok=True)
            config_path = os.path.join(config_dir, 'config.json')

        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """Set a configuration value and persist it."""
        self.config[key] = value
        self._save_config()

    def delete(self, key: str):
        """Delete a configuration key."""
        if key in self.config:
            del self.config[key]
            self._save_config()

    def get_api_key(self) -> Optional[str]:
        """Get stored Anthropic API key."""
        return self.get('anthropic_api_key')

    def set_api_key(self, api_key: str):
        """Set Anthropic API key."""
        self.set('anthropic_api_key', api_key)

    def has_api_key(self) -> bool:
        """Check if API key is configured."""
        key = self.get_api_key()
        return key is not None and len(key) > 0

    def get_all(self) -> Dict:
        """Get all configuration values (excluding sensitive data)."""
        safe_config = self.config.copy()
        # Mask API key for security
        if 'anthropic_api_key' in safe_config:
            key = safe_config['anthropic_api_key']
            if key:
                safe_config['anthropic_api_key'] = key[:8] + '...' + key[-4:] if len(key) > 12 else '***'
        return safe_config


# Global instance
_config_manager = None


def get_config() -> ConfigManager:
    """Get or create global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
