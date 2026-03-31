#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
	from Bio.SeqUtils import gc_fraction
except ImportError:
	from Bio.SeqUtils import GC as _legacy_gc

	def gc_percent(sequence):
		return _legacy_gc(sequence)
else:
	def gc_percent(sequence):
		return gc_fraction(sequence) * 100
