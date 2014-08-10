"""An application searcher"""



# -----------------------------
# - Imports
# -----------------------------

# Standard Library
import sys
from argparse import ArgumentParser
from pprint import pprint
from importlib import import_module
from warnings import warn

# Import from third party libraries
from xdg import BaseDirectory, DesktopEntry
import xdg.Exceptions

# Import 'local' modules
import bad # Warnings and exceptions
from utilities import isItemDict



# -----------------------------
# - Main Classes
# -----------------------------

class Indelve:
	"""Indelve: an application searcher.

	The main class of indelve. This is where all the action happens.
	"""


	def __init__(self,providers=None):
		"""Initialise the indelve class, loading the search providers specified by the list `providers` (default:all)

		Issues a `bad.providerLoadWarning` when a provider couldn't be loaded
		"""

		# If `providers` is not specified, load all the provider modules
		if providers == None:
			providers = self.listProviders()

		# The dictionary of `Provider` class instances
		self.providerInstances = {}

		# Loop through the specified providers
		for provider in providers:
			# Attempt to import the provider, sending a warning that fails
			try:
				providerModule = import_module("indelve.providers."+provider)
			except ImportError:
				warn(provider, bad.providerLoadWarning)
				continue
			# Now load the provider's `Provider` class; if there's an exception with this, then there's a real problem with the code, so let it pass through
			self.providerInstances[provider] = providerModule.Provider()


	def listProviders(self,descriptions=False):
		"""Lists the possible provider modules.

		If `descriptions` is False (default) it just provides a list, otherwise it provides a dict with entries:
		"provider_name" : {
			"short" : "<short description>",
			"long" : "<long description>",
			 }
		See indelve.proivders.abstract.Provider.description for more information.
		"""

		# The list of providers will be the `providers` packages's __all__ list
		initModule = import_module("indelve.providers.__init__")
		providerList = initModule.__all__

		if not descriptions:
			# If we don't need the descriptions, then this is all we need
			return providerList
		else:
			# Otherwise, load up all the provider modules to get their short and long descriptions
			providerDict = {}
			for provider in providerList:
				# Get the description dictionary by loading the the provider module
				providerModule = import_module("indelve.providers."+provider)
				descriptionDict = providerModule.Provider.description
				# Make sure the dictionary has the necessary keys
				if "short" not in descriptionDict or "long" not in descriptionDict:
					raise NotImplementedError("Provider '"+provider+"' does not have a proper description dictionary.")
				# Add it to the dictionary to be returned
				providerDict[provider] = descriptionDict
			return providerDict


	def refresh(self,force=False):
		"""Refresh all providers' databases, if that makes sense.

		If the provider does not have a database, then this has no effect on them.
		The `force` argument indicates that the providers should completely reload their databases, not just check for new items."""

		# Loop through the provider instances
		for name in self.providerInstances:
			# Refresh this provider's database
			self.providerInstances[name].refresh(force)


	def search(self,query):
		"""Search for `query` using all the loaded providers.

		Returns a list of <item-dict>'s sorted by relevance. (See providers.abstract.Provider.search for a specification for <item-dict>)
		"""

		# Do some checking
		if not isinstance(query, str):
			raise TypeError("Parameter 'query' should be a string.")
		if len(query) == 0:
			raise ValueError("Parameter 'query' shouldn't be empty.")

		# The list of item dicts
		items = []

		# Loop through the provider instances
		for name in self.providerInstances:
			# Try gettin the results from this provider; it may be that `query` is not right for the provider, in which case ignore it
			try:
				results = self.providerInstances[name].search(query)
			except ValueError:
				continue
			# Verify that each item is indeed an <item-dict>
			for item in items:
				assert isItemDict(item)
			# Add the results to our list
			items.extend(results)

		# Sort the items by relevance
		items.sort(key=lambda a:a["relevance"])

		# Finally return the sorted list
		return items