import os
import json
from tqdm import tqdm
from gpt_query import inference_azure
from dir_path import *
from entity import convert
import numpy as np
import pandas as pd 
import datetime


root_path = os.path.abspath(os.sep)


def update_QA(q_ids = None, manual_output = "manual.txt"):
    
    file_path = root_path + qa_rootpath + "qa/QA.json"
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        with open(file_path, 'r') as file:
            try:
                data = json.load(file)
            except (EOFError, json.decoder.JSONDecodeError):
                return
    else:
        return
    not_converted = ""
    
    for ind, q_a in tqdm(enumerate(data)):
        if q_ids is not None:
            if q_a["id"] not in q_ids:
                continue
        if "Masked_Q" not in q_a.keys():
            q_a["Masked_Q"] = dict()

            simple_prompt = """Can you combine the following two sentences into one sentence without loss of information? Don't write any words except for the sentence you write.

[Sentence]
1. """
            updated_sentence = q_a["Triplets"][0]
            for i in range(1, len(q_a["Triplets"])):
                prompt = simple_prompt + updated_sentence + '\n2. ' +  q_a["Triplets"][i]
                updated_sentence = inference_azure(prompt)
                # print(f"[{updated_sentence}] + [{q_a['Triplets'][i]}] -> {updated_sentence}")
            data[ind]["Masked_Q"]["Original"] = updated_sentence

            data[ind]["Masked_Q"]["Masked"] = list()
            checked = list()
            
            for item_ in q_a["Hops_wiki"]:
                for i in range(2):
                    if item_[i] not in checked:
                        checked.append(item_[i])
                        if item_[i] not in updated_sentence:
                            not_converted += f"{q_a['id']} ) {item_[i]}"
                            data[ind]["Masked_Q"]["Masked"].append(updated_sentence)
                        else:
                            data[ind]["Masked_Q"]["Masked"].append(updated_sentence.replace(item_[i], "[BLANK]"))

    
            data[ind]["Masked_Q"]["Answers"] = checked.copy()
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
    with open(manual_output, 'a') as file:
        file.write(not_converted)

def check_answer(result_path, answer):
    with open(result_path, "r") as file:
        result = file.read()
        response_ans = result.split("Answer:")[-1]
        if response_ans[0] == " ": 
            response_ans = response_ans[1:]
        if response_ans.lower() == answer.lower():
            return (True, None)
        else:
            return (False, response_ans)

