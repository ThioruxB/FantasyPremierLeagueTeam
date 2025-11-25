
import requests
import pandas as pd
import matplotlib.pyplot as plt

# Fetch data from the FPL API
url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
response = requests.get(url)
data = response.json()

# Create DataFrame
players_df = pd.DataFrame(data['elements'])
players_df['cost_in_millions'] = players_df['now_cost'] / 10.0

# Generate scatter plot
plt.figure(figsize=(10, 6))
plt.scatter(players_df['cost_in_millions'], players_df['total_points'], alpha=0.5)
plt.title('Precio vs. Puntos Totales')
plt.xlabel('Precio (en millones)')
plt.ylabel('Puntos Totales')
plt.grid(True)

# Save the plot
plt.savefig('scatter_plot.png')

print("Gráfico de dispersión guardado como scatter_plot.png")
