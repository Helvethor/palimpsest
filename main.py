#!/usr/bin/env python3

# Copyright 2017 Vincent Pasquier
#
# This file is part of palimpsest.
#
# palimpsest is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# palimpsest is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with palimpsest.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import time
import json
import logging
import argparse
import syncer
import palimpsest
from watchdog.observers import Observer


DEFAULT_CONFIG = {
	'resources_file': 'resources.json',
	'src_dir': 'src',
	'out_dir': 'out',
	'force': False,
	'daemon': False,
	'debug': False
}


def parse_config(config_file):
	config = DEFAULT_CONFIG
	try:
		with open(config_file, 'r') as config_fd:
			config.update(json.load(config_fd))
	except Exception as e:
		sys.stderr.write(f'{e}\n')
		sys.exit(1)

	resources_file = config['resources_file']
	if not os.path.isabs(resources_file):
		resources_file = os.path.join(os.path.split(config_file)[0], resources_file)
		config['resources_file'] = resources_file

	return config

def main():
	
	parser = argparse.ArgumentParser(description='Preprocess configuration files')
	parser.add_argument('--config-file',
		help='JSON configuration file')
	parser.add_argument('--resources-file',
		help='JSON file containing key-values to use')
	parser.add_argument('--src-dir', 
		help='Directory containing source files')
	parser.add_argument('--out-dir',
		help='Directory to output processed files to')
	parser.add_argument('--force', default=None, action='store_true',
		help='Process every file')
	parser.add_argument('--daemon', default=None, action='store_true',
		help='Continuously watch for changes in src_dir')
	parser.add_argument('--debug', default=None, action='store_true',
		help='Show debug information')
	args = vars(parser.parse_args())

	if args['config_file'] is not None:
		config = parse_config(args['config_file'])
	else:
		config = DEFAULT_CONFIG
	args = {key: config.get(key, None) if value is None else value
		for key, value in args.items()}

	if args['debug']:
		logging.getLogger('watchdog').setLevel(logging.WARNING)
		logging.basicConfig(level=logging.DEBUG)
		syncer.log.setLevel(logging.DEBUG)
		palimpsest.log.setLevel(logging.DEBUG)

	try:
		with open(args['resources_file']) as resources_fd:
			resources = json.load(resources_fd)
	except Exception as e:
		logging.error(f'{e}')
		sys.exit(1)
	
	ts = palimpsest.PalimpsestTreeSyncer(args['src_dir'], args['out_dir'], resources)
	failures = ts.sync(args['force'])
	if len(failures) > 0:
		log.warn(f'following path could not be synced: {failures}')
	if (args['daemon']):
		ts.daemon()

if __name__ == '__main__':
	main()
