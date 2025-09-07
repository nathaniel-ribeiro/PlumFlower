BOARD_SIZE = (10, 9)
PIECE_SYMBOLS = ['K', 'A', 'E', 'R', 'C', 'H', 'P', 'k', 'a', 'e', 'r', 'c', 'h', 'p']

DIRECTIONS = {
    "rook": [(-1, 0), (1, 0), (0, -1), (0, 1)],
    "horse": [(-2, -1), (-2, 1), (2, -1), (2, 1),
               (-1, -2), (-1, 2), (1, -2), (1, 2)],
    "advisor": [(-1, -1), (-1, 1), (1, -1), (1, 1)],
    "elephant": [(-2, -2), (-2, 2), (2, -2), (2, 2)]
}

RED_PALACE = {(r, c) for r in range(7, 10) for c in range(3, 6)}
BLACK_PALACE = {(r, c) for r in range(0, 3) for c in range(3, 6)}

# helper functions
def is_red(piece): 
    return piece.isupper()

def is_black(piece): 
    return piece.islower()

def is_valid_square(square_idx):
    row, col = square_idx
    return (0 <= row < BOARD_SIZE[0]) and (0 <= col < BOARD_SIZE[1])

class Move:
    def __init__(self, src_square_idx, dest_square_idx):
        assert is_valid_square(src_square_idx)
        assert is_valid_square(dest_square_idx)

        self.src_square_idx = src_square_idx
        self.dest_square_idx = dest_square_idx
    
    def to_long_algebraic(self):
        '''
        Returns the long algebraic form of this move (e.g. g3g4)
        '''
        def square_to_algebraic(square_idx):
            row, col = square_idx
            file_char = chr(col + ord('a')) 
            rank_char = str(BOARD_SIZE[1] - row) 
            return file_char + rank_char
        
        src_algebraic = square_to_algebraic(self.src_square_idx)
        dest_algebraic = square_to_algebraic(self.dest_square_idx)
        return src_algebraic + dest_algebraic

