#!/usr/bin/python

# Standard Library
import sys
import argparse

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
	print providers["applications"].search("Hello")