import unittest
import numpy as np
from game import Board

class TestPawnMoves(unittest.TestCase):
    def test_red_pawn_forward(self):
        # Empty board except for one red pawn
        arr = np.full((10, 9), "", dtype=object)
        arr[6, 4] = "P"  # red pawn at row 6, col 4
        board = Board(arr, "w", 0)
        moves = board.get_legal_moves()
        # Pawn should be able to move forward to (5,4)
        algebraic_moves = [m.to_long_algebraic() for m in moves]
        self.assertIn("e3e4", algebraic_moves)  # check UCI string

if __name__ == "__main__":
    unittest.main()