"""Provides an abstract base class for search providers, specifying methods they must implement"""



# -----------------------------
# - Imports
# -----------------------------

# Standard Library
from abc import ABCMeta, abstractmethod



# -----------------------------
# - Main Classes
# -----------------------------

class Provider:
	"""Abstract base class for search providers"""

	# This is an abstract class
	__metaclass__ = ABCMeta

	# The relevance dictionary, recording how providers should determine the relevance score of their results
	RELEVANCE = {
		"min"           : 0,        # The minimum relelvance score
		"bad"           : 2500,     # A bad match; these are normally ignored
		"acceptable"    : 5000,     # Just high enough chance of being the indendent result to be included
		"good"          : 7500,     # Most searches for things that exist should return these at the top
		"excellent"     : 9000,     # An excellent match; almost certainly the intended result of the search
		"max"           : 10000     # The maximum relevance score
	}

	@abstractmethod
	def __init__(self):
		"""Initialise the provider"""

	@abstractmethod
	def refresh(self,force=False):
		"""Refresh the database of items. 

		If the provider does not have a database, then this should do nothing.
		The `force` argument indicates that the provider should completely reload the database, not just check for new items.
		"""
		pass

	@abstractmethod
	def search(self,query):
		"""Provide results for `query`.

		Must provide a list of <item-dict>'s, each with the following keys:
			"relevance"     : The relevance of the item to `query`, see `Provider.RELEVANCE` above
			"name"          : The main displayed name of the item
			"exec"          : A command to execute if the item is selected
			"desciription"  : (optionally empty) A short desciription
			"icon"          : (optionally empty) Either the absolute path or the XDG icon name of an icon associated with the item
			                    (see http://standards.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html)
		Note: The provider should give a list of ALL results matching the query (ie with non-zero relevance score), no matter how small the score. 
		Any ValueErrors raised will be caught.
		"""
		pass