import pandas as pd
import ast
import re
import numpy as np
from spellchecker import SpellChecker
import word2number.w2n as w2n
from sentence_transformers import SentenceTransformer

import json
import nltk
from nltk.corpus import stopwords
#nltk.download('stopwords')
#nltk.download()
#nltk.download('punkt')
#nltk.download('wordnet')
from pattern.text.en import singularize



model = SentenceTransformer('all-MiniLM-L6-v2')
#model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-mpnet-base-v2')
model_name = "sentence-transformers/all-MiniLM-L6-v2"
from numpy import dot
from numpy.linalg import norm
from datetime import datetime


#slide_data_path = "abbvie_search_V2_wo_embedding.xlsx"
#slide_data_path = "abbvie_search_V3_wo_embedding_icon_psid_singular.csv"
slide_data_path = "abbvie_search_V6.csv"
columns = ['unique_id', 'id', 'company', 'category', 'construct', 'deck_id', 'sid', 'node', 'theme', 'ml_words','s3_bucket', 's3_path', 'pptx_path']
#slide_df = pd.read_csv('abbvie_aa_nsm.csv', names=columns)
#slide_df = slide_df.fillna({'ml_words': ''})
prio_dict = {"category_list": 0, "construct_list": 1, "ml_words_updated": 2, "shape":4, "icon":3, "cat_synnonyms": 5, "cons_synnonyms":6, "EMB":9}
text_prio_list = ["category", "construct", "ml_words", "icon",  "shape", "category_syn", "construct_syn",  "", "", "", "embedding"]
keyword_dict = {}
score_dist = {}
path_dict = {}
emb_dict = {}
category_dict = {}
construct_dict = {}
ml_emb_dict = {}

spell = SpellChecker()
with open('path.json') as json_file:
    path_dict = json.load(json_file)


def clean_kwimage(sent):
    return ' '.join([i.strip().split('::')[0].replace('_', ' ') for i in sent.split(',') if len(i.split('::')) == 2 and i.split('::')[1] == 'object'])

def is_percentage(word, sentence):
    return sentence[sentence.find(word)+len(word):].startswith('%')

def extract_numbers(sentence):
    default_node_count = 99
    node_words = {
        1 : ['uni','paragraph', 'para', 'essay', 'note', 'passage', 'one-pager', 'one-page', 'synopsis', 'epilogue', 'abstract', 'brief',
                'one', 'once','single','solo', 'unit', 'linear', 'i', 'uno','manuscript', 'monograph', 'excerpt', 'document', 'outline',
                'digest', 'prologue', 'briefing', 'thesis', 'prospectus'],
        2 : ['dual', 'bi', 'Two', 'twice', 'double', 'twin', 'pair', 'binary', 'couple', 'duo', 'ii'],
        3 : ['trio', 'triple', 'triplet', 'tri', 'three', 'thrice', 'trifold', 'ternary', 'iii'],
        4 : ['Four', 'quadruple', 'quadruplet', 'quaternary', 'iv'],
        5 : ['penta', 'Five', 'quintuple', 'v'],
        6 : ['hexa', 'six', 'sextuple', 'vi'],
        7 : ['seven', 'septuple', 'vii'],
        8: ['eight', 'octuple', 'viii'],
        9: ['nine, ix'],
        10: ['ten', 'x', 'decennial', 'tenfold']
    }

    word_list = re.findall(r'\b\w+\b', sentence)
    numbers = []
    for word in word_list:
        if is_percentage(word, sentence):  # Skip if it is a percentage
            continue
        try:
            num = w2n.word_to_num(word)
            if 1 <= num <= 7:  # check if the number is in range
                numbers.append(num)
        except ValueError:
            try:
                num = int(word)
                if 1 <= num <= 7:  # check if the number is in range
                    numbers.append(num)
            except ValueError:
                try:
                    num = float(word)
                    if 1 <= num <= 7:  # check if the number is in range
                        numbers.append(num)
                except ValueError:
                    continue
    if numbers:  # check if the list is not empty
        return int(min(numbers)),False, min(numbers)
    for key in node_words:
        for word in node_words[key]:
            if word.lower() in [w.lower() for w in word_list]:
                return key,False, word
    return default_node_count,True, ""

