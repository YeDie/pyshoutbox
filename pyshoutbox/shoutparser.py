#!/usr/bin/python3.4

__title__ = "pyshoutparser"
__version__ = "0.1.0"

from html.parser import HTMLParser
from requests.utils import urlparse
from urllib.parse import parse_qs

class box_parser(HTMLParser):
	last_tagnames = [""]
	title = None
	char_limit = None
	params = {
		"sid": None,
		"shtoken": None,
		"bid": None,
		"aaabbb": None
	}
	data = ""
	
	def handle_starttag(self, tagname, tagattributes):
		self.last_tagnames.insert(0, tagname)
		for tagattribute in tagattributes:
			if (
				tagname == "script" and
				tagattribute[0] == "src" and
				tagattribute[1].find("/s/jscode.php") != -1
			):
				self.handle_jscode_source(tagattribute[1])
			elif (
				tagname == "input" and
				tagattribute[0] == "name" and
				tagattribute[1] == "shtoken"
			):
				self.params["shtoken"] = tagattributes[2][1]
			elif (
				tagname == "input" and
				tagattribute[0] == "name" and
				tagattribute[1] == "aaabbb"
			):
				self.params["aaabbb"] = tagattributes[2][1]
			elif (
				tagname == "span" and
				tagattribute[0] == "id" and
				tagattribute[1] == "charCount"
			):
				self.data = "char_limit"
		
	def handle_endtag(self, tagname):
		self.last_tagnames.insert(0, "/" + tagname)
	
	def handle_data(self, data):
		if (self.last_tagnames[0] == "title"):
			self.title = data
		elif (self.data == "char_limit"):
			try:
				self.char_limit = int(data)
			except ValueError as err:
				self.char_limit = -1
			
			self.data = None
	
	def handle_jscode_source(self, source):
		# This is where we get the box and session IDs from.
		script_url = urlparse(source)
		script_query = parse_qs(script_url.query)
		self.params["sid"] = script_query["sid"][0]
		self.params["bid"] = script_query["b"][0]

class shout_parser(HTMLParser):
	last_tagnames = []
	shouts = []
	shout_template = {
		"name": None, # User name
		"message": None, # Message
		"timestamp": None, # Timestamp
		"user_position": None, # User position
		"online": None, # User online status
		"uid": None, # Unique guest ID
		"idn": None, # Shout identification number (for quoting)
		"sid": None # Shout ID (for editing/deleting)
	}
	shout = dict(shout_template)
	onliners = None
	data = ""
	
	def handle_starttag(self, tagname, tagattributes):
		self.last_tagnames.insert(0, tagname)
		if (
			tagname == "br" and
			self.shout["timestamp"] != None and
			self.shout["message"] == None
		):
			self.data = "message"
			self.shout["message"] = ""
		
		elif (tagname == "br" and self.data == "message"):
			self.shout["message"] += "\n"
			
		for tagattribute in tagattributes:
			if (
				tagname == "div" and
				tagattribute[0] == "id" and
				tagattribute[1] == "onliners"
			):
				data = "onliners"
			
			if (
				tagname == "td" and
				tagattribute[0] == "class" and
				tagattribute[1] in ("cell3b", "altb")
			):
				if not (self.shout["name"] == None):
					self.shouts.append(dict(self.shout))
					self.shout = dict(self.shout_template)
				
				self.handle_shout_data(tagattributes[2][1])
			
			if (tagname == "a" and tagattribute[0] == "idname"):
				self.handle_shout_idname(tagattributes)
			
			if (
				tagname == "a" and
				tagattribute[1] == "button userclick"
			):
				self.handle_shout_id(tagattributes[2][1])
	
	def handle_endtag(self, tagname):
		self.last_tagnames.insert(0, "/" + tagname)
	
	def handle_data(self, data):
		if (self.data == "onliners"):
			try:
				onliners = int(data)
			except ValueError as err:
				onliners = -1
			
			self.data = ""
		
		if (self.data == "message"):
			if (self.last_tagnames[0] == "table"):
				self.data = ""
			else:
				self.shout["message"] += data.rstrip("\n")
	
	def handle_shout_data(self, value):
		if (value.find("ID") != -1):
			# User is guest
			self.shout["timestamp"] = value.partition(
				" - Unique ID: "
			)[0]
			try:
				self.shout["uid"] = int(value.partition(
					" - Unique ID: "
				)[2])
			except ValueError as err:
				self.shout["uid"] = -1
			self.shout["user_position"] = "Guest"
		else:
			if (value.find("Online") != -1):
				self.shout["online"] = 1
				part = " - Online - "
			else:
				self.shout["online"] = 0
				part = " - Offline - "
			
			self.shout["timestamp"] = value.partition(part)[0]
			self.shout["user_position"] = value.partition(part)[2]
			self.shout["uid"] = -1
	
	def handle_shout_idname(self, tagattributes):
		self.shout["name"] = tagattributes[2][1][1:-1]
		try:
			self.shout["idn"] = int(tagattributes[1][1])
		except ValueError as err:
			self.shout["idn"] = -1
	
	def handle_shout_id(self, value):
		try:
			self.shout["sid"] = int(value.partition(";")[0])
		except ValueError as err:
			self.shout["sid"] = -1

box_parser = box_parser(strict=False)
shout_parser = shout_parser(strict=False)
