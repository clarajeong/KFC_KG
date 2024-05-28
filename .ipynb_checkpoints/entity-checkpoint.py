# Information Extraction
import nltk
from nltk.tokenize import word_tokenize
from nltk.tag import pos_tag
from nltk.corpus import stopwords
import inflect
import spacy
from nltk.tag import StanfordNERTagger
from nltk.tokenize import word_tokenize
import os
import requests
import random
import string
from bs4 import BeautifulSoup

import tqdm
from tqdm import tqdm

import requests
import os
import time

from word2number import w2n
import re
import json


from dir_path import *

from cpnet_wiki import format_for_cpnet
from cpnet_wiki import get_node
from cpnet_wiki import check_goodentity
from cpnet_wiki import get_redirect_keyword
from gpt_query import inference_azure
from hash import hash_list

gptmodel = 'gpt-35-turbo-1106' # 'gpt-35-turbo-0613', 'gpt-35-turbo-1106', 'gpt-4-0613', 'gpt-4-1106-Preview'

root_path = os.path.abspath(os.sep)


# Set the path to the Stanford NER Java executable
# Adjust the paths according to where you've saved the Stanford NER and Java on your system
stanford_classifier = stanford_rootpath + '/classifiers/english.all.3class.distsim.crf.ser.gz'
stanford_ner_path = stanford_rootpath + '/stanford-ner.jar'

# Create the NER tagger
st = StanfordNERTagger(stanford_classifier, stanford_ner_path)

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nlp = spacy.load("en_core_web_sm")

nltk.download('stopwords')
stop_words = set(stopwords.words('english'))
# print(stop_words)

p = inflect.engine()

allowed_entities = ['PERSON', 'NORP', 'FAC', 'ORG', 'GPE', 'LOC',  'EVENT', 'WORK_OF_ART', 'LAW', 'LANGUAGE']

ordinals = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth", "eleventh", "twelfth", "thirteenth", "fourteenth", "fifteenth", "sixteenth", "seventeenth", "eighteenth", "nineteenth", "twentieth", "thirtieth", "fortieth", "fiftieth", "sixtieth", "seventieth", "eightieth", "ninetieth", "hundredth", "thousandth", "millionth", "billionth", "trillionth", "quadrillionth", "quintillionth", "sextillionth", "septillionth", "octillionth", "nonillionth", "decillionth"]
direction = ['north', 'south', 'east', 'west']


def is_numeral(s):
    try:
        # Attempt to convert directly to an integer
        int(s)
        return True
    except ValueError:
        pass
    
    try:
        # Try to convert using word2number
        w2n.word_to_num(s)
        return True
    except ValueError:
        pass
    
    # Additional handling for complex numerals like 'hundred and twenty-two'
    try:
        # Remove 'and', which word2number can sometimes struggle with
        cleaned = re.sub(r'\band\b', '', s)
        w2n.word_to_num(cleaned)
        return True
    except ValueError:
        
        for ordin in ordinals:
            if ordin.lower() in s.lower():
                return True
        return False


