# PNG Decoder v3

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A pure Python implementation of a PNG (Portable Network Graphics) image decoder that parses PNG files at the binary level, extracts metadata, and processes image data without relying on external image processing libraries.

## Table of Contents

<!-- - [Usage](#usage) -->
<!-- - [API Reference](#api-reference) -->
<!-- - [Examples](#examples) -->
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [PNG Format Overview](#png-format-overview)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Pure Python Implementation**: No external dependencies for core PNG decoding functionality
- **Binary-level Parsing**: Direct manipulation of PNG file structure and chunks
- **Chunk-based Processing**: Supports critical PNG chunks (IHDR, PLTE, IDAT, IEND)
- **Format Validation**: Validates PNG file signatures and structure
- **Metadata Extraction**: Extracts image dimensions, color type, bit depth, and compression info

## Installation

### Prerequisites

- Python 3.12 or higher
- A virtual environment (recommended)
- [uv](https://astral.sh/uv) (recommended)

### Setting up the Environment

1. **Clone or download the project:**
   ```bash
   git clone https://github.com/Nemesis-AS/png-py.git
   cd png-py
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows
   uv venv env
   env\Scripts\activate
   
   # macOS/Linux
   uv venv env
   source env/bin/activate
   ```

3. **Run the code:**
    ```bash
    python main.py
    ```

## Quick Start

```python
from png_decoder import PNGImage

# Load and validate a PNG file
img = PNGImage("path/to/your/image.png")

# Validate the PNG signature
if img.validate_sign():
    print("Valid PNG file!")
    
    # Parse all chunks
    img.parse_chunks()
    
    # Access image metadata
    print(f"Dimensions: {img.ihdr.width}x{img.ihdr.height}")
    print(f"Color Type: {img.ihdr.color_type}")
    print(f"Bit Depth: {img.ihdr.bit_depth}")
else:
    print("Invalid PNG file!")
```

<!-- ## Usage

### Basic PNG File Analysis

```python
from png_decoder import PNGImage

def analyze_png(filepath):
    """Analyze a PNG file and print its properties."""
    img = PNGImage(filepath)
    
    # Step 1: Validate PNG signature
    if not img.validate_sign():
        print(f"Error: {filepath} is not a valid PNG file")
        return
    
    print(f"✓ Valid PNG file: {filepath}")
    
    # Step 2: Parse chunks
    img.parse_chunks()
    
    # Step 3: Display metadata
    if img.ihdr:
        print(f"Dimensions: {img.ihdr.width} × {img.ihdr.height} pixels")
        print(f"Bit Depth: {img.ihdr.bit_depth} bits per channel")
        print(f"Color Type: {img.ihdr.color_type}")
        print(f"Compression: {img.ihdr.compression_method}")
        print(f"Filter Method: {img.ihdr.filter_method}")
        print(f"Interlace: {img.ihdr.interlace_method}")
    
    # Step 4: Show chunk information
    print(f"\nFound {len(img.chunks)} chunks:")
    for i, chunk in enumerate(img.chunks):
        chunk_type = chunk['type'].decode('ascii')
        print(f"  {i+1}. {chunk_type} ({chunk['size']} bytes)")

# Example usage
analyze_png("images/barrierRed.png")
```

### Working with Image Data

```python
from png_decoder import PNGImage

# Load PNG and access raw data
img = PNGImage("images/img1.png")
img.validate_sign()
img.parse_chunks()

# Access compressed image data
print(f"Compressed data size: {len(img.data)} bytes")
print(f"Number of IDAT chunks: {len(img.data_chunks)}")

# The parse_data() method handles decompression
# (Note: This is currently under development)
``` -->

## Project Structure

```
png_v3/
├── main.py                    # Example usage script
├── pyproject.toml            # Project configuration
├── README.md                 # This file
├── env/                      # Virtual environment (created after setup)
├── images/                   # Sample PNG files for testing
│   ├── barrierRed.png
│   └── img1.png
└── png_decoder/              # Main package
    ├── __init__.py          # Package initialization
    ├── png_image.py         # Main PNGImage class
    ├── chunks.py            # PNG chunk implementations
    └── utils.py             # Utility functions
```

## PNG Format Overview

This decoder implements parsing for the PNG file format as specified in [RFC 2083](https://tools.ietf.org/rfc/rfc2083.txt). Key components include:

### File Structure
1. **PNG Signature**: 8-byte file header identifying PNG format
2. **Chunks**: Self-contained data blocks with type, size, data, and CRC

### Supported Chunks
- **IHDR** (Image Header): Image dimensions, color type, compression info
- **PLTE** (Palette): Color palette for indexed-color images
- **IDAT** (Image Data): Compressed image pixel data
- **IEND** (Image End): Marks the end of the PNG datastream

### Color Types
- `0`: Grayscale
- `2`: Truecolor (RGB)
- `3`: Indexed-color (palette)
- `4`: Grayscale with alpha
- `6`: Truecolor with alpha (RGBA)

## Development

### Setting up Development Environment

1. **Clone the repository and set up environment:**
   ```bash
   git clone <repository-url>
   cd png_v3
   python -m venv env
   
   # Windows
   env\Scripts\activate
   
   # macOS/Linux
   source env/bin/activate
   ```

2. **Install development dependencies:**
   ```bash
   pip install -e .
   # Add development tools as needed:
   pip install black pytest mypy
   ```

### Running the Example

```bash
python main.py
```
<!-- 
### Code Style

This project follows Python best practices:
- Use meaningful variable names
- Follow PEP 8 style guidelines
- Include type hints where appropriate
- Write clear, concise comments

### Testing Your Changes

Test with the provided sample images:
```bash
# Test with sample images
python -c "
from png_decoder import PNGImage
img = PNGImage('images/barrierRed.png')
print('Valid:', img.validate_sign())
img.parse_chunks()
print('Dimensions:', img.ihdr.width, 'x', img.ihdr.height)
"
``` -->

### Current Limitations

<!-- - **Data Processing**: The `parse_data()` method is under development -->
- **Filter Support**: PNG filter algorithms not yet implemented
- **Advanced Chunks**: Some optional PNG chunks are not supported
- **Interlacing**: Adam7 interlacing is not implemented

## Contributing

Contributions are welcome! 
<!-- Here are some areas where help is needed: -->

<!-- ### Priority Areas
1. **Complete data decompression and filtering**
2. **Implement PNG filter algorithms** (Sub, Up, Average, Paeth)
3. **Add support for more chunk types** (tEXt, tIME, etc.)
4. **Improve error handling and validation**
5. **Add comprehensive test suite** -->

<!-- ### How to Contribute
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly with various PNG files
5. Submit a pull request

### Coding Guidelines
- Follow existing code style and structure
- Add docstrings to new functions and classes
- Include type hints for function parameters and return values
- Test with multiple PNG file types and formats -->

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- PNG specification: [W3C PNG Specification](https://www.w3.org/TR/PNG/)
- RFC 2083: [PNG (Portable Network Graphics) Specification](https://tools.ietf.org/rfc/rfc2083.txt)

## Support

**Create an issue** if you find bugs or have feature requests
