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

from binaryornot.check import is_binary
import logging
import syncer
import re


log = logging.getLogger(__name__)


class PalimpsestFileSyncer(syncer.FileSyncer):

	def __init__(self, src_dir, out_dir, w_path, replace):
		super().__init__(src_dir, out_dir, w_path)
		self.replace = replace

	def copy(self):
		if self.check_type():
			return self.process()
		else:
			return super().copy()

	def check_type(self):
		try:
			return not is_binary(self.to_src())
		except Exception as e:
			log.warn(e)
			return False

	def process(self):
		src_file = self.to_src()
		out_file = self.to_out()
		log.debug(f'processing {self.w_path}')
		try:
			with open(src_file) as src_fd, open(out_file, 'w') as out_fd:
				for src_line in src_fd:
					out_fd.write(self.replace(src_line))
		except Exception as e:
			log.warn(f'could not process file {src_file}: {e}')
			return False
		return True


class PalimpsestTreeSyncer(syncer.TreeSyncer):

	file_syncer = lambda self, s, o, w: PalimpsestFileSyncer(s, o, w, self.replace)

	def __init__(self, src_dir, out_dir, resources):
		super().__init__(src_dir, out_dir)
		self.resources = self.flatten_resources(resources, '.', '@{', '}')
		self.regex = re.compile('|'.join(map(re.escape, self.resources.keys())))

	def replace(self, line):
		return self.regex.sub(lambda k: self.resources[k.group(0)], line)

	def flatten_resources(self, resources, separator='.', prefix='', suffix=''):
		out = {}

		for key, value in resources.items():
			if isinstance(value, dict):
				for kkey, vvalue in self.flatten_resources(value, separator).items():
					out[key + separator + kkey] = vvalue 
			else:
				out[key] = value

		if len(prefix) > 0 or len(suffix) > 0:
			out = {prefix + key + suffix: value
				for key, value in out.items()}

		return out
