#!/usr/bin/python

# Standard Library
import sys
import argparse
from pprint import pprint

# Import from 'external' directory
sys.path.insert(1,"external")
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
		print item["relevance"] , ": " , item["name"] , " [" + item["description"] , "]"