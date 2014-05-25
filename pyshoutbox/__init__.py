#!/usr/bin/python3.4

__title__ = "pyshoutbox"
__version__ = "1.0.0"

import requests
from . import shoutparser
from urllib.parse import urlparse, urlunparse

class shoutbox():
	def __init__(self, url=""):
		# Shoutbox data
		self.shoutbox_url = urlparse(url)._asdict()
		self.shoutbox_name = None
		self.shoutbox_title = None
		self.shoutbox_session_id = None
		self.shoutbox_params = {
			"shtoken": None,
			"bid": None,
			"aaabbb": None
		}
		self.shoutbox_char_limit = 200
		self.shoutbox_website_field = True
		self.shoutbox_shouts = []
		
		# User data
		self.user_position = "Guest"
		self.user_name = None
		self.user_website = ""
		
		# Requests
		self.request_session = requests.Session()
		self.request_session.headers["User-Agent"] = "Mozilla/5.0"
		self.request_responce = None
	
	def connect(self, get_url=""):
		if (url_is_valid(get_url)):
			get_url = urlparse(get_url)._asdict()
			self.shoutbox_url = get_url
		elif (url_is_valid(self.shoutbox_url)):
			get_url = self.shoutbox_url
		else:
			return 1
		
		self.shoutbox_name = get_url["netloc"].partition(".")[0]
		
		try:
			self.request_responce = self.request_session.request(
				method = "GET",
				url = url_to_string(get_url)
			)
		except requests.exceptions.ConnectionError as err:
			return 1
		
		if not (self.request_responce.status_code == 200):
			return 1
		
		shoutbox_html = patch_shoutbox(self.request_responce.text)
		shoutparser.box_parser.feed(shoutbox_html)
		
		if (self.shoutbox_title == None):
			self.shoutbox_title = shoutparser.box_parser.title
		self.shoutbox_session_id = shoutparser.box_parser.params["sid"]
		self.shoutbox_params = dict(shoutparser.box_parser.params)
		self.shoutbox_char_limit = shoutparser.box_parser.char_limit
		
		return 0
	
	def get_shout(self, idn):
		if (self.shoutbox_session_id == None):
			return 1
		
		post_url = self.shoutbox_url
		post_url["path"] = "/s/displayidn.php"
		post_url["query"] = "bid=" + self.shoutbox_params["bid"]
		
		post_data = {"idn": str(idn)}
		
		try:
			self.request_responce = self.request_session.request(
				method = "POST",
				url = url_to_string(post_url),
				data = post_data
			)
		except requests.exceptions.ConnectionError as err:
			return 1
		
		if not (self.request_responce.status_code == 200):
			return 1
		
		if (self.request_responce.text == "Possible hacking attempt."):
			return 1
		
		shoutparser.shout_parser.feed(self.request_responce.text)
		
		return dict(shoutparser.shout_parser.shout)
	
	def refresh_shoutloader(self):
		if (self.shoutbox_session_id == None):
			return 1
		
		get_url = self.shoutbox_url
		get_url["path"] = "/s/shoutloader.php"
		get_url["query"] = (
			"bid=" + self.shoutbox_params["bid"] +
			"&u=" + get_url["netloc"].partition(".")[0] +
			"&sup=1" +
			"&token=" + self.shoutbox_params["shtoken"] +
			"&sid=" + self.shoutbox_session_id
		)
		
		try:
			self.request_responce = self.request_session.request(
				method = "GET",
				url = url_to_string(get_url)
			)
		except requests.exceptions.ConnectionError as err:
			return 1
		
		if not (self.request_responce.status_code == 200):
			return 1
		
		if (self.request_responce.text == "1"):
			return 2
		
		shoutparser.shout_parser.feed(self.request_responce.text)
		self.shouts = list(shoutparser.shout_parser.shouts)
		self.shouts.append(shoutparser.shout_parser.shout)
		
		return 0
	
	def post_shout(self, mesg):
		if (self.shoutbox_session_id == None):
			return 1
		if (self.user_name == None):
			return 1
		if (len(mesg) > self.shoutbox_char_limit):
			return 1
		
		post_url = self.shoutbox_url
		post_url["path"] = "/s/process.php"
		
		post_data = {
			"name": self.user_name,
			"message": mesg,
			"shtoken": self.shoutbox_params["shtoken"],
			"bid": self.shoutbox_params["bid"],
			"aaabbb": self.shoutbox_params["aaabbb"],
			"submit": "Shout"
		}
		if (self.shoutbox_website_field):
			post_data["website"] = self.user_website
		
		try:
			self.request_responce = self.request_session.request(
				method = "POST",
				url = url_to_string(post_url),
				data = post_data
			)
		except requests.exceptions.ConnectionError as err:
			return 1
		
		if not (self.request_responce.status_code == 200):
			return 1
		
		if (self.request_responce.text == "1"):
			return 0
	
	def delete_shout(self, shoutid):
		if (self.shoutbox_session_id == None):
			return 1
		
		post_url = self.shoutbox_url
		post_url["path"] = "/s/udelshout.php"
		post_url["query"] = "bid=" + self.shoutbox_params["bid"]
		
		post_data = {"shoutid": str(shoutid)}
		
		try:
			self.request_responce = self.request_session.request(
				method = "GET",
				url = url_to_string(post_url),
				data = post_data
			)
		except requests.exceptions.ConnectionError as err:
			return 1
		
		if not (self.request_responce.status_code == 200):
			return 1
		
		return 0
	
	def user_set_guest(self, name, website=""):
		if not (self.user_position == "Guest"):
			self.user_logout()
		
		self.user_name = name
		self.user_position = "Guest"
	
	def user_login(self, username, password, persistent=True):
		if (self.shoutbox_session_id == None):
			return 1
		
		if not (self.user_position == "Guest"):
			self.user_logout()
		
		persistent = int(persistent)
		
		post_url = self.shoutbox_url
		post_url["path"] = "/l"
		post_url["query"] = "bid=" + self.shoutbox_params["bid"]
		
		post_data = {
			"username": username,
			"password": password,
			"persistent": persistent,
			"submit": "Login",
			"bid": self.shoutbox_params["bid"],
			"n": "1"
		}
		
		try:
			self.request_responce = self.request_session.request(
				method = "POST",
				url = url_to_string(post_url),
				data = post_data
			)
		except requests.exceptions.ConnectionError as err:
			return 1
		
		if not (self.request_responce.status_code == 200):
			return 1
		
		if (self.request_responce.text.find("Login was success") == -1):
			return 2
		
		self.user_name = username
		self.user_position = ""
		return 0
	
	def user_logout(self):
		get_url = self.shoutbox_url
		get_url["query"] = "logout=1"
		
		try:
			self.request_responce = self.request_session.request(
				method = "GET",
				url = url_to_string(get_url)
			)
		except requests.exceptions.ConnectionError as err:
			return 1
		
		if not (self.request_responce.status_code == 200):
			return 1
		
		return 0
	
