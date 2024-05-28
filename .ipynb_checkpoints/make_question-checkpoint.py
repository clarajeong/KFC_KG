from question import *
from format import *
from preprocess import *
from dir_path import *
from cpnet_wiki import find_bestroute

import random
import os
import os.path
import time
import sys

root_path = os.path.abspath(os.sep)
datafilepath = root_path + qa_rootpath + "dataset.json"

def update_datafile(keyword, element):
    dictObj = {}
    try:
        with open(datafilepath, 'r') as fp:
            dictObj = json.load(fp)
    except FileNotFoundError:
        print(f"The file {root_path + qa_rootpath + 'dataset.json'} was not found. An empty structure will be used instead.")
    except json.JSONDecodeError:
        print(f"The file {root_path + qa_rootpath + 'dataset.json'} is empty or not valid JSON. An empty structure will be used instead.")
    
    
    dictObj[keyword] = new_element
    with open(datafilepath, 'w') as json_file:
        json.dump(dictObj, json_file, 
                            indent=4,  
                            separators=(',',': '))


def make_question(startword, hop_type, q_id):
    time_start = time.time()
    prompt1_time = 0 # 0.1 dollar per once
    prompt23_time = 0 # 0.005 dollar per once
    
    if hop_type == 0:
        first_hop = extract_hops(startword, failed_words =list(), used_words = [])
        print("first_hop: ", first_hop)
        if first_hop is None:
            print("Pick another startword.")
            print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
            return None
        next_word = first_hop['end word']
        print(f"next_word: {next_word}")
        word11 = first_hop['start word']
        word12 = next_word
        triplet_list = [first_hop['triplet']]
        answer_list = [word12]
        big_hints = [(word11, word12)]
        qa = generate_question(q_id, triplet_list, answer_list, big_hints, word12, [first_hop['source']])
        print(qa)
        time_end = time.time()
        print("time passed: " ,  time_end - time_start)
        print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
    elif hop_type == 1:
        failed_words = list()
        while True:
            first_hop = extract_hops(startword, failed_words = failed_words, used_words = [])
            print("first_hop: ", first_hop)
            if first_hop is None:
                print("Pick another startword.")
                print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
                return None
            next_word = first_hop['end word']
            print(f"next_word: {next_word}")
            second_hop = extract_hops(next_word, used_words = [startword])
            if second_hop is None:
                failed_words.append(next_word)
                continue
            word11 = first_hop['start word']
            word12 = first_hop['end word']
            word21 = second_hop['start word']
            word22 = second_hop['end word']
            
            triplet_list = [first_hop['triplet'], second_hop['triplet']]
            break
        answer_list = [word12, word22]
        big_hints = [(word11, word12), (word21, word22)]
        
        qa = generate_question(q_id, triplet_list, answer_list, big_hints, word22, [first_hop['source'], second_hop['source']])
        prompt23_time += 1
        print(qa)
        time_end = time.time()
        print("time passed: " ,  time_end - time_start)
        print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
        
    elif hop_type == 2:
        failed_words1 = list()
        while True:
            first_hop = extract_hops(startword,  failed_words = failed_words1, used_words = [])
            print("first_hop: ", first_hop)
            if first_hop is None:
                print("Pick another startword")
                print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
                return None
            next_word = first_hop['end word']
            failed_words2 = list()
            done = False
            while True:
                second_hop = extract_hops(next_word, failed_words = failed_words2, used_words = [startword])
                print("second_hop: ", second_hop)
                if second_hop is None:
                    failed_words1.append(first_hop['end word'])
                    break
                last_word = second_hop['end word']
                
                third_hop = extract_hops(last_word, used_words = [startword, next_word])
                print("third_hop: ", third_hop)
                if third_hop is None:
                    failed_words2.append(second_hop['end word'])
                else:
                    word11 = first_hop['start word']
                    word12 = first_hop['end word']
                    word21 = second_hop['start word']
                    word22 = second_hop['end word']
                    word31 = third_hop['start word']
                    word32 = third_hop['end word']

                    triplet_list = [first_hop['triplet'], second_hop['triplet'], third_hop['triplet']]
                    done = True
                    break
            if done: break
            
        answer_list = [word12, word22, word32]
        
        big_hints = [(word11, word12), (word21, word22), (word31, word32)]
        
        qa = generate_question(q_id, triplet_list, answer_list, big_hints, word32, [first_hop['source'], second_hop['source'], third_hop['source']])
        prompt23_time += 1
        print(qa)
        time_end = time.time()
        print("time passed: " ,  time_end - time_start)
        print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
    elif hop_type == 3:
        failed_words = list()
        
        while True:
            first_hop = extract_hops(startword, failed_words = failed_words, used_words = [])
            print("first_hop: ", first_hop)
            if first_hop is None:
                print("Pick another startword")
                print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
                return None
            next_word1 = first_hop['end word']
            
            second1_hop = extract_hops(next_word1, used_words = [startword])
            print("second1_hop: ", second1_hop)
            if second1_hop is None:
                failed_words.append(first_hop['end word'])
                continue
            second2_hop = extract_hops(next_word1, failed_words = [second1_hop['end word']], used_words = [startword])
            print("second2_hop: ", second2_hop)
            if second2_hop is None:
                failed_words.append(first_hop['end word'])
            else:
                word11 = first_hop['start word']
                word12 = first_hop['end word']
                word21 = second1_hop['start word']
                word22 = second1_hop['end word']
                word31 = second2_hop['start word']
                word32 = second2_hop['end word']
                triplet_list = [first_hop['triplet'], second1_hop['triplet'], second2_hop['triplet']]
                break
        answer_list = [word11, word21, word31]
        big_hints = [(word11, word12), (word21, word22), (word31, word32)]
        
        qa = generate_question(q_id, triplet_list, answer_list, big_hints, word11, [first_hop['source'], second1_hop['source'], second2_hop['source']])
        prompt23_time += 1
        print(qa)
        time_end = time.time()
        print("time passed: " ,  time_end - time_start)
        print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
    elif hop_type == 4:
        failed_words1 = list()
        
        while True:
            first_hop = extract_hops(startword, failed_words = failed_words1, used_words = [])
            print("first_hop: ", first_hop)
            if first_hop is None:
                print("Pick another startword")
                print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
                return None
            
            next_word = first_hop['end word']
            failed_words2 = list()
            done = False
            while True:
                second_hop = extract_hops(next_word, failed_words = failed_words2, used_words = [startword])
                print("second_hop: ", second_hop)
                if second_hop is None:
                    failed_words1.append(first_hop['end word'])
                    break
                third_word = second_hop['end word']
                
                failed_words3 = list()
                while True:
                    third_hop = extract_hops(third_word, failed_words = failed_words2, used_words = [startword, next_word])
                    print("third_hop: ", third_hop)
                    if second_hop is None:
                        failed_words2.append(second_hop['end word'])
                        break
                    last_word = third_hop['end word']
                    
                    forth_hop = extract_hops(last_word, used_words = [startword, next_word, third_word])
                    print("forth_hop: ", forth_hop)
                    if forth_hop is None:
                        failed_words3.append(third_hop['end word'])
                    else:
                        word11 = first_hop['start word']
                        word12 = first_hop['end word']
                        word21 = second_hop['start word']
                        word22 = second_hop['end word']
                        word31 = third_hop['start word']
                        word32 = third_hop['end word']
                        word41 = forth_hop['start word']
                        word42 = forth_hop['end word']
                        triplet_list = [first_hop['triplet'], second_hop['triplet'], third_hop['triplet'], forth_hop['triplet']]
                        done = True
                        break
                if done: break
            if done: break
            
        answer_list = [word12, word22, word32, word42]
        
        big_hints = [(word11, word12), (word21, word22), (word31, word32), (word41, word42)]
        
        qa = generate_question(q_id, triplet_list, answer_list, big_hints, word42, [first_hop['source'], second_hop['source'], third_hop['source'], forth_hop['source']])
        prompt23_time += 1
        print(qa)
        time_end = time.time()
        print("time passed: " ,  time_end - time_start)
        print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
    elif hop_type == 5:
        failed_words1 = list()
        
        extraction_done = False
        while True:
            first_hop = extract_hops(startword,  failed_words = failed_words1, used_words = [])
            print("first_hop: ", first_hop)
            if first_hop is None:
                print("Pick another startword")
                print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
                return None
            second_word = first_hop['end word']
            
            failed_words2 = list()
            done = False
            while True:
                second_hop = extract_hops(second_word,failed_words = failed_words2, used_words = [startword])
                print("second_hop: ", second_hop)
                if second_hop is None:
                    failed_words1.append(first_hop['end word'])
                    break
                third_word = second_hop['end word']
                
                third_hop1 = extract_hops(third_word, used_words = [startword, second_word])
                print("third_hop1: ", third_hop1)
                if third_hop1 is None:
                    failed_words2.append(second_hop['end word'])
                    continue
                third_hop2 = extract_hops(third_word, failed_words = [third_hop1['end word']], used_words = [startword, second_word])
                print("third_hop2: ", third_hop2)
                if third_hop2 is None:
                    failed_words2.append(second_hop['end word'])
                else:
                    word11 = first_hop['start word']
                    word12 = first_hop['end word']
                    word21 = second_hop['start word']
                    word22 = second_hop['end word']
                    word31 = third_hop1['start word']
                    word32 = third_hop1['end word']
                    word33 = third_hop2['end word']
                    triplet_list = [first_hop['triplet'], second_hop['triplet'], third_hop1['triplet'], third_hop2['triplet']]
                    extraction_done = True
                    print("extraction_done: ", extraction_done)
                    break
            if extraction_done:
                break
        answer_list = [word11, word21, word31, word31]
        
        big_hints = [(word11, word12), (word21, word22), (word31, word32), (word31, word33)]
        
        qa = generate_question(q_id, triplet_list, answer_list, big_hints, word11, [first_hop['source'], second_hop['source'], third_hop1['source'], third_hop2['source']])
        prompt23_time += 1
        print(qa)
        time_end = time.time()
        print("time passed: " ,  time_end - time_start)
        print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
    elif hop_type == 6:
        lasthop_extracted = False
        extraction_completed = False
        failed_words1 = list()
        
        while True:
            first_hop = extract_hops(startword, failed_words = failed_words1, used_words = [])
            print("first_hop: ", first_hop)
            if first_hop is None:
                print("Pick another startword")
                print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)
                return None
            second_word = first_hop['end word']
            
            failed_words2 = list()
            
            while True:
                second_hop1 = extract_hops(second_word, failed_words = failed_words2, used_words = [startword])
                print("second_hop1: ", second_hop1)
                if second_hop1 is None:
                    failed_words1.append(first_hop['end word'])
                    break
                failed_words2.append(second_hop1['end word'])
                
                # Check last hop existence
                last_word = second_hop1['end word']
                
                last_hop = extract_hops(last_word, used_words = [startword, second_word])
                print("last_hop: ", last_hop)
                if last_hop is not None:
                    lasthop_extracted = True

                failed_words3 = [second_hop1['end word']]
                while True:
                    # Check second_hop2 
                    second_hop2 = extract_hops(second_word, failed_words = failed_words3, used_words = [startword])
                    print("second_hop2: ", second_hop2)
                    if second_hop2 is None:
                        # There is no appropriate two second hops.
                        failed_words1.append(first_hop['end word'])
                        break
                    else:
                        # Check if this has last hop
                        if lasthop_extracted:
                            extraction_completed = True
                            word11 = first_hop['start word']
                            word12 = first_hop['end word']
                            word21 = second_hop1['start word']
                            word22 = second_hop1['end word']
                            word23 = second_hop2['end word']
                            word31 = last_hop['start word']
                            word32 = last_hop['end word']
                            triplet_list = [first_hop['triplet'], second_hop1['triplet'], second_hop2['triplet'], last_hop['triplet']]
                            
                            break
                        else:
                            last_word = second_hop2['end word']
                            
                            last_hop = extract_hops(last_word, used_words = [startword, second_word])
                            if last_hop is None:
                                failed_words3.append(second_hop2['end word'])
                            else:
                                extraction_completed = True
                                word11 = first_hop['start word']
                                word12 = first_hop['end word']
                                word21 = second_hop1['start word']
                                word22 = second_hop1['end word']
                                word23 = second_hop2['end word']
                                word31 = last_hop['start word']
                                word32 = last_hop['end word']
                                triplet_list = [first_hop['triplet'], second_hop1['triplet'], second_hop2['triplet'], last_hop['triplet']]
                                
                                
                                break
                if not extraction_completed:
                    # There is no appropriate two second hops.
                    continue
                else:
                    # Appropriate two second hops are found.
                    break
            
            if not extraction_completed:
                # There is no appropriate two second hops.
                continue
            else:
                # Appropriate two second hops are found.
                break
        answer_list = [word11, word21, word21, word31]
        big_hints = [(word11, word12), (word21, word22), (word21, word23), (word31, word32)]
        
        qa = generate_question(q_id, triplet_list, answer_list, big_hints, word11, [first_hop['source'], second_hop1['source'], second_hop2['source'], last_hop['source']])
        prompt23_time += 1
        print(qa)
        time_end = time.time()
        print("time passed: " ,  time_end - time_start)
        print("Expected dollar: ", prompt1_time * 0.05 + prompt23_time * 0.005)


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python main.py <startword> <hop_type> <q_id>")
    else:
        startword = sys.argv[1]
        hop_type = int(sys.argv[2])  # Assuming hop_type is expected to be an integer
        q_id = sys.argv[3]  
        
        print(f"Got argument: {startword}, {hop_type}, {q_id}")
        result = make_question(startword, hop_type, q_id)
        