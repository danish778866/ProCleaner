# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.views.decorators.csrf import csrf_exempt
import pandas as pd
import os, sys, json
import requests
import pdb
from myapp.models import Document
from myapp.forms import DocumentForm
from utils.utils import get_similar_strings, normalize_strings


REDIRECT_URI = "http://0.0.0.0:8000/myapp/list/"
APP_ID = "JjLei3oxaRx6qtb6w1EoysY7MemGC1vCctoe24N3"
APP_SECRET = "XErdw5E9Nzok8eqI4jnkKrmtYpoPwQd5m9273HPwQ0wPQa63L5UnjFZ9CMSIwrhPTxO5TzxNVB8w2wO5LBrV88NvzNfnj3UviY3T4yojV5yhl4wzR1J96l0JLEexdS3n"
TOKEN_URL = "http://ad09282b27aca11e98ea412ac368fc7a-1539065101.us-east-1.elb.amazonaws.com/o/token/"
AUTH_URL = "http://ad09282b27aca11e98ea412ac368fc7a-1539065101.us-east-1.elb.amazonaws.com/o/authorize/?response_type=code&client_id=JjLei3oxaRx6qtb6w1EoysY7MemGC1vCctoe24N3&redirect_uri=http://0.0.0.0:8000/myapp/list/&state=1234xyz"
CDRIVE_URL = "http://acdb13cd77acb11e98ea412ac368fc7a-549133274.us-east-1.elb.amazonaws.com"
CDRIVE_UI_URL = "http://a4e6f607c7acd11e98ea412ac368fc7a-425625761.us-east-1.elb.amazonaws.com"
CLIENT_TOKEN_KEY = "procleaner_token"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
CDRIVE_FILES_DIR = os.path.join(PROJECT_DIR, "cdrive_files")
CLEAN_FILES = os.path.join(os.path.join(os.path.join(os.path.join(PROJECT_DIR, "myapp"), "static"), "pdf"), "clean")
CLEAN_FILES_LOCAL = os.path.join(os.path.join(os.path.join(os.path.join(PROJECT_DIR, "myapp"), "static"), "pdf"), "clean_local")
CLEAN_FILES_CDRIVE = os.path.join(os.path.join(os.path.join(os.path.join(PROJECT_DIR, "myapp"), "static"), "pdf"), "clean_cdrive")
CLEAN_FILES_SUFFIX = ".clean"

def upload(request):
    """Return a HttpResponse object for rendering the /myapp/upload page
    
    This view performs the following operations:
        1. Create a form consisting of an input field for a user to upload a file.
        2. Get the OAuth token for the user from authentication (if it doesn't
           exist).
        3. Get the list of files in current users' CDrive.
        4. Render the form and CDrive files.
    """
    form = DocumentForm()
    current_url = request.get_full_path()
    if CLIENT_TOKEN_KEY not in request.session:
        if current_url.endswith("/list/"):
            return HttpResponseRedirect(AUTH_URL)
        else:
            code = request.GET.get('code')
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": APP_ID,
                "client_secret": APP_SECRET,
            }
            response = requests.post(
                url=TOKEN_URL,
                data=data
            )
            request.session[CLIENT_TOKEN_KEY] = response.json()['access_token']
            request.session.set_expiry(response.json()['expires_in'])
    token = request.session.get(CLIENT_TOKEN_KEY)
    cdrive_files = []
    if not token is None:
        post_url = CDRIVE_URL + "/list/"
        header = {"Authorization": "Bearer " + token}
        list_response = requests.get(
            url=post_url,
            headers=header
        )
        if list_response.status_code == requests.codes.ok:
            for r in list_response.json():
                cdrive_files.append(r['file_name'])
    all_documents = Document.objects.all()
    return render(
        request,
        'upload.html',
        {'form': form, 'all_documents': all_documents, 'cdrive_files': cdrive_files, 'c_drive_ui_url': CDRIVE_UI_URL}
    )

