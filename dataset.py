import torch
import pandas as pd
import numpy as np
from tokenizer import BoardTokenizer

class AnnotatedBoardsDataset(torch.utils.data.Dataset):
    def __init__(self, path_to_csv, board_flip_probability=0.0):
        self.df = pd.read_csv(path_to_csv)
        self.tokenizer = BoardTokenizer()
        self.board_flip_probability = board_flip_probability

    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        # ignore game id and cp evaluation
        _, fen, _, win_prob, draw_prob, lose_prob = tuple(row)
        evaluation = np.array([win_prob, draw_prob, lose_prob], dtype=np.half)
        evaluation = torch.from_numpy(evaluation)

        if np.random.rand() <= self.board_flip_probability:
            fen = self.horizontal_flip(fen)

        fen_tokenized = self.tokenizer.encode(fen)
        return fen_tokenized, evaluation
    
    def horizontal_flip(fen):
        board, metadata = fen.split(" ", 1)
        rows = board.split("/")
        rows_flipped = [row.reverse() for row in rows]
        board_flipped = "/".join(rows_flipped)
        fen_flipped = board_flipped + " " + metadata
        return fen_flipped
