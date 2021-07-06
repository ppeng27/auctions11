import random
import math
import time

import threading
import ctypes
import importlib

availableImports = ["random","math"]

log_file_cap=1000*1000 # 1kb max log file size
functionExecutionTime = 0.05

normalX = list(map(lambda x: x/50-1, range(0,100)))
normalY = list(map(lambda x: (math.e **(-x**2/2))/math.sqrt(2*math.pi), normalX))
_sum=0
normalY2=[]
for y in normalY:
    normalY2.append(_sum)
    _sum+=y
normalY2 = list(map(lambda x: x/_sum, normalY2))
def linterp(x,y,x1):
    for i,xn in enumerate(x):
        if x1<xn:
            if (i==0):
                return y[0]
            else:
                return y[i-1] + (y[i]-y[i-1]) * (x1-x[i-1]) / (xn - x[i-1])
    return y[len(y)-1]
class InterruptableThread(threading.Thread):
    def __init__(self, func, *args, **kwargs):
        threading.Thread.__init__(self)
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._result = None
        self.daemon=True

    def run(self):
        self._result = self._func(*self._args, **self._kwargs)

    @property
    def result(self):
        return self._result


def kill_thread(thread):
    """
    thread: a threading.Thread object
    """
    thread_id = thread.ident
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
        thread_id, ctypes.py_object(SystemExit))
    if res > 1:
        ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
        print('Exception raise failure')

