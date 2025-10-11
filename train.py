import torch
from dataset import AnnotatedBoardsDataset
import config
from tokenizer import BoardTokenizer
from model import TransformerClassifier
from tqdm import tqdm

# TODO: move these args into a config file
N_EPOCHS = 1
BATCH_SIZE = 1024
# Initial learning rate for Adam optimizer
LEARNING_RATE = 1e-4
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

device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = BoardTokenizer(MAX_SEQ_LEN)

train_ds = AnnotatedBoardsDataset(f'{config.DATA_DIR}/train.csv', tokenizer, BOARD_FLIP_P)
val_ds = AnnotatedBoardsDataset(f'{config.DATA_DIR}/val.csv', tokenizer)
test_ds = AnnotatedBoardsDataset(f'{config.DATA_DIR}/test.csv', tokenizer)

train_loader = torch.utils.data.DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_loader = torch.utils.data.DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)
test_loader = torch.utils.data.DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)

VOCAB_SIZE = tokenizer.vocab_size
model = TransformerClassifier(VOCAB_SIZE, MAX_SEQ_LEN).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
criterion = torch.nn.KLDivLoss(reduction="batchmean")

for epoch in range(N_EPOCHS):
    model.train()
    train_loss = 0.0
    total = 0

    # train
    for inputs, labels in tqdm(train_loader):
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs).to(device)
        # KL Divergence expects probabilities in the log-space
        log_outputs = torch.log(outputs + 1e-9)
        # smooth targets to reduce overconfidence in totally winning or dead lost positions
        smoothed_labels = (1 - LABEL_SMOOTHING) * labels + LABEL_SMOOTHING / labels.size(-1)
        loss = criterion(log_outputs, smoothed_labels)
        loss.backward()
        optimizer.step()

        train_loss += loss.item() * inputs.size(0)
        total += inputs.size(0)
    
    avg_train_loss = train_loss / total
    print(f"Average train loss: {avg_train_loss}")
    
    # validate
    val_loss = 0.0
    total = 0
    model.eval()
    with torch.no_grad():
        for inputs, labels in tqdm(val_loader):
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs).to(device)
            # KL Divergence expects probabilities in the log-space
            log_outputs = torch.log(outputs + 1e-9)
            loss = criterion(log_outputs, labels)

            val_loss += loss.item() * inputs.size(0)
            total += inputs.size(0)

    avg_val_loss = val_loss / total
    print(f"Average validation loss: {avg_val_loss}")

torch.save(model.state_dict(), "/models/vanilla_transformer_1.pt")