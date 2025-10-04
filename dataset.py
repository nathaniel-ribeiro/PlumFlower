import torch.nn as nn
import torch.utils.data.Dataset as Dataset
import pandas as pd
import config
from tokenizer import BoardTokenizer

class XQAnnotatedDataset(Dataset):
    def __init__(self, path_to_csv, tokenizer):
        self.df = pd.read_csv(path_to_csv)
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.df)
    
    def __get_item__(self, idx):
        row = self.df.iloc[idx]
        _, fen, _, win_prob, draw_prob, lose_prob = tuple(row)
        fen_tokenized = self.tokenizer.encode(fen)
        return fen_tokenized, (win_prob, draw_prob, lose_prob)

train_ds = XQAnnotatedDataset(f'{config.DATA_DIR}/train.csv', BoardTokenizer())
print(train_ds[0])
