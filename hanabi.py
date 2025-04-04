from collections import Counter
import random
import sys
import copy
import time

import numpy as np

GREEN = 0
YELLOW = 1
WHITE = 2
BLUE = 3
RED = 4
ALL_COLORS = [GREEN, YELLOW, WHITE, BLUE, RED]
COLORNAMES = ["green", "yellow", "white", "blue", "red"]

COUNTS = [3,2,2,2,1]

# semi-intelligently format cards in any format
def f(something):
    if type(something) == list:
        return list(map(f, something))
    elif type(something) == dict:
        return {k: something(v) for (k,v) in something.items()}
    elif type(something) == tuple and len(something) == 2:
        return (COLORNAMES[something[0]],something[1])
    return something

def make_deck():
    deck = []
    for col in ALL_COLORS:
        for num, cnt in enumerate(COUNTS):
            for i in range(cnt):
                deck.append((col, num+1))
    random.shuffle(deck)
    return deck
    
def initial_knowledge():
    knowledge = []
    for col in ALL_COLORS:
        knowledge.append(COUNTS[:])
    return knowledge
    
def hint_color(knowledge, color, truth):
    result = []
    for col in ALL_COLORS:
        if truth == (col == color):
            result.append(knowledge[col][:])
        else:
            result.append([0 for i in knowledge[col]])
    return result
    
def hint_rank(knowledge, rank, truth):
    result = []
    for col in ALL_COLORS:
        colknow = []
        for i,k in enumerate(knowledge[col]):
            if truth == (i + 1 == rank):
                colknow.append(k)
            else:
                colknow.append(0)
        result.append(colknow)
    return result
    
def iscard(xxx_todo_changeme14):
    (c,n) = xxx_todo_changeme14
    knowledge = []
    for col in ALL_COLORS:
        knowledge.append(COUNTS[:])
        for i in range(len(knowledge[-1])):
            if col != c or i+1 != n:
                knowledge[-1][i] = 0
            else:
                knowledge[-1][i] = 1
            
    return knowledge
    
HINT_COLOR = 0
HINT_NUMBER = 1
PLAY = 2
DISCARD = 3
    
class Action(object):
    def __init__(self, type, pnr=None, col=None, num=None, cnr=None):
        self.type = type
        self.pnr = pnr
        self.col = col
        self.num = num
        self.cnr = cnr
    def __str__(self):
        if self.type == HINT_COLOR:
            return "hints " + str(self.pnr) + " about all their " + COLORNAMES[self.col] + " cards"
        if self.type == HINT_NUMBER:
            return "hints " + str(self.pnr) + " about all their " + str(self.num)
        if self.type == PLAY:
            return "plays their " + str(self.cnr)
        if self.type == DISCARD:
            return "discards their " + str(self.cnr)
    def __eq__(self, other):
        return (self.type, self.pnr, self.col, self.num, self.cnr) == (other.type, other.pnr, other.col, other.num, other.cnr)
        
class Player(object):
    def __init__(self, name, pnr):
        self.name = name
        self.explanation = []
    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints):
        return random.choice(valid_actions)
    def inform(self, action, player, game):
        pass
    def get_explanation(self):
        return self.explanation
        
def get_possible(knowledge):
    result = []
    for col in ALL_COLORS:
        for i,cnt in enumerate(knowledge[col]):
            if cnt > 0:
                result.append((col,i+1))
    return result
    
def playable(possible, board):
    for (col,nr) in possible:
        if board[col][1] + 1 != nr:
            return False
    return True
    
def potentially_playable(possible, board):
    for (col,nr) in possible:
        if board[col][1] + 1 == nr:
            return True
    return False
    
def discardable(possible, board):
    for (col,nr) in possible:
        if board[col][1] < nr:
            return False
    return True
    
def potentially_discardable(possible, board):
    for (col,nr) in possible:
        if board[col][1] >= nr:
            return True
    return False
    
def update_knowledge(knowledge, used):
    result = copy.deepcopy(knowledge)
    for r in result:
        for (c,nr) in used:
            r[c][nr-1] = max(r[c][nr-1] - used[c,nr], 0)
    return result
        
class InnerStatePlayer(Player):
    def __init__(self, name, pnr):
        self.name = name
        self.explanation = []
        self.pnr = pnr

    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints):
        print(hands)
        handsize = len(knowledge[0])
        possible = []
        for k in knowledge[nr]:
            possible.append(get_possible(k))
        
        discards = []
        duplicates = []
        for i,p in enumerate(possible):
            if playable(p,board):
                return Action(PLAY, cnr=i)
            if discardable(p,board):
                discards.append(i)

        if discards:
            return Action(DISCARD, cnr=random.choice(discards))
            
        playables = []
        for i,h in enumerate(hands):
            if i != nr:
                for j,(col,n) in enumerate(h):
                    if board[col][1] + 1 == n:
                        playables.append((i,j))
        
        if playables and hints > 0:
            i,j = playables[0]
            if random.random() < 0.5:
                return Action(HINT_COLOR, pnr=i, col=hands[i][j][0])
            return Action(HINT_NUMBER, pnr=i, num=hands[i][j][1])
        
        
        for i, k in enumerate(knowledge):
            if i == nr:
                continue
            cards = list(range(len(k)))
            random.shuffle(cards)
            c = cards[0]
            (col,num) = hands[i][c]            
            hinttype = [HINT_COLOR, HINT_NUMBER]
            if hinttype and hints > 0:
                if random.choice(hinttype) == HINT_COLOR:
                    return Action(HINT_COLOR, pnr=i, col=col)
                else:
                    return Action(HINT_NUMBER, pnr=i, num=num)
        
        prefer = []
        for v in valid_actions:
            if v.type in [HINT_COLOR, HINT_NUMBER]:
                prefer.append(v)
        prefer = []
        if prefer and hints > 0:
            return random.choice(prefer)
        return random.choice([Action(DISCARD, cnr=i) for i in range(len(knowledge[0]))])
    def inform(self, action, player, game):
        pass
        
class OuterStatePlayer(Player):
    def __init__(self, name, pnr):
        self.name = name
        self.hints = {}
        self.pnr = pnr
        self.explanation = []

    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints):
        
        handsize = len(knowledge[0])
        possible = []
        for k in knowledge[nr]:
            possible.append(get_possible(k))
        
        discards = []
        duplicates = []
        for i,p in enumerate(possible):
            if playable(p,board):
                return Action(PLAY, cnr=i)
            if discardable(p,board):
                discards.append(i)

        if discards:
            return Action(DISCARD, cnr=random.choice(discards))
            
        playables = []
        for i,h in enumerate(hands):
            if i != nr:
                for j,(col,n) in enumerate(h):
                    if board[col][1] + 1 == n:
                        playables.append((i,j))
        playables.sort(key=lambda i_j: -hands[i_j[0]][i_j[1]][1])
        while playables and hints > 0:
            i,j = playables[0]
            knows_rank = True
            real_color = hands[i][j][0]
            real_rank = hands[i][j][0]
            k = knowledge[i][j]
            
            hinttype = [HINT_COLOR, HINT_NUMBER]
            if (j,i) not in self.hints:
                self.hints[(j,i)] = []
            
            for h in self.hints[(j,i)]:
                hinttype.remove(h)
            
            t = None
            if hinttype:
                t = random.choice(hinttype)
            
            if t == HINT_NUMBER:
                self.hints[(j,i)].append(HINT_NUMBER)
                return Action(HINT_NUMBER, pnr=i, num=hands[i][j][1])
            if t == HINT_COLOR:
                self.hints[(j,i)].append(HINT_COLOR)
                return Action(HINT_COLOR, pnr=i, col=hands[i][j][0])
            
            playables = playables[1:]
        
        for i, k in enumerate(knowledge):
            if i == nr:
                continue
            cards = list(range(len(k)))
            random.shuffle(cards)
            c = cards[0]
            (col,num) = hands[i][c]            
            hinttype = [HINT_COLOR, HINT_NUMBER]
            if (c,i) not in self.hints:
                self.hints[(c,i)] = []
            for h in self.hints[(c,i)]:
                hinttype.remove(h)
            if hinttype and hints > 0:
                if random.choice(hinttype) == HINT_COLOR:
                    self.hints[(c,i)].append(HINT_COLOR)
                    return Action(HINT_COLOR, pnr=i, col=col)
                else:
                    self.hints[(c,i)].append(HINT_NUMBER)
                    return Action(HINT_NUMBER, pnr=i, num=num)

        return random.choice([Action(DISCARD, cnr=i) for i in range(handsize)])
    def inform(self, action, player, game):
        if action.type in [PLAY, DISCARD]:
            x = str(action)
            if (action.cnr,player) in self.hints:
                self.hints[(action.cnr,player)] = []
            for i in range(10):
                if (action.cnr+i+1,player) in self.hints:
                    self.hints[(action.cnr+i,player)] = self.hints[(action.cnr+i+1,player)]
                    self.hints[(action.cnr+i+1,player)] = []
        print(self.hints)

                    
def generate_hands(knowledge, used={}):
    if len(knowledge) == 0:
        yield []
        return
    
    
    
    for other in generate_hands(knowledge[1:], used):
        for col in ALL_COLORS:
            for i,cnt in enumerate(knowledge[0][col]):
                if cnt > 0:
                    
                    result = [(col,i+1)] + other
                    ok = True
                    thishand = {}
                    for (c,n) in result:
                        if (c,n) not in thishand:
                            thishand[(c,n)] = 0
                        thishand[(c,n)] += 1
                    for (c,n) in thishand:
                        if used[(c,n)] + thishand[(c,n)] > COUNTS[n-1]:
                           ok = False
                    if ok:
                        yield  result

