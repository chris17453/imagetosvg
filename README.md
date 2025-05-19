# Image to SVG Converter

A Python script that converts raster images to SVG vectors with reduced colors.

![Bear](bear.jpg)
![Bear-16](assets/bear-16.svg)
![Bear-8](assets/bear-8.svg)
![Bear-5](assets/bear-5.svgg)



## Features

- Reduces an image to a specified number of colors (default is 16)
- Converts to pure vector SVG with no embedded raster images
- Optimizes for horizontal color runs to minimize SVG file size
- Works with various image formats (PNG, JPG, etc.)

## Installation

### Requirements

- Python 3.6 or higher
- pipenv (recommended for dependency management)

### Dependencies

- NumPy
- Pillow (PIL)
- scikit-learn

### Setup

```bash
# Clone or download this repository
git clone https://github.com/yourusername/image-to-svg.git
cd image-to-svg

# Install dependencies with pipenv
pipenv install numpy pillow scikit-learn

# Or use pip directly
pip install numpy pillow scikit-learn
```

## Usage

```bash
# Basic usage (with pipenv)
pipenv run python image_to_svg.py input_image.jpg

# Or activate the environment first
pipenv shell
python image_to_svg.py input_image.jpg

# Specify output file
python image_to_svg.py input_image.png -o output.svg

# Change number of colors (e.g., to 8)
python image_to_svg.py input_image.jpg -c 8
```

### Command Line Arguments

- `input_file`: Path to the input image file (required)
- `-o, --output`: Path to the output SVG file (optional, defaults to input filename with .svg extension)
- `-c, --colors`: Number of colors to use (optional, default: 16)

## How It Works

1. The script loads the input image using Pillow.
2. It uses K-means clustering to reduce the image to the specified number of colors.
3. For each color region, it creates SVG rectangle elements for horizontal runs of pixels.
4. It writes the resulting vector graphics to an SVG file.

## Example

```bash
python image_to_svg.py photo.jpg -c 12
```

This will:
1. Load `photo.jpg`
2. Reduce it to 12 colors
3. Create vector shapes for each color region
4. Save the result as `photo.svg`

## License

BSD 3-Clause Revised License

## Notes

- Processing large images may require significant memory and CPU time
- The resulting SVG files may be large for complex images
- For best results, use images with distinct color regions