def url_is_valid(url):
	if (type(url) is str):
		url = urlparse(url)._asdict()
	if (url["scheme"] == ""):
		url["scheme"] = "http"
	
	if not (url["scheme"] in ("http", "https")):
		return 0
	elif (url["netloc"] == ""):
		return 0
	else:
		return 1

def cut_string(string, searchstring, offset=[0, 0], cut_searchstrings=0):
	startpos = 0
	while (offset[0] >= 0):
		offset[0] -= 1
		if (string.find(searchstring[0], startpos) != -1):
			startpos = string.find(searchstring[0], startpos + 1)
	
	endpos = 0
	while (offset[1] >= 0):
		offset[1] -= 1
		if (string.find(searchstring[1], endpos) != -1):
			endpos = string.find(searchstring[1], endpos + 1)
	
	if (cut_searchstrings):
		string = (
			string[:startpos] +
			string[endpos + len(searchstring[1]):]
		)
	else:
		string = (
			string[:startpos + len(searchstring[0])] +
			string[endpos:]
		)
	
	return string

def patch_shoutbox(html):
	# Remove HTML if tags (messes up parser)
	html = cut_string(
		html,
		["<!--[if lt IE 7]>]", "<![endif]-->"],
		[0, 1],
		1
	)
	# Remove custom header/footer (can mess up parser)
	html = cut_string(
		html,
		[");\" id=\"mbody\">", "<div align='center'>"],
		[0, 0],
		0
	)
	html = cut_string(
		html,
		[
			"</form>\n</div>",
			"<script type=\"text/javascript\">\n\n  var _gaq"
		],
		[0, 0],
		0
	)
	
	return html

def url_to_string(url):
	return urlunparse(tuple(url.values()))
