# Using DSParser

DSParser is a tool for processing exported Discord HTML files. It divides messages by years and saves them into separate files for more convenient viewing and analysis.

## Basic Usage

### Command Line Execution

The simplest way to use DSParser is to run it via command line:

```bash
dsparser --input path/to/discord_export.html --output output_folder
```

### Parameters

- `--input`, `-i`: Path to HTML file with Discord messages (required parameter)
- `--output`, `-o`: Folder for saving output files (default: "output")
- `--chunk-size`, `-c`: Size of processed chunks in MB (default: 10)
- `--workers`, `-w`: Number of worker threads (default: 4)

Example with additional parameters:

```bash
dsparser --input discord_export.html --output messages --chunk-size 20 --workers 8
```

## Using as a Library

DSParser can also be used as a library in your Python code:

```python
from dsparser.parser import parse_discord_html

# Parse Discord HTML file
parse_discord_html(
    input_file='path/to/discord_export.html', 
    output_dir='output',
    workers=4,
    chunk_size_mb=10
)
```

## Recommendations

- For very large files, you can increase `chunk_size` to speed up processing, but this will require more memory
- The number of threads (`workers`) should be set depending on the number of cores in your processor
- Output files will be named by the years of messages, for example: `2023.html`, `2022.html`, etc. 