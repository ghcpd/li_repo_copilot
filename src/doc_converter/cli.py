"""
Command-line interface for document converter.
"""

import argparse
import json
import sys
from pathlib import Path

from .converter import DocumentConverter
from .plugin_manager import PluginManager


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Convert documents to standardized JSON format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a single file
  doc-converter input.docx -o output.json
  
  # Convert all files in a directory
  doc-converter /path/to/docs/ -b /path/to/output/
  
  # Convert with custom plugins
  doc-converter input.pdf -o output.json -p /path/to/plugins/
  
  # Batch convert with recursive processing
  doc-converter /path/to/docs/ -b /path/to/output/ -r
        """
    )
    
    parser.add_argument(
        'input',
        nargs='?',
        help='Input file or directory'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output JSON file (for single file conversion)'
    )
    
    parser.add_argument(
        '-b', '--batch-output',
        help='Output directory (for batch conversion)'
    )
    
    parser.add_argument(
        '-r', '--recursive',
        action='store_true',
        help='Process directories recursively'
    )
    
    parser.add_argument(
        '-p', '--plugin-dir',
        help='Directory containing custom parser plugins'
    )
    
    parser.add_argument(
        '--list-formats',
        action='store_true',
        help='List supported formats and exit'
    )
    
    parser.add_argument(
        '--validate',
        action='store_true',
        help='Validate output JSON against schema'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Initialize converter
    converter = DocumentConverter()
    
    # Load plugins if specified
    if args.plugin_dir:
        plugin_manager = PluginManager(args.plugin_dir)
        plugin_manager.load_plugins()
        
        # Register loaded plugins
        for format_type in plugin_manager.get_loaded_plugins():
            parser_instance = plugin_manager.create_parser_instance(format_type)
            if parser_instance:
                converter.register_parser(format_type, parser_instance)
                if args.verbose:
                    print(f"Loaded plugin for format: {format_type}")
    
    # List formats and exit
    if args.list_formats:
        formats = converter.get_supported_formats()
        print("Supported formats:")
        for fmt in formats:
            print(f"  - {fmt}")
        return 0
    
    # Check input (only if not listing formats)
    if not hasattr(args, 'input') or not args.input:
        parser.print_help()
        return 1
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input path does not exist: {args.input}", file=sys.stderr)
        return 1
    
    try:
        # Single file conversion
        if input_path.is_file():
            if not args.output:
                # Default output name
                args.output = input_path.with_suffix('.json')
            
            if args.verbose:
                print(f"Converting {args.input} -> {args.output}")
            
            result = converter.convert_file(str(input_path), args.output)
            
            # Validate if requested
            if args.validate:
                is_valid = converter.validate_json(result)
                if is_valid:
                    print("✓ Validation passed")
                else:
                    print("✗ Validation failed", file=sys.stderr)
                    return 1
            
            print(f"Successfully converted to {args.output}")
            return 0
        
        # Batch conversion
        elif input_path.is_dir():
            if not args.batch_output:
                print("Error: Batch output directory required (-b)", 
                      file=sys.stderr)
                return 1
            
            if args.verbose:
                print(f"Batch converting from {args.input} to {args.batch_output}")
                if args.recursive:
                    print("Recursive mode enabled")
            
            results = converter.convert_batch(
                str(input_path),
                args.batch_output,
                recursive=args.recursive
            )
            
            # Print summary
            success_count = sum(1 for r in results if r['status'] == 'success')
            error_count = len(results) - success_count
            
            print(f"\nBatch conversion complete:")
            print(f"  Successful: {success_count}")
            print(f"  Failed: {error_count}")
            
            if args.verbose and error_count > 0:
                print("\nErrors:")
                for result in results:
                    if result['status'] == 'error':
                        print(f"  {result['input_file']}: {result['error']}")
            
            return 0 if error_count == 0 else 1
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
