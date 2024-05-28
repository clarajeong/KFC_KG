import requests
from format import *
from dir_path import *
import os
from bs4 import BeautifulSoup


root_path = os.path.abspath(os.sep)

# The result of get_node() is this
# [ERROR]
# {'@context': ['http://api.conceptnet.io/ld/conceptnet5.7/context.ld.json'], 
#  '@id': '/c/en/lincolnnnnn', 
#  'edges': [], 
#  'error': {'details': "'/c/en/lincolnnnnn' is not a node in ConceptNet.", 'status': 404},
#  'version': '5.8.1'}

# [NORMAL]
# {'@context': ['http://api.conceptnet.io/ld/conceptnet5.7/context.ld.json'], 
# '@id': '/c/en/apple', 
# 'edges': [{
#     '@id': '/a/[/r/RelatedTo/,/c/en/apple/,/c/en/fruit/]', 
#     '@type': 'Edge', 
#     'dataset': '/d/verbosity', 
#     'end': {
#         '@id': '/c/en/fruit', 
#         '@type': 'Node', 
#         'label': 'fruit', 
#         'language': 'en', 
#         'term': '/c/en/fruit'}, 
#     'license': 'cc:by/4.0', 
#     'rel': {
#         '@id': '/r/RelatedTo', 
#         '@type': 'Relation', 
#         'label': 'RelatedTo'},
#     'sources': [{
#         '@id': '/and/[/s/process/split_words/,/s/resource/verbosity/]', 
#         '@type': 'Source', 
#         'contributor': '/s/resource/verbosity', 
#         'process': '/s/process/split_words'}, ... ], 
#     'start': {
#         '@id': '/c/en/apple', 
#         '@type': 'Node', 
#         'label': 'apple', 
#         'language': 'en', 
#         'term': '/c/en/apple'}, 
#     'surfaceText': '[[apple]] is related to [[fruit]]', 
#     'weight': 12.80968383684781
#    }, ... ], 
#  'version': '5.8.1'}
   

# Put word as input
def get_node(word):
    obj = requests.get(f'http://api.conceptnet.io/c/en/{word}?offset=0&limit=10000').json()
    return obj


def extract_information(edge):
    uri = edge['rel']['@id']
    start = edge['start']['@id'].split('/')[3]
    end = edge['end']['@id'].split('/')[3]
    return {'id': edge['@id'], 'uri': uri, 'words': (start, end)}


def check_all_en(edge):
    if 'language' in edge['start'].keys() and 'language' in edge['end'].keys():
        if edge['start']['language'] == 'en' and edge['end']['language'] == 'en':
            return True
    return False


# edge_id is the id of the edge
def get_edge(edge_id):
    obj = requests.get(f'http://api.conceptnet.io{edge_id}').json()
    return obj


# This returns boolean & its information.
# This checks whether "target" is the end word of node_list
def navigate(target, node_list):
    for word, prev, edge_id in node_list:
        if word == target:
            return True, prev, edge_id
    return False, None, None



def print_info(relations):
    for route_id in routes:
        obj = get_edge(route_id)
        sentence = format_from_edge(obj)
        print(sentence)



# This returns list of edge_id of first word to "start" word
# "start" should be the "end" word of the last element of node_listlist.
def track(start, node_listlist):
    def track_recurs(word, curr_ind):
        if curr_ind == 0:
            return list()
        else:
            check, prev, edge_id = navigate(word, node_listlist[curr_ind ])
            assert(check)
            new_list = track_recurs(prev, curr_ind - 1) + [edge_id]
            return new_list
    return track_recurs(start, len(node_listlist)-1)



# Node 1, Node 2 주어짐
# Node 1과 2는 모두 conceptnet에 있어야 함
# Return: 가장 짧은 route의 edge list를 return

