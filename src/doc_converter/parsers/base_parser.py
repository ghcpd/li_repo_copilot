"""
Base parser interface for document parsers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime


class BaseParser(ABC):
    """Abstract base class for document parsers."""
    
    def __init__(self):
        self.supported_formats = []
    
    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a document and return standardized JSON format.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing parsed document in standard format
        """
        pass
    
    @abstractmethod
    def can_parse(self, file_path: str) -> bool:
        """
        Check if this parser can handle the given file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            True if parser can handle the file, False otherwise
        """
        pass
    
    def _create_base_structure(self, format_type: str) -> Dict[str, Any]:
        """
        Create base document structure.
        
        Args:
            format_type: Document format (docx, html, txt)
            
        Returns:
            Base document structure dictionary
        """
        return {
            "metadata": {
                "format": format_type,
                "created_date": datetime.now().isoformat(),
                "modified_date": datetime.now().isoformat()
            },
            "content": []
        }
    
    def _add_content_item(self, content: list, item_type: str, 
                         position: int, **kwargs) -> None:
        """
        Add a content item to the document.
        
        Args:
            content: Content list to add to
            item_type: Type of content item
            position: Position index
            **kwargs: Additional item properties
        """
        item = {
            "type": item_type,
            "position": {"index": position}
        }
        item.update(kwargs)
        content.append(item)
