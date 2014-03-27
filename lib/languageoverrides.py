"""
LanguageOverrides

@author: James McCracken
"""

from lex.entryiterator import EntryIterator

BASE_TO_DIALECT = (('Spanish', 'South American Spanish', None),
                   ('Spanish', 'Central American Spanish', None),
                   ('Spanish', 'American Spanish', None),
                   ('Spanish', 'Spanish (originally American)', 'American Spanish',),
                   ('Spanish', 'Spanish (American)', 'American Spanish',),
                   ('Spanish', 'Mexican Spanish', None),
                   ('Spanish', 'Spanish (originally Mexican)', 'Mexican Spanish'),
                   ('Portuguese', 'Brazilian Portuguese', None),
                   ('Dutch', 'South African Dutch', None),)
CONTEXT_MARKERS = [('South American Spanish', ('Quechua',
                    'South America', 'S. America', 'Galibi',
                    'Peru', 'Argentin', 'Chile', 'Bolivia',
                    'Guyan', 'Guarani', 'Andes', 'Andean')),
                   ('Mexican Spanish', ('Mexic', 'Aztec',
                    'Nahuatl', 'Texas',)),
                   ('Central American Spanish', ('Maya', 'Taino',
                    'Carib', 'El Salvador',)),
                   ('North American Spanish', ('California',))]


class LanguageOverrides(object):

    def __init__(self):
        pass

    def list_language_overrides(self):
        """
        Return a dictionary for entries where the etymonLanguage given in
        the entry should be replaced by a new value,
        e.g. 'Spanish' -> 'Mexican Spanish'.

        Return value is a dict where keys are entry IDs and values are
        the replacement language.
        """
        dialect_words = {}
        iterator = EntryIterator(dictType='oed',
                                 verbosity=None,
                                 fixLigatures=True)
        for entry in iterator.iterate():
            language = entry.characteristic_first('etymonLanguage')
            if language:
                dialect = None
                language = language.split('/')[-1]
                if language in ('Spanish', 'Portuguese', 'Dutch'):
                    dialect = _find_dialect(language, entry)
                elif language in ('Germanic', 'West Germanic'):
                    dialect = _check_old_english(entry)
                if dialect:
                    dialect_words[entry.id] = dialect
        return dialect_words


def _find_dialect(language, entry):
    return_value = None
    etym_text = entry.etymology().as_text()[:50]
    for base, indicator, dialect in BASE_TO_DIALECT:
        if not dialect:
            dialect = indicator
        if language == base and indicator in etym_text:
            return_value = dialect
            break

    if return_value == 'American Spanish':
        etym_text = entry.etymology().as_text()[:100]
        def_text = entry.definition(length=100)
        refinement = (_deduce_dialect_from_context(etym_text) or
                      _deduce_dialect_from_context(def_text))
        if refinement:
            return_value = refinement

    return return_value


def _deduce_dialect_from_context(context):
    dialect = None
    for dialect, markers in CONTEXT_MARKERS:
        if any([marker in context for marker in markers]):
            return dialect


def _check_old_english(entry):
    return_value = None
    etym_text = entry.etymology().as_text()[:700]
    for dialect in ('Old English', 'Early Middle English',
                    'Northumbrian', 'Mercian', 'Anglian',
                    'Anglo-Saxon', 'Kentish'):
        if dialect in etym_text:
            return_value = 'West Germanic'
    for beginning in ('Cognate with', 'Compare ', 'Originally cognate'):
        if etym_text.startswith(beginning):
            return_value = 'West Germanic'
    # if return_value == 'West Germanic':
    #    return_value = 'Germanic_'
    return return_value