def generate_hands_simple(knowledge, used={}):
    if len(knowledge) == 0:
        yield []
        return
    for other in generate_hands_simple(knowledge[1:]):
        for col in ALL_COLORS:
            for i,cnt in enumerate(knowledge[0][col]):
                if cnt > 0:
                    yield [(col,i+1)] + other



                    
a = 1   

class SelfRecognitionPlayer(Player):
    def __init__(self, name, pnr, other=OuterStatePlayer):
        self.name = name
        self.hints = {}
        self.pnr = pnr
        self.gothint = None
        self.last_knowledge = []
        self.last_played = []
        self.last_board = []
        self.other = other
        self.explanation = []
    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints):
        handsize = len(knowledge[0])
        possible = []
        if self.gothint:
            
            possiblehands = []
            wrong = 0
            used = {}
            for c in ALL_COLORS:
                for i,cnt in enumerate(COUNTS):
                    used[(c,i+1)] = 0
            for c in trash + played:
                used[c] += 1
            
            for h in generate_hands_simple(knowledge[nr], used):
                newhands = hands[:]
                newhands[nr] = h
                other = self.other("Pinocchio", self.gothint[1])
                act = other.get_action(self.gothint[1], newhands, self.last_knowledge, self.last_trash, self.last_played, self.last_board, valid_actions, hints + 1)
                lastact = self.gothint[0]
                if act == lastact:
                    possiblehands.append(h)
                    def do(c,i):
                        newhands = hands[:]
                        h1 = h[:]
                        h1[i] = c
                        newhands[nr] = h1
                        print(other.get_action(self.gothint[1], newhands, self.last_knowledge, self.last_trash, self.last_played, self.last_board, valid_actions, hints + 1))
                    #import pdb
                    #pdb.set_trace()
                else:
                    wrong += 1
            #print len(possiblehands), "would have led to", self.gothint[0], "and not:", wrong
            #print f(possiblehands)
            if possiblehands:
                mostlikely = [(0,0) for i in range(len(possiblehands[0]))]
                for i in range(len(possiblehands[0])):
                    counts = {}
                    for h in possiblehands:
                        if h[i] not in counts:
                            counts[h[i]] = 0
                        counts[h[i]] += 1
                    for c in counts:
                        if counts[c] > mostlikely[i][1]:
                            mostlikely[i] = (c,counts[c])
                #print "most likely:", mostlikely
                m = max(mostlikely, key=lambda card_cnt: card_cnt[1])
                second = mostlikely[:]
                second.remove(m)
                m2 = max(second, key=lambda card_cnt2: card_cnt2[1])
                if m[1] >= m2[1]*a:
                    #print ">>>>>>> deduced!", f(m[0]), m[1],"vs", f(m2[0]), m2[1]
                    knowledge = copy.deepcopy(knowledge)
                    knowledge[nr][mostlikely.index(m)] = iscard(m[0])

        
        self.gothint = None
        for k in knowledge[nr]:
            possible.append(get_possible(k))
        
        discards = []
        duplicates = []
        for i,p in enumerate(possible):
            if playable(p,board):
                return Action(PLAY, cnr=i)
            if discardable(p,board):
                discards.append(i)

        if discards:
            return Action(DISCARD, cnr=random.choice(discards))
            
        playables = []
        for i,h in enumerate(hands):
            if i != nr:
                for j,(col,n) in enumerate(h):
                    if board[col][1] + 1 == n:
                        playables.append((i,j))
        playables.sort(key=lambda i_j9: -hands[i_j9[0]][i_j9[1]][1])
        while playables and hints > 0:
            i,j = playables[0]
            knows_rank = True
            real_color = hands[i][j][0]
            real_rank = hands[i][j][0]
            k = knowledge[i][j]
            
            hinttype = [HINT_COLOR, HINT_NUMBER]
            if (j,i) not in self.hints:
                self.hints[(j,i)] = []
            
            for h in self.hints[(j,i)]:
                hinttype.remove(h)
            
            if HINT_NUMBER in hinttype:
                self.hints[(j,i)].append(HINT_NUMBER)
                return Action(HINT_NUMBER, pnr=i, num=hands[i][j][1])
            if HINT_COLOR in hinttype:
                self.hints[(j,i)].append(HINT_COLOR)
                return Action(HINT_COLOR, pnr=i, col=hands[i][j][0])
            
            playables = playables[1:]
        
        for i, k in enumerate(knowledge):
            if i == nr:
                continue
            cards = list(range(len(k)))
            random.shuffle(cards)
            c = cards[0]
            (col,num) = hands[i][c]            
            hinttype = [HINT_COLOR, HINT_NUMBER]
            if (c,i) not in self.hints:
                self.hints[(c,i)] = []
            for h in self.hints[(c,i)]:
                hinttype.remove(h)
            if hinttype and hints > 0:
                if random.choice(hinttype) == HINT_COLOR:
                    self.hints[(c,i)].append(HINT_COLOR)
                    return Action(HINT_COLOR, pnr=i, col=col)
                else:
                    self.hints[(c,i)].append(HINT_NUMBER)
                    return Action(HINT_NUMBER, pnr=i, num=num)

        return random.choice([Action(DISCARD, cnr=i) for i in range(handsize)])
    def inform(self, action, player, game):
        if action.type in [PLAY, DISCARD]:
            x = str(action)
            if (action.cnr,player) in self.hints:
                self.hints[(action.cnr,player)] = []
            for i in range(10):
                if (action.cnr+i+1,player) in self.hints:
                    self.hints[(action.cnr+i,player)] = self.hints[(action.cnr+i+1,player)]
                    self.hints[(action.cnr+i+1,player)] = []
        elif action.pnr == self.pnr:
            self.gothint = (action,player)
            self.last_knowledge = game.knowledge[:]
            self.last_board = game.board[:]
            self.last_trash = game.trash[:]
            self.played = game.played[:]
            
TIMESCALE = 40.0/1000.0 # ms
SLICETIME = TIMESCALE / 10.0
APPROXTIME = SLICETIME/8.0

def priorities(c, board):
    (col,val) = c
    if board[col][1] == val-1:
        return val - 1
    if board[col][1] >= val:
        return 5
    if val == 5:
        return 15
    return 6 + (4 - val)
    


SENT = 0
ERRORS = 0
COUNT = 0

CAREFUL = True
        
class TimedPlayer(object):
    def __init__(self, name, pnr):
        self.name = name
        self.explanation = []
        self.last_tick = time.time()
        self.pnr = pnr
        self.last_played = False
        self.tt = time.time()
    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints):
        global SENT, ERRORS, COUNT
        tick = time.time()
        duration = round((tick - self.last_tick)/SLICETIME)
        other = (self.pnr + 1)% len(hands)
        #print(self.pnr, "got", duration)
        if duration >= 10:
            duration = 9
        if duration != SENT:
            ERRORS += 1
            #print("mismatch", nr, f(hands), f(board), duration, SENT)
        COUNT += 1
        other_hand = hands[other][:]
        def prio(c):
            return priorities(c,board)
        other_hand.sort(key=prio)
        #print(f(other_hand), f(board), list(map(prio, other_hand)), f(hands))
        p = prio(other_hand[0])
        delta = 0.0
        if p >= 5:
            delta += 5
        #print("idx", hands[other].index(other_hand[0]))
        def fix(n):
            if n >= len(other_hand):
               return len(other_hand) - 1
            return int(round(n))
        delta += hands[other].index(other_hand[0])
        if duration >= 5:
            action = Action(DISCARD, cnr=fix(duration-5))
        else:
            action = Action(PLAY, cnr=fix(duration))
        if self.last_played and hints > 0 and CAREFUL:
            action = Action(HINT_COLOR, pnr=other, col=other_hand[0][0])
        t1 = time.time()
        SENT = delta
        #print(self.pnr, "convey", round(delta))
        delta -= 0.5
        while (t1 - tick) < delta*SLICETIME:
            time.sleep(APPROXTIME)
            t1 = time.time()
        self.last_tick = time.time()
        return action
    def inform(self, action, player, game):
        self.last_played = (action.type == PLAY)
        self.last_tick = self.tt
        self.tt = time.time()
        #print(action, player)
    def get_explanation(self):
        return self.explanation
            
            
CANDISCARD = 128

def format_intention(i):
    if isinstance(i, str):
        return i
    if i == PLAY:
        return "Play"
    elif i == DISCARD:
        return "Discard"
    elif i == CANDISCARD:
        return "Can Discard"
    return "Keep"
    
def whattodo(knowledge, pointed, board):
    possible = get_possible(knowledge)
    play = potentially_playable(possible, board)
    discard = potentially_discardable(possible, board)
    
    if play and pointed:
        return PLAY
    if discard and pointed:
        return DISCARD
    return None

def pretend(action, knowledge, intentions, hand, board):
    (type,value) = action
    positive = []
    haspositive = False
    change = False
    if type == HINT_COLOR:
        newknowledge = []
        for i,(col,num) in enumerate(hand):
            positive.append(value==col)
            newknowledge.append(hint_color(knowledge[i], value, value == col))
            if value == col:
                haspositive = True
                if newknowledge[-1] != knowledge[i]:
                    change = True
    else:
        newknowledge = []
        for i,(col,num) in enumerate(hand):
            positive.append(value==num)
            
            newknowledge.append(hint_rank(knowledge[i], value, value == num))
            if value == num:
                haspositive = True
                if newknowledge[-1] != knowledge[i]:
                    change = True
    if not haspositive:
        return False, 0, ["Invalid hint"]
    if not change:
        return False, 0, ["No new information"]
    score = 0
    predictions = []
    pos = False
    for i,c,k,p in zip(intentions, hand, newknowledge, positive):
        
        action = whattodo(k, p, board)
        
        if action == PLAY and i != PLAY:
            #print "would cause them to play", f(c)
            return False, 0, predictions + [PLAY]
        
        if action == DISCARD and i not in [DISCARD, CANDISCARD]:
            #print "would cause them to discard", f(c)
            return False, 0, predictions + [DISCARD]
            
        if action == PLAY and i == PLAY:
            pos = True
            predictions.append(PLAY)
            score += 3
        elif action == DISCARD and i in [DISCARD, CANDISCARD]:
            pos = True
            predictions.append(DISCARD)
            if i == DISCARD:
                score += 2
            else:
                score += 1
        else:
            predictions.append(None)
    if not pos:
        return False, score, predictions
    return True,score, predictions
    
