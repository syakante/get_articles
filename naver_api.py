import requests
import json
import datetime

headers = json.load(open('naver_headers.json'))

options = {
	"method": "GET",
	"Content-Type": "text/json;charset=utf-8"
	}

def myDate(datestr):
	return(datetime.datetime.strptime(datestr, "%a, %d %b %Y %H:%M:%S %z"))

def naver_main(myQuery:str, startDate:str):
	articles = []
	page = 1
	startDate = startDate + "T00:00:00-05:00"
	startDate_dt = datetime.datetime.fromisoformat(startDate)
	fetchDate = datetime.datetime.now(tz=datetime.timezone.utc)
	#cases:
	#1) over all of time, there's <100 results for this query
	#2) there's >=100 results, and the 100th result is too recent, so we need to search more to reach startDate
	#3) there's >=100 results, and the 100th result is too old, so we need to cut down within the 100 results to reach startDate
	while fetchDate >= startDate_dt:
		#the logic is kinda ... but basically this loop will run at least once
		saveResponse = requests.get(f"https://openapi.naver.com/v1/search/news.json?query={myQuery}&display=100&start={page}&sort=date", params = options, headers = headers)
		jsonResponse = saveResponse.json()
		#check if response is error
		if('errorResponse' in jsonResponse.keys()):
			#TODO: more thorough error handling ._.
			print("error")
			return([])
		articles.extend(jsonResponse['items'])

		fetchDate = myDate(articles[-1]['pubDate'])
		if len(jsonResponse['items']) < 100:
			#i.e. no more results
			break
		page += 100
	#so by now fetchDate = articles[-1] will have happened at least once
	if fetchDate < startDate_dt:
		print("Last item's date exceeds threshold (too old, need to cut down)")
		left = 0
		right = len(articles) - 1
		result = -1
		while left <= right:
			mid = (left + right) // 2
			if myDate(articles[mid]['pubDate']) >= startDate_dt:
				result = mid
				left = mid + 1
			else:
				right = mid - 1
	print("Naver done.")
	return(articles[:result + 1])
	# with open("naver_out.json", "w") as outfile:
	# 	json.dump(articles[:result + 1], outfile)
	# 	print("ok")