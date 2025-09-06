BOARD_SIZE = (10, 9)

class Move:
    def __init__(self, src_square_idx, dest_square_idx):
        assert 0 <= src_square_idx[0] <= BOARD_SIZE[0] - 1
        assert 0 <= src_square_idx[1] <= BOARD_SIZE[1] - 1
        assert 0 <= dest_square_idx[0] <= BOARD_SIZE[0] - 1
        assert 0 <= dest_square_idx[1] <= BOARD_SIZE[1] - 1

        self.src_square_idx = src_square_idx
        self.dest_square_idx = dest_square_idx
    
    def to_long_algebraic(self):
        '''
        Returns the long algebraic form of this move (e.g. g3g4)
        '''
        src_algebraic = (self.src_square_idx[0] + ord('a')) + ("")
        dest_algebraic = (self.dest_square_idx[0] + ord('a')) + ("")
        return src_algebraic + dest_algebraic

class Board:
    def __init__(self, board_array, whose_turn, plies_since_capture):
        assert board_array.shape == BOARD_SIZE
        assert whose_turn == "r" or whose_turn == "b"
        assert plies_since_capture >= 0
        
        self.board_array = board_array
        self.whose_turn = whose_turn
        self.plies_since_capture = plies_since_capture
    
    def to_fen(self):
        '''
        Returns the corresponding FEN string for this board.
        '''

    def make_move(self, move):
        '''
        Returns the new board after making the specified move. If the move is illegal, raises a ValueError().
        Does not modify this board.
        '''
        pass
    def get_legal_moves(self):
        '''
        Returns list of legal Moves for this board.
        '''
        pass