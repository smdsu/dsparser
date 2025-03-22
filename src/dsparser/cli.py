"""
Command-line interface for DSParser
"""

import argparse
from dsparser.parser import parse_discord_html


def create_parser():
    """
    Creates and configures command-line argument parser
    
    Returns:
        ArgumentParser: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Parallel parsing of Discord HTML message file and splitting by years."
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Path to input HTML file."
    )
    parser.add_argument(
        "--output", "-o", default="output",
        help="Folder to save output files (default: output)."
    )
    parser.add_argument(
        "--chunk-size", "-c", type=int, default=10,
        help="Size of chunk to process in MB (default: 10)."
    )
    parser.add_argument(
        "--workers", "-w", type=int, default=4,
        help="Number of worker threads for parallel processing (default: 4)."
    )
    return parser


def main():
    """
    Main CLI function for DSParser.
    
    This function is the single entry point for all command calls.
    It is also imported and used in other modules to run the
    script directly, for example from __main__.py or parser.py.
    """
    parser = create_parser()
    args = parser.parse_args()
    
    parse_discord_html(args.input, args.output, args.workers, args.chunk_size)


if __name__ == "__main__":
    main() 