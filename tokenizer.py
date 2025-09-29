import re

VOCAB = ['r', 'n', 'b', 'a',
         'k', 'c', 'R', 'N',
         'B', 'A', 'K', 'C',
         '.', 'w', '0',
         '1', '2', '3', '4',
         '5', '6', '7', '8',
         '9']

class FENTokenizer:
    def __init__(self):
        pass

    def encode(fen_batch):
        tokenized_batch = [None] * len(fen_batch)
        for i, fen in enumerate(fen_batch):
            match = re.search(r'([rnbakcRNBAKC0-9]/){9}([rnbakcRNBAKC0-9]) ([wb]) - - (\d+) (\d+)', fen)
            tokenized = None
            if match:
                rows = [re.sub(r'\d', lambda match: "." * int(match), match.group(i)) for i in range(10)]
                whose_turn = match.group(10)
                capture_clock = match.group(11).zfill(2)
                halfmove_clock = match.group(12).zfill(3)
                tokenized = rows.split() + [whose_turn] + capture_clock.split() + halfmove_clock.split()
            
            tokenized_batch[i] = tokenized
        return tokenized_batch

    def decode(tokenized_batch):
        pass