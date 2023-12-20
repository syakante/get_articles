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

def naver_main(myQuery:str, startDate:str, endDate:str):
	articles = []
	page = 1
	startDate = startDate + "T00:00:00-05:00" #DC time (hacked together)
	endDate = endDate + "T00:00:00-05:00"
	startDate_dt = datetime.datetime.fromisoformat(startDate)
	endDate_dt = datetime.datetime.fromisoformat(endDate)
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
			print("Finished pagination.")
			#i.e. no more results
			break
		page += 100
		print("On page", page//100, "of results.")
		if page > 1000: #api's maximum...
			break
	#so by now fetchDate = articles[-1] will have happened at least once
	
	def search(L, cmp_date):
		left = 0
		right = len(L) - 1
		result = -1
		while left <= right:
			mid = (left + right) // 2
			if myDate(L[mid]['pubDate']) >= cmp_date:
				result = mid
				left = mid + 1
			else:
				right = mid - 1
		return(result)

	start_id = -2
	if fetchDate < startDate_dt:
		#print("Last item's date exceeds threshold (too old, need to cut down)")
		start_id = search(articles, startDate_dt)
	ret = articles[:start_id+1]
	latestDate = myDate(ret[0]['pubDate'])
	end_id = 0
	if endDate_dt < latestDate:
		#print("here")
		end_id = search(ret, endDate_dt)
	ret = ret[end_id:]
	print("Found", len(ret), "results from Naver.")
	return(ret)
	# with open("naver_out.json", "w") as outfile:
	# 	json.dump(articles[:result + 1], outfile)
	# 	print("ok")