HINT_VALUE = 0.5
    
def pretend_discard(act, knowledge, board, trash):
    which = copy.deepcopy(knowledge[act.cnr])
    for (col,num) in trash:
        if which[col][num-1]:
            which[col][num-1] -= 1
    for col in ALL_COLORS:
        for i in range(board[col][1]):
            if which[col][i]:
                which[col][i] -= 1
    possibilities = sum(map(sum, which))
    expected = 0
    terms = []
    for col in ALL_COLORS:
        for i,cnt in enumerate(which[col]):
            rank = i+1
            if cnt > 0:
                prob = cnt*1.0/possibilities
                if board[col][1] >= rank:
                    expected += prob*HINT_VALUE
                    terms.append((col,rank,cnt,prob,prob*HINT_VALUE))
                else:
                    dist = rank - board[col][1]
                    if cnt > 1:
                        value = prob*(6-rank)/(dist*dist)
                    else:
                        value = (6-rank)
                    if rank == 5:
                        value += HINT_VALUE
                    value *= prob
                    expected -= value
                    terms.append((col,rank,cnt,prob,-value))
    return (act, expected, terms)

def format_knowledge(k):
    result = ""
    for col in ALL_COLORS:
        for i,cnt in enumerate(k[col]):
            if cnt > 0:
                result += COLORNAMES[col] + " " + str(i+1) + ": " + str(cnt) + "\n"
    return result

class IntentionalPlayer(Player):
    def __init__(self, name, pnr):
        self.name = name
        self.hints = {}
        self.pnr = pnr
        self.gothint = None
        self.last_knowledge = []
        self.last_played = []
        self.last_board = []
        self.explanation = []
    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints):
        handsize = len(knowledge[0])
        possible = []
        result = None
        self.explanation = []
        self.explanation.append(["Your Hand:"] + list(map(f, hands[1-nr])))
        
        self.gothint = None
        for k in knowledge[nr]:
            possible.append(get_possible(k))
        
        discards = []
        duplicates = []
        for i,p in enumerate(possible):
            if playable(p,board):
                result = Action(PLAY, cnr=i)
            if discardable(p,board):
                discards.append(i)

        if discards and hints < 8 and not result:
            result =  Action(DISCARD, cnr=random.choice(discards))
            
        playables = []
        useless = []
        discardables = []
        othercards = trash + board
        intentions = [None for i in range(handsize)]
        for i,h in enumerate(hands):
            if i != nr:
                for j,(col,n) in enumerate(h):
                    if board[col][1] + 1 == n:
                        playables.append((i,j))
                        intentions[j] = PLAY
                    if board[col][1] >= n:
                        useless.append((i,j))
                        if not intentions[j]:
                            intentions[j] = DISCARD
                    if n < 5 and (col,n) not in othercards:
                        discardables.append((i,j))
                        if not intentions[j]:
                            intentions[j] = CANDISCARD
        
        self.explanation.append(["Intentions"] + list(map(format_intention, intentions)))
        
        
            
        if hints > 0:
            valid = []
            for c in ALL_COLORS:
                action = (HINT_COLOR, c)
                #print "HINT", COLORNAMES[c],
                (isvalid,score,expl) = pretend(action, knowledge[1-nr], intentions, hands[1-nr], board)
                self.explanation.append(["Prediction for: Hint Color " + COLORNAMES[c]] + list(map(format_intention, expl)))
                #print isvalid, score
                if isvalid:
                    valid.append((action,score))
            
            for r in range(5):
                r += 1
                action = (HINT_NUMBER, r)
                #print "HINT", r,
                
                (isvalid,score, expl) = pretend(action, knowledge[1-nr], intentions, hands[1-nr], board)
                self.explanation.append(["Prediction for: Hint Rank " + str(r)] + list(map(format_intention, expl)))
                #print isvalid, score
                if isvalid:
                    valid.append((action,score))
                 
            if valid and not result:
                valid.sort(key=lambda a_s: -a_s[1])
                #print valid
                (a,s) = valid[0]
                if a[0] == HINT_COLOR:
                    result = Action(HINT_COLOR, pnr=1-nr, col=a[1])
                else:
                    result = Action(HINT_NUMBER, pnr=1-nr, num=a[1])

        self.explanation.append(["My Knowledge"] + list(map(format_knowledge, knowledge[nr])))
        possible = [ Action(DISCARD, cnr=i) for i in range(handsize) ]
        
        scores = [pretend_discard(p, knowledge[nr], board, trash) for p in possible]
        def format_term(xxx_todo_changeme):
            (col,rank,n,prob,val) = xxx_todo_changeme
            return COLORNAMES[col] + " " + str(rank) + " (%.2f%%): %.2f"%(prob*100, val)
            
        self.explanation.append(["Discard Scores"] + ["\n".join(map(format_term, a_s_t[2])) + "\n%.2f"%(a_s_t[1]) for a_s_t in scores])
        scores.sort(key=lambda a_s_t10: -a_s_t10[1])
        if result:
            return result
        return scores[0][0]
        
        return random.choice([Action(DISCARD, cnr=i) for i in range(handsize)])
    def inform(self, action, player, game):
        if action.type in [PLAY, DISCARD]:
            x = str(action)
            if (action.cnr,player) in self.hints:
                self.hints[(action.cnr,player)] = []
            for i in range(10):
                if (action.cnr+i+1,player) in self.hints:
                    self.hints[(action.cnr+i,player)] = self.hints[(action.cnr+i+1,player)]
                    self.hints[(action.cnr+i+1,player)] = []
        elif action.pnr == self.pnr:
            self.gothint = (action,player)
            self.last_knowledge = game.knowledge[:]
            self.last_board = game.board[:]
            self.last_trash = game.trash[:]
            self.played = game.played[:]
            
            
            
class SelfIntentionalPlayer(Player):
    def __init__(self, name, pnr):
        self.name = name
        self.hints = {}
        self.pnr = pnr
        self.gothint = None
        self.last_knowledge = []
        self.last_played = []
        self.last_board = []
        self.explanation = []
    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints):
        handsize = len(knowledge[0])
        possible = []
        result = None
        self.explanation = []
        self.explanation.append(["Your Hand:"] + list(map(f, hands[1-nr])))
        action = []
        if self.gothint:
            (act,plr) = self.gothint
            if act.type == HINT_COLOR:
                for k in knowledge[nr]:
                    action.append(whattodo(k, sum(k[act.col]) > 0, board))
            elif act.type == HINT_NUMBER:
                for k in knowledge[nr]:
                    cnt = 0
                    for c in ALL_COLORS:
                        cnt += k[c][act.num-1]
                    action.append(whattodo(k, cnt > 0, board))
                    

        if action:
            self.explanation.append(["What you want me to do"] + list(map(format_intention, action)))
            for i,a in enumerate(action):
                if a == PLAY and (not result or result.type == DISCARD):
                    result = Action(PLAY, cnr=i)
                elif a == DISCARD and not result:
                    result = Action(DISCARD, cnr=i)

        self.gothint = None
        for k in knowledge[nr]:
            possible.append(get_possible(k))
        
        discards = []
        duplicates = []
        for i,p in enumerate(possible):
            if playable(p,board) and not result:
                result = Action(PLAY, cnr=i)
            if discardable(p,board):
                discards.append(i)

        if discards and hints < 8 and not result:
            result =  Action(DISCARD, cnr=random.choice(discards))
            
        playables = []
        useless = []
        discardables = []
        othercards = trash + board
        intentions = [None for i in range(handsize)]
        for i,h in enumerate(hands):
            if i != nr:
                for j,(col,n) in enumerate(h):
                    if board[col][1] + 1 == n:
                        playables.append((i,j))
                        intentions[j] = PLAY
                    if board[col][1] >= n:
                        useless.append((i,j))
                        if not intentions[j]:
                            intentions[j] = DISCARD
                    if n < 5 and (col,n) not in othercards:
                        discardables.append((i,j))
                        if not intentions[j]:
                            intentions[j] = CANDISCARD
        
        self.explanation.append(["Intentions"] + list(map(format_intention, intentions)))
        
        
            
        if hints > 0:
            valid = []
            for c in ALL_COLORS:
                action = (HINT_COLOR, c)
                #print "HINT", COLORNAMES[c],
                (isvalid,score,expl) = pretend(action, knowledge[1-nr], intentions, hands[1-nr], board)
                self.explanation.append(["Prediction for: Hint Color " + COLORNAMES[c]] + list(map(format_intention, expl)))
                #print isvalid, score
                if isvalid:
                    valid.append((action,score))
            
            for r in range(5):
                r += 1
                action = (HINT_NUMBER, r)
                #print "HINT", r,
                
                (isvalid,score, expl) = pretend(action, knowledge[1-nr], intentions, hands[1-nr], board)
                self.explanation.append(["Prediction for: Hint Rank " + str(r)] + list(map(format_intention, expl)))
                #print isvalid, score
                if isvalid:
                    valid.append((action,score))
                 
            if valid and not result:
                valid.sort(key=lambda a_s5: -a_s5[1])
                #print valid
                (a,s) = valid[0]
                if a[0] == HINT_COLOR:
                    result = Action(HINT_COLOR, pnr=1-nr, col=a[1])
                else:
                    result = Action(HINT_NUMBER, pnr=1-nr, num=a[1])

        self.explanation.append(["My Knowledge"] + list(map(format_knowledge, knowledge[nr])))
        possible = [ Action(DISCARD, cnr=i) for i in range(handsize) ]
        
        scores = [pretend_discard(p, knowledge[nr], board, trash) for p in possible]
        def format_term(xxx_todo_changeme13):
            (col,rank,n,prob,val) = xxx_todo_changeme13
            return COLORNAMES[col] + " " + str(rank) + " (%.2f%%): %.2f"%(prob*100, val)
            
        self.explanation.append(["Discard Scores"] + ["\n".join(map(format_term, a_s_t7[2])) + "\n%.2f"%(a_s_t7[1]) for a_s_t7 in scores])
        scores.sort(key=lambda a_s_t11: -a_s_t11[1])
        if result:
            return result
        return scores[0][0]
        
        return random.choice([Action(DISCARD, cnr=i) for i in range(handsize)])
    def inform(self, action, player, game):
        if action.type in [PLAY, DISCARD]:
            x = str(action)
            if (action.cnr,player) in self.hints:
                self.hints[(action.cnr,player)] = []
            for i in range(10):
                if (action.cnr+i+1,player) in self.hints:
                    self.hints[(action.cnr+i,player)] = self.hints[(action.cnr+i+1,player)]
                    self.hints[(action.cnr+i+1,player)] = []
        elif action.pnr == self.pnr:
            self.gothint = (action,player)
            self.last_knowledge = game.knowledge[:]
            self.last_board = game.board[:]
            self.last_trash = game.trash[:]
            self.played = game.played[:]
            

    
