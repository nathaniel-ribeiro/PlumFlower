import copy
import numpy as np

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
    def __init__(self, board_array: np.ndarray, whose_turn: str, halfmove_clock: int):
        assert board_array.shape == BOARD_SIZE
        for square in board_array.flatten():
            assert square == "" or square in PIECE_SYMBOLS
        assert whose_turn in ("w", "b")
        assert halfmove_clock >= 0
        self.board_array = board_array
        self.whose_turn = whose_turn
        self.halfmove_clock = halfmove_clock

    # ---------- Helper: apply move to a numpy board array (no Board created) ----------
    def _apply_move_array(self, board_array: np.ndarray, move) -> np.ndarray:
        new_arr = board_array.copy()  # shallow copy is fine for numpy
        sr, sc = move.src_square_idx
        dr, dc = move.dest_square_idx
        piece = new_arr[sr, sc]
        new_arr[dr, dc] = piece
        new_arr[sr, sc] = ""
        return new_arr

    # ---------- Helper: generate pseudo-legal moves for piece on a given array ----------
    def _generate_piece_moves_at(self, piece: str, square, board_array: np.ndarray):
        moves = []
        r, c = square
        side_red = is_red(piece)
        piece_u = piece.upper()

        def enemy_or_empty(rr, cc):
            if not is_valid_square((rr, cc)): return False
            target = board_array[rr, cc]
            return target == "" or (side_red and is_black(target)) or (not side_red and is_red(target))

        # King (general)
        if piece_u == "K":
            palace = RED_PALACE if side_red else BLACK_PALACE
            for dr, dc in DIRECTIONS["orth"]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in palace and enemy_or_empty(nr, nc):
                    moves.append(Move((r, c), (nr, nc)))
            # flying/facing general capture (scan both vertical directions)
            for dr, dc in [(-1,0),(1,0)]:
                nr = r + dr
                nc = c
                while is_valid_square((nr, nc)):
                    if board_array[nr, nc] != "":
                        if board_array[nr, nc].upper() == "K":  # found other general
                            moves.append(Move((r, c), (nr, nc)))
                        break
                    nr += dr

        # Advisor
        elif piece_u == "A":
            palace = RED_PALACE if side_red else BLACK_PALACE
            for dr, dc in DIRECTIONS["diag"]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in palace and enemy_or_empty(nr, nc):
                    moves.append(Move((r, c), (nr, nc)))

        # Elephant
        elif piece_u == "E":
            own_half = range(5, 10) if side_red else range(0, 5)
            for dr, dc in DIRECTIONS["elec"]:
                nr, nc = r + dr, c + dc
                eye_r, eye_c = r + dr // 2, c + dc // 2
                if is_valid_square((nr, nc)) and nr in own_half:
                    if board_array[eye_r, eye_c] == "":
                        if enemy_or_empty(nr, nc):
                            moves.append(Move((r, c), (nr, nc)))

        # Rook (Chariot)
        elif piece_u == "R":
            for dr, dc in DIRECTIONS["orth"]:
                nr, nc = r + dr, c + dc
                while is_valid_square((nr, nc)):
                    if board_array[nr, nc] == "":
                        moves.append(Move((r, c), (nr, nc)))
                    else:
                        if (side_red and is_black(board_array[nr, nc])) or (not side_red and is_red(board_array[nr, nc])):
                            moves.append(Move((r, c), (nr, nc)))
                        break
                    nr += dr
                    nc += dc

        # Cannon
        elif piece_u == "C":
            for dr, dc in DIRECTIONS["orth"]:
                nr, nc = r + dr, c + dc
                # non-capture moves (slide until first piece)
                while is_valid_square((nr, nc)) and board_array[nr, nc] == "":
                    moves.append(Move((r, c), (nr, nc)))
                    nr += dr
                    nc += dc
                # find first piece (screen)
                if not is_valid_square((nr, nc)):
                    continue
                # now scan beyond the screen to find the first piece to capture
                nr2, nc2 = nr + dr, nc + dc
                while is_valid_square((nr2, nc2)):
                    if board_array[nr2, nc2] != "":
                        if (side_red and is_black(board_array[nr2, nc2])) or (not side_red and is_red(board_array[nr2, nc2])):
                            moves.append(Move((r, c), (nr2, nc2)))
                        break
                    nr2 += dr
                    nc2 += dc

        # Horse (Knight / 'H')
        elif piece_u == "H":
            # horse moves with leg-blocking checks
            knight_patterns = [
                ((-2, -1), (-1, 0)), ((-2, 1), (-1, 0)),
                ((2, -1), (1, 0)), ((2, 1), (1, 0)),
                ((-1, -2), (0, -1)), ((1, -2), (0, -1)),
                ((-1, 2), (0, 1)), ((1, 2), (0, 1))
            ]
            for (dr, dc), (lr, lc) in knight_patterns:
                nr, nc = r + dr, c + dc
                leg_r, leg_c = r + lr, c + lc
                if is_valid_square((nr, nc)) and is_valid_square((leg_r, leg_c)):
                    if board_array[leg_r, leg_c] == "":
                        if enemy_or_empty(nr, nc):
                            moves.append(Move((r, c), (nr, nc)))

        # Pawn
        elif piece_u == "P":
            forward = -1 if side_red else 1
            nr, nc = r + forward, c
            if is_valid_square((nr, nc)) and enemy_or_empty(nr, nc):
                moves.append(Move((r, c), (nr, nc)))
            # sideways after crossing river
            crossed = (r < 5) if side_red else (r > 4)
            if crossed:
                for dc in (-1, 1):
                    nr, nc = r, c + dc
                    if is_valid_square((nr, nc)) and enemy_or_empty(nr, nc):
                        moves.append(Move((r, c), (nr, nc)))

        return moves

    # ---------- Helper: detect check on a raw array ----------
    def _is_in_check_on_array(self, board_array: np.ndarray, side: str) -> bool:
        # locate own general
        target = "K" if side == "w" else "k"
        gen_pos = None
        for r in range(BOARD_SIZE[0]):
            for c in range(BOARD_SIZE[1]):
                if board_array[r, c] == target:
                    gen_pos = (r, c)
                    break
            if gen_pos: break
        if gen_pos is None:
            # missing general -> consider it 'in check' (or illegal)
            return True

        # check if any enemy piece attacks gen_pos
        attacker_is_red = (side == "b")  # enemy is red when side is black
        for r in range(BOARD_SIZE[0]):
            for c in range(BOARD_SIZE[1]):
                p = board_array[r, c]
                if p == "": continue
                if attacker_is_red and not is_red(p): continue
                if (not attacker_is_red) and not is_black(p): continue
                # generate pseudo moves for that piece on this array
                moves = self._generate_piece_moves_at(p, (r, c), board_array)
                for mv in moves:
                    if mv.dest_square_idx == gen_pos:
                        return True
        return False

    # ---------- Public: get_legal_moves (no recursion) ----------
    def get_legal_moves(self):
        pseudo_moves = []
        for r in range(BOARD_SIZE[0]):
            for c in range(BOARD_SIZE[1]):
                p = self.board_array[r, c]
                if p == "": continue
                if self.whose_turn == "w" and not is_red(p): continue
                if self.whose_turn == "b" and not is_black(p): continue
                pseudo_moves.extend(self._generate_piece_moves_at(p, (r, c), self.board_array))

        legal_moves = []
        for mv in pseudo_moves:
            # simulate on raw array (does NOT call make_move)
            new_arr = self._apply_move_array(self.board_array, mv)
            # if own side NOT in check on the resulting array, move is legal
            if not self._is_in_check_on_array(new_arr, self.whose_turn):
                legal_moves.append(mv)
        return legal_moves

    # ---------- Public: make_move (validates against get_legal_moves) ----------
    def make_move(self, move):
        # validate
        legal = self.get_legal_moves()
        found = any((m.src_square_idx == move.src_square_idx and m.dest_square_idx == move.dest_square_idx) for m in legal)
        if not found:
            raise ValueError(f"Illegal move: {move.to_long_algebraic()}")

        # apply move and return new Board
        new_arr = self._apply_move_array(self.board_array, move)
        sr, sc = move.src_square_idx
        dr, dc = move.dest_square_idx
        piece_moved = self.board_array[sr, sc]
        captured = self.board_array[dr, dc]

        # halfmove clock reset on pawn move or capture
        if piece_moved.upper() == "P" or captured != "":
            new_halfmove = 0
        else:
            new_halfmove = self.halfmove_clock + 1

        new_turn = "b" if self.whose_turn == "w" else "w"
        return Board(new_arr, new_turn, new_halfmove)