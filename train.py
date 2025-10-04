import torch
import numpy as np
from dataset import AnnotatedBoardsDataset
import config
from tokenizer import BoardTokenizer

train_ds = AnnotatedBoardsDataset(f'{config.DATA_DIR}/train.csv')
val_ds = AnnotatedBoardsDataset(f'{config.DATA_DIR}/val.csv')
test_ds = AnnotatedBoardsDataset(f'{config.DATA_DIR}/test.csv')

train_loader = torch.utils.data.DataLoader(train_ds, batch_size=512, shuffle=True)
val_loader = torch.utils.data.DataLoader(val_ds, batch_size=512, shuffle=False)
test_loader = torch.utils.data.DataLoader(val_ds, batch_size=512, shuffle=False)

tokenizer = BoardTokenizer()