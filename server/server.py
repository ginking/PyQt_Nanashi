import socket
import random
import time

STATUS_ERROR = -1
STATUS_IDLE = 0
STATUS_BLUE_TURN = 1
STATUS_RED_TURN = 2
STATUS_BLUE_WIN = 3
STATUS_RED_WIN = 4
STATUS_DRAW = 5
STATUS_FULL = 6

JUDGEMENT_PLAYING = 0
JUDGEMENT_BLUE = 1
JUDGEMENT_RED = 2
JUDGEMENT_DRAW = 3

PORT = 8081
MAXBUFF = 1024

TABLENUM = 4
IP_TABLE = [[0, 0], [0, 0], [0, 0], [0, 0]]
CHESSBOARD_TABLE = ['', '', '', '']
STATUS_TABLE = [0, 0, 0, 0]
TIME_TABLE = [0, 0, 0, 0]
EXPIRE_TIME = 5

timestone = 0
timestoneFlag = False

MAPNUM = 12
MAPS = [
    '1000000000000000000000000000000000000000000000000000000000000002',
    '1000000000000000000000000003300000033000000000000000000000000002',
    '1000000000000000000330000030030000300300000330000000000000000002',
    '0000000000000000000330000031230000321300000330000000000000000000',
    '1000000200300300033003300000000000000000033003300030030020000001',
    '0000000000000000000110000003300000033000000220000000000000000000',
    '3000000330000003130000321300003213000032130000323000000330000003',
    '1000000000000000000330000000300000030000000330000000000000000002',
    '0000000000000000000030000001330000332000000300000000000000000000',
    '0000000003000030003113000020020000200200003113000300003000000000',
    '0000000000000000003003000003320000133000003003000000000000000000',
    '0000000000000000003003000233331000300300003003000003300000000000'
]


def randomChessBoard():
    return MAPS[random.randint(0, MAPNUM-1)]

def updateChessBoard(data, table):
    global CHESSBOARD_TABLE
    CHESSBOARD_TABLE[table] = data

def checkTimeout():
    global timestone
    global timestoneFlag
    global IP_TABLE
    global CHESSBOARD_TABLE
    global STATUS_TABLE
    global TIME_TABLE

    print 'checking timeout...'

    if (timestoneFlag == False):
        timestoneFlag = True
        timestone = time.time()
    timenow = time.time()
    telapse = timenow - timestone
    timestone = timenow
    for table in xrange(0, TABLENUM):
        TIME_TABLE[table] += telapse
        if (STATUS_TABLE[table] != STATUS_IDLE):
            if (TIME_TABLE[table] > EXPIRE_TIME):
                tempStatus = -1
                if (STATUS_TABLE[table] == STATUS_BLUE_TURN):
                    tempStatus = STATUS_RED_WIN
                else:
                    tempStatus = STATUS_BLUE_WIN
                # declare result
                infoBlue = str(tempStatus) + '@0@' + CHESSBOARD_TABLE[table]
                infoRed = str(tempStatus) + '@1@' + CHESSBOARD_TABLE[table]
                soc.sendto(infoBlue, IP_TABLE[table][0])
                soc.sendto(infoRed, IP_TABLE[table][1])
                # clear game
                IP_TABLE[table] = [0, 0]
                CHESSBOARD_TABLE[table] = ''
                STATUS_TABLE[table] = STATUS_IDLE
                print 'Table %d: Time out. Status: %d' % (table, tempStatus)


def judgeGame(gamestr):
    blueNum = redNum = 0
    blankFlag = False
    for i in xrange(0, len(gamestr)):
        if (gamestr[i] == '0'):
            blankFlag = True
        elif (gamestr[i] == '1'):
            blueNum += 1
        elif (gamestr[i] == '2'):
            redNum += 1
    if (blankFlag == True):
        if (blueNum == 0):
            return JUDGEMENT_RED
        if (redNum == 0):
            return JUDGEMENT_RED
        return JUDGEMENT_PLAYING
    elif (blueNum > redNum):
        return JUDGEMENT_BLUE
    elif (blueNum < redNum):
        return JUDGEMENT_RED
    else:
        return JUDGEMENT_DRAW

# main part

soc = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
soc.bind(('', PORT))
print 'UDP LISTENING...'

