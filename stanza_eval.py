import os
import argparse
import pandas
import stanza

import ud_vs_sud.conll18_ud_eval
from ud_vs_sud.mcnemar import evaluate_wrapper
from ud_vs_sud.combo_trainer import eval_on_file
from stanza.utils.conll import CoNLL


parser = argparse.ArgumentParser()
parser.add_argument('-c', action='store_true')
args = parser.parse_args()


def final_eval(score_dicts):
    scores = {}
    scores_sorted = {}
    scores_sorted["UAS"] = {}
    scores_sorted["LAS"] = {}
    scores_sorted["UAS"]["UD"] = []
    scores_sorted["UAS"]["SUD"] = []
    scores_sorted["UAS"]["statistic"] = []  # Mcnemar
    scores_sorted["UAS"]["p-value"] = []  # Mcnemar
    scores_sorted["LAS"]["UD"] = []
    scores_sorted["LAS"]["SUD"] = []
    scores_sorted["LAS"]["statistic"] = []  # Mcnemar
    scores_sorted["LAS"]["p-value"] = []  # Mcnemar
    name = []

    for score_dict in score_dicts:
        treebank_name, treebank_type = score_dict["base_name"].split("-")[:2]
        treebank_type = treebank_type.upper()
        if treebank_name in scores:
            scores[treebank_name][treebank_type] = score_dict["test"]
        else:
            scores[treebank_name] = {treebank_type: score_dict["test"]}

    for treebank_name in scores:
        name.append(treebank_name)
        ud_score = scores[treebank_name]["UD"]
        sud_score = scores[treebank_name]["SUD"]

        scores_sorted["UAS"]["UD"].append(ud_score.get("UAS").f1)
        scores_sorted["LAS"]["UD"].append(ud_score.get("LAS").f1)
        scores_sorted["UAS"]["SUD"].append(sud_score.get("UAS").f1)
        scores_sorted["LAS"]["SUD"].append(sud_score.get("LAS").f1)

        mcnemar_results = evaluate_wrapper(ud_score, sud_score)
        scores_sorted["UAS"]["statistic"].append(mcnemar_results["UAS"][0])
        scores_sorted["UAS"]["p-value"].append(mcnemar_results["UAS"][1])
        scores_sorted["LAS"]["statistic"].append(mcnemar_results["LAS"][0])
        scores_sorted["LAS"]["p-value"].append(mcnemar_results["LAS"][1])

    results_sorted = pandas.DataFrame.from_dict(
        {(i, j): scores_sorted[i][j] for i in scores_sorted.keys() for j in scores_sorted[i].keys()})
    results_sorted.index = name
    file_name_final = 'results_stanza_final_sorted.csv'
    results_sorted.to_csv(file_name_final)


def get_sents(test_filename):
    with open('eval/' + test_filename, mode='r', encoding='utf-8') as test:
        lines = test.readlines()
        out_sents = []
        for line in lines:
            if line.startswith('# text = '):
                sentence = line.replace('# text = ', '')
                out_sents.append(sentence + '\n')

    out_file = test_filename.replace('.conllu', '-sents.txt')
    with open('eval/' + out_file, mode='w', encoding='utf-8') as out_test:
        out_test.writelines(out_sents)
    return out_file


def get_conjs(test_filename):
    with open('eval/' + test_filename, mode='r', encoding='utf-8') as test:
        text = test.read()
        sents = text.split('\n\n')
        out_sents = ''
        for sent in sents:
            if '\tconj\t' in sent:
                out_sents += sent + '\n\n'

    out_file = test_filename.replace('.conllu', '-conj.conllu')
    with open('eval/' + out_file, mode='w', encoding='utf-8') as out_test:
        out_test.writelines(out_sents)
    return out_file


def generate_on_file(sents_file, scheme):
    with open('eval/' + sents_file, mode='r', encoding='utf-8') as file:
        sents = file.read()
    if scheme == 'sud':
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
        nlp = stanza.Pipeline(**config)
        print('predicting the test sentences using the sud model...')
        doc = nlp(sents)
        print('done!')
    else:
        config = {
            'processors': 'tokenize,pos,lemma,depparse',
            'lang': 'en',
            'use_gpu': True,
            'pos_model_path': './saved_models/en_compare-ud_charlm_tagger.pt',
            'depparse_model_path': './saved_models/en_compare-ud_charlm_parser.pt',
            'tokenize_pretokenized': False,
            'tokenize_no_ssplit': True,
            'download_method': stanza.DownloadMethod.REUSE_RESOURCES
        }
        nlp = stanza.Pipeline(**config)
        print('predicting the test sentences using the ud model...')
        doc = nlp(sents)
        print('done!')
    predicted = scheme + '_test_predicted.conllu'
    CoNLL.write_doc2conll(doc, 'eval/' + predicted)
    return predicted


ud_model_file = 'en_compare-ud_charlm_parser.pt'
sud_model_file = 'en_combined-sud_charlm_parser.pt'
sud_test_file = 'en_combined-ud-test.conllu'
ud_test_file = 'en_compare-ud-test.conllu'
if args.c:
    sud_test_file = get_conjs(sud_test_file)
    ud_test_file = get_conjs(ud_test_file)

sud = get_sents(sud_test_file)
ud = get_sents(ud_test_file)

sud_predicted = generate_on_file(sud, 'sud')
ud_predicted = generate_on_file(ud, 'ud')

sud_scores = eval_on_file('eval/' + sud_predicted, 'eval/' + sud_test_file)
ud_scores = eval_on_file('eval/' + ud_predicted, 'eval/' + ud_test_file)
score_dicts = [{'base_name': 'test-sud', 'test': sud_scores}, {'base_name': 'test-ud', 'test': ud_scores}]
final_eval(score_dicts)
