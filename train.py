import torch
from dataset import AnnotatedBoardsDataset
import config
from tokenizer import BoardTokenizer
from model import TransformerClassifier
import numpy as np
import time

# TODO: move these args into a config file
MAX_EPOCHS = 100
# batch size of 1024 requires ~20 GB VRAM, batch size of 2048 requires ~40 GB
BATCH_SIZE = 1024
PATIENCE = 3
# Initial learning rate for Adam optimizer
LEARNING_RATE = 1e-3
# probability of horizontally flipping the board for data augmentation
# Range: [0.0, 1.0]
BOARD_FLIP_P = 0.5
# embedding dimension
D_MODEL = 256
# number of heads in each transformer encoder layer.
N_HEADS = 8
# number of layers in the transformer encoder.
N_LAYERS = 8
# 90 tokens for board + 1 token for whose turn + 3 tokens halfmove clock + 3 tokens fullmove clock
MAX_SEQ_LEN = 97
# blends Pikafish WDL probabilities with a uniform distribution.
# Range: [0.0, 1.0]
# 0.0 is no smoothing, 1.0 smooths all targets to be the uniform distribution
LABEL_SMOOTHING = 0.05
DROPOUT = 0.2

device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = BoardTokenizer(MAX_SEQ_LEN)

train_ds = AnnotatedBoardsDataset(f'{config.DATA_DIR}/train.csv', tokenizer, BOARD_FLIP_P)
val_ds = AnnotatedBoardsDataset(f'{config.DATA_DIR}/val.csv', tokenizer)
test_ds = AnnotatedBoardsDataset(f'{config.DATA_DIR}/test.csv', tokenizer)

print("Created datasets!")

train_loader = torch.utils.data.DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_loader = torch.utils.data.DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)
test_loader = torch.utils.data.DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)

VOCAB_SIZE = tokenizer.vocab_size
model = TransformerClassifier(VOCAB_SIZE, MAX_SEQ_LEN, D_MODEL, 3, N_LAYERS, N_HEADS, DROPOUT).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
criterion = torch.nn.KLDivLoss(reduction="batchmean")

parameter_count = sum(p.numel() for p in model.parameters())
print(f"Model has {parameter_count/1e6:.1f} M params")
old_val_loss = np.inf
patience = PATIENCE
scaler = torch.amp.GradScaler(device)
for epoch in range(MAX_EPOCHS):
    model.train()
    train_loss = 0.0
    total = 0

    # train
    tick = time.time()
    for inputs, labels in train_loader:
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        with torch.autocast(device_type=device):
            outputs = model(inputs)
            # KL Divergence expects probabilities in the log-space
            log_outputs = torch.log(outputs + 1e-8)
            # smooth targets to reduce overconfidence in totally winning or dead lost positions
            smoothed_labels = (1 - LABEL_SMOOTHING) * labels + LABEL_SMOOTHING / labels.size(-1)
            loss = criterion(log_outputs, smoothed_labels)
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()

        train_loss += loss.item() * inputs.size(0)
        total += inputs.size(0)
    
    avg_train_loss = train_loss / total
    
    # validate
    val_loss = 0.0
    total = 0
    model.eval()
    with torch.no_grad():
        with torch.autocast(device_type=device):
            for inputs, labels in val_loader:
                inputs, labels = inputs.to(device), labels.to(device)
                outputs = model(inputs)
                # KL Divergence expects probabilities in the log-space
                log_outputs = torch.log(outputs + 1e-8)
                loss = criterion(log_outputs, labels)

                val_loss += loss.item() * inputs.size(0)
                total += inputs.size(0)

    avg_val_loss = val_loss / total
    if device == "cuda": torch.cuda.synchronize()
    tock = time.time()
    elapsed_mins = (tock - tick) // 60

    print(f"Losses for epoch {epoch}: \t Train: {avg_train_loss:.3f} \t Val: {avg_val_loss:.3f} \t in {elapsed_mins} mins")
    if avg_val_loss < old_val_loss:
        patience = PATIENCE
    else:
        patience -= 1

    if patience <= 0:
        break
    old_val_loss = avg_val_loss

torch.save(model.state_dict(), "./models/rishi.pt")