# ==============================CS-199==================================
# FILE:			MyAI.py
#
# AUTHOR: 		Justin Chung
#
# DESCRIPTION:	This file contains the MyAI class. You will implement your
#				agent in this file. You will write the 'getAction' function,
#				the constructor, and any additional helper functions.
#
# NOTES: 		- MyAI inherits from the abstract AI class in AI.py.
#
#				- DO NOT MAKE CHANGES TO THIS FILE.
# ==============================CS-199==================================

from AI import AI
from Action import Action

from itertools import combinations
from collections import defaultdict
import random

class MyAI( AI ):

	def __resetAllVar(self) -> None:
		MyAI.Q = set()
		
		MyAI.Safe = set()
		MyAI.Bomb = set()
		
		MyAI.Revisit = set()
		MyAI.FlagQ = set()
		
		MyAI.sentToUncover = (0,0,0)
		
		MyAI.READY_TO_LEAVE = False
		MyAI.UNFLAGGING = False
		
		MyAI.DEBUG = False
	
	def __turnOnDebug(self):
		MyAI.DEBUG = True
	
	def __init__(self, rowDimension, colDimension, totalMines, startX, startY):
		self.__resetAllVar()
		
		self.rowDimension = rowDimension
		self.colDimension = colDimension
		self.totalMines = totalMines
		self.startX = startX+1
		self.startY = startY+1
		
		self.Anna = MyAI.__Anna(self.colDimension, self.rowDimension)
		self.Ramon = MyAI.__Ramon(self.colDimension, self.rowDimension, self.totalMines, [])
		
