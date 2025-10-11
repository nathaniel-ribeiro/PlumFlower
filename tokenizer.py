import re

class BoardTokenizer:
    def __init__(self):
        self.metadata_regex = re.compile(r"^([wb]) - - (\d+) (\d+)$")

    def encode(self, fen):
        board, metadata = fen.split(" ", 1)
        rows = board.split("/")
        # replace digit n with n empty square tokens
        rows = "".join([re.sub(r'\d', lambda m: "." * int(m.group(0)), row) for row in rows])
        # use e and E for black and red elephants to disambiguate from whose turn to move
        rows = rows.replace("b", "e").replace("B", "E")
            
        m = self.metadata_regex.match(metadata)
        whose_move = m.group(1)
        # left pad with zeros to ensure fixed length
        capture_clock = m.group(2).zfill(3)
        halfmove_clock = m.group(3).zfill(3)
            
        tokenized = list(rows) + list(whose_move) + list(capture_clock) + list(halfmove_clock)
        # 90 squares + 1 token whose move + 3 digits for capture clock + 3 digits for fullmove clock = 96 tokens
        if(len(tokenized) != 97):
            print(fen)
            raise ValueError(f"Expected tokenized FEN to be 97 chars, got {len(tokenized)}")
        return tokenized