from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

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

try:
    # Open the webpage
    driver.get('https://www.obi.de/search/waschbecken%20/')

    # Wait until the button is clickable, then click it using JavaScript
    button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.tw-inline-block.tw-underline.tw-stretched-link.tw-transition-opacity.hover\\:tw-underline.hover\\:tw-text-orange'))
    )
    driver.execute_script("arguments[0].click();", button)

    # Wait until the input box is present and interactable
    input_box = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'input.disc-sf__input.tw-block.tw-bg-transparent.tw-w-full.tw-py-4.tw-pr-9'))
    )

    # Check if the input box is visible and enabled
    if input_box.is_displayed() and input_box.is_enabled():
        print("Input box is visible and enabled")
        input_box.send_keys('10247')
    else:
        print("Input box is not interactable")

    # Wait for the results to load and be present on the page
    results = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'span.tw-font-obi.tw-leading-none.tw-text-gray-900'))
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
                print(f"Found label: {parent_label.get_attribute('data-store-name')}")
                driver.execute_script("arguments[0].click();", parent_label)
                print("Label clicked.")
    else:
        print(f"No distances found lower than {input_distance} km")

finally:
    # Close the WebDriver
    driver.quit()
