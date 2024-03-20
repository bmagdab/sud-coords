import re

import numpy as np

import syll
import stanza
from types import NoneType


config = {
        'processors': 'tokenize,pos,lemma,depparse',
        'lang': 'en',
        'use_gpu': True,
        'pos_model_path': './saved_models/en_combined-sud_charlm_tagger.pt',
        'depparse_model_path': './saved_models/en_combined-sud_charlm_parser.pt',
        'tokenize_pretokenized': False,
        'tokenize_no_ssplit': True,
        'download_method': stanza.DownloadMethod.REUSE_RESOURCES
}
nlp = stanza.Pipeline(**config)  # Initialize the pipeline using a configuration dict


def dep_children(sentence):
    """
    for every word in a given sentence finds a list of IDs of that words dependents
    :param sentence: a Stanza object
    :return: nothing
    """
    for word in sentence.words:
        word.children = []
        for w in sentence.words:
            if w.head == word.id:
                word.children.append(w.id)


def word_indexer(sentence):
    """
    i don't think i need this? maybe if there are double spaces in tsv files but i can deal with that
    :param sentence:
    :return:
    """
    sent_text = sentence.text
    current_id = 0
    for word in sentence.words:
        match = re.search(re.escape(word.text), sent_text)
        word.start = match.start() + current_id
        word.end = match.end() + current_id
        sent_text = sent_text[match.end():]
        current_id = match.end() + current_id


def middle_conjuncts(coord, sentence):
    conj_list = coord['other_conjuncts']
    conjunct_lengths = []
    for head in conj_list:
        conjunct = []
        for child in sentence.words[head-1].children:
            if sentence.words[child-1].deprel not in ['cc', 'punct'] \
                    and sentence.words[child-1] != coord['R']\
                    and child not in conj_list:
                conjunct.append(child)

        keep_looking = True
        while keep_looking and conjunct:
            for id in conjunct:
                for i in sentence.words[id - 1].children:
                    if sentence.words[i - 1].deprel != 'conj':
                        conjunct.append(i)
                else:
                    keep_looking = False
        conjunct.append(head)
        conjunct.sort()

        # removes some of the punctuation from the beginning of the conjunct
        while sentence.words[min(conjunct) - 1].text in [',', ';', '-', ':', '--']:
            conjunct.remove(min(conjunct))

        txt = sentence.text[sentence.words[min(conjunct) - 1].start - sentence.words[0].start:
                            sentence.words[max(conjunct) - 1].end - sentence.words[0].start]

        to_rem = [] # removing punctuation, I want only words in this
        for id in conjunct:
            if sentence.words[id - 1].deprel == 'punct':
                to_rem.append(id)

        for id in reversed(to_rem):
            conjunct.remove(id)

        conjunct_lengths.append((len(conjunct), len(txt)))

    return conjunct_lengths


def coord_info(crd, sent, conj):
    """
    collects information on elements of a coordination: text of the conjunct, number of words, tokens and syllables
    :param crd: coordination (a dictionary containing the left and right elements of coordination, its head and the conjunct, if there is one)
    :param sent: sentence (Stanza object) where the coordination was found
    :param conj: which element of a coordination is to be considered (takes values "L" or "R")
    :param other_ids: a list of word IDs, that belong to the opposite element of the coordination
    :return: a list of word IDs, that belong to the element of the coordination that was specified by the conj parameter
    """
    txt_ids = []

    for id in crd[conj].children:
        if (id not in crd['other_conjuncts'] and sent.words[id - 1].deprel != 'cc'
                and (id < crd['R'].id)*(conj == 'L')+(conj == 'R')):

            if not isinstance(sent.words[id - 1].feats, NoneType) and 'Shared=Yes' in sent.words[id - 1].feats:
                continue
            elif not isinstance(sent.words[id - 1].feats, NoneType) and 'Shared=No' in sent.words[id - 1].feats:
                txt_ids.append(id)
                continue

            if ((id < crd[conj].id)*(conj == 'L')+(id > crd[conj].id)*(conj == 'R') and
                    re.match('compound', sent.words[id - 1].deprel)):
                txt_ids.append(id)
                continue

            elif (id < crd['L'].id)*(conj == 'L')+(id > crd['R'].id)*(conj == 'R') and \
                    sent.words[id - 1].deprel != 'conj@emb':
                for c in [crd['L'].id]*(conj == 'R')+crd['other_conjuncts']+[crd['R'].id]*(conj == 'L'):
                    for c_child in sent.words[c - 1].children:
                        if sent.words[c_child - 1].deprel == sent.words[id - 1].deprel:
                            txt_ids.append(id)
                            break
                    if id in txt_ids:
                        break

            else:
                # all children of the head appearing between the head and other elements of the coordination are part of the conjunct
                txt_ids.append(id)

    # the loop below looks through words already included in the conjunct and adds their children, repeats until there
    # are no more words to be added
    keep_looking = True
    while keep_looking and txt_ids:
        for id in txt_ids:
            for i in sent.words[id - 1].children:
                txt_ids.append(i)
            else:
                keep_looking = False
    txt_ids.append(crd[conj].id)
    txt_ids.sort()

    # removes some of the punctuation from the beginning of the conjunct
    while (sent.words[min(txt_ids)-1].text in [',', ';', '-', ':', '--']
           or (sent.words[min(txt_ids)-1].deprel == 'cc' and sent.words[min(txt_ids)-1] not in [crd['L'], crd['R']])):
        txt_ids.remove(min(txt_ids))

    words = 0
    tokens = 0
    for id in range(min(txt_ids), max(txt_ids) + 1):
        tokens += 1
        if sent.words[id - 1].deprel != 'punct':
            words += 1

    txt = sent.text[sent.words[min(txt_ids) - 1].start - sent.words[0].start:sent.words[max(txt_ids) - 1].end - sent.words[0].start]

    syllables = 0
    for w in txt.split():
        syllables += syll.count_word(w)

    crd[conj+'conj'] = txt
    crd[conj+'words'] = words
    crd[conj+'tokens'] = tokens
    crd[conj+'syl'] = syllables


