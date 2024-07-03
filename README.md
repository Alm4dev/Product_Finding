Product Finding Application README
Welcome to the Product Finding application! This application scrapes product information from various e-commerce websites and displays the closest products based on the specified dimensions. The application is built using Python, Selenium, BeautifulSoup, and Streamlit.

Features
Scrape product data from Idealo, Obi, and Manomano websites.
Extract product dimensions and prices.
Filter and display the closest products based on user-provided dimensions.
For Obi, specify a postal code and radius to find products within a certain distance.
Prerequisites
Python 3.x
Selenium
BeautifulSoup4
Requests
Streamlit
ChromeDriver
Installation
Clone the repository:

bash
Copy code
git clone https://github.com/Alm4dev/Product_Finding.git
cd Product_Finding
Install the required Python packages:

bash
Copy code
pip install -r requirements.txt
Download and set up ChromeDriver:

Download the appropriate ChromeDriver for your Chrome browser version from ChromeDriver.

Ensure the chromedriver executable is placed in a directory that's part of your system's PATH or update the path in the code where the ChromeDriver is initialized.

Usage
Run the Streamlit application. Replace the path with the actual path to your bauhaus.py file:

bash
Copy code
streamlit run C:\Users\Acer\PycharmProjects\Aufgabe\bauhaus.py
For other users, replace C:\Users\Acer\PycharmProjects\Aufgabe\bauhaus.py with your actual path:

bash
Copy code
streamlit run your/path/to/bauhaus.py
In the Streamlit interface, select the website you want to scrape from:

Idealo
Obi
Manomano
Select the product type:

Heizkörper
Waschbecken
Enter the dimensions:

Width (cm)
Depth (cm)
Height (cm)
Capacity (W) (optional)
For Obi, enter the postal code and radius (maximum distance in km).

Click the "Search" button to start scraping and finding products.

ChromeDriver Path
Please ensure you update the path to your ChromeDriver executable in the code:

python
Copy code
# For Manomano
service = Service('path/to/your/chromedriver')

# For Obi
service = Service('path/to/your/chromedriver')
Obi Specific Instructions
When scraping products from Obi, you can specify your postal code and the maximum distance (radius) you want the market to be from your location. This helps in finding products available within a certain range.

Code Overview
Main Functions
manomano_scrap(search_type): Scrapes product data from Manomano based on the specified product type.

extract_dimensions2(description): Extracts dimensions from the product description using regular expressions.

find_closest_products_manomano(products_data, width, height): Finds the closest products from Manomano based on the provided dimensions.

scrape_products(url, headers, product_type): Scrapes product data from Idealo using BeautifulSoup.

extract_dimensions(description): Extracts dimensions from product descriptions using regular expressions.

scrape_obi_products(product_type, zip_code, radius): Scrapes product data from Obi based on the product type, postal code, and radius.

find_closest_products(products_data, width, height, product_type): Finds the closest products based on the provided dimensions and product type.

Streamlit Interface
The Streamlit interface allows users to input their preferences and initiate the scraping process. The closest products are displayed based on the input dimensions and criteria.