# 		self.__turnOnDebug()
# 		self.Anna.turnOnDebug()
# 		self.Ramon.turnOnDebug()

	def __printEverything(self) -> None:
		print(len(MyAI.Q), "Q is now: ")
		for i in MyAI.Q:
			print(i, end = " ")
		print("\n", len(MyAI.Revisit), "Revisit is now: ")
		for r in MyAI.Revisit:
			print(r, end = " ")
		print("\n", len(MyAI.Safe), "Safe is now: ")
		for s in MyAI.Safe:
			print(s, end = " ")
		print("\n", len(MyAI.Bomb), "Bomb is now: ")
		for b in MyAI.Bomb:
			print(b, end = " ")
		print("\n")
	
	def getAction(self, number: int) -> "Action Object":
		''' this is Pablo, the main Player, who only does stuff that is absolutely safe.
		he is able to do all actions, manipulate main Variables, and determine when
		to finish the game.
		When he runs out of safe things to do, he will ask Anna, who then analyzes
		the situation for him'''
		
		if MyAI.READY_TO_LEAVE:
			if MyAI.DEBUG:
				print('leaving game')
			self.__resetAllVar()
			return Action(AI.Action.LEAVE)
		
		if MyAI.UNFLAGGING:
			return self.__unflag()
		
		if len(MyAI.Safe) == 0:
			MyAI.Q.add((self.startX,self.startY))
			MyAI.sentToUncover = (self.startX,self.startY,-1)
		
		if number != -1:
			MyAI.sentToUncover = (MyAI.sentToUncover[0],MyAI.sentToUncover[1],number)
			MyAI.Safe.add((MyAI.sentToUncover[0],MyAI.sentToUncover[1]))
			
		X = MyAI.sentToUncover
		try:
			MyAI.Q.remove((MyAI.sentToUncover[0],MyAI.sentToUncover[1]))
		except KeyError:
			print('sent To Uncover is', (MyAI.sentToUncover[0],MyAI.sentToUncover[1]))
			print('Q is', MyAI.Q)
			raise
		
		self.__put(X)
		
		self.__revist()
		
		if (len(MyAI.Q) == 0) and (len(MyAI.Bomb) == self.totalMines) \
		and ((len(MyAI.Bomb) + len(MyAI.Safe)) == self.rowDimension*self.colDimension):
			MyAI.UNFLAGGING = True
			return self.__unflag()

		elif len(MyAI.Q) == 0 and len(MyAI.Revisit) != 0:
			if self.DEBUG: print("Asking Anna...")
			for r in MyAI.Revisit:
				if MyAI.DEBUG: print("\nAsking Anna about", r)
				self.Anna.askAnna(r)
				if self.Anna.hasAnIdea():
					if MyAI.DEBUG: print("\nAnna has an idea about", r)
					MyAI.Bomb = MyAI.Bomb | self.Anna.getBomb()
					MyAI.FlagQ = MyAI.FlagQ | self.Anna.getBomb()
					MyAI.Q = MyAI.Q | self.Anna.getSafe()
					MyAI.Safe = MyAI.Safe | self.Anna.getSafe()
				self.Ramon.updateScenarios(self.Anna.getScenarios())
			if len(MyAI.Q) == 0:
				self.__revist()

		elif len(MyAI.Q) == 0 and len(MyAI.Revisit) == 0:
			if MyAI.DEBUG: print("Q and Revisit are both empty state")
			if len(MyAI.Bomb) < self.totalMines and ((self.totalMines - len(MyAI.Bomb)) == self.__remainTiles()):
				if MyAI.DEBUG: print("remaining tiles are all mines")
				MyAI.Bomb = MyAI.Bomb | self.__remainTiles()
				MyAI.FlagQ = MyAI.Bomb
				MyAI.UNFLAGGING = True
				return self.__unflag()
			elif len(MyAI.Bomb) == self.totalMines:
				if MyAI.DEBUG: print("remaining tiles are all safe")
				MyAI.Q = MyAI.Q | self.__remainTiles()
			else:
				if MyAI.DEBUG: print("remaining tiles are unknown")
				MyAI.Q.add(self.__remainTiles().pop())
		
		if MyAI.DEBUG: self.__printEverything()
		
		try: 
			XY = next(iter(MyAI.Q))
		except StopIteration: 
			if MyAI.DEBUG: print("Q is empty!")
			MyAI.Q = MyAI.Q | self.Ramon.askRamon()
			XY = next(iter(MyAI.Q))
		
		self.Ramon.clearScenarios()
		MyAI.sentToUncover = (XY[0],XY[1],-1)
		if MyAI.DEBUG: print("this move is to uncover", MyAI.sentToUncover[0], MyAI.sentToUncover[1])
		return Action(AI.Action.UNCOVER, MyAI.sentToUncover[0]-1, MyAI.sentToUncover[1]-1)
	
	def __revist(self) -> None:
		while True:
			if not self.__iterRevisit():
				break
			
	def __remainTiles(self) -> set:
		totalSet = set()
		for i in range(1, self.colDimension+1):
			for j in range(1, self.rowDimension+1):
				totalSet.add((i,j))
		return totalSet - MyAI.Bomb - MyAI.Safe
		
	def __unflag(self) -> Action:
		''' removes a random element from FlagQ, and returns that unflag Action'''
		if len(MyAI.FlagQ) != 0:
			mineXY = MyAI.FlagQ.pop()
			if len(MyAI.FlagQ) == 0:
				MyAI.UNFLAGGING = False
				MyAI.READY_TO_LEAVE = True
			if MyAI.DEBUG:
				print('flagging', mineXY[0], mineXY[1])
			return Action(AI.Action.FLAG, mineXY[0]-1, mineXY[1]-1)
		
	def __iterRevisit(self) -> bool:
		''' iterate through revisit to remove any tiles that are good to uncover,
		returns false if none of those tiles are discovered'''
		iterable = False
		tempSet = set()
		for t in MyAI.Revisit:
			if MyAI.reveal(t, MyAI.Safe, MyAI.Bomb, self.colDimension, self.rowDimension)[1] != "revisit":
				if MyAI.DEBUG:
					print((t[0],t[1]),"can be removed from revisit")
				tempSet.add((t[0],t[1]))
				iterable = True
			self.__put(t)
		MyAI.Revisit = self.__updateRevisit(tempSet)
		return iterable
	
	def __updateRevisit(self, tempSet: set) -> set:
		''' gets a set that needs to be removed from revisit and returns a result set after removing'''
		return MyAI.Revisit - set([(r[0],r[1],r[2]) for r in MyAI.Revisit if (r[0],r[1]) in tempSet])

	def __put(self, tile: "list of 3 elements") -> None:
		'''according to the type, put the set in bombQ, uncoverQ, or the tile itself to revisit'''
		result = MyAI.reveal(tile, MyAI.Safe, MyAI.Bomb, self.colDimension, self.rowDimension)
		resultType = result[1]
		resultSet = result[0]
		if resultType == "bomb":
			MyAI.FlagQ = MyAI.FlagQ | resultSet
			MyAI.Bomb = MyAI.Bomb | resultSet
		elif resultType == "uncover":
			resultSet = resultSet - MyAI.Safe
			MyAI.Q = MyAI.Q | resultSet
		else:
			MyAI.Revisit.add(tile)
	
	@staticmethod
	def reveal(tile: "list of 3 elements", ss: set, ms: set, colD: int, rowD: int) -> "tuple({tuple()},str)":
		'''determine the surrounding environment of the tile'''
		hint = tile[2]
		coord = (tile[0],tile[1])
		if hint == 0:
			return (MyAI.getCoordAround(coord, colD, rowD),"uncover")
		else:
			mineSet = MyAI.getMinesAround(coord, ms, colD, rowD)
			unknownSet = MyAI.getUnknownAround(coord, ss, ms, colD, rowD)
			mineNumber = len(mineSet)
			unknownNumber = len(unknownSet)	
			if mineNumber == hint:
				return (unknownSet,"uncover")
			elif mineNumber < hint:
				if (mineNumber + unknownNumber) == hint:
					return (unknownSet,"bomb")
				else:			
					return (set(),"revisit")
			else:
				raise ArithmeticError
	
	@staticmethod
	def getCoordAround(coord: tuple, colD: int, rowD: int) -> set:
		'''get coordinates (maximum 8) around a tile'''
		X = coord[0]
		Y = coord[1]
		tempSet = {(X-1,Y-1),(X-1,Y),(X-1,Y+1),
				(X,Y-1),(X,Y+1),
				(X+1,Y-1),(X+1,Y),(X+1,Y+1)}
		return set([i for i in tempSet if i[0] <= colD and i[1] <= rowD and i[0] >= 1 and i[1] >= 1])
	
	@staticmethod
	def getMinesAround(coord: tuple, ms: set, colD: int, rowD: int) -> set:
		''' need to provide a set that contains mines'''
		return (MyAI.getCoordAround(coord, colD, rowD)) & ms

	@staticmethod
	def getUnknownAround(coord: tuple, ss: set, ms: set, colD: int, rowD: int) -> set:
		''' needs to provide a set that contains mines and a set that contains safe tiles'''
		return (MyAI.getCoordAround(coord, colD, rowD) - ss - ms)

	class __Anna():
		''' Anna is the Analyzer. 
		She is only called when Pablo has already discovered every tile 
		that is certain/absolutely safe to uncover.
		Pablo gives Anna a tile that she needs to analyze
		Anna can draw scenarios and compare them, giving Pablo more insights'''
		def __clearAllVar(self) -> None:
			self.__tBomb = set()
			self.__tSafe = set()
			self.__scenarios = []
			
		def __init__(self, colD: int, rowD: int):
			self.__colD = colD
			self.__rowD = rowD
			
			self.__tBomb = set()
			self.__tSafe = set()
			
			self.__probBomb = set()
			self.__probSafe = set()
			
			self.__scenarios = []
			
			self.__debug = False
			
		def turnOnDebug(self):
			self.__debug = True
		
		def __printSets(self) -> None:
			print("tBomb: ", end = " ")
			for b in self.__tBomb:
				print (b, end = " ")
			print("\ntSafe: ", end = " ")
			for s in self.__tSafe:
				print(s, end = " ")
