import json
import re
import time
import os
try:
    import urllib.request as request
except:
    print('this program requires urllib.request!')
    exit()

which_bots = set(input('type bot names separated by comma:\n').split(','))
print('you selected: {}'.format(which_bots))

if len(which_bots) == 1 and which_bots.issubset(('',)):
    which_bots.clear()

if len(which_bots) > 3:
    print('too many bots, exit')
    exit()

all_log_json_url = 'http://auctions11.usydrobotics.club/api/fullLogs/stat'

all_log_json = None

with request.urlopen(all_log_json_url) as url:
    all_log_json = json.loads(url.read().decode())

filename_regex = re.compile(r'fullLog_(\w+)_v_(\w+)_v_(\w+)_(\d+)\.txt')

log_dict = {}

cnt = 0
for entry in all_log_json:
    out = filename_regex.match(entry).groups()
    if len(out) != 4:
        print(entry, out)
    bots = out[:3]
    timestamp = int(out[3])
    log_dict[timestamp] = (bots,entry)
    if which_bots.issubset(bots):
        cnt += 1

print('totally {} logs, {} filtered out'.format(len(log_dict), cnt))

download = []

n_download = int(input('how many latest out of {}?\n'.format(cnt)))

cnt = 0
for timestamp in sorted(log_dict, reverse=True):
    (bots,entry) = log_dict[timestamp]
    if which_bots.issubset(bots):
        cnt += 1
        print('{}\t{}'.format(time.ctime(timestamp/1000), bots))
        download.append(entry)

    if cnt >= n_download:
        break

if not os.path.exists('logs'):
    os.mkdir('logs')

for entry in download:
    url = request.urlopen('http://auctions11.usydrobotics.club/api/fullLogs/{}'.format(entry))
    fp = open('logs/{}'.format(entry), 'wb')
    fp.write(url.read())
    fp.close()
    url.close()
