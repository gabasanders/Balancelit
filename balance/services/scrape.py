import requests
from bs4 import BeautifulSoup

def extract_nfce_data(url):
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'lxml')

        # 1. Find the results table by ID
        table = soup.find('table', {'id': 'tabResult'})
        
        if not table:
            print("Could not find the items table. The site may have changed or blocked access.")
            return []

        extracted_items = []

        
        for row in table.find_all('tr'):
            # Keep parsing resilient in case a specific row is malformed
            try:
                name = row.find('span', class_='txtTit').get_text(strip=True)
                
                # Clean string to keep only the raw value
                code = row.find('span', class_='RCod').get_text(strip=True).replace('(Código:', '').replace(')', '').strip()
                
                # Quantity (remove "Qtde.:" label)
                quantity = row.find('span', class_='Rqtd').get_text(strip=True).replace('Qtde.:', '').strip()
                
                # Unit price (remove "Vl. Unit.:" label)
                unit_price = row.find('span', class_='RvlUnit').get_text(strip=True).replace('Vl. Unit.:', '').strip()
                
                # Item total
                total_price = row.find('span', class_='valor').get_text(strip=True)

                extracted_items.append({
                    'item': name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_price': total_price
                })
            except AttributeError:
                continue # Skip rows that don't match the pattern (headers/dividers)

        return extracted_items

    except requests.exceptions.RequestException as e:
        print(f"Error connecting to the site: {e}")
        return []
