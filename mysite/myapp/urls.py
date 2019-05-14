from django.conf.urls import url
from myapp.views import list, show_doc, profiler_choice, clean_file, downloads_page, list_tuples

urlpatterns = [
    url(r'^list/$', list, name='list'),
    url(r'^show_doc/$', show_doc, name='show_doc'),
    url(r'^profiler_choice/$', profiler_choice, name='profiler_choice'),
    url(r'^clean_file/$', clean_file, name='clean_file'),
    url(r'^downloads/$', downloads_page, name='downloads_page'),
    url(r'^list_tuples/$', list_tuples, name='list_tuples'),
]