def do_sample(knowledge):
    if not knowledge:
        return []
        
    possible = []
    
    for col in ALL_COLORS:
        for i,c in enumerate(knowledge[0][col]):
            for j in range(c):
                possible.append((col,i+1))
    if not possible:
        return None
    
    other = do_sample(knowledge[1:])
    if other is None:
        return None
    sample = random.choice(possible)
    return [sample] + other
    
def sample_hand(knowledge):
    result = None
    while result is None:
        result = do_sample(knowledge)
    return result
    
used = {}
for c in ALL_COLORS:
    for i,cnt in enumerate(COUNTS):
        used[(c,i+1)] = 0

    

class SamplingRecognitionPlayer(Player):
    def __init__(self, name, pnr, other=IntentionalPlayer, maxtime=5000):
        self.name = name
        self.hints = {}
        self.pnr = pnr
        self.gothint = None
        self.last_knowledge = []
        self.last_played = []
        self.last_board = []
        self.other = other
        self.maxtime = maxtime
        self.explanation = []
    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints):
        handsize = len(knowledge[0])
        possible = []
        
        if self.gothint:
            possiblehands = []
            wrong = 0
            used = {}
            
            for c in trash + played:
                if c not in used:
                    used[c] = 0
                used[c] += 1
            
            i = 0
            t0 = time.time()
            while i < self.maxtime:
                i += 1
                h = sample_hand(update_knowledge(knowledge[nr], used))
                newhands = hands[:]
                newhands[nr] = h
                other = self.other("Pinocchio", self.gothint[1])
                act = other.get_action(self.gothint[1], newhands, self.last_knowledge, self.last_trash, self.last_played, self.last_board, valid_actions, hints + 1)
                lastact = self.gothint[0]
                if act == lastact:
                    possiblehands.append(h)
                    def do(c,i):
                        newhands = hands[:]
                        h1 = h[:]
                        h1[i] = c
                        newhands[nr] = h1
                        print(other.get_action(self.gothint[1], newhands, self.last_knowledge, self.last_trash, self.last_played, self.last_board, valid_actions, hints + 1))
                    #import pdb
                    #pdb.set_trace()
                else:
                    wrong += 1
            #print "sampled", i
            #print len(possiblehands), "would have led to", self.gothint[0], "and not:", wrong
            #print f(possiblehands)
            if possiblehands:
                mostlikely = [(0,0) for i in range(len(possiblehands[0]))]
                for i in range(len(possiblehands[0])):
                    counts = {}
                    for h in possiblehands:
                        if h[i] not in counts:
                            counts[h[i]] = 0
                        counts[h[i]] += 1
                    for c in counts:
                        if counts[c] > mostlikely[i][1]:
                            mostlikely[i] = (c,counts[c])
                #print "most likely:", mostlikely
                m = max(mostlikely, key=lambda card_cnt3: card_cnt3[1])
                second = mostlikely[:]
                second.remove(m)
                m2 = max(second, key=lambda card_cnt4: card_cnt4[1])
                if m[1] >= m2[1]*a:
                    #print ">>>>>>> deduced!", f(m[0]), m[1],"vs", f(m2[0]), m2[1]
                    knowledge = copy.deepcopy(knowledge)
                    knowledge[nr][mostlikely.index(m)] = iscard(m[0])

        
        self.gothint = None
        for k in knowledge[nr]:
            possible.append(get_possible(k))
        
        discards = []
        duplicates = []
        for i,p in enumerate(possible):
            if playable(p,board):
                return Action(PLAY, cnr=i)
            if discardable(p,board):
                discards.append(i)

        if discards:
            return Action(DISCARD, cnr=random.choice(discards))
            
        playables = []
        for i,h in enumerate(hands):
            if i != nr:
                for j,(col,n) in enumerate(h):
                    if board[col][1] + 1 == n:
                        playables.append((i,j))
        playables.sort(key=lambda i_j12: -hands[i_j12[0]][i_j12[1]][1])
        while playables and hints > 0:
            i,j = playables[0]
            knows_rank = True
            real_color = hands[i][j][0]
            real_rank = hands[i][j][0]
            k = knowledge[i][j]
            
            hinttype = [HINT_COLOR, HINT_NUMBER]
            if (j,i) not in self.hints:
                self.hints[(j,i)] = []
            
            for h in self.hints[(j,i)]:
                hinttype.remove(h)
            
            if HINT_NUMBER in hinttype:
                self.hints[(j,i)].append(HINT_NUMBER)
                return Action(HINT_NUMBER, pnr=i, num=hands[i][j][1])
            if HINT_COLOR in hinttype:
                self.hints[(j,i)].append(HINT_COLOR)
                return Action(HINT_COLOR, pnr=i, col=hands[i][j][0])
            
            playables = playables[1:]
        
        for i, k in enumerate(knowledge):
            if i == nr:
                continue
            cards = list(range(len(k)))
            random.shuffle(cards)
            c = cards[0]
            (col,num) = hands[i][c]            
            hinttype = [HINT_COLOR, HINT_NUMBER]
            if (c,i) not in self.hints:
                self.hints[(c,i)] = []
            for h in self.hints[(c,i)]:
                hinttype.remove(h)
            if hinttype and hints > 0:
                if random.choice(hinttype) == HINT_COLOR:
                    self.hints[(c,i)].append(HINT_COLOR)
                    return Action(HINT_COLOR, pnr=i, col=col)
                else:
                    self.hints[(c,i)].append(HINT_NUMBER)
                    return Action(HINT_NUMBER, pnr=i, num=num)

        return random.choice([Action(DISCARD, cnr=i) for i in range(handsize)])
    def inform(self, action, player, game):
        if action.type in [PLAY, DISCARD]:
            x = str(action)
            if (action.cnr,player) in self.hints:
                self.hints[(action.cnr,player)] = []
            for i in range(10):
                if (action.cnr+i+1,player) in self.hints:
                    self.hints[(action.cnr+i,player)] = self.hints[(action.cnr+i+1,player)]
                    self.hints[(action.cnr+i+1,player)] = []
        elif action.pnr == self.pnr:
            self.gothint = (action,player)
            self.last_knowledge = game.knowledge[:]
            self.last_board = game.board[:]
            self.last_trash = game.trash[:]
            self.played = game.played[:]
            
