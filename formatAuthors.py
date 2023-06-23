import spacy
nlp = spacy.load('en_core_web_sm')

with open('korean-surnames.txt', 'r') as f:
	krSurnames = f.read().splitlines()

def nameFormat(s:str) -> str:
	#for names written in english
	#this doesn't catch korean names that are formatted as Last First and the first name syllables aren't delimited
	#nameL = [titlecase(x) for x in s.split(" ")]\
	doc = nlp(s)
	nameL = [x.title() for x in s.split(" ")]
	if len(nameL) > 3 or len(nameL) < 2 and not (any('PERSON' == e.label_ for e in doc.ents) or any(x in krSurnames for x in nameL)):
		return('unlikelyName')
		# "author" can be like "World Nation News Desk"
		# or a definite wrong scraping like "asdf International. To"
	if(len(nameL) > 2 and nameL[0] in krSurnames):
		ret = nameL[0]+", "+" ".join(nameL[1:])
		return(ret)
	first = " ".join(nameL[:-1])
	last = nameL[-1]
	if(first in krSurnames and "-" in last):
		ret = first+", "+last
		return(ret)
	ret = last+", "+first
	return(ret)

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
	if(len(authors) > 2):
		if(any([x == "unlikelyName" for x in authors])):
			if(authors[0] == "unlikelyName" and all([x != "unlikelyName" for x in authors[1:]])):
				authors = authors[1:]
			elif(authors[0] != "unlikelyName" and all([x == "unlikelyName" for x in authors[1:]])):
				authors = [authors[0]]
			elif(authors[0] == "unlikelyName" and not all([x != "unlikelyName" for x in authors[1:]])):
				authors = [L[0]]
			else:
				#authors[0] != "unlikelyName" and not all([x == "unlikelyName" for x in authors[1:]]:
				#...idk
				authors = [authors[0]]
	if(len(authors) == 1):
		#len(authors) < 2 i.e. len of 1
		if(authors[0] == "unlikelyName"):
			return(L[0])
		else:
			return(authors[0])
	authors[-1] = "and "+authors[-1]
	authors = [x+"," for x in authors[:-1]] + [authors[-1]]
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