def convert(sentence, random_entity):
    ans = sentence.replace("[BLANK]", "###___###")
    for entity in random_entity.keys():
        ans = ans.replace(" "+entity+" ", " "+random_entity[entity]+" ")
        ans = ans.replace(" "+entity.lower()+" ", " "+random_entity[entity]+" ")
        ans = ans.replace(" "+entity.capitalize()+" ", " "+random_entity[entity]+" ")
        ans = ans.replace(" "+entity.upper()+" ", " "+random_entity[entity]+" ")

        ans = ans.replace(" "+entity + "s ", " "+random_entity[entity] + "s ")
        ans = ans.replace(" "+entity.lower() + "s ", " "+random_entity[entity] + "s ")
        ans = ans.replace(" "+entity.capitalize() + "s ", " "+random_entity[entity] + "s ")
        ans = ans.replace(" "+entity.upper() + "s ", " "+random_entity[entity] + "s ")

        ans = ans.replace(" "+entity + "es ", " "+random_entity[entity] + "es ")
        ans = ans.replace(" "+entity.lower() + "es ", " "+random_entity[entity] + "es ")
        ans = ans.replace(" "+entity.capitalize() + "es ", " "+random_entity[entity] + "es ")
        ans = ans.replace(" "+entity.upper() + "es ", " "+random_entity[entity] + "es ")

        ans = ans.replace(" "+entity + "n ", " "+random_entity[entity] + "n ")
        ans = ans.replace(" "+entity.lower() + "n ", " "+random_entity[entity] + "n ")
        ans = ans.replace(" "+entity.capitalize() + "n ", " "+random_entity[entity] + "n ")
        ans = ans.replace(" "+entity.upper() + "n ", " "+random_entity[entity] + "n ")
        
        ans = ans.replace(" "+entity + "ns ", " "+random_entity[entity] + "ns ")
        ans = ans.replace(" "+entity.lower() + "ns ", " "+random_entity[entity] + "ns ")
        ans = ans.replace(" "+entity.capitalize() + "ns ", " "+random_entity[entity] + "ns ")
        ans = ans.replace(" "+entity.upper() + "ns ", " "+random_entity[entity] + "ns ")

        ans = ans.replace(" "+entity + "ese ", " "+random_entity[entity] + "ese ")
        ans = ans.replace(" "+entity.lower() + "ese ", " "+random_entity[entity] + "ese ")
        ans = ans.replace(" "+entity.capitalize() + "ese ", " "+random_entity[entity] + "ese ")
        ans = ans.replace(" "+entity.upper() + "ese ", " "+random_entity[entity] + "ese ")

        ans = ans.replace(" "+entity + "ette ", " "+random_entity[entity] + "ette ")
        ans = ans.replace(" "+entity.lower() + "ette ", " "+random_entity[entity] + "ette ")
        ans = ans.replace(" "+entity.capitalize() + "ette ", " "+random_entity[entity] + "ette ")
        ans = ans.replace(" "+entity.upper() + "ette ", " "+random_entity[entity] + "ette ")

        ans = ans.replace(" "+entity + "let ", " "+random_entity[entity] + "let ")
        ans = ans.replace(" "+entity.lower() + "let ", " "+random_entity[entity] + "let ")
        ans = ans.replace(" "+entity.capitalize() + "let ", " "+random_entity[entity] + "let ")
        ans = ans.replace(" "+entity.upper() + "let ", " "+random_entity[entity] + "let ")

        ans = ans.replace(" "+entity+"ern ", " "+random_entity[entity]+"ern ")
        ans = ans.replace(" "+entity.lower()+"ern ", " "+random_entity[entity]+"ern ")
        ans = ans.replace(" "+entity.capitalize()+"ern ", " "+random_entity[entity]+"ern ")
        ans = ans.replace(" "+entity.upper()+"ern ", " "+random_entity[entity]+"ern ")
    return ans.replace("###___###", "[BLANK]")


def filter_words_in_edge(center, words):
    node_info = get_node(format_for_cpnet(center))
    if 'error' in node_info.keys() or 'edges' not in node_info.keys() or len(node_info['edges']) <= 1:
        return list()
    neighbors = set()
    for edge in node_info['edges']:        
        
        if 'language' in edge['start'].keys() and edge['start']['language'] == 'en':
            startword = edge['start']['@id'].split('/')[3]
            if not startword == format_for_cpnet(center):
                neighbors.add(startword)
                
        if 'language' in edge['end'].keys() and edge['end']['language'] == 'en':
            endword = edge['end']['@id'].split('/')[3]
            if not endword == format_for_cpnet(center):
                neighbors.add(endword)
        
    ans = list(filter(lambda x: format_for_cpnet(x) in neighbors, words))
    return ans



