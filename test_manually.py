from gpt_query import inference_azure
from dir_path import *
import os
import json



root_path = os.path.abspath(os.sep)


def check_answer(result_path, answer):
    with open(result_path, "r") as file:
        result = file.read()
        response_ans = result.split("Answer:")[-1]
        if response_ans[0] == " ": 
            response_ans = response_ans[1:]
        if int(response_ans) == int(answer):
            return (True, None)
        else:
            return (False, response_ans)


def ask_gpt_manually(q_ids, ratio_list = [1, 0.5, 0.25], models = ['gpt-35-turbo-1106', 'gpt-4-1106-Preview']):
    temp = open(f'{root_path + qa_rootpath}result/openai_LLM/multiple_choice/temporary.txt', 'w')
    
    for id_ in q_ids:
        with open(root_path + qa_rootpath + "qa/QA.json", "r") as file:
            data = json.load(file)
        question_info = None
        for element in data:
            # print(id_, element["id"], id_ == element["id"])
            if id_ == element["id"]:
                question_info = element
                break
        assert(question_info is not None)

        answer = question_info['Multiple_choice_wiki']['answerKey']
        
        for ratio in ratio_list:
            reasoning = question_info["Question_triplet_answer"][str(int(ratio*100))]
            try:
                with open(f'{root_path + qa_rootpath}query_prompt/{id_}_Qtriplet_ratio{int(ratio*100)}_unmasked.txt', 'r') as f:
                    query = f.read()
                    assert('[Information]' in query)
                    assert("Let's think step by step" in query)
            except:
                continue
            
            
            for gptmodel in models:
                justanswer = inference_azure(query, gptmodel)
                f = open(f'{root_path + qa_rootpath}result/openai_LLM/multiple_choice/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_onlyanswer.txt', 'w')
                f.write(f"Model: {gptmodel}\nMASKED? : No\nAnswer: {answer}\nInformation used: {reasoning}\nTriplets ratio:{ratio*100}%\nExplicitly asked to write information number: No\nquery:\n{query.split('[Information]')[0]}\n\nOutput:{justanswer}")
                f.close()
                print(f"Saved results on {root_path + qa_rootpath}result/openai_LLM/multiple_choice/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_onlyanswer.txt")
                temp.write("\n=============\n")
                temp.write(f"Model: {gptmodel}\nMASKED? : No\nAnswer: {answer}\nInformation used: {reasoning}\nTriplets ratio:{ratio*100}%\nExplicitly asked to write information number: No\nquery:\n{query.split('[Information]')[0]}\n\nOutput:{justanswer}")

                new_query = query.split("Let's think step by step")[0] + '''Please write what information you used in our given information by writing information number. Write minimal but essential information you used in solving this problem.
Let's think step by step'''
                answer_with_info = inference_azure(new_query, gptmodel)
                f = open(f'{root_path + qa_rootpath}result/openai_LLM/multiple_choice/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_with_reasoning.txt', 'w')
                f.write(f"Model: {gptmodel}\nMASKED? : No\nAnswer: {answer}\nInformation used: {reasoning}\nTriplets ratio:{ratio*100}%\nExplicitly asked to write information number: Yes\nquery:\n{query.split('[Information]')[0]}\n\nOutput:{answer_with_info}")
                f.close()
                print(f"Saved results on {root_path + qa_rootpath}result/openai_LLM/multiple_choice/{id_}_{int(ratio*100)}_{gptmodel}_UNMASKED_with_reasoning.txt")
                temp.write("\n=============\n")
                temp.write(f"Model: {gptmodel}\nMASKED? : No\nAnswer: {answer}\nInformation used: {reasoning}\nTriplets ratio:{ratio*100}%\nExplicitly asked to write information number: Yes\nquery:\n{query.split('[Information]')[0]}\n\nOutput:{answer_with_info}")
        
            with open(f'{root_path + qa_rootpath}query_prompt/{id_}_Qtriplet_ratio{int(ratio*100)}_masked.txt', 'r') as f:
                query = f.read()
                assert('[Information]' in query)
                assert("Let's think step by step" in query)
            
            for gptmodel in models:
                justanswer = inference_azure(query, gptmodel)
                f = open(f'{root_path + qa_rootpath}result/openai_LLM/multiple_choice/{id_}_{int(ratio*100)}_{gptmodel}_MASKED_onlyanswer.txt', 'w')
                f.write(f"Model: {gptmodel}\nMASKED? : Yes\nAnswer: {answer}\nInformation used: {reasoning}\nTriplets ratio:{ratio*100}%\nExplicitly asked to write information number: No\nquery:\n{query.split('[Information]')[0]}\n\nOutput:{justanswer}")
                f.close()
                print(f"Saved results on {root_path + qa_rootpath}result/openai_LLM/multiple_choice/{id_}_{int(ratio*100)}_{gptmodel}_MASKED_onlyanswer.txt")
                temp.write("\n=============\n")
                temp.write(f"Model: {gptmodel}\nMASKED? : Yes\nAnswer: {answer}\nInformation used: {reasoning}\nTriplets ratio:{ratio*100}%\nExplicitly asked to write information number: No\nquery:\n{query.split('[Information]')[0]}\n\nOutput:{justanswer}")

                new_query = query.split("Let's think step by step")[0] + '''Please write what information you used in our given information by writing information number.
Let's think step by step'''
                answer_with_info = inference_azure(new_query, gptmodel)
                f = open(f'{root_path + qa_rootpath}result/openai_LLM/multiple_choice/{id_}_{int(ratio*100)}_{gptmodel}_MASKED_with_reasoning.txt', 'w')
                f.write(f"Model: {gptmodel}\nMASKED? : Yes\nAnswer: {answer}\nInformation used: {reasoning}\nTriplets ratio:{ratio*100}%\nExplicitly asked to write information number: Yes\nquery:\n{query.split('[Information]')[0]}\n\nOutput:{answer_with_info}")
                f.close()
                print(f"Saved results on {root_path + qa_rootpath}result/openai_LLM/multiple_choice/{id_}_{int(ratio*100)}_{gptmodel}_MASKED_with_reasoning.txt")
                temp.write("\n=============\n")
                temp.write(f"Model: {gptmodel}\nMASKED? : Yes\nAnswer: {answer}\nInformation used: {reasoning}\nTriplets ratio:{ratio*100}%\nExplicitly asked to write information number: Yes\nquery:\n{query.split('[Information]')[0]}\n\nOutput:{answer_with_info}")
    temp.close()