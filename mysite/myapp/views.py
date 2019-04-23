# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
import py_stringsimjoin as ssj
import py_stringmatching as sm
import pandas as pd
import os, sys, json

from myapp.models import Document
from myapp.forms import DocumentForm, ProfilerChoiceForm

def downloads_page(request):
    project_dir = os.path.dirname(os.path.realpath(__file__))
    processed_dir = project_dir + os.sep + "static" + os.sep + "pdf"
    all_documents = Document.objects.all()
    docs_to_show = []
    for document in all_documents:
        doc_to_show = {}
        file_url = document.docfile.url
        file_name = os.path.basename(file_url)
        doc_to_show['file'] = True
        doc_to_show['file_name'] = file_name
        doc_to_show['file_url'] = file_url
        rules_file_path = processed_dir + os.sep + file_name + ".rules"
        if os.path.exists(rules_file_path):
            rules_file = True
            rules_file_name = file_name + ".rules"
            rules_file_url = rules_file_path
        else:
            rules_file = False
            rules_file_name = ""
            rules_file_url = ""
        doc_to_show['rules_file'] = rules_file
        doc_to_show['rules_file_name'] = rules_file_name
        doc_to_show['rules_file_url'] = rules_file_url
        clean_file_path = processed_dir + os.sep + file_name + ".clean"
        print(clean_file_path)
        if os.path.exists(clean_file_path):
            print("Hah")
            clean_file = True
            clean_file_name = file_name + ".clean"
            clean_file_url = clean_file_path
        else:
            print("Nah")
            clean_file = False
            clean_file_name = ""
            clean_file_url = ""
        doc_to_show['clean_file'] = clean_file
        doc_to_show['clean_file_name'] = clean_file_name
        doc_to_show['clean_file_url'] = clean_file_url
        docs_to_show.append(doc_to_show)
        print(docs_to_show)
    return render(request, 'downloads.html', {'docs_to_show': docs_to_show})

def list(request):
    # Handle file upload
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        process_file = request.POST.getlist('process_file')
        if form.is_valid():
            if 'docfile' in request.FILES:
                newdoc = Document(docfile=request.FILES['docfile'])
                newdoc.save()
                project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
                table_path = project_dir + newdoc.docfile.url
                A = pd.read_csv(table_path, names=['foo'])
                A['id'] = range(0, len(A))
                column_order = ['id', 'foo']
                whitespace_striper = lambda x: x.strip()
                A['foo'] = A['foo'].apply(whitespace_striper)
                A[column_order].to_csv(table_path, index=False)

                # Redirect to the document list after POST
                request.session['uploaded_file_path'] = newdoc.docfile.url
            else:
                request.session['uploaded_file_path'] = process_file[0]

            return HttpResponseRedirect(reverse('profiler_choice'))
    else:
        form = DocumentForm()  # A empty, unbound form

    # Load documents for the list page
    all_documents = Document.objects.all()

    # Render list page with the documents and the form
    return render(
        request,
        'list.html',
        {'form': form, 'all_documents': all_documents}
    )

def profiler_choice(request):
    form = ProfilerChoiceForm()
    profiler_options = [["1", "Clean Strings"], ["2", "Profile"], ["3", "Find Errors"]]
    uploaded_file_name = request.session.get('uploaded_file_path')
    return render(request, 'profiler_choice.html', {'form': form, 'profiler_options': profiler_options})

def clean_file(request):
    ret_val = ""
    checks = request.POST.getlist('clean')
    substitute = {}
    uploaded_file_name = request.session.get('uploaded_file_path')
    project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    rules_file_path = project_dir + os.sep + "myapp" + os.sep + "static" + os.sep + "pdf" + os.sep + os.path.basename(uploaded_file_name) + ".rules"
    rules_file = open(rules_file_path, "w")
    for substitution in checks:
        words = substitution.split(",")
        ret_val = ret_val + words[1] + " "
        substitute[words[1]] = words[0]
        rules_file.write(words[1] + "->" + words[0] + "\n")
    rules_file.close()
    uploaded_file_path = project_dir + uploaded_file_name
    cleaned_file_path = project_dir + os.sep + "myapp" + os.sep + "static" + os.sep + "pdf" + os.sep + os.path.basename(uploaded_file_name) + ".clean"
    A = pd.read_csv(uploaded_file_path)
    new_foo = []
    for index, row in A.iterrows():
        if row['foo'] in substitute:
            #A.set_value(index, 'foo', substitute[row['foo']])
            new_foo.append(substitute[row['foo']])
        else:
            new_foo.append(row['foo'])
    A['new_foo'] = new_foo
    column_order = ['id','foo','new_foo']
    A[column_order].to_csv(cleaned_file_path, index=False)
    return render(request, 'clean_file.html', {'cleaned_file_name': os.path.basename(uploaded_file_name) + 
                                               ".clean", 'rules_file_name': os.path.basename(uploaded_file_name) + ".rules"})

