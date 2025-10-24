"""
Plain text document parser.
"""

import os
import re
from typing import Dict, Any, List
from datetime import datetime
from .base_parser import BaseParser


class TxtParser(BaseParser):
    """Parser for plain text documents."""
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ['txt']
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a plain text document."""
        return file_path.lower().endswith(('.txt', '.text'))
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse plain text document.
        
        Args:
            file_path: Path to text file
            
        Returns:
            Standardized document structure
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content_text = f.read()
        
        result = self._create_base_structure('txt')
        
        # Extract metadata
        self._extract_metadata(content_text, result['metadata'], file_path)
        
        # Parse content
        self._parse_text(content_text, result['content'])
        
        return result
    
    def _extract_metadata(self, text: str, metadata: Dict[str, Any], 
                         file_path: str) -> None:
        """Extract document metadata from text file."""
        # Try to extract title from first line
        lines = text.split('\n')
        if lines:
            first_line = lines[0].strip()
            if first_line and len(first_line) < 100:
                metadata['title'] = first_line
        
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
        metadata['word_count'] = len(text.split())
    
    def _parse_text(self, text: str, content: list) -> None:
        """Parse text content."""
        lines = text.split('\n')
        position = 0
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if not line:
                i += 1
                continue
            
            # Check if it's a heading (all caps, short line, or starts with #)
            if self._is_heading(line):
                level = self._get_heading_level(line)
                clean_text = line.lstrip('#').strip()
                
                self._add_content_item(
                    content, 'heading', position,
                    level=level,
                    text=clean_text
                )
                position += 1
                i += 1
                continue
            
            # Check if it's a list item
            if self._is_list_item(line):
                items, consumed = self._parse_list_block(lines[i:])
                if items:
                    ordered = self._is_ordered_list(lines[i])
                    self._add_content_item(
                        content, 'list', position,
                        ordered=ordered,
                        items=items
                    )
                    position += 1
                    i += consumed
                    continue
            
            # Check if it's a table
            if '|' in line:
                rows, consumed = self._parse_table_block(lines[i:])
                if rows and len(rows) > 1:
                    headers = rows[0] if rows else []
                    self._add_content_item(
                        content, 'table', position,
                        headers=headers,
                        rows=rows
                    )
                    position += 1
                    i += consumed
                    continue
            
            # Otherwise, treat as paragraph
            para_text, consumed = self._parse_paragraph_block(lines[i:])
            if para_text:
                self._add_content_item(
                    content, 'paragraph', position,
                    text=para_text
                )
                position += 1
                i += consumed
            else:
                i += 1
    
    def _is_heading(self, line: str) -> bool:
        """Check if line is a heading."""
        # Check for markdown-style headings
        if line.startswith('#'):
            return True
        
        # Check for all caps (and short enough to be a heading)
        if line.isupper() and len(line) < 80:
            return True
        
        return False
    
    def _get_heading_level(self, line: str) -> int:
        """Determine heading level."""
        if line.startswith('#'):
            # Count leading # symbols
            level = 0
            for char in line:
                if char == '#':
                    level += 1
                else:
                    break
            return min(level, 6)
        
        return 1
    
    def _is_list_item(self, line: str) -> bool:
        """Check if line is a list item."""
        # Unordered list markers
        if re.match(r'^[\*\-\+]\s+', line):
            return True
        
        # Ordered list markers
        if re.match(r'^\d+[\.\)]\s+', line):
            return True
        
        return False
    
    def _is_ordered_list(self, line: str) -> bool:
        """Check if list is ordered."""
        return bool(re.match(r'^\d+[\.\)]\s+', line))
    
    def _parse_list_block(self, lines: List[str]) -> tuple:
        """Parse consecutive list items."""
        items = []
        consumed = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                break
            
            if self._is_list_item(stripped):
                # Remove list marker
                text = re.sub(r'^[\*\-\+\d\.\)]+\s+', '', stripped)
                items.append({'text': text})
                consumed += 1
            else:
                break
        
        return items, consumed
    
    def _parse_table_block(self, lines: List[str]) -> tuple:
        """Parse table block (markdown-style)."""
        rows = []
        consumed = 0
        
        for line in lines:
            stripped = line.strip()
            if not stripped or '|' not in stripped:
                break
            
            # Skip separator lines (e.g., |---|---|)
            if re.match(r'^\|[\s\-\|]+\|$', stripped):
                consumed += 1
                continue
            
            # Parse table row
            cells = [cell.strip() for cell in stripped.split('|')]
            # Remove empty cells from start/end
            cells = [c for c in cells if c]
            
            if cells:
                rows.append(cells)
            consumed += 1
        
        return rows, consumed
    
    def _parse_paragraph_block(self, lines: List[str]) -> tuple:
        """Parse paragraph (consecutive non-empty lines)."""
        para_lines = []
        consumed = 0
        
        for line in lines:
            stripped = line.strip()
            
            if not stripped:
                break
            
            # Stop at headings, lists, or tables
            if self._is_heading(stripped) or \
               self._is_list_item(stripped) or \
               '|' in stripped:
                break
            
            para_lines.append(stripped)
            consumed += 1
        
        text = ' '.join(para_lines)
        return text, consumed
