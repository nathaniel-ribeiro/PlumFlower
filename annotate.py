import subprocess
import threading
import queue
import re
import config
from game import Game
from functools import cache

engine = None

class PikafishEngine:
    def __init__(self):
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
        self.send(f"position startpos moves {" ".join(moves)}")

    def get_best_move(self, depth=15):
        self.bestmove = None
        self.send(f"go depth {depth}")
        while self.bestmove is None:
            for line in self._flush_output(timeout=0.5):
                if line.startswith("bestmove"):
                    self.bestmove = line.split()[1]
        return self.bestmove

    def evaluate(self, move_history, depth=15):
        score = None
        self.setup_game(move_history)
        self.send(f"go depth {depth}")
        while score is None:
            for line in self._flush_output(timeout=0.5):
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

    def quit(self):
        self.send("quit")
        self.engine.wait()


def annotate(game):
    global engine
    boards = list()
    evaluations = list()

    # only spawn one engine to avoid atrocious overhead
    if engine is None:
        engine = PikafishEngine()

    for ply in range(len(game.move_history)):
        score = engine.evaluate(game.move_history[:ply])
        score_red_perspective = score * (-1)**ply
        print(score_red_perspective)
    print(game.result)