def show_doc(request):
    project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    uploaded_file = request.session.get('uploaded_file_path')
    print(request.POST)
    if request.method == 'POST':
        if "merge" in request.POST:
            values = ','.join(request.POST.getlist('merge'))
            table_path = project_dir + uploaded_file
            A = pd.read_csv(table_path)
            values_list = values.split("|")
            for value in values_list:
                current_values = value.split(",")
                retain_value = current_values[0].strip()
                for i in range(1, len(current_values)):
                    current_value = current_values[i].strip()
                    A['foo'].loc[A['foo'] == current_value] = retain_value
            A.to_csv(table_path, index=False)
            profiler_choice = "1"
        else:
            profiler_choice = request.POST['profiler_choice']
        if profiler_choice == "1":
            table_A_path = project_dir + uploaded_file
            table_B_path = project_dir + uploaded_file
            A = pd.read_csv(table_A_path, names=['id', 'foo'])
            B = pd.read_csv(table_B_path, names=['id', 'foo'])
            qg3_tok = sm.QgramTokenizer(qval=3)
            output_pairs = ssj.jaccard_join(A, B, 'id', 'id', 'foo', 'foo' , qg3_tok, 0.6,
                                        l_out_attrs=['foo'], r_out_attrs=['foo'])
            similar_pairs = []
            considered_pairs = []
            similar_strings = []
            similar_strings_1 = []
            similar_strings_2 = []
            similar_strings_3 = []
            for index, row in output_pairs.iterrows():
                if row['_sim_score'] > 0.6 and row['_sim_score'] < 1.0:
                    current_pair = {}
                    current_pair['0'] = row['l_foo']
                    current_pair['1'] = row['r_foo']
                    pair_together = current_pair['1'] + current_pair['0']
                    pair_to_add = current_pair['0'] + current_pair['1']
                    if pair_together not in considered_pairs and current_pair['0'] != current_pair['1']:
                        similar_pairs.append(current_pair)
                        considered_pairs.append(pair_to_add)
                        if row['l_foo'] not in similar_strings:
                            similar_strings.append(row['l_foo'])
                        if row['r_foo'] not in similar_strings:
                            similar_strings.append(row['r_foo'])
                        if len(similar_strings) >= 90:
                            break
            num_pairs = len(similar_pairs)
            similar_strings.sort()
            num_each = len(similar_strings) / 3
            print(similar_strings)
            similar_strings_1 = similar_strings[0:num_each]
            similar_strings_2 = similar_strings[num_each:2 * num_each]
            similar_strings_3 = similar_strings[2 * num_each:]
            return render(request, 'show_doc.html', 
                          {'file_path': uploaded_file, 'similar_pairs': similar_pairs, 
                           'num_pairs': num_pairs,
                           'similar_strings_1': similar_strings_1,
                           'similar_strings_2': similar_strings_2,
                           'similar_strings_3': similar_strings_3
                          })
        elif profiler_choice == "2":
            table_A_path = project_dir + uploaded_file
            A = pd.read_csv(table_A_path, names=['id', 'foo'])
            stats, lengths = stats_length_strings(A, 'foo')
            stats_words, lengths_words, num_capitals = stats_words_in_strings(A, 'foo')
            json_data = json.dumps({"lengths": lengths})
            return render(request, 'show_stats.html', 
                {'stats': stats, 
                'lengths': lengths,
                'stats_words': stats_words,
                'lengths_words': lengths_words,
                'num_capitals': num_capitals
                })
        else:
            table_A_path = project_dir + uploaded_file
            A = pd.read_csv(table_A_path, names=['id', 'foo'])

            # total number of strings
            total = float(len(A['foo']))

            # find uniqueness
            n_uniques, pervasiveness_uniques, duplicates = fraction_uniques(A, 'foo')

            # find missing values - useless for now as doesn't account for -1, unknown
            n_missing, pervasiveness_missing = contains_missing_values_global_syn(A, 'foo')
            
            # type recognition
            type_pervasiveness_dict = type_recognition(A, 'foo')

            # return the different errors to the corresponding html
            return render(request, 'show_errors.html', {
                'n_uniques': n_uniques,
                'pervasiveness_uniques': pervasiveness_uniques, 
                'duplicates': duplicates,
                'n_missing': n_missing,
                'pervasiveness_missing': pervasiveness_missing,
                'type_pervasiveness_dict': type_pervasiveness_dict
                })


