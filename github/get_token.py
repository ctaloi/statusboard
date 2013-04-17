#! /usr/bin/env python

import json, urllib2, argparse, base64, sys, os
from getpass import getpass

AUTH_URL		=	'https://api.github.com/authorizations'

username		=	raw_input('Your Github username: ')
password 		=	getpass('Your Github password: ')

request 		=	urllib2.Request(AUTH_URL, data = '{"scopes": ["repo"], "note": "Panic Status Board python scripts"}')
request.add_header('Content-Type', 'application/json')
request.add_header('Authorization', 'Basic %s' % (base64.urlsafe_b64encode('%s:%s' % (username, password))))
request.add_header('Accept', 'application/json')
try:
	response	=	urllib2.urlopen(request)
except:
	sys.stderr.write('There was a problem making the request to Github\n')
	sys.stderr.flush()
	sys.exit(os.EX_UNAVAILABLE)

data 			=	json.load(response)

sys.stdout.write('Your Github API token is: %s\n' % data.get('token'))
sys.stdout.flush()
sys.exit(os.EX_OK)