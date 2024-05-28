import json
import random
import os


from gpt_query import inference_azure
from dir_path import *
import preprocess
from cpnet_wiki import get_redirect_keyword
from cpnet_wiki import wiki_word_in_cpnet
from multiple_choice import final_choice
from triplet_extract_ratio import triplet_extract_ratio
from format import *
from urllib.parse import unquote


root_path = os.path.abspath(os.sep)
pronouns = ["they", "this", "these", "that", "those", "their", "them"] # Demonstractive pronoun



def check_pronoun(phrase):
    phrase = phrase.lower()
    for word in pronouns:
        if word in phrase:
            return True
    return False



def read_line(filename, linenum):
    file = open(filename)
    line = 0
    while True:
        line += 1
        file_content = file.readline()
        if not file_content:
            file.close()
            return None
        if line == linenum:
            file.close()
            return file_content

# failed_words: The lists of words you want to exclude from extracting. You might have already tried this one and failed
# used_words: The list of words you already used in making question. This is to prevent circular hop question.
# Return the whole dictionary element
def extract_hops(keyword, failed_words = list(), used_words = list()):
    print(f"\nutils/question.py extract_hops({keyword}, {failed_words}, {used_words}) Start")
    keyword = get_redirect_keyword(keyword)
    if os.path.exists(f'{root_path + qa_rootpath}wiki_files/{format_for_wiki(keyword)}_info.json'):
        print(f"Found {root_path + qa_rootpath}wiki_files/{format_for_wiki(keyword)}_info.json file")
        with open(root_path + qa_rootpath + "organized_data.json", "r") as f:
            org_data = json.load(f)
    else:
        print(f"There is no {root_path + qa_rootpath}wiki_files/{format_for_wiki(keyword)}_info.json file")
        preprocess.extract_info(keyword)
        preprocess.extract_triplet(keyword)
        with open(root_path + qa_rootpath + "organized_data.json", "r") as f:
            org_data = json.load(f)
    
    
    
    hops = org_data[keyword]
    # print(hops)
    if len(hops) <= len(failed_words):
        return None
    available_hops = list()
    for i in range(len(hops)):
        if hops[i]['end word'] in failed_words or hops[i]['end word'] in used_words:
            continue
        available_hops.append(hops[i])
    if len(available_hops) == 0:
        return None
    return random.choice(available_hops)


def generate_question(q_id, triplet_list, answer_list, big_hints, target_answer, hops_list):
    print(f"generate_question({q_id}, {triplet_list}, {answer_list}, {big_hints}, {target_answer}, {hops_list}) called")
    assert(len(triplet_list) == len(answer_list))
    
    prompt2_file = open(root_path + qa_rootpath + "prompt/prompt2.txt", "r")
    prompt2 = prompt2_file.read()
    
    prompt2 += "\n[Triplet & Answer]\n"
    for i, hint in enumerate(triplet_list):
        prompt2 += f"{i+1}.\nTriplet: {hint} \nAnswer: {answer_list[i]} \n\n"
    
    prompt2 += "[Your format]\n"
    for i in range(len(triplet_list)):
        prompt2 += f"Q{i+1}: \nA{i+1}: \n\n"
    
    output2 = inference_azure(prompt2)
    question_decomposition = output2.split('Q')[1:]

    if len(triplet_list)== 0:
        if 'A:' in question_decomposition[0]:
            output3 = question_decomposition[0].split("A:")[0]
        else:
            output3 = question_decomposition[0]
    else:
        prompt3_file = open(root_path + qa_rootpath + "prompt/prompt3.txt", "r")
        prompt3 = prompt3_file.read()
        
        prompt3 += "\n[Small questions & Answer]\n"
        prompt3 += output2
        
        prompt3 += f"\n\n[Your Format]\nQ: \nA: {target_answer}"
        
        output3 = inference_azure(prompt3)
        print(f"GPT output is: ", output3)
        if 'A:' in output3:
            output3 = output3.replace("Q:", '').split("A:")[0]
    wiki_multiple_choice = final_choice(target_answer)
    cpnet_multiple_choice = dict()
    cpnet_multiple_choice["choices"] = list()
    no_answer_title = list()
    
    for i, _ in enumerate(wiki_multiple_choice["choices"]):
        word = unquote(wiki_multiple_choice["choices"][i]["text"])
        label = wiki_multiple_choice["choices"][i]["label"]
        wiki_multiple_choice["choices"][i]["text"] = get_redirect_keyword(word)
        if not label == wiki_multiple_choice["answerKey"]:
            keyword = wiki_multiple_choice["choices"][i]["text"]
            if not os.path.exists(f'{root_path + qa_rootpath}wiki_files/{keyword}_info.json'):
                preprocess.extract_info(keyword)
                preprocess.extract_triplet(keyword)
            no_answer_title.append({"name": keyword})
        cpnet_multiple_choice["choices"].append( {"label":label, "text": wiki_word_in_cpnet(word)})
        
    cpnet_multiple_choice["answerKey"] = wiki_multiple_choice["answerKey"]
    cpnet_multiple_choice["choicelevel"] = wiki_multiple_choice["choicelevel"]

    hops_wiki = list()
    hops_cpnet = list()
    for hint in big_hints:
        hops_wiki.append((get_redirect_keyword(hint[0]), get_redirect_keyword(hint[1])))
        hops_cpnet.append((wiki_word_in_cpnet(get_redirect_keyword(hint[0])), wiki_word_in_cpnet(get_redirect_keyword(hint[1]))))
        
    # preadd_question = f"""[Question]
    # {output3}
    
    # [Choices]
    # {wiki_multiple_choice}
    
    # """
    # Make Triplets by ratio
    triplet_ans100 = triplet_extract_ratio(q_id, hops_list + no_answer_title, 1)
    triplet_ans50 = triplet_extract_ratio(q_id, hops_list + no_answer_title, 0.5)
    triplet_ans25 = triplet_extract_ratio(q_id, hops_list + no_answer_title, 0.25)
    q_triplet_answer = dict()
    q_triplet_answer[100] = triplet_ans100
    q_triplet_answer[50] = triplet_ans50
    q_triplet_answer[25] = triplet_ans25
    
    
    new_element = {"id": q_id, "Question": output3, "Answer": target_answer,   "Multiple_choice_wiki": wiki_multiple_choice, "Multiple_choice_cpnet": cpnet_multiple_choice, "Question_decompositions": question_decomposition, "Hops_wiki": hops_wiki, "Hops_cpnet": hops_cpnet, "Triplets": triplet_list, "Referred_files": hops_list, "Question_triplet_answer": q_triplet_answer}
    
    file_path = root_path + qa_rootpath + "qa/QA.json"
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
            except (EOFError, json.decoder.JSONDecodeError):
                data = []  
                
    else:
        data = [] 
        

    # Add the new dictionary to the list
    data.append(new_element)
    
    
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
        
            
    return new_element
        
  
    