# Implementation
# Node 1, Node 2가 conceptnet에 있는지 체크
# Node 1에서 먼저 next level check
# 이후 Node 2 
# ... 반복
def find_bestroute(word1, word2, max_depth = None):
    # word1, word2 should be in conceptnet
    print(f"\nfind_bestroute({word1}, {word2}, {max_depth}) Start")
    if word1 == word2:
        return list()
    
    front_listlist = list()
    back_listlist = list()
    
    # Element Type: (currentword, previousword, edge_id)
    front_list = [(word1, None, None)]
    back_list = [(word2, None, None)]
    
    front_listlist.append(front_list)
    back_listlist.append(back_list)
    
    bridge = None
    
    
    depth = 0
    front_route = None
    back_route = None
    
    route_found = False
    while not route_found:
        depth += 1
        if max_depth is not None and depth > max_depth:
            return None
        print(f"Depth is {depth}")
        
        # First node
        front_list = list()
        for (front_word, _, _) in front_listlist[-1]:
            print(f"front word is: {front_word}")
            
            obj = get_node(front_word)
            for i in range(len(obj['edges'])):
                if check_all_en(obj['edges'][i]):
                    info = extract_information(obj['edges'][i])
                    # if not (front_word == info['words'][0] or front_word == info['words'][1]):
                    #     continue
                    assert(front_word == info['words'][0] or front_word == info['words'][1])
                    if front_word == info['words'][0]:
                        next_word = info['words'][1]
                    else:
                        next_word = info['words'][0]
                    
                    check, prev, edge_id = navigate(next_word, back_list)
                    if check:
                        # Found the route!
                        front_route = track(front_word, front_listlist) + [info['id']]
                        back_route = track(next_word, back_listlist)
                        route_found = True
                        break
                    
                    front_list.append((next_word, front_word, info['id']))
            if route_found:
                break
        if route_found:
            break
        front_listlist.append(front_list)
        
        # Second node
        back_list = list()
        for (back_word, _, _) in back_listlist[-1]:
            print(f"back word is: {back_word}")
            obj = get_node(back_word)
            for i in range(len(obj['edges'])):
                if check_all_en(obj['edges'][i]):
                    info = extract_information(obj['edges'][i])
                    # if not (back_word == info['words'][0] or back_word == info['words'][1]):
                    #     continue
                    assert(back_word == info['words'][0] or back_word == info['words'][1])
                    if back_word == info['words'][0]:
                        next_word = info['words'][1]
                    else:
                        next_word = info['words'][0]
                    
                    check, prev, edge_id = navigate(next_word, front_list)
                    if check:
                        # Found the route!
                        front_route = track(back_word, back_listlist)
                        back_route = track(next_word, front_listlist) + [info['id']]
                        route_found = True
                        break
                    
                    back_list.append((next_word, back_word, info['id']))
            if route_found:
                break
        if route_found:
            break
        back_listlist.append(back_list)
    print(f"\nfind_bestroute({word1}, {word2}, {max_depth}) Done")
    return front_route + back_route