def gpt_entity_particular(text, helper_word):
    
    query = f'''List all the noun entity related to '{helper_word}' from [Article].
Your response should strictly follow the format of [Format].
In particular, you should not write index of line in front of the list nor write any descriptive words except for the entity. \n\n'''
    index = 1
    
    query += '''\n[Format]
Entity 1
Entity 2
Entity 3
...\n'''
    query += "\n[Article]\n"

    print("\ngpt_entity_particular(): Query in gpt_entity(): \n", query)
    
    query += text
    
    output = inference_azure(query, gptmodel)
    
    print("\ngpt_entity_particular(): output of GPT: \n", output)
    splitted_output = output.split('\n')
    gpt_entity = list()
    for word in splitted_output:
        if len(word) == 0:
            continue
        gpt_entity.append(word)
    gpt_entity = list(set(gpt_entity))
    print("\ngpt_entity_particular(): entity list: \n", gpt_entity)
    ans = filter_words_in_edge(helper_word, gpt_entity)
    print("\ngpt_entity_particular(): filtered entity: \n", ans)
    return ans


def gpt_entity(text, helper_words = None):
    

    query = '''List all the noun entity from [Article].
Your list must meet with the conditions [Condition].
Your response should strictly follow the format of [Format].
In particular, you should not write index of line in front of the list nor write any descriptive words except for the entity. \n\n'''
    query += "[Condition]\n"
    query += "1. All the proper noun should be in your entity list\n"
    index = 1
    
    if helper_words is not None:
        for i in range(len(helper_words)):
            index += 1
            query += f"{index}. For nouns except for proper noun, every noun related to '{helper_words[i]}' should be in your entity list.\n"

    query += '''\n[Format]
Entity 1
Entity 2
Entity 3
...\n'''
    query += "\n[Article]\n"

    print("\ngpt_entity(): Query in gpt_entity(): \n", query)
    
    query += text
    
    output = inference_azure(query, gptmodel)

    print("\ngpt_entity(): output of GPT: \n", output)
    splitted_output = output.split('\n')
    ans = list()
    for word in splitted_output:
        if len(word) == 0:
            continue
        ans.append(word)
    print("\ngpt_entity(): entity list: \n", ans)
    return ans


def preprocess(sent):
    sent = nltk.word_tokenize(sent)
    sent = nltk.pos_tag(sent)
    return sent



def extract_normal_entity(text, essential_check  = list()):
    final_entity = set()
    preprocessed_ex = text.replace("-", " ").replace("&", " ").replace("–", " ")

    spacy_manual = set()
    spacy_manual_doc = nlp(preprocessed_ex)
    checked = set()
    for entity in tqdm(list(spacy_manual_doc.ents) + essential_check):
        entity_label = None
        if not isinstance(entity, str):
            entity_label = entity.label_
            entity = entity.text
        
        if entity in checked:
            continue
        checked.add(entity)
        
        if is_numeral(entity):
            continue
        # Directly put people related entity in final entity
        if len(entity) > 1 and check_goodentity(entity.replace('\n', ''), no_incident = False):
            for word in entity.split(" "):
                if word.lower() in stop_words: 
                    continue
                final_entity.add(word)
            
            continue
        
        if (entity_label is None or entity_label in allowed_entities) and len(entity) > 1:
            entity_ = entity
            
            splitted_entities = entity_.replace('\n', '').split(' ')
            
            for ent in splitted_entities:
                if ent.lower() == 'a' or ent.lower() == 'the':
                    continue
                spacy_manual.add(ent)

    
    nltk_singular = set()
    nltk_plural = set()
    nltk_sent = preprocess(preprocessed_ex)
    # print(sent)
    for entity in nltk_sent:
        if entity[1] == "NNP":
            for word in entity[0].split(" "):
                if word.lower() in stop_words:
                    continue
                nltk_singular.add(word)
        elif entity[1] == "NNPS":
            for word in p.singular_noun(entity[0]).split(" "):
                if word.lower() in stop_words:
                    continue
                nltk_plural.add(word)

    spacy_singular = set()
    spacy_plural = set()
    spacy_doc = nlp(preprocessed_ex)
    for token in spacy_doc:
        
        if token.tag_ == "NNP":
            for word in token.text.split(" "):
                if word.lower() in stop_words:
                    continue
                spacy_singular.add(word)
        elif token.tag_ == "NNPS":
            for word in token.text.split(" "):
                if word.lower() in stop_words:
                    continue
                spacy_plural.add(word)

    sp_nl_ent = nltk_singular.intersection(spacy_singular)
    sp_nl_ent.update(nltk_plural.intersection(spacy_plural))
    sp_nl_ent.update(spacy_manual)

    sp_nl_filter1_ent = set()
    for word in sp_nl_ent:
        single_doc = nlp(word)
        for token in single_doc:
            if token.tag_ == "NNP":
                sp_nl_filter1_ent.add(token.text)
            elif token.tag_ == "NNPS":
                sp_nl_filter1_ent.add(p.singular_noun(token.text))
    
    sp_nl_filter2_ent = set()
    for word in sp_nl_ent:
        lower_doc = nlp(word.lower())
        for token in lower_doc:
            if token.tag_ == "NNP":
                sp_nl_filter2_ent.add(word)
            elif token.tag_ == "NNPS":
                sp_nl_filter2_ent.add(p.singular_noun(word))

    stan_text = preprocessed_ex
    stan_tokenized_text = word_tokenize(stan_text)
    stan_classified_text = st.tag(stan_tokenized_text)
    
    stan_entity = set()
    
    for entity in stan_classified_text:
        if is_numeral(entity[0]):
            continue
        if entity[1] in ['PERSON', 'LOCATION', 'ORGANIZATION']:
            stan_entity.add(entity[0])

    
    for word in sp_nl_ent:
        if word.lower() in stop_words or is_numeral(word) or len(word) < 3:
            continue
        for dir in direction:
            if dir.lower() in word.lower():
                continue
        count = 0
        if word in sp_nl_filter1_ent:
            count += 1
        if word.lower() in sp_nl_filter2_ent:
            count += 1
        if word in stan_entity:
            count += 1
        if count > 1:
            final_entity.add(word)

    return final_entity


