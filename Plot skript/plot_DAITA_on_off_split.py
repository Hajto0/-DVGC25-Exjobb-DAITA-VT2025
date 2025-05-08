import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sys
import os

def create_seaborn_plot(ax, data, x_col, y_col, hue_col, title, xlabel, ylabel, ylim=None):
    daita_name = data[hue_col].unique()[data[hue_col].unique() != 'Undefended'][0] if len(data[hue_col].unique()) > 1 else 'Daita'
    palette = {
        'Undefended': 'C1',  # Orange för Undefended
        daita_name: 'C0'     # Blå för Daita
    }
    sns.lineplot(data=data, x=x_col, y=y_col, hue=hue_col, marker='o', ax=ax, palette=palette)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(title=hue_col)
    unique_x = data[x_col].unique()
    ax.set_xticks(range(len(unique_x)))
    ax.set_xticklabels(unique_x, rotation=45, ha='right')
    if ylim:
        ax.set_ylim(ylim)

def main(fname, output_name):
    daita_name = os.path.splitext(os.path.basename(fname))[0]
    print(f"Använder filnamn som Daita-namn: {daita_name}")

    data = pd.read_csv(fname)
    print("Kolumner i CSV-filen:", data.columns.tolist())

    data = data.rename(columns={
        "Average Duration (s)": "duration (sec)",
        "Average Bandwidth (MiB)": "bandwidth (MiB)",
        "Average Sent Bandwidth (MiB)": "bandwidth sent (MiB)",
        "Average Received Bandwidth (MiB)": "bandwidth recv (MiB)",
        "DF Accuracy": "df (accuracy)",
        "RF Accuracy": "rf (accuracy)",
        "Defense": "defense"
    })

    server_impact = data.copy()

    for server in server_impact['Server'].unique():
        undefended = server_impact[(server_impact['Server'] == server) & (server_impact['defense'] == 'Undefended')]
        if not undefended.empty:
            baseline_bw = undefended['bandwidth (MiB)'].iloc[0]
            baseline_sent = undefended['bandwidth sent (MiB)'].iloc[0]
            baseline_recv = undefended['bandwidth recv (MiB)'].iloc[0]
            baseline_duration = undefended['duration (sec)'].iloc[0]
            
            daita_mask = (server_impact['Server'] == server) & (server_impact['defense'].str.lower() == 'daita')
            if not server_impact[daita_mask].empty:
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
                print(f"Server: {server}, Ingen Daita-data")

    undefended_mask = server_impact['defense'] == 'Undefended'
    server_impact.loc[undefended_mask, 'bandwidth overhead (x)'] = 0
    server_impact.loc[undefended_mask, 'bandwidth overhead sent (x)'] = 0
    server_impact.loc[undefended_mask, 'bandwidth overhead recv (x)'] = 0
    server_impact.loc[undefended_mask, 'oh latency (x)'] = 0

    server_impact['defense'] = server_impact['defense'].apply(
        lambda x: daita_name if x.lower() == 'daita' else x
    )

    print(f"Unika Defense-värden efter bearbetning: {server_impact['defense'].unique().tolist()}")

    sns.set_theme(style="darkgrid")

    # Figur 1: Fingerprinting Accuracy
    fig1, axs1 = plt.subplots(1, 2, figsize=(12, 6))
    create_seaborn_plot(axs1[0], server_impact, 'Server', 'df (accuracy)', 'defense',
                        'Deep Fingerprinting Attack Accuracy', 'server', 'accuracy', (0.0, 1.0))
    create_seaborn_plot(axs1[1], server_impact, 'Server', 'rf (accuracy)', 'defense',
                        'Robust Fingerprinting Attack Accuracy', 'server', 'accuracy', (0.0, 1.0))
    for ax in axs1.flat:
        if ax.get_legend():
            ax.get_legend().set_title('')
    plt.tight_layout()
    fig1.savefig(f'{output_name}_Fingerprinting_Accuracy.png')
    plt.close(fig1)
    print(f'Figure saved to {output_name}_Fingerprinting_Accuracy.png')

    # Figur 2: Bandwidth Overhead
    fig2, axs2 = plt.subplots(1, 2, figsize=(12, 6))
    create_seaborn_plot(axs2[0], server_impact, 'Server', 'bandwidth (MiB)', 'defense',
                        'Total Bandwidth Used For Website Visit', 'server', 'bandwidth used (MiB)', (0, None))
    create_seaborn_plot(axs2[1], server_impact, 'Server', 'bandwidth overhead (x)', 'defense',
                        'Defense Bandwidth Overhead', 'server', 'bandwidth overhead (X)', (-0.1, None))
    
    for ax in axs2.flat:
        if ax.get_legend():
            ax.get_legend().set_title('')
    plt.tight_layout()
    fig2.savefig(f'{output_name}_Total_Bandwidth.png')
    plt.close(fig2)
    print(f'Figure saved to {output_name}_Total_Bandwidth.png')

    # Figur 3: Duration Overhead
    fig3, axs3 = plt.subplots(1, 2, figsize=(12, 6))
    create_seaborn_plot(axs3[0], server_impact, 'Server', 'duration (sec)', 'defense',
                        'Total Duration For Website Visit', 'server', 'duration (sec)', (-0.1, None))
    create_seaborn_plot(axs3[1], server_impact, 'Server', 'oh latency (x)', 'defense',
                        'Defense Duration Overhead', 'server', 'delay overhead (sec)', (-0.1, None))
    
    for ax in axs3.flat:
        if ax.get_legend():
            ax.get_legend().set_title('')
    plt.tight_layout()
    fig3.savefig(f'{output_name}_Duration.png')
    plt.close(fig3)
    print(f'Figure saved to {output_name}_Duration.png')

    # Figur 4: Bandwidth Overhead Sent
    fig4, axs4 = plt.subplots(1, 2, figsize=(12, 6))
    create_seaborn_plot(axs4[0], server_impact, 'Server', 'bandwidth sent (MiB)', 'defense',
                        'Total Bandwidth Sent During Website Visit', 'server', 'bandwidth sent (MiB)', (0, None))
    create_seaborn_plot(axs4[1], server_impact, 'Server', 'bandwidth overhead sent (x)', 'defense',
                        'Defense Bandwidth Overhead Sent', 'server', 'bw overhead sent (X)', (None, None))
    
    for ax in axs4.flat:
        if ax.get_legend():
            ax.get_legend().set_title('')
    plt.tight_layout()
    fig4.savefig(f'{output_name}_Bandwidth_Sent.png')
    plt.close(fig4)
    print(f'Figure saved to {output_name}_Bandwidth_Sent.png')

    # Figur 5: Bandwidth Overhead Received
    fig5, axs5 = plt.subplots(1, 2, figsize=(12, 6))
    create_seaborn_plot(axs5[0], server_impact, 'Server', 'bandwidth recv (MiB)', 'defense',
                        'Total Bandwidth Received During Website Visit', 'server', 'bandwidth received (MiB)', (0, None))
    create_seaborn_plot(axs5[1], server_impact, 'Server', 'bandwidth overhead recv (x)', 'defense',
                        'Defense Bandwidth Overhead Received', 'server', 'bw overhead received (X)', (-0.1, None))
    for ax in axs5.flat:
        if ax.get_legend():
            ax.get_legend().set_title('')
    plt.tight_layout()
    fig5.savefig(f'{output_name}_Bandwidth_Received.png')
    plt.close(fig5)
    print(f'Figure saved to {output_name}_Bandwidth_Received.png')

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <csv_filename> <output_name>")
    else:
        main(sys.argv[1], sys.argv[2])