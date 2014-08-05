"""A provider that searches the installed applications, as specified by http://standards.freedesktop.org/desktop-entry-spec/latest/"""

# Standard Library 
import os
from datetime import datetime
import math

# Import from 'external' directory ("external" is added to `sys.path` in indelve.py)
from xdg import BaseDirectory, DesktopEntry
import xdg.Exceptions

# Import the abstract base class
import abstract

def _getXdgApplicationFiles():
	"""Provide a list of the application files, with full paths.
	Specification: http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html"""
	files = []
	# Loop over the directories in $XDG_DATA_DIRS (essentially; see xdg doc)
	for directory in BaseDirectory.load_data_paths("applications"):
		files.extend([os.path.join(directory,filename) for filename in os.listdir(directory)])
	return files

class LoadError(Exception):
	"""An exception for when there's a problem loading the database."""
	pass

class FileParseError(Exception):
	"""An exception for when there's a problem parsing a file for the database."""
	def __init__(self,fullPath,message):
		self.message = message
		self.fullPath = fullPath
	def __str__(self):
		return self.fullPath + ": " + self.message
	pass

class Provider(abstract.Provider):
	"""The provider for application searching."""

	# The dictionary recording how search results are scored based on the query
	SCORING = {
		"substring": { 					# Matching whole substrings
			"+found": {					# Increment when the substring is found
				"name": 		2500,
				"comment":		750,
				"genericName":	1800
			},
			"+start_string": {			# Additional increment for when it's at the start of the string
				"name": 		3000,
				"comment":		0,
				"genericName":	2600
			},
			"+start_word": {			# Additional increment for when it's at the start of a word (but not the first)
				"name": 		2500,
				"comment":		750,
				"genericName":	1800
			}
		}
	}

	def __init__(self):
		"""Initialise the class by loading up the database."""
		self.database = [] # The database of applications
		self.lastRefreshTime = datetime.min # The last time the application database was refreshed (initially set a LONG time ago)
		self._loadApplications()

	def _loadApplications(self):
		"""Load the applications from the XDG application paths."""

		# Make sure the current database is empty
		if self.database != []:
			raise LoadError("Database already loaded")

		# Loop over the files in the application directories
		for fullPath in _getXdgApplicationFiles():
			# Try to add a dictionay of information about the application specified by `fullPath`
			self._addApplication(fullPath)

		# The database is fresh now
		self.lastRefreshTime = datetime.now()

	def _addApplication(self,fullPath):
		"""Add the details of the application specified by `fullPath`, if possible.
		Returns `True` on success, and the exception that occured on failure."""
		try:
			self.database.append(self._getApplicationDict(fullPath))
			return True
		except (xdg.Exceptions.ParsingError, 
			xdg.Exceptions.DuplicateGroupError, 
			xdg.Exceptions.DuplicateKeyError, 
			os.error, 
			FileParseError) as e:
			return e

	def _getApplicationDict(self,fullPath):
		"""Return a dict with information about the application specified by fullPath."""

		# Check that this is a .desktop file
		if not os.path.isfile(fullPath):
			raise FileParseError(fullPath,"Is directory")
		if os.path.splitext(fullPath)[1].lower() != ".desktop":
			raise FileParseError(fullPath,"Isn't a .desktop file")

		# Try to parse the desktop file; this may produce exceptions
		entry = DesktopEntry.DesktopEntry(fullPath)

		# Make sure this isn't hidden (which is equivalent to not existing at all)
		if entry.getHidden():
			raise FileParseError(fullPath,"Is hidden")

		# Test the `TryExec` key, if it exists
		try:
			if entry.findTryExec() == None:
				raise FileParseError(fullPath,"TryExec failed")
		except xdg.Exceptions.NoKeyError: # If the key doesn't exist, silently ignore it
			pass

		# Make sure this isn't a screensaver
		if "Screensaver" in entry.getCategories():
			raise FileParseError(fullPath,"Is screensaver")

		# Make sure is has a command to execute
		if not entry.getExec():
			raise FileParseError(fullPath,"Has no `exec` key")

		# Add the information from the file to the database
		return {
			"name": entry.getName(),
			"exec": entry.getExec(),
			"comment": entry.getComment(),
			"genericName": entry.getGenericName(),
			"icon": entry.getIcon()
			}

	def refresh(self, force=False):
		"""Reload the applications; only checking for new applictions, unless `force=True`"""

		# If we're forcing, then delete and recreate the database; otherwise only look for new files
		if force:
			self.database = []
			self._loadApplications()
		else:
			# Loop over the files in the application directories
			for fullPath in _getXdgApplicationFiles():

				# If one was modified since the last load, then attempt to load it up
				modifiedTime = datetime.fromtimestamp(os.path.getmtime())
				if modifiedTime > self.lastRefreshTime:
					self._addApplication(fullPath)

	def search(self, query):
		"""Search the database using `query`"""

		# Do some checking
		if not isinstance(query, str):
			raise TypeError("Parameter 'query' should be a string.")
		if len(query) == 0:
			raise ValueError("Parameter 'query' shouldn't be empty.")

		# Get a lowercase verson of query
		queryLower = query.lower()

		# Search for whole substring matches
		matchesSub = [] # A list of <item-dict>'s; specified by the abstract search method docstring
		for app in self.database:
			# Set the score to 0 initially
			score = 0
			# Add to the score using `self.SCORING`
			for key in self.SCORING["substring"]["+found"].keys():
				# Determine the indicies of the the substring `query`
				index = app[key].lower().find(query)
				if index != -1:
					# Add to score for the match
					score += self.SCORING["substring"]["+found"][key]
					if index == 0:
						# Add to score for the match being at the start of the string
						score += self.SCORING["substring"]["+start_string"][key]
					elif app[key][index-1] == " ":
						# Add to the score for the match being at the start of a word
						score += self.SCORING["substring"]["+start_word"][key]
			# Matches for longer strings are more impressive
			score *= math.log(len(query))/2 + 1 
			# If a match is found, then add it to the list of matches
			if score > 0:
				matchesSub.append({
					"relevance": score,
					"name": app["name"],
					"description": app["comment"],
					"icon": app["icon"]
					})

		return matchesSub