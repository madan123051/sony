"""Internationalization module for PMCA GUI"""
import json
import os
from typing import Dict, Any

class I18nManager:
    """Internationalization manager"""
    
    def __init__(self):
        self.current_language = 'en'
        self.translations = {}
        self.supported_languages = ['en', 'zh-cn']
        self.language_names = {
            'en': 'English',
            'zh-cn': '中文 (简体)'
        }
        self.load_translations()
        self.load_saved_language()
    
    def load_saved_language(self):
        """Load saved language from config"""
        try:
            from pmca.config_manager import config_manager
            saved_language = config_manager.get_language()
            if saved_language in self.supported_languages:
                self.current_language = saved_language
        except ImportError:
            pass
    
    def load_translations(self):
        """Load all translation files"""
        current_dir = os.path.dirname(__file__)
        for lang in self.supported_languages:
            lang_file = os.path.join(current_dir, f'{lang}.json')
            if os.path.exists(lang_file):
                try:
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        self.translations[lang] = json.load(f)
                except Exception as e:
                    print(f"Error loading translation file {lang_file}: {e}")
                    self.translations[lang] = {}
            else:
                self.translations[lang] = {}
    
    def set_language(self, language: str):
        """Set current language and save to config"""
        if language in self.supported_languages:
            self.current_language = language
            try:
                from pmca.config_manager import config_manager
                config_manager.set_language(language)
            except ImportError:
                pass
            return True
        return False
    
    def get_language(self) -> str:
        """Get current language"""
        return self.current_language
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get supported languages with their display names"""
        return self.language_names
    
    def _(self, key: str, **kwargs) -> str:
        """Get translated text"""
        translation = self.translations.get(self.current_language, {}).get(key)
        
        # Fallback to English if translation not found
        if translation is None:
            translation = self.translations.get('en', {}).get(key)
        
        # Fallback to key if no translation found
        if translation is None:
            translation = key
        
        # Format with provided kwargs
        try:
            return translation.format(**kwargs)
        except:
            return translation

# Global i18n manager instance
i18n_manager = I18nManager()

# Convenience function
def _(key: str, **kwargs) -> str:
    """Get translated text - convenience function"""
    return i18n_manager._(key, **kwargs)