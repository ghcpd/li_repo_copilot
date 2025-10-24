"""
Main document converter module with plugin architecture support.
"""

import os
import json
from typing import Dict, Any, List, Optional, Type
from pathlib import Path

from .format_detector import FormatDetector
from .parsers.base_parser import BaseParser
from .parsers.docx_parser import DocxParser
from .parsers.html_parser import HtmlParser
from .parsers.txt_parser import TxtParser


class DocumentConverter:
    """
    Main converter class for processing documents.
    
    Supports plugin architecture for extensibility.
    """
    
    def __init__(self):
        self._parsers: Dict[str, BaseParser] = {}
        self._register_default_parsers()
    
    def _register_default_parsers(self) -> None:
        """Register default document parsers."""
        self.register_parser('docx', DocxParser())
        self.register_parser('html', HtmlParser())
        self.register_parser('txt', TxtParser())
    
    def register_parser(self, format_type: str, parser: BaseParser) -> None:
        """
        Register a parser for a specific format (plugin architecture).
        
        Args:
            format_type: Document format identifier
            parser: Parser instance
        """
        self._parsers[format_type] = parser
    
    def convert_file(self, file_path: str, 
                    output_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Convert a single document file to JSON format.
        
        Args:
            file_path: Path to input document
            output_path: Optional path to save JSON output
            
        Returns:
            Standardized document structure as dictionary
            
        Raises:
            ValueError: If format is not supported
            FileNotFoundError: If file does not exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Detect format
        format_type = FormatDetector.detect_format(file_path)
        
        if not format_type:
            raise ValueError(
                f"Unable to detect format for file: {file_path}"
            )
        
        if format_type not in self._parsers:
            raise ValueError(
                f"No parser registered for format: {format_type}"
            )
        
        # Parse document
        parser = self._parsers[format_type]
        result = parser.parse(file_path)
        
        # Add source file info
        result['metadata']['source_file'] = os.path.basename(file_path)
        result['metadata']['source_path'] = os.path.abspath(file_path)
        
        # Save to file if output path specified
        if output_path:
            self._save_json(result, output_path)
        
        return result
    
    def convert_batch(self, input_dir: str, output_dir: str,
                     recursive: bool = False) -> List[Dict[str, Any]]:
        """
        Convert multiple documents in a directory.
        
        Args:
            input_dir: Directory containing input documents
            output_dir: Directory to save JSON outputs
            recursive: Whether to process subdirectories
            
        Returns:
            List of conversion results
            
        Raises:
            NotADirectoryError: If input_dir is not a directory
        """
        if not os.path.isdir(input_dir):
            raise NotADirectoryError(f"Not a directory: {input_dir}")
        
        # Create output directory if needed
        os.makedirs(output_dir, exist_ok=True)
        
        results = []
        
        # Get list of files
        if recursive:
            files = []
            for root, _, filenames in os.walk(input_dir):
                for filename in filenames:
                    files.append(os.path.join(root, filename))
        else:
            files = [os.path.join(input_dir, f) 
                    for f in os.listdir(input_dir)
                    if os.path.isfile(os.path.join(input_dir, f))]
        
        # Process each file
        for file_path in files:
            if not FormatDetector.is_supported(file_path):
                continue
            
            try:
                # Generate output filename
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                output_path = os.path.join(output_dir, f"{base_name}.json")
                
                # Convert file
                result = self.convert_file(file_path, output_path)
                results.append({
                    'input_file': file_path,
                    'output_file': output_path,
                    'status': 'success',
                    'result': result
                })
                
            except Exception as e:
                results.append({
                    'input_file': file_path,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def _save_json(self, data: Dict[str, Any], file_path: str) -> None:
        """Save data to JSON file."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_supported_formats(self) -> List[str]:
        """
        Get list of supported document formats.
        
        Returns:
            List of format identifiers
        """
        return list(self._parsers.keys())
    
    def validate_json(self, data: Dict[str, Any]) -> bool:
        """
        Validate document JSON against schema.
        
        Args:
            data: Document data to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Basic validation
            if 'metadata' not in data or 'content' not in data:
                return False
            
            if 'format' not in data['metadata']:
                return False
            
            if not isinstance(data['content'], list):
                return False
            
            # Validate content items
            for item in data['content']:
                if 'type' not in item or 'position' not in item:
                    return False
                
                if 'index' not in item['position']:
                    return False
            
            return True
            
        except Exception:
            return False
