from sklearn.model_selection import train_test_split
import pandas as pd
import config

if __name__ == "__main__":
    df = pd.read_csv(f"{config.DATA_DIR}/annotated_games.csv")
    df.info(memory_usage='deep')

    unique_game_ids = df['Game ID'].unique()
    # split game ids into 80% train, 10% val, 10% test
    train_ids, val_test_ids = train_test_split(unique_game_ids, test_size=0.2, random_state=42)
    val_ids, test_ids = train_test_split(val_test_ids, test_size=0.5, random_state=42)

    train_df = df[df['Game ID'].isin(train_ids)].copy()
    val_df = df[df['Game ID'].isin(val_ids)].copy()
    test_df = df[df['Game ID'].isin(test_ids)].copy()

    # remove duplicate boards within folds but NOT across folds
    train_df.drop_duplicates(subset=['FEN'], inplace=True)
    val_df.drop_duplicates(subset=['FEN'], inplace=True)
    test_df.drop_duplicates(subset=['FEN'], inplace=True)

    train_df.to_csv(f'{config.DATA_DIR}/train.csv', index=False)
    val_df.to_csv(f'{config.DATA_DIR}/val.csv', index=False)
    test_df.to_csv(f'{config.DATA_DIR}/test.csv', index=False)
