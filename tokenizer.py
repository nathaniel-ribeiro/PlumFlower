import re

FEN_METADATA_REGEX = re.compile(
    r"^([wb]) - - (\d+) (\d+)$"
)

class BoardTokenizer:
    def __init__(self):
        pass

    def encode(self, fen_batch):
        tokenized_batch = [None] * len(fen_batch)
        for i, fen in enumerate(fen_batch):
            board, metadata = fen.split(" ", 1)
            rows = board.split("/")
            # replace digit n with n empty square tokens
            rows = "".join([re.sub(r'\d', lambda m: "." * int(m.group(0)), row) for row in rows])
            # use e and E for black and red elephants to disambiguate from whose turn to move
            rows = rows.replace("b", "e").replace("B", "E")
            
            m = FEN_METADATA_REGEX.match(metadata)
            whose_move = m.group(1)
            # left pad with zeros to ensure fixed length
            capture_clock = m.group(2).zfill(2)
            halfmove_clock = m.group(3).zfill(3)
            
            tokenized = list(rows) + list(whose_move) + list(capture_clock) + list(halfmove_clock)
            # 90 squares + 1 token whose move + 2 digits for capture clock + 3 digits for halfmove clock = 95 tokens
            assert len(tokenized) == 96
            tokenized_batch[i] = tokenized
        return tokenized_batch