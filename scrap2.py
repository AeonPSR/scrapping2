from bs4 import BeautifulSoup
from urllib.parse import urljoin
import requests
import re
import os
import pandas as pd


def scrapProductPage(siteURL, URL, data):
	
	def FindAndAdd(dataName, htmlclass, parentClassName, positionChild):
		parent = soup.find(htmlclass, class_=parentClassName)
		if parent:
			childrens = parent.find_all(recursive=False)
			if len(childrens) >= (positionChild + 1):
				data[dataName].append(childrens[positionChild].get_text(strip=True))
			else:
				print(dataName + " not found. URL:"+URL)
				data[dataName].append('Error 404')
		else:
			print(parentClassName + " not found. URL:"+URL)
			data[dataName].append('Error 404')
	
	# Make a request to the website with headers using a browser request
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'}
	response = requests.get(URL, headers=headers)
	soup = BeautifulSoup(response.text, 'html.parser')

	data['product_page_URL'].append(URL)
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
		print("Review Module not found. URL:"+URL)
		data["review_rating"].append('Error 404')

	# Image
	imageParent = soup.find("div", class_="item")
	if imageParent:
		childrens = imageParent.find_all(recursive=False)
		if len(childrens) >= (1):
			shortURL = childrens[0].get('src')
			data["image_URL"].append(urljoin(siteURL, shortURL))
		else:
			print("image_URL not found. URL:"+URL)
			data["image_URL"].append('Error 404')
	else:
		print("Item class not found. URL:"+URL)
		data["image_URL"].append('Error 404')
	table_stripped = soup.find('table', class_='table-striped')
	if table_stripped:
		table_children = table_stripped.find_all(recursive=False)
		# price_excluding_tax
		if len(table_children) >= 3:
			price_text = table_children[2].find_all(recursive=False)[1].get_text(strip=True)
			data['price_excluding_tax'].append(price_text[1:]) # Without this, a ghost Â appear due to how monetary symbols are encoded
		else:
			print("Not enough children in tbody. URL:"+URL)
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

def LinksExtraction(siteURL, sectionURL):
	CurrentPage = 1
	links = []
	sectionURL = sectionURL.replace("index.html", "")
	while True:
		
		if (CurrentPage == 1):
			CurrentPageURL = urljoin(sectionURL, f"index.html")
		else:
			CurrentPageURL = urljoin(sectionURL, f"page-{CurrentPage}.html")

		# Make a request to the website with headers using a browser request
		headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'}
		response = requests.get(CurrentPageURL, headers=headers)
		soup = BeautifulSoup(response.text, 'html.parser')

		# Get all links (need to expand to take several pages)
		list_items = soup.find_all('article', class_='product_pod')

		for product_pod in list_items:
			relativeLink = product_pod.find('h3').find('a')['href']
			absoluteLink = (siteURL + "catalogue/" + relativeLink.replace("../", ""))
			links.append(absoluteLink)
		#Check if there's another page or not
		next_page_link = soup.find('li', class_='next')
		if not next_page_link:
			break
		CurrentPage += 1
	return links

def imageDownload(data, output_path):
	output_path = "images/"+output_path
	for idx, image_url in enumerate(data['image_URL']):
		if not os.path.exists(output_path):
			os.makedirs(output_path)
		image_filename = f"image_{idx + 1}.jpg"  # Generate a filename for the image
		image_path = os.path.join(output_path, image_filename)  # Combine with output folder path

		# Download the image
		response = requests.get(image_url)
		if response.status_code == 200:
			with open(image_path, 'wb') as f:
				f.write(response.content)
		print(f"Image {idx + 1} downloaded successfully.")
	else:
		print(f"Failed to download image {idx + 1}.")

def extractSection(name, sectionURL, siteURL):
	# The dictionnary
	data = {
		'product_page_URL': [],
		'upc': [],
		'title': [],
		'price_including_tax': [],
		'price_excluding_tax': [],
		'number_available': [],
		'product_description': [],
		'category': [],
		'review_rating': [],
		'image_URL': [],
	}

	sectionURL = siteURL + sectionURL

	linksSection = LinksExtraction(siteURL, sectionURL)
	for link in linksSection:
		scrapProductPage(siteURL, link, data)
	# Export to file
	imageDownload(data, name) #download images
	df = pd.DataFrame(data)
	df.to_csv("files/"+name+".csv", index=False, encoding='utf-8')

def extractListSections(siteURL):

	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36'}
	response = requests.get(siteURL, headers=headers)
	soup = BeautifulSoup(response.text, 'html.parser')

	categories = []
	nav_list = soup.find('ul', class_='nav-list')
	link_items = nav_list.find_all('a')

	for link in link_items:
		name = link.text.strip()
		href = link['href']
		categories.append([name, href])
	return categories

siteURL = "https://books.toscrape.com/"
#extractSection("Mystery", siteURL, "https://books.toscrape.com/catalogue/category/books/mystery_3/")

# Make a request to the website with headers using a browser request

categories = extractListSections(siteURL)
categories = categories[1:] #Removing the first element that is the full list of books

i = 0
for element in categories:
	extractSection(categories[i][0], categories[i][1], siteURL)
	i = i + 1
