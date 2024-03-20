import re
import os
import csv


def create_conllu(sent_list, genre, year):
    """
    creates a conllu file with sentences with coordinations, with every tree comes the text of the sentence and the same
    sentence id that is in the csv file
    this function is based on doc2conll from stanza.utils.conll, described as deprecated and to be removed
    :param sent_list: list of sentences (stanza object) that had a coordination in them
    :param file_path: name for the conllu file
    """
    doc_conll = []
    for sentence in sent_list:
        sent_conll = []
        for com in sentence.comments:
            if re.match('# sent_id = ', com):
                sent_conll.append('# sent_id = ' + sentence.sent_id)
            else:
                sent_conll.append(com)
        for token in sentence.tokens:
            sent_conll.extend(token.to_conll_text().split('\n'))
        doc_conll.append(sent_conll)

    path = os.getcwd() + '/out_files/sud_' + str(genre) + '_' + str(year) + '.conllu'
    with open(path, mode='w', encoding='utf-8') as conll_file:
        for sent in doc_conll:
            for line in sent:
                conll_file.write(line + '\n')
            conll_file.write('\n')


def create_csv(crd_list, genre, year, source):
    """
    creates a .csv table where every row has information about one coordination
    :param crd_list: list of dictionaries, each dictionary represents a coordination
    :param genre: genre of the parsed file, information included in the filename and in the table
    :param year: year in which the parsed text was published, included in the filename and the table
    :param source: name of the source file
    :return: nothing
    """
    if len(year) == 1:
        year = '0' + year
    path = os.getcwd() + '/out_files/sud_' + str(genre) + '_' + str(year) + '.csv'
    with open(path, mode='w', newline="", encoding='utf-8-sig') as outfile:
        writer = csv.writer(outfile)
        col_names = ['governor.position', 'governor.word', 'governor.tag', 'governor.pos', 'governor.ms',
                     'conjunction.word', 'conjunction.tag', 'conjunction.pos', 'conjunction.ms', 'no.conjuncts',
                     'L.conjunct', 'L.dep.label', 'L.head.word', 'L.head.tag', 'L.head.pos', 'L.head.ms', 'L.words',
                     'L.tokens', 'L.syllables', 'L.chars', 'R.conjunct', 'R.dep.label', 'R.head.word', 'R.head.tag',
                     'R.head.pos', 'R.head.ms', 'R.words', 'R.tokens', 'R.syllables', 'R.chars', 'all.conj.lengths', 'sentence', 'sent.id',
                     'genre', 'converted.from.file']
        writer.writerow(col_names)

        for coord in crd_list:
            writer.writerow(['0' if 'gov' not in coord.keys() else 'L' if coord['L'].id > coord['gov'].id else 'R',     # governor.position
                             str(coord['gov'].text) if 'gov' in coord.keys() else '',                                   # governor.word
                             coord['gov'].xpos if 'gov' in coord.keys() else '',                                        # governor.tag
                             coord['gov'].upos if 'gov' in coord.keys() else '',                                        # governor.pos
                             coord['gov'].feats if 'gov' in coord.keys() else '',                                       # governor.ms
                             str(coord['conj'].text) if 'conj' in coord.keys() else '',                                 # conjunction.word
                             coord['conj'].xpos if 'conj' in coord.keys() else '',                                      # conjunction.tag
                             coord['conj'].upos if 'conj' in coord.keys() else '',                                      # conjunction.pos
                             coord['conj'].feats if 'conj' in coord.keys() else '',                                     # conjunction.ms
                             int(2 + len(coord['other_conjuncts'])),                                                    # no.conjuncts
                             str(coord['Lconj']),                                                                       # L.conjunct
                             coord['L'].deprel,                                                                         # L.dep.label
                             str(coord['L'].text),                                                                      # L.head.word
                             coord['L'].xpos,                                                                           # L.head.tag
                             coord['L'].upos,                                                                           # L.head.pos
                             coord['L'].feats,                                                                          # L.head.ms
                             int(coord['Lwords']),                                                                      # L.words
                             int(coord['Ltokens']),                                                                     # L.tokens
                             int(coord['Lsyl']),                                                                        # L.syllables
                             len(coord['Lconj']),                                                                       # L.chars
                             str(coord['Rconj']),                                                                       # R.conjunct
                             coord['R'].deprel,                                                                         # R.dep.label
                             str(coord['R'].text),                                                                      # R.head.word
                             coord['R'].xpos,                                                                           # R.head.tag
                             coord['R'].upos,                                                                           # R.head.pos
                             coord['R'].feats,                                                                          # R.head.ms
                             int(coord['Rwords']),                                                                      # R.words
                             int(coord['Rtokens']),                                                                     # R.tokens
                             int(coord['Rsyl']),                                                                        # R.syllables
                             len(coord['Rconj']),                                                                       # R.chars
                             coord['conj_lengths'],                                                                     # all.conj.lengths
                             str(coord['sentence']),                                                                    # sentence
                             coord['sent_id'],                                                                          # sent.id
                             genre,                                                                                     # genre
                             source])                                                                                   # converted.from.file
