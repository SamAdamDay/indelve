"""A provider that searches the installed applications, as specified by http://standards.freedesktop.org/desktop-entry-spec/latest/"""

# Standard Library 
import os
from datetime import datetime
import math

# Import from third party libraries
from xdg import BaseDirectory, DesktopEntry
import xdg.Exceptions

# Import the abstract base class
import abstract

# Import from the utilities module
from utilities import which

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
			},
			"-multiples": {				# Penalise searches that match in multiple keys - these tend to have skewed results otherwise
				0:				0,
				1:				0,
				2:				2000,
				3:				4000
			}
		},
		"acronym": {					# Matching acronyms
			"+found": {					# Increment when the acronym is found somewhere
				"name":			3000,
				"genericName":	3000,
			},
			"+start_string": {			# Additional increment for when it's at the start of the string
				"name":			800,
				"genericName":	800,
			},
			"+letter_word": {			# Additional increment per letter that is at the beginning of a word
				"name":			1200,
				"genericName":	1000,
			},
			"+letter_capital": {		# Additional increment per letter that is uppercase where the previous character is a lowercase letter
				"name":			800,
				"genericName":	700,
			},
			"-letter_non": {			# Penalty per letter not matching +letter_word or +letter_capital
				"name":			500,
				"genericName":	500,
			},
			"-letter_word_skip": {		# Penalty per letter that skips a word (e.g. "rv" matching "Remote Desktop Viewer")
				"name":			1200,
				"genericName":	1000,
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

		# Make sure this is an application
		if entry.getType() != "Application":
			raise FileParseError(fullPath,"Isn't an application")

		# Make sure this isn't hidden (which is equivalent to not existing at all)
		if entry.getHidden():
			raise FileParseError(fullPath,"Is hidden")

		# Test the `TryExec` key, if it exists
		try:
			if which(entry.getTryExec()) == None:
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


	def _acronymMaxiumScore(self, string, acronym, key, first=False):
		"""Recurively determine the maximal score when finding `acronym` in `string` using `self.SCORING`. 

		`acronym` is assumed to be lowercase and not contain " _-".
		`key` is the application key being considered.
		`first` specifies whether this is the first time through, and so if "+start_string" can be applied.
		"""

		# If there's no more acronym left then we've found a match!
		if len(acronym) == 0:
			#print "0"
			return self.SCORING["acronym"]["+found"][key]

		# The maximum score
		maxScore = 0

		# What's left of the string: it will be repeatedly shortened as the possible acronym matches are evaluates
		stringLeft = string

		# For each occurence of `acronym[0]`, determine the maximum score attained by selecting that as the beginning of the acronym match
		while True:

			# Determine the index of the first occurence in `string` of the first letter of the acronym
			index = stringLeft.lower().find(acronym[0])

			# If the first acronym letter isn't there, then we're done
			if index == -1: 
				break

			# The score for the current letter
			letterScore = 0

			# Determine whether this is the first letter of the original string (so also the beginning of a word)
			if first and index == 0 and stringLeft == string:
				letterScore += self.SCORING["acronym"]["+start_string"][key]
				letterScore += self.SCORING["acronym"]["+letter_word"][key] # This is the only time this happens when `index` == 0, since `" " not in acronym`
			# Determine whether this is the first letter of a word
			if index > 0 and stringLeft[index-1] == " ":
				letterScore += self.SCORING["acronym"]["+letter_word"][key]
			# Determine whether this is an uppercase letter following a lowercase letter (note: the letter proceeding `stringLeft` is almost always `acronym[0]`)
			if index > 0 and stringLeft[index].upper() == stringLeft[index] and stringLeft[index-1].lower() == stringLeft[index-1] and stringLeft[index-1].upper() != stringLeft[index-1]:
				letterScore += self.SCORING["acronym"]["+letter_capital"][key]

			# If `letterScore` hasn't changed, then none of the conditions have held
			if letterScore == 0:
				letterScore = 0 - self.SCORING["acronym"]["-letter_non"][key]

			# Determine whether this has skipped a word (see if there is a space in any of the characters of `string` up to `index` ajdusted to `string` -2)
			if not first and " " in string[:index-len(stringLeft)-1]:
				letterScore -= self.SCORING["acronym"]["-letter_word_skip"][key]

			# Remove up to and including the first match
			stringLeft = stringLeft[index+1:]

			# Determine the maximum score from stringLeft and the rest of the acronym
			remainScore = self._acronymMaxiumScore(stringLeft, acronym[1:], key)

			# Only include this as a possibility if the remained of the acronym actually matched the remained of the string
			nextScore = letterScore + remainScore if remainScore != 0 else 0

			# Calculate the rolling maximum
			maxScore = max(maxScore, nextScore)

		# This is the final calculated maximum score
		return maxScore


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

		# All the matches
		matches = [] # A list of <item-dict>'s; specified by the abstract search method docstring

		# Loop through the database, looking for matches
		for app in self.database:

			## Search for whole substring matches
			# The score under substring
			scoreSub = 0
			# The number of keys in which there are matches
			keysMatched = 0
			# Add to the score using `self.SCORING`
			for key in self.SCORING["substring"]["+found"].keys():
				# Determine the indicies of the the substring `queryLower`
				index = app[key].lower().find(queryLower)
				if index != -1:
					keysMatched += 1
					# Add to score for the match
					scoreSub += self.SCORING["substring"]["+found"][key]
					if index == 0:
						# Add to score for the match being at the start of the string
						scoreSub += self.SCORING["substring"]["+start_string"][key]
					elif app[key][index-1] == " ":
						# Add to the score for the match being at the start of a word
						scoreSub += self.SCORING["substring"]["+start_word"][key]
			# Penalise multiple matches
			scoreSub -= self.SCORING["substring"]["-multiples"][keysMatched]
			# Matches for longer strings are more impressive
			scoreSub = int(scoreSub * (math.log(len(query))/5 + 1))

			## Search for acronym matches ('gimp' matches 'GNU Image Manipulation Program' and 'low' matches 'LibreOffice Writer')
			# The score under acronym
			scoreAcr = 0
			# Add to the score using `self.SCORING`
			for key in self.SCORING["acronym"]["+found"].keys():
				# Find the maximum possible score of matching an acronym recursively (this is pretty neat)
				maxScore = self._acronymMaxiumScore(app[key],queryLower.translate(None," _-"),key,True)
				# Calculate the rolling maximum (the keys searched are distinct, and searches will almost certainly be aiming for only one)
				scoreAcr = max(scoreAcr,maxScore)

			# The score is the max of the two match type scores (adding makes no sense since they represent differen types of search)
			score = max(scoreSub,scoreAcr)

			# Make sure the score is valid
			if score < abstract.Provider.RELEVANCE["min"]: # module.class.dictionay[string]! :)
				score = abstract.Provider.RELEVANCE["min"]
			if score > abstract.Provider.RELEVANCE["max"]:
				score = abstract.Provider.RELEVANCE["max"]

			# If a match is found, then add it to the list of matches
			if score > 0:
				matches.append({
					"relevance": score,
					"name": app["name"],
					"exec": app["exec"],
					"description": app["comment"],
					"icon": app["icon"]
					})

		return matches