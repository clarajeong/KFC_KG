from cpnet_wiki import get_redirect_keyword
from dir_path import *
import random
import os
from format import *


root_path = os.path.abspath(os.sep)

def triplet_extract_ratio(id_, sources, ratio, pre_add = ""):
    not_important_triplet_list = list()
    important_triplet_list = list()
    for source in sources:
        name = source['name']
        triplet_file = open(root_path + qa_rootpath + f"wiki_files/{format_for_wiki(name)}_triplets.txt", "r")
        line = 0
        while True:
            triplet = triplet_file.readline()
            if not triplet: break
            line += 1
            if 'line' in source.keys() and line == source['line']:
                important_triplet_list.append(triplet)
            else:
                not_important_triplet_list.append(triplet)
    print(important_triplet_list)
    print()
    print(not_important_triplet_list)
    total_len = len(important_triplet_list) + len(not_important_triplet_list)
    important_len = len(important_triplet_list)
    random.shuffle(not_important_triplet_list)
    random.shuffle(important_triplet_list)

    filtered_triplets = random.choices(not_important_triplet_list, k = int(len(not_important_triplet_list) * ratio))
    
    print(range(1, total_len+1), important_len)
    
    answerline = random.sample(range(1, total_len+1), important_len)
    answerline.sort()
    for i, line in enumerate(answerline):
        filtered_triplets.insert(line - 1, important_triplet_list[i])
    
    f = open(f'{root_path + qa_rootpath}Question_triplet/{id_}_Qtriplet_ratio{int(ratio*100)}.txt', 'w')
    f.write(pre_add)
    for triplet in filtered_triplets:
        f.write(triplet)
    f.close()
    return answerline