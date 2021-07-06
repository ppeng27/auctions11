# import random
random = None
math = None


class CompetitorInstance():
    def __init__(self):
        # initialize personal variables
        pass

    def onGameStart(self, engine, gameParameters):
        # engine: an instance of the game engine with functions as outlined in the documentation.
        self.engine = engine
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
            self.engine.makeBid(lastBid+11)
        pass

    def onAuctionEnd(self):
        # Now is the time to request a swap, if you want
        # engine.swapTo(12)
        pass
