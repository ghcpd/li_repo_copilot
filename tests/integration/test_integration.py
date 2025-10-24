"""
Integration tests for document converter.
"""

import os
import tempfile
import json
import shutil
import pytest
from doc_converter import DocumentConverter


class TestIntegration:
    """Integration tests for end-to-end conversion."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.converter = DocumentConverter()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_full_html_conversion(self):
        """Test complete HTML to JSON conversion."""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Integration Test Document</title>
            <meta name="author" content="Test Author">
        </head>
        <body>
            <h1>Main Title</h1>
            <p>This is a paragraph with <b>bold</b> and <i>italic</i> text.</p>
            
            <h2>Section 1</h2>
            <p>Another paragraph here.</p>
            
            <ul>
                <li>List item 1</li>
                <li>List item 2</li>
                <li>List item 3</li>
            </ul>
            
            <table>
                <thead>
                    <tr><th>Name</th><th>Value</th></tr>
                </thead>
                <tbody>
                    <tr><td>Item A</td><td>100</td></tr>
                    <tr><td>Item B</td><td>200</td></tr>
                </tbody>
            </table>
            
            <a href="https://example.com">External Link</a>
            <img src="test.png" alt="Test Image" width="400" height="300">
        </body>
        </html>
        """
        
        input_file = os.path.join(self.temp_dir, 'test.html')
        output_file = os.path.join(self.temp_dir, 'test.json')
        
        with open(input_file, 'w') as f:
            f.write(html_content)
        
        # Convert
        result = self.converter.convert_file(input_file, output_file)
        
        # Verify metadata
        assert result['metadata']['format'] == 'html'
        assert result['metadata']['title'] == 'Integration Test Document'
        assert result['metadata']['author'] == 'Test Author'
        
        # Verify content types
        content_types = [item['type'] for item in result['content']]
        assert 'heading' in content_types
        assert 'paragraph' in content_types
        assert 'list' in content_types
        assert 'table' in content_types
        assert 'link' in content_types
        assert 'image' in content_types
        
        # Verify file was saved
        assert os.path.exists(output_file)
        with open(output_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data['metadata']['format'] == 'html'
    
    def test_full_txt_conversion(self):
        """Test complete TXT to JSON conversion."""
        txt_content = """# Main Document Title

This is the introduction paragraph with some important information.

## Section 1: Getting Started

This section covers the basics.

* First item in list
* Second item in list
* Third item in list

## Section 2: Data

| Name   | Age | City     |
|--------|-----|----------|
| Alice  | 30  | New York |
| Bob    | 25  | Boston   |

### Subsection 2.1

More detailed content goes here.

1. Step one
2. Step two
3. Step three
"""
        
        input_file = os.path.join(self.temp_dir, 'test.txt')
        output_file = os.path.join(self.temp_dir, 'test.json')
        
        with open(input_file, 'w') as f:
            f.write(txt_content)
        
        # Convert
        result = self.converter.convert_file(input_file, output_file)
        
        # Verify metadata
        assert result['metadata']['format'] == 'txt'
        assert 'word_count' in result['metadata']
        
        # Verify headings
        headings = [item for item in result['content'] if item['type'] == 'heading']
        assert len(headings) >= 3
        
        # Verify different heading levels
        levels = [h['level'] for h in headings]
        assert 1 in levels
        assert 2 in levels
        
        # Verify lists
        lists = [item for item in result['content'] if item['type'] == 'list']
        assert len(lists) >= 2
        
        # Check unordered and ordered lists
        has_unordered = any(not l['ordered'] for l in lists)
        has_ordered = any(l['ordered'] for l in lists)
        assert has_unordered
        assert has_ordered
        
        # Verify table
        tables = [item for item in result['content'] if item['type'] == 'table']
        assert len(tables) >= 1
        
        # Verify validation
        assert self.converter.validate_json(result)
    
    def test_batch_conversion_mixed_formats(self):
        """Test batch conversion of mixed format files."""
        # Create multiple test files
        html_file = os.path.join(self.temp_dir, 'doc1.html')
        txt_file = os.path.join(self.temp_dir, 'doc2.txt')
        
        with open(html_file, 'w') as f:
            f.write('<html><body><h1>HTML Doc</h1><p>Content</p></body></html>')
        
        with open(txt_file, 'w') as f:
            f.write('# Text Doc\n\nSome content here.')
        
        # Create output directory
        output_dir = os.path.join(self.temp_dir, 'output')
        os.makedirs(output_dir)
        
        # Batch convert
        results = self.converter.convert_batch(self.temp_dir, output_dir)
        
        # Verify results
        assert len(results) == 2
        assert all(r['status'] == 'success' for r in results)
        
        # Verify output files
        assert os.path.exists(os.path.join(output_dir, 'doc1.json'))
        assert os.path.exists(os.path.join(output_dir, 'doc2.json'))
        
        # Verify content
        with open(os.path.join(output_dir, 'doc1.json'), 'r') as f:
            html_result = json.load(f)
        assert html_result['metadata']['format'] == 'html'
        
        with open(os.path.join(output_dir, 'doc2.json'), 'r') as f:
            txt_result = json.load(f)
        assert txt_result['metadata']['format'] == 'txt'