class DirectionSwitch:
    def __init__(self):
        self.north = "north"
        self.south = "south"
        self.east = "east"
        self.west = "west"
        self.northeast = "northeast"
        self.northwest = "northwest"
        self.southeast = "southeast"
        self.southwest = "southwest"
        self.front = "front"
        self.back = "back"
        self.left = "left"
        self.right = "right"

    def rotate_90(self):
        self.north = self.west
        self.south = self.east
        self.east = self.north
        self.west = self.south
        self.northeast = self.northwest
        self.northwest = self.southwest
        self.southeast = self.northeast
        self.southwest = self.southeast
        self.front = self.left
        self.back = self.right
        self.left = self.back
        self.right = self.front

    def reflect_nsaxis(self):
        self.east = self.west
        self.west = self.east
        self.northeast = self.northwest
        self.northwest = self.northeast
        self.southeast = self.southwest
        self.southwest = self.southeast
        self.left = self.right
        self.right = self.left

    def reflect_weaxis(self):
        self.north = self.south
        self.south = self.north
        self.northeast = self.southeast
        self.northwest = self.southwest
        self.southeast = self.northeast
        self.southwest = self.northwest
        self.front = self.back
        self.back = self.front

    def rotate(self, degrees = 90):
        rotate_time = int(degrees/90) % 4
        for i in range(rotate_time):
            self.rotate_90()
    
    def reflect(self, axis = "ns"):
        assert(axis in ["ns", "we", "origin"])
        if axis == "ns":
            self.reflect_nsaxis()
        elif axis == "we":
            self.reflect_weaxis()
        else:
            self.reflect_nsaxis()
            self.reflect_weaxis()

    def final(self):
        final_temp1 = [ "north", "south", "east", "west", "northeast", "northwest", "southeast", "southwest", "front", "back", "left", "right" ]
        final_temp2 = [self.north, self.south , self.east, self.west, self.northeast, self.northwest , self.southeast , self.southwest , self.front, self.back, self.left, self.right]

        final = dict()
        for i in range(len(final_temp1)):
            final[final_temp1[i]] = final_temp2[i]
            final[final_temp1[i].capitalize()] = final_temp2[i].capitalize()
        return final
        
    
    def help(self):
        usage = '''
        1. For rotation
        If you want to rotate clockwise, x degrees,
        call rotate(x)

        2. For reflection
        If you want to reflect direction, call reflect(axis = sth)
        If you want to reflect direction by north-south axis, put "ns" in sth
        If you want to reflect direction by west-east axis, put "we" in sth
        If you want to reflect direction by origin, put "origin" in sth

        3. Return final result
        Call final(). You will get dictionary.
        
        '''
        print(usage)

