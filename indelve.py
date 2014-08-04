#!/usr/bin/python

# Standard Library
import sys
import os
import argparse
from datetime import datetime

# Import from `external` directory
sys.path.insert(0,"external")
from xdg import BaseDirectory, DesktopEntry
import xdg.Exceptions

def getXdgApplicationFiles():
	"""Provide a list of the application files, with full paths.
	Specification: http://standards.freedesktop.org/basedir-spec/basedir-spec-latest.html"""
	files = []
	# Loop over the directories in $XDG_DATA_DIRS (essentially; see xdg doc)
	for directory in BaseDirectory.load_data_paths("applications"):
		files.extend([os.path.join(directory,filename) for filename in os.listdir(directory)])
	return files

class DatabaseLoadError(Exception):
	"""An exception for when there's a problem loading the database."""
	pass

class DatabaseFileParseError(Exception):
	"""An exception for when there's a problem parsing a file for the database."""
	pass

class Database:
	"""The class for the database of applications."""

	def __init__(self):
		"""Initialise the class by loading up the database."""
		self.database = [] # The database of applications
		self.lastRefreshTime = datetime.min # The last time the application database was refreshed (initially set a a LONG time ago)
		self._loadApplications()

	def _loadApplications(self):
		"""Load the applications from the XDG application paths."""

		# Make sure the current database is empty
		if self.database != []:
			raise DatabaseLoadError("Database already loaded")

		# Loop over the files in the application directories
		for fullPath in getXdgApplicationFiles():
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
		except (xdg.Exceptions.ParsingError, xdg.Exceptions.DuplicateGroupError, xdg.Exceptions.DuplicateKeyError, os.error, DatabaseFileParseError) as e:
			return e

	def _getApplicationDict(self,fullPath):
		"""Return a dict with information about the application specified by fullPath."""

		# Check that this is a .desktop file
		if not os.path.isfile(fullPath):
			raise DatabaseFileParseError("Is directory")
		if str.lower(os.path.splitext(fullPath)[1]) != ".desktop":
			raise DatabaseFileParseError("Isn't a .desktop file")

		# Try to parse the desktop file; any validation errors will be caught and ignored
		entry = DesktopEntry.DesktopEntry(fullPath)

		# Make sure this isn't hidden (which is equivalent to not existing at all)
		if entry.getHidden():
			raise DatabaseFileParseError("Is hidden")

		# Test the `TryExec` key, if it exists
		try:
			if entry.findTryExec() == None:
				raise DatabaseFileParseError("TryExec failed")
		except xdg.Exceptions.NoKeyError: # If the key doesn't exist, silently ignore it
			pass

		# Make sure this isn't a screensaver
		if "Screensaver" in entry.getCategories():
			raise DatabaseFileParseError("Is screensaver")

		# Add the information from the file to the database
		return {
			"name": entry.getName(),
			"exec": entry.getExec(),
			"comment": entry.getComment(),
			"genericName": entry.getGenericName(),
			"icon": entry.getIcon()
			}

	def refresh(self, force=True):
		"""Reload the applications; only checking for new applictions, unless `force=True`"""

		# If we're forcing, then delete and recreate the database; otherwise only look for new files
		if force:
			self.database = []
			self._loadApplications()
		else:
			# Loop over the files in the application directories
			for fullPath in getXdgApplicationFiles():

				# If one was modified since the last load, then attempt to load it up
				modifiedTime = datetime.fromtimestamp(os.path.getmtime())
				if modifiedTime > self.lastRefreshTime:
					self._addApplication(fullPath)


if __name__ == '__main__':
	database = Database()
	print database.database