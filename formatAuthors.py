#ughhhhh need to revamp this!!!!

import spacy
from string import printable
nlp = spacy.load('en_core_web_sm')

with open('korean-surnames.txt', 'r') as f:
	krSurnames = f.read().splitlines()

def is_latin(text):
	return not bool(set(text) - set(printable))

def likelyName(nameL):
	doc = nlp(" ".join(nameL))
	newsWords = {'News', 'Daily', '뉴스', 'Radio'}
	nameSet = set(nameL)
	NLPcheck = any('PERSON' == e.label_ for e in doc.ents) 
	surnameCheck = any(x in krSurnames for x in nameL)
	noNewsWordsCheck = (len(newsWords.intersection(nameSet)) == 0)
	return (NLPcheck or surnameCheck and noNewsWordsCheck)

def nameFormat(s:str) -> str:
	#for names written in english
	#this doesn't catch korean names that are formatted as Last First and the first name syllables aren't delimited
	#intends to turn "John Doe" into "Doe, John"
	#nameL = [titlecase(x) for x in s.split(" ")]\
	if is_latin(s):
		nameL = [x.title() for x in s.split(" ")] #so John Doe --> ["John", "Doe"]
		if("For" in nameL):
			i = nameL.index("For")
			nameL = nameL[:i]
		if len(nameL) > 3 or len(nameL) < 2 or not likelyName(nameL):
			#...should clean above so less spaghetti
			#something like a likelyName bool function
			return('unlikelyName')
			# "author" can be like "World Nation News Desk"
			# or a definite wrong scraping like "asdf International. To"
		if(len(nameL) > 2 and nameL[0] in krSurnames):
			ret = nameL[0]+", "+" ".join(nameL[1:])
			return(ret)
		first = " ".join(nameL[:-1])
		last = nameL[-1]
		if(first in krSurnames and "-" in last):
			ret = first+" "+last
			return(ret)
		ret = last+", "+first
		return(ret)
	else: #non-latin
		if len(s) > 3 or len(s) < 2:
			return('unlikelyName')
		return s

def authorListFormat(L) -> str:
	if not L or len(L) == 0:
		return('')
	try:
		authors = [nameFormat(x) for x in L]
	except Exception as e:
		print("nameFormat error:", e)
		return('')
	if(authors[0] == ''):
		return('')
	authors = [x for x in authors if x != ''] #eh....
	if(len(authors) > 1): #what? why? (used to be 2)
		if(any([x == "unlikelyName" for x in authors])):
			if(authors[0] == "unlikelyName" and all([x != "unlikelyName" for x in authors[1:]])):
				authors = authors[1:]
			elif(authors[0] != "unlikelyName" and all([x == "unlikelyName" for x in authors[1:]])):
				authors = [authors[0]]
			elif(authors[0] == "unlikelyName" and not all([x != "unlikelyName" for x in authors[1:]])):
				authors = [L[0]]
			else:
				#can use index bc upper if is any([x == unlikelyname])
				authors = authors[:authors.index("unlikelyName")]
	if(len(authors) == 1):
		if(authors[0] == "unlikelyName" and is_latin(L[0])):
			return(L[0]) #..?
		if(authors[0] == "unlikelyName" and not is_latin(L[0])):
			return("")
		else:
			return(authors[0])
	authors = [x+"," for x in authors[:-1]] + [authors[-1]]
	#TODO
	#also need to sth sth with "and" before final, but ignore comma if only 2
	#I think by citation standards say et al after 20 authors but uh... hopefully should never come to that...
	return(" ".join(authors))

# if __name__ == "__main__":
# 	a = ["Anthony Kuhn Erika Ramirez Gabe O'Connor William Troop Mary Louise Kelly", 'Anthony Kuhn', 'Erika Ramirez', "Gabe O'Connor", 'Mary Louise Kelly', 'William Troop']
# 	b = ['Victor Cha', 'Victor Cha Is Vice Dean', 'D. S. Song Korea Foundation Professor Of Government At Georgetown University', 'Senior Vice President For Asia At The Center For Strategic', 'International Studies. To', 'He Was Director For Asian Affairs At The National Security Council.', 'Michael Kimmage', 'Maria Lipman', 'Margaret Macmillan', 'Ye Myo Hein']
# 	c = ['World Nation News Desk', 'Https', 'Worldnationnews.Com', 'World Nation News Is A Digital News Portal Website. Which Provides Important', 'Latest Breaking News Updates To Our Audience In An Effective', 'Efficient Ways', 'Like World S Top Stories', 'Entertainment', 'Sports', 'Technology']
# 	d = ['Soo-Hyang Choi']
# 	e = ['Afjsdf Akjghdf']

# 	print(authorListFormat(a))
# 	print(authorListFormat(b))
# 	print(authorListFormat(c))
# 	print(authorListFormat(d))
# 	print(authorListFormat(e))