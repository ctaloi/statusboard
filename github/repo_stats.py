#! /usr/bin/env python

# This script ranks the top 5 repositories belong to the user
# by the total number of forks, stars and open issues.

# Once the script has run, you can point Panic's Status Board at
# the JSON file in the S3 bucket you specify below.

# Recommended to run on a cron job no more than every 15 minutes
# due to rate limiting.

# DO NOT COMMIT THESE SETTINGS TO A PUBLIC REPOSITORY!

GITHUB_TOKEN        =   '' # :string, you can run the get_token.py script in this folder to get a token if you don't have one

AWS_BUCKET_NAME     =   '' # :string, the Amazon S3 bucket you want to store your data in
AWS_KEY_NAME        =   '/github/repo-stats.json' # :string, the name you want your data to be saved as on S3 (should end in .json)
AWS_KEY             =   '' # :string, an AWS Access Key ID with access to the specified S3 bucket
AWS_SECRET          =   '' # :string, the AWS Secret Access Key that matches the AWS_KEY setting

GRAPH_TITLE         =   'Top 5 Repos by Engagement' # :string, the label to appear on the Status Board graph

import json, urllib, sys, boto
from datetime import datetime, timedelta

LABELS      =   {
    'stargazers':   'Stars',
    'forks':        'Forks',
    'issues':       'Open Issues',
}

COLORS      =   {
    'stargazers':   'yellow',
    'forks':        'purple',
    'issues':       'red',
}

repos   =   {}

def build_uri(uri):
    if uri.find('https') == -1:
        uri =   'https://api.github.com/%s' % uri.lstrip('/')
    if uri.find('?') == -1:
        uri =   uri + '?'
    return '%s&access_token=%s' % (uri, GITHUB_TOKEN)

def get_data(uri):
    response    =   urllib.urlopen(build_uri(uri))
    headers     =   response.headers
    data        =   json.load(response)
    if headers.get('Link'):
        # see if we have a next page to grab
        links   =   headers.get('Link').split(',')
        links   =   [link.strip() for link in links]
        for link in links:
            link    =   link.split(';')
            if len(link) == 2:
                link_uri    =   link.pop(0).strip('<>').strip('')
                link_rel    =   link.pop(0).replace('rel=', '').replace('"', '').strip()
                if link_rel == "next":
                    # we can assume the data is a list or it wouldn't be paginated
                    data    =   data + get_data(link_uri)
    return data

username    =   get_data('/user').get('login')
totals      =   []

for repo in get_data('/user/repos?type=public'):
    if repo.get('owner').get('login') == username:
        repos[repo.get('name')] =   {
            "stargazers":   repo.get('watchers_count'),
            "forks":        repo.get('forks_count'),
            "issues":       repo.get('open_issues'),
            "total":        repo.get('watchers_count') + repo.get('forks_count') + repo.get('open_issues')
        }
        totals.append(repos[repo.get('name')].get('total'))

totals.sort(reverse = True)
if len(totals) > 5:
    threshold   =   totals[4]
    repos       =   dict((k, v) for k, v in repos.iteritems() if v.get('total') >= threshold)

repos   =   sorted(repos.iteritems(), key = lambda x: x[1].get('total'))
if len(repos) > 5:
    repos   =   repos[-5:]

datasequences   =   []
for stat in LABELS:
    label   =   LABELS.get(stat)
    dp      =   []
    for repo, numbers in repos:
        dp.append({"title": repo, "value": numbers.get(stat)})
    datasequences.append({
        "title":        label,
        "color":        COLORS.get(stat),
        "datapoints":   dp,
    })

graph   =   {
    "graph":    {
        "title":            GRAPH_TITLE,
        "type":             "bar",
        "datasequences":    datasequences,
    },
}

s3      =   boto.connect_s3(AWS_KEY, AWS_SECRET)
bucket  =   s3.get_bucket(AWS_BUCKET_NAME)
key     =   bucket.get_key('%s' % AWS_KEY_NAME)
if key is None:
    key =   bucket.new_key('%s' % AWS_KEY_NAME)
key.set_contents_from_string(json.dumps(graph))
key.set_acl('public-read')

sys.exit()