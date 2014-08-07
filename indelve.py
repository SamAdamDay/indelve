#!/usr/bin/python

# Use the indelve package
from indelve import Indelve
import sys

if __name__ == '__main__':
	indelve = Indelve(["applications"])
	items = indelve.search(sys.argv[1])
	
	for item in items:
		print item["relevance"] , ": " , item["name"] , "[ " + item["description"] , "]"