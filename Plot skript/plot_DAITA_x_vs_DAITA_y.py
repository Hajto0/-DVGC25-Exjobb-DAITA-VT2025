import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sys
import os

def create_seaborn_plot(ax, data, x_col, y_col, hue_col, title, xlabel, ylabel, ylim=None):
    sns.lineplot(data=data, x=x_col, y=y_col, hue=hue_col, marker='o', ax=ax)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(title=hue_col)
    unique_x = data[x_col].unique()
    ax.set_xticks(range(len(unique_x)))
    ax.set_xticklabels(unique_x, rotation=45, ha='right')
    if ylim:
        ax.set_ylim(ylim)
    ax.grid(True)

def calculate_overhead(data, daita_version):
    # Byt namn på kolumner
    data = data.rename(columns={
        "Average Duration (s)": "duration (sec)",
        "Average Bandwidth (MiB)": "bandwidth (MiB)",
        "Average Sent Bandwidth (MiB)": "bandwidth sent (MiB)",
        "Average Received Bandwidth (MiB)": "bandwidth recv (MiB)",
        "DF Accuracy": "df (accuracy)",
        "RF Accuracy": "rf (accuracy)",
        "Defense": "defense"
    })

    # Skapa en kopia för overhead-beräkningar
    server_impact = data.copy()

    # Lägg till kolumn för Daita-version (filnamnet)
    server_impact['daita_version'] = daita_version

    # För varje server, beräkna overhead
    print(f"\nDebugging: Bandwidth Overhead Sent (x) för {daita_version}:")
    for server in server_impact['Server'].unique():
        print(f"\nServer: {server}")
        undefended = server_impact[(server_impact['Server'] == server) & (server_impact['defense'] == 'Undefended')]
        daita = server_impact[(server_impact['Server'] == server) & (server_impact['defense'] == 'Daita')]

        if not undefended.empty:
            baseline_bw = undefended['bandwidth (MiB)'].iloc[0]
            baseline_sent = undefended['bandwidth sent (MiB)'].iloc[0]
            baseline_recv = undefended['bandwidth recv (MiB)'].iloc[0]
            baseline_duration = undefended['duration (sec)'].iloc[0]

            print(f"  Undefended:")
            print(f"    Baseline bandwidth sent (MiB): {baseline_sent}")
            print(f"    Bandwidth overhead sent (x): 0")

            # Sätt overhead till 0 för Undefended
            undefended_mask = (server_impact['Server'] == server) & (server_impact['defense'] == 'Undefended')
            server_impact.loc[undefended_mask, 'bandwidth overhead (x)'] = 0
            server_impact.loc[undefended_mask, 'bandwidth overhead sent (x)'] = 0
            server_impact.loc[undefended_mask, 'bandwidth overhead recv (x)'] = 0
            server_impact.loc[undefended_mask, 'oh latency (x)'] = 0

            if not daita.empty:
                daita_mask = (server_impact['Server'] == server) & (server_impact['defense'] == 'Daita')
                daita_sent = server_impact.loc[daita_mask, 'bandwidth sent (MiB)'].iloc[0]
                overhead_sent = server_impact.loc[daita_mask, 'bandwidth sent (MiB)'] / baseline_sent if baseline_sent != 0 else float('inf')
                
                print(f"  Daita:")
                print(f"    Bandwidth sent (MiB): {daita_sent}")
                print(f"    Bandwidth overhead sent (x): {overhead_sent.iloc[0]}")

                server_impact.loc[daita_mask, 'bandwidth overhead (x)'] = (
                    server_impact.loc[daita_mask, 'bandwidth (MiB)'] / baseline_bw if baseline_bw != 0 else float('inf')
                )
                server_impact.loc[daita_mask, 'bandwidth overhead sent (x)'] = (
                    server_impact.loc[daita_mask, 'bandwidth sent (MiB)'] / baseline_sent if baseline_sent != 0 else float('inf')
                )
                server_impact.loc[daita_mask, 'bandwidth overhead recv (x)'] = (
                    server_impact.loc[daita_mask, 'bandwidth recv (MiB)'] / baseline_recv if baseline_recv != 0 else float('inf')
                )
                server_impact.loc[daita_mask, 'oh latency (x)'] = (
                    server_impact.loc[daita_mask, 'duration (sec)'] / baseline_duration if baseline_duration != 0 else float('inf')
                )
            else:
                print("  Ingen Daita-data")
        else:
            print("  Ingen Undefended-data")

    # Byt namn på "Daita" till "DAITA"
    server_impact['defense'] = server_impact['defense'].apply(lambda x: x.upper() if x.lower() == 'daita' else x)
    return server_impact

