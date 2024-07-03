import copy

import requests
from bs4 import BeautifulSoup
import time
import re
import random
def find_closest_products(breite_input, tiefe_input):
    closest_products = []

    # List of products with both dimensions available
    products_with_dimensions = [p for p in products_data if p['breite'] is not None and p['tiefe'] is not None]

    # Sort products with dimensions available by total difference
    products_with_dimensions.sort(key=lambda x: abs(x['breite'] - breite_input) + abs(x['tiefe'] - tiefe_input))

    # Track seen products to avoid duplicates
    seen_products = set()

    # Iterate through sorted products and select top 3 closest unique products
    for product in products_with_dimensions:
        if len(closest_products) >= 3:
            break
        # Ensure unique products
        product_key = (product['name'], product['price'], product['link'])
        if product_key not in seen_products:
            closest_products.append({
                'name': product['name'],
                'price': product['price'],
                'link': product['link']
            })
            seen_products.add(product_key)

    # If fewer than 3 products with dimensions available, fill with products with None values
    if len(closest_products) < 3:
        for p in products_data:
            if len(closest_products) >= 3:
                break
            if p['breite'] is None or p['tiefe'] is None:
                product_key = (p['name'], p['price'], p['link'])
                if product_key not in seen_products:
                    closest_products.append({
                        'name': p['name'],
                        'price': p['price'],
                        'link': p['link']
                    })
                    seen_products.add(product_key)

    return closest_products[:3]  # Return at most 3 closest products


Pr_links=[]
Page_url1 = 'https://www.idealo.de/preisvergleich/ProductCategory/11632I16-45.html?q=Waschbecken'

user_agents = [

    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',

]

headers = {
    'User-Agent': random.choice(user_agents),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'none',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive'
}
products_data = []

try:
    for xx in range(7):
        req = requests.get(Page_url1, headers=headers)
        req.raise_for_status()

        breite_pattern = re.compile(r'Breite\s*([\d,]+)\s*cm')
        tiefe_pattern = re.compile(r'Tiefe\s*([\d,]+)\s*cm')

        soup = BeautifulSoup(req.text, 'html.parser')
        product_elements = soup.findAll('div', class_="sr-resultList__item_m6xdA")

        for product in product_elements:
            product_data = {}

            # Extract and store product link
            link_tag = product.find('a', href=True)
            product_data['link'] = link_tag['href'] if link_tag else None

            # Extract and store product name
            name_tag = product.find('div', class_='sr-productSummary__title_f5flP')
            product_data['name'] = name_tag.text.strip() if name_tag else None

            # Extract and store product price
            price_tag = product.find('div', class_='sr-detailedPriceInfo__price_sYVmx')
            product_data['price'] = price_tag.text.strip()[2:] if price_tag else None

            # Extract and store product width (Breite) and depth (Tiefe)
            product_text = product.get_text()
            breite_match = breite_pattern.search(product_text)
            tiefe_match = tiefe_pattern.search(product_text)

            if breite_match:
                breite_value = breite_match.group(1).replace(',', '.')
                product_data['breite'] = float(breite_value)
            else:
                product_data['breite'] = None

            if tiefe_match:
                tiefe_value = tiefe_match.group(1).replace(',', '.')
                product_data['tiefe'] = float(tiefe_value)
            else:
                product_data['tiefe'] = None

            products_data.append(product_data)

        time.sleep(1)

    # Print the collected product data
    for product in products_data:
        print(product)
        prices = [float(price.replace(',', '.')) for price in product['price'] if
                  price.replace(',', '.').replace('.', '').isdigit()]

    prices = [float(product['price'].replace(' €', '').replace('.', '').replace(',', '.')) for product in products_data if product['price']]
    average_price = sum(prices) / len(prices) if prices else 0

    print(f"Durchschnittspreis : {average_price:.2f} €")
except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
# Get user input for Breite and Tiefe
breite_input = float(input("Enter Breite (width) in cm: "))
tiefe_input = float(input("Enter Tiefe (depth) in cm: "))

# Find and print the closest 3 products
closest_products = find_closest_products(breite_input, tiefe_input)

if closest_products:
    print("Closest products found:")
    for i, product in enumerate(closest_products, 1):
        print(f"Product {i}:")
        print(f"Name: {product['name']}")
        print(f"Price: {product['price']}")
        print(f"Link: {product['link']}")
        print()
else:
    print("No products found with the given dimensions.")