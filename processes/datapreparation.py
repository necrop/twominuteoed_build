"""
DataPreparation -- Prepare JSON data files to be read by the D3 app

@author: James McCracken
"""

import os
import random
from collections import defaultdict
import json
import numpy

import twominuteconfig
from processes.entrylister import EntryCache
from lib.coordinates import Coordinates

ANIMATION_START = twominuteconfig.ANIMATION_START
START_YEAR = twominuteconfig.START_YEAR
END_YEAR = twominuteconfig.END_YEAR
LANGUAGE_GROUPS = twominuteconfig.LANGUAGE_GROUPS
CENTRAL_POINT = twominuteconfig.CENTRAL_POINT


class DataPreparation(object):

    """
    Prepare JSON data files to be read by the D3 app.
    """

    def __init__(self):
        self.entry_cache = None
        self.groups = None

    def load_data(self, **kwargs):
        self.entry_cache = EntryCache(**kwargs)
        self.groups = self.entry_cache.group_by_year()

    def write(self, **kwargs):
        out_dir = kwargs.get('out_dir')
        files = {k: os.path.join(out_dir, v) for k, v in
            kwargs.items() if k != 'out_dir'}
        language_index = self._write_language_file(files['languages'])
        self._write_running_totals_file(files['running_totals'])
        self._write_increase_rate_file(files['increase_rate'])

        entries = defaultdict(list)
        examples = {}
        for year, entry_list in self.groups:
            if year >= START_YEAR and year <= END_YEAR:
                for entry in entry_list:
                    entry.coordinates()
                entry_list = _winnow(entry_list)
                examples[year] = list(_choose_examples(entry_list, year))
                for entry in entry_list:
                    freq = float('%.1g' % entry.frequency)
                    if freq >= 1:
                        freq = int(freq)
                    freq = max(freq, 0.0001)
                    entries[year].append((
                        entry.id,
                        entry.lemma,
                        entry.band,
                        freq,
                        language_index[entry.language],
                    ))

        _write_words_file(entries, files['words'])
        _write_examples_file(examples, files['examples'], files['examples_log'])

    def _write_running_totals_file(self, out_file):
        running_totals = {499: {group: 0 for group in LANGUAGE_GROUPS}}
        for year in range(500, END_YEAR + 1):
            # Find the list of entries for this year
            entries = []
            for year2, elist in self.groups:
                if year2 == year:
                    entries = elist
                    break

            # Initially, set the running totals to be the same as last year's
            running_totals[year] = {}
            for group in LANGUAGE_GROUPS:
                running_totals[year][group] = running_totals[year - 1][group]
            # ...then add on to the counts for this year
            for entry in [e for e in entries
                          if e.language_group() in LANGUAGE_GROUPS]:
                running_totals[year][entry.language_group()] += entry.frequency

        minified = {}
        for year, vals in running_totals.items():
            if year >= START_YEAR:
                this_year = []
                for group in LANGUAGE_GROUPS:
                    this_year.append(int(vals[group]))
                minified[year] = this_year

        with open(out_file, 'w') as filehandle:
            json.dump(minified, filehandle)

    def _write_increase_rate_file(self, out_file):
        rates = defaultdict(int)
        for year in range(500, END_YEAR + 1):
            span = ((int(year / 20)) * 20) + 10
            entries = []
            for year2, entry_list in self.groups:
                if year2 == year:
                    entries = entry_list
                    break
            rates[span] += sum([e.frequency for e in entries])

        rates = [(k, v / 20) for k, v in rates.items()]
        rates.sort(key=lambda a: a[0])

        years = range(START_YEAR, END_YEAR + 1)
        freqs = numpy.interp(years,
                             [r[0] for r in rates],
                             [r[1] for r in rates])
        rates = {year2: int(f) for year2, f in zip(years, freqs)}

        with open(out_file, 'w') as filehandle:
            json.dump(rates, filehandle)

    def _write_language_file(self, out_file):
        coords = Coordinates()
        langs = defaultdict(lambda: {'count': 0, 'group': None})
        for year, entry_list in self.groups:
            if year >= START_YEAR and year <= END_YEAR:
                entry_list = list(entry_list)
                for entry in entry_list:
                    langs[entry.language]['count'] += 1
                    langs[entry.language]['group'] = entry.language_group_initial()

        for language in langs.keys():
            # Number of possible points (between 3 and 30, depending on
            #  the frequency of the language)
            num_points = int(langs[language]['count'] / 5)
            num_points = max(4, min(num_points, 30))
            # Select a bunch of random points within the language's geo region
            langs[language]['coords'] = [coords.randomize(
                language, decimalPlaces=2) for i in range(num_points)]

        langs2 = []
        for language, vals in langs.items():
            langs2.append({'l': language,
                           'g': vals['group'],
                           'c': vals['coords']})
        with open(out_file, 'w') as filehandle:
            json.dump(langs2, filehandle)

        language_index = {row['l']: i for i, row in enumerate(langs2)}
        return language_index


