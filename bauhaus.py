import re
import requests
import time
import random
import streamlit as st
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Set up Chrome options for headless mode
options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--headless')  # Run Chrome in headless mode

# Initialize the Chrome driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def manomano_scrap(search_type):
    products_data = []
    try:
        # Navigate to the search results page based on type
        if search_type == 'Heizkörper':
            driver.get('https://www.manomano.de/suche/Heizk%C3%B6rper+')
        elif search_type == 'Waschbecken':
            driver.get('https://www.manomano.de/suche/Waschbecken+')
        else:
            st.write(f"Unsupported search type: {search_type}")
            return []

        # Wait until the page is fully loaded
        driver.implicitly_wait(10)

        # Get the entire page content
        page_content = driver.page_source

        # Parse the page content using BeautifulSoup
        soup = BeautifulSoup(page_content, 'html.parser')

        # Find the main <div> element containing products
        div_element = soup.find('div', class_='tG5dru JqwSfJ c5PGVKq')

        # Base URL for product links
        baseurl = 'https://www.manomano.de'

        # Check if the <div> element was found
        if div_element:
            # Find all <a> tags within the <div> element
            a_tags = div_element.find_all('a', href=True)

            for product in a_tags:
                product_data = {}

                # Extract and store product link
                product_data['link'] = baseurl + product['href'] if product.get('href') else None

                # Extract and store product name
                product_data['name'] = product.text.strip() if product.text else None
                dimensions = extract_dimensions2(product_data['name'])
                if dimensions:
                    product_data.update(dimensions)

                # Extract and store product price
                price_tag = product.find('span', class_='qMW3rO ZR6iYG yAMbPQ XKoSfQ bT_DYl')
                if price_tag:
                    price_text = price_tag.text.strip()
                    price_match = re.search(r'(\d+[\.,]?\d*)\s*€', price_text)
                    if price_match:
                        price = price_match.group(1).replace('.', '').replace(',', '.')
                        product_data['price'] = float(price) if price else None
                products_data.append(product_data)
        else:
            st.write("No products found.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
    finally:
        # Close the Chrome session
        driver.quit()

    return products_data

def extract_dimensions2(description):
    # Combined regex to find dimensions in different formats
    dimension_pattern = re.compile(
        r'(\d+(?:\,?\d+)?)\s*x\s*(\d+(?:\,?\d+)?)\s*x\s*(\d+(?:\,?\d+)?)\s*cm|(\d+(?:\,?\d+)?)\s*cm|(\d+)\s*x\s*(\d+)\s*mm|(\d+)\s*x\s*(\d+)\s*cm')

    matches = dimension_pattern.findall(description)

    dimensions = {}

    for match in matches:
        if match[0] and match[1] and match[2]:  # Width x Depth x Height in cm
            dimensions['breite'] = float(match[1].replace(',', '.'))
            dimensions['Höhe'] = float(match[2].replace(',', '.'))
            dimensions['tiefe'] = float(match[0].replace(',', '.'))
        elif match[3]:  # Single width in cm
            dimensions['breite'] = float(match[3].replace(',', '.'))
        elif match[4] and match[5]:  # Width x Height in mm
            dimensions['breite'] = float(match[5]) / 10.0  # Convert mm to cm
            dimensions['Höhe'] = float(match[4]) / 10.0  # Convert mm to cm
        elif match[6] and match[7]:  # Width x Height in cm
            dimensions['breite'] = float(match[7])
            dimensions['Höhe'] = float(match[6])

    return dimensions

def find_closest_products_manomano(products_data, width, height):
    if width or height:
        # Filter products with width or height
        products_with_dimensions = [p for p in products_data if 'breite' in p or 'Höhe' in p]

        # Sort products based on the closest width or height
        products_with_dimensions.sort(key=lambda x: (
            abs((x.get('breite', float('inf')) or 0) - width) + abs((x.get('Höhe', float('inf')) or 0) - height)
        ))

        # Return the closest 3 products with dimensions
        return products_with_dimensions[:3]

    # If no width or height provided, return the first 3 products
    return products_data[:3]

def scrape_products(url, headers, product_type):
    products_data = []

    try:
        for xx in range(7):  # Adjust number of pages to scrape as needed
            req = requests.get(url, headers=headers)
            req.raise_for_status()

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

                # Extract product dimensions based on product type
                product_text = product.get_text()

                if product_type == 'Waschbecken':
                    # Extract Breite and Tiefe for Waschbecken
                    breite_pattern = re.compile(r'Breite\s*([\d,]+)\s*(cm|mm)', re.IGNORECASE)
                    tiefe_pattern = re.compile(r'Tiefe\s*([\d,]+)\s*(cm|mm)', re.IGNORECASE)

                    breite_match = breite_pattern.search(product_text)
                    tiefe_match = tiefe_pattern.search(product_text)

                    if breite_match:
                        breite_value = float(breite_match.group(1).replace(',', '.'))
                        if breite_match.group(2).lower() == 'mm':
                            breite_value /= 10  # Convert mm to cm
                        product_data['breite'] = breite_value
                    else:
                        product_data['breite'] = None

                    if tiefe_match:
                        tiefe_value = float(tiefe_match.group(1).replace(',', '.'))
                        if tiefe_match.group(2).lower() == 'mm':
                            tiefe_value /= 10  # Convert mm to cm
                        product_data['tiefe'] = tiefe_value
                    else:
                        product_data['tiefe'] = None

                elif product_type == 'Heizkörper':
                    # Extract Breite and Höhe if available in the product name
                    dimension_match = re.search(r'(\d+(?:,\d+)?)\s*[xX]\s*(\d+(?:,\d+)?)\s*(mm|cm)', product_text, re.IGNORECASE)

                    if dimension_match:
                        dim1 = float(dimension_match.group(1).replace(',', '.'))
                        dim2 = float(dimension_match.group(2).replace(',', '.'))
                        unit = dimension_match.group(3).lower()

                        if unit == 'mm':
                            dim1 /= 10  # Convert mm to cm
                            dim2 /= 10  # Convert mm to cm

                        if dim1 > dim2:
                            Höhe_value = dim1
                            breite_value = dim2
                        else:
                            Höhe_value = dim2
                            breite_value = dim1

                        product_data['breite'] = breite_value
                        product_data['Höhe'] = Höhe_value
                    else:
                        product_data['breite'] = None
                        product_data['Höhe'] = None

                products_data.append(product_data)

            time.sleep(random.uniform(1, 3))  # Random delay between requests

            next_page_link = soup.find('a', class_='sr-pagination__link--next')
            if next_page_link:
                next_page_url = 'https://www.idealo.de' + next_page_link.get('href')
                url = next_page_url
            else:
                break  # Stop if no more pages

    except requests.RequestException as e:
        st.error(f"An error occurred while scraping products: {str(e)}")

    return products_data

# Streamlit app
st.title('Product Scraper')

search_type = st.selectbox('Select product type', ['Heizkörper', 'Waschbecken'])
if st.button('Scrape ManoMano'):
    products_data = manomano_scrap(search_type)
    st.write(products_data)

width = st.number_input('Width (cm)', min_value=0.0)
height = st.number_input('Height (cm)', min_value=0.0)
if st.button('Find Closest Products'):
    closest_products = find_closest_products_manomano(products_data, width, height)
    st.write(closest_products)
