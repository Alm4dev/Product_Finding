from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import re


def manomano_scrap(search_type):
    # Set up Chrome options
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Set up Chrome service
    service = Service('C:/Users/Acer/Desktop/chromedriver-win64/chromedriver.exe')

    # Create a new Chrome session
    driver = webdriver.Chrome(service=service, options=options)

    products_data = []

    def extract_dimensions(description):
        # Regex to find dimensions (width x depth x height) or single width
        dimension_pattern = re.compile(
            r'(\d+(?:\,?\d+)?)\s*x\s*(\d+(?:\,?\d+)?)\s*x\s*(\d+(?:\,?\d+)?)\s*cm|(\d+(?:\,?\d+)?)\s*cm')

        matches = dimension_pattern.findall(description)

        dimensions = {}

        for match in matches:
            if match[0] and match[1] and match[2]:  # Width x Depth x Height
                dimensions['breite'] = float(match[1].replace(',', '.'))
                dimensions['hohe'] = float(match[2].replace(',', '.'))
                dimensions['tiefe'] = float(match[0].replace(',', '.'))
            elif match[3]:  # Single width
                dimensions['breite'] = float(match[3].replace(',', '.'))

        return dimensions

    try:
        # Navigate to the search results page based on type
        if search_type == 'Heizkörper':
            driver.get('https://www.manomano.de/suche/Heizk%C3%B6rper+')
        elif search_type == 'Waschbecken':
            driver.get('https://www.manomano.de/suche/Waschbecken+')
        else:
            print(f"Unsupported search type: {search_type}")
            return

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
                dimensions = extract_dimensions(product_data['name'])
                if dimensions:
                    product_data.update(dimensions)

                # Extract and store product price
                price_tag = product.find('span', class_='qMW3rO ZR6iYG yAMbPQ XKoSfQ bT_DYl')
                if price_tag:
                    price_text = price_tag.text.strip().replace('€', '').replace(' ', '').replace(',', '.')
                    product_data['price'] = float(price_text) if price_text else None

                products_data.append(product_data)

            # Print the collected product data
            for product in products_data:
                print(product)
        else:
            print("No products found.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the Chrome session
        driver.quit()


# Example usage:
manomano_scrap('Heizkörper')
