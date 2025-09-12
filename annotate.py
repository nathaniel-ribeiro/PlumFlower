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
        self._wait_for("uciok")
        self.send("isready")
        self._wait_for("readyok")
        self.send(f"setoption name Threads value {threads}")
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

    def set_position(self, fen):
        self.send(f"position fen {fen}")

    def setup_game(self, move_history):
        moves = " ".join(move_history)
        self.send(f"position startpos moves {moves}")

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

    def evaluate(self, move_history, think_time):
        self.setup_game(move_history)
        self.send(f"go movetime {think_time}")
        lines = self._wait_for("bestmove")
        score = None
        for line in lines:
            if "score cp" in line:
                match = re.search(r"score cp (-?\d+)", line)
                if match:
                    score = int(match.group(1)) / 100.0
            elif "score mate" in line:
                match = re.search(r"score mate (-?\d+)", line)
                if match:
                    mate_in_n = int(match.group(1))
                    score = f"M{mate_in_n}" if mate_in_n > 0 else f"-M{abs(mate_in_n)}"
        return score

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
        # score could be a number or string indicating mate
        if type(score) is float:
            score_red_perspective = score if red_turn else -score
        elif type(score) is str:
            score_red_perspective = score if red_turn else (score[1:] if score.startswith("-") else f"-{score}")
        red_turn = not red_turn

        evaluations.append(score_red_perspective)
        boards.append(board)

    # drop the starting board (ply 0)
    return boards[1:], evaluations[1:]

