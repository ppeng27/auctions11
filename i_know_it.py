# import random
# import math
# import time

random = None
math = None
time = None


class CompetitorInstance():
    def __init__(self):
        # initialize personal variables
        self.bot_name = 'i_know_it'

    def onGameStart(self, engine, game_parameters):
        # engine: an instance of the game engine with functions as outlined in the documentation.
        self.engine = engine
        # gameParameters: A dictionary containing a variety of game parameters
        self.gameParameters = game_parameters
        self.round = 0
        self.auction = 0
        self.mean = game_parameters["meanTrueValue"]
        self.stddev = game_parameters["stddevTrueValue"]
        self.minb = game_parameters["minimumBid"]
        self.num_players = game_parameters["numPlayers"]
        global random
        global math
        global time
        random = engine.random
        math = engine.math
        time = engine.time
        random.seed('{}:{}'.format(self.bot_name,
                                   time.time_ns() // 100000000000))
        self.magics = list(range(8, 24))
        random.shuffle(self.magics)
        self.magics_knows = list(range(8, 24))
        random.shuffle(self.magics_knows)

        self.enemy = set()

    def onAuctionStart(self, index, true_value):
        # index is the current player's index, that usually stays put from game to game
        # trueValue is -1 if this bot doesn't know the true value
        self.index = index
        self.knows_true_value = true_value != -1
        self.true_value = true_value
        self.recv_true_value = False
        self.bid_info = {}
        for index in range(self.num_players):
            self.bid_info[index] = {}
        self.bid_seq = []
        self.last_bid = 1

        self.teammate_dknows = set()
        self.teammate_dknows_yes = dict()
        self.teammate_dknows_no = set()
        self.teammate_knows = set()
        self.teammate_knows_yes = dict()
        self.teammate_knows_no = set()
        self.teammate_all = set()
        # self.enemy = set()

        self.has_identified_teammates = False
        self.broadcast = False
        self.team_hold_it = False
        self.no_one_knows = False

    def onBidMade(self, who_made_bid, how_much):
        # whoMadeBid is the index of the player that made the bid
        # howMuch is the amount that the bid was

        actual_magic = how_much - self.last_bid

        if self.broadcast and not self.knows_true_value:
            if who_made_bid in self.teammate_knows:
                index = self.magics_knows.index(actual_magic)
                if index == 15:
                    self.recv_true_value = True
                    self.broadcast = False
                    self.true_value = math.ceil(self.broadcast_value)
                    self.engine.print('recv value {}'.format(self.true_value))
                elif index == 14:
                    self.recv_true_value = True
                    self.broadcast = False
                    self.true_value = math.floor(self.broadcast_value)
                    self.engine.print('recv value {}'.format(self.true_value))
                else:
                    if self.broadcast_value == self.mean:
                        z = index / 7 - 1
                    else:
                        z = index / 14
                    self.broadcast_value = z * self.broadcast_stddev + self.broadcast_value
                    self.broadcast_stddev = self.broadcast_stddev / 5
                    self.engine.print('recv value z({}) i({}) v({}) stddev({}) by ({})'.format(
                        z, index, self.broadcast_value, self.broadcast_stddev, self.index))

        expect_magic = self.magics[math.floor(
            self.last_bid) % len(self.magics)]
        expect_magic_knows = self.magics_knows[math.floor(
            self.last_bid) % len(self.magics_knows)]

        if not self.has_identified_teammates:
            if actual_magic == expect_magic:
                if who_made_bid not in self.teammate_dknows_yes:
                    self.teammate_dknows_yes[who_made_bid] = 1
                else:
                    self.teammate_dknows_yes[who_made_bid] += 1
            else:
                self.teammate_dknows_no.add(who_made_bid)

            if actual_magic == expect_magic_knows:
                if who_made_bid not in self.teammate_knows_yes:
                    self.teammate_knows_yes[who_made_bid] = 1
                else:
                    self.teammate_knows_yes[who_made_bid] += 1
            else:
                self.teammate_knows_no.add(who_made_bid)

            self.teammate_knows = self.teammate_knows_yes.keys() - self.teammate_knows_no
            self.teammate_dknows = self.teammate_dknows_yes.keys() - self.teammate_dknows_no
            self.teammate_all = self.teammate_knows.union(self.teammate_dknows)

            if 2 <= len(self.teammate_all) <= 3 and len(self.teammate_knows) <= 1:
                self.has_identified_teammates = True
                for know in self.teammate_knows:
                    if self.teammate_knows_yes[know] < 3:
                        self.has_identified_teammates = False
                for dknow in self.teammate_dknows:
                    if self.teammate_dknows_yes[dknow] < 3:
                        self.has_identified_teammates = False

            if self.has_identified_teammates and not self.broadcast:
                if len(self.teammate_knows) == 1:
                    self.engine.print("broadcast!")
                    self.broadcast = True
                    self.broadcast_value = self.mean
                    self.broadcast_stddev = self.stddev
                else:
                    # no one knows true value
                    self.no_one_knows = True

        if self.has_identified_teammates:
            if who_made_bid in self.teammate_all:
                self.team_hold_it = True
            else:
                self.team_hold_it = False

        if not (8 <= actual_magic <= 23):
            self.enemy.add(who_made_bid)

        if who_made_bid < self.index:
            self.bid_info[who_made_bid][self.round] = how_much
            self.bid_seq.append((who_made_bid, self.round, how_much))
        else:
            self.bid_info[who_made_bid][self.round - 1] = how_much
            self.bid_seq.append((who_made_bid, self.round - 1, how_much))

        self.last_bid = how_much
        return

    def onMyTurn(self, last_bid):
        # print(self.index, self.round)
        self.round += 1

        magic = self.magics[math.floor(last_bid) % len(self.magics)]
        magic_knows = self.magics_knows[math.floor(
            last_bid) % len(self.magics_knows)]
        magic_random = random.randint(8, 23)

        pr = 32/50
        if last_bid > self.mean/4:
            pr = 16/100
        if last_bid > self.mean*3/4:
            pr = 2/50

        if self.no_one_knows:
            if random.random() < pr and last_bid + magic_random <= self.mean:
                self.engine.makeBid(last_bid + magic_random)
            return

        if self.broadcast and self.knows_true_value:
            if abs(self.broadcast_value - self.true_value) < 1:
                if self.true_value > self.broadcast_value:
                    self.engine.makeBid(last_bid + self.magics_knows[15])
                else:
                    self.engine.makeBid(last_bid + self.magics_knows[14])
                self.engine.print('send value {}'.format(self.true_value))
                self.broadcast = False
                return
            z = (self.true_value - self.broadcast_value) / \
                self.broadcast_stddev
            if self.broadcast_value == self.mean:
                index = math.floor((z + 1) * 7)
                self.broadcast_value = (index / 7 - 1) * \
                    self.broadcast_stddev + self.broadcast_value
            else:
                index = math.floor(z * 14)
                self.broadcast_value = (index / 14) * \
                    self.broadcast_stddev + self.broadcast_value
            self.broadcast_stddev /= 5
            if 0 <= index < 14:
                self.engine.makeBid(last_bid + self.magics_knows[index])
                self.engine.print('send value z({}) i({}) v({}) stddev({}) from ({})'.format(
                    z, index, self.broadcast_value, self.broadcast_stddev, self.index))
            elif index < 0:
                self.engine.makeBid(last_bid + self.magics_knows[14])
                self.engine.print('send value {}'.format(self.true_value))
                self.broadcast = False
            else:
                self.engine.makeBid(last_bid + self.magics_knows[15])
                self.engine.print('send value {}'.format(self.true_value))
                self.broadcast = False
            return

        # don't know true value
        if not self.knows_true_value:
            # hasn't identified roles
            if not self.has_identified_teammates:
                # random and small enough
                if random.random() < pr and last_bid + magic <= self.mean:
                    self.engine.makeBid(last_bid + magic)
            # already identify all roles (and someone knows true value)
            # random hit or no teammate holds it
            elif random.random() < pr or not self.team_hold_it:
                # haven't receive broadcasted true value yet
                if not self.recv_true_value:
                    # not too expensive
                    if last_bid + magic_random <= self.mean:
                        self.engine.makeBid(last_bid + magic_random)
                # end game strategy
                elif self.true_value - 30 <= last_bid <= self.true_value - 8:
                    if last_bid <= self.true_value - 15:
                        self.engine.makeBid(self.true_value - 7)
                    else:
                        self.engine.makeBid(last_bid + 8)
                # received broadcasted true value
                # and not too expensive
                elif last_bid + magic_random <= self.true_value:
                    self.engine.makeBid(last_bid + magic_random)
            return

        # randomise magic
        if self.has_identified_teammates:
            magic_knows = magic_random

        # know true value
        if self.knows_true_value:
            # no teammate holds it or random hit
            # and price not very high
            if (random.random() < pr or not self.team_hold_it) and last_bid + magic_knows <= self.true_value - 50:
                self.engine.makeBid(last_bid + magic_knows)

    def onAuctionEnd(self):
        # Now is the time to report team members, or do any cleanup.
        # print(self.index, self.round)

        teammate = list(self.teammate_knows) + list(self.teammate_dknows)
        teammate_knows = list(self.teammate_knows)
        non_npc = list(self.enemy)

        self.engine.print("knows: {}".format(teammate_knows))
        self.engine.print("teammates: {}".format(teammate))
        self.engine.print("non_npc: {}".format(non_npc))

        if len(teammate_knows) > 1:
            teammate_knows = []
        if len(teammate) > 3:
            teammate = []
        if len(non_npc) > 6:
            non_npc = []

        self.engine.reportTeams(
            teammate,
            non_npc,
            teammate_knows
        )
        self.auction += 1
        return
