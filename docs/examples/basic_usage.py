"""
Example of basic DSParser usage
"""

from dsparser.parser import parse_discord_html

def main():
    # Parse Discord HTML file
    parse_discord_html(
        input_file='discord_export.html',  # Path to Discord export file
        output_dir='parsed_messages',      # Folder for saving results
        workers=4,                         # Number of worker threads
        chunk_size_mb=10                   # Chunk size in MB
    )
    
    print("Parsing completed! Results saved in 'parsed_messages' folder")

if __name__ == "__main__":
    main() 