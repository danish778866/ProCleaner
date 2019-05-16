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
import requests

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
    form = DocumentForm()  # A empty, unbound form
    current_url = request.get_full_path()
    project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    print(project_dir)
    if "procleaner_token" not in request.session:
        if current_url.endswith("/list/"):
            print(2)
            print("See" + str(request.session.get("procleaner_token", "Loool")))
            authorize_url = "http://a250afd7c6eba11e98ea412ac368fc7a-312971903.us-east-1.elb.amazonaws.com/o/authorize/?response_type=code&client_id=JjLei3oxaRx6qtb6w1EoysY7MemGC1vCctoe24N3&redirect_uri=http://0.0.0.0:8000/myapp/list/&state=1234xyz";
            return HttpResponseRedirect(authorize_url)
        else:
            print(3)
            print("See" + str(request.session.get("procleaner_token", "Loool")))
            code = request.GET.get('code')
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "http://0.0.0.0:8000/myapp/list/",
                "client_id": "JjLei3oxaRx6qtb6w1EoysY7MemGC1vCctoe24N3",
                "client_secret": "XErdw5E9Nzok8eqI4jnkKrmtYpoPwQd5m9273HPwQ0wPQa63L5UnjFZ9CMSIwrhPTxO5TzxNVB8w2wO5LBrV88NvzNfnj3UviY3T4yojV5yhl4wzR1J96l0JLEexdS3n",
            }
            token_url = "http://a250afd7c6eba11e98ea412ac368fc7a-312971903.us-east-1.elb.amazonaws.com/o/token/"
            response = requests.post(
                url=token_url,
                data=data
            )
            request.session["procleaner_token"] = response.json()['access_token']
            print("Token " + str(response.json()['access_token']))
            request.session.set_expiry(response.json()['expires_in'])
    else:
        print(4)
        print("See" + str(request.session.get("procleaner_token", "Loool")))
    cdrive_url = "http://a7648f6f5702911e98ea412ac368fc7a-1169430973.us-east-1.elb.amazonaws.com"
    token = request.session.get("procleaner_token")
    cdrive_files = []
    print(request.COOKIES)
    print(token)
    if not token is None:
        #request.session["procleaner_token"] = token
        post_url = cdrive_url + "/list/"
        header = {"Authorization": "Bearer " + token}
        list_response = requests.get(
            url=post_url,
            headers=header
        )
        for r in list_response.json():
            cdrive_files.append(r['file_name'])
    # Load documents for the list page
    all_documents = Document.objects.all()
    # Render list page with the documents and the form
    #request.session.flush()
    return render(
        request,
        'list.html',
        {'form': form, 'all_documents': all_documents, 'cdrive_files': cdrive_files}
    )

def profiler_choice(request):
    form = ProfilerChoiceForm()
    profiler_options = [["1", "Clean Strings"], ["2", "Profile"], ["3", "Find Errors"]]
    uploaded_file_name = request.session.get('uploaded_file_path')
    return render(request, 'profiler_choice.html', {'form': form, 'profiler_options': profiler_options})

