class CompetitorInstance():
    def __init__(self):
        pass
    
    def onGameStart(self, engine, gameParameters):
        self.engine=engine
        self.gameParameters = gameParameters
    
    def onAuctionStart(self, index, trueValue):
        pass

    def onBidMade(self, whoMadeBid, howMuch):
        pass

    def onMyTurn(self,lastBid):
        if (lastBid<self.gameParameters["meanTrueValue"]):
            self.engine.makeBid(lastBid+11)
        pass

    def onAuctionEnd(self):
        pass