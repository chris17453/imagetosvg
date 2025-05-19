# Makefile to generate SVG versions of bear.jpg with different color settings

# Default target
all: bear-2.svg bear-3.svg bear-4.svg bear-5.svg bear-6.svg bear-7.svg bear-8.svg bear-9.svg bear-10.svg bear-11.svg bear-12.svg bear-13.svg bear-14.svg bear-15.svg bear-16.svg

# Define Python script
SCRIPT = image_to_svg.py
INPUT = bear.jpg

# Rule for generating SVGs with different color counts
bear-%.svg: $(INPUT) $(SCRIPT)
	python $(SCRIPT) $(INPUT) -o assets/$@ -c $*

# Clean all generated SVGs
clean:
	rm -f bear-*.svg

.PHONY: all clean