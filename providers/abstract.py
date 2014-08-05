"""Provides an abstract base class for search providers, specifying methods they must implement"""

# Standard Library
from abc import ABCMeta, abstractmethod

class Provider:
	"""Abstract base class for search providers"""

	# This is an abstract class
	__metaclass__ = ABCMeta

	@abstractmethod
	def __init__(self):
		"""Initialise the provider"""

	@abstractmethod
	def refresh(self,force=False):
		"""Refresh the database of items. 

		If the provider does not have a database, then this should do nothing.
		The `force` argument indicates that the provider should completely reload the database, not just check for new items
		"""
		pass

	@abstractmethod
	def search(self,query):
		"""Provide results for `query`.

		Must provide a list of dicts of the with the following keys:
			"relevance"     : The relevance of the item to `query`
			"name"          : The main displayed name of the item
			"desciription"  : (optionally empty) A short desciription
			"icon"          : (optionally empty) Either the absolute path or the XDG icon name of an icon associated with the item
			                  (see http://standards.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html)
		"""
		pass