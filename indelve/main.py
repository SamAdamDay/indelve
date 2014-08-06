#!/usr/bin/python

# Standard Library
import sys
from argparse import ArgumentParser
from pprint import pprint

# Import from third party libraries
from xdg import BaseDirectory, DesktopEntry
import xdg.Exceptions

# Import the search providers
import providers.applications

if __name__ == '__main__':
	providers = {
		"applications" : providers.applications.Provider()
	}
	items = providers["applications"].search(sys.argv[1])
	items.sort(key=lambda a:a["relevance"])
	for item in items:
		print item["relevance"] , ": " , item["name"] , "[ " + item["description"] , "]"