class FullyIntentionalPlayer(Player):
    def __init__(self, name, pnr):
        self.name = name
        self.hints = {}
        self.pnr = pnr
        self.gothint = None
        self.last_knowledge = []
        self.last_played = []
        self.last_board = []
    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints):
        handsize = len(knowledge[0])
        possible = []        
        
        self.gothint = None
        for k in knowledge[nr]:
            possible.append(get_possible(k))
        
        discards = []
        plays = []
        duplicates = []
        for i,p in enumerate(possible):
            if playable(p,board):
                plays.append(i)
            if discardable(p,board):
                discards.append(i)
            
        playables = []
        useless = []
        discardables = []
        othercards = trash + board
        intentions = [None for i in range(handsize)]
        for i,h in enumerate(hands):
            if i != nr:
                for j,(col,n) in enumerate(h):
                    if board[col][1] + 1 == n:
                        playables.append((i,j))
                        intentions[j] = PLAY
                    if board[col][1] <= n:
                        useless.append((i,j))
                        if not intentions[j]:
                            intentions[j] = DISCARD
                    if n < 5 and (col,n) not in othercards:
                        discardables.append((i,j))
                        if not intentions[j]:
                            intentions[j] = CANDISCARD

        if hints > 0:
            valid = []
            for c in ALL_COLORS:
                action = (HINT_COLOR, c)
                #print "HINT", COLORNAMES[c],
                (isvalid,score) = pretend(action, knowledge[1-nr], intentions, hands[1-nr], board)
                #print isvalid, score
                if isvalid:
                    valid.append((action,score))
            
            for r in range(5):
                r += 1
                action = (HINT_NUMBER, r)
                #print "HINT", r,
                (isvalid,score) = pretend(action, knowledge[1-nr], intentions, hands[1-nr], board)
                #print isvalid, score
                if isvalid:
                    valid.append((action,score))
            if valid:
                valid.sort(key=lambda a_s6: -a_s6[1])
                #print valid
                (a,s) = valid[0]
                if a[0] == HINT_COLOR:
                    return Action(HINT_COLOR, pnr=1-nr, col=a[1])
                else:
                    return Action(HINT_NUMBER, pnr=1-nr, num=a[1])
            
        
        for i, k in enumerate(knowledge):
            if i == nr or True:
                continue
            cards = list(range(len(k)))
            random.shuffle(cards)
            c = cards[0]
            (col,num) = hands[i][c]            
            hinttype = [HINT_COLOR, HINT_NUMBER]
            if (c,i) not in self.hints:
                self.hints[(c,i)] = []
            for h in self.hints[(c,i)]:
                hinttype.remove(h)
            if hinttype and hints > 0:
                if random.choice(hinttype) == HINT_COLOR:
                    self.hints[(c,i)].append(HINT_COLOR)
                    return Action(HINT_COLOR, pnr=i, col=col)
                else:
                    self.hints[(c,i)].append(HINT_NUMBER)
                    return Action(HINT_NUMBER, pnr=i, num=num)

        return random.choice([Action(DISCARD, cnr=i) for i in range(handsize)])
    def inform(self, action, player, game):
        if action.type in [PLAY, DISCARD]:
            x = str(action)
            if (action.cnr,player) in self.hints:
                self.hints[(action.cnr,player)] = []
            for i in range(10):
                if (action.cnr+i+1,player) in self.hints:
                    self.hints[(action.cnr+i,player)] = self.hints[(action.cnr+i+1,player)]
                    self.hints[(action.cnr+i+1,player)] = []
        elif action.pnr == self.pnr:
            self.gothint = (action,player)
            self.last_knowledge = game.knowledge[:]
            self.last_board = game.board[:]
            self.last_trash = game.trash[:]
            self.played = game.played[:]
        
def format_card(xxx_todo_changeme15):
    (col,num) = xxx_todo_changeme15
    return COLORNAMES[col] + " " + str(num)
        
def format_hand(hand):
    return ", ".join(map(format_card, hand))
    