# 			print("\nScenarios: ", end = " ")
# 			for s in self.__scenarios:
# 				print(s, end = " ")
				
		def hasAnIdea(self) -> bool:
			#return (len(self.__tSafe) > 0)
			return (len(self.__tBomb) > 0 or len(self.__tSafe) > 0)
		
		def getBomb(self) -> set:
			return self.__tBomb
		
		def getSafe(self) -> set:
			return self.__tSafe
		
		def getScenarios(self) -> list:
			return self.__scenarios
		
		def askAnna(self, tile: tuple):
			self.__clearAllVar()
			
			bombScenarios = self.__initGuess(tile)
			for s in bombScenarios:
				if self.__debug: print("creating {scenario}'s scenario...".format(scenario = s))
				self.__executeGuess(set(s))
				
			if len(self.__scenarios) == 1:
				self.__realizeScenario(self.__scenarios[0])
			elif len(self.__scenarios) > 1:
				self.__realizeScenario(self.__compareScenario())
			
			if self.__debug: self.__printSets()
				
		def __initGuess(self, w: tuple) -> set:
			'''gets a tile and returns possible bomb scenarios in a set {{(),(),...},{},{},...}'''
			unknownTiles = MyAI.getUnknownAround((w[0],w[1]), MyAI.Safe, MyAI.Bomb, self.__colD, self.__rowD)
			mineSet = MyAI.getMinesAround((w[0],w[1]), MyAI.Bomb, self.__colD, self.__rowD)
			remainingMineNum = w[2] - len(mineSet)
			comb = combinations(unknownTiles, remainingMineNum)
			return set([i for i in list(comb)])
		
		def __executeGuess(self, bombSet: set) -> bool:
			'''gets a set of possible bombs, and starts to resolves the rest of the tiles
			according to this set of bombs.
			it returns true if a scenario does exist for this guess, false otherwise
			if it's true, it also adds the scenario to the self.__scenarios set'''

			self.__probBomb = MyAI.Bomb | bombSet
			self.__probSafe = MyAI.Safe
			tempSet = MyAI.Revisit
			try:
				while True:
					oldLength = len(tempSet)
					tempSet = self.__getRevisitSet(tempSet)
					if len(tempSet) == oldLength:
						break
			except ArithmeticError:
				if self.__debug: print("invalid Scenario")
				return False
			self.__scenarios.append(self.__formScenario())
			return True
		
		def __formScenario(self) -> "{(1,1,'bomb'),(,,),...}":
			resultSet = set()
			for b in self.__probBomb:
				if b not in MyAI.Bomb:
					resultSet.add((b[0],b[1],"bomb"))
			for s in self.__probSafe:
				if s not in MyAI.Safe:
					resultSet.add((s[0],s[1],"safe"))
			if self.__debug: print("scenarios formed: ", resultSet)
			return resultSet
	
		def __getRevisitSet(self, iteringSet: set) -> set:
			tempSet = set()
			for i in iteringSet:
				if MyAI.reveal(i, self.__probSafe, self.__probBomb, self.__colD, self.__rowD)[1] == "revisit":
					tempSet.add(i)
				self.__fillProbSet(i)
			return tempSet
				
		def __fillProbSet(self, tile: tuple) -> None:
			reveal = MyAI.reveal(tile, self.__probSafe, self.__probBomb, self.__colD, self.__rowD)
			revealSet = reveal[0]
			revealResult = reveal[1]
			if revealResult == "uncover":
				self.__probSafe = self.__probSafe | revealSet
			elif revealResult == "bomb":
				self.__probBomb = self.__probBomb | revealSet
			else:
				pass
		
		def __realizeScenario(self, scenario: set) -> None:
			'''make scenario come true, adding it to tBomb and tSafe'''
			for i in scenario:
				if i[2] == "bomb":
					self.__tBomb.add((i[0],i[1]))
				elif i[2] == "safe":
					self.__tSafe.add((i[0],i[1]))
			return
		
		def __compareScenario(self) -> "a scenario":
			'''compares two scenario and check if any of the tiles are same.
			put those tiles to tBomb & tSafe'''
			commonTiles = self.__scenarios[0] & self.__scenarios[1]
			for i in self.__scenarios[2:]:
				commonTiles = commonTiles & i
			if self.__debug: print("Common tiles are: ", commonTiles)
			return commonTiles
			

			
	class __Ramon():
		''' Ramon is the Random Number Mathematician.
		He is only called when Anna has no idea what to do
		aka when Anna has multiple scenarios that do not have anything in common.
		Ramon calculate probabilities of mines in Anna's scenarios
		as well as mines in the remaining random tiles
		When Ramon is called, there's a chance of uncovering a mine and ending the game'''
		
		def __init__(self, colD: int, rowD: int, mineNum: int, scenarios: list):
			self.__colD = colD
			self.__rowD = rowD
			self.__scenarios = scenarios
			self.__mineNum = mineNum
			
			self.__debug = False
		
		def turnOnDebug(self):
			self.__debug = True
		
		def updateScenarios(self, scenarios: list):
			self.__scenarios.extend(scenarios)
			#print(len(self.__scenarios), "scenarios updated")
		
		def clearScenarios(self) -> None:
			self.__scenarios = []
			#print('scenarios cleared')
		
		def askRamon(self) -> set:
			if self.__debug: input("Asking Ramon...continue?")
			if self.__debug: print(len(self.__scenarios),"scenarios are", self.__scenarios)
			resultSet = set()
			remainingTiles = self.__getRemainingTiles()
			if self.__debug: print(len(remainingTiles), "remaining tiles are:", remainingTiles)
			if len(remainingTiles) == 0:
				if self.__debug: print("No remaining tiles. Uncovering scenarios tiles...")
				resultSet.add(self.__minMineProbTile()[0])
			else:
				if self.__uncoverRand():
					if self.__debug: print("Random WIN! Uncovering random tiles...")
					remainingTiles = list(remainingTiles)
					random.shuffle(remainingTiles)
					resultSet.add(remainingTiles[0])
				else:
					if self.__debug: print("Non-Random WIN! Uncovering scenarios tiles...")
					resultSet.add(self.__minMineProbTile()[0])
			return resultSet
			
		def __getRemainingTiles(self) -> set:
			totalSet = set()
			for i in range(1, self.__colD+1):
				for j in range(1, self.__rowD+1):
					totalSet.add((i,j))
			unknownSet = set()
			for s in self.__scenarios:
				for t in s:
					unknownSet.add((t[0],t[1]))
			return (totalSet - MyAI.Safe - MyAI.Bomb - unknownSet)
		
		def __getRemainingMineNum(self) -> int:
			return (self.__mineNum - len(MyAI.Bomb))
		
		def __minBombInScenarios(self) -> (int, float):
			'''supposed number of bombs in total in scenario tiles'''
			bombSet = set()
			for s in self.__scenarios:
				for t in s:
					if t[2] == 'bomb':
						bombSet.add(t)
			if self.__debug: print(len(bombSet), 'scenario bomb sets are', bombSet)
			return len(bombSet)/2
		
		def __uncoverRand(self) -> bool:
			''' returns true if random tiles are safer to uncover than the tiles that are being calculated 
			also returns the probability of bombs'''
			bombInScene = self.__minBombInScenarios()
			bombRemainTotal = self.__getRemainingMineNum()
			bombNotInSce = bombRemainTotal - bombInScene
			randomMineProb = bombNotInSce/len(self.__getRemainingTiles())
			lowestMineProbInSce = self.__minMineProbTile()[1]
			if self.__debug: print("bomb in scene:", bombInScene, "random mine Prob", randomMineProb, "bomb total:", bombRemainTotal)
			if bombNotInSce <= -0.5:
				return True
			else:
				return (randomMineProb - lowestMineProbInSce) <= -0.05

	
		def __minMineProbTile(self) -> (tuple,float):
			''' returns a tile in the scenario that is the least likely to 
			be the mine'''
			appearanceDict = defaultdict(int)
			bombDict = defaultdict(int)
			for s in self.__scenarios:
				for t in s:
					appearanceDict[(t[0],t[1])]+=1
					if t[2] == "bomb":
						bombDict[(t[0],t[1])]+=1
			minProbTile = tuple()
			min = 1
			for k in appearanceDict.keys():
				if k in bombDict:
					if bombDict[k]/appearanceDict[k] < min:
						if self.__debug: print("for", k, "bomb is", bombDict[k], "appearance is", appearanceDict[k])
						min = bombDict[k]/appearanceDict[k]
						minProbTile = k
			if self.__debug: print("The safest tile is", minProbTile, "with a possibility of", min)
			return (minProbTile, min)
			
			
			
	

	
	
		

