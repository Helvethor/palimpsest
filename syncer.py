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
import re
import time
import shutil
import logging
import inspect
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


log = logging.getLogger(__name__)


class PathSyncer:

	def __init__(self, src_dir, out_dir, w_path):
		self.src_dir = os.path.abspath(src_dir)
		self.out_dir = os.path.abspath(out_dir)
		self.w_path = w_path

	@staticmethod
	def is_dir(path):
		return os.path.isdir(path) and not os.path.islink(path)
	
	@staticmethod
	def is_file(path):
		return os.path.isfile(path) and not os.path.islink(path)

	@staticmethod
	def is_symlink(path):
		return os.path.islink(path)

	@classmethod
	def remove(cls, path):
		try:
			if cls.is_dir(path):
				shutil.rmtree(path)
			else:
				os.remove(path)
		except Exception as e:
			log.warn(e)
			return False
		return True

	@staticmethod
	def get_mtime(path):
		return os.lstat(path).st_mtime

	def to_any(self, base_dir):
		return os.path.abspath(os.path.join(base_dir, self.w_path))

	def to_src(self):
		return self.to_any(self.src_dir)

	def to_out(self):
		return self.to_any(self.out_dir)

	def sync(self):
		if os.path.lexists(self.to_src()):
			return False
		if os.path.lexists(self.to_out()):
			return self.remove(self.to_out())

	def check(self):
		return self.check_mtime()
		
	def check_mtime(self):
		src_path = self.to_src()
		out_path = self.to_out()
		if not os.path.lexists(out_path):
			return False
		src_mtime = self.get_mtime(src_path)
		out_mtime = self.get_mtime(out_path)
		return out_mtime > src_mtime


class DirSyncer(PathSyncer):

	def copy(self):
		out_dir = self.to_out()
		try:
			os.makedirs(out_dir)
		except Exception as e:
			log.warn(e)
			return False
		return True

	def sync(self):
		src_dir = self.to_src()
		out_dir = self.to_out()
		
		log.debug(f'syncing dir {self.w_path}')
		if self.is_dir(src_dir):
			if self.is_dir(out_dir):
				return True
			else:
				return self.copy()
		else:
			if os.lexists(src_dir):
				return False
			elif os.lexists(out_dir):
				return self.remove(out_dir)


class FileSyncer(PathSyncer):

	def copy(self):
		log.debug(os.path.exists(self.to_src()))
		try:
			shutil.copy2(self.to_src(), self.to_out())
		except Exception as e:
			log.debug(self.to_src())
			log.warn(e)
			return False
		return True

	def sync(self):
		src_file = self.to_src()
		out_file = self.to_out()

		log.debug(f'syncing file {self.w_path}')
		if self.is_file(src_file):
			if os.path.lexists(out_file):
				log.debug(f'remove {out_file}')
				self.remove(out_file)
			return self.copy()
		else:
			if os.path.lexists(src_file):
				return False
			elif os.path.lexists(out_file):
				return self.remove(out_file)


class SymlinkSyncer(PathSyncer):
		
	def copy(self):
		try:
			shutil.copy2(self.to_src(), self.to_out(), follow_symlinks=False)
		except Exception as e:
			log.warn(e)
			return False
		return True

	def sync(self):
		src_symlink = self.to_src()
		out_symlink = self.to_out()

		log.debug(f'syncing symlink {self.w_path}')
		if self.is_symlink(src_symlink):
			self.remove(out_symlink)
			if not self.copy():
				log.warn(f'could not copy {self.w_path}')
				return False
		else:
			if os.path.lexists(src_symlink):
				log.warn('{src_symlink} is not a symlink')
				return False
			elif os.path.lexists(out_symlink):
				if not self.remove(out_symlink):
					log.warn('could not remove {out_symlink}')
					return False
		return True

	def check(self):
		return self.check_target()

	def check_target(self):
		src_link = os.readlink(self.to_src())
		out_link = os.readlink(self.to_out())
		if os.path.realpath(self.to_src()) == os.path.realpath(self.to_out()):
			return True
		elif src_link == out_link:
			return True
		return False


class TreeSyncer(FileSystemEventHandler):

	dir_syncer = DirSyncer
	file_syncer = FileSyncer
	symlink_syncer = SymlinkSyncer

	def __init__(self, src_dir, out_dir):
		self.src_dir = os.path.abspath(src_dir)
		self.out_dir = os.path.abspath(out_dir)
		self.dir_thread = []

	def walk(self):
		w_dirs = []
		w_files = []
		w_symlinks = []
		os.chdir(self.src_dir)
		
		def walk():
			for dir_path, dir_names, file_names in os.walk('.'):
				for dir_name in dir_names:
					yield os.path.join(dir_path, dir_name)
				for file_name in file_names:
					yield os.path.join(dir_path, file_name)

		return walk()

	def path_syncer(self, path):
		if os.path.isabs(path):
			os.chdir(self.src_dir)
			w_path = os.path.relpath(path)
		else:
			w_path = path

		if PathSyncer.is_symlink(w_path):
			return self.symlink_syncer(self.src_dir, self.out_dir, w_path)
		elif PathSyncer.is_dir(w_path):
			return self.dir_syncer(self.src_dir, self.out_dir, w_path)
		elif PathSyncer.is_file(w_path):
			return self.file_syncer(self.src_dir, self.out_dir, w_path)
		return PathSyncer(self.src_dir, self.out_dir, w_path)

	def sync(self, force=False):
		failed = []

		for i, w_path in enumerate(self.walk()):
			path_syncer = self.path_syncer(w_path)
			if force or not path_syncer.check():
				if not path_syncer.sync():
					failed.append(w_path)

		return failed

	def daemon(self):
		observer = Observer()
		observer.schedule(self, self.src_dir, recursive=True)
		observer.start()

		try:
			while True:
				time.sleep(1)
		except KeyboardInterrupt:
			observer.stop()
		except Exception as e:
			log.error(e)

		observer.join()

	def on_any_event(self, event):
		log.debug(event)

	def on_created(self, event):
		path_syncer = self.path_syncer(event.src_path)
		if not path_syncer.sync():
			log.warn(f'could not sync {event.src_path}')

	def on_modified(self, event):
		path_syncer = self.path_syncer(event.src_path)
		if not path_syncer.sync():
			log.warn(f'could not sync {event.src_path}')

	def on_deleted(self, event):
		path_syncer = self.path_syncer(event.src_path)
		if not path_syncer.sync():
			log.warn(f'could not sync {event.src_path}')

	def on_moved(self, event):
		src_syncer = self.path_syncer(event.src_path)
		out_syncer = self.path_syncer(event.dest_path)

		os.rename(src_syncer.to_out(), out_syncer.to_out())
