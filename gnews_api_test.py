import argparse
import time
from datetime import date, datetime

#TODO:
#also call naver API js to get more urls
#and make sure to remove duplicate urls; naver API urls will have like ?src=naver or similar at the end
#so account for that when checking similarlity.
#then do n3k for all urls
#and merge publisher information; choose whichever one is more reliable 
#for gnews it'll be whatever gnews got
#but naver doesn't give publisher info (booooooo)
#figure out if theres some way to get that
#otherwise use n3k meta og site_name
#The user will check the outputted xlsx for errors etc
#Then make a new script that'll take that excel and make a word doc
#Final step is to unspaghettify code
#and remember i modified the n3k library, specifically extractors.py I think

def naver(query:str, startDate:str):
	results = pd.DataFrame(naver_main(query, startDate)) #list of dicts -> pd
	#columns: title (bad, gets cut off), originallink, link (usually naver link), description (no need), pubDate
	#columns to have for merge: publisher, published date, title, url
	results.drop(['title', 'link', 'description'], axis=1, inplace=True)
	results['publisher'] = "_sitename_notgiven"
	results['title'] = "titleNotGiven"
	results.rename(columns = {"originallink": "url", "pubDate": "published date"}, inplace=True)
	#.....
	results['published date'] = results.apply(lambda x: datetime.strptime(x['published date'], "%a, %d %b %Y %H:%M:%S %z").replace(tzinfo=None), axis=1)
	return(results)


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
	p = subprocess.Popen([nodepath, 'get_authors.js', articleURL], stdout=subprocess.PIPE, executable=nodepath)
	out = p.stdout.read().decode('utf8').split('\t') #surely there won't be a \n in the authors or title...
	try:
		if(len(out) == 2):
			return([out[0], nameFormat(out[1]), "NA"])
		else:
			return([articleURL, "titleNotFound_py", "authorNotFound_py", ""])
	except Exception as e:
		print("Node article didn't work as expected.")
		print("Node output:", out)
		print("Error:", e)
		return([articleURL, "titleNotFound_py2", "authorNotFound_py2", "NA"])

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
			#print("Trying with Node.")
			#and then try with node extractor. lol.
			#return(node_cite_info(articleURL))
			#i give up...
			return([articleURL, "titleNotFound_n3kerror, authorNotFound_n3kerror", "sitenameNotFound_n3kerror"])
	try:
		authors = authorListFormat(myArticle.authors)
		#i want to also check if publisher is the author and ignore if so but idt it will work
		#print("ok1", end=" ")
		if(len(myArticle.authors) > 0 and (authors == 'unlikelyName' or authors.isspace() or authors == '')):
			authors = myArticle.authors[0]
		#print("ok2")
	except Exception as e:
		print("Author parse error:", e)
		print("url:", articleURL)
		authors = 'authorParseError'
	#n3k pubdate unreliable so just parse the gnews date instead...
	#get publisher from outside n3k too
	title = myArticle.title #bc gnews result can be concatenated and has - publisher at the end
	#temporaryily just including pre-processed .authors list too
	sitename = myArticle.meta_data['og'].get('site_name', '_sitename_notfound')
	canonurl = myArticle.canonical_link
	if(len(authors) == 0):
		authors = "authorNotFound"
	return([canonurl, title, authors, sitename])
	
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