class ProbabilisticPlayer (Player):
    def __init__(self, name, pnr, w_p=0.3, w_i=0.3, w_u=0.5, greedy=0.6):
        self.name = name
        self.hints = {}
        self.pnr = pnr
        self.gothint = None
        self.last_knowledge = []
        self.last_played = []
        self.last_board = [(c, 0) for c in ALL_COLORS]
        self.playable_cards = [[col, 0] for col in ALL_COLORS]
        self.hits = 3
        
        self.probability_threshold = { #dictionary of {number_of_hits_left: minimum_probability} ~ if we want to play a card we need to be at least mp sure that it is correct
            3: 0.5,
            2: 0.6,
            1: 0.9,
        }
        
        self.w_playable = w_p
        self.w_important = w_i
        self.w_unusable = w_u
        
        
        self.base_greedy = self.greedy = 0.6 #The probability of the AI being greedy with last hint

    def get_action(self, nr, hands, knowledge, trash, played, board, valid_actions, hints):
        
        """
        Determines the best action for the AI to take, it evaluates the following actions:
         1. **Playing a card**: If the probability of a card in hand being playable is above a certain threshold based on the number of mistakes made in the game so far, it will play that card
         2. **Giving a hint**: If a hint is available, and there is a hint that would help the player learn more about the cards in their hand, the AI will give that hint
         3. **Discarding a card**: The AI calculates a utility value for each card in hand and discards the card with the lowest value

        Args: explained by yawgmoth in the README.md file
        
        Returns:
            Action: the action the AI has decided to take.
        """
        # knowledge already filters out based on hints given, we want to further filter out by removing any cards we know it cannot be
        # i.e. cards in the opponents hand, cards already played, and cards in the trash
        
        updated_hand_knowledge = self.update_hand_knowledge(knowledge[nr], trash, played, hands)
        self.update_playable_cards(board)
        playable_cards = self.get_target_cards_filter(self.playable_cards)
    
        #possible play actions
        card_to_play = self.card_to_play(updated_hand_knowledge, playable_cards)
        if card_to_play > -1:
            return Action(PLAY, cnr=card_to_play)

        usable_cards = self.get_usable_cards(board)
        unusable_cards = self.get_unusable_cards(usable_cards, trash)
        important_cards = self.get_important_cards(usable_cards, unusable_cards, trash)
           
        if hints > 0:
            for hint in self.card_to_hint(hints, hands, knowledge, board, unusable_cards, important_cards):
                if hint is not None:
                    return hint
                       
        #substract 1 from the second value so that the number aligns with 0 indexing
        played_cards = np.array([(col, num - 1) for (col, num) in played], dtype=int).reshape(-1, 2) #While unlikely to be necessary, this ensures that if the list is empty, it will still be treated as an np.array of the correct shape(N rows, each with 2 columns representing colour, rank)       
        unusable_cards[:, 1] -= 1
        targets_to_discard = np.vstack((played_cards, unusable_cards)) #We can freely discard played cards since there is no stack to place them on

        important_cards[:, 1] -= 1
        
        card_to_discard = self.find_lowest_utility_card(hand_knowledge=updated_hand_knowledge, 
                                                        playable_cards=self.playable_cards, 
                                                        important_cards=important_cards, 
                                                        unusable_cards=targets_to_discard)
            
        return Action(DISCARD, cnr=card_to_discard)

    def update_playable_cards(self, board):
        """
        Updates which cards are immediately playable
        
        Args:
            board (list): shows the top most card for each colour, (col, 0) if no card has been played on that pile
        """
        for i, (col, num) in enumerate(board):
            self.playable_cards[i] = [col, 4] if num == 5 else [col, num] #this is to store which cards are playable as indexes for a numpy array. if a stack of colours is complete, then we simply keep the playable as [col, 4] since that would refer to a card with (col, 5) because of 0-indexing. and since there is only 1 copy of each (col, 5), it should theoretically never cause a problem. 
    
        
    def get_target_cards_filter(self, target_cards):
        """
        A helper function that takes a list/array of tuples (cards) and splits them into 2 lists one representing the colour of each card, and the other representing its rank
        Mainly used for easy indexing with numpy arrays 

        Args:
            target_cards (list-like[(int, int)]): A list of tuples (col, rank), is usually a numpy array

        Returns:
            col_ind: list of each cards colour in target_cards
            rank_ind: list of each cards rank in target_cards
        """
        if len(target_cards) == 0:
            return [], []
        col_ind, rank_ind = zip(*target_cards)
        return col_ind, rank_ind    
    
    def update_hand_knowledge(self, hand_knowledge, trash, played, hands):
        """
        Uses the list of cards that:
          - In the trash
          - Have been successfully played
          - In each other players hand
        
        To update the knowledge the AI player has about their own hand

        Args:
            hand_knowledge (list[list[int]]): knowledge[nr] (see README.md)
            trash (list[(int, int)]): List of cards that are in the trash
            played (list[(int, int)]): List of cards that have been successfully played
            hands (list[list[(int, int)]]): list of cards that each player has where hands[nr] 

        Returns:
            np.ndarray[np.ndarray[int]]: the updated hand knowledge returned as a numpy array
        """
        used_cards = trash + played + [card for hand in hands for card in hand]
        card_counts = Counter(used_cards)
        used = dict(card_counts)
        return np.array(update_knowledge(hand_knowledge, used))

    def card_to_play(self, hand_knowledge, playable):
        """
        Using the AIs knowledge of their hand, calculates which cards have the highest probability of being playable and returns it if the probability of being playable is equal to or higher than the probability threshold

        Args:
            hand_knowledge (np.ndarray[np.ndarray[int]]): the AIs knowledge of their own hand
            playable (list[int], list[int]): 2 lists representing the colours of each playable card and the rank of each playable card, used for numpy array indexing. col[int],rank[int]

        Raises:
            ValueError: raised if there is a card with no possible values in hand knowledge. card[col] = [0,0,0,0,0] for each colout

        Returns:
            int: the index of the most likely to be playable card if it is above the probability threshold. Returns -1 if no applicable card
        """
        card_to_play = -1
        p_playable = 0
        for i, card in enumerate(hand_knowledge): #iterate through each card in hand, each card is a col, rank 2d list. divide entire 
            total_number_of_possible_cards = np.sum(card)
            if total_number_of_possible_cards == 0:
                raise ValueError(f"Invalid state: there are no possible values for card {i + 1}. This suggests an error in hand knowledge representation")

            probabilities = card.copy()/total_number_of_possible_cards
            probability_of_playable = np.sum(probabilities[playable])
            
            if probability_of_playable > p_playable and probability_of_playable >= self.probability_threshold[self.hits]:
                card_to_play = i
                p_playable = probability_of_playable
        return card_to_play
        
    def card_to_hint(self, hints, hands, knowledge, board, unusable, important):
        """
        A helper function that calls each hint-finding function and yields the result

        Args:
            hints (int): number of hints left
            hands (list[list[tuple(int, int)]]): list of hands each player has
            knowledge (list[list[list[int]]]): see README.md, knowledge structure containing the hands of all players
            board (list[tuple(int, int)]): the current board state
            unusable (np.ndarray[(N,2), dtype=int]): list of cards unusable cards
            important (np.ndarray[(N,2), dtype=int]): list of cards which are usable, and only have 1 copy left in any players hands or deck

        Yields:
            Action: a hint action if a hint can be found for that function, otherwise returns None
        """
        if hints == 1 and np.random.rand() > self.greedy:
            self.greedy = self.base_greedy
            yield None
        else:
            if hints == 1:
                self.greedy *= self.base_greedy
        
            yield self.hint_playable(hands, knowledge)
            yield self.hint_discardable(hands, knowledge, board, unusable)
            yield self.hint_important(hands, knowledge, important)
            yield self.hint_highest_info(hands, knowledge, hints)

    def hint_playable(self, hands, knowledge):
        """
        Hint function that finds a hint that hints towards a playable card if there is one

        Args:
            hands (list[list[tuple(int, int)]]): each players' hands
            knowledge (list[list[list[int]]]): see README.md, knowledge structure containing the hands of all players

        Returns:
            Action: returns a hint action that gives a hint towards a playable card. Returns None if no useful hint is found
        """
        op_playable = self.get_opponents_playable_cards(hands)
        return self.get_best_hint_for_all_opponent(
            target_cards=op_playable,
            hands = hands,
            knowledge=knowledge
        )
        
    def hint_discardable(self, hands, knowledge, board, unusable):
        """
        Hint function that finds a hints towards a discardable card if there is one

        Args:
            hands (list[list[tuple(int, int)]]): each players' hands
            knowledge (list[list[list[int]]]): see README.md, knowledge structure containing the hands of all players
            board (list[tuple(int, int)]): the current board state
            unusable (np.ndarray[(N,2), dtype=int]): list of cards unusable cards

        Returns:
            Action: returns a hint action that gives a hint towards a discardable card. Returns None if no useful hint is found
        """
        op_discardable = self.get_opponents_discardable_cards(hands=hands, board=board, unusable=unusable)
        return self.get_best_hint_for_all_opponent(
            target_cards=op_discardable,
            hands=hands, 
            knowledge=knowledge
            )

    def hint_important(self, hands, knowledge, important_cards):
        """
        Hint function that finds a hints towards an important card if there is one. A card is important if it is still usable but there is only 1 copy of that card left in any players hand or deck

        Args:
            hands (list[list[tuple(int, int)]]): each players' hands
            knowledge (list[list[list[int]]]): see README.md, knowledge structure containing the hands of all players
            unusable (np.ndarray[(N,2), dtype=int]): list of cards important cards

        Returns:
            Action: returns a hint action that gives a hint towards an important card. Returns None if no useful hint is found
        """
        op_important = self.get_opponents_important_cards(hands=hands, important_cards=important_cards)
        return self.get_best_hint_for_all_opponent(
            target_cards=op_important,
            hands=hands,
            knowledge=knowledge
        )
        
    def hint_highest_info(self, hands, knowledge, hints):
        """
        A hint function that gives the hint that will give the player the most information about their hand. If there is only 1 hint, there is a chance for the AI
        to not return a hint as to not be greedy and hoard hints. The chance of not giving a hint increases if the AI does give a highest info hint when only 1 hint is left
        and resets if the AI decides to not give a hint.       
        
        
        Args:
            hands (list[list[tuple(int, int)]]): each players' hands
            knowledge (list[list[list[int]]]): see README.md, knowledge structure containing the hands of all players
            hints (int): number of hints available

        Returns:
            Action: Returns the hint that gives a player the most information about the cards in their hand. Otherwise returns None
        """
        op_cards = self.get_opponents_all_cards(hands=hands)
        return self.get_best_hint_for_all_opponent(
                target_cards=op_cards,
                hands=hands,
                knowledge=knowledge,
            )
    def get_best_hint_for_all_opponent(self, target_cards, hands, knowledge):
        """
        Uses expected information gain from a hint to find the best hint to give.

        Args:
            target_cards (dict{int: list[int]}): dict[int, list[int]]: a (player_number: card_index) dictionary where the card_index refer to the cards that we want to hint about.
            hands (list[list[tuple(int, int)]]): each players' hands
            knowledge (list[list[list[int]]]): see README.md, knowledge structure containing the hands of all players

        Returns:
            Action: a hint that gives the highest information gain 
        """
        best_hint = None
        expected_information_gain = 0
        
        if any(len(card) for card in target_cards.values()):
    
            for pnr, target in target_cards.items():
                hint, eig = self.get_best_hint(np.array(hands[pnr]), np.array(knowledge[pnr]), pnr, target)
                if best_hint is None or eig > expected_information_gain:
                    best_hint = hint
                    expected_information_gain = eig

            if expected_information_gain > 0:
                return best_hint
            else:
                return None

        
    def get_opponents_cards(self, hands, condition):
        """
        Finds for each player's hands, which cards fufill a certain condition

        Args:
            hands (list[list[tuple(int, int)]]): each players' hands
            condition (Callable[[int, int], bool]): A function that takes a cards colour and rank, and returns if that card fulfills the condition 

        Returns:
            dict[int, list[int]]: a (player_number: card_index) dictionary
        """
        op_cards = {}
        for pnr, hand in enumerate(hands):
                if pnr == self.pnr:
                    continue
                op_cards[pnr] = [cnr for cnr, (col, rank) in enumerate(hand) if condition(col, rank)]
                
        
        return op_cards


    def get_opponents_playable_cards(self, hands):
        """
        Finds all cards in each opponents hands that are playable

        Args:
            hands (list[list[tuple(int, int)]]): each players' hands

        Returns:
            dict{int: list[int]}: a (player_number: card_index) dictionary where the card_index refers to the playable cards in that players hand
        """
        return self.get_opponents_cards(hands, lambda col, rank: [col, rank - 1] in self.playable_cards)

    def get_opponents_discardable_cards(self, hands, board, unusable):
        """
        Finds all cards in each opponents hands that are discardable

        Args:
            hands (list[list[tuple(int, int)]]): each players' hands

        Returns:
            dict{int: list[int]}: a (player_number: card_index) dictionary where the card_index refers to the discardable cards in that players hand
        """
        return self.get_opponents_cards(hands, lambda col, rank: board[col][1] >= rank or np.any(np.all(unusable == (col, rank), axis=1)))

    def get_opponents_all_cards(self, hands):
        """
        Finds all cards in each opponents hands, used for highest info hints

        Args:
            hands (list[list[tuple(int, int)]]): each players' hands

        Returns:
            dict{int: list[int]}: a (player_number: card_index) dictionary 
        """
        return self.get_opponents_cards(hands, lambda col, rank: True)
    
    def get_opponents_important_cards(self, hands, important_cards):
        """
        Finds all cards in each opponents hands that are important, i.e. they are usable and there is only one left that isn't in trash

        Args:
            hands (list[list[tuple(int, int)]]): each players' hands

        Returns:
            dict{int: list[int]}: a (player_number: card_index) dictionary where the card_index refers to the playable cards in that players hand
        """
        return self.get_opponents_cards(hands, lambda col, rank: np.any(np.all(important_cards == (col, rank), axis= 1)))
    


    def entropy(self, probability_distribution):
        """
        Calculates the entropy of a probability distribution through the Shannon entropy formula:
                        entropy = -Σp(x)log2(x)

        Args:
            probability_distribution (np.ndarray[float]): a 2d array representing the probability distribution a card can have. Can be used on higher dimensional arrays if necessary

        Returns:
            float: entropy
        """
        probability_distribution = probability_distribution[probability_distribution > 0]
        return -np.sum(probability_distribution * np.log2(probability_distribution))
        
    def information_gain(self, prob_dist_before, prob_dist_after):
        """
        Converts 2 probability distributions into entropy and finds the change in entropy by calculating entropy_before - entropy_after

        Args:
            prob_dist_before (np.ndarray(float)): probability distribution of a card before a hint was given
            prob_dist_after (np.ndarray(float)): probability distribution of a card after a hint was given, presumably of the same shape as probability distribution before.

        Returns:
            float: change in entropy
        """
        return self.entropy(prob_dist_before) - self.entropy(prob_dist_after)
            
    def get_best_hint(self, hand, knowledge, pnr, target):
        """
        for a given card in a given players hand, simulate both the colour hint and the number hint and find the hint that gives the highest information gain

        Args:
            hand (list[tuple(int, int)]): player pnr's hand
            knowledge (list[list[int]]]): see README.md, knowledge structure containing the hands of a single player
            pnr (int): player number
            target (list[ind]): list of target card indexes in pnr's hand

        Returns:
            (Action, float): returns both the best hint for that card as well as the information gain of that hint
        """
        targets_in_hand = hand[target]    
        possible_colour_hints = np.unique(targets_in_hand[:, 0])
        possible_rank_hints = np.unique(targets_in_hand[:, 1])

        possible_hints = [Action(type=HINT_COLOR, pnr=pnr, col=col) for col in possible_colour_hints] + [Action(type=HINT_NUMBER, pnr=pnr, num=num) for num in possible_rank_hints]
        info_gain = np.zeros(len(possible_hints))
        for i, hint in enumerate(possible_hints):
            prob_dist_before_hint = self.calculate_prob_dist(knowledge)
            knowledge_after_hint = self.simulate_hint(hand, knowledge, hint)
            prob_dist_after_hint = self.calculate_prob_dist(knowledge_after_hint)

            info_gain[i] = self.calculate_net_info_gain(prob_dist_before_hint, prob_dist_after_hint, target)
            
        best = np.argmax(info_gain)
        return (possible_hints[best], info_gain[best])
    
    def calculate_prob_dist(self, knowledge):
        """
        Calculates the probability distribution of each card in a players hand.

        Args:
            knowledge (list[list[int]]]): see README.md, knowledge structure containing the hands of a single player

        Returns:
            np.ndarray[[float]]: a 2d np.array of the probability distributions. of the same shape as knowledge
        """
        return np.array([
            card_dist/np.sum(card_dist) if np.sum(card_dist) > 0 else np.zeros_like(card_dist) 
            for card_dist in knowledge
            ])
                
    def simulate_hint(self, hand, knowledge, hint):
        """
        A helper function that calls other simulate hint functions that simulate either a colour hint or a rank hint

        Args:
            hand (list[tuple(int, int)]): player pnr's hand
            knowledge (list[list[int]]]): see README.md, knowledge structure containing the hands of a single player
            hint (Action): a given hint

        Returns:
            np.ndarray([float]): an updated knowledge after the hint has been simulated. same shape as knowledge
        """
        if hint.type == HINT_COLOR:
            return self.simulate_colour_hint(hand, knowledge, hint.col)
        else:
            return self.simulate_rank_hint(hand, knowledge, hint.num)
    
    def simulate_colour_hint(self, hand, knowledge, col):
        """
        Simulates hinting a specific colour to a player

        Args:
            hand (list[tuple(int, int)]): player pnr's hand
            knowledge (list[list[int]]]): see README.md, knowledge structure containing the hands of a single player
            col (int): a number representing a colour

        Returns:
            np.ndarray([float]): an updated knowledge after the colour hint has been simulated. same shape as knowledge
        """
        post_hint_knowledge = knowledge.copy()
        matching_colour_indexes = np.array([card[0] == col for card in hand])

        post_hint_knowledge[matching_colour_indexes] = 0
        post_hint_knowledge[matching_colour_indexes, col] = knowledge[matching_colour_indexes, col]
        post_hint_knowledge[~matching_colour_indexes, col] = 0

        return post_hint_knowledge
            
    def simulate_rank_hint(self, hand, knowledge, num):
        """
        Simulates hinting a specific rank to a player

        Args:
            hand (list[tuple(int, int)]): player pnr's hand
            knowledge (list[list[int]]]): see README.md, knowledge structure containing the hands of a single player
            num (int): a cards rank to be hinted

        Returns:
            np.ndarray([float]): an updated knowledge after the number hint has been simulated. same shape as knowledge
        """
        post_hint_knowledge = knowledge.copy()
        matching_number_indexes = np.array([card[1] == num for card in hand])
        
        post_hint_knowledge[matching_number_indexes] = 0 
        post_hint_knowledge[matching_number_indexes, :, num - 1] = knowledge[matching_number_indexes, :, num -1]
        post_hint_knowledge[~matching_number_indexes, :, num - 1] = 0
        
        return post_hint_knowledge 
    
    def calculate_net_info_gain(self, before_dist, after_dist, target_indexes, lamda_weight=0.9):
        """
        Calculates the information gain of each card, while also demeriting informatin gain on non_playable cards

        Args:
            before_dist (np.ndarray[[float]]): probability distribution before a hint is given
            after_dist (np.ndarray[[float]]): probability distribution after a hint is given 
            target_indexes (list[int]): a list of cards that are the targets for our hint
            lamda_weight (float, optional): weighting used to control the trade-off between information gain on important cards vs information gain on non-important cards. Defaults to 0.9.

        Returns:
            float: the net information gain
        """
        info_gain_targets = info_gain_non_targets = 0
        for i, (b_dist, a_dist) in enumerate(zip(before_dist, after_dist)):
            info_gain = self.information_gain(b_dist, a_dist)
            if i in target_indexes:
                info_gain_targets += info_gain
            else:
                info_gain_non_targets += info_gain
        
        return (lamda_weight * info_gain_targets - (1-lamda_weight) * info_gain_non_targets)
     
    def get_usable_cards(self, board):
        """
        Finds all the cards that are still usable based on the board.
        NOTE: a usable card is not necessarily immediately playable but will still need to be used at some point in the future 

        Args:
            board (list[tuple(int, int)]): the current board state

        Returns:
            np.ndarray[[int, int]]: A numpy array of cards that are still usable
        """
        return np.array([(col, i) for (col, rank) in board for i in range(rank + 1, 6)], dtype=int)

    
    def get_unusable_cards(self, usable, trash):
        """
        Finds which cards that are unusable. It does this by finding any card who has all its copies in the trash and adds every card of that colour with a higher rank to the unusable list
        Because this is used to hint which cards to discard/which cards are most likely to be discardable, we don't need to add cards that are already all in the trash to the list as those will already be impossible to have in hand

        Args:
            usable (np.ndarry[[int, int]]): list of usable cards
            trash (list[tuple(int, int)]): list of cards that are in the trash

        Returns:
            np.ndarray[[int, int]] - numpy array of cards that are unusable
        """
        if len(trash) == 0:
            return np.empty((0,2), dtype=int)
        unique_cards, count_cards = np.unique(trash, return_counts=True, axis=0)
        
        count_cards_left = np.array([COUNTS[num - 1] for (_, num) in unique_cards]) - count_cards
        none_left_in_deck = unique_cards[count_cards_left == 0]
        if len(none_left_in_deck) == 0:
            return np.empty((0,2), dtype=int)
        
        unusable_by_extension_mask = np.any(
            (usable[:, None, 0] == none_left_in_deck[:, 0]) &
            (usable[:, None, 1] > none_left_in_deck[:, 1]),
            axis=1
        )
        return usable[unusable_by_extension_mask]
    
    def remove_unusable_from_usable(self, usable, unusable):
        """
        Takes an array of usable cards and an array of unusable cards and returns the cards in the usable array that are not in the unusable array

        Args:
            usable (np.ndarry[[int, int]]): array of usable cards
            unusable (np.ndarry[[int, int]]): array of unusable cards

        Returns:
            np.ndarry[[int, int]]: usable - unusable
        """
        usable_set = {tuple(card) for card in usable}
        unusable_set = {tuple(card) for card in unusable}
        set_diff = usable_set - unusable_set
        return np.array([list(card) for card in set_diff]) if set_diff else np.empty((0, usable.shape[1]))

    def get_important_cards(self, usable, unusable, trash):
        """
        Takes an array of usable cards, unusable cards and a list of cards in the trash to find which cards have only a single copy left in any players hand/deck, is in the usable array and not in the unusable array 

        Args:
            usable (np.ndarry[[int, int]]): array of usable cards
            unusable (np.ndarry[[int, int]]): array of unusable cards
            trash (_type_): _description_

        Returns:
            np.ndarry[[int, int]]: array of important cards
        """
        usable =  self.remove_unusable_from_usable(usable, unusable)#a card isn't considered important if they are cannot be played at all even if there is only 1 of it left.
        
        count_cards_left = np.array([COUNTS[num - 1] for (_, num) in usable])
        if len(trash) > 0:
            unique_cards, count_cards = np.unique(trash, return_counts=True, axis=0)           
            for i, card in enumerate(usable):
                index_match = np.where((unique_cards == card).all(axis=1))[0]
                if index_match.size > 0:
                    count_cards_left[i] -= count_cards[index_match[0]]
        
        return usable[count_cards_left == 1]

    def find_lowest_utility_card(self, hand_knowledge, playable_cards, important_cards, unusable_cards):
        """
        Iterates through each card in hand_knowledge and calculates the utility value of that card

        Args:
            hand_knowledge (np.ndarray[[int]]]): see README.md, knowledge structure containing the hands of a single player
            playable_cards (list[tuple(int, int)]): a list of playable cards
            important_cards (np.ndarray[[int, int]]): a numpy array of important cards
            unusable_cards (np.ndarray): a numpy array of cards of unusable cards

        Returns:
            int: the index of the card in hand with the lowest utility
        """
        hand_utilities = np.zeros(len(hand_knowledge)) 
        for i, card in enumerate(hand_knowledge):
            uv = self.find_utility_value(card, playable_cards, important_cards, unusable_cards, i)
            hand_utilities[i] = uv
        
        return np.argmin(hand_utilities)
    
    def find_utility_value(self, card, playable_cards, important_cards, unusable_cards, ind):
        """
        Uses the probability of a card being playable, being important and being unusable to calculate the utility value of that card. Each property is weighted as such:
            - Playable: 0.3
            - Important: 0.3
            - Unusable: 0.5

        Args:
            card (np.ndarray[[int]]): knowledge structure for a single card in hand
            playable_cards (list[tuple(int, int)]): a list of playable cards
            important_cards (np.ndarray[[int, int]]): a numpy array of important cards
            unusable_cards (np.ndarray): a numpy array of cards of unusable cards
            ind (int): index of card

        Raises:
            ValueError: raises an error if there is no possible (col, rank) to assign to the card, i.e. np.sum(card) == 0

        Returns:
            float: the utility value of the card
        """
        number_of_possibilities = np.sum(card)
        if number_of_possibilities == 0:
            raise ValueError(f"Invalid state: there are no possible values for card {ind + 1}. This suggests an error in hand knowledge representation")
        
        probabilities = card.copy()/number_of_possibilities
        p_c = self.get_target_cards_filter(playable_cards)
        i_c = self.get_target_cards_filter(important_cards)
        u_c = self.get_target_cards_filter(unusable_cards)
        
        return np.sum(probabilities[p_c]) * self.w_playable + np.sum(probabilities[i_c]) * self.w_important - np.sum(probabilities[u_c]) * self.w_unusable  
        

    def inform(self, action, player, game):
        """
        Overriden function from the Player Parent class.
        Updates the AI's internal state based on an action taken in the game.
        If a card has been discarded, clears hint information about that card and shifts subsequent cards forward
        If a card is hinted, stores the hint action and player who gave it in
        Saves snapshot of game state before acting on the hint, including:
            - board state ('self.last_board')
            - trash pile ('self.last_trash')
            - played cards ('self.played')

        Args:
            action (Action): The action that was taken, which could be a play, discard, or hint.
            player (int): The player who took the action.
            game (Game): The current state of the game, including hits, knowledge, board, and trash.

        """
        self.hits = game.hits
        if action.type in [PLAY, DISCARD]:
            x = str(action)
            if (action.cnr,player) in self.hints:
                self.hints[(action.cnr,player)] = []
            for i in range(10):
                if (action.cnr+i+1,player) in self.hints:
                    self.hints[(action.cnr+i,player)] = self.hints[(action.cnr+i+1,player)]
                    self.hints[(action.cnr+i+1,player)] = []
        elif action.pnr == self.pnr:
            self.gothint = (action,player)
            self.last_knowledge = game.knowledge[:]
            self.last_board = game.board[:]
            self.last_trash = game.trash[:]
            self.played = game.played[:]

    
    