def main(file1, file2, ouput_name):
    # Extrahera filnamn utan .csv
    daita_version1 = os.path.splitext(os.path.basename(file1))[0]
    daita_version2 = os.path.splitext(os.path.basename(file2))[0]

    # Läs CSV-filerna
    data1 = pd.read_csv(file1)
    data2 = pd.read_csv(file2)
    print("Kolumner i första CSV-filen:", data1.columns.tolist())
    print("Kolumner i andra CSV-filen:", data2.columns.tolist())

    # Beräkna overhead för båda filerna
    server_impact1 = calculate_overhead(data1, daita_version1)
    server_impact2 = calculate_overhead(data2, daita_version2)

    # Hitta gemensamma servrar
    common_servers = set(server_impact1['Server']).intersection(set(server_impact2['Server']))
    if not common_servers:
        print("Inga gemensamma servrar hittades mellan filerna.")
        return

    print("\nGemensamma servrar:", common_servers)

    # Filtrera data till gemensamma servrar och Daita
    plot_data1 = server_impact1[server_impact1['Server'].isin(common_servers) & (server_impact1['defense'] == 'DAITA')]
    plot_data2 = server_impact2[server_impact2['Server'].isin(common_servers) & (server_impact2['defense'] == 'DAITA')]

    # Kombinera data för plottning
    plot_data = pd.concat([
        plot_data1[['Server', 'daita_version', 'bandwidth overhead (x)', 'bandwidth overhead sent (x)', 
                    'bandwidth overhead recv (x)', 'oh latency (x)']],
        plot_data2[['Server', 'daita_version', 'bandwidth overhead (x)', 'bandwidth overhead sent (x)', 
                    'bandwidth overhead recv (x)', 'oh latency (x)']]
    ])

    # Set theme
    sns.set_theme(style="darkgrid")

    # Skapa subplots
    fig, axs = plt.subplots(2, 2, figsize=(12, 10))

    # Plot: Bandwidth Overhead
    create_seaborn_plot(axs[0, 0], plot_data, 'Server', 'bandwidth overhead (x)', 'daita_version',
                        'Bandwidth Overhead', 'Server', 'Bandwidth Overhead (x)', (0, 10.0))

    # Plot: Bandwidth Overhead Sent
    create_seaborn_plot(axs[0, 1], plot_data, 'Server', 'bandwidth overhead sent (x)', 'daita_version',
                        'Bandwidth Overhead Sent', 'Server', 'Bandwidth Overhead Sent (x)', (0, None))

    # Plot: Bandwidth Overhead Received
    create_seaborn_plot(axs[1, 0], plot_data, 'Server', 'bandwidth overhead recv (x)', 'daita_version',
                        'Bandwidth Overhead Received', 'Server', 'Bandwidth Overhead Received (x)', (0, 3))

    # Plot: Latency Overhead
    create_seaborn_plot(axs[1, 1], plot_data, 'Server', 'oh latency (x)', 'daita_version',
                        'Visit Duration Overhead', 'Server', 'Latency Overhead (x)', (1, 1.5))

    # Remove legend titles
    for ax in axs.flat:
        if ax.get_legend():
            ax.get_legend().set_title('')

    plt.tight_layout()
    plt.savefig(f'{ouput_name}.png')
    #plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python script.py <csv_file1> <csv_file2>")
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3])