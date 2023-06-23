print("Importing libraries and files...")

from gnews import GNews
from collections import Counter
import subprocess
import concurrent.futures
from multiprocessing.dummy import Pool as ThreadPool
import requests
from time import time
from newspaper import Article
import pandas as pd
import spacy
from formatAuthors import nameFormat, authorListFormat

nlp = spacy.load('en_core_web_sm')
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

def article_extract(articleURL:str):
	p = subprocess.Popen([nodepath, 'extractortest.js', articleURL], stdout=subprocess.PIPE)
	out = p.stdout.read().decode('utf8')
	return(out)
#looks like node is slightly slower (though only slightly).
#Will just use newspaper3k for now, but worth checking speed metrics/multithread compatability with node as well

def newspaper3k_extract(articleURL:str):
	myArticle = Article(url=articleURL)
	myArticle.download()
	myArticle.parse()
	return(myArticle.text)

def n3k_authors(url:str):
	a = Article(url)
	a.download()
	a.parse()
	return(a.authors)

def node_cite_info(articleURL:str):
	p = subprocess.Popen([nodepath, 'get_authors.js', articleURL], stdout=subprocess.PIPE)
	out = p.stdout.read().decode('utf8').split('\t') #surely there won't be a \n in the authors or title...
	try:
		if(len(out) == 2):
			return([out[0], nameFormat(out[1]), "NA"])
		else:
			return(["titleNotFound_py", "authorNotFound_py", "NA"])
	except Exception as e:
		print("Node article didn't work as expected.")
		print("Node output:", out)
		print("Error:", e)
		return(["titleNotFound_py2", "authorNotFound_py2", "NA"])

def n3k_cite_info(articleURL:str):
	myArticle = Article(url = articleURL)
	try:
		myArticle.download()
		myArticle.parse()
	except Exception as e:
		if("404" in str(e)):
			print("404 error on", articleURL)
			return(["titleNotFound_404", "authorNotFound_404", "404"])
		else:
			print("N3k Article download error:", e)
			print("Trying with Node.")
			#return(['DLerror', 'DLerror'])
			#and then try with node extractor. lol.
			return(node_cite_info(articleURL))
	try:
		authors = authorListFormat(myArticle.authors)
		#print("ok1", end=" ")
		if(len(myArticle.authors) > 0 and authors == 'unlikelyName' or authors.isspace() or authors == ''):
			authors = myArticle.authors[0]
		#print("ok2")
	except Exception as e:
		print("Author parse error:", e)
		print("url:", articleURL)
		authors = 'authorParseError'
	#n3k pubdate unreliable so just parse the gnews date instead...
	#get publisher from outside n3k too
	title = myArticle.title
	#temporaryily just including pre-processed .authors list too
	return([title, authors, myArticle.authors])
	
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
# df['title'] = df['title'].apply(lambda x: "".join(x.split(' - ')[0:-1]))
# print("Adjusted titles.")
#df['url'] = df['url'].apply(lambda x: requests.get(x).url)
#^ request is pretty slow. thread here?

with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
	#df['url'] = df['url'].apply(lambda url: requests.get(url).url)
	res = executor.map(lambda x: requests.get(x).url, df['url'])
df['url'] = list(res) #i think order isnt preserved so uh...
print(df['url'])
print("Got urls.")
df = df[['cbsnews.com/essentials' not in x for x in df['url']]]
print("Filtered cbs.")
#print("Getting text...")
# df['text'] = df.apply(rowURLtoText, axis=1)
# df2 = df[['victor cha' in x.lower() for x in df['text']]]
#filtered_articles = [x for x in results if ("www.politico.com" not in x['publisher']['href'] or "victor cha" in parse_politico(requests.get(x['url']).url).lower())]
start = time()
df = df[df.apply(lambda x: ("www.politico.com" not in x['site'] or "victor cha" in parse_politico(requests.get(x['url']).url).lower()), axis=1)]
end = time()
print("(Took", end-start, "to filter politico.)")
# filtered_articles = [x for x in filtered_articles if ("koreajoongangdaily" not in x['publisher']['href'] or "victor cha" in newspaper3k_extract(requests.get(x['url']).url).lower())]
start = time()
df = df[df.apply(lambda x: ("koreajoongangdaily" not in x['site'] or "victor cha" in newspaper3k_extract(requests.get(x['url']).url).lower()), axis=1)]
end = time()
print("(Took", end-start, "to filter joongang.)")

#issue:
#some articles that we get from gnews are totally irrelevant (about boy bands or something)
#or are not actually about the subject because the site has their name somewhere on the site but not the article
#trying to filter by getting article text and checking for exact match doesn't always work
#bc of paywalled articles and article text extract sometimes failing to properly get article text
#idk. I think just manually see which websites are problematic and specially treat those.
#Currently just politico and JoongAng so not too bricked, I guess.

#todo: get citation info, group by site on docx output
df = df.drop('description', axis=1)
pool = ThreadPool(10)
print("trying n3k...")
results = pool.map(n3k_cite_info, df['url'].tolist())
#df[['title', 'author', 'publish_date']] = df['url'].apply(n3k_cite_info).apply(pd.Series)
#extremely lazy I give up df updating
d = pd.DataFrame(results)
df['title'] = d.iloc[:, 0]
df['author'] = d.iloc[:, 1]
df['author_raw'] = d.iloc[:, 2]
pool.close()

df.to_excel("test.xlsx")

#TODO:
#see test.xlsx and look through which articles keep bricking things for everyone else
#e.g. politico, foreign affairs, NK News...
#and also adjust search terms (e.g. that one real estate article/hong kong arts festival)