#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
from urllib import urlencode
from urllib2 import urlopen
from datetime import datetime


CONFIG_PATH = './config.json'


def _parse_dt(dt_str):
    return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%SZ')


def get_repo_base(config):
    repo = config['repo']
    return 'https://api.github.com/repos/%s' % repo


def gen_release_url(config):
    base = get_repo_base(config)
    return '%s/releases?per_page=1' % base


def gen_recent_closed_pr_url(config):
    base = get_repo_base(config)
    return '%s/pulls?state=closed&sort=update&direction=desc' % base


def load_config(path):
    """Load config file.

    {
      "access_token": "keep-it-secret",
      "repo": "user/repo",
      "branch": "master" // optional
    }
    """
    default = {'branch': 'master'}
    if not os.path.isfile(path):
        print 'Failed to load config.json'
        sys.exit(1)
    with open(path, 'r') as infile:
        content = infile.read()
    data = json.loads(content)
    default.update(data)
    return default


def call_url(url, config):
    qs = urlencode({'access_token': config['access_token']})
    if '?' in url:
        url = '{}&{}'.format(url, qs)
    else:
        url = '{}?{}'.format(url, qs)
    req = urlopen(url)
    result = req.read()
    data = json.loads(result)
    return data


def get_latest_release_time(config):
    url = gen_release_url(config)
    releases = call_url(url, config)
    created_at = releases[0]['created_at']
    return _parse_dt(created_at)


def get_closed_pull_after(dt, config):
    def select_pr(pr):
        return (
            _parse_dt(pr['merged_at']) > dt and
            config['branch'] == pr['base']['ref']
        )

    url = gen_recent_closed_pr_url(config)
    pulls = call_url(url, config)
    after_pulls = filter(select_pr, pulls)
    return after_pulls


def report_pulls(pulls):
    fmt = '* {idx}. #{pull[number]} #{pull[title]} by @{pull[user][login]}'
    for idx, each in enumerate(pulls):
        print fmt.format(idx=idx+1, pull=each)


def main():
    config = load_config(CONFIG_PATH)
    latest_time = get_latest_release_time(config)
    pulls = get_closed_pull_after(latest_time, config)
    report_pulls(pulls)


if __name__ == '__main__':
    main()
