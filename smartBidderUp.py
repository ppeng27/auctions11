random = None
math = None
time = None


class CompetitorInstance():
    def __init__(self):
        # initialize personal variables
        pass

    def onGameStart(self, engine, gameParameters):
        # engine: an instance of the game engine with functions as outlined in the documentation.
        self.engine = engine
        # gameParameters: A dictionary containing a variety of game parameters
        self.gameParameters = gameParameters
        self.round = 0
        self.auction = 0
        self.mean = gameParameters["meanTrueValue"]
        self.minb = gameParameters["minimumBid"]
        self.numPlayers = gameParameters["numPlayers"]
        global random
        global math
        global time
        random = engine.random
        math = engine.math
        time = engine.time
        random.seed(time.time_ns() // 100000000000)
        self.magics = list(range(8, 24))
        random.shuffle(self.magics)
        self.magics_knows = list(range(8, 24))
        random.shuffle(self.magics_knows)
        # print(self.magics)
        # print(self.magics_knows)

    def onAuctionStart(self, index, trueValue):
        # index is the current player's index, that usually stays put from game to game
        # trueValue is -1 if this bot doesn't know the true value
        self.index = index
        self.knowsTrueValue = trueValue != -1
        self.trueValue = trueValue
        self.bidInfo = {}
        for index in range(self.numPlayers):
            self.bidInfo[index] = {}
        self.bidSeq = []

    def onBidMade(self, whoMadeBid, howMuch):
        # whoMadeBid is the index of the player that made the bid
        # howMuch is the amount that the bid was
        if whoMadeBid < self.index:
            self.bidInfo[whoMadeBid][self.round] = howMuch
            self.bidSeq.append((whoMadeBid, self.round, howMuch))
        else:
            self.bidInfo[whoMadeBid][self.round - 1] = howMuch
            self.bidSeq.append((whoMadeBid, self.round - 1, howMuch))
        return

    def onMyTurn(self, lastBid):
        # print(self.index, self.round)
        magic = self.magics[math.floor(lastBid) % len(self.magics)]
        magic_knows = self.magics_knows[math.floor(
            lastBid) % len(self.magics_knows)]
        pr = 32/50
        if lastBid > self.mean/4:
            pr = 16/100
        if lastBid > self.mean*3/4:
            pr = 2/50
        if not self.knowsTrueValue and random.random() < pr:
            self.engine.makeBid(lastBid + magic)
        if self.knowsTrueValue and lastBid + magic_knows <= self.trueValue - 50:
            self.engine.makeBid(lastBid + magic_knows)
        self.round += 1

    def onAuctionEnd(self):
        # Now is the time to report team members, or do any cleanup.
        # print(self.index, self.round)

        teammate_no = set()
        teammate_yes = set()

        teammate_knows_no = set()
        teammate_knows_yes = set()

        non_npc = set()

        lastBid = 1
        for (who, round, bid) in self.bidSeq:
            expect_magic = self.magics[math.floor(
                lastBid) % len(self.magics)]
            expect_magic_knows = self.magics_knows[math.floor(
                lastBid) % len(self.magics_knows)]
            actual_magic = bid - lastBid
            if actual_magic == expect_magic:
                teammate_yes.add(who)
            else:
                teammate_no.add(who)
            if actual_magic == expect_magic_knows:
                teammate_knows_yes.add(who)
            else:
                teammate_knows_no.add(who)
            if not (8 <= actual_magic <= 23):
                non_npc.add(who)
            lastBid = bid

        teammate = list(teammate_yes - teammate_no)
        teammate_knows = list(teammate_knows_yes - teammate_knows_no)
        non_npc = list(non_npc)

        if len(teammate_knows) > 1:
            print("too much teammate_knows")
            print(teammate_knows_yes)
            print(teammate_knows_no)
            teammate_knows = []
        if len(teammate) > 3:
            print("too much teammate")
            print(teammate_yes)
            print(teammate_no)
            teammate = []
        if len(non_npc) > 6:
            print("too much non_npc")
            print(non_npc)
            non_npc = []

        self.engine.reportTeams(
            teammate + teammate_knows, non_npc, teammate_knows)
        self.auction += 1
        return
