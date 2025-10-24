"""
Example plugin for PDF document parsing.

This demonstrates how to create a custom parser plugin.
"""

from doc_converter.parsers import BaseParser
from typing import Dict, Any


class PdfParser(BaseParser):
    """
    Example PDF parser plugin.
    
    To use this plugin:
    1. Install PyPDF2: pip install PyPDF2
    2. Place this file in your plugins directory
    3. Run: doc-converter document.pdf -o output.json -p ./plugins/
    """
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ['pdf']
        self._pypdf2 = None
    
    def _import_pypdf2(self):
        """Lazy import of PyPDF2 library."""
        if self._pypdf2 is None:
            try:
                import PyPDF2
                self._pypdf2 = PyPDF2
            except ImportError:
                raise ImportError(
                    "PyPDF2 is required for PDF parsing. "
                    "Install it with: pip install PyPDF2"
                )
        return self._pypdf2
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a PDF document."""
        return file_path.lower().endswith('.pdf')
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse PDF document.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Standardized document structure
        """
        PyPDF2 = self._import_pypdf2()
        
        result = self._create_base_structure('pdf')
        
        with open(file_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            # Extract metadata
            self._extract_metadata(pdf_reader, result['metadata'])
            
            # Parse content from each page
            position = 0
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                
                # Simple paragraph extraction
                paragraphs = text.split('\n\n')
                for para in paragraphs:
                    para = para.strip()
                    if para:
                        self._add_content_item(
                            result['content'],
                            'paragraph',
                            position,
                            text=para
                        )
                        position += 1
        
        return result
    
    def _extract_metadata(self, pdf_reader, metadata: Dict[str, Any]) -> None:
        """Extract PDF metadata."""
        info = pdf_reader.metadata
        
        if info:
            if info.get('/Title'):
                metadata['title'] = info['/Title']
            if info.get('/Author'):
                metadata['author'] = info['/Author']
            if info.get('/CreationDate'):
                metadata['created_date'] = info['/CreationDate']
            if info.get('/ModDate'):
                metadata['modified_date'] = info['/ModDate']
        
        metadata['page_count'] = len(pdf_reader.pages)


class MarkdownParser(BaseParser):
    """
    Example Markdown parser plugin.
    
    To use this plugin:
    1. Install markdown: pip install markdown
    2. Place this file in your plugins directory
    3. Run: doc-converter document.md -o output.json -p ./plugins/
    """
    
    def __init__(self):
        super().__init__()
        self.supported_formats = ['markdown', 'md']
        self._markdown = None
    
    def _import_markdown(self):
        """Lazy import of markdown library."""
        if self._markdown is None:
            try:
                import markdown
                self._markdown = markdown
            except ImportError:
                raise ImportError(
                    "markdown is required for Markdown parsing. "
                    "Install it with: pip install markdown"
                )
        return self._markdown
    
    def can_parse(self, file_path: str) -> bool:
        """Check if file is a Markdown document."""
        return file_path.lower().endswith(('.md', '.markdown'))
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse Markdown document.
        
        Args:
            file_path: Path to Markdown file
            
        Returns:
            Standardized document structure
        """
        markdown_lib = self._import_markdown()
        
        with open(file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        result = self._create_base_structure('markdown')
        
        # Convert to HTML and parse
        html_content = markdown_lib.markdown(md_content)
        
        # Use HTML parser for structure
        from doc_converter.parsers import HtmlParser
        html_parser = HtmlParser()
        
        # Create temp HTML file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', 
                                        delete=False) as tmp:
            tmp.write(html_content)
            tmp_path = tmp.name
        
        try:
            html_result = html_parser.parse(tmp_path)
            result['content'] = html_result['content']
        finally:
            import os
            os.unlink(tmp_path)
        
        # Update format
        result['metadata']['format'] = 'markdown'
        
        return result