# Given list of words,
# For Time efficiency, save paths that were already passed.
# In this case, max depth is recommended.
def find_bestroute_cross_twoedge(wordlist, one_edge = False, weight_limit = 1.0):
    
    def check_weightlimit_ok(edge):
        if 'weight' in edge.keys():
            if edge['weight'] > weight_limit:
                return True
        return False
    
    # "panda" : [{"child": animal, "id": 'blahblah'}, {, }, ...]
    word_tree = dict()
    bestroutes = list()
    
    for i in range(len(wordlist)):
        for j in range(i + 1, len(wordlist)):
            
            word1 = wordlist[i]
            word2 = wordlist[j]
            
            # print(f"\nword1 is {word1}, word2 is {word2}.")
            
            find_bestroute = False
            front_list = None
            back_list = None
            
            # word1, word2 should be in conceptnet
            
            if word1 in word_tree.keys():
                # word1 child information is found.
                front_list = word_tree[word1]
                
                # Check for one edge route
                for word1_childinfo in front_list:
                    if word1_childinfo["child"] == word2:
                        print(f"One edge route between {word1} and {word2} found!")
                        bestroutes.append(word1_childinfo["id"])
                        find_bestroute = True
                        break
                if find_bestroute:
                    continue
                
                # Check for two edge route
                if not one_edge:
                    if word2 in word_tree.keys():
                        # word1, word2 child information is found
                        back_list = word_tree[word2]
                        for word1_childinfo in front_list:
                            for word2_childinfo in back_list:
                                if word1_childinfo["child"] == word2_childinfo["child"]:
                                    # word1 child and word2 child has word in common
                                    print(f"Two edge route between {word1} and {word2} found!")
                                    find_bestroute = True
                                    bestroutes.append(word1_childinfo["id"])
                                    bestroutes.append(word2_childinfo["id"])
                                    break
                            if find_bestroute:
                                break
                        continue
                                
                    else:
                        # word1 child information is found. word2 child information is not found
                        pass
                    
            elif word2 in word_tree.keys():
                # word2 child information is found. word1 child information is not found.
                
                temp = word1
                word1 = word2
                word2 = temp
                # word1 and word2 is swapped, for convenience in coding
                
                front_list = word_tree[word1]
                
                # Check for one edge route
                for word1_childinfo in front_list:
                    if word1_childinfo["child"] == word2:
                        print(f"One edge route between {word1} and {word2} found!")
                        bestroutes.append(word1_childinfo["id"])
                        find_bestroute = True
                        break
                if find_bestroute:
                    continue
                
                if one_edge:
                    continue
                
            else:
                # word1, word2 child information is not found. 
                pass
            
            
            if front_list is None:
                # word1, word2 child information is both not found. 
                
                obj = get_node(word1)
                temp = list()
                
                for k in range(len(obj['edges'])):
                    if check_all_en(obj['edges'][k]) and check_weightlimit_ok(obj['edges'][k]):
                        info = extract_information(obj['edges'][k])
                        assert(word1 == info['words'][0] or word1 == info['words'][1])
                        if word1 == info['words'][0]:
                            next_word = info['words'][1]
                        else:
                            next_word = info['words'][0]
                        
                        
                        if next_word == word2:
                            # found one edge!
                            print(f"One edge route between {word1} and {word2} found!")
                            find_bestroute = True
                            bestroutes.append(info['id'])
                            break
                        
                        temp.append({"child":next_word, "id":info['id']})
                if find_bestroute:
                    continue
                
                
                word_tree[word1] = temp.copy()
                front_list = word_tree[word1]
            
            if not one_edge:
                # We made front_list, but there is no one-edge route. 
                # Let's find back_list and find two-edge route.
                
                # There is front_list, but there is no back_list
                assert(back_list is None)
                obj = get_node(word2)
                temp = list()
                
                for k in range(len(obj['edges'])):
                    if check_all_en(obj['edges'][k]) and check_weightlimit_ok(obj['edges'][k]):
                        info = extract_information(obj['edges'][k])
                        assert(word2 == info['words'][0] or word2 == info['words'][1])
                        if word2 == info['words'][0]:
                            next_word = info['words'][1]
                        else:
                            next_word = info['words'][0]

                        for word1_childinfo in front_list:
                            if next_word == word1_childinfo["child"]:
                                # found two edge!
                                print(f"Two edge route between {word1} and {word2} found!")
                                find_bestroute = True
                                bestfroutes.append(word1_childinfo["id"])
                                bestroutes.append(info['id'])
                                break
                        if find_bestroute:
                            break
                        
                        temp.append({"child": next_word, "id": info['id']})
                word_tree[word2] = temp.copy()
            
    return bestroutes



