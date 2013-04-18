#! /usr/bin/env python

# This script collects the lines of code committed over the past 
# seven days on Github in all of the repositories the authorizing
# user has access to.

# Once the script has run, you can point Panic's Status Board at
# the JSON file in the S3 bucket you specify below.

# Recommended to run on a cron job no more than every 15 minutes
# due to rate limiting.

# DO NOT COMMIT THESE SETTINGS TO A PUBLIC REPOSITORY!

GITHUB_TOKEN        =   '' # :string, you can run the get_token.py script in this folder to get a token if you don't have one
GITHUB_NAMES        =   [] # :list of strings, the Github names (both username and full display names) you want to output data for

AWS_BUCKET_NAME     =   '' # :string, the Amazon S3 bucket you want to store your data in
AWS_KEY_NAME        =   '/github/commits.json' # :string, the name you want your data to be saved as on S3 (should end in .json)
AWS_KEY             =   '' # :string, an AWS Access Key ID with access to the specified S3 bucket
AWS_SECRET          =   '' # :string, the AWS Secret Access Key that matches the AWS_KEY setting

GRAPH_TITLE         =   'Lines of Code Committed' # :string, the label to appear on the Status Board graph

# end config

LABELS      =   {
    'total':        'Total Lines',
    'additions':    'Lines Added',
    'deletions':    'Lines Removed',
}

COLORS      =   {
    'total':        'aqua',
    'additions':    'green',
    'deletions':    'red',
}

import json, urllib, sys, boto
from datetime import datetime, timedelta

loc         =   {}
today       =   datetime.now().date()
i           =   0
max_lines   =   0

while i < 7:
    loc[(today - timedelta(days = i)).isoformat()]  =   {
        "total": 0,
        "additions":  0,
        "deletions": 0
    }
    i   +=  1

def build_uri(uri):
    if uri.find('https') == -1:
        uri =   'https://api.github.com/%s' % uri.lstrip('/')
    if uri.find('?') == -1:
        uri =   uri + '?'
    return '%s&access_token=%s' % (uri, GITHUB_TOKEN)

def get_data(uri):
    return json.load(urllib.urlopen(build_uri(uri)))

for repo in get_data('/user/repos'):
    for commit in get_data('/repos/%s/commits' % repo.get('full_name')):
        if commit.get('commit') and commit.get('commit').get('committer') and commit.get('commit').get('committer').get('name') in GITHUB_NAMES:
            commit_date =   commit.get('commit').get('committer').get('date').split('T').pop(0)
            if commit_date in loc:
                commit_data                 =   get_data(commit.get('url'))
                for stat in loc[commit_date].keys():
                    loc[commit_date][stat]  +=  commit_data.get('stats').get(stat)
                if loc[commit_date]['total'] > max_lines:
                    max_lines       =   loc[commit_date]['total']

datasequences   =   []
for stat in LABELS:
    label   =   LABELS.get(stat)
    dp      =   []
    for day in loc:
        numbers =   loc.get(day)
        dp.append({"title": day, "value": numbers.get(stat)})
    dp.sort(key = lambda x: x.get('title'))
    datasequences.append({
        "title":        label,
        "color":        COLORS.get(stat),
        "datapoints":   dp,
    })


datapoints  =   [{"title": x, "value": loc[x]} for x in loc]
datapoints.sort(key = lambda x: x.get('title'))

graph   =   {
    "graph":    {
        "title":            GRAPH_TITLE,
        "type":             "bar",
        "yAxis":            {
            "minValue": 0,
            "maxValue": max_lines,
        },
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