def list_tuples(request):
    form = DocumentForm(request.POST, request.FILES)
    load_from_cdrive = False
    if 'process_file' in request.POST:
        load_from_cdrive = False
        process_file = request.POST.getlist('process_file')
    elif 'cdrive_file' in request.POST:
        load_from_cdrive = True

    if form.is_valid():
        print(request.POST)
        if load_from_cdrive:
            project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            cdrive_file_dir = project_dir + os.sep + "cdrive_files"
            cdrive_file = request.POST.getlist('cdrive_file')[0]
            cdrive_url = "http://a7648f6f5702911e98ea412ac368fc7a-1169430973.us-east-1.elb.amazonaws.com"
            token = request.session["procleaner_token"]
            print(request.COOKIES)
            print(token)
            get_url = cdrive_url + "/file-content?file_name=" + str(cdrive_file)
            header = {"Authorization": "Bearer " + token}
            read_response = requests.get(url=get_url, headers=header)
            tuples = read_response.json().split("\n")
            A = pd.DataFrame(tuples)
            A.columns = ['foo']
            A['id'] = range(0, len(A))
            column_order = ['id', 'foo']
            A[column_order].to_csv(os.path.join(cdrive_file_dir, cdrive_file), index=False)
            sample_tuples = tuples[1:10]
            request.session['uploaded_file_path'] = cdrive_file
            request.session['file_type'] = "CDrive"
        elif 'docfile' in request.FILES:
            newdoc = Document(docfile=request.FILES['docfile'])
            newdoc.save()
            project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            table_path = project_dir + newdoc.docfile.url
            A = pd.read_csv(table_path, names=['foo'])
            A['id'] = range(0, len(A))
            column_order = ['id', 'foo']
            whitespace_striper = lambda x: str(x).strip()
            A['foo'] = A['foo'].apply(whitespace_striper)
            A[column_order].to_csv(table_path, index=False)
            request.session['uploaded_file_path'] = newdoc.docfile.url
            request.session['file_type'] = "Local"
            sample_tuples = A['foo'].head().tolist()
        else:
            request.session['uploaded_file_path'] = process_file[0]
            request.session['file_type'] = "Local"
            project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
            table_path = project_dir + process_file[0]
            A = pd.read_csv(table_path, names=['foo'])
            sample_tuples = A['foo'].head().tolist()
        return render(request, 'list_tuples.html', {'sample_tuples': sample_tuples})


def clean_file(request):
    #ret_val = ""
    #checks = request.POST.getlist('clean')
    #substitute = {}
    #uploaded_file_name = request.session.get('uploaded_file_path')
    #project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    #rules_file_path = project_dir + os.sep + "myapp" + os.sep + "static" + os.sep + "pdf" + os.sep + os.path.basename(uploaded_file_name) + ".rules"
    #rules_file = open(rules_file_path, "w")
    #for substitution in checks:
    #    words = substitution.split(",")
    #    ret_val = ret_val + words[1] + " "
    #    substitute[words[1]] = words[0]
    #    rules_file.write(words[1] + "->" + words[0] + "\n")
    #rules_file.close()
    #uploaded_file_path = project_dir + uploaded_file_name
    #cleaned_file_path = project_dir + os.sep + "myapp" + os.sep + "static" + os.sep + "pdf" + os.sep + os.path.basename(uploaded_file_name) + ".clean"
    #A = pd.read_csv(uploaded_file_path)
    #new_foo = []
    #for index, row in A.iterrows():
    #    if row['foo'] in substitute:
    #        #A.set_value(index, 'foo', substitute[row['foo']])
    #        new_foo.append(substitute[row['foo']])
    #    else:
    #        new_foo.append(row['foo'])
    #A['new_foo'] = new_foo
    #column_order = ['id','foo','new_foo']
    #A[column_order].to_csv(cleaned_file_path, index=False)
    #return render(request, 'clean_file.html', {'cleaned_file_name': os.path.basename(uploaded_file_name) + 
    #                                           ".clean", 'rules_file_name': os.path.basename(uploaded_file_name) + ".rules"})
    uploaded_file_name = request.session.get('uploaded_file_path')
    project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    uploaded_file_path = project_dir + uploaded_file_name
    cleaned_file_path = project_dir + os.sep + "myapp" + os.sep + "static" + os.sep + "pdf" + os.sep + os.path.basename(uploaded_file_name) + ".clean"
    A = pd.read_csv(uploaded_file_path)
    A.to_csv(cleaned_file_path, index=False)
    return render(request,
                  'clean_file.html',
                  {'clean_file_name': os.path.basename(uploaded_file_name) + ".clean"}
                 )