class Board:
    def __init__(self, board_array, whose_turn, halfmove_clock):
        assert board_array.shape == BOARD_SIZE
        for square in board_array.flatten():
            assert square == "" or square in PIECE_SYMBOLS
        assert whose_turn == "w" or whose_turn == "b"
        assert halfmove_clock >= 0
        
        self.board_array = board_array
        self.whose_turn = whose_turn
        self.halfmove_clock = halfmove_clock
    
    def to_fen(self):
        """
        Returns the Xiangqi FEN string for this board.
        """
        fen_rows = []
        for row in range(BOARD_SIZE[0]):  # 0 (top) -> 9 (bottom)
            empty_count = 0
            fen_row = ""
            for col in range(BOARD_SIZE[1]):
                piece = self.board_array[row, col]
                if piece == "":
                    empty_count += 1
                else:
                    if empty_count > 0:
                        fen_row += str(empty_count)
                        empty_count = 0
                    fen_row += piece
            if empty_count > 0:
                fen_row += str(empty_count)
            fen_rows.append(fen_row)

        board_part = "/".join(fen_rows)

        # Xiangqi FEN typically ignores castling/en passant -> "- -"
        # Fullmove number is not tracked in your class, so we’ll set it to 1 by default
        fen = f"{board_part} {self.whose_turn} - - {self.halfmove_clock} 1"
        return fen

    def make_move(self, move):
        '''
        Returns the new board after making the specified move. If the move is illegal, raises a ValueError().
        Does not modify this board. Note that this handles switching whose turn it is to move and adjusting
        halfmove clock appropriately.
        '''
        pass
    
    def get_legal_moves(self):
        """
        Returns list of legal Moves for this board.
        """
        pseudo_moves = []
        for row in range(BOARD_SIZE[0]):
            for col in range(BOARD_SIZE[1]):
                piece = self.board_array[row, col]
                if piece == "":
                    continue
                if self.whose_turn == "w" and not is_red(piece):
                    continue
                if self.whose_turn == "b" and not is_black(piece):
                    continue
                pseudo_moves.extend(self._generate_piece_moves(piece, (row, col)))

        # Filter: keep only moves that don’t leave king in check
        legal_moves = []
        for move in pseudo_moves:
            new_board = self.make_move(move)
            if not new_board._in_check(self.whose_turn):
                legal_moves.append(move)

        return legal_moves

    def _generate_piece_moves(self, piece, square):
        moves = []
        r, c = square
        side_red = is_red(piece)

        # ---------------- King ----------------
        if piece in ["K", "k"]:
            palace = RED_PALACE if side_red else BLACK_PALACE
            for dr, dc in DIRECTIONS["rook"]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in palace:
                    if self.board_array[nr, nc] == "" or is_red(piece) != is_red(self.board_array[nr, nc]):
                        moves.append(Move((r, c), (nr, nc)))

            # "flying general" rule: if kings face each other
            # scan vertically, if no pieces in between, can capture
            dr = -1 if side_red else 1
            nr, nc = r + dr, c
            blocked = False
            while is_valid_square((nr, nc)):
                if self.board_array[nr, nc] != "":
                    if self.board_array[nr, nc] in ["K", "k"]:
                        moves.append(Move((r, c), (nr, nc)))
                    break
                nr += dr

        # ---------------- Advisor ----------------
        elif piece in ["A", "a"]:
            palace = RED_PALACE if side_red else BLACK_PALACE
            for dr, dc in DIRECTIONS["advisor"]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in palace:
                    if self.board_array[nr, nc] == "" or is_red(piece) != is_red(self.board_array[nr, nc]):
                        moves.append(Move((r, c), (nr, nc)))

        # ---------------- Elephant ----------------
        elif piece in ["E", "e"]:
            own_half = range(5, 10) if side_red else range(0, 5)
            for dr, dc in DIRECTIONS["elephant"]:
                nr, nc = r + dr, c + dc
                eye_r, eye_c = r + dr // 2, c + dc // 2
                if nr in own_half and is_valid_square((nr, nc)):
                    if self.board_array[eye_r, eye_c] == "":
                        if self.board_array[nr, nc] == "" or is_red(piece) != is_red(self.board_array[nr, nc]):
                            moves.append(Move((r, c), (nr, nc)))

        # ---------------- Rook ----------------
        elif piece in ["R", "r"]:
            for dr, dc in DIRECTIONS["rook"]:
                nr, nc = r + dr, c + dc
                while is_valid_square((nr, nc)):
                    if self.board_array[nr, nc] == "":
                        moves.append(Move((r, c), (nr, nc)))
                    else:
                        if is_red(piece) != is_red(self.board_array[nr, nc]):
                            moves.append(Move((r, c), (nr, nc)))
                        break
                    nr += dr
                    nc += dc

        # ---------------- Cannon ----------------
        elif piece in ["C", "c"]:
            for dr, dc in DIRECTIONS["rook"]:
                nr, nc = r + dr, c + dc
                # move like rook until first piece
                while is_valid_square((nr, nc)) and self.board_array[nr, nc] == "":
                    moves.append(Move((r, c), (nr, nc)))
                    nr += dr
                    nc += dc
                # now look for a capture after exactly one screen
                nr += dr
                nc += dc
                while is_valid_square((nr, nc)):
                    if self.board_array[nr - dr, nc - dc] != "":  # found a screen
                        if self.board_array[nr, nc] != "":
                            if is_red(piece) != is_red(self.board_array[nr, nc]):
                                moves.append(Move((r, c), (nr, nc)))
                        break
                    nr += dr
                    nc += dc

        # ---------------- Knight ----------------
        elif piece in ["H", "h"]:
            # mapping: (knight move, blocking leg)
            knight_moves = [
                ((-2, -1), (-1, 0)), ((-2, 1), (-1, 0)),
                ((2, -1), (1, 0)), ((2, 1), (1, 0)),
                ((-1, -2), (0, -1)), ((1, -2), (0, -1)),
                ((-1, 2), (0, 1)), ((1, 2), (0, 1))
            ]
            for (dr, dc), (lr, lc) in knight_moves:
                nr, nc = r + dr, c + dc
                lr, lc = r + lr, c + lc
                if is_valid_square((nr, nc)) and is_valid_square((lr, lc)):
                    if self.board_array[lr, lc] == "":
                        if self.board_array[nr, nc] == "" or is_red(piece) != is_red(self.board_array[nr, nc]):
                            moves.append(Move((r, c), (nr, nc)))

        # ---------------- Pawn ----------------
        elif piece in ["P", "p"]:
            forward = -1 if side_red else 1
            nr, nc = r + forward, c
            if is_valid_square((nr, nc)):
                if self.board_array[nr, nc] == "" or is_red(piece) != is_red(self.board_array[nr, nc]):
                    moves.append(Move((r, c), (nr, nc)))

            crossed_river = (r < 5) if side_red else (r > 4)
            if crossed_river:
                for dc in [-1, 1]:
                    nr, nc = r, c + dc
                    if is_valid_square((nr, nc)):
                        if self.board_array[nr, nc] == "" or is_red(piece) != is_red(self.board_array[nr, nc]):
                            moves.append(Move((r, c), (nr, nc)))

        return moves