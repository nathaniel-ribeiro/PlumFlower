class Move:
    def __init__(self, src_square_idx, dest_square_idx):
        self.src_square_idx = src_square_idx
        self.dest_square_idx = dest_square_idx
    
    def to_long_algebraic():
        pass

class Board:
    def __init__(self, board_array, whose_turn, plies_since_capture):
        self.board_array = board_array
        self.whose_turn = whose_turn
        self.plies_since_capture = plies_since_capture

    def make_move(self, move):
        '''
        Returns the new board after making the specified move. If the move is illegal, raises a ValueError().
        Does not modify this board.
        '''
        pass
    def get_legal_moves(self):
        '''
        Returns list of legal Moves in arbitrary order
        '''
        pass