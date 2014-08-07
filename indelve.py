#!/usr/bin/python

# Standard Library
from argparse import ArgumentParser

# Use the indelve package
from indelve import Indelve
import sys

# The main attraction
if __name__ == '__main__':

	# Configure the argument parser
	argParser = ArgumentParser(description="A command-line application launcher")
	argParser.add_argument(
		"-c",
		"--columns",
		nargs=1,
		action="store",
		dest="columns", # Explicit is better than implicit.
		help="The columns to display."
		)
	argParser.add_argument(
		"-f",
		"--format",
		nargs=1,
		action="store",
		dest="format", # import this
		help="The format of the output."
		)
	argParser.add_argument(
		"-i",
		"--interactive",
		action="store_true",
		dest="interactive", # Words to live by.
		help="Interactive mode: each change in <query> will generate a new set of results."
		)
	argParser.add_argument(
		"query",
		nargs="?",
		default="-",
		help="The search query. Normally only a few letters. If omitted or '-', will be read from STDIN."
		)
	args = argParser.parse_args()

	indelve = Indelve(["applications"])
	items = indelve.search(args.query)
	
	for item in items:
		print item["relevance"] , ": " , item["name"] , "[ " + item["description"] , "]"