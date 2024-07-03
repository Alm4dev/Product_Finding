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
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Function to extract dimensions from the description
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

            time.sleep(1)  # Add a delay to respect server load limits

        return products_data

    except requests.exceptions.RequestException as e:
        st.error(f"Request failed: {e}")
        return []
def extract_dimensions(description):
    dimension_pattern = re.compile(
        r'(\d+(\.\d+)?)\s*(cm|mm)\s*[xX×]?\s*(\d+(\.\d+)?)?\s*(cm|mm)?\s*[xX×]?\s*(\d+(\.\d+)?)?\s*(cm|mm)?')

    matches = dimension_pattern.findall(description)
    if matches:
        width = depth = height = None
        for match in matches:
            values = [float(match[0]), float(match[3]) if match[3] else None, float(match[6]) if match[6] else None]
            units = [match[2], match[5] if match[5] else None, match[8] if match[8] else None]

            if values[1] is None and values[2] is None:
                width = values[0]
            elif values[2] is None:
                if values[0] > values[1]:
                    height = values[0]
                    width = values[1]
                else:
                    height = values[1]
                    width = values[0]
            else:
                width = values[0]
                depth = values[1]
                height = values[2]
        return {'width': width, 'depth': depth, 'height': height}
    return {'width': None, 'depth': None, 'height': None}

# Function to scrape products from obi.de using Selenium
def scrape_obi_products(product_type, zip_code, radius):
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service('C:/Users/Acer/Desktop/chromedriver-win64/chromedriver.exe')  # Update the path to your chromedriver

    driver = webdriver.Chrome(service=service, options=options)
    driver.maximize_window()

    baseurl = 'https://www.obi.de'

    try:
        if product_type == 'Heizkörper':
            driver.get('https://www.obi.de/search/heizk%C3%B6rper%20/')
        elif product_type == 'Waschbecken':
            driver.get('https://www.obi.de/search/waschbecken%20/')

        button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.tw-inline-block.tw-underline.tw-stretched-link.tw-transition-opacity.hover\\:tw-underline.hover\\:tw-text-orange'))
        )
        driver.execute_script("arguments[0].click();", button)

        input_box = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input.disc-sf__input.tw-block.tw-bg-transparent.tw-w-full.tw-py-4.tw-pr-9'))
        )
        input_box.send_keys(zip_code)

        results = WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'span.tw-font-obi.tw-leading-none.tw-text-gray-900'))
        )

        distances = []
        span_elements = []
        for result in results:
            text = result.text.strip()
            if text.endswith("km"):
                distance_str = text[:-2].replace(",", ".")
                try:
                    distance = float(distance_str)
                    distances.append(distance)
                    span_elements.append(result)
                except ValueError:
                    continue

        closest_lower_distance = None
        closest_span_element = None
        for i, distance in enumerate(distances):
            if distance <= radius:
                if closest_lower_distance is None or radius - distance < radius - closest_lower_distance:
                    closest_lower_distance = distance
                    closest_span_element = span_elements[i]

        if closest_lower_distance is not None:
            st.write(f"The closest lower distance to {radius} km is {closest_lower_distance} km")
            if closest_span_element:
                # Find the associated label and click it
                parent_label = closest_span_element.find_element(By.XPATH, './ancestor::label')
                if parent_label:
                    st.write(f"Found label: {parent_label.get_attribute('data-store-name')}")
                    driver.execute_script("arguments[0].click();", parent_label)
                    st.write("Label clicked.Please wait")

                    time.sleep(5)

                    page_source = driver.page_source
                    soup = BeautifulSoup(page_source, 'html.parser')
                    products_data = []

                    if product_type == 'Heizkörper':
                        product_elements = soup.findAll('div', class_="artikelkachel tw-relative tw-w-full tw-bg-white tw-shadow-none lg:tw-rounded lg:tw-border lg:tw-border-gray-300 tw-border-gray-300 find-outline-2 tw-duration-100 tw-h-full tw-border-t")
                    elif product_type == 'Waschbecken':
                        product_elements = soup.findAll('div', class_="artikelkachel tw-relative tw-w-full tw-bg-white tw-shadow-none lg:tw-rounded lg:tw-border lg:tw-border-gray-300 tw-border-gray-300 find-outline-2 tw-duration-100 tw-h-full tw-border-t")

                    for product in product_elements:
                        product_data = {}

                        link_tag = product.find('a', href=True)
                        product_data['link'] = baseurl + link_tag['href'] if link_tag else None

                        name_tag = product.find('p', class_='tw-font-sans tw-text-base lg:tw-overflow-hidden lg:tw-bg-white lg:tw-h-18')
                        product_data['name'] = name_tag.text.strip() if name_tag else None

                        dimensions = extract_dimensions(product_data['name'])
                        product_data['breite'] = dimensions.get('width', None)
                        product_data['tiefe'] = dimensions.get('depth', None)
                        product_data['Höhe'] = dimensions.get('height', None)

                        price_tag = product.find('span', class_='tw-inline-flex')
                        product_data['price'] = price_tag.text.strip() if price_tag else None

                        products_data.append(product_data)

                    return products_data
        else:
            st.write(f"No distances found lower than {radius} km")
        return []
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return []
    finally:
        time.sleep(5)
        driver.quit()