class Game(object):
    
    def __init__(self, players, log=sys.stdout, format=0):
        self.players = players
        self.hits = 3
        self.hints = 8
        self.current_player = 0
        self.board = [(c,0) for c in ALL_COLORS]
        self.played = []
        self.deck = make_deck()
        self.extra_turns = 0
        self.hands = []
        self.knowledge = []
        self.make_hands()
        self.trash = []
        self.log = log
        self.turn = 1
        self.format = format
        self.dopostsurvey = False
        self.study = False
        if self.format:
            print(self.deck, file=self.log)
    def make_hands(self):
        handsize = 4
        if len(self.players) < 4:
            handsize = 5
        for i, p in enumerate(self.players):
            self.hands.append([])
            self.knowledge.append([])
            for j in range(handsize):
                self.draw_card(i)
    def draw_card(self, pnr=None):
        if pnr is None:
            pnr = self.current_player
        if not self.deck:
            return
        self.hands[pnr].append(self.deck[0])
        self.knowledge[pnr].append(initial_knowledge())
        del self.deck[0]
    def perform(self, action):
        for p in self.players:
            p.inform(action, self.current_player, self)
        if format:
            print("MOVE:", self.current_player, action.type, action.cnr, action.pnr, action.col, action.num, file=self.log)
        if action.type == HINT_COLOR:
            self.hints -= 1
            print(self.players[self.current_player].name, "hints", self.players[action.pnr].name, "about all their", COLORNAMES[action.col], "cards", "hints remaining:", self.hints, file=self.log)
            print(self.players[action.pnr].name, "has", format_hand(self.hands[action.pnr]), file=self.log)
            for (col,num),knowledge in zip(self.hands[action.pnr],self.knowledge[action.pnr]):
                if col == action.col:
                    for i, k in enumerate(knowledge):
                        if i != col:
                            for i in range(len(k)):
                                k[i] = 0
                else:
                    for i in range(len(knowledge[action.col])):
                        knowledge[action.col][i] = 0
        elif action.type == HINT_NUMBER:
            self.hints -= 1
            print(self.players[self.current_player].name, "hints", self.players[action.pnr].name, "about all their", action.num, "hints remaining:", self.hints, file=self.log)
            print(self.players[action.pnr].name, "has", format_hand(self.hands[action.pnr]), file=self.log)
            for (col,num),knowledge in zip(self.hands[action.pnr],self.knowledge[action.pnr]):
                if num == action.num:
                    for k in knowledge:
                        for i in range(len(COUNTS)):
                            if i+1 != num:
                                k[i] = 0
                else:
                    for k in knowledge:
                        k[action.num-1] = 0
        elif action.type == PLAY:
            (col,num) = self.hands[self.current_player][action.cnr]
            print(self.players[self.current_player].name, "plays", format_card((col,num)), end=' ', file=self.log)
            if self.board[col][1] == num-1:
                self.board[col] = (col,num)
                self.played.append((col,num))
                if num == 5:
                    self.hints += 1
                    self.hints = min(self.hints, 8)
                print("successfully! Board is now", format_hand(self.board), file=self.log)
            else:
                self.trash.append((col,num))
                self.hits -= 1
                print("and fails. Board was", format_hand(self.board), file=self.log)
            del self.hands[self.current_player][action.cnr]
            del self.knowledge[self.current_player][action.cnr]
            self.draw_card()
            print(self.players[self.current_player].name, "now has", format_hand(self.hands[self.current_player]), file=self.log)
        else:
            self.hints += 1 
            self.hints = min(self.hints, 8)
            self.trash.append(self.hands[self.current_player][action.cnr])
            print(self.players[self.current_player].name, "discards", format_card(self.hands[self.current_player][action.cnr]), file=self.log)
            print("trash is now", format_hand(self.trash), file=self.log)
            del self.hands[self.current_player][action.cnr]
            del self.knowledge[self.current_player][action.cnr]
            self.draw_card()
            print(self.players[self.current_player].name, "now has", format_hand(self.hands[self.current_player]), file=self.log)
    def valid_actions(self):
        valid = []
        for i in range(len(self.hands[self.current_player])):
            valid.append(Action(PLAY, cnr=i))
            valid.append(Action(DISCARD, cnr=i))
        if self.hints > 0:
            for i, p in enumerate(self.players):
                if i != self.current_player:
                    for col in set([col_num[0] for col_num in self.hands[i]]):
                        valid.append(Action(HINT_COLOR, pnr=i, col=col))
                    for num in set([col_num1[1] for col_num1 in self.hands[i]]):
                        valid.append(Action(HINT_NUMBER, pnr=i, num=num))
        return valid
    def run(self, turns=-1):
        self.turn = 1
        while not self.done() and (turns < 0 or self.turn < turns):
            self.turn += 1
            if not self.deck:
                self.extra_turns += 1
            hands = []
            for i, h in enumerate(self.hands):
                if i == self.current_player:
                    hands.append([])
                else:
                    hands.append(h)
            action = self.players[self.current_player].get_action(self.current_player, hands, self.knowledge, self.trash, self.played, self.board, self.valid_actions(), self.hints)
            self.perform(action)
            self.current_player += 1
            self.current_player %= len(self.players)
        print("Game done, hits left:", self.hits, file=self.log)
        points = self.score()
        print("Points:", points, file=self.log)
        return points
    def score(self):
        return sum([col_num8[1] for col_num8 in self.board])
    def single_turn(self):
        if not self.done():
            if not self.deck:
                self.extra_turns += 1
            hands = []
            for i, h in enumerate(self.hands):
                if i == self.current_player:
                    hands.append([])
                else:
                    hands.append(h)
            action = self.players[self.current_player].get_action(self.current_player, hands, self.knowledge, self.trash, self.played, self.board, self.valid_actions(), self.hints)
            self.perform(action)
            self.current_player += 1
            self.current_player %= len(self.players)
    def external_turn(self, action): 
        if not self.done():
            if not self.deck:
                self.extra_turns += 1
            self.perform(action)
            self.current_player += 1
            self.current_player %= len(self.players)
    def done(self):
        if self.extra_turns == len(self.players) or self.hits == 0:
            return True
        for (col,num) in self.board:
            if num != 5:
                return False
        return True
    def finish(self):
        if self.format:
            print("Score", self.score(), file=self.log)
            self.log.close()
        
    
