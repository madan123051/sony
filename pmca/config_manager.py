"""Configuration management for PMCA GUI"""
import json
import os
from pathlib import Path

class ConfigManager:
    """Configuration manager for saving and loading user preferences"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.pmca'
        self.config_file = self.config_dir / 'config.json'
        self.config = self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        # Default configuration
        return {
            'language': 'en'
        }
    
    def save_config(self):
        """Save configuration to file"""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_language(self):
        """Get current language setting"""
        return self.config.get('language', 'en')
    
    def set_language(self, language):
        """Set language setting"""
        self.config['language'] = language
        return self.save_config()

# Global config manager instance
config_manager = ConfigManager()