def api_extract_relation(wordlistlist, max_depth = 3):
    relationlist = list()
    formatlist = list()
    
    sentence = 0
    for wordlist in wordlistlist:
        sentence += 1
        print(f"sentence {sentence}: {wordlist}")
        for i in range(len(wordlist)):
            for j in range(i + 1, len(wordlist)):
                obj = requests.get(f'http://api.conceptnet.io/query?node=/c/en/{wordlist[i]}&other=/c/en/{wordlist[j]}').json()
                if len(obj['edges']) <= max_depth:
                    for edge in obj['edges']:
                        if not edge['@id'] in relationlist:
                            relationlist.append(edge['@id'])
                            formatlist.append(format_from_edge(edge))
    return {'relation': relationlist, 'format': formatlist}



def wiki_word_in_cpnet(word):
    # print("word: ", word)
    try:
        cpnet_obj = requests.get(f'http://api.conceptnet.io/c/en/{format_for_cpnet(word)}?offset=0&limit=10').json()
    
    except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError) as e:
        print(f"Error: {e}")
        return None
    if not "error" in cpnet_obj.keys() and ("edges" in cpnet_obj.keys() and len(cpnet_obj["edges"]) > 0):
        return format_for_cpnet(word)
    
    
    wiki_obj = requests.get(f'https://en.wikipedia.org/w/api.php?action=query&format=json&list=backlinks&bltitle={format_for_wiki(get_redirect_keyword(word))}&blfilterredir=redirects').json()
    # print("format_for_wiki(word): ", format_for_wiki(word))
    # print("wiki_obj: ", wiki_obj)
    redirect_words = list()
    if 'query' in wiki_obj.keys() and 'backlinks' in wiki_obj['query'].keys() :
        redirect_words = [info['title'] for info in wiki_obj['query']['backlinks']]
    
    for re_word in redirect_words:
        try:
            cpnet_obj = requests.get(f'http://api.conceptnet.io/c/en/{format_for_cpnet(re_word)}?offset=0&limit=10').json()
        except (requests.exceptions.RequestException, requests.exceptions.JSONDecodeError) as e:
            print(f"Error: {e}")
            return None
        if not "error" in cpnet_obj.keys() or ("edges" in cpnet_obj.keys() and len(cpnet_obj["edges"]) > 0):
            return format_for_cpnet(re_word)
    return None



def wiki_word_list_in_cpnet(word_list):
    word_pair_list = list()
    for word in word_list:
        cpnet_word = wiki_word_in_cpnet(word)
        if cpnet_word is not None:
            word_pair_list.append((word, cpnet_word))
    return word_pair_list


def get_redirect_url(keyword):
    keyword = get_redirect_keyword(keyword).replace("_", " ")
    start_url = f"https://en.wikipedia.org/wiki/{keyword}"
    response = requests.get(start_url)
    return response.url

# def get_redirect_keyword(keyword):
#     redirect_url = get_redirect_url(keyword.replace("_", " "))
#     if "wiki/" not in redirect_url:
#         print(f"cpnet_wiki.py get_redirect_keyword(): Error. 'wiki/' not in {redirect_url}.")
#         return None
#     return redirect_url.split("wiki/")[1].split('/')[0].replace("_", " ")

def get_redirect_keyword(keyword):
    
    # Start a session
    S = requests.Session()
    
    # Specify the API endpoint
    URL = "https://en.wikipedia.org/w/api.php"
    
    # Set the parameters for the initial search
    SEARCH_PARAMS = {
        'action': 'query',
        'format': 'json',
        'list': 'search',
        'srsearch': keyword  # The search term
    }
    
    # Make the GET request for the search
    search_data = S.get(url=URL, params=SEARCH_PARAMS).json()
    
    # Checking if there are search results
    if search_data['query']['search']:
        title = search_data['query']['search'][0]['title']
        return title
    else:
        return keyword


