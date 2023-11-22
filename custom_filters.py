#Some websites have the keyword text somewhere in the webpage
#but the article isn't actually about the keyword
#e.g. "read more" section
#so storing websites where this happens + where on that website the article/not-article split happens
#examples of articles with word in webpage but not in article:
#"https://www.politico.com/newsletters/national-security-daily/2023/09/20/ramaswamys-master-plan-to-combat-china-00117031"
#"https://www.politico.com/newsletters/national-security-daily/2022/01/26/the-nscs-weekly-ukraine-crisis-club-00002477"
#--> drop everything after class="story-related"

#"https://www.washingtonexaminer.com/policy/defense-national-security/how-the-so-called-hastert-rule-could-torpedo-ukraines-war-effort"
#idk what to do with this one..

#"https://www.bushcenter.org/newsroom/bush-institute-statement-on-terrorist-attacks-in-israel"
#--> case where word was in gnews index but not in actual article text, and n3k's article text doesn't have it

#website: where the article ends and the irrelevant stuff begins
#need to figure out how to store this e.g. class and id? or just the class/id's value?
SITE_SPLIT = { 'www.politico.com': 'class="story-related"'}

def urlFilter(articleURL:str):
	#t/f if should download n3k article_html to 2x check if article is actually relevant
	#update as necessary...
	if('korea' not in articleUrl or '.kr/' not in articleUrl):
		return True
	return False

def articleTextCheck(A, query:str) -> bool:
	#article is the Article object from n3k library
	#query... need it to be some kind of global var
	#return T/F true if it needs to be dropped

	#the article that gets passed through this function will have been selected
	#by urlFilter anyway so it's guaranteed to have the article_html attribute
	#all articles should have the text attribute (unless something went wrong, but the n3k error try/except
	#should have already happened by the time this func gets called. Still, have some check for if .text = '')

	#The purpose of this is to do the article text check while we still have the Article object
	#so we only have to download it once. The download happens during the n3k_cite_info function
	#which outputs the cite info (url, title, authors, sitename)
	#so this outputs a bool and add some process where if(articleTextCheck)
	#then make title/authors/sitename = some dummy value
	#and later check the pandas df for that dummy value and remove those rows

	#first check if n3k article text has the text at all
	#and the only reason we got the result is bc the webpage but not the article has the search word
	#e.g. the george bush one

	if(query not in A.text):
		return True

	#next check if it's in our website (black?)list and split the article_html
	#there should hopefully... be some way to split the html i.e. the closing tags like </div> will be lost
	#but we can still clean up the html to just get text stuff...

	return False