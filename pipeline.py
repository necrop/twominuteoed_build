"""
Pipeline -- runs processes for building data for the 'two-minute-OED' app.

@author: James McCracken
"""

import twominuteconfig


def dispatch():
    for function_name, status in twominuteconfig.PIPELINE:
        if status:
            print('=' * 30)
            print('Running "%s"...' % function_name)
            print('=' * 30)
            function = globals()[function_name]
            function()


def analyse_language_frequency():
    from processes.languagefrequency import LanguageFrequency
    analyser = LanguageFrequency(outDir=twominuteconfig.LANGUAGE_FREQUENCY_DIR,)
    analyser.store_values()


def list_entries():
    from processes.entrylister import EntryLister
    entry_lister = EntryLister(outFile=twominuteconfig.TIMELINE_DATA)
    entry_lister.store_values()


def prepare_json_files():
    from processes.datapreparation import DataPreparation
    data_prep = DataPreparation()
    data_prep.load_data(languageCoordinates=twominuteconfig.LANGUAGE_COORDINATES,
                        inFile=twominuteconfig.TIMELINE_DATA,
                        includeEnglish=True,
                        includeGermanic=True,)
    data_prep.write(out_dir=twominuteconfig.DATAVIS_DIR,
                    words='words.json',
                    examples='examples.json',
                    examples_log='two_min_oed_examples.txt',
                    languages='languages.json',
                    running_totals='running_totals.json',
                    increase_rate='increase_rates.json',)


if __name__ == '__main__':
    dispatch()