def main(query:str, startDate:str, endDate:str, outfile:str):
	#query = 'Beyond Parallel'
	#startDate = '2022-12-01'
	#endDate = '2023-07-26'
	#set to today if no end date specified. I think Y-m-d is the correct format.
	sQuery = '"' + query + '"' + ' AND Korea before:' + endDate + " after:" + startDate
	sQuery_kr = '"' + query + '"' + 'before:' + endDate + " after:" + startDate
	print("Getting news...")
	start = time.time()
	google_news = GNews(exclude_websites = ['csis.org', 'youtube.com'], max_results = 1000)
	google_news_kr = GNews(exclude_websites = ['csis.org', 'youtube.com'], max_results = 1000, country = 'KR', language = 'ko')
	results = google_news.get_news(sQuery)
	results_kr = google_news_kr.get_news(sQuery_kr)
	end = time.time()
	print("Found", len(results)+len(results_kr), "results for", query, "in date range", startDate, "to", endDate)
	print("Took", end-start)

	df_en = pd.DataFrame(results)
	df_kr = pd.DataFrame(results_kr)
	df = pd.concat([df_en, df_kr], ignore_index=True)
	df = pd.concat([df.drop(['publisher'], axis=1), df['publisher'].apply(pd.Series).rename(columns = {"href": "site", "title": "publisher"})], axis=1)
	#df = pd.concat([df.drop(['publisher', 'title'], axis=1), df['publisher'].apply(pd.Series).rename(columns = {"href": "site"})], axis=1)
	print("Made data frame.")

	# df['title'] = df['title'].apply(lambda x: "".join(x.split(' - ')[0:-1]))
	# print("Adjusted titles.")
	#df['url'] = df['url'].apply(lambda x: requests.get(x).url)
	#^ request is pretty slow. thread here?

	with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
		#df['url'] = df['url'].apply(lambda url: requests.get(url).url)
		res = executor.map(lambda x: requests.get(x).url, df['url'])
	df['url'] = list(res) #i think order isnt preserved so uh...
	#print(df['url'])
	print("Got urls.")

	#append Naver urls and remove duplicates here
	#also note naver urls have html stuff like &quot
	#...either find a good way to match identical urls even with src=Naver or whatever equivalent (since this distinction differs across sites)
	#or maybe just match by same title+domain?

	df = df[['cbsnews.com/essentials' not in x for x in df['url']]]
	print("Filtered cbs.")
	#print("Getting text...")
	# df['text'] = df.apply(rowURLtoText, axis=1)
	# df2 = df[['victor cha' in x.lower() for x in df['text']]]
	#filtered_articles = [x for x in results if ("www.politico.com" not in x['publisher']['href'] or "victor cha" in parse_politico(requests.get(x['url']).url).lower())]
	start = time.time()
	df = df[df.apply(lambda x: ("www.politico.com" not in x['site'] or query.lower() in parse_politico(requests.get(x['url']).url).lower()), axis=1)]
	end = time.time()
	print("(Took", end-start, "to filter politico.)")
	# filtered_articles = [x for x in filtered_articles if ("koreajoongangdaily" not in x['publisher']['href'] or "victor cha" in newspaper3k_extract(requests.get(x['url']).url).lower())]
	start = time.time()
	df = df[df.apply(lambda x: ("koreajoongangdaily" not in x['site'] or query.lower() in newspaper3k_extract(requests.get(x['url']).url).lower()), axis=1)]
	end = time.time()
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
	df['published date'] = df.apply(lambda x: datetime.strptime(x['published date'], "%a, %d %b %Y %H:%M:%S %Z"), axis=1)

	tmp = df.shape[0]
	df = pd.concat([df, naver(query, startDate)], ignore_index = True)
	tmp = df.shape[0]-tmp
	print("Found", tmp, "results on Naver.")

	pool = ThreadPool(10)
	print("trying n3k...")
	results = pool.map(n3k_cite_info, df['url'].tolist())
	#df[['title', 'author', 'publish_date']] = df['url'].apply(n3k_cite_info).apply(pd.Series)
	#extremely lazy I give up df updating
	d = pd.DataFrame(results)

	pool.close()

	df = df.merge(d, left_on = "url", right_on = 0)
	df = df.drop(['title', 'site'], axis=1)
	df.columns = ['date', 'url', 'publisher1', 'url2', 'title', 'author', 'publisher2']
	#idr what url was lol
	df.drop(['url2'], axis=1, inplace=True,)


	def helper(pub1, pub2):
		ret = "_sitename_notfound"
		if(pub1 == "_sitename_notgiven"):
			ret = pub2
		else:
			ret = pub1
		if("," in ret):
			ret = ret.split(",")[0]
		return ret

		#if publisher2 is notfound then itcantbehelped.jpg
	df['publisher'] = df.apply(lambda x: helper(x['publisher1'], x['publisher2']), axis=1)
	df.drop(['publisher1', 'publisher2'], axis=1, inplace=True)

	df.sort_values(by='publisher', inplace=True)

	df.drop_duplicates('url', inplace=True, keep='last') #since sorted by publisher earlier, this should discard _sitename and keep other

	#print(df['date'])
	
	df.sort_values(by='date', inplace=True)
	df['date'] = df.apply(lambda x: datetime.strftime(x['date'], "%Y-%m-%d"), axis=1)

	df.to_excel(outfile, index=False)
	print("Done. Wrote to", outfile)

	#TODO:
	#see test.xlsx and look through which articles keep bricking things for everyone else
	#e.g. politico, foreign affairs, NK News...
	#and also adjust search terms (e.g. that one real estate article/hong kong arts festival)

if __name__ == "__main__":
	today = date.today().strftime("%Y-%m-%d")
	parser = argparse.ArgumentParser(description = "Retrieve Google and Naver news results given a search query and time frame.")
	parser.add_argument("--query", "-q", type=str, required=True, help="Search query. If there are spaces, put the whole query in double quotes.")
	parser.add_argument("--start", "-s", type=str, required=True, help="Start date, formatted as YYYY-MM-DD.")
	parser.add_argument("--end", "-e", type=str, required=False, help="End date, formatted as YYYY-MM-DD. If not used, defaults to today.",
		nargs = "?", default = today, const=today)
	parser.add_argument("--output", "-o", type=str, required=True, help="Filename of output file.")

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

# I think one future todo (along with removing node dependency) is replace inplace=True on pandas methods with df = df.method()