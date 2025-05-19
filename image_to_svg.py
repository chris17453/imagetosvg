#!/usr/bin/env python3
import sys
import numpy as np
from PIL import Image
from sklearn.cluster import KMeans
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse
from skimage import measure, morphology

def quantize_colors(image_path, n_colors=5):
    """Reduce image to n_colors using K-means clustering."""
    # Open the image
    img = Image.open(image_path).convert('RGB')
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

def create_svg(labels, colors, output_path, min_area=50, simplify_factor=2):
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
    
    # Count unique colors
    unique_colors = len(np.unique(labels))
    is_bicolor = unique_colors <= 2
    
    # Set background to the most common color
    color_counts = np.bincount(labels.flatten())
    most_common_color_idx = np.argmax(color_counts)
    bg_color = colors[most_common_color_idx]
    r, g, b = bg_color
    hex_bg_color = f'#{r:02x}{g:02x}{b:02x}'
    
    # Add background rectangle
    ET.SubElement(svg, 'rect', {
        'x': '0',
        'y': '0',
        'width': str(width),
        'height': str(height),
        'fill': hex_bg_color
    })
    
    print("Creating SVG elements...")
    
    # Special case for bicolor images to avoid the diagonal artifact
    if is_bicolor:
        # Find the second color
        second_color_idx = 1 if most_common_color_idx == 0 else 0
        
        # Get the second color in hex
        r, g, b = colors[second_color_idx]
        hex_color = f'#{r:02x}{g:02x}{b:02x}'
        
        # Create a more aggressively preprocessed mask for the second color
        mask = (labels == second_color_idx).astype(np.uint8)
        
        # Apply stronger morphological operations for bi-color images
        mask = morphology.binary_closing(mask, morphology.disk(3))
        mask = morphology.remove_small_objects(mask.astype(bool), min_size=min_area)
        mask = morphology.remove_small_holes(mask.astype(bool), area_threshold=min_area)
        
        # Create a group for this color
        color_group = ET.SubElement(svg, 'g', {
            'fill': hex_color,
            'stroke': 'none'
        })
        
        # Find contours
        contours = measure.find_contours(mask, 0.5)
        
        # Create SVG paths for each contour
        for contour in contours:
            # Skip small contours
            if len(contour) < min_area:
                continue
            
            # Simplify contour more aggressively
            step = max(1, len(contour) // 100)  # More aggressive simplification
            simplified_contour = contour[::step]
            
            # Create path
            path_data = f"M {simplified_contour[0][1]},{simplified_contour[0][0]}"
            for x, y in simplified_contour[1:]:
                path_data += f" L {y},{x}"
            path_data += " Z"  # Close path
            
            ET.SubElement(color_group, 'path', {
                'd': path_data
            })
    else:
        # Regular processing for images with more than 2 colors
        for color_idx, color in enumerate(colors):
            if color_idx == most_common_color_idx:
                continue  # Skip background color
                
            # Convert color to hex
            r, g, b = color
            hex_color = f'#{r:02x}{g:02x}{b:02x}'
            
            # Create binary mask for this color
            mask = (labels == color_idx).astype(np.uint8)
            
            # Apply morphological operations
            mask = morphology.binary_dilation(mask, morphology.disk(2))
            mask = morphology.binary_erosion(mask, morphology.disk(1))
            mask = morphology.binary_opening(mask, morphology.disk(1))
            
            # Find contours
            contours = measure.find_contours(mask, 0.5)
            
            # Create a group for this color
            color_group = ET.SubElement(svg, 'g', {
                'fill': hex_color,
                'stroke': 'none'
            })
            
            # Create SVG paths for each contour
            for contour in contours:
                # Skip small contours
                if len(contour) < min_area:
                    continue
                    
                # Simplify contour
                simplified_contour = contour[::simplify_factor]
                
                # Create path
                path_data = f"M {simplified_contour[0][1]},{simplified_contour[0][0]}"
                for x, y in simplified_contour[1:]:
                    path_data += f" L {y},{x}"
                path_data += " Z"  # Close path
                
                ET.SubElement(color_group, 'path', {
                    'd': path_data
                })
    
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
    parser.add_argument('-c', '--colors', type=int, default=5, help='Number of colors (default: 5)')
    parser.add_argument('-m', '--min_area', type=int, default=50, 
                        help='Minimum area for shapes (default: 50)')
    parser.add_argument('-s', '--simplify', type=int, default=2,
                        help='Path simplification factor (default: 2)')
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
        create_svg(labels, colors, args.output, args.min_area, args.simplify)
        
        print(f"SVG successfully saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()