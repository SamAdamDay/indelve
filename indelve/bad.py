"""Warning and exception classes for indelve"""



# -----------------------------
# - Warnings
# -----------------------------

class IndelveInitWarning(Warning):
	"""The warning class for when there was a problem initialising the Indelve class."""
	pass


class ProviderLoadWarning(IndelveInitWarning):
	"""The warning class for when a provider couldn't be loaded."""
	pass



# -----------------------------
# - Exceptions
# -----------------------------

class ProviderLoadError(Exception):
	"""The exception class for when a provider couldn't be loaded"""

	def __init__(self,provider):
		"""Initialises the exception with provider name `provider`"""

		if not isinstance(provider, str):
			raise ValueError("Parameter 'provider' should be a string.")

		self.provider = provider

	def __str__(self):
		"""Return an 'informal' string representation of the exception"""

		return "Could not load provider '"+self.provider+"'"


class IndelveInitError(Exception):
	"""The exception class for when there was a problem initialising the Indelve class."""
	pass


class NoProvidersError(IndelveInitError):
	"""The exception class for when no providers were successfully loaded."""
	pass