def _winnow(entries):
    def weighted_choice_sub(weights):
        random_num = random.random() * sum(weights)
        for i, weight in enumerate(weights):
            random_num -= weight
            if random_num < 0:
                return i

    # Remove words with English etymology
    entries = [e for e in entries if e.language not in
               ('English', 'Germanic', 'West Germanic')]

    entries = _remove_vulgar(entries)

    # Sort by distance from UK (from Leicester, in fact)
    entries.sort(key=lambda p: p.distance(CENTRAL_POINT[0], CENTRAL_POINT[1]))

    # Now winnow down to 50 entries at the most, using weighted random choice
    #   so that points further from Leicester have less chance of being
    #   winnowed out.
    # (Hopefully, this means that entries will tend to be winnowed
    #   from the indistinct morass of French and Germanic entries).
    while len(entries) > 50:
        weights = [len(entries) - i + 3 for i, e in enumerate(entries)]
        index = weighted_choice_sub(weights)
        entries.pop(index)
    entries.sort(key=lambda e: e.frequency, reverse=True)
    return entries


def _choose_examples(entries, year):
    """
    Select items from the list of entries that represent the
    northernmost, southernmost, easternmost, and westernmost,
    plus the largest, plus a random one.

    Returns a set, to prevent duplication.
    """
    if year <= ANIMATION_START:
        return set()

    if entries:
        # Filter to remove high-frequency stuff
        filtered = entries[:]
        filtered.sort(key=lambda e: e.frequency, reverse=True)
        hifreq = []
        while len(filtered) > 10 and len(hifreq) < 10:
            hifreq.append(filtered.pop(0))

        # hifreq = max(entries, key=lambda e: e.frequency)
        nth = max(filtered, key=lambda e: e.latitude())
        sth = min(filtered, key=lambda e: e.latitude())
        west = max(filtered, key=lambda e: e.longitude())
        east = min(filtered, key=lambda e: e.longitude())
        rnd1 = random.choice(filtered)  # throw in a random example
        rnd2 = random.choice(filtered)  # throw in a random example
        choices = set([(e.id, e.lemma) for e in (nth, sth, east, west,
                                                 rnd1, rnd2)])
        if len(choices) < 6:
            extra = random.choice(filtered)
            choices.add((extra.id, extra.lemma,))
        return choices
    else:
        return set()


def _write_words_file(entries, out_file):
    for year in range(ANIMATION_START, END_YEAR + 1):
        if year not in entries:
            entries[year] = []
    with open(out_file, 'w') as filehandle:
        json.dump(entries, filehandle)


def _write_examples_file(examples, out_file, log_file):
    for year in range(ANIMATION_START, END_YEAR + 1):
        if year not in examples:
            examples[year] = []
    with open(out_file, 'w') as filehandle:
        json.dump(examples, filehandle)

    with open(log_file, 'w') as filehandle:
        for year in range(ANIMATION_START, END_YEAR + 1):
            for entry in examples[year]:
                filehandle.write('%s\t%s\n' % (entry[0], entry[1]))


def _remove_vulgar(entries):
    swears = ('shit', 'fuck', 'bugger', 'cunt', 'piss',)
    entries2 = []
    for e in entries:
        if not any ([swear in e.lemma for swear in swears]):
            entries2.append(e)
    return entries2
