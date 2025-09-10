import os
from multiprocessing import cpu_count

NUM_WORKERS = 1
# path to executable to run pikafish engine. File needs execution permissions and compiler used to build must be available!
PATH_TO_PIKAFISH_BINARY = os.path.expanduser("~/Pikafish/src/pikafish")
# directory where PGN files for training and CSV of board states with annotations should be saved
DATA_DIR = "./data"
# time that engine will think before producing the best move. Deepmind used 50 ms
PIKAFISH_MOVETIME_MS = 50
# Stockfish/Pikafish recommends num_cores * 2 - 1
PIKAFISH_THREADS = cpu_count() * 2 - 1