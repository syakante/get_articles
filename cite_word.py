import pandas as pd
from datetime import datetime
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

infile = "example media covg.xlsx"
outfile = "example output.docx"

raw = pd.read_excel(infile)
raw = raw.fillna('')
#assume at this point the excel is correct
#and has at least the columns "date" in yyyy-mm-dd, "url", "title", "author", no weird html text anywhere, etc
#sorting groups:
#group by publisher, and within publisher, sort by date. If same date then technically by author last name but idrc

#bullet bold: publisher
#indent bullet: author name. "Title." <i>publisher</i>, date, url.
#*for date, format %d %b %Y, add . after month if abbreviated (i.e. not May, June, or July)

from docx import Document
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT

def format_date(date):
	#in: yyyy-mm-dd
	#out: dd mon., yyyy
	# _, m, _ = date.split("-")
	# month = int(m)
	#mydate = datetime.strptime(date, "%Y-%m-%d")
	mydate = date.to_pydatetime()
	if 5 <= mydate.month and mydate.month <= 7:
		ret = datetime.strftime(mydate, "%d %b %Y")
	else:
		ret = datetime.strftime(mydate, "%d %b. %Y")
	return(ret)

def add_citation(doc, author, title, publisher, date, url, level=2):
	if(level == 1):
		mystyle = 'ListNumber'
	else:
		mystyle = 'ListNumber'+str(level)
	out = doc.add_paragraph()
	out.style = mystyle
	run = out.add_run()
	if(len(author) > 0):
		run.add_text(author+'. "'+title+'."')
	else:
		run.add_text('"'+title+'."')
	
	publisher_run = out.add_run(publisher)
	publisher_run.italic = True
	publisher_run.add_text(', ')

	run2 = out.add_run(format_date(date))
	run2.add_text(', '+url)

	
doc = Document()

title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title_run = title.add_run()
title_font = title_run.font
title_font.size = Pt(14)
title_run.bold = True
title_run.add_text("Media Coverage Example")

blank = doc.add_paragraph()
blank.alignment = WD_ALIGN_PARAGRAPH.LEFT

publishers = sorted(set(raw['publisher']))

#idk sort later test for now
for p in publishers:
	subset = raw[raw['publisher'] == p]
	pub_header = doc.add_paragraph()
	pub_header.style = "List Bullet"
	pub_run = pub_header.add_run(p)
	pub_run.add_text(' ('+str(subset.shape[0])+')')
	pub_run.bold = True
	#le for loop
	for i in range(subset.shape[0]):
		add_citation(doc, *subset.iloc[i, [subset.columns.get_loc(col) for col in ['author', 'title', 'publisher', 'date', 'url']]])


doc.save(outfile)
print("ok...")