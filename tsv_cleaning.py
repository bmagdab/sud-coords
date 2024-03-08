from collections import deque

# with open('files/split_news_1993.tsv', mode='r+') as file:
#     lines = file.readlines()
#     print(lines[179009:179100])

with open('files/split_news_1993.tsv', mode='r+') as file:
    lines = file.readlines()
    dirt = ['\t in his pockets\t\t\t\t\n']
    out = deque()
    for line in lines:
        if line not in dirt:
            out.append(line)

with open('files/split_news_1993.tsv', mode='w') as file:
    file.writelines(out)

# with open('files/split_fic_1999.tsv', mode='r+') as file:
#     lines = file.readlines()
#     dirt = ['\t Weirs False\t\t\t\t\n']
#     out = deque()
#     for line in lines:
#         if line not in dirt:
#             out.append(line)
#
# with open('files/split_fic_1999.tsv', mode='w') as file:
#     file.writelines(out)

# with open('files/split_fic_1998.tsv', mode='r+') as file:
#     lines = file.readlines()
#     dirt = ['\t Dentist  Pearly gray\t\t\t\t\n',
#             '\t : Christian Fiction Section\t\t\t\t\n',
#             '\t the preceding three paragraphs .\t\t\t\t\n',
#             '\t Index Sources # Section : STORY\t\t\t\t\n']
#     out = deque()
#     for line in lines:
#         if line not in dirt:
#             out.append(line)
#
# with open('files/split_fic_1998.tsv', mode='w') as file:
#     file.writelines(out)

# with open('files/split_fic_1997.tsv', mode='r+') as file:
#     lines = file.readlines()
#     dirt = ['\t - The 1004491\t\t\t\t\n']
#     out = deque()
#     for line in lines:
#         if line not in dirt:
#             out.append(line)
#
# with open('files/split_fic_1997.tsv', mode='w') as file:
#     file.writelines(out)

# with open('files/split_fic_1996.tsv', mode='r+') as file:
#     lines = file.readlines()
#     dirt = ['\t TO THE LADIES AID\t\t\t\t\n',
#             '\t flute , one harmonica , walking side-by-side and playing different songs , the flute something Renaissance-like and polyphonic , the harmonica something more like jazz or German atonal .\t\t\t\t\n',
#             '\t Rosen THE MESSIAH #\t\t\t\t\n',
#             "\t V. LOS NINOS CHILDREN 'S FURNITURE STORE AND THE CONTINENTAL ARCADE COMPANY EPILOGUE # Section : WILD KINGDOM PROLOGUE\t\t\t\t\n"]
#     out = deque()
#     for line in lines:
#         if line not in dirt:
#             out.append(line)
#
# with open('files/split_fic_1996.tsv', mode='w') as file:
#     file.writelines(out)

# with open('files/split_fic_1995.tsv', mode='r+') as file:
#     lines = file.readlines()
#     dirt = ['\t , Dickens , Orwell . . . and Me II\t\t\t\t\n', '\t : : C:D #\t\t\t\t\n']
#     out = deque()
#     for line in lines:
#         if line not in dirt:
#             out.append(line)
#
# with open('files/split_fic_1995.tsv', mode='w') as file:
#     file.writelines(out)

# with open('files/split_fic_1994.tsv', mode='r+') as file:
#     lines = file.readlines()
#     dirt = ['\t with remembrances of past triflings with the truth , and heads for Wal-Mart to buy a larger size .\t\t\t\t\n']
#     out = deque()
#     for line in lines:
#         if line not in dirt:
#             out.append(line)
#
# with open('files/split_fic_1994.tsv', mode='w') as file:
#     file.writelines(out)

# with open('files/split_fic_1993.tsv', mode='r+') as file:
#     lines = file.readlines()
#     dirt = ['\t : a Russian folk tale\n', '\t\t\t\t\n', '\t Review ; Summer 1993 ; 36 , 4 ; Research Library pg .\n']
#     out = deque()
#     for line in lines:
#         if line not in dirt:
#             out.append(line)
#
# with open('files/split_fic_1993.tsv', mode='w') as file:
#     file.writelines(out)
