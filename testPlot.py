import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sys

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

def main(fname):
    # Load the CSV file
    data = pd.read_csv(fname)
    print("Kolumner i CSV-filen:", data.columns.tolist())  # För felsökning

    # Byt namn på kolumner för att matcha grafer
    data = data.rename(columns={
        "Average Duration (s)": "duration (sec)",
        "Average Bandwidth (MiB)": "bandwidth (MiB)",
        "Average Sent Bandwidth (MiB)": "bandwidth sent (MiB)",
        "Average Received Bandwidth (MiB)": "bandwidth recv (MiB)",
        "DF Accuracy": "df (accuracy)",
        "RF Accuracy": "rf (accuracy)",
        "Defense": "defense"
    })

    # Beräkna overhead för Daita relativt Undefended
    server_impact = data.copy()

    # För varje server, beräkna overhead där Daita finns
    for server in server_impact['Server'].unique():
        # Hämta Undefended-värden som baslinje
        undefended = server_impact[(server_impact['Server'] == server) & (server_impact['defense'] == 'Undefended')]
        if not undefended.empty:
            baseline_bw = undefended['bandwidth (MiB)'].iloc[0]
            baseline_sent = undefended['bandwidth sent (MiB)'].iloc[0]
            baseline_recv = undefended['bandwidth recv (MiB)'].iloc[0]
            baseline_duration = undefended['duration (sec)'].iloc[0]

            # Beräkna overhead för Daita som skillnad
            daita_mask = (server_impact['Server'] == server) & (server_impact['defense'] == 'Daita')
            server_impact.loc[daita_mask, 'bandwidth overhead (x)'] = (
                server_impact.loc[daita_mask, 'bandwidth (MiB)'] - baseline_bw
            )
            server_impact.loc[daita_mask, 'bandwidth overhead sent (x)'] = (
                server_impact.loc[daita_mask, 'bandwidth sent (MiB)'] - baseline_sent
            )
            server_impact.loc[daita_mask, 'bandwidth overhead recv (x)'] = (
                server_impact.loc[daita_mask, 'bandwidth recv (MiB)'] - baseline_recv
            )
            server_impact.loc[daita_mask, 'oh latency (x)'] = (
                server_impact.loc[daita_mask, 'duration (sec)'] - baseline_duration
            )

    # Sätt overhead till 0 för Undefended
    undefended_mask = server_impact['defense'] == 'Undefended'
    server_impact.loc[undefended_mask, 'bandwidth overhead (x)'] = 0
    server_impact.loc[undefended_mask, 'bandwidth overhead sent (x)'] = 0
    server_impact.loc[undefended_mask, 'bandwidth overhead recv (x)'] = 0
    server_impact.loc[undefended_mask, 'oh latency (x)'] = 0

    # Byt namn på "Daita" till "DAITA"
    server_impact['defense'] = server_impact['defense'].apply(lambda x: x.upper() if x.lower() == 'daita' else x)

    # Set theme
    sns.set_theme(style="darkgrid")

    # Skapa subplots
    fig, axs = plt.subplots(5, 2, figsize=(12, 18))

    # Deep Fingerprinting Accuracy
    create_seaborn_plot(axs[0, 0], server_impact, 'Server', 'df (accuracy)', 'defense',
                        'Deep Fingerprinting attack accuracy', 'server', 'accuracy', (0.0, 1.0))

    # Robust Fingerprinting Accuracy
    create_seaborn_plot(axs[0, 1], server_impact, 'Server', 'rf (accuracy)', 'defense',
                        'Robust Fingerprinting attack accuracy', 'server', 'accuracy', (0.0, 1.0))

    # Bandwidth Overhead
    create_seaborn_plot(axs[1, 0], server_impact, 'Server', 'bandwidth overhead (x)', 'defense',
                        'defense bandwidth overhead', 'server', 'bandwidth overhead (MiB)', (-0.1, 3.0))

    # Bandwidth (starting from 0)
    create_seaborn_plot(axs[1, 1], server_impact, 'Server', 'bandwidth (MiB)', 'defense',
                        'total bandwidth used for website visit', 'server', 'bandwidth used (MiB)', (0, None))

    # Delay Overhead
    #create_seaborn_plot(axs[2, 0], server_impact, 'Server', 'oh latency (x)', 'defense',
    #                    'defense delay overhead', 'server', 'delay overhead (sec)', (-0.1, 3.0))

    # Duration (starting from 0)
    create_seaborn_plot(axs[2, 1], server_impact, 'Server', 'duration (sec)', 'defense',
                        'total duration for website visit', 'server', 'duration (sec)', (0, None))

    # Bandwidth Overhead Sent
    create_seaborn_plot(axs[3, 0], server_impact, 'Server', 'bandwidth overhead sent (x)', 'defense',
                        'defense bandwidth overhead sent', 'server', 'bw overhead sent (MiB)', (-0.1, 3.0))

    # Bandwidth Overhead Received
    create_seaborn_plot(axs[3, 1], server_impact, 'Server', 'bandwidth overhead recv (x)', 'defense',
                        'defense bandwidth overhead received', 'server', 'bw overhead received (MiB)', (-0.1, 3.0))

    # Bandwidth Sent (starting from 0)
    create_seaborn_plot(axs[4, 0], server_impact, 'Server', 'bandwidth sent (MiB)', 'defense',
                        'total bandwidth sent during website visit', 'server', 'bandwidth sent (MiB)', (0, None))

    # Bandwidth Received (starting from 0)
    create_seaborn_plot(axs[4, 1], server_impact, 'Server', 'bandwidth recv (MiB)', 'defense',
                        'total bandwidth received during website visit', 'server', 'bandwidth received (MiB)', (0, None))

    # Remove legend titles
    for ax in axs.flat:
        if ax.get_legend():
            ax.get_legend().set_title('')

    plt.tight_layout()
    plt.savefig('results.pdf')
    # plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <csv_filename>")
    else:
        main(sys.argv[1])