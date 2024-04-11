from bs4 import BeautifulSoup
from urllib.parse import urljoin
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
baseUrl = "https://books.toscrape.com/"
url = 'https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html'
response = requests.get(url, headers=headers)

# Parse the HTML content
soup = BeautifulSoup(response.text, 'html.parser')

data['product_page_url'].append('TODO')

def FindAndAdd(dataName, htmlclass, parentClassName, positionChild):
	parent = soup.find(htmlclass, class_=parentClassName)
	if parent:
		childrens = parent.find_all(recursive=False)
		if len(childrens) >= (positionChild + 1):
			data[dataName].append(childrens[positionChild].get_text(strip=True))
		else:
			print(dataName + " not found.")
			data[dataName].append('Error 404')
	else:
		print(parentClassName + " not found")
		data[dataName].append('Error 404')

FindAndAdd("category", "ul", "breadcrumb", 2)
FindAndAdd("title", "div", "product_main", 0)
FindAndAdd("product_description", "article", "product_page", 2)
FindAndAdd("upc", "table", "table", 0)

# Stuff that need a custom code

# Review
starModule = soup.find("p", class_="star-rating")
if starModule:
	classes = starModule.get('class')
	data["review_rating"].append([c for c in classes if c != 'star-rating'][0])
	# This extract the other class, that hold the information of how many stars there are.
else:
	print("Review Module  not found")
	data["review_rating"].append('Error 404')

# Image
imageParent = soup.find("div", class_="item")
if imageParent:
	childrens = imageParent.find_all(recursive=False)
	if len(childrens) >= (1):
		shorturl = childrens[0].get('src')
		data["image_url"].append(urljoin(baseUrl, shorturl))
	else:
		print("image_url not found.")
		data["image_url"].append('Error 404')
else:
	print("Item class not found")
	data["image_url"].append('Error 404')


table_stripped = soup.find('table', class_='table-striped')
if table_stripped:
	table_children = table_stripped.find_all(recursive=False)
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
	# number_available
	if len(table_children) >= 6:
		nbr_text = table_children[5].find_all(recursive=False)[1].get_text(strip=True)
		data['number_available'].append(re.sub(r'\D', '', nbr_text)) # Remove the text
	else:
		print("Not enough children in tbody.")
		data['number_available'].append('Error 404')
else:
	print("Table with class 'table-striped' not found.")


# Export to file
df = pd.DataFrame(data)
df.to_csv('data.csv', index=False, encoding='utf-8')