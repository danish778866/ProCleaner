import py_stringsimjoin as ssj
import py_stringmatching as sm
import pandas as pd

def get_similar_strings(table_path):
    A = pd.read_csv(table_path, names=['id', 'foo'])
    B = pd.read_csv(table_path, names=['id', 'foo'])
    qg3_tok = sm.QgramTokenizer(qval=3)
    output_pairs = ssj.jaccard_join(A, B, 'id', 'id', 'foo', 'foo' , qg3_tok, 0.6,
                            l_out_attrs=['foo'], r_out_attrs=['foo'])
    considered_pairs = []
    similar_strings = []
    for index, row in output_pairs.iterrows():
        if row['_sim_score'] > 0.6 and row['_sim_score'] < 1.0:
            if row['l_foo'] not in similar_strings:
                similar_strings.append(row['l_foo'])
            if row['r_foo'] not in similar_strings:
                similar_strings.append(row['r_foo'])
            if len(similar_strings) >= 21:
                break
    similar_strings.sort()
    return similar_strings

def normalize_strings(table_path, values):
    A = pd.read_csv(table_path)
    values_list = values.split("|")
    for value in values_list:
        current_values = value.split(",")
        retain_value = current_values[0].strip()
        for i in range(1, len(current_values)):
            current_value = current_values[i].strip()
            A['foo'].loc[A['foo'] == current_value] = retain_value
    A.to_csv(table_path, index=False)
