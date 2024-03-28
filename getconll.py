import stanza
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

# reading raw text from a file:
# with open('test_files/spoken_test.txt', mode='r') as spok:
#         text = spok.read()

# parsing without a file:
doc = nlp("The history book on the shelf is always repeating itself.")
CoNLL.write_doc2conll(doc, 'test_files/output.conllu')

# reading a parsed tree from a .conllu file
# doc = CoNLL.conll2doc('test_files/output.conllu')

# latex dependency tree:
# for sent in doc.sentences:
#     print('\\begin{dependency}[theme = simple]\n\t\\begin{deptext}\n\t\t',
#       *[f'{word.text}\&' if word.text != "." else f'{word.text}\\\\\n\t' for word in sent.words],
#       '\end{deptext}',
#       *[f'\n\t\depedge{{{word.head}}}{{{word.id}}}{{{word.deprel}}}' if word.deprel != "root" else f'\n\t\deproot{{{word.id}}}{{root}}' for word in sent.words],
#       '\n\end{dependency}')
