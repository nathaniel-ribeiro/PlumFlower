import numpy as np
from oracle import PikafishEngine
from multiprocessing import cpu_count
import time
from tqdm import tqdm

if __name__ == "__main__":
    movetimes_to_try = np.linspace(99, 999, 16)
    # starting position
    move_history = ""
    overhead_factors = np.zeros(movetimes_to_try.shape[0])
    evaluations = list()
    for i, movetime_ms in tqdm(enumerate(movetimes_to_try), total=len(movetimes_to_try)):
        engine = PikafishEngine(threads = cpu_count() * 2 - 1)
        tick = time.time()
        evaluation = engine.evaluate(move_history=move_history, think_time=movetime_ms)
        evaluations.append(evaluation)
        tock = time.time()
        actual_time = tock - tick
        overhead_factor = (actual_time * 1000) / movetime_ms
        overhead_factors[i] = overhead_factor
        engine.quit()
    
    print(overhead_factors)
    print(evaluations)