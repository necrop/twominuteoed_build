"""
EntryLister

@author: James McCracken
"""

import math
import random
import csv
import itertools
from collections import defaultdict
import numpy

from lex.oed.resources.vitalstatistics import VitalStatisticsCache
from lex.oed.resources.frequencyiterator import FrequencyIterator

import twominuteconfig
from lib.coordinates import Coordinates
from lib.languageoverrides import LanguageOverrides


class EntryLister(object):

    def __init__(self, **kwargs):
        self.freq_dir = kwargs.get('frequencyDir')
        self.vs_dir = kwargs.get('vitalStatisticsDir')
        self.coords_file = kwargs.get('languageCoordinates')
        self.out_file = kwargs.get('outFile')

    def store_values(self):
        print('Loading coordinates...')
        coords = Coordinates(FILEPATH=self.coords_file)
        print('Checking language overrides...')
        overrides = LanguageOverrides().list_language_overrides()
        print('Loading OED vital statistics...')
        vitalstats = VitalStatisticsCache(vitalStatisticsDir=self.vs_dir)

        entries = []
        iterator = FrequencyIterator(message='Listing entries')
        for entry in iterator.iterate():
            if (entry.has_frequency_table() and
                not ' ' in entry.lemma and
                not '-' in entry.lemma):
                language_breadcrumb = vitalstats.find(entry.id, field='language')
                year = vitalstats.find(entry.id, field='first_date') or 0

                languages = []
                if language_breadcrumb is not None:
                    languages = [l for l in language_breadcrumb.split('/')
                                 if coords.is_listed(l)
                                 or l == 'English']
                else:
                    languages = ['unspecified', ]
                if entry.id in overrides:
                    languages = [overrides[entry.id], ]

                if languages:
                    # pick the most granular level (e.g. 'Icelandic' in
                    #  preference to 'Germanic')
                    language = languages[-1]
                    # Find frequency for this word
                    freq_table = entry.frequency_table()
                    frequency = freq_table.frequency(period='modern')
                    band = freq_table.band(period='modern')
                    row = (entry.lemma,
                           entry.id,
                           year,
                           frequency,
                           band,
                           language)
                    entries.append(row)

        entries = sorted(entries, key=lambda entry: entry[2])

        with (open(self.out_file, 'w')) as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(entries)


class EntryCache(object):

    def __init__(self, **kwargs):
        self.coords_file = kwargs.get('languageCoordinates')
        self.in_file = kwargs.get('inFile')
        self.include_english = kwargs.get('includeEnglish', False)
        self.include_germanic = kwargs.get('includeGermanic', False)
        self.include_unspecified = kwargs.get('includeUnspecified', False)
        self.entries = list()
        self.cumulations = dict()
        Coordinates(FILEPATH=self.coords_file)

    def load_data(self):
        self.entries = []
        with (open(self.in_file, 'r')) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                entry = Entry(row)
                if entry.year < 500:
                    pass
                elif (not self.include_english and
                      entry.language == 'English'):
                    pass
                elif (not self.include_unspecified and
                      entry.language == 'unspecified'):
                    pass
                elif (not self.include_germanic and
                      entry.language in ('Germanic', 'West Germanic',)):
                    pass
                else:
                    self.entries.append(entry)

    def dither(self):
        if not self.entries:
            self.load_data()
        self.entries = sorted(self.entries, key=lambda e: e.dithered_year())

    def group_by_year(self):
        self.dither()
        return [(k, list(g)) for k, g in itertools.groupby(
                self.entries, lambda e: e.dithered_year())]

    def cumulate(self, year):
        if not self.cumulations:
            totals = defaultdict(lambda: 0)
            for entry in self.entries:
                totals[entry.language_group()] += entry.frequency
                self.cumulations[entry.dithered_year()] = \
                    {key: value for key, value in totals.items()}
        if year in self.cumulations:
            return self.cumulations[year]
        else:
            for year2 in range(year, year - 100, -1):
                if year2 in self.cumulations:
                    return self.cumulations[year2]
        return {}

    def cumulative_total(self, year):
        return sum(self.cumulate(year).values())


def _compute_dither_range(dithers, end_year):
    years = range(500, end_year + 1)
    values = numpy.interp(years, [d[0] for d in dithers], [d[1] for d in dithers])
    return {y: int(v) for y, v in zip(years, values)}


class Entry(object):

    coords = Coordinates()
    dither_range = _compute_dither_range(twominuteconfig.DITHERS,
                                         twominuteconfig.END_YEAR)

    def __init__(self, row):
        (self.lemma, self.id, self.year, self.frequency,
         self.band, self.language) = row
        # self.lemma = self.lemma.decode('utf8')
        # self.language = self.language.decode('utf8')
        self.year = int(self.year)
        self.band = int(self.band)
        self.frequency = float(self.frequency)

    def dithered_year(self):
        try:
            return self.__dithered_year
        except AttributeError:
            if self.year in self.dither_range:
                dither_range = self.dither_range[self.year]
                if dither_range < 1:
                    self.__dithered_year = self.year
                else:
                    self.__dithered_year = int(
                        self.year - (dither_range / 2) +
                        random.randint(0, dither_range))
            else:
                self.__dithered_year = random.randint(600, 700)

            return self.__dithered_year

    def coordinates(self):
        """
        Return a tuple containing (latitude, longitude)
        """
        try:
            return self.__coordinates
        except AttributeError:
            self.__coordinates = Entry.coords.randomize(self.language)
            return self.__coordinates

    def latitude(self):
        if self.coordinates() is None:
            return None
        else:
            return self.coordinates()[0]

    def longitude(self):
        if self.coordinates() is None:
            return None
        else:
            return self.coordinates()[1]

    def language_group(self):
        if self.language == 'English':
            return 'english'
        elif self.language == 'unspecified':
            return 'unspecified'
        else:
            return Entry.coords.group(self.language)

    def language_group_initial(self):
        if self.language_group().lower() == 'greek':
            return 'k'
        else:
            return self.language_group().lower()[0]

    def distance(self, longitude, latitude):
        """
        Measure the distance (on the earth's surface) between this
        point and another point. The distance returned is relative to
        Earth's radius; to get the distance in miles, multiply by 3960.

        Returns float
        """
        delta_lat = math.radians(latitude - self.latitude())
        delta_lon = math.radians(longitude - self.longitude())
        a = (math.sin(delta_lat / 2) * math.sin(delta_lat / 2) +
             math.cos(math.radians(self.latitude())) *
             math.cos(math.radians(latitude)) *
             math.sin(delta_lon / 2) *
             math.sin(delta_lon / 2))
        distance = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return distance


