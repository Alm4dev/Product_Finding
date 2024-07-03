from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import re

# Initialize the WebDriver (e.g., Chrome)

# Set up Chrome options
options = Options()
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Set up Chrome service
service = Service('C:/Users/Acer/Desktop/chromedriver-win64/chromedriver.exe')

# Create a new Chrome session
driver = webdriver.Chrome(service=service, options=options)
driver.maximize_window()
Page_url1 = 'https://www.obi.de/search/waschbecken%20/'
Page_url2 = 'https://www.obi.de/search/heizk%C3%B6rper%20/'
baseurl = 'https://www.obi.de'


def extract_dimensions(description):
    # Regex to find dimensions
    dimension_pattern = re.compile(
        r'(\d+(\.\d+)?)\s*(cm|mm)\s*[xX×]?\s*(\d+(\.\d+)?)?\s*(cm|mm)?\s*[xX×]?\s*(\d+(\.\d+)?)?\s*(cm|mm)?')

    matches = dimension_pattern.findall(description)
    if matches:
        # Initialize dimensions
        width = depth = height = None
        # Determine dimensions based on the number of matches and their values
        for match in matches:
            values = [float(match[0]), float(match[3]) if match[3] else None, float(match[6]) if match[6] else None]
            units = [match[2], match[5] if match[5] else None, match[8] if match[8] else None]

            # Single dimension (assume width)
            if values[1] is None and values[2] is None:
                width = values[0]

            # Two dimensions (larger is height, smaller is width)
            elif values[2] is None:
                if values[0] > values[1]:
                    height = values[0]
                    width = values[1]
                else:
                    height = values[1]
                    width = values[0]

            # Three dimensions (width x depth x height)
            else:
                width = values[0]
                depth = values[1]
                height = values[2]

        # Return extracted dimensions
        return {
            'width': width,
            'depth': depth,
            'height': height
        }
    return {'width': None, 'depth': None, 'height': None}


type = 'Heizkörper'
try:
    if type == 'Heizkörper':
        driver.get('https://www.obi.de/search/heizk%C3%B6rper%20/')

    if type == 'Waschbecken':
        driver.get('https://www.obi.de/search/waschbecken%20/')

    # Wait until the button is clickable, then click it using JavaScript
    button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR,
                                    'button.tw-inline-block.tw-underline.tw-stretched-link.tw-transition-opacity.hover\\:tw-underline.hover\\:tw-text-orange'))
    )
    driver.execute_script("arguments[0].click();", button)

    # Wait until the input box is present and interactable
    input_box = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'input.disc-sf__input.tw-block.tw-bg-transparent.tw-w-full.tw-py-4.tw-pr-9'))
    )

    # Check if the input box is visible and enabled
    if input_box.is_displayed() and input_box.is_enabled():
        print("Input box is visible and enabled")
        input_box.send_keys('10247')
    else:
        print("Input box is not interactable")

    # Wait for the results to load and be present on the page
    results = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR,
                                             'div.tw-flex-shrink-0.tw-font-sans.tw-font-bold.tw-text-gray-900.tw-text-sm.tw-px-2.tw-py-px.tw-bg-gray-300.tw-rounded-tl.tw-rounded-br'))
    )

    # Extract distances
    distances = []
    span_elements = []  # To keep track of span elements
    for result in results:
        text = result.text.strip()  # Remove any leading/trailing whitespace
        if text.endswith("km"):
            distance_str = text[:-2].replace(",", ".")  # Remove "km" and replace comma with dot for float conversion
            try:
                distance = float(distance_str)
                distances.append(distance)
                span_elements.append(result)
                print(f"Found distance: {distance} km")
            except ValueError:
                print(f"Failed to convert {distance_str} to float")

    # Print all collected distances
    print(f"All collected distances: {distances}")

    # Input distance to compare
    input_distance = 2  # You can change this value as needed

    # Find the closest lower distance
    closest_lower_distance = None
    closest_span_element = None
    for i, distance in enumerate(distances):
        if distance <= input_distance:
            if closest_lower_distance is None or input_distance - distance < input_distance - closest_lower_distance:
                closest_lower_distance = distance
                closest_span_element = span_elements[i]

    if closest_lower_distance is not None:
        print(f"The closest lower distance to {input_distance} km is {closest_lower_distance} km")
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
                print("Button clicked.")

                # Wait for the page to load after the click
                time.sleep(5)

                # Scraping the page after clicking the label
                page_source = driver.page_source
                soup = BeautifulSoup(page_source, 'html.parser')
                products_data = []
                if type == 'Heizkörper':
                    product_elements = soup.findAll('div',
                                                    class_="artikelkachel tw-relative tw-w-full tw-bg-white tw-shadow-none lg:tw-rounded lg:tw-border lg:tw-border-gray-300 tw-border-gray-300 find-outline-2 tw-duration-100 tw-h-full tw-border-t")
                if type == 'Waschbecken':
                    product_elements = soup.findAll('div',
                                                    class_="artikelkachel tw-relative tw-w-full tw-bg-white tw-shadow-none lg:tw-rounded lg:tw-border lg:tw-border-gray-300 tw-border-gray-300 find-outline-2 tw-duration-100 tw-h-full tw-border-t")

                for product in product_elements:
                    product_data = {}

                    # Extract and store product link
                    link_tag = product.find('a', href=True)
                    product_data['link'] = baseurl + link_tag['href'] if link_tag else None

                    # Extract and store product name
                    if type == 'Heizkörper':
                        name_tag = product.find('p',
                                                class_='tw-font-sans tw-text-base lg:tw-overflow-hidden lg:tw-bg-white lg:tw-h-18')
                    if type == 'Waschbecken':
                        name_tag = product.find('p',
                                                class_='tw-font-sans tw-text-base lg:tw-overflow-hidden lg:tw-bg-white lg:tw-h-18')
                    product_data['name'] = name_tag.text.strip() if name_tag else None

                    dimensions = extract_dimensions(product_data['name'])
                    product_data['breite'] = dimensions.get('width', None)
                    product_data['tiefe'] = dimensions.get('depth', None)
                    product_data['hohe'] = dimensions.get('height', None)

                    # Extract and store product price
                    if type == 'Heizkörper':
                        price_tag = product.find('span', class_='tw-inline-flex')
                    if type == 'Waschbecken':
                        price_tag = product.find('span', class_='tw-inline-flex')
                    product_data['price'] = price_tag.text.strip() if price_tag else None

                    products_data.append(product_data)

                # Print the collected product data
                print(products_data)

finally:
    # Close the WebDriver
    driver.quit()