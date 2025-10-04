import torch
import pandas as pd
import numpy as np

class AnnotatedBoardsDataset(torch.utils.data.Dataset):
    def __init__(self, path_to_csv):
        self.df = pd.read_csv(path_to_csv)

    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        # ignore game id and cp evaluation
        _, fen, _, win_prob, draw_prob, lose_prob = tuple(row)
        evaluation = np.array([win_prob, draw_prob, lose_prob], dtype=np.half)
        evaluation = torch.from_numpy(evaluation)
        return fen, evaluation
