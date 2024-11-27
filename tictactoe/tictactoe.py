"""
Tic Tac Toe Player
"""

import math
import copy

X = "X"
O = "O"
EMPTY = None


def initial_state():
    """
    Returns starting state of the board.
    """
    return [[EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY]]


def player(board):
    """
    Returns player who has the next turn on a board.
    """
    
    countX = 0
    countO = 0

    for row in range(len(board)):
        for col in range(len(board[row])):
            if board[row][col] == X: 
                countX += 1
            elif board[row][col] == O:
                countO += 1

    if countX == countO:
        return X
    
    return O


def actions(board):
    """
    Returns set of all possible actions (i, j) available on the board.
    """

    possible_actions = set() 

    for row in range(len(board)):
        for col in range(len(board[row])):
            if board[row][col] == EMPTY:
                possible_actions.add((row, col))

    return possible_actions


def result(board, action):
    """
    Returns the board that results from making move (i, j) on the board.
    """
    
    if action not in actions(board):
        raise Exception('not a valid action')

    row, col = action 
    new_board = copy.deepcopy(board)
    new_board[row][col] = player(board)

    return new_board


def check_rows(board, player):

    for row in range(len(board)):
        count = 0
        for col in range(len(board[0])):
            if board[row][col] == player:
                count += 1

        if count == len(board):
            return True 
    
    return False


def check_cols(board, player):

    for col in range(len(board)):
        count = 0
        for row in range(len(board[col])):
            if board[row][col] == player:
                count += 1

        if count == len(board):
            return True 
    
    return False


def check_main_diagonal(board, player):
    count = 0

    for pos in range(len(board)):
        if board[pos][pos] == player:
            count += 1

        if count == len(board):
            return True 
    
    return False


def check_secondary_diagonal(board, player):
    count = 0

    for pos in range(len(board)):
        if board[pos][len(board) - pos - 1] == player:
            count += 1

        if count == len(board):
            return True 
    
    return False


def winner(board):
    """
    Returns the winner of the game, if there is one.
    """
    
    players = {X, O}

    for possible_winner in players:
        if check_rows(board, possible_winner):
            return possible_winner 
        if check_cols(board, possible_winner):
            return possible_winner 
        if check_main_diagonal(board, possible_winner):
            return possible_winner 
        if check_secondary_diagonal(board, possible_winner):
            return possible_winner 

    return None 


def terminal(board):
    """
    Returns True if game is over, False otherwise.
    """

    count = 0
    
    for row in range(len(board)):
        for col in range(len(board[row])):
            if board[row][col] != EMPTY:
                count += 1

    if winner(board) == X or winner(board) == O or count == len(board) * len(board[0]):
        return True 

    return False


def utility(board):
    """
    Returns 1 if X has won the game, -1 if O has won, 0 otherwise.
    """

    the_winner = winner(board)

    if the_winner == X:
        return 1
    elif the_winner == O:
        return -1
    
    return 0


def max_value(board):
    value = -1

    if terminal(board): 
        return utility(board)
    
    for action in actions(board):
        value = max(value, min_value(result(board, action)))

    return value


def min_value(board):
    value = 1

    if terminal(board): 
        return utility(board)
    
    for action in actions(board):
        value = min(value, max_value(result(board, action)))

    return value


def minimax(board):
    """
    Returns the optimal action for the current player on the board.
    """

    if terminal(board):
        return None

    current_player = player(board)

    if current_player == X:
        plays = []
        for action in actions(board): 
            value = min_value(result(board, action))
            if value == 1:
                return action

            best_play = [value, action]
            plays.append(best_play)

        return sorted(plays, key=lambda x: x[0], reverse=True)[0][1]
    
    if current_player == O:
        plays = []
        for action in actions(board): 
            value = max_value(result(board, action))
            if value == -1:
                return action

            best_play = [value, action]
            plays.append(best_play)

        return sorted(plays, key=lambda x: x[0])[0][1]

