"""
Coordinates -- Latitude/longitude coordinates for geographic regions

@author: James McCracken
"""

import csv
from collections import defaultdict
import random
import math
import bisect

import numpy

import twominuteconfig

DEFAULT_FILE = twominuteconfig.LANGUAGE_COORDINATES


class Coordinates(object):

    """
    Latitude/longitude coordinates for geographic regions
    representing languages.
    """

    data = defaultdict(dict)

    def __init__(self, **kwargs):
        self.in_file = kwargs.get('filepath') or DEFAULT_FILE
        if not Coordinates.data:
            self.load_values()

    def load_values(self):
        headers = None
        with (open(self.in_file, 'r')) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if headers is None:
                    headers = row
                else:
                    lang = _normalize(row.pop(0))
                    group = _normalize(row.pop(0))

                    # split coordinates into a series of 'squares', 4
                    #  coordinates per square
                    coords = [float(c.strip()) for c in row if c.strip()]
                    squares = [coords[i:i + 4] for i in range(0, len(coords), 4)]

                    areas = []
                    for square in squares:
                        areas.append({'latitude': (min(square[0], square[2]),
                                                   max(square[0], square[2])),
                                      'longitude': (min(square[1], square[3]),
                                                    max(square[1], square[3])), })

                    Coordinates.data[lang] = {
                        'group': group,
                        'areas': areas,
                        'wrg': WeightedRandomGenerator([_size(a) for a in areas])
                    }

    def is_listed(self, language):
        language = _normalize(language)
        if language in Coordinates.data:
            return True
        else:
            return False

    def group(self, language):
        language = _normalize(language)
        if not self.is_listed(language):
            return None
        else:
            return Coordinates.data[language]['group']

    def coords(self, language):
        language = _normalize(language)
        if not self.is_listed(language):
            return None
        else:
            return Coordinates.data[language]['areas']

    def centre(self, language):
        language = _normalize(language)
        if not self.is_listed(language):
            return None
        else:
            area = Coordinates.data[language]['areas'][0]
            return (numpy.mean(area['latitude']),
                    numpy.mean(area['longitude']),)

    center = centre

    def randomize(self, language, **kwargs):
        decimal_places = kwargs.get('decimalPlaces')
        language = _normalize(language)
        if not self.is_listed(language):
            return None
        else:
            # Pick one of the areas defined for this language
            if len(Coordinates.data[language]['areas']) == 1:
                chosen_area = Coordinates.data[language]['areas'][0]
            else:
                i = Coordinates.data[language]['wrg'].choose()
                chosen_area = Coordinates.data[language]['areas'][i]
            # Pick a random point within this area
            lat = random.uniform(chosen_area['latitude'][0],
                                 chosen_area['latitude'][1])
            lon = random.uniform(chosen_area['longitude'][0],
                                 chosen_area['longitude'][1])
            if not decimal_places:
                return (lat, lon)
            else:
                formatter = '%.' + str(decimal_places) + 'f'
                return (float(formatter % lat), float(formatter % lon))


class WeightedRandomGenerator(object):

    def __init__(self, weights):
        self.totals = []
        running_total = 0
        for weight in weights:
            running_total += weight
            self.totals.append(running_total)

    def choose(self):
        rand_num = random.random() * self.totals[-1]
        return bisect.bisect_right(self.totals, rand_num)


def _normalize(language):
    """
    Return a normalized version of a language name (to make
    """
    return language.lower().replace(' ', '').replace('-', '')


def _size(coordinates):
    """
    Return the size of a square defined by two pairs of lat/lon
    coordinates.
    """
    lat1 = coordinates['latitude'][0]
    lat2 = coordinates['latitude'][1]
    lon1 = coordinates['longitude'][0]
    lon2 = coordinates['longitude'][1]
    return abs(math.sin(lat1) - math.sin(lat2)) * abs(lon1 - lon2)
