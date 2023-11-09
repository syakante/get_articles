import argparse
import time
from datetime import date, datetime

def naver(query:str, startDate:str):
	results = pd.DataFrame(naver_main(query, startDate)) #list of dicts -> pd
	#columns: title (bad, gets cut off), originallink, link (usually naver link), description (no need), pubDate
	#columns to have for merge: publisher, published date, title, url
	if results.size == 0:
		return([])
	else:
		results.drop(['title', 'link', 'description'], axis=1, inplace=True)
		results.rename(columns = {"originallink": "url", "pubDate": "published date"}, inplace=True)
		return(results['url'].tolist())

def newspaper3k_extract(articleURL:str):
	myArticle = Article(url=articleURL)
	myArticle.download()
	myArticle.parse()
	return(myArticle.text)

def n3k_cite_info(articleURL:str):
	#aiee spaghetti
	myArticle = Article(url = articleURL)
	try:
		myArticle.download()
		myArticle.parse()
	except Exception as e:
		if("404" in str(e)):
			print("404 error on", articleURL)
			return([articleURL, "titleNotFound_404", "authorNotFound_404", "404"])
		else:
			print("N3k Article download error:", e)
			return([articleURL, "titleNotFound_n3kerror, authorNotFound_n3kerror", "sitenameNotFound_n3kerror"])
	try:
		authors = authorListFormat(myArticle.authors)
		#i want to also check if publisher is the author and ignore if so but idt it will work
		if(len(myArticle.authors) > 0 and (authors == 'unlikelyName' or authors.isspace() or authors == '')):
			authors = myArticle.authors[0]
		#print("ok2")
	except Exception as e:
		print("Author parse error:", e)
		print("url:", articleURL)
		authors = 'authorParseError'
	#n3k pubdate, publisher unreliable (?) but icbf
	title = myArticle.title #bc gnews result can be concatenated and has - publisher at the end
	#temporaryily just including pre-processed .authors list too
	sitename = myArticle.meta_data['og'].get('site_name', '_sitename_notfound')
	canonurl = myArticle.canonical_link
	if(len(authors) == 0):
		authors = "authorNotFound"
	if myArticle.publish_date:
		pubdate = datetime.timestamp(myArticle.publish_date) #datetime.datetime object -> timestamp bc of timezone naive/aware stuff
	else:
		pubdate = "publish_date not found"
	return([canonurl, title, authors, sitename, pubdate])
	
def main(query:str, startDate:str, endDate:str, outfile:str, exactQuery=False):
	if exactQuery:
		sQuery = '"' + query + '"' + ' before:' + endDate + " after:" + startDate
	else:
		sQuery = '"' + query + '"' + ' AND Korea before:' + endDate + " after:" + startDate
	sQuery_kr = '"' + query + '"' + 'before:' + endDate + " after:" + startDate
	print("Getting news...")
	start = time.time()
	google_news_en = GNews(exclude_websites = ['csis.org', 'youtube.com'], max_results = 1000)
	google_news_kr = GNews(exclude_websites = ['csis.org', 'youtube.com'], max_results = 1000, country = 'KR', language = 'ko')
	results_en = pd.DataFrame(google_news_en.get_news(sQuery))
	results_kr = pd.DataFrame(google_news_kr.get_news(sQuery_kr))
	end = time.time()
	print("Found", len(results_en)+len(results_kr), "results for", query, "in date range", startDate, "to", endDate)
	print("Took", end-start)

	gnews_results = pd.concat([results_en, results_kr], ignore_index=True)
	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		res = executor.map(lambda x: requests.get(x).url, gnews_results['url'])
	#do this bc the gnews api returns the rss url and not the actual url (maybe diff. from canon url)
	gnews_urls = list(res)
	print("Got urls.")

	gnews_urls = [i for (i, v) in zip(gnews_urls, ['cbsnews.com/essentials' not in x for x in gnews_urls]) if v]
	print("Filtered cbs.")
	start = time.time()
	#df = df[df.apply(lambda x: ("www.politico.com" not in x['site'] or query.lower() in parse_politico(requests.get(x['url']).url).lower()), axis=1)]
	#basically, if url is www.politico.com --> do parse_politico --> if query isnt in the site text, drop it
	#work in progress bc n3k thinks the whole webpage is the article when it really stops after <aside class="story-related">
	#but im trying to figure out how to monkey patch n3k to do this... or find some other hack tbh
	#for now just ignore all politico...
	gnews_urls = [i for (i, v) in zip(gnews_urls, ['www.politico.com' not in x for x in gnews_urls]) if v]
	end = time.time()
	print("(Took", end-start, "to filter politico.)")
	# filtered_articles = [x for x in filtered_articles if ("koreajoongangdaily" not in x['publisher']['href'] or "victor cha" in newspaper3k_extract(requests.get(x['url']).url).lower())]
	start = time.time()
	gnews_urls = [i for (i, v) in zip(gnews_urls, ['joongang' not in x or "victor cha" in newspaper3k_extract(x).lower() for x in gnews_urls]) if v]
	end = time.time()
	print("(Took", end-start, "to filter joongang.)")

	#by now you have your list of good urls gotten from gnews (though not yet canonical)
	#naver(query, startDate) --> outputs a df of (see naver function)
	#? if im going to n3k everything anyway why not just get the url only from here too
	#...tbh at this point just make a new .py file
	naver_urls = naver(query, startDate)
	all_urls = gnews_urls + naver_urls
	#why not parallelize this
	df = pd.DataFrame([n3k_cite_info(url) for url in all_urls])
	df.to_excel(outfile)


if __name__ == "__main__":
	today = date.today().strftime("%Y-%m-%d")
	parser = argparse.ArgumentParser(description = "Retrieve Google and Naver news results given a search query and time frame.")
	parser.add_argument("--query", "-q", type=str, required=True, help="Search query. If there are spaces, put the whole query in double quotes.")
	parser.add_argument("--start", "-s", type=str, required=True, help="Start date, formatted as YYYY-MM-DD.")
	parser.add_argument("--end", "-e", type=str, required=False, help="End date, formatted as YYYY-MM-DD. If not used, defaults to today.",
		nargs = "?", default = today, const=today)
	parser.add_argument("--output", "-o", type=str, required=True, help="Filename of output file.")
	parser.add_argument("--exact", "-x", type=str, required=False, help="T/F search for your exact query (i.e. quotes around it in the search engine).")

	args = parser.parse_args()

	print('Getting results for "', args.query, '", from', args.start, 'to', args.end)

	print("Importing libraries and files...")

	from gnews import GNews
	from collections import Counter
	import subprocess
	import concurrent.futures
	from multiprocessing.dummy import Pool as ThreadPool
	import requests
	from newspaper import Article
	import pandas as pd
	import spacy
	from formatAuthors import nameFormat, authorListFormat
	from naver_api import naver_main

	nlp = spacy.load('en_core_web_sm')
	# queries_path='queries.txt'
	# with open(queries_path) as f:
	# 	queryList = f.read().split('\n')

	with open('nodepath.txt', 'r') as f:
		nodepath = f.read()

	main(query = args.query, startDate = args.start, endDate = args.end, outfile = args.output)
