from django.shortcuts import render
from django.http import HttpResponse
from gnowsys_ndf.ndf.models import *
from django.template import RequestContext

from stemming.porter2 import stem

import string

import itertools

collection = get_database()[Node.collection_name]

def search(request,group_id):
	"""Renders a list of all 'Page-type-GSystems' available within the database.
    	"""
    	ins_objectid  = ObjectId()
    	if ins_objectid.is_valid(group_id) is False :
        	group_ins = collection.Node.find_one({'_type': "Group","name": group_id})
        	auth = collection.Node.one({'_type': 'Author', 'name': unicode(request.user.username) })
        	if group_ins:
        	    group_id = str(group_ins._id)
        	else :
        	    auth = collection.Node.one({'_type': 'Author', 'name': unicode(request.user.username) })
        	    if auth :
                	group_id = str(auth._id)
	else:
        	pass        
        
	#return HttpResponse("Hello %s" % group_id)
	return render(request,"ndf/search_home.html",{"groupid":group_id},context_instance = RequestContext(request))
	
def remove_punctuation(s):
	#Helper Function for: process_search
	#Pre-condition:A string
	#Post-condition:A string without punctuation
	
	#For this we are going to use another method called as "translate()"
	
	#The method translate() returns a copy of the string in which all characters have been translated using 
	#table (constructed with the maketrans() function in the string module), optionally deleting all characters
	#found in the string deletechars.
	#str.translate(table[, deletechars])
	
	#A very nice description of this has been provided at tutorialspoint.com
	#return s.translate(string.maketrans("",""),string.punctuation)
	#This is unicode.translate which is a bit different from normal translate function
	
	#This method removes punctuation even if it is present inside a word.Thus this function can be very good or very bad
	
	translate_table = dict((ord(c),None) for c in string.punctuation)
	return s.translate(translate_table)
	
def remove_extra(s_l):
	#Helper Function for:process_search
	#Pre-condition:A list of words from which you want to remove unneccesary words
	#Post-Condition:A list of words from without the extra words
	
	#This function works just fine
	remove_list = ["a","an","the","and","on","at","or","is"]
	
	for i in remove_list:
		for j in s_l:
			if i == j:
				s_l.remove(j)
	
	return s_l
	
	
def stem_list(s_l):
	#Helper Function for:process_search
	#Pre-condition:A list of words 
	#Post-Condition:A list of stemmed words
			
	s_stem_l = []
	
	for i in s_l:
		s_stem_l.append(stem(i.lower()))
		
	#print s_stem_l
	return s_stem_l
	
	
def process_search(request,group_id):

	################################### Flow 1 ###############################################
	print "TEXT TO BE SEARCHED",request.GET["text_to_be_searched"] #Comment this line
	
	search_by_name = False
	search_by_tags = False
	search_by_content = False
	
	#Getting the list of options how the user wants to perform the search
	some_var = request.GET.getlist('opt[]')
	
	#Setting the appropritate Python Variables to True and False
	for i in some_var:
		if i == "name":
			search_by_name = True
		if i == "tags":
			search_by_tags = True
		if i == "content":
			search_by_content = True
				
	
	#If none of the checkboxes are selected, i..e all the variables have been set to false.
	#In such a scene we have to search by all(i.e. name,tags,content)
	
	
	if not search_by_name and not search_by_tags and not search_by_content:
		search_by_name = True
		search_by_tags = True
		search_by_content = True
	
	
	print search_by_name,search_by_tags,search_by_content #Comment this line
	
	#####################################################################################################
	
	search_text = request.GET["text_to_be_searched"]
	search_text_copy = request.GET["text_to_be_searched"]
	
	search_text = remove_punctuation(search_text)
	search_text_l = search_text.split()
	
	print search_text #Comment this line
	print search_text_l #Comment this line
	
	search_text_l = remove_extra(search_text_l)
	stem_split_search_text = stem_list(search_text_l)
	
	print stem_split_search_text
	
	return HttpResponse("Hello")
	
def perform_map_reduce(request,group_id):
	#This function shall perform map reduce on all the objects which are present in the ToReduce() class Collection
	all_instances = list(collection.ToReduce.find({'required_for':'map_reduce_to_reduce'}))
	for particular_instance in all_instances:
		print particular_instance._id,'\n'
		particular_instance_id  = particular_instance.id_of_document_to_reduce
		#Now Pick up a node from the Node Collection class
		orignal_node = collection.Node.find_one({"_id":particular_instance_id})		
		map_reduce_node = collection.MyReduce.find_one({'required_for':'map_reduce_reduced','orignal_doc_id':particular_instance_id})
		if map_reduce_node:
			map_reduce_node.content_org = dict(map_reduce(orignal_node.content_org,mapper,reducer))
			map_reduce_node.save()
		else:
			z = collection.MyReduce()
			z.content_org = dict(map_reduce(orignal_node.content_org,mapper,reducer))
			z.orignal_doc_id = particular_instance_id
			z.required_for = u'map_reduce_reduced'
			z.save()
		#After performing MapReduce that particular instance should be removed from the ToReduce() class collection
		particular_instance.delete()		
	return HttpResponse("Map Reduce was performed successfully")
	
def mapper(input_value):
	#Step1: Remove all the punctuation from the content
	#Step2: Remove unnecessay words from the content
	#Step3: Convert these words to lower case and stem these words
	
	#This map functions converts all the words to lower case and then stems these words
	input_value = remove_punctuation(input_value)
	input_value_l = remove_extra(input_value.split())
	l = []
	for i in input_value_l:
		l.append([stem(i.lower()),1])
	print "PRINTING THE LIST _____________________________________*_________________________________",l
	return l
	
def reducer(intermediate_key,intermediate_value_list):
	return (intermediate_key,sum(intermediate_value_list))

def map_reduce(x,mapper,reducer):
	intermediate = mapper(x)
	groups = {}
	for key,group in itertools.groupby(sorted(intermediate),lambda x:x[0]):
		groups[key] = list([y for x,y in group])
		
	reduced_list = [reducer(intermediate_key,groups[intermediate_key]) for intermediate_key in groups ]
	print reduced_list,'\n'
	return reduced_list
	
