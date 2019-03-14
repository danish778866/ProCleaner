from django import forms

PROFILER_CHOICES = (('1', 'Find Similarity'), ('2', 'Profile'))

class DocumentForm(forms.Form):
    docfile = forms.FileField(
        label = 'Select a File',
        help_text = 'max. 42 megabytes'
    )

class ProfilerChoiceForm(forms.Form):
    profiler_choice_label = forms.ChoiceField(widget=forms.RadioSelect, choices=PROFILER_CHOICES)