while True:
    checkTimeout()

    data, addr = soc.recvfrom(MAXBUFF)
    print 'Received:', data, ' --- From', addr

    # check cough
    if (data == '$'):
        continue

    table, side, flag = -1, -1, False
    emptyTable, emptySide, emptyFlag = -1, -1, False
    # traverse IP_TABLE
    for i in xrange(0, TABLENUM):
        if ((table != -1) or (emptyTable != -1)):
            break
        for j in (0, 1):
            if (IP_TABLE[i][j] == addr):
                table, side, flag = i, j, True
                break
            if (IP_TABLE[i][j] == 0):
                emptyTable, emptySide, emptyFlag = i, j, True
                break
    
    # check if ip exists
    if (flag == True):
        # check if opponent exists
        if (IP_TABLE[table][1-side] == 0):
            # if it is a quit msg
            if (data.strip() == '#'):
                soc.sendto('#', addr) # quit ack
                IP_TABLE[table] = [0, 0]
                print 'He quit. He is %d.' % side
                continue
            # tell him again to wait
            infoWait = str(STATUS_IDLE) + '@' + str(side)
            soc.sendto(infoWait, addr)
            print 'IP exists. But no opponent.'
            continue
        else:
            # if it is a quit msg
            if (data.strip() == '#'):
                # tell the opponent
                if (side == 0):
                    tempStatus = STATUS_RED_WIN
                else:
                    tempStatus = STATUS_BLUE_WIN
                infoOppo = str(tempStatus) + '@' + str(1-side) + '@' + CHESSBOARD_TABLE[table]
                soc.sendto(infoOppo, IP_TABLE[table][1-side])
                # clear game
                IP_TABLE[table] = [0, 0]
                CHESSBOARD_TABLE[table] = ''
                STATUS_TABLE[table] = STATUS_IDLE
                print 'He quit. He is %d.' % side
                continue
            # check game status
            if (STATUS_TABLE[table] == STATUS_IDLE):
                # init new game
                TIME_TABLE[table] = 0
                CHESSBOARD_TABLE[table] = randomChessBoard()
                infoBlue = str(STATUS_BLUE_TURN) + '@0@' + CHESSBOARD_TABLE[table]
                infoRed = str(STATUS_BLUE_TURN) + '@1@' + CHESSBOARD_TABLE[table]
                soc.sendto(infoBlue, IP_TABLE[table][0])
                soc.sendto(infoRed, IP_TABLE[table][1])
                STATUS_TABLE[table] = STATUS_BLUE_TURN
                print 'Table %d: New Game Started (THIS NOT GONNA HAPPEN)' % table
            elif (STATUS_TABLE[table] == STATUS_BLUE_TURN):
                if (side == 0):
                    # update timetable
                    TIME_TABLE[table] = 0
                    # parse data, analyse and judge
                    updateChessBoard(data, table) # update directly
                    res = judgeGame(CHESSBOARD_TABLE[table]) # judge result
                    if (res == JUDGEMENT_PLAYING): # still playing
                        infoBlue = str(STATUS_RED_TURN) + '@0@' + CHESSBOARD_TABLE[table]
                        infoRed = str(STATUS_RED_TURN) + '@1@' + CHESSBOARD_TABLE[table]
                        soc.sendto(infoBlue, IP_TABLE[table][0])
                        soc.sendto(infoRed, IP_TABLE[table][1])
                        STATUS_TABLE[table] = STATUS_RED_TURN
                        print 'Table %d: the Blue updated' % table
                    else: # game end
                        tempStatus = -1
                        if (res == JUDGEMENT_BLUE):
                            tempStatus = STATUS_BLUE_WIN
                        elif (res == JUDGEMENT_RED):
                            tempStatus = STATUS_RED_WIN
                        else: # draw
                            tempStatus = STATUS_DRAW
                        # declare result
                        infoBlue = str(tempStatus) + '@0@' + CHESSBOARD_TABLE[table]
                        infoRed = str(tempStatus) + '@1@' + CHESSBOARD_TABLE[table]
                        soc.sendto(infoBlue, IP_TABLE[table][0])
                        soc.sendto(infoRed, IP_TABLE[table][1])
                        # clear game
                        IP_TABLE[table] = [0, 0]
                        CHESSBOARD_TABLE[table] = ''
                        STATUS_TABLE[table] = STATUS_IDLE
                        print 'Table %d: the Blue updated. GAME END. Status: %d' % (table, tempStatus)
                else:
                    # ignore data
                    infoRed = str(STATUS_BLUE_TURN) + '@1@' + CHESSBOARD_TABLE[table]
                    soc.sendto(infoRed, IP_TABLE[table][1])
                    print 'Not his turn. Blue turn. He is red.'
                    continue
            elif (STATUS_TABLE[table] == STATUS_RED_TURN):
                if (side == 1):
                    # update timetable
                    TIME_TABLE[table] = 0
                    # parse data, analyse and judge
                    updateChessBoard(data, table) # update directly
                    res = judgeGame(CHESSBOARD_TABLE[table]) # judge result
                    if (res == JUDGEMENT_PLAYING): # still playing
                        infoBlue = str(STATUS_BLUE_TURN) + '@0@' + CHESSBOARD_TABLE[table]
                        infoRed = str(STATUS_BLUE_TURN) + '@1@' + CHESSBOARD_TABLE[table]
                        soc.sendto(infoBlue, IP_TABLE[table][0])
                        soc.sendto(infoRed, IP_TABLE[table][1])
                        STATUS_TABLE[table] = STATUS_BLUE_TURN
                        print 'Table %d: the Red updated' % table
                    else: # end game
                        tempStatus = -1
                        if (res == JUDGEMENT_BLUE):
                            tempStatus = STATUS_BLUE_WIN
                        elif (res == JUDGEMENT_RED):
                            tempStatus = STATUS_RED_WIN
                        else: # draw
                            tempStatus = STATUS_DRAW
                        # declare result
                        infoBlue = str(tempStatus) + '@0@' + CHESSBOARD_TABLE[table]
                        infoRed = str(tempStatus) + '@1@' + CHESSBOARD_TABLE[table]
                        soc.sendto(infoBlue, IP_TABLE[table][0])
                        soc.sendto(infoRed, IP_TABLE[table][1])
                        # clear game
                        IP_TABLE[table] = [0, 0]
                        CHESSBOARD_TABLE[table] = ''
                        STATUS_TABLE[table] = STATUS_IDLE
                        print 'Table %d: the Red updated. GAME END. Status: %d' % (table, tempStatus)
                else:
                    # ignore data
                    infoBlue = str(STATUS_RED_TURN) + '@0@' + CHESSBOARD_TABLE[table]
                    soc.sendto(infoBlue, IP_TABLE[table][0])
                    print 'Not his turn. Red turn. He is blue.'
                    continue
            else: # error handler
                try:
                    infoBlue = str(STATUS_ERROR) + '@0@' + CHESSBOARD_TABLE[table]
                    infoRed = str(STATUS_ERROR) + '@1@' + CHESSBOARD_TABLE[table]
                    soc.sendto(infoBlue, IP_TABLE[table][0])
                    soc.sendto(infoRed, IP_TABLE[table][1])
                    TIME_TABLE[table] = 0
                    IP_TABLE[table] = [0, 0]
                    CHESSBOARD_TABLE[table] = ''
                    STATUS_TABLE[table] = STATUS_IDLE
                except:
                    print 'Game system crashed. Sorry.'
                    sys.exit()
    else:
        # if it is a quit msg
        if (data.strip() == '#'):
            # ignore
            print 'He quit. He is not logged in.'
            continue
        if (emptyFlag == True):
            # put into empty position
            IP_TABLE[emptyTable][emptySide] = addr
            # check if opponent exists
            if (IP_TABLE[emptyTable][1-emptySide] == 0):
                # tell client to wait opponent
                infoWait = str(STATUS_IDLE) + '@' + str(emptySide)
                soc.sendto(infoWait, addr)
                print 'Sit into Table %d Side %d. Waiting for opponent.' % (emptyTable, emptySide)
            else:
                # init new game
                TIME_TABLE[emptyTable] = 0
                CHESSBOARD_TABLE[emptyTable] = randomChessBoard()
                infoBlue = str(STATUS_BLUE_TURN) + '@0@' + CHESSBOARD_TABLE[emptyTable]
                infoRed = str(STATUS_BLUE_TURN) + '@1@' + CHESSBOARD_TABLE[emptyTable]
                print IP_TABLE[emptyTable]
                soc.sendto(infoBlue, IP_TABLE[emptyTable][0])
                soc.sendto(infoRed, IP_TABLE[emptyTable][1])
                STATUS_TABLE[emptyTable] = STATUS_BLUE_TURN
                print 'Table %d: New Game Started (THIS GONNA HAPPEN)' % emptyTable
        else:
            # tell client to retry after a while
            infoFull = str(STATUS_FULL) + '@0'
            soc.sendto(infoFull, addr)
            print 'He had no table to sit down.'

print 'What happend?'
sys.exit()