def convert_direction(text:str, direct_info:DirectionSwitch):
    direction_map = direct_info.final()
    for direction, new_direction in direction_map.items():
        text = text.replace(direction, new_direction)
    return text

def extractNconvert_entity(id_):
    start_time = time.time()

    with open(root_path + qa_rootpath + "qa/QA.json", "r") as file:
        data = json.load(file)
    question_info = None
    for element in data:
        # print(id_, element["id"], id_ == element["id"])
        if id_ == element["id"]:
            
            question_info = element
            break
    assert(question_info is not None)
    entities = set()
    essential = set()
    for hop in question_info['Hops_wiki']:
        essential.add(hop[0])
        essential.add(hop[1])
    for unused in question_info['Multiple_choice_wiki']["choices"]:
        essential.add(unused["text"])
    for word in essential:
        splitted = word.split(" ")
        for small_word in splitted:
            if small_word.lower() not in stop_words:
                entities.add(small_word)

    with open(f'{root_path + qa_rootpath}Question_triplet/{id_}_Qtriplet_ratio100.txt', 'r') as file:
        total_text = file.read()
    
    entities.update(extract_normal_entity(total_text))

    # Related entities considered
    print("entities: ", entities)
    for word in essential:
        entities.update(set(gpt_entity_particular(total_text, word)))
    print("After GPT, entity: ", entities)

    # Redirection Considered
    # ex) USA -> United States of America
    redirected_dict = dict()
    from_set = set()
    to_set = set()
    
    for entity in total_text.replace('")', " ").replace('("', " ").replace('", "', " ").split(" "):
        if len(entity.replace('.', "")) > 1 and entity == entity.upper():
            if entity == "T." or is_numeral(entity):
                continue
            
            redirect = get_redirect_keyword(entity)
            if redirect is not None:
                # print("Redirection not None with: ", entity)
                # print("Redirected to : ", redirect)
                from_set.add(entity)
                to_set.add(redirect)
                redirected_dict[entity] = redirect
    for entity in from_set:
        if entity in entities:
            entities.remove(entity)

    if "Choices" in entities:
        entities.remove("Choices")
    if "choices" in entities:
        entities.remove("choices")
    if "Choice" in entities:
        entities.remove("Choice")
    if "choice" in entities:
        entities.remove("choice")
    if "Question" in entities:
        entities.remove("Question")
    if "question" in entities:
        entities.remove("question")
    
    entity_conversion = dict()
    entities = list(entities)
    
    
    new_entity_hash = hash_list(len(entities))
    random.shuffle(new_entity_hash)

    for i, original_entity in enumerate(entities):
        entity_conversion[original_entity] = new_entity_hash[i]

    for from_entity in from_set:
        redirect = redirected_dict[from_entity]
        if redirect in entity_conversion.keys():
            entity_conversion[from_entity] = entity_conversion[redirect]
            continue
        redirect_split = redirect.split(" ")
        converted  = ""
        for redirect_word in redirect_split:
            if redirect_word in entity_conversion.keys():
                converted += entity_conversion[redirect_word] + ' '
            else:
                converted += redirect_word + ' '
        entity_conversion[from_entity] = converted
    
    
    direction = DirectionSwitch()
    direction.rotate()
    direction.reflect()
    direction_conversion = direction.final()
    entity_conversion.update(direction_conversion)

    print("Total time: ", time.time() - start_time)
    
    with open(f'{root_path + qa_rootpath }entity_conversion/id_{id_}_entity_conversion_hash.json', "w") as json_file:
        json.dump(entity_conversion, json_file)

    print(f"Entity conversion done on {id_} in {root_path + qa_rootpath }entity_conversion/id_{id_}_entity_conversion_hash.json. Check the entity.")
    
