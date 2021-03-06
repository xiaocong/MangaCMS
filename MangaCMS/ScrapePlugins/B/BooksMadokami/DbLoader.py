
import WebRequest
import html.parser
import urllib.parse
import urllib.error
import time
import settings
import re
import os.path
import datetime
import MangaCMS.ScrapePlugins.LoaderBase
import MangaCMS.ScrapePlugins.RunBase
import nameTools as nt
from concurrent.futures import ThreadPoolExecutor

MASK_PATHS = [


	'/mango/Admin%20cleanup',
	'/mango/Admin cleanup',
	'/mango/Info',
	'/mango/Manga',
	'/mango/Misc',
	'/mango/Raws',
	'/mango/Requests',
	'/mango/READ.txt',

	'/Admin%20cleanup',
	'/Admin cleanup',
	'/Info',
	'/Manga',
	'/Misc',
	'/Raws',
	'/Requests',
	'/READ.txt',

]

HTTPS_CREDS = [
	("manga.madokami.al",         settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("http://manga.madokami.al",  settings.mkSettings["login"], settings.mkSettings["passWd"]),
	("https://manga.madokami.al", settings.mkSettings["login"], settings.mkSettings["passWd"]),
	]

class DbLoader(MangaCMS.ScrapePlugins.LoaderBase.LoaderBase):

	logger_path = "Main.Books.Mk.Fl"
	plugin_name = "Books.Madokami Link Retreiver"

	plugin_key = "bmk"
	is_manga    = False
	is_hentai   = False
	is_book     = True

	dbName = settings.DATABASE_DB_NAME

	tableName = "BookItems"
	url_base     = "https://manga.madokami.al/"
	tree_api     = "https://manga.madokami.al/stupidapi/lessdumbtree"

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.wg = WebRequest.WebGetRobust(creds=HTTPS_CREDS)

	def checkLogin(self):
		pass


	def process_tree_elements(self, elements, cum_path="/"):
		ret = []

		for element in elements:

			if element['type'] == "report":
				continue
			elif element['type'] == 'directory':
				name = element['name']
				name = urllib.parse.quote(name)
				item_path = os.path.join(cum_path, name)
				ret.extend(self.process_tree_elements(element['contents'], item_path))
			elif element['type'] == 'file':


				name = element['name']
				name = urllib.parse.quote(name)
				item_path = os.path.join(cum_path, name)


				if any([item_path.startswith(prefix) for prefix in MASK_PATHS]):
					continue

				if item_path.startswith("/Novels/"):
					# Parse out the series name if we're in a directory we understand,
					# otherwise just assume the dir name is the series.
					match = re.search(r'/Novels/[^/]/[^/]{2}/[^/]{4}/([^/]+)/', item_path)
					if match:
						sname = match.group(1)
					else:
						sname = os.path.split(cum_path)[-1]



					item = {
						'source_id'   : urllib.parse.urljoin(self.url_base, item_path),
						'origin_name' : element['name'],
						'series_name' : nt.getCanonicalMangaUpdatesName(sname),
						'posted_at'   : datetime.datetime.now()
					}


					if 'uchiage' in item_path.lower():
						print("Item: ", item_path, element)
						print()
						print(item)
						print()

					ret.append(item)
			else:
				self.log.error("Unknown element type: '%s'", element)

		return ret

	def get_feed(self):
		treedata = self.wg.getJson(self.tree_api)
		assert 'contents' in treedata
		assert treedata['name'] == 'mango'
		assert treedata['type'] == 'directory'
		data_unfiltered = self.process_tree_elements(treedata['contents'])
		return data_unfiltered
		# return []



	def setup(self):
		# Muck about in the webget internal settings
		self.wg.errorOutCount = 4
		self.wg.retryDelay    = 5

		self.log.info( "Loading Madokami Main Feed")




class Runner(MangaCMS.ScrapePlugins.RunBase.ScraperBase):
	loggerPath = "Main.Manga.MkL.Run"

	pluginName = "MkFLoader"


	def _go(self):

		self.log.info("Checking Mk feeds for updates")
		fl = FeedLoader()
		fl.go()

if __name__ == "__main__":
	import utilities.testBase as tb

	with tb.testSetup(load=False):

		run = DbLoader()
		# run.go()
		run.do_fetch_feeds()

