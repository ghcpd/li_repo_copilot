"""
Example usage of the Document Converter library.
"""

from doc_converter import DocumentConverter

# Example 1: Convert a single file
def convert_single_file():
    converter = DocumentConverter()
    
    # Convert DOCX file
    result = converter.convert_file('sample.docx', 'output.json')
    
    print(f"Converted: {result['metadata']['source_file']}")
    print(f"Format: {result['metadata']['format']}")
    print(f"Content items: {len(result['content'])}")


# Example 2: Batch convert multiple files
def convert_batch_files():
    converter = DocumentConverter()
    
    # Convert all supported files in a directory
    results = converter.convert_batch(
        input_dir='./documents',
        output_dir='./output',
        recursive=True
    )
    
    for result in results:
        if result['status'] == 'success':
            print(f"✓ {result['input_file']}")
        else:
            print(f"✗ {result['input_file']}: {result['error']}")


# Example 3: Register custom parser (plugin architecture)
def register_custom_parser():
    from doc_converter.parsers import BaseParser
    
    class CustomParser(BaseParser):
        def __init__(self):
            super().__init__()
            self.supported_formats = ['custom']
        
        def can_parse(self, file_path: str) -> bool:
            return file_path.endswith('.custom')
        
        def parse(self, file_path: str):
            result = self._create_base_structure('custom')
            # Custom parsing logic here
            return result
    
    converter = DocumentConverter()
    converter.register_parser('custom', CustomParser())
    
    # Now you can convert .custom files
    result = converter.convert_file('document.custom')


# Example 4: Working with the parsed data
def analyze_document():
    converter = DocumentConverter()
    result = converter.convert_file('sample.html')
    
    # Count different content types
    headings = [item for item in result['content'] if item['type'] == 'heading']
    paragraphs = [item for item in result['content'] if item['type'] == 'paragraph']
    tables = [item for item in result['content'] if item['type'] == 'table']
    
    print(f"Headings: {len(headings)}")
    print(f"Paragraphs: {len(paragraphs)}")
    print(f"Tables: {len(tables)}")
    
    # Print heading hierarchy
    print("\nDocument Structure:")
    for heading in headings:
        indent = "  " * (heading['level'] - 1)
        print(f"{indent}H{heading['level']}: {heading['text']}")


if __name__ == '__main__':
    print("Document Converter Examples")
    print("=" * 50)
    
    # Uncomment to run examples
    # convert_single_file()
    # convert_batch_files()
    # register_custom_parser()
    # analyze_document()
