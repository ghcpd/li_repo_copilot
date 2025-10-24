"""
Plugin manager for extensible parser support.
"""

import importlib
import os
import sys
from typing import Dict, Type, List
from pathlib import Path

from .parsers.base_parser import BaseParser


class PluginManager:
    """
    Manages plugins for document parsers.
    
    Allows users to create custom parsers and register them dynamically.
    """
    
    def __init__(self, plugin_dir: str = None):
        """
        Initialize plugin manager.
        
        Args:
            plugin_dir: Directory containing plugin modules
        """
        self.plugin_dir = plugin_dir
        self._loaded_plugins: Dict[str, Type[BaseParser]] = {}
    
    def load_plugins(self) -> None:
        """Load all plugins from plugin directory."""
        if not self.plugin_dir or not os.path.exists(self.plugin_dir):
            return
        
        # Add plugin directory to path
        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)
        
        # Find all Python files in plugin directory
        plugin_files = [f for f in os.listdir(self.plugin_dir)
                       if f.endswith('.py') and not f.startswith('_')]
        
        # Load each plugin
        for plugin_file in plugin_files:
            module_name = plugin_file[:-3]
            try:
                module = importlib.import_module(module_name)
                self._register_plugin_from_module(module)
            except Exception as e:
                print(f"Warning: Failed to load plugin {module_name}: {e}")
    
    def _register_plugin_from_module(self, module) -> None:
        """Register parser classes from a plugin module."""
        # Look for BaseParser subclasses in the module
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            
            # Check if it's a class and subclass of BaseParser
            if (isinstance(attr, type) and 
                issubclass(attr, BaseParser) and 
                attr is not BaseParser):
                
                # Create instance to get supported formats
                try:
                    instance = attr()
                    for format_type in instance.supported_formats:
                        self._loaded_plugins[format_type] = attr
                except Exception as e:
                    print(f"Warning: Failed to instantiate {attr_name}: {e}")
    
    def get_plugin(self, format_type: str) -> Type[BaseParser]:
        """
        Get parser class for a format.
        
        Args:
            format_type: Document format identifier
            
        Returns:
            Parser class or None if not found
        """
        return self._loaded_plugins.get(format_type)
    
    def get_loaded_plugins(self) -> List[str]:
        """
        Get list of loaded plugin formats.
        
        Returns:
            List of format identifiers
        """
        return list(self._loaded_plugins.keys())
    
    def create_parser_instance(self, format_type: str) -> BaseParser:
        """
        Create parser instance for a format.
        
        Args:
            format_type: Document format identifier
            
        Returns:
            Parser instance or None if not found
        """
        parser_class = self.get_plugin(format_type)
        if parser_class:
            return parser_class()
        return None
