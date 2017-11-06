#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import time
import random
import requests
import hashlib
import json
from os import path
from lxml import etree

reload(sys)
sys.setdefaultencoding('utf-8')

BDUSS = ''  # BDUSS(without url-encode)
tbs = ''  # get from login API

forums = [
    # (kw, fid)
]

s = requests.Session()
data = {
    'BDUSS': BDUSS,
    'tbs': tbs
}


def calc_sign(param_map):
    """com/baidu/tbadk/m/a.java#addSign"""
    keys = param_map.keys()
    keys.sort()
    param_str = ''.join(k + '=' + param_map[k] for k in keys)
    return hashlib.md5(param_str + 'tiebaclient!!!').hexdigest().upper()


def send_request(url, data):
    data['sign'] = calc_sign(data)
    resp = s.post(url, data=data)
    result = resp.content.decode('unicode-escape')
    json_result = json.loads(result)
    return result, json_result


def update_tbs():
    login_url = 'http://c.tieba.baidu.com/c/s/login'
    login_data = {'bdusstoken': data['BDUSS']}
    result, j = send_request(login_url, login_data)
    return j['anti']['tbs']


def read_forums():
    filename = 'forums.txt'
    if path.exists(filename):
        with open(filename, 'rb') as f:
            saved_forums = json.loads(f.read())
            return saved_forums
    else:
        new_forums = get_forums()
        with open(filename, 'wb') as f:
            f.write(json.dumps(new_forums))
        return new_forums


def get_forums():
    print('>> get forums..')
    url = 'http://tieba.baidu.com/mo/m?tn=bdFBW&tab=favorite'
    cookies = {'BDUSS': data['BDUSS']}
    # ignore cookies
    resp = requests.get(url, cookies=cookies)
    dom = etree.HTML(resp.content)
    table = dom.cssselect('div.d > table.tb')[0]
    kws = map(lambda tr: tr[0][0].text, table)
    print('>> your forum names:', ','.join(kws))
    print('>> get forum: kw -> fid')
    fids = map(get_fid, kws)
    return zip(kws, fids)


def get_fid(kw):
    time.sleep(3 + 5 * random.random())
    # ignore cookies
    resp = requests.get('http://tieba.baidu.com/mo/m?kw=' + kw)
    dom = etree.HTML(resp.content)
    node = dom.cssselect('input[type="hidden"][name="fid"]')[0]
    fid = node.get('value')
    print('>> get forum: (%s, %s)' % (kw, fid))
    return fid


def sign(kw, fid):
    sign_url = 'http://c.tieba.baidu.com/c/c/forum/sign'
    sign_data = {'kw': kw, 'fid': fid}
    sign_data.update(data)
    result, j = send_request(sign_url, sign_data)
    if j['error_code'] == '160002':
        print('>> signed', kw)
    elif j['error_code'] == '0':
        info = j['user_info']
        level = info['level_name']
        cont = info['cont_sign_num']
        print('>> sign %s: %s %s' % (kw, level, cont))
    else:
        print(result)


def add_post(kw, fid, tid, content):
    post_url = 'http://c.tieba.baidu.com/c/c/post/add'
    post_data = {'kw': kw, 'fid': fid, 'tid': tid, 'content': content}
    post_data.update(data)
    result, j = send_request(post_url, post_data)
    print(result)


if __name__ == '__main__':
    if not data['BDUSS']:
        print('>> no BDUSS..')
        sys.exit(1)
    if not data['tbs']:
        print('>> update tbs..')
        data['tbs'] = update_tbs()
        print('>> tbs:', data['tbs'])
    if not forums:
        forums = read_forums()
    for kw, fid in forums:
        time.sleep(3 + 5 * random.random())
        sign(kw, fid)
