import pandas as pd
from oracle import PikafishEngine
import config
from game import Game
import time
import os
from argparse import ArgumentParser

def Full_Puzzle_Test(save_results = False):
    #Read csv
    file_dir = "~/Rishi/data/puzzles_data_5000.csv"
    df = pd.read_csv(file_dir)

    #Start engine
    engine = PikafishEngine(threads=config.PIKAFISH_THREADS)
    Success = 0
    Alternate_Success = 0
    Fail = 0
    Puzzle_Count = 1
    results = []
    start_time = time.time()

    #For each puzzle, generate fen
    #Then, calculate answers
    for pid, group in df.groupby("puzzle_id"):
        group = group.sort_values("index", kind="stable")
        engine.new_game()
        preset = group.loc[~group["is_solution_move"], "move"].tolist()
        solution = group.loc[group["is_solution_move"], "move"].tolist()
        #Only applies to our current puzzle set since everything is "Mate in N" puzzles
        category = int(group["category"].iloc[0][-1:])

        fen = engine.get_fen_after_moves(preset)

        puzzle_solved = Solve_Puzzle(engine,fen,solution,category)

        result_log = "Puzzle "+ str(Puzzle_Count) + " | pid = " + pid #+ " | category = " + group["category"].iloc[0]

        if(puzzle_solved): 
            Success += 1
            print(result_log + " | Success")
            results.append({"puzzle_index": Puzzle_Count, "pid": pid, "category": group["category"].iloc[0], "result": "Success"})
        elif(Check_Alternate_Answer(engine,fen,category)):
            Alternate_Success += 1
            print(result_log + " | Success(Alternate Solution)")
            results.append({"puzzle_index": Puzzle_Count, "pid": pid, "category": group["category"].iloc[0], "result": "Success(Alternate Solution)"})
        else: 
            Fail += 1
            print(result_log + " | Fail")
            results.append({"puzzle_index": Puzzle_Count, "pid": pid, "category": group["category"].iloc[0], "result": "Fail"})
        Puzzle_Count += 1

    print("Success : "+ str(Success))
    print("Alternate Success : "+ str(Alternate_Success))
    print("Fail : "+ str(Fail))
    print("Accuracy : " + str((Success+Alternate_Success)/(Success+Alternate_Success+Fail)*100) + "%")
    print("Elapsed Time : " + str(time.time()-start_time) + "s")

    if(save_results):
        out_path = os.path.expanduser("~/Rishi/data/pikafish_puzzle_results.csv")
        pd.DataFrame(results).to_csv(out_path, index=False)

    engine.quit()

def Puzzle_Test(pid):
    #Read csv
    file_dir = "~/Rishi/data/puzzles_data_5000.csv"
    df = pd.read_csv(file_dir)

    #Start engine
    engine = PikafishEngine(threads=config.PIKAFISH_THREADS)
    start_time = time.time()

    puzzle = df[df["puzzle_id"] == pid].copy()
    if puzzle.empty:
        raise ValueError(f"puzzle_id {pid!r} not found")
    
    puzzle = puzzle.sort_values("index", kind="stable")
    engine.new_game()
    preset = puzzle.loc[~puzzle["is_solution_move"], "move"].tolist()
    solution = puzzle.loc[puzzle["is_solution_move"], "move"].tolist()
    #Only applies to our current puzzle set since everything is "Mate in N" puzzles
    category = int(puzzle["category"].iloc[0][-1:])

    fen = engine.get_fen_after_moves(preset)
    print(fen)
    
    puzzle_solved = Solve_Puzzle(engine,fen,solution,category,True)
    print(category)

    if(puzzle_solved): print("Success")
    elif(Check_Alternate_Answer(engine,fen,category)): print("Success(Alternate Solution)")
    else:print("Fail")
        
    engine.quit()

#Solve a single puzzle with the fen and solution as parameters
def Solve_Puzzle(engine,fen,solution,category,single_test = False):
    engine.new_game()
    engine.set_position(fen)
    puzzle_solved = True
    for i in range(0,len(solution),2):
        best_move = engine.get_best_move(config.PIKAFISH_MOVETIME_MS)
        
        #For Debugging Issues
        if(single_test):
            print("Solution : " + solution[i])
            print("Pikafish Best Move : " + best_move)
            print()
        if best_move != solution[i]:
            puzzle_solved = False
            break
        engine.play_moves(fen,tuple(solution[:i+2]))
     
    return puzzle_solved

#Check if Pikafish's answer is still Mate in N
def Check_Alternate_Answer(engine,fen,category):
    engine.new_game()
    engine.set_position(fen)
    for i in range(category):
        best_move = engine.get_best_move(config.PIKAFISH_MOVETIME_MS)
        fen = engine.play_moves(fen,[best_move])
        #Opponent's optimal move
        if i!=category-1:
            best_move = engine.get_best_move(config.PIKAFISH_MOVETIME_MS)
            fen = engine.play_moves(fen,[best_move])
    return engine.is_checkmate(config.PIKAFISH_MOVETIME_MS)

#No arg : run all
#-a : run all and save results in csv
#-p puzzle_id : run just that puzzle printint each move
def main():
    parser = ArgumentParser(description="Pikafish puzzle solver")
    parser.add_argument("-a", "--all", action="store_true", help="solve all puzzles(default)")
    parser.add_argument("-p", "--puzzle-id", dest="puzzle_id", help="solve a single puzzle_id")
    args = parser.parse_args()

    if args.puzzle_id:
        Puzzle_Test(args.puzzle_id)
    elif args.all:
        Full_Puzzle_Test(True)
    else:
        Full_Puzzle_Test() 

if __name__ == "__main__":
    main()