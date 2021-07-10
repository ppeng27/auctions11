import random
import math
import time

# random, math, time = None, None, None


class CompetitorInstance():
    def __init__(self):
        self.bot_name = 'i_know_it'
        self.engine = None
        self.game_parameters = None

        self.info = {
            'index': None,
            'know_true': None,
            'true_value': None,
            'bid_info': None,
            'bid_seq': []
        }

        # encoding variables
        self.magic_encodings = None
        self.magic_know_encodings = None

    def onGameStart(self, engine, game_parameters):
        '''
        1) engine: an instance of the game engine with functions as outlined in the documentation.
        2) game_parameters: A dictionary containing a variety of game parameters
        '''

        self.engine = engine
        self.game_parameters = game_parameters
        self.auction_round = 0
        self.info['bid_info'] = {i: {} for i in range(self.game_parameters['auctionsCount'])}

        # define modules
        # global random
        # global math
        # global time

        # random, math, time = (engine.random, engine.math, engine.time)

        # define our encoding protocol
        random.seed('{}:{}'.format(self.bot_name, time.time_ns() // 100000000000))  # define a pseudo-random encryption key based on time
        self.magic_encodings = list(range(8, 24))
        self.magic_know_encodings = list(range(8, 24))
        random.shuffle(self.magic_encodings)
        random.shuffle(self.magic_know_encodings)

    def onAuctionStart(self, index, true_value):
        '''
        1) index is the current player's index, that usually stays put from game to game
        2) trueValue is -1 if this bot doesn't know the true value
        '''

        # intialise bot and competitor information
        self.info['index'] = index
        self.info['know_true'] = true_value != - 1
        self.info['true_value'] = true_value
        self.info['bid_seq'] = []

    def onBidMade(self, who_made_bid, how_much):
        '''
        1) whoMadeBid is the index of the player that made the bid
        2) howMuch is the amount that the bid was
        '''

        data = (who_made_bid, how_much)

        self.info['bid_seq'].append(data)

    def onMyTurn(self, last_bid):
        '''
        1) last_bid is the last bid that was made
        '''

        # prepare bid with encodings and probability of bidding
        magic_encodings = self.magic_encodings[math.floor(last_bid) % len(self.magic_encodings)]
        magic_know_encodings = self.magic_know_encodings[math.floor(last_bid) % len(self.magic_know_encodings)]

        pr = 4/25 if last_bid > self.game_parameters['meanTrueValue']/4 else\
             2/50 if last_bid > self.game_parameters['meanTrueValue'] * 3/4 else\
             32/50

        # make bid
        if not self.info['know_true'] and random.random() < pr:
            self.engine.makeBid(last_bid + magic_encodings)
        if self.info['know_true'] and last_bid + magic_know_encodings <= self.info['true_value'] - 50:
            self.engine.makeBid(last_bid + magic_know_encodings)

    def onAuctionEnd(self):
        '''
        1) Now is the time to report team members, or do any cleanup.
        '''

        team, not_team = set(), set()
        team_knows, not_team_knows = set(), set()
        non_npc = set()

        last_bid = 1
        for bot, bid in self.info['bid_seq']:
            # prepare checks for encodings
            expected_magic = self.magic_encodings[math.floor(last_bid) % len(self.magic_encodings)]
            expected_magic_know = self.magic_know_encodings[math.floor(last_bid) % len(self.magic_know_encodings)]
            check = bid - last_bid

            # check magic
            if expected_magic == check:
                team.add(bot)
            else:
                not_team.add(bot)

            if expected_magic_know == check:
                team_knows.add(bot)
            else:
                not_team_knows.add(bot)

            if not (8 <= check <= 23):
                non_npc.add(bot)

            # add data
            if bot not in self.info['bid_info'][self.auction_round]:
                self.info['bid_info'][self.auction_round][bot] = [check]
            else:
                self.info['bid_info'][self.auction_round][bot].append(check)

            last_bid = bid

        # format and send report
        team_knows = list(team_knows - not_team_knows)
        team = list(team - not_team) + team_knows
        non_npc = list(non_npc)

        self.engine.reportTeams(team, [], team_knows)

        self.auction_round += 1
