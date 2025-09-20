# Rishi (ऋषि)
Searchless transformer-based Xiangqi engine trained off of Pikafish annotations

## What is this?
Rishi (Sanskrit: ऋषि), meaning sage or one who can see divine knowledge in Sanskrit, is an academic project focused on replicating Deepmind's success in searchless chess for the game of Xiangqi (Chinese chess). The goal is not raw playing strength, so this repository is largely unoptimized.

## Data used
[150k tournament games](https://github.com/CGLemon/chinese-chess-PGN)

## Troubleshooting
Encountering a broken pipe error when using the ```PikafishEngine``` interface? Ensure whatever compiler you used to build Pikafish is loaded.

OOM errors in SLURM or job hangs unexpectedly? Reduce ```NUM_WORKERS``` in ```config.py```, overly large values can trigger SLURM errors (reason not exactly known).

## Acknowledgments
A huge thank you to the Xiangqi.com community for directing us towards helpful resources and being very accomodating! Thank you to CGLemon on GitHub for curating a PGN-format dataset of games.
