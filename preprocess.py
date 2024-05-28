from gpt_query import inference_azure
from dir_path import *
from format import *
import os
import json
from bs4 import BeautifulSoup
import requests
from cpnet_wiki import wiki_word_in_cpnet
from cpnet_wiki import get_redirect_url
from cpnet_wiki import get_redirect_keyword
from cpnet_wiki import test_geo
from cpnet_wiki import test_animal
from cpnet_wiki import test_people
from cpnet_wiki import test_incident
from tqdm import tqdm
from urllib.parse import unquote
from cpnet_wiki import check_goodentity

import re

def contains_numerical_symbol(text):
    pattern = r'[0-9]' 
    match = re.search(pattern, text)
    return bool(match)


root_path = os.path.abspath(os.sep)
datafilepath = root_path + qa_rootpath + "organized_data.json"

def update_datafile(keyword, element):
    
    dictObj = dict()
    try:
        with open(datafilepath, 'r') as fp:
            dictObj = json.load(fp)
    except FileNotFoundError:
        print(f"The file {datafilepath} was not found. An empty structure will be used instead.")
    except json.JSONDecodeError:
        print(f"The file {datafilepath} is empty or not valid JSON. An empty structure will be used instead.")
    
    if keyword in dictObj.keys():
        dictObj[keyword].append(element)
    else:
        dictObj[keyword] = [element]
    with open(datafilepath, 'w') as json_file:
        json.dump(dictObj, json_file, 
                            indent=4,  
                            separators=(',',': '))


def extract_info(keyword):
    print(f"extract_info({keyword}) Start.")
    keyword = get_redirect_keyword(unquote(keyword))
    plainfile = open(root_path + qa_rootpath + f"wiki_files/{format_for_wiki(keyword)}_plain.txt", "w")

    
    # Extract plaintext
    S = requests.Session()
    URL = "https://en.wikipedia.org/w/api.php"
    PARAMS = {'action': 'query','format': 'json','titles': keyword,'prop': 'extracts', "explaintext": True}
    DATA = S.get(url = URL, params = PARAMS).json()
    assert(len(DATA["query"]["pages"].values()))
    plaintext = list(DATA["query"]["pages"].values())[0]["extract"].replace("\n", " ").replace("===", '\n').replace("==", '\n\n')
    cut_from = plaintext.find('See also')
    plaintext = plaintext[:cut_from]
    plainfile.write(plaintext)
    plainfile.close()

    page = requests.get(get_redirect_url(keyword))
    soup = BeautifulSoup(page.content, 'html.parser')
    html_splitted = str(soup.find_all('p')).replace("(", "([INSIDE_SG]__").replace(")", "(").split("(")
    
    html = ""
    for phrase in html_splitted:
        if "[INSIDE_SG]__" in phrase:
            continue
        html += phrase
    
    all_link = list()
    good_link = list()
    soup = BeautifulSoup(html, features="lxml")

    dup_check = set()
    print(f"utils/preprocess.py extract_info(): Checking good links on {keyword}")
    # For efficiency
    valid_n = 0
    all_n = 0
    for a in tqdm(soup.find_all('a', href=True)):
        
        if '#cite' in a['href']:
            continue
        else:
            if 'title' in a.attrs:
                if all_n >= 700 or valid_n >=30:
                    break
                all_n += 1
                if a["title"] in dup_check:
                    continue
                if 'class' in a.attrs:
                    if 'mw-redirect' in a['class']:
                        title_word = get_redirect_keyword(a["title"])
                        cpnet_word = wiki_word_in_cpnet(title_word)
                    else:
                        cpnet_word = wiki_word_in_cpnet(a["title"])
                        title_word = a["title"]
                else:
                    cpnet_word = wiki_word_in_cpnet(a["title"])
                    title_word = a["title"]
                if title_word in dup_check:
                    continue
                dup_check.add(title_word)
                all_link.append((a.text, title_word, cpnet_word))
                if cpnet_word is not None and check_goodentity(title_word):
                    valid_n += 1
                    print(f"{valid_n} / 30 ) ", a.text, title_word, cpnet_word)
                    good_link.append((a.text, title_word, cpnet_word))
                    

    info_data = dict()
    info_data["all_link"] = all_link
    info_data["good_link"] = good_link
    
    
    with open(root_path + qa_rootpath + f"wiki_files/{format_for_wiki(keyword)}_info.json", "w", encoding="utf-8") as f:
        json.dump(info_data, f, ensure_ascii=False) 

