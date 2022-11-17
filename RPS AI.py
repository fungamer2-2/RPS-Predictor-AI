from abc import ABC, abstractmethod
import random

"""
0 beats 2
1 beats 0
2 beats 1
"""

def get_result(cpu, player):
	if cpu == (player + 1) % 3:
		return 1
	elif cpu == player:
		 return 0
	else:
		return -1

class Predictor(ABC):
	
	def __init__(self, name):
		self.name = name
		self.score = 0
		
	def change_score(self, result):
		self.score *= 0.92 #Decays the score to help it adapt to a changing player strategy
		self.score += result
		
	def record(self, cpu, player):
		pass
			
	@abstractmethod
	def get_move(self):
		#0 = Rock, 1 = Paper, 2 = Scissors
		return 1

class Random(Predictor):
	
	def __init__(self):
		super().__init__("Random")
		
	def get_move(self):
		return random.randint(0, 2)
		
class BeatLastMove(Predictor):
	
	def __init__(self):
		super().__init__("Beat Last Move")
		self.player_last_move = None
	
	def record(self, cpu, player):
		self.player_last_move = player
		
	def get_move(self):
		if self.player_last_move == None:
			return random.randint(0, 2)
		return (self.player_last_move + 1) % 3

class CopyLastMove(Predictor):
	
	def __init__(self):
		super().__init__("Copy Last Move")
		self.player_last_move = None
	
	def record(self, cpu, player):
		self.player_last_move = player
		
	def get_move(self):
		if self.player_last_move == None:
			return random.randint(0, 2)
		return self.player_last_move

class LoseToLastMove(Predictor):
	
	def __init__(self):
		super().__init__("Lose to Last Move")
		self.player_last_move = None
	
	def record(self, cpu, player):
		self.player_last_move = player
		
	def get_move(self):
		if self.player_last_move == None:
			return random.randint(0, 2)
		return (self.player_last_move - 1) % 3

class BeatMostFrequent(Predictor):
	
	def __init__(self):
		super().__init__("Beat Most Frequent Move")
		self.moves = [0, 0, 0]
		
	def record(self, cpu, player):
		for i in range(3):
			self.moves[player] *= 0.92
		self.moves[player] += 1
		
	def get_move(self):
		if self.moves == [0, 0, 0]:
			return random.randint(0, 2)
		most = 0
		for i in range(len(self.moves)):
			if self.moves[i] > self.moves[most]:
				most = i
		return (most + 1) % 3

class AntiRotation(Predictor):
	
	def __init__(self):
		super().__init__("Anti-Rotation")	
		self.last1 = -1
		self.last2 = -1
		self.m = 1
		
	def record(self, cpu, player):
		self.last1 = self.last2
		self.last2 = player
		self.m += 1
		
	def get_move(self):
		if self.m == 1:
			return random.randint(0, 2)
		if self.m == 2:
			return (self.last2 + 1) % 3
		rot = self.last2 - self.last1
		return (self.last2 + rot + 1) % 3
		
class BeatPlayerMostCommonSelfFollowUp(Predictor):
	
	def __init__(self):
		super().__init__("Beat Most Common Player Self-Follow-Up")
		self.moves = [[0]*3 for _ in range(3)]
		self.m = 1
		self.last1 = -1
		self.last2 = -1
		
	def record(self, cpu, player):
		for row in self.moves:
			for i in range(3):
				row[i] *= 0.92
		self.last1 = self.last2
		self.last2 = player
		if self.m >= 2:
			self.moves[self.last1][self.last2] += 1
		self.m += 1
		
	def get_move(self):
		if self.m == 1:
			return random.randint(0, 2)
		if self.m == 2:
			return (self.last2 + 1) % 3
		moves = self.moves[self.last2]
		m = 0
		for i in range(3):
			if moves[i] > moves[m]:
				m = i
		return (m + 1) % 3
		
class WeightedFrequentist(Predictor):
	
	def __init__(self):
		super().__init__("Weighted Frequentist")
		self.moves = [0, 0, 0]
		
	def record(self, cpu, player):
		for i in range(3):
			self.moves[i] *= 0.92
		self.moves[player] += 1
		
	def get_move(self):
		if self.moves == [0, 0, 0]:
			return random.randint(0, 2)
		s = sum(self.moves)
		r = random.uniform(0, s)
		for i in range(len(self.moves)):
			r -= self.moves[i]
			if r < 0:
				return i
		print("ERROR: This should never happen")
		return random.randint(0, 2)
		
class AntiWinStayLoseShift(Predictor):
	
	def __init__(self):
		super().__init__("Anti Win-Stay-Lose Shift")
		self.last_result = 0
		self.my_last = 0
		self.their_last = 0
		
	def record(self, cpu, player):
		self.last_result = get_result(cpu, player)
		self.my_last = cpu
		self.their_last = player
		
	def get_move(self):
		if self.last_result == -1:
			return (self.their_last + 1) % 3
		elif self.last_result == 1:
			return (self.my_last + 1) % 3
		else:
			return random.randint(0, 2)
		
class AI(Predictor):
	
	def __init__(self, debug=False):
		super().__init__("AI")
		self.predictors = [
			Random(),
			BeatLastMove(),
			BeatMostFrequent(),
			AntiWinStayLoseShift(),
			WeightedFrequentist(),
			LoseToLastMove(),
			CopyLastMove(),
			AntiRotation(),
			BeatPlayerMostCommonSelfFollowUp()
		]
		self.strategy = None
		self.debug = debug
		
	def record(self, cpu, player):
		self.strategy.change_score(get_result(cpu, player))
		self.strategy.record(cpu, player)
		result = -1
		for p in self.predictors:
			if p is not self.strategy:
				move = p.get_move()
				p.change_score(get_result(move, player))
				p.record(move, player)
				
	def get_move(self):
		strategy = None
		highest = float("-inf")
		for p in self.predictors:
			if self.debug:
				print(f"{p.name}: {p.score:.3f}")
			if p.score > highest:
				highest = p.score
				strategy = p
		self.strategy = strategy
		if self.debug:
			print(f"Strategy: {strategy.name}")
		return strategy.get_move()
		
wins = 0
losses = 0
ties = 0
ai = AI()
while True:
	print(f"Wins: {wins}")
	print(f"Losses: {losses}")
	print(f"Ties: {ties}")
	valid = False
	while not valid:
		choice = input("(R)ock, (P)aper, or (S)cissors? ")
		if choice.upper() in ["R", "P", "S"]:
			valid = True
		else:
			print("Please enter (R)ock, (P)aper, or (S)cissors")
	move = ["R", "P", "S"].index(choice.upper())
	move_str = ["Rock", "Paper", "Scissors"][move]
	print(f"You chose {move_str}")
	ai_move = ai.get_move()
	move_str = ["Rock", "Paper", "Scissors"][ai_move]
	print(f"The computer chose {move_str}")
	res = get_result(move, ai_move)
	if res == 1:
		print("You won!")
		wins += 1
	elif res == -1:
		print("You lost.")
		losses += 1
	else:
		print("Tie!")
		ties += 1
	ai.record(ai_move, move)
	print()