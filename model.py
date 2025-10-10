import torch
import torch.nn as nn
import torch.functional as F

# 8-layer, 8-head transformer
# embedding dim 256
# SwiGLU activation
# learnable positional embeddings
# scaled dot product attention

class RishiTransformer(nn.Module):
    def __init__(self, vocab_size, embedding_dim, out_dim, n_layers, n_heads):
        super(RishiTransformer, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        encoder_layer = nn.TransformerEncoderLayer(embedding_dim, n_heads)
        self.encoder = nn.TransformerEncoder(encoder_layer, n_layers)
        self.linear1 = nn.Linear(embedding_dim, embedding_dim)
        self.linear2 = nn.Linear(embedding_dim, out_dim)
    
    def forward(self, x):
        x = self.embedding(x)
        x = self.encoder(x)
        x = self.linear1(x)
        x = F.relu(x)
        x = self.linear2(x)
        x = torch.softmax(x, dim=-1)
        return x