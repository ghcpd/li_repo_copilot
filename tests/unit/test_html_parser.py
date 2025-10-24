"""
Unit tests for HTML parser.
"""

import os
import tempfile
import pytest
from doc_converter.parsers.html_parser import HtmlParser


class TestHtmlParser:
    """Test HTML parser functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.parser = HtmlParser()
    
    def test_can_parse_html(self):
        """Test can_parse for HTML files."""
        assert self.parser.can_parse('page.html') is True
        assert self.parser.can_parse('page.htm') is True
        assert self.parser.can_parse('PAGE.HTML') is True
    
    def test_cannot_parse_other_formats(self):
        """Test can_parse rejects other formats."""
        assert self.parser.can_parse('document.docx') is False
        assert self.parser.can_parse('file.txt') is False
    
    def test_parse_simple_html(self):
        """Test parsing simple HTML."""
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Test Document</title></head>
        <body>
            <h1>Main Heading</h1>
            <p>This is a paragraph.</p>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            assert result['metadata']['format'] == 'html'
            assert result['metadata']['title'] == 'Test Document'
            assert len(result['content']) > 0
        finally:
            os.unlink(temp_path)
    
    def test_parse_headings(self):
        """Test parsing HTML headings."""
        html = """
        <html><body>
            <h1>Heading 1</h1>
            <h2>Heading 2</h2>
            <h3>Heading 3</h3>
        </body></html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            headings = [item for item in result['content'] if item['type'] == 'heading']
            assert len(headings) == 3
            assert headings[0]['level'] == 1
            assert headings[1]['level'] == 2
            assert headings[2]['level'] == 3
        finally:
            os.unlink(temp_path)
    
    def test_parse_list(self):
        """Test parsing HTML lists."""
        html = """
        <html><body>
            <ul>
                <li>Item 1</li>
                <li>Item 2</li>
            </ul>
            <ol>
                <li>Ordered 1</li>
                <li>Ordered 2</li>
            </ol>
        </body></html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            lists = [item for item in result['content'] if item['type'] == 'list']
            assert len(lists) == 2
            assert lists[0]['ordered'] is False
            assert lists[1]['ordered'] is True
        finally:
            os.unlink(temp_path)
    
    def test_parse_table(self):
        """Test parsing HTML tables."""
        html = """
        <html><body>
            <table>
                <thead>
                    <tr><th>Header 1</th><th>Header 2</th></tr>
                </thead>
                <tbody>
                    <tr><td>Data 1</td><td>Data 2</td></tr>
                </tbody>
            </table>
        </body></html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            tables = [item for item in result['content'] if item['type'] == 'table']
            assert len(tables) == 1
            assert len(tables[0]['headers']) == 2
            assert len(tables[0]['rows']) >= 1
        finally:
            os.unlink(temp_path)
    
    def test_parse_image(self):
        """Test parsing HTML images."""
        html = """
        <html><body>
            <img src="image.png" alt="Test Image" width="500" height="300">
        </body></html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            images = [item for item in result['content'] if item['type'] == 'image']
            assert len(images) == 1
            assert images[0]['src'] == 'image.png'
            assert images[0]['alt'] == 'Test Image'
            assert images[0]['width'] == 500.0
        finally:
            os.unlink(temp_path)
    
    def test_parse_link(self):
        """Test parsing HTML links."""
        html = """
        <html><body>
            <a href="https://example.com" target="_blank">Click here</a>
        </body></html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            f.write(html)
            temp_path = f.name
        
        try:
            result = self.parser.parse(temp_path)
            
            links = [item for item in result['content'] if item['type'] == 'link']
            assert len(links) == 1
            assert links[0]['href'] == 'https://example.com'
            assert links[0]['target'] == '_blank'
        finally:
            os.unlink(temp_path)
    
    def test_extract_style(self):
        """Test style extraction."""
        html = '<p><b>Bold</b> <i>Italic</i> <u>Underline</u></p>'
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        p = soup.find('p')
        
        style = self.parser._extract_style(p)
        assert style.get('bold') is True
        assert style.get('italic') is True
        assert style.get('underline') is True
