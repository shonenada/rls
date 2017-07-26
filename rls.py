#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
from urllib import urlencode
from urllib2 import urlopen
from datetime import datetime


CONFIG_PATH = './config.json'


def parse_dt(dt_str):
    return datetime.strptime(dt_str, '%Y-%m-%dT%H:%M:%SZ')


def get_repo_base(config):
    repo = config['repo']
    return 'https://api.github.com/repos/%s' % repo


def gen_latest_release_url(config):
    base = get_repo_base(config)
    return '%s/releases/latest' % base


def gen_recent_closed_pr_url(config):
    base = get_repo_base(config)
    return '%s/pulls?state=closed&sort=update&direction=desc&per_page=50' % base


def gen_commits_url(config, since):
    base = get_repo_base(config)
    return '%s/commits?per_page=50' % base


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


def get_latest_release(config):
    url = gen_latest_release_url(config)
    release = call_url(url, config)
    return release


def get_latest_release_time(config):
    latest_release = get_latest_release(config)
    created_at = latest_release['created_at']
    return parse_dt(created_at)


def get_closed_pull_after(config, dt):
    def select_pr(pr):
        return (
            pr['merged_at'] is not None and
            parse_dt(pr['merged_at']) > dt and
            config['branch'] == pr['base']['ref']
        )

    url = gen_recent_closed_pr_url(config)
    pulls = call_url(url, config)
    after_pulls = filter(select_pr, pulls)
    return after_pulls


def get_commits_after(config, dt):
    def select_commit(commit):
        return (parse_dt(commit['commit']['committer']['date']) > dt and
                commit['commit']['committer']['name'] != 'GitHub')

    url = gen_commits_url(config, dt)
    commits = call_url(url, config)
    after_commits = filter(select_commit, commits)
    return after_commits


def report_pulls(pulls):
    if not pulls:
        return

    print 'new pull request(s):'
    fmt = '* {idx}. [{dt}]: #{pull[number]} {pull[title]} by @{pull[user][login]}'
    for idx, each in enumerate(pulls):
        dt = parse_dt(each['created_at'])
        print fmt.format(idx=idx+1, pull=each, dt=dt)


def report_commits(commits):
    if not commits:
        return

    print 'new commit(s):'
    fmt = '* {idx}. [{dt}]: {commit[message]} by @{commit[author][name]}'
    for idx, each in enumerate(commits):
        commit = each['commit']
        dt = parse_dt(commit['author']['date'])
        print fmt.format(idx=idx+1, commit=commit, dt=dt)


def do_report_commits(config):
    latest_time = get_latest_release_time(config)
    commits = get_commits_after(config, latest_time)
    report_commits(commits)


def do_report_pulls(config):
    latest_time = get_latest_release_time(config)
    pulls = get_closed_pull_after(config, latest_time)
    report_pulls(pulls)


def cli():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', default=CONFIG_PATH)
    parser.add_argument('-i', '--commit', action='store_true', default=False)
    parser.add_argument('-p', '--pull', action='store_true', default=False)

    args = parser.parse_args()
    config = load_config(args.config)

    if args.commit:
        do_report_commits(config)
        print ''

    if args.pull:
        do_report_pulls(config)


if __name__ == '__main__':
    cli()
