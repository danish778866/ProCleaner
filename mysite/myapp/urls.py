from django.conf.urls import url
from myapp.views import upload, show_doc, choices, download, downloads_page, sample, upload_cdrive, remove_token

urlpatterns = [
    url(r'^list/$', upload, name='upload'),
    url(r'^show_doc/$', show_doc, name='show_doc'),
    url(r'^choices/$', choices, name='choices'),
    url(r'^download/$', download, name='download'),
    url(r'^downloads/$', downloads_page, name='downloads_page'),
    url(r'^sample/$', sample, name='sample'),
    url(r'^upload_cdrive/$', upload_cdrive, name='upload_cdrive'),
    url(r'^remove_token/$', remove_token, name='remove_token'),
]
