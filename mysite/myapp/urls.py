from django.conf.urls import url
from myapp.views import upload, show_doc, choices, clean_file, downloads_page, sample

urlpatterns = [
    url(r'^list/$', upload, name='upload'),
    url(r'^show_doc/$', show_doc, name='show_doc'),
    url(r'^choices/$', choices, name='choices'),
    url(r'^clean_file/$', clean_file, name='clean_file'),
    url(r'^downloads/$', downloads_page, name='downloads_page'),
    url(r'^sample/$', sample, name='sample'),
]