def coord_finder(sentence, conjunct, embedded=False):
    """
    finds all the conjuncts in the coordination
    :param sentence: stanza sentence object, the sentence that contains the currently investigated coordination
    :param conjunct: stanza word object, the last known conjunct in the investigated coordination
    :param embedded: boolean, limits how far the function goes in searching if the coordination is embedded in another
    :return:
    """
    conjuncts = [conjunct.id]
    for child in conjunct.children:
        if not embedded and 'conj' in sentence.words[child-1].deprel:
            conjuncts.append(child)
            conjuncts = conjuncts + coord_finder(sentence, sentence.words[child-1])
        elif embedded and 'conj@emb' == sentence.words[child-1].deprel:
            conjuncts.append(child)
            conjuncts = conjuncts + coord_finder(sentence, sentence.words[child - 1], embedded=True)
    return conjuncts


def extract_coords(doc, marker='', conll_list=None, id_list=None):
    """
    finds coordinations in a given text, creates a conllu file containing every sentence with a found coordination
    :param doc: stanza document object with parsed sentences
    :param marker: marker of the parsed text
    :param conll_list: list for sentences, to later create a conllu file corresponding to the table of coordinations
    :param id_list: list of ids of sentences in the document
    :return: list of dictionaries representing coordinations
    """
    if marker == '' and not conll_list and not id_list:
        preparsed = True
        conll_list = []
        id_list = []
    else:
        preparsed = False

    coordinations = []
    for sent in doc.sentences:
        if not preparsed:
            index = id_list[marker].pop()
        # updating sentence count so that it corresponds to the sentence ids in the source .tsv file
        dep_children(sent)
        word_indexer(sent)

        coords = []
        embedded = []
        # every word that has a conj dependency becomes a key in the coords dictionary, its values are all words that are
        # connected to the key with a conj dependency
        for dep in sent.dependencies:
            if re.fullmatch('conj', dep[1]):
                coords.append(list(dict.fromkeys([dep[0].id] + coord_finder(sent, dep[2]))))
            elif re.fullmatch('conj@emb', dep[1]):
                embedded.append(list(dict.fromkeys([dep[0].id] + coord_finder(sent, dep[2], embedded=True))))

        to_remove = []
        for i, coord in enumerate(coords):
            for coord2 in coords:
                if set(coord).intersection(set(coord2)) == set(coord) and coord != coord2:
                    to_remove.append(i)

        to_remove = list(dict.fromkeys(to_remove))
        for r in reversed(to_remove):
            coords.remove(coords[r])

        for emb in embedded:
            for i, coord in enumerate(coords):
                if set(emb).intersection(set(coord)) == set(emb):
                    coords[i] = list(np.concatenate((np.setdiff1d(coord, emb[1:]), np.setdiff1d(emb[1:], coord))))

        coords += embedded

        if not preparsed and coords:
            # if there are any valid conj dependencies in a sentence, it will be included in the .conllu file
            # a sentence id including the @@ marker from COCA source files is assigned and will be both in the .conllu
            # and .csv file
            sent.sent_id = str(marker) + '-' + str(index)
            conll_list.append(sent)

        # this loop writes down information about every coordination based on the list of elements of a coordination
        for crd in coords:
            if len(crd) > 1:
                crd.sort()
                coord = {'L': sent.words[min(crd) - 1], 'R': sent.words[max(crd) - 1]}
                crd.pop(0)
                crd.pop(-1)
                coord['other_conjuncts'] = crd
                if coord['L'].head != 0:
                    coord['gov'] = sent.words[coord['L'].head - 1]
                for child in coord['R'].children:
                    if sent.words[child-1].deprel == 'cc':
                        coord['conj'] = sent.words[child-1]
                        break
                coord_info(coord, sent, 'R')
                coord_info(coord, sent, 'L')
                coord['conj_lengths'] = [(coord['Lwords'], len(coord['Lconj']))] + middle_conjuncts(coord, sent) + \
                                        [(coord['Rwords'], len(coord['Rconj']))]
                coord['sentence'] = sent.text
                coord['sent_id'] = sent.sent_id
                coordinations.append(coord)

    return coordinations
