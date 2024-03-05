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

doc = nlp('This magma often does not reach the surface but cools at depth.')
CoNLL.write_doc2conll(doc, "test_files/output.conllu")

# for sent in doc.sentences:
#     print('\\begin{dependency}[theme = simple]\n\t\\begin{deptext}\n\t\t',
#       *[f'{word.text}\&' if word.text != "." else f'{word.text}\\\\\n\t' for word in sent.words],
#       '\end{deptext}',
#       *[f'\n\t\depedge{{{word.head}}}{{{word.id}}}{{{word.deprel}}}' if word.deprel != "root" else f'\n\t\deproot{{{word.id}}}{{root}}' for word in sent.words],
#       '\n\end{dependency}')
