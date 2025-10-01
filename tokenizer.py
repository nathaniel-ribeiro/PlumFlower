import re

class BoardTokenizer:
    def __init__(self):
        pass

    def encode(fen_batch):
        tokenized_batch = [None] * len(fen_batch)
        for i, fen in enumerate(fen_batch):
            match = re.search(r'([rnbakcRNBAKC0-9]/){9}([rnbakcRNBAKC0-9]) ([wb]) - - (\d+) (\d+)', fen)
            tokenized = None
            if match:
                rows = "".join([re.sub(r'\d', lambda match: "." * int(match), match.group(i)) for i in range(10)])
                # uses e and E to denote black and red elephants rather than b (already used in FEN to show black to move)
                rows = rows.replace("b", "e")
                rows = rows.replace("B", "E")
                
                whose_turn = match.group(10)
                # left pad with zeros to ensure a fixed length
                capture_clock = match.group(11).zfill(2)
                halfmove_clock = match.group(12).zfill(3)
                tokenized =  list(rows) + list(whose_turn) + list(capture_clock) + list(halfmove_clock)
            
            tokenized_batch[i] = tokenized
        return tokenized_batch