"""
LanguageFrequency

@author: James McCracken
"""

import os
from collections import defaultdict
import csv

from lex.oed.resources.frequencyiterator import FrequencyIterator
from lex.oed.resources.vitalstatistics import VitalStatisticsCache
import twominuteconfig

YEARS = list(range(1750, 2010, 10))

EUROPEAN = twominuteconfig.EUROPEAN_LANGUAGES
NONEUROPEAN = twominuteconfig.NONEUROPEAN_LANGUAGES
TOP_LEVELS = EUROPEAN + NONEUROPEAN


class LanguageFrequency(object):

    def __init__(self, **kwargs):
        self.out_dir = kwargs.get('out_dir')
        self.csv1 = os.path.join(self.out_dir, 'language_frequency.csv')
        self.csv2 = os.path.join(self.out_dir, 'language_entrycounts.csv')

    def store_values(self):
        def nullvalues():
            return {y: 0 for y in YEARS}
        languages = defaultdict(nullvalues)
        num_entries = defaultdict(nullvalues)
        vitalstats = VitalStatisticsCache()
        iterator = FrequencyIterator(message='Measuring language frequency')
        for entry in iterator.iterate():
            if (entry.has_frequency_table() and
                not ' ' in entry.lemma and
                not '-' in entry.lemma):
                freq_table = entry.frequency_table()
                ltext = vitalstats.find(entry.id, field='indirect_language') or 'unspecified'
                langs = ltext.split('/')
                for year in YEARS:
                    frequency = freq_table.frequency(year=year, interpolated=True)
                    for language in langs:
                        languages[language][year] += frequency
                        if entry.start < year:
                            num_entries[language][year] += 1

        rows1 = []
        rows1.append(['language', ] + YEARS)
        for lang in sorted(languages.keys()):
            row = [lang, ] + [languages[lang][y] for y in YEARS]
            rows1.append(row)

        rows2 = []
        rows2.append(['language', ] + YEARS)
        for lang in sorted(languages.keys()):
            row = [lang, ] + [num_entries[lang][y] for y in YEARS]
            rows2.append(row)

        with (open(self.csv1, 'w')) as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows1)

        with (open(self.csv2, 'w')) as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(rows2)

    def load_values(self):
        def load_file(file, function):
            data = defaultdict(dict)
            headers = None
            with (open(file, 'r')) as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if headers is None:
                        row.pop(0)
                        headers = [int(year) for year in row]
                    else:
                        lang = row.pop(0)
                        for year, val in zip(headers, row):
                            data[lang][year] = function(val)
            return data

        self.language_frequency = load_file(self.csv1, float)
        self.language_entrycounts = load_file(self.csv2, int)

        self.totals = dict()
        for year in YEARS:
            self.totals[year] = sum([self.language_frequency[l][year]
                                     for l in TOP_LEVELS
                                     if l in self.language_frequency])

    def add_non_european(self):
        sum_frequencies = dict()
        sum_counts = dict()
        for year in YEARS:
            sum_frequencies[year] = sum([self.language_frequency[l][year]
                                         for l in NONEUROPEAN])
            sum_counts[year] = sum([self.language_entrycounts[l][year]
                                    for l in NONEUROPEAN])
        self.language_frequency['Non-European'] = sum_frequencies
        self.language_entrycounts['Non-European'] = sum_counts

    def percentage(self, language, year):
        return ((100 / self.totals[year]) *
                self.language_frequency[language][year])
