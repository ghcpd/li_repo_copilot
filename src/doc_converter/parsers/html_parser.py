"""
HTML document parser.
"""

import os
from typing import Dict, Any, List
from datetime import datetime
from .base_parser import BaseParser


class HtmlParser(BaseParser):
    """Parser for HTML documents."""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ['html']
        self._bs4 = None
    
    def _import_bs4(self):
        """Lazy import of BeautifulSoup library."""
        if self._bs4 is None:
            try:
                from bs4 import BeautifulSoup
                self._bs4 = BeautifulSoup
            except ImportError:
                raise ImportError(
                    "beautifulsoup4 is required for HTML parsing. "
                    "Install it with: pip install beautifulsoup4"
                )
        return self._bs4
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is an HTML document."""
        return file_path.lower().endswith(('.html', '.htm'))
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse HTML document.
        
        Args:
            file_path: Path to HTML file
            
        Returns:
            Standardized document structure
        """
        BeautifulSoup = self._import_bs4()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = self._create_base_structure('html')
        
        # Extract metadata
        self._extract_metadata(soup, result['metadata'], file_path)
        
        # Parse content
        self._parse_body(soup, result['content'])
        
        return result
    
    def _extract_metadata(self, soup, metadata: Dict[str, Any], 
                         file_path: str) -> None:
        """Extract document metadata from HTML."""
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        # Meta tags
        author_meta = soup.find('meta', {'name': 'author'})
        if author_meta and author_meta.get('content'):
            metadata['author'] = author_meta['content']
        
        # File stats
        try:
            stat = os.stat(file_path)
            metadata['created_date'] = datetime.fromtimestamp(
                stat.st_ctime).isoformat()
            metadata['modified_date'] = datetime.fromtimestamp(
                stat.st_mtime).isoformat()
        except Exception:
            pass
        
        # Word count
        body = soup.find('body')
        if body:
            text = body.get_text()
            metadata['word_count'] = len(text.split())
    
    def _parse_body(self, soup, content: list) -> None:
        """Parse HTML body content."""
        body = soup.find('body')
        if not body:
            body = soup
        
        position = 0
        
        # Process all elements in order
        for element in body.descendants:
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                self._parse_heading(element, content, position)
                position += 1
            
            elif element.name == 'p':
                self._parse_paragraph(element, content, position)
                position += 1
            
            elif element.name in ['ul', 'ol']:
                self._parse_list(element, content, position)
                position += 1
            
            elif element.name == 'table':
                self._parse_table(element, content, position)
                position += 1
            
            elif element.name == 'img':
                self._parse_image(element, content, position)
                position += 1
            
            elif element.name == 'a':
                self._parse_link(element, content, position)
                position += 1
    
    def _parse_heading(self, element, content: list, position: int) -> None:
        """Parse heading element."""
        level = int(element.name[1])  # h1 -> 1, h2 -> 2, etc.
        text = element.get_text().strip()
        
        if not text:
            return
        
        style = self._extract_style(element)
        
        self._add_content_item(
            content, 'heading', position,
            level=level,
            text=text,
            style=style
        )
    
    def _parse_paragraph(self, element, content: list, position: int) -> None:
        """Parse paragraph element."""
        text = element.get_text().strip()
        
        if not text:
            return
        
        style = self._extract_style(element)
        
        self._add_content_item(
            content, 'paragraph', position,
            text=text,
            style=style
        )
    
    def _parse_list(self, element, content: list, position: int) -> None:
        """Parse list element."""
        ordered = element.name == 'ol'
        items = []
        
        for li in element.find_all('li', recursive=False):
            item_text = li.get_text().strip()
            items.append({
                'text': item_text,
                'style': self._extract_style(li)
            })
        
        if items:
            self._add_content_item(
                content, 'list', position,
                ordered=ordered,
                items=items
            )
    
    def _parse_table(self, element, content: list, position: int) -> None:
        """Parse table element."""
        rows_data = []
        headers = []
        
        # Extract headers
        thead = element.find('thead')
        if thead:
            header_row = thead.find('tr')
            if header_row:
                headers = [th.get_text().strip() 
                          for th in header_row.find_all(['th', 'td'])]
        
        # Extract rows
        tbody = element.find('tbody') or element
        for row in tbody.find_all('tr'):
            row_data = [cell.get_text().strip() 
                       for cell in row.find_all(['td', 'th'])]
            if row_data:
                rows_data.append(row_data)
        
        if rows_data:
            self._add_content_item(
                content, 'table', position,
                headers=headers,
                rows=rows_data
            )
    
    def _parse_image(self, element, content: list, position: int) -> None:
        """Parse image element."""
        src = element.get('src', '')
        alt = element.get('alt', '')
        width = element.get('width')
        height = element.get('height')
        
        item_data = {
            'src': src,
            'alt': alt
        }
        
        if width:
            try:
                item_data['width'] = float(width)
            except ValueError:
                pass
        
        if height:
            try:
                item_data['height'] = float(height)
            except ValueError:
                pass
        
        self._add_content_item(content, 'image', position, **item_data)
    
    def _parse_link(self, element, content: list, position: int) -> None:
        """Parse link element."""
        href = element.get('href', '')
        text = element.get_text().strip()
        target = element.get('target', '')
        
        if href:
            self._add_content_item(
                content, 'link', position,
                text=text,
                href=href,
                target=target
            )
    
    def _extract_style(self, element) -> Dict[str, Any]:
        """Extract style information from element."""
        style = {}
        
        # Check for bold
        if element.find(['b', 'strong']):
            style['bold'] = True
        
        # Check for italic
        if element.find(['i', 'em']):
            style['italic'] = True
        
        # Check for underline
        if element.find('u'):
            style['underline'] = True
        
        # Check inline styles
        style_attr = element.get('style', '')
        if 'color:' in style_attr:
            # Simple color extraction
            parts = style_attr.split('color:')
            if len(parts) > 1:
                color = parts[1].split(';')[0].strip()
                style['color'] = color
        
        return style