def load_slidedf(slide_data_path):
    #df = pd.read_excel(slide_data_path)
    df = pd.read_csv(slide_data_path)
    return df

def count_and_store_matching_words_array_v1(words_list, search_words, columns_values):
    #words_list = slide_descrip_json[words_key]
    words_list = words_list.replace("[", "").replace("]", "").replace("'", "").replace('"', '')
    words_list = words_list.split(", ")
    matching_words = [word for word in search_words if word in words_list]
    matching_columns = [col for col, col_values in columns_values.items() if any(word in col_values for word in matching_words)]
    return len(matching_words), matching_words, matching_columns

def calc_matched_keyword_with_query(words_list, query, columns_values):
    #words_list = slide_descrip_json[words_key]
    words_list = words_list.lower().replace("[", "").replace("]", "").replace("'", "").replace('"', '')
    words_list = words_list.split(", ")
    matching_columns =[]
    if query in words_list:
        matching_columns = [col for col, col_values in columns_values.items() if query in col_values]
        return 11, query, matching_columns
    else:
        return 0, query, matching_columns

def get_priority(x):
    if 'category_list' in x:
        return prio_dict['category_list']
    elif 'construct_list' in x:
        return prio_dict['construct_list']
    elif 'ml_words_updated' in x:
        return prio_dict['ml_words_updated']
    elif 'shape' in x:
        return prio_dict['shape']
    elif 'icon' in x:
        return prio_dict['icon']
    elif 'cat_synnonyms' in x:
        return prio_dict['cat_synnonyms']
    elif 'cons_synnonyms' in x:
        return prio_dict['cons_synnonyms']

def pre_keyword_search(query, df_search):
    columns_to_check = ['category_list', 'construct_list', 'ml_words_updated', 'shape', 'icon', 'cat_synnonyms','cons_synnonyms']
    df_search['itm_prio'], df_search['word'], df_search['matched_columns'] = zip(*df_search.apply(
        lambda row: calc_matched_keyword_with_query(row['description'], query, {col: row[col] for col in columns_to_check}), axis=1))

    filtered_df = df_search[df_search['itm_prio'] == 11]
    filtered_df['priority'] = filtered_df['matched_columns'].apply(lambda x: get_priority(x))
    filtered_df['cosine_score'] = [99 for i in range(filtered_df.shape[0])]
    filtered_df['word_rank'] = [-99 for i in range(filtered_df.shape[0])]

    return filtered_df

def keyword_search(query, df_search):

    columns_to_check = ['category_list', 'construct_list', 'ml_words_updated', 'shape', 'icon', 'cat_synnonyms', 'cons_synnonyms']
    search_words = query.split(" ")

    # Apply function to each row
    df_search['word_rank'], df_search['word'], df_search['matched_columns'] = zip(*df_search.apply(
        lambda row: count_and_store_matching_words_array_v1(row['description'], search_words, {col: row[col] for col in columns_to_check}), axis=1))
    filtered_df = df_search[df_search['word_rank'] > 0]
    filtered_df['priority'] = filtered_df['matched_columns'].apply(lambda x: get_priority(x))
    filtered_df['cosine_score'] = [99 for i in range(filtered_df.shape[0])]
    filtered_df['itm_prio'] = [-1 for i in range(filtered_df.shape[0])]

    return True, filtered_df


def correct_spelling(word):
    spell = SpellChecker()
    # Find and return the most likely correct word
    return spell.correction(word)

