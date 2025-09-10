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

print("Starting annotations...")

def worker(games_batch):
    engine = PikafishEngine(threads=config.PIKAFISH_THREADS)
    boards_for_batch, evaluations_for_batch, game_ids_for_batch = list(), list(), list()
    for game in games_batch:
        boards_for_game, evaluations_for_game = annotate(game, engine=engine, think_time=config.PIKAFISH_MOVETIME_MS)
        boards_for_batch.extend(boards_for_game)
        evaluations_for_batch.extend(evaluations_for_game)
        # add the game id to each board state for that game
        game_ids_for_batch.extend([game.id for _ in range(len(boards_for_game))])
    engine.quit()
    return game_ids_for_batch, boards_for_batch, evaluations_for_batch

batch_size = len(games) // config.NUM_WORKERS if len(games) % config.NUM_WORKERS == 0 else len(games) // config.NUM_WORKERS + 1
batches = [games[i:i+batch_size] for i in range(0, len(games), batch_size)]

tick = time.time()
with Pool(config.NUM_WORKERS) as pool:
    for game_ids, boards, evaluations in pool.imap_unordered(worker, batches):
        df = pd.DataFrame({'Game ID': game_ids,'FEN': boards, 'Evaluation': evaluations})
        df.to_csv(
            f'{config.DATA_DIR}/annotated_games.csv',
            mode='a',
            header=not pd.io.common.file_exists(f'{config.DATA_DIR}/annotated_games.csv'),
            index=False
        )

tock = time.time()
total_time = tock - tick
average_time_per_game = total_time / len(games)
expected_total_seconds = average_time_per_game * 150000
expected_hours = expected_total_seconds / 3600
print(f"Expected time for annotating 150k games: {expected_hours:.1f} h")