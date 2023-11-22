import argparse
import time
from datetime import date, datetime, timezone

def naver(query:str, startDate:str, endDate:str):
	results = pd.DataFrame(naver_main(query, startDate, endDate)) #list of dicts -> pd
	#columns: title (bad, gets cut off), originallink, link (usually naver link), description (no need), pubDate
	#columns to have for merge: publisher, published date, title, url
	if results.size == 0:
		return(pd.DataFrame(columns=['title', 'url', 'date']))
	else:
		results.drop(['link', 'description'], axis=1, inplace=True)
		results.rename(columns = {"originallink": "url", "pubDate": "date"}, inplace=True)
		#example date: 'Thu, 07 Sep 2023 20:21:00 +0900'
		results['date'] = results.apply(lambda x: datetime.strptime(x['date'], "%a, %d %b %Y %H:%M:%S %z"), axis=1)
		return(results) #title, url, date

def newspaper3k_extract(articleURL:str):
	myArticle = Article(url=articleURL)
	myArticle.download()
	myArticle.parse()
	return(myArticle.text)

def n3k_cite_info(articleURL:str):
	#aiee spaghetti
	flag = False
	if(urlFilter(articleURL)):
		flag = True
	myArticle = Article(url = articleURL, keep_article_html = flag)
	try:
		myArticle.download()
		myArticle.parse()
	except Exception as e:
		if("404" in str(e)):
			print("404 error on", articleURL)
			return([articleURL, "_titleNotFound_404", "_authorNotFound_404", "_404"])
		else:
			print("N3k Article download error:", e)
			return([articleURL, "_titleNotFound_n3kerror", "_authorNotFound_n3kerror", "_sitenameNotFound_n3kerror"])
	try:
		authors = authorListFormat(myArticle.authors)
		#i want to also check if publisher is the author and ignore if so but idt it will work
		if(len(myArticle.authors) > 0 and (authors == 'unlikelyName' or authors.isspace() or authors == '')):
			authors = myArticle.authors[0]
		#need to double-check logic here
	except Exception as e:
		print("Author parse error:", e)
		print("url:", articleURL)
		authors = '_authorParseError'
	#n3k pubdate, publisher unreliable (?) but icbf
	title = myArticle.title #bc gnews result can be concatenated and has - publisher at the end
	#temporaryily just including pre-processed .authors list too
	sitename = myArticle.meta_data['og'].get('site_name', '_sitename_notfound')
	canonurl = myArticle.canonical_link
	if(len(authors) == 0):
		authors = "_authorNotFound"
	# if myArticle.publish_date:
	# 	#pubdate = myArticle.publish_date.replace(tzinfo = timezone.utc)
	# 	pubdate = datetime.strftime(myArticle.publish_date, "%Y-%m-%d")
	# else:
	# 	pubdate = "_not found"
	return([canonurl, title, authors, sitename])

def gnews(query:str, startDate:str, endDate:str, exactQuery=False): #-> 1-d list of string urls
	global query
	#careful...
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

	if len(results_en) == 0:
		gnews_results = results_kr
	elif len(results_kr) == 0:
		gnews_results = results_en
	elif len(results_en) > 0 and len(results_kr) > 0: 
		gnews_results = pd.concat([results_en, results_kr], ignore_index=True, axis=0)

	if gnews_results.size == 0:
		print("0 results found from Google News.")
		return pd.DataFrame(columns=['title', 'url', 'date'])

	print("Found", gnews_results.shape[0], "results for", query, "in date range", startDate, "to", endDate)
	print("Took", end-start)

	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		tmp = executor.map(lambda x: requests.get(x).url, gnews_results['url'])
	#do this bc the gnews api returns the rss url and not the actual url (maybe diff. from canon url)
	#? somehow getting 0 urls after ^
	res = list(tmp)
	gnews_results['url'] = res
	gnews_urls = res
	print("Got urls.")
	
	if len(gnews_urls) == 0:
		print("0 results after filtering.")
		return pd.DataFrame(columns=['title', 'url', 'date'])

	gnews_urls = [i for (i, v) in zip(gnews_urls, ['cbsnews.com/essentials' not in x for x in gnews_urls]) if v]
	print("Filtered cbs.")
	#need to manual filter certain cases
	#see test.py...

	df = gnews_results[gnews_results['url'].isin(gnews_urls)].copy()
	df.drop(['description', 'publisher'], axis=1, inplace=True)
	df.rename(columns = {'published date': 'date'}, inplace=True)
	df['date'] = df.apply(lambda x: datetime.strptime(x['date'], "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo = timezone.utc), axis=1)
	return df

def main(query:str, startDate:str, endDate:str, outfile:str, exactQuery=False):
	gnews_df = gnews(query, startDate, endDate, exactQuery) #title, url, date
	naver_df = naver(query, startDate, endDate) #title, url, date
	df = pd.concat([gnews_df, naver_df], ignore_index = True, axis=0)
	#print(df)
	#df.columns = ['title', 'url', 'date']
	#ended up being title date url? what? when? how?
	
	all_urls = list(df['url'])
	
	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		tmp = executor.map(lambda x: n3k_cite_info(x), all_urls)
	n3k_df = pd.DataFrame(list(tmp))
	n3k_df.columns = ['url', 'title', 'authors', 'publisher']
	#priorities:
	#url is the same
	#prefer title from gnews/naver, unless it ends in ... (cut off from search engine), then use n3k
	#author is only n3k
	#publisher is n3k only
	#use date from gnews/naver (unless there isn't one, which I can't think of why it would happen...)
	#not considering priority of duplicate url for now
	def make_row(index):
		thisUrl = n3k_df.at[index,'url']
		title_api = df.at[index, 'title']
		title_n3k = n3k_df.at[index, 'title']
		thisAuth = n3k_df.at[index, 'authors']
		thisPub = n3k_df.at[index, 'publisher']
		thisDate = datetime.strftime(df.at[index, 'date'], "%Y-%m-%d")

		title_api = ''.join(title_api.split(' - ')[:-1])
		thisTitle = title_api
		if (title_api[-3:] == '...'):
			thisTitle = title_n3k
		return([thisUrl, thisTitle, thisAuth, thisPub, thisDate])

	out = pd.DataFrame([make_row(i) for i in range(len(all_urls))])
	out.columns = ['url', 'title', 'authors', 'publisher', 'date']
	#df['date'] = df.apply(lambda x: datetime.strftime(x['date'], "%Y-%m-%d"), axis=1)
	out.sort_values(by='publisher', inplace=True)
	out.drop_duplicates('url', inplace=True, keep='last') #since sorted by publisher earlier, this should discard _sitename and keep other
	out.sort_values(by='date', inplace=True)
	out.to_excel(outfile, index=False)
	print("Done. Wrote to", outfile)


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
	#from collections import Counter
	import subprocess
	import concurrent.futures
	from multiprocessing.dummy import Pool as ThreadPool
	import requests
	from newspaper import Article
	from newspaper.parsers import Parser
	from newspaper.extractors import ContentExtractor
	import pandas as pd
	import sys
	from formatAuthors import nameFormat, authorListFormat
	from naver_api import naver_main
	from custom_filters import urlFilter

	import monkeypatch
	#OriginalClass.class_method = classmethod(custom_class_method)
	Parser.getElementsByTag = monkeypatch.getElementsByTag_custom
	ContentExtractor.get_authors = monkeypatch.get_authors_custom
	ContentExtractor.is_latin = monkeypatch.is_latin

	main(query = args.query, startDate = args.start, endDate = args.end, outfile = args.output, exactQuery = args.exact)
