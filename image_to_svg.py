#!/usr/bin/env python3
import sys
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse

def quantize_colors(image_path, n_colors=16):
    """Reduce image to n_colors using K-means clustering."""
    # Open the image
    img = Image.open(image_path).convert('RGB')  # Convert to RGB for simplicity
    width, height = img.size
    
    # Get pixel data
    pixels = np.array(img)
    pixels_flat = pixels.reshape(-1, 3)
    
    # Perform K-means clustering
    print("Performing color clustering...")
    kmeans = KMeans(n_clusters=n_colors, random_state=0).fit(pixels_flat)
    labels = kmeans.labels_
    centers = kmeans.cluster_centers_
    
    # Create a new array with the quantized colors
    quantized_flat = centers[labels].astype(np.uint8)
    quantized = quantized_flat.reshape(height, width, 3)
    
    # Return the labels in 2D shape for easier processing
    return quantized, labels.reshape(height, width), centers.astype(np.uint8)

def create_svg(quantized, labels, colors, output_path):
    """Create an SVG with vector paths for each color region."""
    height, width = labels.shape
    
    # Create SVG root element
    svg = ET.Element('svg', {
        'xmlns': 'http://www.w3.org/2000/svg',
        'version': '1.1',
        'width': str(width),
        'height': str(height),
        'viewBox': f'0 0 {width} {height}'
    })
    
    print("Creating SVG elements...")
    # Create rectangles for color regions
    for color_idx, color in enumerate(colors):
        # Convert color to hex
        r, g, b = color
        hex_color = f'#{r:02x}{g:02x}{b:02x}'
        
        # Create a group for this color
        color_group = ET.SubElement(svg, 'g', {
            'fill': hex_color,
            'stroke': 'none'
        })
        
        # Find all pixels of this color and create rectangles for horizontal runs
        for y in range(height):
            x = 0
            while x < width:
                if labels[y, x] == color_idx:
                    # Start of a run
                    start_x = x
                    # Find end of run
                    while x < width and labels[y, x] == color_idx:
                        x += 1
                    # Create a rectangle for this run
                    run_width = x - start_x
                    if run_width > 0:
                        rect = ET.SubElement(color_group, 'rect', {
                            'x': str(start_x),
                            'y': str(y),
                            'width': str(run_width),
                            'height': '1'
                        })
                else:
                    x += 1
    
    # Create XML tree and save to file
    print("Writing SVG file...")
    tree = ET.ElementTree(svg)
    
    # Handle indent for Python versions before 3.9
    try:
        ET.indent(tree, space="  ")
    except AttributeError:
        # For Python < 3.9, indent is not available
        pass
    
    tree.write(output_path, encoding='utf-8', xml_declaration=True)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert an image to SVG with reduced colors')
    parser.add_argument('input_file', help='Input image file')
    parser.add_argument('-o', '--output', help='Output SVG file')
    parser.add_argument('-c', '--colors', type=int, default=16, help='Number of colors (default: 16)')
    args = parser.parse_args()
    
    # Set default output path if not specified
    if args.output is None:
        input_path = Path(args.input_file)
        args.output = str(input_path.with_suffix('.svg'))
    
    print(f"Converting {args.input_file} to SVG with {args.colors} colors...")
    
    try:
        # Quantize colors
        quantized, labels, colors = quantize_colors(args.input_file, args.colors)
        
        # Create SVG
        create_svg(quantized, labels, colors, args.output)
        
        print(f"SVG successfully saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()