def show_doc(request):
    if request.session["file_type"] == "CDrive":
        project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__))) + os.sep + "cdrive_files" + os.sep
    else:
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
        else:
            column_name = 'foo'
            table_A_path = project_dir + uploaded_file
            A = pd.read_csv(table_A_path) #headers will be inferred automatically
            total_n_values = len(A)

            # find missing values so as to calculate further errors on only non-missing entries
            n_missing, pervasiveness_missing, type_missing_values_caught, col_missing = contains_missing_values_global_syn(A, column_name)
            
            # A only with non-missing values
            A_without_missing_values = A[~A[col_missing]]
            
            total_non_missing_values = len(A_without_missing_values)
            # redirect to show_missing_messages page, if no non-missing values in file.
            if total_non_missing_values == 0:
                message = "The file doesn't contain any non-missing values. No additional errors will be found."
                return render(request, 'show_missing_messages.html', {
                'message': message,
                'n_values': total_non_missing_values,
                'n_missing': n_missing,
                'pervasiveness_missing': pervasiveness_missing,
                'type_missing_values_caught': type_missing_values_caught
                })

            if profiler_choice == "2":
                # calculate stats for strings lengths
                stats, lengths = stats_length_strings(A_without_missing_values, column_name)
                # calculate stats for no. of words in strings
                stats_words, lengths_words, num_capitals = stats_words_in_strings(A_without_missing_values, column_name)

                # json_data = json.dumps({"lengths": lengths})
                return render(request, 'show_stats.html', 
                    {'total_values': total_n_values,
                    'n_values': total_non_missing_values,
                    'n_missing': n_missing,
                    'pervasiveness_missing': pervasiveness_missing,
                    'type_missing_values_caught': type_missing_values_caught,
                    'stats': stats, 
                    'lengths': lengths,
                    'stats_words': stats_words,
                    'lengths_words': lengths_words,
                    'num_capitals': num_capitals
                    })
            else:
                # find uniqueness
                n_uniques, pervasiveness_uniques, duplicates = fraction_uniques(A_without_missing_values, column_name)

                # type recognition in non-missing values of column given by column_name
                type_pervasiveness_dict = type_recognition(A_without_missing_values, column_name)

                # return the different errors to the corresponding html
                return render(request, 'show_errors.html', {
                    'total_values': total_n_values,
                    'n_values': total_non_missing_values,
                    'n_uniques': n_uniques,
                    'pervasiveness_uniques': pervasiveness_uniques*100, 
                    'duplicates': duplicates,
                    'n_missing': n_missing,
                    'pervasiveness_missing': pervasiveness_missing,
                    'type_missing_values_caught': type_missing_values_caught,
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
        A list to generate histogram on string lengths in the column
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
        A list to generate histogram on number of words in the column
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
        Number of Uniques
        Number of Unique Values/ Number of total values
        A sample of duplicates returned as a list
    """
    n_uniques = len(df[col_name].unique())
    pervasiveness = n_uniques/float(len(df[col_name]))
    boolean_duplicates = df[col_name].duplicated()
    # take the duplicates, uniquify them, so we don't display the same duplicate multiple times
    duplicates = df[boolean_duplicates == True][col_name].head().unique().tolist()
    return n_uniques, pervasiveness, duplicates

def contains_missing_values_global_syn(df, col_name) :
    """
    Tells the pervasiveness of the missing values in the string column
    Note: NaN, was not used, as it is only valid for floating point numbers
    Args:
        df (DataFrame): the dataframe
        col_name (str): column name representing the column in question
    Returns:
        n_missing_values: No. of missing values
        n_missing_values/float(total_values): No. of Missing Values/ Total no. of values in the column
        type_missing_values_caught: missing values detected in the given column
        col_missing: col name of boolean column, each entry of which tells whether the corresponding entry in col_name is missing value or not
    """
    # tell the df to consider these values as missing values in addition to what it considers normally(None type)
    list_missing_types = ["unknown", "Unknown", "NA", "na", "N/A", "n/a", "missing", "Missing"]
    # create a new column in the df which stores whether the corresponding entry in col_name is missing or not
    col_missing = 'bool_missing'
    # replace the occurences of these values in the column copy, by None
    df['tmp_missing'] = df[col_name].replace(list_missing_types, [None for i in range(len(list_missing_types))])
    # calculate the number of missing values based on tmp_missing column
    df[col_missing] = df['tmp_missing'].isnull()
    n_missing_values = df[col_missing].sum().sum()
    total_values = len(df[col_missing])
    # missing values detected in the given column
    type_missing_values_caught = df[df[col_missing]][col_name].unique().tolist()
    
    return n_missing_values, (n_missing_values*100)/float(total_values), type_missing_values_caught, col_missing

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
    from collections import OrderedDict
    boolean_alpha = df[col_name].str.isalpha()
    n_alpha = sum(boolean_alpha)
    pervasivness_alpha = n_alpha/float(len(df[col_name]))
    alpha_sample = df[boolean_alpha][col_name].head().tolist()
    
    boolean_alphanum = df[col_name].str.isalnum()
    n_alphanumeric = sum(boolean_alphanum)
    pervasivness_alphanumeric = n_alphanumeric/float(len(df[col_name]))
    alpha_num_sample = df[boolean_alphanum][col_name].head().tolist()
    
    boolean_numeric = df[col_name].str.isdigit()
    n_numeric = sum(boolean_numeric)
    pervasivness_numeric = n_numeric/float(len(df[col_name]))
    numeric_sample = df[boolean_numeric][col_name].head().tolist()
    
    
    # validate phone number entries
    import re
    def validNumber(phone_number):
        pattern = re.compile("\D?(\d{0,3}?)\D{0,2}(\d{3})?\D{0,2}(\d{3})\D?(\d{4})$", re.IGNORECASE)
        return pattern.match(phone_number) is not None

    boolean_phone = df[col_name].apply(validNumber)
    n_phone = sum(boolean_phone)
    pervasivness_phone = n_phone/float(len(df[col_name]))
    phone_sample = df[boolean_phone][col_name].head().tolist()
    
    # validate date entries
    import datetime
    def validate_date(date_text):
        # Y means four letter year, y means two letter year.
        list_formats = ['%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y', #1994-07-14, 14-07-1994, 07-14-1994
            '%y-%m-%d', '%d-%m-%y', '%m-%d-%y', #94-07-14, 14-07-94, 07-14-94
            '%m/%d/%y', '%d/%m/%y', '%m/%d/%Y', '%d/%m/%Y'] #07/14/94, 14/07/94, 07/14/1994, 14/07/1994
        
        counter = 0
        for fmt in list_formats:
            try:
                datetime.datetime.strptime(date_text, fmt)
                counter = counter + 1 #if atleast one of the formats match, counter will be incremented
            except ValueError:
                print("Date Format Mismatch")
        if counter == 0: # no format matched to date_text
            return False
        else:
            return True


    boolean_date = df[col_name].apply(validate_date)
    n_date = sum(boolean_date)
    pervasivness_date = n_date/float(len(df[col_name]))
    date_sample = df[boolean_date][col_name].head().tolist()

    return OrderedDict([('No. of Alphabetic Strings', n_alpha),
                      ('Pervasiveness of Alphabetic Strings', pervasivness_alpha*100),
                      ('Sample of Alphabetic Strings Detected', alpha_sample),
                      ('No. of Alphanumeric Strings', n_alphanumeric),
                      ('Pervasiveness of Alphanumeric Strings', pervasivness_alphanumeric*100),
                      ('Sample of Alphanumeric Strings Detected', alpha_num_sample),
                      ('No. of Numerics', n_numeric),
                      ('Pervasiveness of Numerics', pervasivness_numeric*100),
                      ('Sample of Detected Numerics', numeric_sample),
                      ('No. of Detected Phone Numbers', n_phone,),
                      ('Pervasivness of Detected Phone Numbers', pervasivness_phone*100),
                      ('Sample of Detected Phone Numbers', phone_sample),
                      ('No. of Dates Detected', n_date),
                      ('Pervasiveness of Dates', pervasivness_date*100),
                      ('Sample of Detected Dates', date_sample)])

    

    

    
    
