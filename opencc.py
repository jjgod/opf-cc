#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ctypes import cast, cdll, c_char_p, c_int, c_size_t, c_void_p
from ctypes.util import find_library
import sys

class ConvertError(Exception):
	pass

class DictType:
	TEXT,DATRIE = 0,1

class OpenCC:

	def __init__(self, config=None, verbose=True):
		self.libopencc = cdll.LoadLibrary(find_library('opencc'))
		self.libopencc.opencc_new.restype = c_void_p
		self.libopencc.opencc_convert.argtypes = [c_void_p, c_char_p]
		# for checking for the returned '-1' pointer in case opencc_convert() fails.
		# c_char_p always tries to convert the returned (char *) to a Python string,
		self.libopencc.opencc_convert.restype = c_void_p
		self.libopencc.opencc_free_string.argtypes = [c_char_p]
		self.libopencc.opencc_delete.argtypes = [c_void_p]

		self.config = config
		self.verbose = verbose
		self.od = None
	
	def __enter__(self):
		if self.config is None:
			self.od = self.libopencc.opencc_new(0)
		else:
			self.od = self.libopencc.opencc_new(c_char_p(self.config))
		return self

	def __exit__(self, type, value, traceback):
		self.libopencc.opencc_delete(self.od)
		self.od = None

	def __perror(self, message):
		pass
	
	def convert(self, text):
		retv_c = self.libopencc.opencc_convert(self.od, text, len(text))
		if retv_c == -1:
			self.__perror('OpenCC error:')
			raise ConvertError()
		retv_c = cast(retv_c, c_char_p)
		str_buffer = retv_c.value
		self.libopencc.opencc_free_string(retv_c);
		return str_buffer

if __name__ == "__main__":
	with sys.stdin as fp:
		text = fp.read()
	with OpenCC() as converter:
		print converter.convert(text)
