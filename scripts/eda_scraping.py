
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

def perform_eda(event_data_path, player_data_path):
    # Load data
    event_df = pd.read_csv(event_data_path)
    player_df = pd.read_csv(player_data_path)

    print("--- Event Data EDA ---")
    print("\nShape:", event_df.shape)
    print("\nInfo:")
    event_df.info()
    print("\nDescription:")
    print(event_df.describe(include='all'))
    print("\nMissing Values:")
    print(event_df.isnull().sum())

    print("--- Player Data EDA ---")
    print("\nShape:", player_df.shape)
    print("\nInfo:")
    player_df.info()
    print("\nDescription:")
    print(player_df.describe(include='all'))
    print("\nMissing Values:")
    print(player_df.isnull().sum())

    # Example Visualizations (can be expanded)
    plt.figure(figsize=(12, 6))
    sns.countplot(data=event_df, y='type', order=event_df['type'].value_counts().index)
    plt.title('Distribution of Event Types')
    plt.tight_layout()
    plt.savefig('event_type_distribution.png')
    plt.close()

    plt.figure(figsize=(12, 6))
    sns.countplot(data=player_df, y='position', order=player_df['position'].value_counts().index)
    plt.title('Distribution of Player Positions')
    plt.tight_layout()
    plt.savefig('player_position_distribution.png')
    plt.close()

    print("\nEDA complete. Basic plots saved as event_type_distribution.png and player_position_distribution.png")

if __name__ == '__main__':
    perform_eda('EventData.csv', 'PlayerData.csv')
