"""
Unit tests for plugin manager.
"""

import os
import sys
import tempfile
import pytest
from doc_converter.plugin_manager import PluginManager
from doc_converter.parsers import BaseParser


class TestPluginManager:
    """Test plugin manager functionality."""
    
    def test_init_with_directory(self):
        """Test initialization with plugin directory."""
        temp_dir = tempfile.mkdtemp()
        try:
            manager = PluginManager(temp_dir)
            assert manager.plugin_dir == temp_dir
        finally:
            os.rmdir(temp_dir)
    
    def test_init_without_directory(self):
        """Test initialization without plugin directory."""
        manager = PluginManager()
        assert manager.plugin_dir is None
    
    def test_load_plugins_no_directory(self):
        """Test loading plugins with no directory."""
        manager = PluginManager()
        manager.load_plugins()
        assert len(manager.get_loaded_plugins()) == 0
    
    def test_load_plugins_empty_directory(self):
        """Test loading plugins from empty directory."""
        temp_dir = tempfile.mkdtemp()
        try:
            manager = PluginManager(temp_dir)
            manager.load_plugins()
            assert len(manager.get_loaded_plugins()) == 0
        finally:
            os.rmdir(temp_dir)
    
    def test_load_plugins_with_custom_parser(self):
        """Test loading custom parser plugin."""
        temp_dir = tempfile.mkdtemp()
        
        # Create a simple plugin file
        plugin_code = '''
from doc_converter.parsers import BaseParser

class CustomParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.supported_formats = ['custom']
    
    def can_parse(self, file_path):
        return file_path.endswith('.custom')
    
    def parse(self, file_path):
        return self._create_base_structure('custom')
'''
        
        plugin_file = os.path.join(temp_dir, 'custom_parser.py')
        with open(plugin_file, 'w') as f:
            f.write(plugin_code)
        
        try:
            # Add temp_dir to path for import
            sys.path.insert(0, temp_dir)
            
            manager = PluginManager(temp_dir)
            manager.load_plugins()
            
            plugins = manager.get_loaded_plugins()
            assert 'custom' in plugins
            
        finally:
            # Cleanup
            sys.path.remove(temp_dir)
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_get_plugin(self):
        """Test getting parser class for format."""
        temp_dir = tempfile.mkdtemp()
        
        plugin_code = '''
from doc_converter.parsers import BaseParser

class TestParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.supported_formats = ['test']
    
    def can_parse(self, file_path):
        return True
    
    def parse(self, file_path):
        return {}
'''
        
        plugin_file = os.path.join(temp_dir, 'test_parser.py')
        with open(plugin_file, 'w') as f:
            f.write(plugin_code)
        
        try:
            sys.path.insert(0, temp_dir)
            
            manager = PluginManager(temp_dir)
            manager.load_plugins()
            
            parser_class = manager.get_plugin('test')
            assert parser_class is not None
            
        finally:
            sys.path.remove(temp_dir)
            import shutil
            shutil.rmtree(temp_dir)
    
    def test_create_parser_instance(self):
        """Test creating parser instance."""
        temp_dir = tempfile.mkdtemp()
        
        plugin_code = '''
from doc_converter.parsers import BaseParser

class InstanceParser(BaseParser):
    def __init__(self):
        super().__init__()
        self.supported_formats = ['inst']
    
    def can_parse(self, file_path):
        return True
    
    def parse(self, file_path):
        return {}
'''
        
        plugin_file = os.path.join(temp_dir, 'instance_parser.py')
        with open(plugin_file, 'w') as f:
            f.write(plugin_code)
        
        try:
            sys.path.insert(0, temp_dir)
            
            manager = PluginManager(temp_dir)
            manager.load_plugins()
            
            parser = manager.create_parser_instance('inst')
            assert parser is not None
            assert isinstance(parser, BaseParser)
            
        finally:
            sys.path.remove(temp_dir)
            import shutil
            shutil.rmtree(temp_dir)
