from bs4 import BeautifulSoup
import requests
import re
import pandas as pd

# The dictionnary
data = {
	'product_page_url': [],
	'upc': [],
	'title': [],
	'price_including_tax': [],
	'price_excluding_tax': [],
	'number_available': [],
	'product_description': [],
	'category': [],
	'review_rating': [],
	'image_url': [],
}

# Make a request to the website with headers using a browser request
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'
}
url = 'https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html'
response = requests.get(url, headers=headers)

# Parse the HTML content
soup = BeautifulSoup(response.text, 'html.parser')

data['product_page_url'].append('error')
data['title'].append('error')
data['number_available'].append('error')
data['product_description'].append('error')
data['category'].append('error')
data['review_rating'].append('error')
data['image_url'].append('error')

table_stripped = soup.find('table', class_='table-striped')
if table_stripped:
	table_children = table_stripped.find_all(recursive=False)
	# upc
	if len(table_children) >= 1: 
		data['upc'].append(table_children[0].find_all(recursive=False)[1].get_text(strip=True))
	else:
		print("Not enough children in tbody.")
		data['upc'].append('Errror 404')
	# price_excluding_tax
	if len(table_children) >= 3: 
		price_text = table_children[2].find_all(recursive=False)[1].get_text(strip=True)
		data['price_excluding_tax'].append(price_text[1:]) # Without this, a ghost Â appear due to how monetary symbols are encoded
	else:
		print("Not enough children in tbody.")
		data['price_excluding_tax'].append('Errror 404')
	# price_including_tax
	if len(table_children) >= 4: 
		price_text = table_children[3].find_all(recursive=False)[1].get_text(strip=True)
		data['price_including_tax'].append(price_text[1:]) # Without this, a ghost Â appear due to how monetary symbols are encoded
	else:
		print("Not enough children in tbody.")
		data['price_including_tax'].append('Error 404')
	
else:
	print("Table with class 'table-striped' not found.")


# Export to file
df = pd.DataFrame(data)
df.to_csv('data.csv', index=False, encoding='utf-8')