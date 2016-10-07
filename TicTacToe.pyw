"""
Tic-Tac-Toe
Compatible Python 2 and Python 3
"""

try:
    # Python 2
    from Tkinter import *
    import tkMessageBox as messagebox
    from ConfigParser import ConfigParser
except ImportError:
    # Python 3
    from tkinter import *
    from configparser import ConfigParser
from PIL import Image, ImageTk
from math import sqrt
from time import time, sleep
from random import shuffle
from os import path
try:
    from pyglet import media
    SOUND = True
except ImportError:
    media = None
    SOUND = False

# Parametrization - BEGIN
# (these constants can be changed)
PLAYER = 'X'              # player is X or O
COLOR_X = 'blue'          # color for X
COLOR_O = 'blue'          # color for O
COLOR_X_PLAY = '#0099FF'  # recent move color for X
COLOR_O_PLAY = '#0099FF'  # recent move color for O
COLOR_WIN = 'green'       # color for winning line
TIME_COLOR = 500          # time to display recent move color in millisecond
TIME_END = 1500           # time to display end game board before restarting in millisecond
# Parametrization - END

assert PLAYER == 'X' or PLAYER == 'O'
assert TIME_COLOR < TIME_END
COMPUTER = 'X' if PLAYER == 'O' else 'O'
TIME_COLOR_S = TIME_COLOR / 1000.
TIME_END_S = TIME_END / 1000.
EMPTY = '.'                     # empty square on the board
COMPUTER_TURN = 'Computer'      # computer's turn to play
PLAYER_TURN = 'Player'          # player's turn to play
CONFIG_FILE = 'TicTacToe.ini'   # configuration file, created automatically if necessary
CONFIG_SECTION = 'Tic-Tac-Toe'  # header in configuration file
BACKGROUND = 'TicTacToe.png'    # background image (9 squares)
SIZE = 600                      # actual size of the square background image (in pixel)
MARGIN = SIZE / 25              # [=24] margin from edges of each square to draw X and O

"""
SQUARE is associated with the BACKGROUND picture
each line = [TopLeft_X, TopLeft_Y, BottomRight_X, BottomRight_Y] of the corresponding square
|---|---|---|
| 0 | 1 | 2 |
|---|---|---|
| 3 | 4 | 5 |
|---|---|---|
| 6 | 7 | 8 |
|---|---|---|
"""
SQUARE = [[0, 0, 189, 189],      # square 0
          [205, 0, 394, 189],    # square 1
          [410, 0, 599, 189],    # square 2
          [0, 205, 189, 394],    # square 3
          [205, 205, 394, 394],  # square 4
          [410, 205, 599, 394],  # square 5
          [0, 410, 189, 599],    # square 6
          [205, 410, 394, 599],  # square 7
          [410, 410, 599, 599]]  # square 8

# if a .MP3 file doesn't exist, corresponding sound will no be played
SOUND = {}
SOUND['start']= SOUND and path.exists('shall_we_play_a_game.mp3')
SOUND['beep'] = SOUND and path.exists('computer_error.mp3')
SOUND['computer turn'] = SOUND and path.exists('bike_horn.mp3')
SOUND['computer wins 1'] = SOUND and path.exists('pig_snort.ogg')
SOUND['computer wins 2'] = SOUND and path.exists('evil_laugh.mp3')
SOUND['player wins'] = SOUND and path.exists('nice_one.mp3')
SOUND['nobody wins'] = SOUND and path.exists('cow_moo.mp3')
SOUND['move'] = SOUND and path.exists('punch_or_whack.mp3')


WIN = [[0, 1, 2], [3, 4, 5], [6, 7, 8],   # 3 horizontals
       [0, 3, 6], [1, 4, 7], [2, 5, 8],   # 3 verticals
       [0, 4, 8], [2, 4, 6]]              # 2 diagonals


def win(gameBoard):
    """
    return: set([])                if game is not finished
            set([-1]) = {-1}       if game is tie
            set([winning squares]) if game is won
    """
    board = set([])
    for x in WIN:
        if (gameBoard[x[0]] != EMPTY and
                gameBoard[x[0]] == gameBoard[x[1]] and
                gameBoard[x[0]] == gameBoard[x[2]]):
            board.update(x)
    if board == set([]):
        if EMPTY not in gameBoard:
            board = {-1}
    return board

def whichMove(move):
    # move is a list of [[move, score of move], ...]
    # return a random element move with same score as the first score in the list
    same = [x[0] for x in move if x[1] == move[0][1]]
    shuffle(same)
    return same[0]


