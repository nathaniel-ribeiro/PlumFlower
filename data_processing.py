import subprocess
from game import Game
import re
from oracle import annotate_game, PikafishEngine
import pandas as pd
import config
from tqdm import tqdm
import multiprocessing as mp
from multiprocessing import Pool
import time
import os
import shutil
import polars as pl
import math

# extract all PGN game files
result = subprocess.run(f"find {config.DATA_DIR} -type f -name '*.pgns'", shell=True, check=True, capture_output=True)
filenames = result.stdout.decode('utf-8').splitlines()

games = list()
for filename in filenames:
    with open(filename, encoding='utf-8') as f:
        contents = f.read()
    
    games_info = [game_info.strip() for game_info in contents.split('\n\n') if game_info.strip()]

    print("Importing PGN files...")
    for game_info in tqdm(games_info):
        # extract metadata such as player names and event date
        metadata_matches = re.findall(r'^\[(\w+)\s+"(.*?)"\]$', game_info, flags=re.MULTILINE)
        metadata = {key: value for key, value in metadata_matches}

        # converts move history from more human readable format -> simple list of long algebraic moves
        moves_text = re.sub(r'^\[.*\]$', '', game_info, flags=re.MULTILINE)
        moves_text = re.sub(r'\d+-\d+$', '', moves_text, flags=re.MULTILINE)
        moves = re.findall(r'\b([A-I0-9]+-[A-I0-9]+)\b', moves_text)
        moves = [m.lower().replace('-', '') for m in moves]

        # dirty hack to trim off stray numbers that get appended, fix the regex later
        if(moves[-1].isdigit()):
            moves = moves[:-1]
        
        game = Game(moves, *metadata.values())
        games.append(game)

print("Starting annotations...")

def worker(args):
    indices, me = args
    engine = PikafishEngine(threads=config.PIKAFISH_THREADS)

    out_path = os.path.join(config.DATA_DIR, f"annotated_worker_{me}.csv")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("Game ID,FEN,Evaluation\n")
        for idx in indices:
            game = games[idx]   # games is global and already in memory
            boards, evals = annotate_game(game, engine=engine,
                                          think_time=config.PIKAFISH_MOVETIME_MS)
            for fen, val in zip(boards, evals):
                f.write(f"{game.id},{fen},{val}\n")
            f.flush()
    engine.quit()
    return out_path

n = len(games)
batch_size = math.ceil(n / config.NUM_WORKERS)
batches = [
    (range(i*batch_size, min((i+1)*batch_size, n)), i)
    for i in range(config.NUM_WORKERS)
]

with Pool(config.NUM_WORKERS) as pool:
    # each worker writes directly to its own CSV file
    partial_files = list(tqdm(pool.imap_unordered(worker, batches), total=config.NUM_WORKERS))

aggregated_path = f"{config.DATA_DIR}/annotated_games.csv"

# combine results of workers
with open(aggregated_path, "w", encoding="utf-8") as fout:
    fout.write("Game ID,FEN,Evaluation\n")

    for tmp_path in partial_files:
        with open(tmp_path, "r", encoding="utf-8") as fin:
            next(fin)
            shutil.copyfileobj(fin, fout)

# cleanup
for f in partial_files:
    os.remove(f)

# deduplicate board states
final_path = f"{config.DATA_DIR}/annotated_games_deduplicated.csv"
# specify schema to be all strings since evaluation can be a number or "M..."
pl.scan_csv(aggregated_path, schema={"Game ID": pl.String, "FEN": pl.String, "Evaluation": pl.String}).unique(subset=["FEN"]).collect(engine="streaming").write_csv(final_path)