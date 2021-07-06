class CompetitorInstance():
    def __init__(self):
        # initialize personal variables
        pass
    
    def onGameStart(self, engine, gameParameters):
        # engine: an instance of the game engine with functions as outlined in the documentation.
        self.engine=engine
        # gameParameters: A dictionary containing a variety of game parameters
        self.gameParameters = gameParameters
    
    def onAuctionStart(self, index, trueValue):
        # index is the current player's index, that usually stays put from game to game
        # trueValue is -1 if this bot doesn't know the true value 
        pass

    def onBidMade(self, whoMadeBid, howMuch):
        # whoMadeBid is the index of the player that made the bid
        # howMuch is the amount that the bid was
        pass

    def onMyTurn(self,lastBid):
        # lastBid is the last bid that was made
        if (lastBid < self.gameParameters["meanTrueValue"]):
            # But don't bid too high!
            self.engine.makeBid(lastBid+11)
        pass

    def onAuctionEnd(self):
        # Now is the time to report team members, or do any cleanup.
        pass