class Game(Frame):

    def readConfig(self):
        try:
            config = ConfigParser()
            config.read(CONFIG_FILE)
            self.sound = config.getboolean(CONFIG_SECTION, 'sound')
            self.level = config.getint(CONFIG_SECTION, 'level')
        except:
            self.sound = True
            self.level = 0
        return

    def writeConfig(self):
        config = ConfigParser()
        config.add_section(CONFIG_SECTION)
        config.set(CONFIG_SECTION, 'sound', str(self.sound))
        config.set(CONFIG_SECTION, 'level', str(self.level))
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
        return

    def __init__(self, root):
        Frame.__init__(self, root)
        self.root = root
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.original = Image.open(BACKGROUND)
        self.image = ImageTk.PhotoImage(self.original)
        self.width = self.original.size[0]
        self.height = self.original.size[1]
        self.display = Canvas(self, width=self.width, height=self.height)
        self.display.create_image(0, 0, image=self.image, anchor=NW, tags='IMG')
        self.display.grid(row=0, sticky=W+E+N+S)
        self.pack(fill=BOTH, expand=1)
        self.root.focus_set()
        self.root.bind('<Escape>', self.on_closing)  # ESC closes the program
        self.root.bind('<Button-1>', self.onMouse)   # any mouse click
        self.root.bind('<Configure>', self.resize)   # any resize of window
        self.root.bind('<Key>', self.keyboard)       # any key pressed
        self.turn = PLAYER_TURN
        self.next = PLAYER_TURN
        self.scorePlayer = 0
        self.scoreComputer = 0
        self.sound = True
        self.level = 0
        self.squareContent = []
        self.lastSquarePlayed = -1
        self.winner = set([])
        self.winStatus = ''
        self.readConfig()
        self.initialization()
        self.draw(False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
        return

    def on_closing(self, event=None):
        # called by pressing ESC -> event parameter is given
        # called by Window Manager -> none
        if messagebox.askokcancel("Tic-Tac-Toe", "Do you want to quit?"):
            # Note: self.root.destroy() may produce error
            # in PyCharm environment because of unfinished self.root.update()
            # of self.root.update_idletasks() calls
            self.root.destroy()  # use in IDLE environment
            # self.root.quit()   # use in PyCharm environment
            sys.exit(0)

    def initialization(self):
        self.squareContent = [EMPTY, EMPTY, EMPTY,
                              EMPTY, EMPTY, EMPTY,
                              EMPTY, EMPTY, EMPTY]
        self.turn == COMPUTER_TURN    # flush potential player's clicks made on game board
        self.root.update_idletasks()  # which may call function onMouse()
        self.root.update()            #
        self.lastSquarePlayed = -1
        self.winner = set([])
        self.playSound('start')
        self.winStatus = ''
        self.turn = self.next
        self.title()
        self.draw(False)
        if self.turn == COMPUTER_TURN:
            self.computerMove()
        return

    def resize(self, event):
        size = (event.width, event.height)
        resize = self.original.resize(size, Image.ANTIALIAS)
        self.image = ImageTk.PhotoImage(resize)
        self.display.delete('IMG')
        self.display.create_image(0, 0, image=self.image, anchor=NW, tags='IMG')
        self.width = size[0]
        self.height = size[1]
        self.draw(False)
        return

    def title(self):
        t = 'Tic-Tac-Toe  ' + str(self.scorePlayer) + ' : ' + str(self.scoreComputer) + '  ['
        if not self.sound:
            t += 'no '
        t += 'sound - level ' + str(self.level) + ']  '
        if self.turn != 'END':
            t += self.turn + '\'s turn'
        else:
            t += self.winStatus
        self.root.title(t)
        return

    def keyboard(self, event):
        if event.char == 's' or event.char == 'S':
            # letter s: toggle sound / no sound
            self.sound = not self.sound
            self.writeConfig()
        try:
            # number (0 to 9) pressed: set game difficulty level
            self.level = int(event.char)
            self.writeConfig()
        except ValueError:
            # other key pressed
            pass
        self.title()
        return

    def draw(self, repeat=False):
        self.display.delete('all')
        self.display.create_image(0, 0, image=self.image, anchor=NW, tags='IMG')
        for s in range(9):
            if self.squareContent[s] == 'X':
                if s in self.winner:
                    color = COLOR_WIN
                elif self.lastSquarePlayed == s and repeat:
                    color = COLOR_X_PLAY
                else:
                    color = COLOR_X
                self.display.create_line((SQUARE[s][0] + MARGIN) * self.scaleX(),
                                         (SQUARE[s][1] + MARGIN) * self.scaleY(),
                                         (SQUARE[s][2] - MARGIN) * self.scaleX(),
                                         (SQUARE[s][3] - MARGIN) * self.scaleY(),
                                         fill=color, width=(MARGIN * self.scaleXY()))
                self.display.create_line((SQUARE[s][0] + MARGIN) * self.scaleX(),
                                         (SQUARE[s][3] - MARGIN) * self.scaleY(),
                                         (SQUARE[s][2] - MARGIN) * self.scaleX(),
                                         (SQUARE[s][1] + MARGIN) * self.scaleY(),
                                         fill=color, width=(MARGIN * self.scaleXY()))
            elif self.squareContent[s] == 'O':
                if s in self.winner:
                    color = COLOR_WIN
                elif self.lastSquarePlayed == s and repeat:
                    color = COLOR_O_PLAY
                else:
                    color = COLOR_O
                self.display.create_oval((SQUARE[s][0] + MARGIN) * self.scaleX(),
                                         (SQUARE[s][1] + MARGIN) * self.scaleY(),
                                         (SQUARE[s][2] - MARGIN) * self.scaleX(),
                                         (SQUARE[s][3] - MARGIN) * self.scaleY(),
                                         outline=color, width=(MARGIN * self.scaleXY()))
        if repeat:
            # the last move will not be highlighted anymore the next time draw() is called
            self.after(TIME_COLOR, self.draw)
        self.root.update()
        return

    def scaleX(self):
        return 1. * self.width / SIZE

    def scaleY(self):
        return 1. * self.height / SIZE

    def scaleXY(self):
        return sqrt(self.scaleX() * self.scaleY())

    def inside(self, event, box):
        return (box[0] * self.scaleX() <= event.x <= box[2] * self.scaleX() and
                box[1] * self.scaleY() <= event.y <= box[3] * self.scaleY())

    def onMouse(self, event):
        if self.turn == PLAYER_TURN:
            square = -1
            for s in range(9):
                if self.inside(event, SQUARE[s]):
                    square = s
                    break
            if square != -1 and self.squareContent[square] == EMPTY:
                self.lastSquarePlayed = square
                self.squareContent[square] = PLAYER
                self.winner = win(self.squareContent)
                self.endMove(True)
            else:
                self.playSound('beep')
        else:
            self.playSound('computer turn')
        return

    def endMove(self, isPlayer):
        if self.winner == set([]):
            # game is not finished
            self.draw(True)
            self.turn = COMPUTER_TURN if isPlayer else PLAYER_TURN
            self.playSound('move')
            self.title()
            if isPlayer:
                self.computerMove()
        elif self.winner == {-1}:
            # game is tied
            self.draw(True)
            self.turn = 'END'
            self.next = COMPUTER_TURN if self.next == PLAYER_TURN else PLAYER_TURN
            self.playSound('nobody wins')
            self.winStatus = 'Game is tied!'
            self.title()
            sleep(TIME_COLOR_S)
            self.root.update()  # update display (re-draw() board)
            sleep(TIME_END_S - TIME_COLOR_S)
            self.initialization()
        else:
            # game is won
            self.draw(False)
            self.turn = 'END'
            if isPlayer:
                self.next = COMPUTER_TURN
                self.playSound('player wins')
                self.winStatus = PLAYER_TURN + ' [' + PLAYER + '] wins!!'
                self.scorePlayer += 1
            else:
                self.next = PLAYER_TURN
                self.playSound('computer wins')
                self.winStatus = COMPUTER_TURN + ' [' + COMPUTER + '] wins!!'
                self.scoreComputer += 1
            self.title()
            sleep(TIME_END_S)
            self.initialization()
        return

    def playSound(self, sound):
        if not self.sound or not SOUND:
            return
        if sound == 'start' and SOUND['start']:
            media.load('shall_we_play_a_game.mp3').play()
        elif sound == 'beep' and SOUND['beep']:
            media.load('computer_error.mp3').play()
        elif sound == 'computer turn' and SOUND['computer turn']:
            media.load('bike_horn.mp3').play()
        elif sound == 'computer wins' and (SOUND['computer wins 1'] or SOUND['computer wins 2']):
            if self.level <= 1 and SOUND['computer wins 1']:
                media.load('pig_snort.ogg').play()
            elif self.level <= 1 and SOUND['computer wins 2']:
                media.load('evil_laugh.mp3').play()
            elif self.level > 1 and SOUND['computer wins 2']:
                media.load('evil_laugh.mp3').play()
            elif self.level > 1 and SOUND['computer wins 1']:
                media.load('pig_snort.ogg').play()
            else:
                pass
        elif sound == 'player wins' and SOUND['player wins']:
            media.load('nice_one.mp3').play()
        elif sound == 'nobody wins' and SOUND['nobody wins']:
            media.load('cow_moo.mp3').play()
        elif sound == 'move' and SOUND['move']:
            media.load('punch_or_whack.mp3').play()
        else:
            pass
        return

    def autoPlay(self, board, turn, maxDepthAllowed):
        winner = win(board)
        if winner == {-1}:
            # game is tied
            return 0
        elif winner != set([]):
            # game is won
            winner = board[winner.pop()]
            if turn == COMPUTER_TURN:
                # the last move was made by PLAYER -> winner is PLAYER
                assert winner == PLAYER
                return -100
            else:
                # the last move was made by COMPUTER -> winner is COMPUTER
                assert winner == COMPUTER
                return 100 + maxDepthAllowed  # will force the speediest possible win
        elif maxDepthAllowed <= 0:
            # maximum recursion reached for level of play
            if turn == COMPUTER_TURN:
                return 50
            else:
                return -50
        else:
            # game is not finished
            possibleMove = [m for m in range(9) if board[m] == EMPTY]
            score = {}
            backup = list(board)
            for m in possibleMove:
                board[m] = COMPUTER if turn == COMPUTER_TURN else PLAYER
                nextMove = PLAYER_TURN if turn == COMPUTER_TURN else COMPUTER_TURN
                score[m] = self.autoPlay(list(board), nextMove, maxDepthAllowed - 1)
                board = list(backup)
            # best move
            possibleMove = [[m, score[m]] for m in possibleMove]
            if turn == PLAYER_TURN:
                possibleMove = sorted(possibleMove, key=lambda item: item[1], reverse=False)
            else:
                possibleMove = sorted(possibleMove, key=lambda item: item[1], reverse=True)
            return possibleMove[0][1]  # return the score of the best move

    def computerMoveAI(self, board):
        possibleMove = [m for m in range(9) if board[m] == EMPTY]
        shuffle(possibleMove)
        if self.level == 0:
            # random move
            return possibleMove[0]
        elif self.level == 1:
            # block (if necessary) or random move
            bestMove = []
            backup = list(board)
            for m in possibleMove:
                board[m] = PLAYER
                winner = win(board)
                if winner != set([]):
                    bestMove.append(m)
                board = list(backup)
            bestMove.append(possibleMove[0])
            return bestMove[0]
        else:
            # best move
            score = {}
            backup = list(board)
            maxDepthAllowed = self.level - 2
            for m in possibleMove:
                board[m] = COMPUTER
                score[m] = self.autoPlay(list(board), PLAYER_TURN, maxDepthAllowed)
                board = list(backup)
                self.root.update()  # update display (possible re-draw() board)
            bestMove = [[m, score[m]] for m in possibleMove]
            bestMove = sorted(bestMove, key=lambda item:item[1], reverse=True)
            if bestMove[0][1] < 0:
                # in case COMPUTER loses, he still needs to try to block PLAYER
                # by playing one of PLAYER immediate winning moves in case there
                # are more than one (can be easily the case in level 1 or 2)
                bestMove2 = []
                for m in possibleMove:
                    board[m] = PLAYER
                    winner = win(board)
                    if winner != set([]):
                        bestMove2.append([m, 0])
                    board = list(backup)
                if bestMove2:
                    bestMove = list(bestMove2)
            return whichMove(bestMove)

    def computerMove(self):
        beginTime = time()
        square = self.computerMoveAI(list(self.squareContent))
        endTime = time()
        if (endTime - beginTime) < TIME_COLOR_S:
            sleep(TIME_COLOR_S - (endTime - beginTime))
        if square != -1:
            self.squareContent[square] = COMPUTER
            self.lastSquarePlayed = square
            self.draw(True)
            self.winner = win(self.squareContent)
            self.root.update_idletasks()  # flush potential player's clicks made on game board
            self.endMove(False)
        return

if __name__ == "__main__":
    app = Game(Tk())