def sample(request):
    upload_type = ""
    if 'cdrive_file' in request.POST:
        upload_type = "CDrive"
    elif 'docfile' in request.FILES:
        upload_type = "Local"
    if upload_type == "CDrive":
        cdrive_file = request.POST.getlist('cdrive_file')[0]
        token = request.session[CLIENT_TOKEN_KEY]
        get_url = CDRIVE_URL + "/file-content?file_name=" + str(cdrive_file)
        header = {"Authorization": "Bearer " + token}
        read_response = requests.get(url=get_url, headers=header)
        tuples = read_response.json().split("\n")
        uploaded_df = pd.DataFrame(tuples)
        uploaded_df.columns = ['foo']
        uploaded_df['id'] = range(0, len(uploaded_df))
        column_order = ['id', 'foo']
        uploaded_df[column_order].to_csv(os.path.join(CDRIVE_FILES_DIR, cdrive_file), index=False)
        sample_tuples = tuples[1:10]
        request.session['uploaded_file'] = cdrive_file
        request.session['file_type'] = "CDrive"
    elif upload_type == "Local":
        uploaded_doc = Document(docfile=request.FILES['docfile'])
        uploaded_doc.save()
        uploaded_doc_path = os.path.join(PROJECT_DIR, uploaded_doc.docfile.url[1:])
        uploaded_df = pd.read_csv(uploaded_doc_path, names=['foo'])
        uploaded_df['id'] = range(0, len(uploaded_df))
        column_order = ['id', 'foo']
        whitespace_striper = lambda x: str(x).strip()
        uploaded_df['foo'] = uploaded_df['foo'].apply(whitespace_striper)
        uploaded_df[column_order].to_csv(uploaded_doc_path, index=False)
        request.session['uploaded_file'] = uploaded_doc.docfile.url
        request.session['file_type'] = "Local"
        sample_tuples = uploaded_df['foo'].head(10).tolist()
    return render(request, 'sample.html', {'sample_tuples': sample_tuples})

def choices(request):
    profiler_options = [["1", "Clean Strings"], ["2", "Profile"], ["3", "Find Errors"]]
    return render(request, 'choices.html', {'profiler_options': profiler_options})

@csrf_exempt
def upload_cdrive(request):
    uploaded_file = request.session.get('uploaded_file')
    if request.session["file_type"] == "CDrive":
        uploaded_file_path = os.path.join(CDRIVE_FILES_DIR, uploaded_file)
    else:
        uploaded_file_path = os.path.join(PROJECT_DIR, uploaded_file)
    clean_file_name = os.path.basename(uploaded_file) + CLEAN_FILES_SUFFIX
    clean_file_path = os.path.join(CLEAN_FILES, clean_file_name)
    files = {'file': open(clean_file_path, 'rb')}
    post_url = CDRIVE_URL + "/upload/"
    token = request.session[CLIENT_TOKEN_KEY]
    header = {"Authorization": "Bearer " + token}
    try:
        upload_response = requests.post(post_url, files=files, headers=header)
        django_response = HttpResponse(
            content=upload_response.content,
            status=upload_response.status_code,
            content_type=upload_response.headers['Content-Type']
        )
    except:
        django_response = HttpResponseBadRequest
    return django_response

@csrf_exempt
def remove_token(request):
    if CLIENT_TOKEN_KEY in request.session:
        del request.session[CLIENT_TOKEN_KEY]
    if "uploaded_file" in request.session:
        del request.session["uploaded_file"]
    if "file_type" in request.session:
        del request.session["file_type"]
    return HttpResponse('')

def download(request):
    uploaded_file = request.session.get('uploaded_file')
    if request.session["file_type"] == "CDrive":
        uploaded_file_path = os.path.join(CDRIVE_FILES_DIR, uploaded_file)
    else:
        uploaded_file_path = os.path.join(PROJECT_DIR, uploaded_file[1:])
    clean_file_name = os.path.basename(uploaded_file) + CLEAN_FILES_SUFFIX
    clean_file_path = os.path.join(CLEAN_FILES, clean_file_name)
    if not os.path.exists(CLEAN_FILES):
        os.makedirs(CLEAN_FILES)
    uploaded_df = pd.read_csv(uploaded_file_path)
    uploaded_df.to_csv(clean_file_path, index=False)
    return render(request,
                  'download.html',
                      {
                          'clean_file_name': clean_file_name,
                          'clean_file_path': clean_file_path,
                          'c_drive_ui_url': CDRIVE_UI_URL
                      }
                 )

