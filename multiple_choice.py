import random
import requests
from format import *
from cpnet_wiki import get_node
from cpnet_wiki import check_all_en
from cpnet_wiki import extract_information
from cpnet_wiki import wiki_word_in_cpnet
from cpnet_wiki import get_redirect_url
from cpnet_wiki import get_redirect_keyword
from cpnet_wiki import entity_type
from cpnet_wiki import same_entity
from bs4 import BeautifulSoup
import string
from random_word import RandomWords

def check_matchscore(word1, word2):
    splitted1 = word1.split(" ")
    splitted2 = word2.split(" ")
    total_n = len(splitted1) * len(splitted2)
    count_n = 0
    for w1 in splitted1:
        for w2 in splitted2:
            if w1.lower() == w2.lower() or w1.lower() in w2.lower() or w2.lower() in w1.lower():
                count_n += 1
    return count_n / total_n

def category_from_word(word):
    url = get_redirect_url(word)
    response = requests.get(url)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    catlinks = soup.find('div', id='mw-normal-catlinks')
    if catlinks:
        categories = [cat.get_text() for cat in catlinks.find_all('a')]
        return categories
    else:
        return None

def search_parent(category):
    url = f'https://en.wikipedia.org/wiki/Category:{category.replace(" ", "_")}'
    response = requests.get(url)
    if response.status_code == 404:
        return None
    content = response.text
    
    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find the div for the category links at the bottom of the page
    catlinks = soup.find('div', {'id': 'mw-normal-catlinks'})
    if catlinks:
        # Find all 'a' tags within this div
        links = catlinks.find_all('a')
        # Extract the text for each category link
        categories = [link.text for link in links if link.get('href').startswith('/wiki/Category:')]
        return categories
    return []
    

def search_child(category):
    
    url = f'https://en.wikipedia.org/wiki/Category:{category.replace(" ", "_")}'
    response = requests.get(url)
    if response.status_code == 404:
        return None
    content = response.text
    
    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    
    # Function to extract links from a specific section
    def extract_links(section_title):
        # Find the div that contains the section title
        div = soup.find('div', id='mw-pages' if section_title == "Pages in category" else 'mw-subcategories')
        if div is None:
            return None
        # Find all 'a' tags within this div
        links = div.find_all('a')
        # Return a dictionary of link titles and URLs
        return {link.text: f"https://en.wikipedia.org{link.get('href')}" for link in links}

    subcat_links = extract_links("Subcategories")
    if subcat_links is None:
        return list()
    categories = [title for title, _ in subcat_links.items()]
    return categories

def search_page(category):
    url = f'https://en.wikipedia.org/wiki/Category:{category.replace(" ", "_")}'
    response = requests.get(url)
    if response.status_code == 404:
        return None
    content = response.text
    
    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    
    # Function to extract links from a specific section
    def extract_links(section_title):
        # Find the div that contains the section title
        div = soup.find('div', id='mw-pages' if section_title == "Pages in category" else 'mw-subcategories')
        if div is None:
            return None
        # Find all 'a' tags within this div
        links = div.find_all('a')
        # Return a dictionary of link titles and URLs
        return {link.text: f"https://en.wikipedia.org{link.get('href')}" for link in links}
    
    pages_links = extract_links("Pages in category")
    if pages_links is None:
        return list()
    page = list()
    for title, _ in pages_links.items():
        if len(title.split(" ")) > 6:
            continue
        page.append(title)
    return page

def choose_by_wiki_recur(answer, word, num, max_iter, entity_type):
    print(f"choose_by_wiki_recur({word})")
    if max_iter == 0:
        return []
    current_page = search_page(word)
    page_matchscore = [check_matchscore(word, page_t) for page_t in current_page]
    print(f"   Pages in {word}: {current_page}")
    final_choice = list()
    if sum(1 for score in page_matchscore if score < 0.3) >= num:
        ans = list()
        # print("CH1")
        for i in range(len(page_matchscore)):
            if page_matchscore[i] < 0.3:
                ans.append(current_page[i])

        # print("CH2")
        final_choice = random.sample(ans, num)
        for choice in final_choice:
            ans.remove(choice)

        # print("CH3")
        remove_list = list()
        for page_title in final_choice:
            print(f"      {page_title} in {final_choice}")
            # api_info = get_node(page_title)
            if not same_entity(entity_type, page_title) or get_redirect_keyword(answer) == get_redirect_keyword(page_title) or not wiki_word_in_cpnet(page_title) :
                remove_list.append(page_title)
                if len(ans) > 0:
                    new_choice = random.choice(ans)
                    ans.remove(new_choice)
                    final_choice.append(new_choice)
                
        # print("CH4")
        
        for remove_title in remove_list:
            final_choice.remove(remove_title)
        if len(final_choice) >= num:
            return final_choice
            
    
    upper_cat = search_parent(word)
    print(f"   Upper category of {word}: {upper_cat}")
    for parent in upper_cat:
        if check_matchscore(word, parent) >= 0.3:
            continue
        response = choose_by_wiki_recur(answer, parent, num, max_iter-1, entity_type)
        return response + final_choice
    #     if len(response) >= num:
    #         return response + final_choice
    return []

