import argparse
import time
from datetime import date, datetime, timezone, timedelta

IGNORE_SITES = ['csis.org', 'twitter.com', 'youtube.com', 'facebook.com', 'linkedin.com']

def kr_query(query:str) -> str:
	query = query.lower()
	if('korea chair' in query):
		query = query.replace('korea chair', '코리아 체어') #assuming csis is already in the query and double quotes around eng query
	if('victor cha' in query):
		query = query.replace('victor cha', '빅터 차')
	if('beyond parallel' in query):
		query = query.replace('beyond parallel', '비욘드 패럴렐')
	return(query)

def naver(query:str, startDate:str, endDate:str):
	print('Searching Naver for', query, ' from', startDate, 'to', endDate, '...')
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
		results['title'] = results.apply(lambda x: unescape(x['title']), axis=1)
		return(results) #title, url, date

def newspaper3k_extract(articleURL:str):
	myArticle = Article(url=articleURL)
	myArticle.download()
	myArticle.parse()
	return(myArticle.text)

def n3k_cite_info(articleURL:str):
	#aiee spaghetti
	# flag = False
	# if(urlFilter(articleURL)):
	# 	flag = True
	# myArticle = Article(url = articleURL, keep_article_html = flag)
	myArticle = Article(url = articleURL)
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
	canonurl = myArticle.canonical_link
	if canonurl == '':
		canonurl = articleURL
	if(urlFilter(canonurl) and articleTextCheck(myArticle)):
		return([canonurl, "_skip", "_skip", "_skip"])	
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
	if(len(authors) == 0):
		authors = "_authorNotFound"
	return([canonurl, title, authors, sitename])

def queryDateStr(query:str, startDate:str, endDate:str):
	return(query + ' before:' + endDate + ' after:' + startDate)

def gnews_recurse(gnews_obj, startDate, endDate, query:str, rec_lvl = 0):
	#recursvie func to get all results from gnews by recursively splitting date range

	#base case: <100 results so just return it
	print("Getting results from", startDate, "to", endDate)
	base_result = pd.DataFrame(gnews_obj.get_news(queryDateStr(query, startDate, endDate))) #assuming query doesn't have date attached
	if(len(base_result) < 100):
		print("Got <100 results.")
		return base_result

	print("Recursion level", rec_lvl)

	#get dates
	start_dt = date.fromisoformat(startDate)
	end_dt = date.fromisoformat(endDate)
	mid_date = start_dt + (end_dt - start_dt)/2
	mid_str1 = mid_date.isoformat()
	mid_str2 = (mid_date + timedelta(days=1)).isoformat() #(add 1 day to 2nd date so no overlap)

	#make two queries based on split date
	#base_query = query.split(" before:")[0]
	query1 = queryDateStr(query, startDate, mid_str1)
	query2 = queryDateStr(query, mid_str2, endDate)
	#results2 = pd.DataFrame(gnews_obj.get_news(query2))
	
	results_left = gnews_recurse(gnews_obj, startDate, mid_str1, query, rec_lvl+1)
	results_right = gnews_recurse(gnews_obj, mid_str2, endDate, query, rec_lvl+1)

	return(pd.concat([results_left, results_right], ignore_index=True, axis=0))


def myFetch(url):
	try:
		return(requests.get(url, timeout=10).url)
	except requests.exceptions.Timeout as e:
		print(f"Request timed out for URL: {url}. Error: {e}")
		return("_url_error_timeout")
	except requests.exceptions.RequestException as e:
		print(f"Error fetching URL: {url}. Error: {e}")
		return("_url_error")

