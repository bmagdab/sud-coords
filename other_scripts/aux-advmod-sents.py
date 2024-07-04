import re

with open('../files/export.conllu', mode='r', encoding='utf-8') as file:
    text = file.read()
    sents = text.split('\n\n')
    pattern = 0
    coordinations = 0
    for sent in sents:
        if re.search('\tconj\t', sent):
            conll = sent.split('\n')
            tokens = [tok.split('\t') for tok in conll if not tok.startswith('#')]
            coords = []
            for token in tokens:
                if token[7] == 'conj' and token[6] not in coords:
                    coords.append(token[6])
            print(coords)
            coordinations += len(coords)
            if re.search('\taux\t', sent) and re.search('\tadvmod\t', sent):
                for head in coords:
                    for dep in tokens:
                        if dep[6] == head and dep[7] == 'aux':
                            aux = dep
                        elif dep[6] == head and dep[7] == 'advmod':
                            advmod = dep
                    if advmod and aux and advmod[0] < head and aux[0] < head:
                        pattern += 1
    print(f'number of matches for the pattern: {pattern}')
    print(f'number of coordinations: {coordinations}')
    print(f'total number of sentences: {len(sents)}')
    print(f'percentage of coordinations with the pattern: {pattern/coordinations}')
