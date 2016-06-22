#!/usr/bin/env python3.5
import requests
import re
from urllib.parse import urlsplit
import traceback
import sys

class DEBUG(object):
	VERBOSE=3
	DEBUG=2
	INFO=1
	QUIET=-1


class UrlParser(object):
	URL_RE = re.compile(r'<a href="([^"]*)"', re.I)
	PROT_RE = re.compile(r'^https?://')
	# add this too?
	# r'https?://[^"]*\.[^"]*'

	@staticmethod
	def _fetch_html(url):
		# TODO: add force untrusted ssl support
		# r = requests.head(url, allow_redirects=True, verify=False)
		r = requests.head(url, allow_redirects=True)
		r.raise_for_status()
		if r.headers['Content-Type'].startswith('text/'):
			r = requests.get(url, allow_redirects=True)
			return r.text
		return ''

	@staticmethod
	def _get_base_url(url):
		return "{0.scheme}://{0.netloc}".format(urlsplit(url))

	@staticmethod
	def _get_domain(url):
		return '.'.join(urlsplit(url).netloc.split('.')[-2:])

	@classmethod
	def parse(cls, top_url, url_map=[], same_domain=True):
		if not cls.PROT_RE.search(top_url):
			top_url = 'http://' + top_url
		base_url = cls._get_base_url(top_url)
		base_domain = cls._get_domain(base_url)
		html = cls._fetch_html(top_url)
		for match in cls.URL_RE.finditer(html):
			url = match.group(1).strip()
			pos = url.find('#')
			if pos > -1:
				url = url[:pos]
			if len(url) == 0:
				continue
			if not cls.PROT_RE.search(url):
				if url[0] != '/':
					url = '/' + url
				url = base_url + url
			if (url not in url_map and
				(not same_domain or base_domain == cls._get_domain(url))):
				
				url_map.append(url)
		return url_map

class FSpider(object):

	def __init__(self, urls):
		super()
		self.urls = urls
		self.verbose = DEBUG.INFO

	def verbosity(self, val=None):
		if type(val) == int:
			self.verbose = val
		return self.verbose

	def same_domain(self, val=None):
		if type(val) == bool:
			self.same_domain = val
		return self.same_domain

	def spidey(self):
		for url in self.urls:
			if not UrlParser.PROT_RE.search(url):
				url = 'http://' + url

			try:
				r = requests.head(url, allow_redirects=True)
				r.raise_for_status()
				url = r.url
			except HTTPError:
				print('Can\'t reach skipping:', url)
				continue

			url = url.strip('/')

			print('Spidering: ', url)
			visited = [] # visited map
			url_map = [url]
			to_visit = [url]
			while len(to_visit) > 0:
				try:
					url = to_visit.pop()
					print('Trying:', url, '\tstatus:', end='')
					url_map = UrlParser.parse(url, url_map, self.same_domain)
					visited.append(url)
					for u in url_map:
						if u not in visited:
							to_visit.append(u)
					if self.verbose >= DEBUG.VERBOSE:
						print('url_map:', url_map)
						print('visited:', visited)
						print('to_visit:', to_visit)
					print('SUCCESS')
				except requests.HTTPError:
					if url not in visited:
						visited.append(url)
					print('FAIL')
				except requests.ConnectionError:
					print('CONNECTION_FAIL!\a')
					if self.verbose >= DEBUG.VERBOSE:
						print ('-'*30)
						traceback.print_exc(file=sys.stdout)
						print ('-'*30)

def main():
	import argparse
	parser = argparse.ArgumentParser(description='Spider URLs in given order.\n' +
		'by Fma')
	# urls
	parser.add_argument('urls', metavar='URL', type=str, nargs='+',
						help='Path to spider')
	# verbosity level
	parser.add_argument('--verbose', metavar='INT', type=int,
		help='Verbosity level', default=0)
	parser.add_argument('--no-same-domain', help='spider different domains',
		action='store_false', default=True)

	args = parser.parse_args()
	spider = FSpider(args.urls)
	spider.same_domain(args.no_same_domain)
	spider.verbosity(args.verbose)
	try:
		spider.spidey()
	except KeyboardInterrupt:
		print('\n\nUser interrupted canceling and quiting\n\a')

if __name__ == "__main__":
   main()
