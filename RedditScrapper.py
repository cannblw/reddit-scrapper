#  -*- coding: utf-8 -*-

import json
import requests
import time
import uuid
import sys
import os
from bs4 import BeautifulSoup

# Pages per sub to retrieve per subreddit every time we loop all subreddits
PAGES_PER_SUB = 1

def PrintException():
    exc_type, exc_obj, tb = sys.exc_info()
    f = tb.tb_frame
    lineno = tb.tb_lineno
    filename = f.f_code.co_filename
    linecache.checkcache(filename)
    line = linecache.getline(filename, lineno, f.f_globals)
    print ('EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj))

def jprint(j):
    print( json.dumps(j, indent=4) )

def parse_imgur_img(url, size='m'):
    _id = url.split('/')[-1]
    cover = 'https://i.imgur.com/' + _id + size + '.jpg'
    return cover

def parse_imgur_album(url, size='m'):
    headers = requests.utils.default_headers()
    headers.update({
        'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; HTC One M9 Build/MRA58K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36'
        #'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0.1; E6653 Build/32.2.A.0.253) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.98 Mobile Safari/537.36'
    })
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, 'html.parser')

    img = soup.find('img', {'class': 'Image'})
    if img is None:
        return -1

    src = str(img['src'])
    _id = src.split('/')[-1]
    _id = _id.split('.')[0]

    cover = 'https://i.imgur.com/' + _id + size + '.jpg'
    return cover

def parse_gfycat(url):
    _id = url.split('/')[-1]
    if '?' in _id:
        _id = _id.split('?')[0]

    cover = 'http://thumbs.gfycat.com/' + _id + '-poster.jpg'
    return cover

cnt = 0
totalPosts = 0

subs = []
after = {}
lastAfter = {}
filename = {}

with open('subreddits.txt') as f:
    for line in f:
        subs.append(line.rstrip('\n').strip())

for s in subs:
    with open('after_' + s + '.txt', 'a+') as f:
        f.seek(0)
        after[s] = f.readline().rstrip('\n').strip()

    filename[s] = s + time.strftime('_%Y_%m_%d_%H_%M_%S_') + uuid.uuid4().hex[0:10] + '.txt'

while(True):
    for subreddit in subs:
        print('\nFilename:', filename[subreddit])

        print('Subreddit:', subreddit)

        lastAfter[subreddit] = after[subreddit]

        for i in range(PAGES_PER_SUB):
            try:
                # Set base url
                baseURL = 'https://www.reddit.com/r/' + subreddit + '/new.json?show=all&raw_json=1&limit=1000&after=' + str(after[subreddit])

                cnt += 1
                print('\nRequest to reddit number', cnt)
                print('Target url:', baseURL)
                print('-------------------------------')
                print('-------------------------------')
                print('Current after is:', after[subreddit])
                print('Posts retrieved:', totalPosts)
                print('-------------------------------')

                if after[subreddit] is not None:
                    with open('after_' + subreddit + '.txt', 'w+') as wf:
                        wf.write(after[subreddit])

                # Perform request
                headers = requests.utils.default_headers()
                headers.update({
                    'User-Agent': 'RedditBot 1.0X'
                })
                j = requests.get(baseURL, headers=headers).json()

                # Get after and children
                lastAfter[subreddit] = after[subreddit]
                after[subreddit] = j['data']['after']
                children = j['data']['children']

                # For each post
                for item in children:
                    post = {}

                    # If it is not imgur, reddituploads or gfycat, skip
                    if not ('//imgur.com' in item['data']['url'] or 'i.reddituploads.com' in item['data']['url'] or '//gfycat.com' in item['data']['url']):
                        continue

                    # Get fields from post
                    post['title'] = item['data']['title']
                    post['author'] = item['data']['author']
                    post['url'] = item['data']['url']
                    post['reddit_permalink'] = item['data']['permalink']
                    post['reddit_score'] = item['data']['score']
                    post['reddit_date'] = item['data']['created_utc']

                    if post['author'] == '[deleted]':
                        continue

                    post['thumbnail'] = post['url']
                    # Gfycat
                    if '//gfycat.com' in post['url']:
                        post['thumbnail'] = parse_gfycat(post['url'])
                    # Imgur single picture
                    if ('//imgur.com' in post['thumbnail']) and ('/a/' not in post['url']):
                        post['thumbnail'] = parse_imgur_img(post['url'])
                    # Imgur album
                    if '//imgur.com/a/' in post['thumbnail']:
                        thumb = parse_imgur_album(post['url'])
                        if thumb == -1:
                            continue
                        else:
                            post['thumbnail'] = thumb

                    # Fix imgur jpgm error
                    if 'jpgm' in post['thumbnail'] or 'jpgh' in post['thumbnail'] or 'jpgl' in post['thumbnail']:
                        jpgm_id = post['thumbnail'].split('.')[-3].split('/')[1]
                        jpgm_url = 'https://i.imgur.com/' + jpgm_id + 'm.jpg'
                        post['thumbnail'] = jpgm_url

                    '''
                    if '//imgur.com/a/' in post['thumbnail']:
                        _id = post['url'].split('/')[-1]
                        has_imgur_error = False
                        for attempt in range(200):
                            res = requests.get('https://api.imgur.com/3/album/' + _id)

                            if res.status_code == 200:
                                has_imgur_error = False
                                _pic_id = (res.json())['data']['cover']
                                post['thumbnail'] = 'https://i.imgur.com/' + _pic_id + 'm.jpg'
                                break
                            else:
                                has_imgur_error = True
                                print('Attempt ' + str(attempt+1) + ' to connect to imgur failed with code ' + str(res.status_code) + '. Trying again...')
                                time.sleep(0.25)
                                continue
                        if has_imgur_error:
                            print('Skipping album...')
                            print('-----------------------------------------------------------------')
                            continue
                        '''

                    #print (post['permalink'])
                    #print('-----------------------------------------------------------------')

                    with open(os.path.normpath(os.path.join('./unprocessed_json', filename[subreddit])),'a+', encoding='utf-8') as f:
                        f.write(json.dumps(post, ensure_ascii=False))
                        f.write("\n")

                    totalPosts+=1

            except Exception as e:
                print('An error occurred in attempt ', cnt)
                print('Last after was', lastAfter[subreddit])
                print ('Error message:', str(e))
                try:
                    PrintException()
                except:
                    pass

                print('')
                for i in range(60):
                    sys.stdout.write('Restarting in %d seconds...\r' % (60-i) )
                    sys.stdout.flush()
                    time.sleep(1)
