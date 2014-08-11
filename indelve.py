#!/usr/bin/python

# Standard Library
from argparse import ArgumentParser

# Use the indelve package
from indelve import Indelve
import sys

# The main attraction
if __name__ == '__main__':

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
		dest="providers", # Explicit is better than implicit.
		help="A comma-separated list of the providers to use to determine the results."
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

	# Initialise indelve
	indelve = Indelve()

	# Search for for the query
	items = indelve.search(args.query)
	
	for item in items:
		print item["relevance"] , ": " , item["name"] , "[ " + item["description"] , "]"