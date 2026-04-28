import requests
from bs4 import BeautifulSoup

def extract_nfce_data(url):
    # Headers are essential to mimic a real browser and avoid 403 errors
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    try:
        # Requesting the website content
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Check for HTTP errors (403, 404, 500, etc.)

        # Parsing the HTML using lxml for better performance
        soup = BeautifulSoup(response.text, 'lxml')

        # 1. Locate the results table by its ID
        results_table = soup.find('table', {'id': 'tabResult'})
        
        if not results_table:
            print("Error: Could not find the items table. The site layout might have changed.")
            return []

        extracted_items = []

        # 2. Iterate through each row (tr) in the table
        for row in results_table.find_all('tr'):
            try:
                # Extracting data using the specific classes from the HTML
                product_name = row.find('span', class_='txtTit').get_text(strip=True)
                
                # Extracting quantity and removing the "Qtde.:" label
                quantity = row.find('span', class_='Rqtd').get_text(strip=True).replace('Qtde.:', '').strip()
                
                # Extracting unit value and removing "Vl. Unit.:"
                unit_price = row.find('span', class_='RvlUnit').get_text(strip=True).replace('Vl. Unit.:', '').strip()
                
                # Extracting the total value of the item
                total_price = row.find('span', class_='valor').get_text(strip=True)

                extracted_items.append({
                    'product': product_name,
                    'qty': quantity,
                    'unit_price': unit_price,
                    'total': total_price
                })
            except AttributeError:
                # Skip rows that don't match the expected structure (like spacers or headers)
                continue 

        return extracted_items

    except requests.exceptions.RequestException as e:
        print(f"Connection error: {e}")
        return []


