# DSParser - Discord Messages Parser

DSParser is a tool for parsing and organizing messages from exported Discord HTML files. The script automatically separates messages by years and saves them into separate HTML files.

## Features

- Fast parallel processing of large HTML files
- Multi-threaded processing for optimal performance
- Ability to compile into a standalone executable file
- Modular architecture

## Installation

### Pre-compiled Versions

For users who don't want to install Python and dependencies, ready-to-use executable files are available:

1. Download the latest version from the [Releases section](https://github.com/thesamedesu/dsparser/releases)
2. Choose the version for your operating system
3. Run the program from the command line:

```bash
# Windows
dsparser.exe --input path/to/discord_export.html --output output_folder

# Linux/macOS
./dsparser --input path/to/discord_export.html --output output_folder
```

### Installation from source code

```bash
git clone https://github.com/thesamedesu/dsparser.git
cd dsparser
pip install -e .
```

## Usage

```bash
# Run as an installed package
dsparser --input path/to/discord_export.html --output output_folder

# Run from cloned repository
python -m dsparser --input path/to/discord_export.html --output output_folder
```

### Command line parameters

- `--input`, `-i`: Path to Discord HTML file with messages (required)
- `--output`, `-o`: Path to save output files (default: "output")
- `--chunk-size`, `-c`: Size of processed chunks in MB (default: 10)
- `--workers`, `-w`: Number of worker threads (default: 4)

## Project Structure

```
dsparser/
├── src/
│   └── dsparser/
│       ├── __init__.py           - Package metadata
│       ├── __main__.py           - Entry point for python -m dsparser
│       ├── cli.py                - Command line interface
│       ├── parser.py             - Main parser code
│       └── utils/
│           ├── __init__.py       - Subpackage initialization
│           └── html_helpers.py   - Helper functions for working with HTML
├── docs/
│   ├── usage.md                  - Usage documentation
│   └── examples/
│       └── basic_usage.py        - Example usage
├── setup.py                      - Setup script
└── README.md                     - Main documentation
```

## Design Principles

The project follows these design principles:

- **DRY (Don't Repeat Yourself)** - Avoiding code duplication through centralization of common functions
- **Separation of Responsibilities** - Each module is responsible for specific functionality
- **Modularity** - Code is organized into modules with clear interfaces

## Requirements

- Python 3.6+
- beautifulsoup4
- tqdm

## License

MIT License 