from math import sqrt
import os
import concurrent.futures
import matplotlib.pyplot as plt
import numpy as np
import time


class Analyser:
    def __init__(self):
        self.phase1 = []
        self.phase2 = []
        self.phase3 = []

        self.x_coors = []
        self.y_coors = []

    def mean(self, data):
        return float(sum(data) / len(data))

    def variance(self, data):
        mu = self.mean(data)
        return self.mean([(x - mu) ** 2 for x in data])

    def std(self, data):
        return sqrt(self.variance(data))

    def skew(self, data):
        mu = self.mean(data)
        std = self.std(data)
        n = len(data)

        return (sqrt(n*(n-1))/(n-2)) * (sum(map(lambda x: (x - mu)**3 / n, data)) / (std**3))

    def process(self, f):
        names = None
        npcs = None
        true_mu = None

        for line in f:
            data = line.strip()

            if 'True mu' in data:
                true_mu = int(data.split(':')[-1])
            elif len(data.split(',')) == 10:
                names = data.split(',')
                npcs = [i for i, bot in enumerate(names) if bot == 'NPC']
            else:
                bids = data.split(',')[1:]

                bidder = []
                npc_prevs = [None for _ in range(len(npcs))]
                for i, bid in enumerate(bids):
                    if len(bidder) != (len(set(bidder))):
                        npc_prevs = [int(bids[i - 1].split(':')[-1]) if prev == None else prev for prev in npc_prevs]
                        npc_bids = [1 if npc in set(bidder) else 0 for npc in npcs]

                        for j, prev in enumerate(npc_prevs):
                            if prev > true_mu * 3/4:
                                analyser.phase3.append(npc_bids[j])
                            elif prev > true_mu/4:
                                analyser.phase2.append(npc_bids[j])
                            else:
                                analyser.phase1.append(npc_bids[j])

                        bidder = [bidder[-1]]

                    bot, amt = list(map(lambda x: int(x), bid.split(':')))

                    if bot in npcs:
                        npc_prevs[npcs.index(bot)] = int(bids[i - 1].split(':')[-1])

                    bidder.append(bot)

    def calculate(self):
        self.x_coors = [1, 2, 3]
        self.freqs = [
            self.phase1.count(1)/len(self.phase1),
            self.phase2.count(1)/len(self.phase2),
            self.phase3.count(1)/len(self.phase3)
        ]
        self.skews = [
            self.skew(self.phase1),
            self.skew(self.phase2),
            self.skew(self.phase3)
        ]

    def show(self):
        self.calculate()
        m1, b1 = np.polyfit(np.array(self.x_coors), np.array(self.freqs), 1)
        m2, b2 = np.polyfit(np.array(self.x_coors), np.array(self.skews), 1)

        plt.xticks(np.arange(min(self.x_coors), max(self.x_coors)+1, 1.0))

        plt.scatter(1, self.freqs[0], alpha=0.5, label='Phase 1 | {:.2f}%'.format(self.freqs[0] * 100))
        plt.scatter(2, self.freqs[1], alpha=0.5, label='Phase 2 | {:.2f}%'.format(self.freqs[1] * 100))
        plt.scatter(3, self.freqs[2], alpha=0.5, label='Phase 3 | {:.2f}%'.format(self.freqs[2] * 100))

        plt.scatter(1, self.skews[0], alpha=0.5, label='Phase 1 Skew | {}'.format(self.skews[0]))
        plt.scatter(2, self.skews[1], alpha=0.5, label='Phase 2 Skew | {}'.format(self.skews[1]))
        plt.scatter(3, self.skews[2], alpha=0.5, label='Phase 3 Skew | {}'.format(self.skews[2]))

        plt.plot(np.array(self.x_coors), m1 * np.array(self.x_coors) + b1, alpha=0.5, label='Frequencies')
        plt.plot(np.array(self.x_coors), m2 * np.array(self.x_coors) + b2, alpha=0.5, label='Skews')

        plt.title('NPC Bidding Behaviour per Phase')
        plt.xlabel('Phases')
        plt.ylabel('% Density (Freq) | Skewness')
        plt.legend(loc='upper left')
        plt.show()


# MAIN
START = time.time()

analyser = Analyser()
with concurrent.futures.ThreadPoolExecutor() as executor:
    for filename in os.listdir(os.path.abspath('logs')):
        with open(os.path.abspath('logs') + '/' + filename, 'r') as f:
            executor.submit(analyser.process(f))

END = time.time()

print('Analysed {} logs.\n'.format(len(os.listdir(os.path.abspath('logs')))))
print('Runtime: {:.2f}/s'.format(END - START))

analyser.show()
