from gnews import GNews
from collections import Counter
import subprocess
import requests
from time import time
from newspaper import Article
import pandas as pd
# queries_path='queries.txt'
# with open(queries_path) as f:
# 	queryList = f.read().split('\n')

with open('nodepath.txt', 'r') as f:
	nodepath = f.read()

query = 'Victor Cha'
startDate = '2022-01-01'
endDate = '2022-12-31'
#set to today if no end date specified. I think Y-m-d is the correct format.
sQuery = '"' + query + '"' + ' AND "Korea" before:' + endDate + " after:" + startDate
print("Getting news...")
start = time()
google_news = GNews(exclude_websites = ['csis.org', 'youtube.com'], max_results = 1000)
results = google_news.get_news(sQuery)
end = time()
print("Found", len(results), "results for", query, "in date range", startDate, "to", endDate)
print("Took", end-start)

def parse_politico(articleURL:str):
	#given one POLITICO article (of the dictionary format one gets from Gnews),
	#determine whether or not it actually mentions Victor Cha in the article body
	#and not all the useless crap at the bottom
	p = subprocess.Popen([nodepath, 'politico_extractor.js', articleURL], stdout=subprocess.PIPE)
	#node_output = subprocess.check_output([nodepath, 'politico_extractor.js', articleURL], encoding='utf-8').strip()
	out = p.stdout.read().decode('utf8')
	return(out)

# def article_extract(articleURL:str):
# 	p = subprocess.Popen([nodepath, 'extractortest.js', articleURL], stdout=subprocess.PIPE)
# 	out = p.stdout.read().decode('utf8')
# 	return(out)
#looks like node is slightly slower (though only slightly).
#Will just use newspaper3k for now, but worth checking speed metrics/multithread compatability with node as well

def newspaper3k_extract(articleURL:str):
	myArticle = Article(url=articleURL)
	myArticle.download()
	myArticle.parse()
	return(myArticle.text)

def rowURLtoText(row):
	#since we want to use politico extractor if politico else n3k
	if('www.politico.com' in row['site']):
		return(parse_politico(row['url']))
	else:
		try:
			return(newspaper3k_extract(row['url']))
		except Exception as e:
			print(e)
			return("(error)")

df = pd.DataFrame(results)
df = pd.concat([df.drop(['publisher'], axis=1), df['publisher'].apply(pd.Series).rename(columns = {"href": "site", "title": "publisher"})], axis=1)
print("Made data frame.")
df['title'] = df['title'].apply(lambda x: "".join(x.split(' - ')[0:-1]))
print("Adjusted titles.")
df['url'] = df['url'].apply(lambda x: requests.get(x).url)
#^ request is pretty slow. thread here?
print("Got urls.")
df = df[['cbsnews.com/essentials' not in x for x in df['url']]]
print("Filtered cbs.")
print("Getting text...")
start = time()
df['text'] = df.apply(rowURLtoText, axis=1)
df = df[['victor cha' in x.lower() for x in df['text']]]
end = time()
print("Done. Took", end-start)
#print("Filtering articles:")

#filtered_articles = [x for x in results if ("www.politico.com" not in x['publisher']['href'] or "victor cha" in parse_politico(requests.get(x['url']).url).lower())]
# start = time()
# filtered_articles = [x for x in filtered_articles if ("koreajoongangdaily" not in x['publisher']['href'] or "victor cha" in newspaper3k_extract(requests.get(x['url']).url).lower())]
# end = time()
# print("Took", end-start, "to filter joongang with newspaper3k.")
# filtered_articles = [x for x in filtered_articles if "cbsnews.com/essentials" not in x['publisher']['href']]
# end = time()
# #print("Took", end-start, "to filter CBS.")
# print("removed", len(results) - len(filtered_articles), "irrelevant articles.")

# print("Results:")
# print("There were", len(set([x['publisher']['title'] for x in filtered_articles])), "different publishers.")
# print("Publisher counts:")
# for k,v in Counter([x['publisher']['title'] for x in filtered_articles]).items():
# 	print(k, ": ", v, sep="")
# print("Articles:")
# for x in filtered_articles:
# 	s = x['title'] + ' on ' + x['published date'][5:16]
# 	print(s)
print(df)