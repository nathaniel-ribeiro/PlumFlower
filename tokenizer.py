import re

#TODO: can't re-use symbol for black and black elephant
VOCAB = ['r', 'n', 'b', 'a',
         'k', 'c', 'R', 'N',
         'B', 'A', 'K', 'C',
         '.', 'w', 'b', '0',
         '1', '2', '3', '4',
         '5', '6', '7', '8',
         '9', '-']

class FENTokenizer:
    def __init__(self):
        pass

    def encode(fen_batch):
        tokenized_batch = [None] * len(fen_batch)
        for i, fen in enumerate(fen_batch):
            match = re.search(r'([rnbakcRNBAKC0-9]/){9}([rnbakcRNBAKC0-9]) ([wb]) - - (\d+) (\d+)', fen)
            tokenized = ""
            if match:
                # groups 0 through 9 -> rows of the board
                # group 10 -> whose turn
                # group 11 -> moves since capture or pawn move
                # group 12 -> halfmove clock
                rows = [match.group(i) for i in range(10)]
                for row in rows:
                    for char in row:
                        # digit represents number of blank spaces
                        if char.isdigit():
                            tokenized += ("." * int(char))
                        else:
                            tokenized += char
                
                #whose turn
                tokenized += match.group(10)
                # pad moves since capture to be 2 digits
                tokenized += "." + match.group(11) if len(match.group(11)) == 1 else match.group(11)
                # pad half move clock to be 2 digits
                tokenized += "." + match.group(12) if len(match.group(12)) == 1 else match.group(12)
            
            tokenized_batch[i] = tokenized
        return tokenized_batch

    def decode(tokenized_batch):
        pass