class GameEngine():
    def __init__(self, logs="all"):
        if logs == "all":
            logs = "engine|competitors|errors"
        self.loggingLevel = logs
        self.auctionNumber = 0
        self.currentTurn = 0
        self.currentBid = 0
        self.currentBidPlayer = 0
        self.resettingBidPlayer = 0
        self.trueValue = 0
        self._print = print
        meanTrueValue=random.randint(2000,20000)
        stdDevValue = int(meanTrueValue*(0.1+random.random()*0.3))
        self.gameParameters = {
            "knowledgePenalty": 50,
            "minimumBid": 8,
            "meanTrueValue": meanTrueValue,
            "stddevTrueValue": stdDevValue,
            "numPlayers": 0,
            "knownTrueValueProbability": 0.75,
            "penaltyMax": meanTrueValue+stdDevValue*3,
            "auctionsCount":5
        }
        self.competitors = []
        self.teams = {}
        self.allPassed = True
        self.internalPrint=self._internalPrint
        # libraries
        self.currentPrintingPlayer=""
        for toImport in availableImports:
            self.__dict__[toImport]=importlib.import_module(toImport)
        pass

    def callWithTimeout(self,team, fn, t, *args, **kwargs):
        self.currentPrintingPlayer=team
        def tryfn(*args, **kwargs):
            try:
                fn(*args, **kwargs)
            except Exception as e:
                self.internalPrint("error",team,f"Team {team}'s execution raised an error:{type(e)} {e}")
        it = InterruptableThread(tryfn, *args, **kwargs)
        it.start()
        it.join(t)
        if not it.is_alive():
            return it.result
        kill_thread(it)
        self.internalPrint("error",team,f"Team {team}'s execution timed out (>{t}s)")

    def registerBot(self, bot, team=None):
        self.competitors.append({
            "instance": bot,
            "team": team,
            "knowsTrue": False
        })
        if team is not None:
            if team not in self.teams:
                self.teams[team] = {
                    "score": 0,
                    "playersInTeam": 1,
                    "logcharcount":0,
                    "overlogging":False
                }
            else:
                self.teams[team]["playersInTeam"] += 1

    def runGame(self):
        random.shuffle(self.competitors)
        self.internalPrint("minlog","!ml",f"{','.join([c['team'] for c in self.competitors])}/")
        self.gameParameters["numPlayers"]=len(self.competitors)
        for c in self.competitors:
            self.callWithTimeout(c["team"],
                c["instance"].onGameStart, functionExecutionTime, self, self.gameParameters)
        for self.auctionNumber in range(self.gameParameters["auctionsCount"]):
            # Reset the game
            self.currentBid = 1
            self.currentTurn = 0
            self.resettingBidPlayer = random.randint(
                0, len(self.competitors)-1)
            self.currentBidPlayer = (
                self.resettingBidPlayer+1) % len(self.competitors)
            self.lastBidPlayer = self.resettingBidPlayer
            self.nPassed = 0
            self.trueValue = int ( linterp(normalY2, normalX, random.random())* self.gameParameters["stddevTrueValue"] + self.gameParameters["meanTrueValue"])
            self.internalPrint("minlog","!ml",f"t:{self.trueValue}|")
            # decide who gets true value
            teamsWhoGetTrueValue = {}  # key = teamno, val = whoInTeamGetsIt
            for t in self.teams:
                if random.randint(0, 100) > (1-self.gameParameters["knownTrueValueProbability"])*100:
                    teamsWhoGetTrueValue[t] = random.randint(
                        0, self.teams[t]["playersInTeam"]-1)
                self.teams[t]["report"]={}
            for i, c in enumerate(self.competitors):
                initialised = False
                if c["team"] in teamsWhoGetTrueValue:
                    if teamsWhoGetTrueValue[c["team"]] == 0:
                        self.callWithTimeout(c["team"],c["instance"].onAuctionStart,functionExecutionTime,i, self.trueValue)
                        c["knowsTrue"] = True
                        initialised = True
                        self.internalPrint("minlog","!ml",f"k:{i}|")
                    teamsWhoGetTrueValue[c["team"]] -= 1
                if not initialised:
                    self.callWithTimeout(c["team"],c["instance"].onAuctionStart,functionExecutionTime, i,-1)
                    c["knowsTrue"] = False
            self.internalPrint("engine","engine",f"Starting Auction {self.auctionNumber}")
            self.internalPrint("minlog","!ml",f"{self.currentBidPlayer}:{self.currentBid}|")
            # Main loop
            while self.nPassed < len(self.competitors) and self.currentBid<self.gameParameters["penaltyMax"]:
                self.callWithTimeout(self.competitors[self.currentBidPlayer]["team"],
                    self.competitors[self.currentBidPlayer]["instance"].onMyTurn,
                    functionExecutionTime,
                    self.currentBid
                )
                self.currentBidPlayer = self.currentBidPlayer + 1
                self.currentBidPlayer = self.currentBidPlayer % len(
                    self.competitors)
                self.nPassed += 1
                self.currentTurn += 1

            # Finishing the round
            self.nPassed=-1
            teamindex = self.competitors[self.lastBidPlayer]["team"]
            self.internalPrint("engine","engine","Auction {}: Team {} copped it at a price of {}; true value was {}".format(
                self.auctionNumber, teamindex if teamindex is not None else "[NPC Random]", self.currentBid, self.trueValue))
            if teamindex is not None:
                self.teams[teamindex]["score"] = self.teams[teamindex]["score"] + \
                    self.trueValue - self.currentBid - \
                    (self.gameParameters["knowledgePenalty"]
                     if self.competitors[self.currentBidPlayer]["knowsTrue"] else 0)
            for t in self.teams:
                self.teams[t]["protoReportScore"]=0
            for i,c in enumerate(self.competitors):
                self.currentBidPlayer = i
                self.callWithTimeout(c["team"],c["instance"].onAuctionEnd,functionExecutionTime)
            for t in self.teams:
                self.teams[t]["score"] += self.teams[t]["protoReportScore"]
            self.internalPrint("minlog","!ml",f"/")
        self.internalPrint("engine","engine","Final scores:")
        for i in self.teams:
            self.internalPrint("engine","engine","Team {}: {}".format(i, self.teams[i]["score"]))
        return self.teams

    def makeBid(self, amount):
        valid=True
        reason = ""
        try:
            amount = int(amount)
        except Exception:
            reason="(Not an int)"
            valid = False
        if valid and  amount < self.currentBid+self.gameParameters["minimumBid"]:
            reason="(Not enough)"
            valid=False
        if not valid:
            self.internalPrint("error",self.currentPrintingPlayer,f"Bad bid! Cannot bid {amount} {reason}")
        else:
            self.currentBid = amount
            self.lastBidPlayer = self.currentBidPlayer
            self.nPassed = 0
            self.internalPrint("engine","engine",f"competitor {self.currentBidPlayer} made a bid of {self.currentBid}")
            self.internalPrint("minlog","!ml",f"{self.currentBidPlayer}:{self.currentBid}|")
            # save the currentPrintingPlayer so that log owners still make sense
            savedPlayer = self.currentPrintingPlayer
            for c in self.competitors:
                self.callWithTimeout(c["team"],c["instance"].onBidMade,functionExecutionTime,self.currentBidPlayer,self.currentBid)
            self.currentPrintingPlayer=savedPlayer

    def reportTeams(self, reportOwnTeam, reportNNPC, reportKnown):
        # check we are in the right state
        if (self.nPassed!=-1):
            self.internalPrint("error",self.currentPrintingPlayer,f"Bad report! Still in auction.")
            return

        self.internalPrint("minlog","!ml",f"r:{self.currentBidPlayer}")
        protoReportScore = 0
        reportingDone = False
        # check reportOwnTeam
        if type(reportOwnTeam) != list:
            self.internalPrint("error",self.currentPrintingPlayer,f"Bad report! Own team list was not a <class list>.")
        elif len(reportOwnTeam)>20:
            self.internalPrint("error",self.currentPrintingPlayer,f"Bad report! Own team list was too long.")
        else:
            reportOwnTeamDict={}
            try:
                for tm in reportOwnTeam:
                    tm = int(tm)
                    if tm<0:
                        raise ValueError
                    reportOwnTeamDict[tm]=True
                for tm in reportOwnTeamDict:
                    if self.competitors[int(tm)]["team"]==self.currentPrintingPlayer and int(tm) !=self.currentBidPlayer: 
                        protoReportScore+=100/(self.teams[self.currentPrintingPlayer]['playersInTeam']-1)
                        reportingDone = True
                    else:
                        if self.teams[self.currentPrintingPlayer]['playersInTeam']==1:
                            protoReportScore-=100
                        else:
                            protoReportScore-=100/(self.teams[self.currentPrintingPlayer]['playersInTeam']-1)
                        reportingDone = True
                self.internalPrint("minlog","!ml",f":o:{','.join(map(lambda i: str(i), reportOwnTeam))}")
            except ValueError:
                self.internalPrint("error",self.currentPrintingPlayer,f"Bad report of ownTeam! Reported bot {tm} was not a positive integer.")
        # check reportNPC
        if type(reportNNPC) != list:
            self.internalPrint("error",self.currentPrintingPlayer,f"Bad report! competitor list was not a <class list>.")
        elif len(reportNNPC)>20:
            self.internalPrint("error",self.currentPrintingPlayer,f"Bad report! competitor list was too long.")
        else:
            reportNNPCDict={}
            try: 
                for tm in reportNNPC:
                    tm = int(tm)
                    if tm<0:
                        raise ValueError
                    reportNNPCDict[tm]=True
                for tm in reportNNPCDict:
                    if self.competitors[int(tm)]["team"]!=None:
                        if (self.competitors[int(tm)]["team"]!=self.currentPrintingPlayer):
                            protoReportScore+=15
                            reportingDone = True
                    else:
                        protoReportScore-=90
                        reportingDone = True
                self.internalPrint("minlog","!ml",f":n:{','.join(','.join(map(lambda i: str(i), reportNNPC)))}")
            except ValueError:
                self.internalPrint("error",self.currentPrintingPlayer,f"Bad report of NPC bots! Reported bot {tm} was not a positive integer.")
        # check reportKnown
        if type(reportKnown) != list:
            self.internalPrint("error",self.currentPrintingPlayer,f"Bad report! Known true list was not a <class list>.")
        elif len(reportKnown)>20:
            self.internalPrint("error",self.currentPrintingPlayer,f"Bad report! Known true list was too long.")
        else:
            try:
                reportKnownDict={}
                for tm in reportKnown:
                    tm = int(tm)
                    if tm<0:
                        raise ValueError
                    reportKnownDict[tm]=True
                for tm in reportKnownDict:
                    if self.competitors[int(tm)]["knowsTrue"] and int(tm) !=self.currentBidPlayer:
                        protoReportScore+=100
                        reportingDone=True
                    else:
                        protoReportScore-=50
                        reportingDone=True
                self.internalPrint("minlog","!ml",f":k:{','.join(map(lambda i: str(i), reportKnown))}")
            except ValueError:
                self.internalPrint("error",self.currentPrintingPlayer,f"Bad report of known value bots! Reported bot {tm} was not a positive integer.")
        self.internalPrint("minlog","!ml",f"|")
        if reportingDone and self.teams[self.currentPrintingPlayer]["protoReportScore"]<protoReportScore:
            self.teams[self.currentPrintingPlayer]["protoReportScore"]=protoReportScore

    def _internalPrint(self,loggingLevel,source,msg):
        if loggingLevel in self.loggingLevel:
            formattedMessage = self.formatMessage(source,msg)
            self._print (formattedMessage+"\n")

    def formatMessage(self,source,msg):
        return f"{self.auctionNumber}:{self.currentTurn}::{source}::{msg}"

    def print(self, msg):
        self.teams[self.currentPrintingPlayer]["logcharcount"]+=len(msg)
        if (self.teams[self.currentPrintingPlayer]["logcharcount"]<log_file_cap):
            self.internalPrint('competitors',self.currentPrintingPlayer,msg)
        elif not self.teams[self.currentPrintingPlayer]["overlogging"]:
            self.teams[self.currentPrintingPlayer]["overlogging"]=True
            self.internalPrint('error',self.currentPrintingPlayer,"Log buffer exceeded")

class NPCRandomBot():
    def __init__(self):
        pass

    def onGameStart(self, engine, gameParameters):
        self.mean = gameParameters["meanTrueValue"]
        self.minp = gameParameters["minimumBid"]
        self.engine = engine

    def onAuctionStart(self, index, trueValue):
        pass

    def onBidMade(self, whoMadeBid, howMuch):
        pass

    def onMyTurn(self, lastBid):
        pr=32/50
        if lastBid>self.mean/4:
            pr=16/100
        if lastBid>self.mean*3/4:
            pr=2/50
        if random.random() < pr:
            self.engine.makeBid(math.floor(
                lastBid+(self.minp*(1+2*random.random()))))

    def onAuctionEnd(self):
        pass
