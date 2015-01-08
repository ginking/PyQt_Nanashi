import sys
import socket
import random
import thread
from PyQt4 import QtCore, QtGui

SERVER_PORT = 8081
MAXBUFF = 1024
HOST_NAME = 'localhost'
HOST_ADDR = '127.0.0.1'

STATUS_ERROR = -1
STATUS_IDLE = 0
STATUS_BLUE_TURN = 1
STATUS_RED_TURN = 2
STATUS_BLUE_WIN = 3
STATUS_RED_WIN = 4
STATUS_DRAW = 5
STATUS_FULL = 6

def randomPortNum():
    return random.randint(8082, 8999)

def setCharAt(tar, c, i):
    return tar[:i] + c + tar[(i+1):] # unsafe


class MyWindow(QtGui.QMainWindow):

    def __init__(self):
        super(MyWindow, self).__init__()
        self.setWindowTitle('Nanashi')

        self.label1 = QtGui.QLabel('NANASHI Game v1.0 By Hao\nRight Click for the Menu')
        self.label1.setAlignment(QtCore.Qt.AlignCenter)
        self.setCentralWidget(self.label1)

        self.popMenu = QtGui.QMenu()
        newgameaction = QtGui.QAction('New Game', self)
        coughaction = QtGui.QAction('Cough', self)
        quitgameaction = QtGui.QAction('Quit Game', self)
        self.popMenu.addAction(newgameaction)
        self.popMenu.addAction(coughaction)
        self.popMenu.addAction(quitgameaction)
        self.connect(newgameaction, QtCore.SIGNAL('triggered()'), self.onNewGame)
        self.connect(coughaction, QtCore.SIGNAL('triggered()'), self.onCough)
        self.connect(quitgameaction, QtCore.SIGNAL('triggered()'), self.onQuitGame)

        self.chessPositions = '0000000003000030003113000020020000200200003113000300003000000000'
        self.gameStatus = STATUS_IDLE
        self.side = None
        self.activePos = None
        self.cSocket = None

        self.recvFlag = False
        self.dThreadDone = False
        self.dThread = thread.start_new_thread(self.listen2server, ())

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 150, 400, 400)
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint)
        self.setFixedSize(self.width(), self.height())
        self.show() # repaint window

    def initSocket(self):
        while True:
            try:
                cPort = randomPortNum() # in (8082, 8999)
                self.cSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.cSocket.bind(('', cPort))
                print 'success: [initSocket] port number is %d' % cPort
                break
            except:
                print 'error: [initSocket] port number taken. retrying...'
                continue
        return

    def listen2server(self):
        if (self.cSocket is None):
            self.initSocket() # init udp socket
        while (not self.dThreadDone):
            data = addr = None
            try:
                data, addr = self.cSocket.recvfrom(MAXBUFF)
                self.recvFlag = True
                print 'Received:', data, '--- From', addr
                self.onServerMsg(data, addr)
            except:
                continue
        return

    def paintEvent(self, e):
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawChess(qp)
        qp.end()

    def onNewGame(self):
        if (self.gameStatus != STATUS_IDLE):
            return
        self.label1.setText('') # hide center label
        self.setWindowTitle('Nanashi\t(Connecting...)')
        data = addr = None
        # while True:
        #   if (self.recvFlag):
        #       self.recvFlag = False
        #       break
        #   self.cSocket.sendto('NG', (HOST_NAME, SERVER_PORT))
        self.cSocket.sendto('NG', (HOST_NAME, SERVER_PORT))
        # self.onServerMsg(data, addr)

    def onCough(self):
        self.cSocket.sendto('$', (HOST_NAME, SERVER_PORT))

    def onQuitGame(self):
        self.dThreadDone = True
        self.cSocket.sendto('#', (HOST_NAME, SERVER_PORT))
        sys.exit()

    def mousePressEvent(self, event):
        if (event.button() != QtCore.Qt.LeftButton):
            return
        x = event.x()
        y = event.y()
        # print x, y
        # self.side = 1
        if (self.gameStatus == STATUS_IDLE):
            print 'idle left click'
            return
        print 'left clicked'
        if ((self.gameStatus == STATUS_BLUE_TURN) and (self.side == 1)):
            return
        if ((self.gameStatus == STATUS_RED_TURN) and (self.side == 0)):
            return
        clickPos = x / 50 * 8 + y / 50
        if (int(self.chessPositions[clickPos]) == 3): # rock
            return
        elif (int(self.chessPositions[clickPos]) == (1-self.side)+1): # opponent
            return
        elif (int(self.chessPositions[clickPos]) == self.side+1): # self
            self.activePos = clickPos # activate position
            self.update()
            return
        # on a blank
        if (self.activePos is None): # not active
            return
        # already activated
        tempCb = self.updateChessBoard(clickPos)
        # while True:
        #   if (self.recvFlag):
        #       self.recvFlag = False
        #       break
        #   self.cSocket.sendto(tempCb, (HOST_NAME, SERVER_PORT))
        self.cSocket.sendto(tempCb, (HOST_NAME, SERVER_PORT))
        # self.onServerMsg(data, addr)

    # when click on a blank with an active position
    def updateChessBoard(self, clickPos):
        res = self.chessPositions
        # if it is a jump
        if ((abs(clickPos-self.activePos) == 16) or ((clickPos/8 == self.activePos/8) and (abs(clickPos-self.activePos) == 2))):
            res = setCharAt(res, '0', self.activePos)
        elif ((abs(clickPos/8-self.activePos/8) > 1) or (abs(clickPos%8-self.activePos%8) > 1)):
            return res
        # put a new chess in the blank
        res = setCharAt(res, str(self.side+1), clickPos)
        # change the color of adjacent chess
        tar = []
        if ((clickPos % 8 != 0) and (res[clickPos-1] != '3') and (res[clickPos-1] != '0')): # up
            tar.append(clickPos-1)
        if ((clickPos / 8 != 0) and (res[clickPos-8] != '3') and (res[clickPos-8] != '0')): # left
            tar.append(clickPos-8)
        if ((clickPos % 8 != 7) and (res[clickPos+1] != '3') and (res[clickPos+1] != '0')): # down
            tar.append(clickPos+1)
        if ((clickPos / 8 != 7) and (res[clickPos+8] != '3') and (res[clickPos+8] != '0')): # right
            tar.append(clickPos+8)
        if ((clickPos/8 > 0) and (clickPos%8 > 0) and (res[clickPos-9] != '3') and (res[clickPos-9] != '0')): # upleft
            tar.append(clickPos-9)
        if ((clickPos/8 > 0) and (clickPos%8 < 7) and (res[clickPos-7] != '3') and (res[clickPos-7] != '0')): # downleft
            tar.append(clickPos-7)
        if ((clickPos/8 < 7) and (clickPos%8 > 0) and (res[clickPos+7] != '3') and (res[clickPos+7] != '0')): # upright
            tar.append(clickPos+7)
        if ((clickPos/ 8 < 7) and (clickPos%8 < 7) and (res[clickPos+9] != '3') and (res[clickPos+9] != '0')): # downright
            tar.append(clickPos+9)
        for _ in tar:
            res = setCharAt(res, str(self.side+1), _)
        return res

    def onServerMsg(self, data, addr):
        dataArr = data.strip().strip('@').split('@')
        status = int(dataArr[0])
        if (self.gameStatus == STATUS_IDLE):
            if (status == STATUS_ERROR):
                self.setWindowTitle('Nanashi\t(Server error.)')
            elif (status == STATUS_FULL):
                self.setWindowTitle('Nanashi\t(Server busy. Try later.)')
            elif (status == STATUS_IDLE):
                self.setWindowTitle('Nanashi\t(Connected. Waiting for opponent.)')
            elif (status == STATUS_BLUE_TURN): # start new game
                side = dataArr[1]
                cb = dataArr[2]
                self.chessPositions = cb # set chessboard
                self.side = int(side) # set color
                if (self.side == 0): # check my color
                    self.setWindowTitle('Nanashi\t(Blue. Your turn.)')
                else:
                    self.setWindowTitle('Nanashi\t(Red. Opponent turn.)')
                self.gameStatus = status
                self.update()
            else:
                self.setWindowTitle('Nanashi\t(Unidentified error.)')
        elif ((self.gameStatus == STATUS_BLUE_TURN) or (self.gameStatus == STATUS_RED_TURN)):
            if (status == STATUS_ERROR):
                self.setWindowTitle('Nanashi\t(Server error.)')
                self.gameStatus = STATUS_IDLE
                self.activePos = None
            elif (status == STATUS_BLUE_TURN): # now blue turn
                cb = dataArr[2]
                self.chessPositions = cb # update chessboard
                if (self.side == 0): # check my color
                    self.setWindowTitle('Nanashi\t(Blue. Your turn.)')
                else:
                    self.setWindowTitle('Nanashi\t(Red. Opponent turn.)')
                self.gameStatus = status # update status
                self.activePos = None
                self.update()
            elif (status == STATUS_RED_TURN): # now red turn
                cb = dataArr[2]
                self.chessPositions = cb # update chessboard
                if (self.side == 0): # check my color
                    self.setWindowTitle('Nanashi\t(Blue. Opponent turn.)')
                else:
                    self.setWindowTitle('Nanashi\t(Red. Your turn.)')
                self.gameStatus = status # update status
                self.activePos = None
                self.update()
            elif (status == STATUS_BLUE_WIN): # winner is blue
                cb = dataArr[2]
                self.chessPositions = cb # update chessboard
                if (self.side == 0): # check my color
                    self.setWindowTitle('Nanashi\t(Blue. You win!)')
                else:
                    self.setWindowTitle('Nanashi\t(Red. You lose!)')
                self.gameStatus = STATUS_IDLE # update status
                self.activePos = None
                self.update()
            elif (status == STATUS_RED_WIN): # winner is red
                cb = dataArr[2]
                self.chessPositions = cb # update chessboard
                if (self.side == 0): # check my color
                    self.setWindowTitle('Nanashi\t(Blue. You lose!)')
                else:
                    self.setWindowTitle('Nanashi\t(Red. You win!)')
                self.gameStatus = STATUS_IDLE # update status
                self.activePos = None
                self.update()
            elif (status == STATUS_DRAW): # draw game
                cb = dataArr[2]
                self.chessPositions = cb # update chessboard
                if (self.side == 0): # check my color
                    self.setWindowTitle('Nanashi\t(Blue. Draw game!)')
                else:
                    self.setWindowTitle('Nanashi\t(Red. Draw game!)')
                self.gameStatus = STATUS_IDLE # update status
                self.activePos = None
                self.update()

    def contextMenuEvent(self, event):
        self.popMenu.exec_(event.globalPos())

    def drawChess(self, qp):
        for i in xrange(0, len(self.chessPositions)):
            boardX = i / 8
            boardY = i % 8
            posX = boardX * 50
            posY = boardY * 50
            if (self.chessPositions[i] == '0'):
                brush = QtGui.QBrush(QtGui.QColor(255, 255, 255))
            elif (self.chessPositions[i] == '1'):
                if (i == self.activePos):
                    brush = QtGui.QBrush(QtGui.QColor(100, 100, 255))
                else:
                    brush = QtGui.QBrush(QtGui.QColor(0, 0, 255))
            elif (self.chessPositions[i] == '2'):
                if (i == self.activePos):
                    brush = QtGui.QBrush(QtGui.QColor(255, 100, 100))
                else:
                    brush = QtGui.QBrush(QtGui.QColor(255, 0, 0))
            elif (self.chessPositions[i] == '3'):
                brush = QtGui.QBrush(QtGui.QColor(0, 0, 0))
            else:
                self.dThreadDone = True
                sys.exit()
            qp.setBrush(brush)
            qp.drawRect(posX, posY, 50, 50)


app = QtGui.QApplication(sys.argv)
mywindow = MyWindow()
app.exec_()