def gnews(query:str, startDate:str, endDate:str, exactQuery=False):

	#not sure abt this V used to add "" around query but maybe just use them in the cli anyway
	if exactQuery == True:
		sQuery = query
	else:
		sQuery = query + " CSIS Korea"
	sQuery_kr = query
	#shockingly annoying new bug: you can't escape double quotes in windows powershell LMAO
	#but it's possible in cmd... sob

	print('Searching GNews for', sQuery, ' from', startDate, 'to', endDate, '...')
	print("Getting news...")
	start = time.time()
	google_news_en = GNews(exclude_websites = IGNORE_SITES, max_results = 1000)
	google_news_kr = GNews(exclude_websites = IGNORE_SITES, max_results = 1000, country = 'KR', language = 'ko')

	#at the time of this writing >100 results isn't actually supported.
	#(I assume it's top 100 results sorted by relevancy...)
	#So for a hack fix I guess try doing the query twice with the date range halved.
	#But then it's a problem if that too has greater than 100 results in which case I guess keep halving.
	'''
	if len(results_en) >= 100:
		results_en = gnews_halve(google_news_en, startDate, endDate, sQuery)
	if len(results_kr) >= 100:
		results_kr = gnews_halve(google_news_kr, startDate, endDate, sQuery_kr)
	
	#? maybe do the split before on some condition so it doesn't take twice as long
	#except there isn't any way to know for sure how many results there are before calling .get_news()
	#TODO think of something here
	if (int(endDate.split('-')[1]) - int(startDate.split('-')[1])) > 3:
		print("here")
		results_en = gnews_halve(google_news_en, startDate, endDate, sQuery)
		results_kr = gnews_halve(google_news_kr, startDate, endDate, sQuery_kr)
		#what about iterate monthly?
	else:
		results_en = pd.DataFrame(google_news_en.get_news(sQuery))
		results_kr = pd.DataFrame(google_news_kr.get_news(sQuery_kr))
	'''
	results_en = gnews_recurse(google_news_en, startDate, endDate, sQuery)
	results_kr = gnews_recurse(google_news_kr, startDate, endDate, sQuery_kr)

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

	print("Found", gnews_results.shape[0], "results for", query, "in date range", startDate, "to", endDate, "from GNews.")
	print("Took", end-start)

	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		tmp = executor.map(lambda x: myFetch(x), gnews_results['url'])

	res = list(tmp)
	gnews_results['url'] = res
	gnews_urls = res
	print("Got urls.")
	
	if len(gnews_urls) == 0:
		print("0 results after filtering.")
		return pd.DataFrame(columns=['title', 'url', 'date'])

	gnews_urls = [i for (i, v) in zip(gnews_urls, ['cbsnews.com/essentials' not in x for x in gnews_urls]) if v]
	gnews_urls = [i for (i, v) in zip(gnews_urls, ['sullcrom.com' not in x for x in gnews_urls]) if v]
	gnews_urls = [i for (i, v) in zip(gnews_urls, ['_url_error' not in x for x in gnews_urls]) if v]
	#^ TODO make this customizable etc

	df = gnews_results[gnews_results['url'].isin(gnews_urls)].copy()
	df.drop(['description', 'publisher'], axis=1, inplace=True)
	df.rename(columns = {'published date': 'date'}, inplace=True)
	df['date'] = df.apply(lambda x: datetime.strptime(x['date'], "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo = timezone.utc), axis=1)
	return df

def main(query:str, startDate:str, endDate:str, outfile:str, exactQuery=False):
	kQuery = kr_query(query)
	kQuery_flag = (kQuery != query)

	gnews_df = gnews(query, startDate, endDate, exactQuery) #title, url, date
	naver_df = naver(query, startDate, endDate) #title, url, date

	df = pd.concat([gnews_df, naver_df], ignore_index = True, axis=0)

	if(kQuery_flag):
		print("Also searching for", kQuery)
		gnews_df_kr = gnews(kQuery, startDate, endDate, exactQuery=False)
		naver_df_kr = naver(kQuery, startDate, endDate)
		df = pd.concat([df, gnews_df_kr, naver_df_kr], ignore_index = True, axis=0)
	
	#print("debug: df.shape", df.shape)
	df.drop_duplicates('url', inplace=True, keep='first', ignore_index=True)
	#print("debug: df.shape", df.shape)

	all_urls = list(df['url'])
	#print("debug: len(all_urls)", len(all_urls))

	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		tmp = executor.map(lambda x: n3k_cite_info(x), all_urls)
	n3k_df = pd.DataFrame(list(tmp))
	n3k_df.columns = ['url', 'title', 'authors', 'publisher']
	#print("debug: n3k_df.shape", n3k_df.shape)
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

		if(' - ' in title_api):
			title_api = ''.join(title_api.split(' - ')[:-1])
		thisTitle = title_api
		if (title_api[-3:] == '...'):
			thisTitle = title_n3k
		return([thisUrl, thisTitle, thisAuth, thisPub, thisDate])

	out = pd.DataFrame([make_row(i) for i in range(n3k_df.shape[0])])
	#print("debug: out.shape", out.shape)
	out.columns = ['url', 'title', 'authors', 'publisher', 'date']
	out = out[out['authors'] != '_skip']
	out.sort_values(by='publisher', inplace=True)
	out.drop_duplicates('url', inplace=True, keep='last') #since sorted by publisher earlier, this should discard _sitename and keep other
	#print("debug: out.shape", out.shape)
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
	parser.add_argument("--exact", "-x", default=False, action='store_true', help="T/F search for your exact query (i.e. quotes around it in the search engine).")

	args = parser.parse_args()

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
	from html import unescape
	from formatAuthors import nameFormat, authorListFormat
	from naver_api import naver_main
	from custom_filters import urlFilter, articleTextCheck

	import monkeypatch
	#OriginalClass.class_method = classmethod(custom_class_method)
	Parser.getElementsByTag = monkeypatch.getElementsByTag_custom
	ContentExtractor.get_authors = monkeypatch.get_authors_custom
	ContentExtractor.is_latin = monkeypatch.is_latin

	main(query = args.query, startDate = args.start, endDate = args.end, outfile = args.output, exactQuery = args.exact)
