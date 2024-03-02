import stanza
# from coords import chunker, create_conllu
from tqdm import tqdm
from stanza.utils.conll import CoNLL

models_path = './saved_models/'
config = {
        'processors': 'tokenize,pos,lemma,depparse',
        'lang': 'en',
        'use_gpu': True,
        'pos_model_path': models_path + 'en_combined-sud_charlm_tagger.pt',
        'depparse_model_path': models_path + 'en_combined-sud_charlm_parser.pt',
        'tokenize_pretokenized': False,
        'download_method': stanza.DownloadMethod.REUSE_RESOURCES
}
nlp = stanza.Pipeline(**config)

# texts, genre, year, source = chunker('split_news_2046.tsv')
# sents = []
# for k in tqdm(texts.keys()):
#         doc = nlp(texts[k])
#         for sent in doc.sentences:
#                 sent.coca_sent_id = str(k) + '-' + str(sent.index)
#                 sents.append(sent)
#
# create_conllu(sents, genre, year)

doc = nlp('John, Mary or her brother and Peter will come.')
CoNLL.write_doc2conll(doc, "files/output.conllu")

