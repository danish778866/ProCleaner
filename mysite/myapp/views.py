# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
import py_stringsimjoin as ssj
import py_stringmatching as sm
import pandas as pd
import os, sys

from myapp.models import Document
from myapp.forms import DocumentForm, ProfilerChoiceForm
def list(request):
    # Handle file upload
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        process_file = request.POST.getlist('process_file')
        if form.is_valid():
            if 'docfile' in request.FILES:
                newdoc = Document(docfile=request.FILES['docfile'])
                newdoc.save()

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
    uploaded_file_name = request.session.get('uploaded_file_path')
    return render(request, 'profiler_choice.html', {'form': form, 'ret': uploaded_file_name})

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
    uploaded_file = open(uploaded_file_path, "r")
    clean_file = open(cleaned_file_path, "w")
    line = uploaded_file.readline()
    while line:
        line = line.strip()
        if line in substitute.keys():
            ret_val = ret_val + line + " "
            clean_file.write(substitute[line] + "\n")
        else:
            clean_file.write(line + "\n")
        line = uploaded_file.readline()
    uploaded_file.close()
    clean_file.close()
    return render(request, 'clean_file.html', {'cleaned_file_name': os.path.basename(uploaded_file_name) + 
                                               ".clean", 'rules_file_name': os.path.basename(uploaded_file_name) + ".rules"})

def show_doc(request):
    project_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    uploaded_file = request.session.get('uploaded_file_path')
    if request.method == 'POST':
        profiler_choice = request.POST['profiler_choice_label']
        if profiler_choice == "1":
            table_A_path = project_dir + uploaded_file
            table_B_path = project_dir + uploaded_file
            A = pd.read_csv(table_A_path, names=['foo'])
            A['id'] = range(0, len(A))
            B = pd.read_csv(table_B_path, names=['foo'])
            B['id'] = range(0, len(B))
            qg3_tok = sm.QgramTokenizer(qval=3)
            #ws = sm.WhitespaceTokenizer(return_set=True)
            output_pairs = ssj.jaccard_join(A, B, 'id', 'id', 'foo', 'foo' , qg3_tok, 0.3,
                                        l_out_attrs=['foo'], r_out_attrs=['foo'])
            similar_pairs = []
            for index, row in output_pairs.iterrows():
                if row['_sim_score'] < 1.0:
                    current_pair = {}
                    current_pair['0'] = row['l_foo']
                    current_pair['1'] = row['r_foo']
                    similar_pairs.append(current_pair)
        else:
            similar_pairs = []
    ret_val = request.POST
    return render(request, 'show_doc.html', {'file_path': uploaded_file, 'ret_val': ret_val, 'similar_pairs': similar_pairs})
    
# Create your views here.
