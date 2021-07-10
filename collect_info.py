import requests
import urllib.request
import re
import concurrent.futures
import time


class API:
    def __init__(self):
        self.root = 'http://auctions11.usydrobotics.club/api/'

        self.competitors = set(['one',
            'relytz',
            'x_axis',
            'ohmypizza',
            'thelarpers',
            'christie',
            'smashbros',
            'yifan_c',
            'one',
            'kaito',
            'ogres_united'
        ])

        self.to_analyse = []

    def request(self, url, collect_logs=False):
        if not collect_logs:
            return requests.get(url).json()

        with urllib.request.urlopen(url) as f:
            return url.replace(self.root + 'fullLogs/', ''), f.read().decode('utf-8')

    def collect_names(self):
        url = self.root + 'fullLogs/stat'
        data = requests.get(url).json()

        for log_name in data:
            competitors = set(re.sub(r'[0-9]', '', log_name).replace('fullLog_', '').replace('_v_', ' ').replace('_.txt', '').split())

            if len(competitors & self.competitors) > 0:
                self.to_analyse.append(self.root + 'fullLogs/' + log_name)

        self.to_analyse = list(set(self.to_analyse))  # ensure no duplicate logs

    def collect_logs(self):
        self.collect_names()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            print('Collecting data...\n')
            futures = [executor.submit(self.request, url, True) for url in self.to_analyse]
            data = [future.result() for future in concurrent.futures.as_completed(futures)]

            print('Sending data...\n')
            futures = [executor.submit(self.format_data, entry[0], entry[1]) for entry in data]

        print('Done!\n')

    def format_data(self, log_name, data):
        # parse important INITIAL bot data for auction 1
        data = data.split('|')
        names = data[0].split('//')[-1]
        true_mean = int(data[1])

        string = '{}\nTrue mu:{}'.format(names, true_mean)

        bids, added = [], False
        for i in range(3, len(data)):
            info = data[i].split(':')

            if not info[0].isdigit():
                if not added:
                    string += ','.join(bids) + '\n'
                    bids = []
                    added = True
                continue

            added = False
            bids.append(':'.join(info))

        with open('logs/{}'.format(log_name), 'w') as f:
            f.write(string.strip())


collector = API()

START = time.time()
collector.collect_logs()
END = time.time()

print('Runtime: {:.2f}/s'.format(END - START))
