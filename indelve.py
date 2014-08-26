#!/usr/bin/python


# Standard Library
from argparse import ArgumentParser
import sys
from textwrap import fill
import console

# Third party libraries
from tabulate import tabulate

# Use the indelve package
from indelve import Indelve
from indelve.bad import *


# Constants
COLUMNS = ("name","exec","description","icon") # The possible colums (ie fields) that can be outputted


# An exception class for errors encountered that are probably due to the user
class HumanError(Exception):
	pass


# The main attraction
if __name__ == '__main__':


	# Get the terminal dimensions
	(terminalWidth, terminalHeight) = console.getTerminalSize()


	## The argument parser

	# Initialise the argument parser
	argParser = ArgumentParser(
		description="A command-line application launcher",
		add_help=False
		)

	# The help option - I want it to be capitalised and end with a full-stop
	argParser.add_argument(
		"-h",
		"--help",
		action="help",
		help="Show this help message and exit."
		)
	# The list of provider-modules to use
	argParser.add_argument(
		"-p",
		"--providers",
		nargs=1,
		action="store",
		default=[""],
		dest="providers", # Explicit is better than implicit.
		help="A comma-separated list of the providers to use to determine the results. Choose from {!s}.".format(COLUMNS)
		)
	# Lists all the provider-modules, with 'short' descriptions
	argParser.add_argument(
		"-l",
		"--list-providers",
		action="store_true",
		dest="listProviders",
		help="List all possible providers, with short descriptions, then exit."
		)
	# Gives the 'long' description of a provider-module
	argParser.add_argument(
		"-d",
		"--provider-description",
		nargs=1,
		dest="providerDescription",
		metavar="PROVIDER",
		help="Give a more detailed description of PROVIDER."
		)
	# The keys in each result's <item-dict> to display (see indelve.providers.abstract.Provider.search)
	argParser.add_argument(
		"-c",
		"--columns",
		nargs=1,
		action="store",
		dest="columns",
		help="A comma-separted list of the columns to display."
		)
	# The format of the results output
	argParser.add_argument(
		"-f",
		"--format",
		nargs=1,
		action="store",
		dest="format",
		help="The format of the output."
		)
	# Whether we'll be using interactive mode
	argParser.add_argument(
		"-i",
		"--interactive",
		action="store_true",
		dest="interactive",
		help="Interactive mode: each change in QUERY will generate a new set of results."
		)
	# The actual search query
	argParser.add_argument(
		"query",
		nargs="?",
		default="-",
		metavar="QUERY",
		help="The search query. Normally only a few letters. If omitted or '-', will be read from standard input."
		)

	# Get all the arguments
	args = argParser.parse_args()


	# The main try-block, catching HumanError's
	try:


		## Some setup

		# Get the list of providers (defaults to None, ie all providers)
		providers = args.providers[0].replace(", ",",").split(",")
		if len(providers) == 0 or providers == [""]:
			providers = None

		# Initialise indelve with the list of providers
		try:
			indelve = Indelve(providers)
		except NoProvidersError:
			raise HumanError("No providers loaded")


		## Descriminate based on the arguments given

		# Print a comma-separated list of providers
		if arguments.listProviders[] == True:
			for provider in indelve.listProviders():
				dictionary = indelve.getProviderDescription(arguments.providerDescription)
				# Print the short description formatted correctly
				print fill(
					"{0<31} - {1}".format(
						arguments.providerDescription,
						dictionary.short
					),
					width = terminalWidth,
					subsequent_indent = " "*34
					)

		# Print a detailed description of the specified provider, if possible
		elif arguments.providerDescription != None:
			try:
				dictionary = indelve.getProviderDescription(arguments.providerDescription[0])
				print arguments.providerDescription[0]
				print dictionary.long
			except ProviderLoadError:
				raise HumanError("Couldn't load description for provider '{}'".format(arguments.providerDescription[0]))

		# Search for the query
		else:

			# Determine if we want to use custom columns
			columns = ["name","description","exec"]
			if arguments.columns[0] != None:
				columns = arguments.columns[0].replace(", ",",").split(",")
				for col in columns:
					if not col in COLUMNS:
						raise HumanError("'{}' is not a valid column".format(col)) 

			# Search for the query
			items = indelve.search(args.query)
			flattened = [[item[col] for col in columns] for item in items]
			print tabulate(flattened,columns)

	except HumanError as ex:
		print "ERROR: {!s}".format(ex)