def ask_gpt_manually(q_ids = None, result_storedir = root_path + qa_rootpath + "result/openai_LLM", ratio_list = [1, 0.5, 0.25], models = ['gpt-35-turbo-1106', 'gpt-4-1106-Preview']):
    update_QA()
    
    with open(root_path + qa_rootpath + "qa/QA.json", "r") as file:
        data = json.load(file)
    if q_ids is None:
        q_ids = [element["id"] for element in data]
    if isinstance(q_ids[0], int) or "_" not in q_ids[0]:
        hops = q_ids.copy()
        q_ids = list()
        for hop_type in hops:
            for element in data:
                if int(hop_type) == int(element["id"].split("_")[0]):
                    q_ids.append(element["id"])

    one_hop_id = list()
    two_hop_id = list()
    three_hop_id = list()
    four_hop_id = list()
    for id_ in q_ids:
        hop_type = int(id_.split("_")[0])
        if hop_type == 0:
            one_hop_id.append(id_)
        elif hop_type == 1:
            two_hop_id.append(id_)
        elif hop_type == 2:
            three_hop_id.append(id_)
        else:
            four_hop_id.append(id_)

    # For writing wrong content
    wrong_content = ""
    result_data_list = list()
    # For writing result csv
    for ratio in ratio_list:
        result_data = np.zeros((3 + 2 * len(one_hop_id) + 3 * len(two_hop_id) + 4 * len(three_hop_id) + 5 * len(four_hop_id), 8), dtype=object)
        result_data[0, 2] = "WO/ Information"
        result_data[0, 4] = "W/ Information"
        result_data[1, 2] = "UNMASKED"
        result_data[1, 4] = "UNMASKED"
        result_data[1, 6] = "MASKED"
        result_data[2, 0] = "Q_ID"
        result_data[2, 1] = "Answer Number"
        result_data[2, 2] = "GPT3.5"
        result_data[2, 3] = "GPT4"
        result_data[2, 4] = "GPT3.5"
        result_data[2, 5] = "GPT4"
        result_data[2, 6] = "GPT3.5"
        result_data[2, 7] = "GPT4"
        result_data_list.append(result_data)
    q_ids= sorted(one_hop_id) + sorted(two_hop_id) + sorted(three_hop_id) + sorted(four_hop_id)

    
    line = 2
    for id_ in q_ids:
        for ratio_ind in range(len(ratio_list)):
            result_data_list[ratio_ind][line+1, 0] = id_
        question_info = None
        for element in data:
            # print(id_, element["id"], id_ == element["id"])
            if id_ == element["id"]:
                question_info = element
                break
        assert(question_info is not None)

        answers = question_info["Masked_Q"]["Answers"]

        for ind_, (question, answer) in enumerate(zip(question_info["Masked_Q"]["Masked"], question_info["Masked_Q"]["Answers"])):
            line += 1
            for ratio_ind in range(len(ratio_list)):
                result_data_list[ratio_ind][line, 1] = ind_
            for ratio_ind, ratio in enumerate(ratio_list):
                reasoning = question_info["Question_triplet_answer"][str(int(ratio*100))]
                
                ###################### UNMASKED without information ######################
                query = f"""Fill in the blank with the appropriate word.
There can be multiple [BLANK]s in a sentence. The same word should be inserted into all the [BLANK]s.
At the end of your response, include "Answer:" and write your final answer after it.

Question: {question}"""
                for model_ind, gptmodel in enumerate(models):
                    if os.path.isfile(f'{result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_{ind_}_infoX.txt'):
                        result = check_answer(f'{result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_{ind_}_infoX.txt', answer)
                        if result[0] :
                            result_data_list[ratio_ind][line, 2 + model_ind] = 1
                        else:
                            result_data_list[ratio_ind][line, 2 + model_ind] = 0
                            wrong_content += f"""
    id: {id_}, NOINFO UNMASKED, answer ind_: {ind_}, model: {gptmodel}
    Answer: {answer}, Response: {result[1]}, ratio: {ratio}
    
    """
                        continue
                    try:
                        justanswer = inference_azure(query, gptmodel)
                    except:
                        print(f"Error in query {query}. UNMASKED W/ INFO. model : {gptmodel}. ID : {id_}. ratio: {ratio}")
                        continue
                    f = open(f'{result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_{ind_}_infoX.txt', 'w')
                    f.write(f"""ID: {id_}\nModel: {gptmodel}\nMASKED? : No\nAnswer: {answer}({answer})\nInformation used: {reasoning}\nTriplets ratio:{ratio*100}%\nInfo:NO\nExplicitly asked to write information number: No\nquery:\nFill in the blank with the appropriate word.
There can be multiple [BLANK]s in a sentence. The same word should be inserted into all the [BLANK]s.
At the end of your response, include "Answer:" and write your final answer after it.

Question: {question}\n\n\nOutput:\n{justanswer}""")
                    f.close()
                    print(f"Saved results on {result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_{ind_}_infoX.txt")
                    result = check_answer(f'{result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_{ind_}_infoX.txt', answer)
                    if result[0] :
                        result_data_list[ratio_ind][line, 2 + model_ind] = 1
                    else:
                        result_data_list[ratio_ind][line, 2 + model_ind] = 0
                        wrong_content += f"""
id: {id_}, NOINFO UNMASKED, answer ind_: {ind_}, model: {gptmodel}
Answer: {answer}, Response: {result[1]}, ratio: {ratio}

"""
                    
                ###################### UNMASKED with information ###############################
                try:
                    with open(f'{root_path + qa_rootpath}query_prompt/{id_}_Qtriplet_ratio{int(ratio*100)}_unmasked.txt', 'r') as f:
                        query = f.read()
                        assert('[Information]' in query)
                        assert("Let's think step by step" in query)
                        query = f"""Fill in the blank with the appropriate word based on the [Information] provided below.
There can be multiple [BLANK]s in a sentence. The same word should be inserted into all the [BLANK]s.
At the end of your response, include "Answer:" and write your final answer after it.


[Question] {question}
[Information]
""" + query.split("[Information]")[1]
                except:
                    continue
                
                for model_ind, gptmodel in enumerate(models):
                    if os.path.isfile(f'{result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_{ind_}_infoO.txt'):
                        result = check_answer(f'{result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_{ind_}_infoO.txt', answer)
                        if result[0] :
                            result_data_list[ratio_ind][line, 4 + model_ind] = 1
                        else:
                            result_data_list[ratio_ind][line, 4 + model_ind] = 0
                            wrong_content += f"""
    id: {id_}, YESINFO UNMASKED, answer ind_: {ind_}, model: {gptmodel}
    Answer: {answer}, Response: {result[1]}, ratio: {ratio}
    
    """
                        continue
                    try:
                        justanswer = inference_azure(query, gptmodel)
                    except:
                        print(f"Error in query {query}. UNMASKED W/ INFO. model : {gptmodel}. ID : {id_}. ratio: {ratio}")
                        continue
                    f = open(f'{result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_{ind_}_infoO.txt', 'w')
                    f.write(f"""ID: {id_}\nModel: {gptmodel}\nMASKED? : No\nAnswer: {answer}({answer})\nInformation used: {reasoning}\nTriplets ratio:{ratio*100}%\nInfo:YES\nExplicitly asked to write information number: No\nquery:\nFill in the blank with the appropriate word based on the [Information] provided below.
There can be multiple [BLANK]s in a sentence. The same word should be inserted into all the [BLANK]s.
At the end of your response, include "Answer:" and write your final answer after it.


[Question] {question}\n\n\nOutput:\n{justanswer}""")
                    f.close()
                    print(f"Saved results on {result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_{ind_}_infoO.txt")
                    result = check_answer(f'{result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_{ind_}_infoO.txt', answer)
                    if result[0] :
                        result_data_list[ratio_ind][line, 4 + model_ind] = 1
                    else:
                        result_data_list[ratio_ind][line, 4 + model_ind] = 0
                        wrong_content += f"""
id: {id_}, YESINFO UNMASKED, answer ind_: {ind_}, model: {gptmodel}
Answer: {answer}, Response: {result[1]}, ratio: {ratio}

"""
                
                ###################### MASKED ######################
                with open(f'{root_path + qa_rootpath }entity_conversion/id_{id_}_entity_conversion_hash.json', "r") as f:
                    entity_conversion = json.load(f)
                converted_question = convert(question, entity_conversion)
                converted_answer = convert(answer, entity_conversion)
                with open(f'{root_path + qa_rootpath}query_prompt/{id_}_Qtriplet_ratio{int(ratio*100)}_masked.txt', 'r') as f:
                    query = f.read()
                    assert('[Information]' in query)
                    assert("Let's think step by step" in query)
                    query = f"""Fill in the blank with the appropriate word based on the [Information] provided below.
There can be multiple [BLANK]s in a sentence. The same word should be inserted into all the [BLANK]s.
At the end of your response, include "Answer:" and write your final answer after it.

[Question] {converted_question}
[Information]
""" + query.split("[Information]")[1]
                for model_ind, gptmodel in enumerate(models):
                    if os.path.isfile(f'{result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_MASKED_{ind_}_infoO.txt'):
                        result = check_answer(f'{result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_MASKED_{ind_}_infoO.txt', converted_answer)
                        if result[0] :
                            result_data_list[ratio_ind][line, 6 + model_ind] = 1
                        else:
                            result_data_list[ratio_ind][line, 6 + model_ind] = 0
                            wrong_content += f"""
    id: {id_}, YESINFO MASKED, answer ind_: {ind_}, model: {gptmodel}
    Answer: {converted_answer}, Response: {result[1]}, ratio: {ratio}
    
    """
                        continue
                    try:
                        justanswer = inference_azure(query, gptmodel)
                    except:
                        print(f"Error in query {query}. MASKED W/ INFO. model : {gptmodel}. ID : {id_}. ratio: {ratio}")
                        continue
                    f = open(f"{result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_MASKED_{ind_}_infoO.txt", 'w')
                    f.write(f"""ID: {id_}\nModel: {gptmodel}\nMASKED? : No\nAnswer: {converted_answer}({answer})\nInformation used: {reasoning}\nTriplets ratio:{ratio*100}%\nInfo:YES\nExplicitly asked to write information number: No\nquery:\nFill in the blank with the appropriate word based on the [Information] provided below.
There can be multiple [BLANK]s in a sentence. The same word should be inserted into all the [BLANK]s.
At the end of your response, include "Answer:" and write your final answer after it.

[Question] {converted_question}\n\n\nOutput:\n{justanswer}""")
                    f.close()
                    print(f"Saved results on {result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_MASKED_{ind_}_infoO.txt")
                    result = check_answer(f'{result_storedir}/blanked_question/full_result/{id_}_{int(ratio*100)}_{gptmodel}_MASKED_{ind_}_infoO.txt', converted_answer)
                    if result[0] :
                        result_data_list[ratio_ind][line, 6 + model_ind] = 1
                    else:
                        result_data_list[ratio_ind][line, 6 + model_ind] = 0
                        wrong_content += f"""
id: {id_}, YESINFO MASKED, answer ind_: {ind_}, model: {gptmodel}
Answer: {converted_answer}, Response: {result[1]}, ratio: {ratio}

"""
    now = str(datetime.datetime.now()).replace(" ", "-").replace(":", "-").split(".")[0]
    assert(not os.path.exists(f"{result_storedir}/blanked_question/organized_result/{now}"))
    os.makedirs(f"{result_storedir}/blanked_question/organized_result/{now}")
    for ratio_ind, ratio in enumerate(ratio_list):
        # convert array into dataframe 
        DF = pd.DataFrame(result_data_list[ratio_ind]) 
          
        # save the dataframe as a csv file 
        DF.to_csv(f"{result_storedir}/blanked_question/organized_result/{now}/BLANKEDquery_result_{int(100*ratio)}_{now}.csv")
        
    with open(f"{result_storedir}/blanked_question/organized_result/{now}/BLANKEDquery_wrong_{now}.txt", "w") as f:
        f.write(wrong_content)
    print(f"Saved results on {result_storedir}/blanked_question/organized_result/{now} folder.\n Check {result_storedir}/blanked_question/organized_result/{now}/BLANKEDquery_wrong_{now}.txt so that is there any wrong formatted answer.")