def convert_final(id_):
    with open(f'{root_path + qa_rootpath }entity_conversion/id_{id_}_entity_conversion_hash.json', "r") as f:
        entity_conversion = json.load(f)

    with open(root_path + qa_rootpath + "qa/QA.json", "r") as file:
        data = json.load(file)
    question_info = None
    for element in data:
        if id_ == element["id"]:
            question_info = element
            break
    assert(question_info)
    question_str = question_info["Question"]
    choices = list()
    for choice in question_info["Multiple_choice_wiki"]["choices"]:
        choices.append(" "+ choice["text"]+" ")

    ratio = 100
    with open(f'{root_path + qa_rootpath}Question_triplet/{id_}_Qtriplet_ratio{ratio}.txt', 'r') as f:
        total_triplets = list()
        while True:
            line = f.readline()
            if not line: break
            
            line = line.replace("\n", "").replace('", "', " ").replace('("', '').replace('")', '')
            total_triplets.append(line)
        f = open(f'{root_path + qa_rootpath}query_prompt/{id_}_Qtriplet_ratio{ratio}_masked.txt', 'w')
        f.write('Question: '+ convert(question_str, entity_conversion) + '\n')
        print(convert(question_str, entity_conversion))
        choicestr = f"""A: {convert(choices[0], entity_conversion)} 
B: {convert(choices[1], entity_conversion)}
C: {convert(choices[2], entity_conversion)}
D: {convert(choices[3], entity_conversion)}
E: {convert(choices[4], entity_conversion)}
"""
        f.write(choicestr)
        f.write('Choose the answer among A, B, C, D and E based on your understand of the following informations: \n\n\n[Information]\n')
        q_num = 0
        for triplets in total_triplets:
            q_num += 1
            f.write(f"{q_num}) " + convert(" "+ triplets+ " ", entity_conversion)+'. \n')
        
        f.write("\n\nLet's think step by step\n")
        f.close()
        print(f"\n\nDone. Check final_query/id_{id_}_final_result_ratio{ratio}_masked.txt")
    
    with open(f'{root_path + qa_rootpath}Question_triplet/{id_}_Qtriplet_ratio{ratio}.txt', 'r') as f:
        total_triplets = list()
        while True:
            line = f.readline()
            if not line: break
            
            line = line.replace("\n", "").replace('", "', " ").replace('("', '').replace('")', '')
            total_triplets.append(line)
        f = open(f'{root_path + qa_rootpath}query_prompt/{id_}_Qtriplet_ratio{ratio}_unmasked.txt', 'w')
        f.write('Question: '+ question_str + '\n')
        choicestr = f"""A: {choices[0]} 
B: {choices[1]}
C: {choices[2]}
D: {choices[3]}
E: {choices[4]}
"""
        f.write(choicestr)
        f.write('Choose the answer among A, B, C, D and E based on your understand of the following informations: \n\n\n[Information]\n')
        q_num = 0
        for triplets in total_triplets:
            q_num += 1
            f.write(f"{q_num}) " + " "+ triplets+ " " + '. \n')
        
        f.write("\n\nLet's think step by step\n")
        f.close()
        print(f"\n\nDone. Check final_query/id_{id_}_final_result_ratio{ratio}_unmasked.txt")

    
    ratio = 50
    with open(f'{root_path + qa_rootpath}Question_triplet/{id_}_Qtriplet_ratio{ratio}.txt', 'r') as f:
        total_triplets = list()
        while True:
            line = f.readline()
            if not line: break
            
            line = line.replace("\n", "").replace('", "', " ").replace('("', '').replace('")', '')
            total_triplets.append(line)
        f = open(f'{root_path + qa_rootpath}query_prompt/{id_}_Qtriplet_ratio{ratio}_masked.txt', 'w')
        f.write('Question: '+ convert(question_str, entity_conversion) + '\n')
        choicestr = f"""A: {convert(choices[0], entity_conversion)} 
B: {convert(choices[1], entity_conversion)}
C: {convert(choices[2], entity_conversion)}
D: {convert(choices[3], entity_conversion)}
E: {convert(choices[4], entity_conversion)}
"""
        f.write(choicestr)
        f.write('Choose the answer among A, B, C, D and E based on your understand of the following informations: \n\n\n[Information]\n')
        q_num = 0
        for triplets in total_triplets:
            q_num += 1
            f.write(f"{q_num}) " + convert(" "+ triplets+ " ", entity_conversion)+'. \n')
        
        f.write("\n\nLet's think step by step\n")
        f.close()
        print(f"\n\nDone. Check final_query/id_{id_}_final_result_ratio{ratio}_masked.txt")

    with open(f'{root_path + qa_rootpath}Question_triplet/{id_}_Qtriplet_ratio{ratio}.txt', 'r') as f:
        total_triplets = list()
        while True:
            line = f.readline()
            if not line: break
            
            line = line.replace("\n", "").replace('", "', " ").replace('("', '').replace('")', '')
            total_triplets.append(line)
        f = open(f'{root_path + qa_rootpath}query_prompt/{id_}_Qtriplet_ratio{ratio}_unmasked.txt', 'w')
        f.write('Question: '+ question_str + '\n')
        choicestr = f"""A: {choices[0]} 
B: {choices[1]}
C: {choices[2]}
D: {choices[3]}
E: {choices[4]}
"""
        f.write(choicestr)
        f.write('Choose the answer among A, B, C, D and E based on your understand of the following informations: \n\n\n[Information]\n')
        q_num = 0
        for triplets in total_triplets:
            q_num += 1
            f.write(f"{q_num}) " + " "+ triplets+ " " + '. \n')
        
        f.write("\n\nLet's think step by step\n")
        f.close()
        print(f"\n\nDone. Check final_query/id_{id_}_final_result_ratio{ratio}_unmasked.txt")


    
    ratio = 25
    with open(f'{root_path + qa_rootpath}Question_triplet/{id_}_Qtriplet_ratio{ratio}.txt', 'r') as f:
        total_triplets = list()
        while True:
            line = f.readline()
            if not line: break
            
            line = line.replace("\n", "").replace('", "', " ").replace('("', '').replace('")', '')
            total_triplets.append(line)
        f = open(f'{root_path + qa_rootpath}query_prompt/{id_}_Qtriplet_ratio{ratio}_masked.txt', 'w')
        f.write('Question: '+ convert(question_str, entity_conversion) + '\n')
        choicestr = f"""A: {convert(choices[0], entity_conversion)} 
B: {convert(choices[1], entity_conversion)}
C: {convert(choices[2], entity_conversion)}
D: {convert(choices[3], entity_conversion)}
E: {convert(choices[4], entity_conversion)}
"""
        f.write(choicestr)
        f.write('Choose the answer among A, B, C, D and E based on your understand of the following informations: \n\n\n[Information]\n')
        q_num = 0
        for triplets in total_triplets:
            q_num += 1
            f.write(f"{q_num}) " + convert(" "+ triplets+ " ", entity_conversion)+'. \n')
        
        f.write("\n\nLet's think step by step\n")
        f.close()
        print(f"\n\nDone. Check final_query/id_{id_}_final_result_ratio{ratio}_masked.txt")

    with open(f'{root_path + qa_rootpath}Question_triplet/{id_}_Qtriplet_ratio{ratio}.txt', 'r') as f:
        total_triplets = list()
        while True:
            line = f.readline()
            if not line: break
            
            line = line.replace("\n", "").replace('", "', " ").replace('("', '').replace('")', '')
            total_triplets.append(line)
        f = open(f'{root_path + qa_rootpath}query_prompt/{id_}_Qtriplet_ratio{ratio}_unmasked.txt', 'w')
        f.write('Question: '+ question_str + '\n')
        choicestr = f"""A: {choices[0]} 
B: {choices[1]}
C: {choices[2]}
D: {choices[3]}
E: {choices[4]}
"""
        f.write(choicestr)
        f.write('Choose the answer among A, B, C, D and E based on your understand of the following informations: \n\n\n[Information]\n')
        q_num = 0
        for triplets in total_triplets:
            q_num += 1
            f.write(f"{q_num}) " + " "+ triplets+ " " + '. \n')
        
        f.write("\n\nLet's think step by step\n")
        f.close()
        print(f"\n\nDone. Check final_query/id_{id_}_final_result_ratio{ratio}_unmasked.txt")