def clean_strings(request):
    uploaded_file = request.session.get('uploaded_file')
    if request.session["file_type"] == "CDrive":
        uploaded_file_path = os.path.join(CDRIVE_FILES_DIR, uploaded_file)
    else:
        uploaded_file_path = os.path.join(PROJECT_DIR, uploaded_file[1:])
    if request.method == 'POST':
        if "merge" in request.POST:
            values = ','.join(request.POST.getlist('merge'))
            normalize_strings(uploaded_file_path, values)
        similar_strings = get_similar_strings(uploaded_file_path)
        similar_strings_1 = []
        similar_strings_2 = []
        similar_strings_3 = []
        num_strings = len(similar_strings)
        show_normalizer = True
        if num_strings == 0:
            show_normalizer = False
        num_each = len(similar_strings) / 3
        similar_strings_1 = similar_strings[0:num_each]
        similar_strings_2 = similar_strings[num_each:2 * num_each]
        similar_strings_3 = similar_strings[2 * num_each:]
        return render(request, 'clean_strings.html', 
                      {'file_path': uploaded_file,
                       'similar_strings_1': similar_strings_1,
                       'similar_strings_2': similar_strings_2,
                       'similar_strings_3': similar_strings_3,
                       'show_normalizer': show_normalizer
                      })

def show_doc(request):
    uploaded_file = request.session.get('uploaded_file')
    if request.session["file_type"] == "CDrive":
        uploaded_file_path = os.path.join(CDRIVE_FILES_DIR, uploaded_file)
    else:
        uploaded_file_path = os.path.join(PROJECT_DIR, uploaded_file[1:])
    if request.method == 'POST':
        profiler_choice = request.POST['profiler_choice']
        if profiler_choice != "1":
            column_name = 'foo'
            table_A_path = uploaded_file_path
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
                    'num_capitals': num_capitals,
                    'c_drive_ui_url': CDRIVE_UI_URL
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
                    'pervasiveness_uniques': pervasiveness_uniques, 
                    'duplicates': duplicates,
                    'n_missing': n_missing,
                    'pervasiveness_missing': pervasiveness_missing,
                    'type_missing_values_caught': type_missing_values_caught,
                    'type_pervasiveness_dict': type_pervasiveness_dict,
                    'c_drive_ui_url': CDRIVE_UI_URL
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
    return n_uniques, round(pervasiveness*100,2), duplicates

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
    
    return n_missing_values, round((n_missing_values*100)/float(total_values),2), type_missing_values_caught, col_missing

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
                      ('Pervasiveness of Alphabetic Strings', round(pervasivness_alpha*100, 2)),
                      ('Sample of Alphabetic Strings Detected', alpha_sample),
                      ('No. of Alphanumeric Strings', n_alphanumeric),
                      ('Pervasiveness of Alphanumeric Strings', round(pervasivness_alphanumeric*100, 2)),
                      ('Sample of Alphanumeric Strings Detected', alpha_num_sample),
                      ('No. of Numerics', n_numeric),
                      ('Pervasiveness of Numerics', round(pervasivness_numeric*100, 2)),
                      ('Sample of Detected Numerics', numeric_sample),
                      ('No. of Detected Phone Numbers', n_phone,),
                      ('Pervasivness of Detected Phone Numbers', round(pervasivness_phone*100, 2)),
                      ('Sample of Detected Phone Numbers', phone_sample),
                      ('No. of Dates Detected', n_date),
                      ('Pervasiveness of Dates', round(pervasivness_date*100, 2)),
                      ('Sample of Detected Dates', date_sample)])

    

    

    
    
