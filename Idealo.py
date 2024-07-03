import re

# Sample product descriptions
product_descriptions = [
    "Badezimmer Badmöbel-Set Paso xl LED 80cm Waschbecken Grau Eiche - Unterschrank 2x Hochschrank Waschbecken Möbel",
    "Waschbecken Waschtisch aus Keramik, Aufsatzwaschbecken Eckig, Kleines Waschbecken Gäste WC, Hänge Waschbecken Bad Weiß, Mini Waschbecken 45 x 31 x 13 cm",
    "Wandbecken Aufsatzwaschbecken BS6001 aus Gussmarmor - Breite wählbar - Weiß glänzend 60cm - mit Armaturloch"
]


def extract_dimensions(description):
    # Regex to find dimensions (width x depth x height) or single width
    dimension_pattern = re.compile(r'(\d+)\s*x\s*(\d+)\s*x\s*(\d+)\s*cm|(\d+)\s*cm')

    matches = dimension_pattern.findall(description)

    dimensions = []

    for match in matches:
        if match[0] and match[1] and match[2]:  # Width x Depth x Height
            dimensions.append({
                'width': int(match[0]),
                'depth': int(match[1]),
                'height': int(match[2])
            })
        elif match[3]:  # Single width
            dimensions.append({
                'width': int(match[3])
            })

    return dimensions


# Process each product description
for description in product_descriptions:
    dimensions = extract_dimensions(description)
    print(f"Description: {description}")
    print(f"Extracted Dimensions: {dimensions}")
    print("-" * 50)