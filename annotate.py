import subprocess
import threading
import queue
import re
import config
from functools import cache

class PikafishEngine:
    def __init__(self, threads):
        self.engine = subprocess.Popen(
            [config.PATH_TO_PIKAFISH_BINARY],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self.output_queue = queue.Queue()
        threading.Thread(target=self._reader_thread, args=(self.engine.stdout,), daemon=True).start()
        threading.Thread(target=self._reader_thread, args=(self.engine.stderr,), daemon=True).start()

        self.send(f"setoption name Threads value {threads}")
        self.send("uci")
        self.send("isready")
        self._flush_output(timeout=1)
        self.bestmove = None

    def _reader_thread(self, pipe):
        for line in iter(pipe.readline, ''):
            self.output_queue.put(line.strip())

    def send(self, cmd):
        self.engine.stdin.write(cmd + "\n")
        self.engine.stdin.flush()

    def _flush_output(self, timeout=0.1):
        lines = []
        while True:
            try:
                lines.append(self.output_queue.get(timeout=timeout))
            except queue.Empty:
                break
        return lines

    def set_position(self, fen):
        self.send(f"position fen {fen}")
    
    def setup_game(self, moves):
        move_history = " ".join(moves)
        self.send(f"position startpos moves {move_history}")

    def get_fen_after_moves(self, moves):
        self.setup_game(moves)
        self.send("d")
        fen = None
        while fen is None:
            for line in self._flush_output(timeout=0.1):
                match = re.search(r"Fen: (.+)", line)
                if match:
                    fen = match.group(1)
        return fen

    def get_best_move(self, think_time):
        self.bestmove = None
        self.send(f"go movetime {think_time}")
        while self.bestmove is None:
            for line in self._flush_output(timeout=0.1):
                if line.startswith("bestmove"):
                    self.bestmove = line.split()[1]
        return self.bestmove

    def evaluate(self, move_history, think_time):
        @cache
        def _evaluate(move_history_str, think_time):
            score = None
            self.setup_game(move_history_str.split())
            self.send(f"go movetime {think_time}")
            while score is None:
                for line in self._flush_output(timeout=0.1):
                    # Engine info lines for evaluation look like: "info depth 15 score cp 34 ..."
                    if "score cp" in line:
                        match = re.search(r"score cp (-?\d+)", line)
                        if match:
                            score = int(match.group(1)) / 100.0  # convert centipawns to pawns
                    elif "score mate" in line:
                        match = re.search(r"score mate (-?\d+)", line)
                        if match:
                            score = 1000 if int(match.group(1)) > 0 else -1000
                    if "bestmove" in line:
                        break
            return score
        
        return _evaluate(" ".join(move_history), think_time)

    def quit(self):
        self.send("quit")
        self.engine.wait()


def annotate(game, engine, think_time):
    boards = list()
    evaluations = list()
    red_turn = True
    for ply in range(len(game.move_history)):
        board = engine.get_fen_after_moves(game.move_history[:ply])
        score = engine.evaluate(game.move_history[:ply], think_time)
        score_red_perspective = score if red_turn else -score
        red_turn = not red_turn

        evaluations.append(score_red_perspective)
        boards.append(board)

    # drop the starting board (ply 0)
    return boards[1:], evaluations[1:]