def get_keyword_match(candidate_word, word, keyword_dict):
    priority = ["category", 'construct', 'ml_words_final', 'shape_final', 'icon_final', 'category_synonyms', 'construct_synonyms']

    return_flag = False
    for prio in priority:
        set_b = set(keyword_dict[prio])
        filtered_words = [word for word in candidate_word if word in set_b]
        if filtered_words or len(filtered_words)>0:
            return_flag = True
            break
    if return_flag is True:
        if isinstance(filtered_words, list):
            return filtered_words[0]
        else:
            filtered_words
    else:
        return spell.correction(word)

def check_query(query):

    with open('all_keyword_names.json') as json_file:
        keyword_dict = json.load(json_file)

    flag_thrs = False
    query = re.sub("[^0-9a-zA-Z ./-]+", ' ', query.lower())
    #query = query.lower()
    word_list = re.findall(r'\S+', query)
    word_list = [singularize(word) for word in word_list]
    filtered_query = []
    #check whether it is a english word or not.
    english_vocab = set(w.lower() for w in nltk.corpus.words.words())
    eng_vocal_bool = [word in english_vocab for word in word_list]

    for i in range(len(eng_vocal_bool)):
        if eng_vocal_bool[i] is False:
            word = word_list[i]
            if spell.unknown([word]):
                candidate_word = spell.candidates(word)
                if candidate_word is not None:
                    filtered_word = get_keyword_match(candidate_word, word, keyword_dict)
                    if filtered_word is not None:
                        flag_thrs = True
                        filtered_query.append(filtered_word)
                    else:
                        flag_thrs = True
                        filtered_query.append(spell.correction(filtered_word))
                else:
                    flag_thrs = False
            else:
                flag_thrs = True
                filtered_query.append(word)
        else:
            flag_thrs = True
            filtered_query.append(word_list[i])

    if flag_thrs is True:
        return True, " ".join(filtered_query).strip()
    else:
        return False, " ".join(filtered_query).strip()

def preprocess_keyword_search(query):

    input_word_list = ["slide", "nodecount", "node", "count", "with", "shape", "icon", "chart"]
    plural_word = ['rockets', 'benefits', 'barriers']

    stop_words = set(stopwords.words('english'))
    words = nltk.word_tokenize(query)
    filtered_words = [word for word in words if word.lower() not in stop_words]
    filtered_words = [word[:-1] if word in plural_word else word for word in filtered_words  ]
    query = ' '.join(filtered_words)

    #Removing words which are not needed in our business requirement
    query = ' '.join([word for word in query.split(" ") if word not in input_word_list])
    return query

def check_filter_keys(query):
    filter_keys = ["icon"]

    itm_prio =""
    flag = False
    for key in filter_keys:
        if key in query:
            flag =True
            itm_prio = key
    return flag, itm_prio

