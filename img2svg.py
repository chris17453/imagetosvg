'''

██╗███╗   ███╗ ██████╗ ██████╗ ███████╗██╗   ██╗ ██████╗ 
██║████╗ ████║██╔════╝ ╚════██╗██╔════╝██║   ██║██╔════╝ 
██║██╔████╔██║██║  ███╗ █████╔╝███████╗██║   ██║██║  ███╗
██║██║╚██╔╝██║██║   ██║██╔═══╝ ╚════██║╚██╗ ██╔╝██║   ██║
██║██║ ╚═╝ ██║╚██████╔╝███████╗███████║ ╚████╔╝ ╚██████╔╝
╚═╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚══════╝  ╚═══╝   ╚═════╝ 
                                                         


'''
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

def create_svg(labels, colors, output_path, min_area=50, simplify_factor=2, layer_method='dark_first'):
    """Create an SVG with vector paths using a mirrored border for better edge handling."""
    height, width = labels.shape
    
    # Create SVG root element
    svg = ET.Element('svg', {
        'xmlns': 'http://www.w3.org/2000/svg',
        'version': '1.1',
        'width': str(width),
        'height': str(height),
        'viewBox': f'0 0 {width} {height}'
    })
    
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
    
    # Calculate color priorities for layering
    color_priorities = []
    for i, color in enumerate(colors):
        if i == most_common_color_idx:
            continue  # Skip background color
        # Calculate brightness (lower value = darker)
        brightness = 0.299 * color[0] + 0.587 * color[1] + 0.114 * color[2]
        color_priorities.append((i, brightness))
    
    # Sort by the chosen method
    if layer_method == 'dark_first':
        color_priorities.sort(key=lambda x: x[1])  # Darkest first
    elif layer_method == 'light_first':
        color_priorities.sort(key=lambda x: x[1], reverse=True)  # Lightest first
    elif layer_method == 'area':
        # Sort by area (calculate area for each color)
        areas = [np.sum(labels == idx) for idx, _ in color_priorities]
        color_priorities = [(idx, area) for (idx, _), area in zip(color_priorities, areas)]
        color_priorities.sort(key=lambda x: x[1], reverse=True)  # Largest first
    elif layer_method == 'hue':
        # Sort by hue
        hues = []
        for idx, _ in color_priorities:
            r, g, b = colors[idx]
            r, g, b = r/255, g/255, b/255
            max_val = max(r, g, b)
            min_val = min(r, g, b)
            
            if max_val == min_val:
                h = 0  # achromatic
            elif max_val == r:
                h = ((g - b) / (max_val - min_val)) % 6
            elif max_val == g:
                h = (b - r) / (max_val - min_val) + 2
            else:
                h = (r - g) / (max_val - min_val) + 4
                
            h *= 60
            hues.append(h)
        
        color_priorities = [(idx, hue) for (idx, _), hue in zip(color_priorities, hues)]
        color_priorities.sort(key=lambda x: x[1])  # Sort by hue
    
    # Process colors in order determined by the chosen sorting method
    for color_idx, _ in color_priorities:
        # Convert color to hex
        r, g, b = colors[color_idx]
        hex_color = f'#{r:02x}{g:02x}{b:02x}'
        
        # Create binary mask for this color
        mask = (labels == color_idx).astype(np.uint8)
        
        # Create a padded mask with mirrored edges (2 pixel border)
        border_size = 2
        padded_mask = np.zeros((height + 2*border_size, width + 2*border_size), dtype=np.uint8)
        
        # Copy the original mask to the center of the padded mask
        padded_mask[border_size:-border_size, border_size:-border_size] = mask
        
        # Mirror edges horizontally
        padded_mask[border_size:-border_size, :border_size] = mask[:, border_size-1::-1]  # left edge
        padded_mask[border_size:-border_size, -border_size:] = mask[:, -1:-border_size-1:-1]  # right edge
        
        # Mirror edges vertically
        padded_mask[:border_size, border_size:-border_size] = mask[border_size-1::-1, :]  # top edge
        padded_mask[-border_size:, border_size:-border_size] = mask[-1:-border_size-1:-1, :]  # bottom edge
        
        # Mirror corners
        padded_mask[:border_size, :border_size] = mask[border_size-1::-1, border_size-1::-1]  # top-left
        padded_mask[:border_size, -border_size:] = mask[border_size-1::-1, -1:-border_size-1:-1]  # top-right
        padded_mask[-border_size:, :border_size] = mask[-1:-border_size-1:-1, border_size-1::-1]  # bottom-left
        padded_mask[-border_size:, -border_size:] = mask[-1:-border_size-1:-1, -1:-border_size-1:-1]  # bottom-right
        
        # Apply morphological operations
        padded_mask = morphology.binary_dilation(padded_mask, morphology.disk(2))
        padded_mask = morphology.binary_erosion(padded_mask, morphology.disk(1))
        padded_mask = morphology.binary_opening(padded_mask, morphology.disk(1))
        
        # Find contours on the padded mask
        contours = measure.find_contours(padded_mask, 0.5)
        
        # Create a group for this color
        color_group = ET.SubElement(svg, 'g', {
            'fill': hex_color,
            'stroke': 'none'
        })
        
        # Create SVG paths for each contour
        for contour in contours:
            # Adjust contour coordinates to account for padding
            contour -= border_size
            
            # Filter out contour points outside the image boundaries with a small margin
            margin = 0.5  # Allow points slightly outside image bounds for smooth edges
            valid_points = (contour[:, 0] >= -margin) & (contour[:, 0] < height+margin) & \
                           (contour[:, 1] >= -margin) & (contour[:, 1] < width+margin)
                           
            if np.sum(valid_points) < min_area:
                continue
                
            contour = contour[valid_points]
            if len(contour) < 3:  # Need at least 3 points for a valid path
                continue
                
            # Simplify contour
            if len(contour) >= simplify_factor * 3:  # Ensure we'll have at least 3 points after simplification
                simplified_contour = contour[::simplify_factor]
            else:
                # Use less aggressive simplification for smaller contours
                step = max(1, len(contour) // 10)
                simplified_contour = contour[::step]
            
            # Ensure we have enough points after simplification
            if len(simplified_contour) < 3:
                simplified_contour = contour  # Use the original contour if simplification is too aggressive
            
            # Create path
            path_data = f"M {simplified_contour[0][1]},{simplified_contour[0][0]}"
            for x, y in simplified_contour[1:]:
                path_data += f" L {y},{x}"
            path_data += " Z"  # Close path
            
            # Add path to SVG
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
    parser.add_argument('-l', '--layer', choices=['dark_first', 'light_first', 'area', 'hue'], 
                    default='dark_first', help='Layering method (default: dark_first)')
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
        create_svg(labels, colors, args.output, args.min_area, args.simplify, args.layer)

        print(f"SVG successfully saved to {args.output}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()