def stats_length_strings(df, col_name) :
    """
    Generates basic statistics(measures of central tendency and histogram) on length of strings
    Args:
        df (DataFrame): the dataframe
        col_name (str): column name representing the column in question
    Returns:
        Measures of central tendency - Min, Max, Mean, Std, Median
        Histogram on string lengths in the column
    """
    df['tmp_lengths'] = df[col_name].str.len()
    
    # Min, Max, Mean, Standard deviation and Median length
    stats = df['tmp_lengths'].agg(['min', 'max', 'mean', 'std', 'median']).round(decimals=2).tolist()
    return stats, df['tmp_lengths'].tolist()

def stats_words_in_strings(df, col_name) :
    """
    Generates basic statistics(measures of central tendency and histogram) on number of words in strings
    Args:
        df (DataFrame): the dataframe
        col_name (str): column name representing the column in question
    Returns:
        Measures of central tendency - Min, Max, Mean, Std, Median
        Histogram on number of words in the column
    """
    df['tmp_words'] = df[col_name].str.split()
    df['tmp_num_words'] = df['tmp_words'].apply(lambda x: len(x))
    
    # Min, Max, Mean, Standard deviation and Median length
    stats = df['tmp_num_words'].agg(['sum', 'min', 'max', 'mean', 'std', 'median']).round(decimals=2).tolist()
    
    # Number of Captitalized Words
    count_words = 0
    count_capitals = 0
    for list_str in df['tmp_words']:
        for w in list_str:
            count_words = count_words + 1
            if w[0].isupper():
                count_capitals = count_capitals+1

    # return stats of words, num_words col to make histogram, and count_capitals
    return stats, df['tmp_num_words'].tolist(), count_capitals
    
def fraction_uniques(df, col_name) :
    """
    Calculates the fraction of unique values in the column
    Args:
        df (DataFrame): the dataframe
        col_name (str): column name representing the column in question
    Returns:
        Number of Unique Values/ Number of total values
    """
    n_uniques = len(df[col_name].unique())
    pervasiveness = n_uniques/float(len(df[col_name]))
    boolean_duplicates = df[col_name].duplicated()
    duplicates = df[boolean_duplicates == True][col_name].head().tolist()
    return n_uniques, pervasiveness, duplicates

def contains_missing_values_global_syn(df, col_name) :
    """
    Tells the pervasiveness of the missing values in the string column
    Note: NaN, was not used, as it is only valid for floating point numbers
    Args:
        df (DataFrame): the dataframe
        col_name (str): column name representing the column in question
    Returns:
        No. of Missing Values/ Total no. of values in the column
    """
    n_missing_values = float(len(df[col_name])) - df[col_name].count()
    return n_missing_values, 1.0 - (n_missing_values/float(len(df[col_name])))

def type_recognition(df, col_name) :
    """
    Tells the pervasivness of different types of the values in the column 
    Note: The types checked for are:
    1. Alphabetic
    2. Alphanumeric
    3. Numeric
    4. Phone
    5. Date
    Args:
        df (DataFrame): the dataframe
        col_name (str): column name representing the column in question
    Returns:
        Dict < Type T, Pervasivness in column(No. of values of T/ Total no. of values in the column)>
    """
    n_alpha = sum(df[col_name].str.isalpha())
    pervasivness_alpha = n_alpha/float(len(df[col_name]))
    
    n_alphanumeric = sum(df[col_name].str.isalnum())
    pervasivness_alphanumeric = n_alphanumeric/float(len(df[col_name]))
    
    n_numeric = sum(df[col_name].str.isdigit())
    pervasivness_numeric = n_numeric/float(len(df[col_name]))
    
    
    # validate phone number entries
    import re
    def validNumber(phone_number):
        pattern = re.compile("\D?(\d{0,3}?)\D{0,2}(\d{3})?\D{0,2}(\d{3})\D?(\d{4})$", re.IGNORECASE)
        return pattern.match(phone_number) is not None

    n_phone = sum(df[col_name].apply(validNumber))
    pervasivness_phone = n_phone/float(len(df[col_name]))
    
    # validate date entries
    import datetime
    def validate_date(date_text):
        try:
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except ValueError:
            return False
    n_date = sum(df[col_name].apply(validate_date))
    pervasivness_date = n_date/float(len(df[col_name]))
    return {
        'n_alpha': n_alpha,
        'pervasivness_alpha': pervasivness_alpha,
        'n_alphanumeric': n_alphanumeric,
        'pervasivness_alphanumeric': pervasivness_alphanumeric,
        'n_numeric': n_numeric,
        'pervasivness_numeric': pervasivness_numeric,
        'n_phone': n_phone,
        'pervasivness_phone': pervasivness_phone,
        'n_date': n_date,
        'pervasivness_date': pervasivness_date       
    }

    

    
    
