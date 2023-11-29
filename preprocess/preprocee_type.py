import pandas as pd

def get_id(dir_path='cmg-data/split-data', type='randomly'):
    with open(f'{dir_path}/{type}/train_id.txt') as file:
        train_id = [line.rstrip() for line in file]
    with open(f'{dir_path}/{type}/test_id.txt') as file:
        test_id = [line.rstrip() for line in file]
    return train_id, test_id

df = pd.read_parquet(f'cmg-data/cmg-data-processed.parquet', engine='fastparquet')
# df = df['text'].to_list()
# print(df[0])
train_id, test_id = get_id(dir_path='cmg-data/split-data', type='cross_project')
train, test = df.loc[df['index'].isin(train_id)], df.loc[df['index'].isin(test_id)]

df_type = pd.read_csv('cluster_tfidf.csv')
type_dict = dict()
for _,row in df_type.iterrows():
    index = str(row['index'])
    index = index.lower()
    type_dict[index] = row['cluster']

import nltk
from nltk import WordNetLemmatizer, pos_tag, WordPunctTokenizer, data
from nltk.corpus import wordnet
from tqdm import tqdm
import re

def write_string_to_file(absolute_filename, string):
    with open(absolute_filename, 'w') as fout:
        fout.write(string)

def word_tokenizer(sentence):
    words = WordPunctTokenizer().tokenize(sentence)
    return words

examples = []

indexs = train['index'].unique()

for index in tqdm(indexs):
    df_commit = train[train['index']==index]
    source_seq = ''
    vcc_msgs = ''
    for _, row in df_commit.iterrows():
        if row['old_path_file'] != None:
            source_seq += '--- ' + row['old_path_file'] + '\n'
        if row['new_path_file'] != None:
            source_seq += '+++ ' + row['new_path_file'] + '\n'
        source_seq += row['diff'] + '\n'
        
        label_words = row['label'].split()
        target_seq = ' '.join(label_words)
        
    examples.append({'diff': source_seq, 'msg': target_seq, 'type': type_dict[index]})

import json
def dump_to_file(obj, file):
    with open(file,'w+') as f:
        for el in obj:
            f.write(json.dumps(el)+'\n')
            
dump_to_file(examples,'train.jsonl')

import nltk
from nltk import WordNetLemmatizer, pos_tag, WordPunctTokenizer, data
from nltk.corpus import wordnet
from tqdm import tqdm
import re

def write_string_to_file(absolute_filename, string):
    with open(absolute_filename, 'w') as fout:
        fout.write(string)

def word_tokenizer(sentence):
    words = WordPunctTokenizer().tokenize(sentence)
    return words

examples = []

indexs = test['index'].unique()

for index in tqdm(indexs):
    df_commit = test[test['index']==index]
    source_seq = ''
    vcc_msgs = ''
    for _, row in df_commit.iterrows():
        if row['old_path_file'] != None:
            source_seq += '--- ' + row['old_path_file'] + '\n'
        if row['new_path_file'] != None:
            source_seq += '+++ ' + row['new_path_file'] + '\n'
        source_seq += row['diff'] + '\n'
        
        label_words = row['label'].split()
        target_seq = ' '.join(label_words)

    if index in type_dict.keys():
        type = type_dict[index]
    else:
        type = 1

    prompt = f"Give a short commit message for code from git diff with type_{{type}}:\n{{diff}}\n---\nShort commit message:\n".format(type=type, diff=source_seq)
    examples.append({'prompt': prompt})

import json
def dump_to_file(obj, file):
    with open(file,'w+') as f:
        for el in obj:
            f.write(json.dumps(el)+'\n')
dump_to_file(examples,'test.input.jsonl')  