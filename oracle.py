import subprocess
import threading
import queue
import re
import config

class PikafishEngine:
    def __init__(self, threads):
        self.engine = subprocess.Popen(
            [config.PATH_TO_PIKAFISH_BINARY],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=4096
        )

        self.output_queue = queue.Queue()
        threading.Thread(
            target=self._reader_thread,
            args=(self.engine.stdout,),
            daemon=True
        ).start()

        threading.Thread(
            target=self._reader_thread,
            args=(self.engine.stderr,),
            daemon=True
        ).start()

        self.send("uci")
        _ = self._wait_for("uciok")
        self.send("isready")
        _ = self._wait_for("readyok")
        self.send(f"setoption name Threads value {threads}")
        _ = self._wait_for("info string Using")
        self.send("setoption name UCI_ShowWDL value true")
        self.bestmove = None

    def _reader_thread(self, pipe):
        for line in iter(pipe.readline, ''):
            self.output_queue.put(line.rstrip())

    def send(self, cmd):
        self.engine.stdin.write(cmd + "\n")
        self.engine.stdin.flush()

    def _wait_for(self, token):
        """Block until a line containing `token` is seen; return all lines."""
        lines = []
        while True:
            line = self.output_queue.get()
            lines.append(line)
            if token in line:
                break
        return lines
    
    def new_game(self):
        self.send("ucinewgame")
        self.send("isready")
        _ = self._wait_for("readyok")

    def set_position(self, fen):
        self.send(f"position fen {fen}")

    def setup_game(self, move_history):
        moves = " ".join(move_history)
        self.send(f"position startpos moves {moves}")

    #Send ucinewgame
    def new_game(self):
        self.send("ucinewgame"); 
        self.send("isready"); 
        self._wait_for("readyok")

    #Play moves from a given FEN and return the new FEN
    def play_moves(self, fen, moves):
        moves_str = " ".join(moves)
        self.send(f"position fen {fen} moves {moves_str}")
        self.send("d")
        lines = self._wait_for("Fen:")
        fen = None
        for line in lines:
            match = re.search(r"Fen: (.+)", line)
            if match:
                fen = match.group(1)
                break
        return fen

    def is_checkmate(self, think_time):
        self.send(f"go movetime {think_time}")
        lines = self._wait_for("bestmove")
        for line in lines:
            line = line.strip()
            if "score mate 0" in line:
                return True
        return False

    def get_fen_after_moves(self, moves):
        self.setup_game(moves)
        self.send("d")
        lines = self._wait_for("Fen:")
        fen = None
        for line in lines:
            match = re.search(r"Fen: (.+)", line)
            if match:
                fen = match.group(1)
                break
        return fen

    def get_best_move(self, think_time):
        self.send(f"go movetime {think_time}")
        lines = self._wait_for("bestmove")
        for line in lines:
            if line.startswith("bestmove"):
                return line.split()[1]
        return None

    def get_all_legal_moves(self):
        self.send("go perft 1")
        lines = self._wait_for("Nodes")
        legal_moves = []
        for line in lines:
            if line.startswith("info") or line.startswith("Nodes") or len(line)==0:
                continue
            parts = line.split(":")
            
            move = parts[0].strip()
            legal_moves.append(move)

        return legal_moves

    def get_all_legal_move_successors(self, fen, think_time = 50):
        self.new_game()
        self.set_position(fen)
        legal_moves = self.get_all_legal_moves()

        top_moves = []
        
        for move in legal_moves:
            self.send(f"position fen {fen}")
            self.send(f"go movetime {think_time} searchmoves {move}")
            lines = self._wait_for("bestmove")
            # n = len(lines)-2
            maxdepth = 0
            final_score = None
            numeric_eval = None #for sorting purposes

            #Fetch score from deepest search where it is not upperbound
            # if("upperbound" in lines[n]):
            #     n-=1
            # line = lines[n]
            # match_score = re.search(r"score (cp|mate) (-?\d+)", line)
            # kind, val = match_score.groups()
            # final_score = f"{kind} {val}"
            # if kind == "mate":
            #     m = int(val)
            #     if m > 0:
            #         numeric_eval = 1_000_000 - m
            #     else:
            #         numeric_eval = -1_000_000 - m
            # else:
            #     numeric_eval = int(val)
            for line in lines:
                if not (line.startswith("info") and "pv" in line):
                    continue
                if "upperbound" in line or "lowerbound" in line:
                    continue

                currdepth = int(re.search(r"\bdepth (\d+)", line).group(1))
                if(currdepth < maxdepth):
                    continue
                maxdepth = currdepth

                #fetch evaluation
                match_score = re.search(r"score (cp|mate) (-?\d+)", line)
                if match_score:
                    kind, val = match_score.groups()
                    final_score = f"{kind} {val}"
                    if kind == "mate":
                        m = int(val)
                        if m > 0:
                            numeric_eval = 1_000_000 - m
                        else:
                            numeric_eval = -1_000_000 - m
                    else:
                        numeric_eval = int(val)
            
            new_fen = self.play_moves(fen,[move])

            top_moves.append({
                "move" : move,
                "score" : final_score,
                "numeric_eval" : numeric_eval,
                "fen" : new_fen
            })

        top_moves.sort(key=lambda x: (x["numeric_eval"] if x["numeric_eval"] is not None else -999999), reverse=True)

        return top_moves


    def evaluate(self, move_history, think_time):
        '''
        @param move_history: list of moves in long algebraic notation to setup position
        @param think_time: how long should Pikafish think before giving an evaluation?
        returns: tuple containing centipawn evaluation (unnormalized) and wdl probabilities (normalized)

        Evaluates the board resulting from the given move_history using Pikafish. 
        Evaluations are from *current* player's perspective.
        '''
        self.setup_game(move_history)
        self.send(f"go movetime {think_time}")
        lines = self._wait_for("bestmove")
        centipawns, win_prob, draw_prob, lose_prob = None, None, None, None
        for line in lines:
            if "wdl" in line:
                match = re.search(r"wdl (\d+) (\d+) (\d+)", line)
                if match:
                    win_prob = int(match.group(1)) / 1000
                    draw_prob = int(match.group(2)) / 1000
                    lose_prob = int(match.group(3)) / 1000
            if "score cp" in line:
                match = re.search(r"score cp (-?\d+)", line)
                if match:
                    centipawns = int(match.group(1))
            elif "score mate" in line:
                match = re.search(r"score mate (-?\d+)", line)
                if match:
                    mate_in_n = int(match.group(1))
                    centipawns = f"M{mate_in_n}" if mate_in_n > 0 else f"-M{abs(mate_in_n)}"
                # handle cases where we/they are already checkmated
                if centipawns == "M0":
                    win_prob = 1.0
                    draw_prob = 0.0
                    lose_prob = 0.0
                elif centipawns == "-M0":
                    win_prob = 0.0
                    draw_prob = 0.0
                    lose_prob = 1.0
        return centipawns, win_prob, draw_prob, lose_prob

    def quit(self):
        self.send("quit")
        self.engine.wait()



def annotate_game(game, engine, think_time):
    boards = list()
    evaluations = list()

    for ply in range(len(game.move_history)):
        board = engine.get_fen_after_moves(game.move_history[:ply])
        centipawns, win_prob, draw_prob, lose_prob = engine.evaluate(game.move_history[:ply], think_time)
        evaluations.append((centipawns, win_prob, draw_prob, lose_prob))
        boards.append(board)
        
    return boards, evaluations