class NullStream(object):
    def write(self, *args):
        pass
        
random.seed(123)

playertypes = {"random": Player, "inner": InnerStatePlayer, "outer": OuterStatePlayer, "self": SelfRecognitionPlayer, "intentional": IntentionalPlayer, "sample": SamplingRecognitionPlayer, "full": SelfIntentionalPlayer, "timed": TimedPlayer, "prob": ProbabilisticPlayer}
names = ["Shangdi", "Yu Di", "Tian", "Nu Wa", "Pangu"]
        
        
def make_player(player, i):
    if player in playertypes:
        return playertypes[player](names[i], i)
    elif player.startswith("self("):
        other = player[5:-1]
        return SelfRecognitionPlayer(names[i], i, playertypes[other])
    elif player.startswith("sample("):
        other = player[7:-1]
        if "," in other:
            othername, maxtime = other.split(",")
            othername = othername.strip()
            maxtime = int(maxtime.strip())
            return SamplingRecognitionPlayer(names[i], i, playertypes[othername], maxtime=maxtime)
        return SamplingRecognitionPlayer(names[i], i, playertypes[other])
    return None 
    
def main(args):
    if not args:
        args = ["random"]*3
    if args[0] == "trial":
        treatments = [["intentional", "intentional"], ["intentional", "outer"], ["outer", "outer"]]
        #[["sample(intentional, 50)", "sample(intentional, 50)"], ["sample(intentional, 100)", "sample(intentional, 100)"]] #, ["self(intentional)", "self(intentional)"], ["self", "self"]]
        results = []
        print(treatments)
        for i in range(int(args[1])):
            result = []
            times = []
            avgtimes = []
            print("trial", i+1)
            for t in treatments:
                random.seed(i)
                players = []
                for i,player in enumerate(t):
                    players.append(make_player(player,i))
                g = Game(players, NullStream())
                t0 = time.time()
                result.append(g.run())
                times.append(time.time() - t0)
                avgtimes.append(times[-1]*1.0/g.turn)
                print(".", end=' ')
            print()
            print("scores:",result)
            print("times:", times)
            print("avg times:", avgtimes)
        
        return
        
        
    players = []
    
    for i,a in enumerate(args):
        players.append(make_player(a, i))
        
    n = 10000
    out = NullStream()
    if n < 3:
        out = sys.stdout
    pts = []
    for i in range(n):
        if (i+1)%100 == 0:
            print("Starting game", i+1)
        random.seed(i+1)
        g = Game(players, out)
        try:
            pts.append(g.run())
            if (i+1)%100 == 0:
                print("score", pts[-1])
        except Exception:
            import traceback
            traceback.print_exc()
    if n < 10:
        print(pts)
    import numpy
    print("average:", numpy.mean(pts))
    print("stddev:", numpy.std(pts, ddof=1))
    print("range", min(pts), max(pts))
    
    
if __name__ == "__main__":
    main(sys.argv[1:])