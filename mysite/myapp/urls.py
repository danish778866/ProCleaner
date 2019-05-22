from django.conf.urls import url
from myapp.views import upload, show_doc, choices, download, sample, upload_cdrive, remove_token, clean_strings

urlpatterns = [
    url(r'^list/$', upload, name='upload'),
    url(r'^show_doc/$', show_doc, name='show_doc'),
    url(r'^choices/$', choices, name='choices'),
    url(r'^download/$', download, name='download'),
    url(r'^sample/$', sample, name='sample'),
    url(r'^upload_cdrive/$', upload_cdrive, name='upload_cdrive'),
    url(r'^remove_token/$', remove_token, name='remove_token'),
    url(r'^clean/$', clean_strings, name='clean_strings'),
]