def choose_by_wiki(word, num, max_iter, entity_type):
    upper_cat = category_from_word(word)
    total_response = []
    if upper_cat is None:
        return []
    random.shuffle(upper_cat)
    for parent in upper_cat:
        if 'categories' in parent.lower():
            continue
        print(f"check_matchscore({word}, {parent}): ", check_matchscore(word, parent))
        if check_matchscore(word, parent) >= 0.6:
            continue
        response = choose_by_wiki_recur(word, parent, num, max_iter, entity_type)
        total_response += response
        if len(total_response) >= num:
            return total_response
    return total_response



def choiceword_list(start_word):
    word = format_for_cpnet(start_word)
    hierarchy_1_edge = list()
    hierarchy_2_edge = list()
    hierarchy_2_5_edge = list()
    hierarchy_3_edge = list()
    leftover = list()
    similar_words = list()
    for edge in get_node(word)['edges']:
        if not isinstance(edge, dict):
            continue
        if not check_all_en(edge):
            continue
        info = extract_information(edge)
        uri = info['uri']
        words = info['words']
        if uri == '/r/DistinctFrom/' or uri == '/r/Antonym/':
            hierarchy_1_edge.append(info)
        elif uri == '/r/LocatedNear/':
            hierarchy_2_edge.append(info)
        elif uri == '/r/PartOf/':
            if word == words[0]:
                hierarchy_2_edge.append(info)
        elif uri == '/r/IsA/' or uri == '/r/DerivedFrom/':
            if word == words[0]:
                hierarchy_3_edge.append(info)
        elif uri == '/r/Synonym/':
            if word == words[0]:
                similar_words.append(words[1])
            else:
                similar_words.append(words[0])
        else:
            leftover.append(info)

    choice_list = list()

    for info in hierarchy_1_edge:
        uri = info['uri']
        words = info['words']
        # Both Type A
        if words[0] == word:
            choice_word = words[1]
        else:
            choice_word = words[0]
        if choice_word in similar_words:
            continue
        choice_list.append(choice_word)
    choice_list = list(set(choice_list))
    if len(choice_list) >= 4:
        print("Ended after 1 hierarchy")
        return (1, choice_list)

    for info in hierarchy_2_edge:
        uri = info['uri']
        words = info['words']
        if uri == '/r/LocatedNear/':
            # Type A
            if words[0] == word:
                choice_word = words[1]
            else:
                choice_word = words[0]
            if choice_word in similar_words:
                continue
            choice_list.append(choice_word)
        else:
            # /r/Partof
            # Type B
            center_word = words[1]
            obj = get_node(center_word)
            for edge in obj['edges']:
                if not isinstance(edge, dict):
                    continue
                if not check_all_en(edge):
                    continue
                info = extract_information(edge)
                if info['uri'] == '/r/PartOf/':
                    if not word == info['words'][0] and center_word == info['words'][1] and info['words'][0] not in similar_words:
                        choice_list.append(info['words'][0])
    choice_list = list(set(choice_list))
    if len(choice_list) >= 4:
        print("Ended after 2 hierarchy")
        return (2, choice_list)

    ## Put hints chosen by wiki
    needed  = 4 - len(choice_list)
    print(choice_list)
    entity_T = entity_type(start_word)
    assert(entity_T is not None)
    choice_list += choose_by_wiki(start_word, needed, 1, entity_T)
    print(choice_list)
    choice_list = list(set(choice_list))
    if len(choice_list) >= 4:
        print("Ended after 2.5 hierarchy")
        return (2.5, choice_list)
    
    for info in hierarchy_3_edge:
        uri = info['uri']
        words = info['words']
        # /r/Partof
        # Type B
        center_word = words[1]
        obj = get_node(center_word)
        for edge in obj['edges']:
            if not isinstance(edge, dict):
                continue
            if not check_all_en(edge):
                continue
            info = extract_information(edge)
            if not word == info['words'][0] and center_word == info['words'][1] and info['words'][0] not in similar_words:
                choice_list.append(info['words'][0])

    choice_list = list(set(choice_list))
    if len(choice_list) >= 4:
        print("Ended after 3 hierarchy")
        return (3, choice_list)
    else:
        print(f"To little valid choices in Conceptnet. {4- (len(choice_list))} random words will be generated")
        lacking_wordN = 4- len(choice_list)
        i = 0
        while True:
            if i >= lacking_wordN:
                break
            r = RandomWords()
            randomW = r.get_random_word()
            obj = get_node(format_for_cpnet(randomW))
            if randomW in choice_list or 'error' in obj.keys() or 'edges' not in obj.keys() or len(obj['edges']) == 0:
                continue
            url = get_redirect_url(randomW)
            response = requests.get(url)
            if response.status_code == 404:
                continue
            choice_list.append(randomW)
            i += 1
    choice_list = list(set(choice_list))
    assert(len(choice_list) >= 4)
    return (-lacking_wordN, choice_list)

def random_choices(choice_list, answer, choice_level, options = 5):
    alphabet = list(string.ascii_uppercase)
    answer_key = random.randint(0, options-1)
    final_choice = random.sample(choice_list, options-1)
    final_choice.insert(answer_key, answer)
    choices = []
    for i in range(len(final_choice)):
        option = dict()
        option["label"] = alphabet[i]
        option["text"] = final_choice[i].replace("_", " ").capitalize()
        choices.append(option)
    return {"choices": choices, "answerKey": alphabet[answer_key], "choicelevel": choice_level}


def final_choice(answer, options = 5):
    print(f"final_choice({answer}, options = {options}) started")
    choice_list = choiceword_list(answer)
    print(choice_list)
    print()
    return (random_choices(choice_list[1], answer, choice_list[0], options))

