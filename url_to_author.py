import csv
import requests
import json
from bs4 import BeautifulSoup
import concurrent.futures
from multiprocessing.dummy import Pool as ThreadPool

html_combos = { 'news.kbs.co.kr': ['span', '.text', {'class_': 'reporter-name'}],
				'newsis.com': ['script', 'author', {'type': 'application/ld+json'}],
				'donga.com': ['meta', 'content', {'property': 'dd:author'}],
				'munhwa.com': ['script', 'author', {'type': 'application/ld+json'}], 
				'chosun.com': ['a', '.text', {'class_': 'article-byline__author'}],
				'news1.kr': ['meta', 'content', {'property': 'article:author'}],
				'koreatimes.co.kr': ['div', 'title', {'class_': 'view_reporter_div'}]}

REPORTER = ['기자', '특파원']

def news1filter(string):
	for r in REPORTER:
		if(r in string):
			i = string.index(r)
			return(string[i-4:i].strip())
	return(string)

def get_value_from_url(url, element, searchfor, **kwargs):
	i = 0
	# if element == 'script':
	# 	i = 1
	#^ do sth about this
	# Send a GET request to the URL
	response = requests.get(url)

	# Check if the request was successful (status code 200)
	if response.status_code == 200:
		# Parse the HTML content
		soup = BeautifulSoup(response.content, 'html.parser')

		# Find the div element with the specified class
		#find_element = soup.find_all(element, **kwargs)
		find_element = soup.find(element, **kwargs)

		# Check if the div element with the specified class was found
		if find_element:
			# Get the value from the title attribute
			# attr_value = div_element.get(attr_to_get)
			# return attr_value
			if(searchfor == '.text'):
				return(find_element.text.strip())
			if(element == 'script'):
				this_json = find_element.string
				try:
					data = json.loads(this_json)
					tmp = data[searchfor]
					if isinstance(tmp, list):
						auth_list = data[searchfor][0]
					else:
						auth_list = data[searchfor]
					return(auth_list['name'])

				except Exception as e:
					print("JSON error", e)
					return 'error'

			return(find_element.get(searchfor))
			
		else:
			print(f"No {element} element with parameters {kwargs} found.")
	else:
		print(f"Failed to retrieve the webpage. Status code: {response.status_code}")

	return 'nothing'

def readcsv(infile:str):
	L = []
	with open(infile, newline='', encoding='utf-8-sig') as csvfile:
		csvreader = csv.reader(csvfile, delimiter=',', quotechar='|')
		for row in csvreader:
			L.extend(row)
	return(L)

def writecsv(outfile:str, L1, L2):
	with open(outfile, 'w', newline='', encoding='utf-8-sig') as csvfile:
		csvwriter = csv.writer(csvfile)
		csvwriter.writerows(zip(L1, L2))

def main(site, infile, outfile):
	#myclass = 'view_reporter_div'
	# element = 'span'
	# myclass = 'reporter-name'
	# myattr = 'title'
	urls = readcsv(infile)
	this_site = html_combos[site]

	#or .text
	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		tmp = executor.map(lambda x: get_value_from_url(x, this_site[0], this_site[1], **this_site[2]), urls)
	tmp2 = list(tmp)
	#print([news1filter(a) for a in authors])
	authors = [news1filter(a) for a in tmp2]
	writecsv(outfile, urls, authors)
	print("ok")

main('news1.kr', 'authors_in.csv', 'authors_out.csv')