def search_V6(query):

    #Calculating Node Count from the Query.
    query = query.lower()

    # ===================================== Check Whether it has ICONS or Not ===========================================
    item_prio_bool, itm_prio = check_filter_keys(query)
    # ===================================================================================================================

    #===================================== Extracting Numbers from the Query ===========================================
    node_count, res_bool, node_word = extract_numbers(query)
    if len(query.split(" "))>1:
        query = query.replace(str(node_word), "")
    #===================================================================================================================

    #===================================== Checking Spell of the Query and Autocorrecting Query ========================
    spell_, query = check_query(query)
    if spell_ is True:

        slide_df = load_slidedf(slide_data_path)
        slide_df = slide_df.fillna({'ml_words': ''})

        #==========================================================================================================================================
        #Added here First entire string check For Aliases.
        filtered_slide_df_pre = pre_keyword_search(query, slide_df)
        slide_df_m1 = pd.DataFrame(slide_df['unique_id'], columns=['unique_id'])
        filt_slide_m1 = pd.DataFrame(filtered_slide_df_pre['unique_id'], columns=['unique_id'])

        # Get values in column 'A' of df1 but not in inner join result of 'A' and 'B' of df1 and df2
        filtered_slide_df_m = slide_df_m1[~slide_df_m1['unique_id'].isin(slide_df_m1.merge(filt_slide_m1, left_on='unique_id', right_on='unique_id', how='inner')
                                                                         ['unique_id'])]
        filtered_slide_df_rest_pre = slide_df[slide_df["unique_id"].isin(filtered_slide_df_m["unique_id"].tolist())]
        #==========================================================================================================================================

        #========================== ADDING KEY WORD SEARCH METHOD HERE ============================================================================
        query_s = preprocess_keyword_search(query)
        print("Final Query going inside the search method is =============================== :", query_s)
        out_bool, filtered_slide_df = keyword_search(query_s, filtered_slide_df_rest_pre)
        if item_prio_bool:
            filtered_slide_df['itm_prio'] = filtered_slide_df['matched_columns'].apply(lambda words: 1 if itm_prio in words else -99)

        slide_df_m2 = pd.DataFrame(filtered_slide_df_rest_pre['unique_id'], columns=['unique_id'])
        filt_slide_id_m2 = pd.DataFrame(filtered_slide_df['unique_id'], columns=['unique_id'])
        filtered_slide_df_m = slide_df_m2[~slide_df_m2['unique_id'].isin(slide_df_m2.merge(filt_slide_id_m2, left_on='unique_id', right_on='unique_id', how='inner')
                                                                         ['unique_id'])]
        filtered_slide_df_rest = filtered_slide_df_rest_pre[filtered_slide_df_rest_pre["unique_id"].isin(filtered_slide_df_m["unique_id"].tolist())]
        #===========================================================================================================================================

        #===========================================================================================================================================
        #Embedding Search Starts Here bcs The Score from Filter Search is not Sufficient here.
        print("query", query)
        keyword_dict.clear()
        score_dist.clear()
        query = query.lower()
        # Convert tokenized sentences to embeddings
        query_emb = model.encode(query, convert_to_tensor=True)

        with open('slide_embeddings_V6_wo_embedding_icon_psid.json') as json_file:
            slide_emb_json = json.load(json_file)

        for index, row in filtered_slide_df_rest.iterrows():
            slide_emb = slide_emb_json[row['unique_id']]
            sc = (dot(query_emb, slide_emb) / (norm(query_emb) * norm(slide_emb)))
            filtered_slide_df_rest.at[index, "cosine_score"] = sc

        filtered_slide_df_rest['priority'] = prio_dict["EMB"]
        filtered_slide_df_rest['itm_prio'] = -99
        #=========================================================================================================================================

        #========================================= Adding Three Dataframe to get a final One =====================================================
        final_slide_df = pd.concat([filtered_slide_df_pre, filtered_slide_df, filtered_slide_df_rest])
        #=========================================================================================================================================

        #======================================== Final Finishing of The Code ======================================================================
        if node_count != 99:
            final_slide_df = final_slide_df[final_slide_df["node"] == node_count]
        else:
            final_slide_df = final_slide_df[final_slide_df["sid"] == final_slide_df["psid"]]

        df_final = final_slide_df[['unique_id', 'cosine_score', 'priority', 'word_rank', 'word', 'itm_prio', 'matched_columns']]
        df_final.rename(columns = {'unique_id':'id', 'cosine_score':'score', 'priority':'emb_type'}, inplace = True)
        df_final['emb_type'] = df_final['emb_type'].apply(lambda x: x[0] if isinstance(x, list) else x)
        df_final = df_final.sort_values(by=['itm_prio', 'word_rank', 'score', 'emb_type'], ascending=[False, False, False, True])
        df_final_head = df_final.head(25)
        res_list = df_final_head.values.tolist()

        fin_res = []
        for l in res_list:
            file_path = str('abbvie_aa_nsm/') + str(path_dict[l[0]]).split('.')[0] + '.png'
            fin_res.append((l[0], file_path, l[1], text_prio_list[l[2]]))

        return fin_res, query_s

    else:
        print("Wrong Input")
        return "Correct your Input."


ss1 = datetime.now()
fin_res, query_s = search_V6("Weighted Average")
ss2 = datetime.now()
