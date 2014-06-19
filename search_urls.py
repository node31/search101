from django.conf.urls import patterns, url

urlpatterns = patterns('gnowsys_ndf.ndf.views.search_views',
		url(r'^$','search',name = 'search'),
		url(r'^process_search/$','process_search',name = 'process_search'),
		url(r'^perform_map_reduce/$','perform_map_reduce',name='perform_map_reduce')		
	)
