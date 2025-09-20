import os
from multiprocessing import cpu_count
import math

# too many engines will cause OOM errors in SLURM
NUM_WORKERS = 8
# path to executable to run pikafish engine. File needs execution permissions and compiler used to build must be available!
PATH_TO_PIKAFISH_BINARY = os.path.expanduser("~/Pikafish/src/pikafish")
# directory where PGN files for training and CSV of board states with annotations should be saved
DATA_DIR = "./data"
# time that engine will think before producing the best move. Deepmind used 50 ms
PIKAFISH_MOVETIME_MS = 50
# Stockfish/Pikafish recommends num_cores * 2 - 1
PIKAFISH_THREADS = 4