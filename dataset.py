import torch
import pandas as pd
import numpy as np
from tokenizer import BoardTokenizer

class AnnotatedBoardsDataset(torch.utils.data.Dataset):
    def __init__(self, path_to_csv, board_flip_probability=0.0, mask_token_probability=0.0):
        self.df = pd.read_csv(path_to_csv)
        self.tokenizer = BoardTokenizer()
        self.board_flip_probability = board_flip_probability
        self.mask_token_probability = mask_token_probability
        self.vocab = ['K', 'A', 'E', 'R', 'C', 'N', 'P',
                      'k', 'a', 'e', 'r', 'c', 'n', 'p',
                      '0', '1', '2', '3', '4', '5', '6',
                      '7', '8', '9', '0', 'w', 'b', '.',
                      '[MASK]']
        
        self.vocab_to_idx = dict(zip(self.vocab, range(len(self.vocab))))
    
    def horizontal_flip(self, fen):
        print(fen)
        board, metadata = fen.split(" ", 2)
        rows = board.split("/")
        rows_flipped = [row.reverse() for row in rows]
        board_flipped = "/".join(rows_flipped)
        fen_flipped = board_flipped + " " + metadata
        return fen_flipped

    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        # ignore game id and cp evaluation
        _, fen, _, win_prob, draw_prob, lose_prob = tuple(row)
        evaluation = np.array([win_prob, draw_prob, lose_prob], dtype=np.half)
        evaluation = torch.from_numpy(evaluation)

        # if np.random.rand() <= self.board_flip_probability:
        #     fen = self.horizontal_flip(fen)

        fen_tokenized = self.tokenizer.encode(fen)
        
        if self.mask_token_probability > 0.0:
            for i, token in enumerate(fen_tokenized):
                # don't mask these since the WDL probs are from current player perspective
                if token == "w" or token == "b":
                    continue
                fen_tokenized[i] = "[MASK]" if np.random.rand() <= self.mask_token_probability else fen_tokenized[i]
        
        # convert tokens to their corresponding indices in the vocab, uint8 ok here since |V| \leq 256
        fen_tokenized_indices = np.array([self.vocab_to_idx[token] for token in fen_tokenized], dtype=np.uint8)
        fen_tokenized_indices = torch.from_numpy(fen_tokenized_indices)
        return fen_tokenized_indices, evaluation

if __name__ == "__main__":
    ds = AnnotatedBoardsDataset("./data/train.csv", 0.5, 0.0)
    print(ds[0])
