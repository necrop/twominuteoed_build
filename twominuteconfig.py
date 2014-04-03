"""
twominuteconfig -- configuration for building 'Two Minute OED' data

@author: James McCracken
"""

import os

from lex import lexconfig

PIPELINE = (
    ('analyse_language_frequency', 0),
    ('list_entries', 0),
    ('prepare_json_files', 1),
)

BASE_DIR = os.path.join(lexconfig.OED_DIR, 'projects/twominuteoed')
SOURCE_DATA = os.path.join(BASE_DIR, 'source_data.csv')
LANGUAGE_COORDINATES = os.path.join(BASE_DIR, 'language_coordinates.csv')
LANGUAGE_FREQUENCY_DIR = os.path.join(BASE_DIR, 'language_frequency')
EXAMPLE_WORDS_LOG = os.path.join(BASE_DIR, 'two_minute_oed_example_words.xml')
DATAVIS_DIR = os.path.join(BASE_DIR, 'twominuteoed/data')

START_YEAR = 800
END_YEAR = 2010
ANIMATION_START = 1150
LANGUAGE_GROUPS = ('germanic', 'english', 'romance', 'latin', 'greek', 'other')

# Coordinates used to measure distance from UK (from Leicester, in fact)
CENTRAL_POINT = (-1.1, 52.6)

COLOURS = {'germanic': '#0000FF', 'romance': '#FF0000', 'latin': '#6600CC',
           'greek': '#3366CC', 'other': '#FFDE00', 'english': '#00CC00',
           'unspecified': '#E95D22'}

# left-latitude, right-latitude, bottom-longitude, top-longitude,
#  start-date, end-date
REGIONS = {'world': (-90, 90, -180, 180, 1000, 2001),
           'europe': (27, 67, -25, 50, 1000, 2001),
           'far east': (-18, 46, 33, 149, 1500, 2001), }

EUROPEAN_LANGUAGES = ('English', 'European languages',
                      'Other sources', 'unspecified')
NONEUROPEAN_LANGUAGES = ('Middle Eastern and Afro-Asiatic languages',
                         'Central and Eastern Asian languages',
                         'Australian Aboriginal',
                         'African languages',
                         'Creoles and pidgins',
                         'Austronesian',
                         'Native American languages',
                         'Indian subcontinent languages',
                         'Eskimo-Aleut')

# Extent to which years can be dithered, for different periods. These
#  values set upper limits for random amounts of dither.
DITHERS = list(reversed([(2010, 0), (1800, 2), (1700, 5), (1500, 10),
                         (1400, 20), (1200, 50), (1100, 70),
                         (950, 100), (500, 150)]))
