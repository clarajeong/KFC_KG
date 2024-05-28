
def format_for_cpnet(word):
    ans = word.lower().replace(" ", "_").replace(".", "")
    if "a_" == ans[:2]:
        return ans[2:]
    elif "an_" == ans[:3]:
        return ans[3:]
    elif "the_" == ans[:4]:
        return ans[4:]
    return ans


def format_for_wiki(word):
    # return word.capitalize().replace(" ", "_")
    return word.replace(" ", "_")


def format_from_edge(edge):
    if 'surfaceText' in edge.keys() and edge['surfaceText'] is not None:
        sentence = edge['surfaceText'].replace("[[", '')
        sentence = sentence.replace("]]", '')
        return sentence
    start_word = edge['start']['@id'].split('/')[3]
    end_word = edge['end']['@id'].split('/')[3]
    relation = edge['rel']['label']

    start_word = start_word.replace("_", " ")
    end_word = end_word.replace("_", " ")
    switched = False
    
    if relation == 'RelatedTo':
        relation = "is related to"
    elif relation == 'FormOf':
        relation = "is a form of"
    elif relation == 'IsA':
        relation = "is a"
    elif relation == 'PartOf':
        relation = 'is part of'
    elif relation == 'HasA':
        relation = 'has a'
    elif relation == 'UsedFor':
        relation = 'is used for'
    elif relation == 'CapableOf':
        relation = 'is capable of'
    elif relation == 'AtLocation':
        relation = 'is a location for'
    elif relation == 'Causes':
        relation = 'causes'
    elif relation == 'HasSubevent':
        relation = 'happens as a subevent of'
    elif relation == 'HasFirstSubevent':
        relation = 'begins with'
    elif relation == 'HasLastSubevent':
        relation = 'ends with'
    elif relation == 'HasPrerequisite':
        switched = True
        relation = 'needs to happen for'
    elif relation == 'HasProperty':
        relation = "is"
    elif relation == 'MotivatedByGoal':
        relation = 'is a step toward accomplishing the goal'
    elif relation == 'ObstructedBy':
        relation = 'is a goal that can be prevented by'
    elif relation == 'Desires':
        relation = 'is a conscious entity that typically wants'
    elif relation == 'CreatedBy':
        switched = True
        relation = 'is a process or agent that creates'
    elif relation == 'Synonym':
        relation = 'is a synonym of'
    elif relation == 'Antonym':
        relation = 'is an antonym of'
    elif relation == 'DistinctFrom':
        relation = 'is distinct from'
    elif relation == 'DerivedFrom':
        relation = 'is derived from'
    elif relation == 'SymbolOf':
        relation = 'is a symbol of'
    elif relation == 'DefinedAs':
        relation = 'is defined as'
    elif relation == 'MannerOf':
        relation = 'is a specific way to do'
    elif relation == 'LocatedNear':
        relation = 'is located near'
    elif relation == 'HasContext':
        relation = 'is a word used in the context of'
    elif relation == 'SimilarTo':
        relation = 'is similar to'
    elif relation == 'EtymologicallyRelatedTo':
        relation = 'has a common origin with'
    elif relation == 'EtymologicallyDerivedFrom':
        relation = 'is derived from'
    elif relation == 'CausesDesire':
        relation = 'makes someone want'
    elif relation == 'MadeOf':
        relation = 'is made of'
    elif relation == 'ReceivesAction':
        switched = True
        relation = 'can be done to'
    elif relation == 'ExternalURL':
        relation = '<URL>'
    else:
        relation = relation
    
    if switched:
        return f'{end_word} {relation} {start_word}'
    return f'{start_word} {relation} {end_word}'

