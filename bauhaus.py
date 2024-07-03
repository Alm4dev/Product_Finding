import re
import time
import random
import streamlit as st
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up Chrome options for headless mode
options = uc.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--headless')  # Run Chrome in headless mode

# Initialize the Chrome driver using undetected_chromedriver
driver = uc.Chrome(options=options)
def manomano_scrap(search_type):
    # Set up Chrome options
   # options = Options()
   # options.add_argument('--no-sandbox')
   # options.add_argument('--disable-dev-shm-usage')
    #driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    #service = Service('C:/Users/Acer/Desktop/chromedriver-win64/chromedriver.exe')  # Update the path to your chromedriver

    # Create a new Chrome session
   # driver = webdriver.Chrome(service=service, options=options)

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
   # options = Options()
   # options.add_argument('--no-sandbox')
   # options.add_argument('--disable-dev-shm-usage')
    #service = Service('C:/Users/Acer/Desktop/chromedriver-win64/chromedriver.exe')  # Update the path to your chromedriver

   # driver = webdriver.Chrome(service=service, options=options)
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
            EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                                                 'div.tw-flex-shrink-0.tw-font-sans.tw-font-bold.tw-text-gray-900.tw-text-sm.tw-px-2.tw-py-px.tw-bg-gray-300.tw-rounded-tl.tw-rounded-br'))
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
            print(f"The closest lower distance to {radius} km is {closest_lower_distance} km")
            if closest_span_element:
                # Find the associated label and click it
                parent_label = closest_span_element.find_element(By.XPATH, './ancestor::label')
                if parent_label:
                    print(f"Found label with data-store-name: {parent_label.get_attribute('data-store-name')}")

                    # Print the parent label's HTML for debugging
                    print(parent_label.get_attribute('outerHTML'))

                    # Now click on the input inside the label
                    input_to_click = parent_label.find_element(By.CSS_SELECTOR, 'input[type="radio"]')
                    if input_to_click:
                        driver.execute_script("arguments[0].click();", input_to_click)
                        print("Input clicked.")

                    # Click the button with the specified class
                    button_to_click = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR,
                                                    'button.disc-sf__results-mobile-button.tw-w-full.tw-font-obi-bold.tw-text-lg.tw-rounded-full.tw-px-8.tw-py-3.tw-bg-orange.hover\\:tw-bg-gray-900.focus\\:tw-bg-gray-900.tw-text-white.hover\\:tw-text-white.tw-transition-colors.tw-inline-block.tw-focus-button'))
                    )
                    driver.execute_script("arguments[0].click();", button_to_click)
                    st.write("Label clicked.Please wait")

                    # Wait for the page to load after the click
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
        products_with_dimensions = [p for p in products_data if 'breite' in p and 'tiefe' in p]
        products_with_dimensions.sort(key=lambda x: abs((x['breite'] or 0) - width) + abs((x['tiefe'] or 0) - height))
    elif product_type == 'Heizkörper':
        products_with_dimensions = [p for p in products_data if 'breite' in p and 'Höhe' in p]
        products_with_dimensions.sort(key=lambda x: abs((x['breite'] or 0) - width) + abs((x['Höhe'] or 0) - height))

    seen_products = set()
    for product in products_with_dimensions:
        product_key = (product['name'], product['price'], product['link'])
        if product_key not in seen_products:
            closest_products.append({
                'name': product['name'],
                'price': product['price'],
                'link': product['link'],
                'breite': product.get('breite', '-'),
                'tiefe' if product_type == 'Waschbecken' else 'Höhe': product.get('tiefe' if product_type == 'Waschbecken' else 'Höhe', '-')
            })
            seen_products.add(product_key)
        if len(closest_products) >= 3:
            break

    return closest_products[:3]


# Streamlit application
st.title('Product Dashboard')

# Input fields
website = st.selectbox('Select Website', ['Idealo', 'obi', 'manomano'])
product_type = st.selectbox('Product Type', ['Heizkörper', 'Waschbecken'])
width = st.number_input('Breite (cm)', min_value=0)
depth = st.number_input('Tiefe (cm)', min_value=0)
height = st.number_input('Höhe (cm)', min_value=0)
capacity = st.number_input('Kapazität (W)', min_value=0)

# Show postal code and radius input only if website is 'obi.de'
if website == 'obi':
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

    if website == 'obi':
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
            products_data = manomano_scrap(product_type)



    if products_data:
        closest_products = find_closest_products_manomano(products_data, width, height)
        st.write('Closest products based on dimensions:')
        for product in closest_products:
            st.write(f"Name: {product['name']}")
            st.write(f"Price: {product['price']}")
            st.write(f"Link: {product['link']}")
            st.write(f"Width: {product.get('breite', '-')} cm")
            st.write(f"Height: {product.get('Höhe', '-')} cm")
            st.write('---')
    else:
        st.warning('No products found.')