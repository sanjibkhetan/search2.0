# -*- coding: utf-8 -*-
#
# @project slideSearch
# @file webs/WebService.py
# @author  Rahul Arya <rahul.arya@prezent.ai>
# @author  Amar Dani <amar.dani@prezent.ai>
# @version 1.0.0
# 
# @section DESCRIPTION
# 
#   WebService.py :  Web Service
# 
# @section LICENSE
# 
# Copyright (c) 2022 Rahul Arya.
# Copyright (c) 2022 Prezentium Inc.
# 
# This source code is protected under international copyright law.  All rights
# reserved and protected by the copyright holders.
#
# This file is confidential and only available to authorized individuals with the
# permission of the copyright holders.  If you encounter this file and do not have
# permission, please contact the copyright holders and delete this file.
#
# THE SOFTWARE IS PROVIDED , WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
import logging
import re
from pathlib import Path
from time import strftime

from flask import Flask, jsonify, render_template, request
# from steps.evaluate_bert import evaluate, ulify
from waitress import serve
#from search import get_sentences
#from searchv1 import searchv1
#from searchv4 import searchv4
#from searchv5 import searchv5
#from search_V1 import search_V1
#from search_V3 import search_V3
#from search_V4 import search_V4
from search_V6 import search_V6
class WebService():
	"""Default WebService class to be called in app."""

	def _GetPath(self, htpath):
		return htpath if htpath.startswith('/') else Path(Path.cwd(),htpath).as_posix()

	def _HandlePost(self, request):
		""" get post content"""
		content_type = request.headers.get('Content-Type')
		if content_type == 'application/json':
			return request.json
		elif re.match('multipart/form-data',content_type) or re.match('application/x-www-form-urlencoded',content_type):
			robj = {}
			for item in request.form.keys():
				robj[item]=request.form[item]
			return robj
		else:
			return {}

	def __init__(self, params):
		"""Constructor."""
		logging.basicConfig()

		use_logger = logging.getLogger('waitress')
		use_logger.setLevel(logging.INFO)
		self.app = Flask(__name__, template_folder='templates')
		app = self.app
		# size 512 Mb 
		app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024 * 1024

		# htpasswd
		app.config['FLASK_AUTH_ALL']= params['FLASK_AUTH_ALL']
		htpath = params['FLASK_HTPASSWD_PATH']
		htpath = htpath if htpath.startswith('/') else Path(Path.cwd(),htpath).as_posix()
		app.config['FLASK_HTPASSWD_PATH'] = htpath

		# auth message
		app.config['FLASK_AUTH_REALM'] = params['FLASK_AUTH_REALM']

		# host and port
		app.config['APP_HTTP_HOST'] = params['APP_HTTP_HOST']
		app.config['APP_HTTP_PORT'] = params['APP_HTTP_PORT']

		# callback
		app.config['APP_CALLBACK_URL'] = params['APP_CALLBACK_URL']
		app.config['APP_CALLBACK_USER'] = params['APP_CALLBACK_USER']
		app.config['APP_CALLBACK_PASS'] = params['APP_CALLBACK_PASS']

		# extra
		app.config['APP_SERVER_NAME'] = params['APP_SERVER_NAME']

		app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'


		@app.after_request
		def after_request(response):
			""" Logging after every request. """
			ts = strftime('[%Y-%b-%d %H:%M:%S]')
			use_logger.info('%s : %s %s %s', ts, request.method, request.full_path, response.status)
			return response

		@app.route('/generatedemo', methods=['GET', 'POST'])
		def generatedemo():
			xdata = {}
			xdata['foptions'] = [ \
				['generate_bert','Generate Bert Embedding','checked'], \
				['generate_openai','Generate OpenAi Embedding',''], \
				]
			xdata['results'] = {}
			payload={}
			QTc_result = False
			try:
				if request.method == 'POST':
					qdata = self._HandlePost(request)
					json_data = {  }
					if 'query' in qdata and len(qdata['query'])>0:
						qry = ' '.join(qdata['query'] \
							.replace("\n",' ') \
							.replace("\r",' ') \
							.replace("“", '"') \
							.replace("”", '"') \
							.replace("‘", "'") \
							.replace("- ", "") \
							.replace('"', "'") \
							.split())
						json_data['sentences']=[ qry ]
						xdata['qry']=qry
					else:
						raise ValueError("Query is blank")
					soption = []
					for xitem in xdata['foptions']:
						if xitem[0] in qdata:
							json_data[ xitem[0] ]=True
							xitem[2] = 'checked'
							soption.append(xitem[0])
						else:
							json_data[ xitem[0] ]=False
							xitem[2] = ''
					lookup = {
							'generate_openai'  : 'OpenAi',
							'generate_bert' : 'Bert',
						}
					xdata['lookup'] = lookup
					def get_emp(text, query):
						ind_val='abbvie_aa_nsm_test'
						if text == "generate_bert":
							x =  get_sentences(query,ind_val)
							return x 
					for look in lookup.keys():
						if look in soption:

							xdata['results'][look]={ 'label' : lookup[look], 'col':get_emp(look, json_data['sentences'][0])}
							
			except ValueError as ve:
				xdata['errormsg'] = str(ve)
			print(xdata)
			return render_template('generatedemov1.html', data = xdata)
		@app.route('/generatedemosynonyms', methods=['GET', 'POST'])
		def generatedemowithsynonyms():
			xdata = {}
			xdata['foptions'] = [ \
				['generate_bert','Generate Bert Embedding','checked'], \
				['generate_openai','Generate OpenAi Embedding',''], \
				]
			xdata['results'] = {}
			payload={}
			QTc_result = False
			try:
				if request.method == 'POST':
					qdata = self._HandlePost(request)
					json_data = {  }
					if 'query' in qdata and len(qdata['query'])>0:
						qry = ' '.join(qdata['query'] \
							.replace("\n",' ') \
							.replace("\r",' ') \
							.replace("“", '"') \
							.replace("”", '"') \
							.replace("‘", "'") \
							.replace("- ", "") \
							.replace('"', "'") \
							.split())
						json_data['sentences']=[ qry ]
						xdata['qry']=qry
					else:
						raise ValueError("Query is blank")
					soption = []
					for xitem in xdata['foptions']:
						if xitem[0] in qdata:
							json_data[ xitem[0] ]=True
							xitem[2] = 'checked'
							soption.append(xitem[0])
						else:
							json_data[ xitem[0] ]=False
							xitem[2] = ''
					lookup = {
							'generate_openai'  : 'OpenAi',
							'generate_bert' : 'Bert',
						}
					xdata['lookup'] = lookup
					def get_emp(text, query):
						ind_val='abbvie_aa_nsm_test_synon'
						if text == "generate_bert":
							x =  get_sentences(query,ind_val)
							return x
					for look in lookup.keys():
						if look in soption:

							xdata['results'][look]={ 'label' : lookup[look], 'col':get_emp(look, json_data['sentences'][0])}
							
			except ValueError as ve:
				xdata['errormsg'] = str(ve)
			print(xdata)
			return render_template('generatedemov2.html', data = xdata)
		@app.route('/generatedemosynonyms_with_lower', methods=['GET', 'POST'])
		def generatedemosynonyms_with_lower():
			xdata = {}
			xdata['foptions'] = [ \
				['generate_bert','Generate Bert Embedding','checked'], \
				['generate_openai','Generate OpenAi Embedding',''], \
				]
			xdata['results'] = {}
			payload={}
			QTc_result = False
			try:
				if request.method == 'POST':
					qdata = self._HandlePost(request)
					json_data = {  }
					if 'query' in qdata and len(qdata['query'])>0:
						qry = ' '.join(qdata['query'] \
							.replace("\n",' ') \
							.replace("\r",' ') \
							.replace("“", '"') \
							.replace("”", '"') \
							.replace("‘", "'") \
							.replace("- ", "") \
							.replace('"', "'") \
							.split())
						json_data['sentences']=[ qry ]
						xdata['qry']=qry
					else:
						raise ValueError("Query is blank")
					soption = []
					for xitem in xdata['foptions']:
						if xitem[0] in qdata:
							json_data[ xitem[0] ]=True
							xitem[2] = 'checked'
							soption.append(xitem[0])
						else:
							json_data[ xitem[0] ]=False
							xitem[2] = ''
					lookup = {
							'generate_openai'  : 'OpenAi',
							'generate_bert' : 'Bert',
						}
					xdata['lookup'] = lookup
					def get_emp(text, query):
						ind_val='abbvie_aa_nsm_test_synon_with_lower'
						if text == "generate_bert":
							x =  get_sentences(query,ind_val)
							return x
					for look in lookup.keys():
						if look in soption:

							xdata['results'][look]={ 'label' : lookup[look], 'col':get_emp(look, json_data['sentences'][0])}
							
			except ValueError as ve:
				xdata['errormsg'] = str(ve)
			print(xdata)
			return render_template('generatedemov3.html', data = xdata)
		@app.route('/generatedemosynonyms_without_lower', methods=['GET', 'POST'])
		def generatedemosynonyms_without_lower():
			xdata = {}
			xdata['foptions'] = [ \
				['generate_bert','Generate Bert Embedding','checked'], \
				['generate_openai','Generate OpenAi Embedding',''], \
				]
			xdata['results'] = {}
			payload={}
			QTc_result = False
			try:
				if request.method == 'POST':
					qdata = self._HandlePost(request)
					json_data = {  }
					if 'query' in qdata and len(qdata['query'])>0:
						qry = ' '.join(qdata['query'] \
							.replace("\n",' ') \
							.replace("\r",' ') \
							.replace("“", '"') \
							.replace("”", '"') \
							.replace("‘", "'") \
							.replace("- ", "") \
							.replace('"', "'") \
							.split())
						json_data['sentences']=[ qry ]
						xdata['qry']=qry
					else:
						raise ValueError("Query is blank")
					soption = []
					for xitem in xdata['foptions']:
						if xitem[0] in qdata:
							json_data[ xitem[0] ]=True
							xitem[2] = 'checked'
							soption.append(xitem[0])
						else:
							json_data[ xitem[0] ]=False
							xitem[2] = ''
					lookup = {
							'generate_openai'  : 'OpenAi',
							'generate_bert' : 'Bert',
						}
					xdata['lookup'] = lookup
					def get_emp(text, query):
						ind_val='abbvie_aa_nsm_test_synon_without_lower'
						if text == "generate_bert":
							x =  get_sentences(query,ind_val)
							return x
					for look in lookup.keys():
						if look in soption:

							xdata['results'][look]={ 'label' : lookup[look], 'col':get_emp(look, json_data['sentences'][0])}
							
			except ValueError as ve:
				xdata['errormsg'] = str(ve)
			print(xdata)
			return render_template('generatedemov4.html', data = xdata)
		@app.route('/abbvie_aa_nsm_with_synonmys_with_lower_space_sep_avg_1000', methods=['GET', 'POST'])
		def abbvie_aa_nsm_with_synonmys_with_lower_space_sep_avg_1000():
			xdata = {}
			xdata['foptions'] = [ \
				['generate_bert','Generate Bert Embedding','checked'], \
				['generate_openai','Generate OpenAi Embedding',''], \
				]
			xdata['results'] = {}
			payload={}
			QTc_result = False
			try:
				if request.method == 'POST':
					qdata = self._HandlePost(request)
					json_data = {  }
					if 'query' in qdata and len(qdata['query'])>0:
						qry = ' '.join(qdata['query'] \
							.replace("\n",' ') \
							.replace("\r",' ') \
							.replace("“", '"') \
							.replace("”", '"') \
							.replace("‘", "'") \
							.replace("- ", "") \
							.replace('"', "'") \
							.split())
						json_data['sentences']=[ qry ]
						xdata['qry']=qry
					else:
						raise ValueError("Query is blank")
					soption = []
					for xitem in xdata['foptions']:
						if xitem[0] in qdata:
							json_data[ xitem[0] ]=True
							xitem[2] = 'checked'
							soption.append(xitem[0])
						else:
							json_data[ xitem[0] ]=False
							xitem[2] = ''
					lookup = {
							'generate_openai'  : 'OpenAi',
							'generate_bert' : 'Bert',
						}
					xdata['lookup'] = lookup
					def get_emp(text, query):
						ind_val='abbvie_aa_nsm_with_synonmys_without_lower_space_sep_avg_1000'
						if text == "generate_bert":
							x =  get_sentences(query,ind_val)
							return x
					for look in lookup.keys():
						if look in soption:

							xdata['results'][look]={ 'label' : lookup[look], 'col':get_emp(look, json_data['sentences'][0])}
							
			except ValueError as ve:
				xdata['errormsg'] = str(ve)
			print(xdata)
			return render_template('generatedemov5.html', data = xdata)
		@app.route('/abbvie_aa_nsm_with_keysearch', methods=['GET', 'POST'])
		def abbvie_aa_nsm_with_keysearch():
			print(";;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;")
			xdata = {}
			xdata['foptions'] = [ \
				['generate_bert','Generate Bert Embedding','checked'], \
				['generate_openai','Generate OpenAi Embedding',''], \
				]
			xdata['results'] = {}
			payload={}
			QTc_result = False
			try:
				if request.method == 'POST':
					qdata = self._HandlePost(request)
					json_data = {  }
					if 'query' in qdata and len(qdata['query'])>0:
						qry = ' '.join(qdata['query'] \
							.replace("\n",' ') \
							.replace("\r",' ') \
							.replace("“", '"') \
							.replace("”", '"') \
							.replace("‘", "'") \
							.replace("- ", "") \
							.replace('"', "'") \
							.split())
						json_data['sentences']=[ qry ]
						xdata['qry']=qry
					else:
						raise ValueError("Query is blank")
					soption = []
					for xitem in xdata['foptions']:
						if xitem[0] in qdata:
							json_data[ xitem[0] ]=True
							xitem[2] = 'checked'
							soption.append(xitem[0])
						else:
							json_data[ xitem[0] ]=False
							xitem[2] = ''
					lookup = {
							'generate_openai'  : 'OpenAi',
							'generate_bert' : 'Bert',
						}
					xdata['lookup'] = lookup
					def get_emp(text, query):
						#ind_val='abbvie_aa_nsm_with_synonmys_without_lower_space_sep_avg_1000'
						if text == "generate_bert":
							x =  searchv4(query)
							return x
					for look in lookup.keys():
						if look in soption:

							xdata['results'][look]={ 'label' : lookup[look], 'col':get_emp(look, json_data['sentences'][0])}
							
			except ValueError as ve:
				xdata['errormsg'] = str(ve)
			#print(xdata)
			return render_template('generatedemov6.html', data = xdata)
		
		@app.route('/abbvie_aa_nsm_with_keysearch_v1', methods=['GET', 'POST'])
		def abbvie_aa_nsm_with_keysearch_v1():
			print("keysearch_v1 object creation done....")
			print("----------- Entered inside GET ----------------")
			xdata = {}
			xdata['foptions'] = [ \
				['generate_bert','Generate Bert Embedding','checked'], \
				['generate_openai','Generate OpenAi Embedding',''], \
				]
			xdata['results'] = {}
			payload={}
			QTc_result = False
			try:
				if request.method == 'POST':
					print("----------- Entered inside POST ----------------")
					qdata = self._HandlePost(request)
					json_data = {  }
					if 'query' in qdata and len(qdata['query'])>0:
						qry = ' '.join(qdata['query'] \
							.replace("\n",' ') \
							.replace("\r",' ') \
							.replace("“", '"') \
							.replace("”", '"') \
							.replace("‘", "'") \
							.replace("- ", "") \
							.replace('"', "'") \
							.split())
						json_data['sentences']=[ qry ]
						xdata['qry']=qry
					else:
						raise ValueError("Query is blank")
					soption = []
					for xitem in xdata['foptions']:
						if xitem[0] in qdata:
							json_data[ xitem[0] ]=True
							xitem[2] = 'checked'
							soption.append(xitem[0])
						else:
							json_data[ xitem[0] ]=False
							xitem[2] = ''
					lookup = {
							'generate_openai'  : 'OpenAi',
							'generate_bert' : 'Bert',
						}
					xdata['lookup'] = lookup
					def get_emp(text, query):
						#ind_val='abbvie_aa_nsm_with_synonmys_without_lower_space_sep_avg_1000'
						if text == "generate_bert":
							x, query_s =  search_V6(query)
							return x
					for look in lookup.keys():
						if look in soption:

							xdata['results'][look]={ 'label' : lookup[look], 'col':get_emp(look, json_data['sentences'][0])}
							
			except ValueError as ve:
				xdata['errormsg'] = str(ve)
			#print(xdata)
			return render_template('generatedemov7.html', data = xdata)

		@app.route('/generate', methods=['GET', 'POST'])
		def generate():
			query = request.args.get('query')
			out = 'aa' #qhandle.get_modified_query(query)
			data = {
				"original" : query,
				"query" : out,
				}
			return jsonify(data)

	def run(self):
		"""Blocking run service."""
		app = self.app
		serve(app, host="0.0.0.0",port=8446)
		#serve(app, host="0.0.0.0")