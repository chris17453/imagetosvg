# Makefile for testing image2svg options

# Source image
IMAGE := chris-ex1.png

# Output directory
OUTPUT_DIR := assets/chris

# Options to test
COLORS := 2 3 4 5 8 12
LAYERING := dark_first light_first area hue
MIN_AREAS := 10 30 50 100
SIMPLIFY_FACTORS := 1 2 4 8

# Python script name
SCRIPT := img2svg.py

all: setup color_test layer_test area_test simplify_test

# Create output directory if it doesn't exist
setup:
	@mkdir -p $(OUTPUT_DIR)
	@echo "Output directory: $(OUTPUT_DIR)"

# Test different color counts
color_test:
	@echo "Testing different color counts..."
	@for c in $(COLORS); do \
		echo "  Processing with $$c colors..."; \
		echo python3 $(SCRIPT) $(IMAGE) -o $(OUTPUT_DIR)/colors_$$c.svg -c $$c; \
		python3 $(SCRIPT) $(IMAGE) -o $(OUTPUT_DIR)/colors_$$c.svg -c $$c; \
	done

# Test different layering methods
layer_test:
	@echo "Testing different layering methods..."
	@for l in $(LAYERING); do \
		echo "  Processing with $$l layering..."; \
		python3 $(SCRIPT) $(IMAGE) -o $(OUTPUT_DIR)/layer_$$l.svg -l $$l; \
	done

# Test different minimum area thresholds
area_test:
	@echo "Testing different minimum area thresholds..."
	@for m in $(MIN_AREAS); do \
		echo "  Processing with minimum area $$m..."; \
		python3 $(SCRIPT) $(IMAGE) -o $(OUTPUT_DIR)/min_area_$$m.svg -m $$m; \
	done

# Test different simplification factors
simplify_test:
	@echo "Testing different simplification factors..."
	@for s in $(SIMPLIFY_FACTORS); do \
		echo "  Processing with simplification factor $$s..."; \
		python3 $(SCRIPT) $(IMAGE) -o $(OUTPUT_DIR)/simplify_$$s.svg -s $$s; \
	done

# Comprehensive test combining options
comprehensive_test:
	@echo "Running comprehensive tests..."
	@for c in 3 5; do \
		for l in dark_first light_first; do \
			for m in 30 50; do \
				for s in 2 4; do \
					echo "  Testing c$$c-l$$l-m$$m-s$$s..."; \
					python3 $(SCRIPT) $(IMAGE) \
						-o $(OUTPUT_DIR)/comp_c$$c-l$$l-m$$m-s$$s.svg \
						-c $$c -l $$l -m $$m -s $$s; \
				done; \
			done; \
		done; \
	done

# Clean generated files
clean:
	@echo "Cleaning output directory..."
	@rm -rf $(OUTPUT_DIR)/*.svg

# Help information
help:
	@echo "Makefile for testing img2svg options"
	@echo ""
	@echo "Available targets:"
	@echo "  all               - Run all test variations"
	@echo "  setup             - Create output directory"
	@echo "  color_test        - Test different color counts"
	@echo "  layer_test        - Test different layering methods"
	@echo "  area_test         - Test different min area thresholds"
	@echo "  simplify_test     - Test different simplification factors"
	@echo "  comprehensive_test - Run tests with combinations of options"
	@echo "  clean             - Remove generated SVG files"
	@echo ""
	@echo "Options being tested:"
	@echo "  Colors: $(COLORS)"
	@echo "  Layering methods: $(LAYERING)"
	@echo "  Min areas: $(MIN_AREAS)"
	@echo "  Simplify factors: $(SIMPLIFY_FACTORS)"
	@echo ""
	@echo "Source image: $(IMAGE)"
	@echo "Output directory: $(OUTPUT_DIR)"

# Make these targets run even if files with the same name exist
.PHONY: all setup color_test layer_test area_test simplify_test comprehensive_test clean help