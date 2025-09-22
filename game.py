import shortuuid 

class Game:
    def __init__(self, move_history, game_type="Chinese Chess", event=None, site=None, date=None, round_num=None, red_team=None, 
                 red=None, black_team=None, black=None, result=None, opening=None, 
                 startpos_fen="rnbakabnr/9/1c5c1/p1p1p1p1p/9/9/P1P1P1P1P/1C5C1/9/RNBAKABNR w - - 0 1", move_format=None):
        self.id = shortuuid.uuid()
        self.game = game_type
        self.event = event
        self.site = site
        self.date = date
        self.round_num = round_num
        self.red_team = red_team
        self.red = red
        self.black_team = black_team
        self.black = black
        self.result = result
        self.opening = opening
        self.startpos_fen = startpos_fen
        self.move_format = move_format
        self.move_history = move_history
