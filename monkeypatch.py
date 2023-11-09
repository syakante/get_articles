#parsers.py
#@classmethod for class Parser(object)
def getElementsByTag_custom(cls, node, tag=None, attr=None, value=None, childs=False, use_regex=False) -> list:
	NS = None
	# selector = tag or '*'
	selector = 'descendant-or-self::%s' % (tag or '*')
	if attr and value:
		if use_regex:
			NS = {"re": "http://exslt.org/regular-expressions"}
			#selector = '%s[re:test(@%s, "%s", "i")]' % (selector, attr, value)
			selector = '%s[contains(@%s, "%s")]' % (selector, attr, value)
		else:
			trans = 'translate(@%s, "%s", "%s")' % (attr, string.ascii_uppercase, string.ascii_lowercase)
			selector = '%s[contains(%s, "%s")]' % (selector, trans, value.lower())
	elems = node.xpath(selector, namespaces=NS)
	# remove the root node
	# if we have a selection tag
	if node in elems and (tag or childs):
		elems.remove(node)
	return elems

#extractors.py
#methods for class ContentExtractor(object):
from string import printable
def is_latin(text):
	return not bool(set(text) - set(printable))
#method get_authors
def get_authors(self, doc):
	"""Fetch the authors of the article, return as a list
	Only works for english articles
	"""
	_digits = re.compile('\d')

	def contains_digits(d):
		return bool(_digits.search(d))

	def uniqify_list(lst):
		"""Remove duplicates from provided list but maintain original order.
		  Derived from http://www.peterbe.com/plog/uniqifiers-benchmark
		"""
		seen = {}
		result = []
		for item in lst:
			if item.lower() in seen:
				continue
			seen[item.lower()] = 1
			result.append(item.title())
		return result

	def is_latin(text):
		return not bool(set(text) - set(printable))

	def parse_byline(search_str):
		"""
		Takes a candidate line of html or text and
		extracts out the name(s) in list form:
		>>> parse_byline('<div>By: <strong>Lucas Ou-Yang</strong>,<strong>Alex Smith</strong></div>')
		['Lucas Ou-Yang', 'Alex Smith']
		"""
		# Remove HTML boilerplate
		search_str = re.sub('<[^<]+?>', '', search_str)

		# Remove original By statement
		search_str = re.sub('[bB][yY][\:\s]|[fF]rom[\:\s]|[기자]', '', search_str)

		search_str = search_str.strip()

		#print("like url:", bool(re.match(r"^(https?://)?(www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", search_str)))
		if(bool(re.match(r"^(https?://)?(www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", search_str))):
			return []
		# Chunk the line by non alphanumeric tokens (few name exceptions)
		# >>> re.split("[^\w\'\-\.]", "Tyler G. Jones, Lucas Ou, Dean O'Brian and Ronald")
		# ['Tyler', 'G.', 'Jones', '', 'Lucas', 'Ou', '', 'Dean', "O'Brian", 'and', 'Ronald']
		name_tokens = re.split("[^\w\'\-\.]", search_str)
		name_tokens = [s.strip() for s in name_tokens]

		_authors = []
		# List of first, last name tokens
		curname = []
		delimiters = ['and', ',', '']

		if (all([is_latin(text) for text in name_tokens])):
			for token in name_tokens:
				#print("current token:", token)
				if token in delimiters:
					if len(curname) > 0:
						_authors.append(' '.join(curname))
						curname = []

				elif not contains_digits(token):
					curname.append(token)

			# One last check at end                
			valid_name = (len(curname) >= 2) and (len(curname) <= 5)
			#print("valid_name:", valid_name)
			if valid_name:
				#print("here")
				_authors.append(' '.join(curname))
			#print("_authors:", _authors)
			return _authors
		else:
			name_tokens = re.split("[^\w\'\-\.]", search_str)
			name_tokens = [s.strip() for s in name_tokens]
			return(name_tokens[0]) #tmp solution tbh

	# Try 1: Search popular author tags for authors

	ATTRS = ['name', 'rel', 'itemprop', 'class', 'id', 'property', 'span', 'i']
	VALS = ['author', 'name', 'tit-name', 'writer', '_byline', 'icon-user-o']
	#^currently does every combo, but may want to hard-code certain combos e.g. i+icon-user-o
	#add class="byLine"
	#often just ends up being the site name
	matches = []
	authors = []

	for attr in ATTRS:
		for val in VALS:
			# found = doc.xpath('//*[@%s="%s"]' % (attr, val))
			if (attr == 'i') and (val != 'icon-user-o'):
				continue
			found = self.parser.getElementsByTag(doc, attr=attr, value=val)
			matches.extend(found)

	for match in matches:
		content = ''
		if match.tag == 'meta':
			mm = match.xpath('@content')
			if len(mm) > 0:
				content = mm[0]
				#print(content)
		else:
			content = match.text or ''
		# print("content:", content)
		# print("authors:", authors)
		# print("parse_byline(content):",parse_byline(content))
		if len(content) > 0:
			if(all([is_latin(text) for text in content])):
				authors.extend(parse_byline(content))
			else: #why nonlatin names become separated by character...
				authors.extend([''.join(parse_byline(content))])
	return(uniqify_list(authors))
