import torch
from dataset import AnnotatedBoardsDataset
import config
from tokenizer import BoardTokenizer
from model import TransformerClassifier
from tqdm import tqdm

N_EPOCHS = 1
BATCH_SIZE = 512
LEARNING_RATE = 1e-4
BOARD_FLIP_P = 0.5
TOKEN_MASKING_P = 0.0
D_MODEL = 256
VOCAB_SIZE = 29
MAX_SEQ_LEN = 96
LABEL_SMOOTHING = 0.0

device = "cuda" if torch.cuda.is_available() else "cpu"
tokenizer = BoardTokenizer()

train_ds = AnnotatedBoardsDataset(f'{config.DATA_DIR}/train.csv', tokenizer, BOARD_FLIP_P, TOKEN_MASKING_P)
val_ds = AnnotatedBoardsDataset(f'{config.DATA_DIR}/val.csv', tokenizer)
test_ds = AnnotatedBoardsDataset(f'{config.DATA_DIR}/test.csv', tokenizer)

train_loader = torch.utils.data.DataLoader(train_ds, batch_size=BATCH_SIZE, shuffle=True)
val_loader = torch.utils.data.DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)
test_loader = torch.utils.data.DataLoader(val_ds, batch_size=BATCH_SIZE, shuffle=False)

#TODO: don't hardcode vocab size, move to global scope instead of being part of dataset?
#TODO: add decode() method to tokenizer so conversion to token indices can happen in tokenizer
model = TransformerClassifier(VOCAB_SIZE, MAX_SEQ_LEN).to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
criterion_train = torch.nn.CrossEntropyLoss(label_smoothing=LABEL_SMOOTHING).to(device)
criterion_val = torch.nn.CrossEntropyLoss().to(device)

for epoch in range(N_EPOCHS):
    model.train()
    train_loss = 0.0
    total = 0

    # train
    for inputs, labels in tqdm(train_loader):
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs).to(device)
        loss = criterion_train(outputs, labels)
        loss.backward()
        optimizer.step()

        train_loss += loss.item() * inputs.size(0)
        total += inputs.size(0)
    
    avg_train_loss = train_loss / total
    print(avg_train_loss)
    
    # validate
    val_loss = 0.0
    total = 0
    model.eval()
    with torch.no_grad():
        for inputs, labels in tqdm(val_loader):
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs).to(device)
            loss = criterion_val(outputs, labels)

            val_loss += loss.item() * inputs.size(0)
            total += inputs.size(0)

    avg_val_loss = val_loss / total
    print(avg_val_loss)