import subprocess
from game import Game
import re
from annotate import annotate, PikafishEngine
import pandas as pd
import config
from tqdm import tqdm
import multiprocessing as mp
from multiprocessing import Pool, cpu_count
import time

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

#TODO: remove this, just for testing
games = games[:100]
print("Starting annotations...")

num_workers = cpu_count()

def worker(games_batch):
    engine = PikafishEngine()
    boards, evaluations = list(), list()
    for game in games_batch:
        board, evaluation = annotate(game, engine=engine, think_time=500)
        boards.extend(board)
        evaluations.extend(evaluation)
    engine.quit()
    return boards, evaluations

batch_size = 10
batches = [games[i:i+batch_size] for i in range(0, len(games), batch_size)]

tick = time.time()
with Pool(num_workers) as pool:
    for boards, evaluations in pool.imap_unordered(worker, batches):
        df = pd.DataFrame({'FEN': boards, 'Evaluation': evaluations})
        df.to_csv(
            'annotated_games.csv',
            mode='a',
            header=not pd.io.common.file_exists('annotated_games.csv'),
            index=False
        )

tock = time.time()
total_time = tock - tick
average_time = total_time / len(games)
print(f"Projected total time: {average_time * 150000} s OR {average_time * 2500} mins OR {average_time * 41.67} hours")