def find_coordinates(wiki_url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful

        soup = BeautifulSoup(response.content, 'html.parser')

        # Find the coordinates link
        coordinates_link = soup.find('a', {'href': '/wiki/Geographic_coordinate_system'})
        
        # Check if this link is part of a parent element that contains "Coordinates:" text
        if coordinates_link and "Coordinates:" in coordinates_link.parent.text:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return False

def test_geo(entity):
    url = f'https://en.wikipedia.org/wiki/{entity.replace(" ", "_")}'
    return find_coordinates(url)

def has_scientific_classification(wiki_title):
    url = f"https://en.wikipedia.org/wiki/{wiki_title}"
    response = requests.get(url)
    
    if response.status_code != 200:
        return False

    soup = BeautifulSoup(response.text, 'html.parser')
    # Looking for the link that leads to 'Taxonomy (biology)' which is usually part of the scientific classification box
    taxonomy_link = soup.find('a', title="Taxonomy (biology)")
    
    if taxonomy_link:
        infobox = soup.find('table', class_='infobox')
        if not infobox:
            return False
    
        # Iterate through rows in the infobox looking for Kingdom entry
        for row in infobox.find_all('tr'):
            header = row.find('td')
            if header is None:
                header = row.find('th')
            if header and ('Kingdom' in header.text or 'Domain' in header.text):
                return True
        return False
    else:
        return False

def test_animal(entity):
    return has_scientific_classification(entity)


def test_people(entity):
    url = f'https://en.wikipedia.org/wiki/{format_for_wiki(entity)}'
    # Fetch the content of the page
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the infobox (right column on Wikipedia pages)
    infobox = soup.find('table', class_='infobox vcard')
    if infobox:
        # Extract all rows in the infobox
        rows = infobox.find_all('tr')
        for row in rows:
            # Check if the row contains 'Born' in its first column
            if 'Born' in row.text:
                # Extract and return the text from this row
                return True

    return False


def test_incident(entity):
    url = f'https://en.wikipedia.org/wiki/{format_for_wiki(entity)}'
    # Fetch the content of the page
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the infobox (right column on Wikipedia pages)
    infobox = soup.find('table', class_='infobox vcard')
    if infobox:
        # Extract all rows in the infobox
        rows = infobox.find_all('tr')
        for row in rows:
            # Check if the row contains 'Born' in its first column
            if 'Date' in row.text or 'Location' in row.text:
                # Extract and return the text from this row
                return True

    return False


def check_goodentity(entity, no_incident =False):
    wiki_url = get_redirect_url(entity)
    try:
        # Fetch the Wikipedia page
        response = requests.get(wiki_url)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Geography
        # Look for the coordinates in the 'geo' class
        geo_tag = soup.find(class_='geo')
        if geo_tag:
            print(f"{entity} is Geography")
            return True
        
        # Animal
        taxonomy_link = soup.find('a', title="Taxonomy (biology)")
        
        if taxonomy_link:
            infobox = soup.find('table', class_='infobox')
            
            if infobox:
                # Iterate through rows in the infobox looking for Kingdom entry
                for row in infobox.find_all('tr'):
                    header = row.find('td')
                    if header is None:
                        header = row.find('th')
                    if header and ('Kingdom' in header.text or 'Domain' in header.text):
                        print(f"{entity} is Animal")
                        return True

        # People
        # Find the infobox (right column on Wikipedia pages)
        infobox = soup.find('table', class_='infobox vcard')
        if infobox is None:
            infobox = infobox = soup.find(class_='infobox-label')
            if infobox:
                if 'Born' in infobox.text:
                    print(f"{entity} is People")
                    return True
        else:
            # Extract all rows in the infobox
            rows = infobox.find_all('tr')
            for row in rows:
                # Check if the row contains 'Born' in its first column
                if 'Born' in row.text:
                    # Extract and return the text from this row
                    print(f"{entity} is People")
                    return True
        if no_incident:
            return False
        # Incident
        infobox = soup.find('table', class_='infobox vcard')
        if infobox:
            # Extract all rows in the infobox
            rows = infobox.find_all('tr')
            for row in rows:
                # Check if the row contains 'Born' in its first column
                if 'Date' in row.text or 'Location' in row.text:
                    # Extract and return the text from this row
                    print(f"{entity} is Incident")
                    return True
        return False
    except requests.RequestException as e:
        return False
    
def entity_type(entity):
    print(f"entity_type({entity}) called")
    wiki_url = get_redirect_url(entity)
    try:
        # Fetch the Wikipedia page
        response = requests.get(wiki_url)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        # print(soup)

        # Geography
        # Look for the coordinates in the 'geo' class
        geo_tag = soup.find(class_='geo')
        if geo_tag:
            print(f"{entity} is Geography")
            return "Geography"
        
        # Animal
        taxonomy_link = soup.find('a', title="Taxonomy (biology)")
        
        if taxonomy_link:
            infobox = soup.find('table', class_='infobox')
            
            if infobox:
                # Iterate through rows in the infobox looking for Kingdom entry
                for row in infobox.find_all('tr'):
                    header = row.find('td')
                    if header is None:
                        header = row.find('th')
                    if header and ('Kingdom' in header.text or 'Domain' in header.text):
                        print(f"{entity} is Animal")
                        return "Animal"

        # People
        # Find the infobox (right column on Wikipedia pages)
        
        infobox = soup.find('table', class_='infobox vcard')
        if infobox is None:
            infobox = infobox = soup.find(class_='infobox-label')
            if infobox:
                if 'Born' in infobox.text:
                    print(f"{entity} is People")
                    return "People"
        else:
            
            # Extract all rows in the infobox
            rows = infobox.find_all('tr')
            for row in rows:
                # Check if the row contains 'Born' in its first column
                if 'Born' in row.text:
                    # Extract and return the text from this row
                    print(f"{entity} is People")
                    return "People"
        # Incident
        infobox = soup.find('table', class_='infobox vcard')
        if infobox:
            # Extract all rows in the infobox
            rows = infobox.find_all('tr')
            for row in rows:
                # Check if the row contains 'Born' in its first column
                if 'Date' in row.text or 'Location' in row.text:
                    # Extract and return the text from this row
                    print(f"{entity} is Incident")
                    return "Incident"
        return None
    except requests.RequestException as e:
        return False

def same_entity(entity_type, entity):
    if entity_type is None:
        return False
    if entity_type == "Geography":
        return True
    if entity_type == "Incident":
        return True
    wiki_url = get_redirect_url(entity)
    try:
        # Fetch the Wikipedia page
        response = requests.get(wiki_url)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        if entity_type == "Animal":
            # Animal
            taxonomy_link = soup.find('a', title="Taxonomy (biology)")
            
            if taxonomy_link:
                infobox = soup.find('table', class_='infobox')
                
                if infobox:
                    # Iterate through rows in the infobox looking for Kingdom entry
                    for row in infobox.find_all('tr'):
                        header = row.find('td')
                        if header is None:
                            header = row.find('th')
                        if header and ('Kingdom' in header.text or 'Domain' in header.text):
                            print(f"{entity} is Animal")
                            return True

        elif entity_type == "People":
            # People
            # Find the infobox (right column on Wikipedia pages)
            infobox = soup.find('table', class_='infobox vcard')
            if infobox is None:
                infobox = infobox = soup.find(class_='infobox-label')
                if infobox:
                    if 'Born' in infobox.text:
                        print(f"{entity} is People")
                        return True
            else:
                # Extract all rows in the infobox
                rows = infobox.find_all('tr')
                for row in rows:
                    # Check if the row contains 'Born' in its first column
                    if 'Born' in row.text:
                        # Extract and return the text from this row
                        print(f"{entity} is People")
                        return True
        return False
    except requests.RequestException as e:
        return False
    