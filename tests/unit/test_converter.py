"""
Unit tests for document converter main class.
"""

import os
import tempfile
import json
import pytest
from doc_converter import DocumentConverter
from doc_converter.parsers import BaseParser


class TestDocumentConverter:
    """Test main converter functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.converter = DocumentConverter()
    
    def test_register_parser(self):
        """Test parser registration."""
        class TestParser(BaseParser):
            def __init__(self):
                super().__init__()
                self.supported_formats = ['test']
            
            def can_parse(self, file_path):
                return file_path.endswith('.test')
            
            def parse(self, file_path):
                return self._create_base_structure('test')
        
        self.converter.register_parser('test', TestParser())
        assert 'test' in self.converter.get_supported_formats()
    
    def test_get_supported_formats(self):
        """Test getting supported formats."""
        formats = self.converter.get_supported_formats()
        assert 'docx' in formats
        assert 'html' in formats
        assert 'txt' in formats
    
    def test_convert_file_txt(self):
        """Test converting a TXT file."""
        content = "# Test Heading\n\nThis is a test paragraph."
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            temp_path = f.name
        
        output_path = temp_path.replace('.txt', '.json')
        
        try:
            result = self.converter.convert_file(temp_path, output_path)
            
            assert result['metadata']['format'] == 'txt'
            assert 'source_file' in result['metadata']
            assert os.path.exists(output_path)
            
            # Verify JSON file
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            assert saved_data['metadata']['format'] == 'txt'
            
        finally:
            os.unlink(temp_path)
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    def test_convert_file_html(self):
        """Test converting an HTML file."""
        html = "<html><body><h1>Test</h1><p>Content</p></body></html>"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            temp_path = f.name
        
        try:
            result = self.converter.convert_file(temp_path)
            
            assert result['metadata']['format'] == 'html'
            assert len(result['content']) > 0
        finally:
            os.unlink(temp_path)
    
    def test_convert_file_not_found(self):
        """Test error handling for missing file."""
        with pytest.raises(FileNotFoundError):
            self.converter.convert_file('nonexistent.txt')
    
    def test_convert_file_unsupported_format(self):
        """Test error handling for unsupported format."""
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.unknown', delete=False) as f:
            f.write(b'\x00\x01\x02')
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                self.converter.convert_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_convert_batch(self):
        """Test batch conversion."""
        # Create temp directory with files
        temp_dir = tempfile.mkdtemp()
        output_dir = tempfile.mkdtemp()
        
        try:
            # Create test files
            for i in range(3):
                file_path = os.path.join(temp_dir, f'test{i}.txt')
                with open(file_path, 'w') as f:
                    f.write(f"Test content {i}")
            
            # Convert batch
            results = self.converter.convert_batch(temp_dir, output_dir)
            
            assert len(results) == 3
            assert all(r['status'] == 'success' for r in results)
            
            # Check output files
            output_files = os.listdir(output_dir)
            assert len(output_files) == 3
            
        finally:
            # Cleanup
            import shutil
            shutil.rmtree(temp_dir)
            shutil.rmtree(output_dir)
    
    def test_convert_batch_not_directory(self):
        """Test error handling for invalid directory."""
        with pytest.raises(NotADirectoryError):
            self.converter.convert_batch('not_a_directory', 'output')
    
    def test_validate_json(self):
        """Test JSON validation."""
        valid_data = {
            'metadata': {'format': 'txt'},
            'content': [
                {
                    'type': 'paragraph',
                    'position': {'index': 0},
                    'text': 'Test'
                }
            ]
        }
        
        assert self.converter.validate_json(valid_data) is True
        
        # Invalid data
        invalid_data = {'metadata': {}}
        assert self.converter.validate_json(invalid_data) is False
