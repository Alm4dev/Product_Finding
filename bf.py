import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import re
import random

# Web scraping function to fetch products data
def scrape_products(url):
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
        for xx in range(7):  # Adjust number of pages to scrape as needed
            req = requests.get(url, headers=headers)
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

            time.sleep(1)  # Add a delay to respect server load limits

        return products_data

    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
        return []

# Function to find closest products based on dimensions
def find_closest_products(products_data, breite_input, tiefe_input):
    closest_products = []

    # List of products with both dimensions available
    products_with_dimensions = [p for p in products_data if p.get('breite') is not None and p.get('tiefe') is not None]

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
                'link': product['link'],
                'breite': product['breite'],  # Ensure to include 'breite' and 'tiefe' here
                'tiefe': product['tiefe']
            })
            seen_products.add(product_key)

    return closest_products

# Streamlit application
st.title('Product Dashboard')

# Input fields
product_type = st.selectbox('Product Type', ['Heizkörper', 'Waschbecken'])
width = st.number_input('Width (cm)', min_value=0)
depth = st.number_input('Depth (cm)', min_value=0)
height = st.number_input('Height (cm)', min_value=0)
capacity = st.number_input('Capacity (W)', min_value=0)
postal_code = st.text_input('Postal Code', '81475')
radius = st.number_input('Radius (km)', min_value=0)

# Search button
if st.button('Search'):
    # Construct URL based on selected product type and other inputs
    if product_type == 'Waschbecken':
        url = 'https://www.idealo.de/preisvergleich/ProductCategory/11632I16-45.html?q=Waschbecken'
    else:  # Default to Heizkörper if not specified
        url = 'https://www.example.com/heizkorper'  # Replace with actual URL for Heizkörper products

    # Fetch products data from web scraping function
    products_data = scrape_products(url)

    if products_data:
        # Find closest products based on user input dimensions
        closest_products = find_closest_products(products_data, width, depth)

        if closest_products:
            st.subheader('Closest Products:')
            for product in closest_products:  # Display closest products found
                st.write(f"Product: {product['name']}")
                if 'breite' in product:
                    st.write(f"Width: {product['breite']} cm")
                if 'tiefe' in product:
                    st.write(f"Depth: {product['tiefe']} cm")
                st.write(f"Price: {product['price']} €")
                st.write(f"Link: {product['link']}")
                st.write('---')
        else:
            st.warning('No products found with the specified dimensions.')
    else:
        st.error('Failed to fetch product data. Please try again later.')
