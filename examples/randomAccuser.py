# import random
random = None
math = None


class CompetitorInstance():
    def __init__(self):
        pass

    def onGameStart(self, engine, gameParameters):
        self.engine = engine
        self.gameParameters = gameParameters
        global random
        random = engine.random
        global math
        math = engine.math

    def onAuctionStart(self, index, trueValue):
        pass

    def onBidMade(self, whoMadeBid, howMuch):
        pass

    def onMyTurn(self, lastBid):
        if random.randint(0, 100) < 20:
            self.engine.makeBid(lastBid+1)
        pass

    def onAuctionEnd(self):
        playerList = list(range(0, self.gameParameters["numPlayers"]))
        reportOwnTeam = random.sample(playerList, 5)
        self.engine.reportTeams(reportOwnTeam, [], [])
        pass