def extract_triplet(keyword):
    print(f"extract_triplet({keyword})")
    keyword = get_redirect_keyword(unquote(keyword))
    with open(root_path + qa_rootpath + f"prompt/prompt1.txt", "r") as f:
        prompt = f.read()
    with open(root_path + qa_rootpath + f"wiki_files/{format_for_wiki(keyword)}_plain.txt", "r") as f:
        plaintext = f.read()
    with open(root_path + qa_rootpath + f"wiki_files/{format_for_wiki(keyword)}_info.json", "r") as f:
        info_data = json.load(f)
    triplet_file = open(root_path + qa_rootpath + f"wiki_files/{format_for_wiki(keyword)}_triplets.txt", "w")
    
    
    prompt += f"""    4. Main Keyword
    {keyword}

    
    
    5. Important Keywords
"""
    for word in info_data["good_link"]:
        if word[2] is not None:
            prompt += f'    {word[0]}\n'
    prompt += f'''
    
    
    6. Text
    Topic: {keyword}
    Content: 
    '''
    
    prompt += plaintext
    # prompt += f"All the text in \n{get_redirect_url(keyword)}\n"
    output = inference_azure(prompt)

    print(f"Got GPT's response. String length : {len(output)}")
    
    splitted_output = output.replace(') (', ')\n(').replace(')(', ')\n(').split('\n')
    
    keyword_in_cpnet = wiki_word_in_cpnet(keyword)
    assert(keyword_in_cpnet is not None)
    line = 0
    for phrase in splitted_output:
        if len(phrase) > 3 and not contains_numerical_symbol(phrase):
            
            splitted_phrase = phrase.replace('" ,"', '", "').replace('" , "', '", "').replace('("', '", "').replace('")', '", "').split('", "')
            if not len(splitted_phrase) == 5:
                print(splitted_phrase)
                continue
            line += 1
            triplet_file.write(phrase + '\n')
            subject = splitted_phrase[1].replace('-', ' ')
            object = splitted_phrase[3].replace('-', ' ')
            
            subject_words = list()
            object_words = list()
            if keyword.lower() in subject.lower():
                subject_words.append((None, keyword, keyword_in_cpnet))
            if keyword.lower() in object.lower():
                object_words.append((None, keyword, keyword_in_cpnet))
            
            for word_phrase in info_data["good_link"]:
                if word_phrase[2] is None:
                    continue
                
                if word_phrase[0].lower() in subject.lower() or word_phrase[1].lower() in subject.lower():
                    fail = False
                    for word1 in word_phrase[0].split(" "):
                        if word1.lower() not in subject.lower().split(" "):
                            fail = True
                            break
                    if fail:
                        fail = False
                        for word1 in word_phrase[1].split(" "):
                            if word1.lower() not in subject.lower().split(" "):
                                fail = True
                                break
                    if fail:
                        continue
                    subject_words.append(word_phrase)
                if word_phrase[0].lower() in object.lower() or word_phrase[1].lower() in object.lower():
                    fail = False
                    for word1 in word_phrase[0].split(" "):
                        if word1.lower() not in object.lower().split(" "):
                            fail = True
                            break
                    if fail:
                        fail = False
                        for word1 in word_phrase[1].split(" "):
                            if word1.lower() not in object.lower().split(" "):
                                fail = True
                                break
                    if fail:
                        continue
                    object_words.append(word_phrase)
            print("subject_words: ", subject_words)
            print("object_words: ", object_words)
            for s_word in subject_words:
                for o_word in object_words:
                    if s_word[1] == o_word[1]:
                        continue
                    element_dict = dict()
                    element_dict['triplet'] = phrase
                    element_dict['start word'] = s_word[1]
                    element_dict['end word'] = o_word[1]
                    element_dict['source'] = dict()
                    element_dict['source']['name'] = keyword
                    element_dict['source']['line'] = line
                    element_dict['cpnet'] = dict()
                    element_dict['cpnet']['start word'] = s_word[2]
                    element_dict['cpnet']['end word'] = o_word[2]
                    update_datafile(s_word[1], element_dict.copy())

                    element_dict['start word'] = o_word[1]
                    element_dict['end word'] = s_word[1]
                    element_dict['cpnet']['start word'] = o_word[2]
                    element_dict['cpnet']['end word'] = s_word[2]
                    update_datafile(o_word[1], element_dict.copy())
                    
    triplet_file.close()

    


