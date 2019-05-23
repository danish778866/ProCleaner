from django.conf.urls import url
from myapp.views import upload, show_doc, choices, download, sample, upload_cdrive, exit_app, clean_strings

urlpatterns = [
    url(r'^list/$', upload, name='upload'),
    url(r'^show_doc/$', show_doc, name='show_doc'),
    url(r'^choices/$', choices, name='choices'),
    url(r'^download/$', download, name='download'),
    url(r'^sample/$', sample, name='sample'),
    url(r'^upload_cdrive/$', upload_cdrive, name='upload_cdrive'),
    url(r'^exit_app/$', exit_app, name='exit_app'),
    url(r'^clean/$', clean_strings, name='clean_strings'),
]
