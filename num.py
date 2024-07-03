from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import re

# Function to extract dimensions from the product description
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

# Function to get the URL and class names based on the input mode
def get_url_and_classes(mode):
    if mode == "Waschbecken":
        return ('https://www.manomano.de/suche/Waschbecken+', 'tG5dru JqwSfJ c5PGVKq', 'oFBZUY zeMsI- c1ox_2g undefined', 'HUq6RR yMvMpv', 'qMW3rO ZR6iYG yAMbPQ XKoSfQ bT_DYl')
    elif mode == "Heizkörper":
        return ('https://www.example.com/search/Heizkoerper+', 'new-div-class-for-heizkoerper', 'new-a-class-for-heizkoerper', 'new-p-class-for-heizkoerper', 'new-span-class-for-heizkoerper')
    else:
        raise ValueError("Invalid mode. Please choose 'Waschbecken' or 'Heizkörper'.")

# Main script
if __name__ == "__main__":
    # Set up Chrome options
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Set up Chrome service
    service = Service('C:/Users/Acer/Desktop/chromedriver-win64/chromedriver.exe')

    # Create a new Chrome session
    driver = webdriver.Chrome(service=service, options=options)

    products_data = []

    try:
        # Get user input for the mode
        mode = input("Enter the mode (Waschbecken or Heizkörper): ")

        # Get the appropriate URL and class names based on the mode
        search_url, div_class, a_class, p_class, span_class = get_url_and_classes(mode)

        # Navigate to the search results page
        driver.get(search_url)
        baseurl = 'https://www.manomano.de' if mode == "Waschbecken" else 'https://www.example.com'

        # Wait until the page is fully loaded
        driver.implicitly_wait(10)

        # Get the entire page content
        page_content = driver.page_source

        # Parse the page content using BeautifulSoup
        soup = BeautifulSoup(page_content, 'html.parser')

        # Find the specific <div> element with the class
        div_element = soup.find('div', class_=div_class)

        # Check if the <div> element was found
        if div_element:
            # Find all <a> tags within the <div> element
            a_tags = div_element.find_all('a', href=True)

            for a_tag in a_tags:
                product_data = {}

                # Extract and store product link
                product_data['link'] = baseurl + a_tag['href'] if a_tag.get('href') else None

                # Extract and store product name
                name_tag = a_tag.find('p', class_=p_class)
                product_data['name'] = name_tag.text.strip() if name_tag else None

                if name_tag:
                    dimensions = extract_dimensions(name_tag.text)
                    if dimensions:
                        # Take the first set of dimensions found
                        dimension = dimensions[0]

                        product_data['breite'] = dimension.get('width', None)
                        product_data['tiefe'] = dimension.get('depth', None)
                        product_data['Höhe'] = dimension.get('height', None)

                # Extract and store product price
                price_tag = a_tag.find('span', class_=span_class)
                if price_tag:
                    price_text = price_tag.text.strip()
                    if price_text:
                        # Remove the Euro symbol
                        price_text = price_text.replace('€', '.').strip()
                        # Replace the space with a dot to correctly format the decimal part
                        price_text = price_text + ' ' + '€'
                        product_data['price'] = price_text.strip() if price_text else None

                products_data.append(product_data)

            # Print the collected product data
            for product in products_data:
                print(product)
        else:
            print(f"Error: The <div> element with class '{div_class}' was not found.")

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the Chrome session
        driver.quit()
