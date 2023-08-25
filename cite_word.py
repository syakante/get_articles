import pandas as pd
from html import unescape
from datetime import datetime

raw = pd.read_json("out.json")
raw = raw.drop(['link', 'description'], axis=1)
raw['title'] = [unescape(t) for t in raw['title']]
raw['pubDate'] = [datetime.strptime(d, "%a, %d %b %Y %H:%M:%S %z").date() for d in raw['pubDate']]
#i give up
raw.to_excel("naver_links.xlsx")