# Function to find closest products based on dimensions
def find_closest_products(products_data, width, height, product_type):
    closest_products = []

    if product_type == 'Waschbecken':
        products_with_dimensions = [p for p in products_data if p.get('breite') is not None and p.get('tiefe') is not None]
        products_with_dimensions.sort(key=lambda x: abs(x['breite'] - width) + abs(x['tiefe'] - height))
    elif product_type == 'Heizkörper':
        products_with_dimensions = [p for p in products_data if p.get('breite') is not None and p.get('Höhe') is not None]
        products_with_dimensions.sort(key=lambda x: abs(x['breite'] - width) + abs(x['Höhe'] - height))

    seen_products = set()
    for product in products_with_dimensions:
        product_key = (product['name'], product['price'], product['link'])
        if product_key not in seen_products:
            closest_products.append({
                'name': product['name'],
                'price': product['price'],
                'link': product['link'],
                'breite': product['breite'],
                'tiefe' if product_type == 'Waschbecken' else 'Höhe': product.get('tiefe' if product_type == 'Waschbecken' else 'Höhe', '-')
            })
            seen_products.add(product_key)
        if len(closest_products) >= 3:
            break

    return closest_products[:3]

# Streamlit application
st.title('Product Dashboard')

# Input fields
website = st.selectbox('Select Website', ['Idealo', 'manomano', 'obi.de'])
product_type = st.selectbox('Product Type', ['Heizkörper', 'Waschbecken', 'OtherProductType'])
width = st.number_input('Width (cm)', min_value=0)
depth = st.number_input('Depth (cm)', min_value=0)
height = st.number_input('Height (cm)', min_value=0)
capacity = st.number_input('Capacity (W)', min_value=0)

# Show postal code and radius input only if website is 'obi.de'
if website == 'obi.de':
    postal_code = st.text_input('Postal Code', '')
    radius = st.number_input('Radius (km)', min_value=0)
else:
    postal_code = None
    radius = None

# Search button
if st.button('Search'):
    user_agents = [
        'Mozilla/5.0 (Windows NT 0.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
    ]
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    products_data = []

    if website == 'obi.de':
        if not postal_code or not radius:
            st.error("Please provide both postal code and radius.")
        else:
            products_data = scrape_obi_products(product_type, postal_code, radius)
            st.write(f"Total products scraped: {len(products_data)}")
            closest_products = find_closest_products(products_data, width, height, product_type)


    else:
        if website == 'Idealo':
            if product_type == 'Waschbecken':
                url = 'https://www.idealo.de/preisvergleich/ProductCategory/11632I16-45.html?q=Waschbecken'
            elif product_type == 'Heizkörper':
                url = 'https://www.idealo.de/preisvergleich/ProductCategory/18398.html?q=Heizk%C3%B6rper&qd=Heizk%C3%B6rper'
            else:
                url = 'https://www.idealo.de/preisvergleich/ProductCategory/OtherProductType.html?q=OtherProductType'
            products_data = scrape_products(url, headers, product_type)
        elif website == 'manomano':
            # Call your existing scraping function for manomano
            pass

    if products_data:
        closest_products = find_closest_products(products_data, width, height, product_type)
        st.write('Closest products based on dimensions and capacity:')
        for product in closest_products:
            st.write(f"Name: {product['name']}")
            st.write(f"Price: {product['price']}")
            st.write(f"Link: {product['link']}")
            st.write(f"Width: {product['breite']} cm")
            if product_type == 'Waschbecken':
                st.write(f"Depth: {product['tiefe']} cm")
            elif product_type == 'Heizkörper':
                st.write(f"Height: {product['Höhe']} cm")
            st.write('---')
    else:
        st.warning('No products found.')
