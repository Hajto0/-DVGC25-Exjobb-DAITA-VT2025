import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sys
import os

def create_seaborn_plot(ax, data, x_col, y_col, hue_col, title, xlabel, ylabel, ylim=None):
    palette = {
        data[hue_col].unique()[0]: 'C1',
        data[hue_col].unique()[1]: 'C0'
    } #if len(data[hue_col].unique()) > 1 else {data[hue_col].unique()[0]: 'blue'}
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
    ax.grid(True)

def create_single_subplot_figure(data, output_name, fig_name, y_col, title, xlabel, ylabel, ylim=None):
    fig = plt.figure(figsize=(6, 6))
    ax = fig.add_subplot(111)
    create_seaborn_plot(ax, data, 'Server', y_col, 'daita_version', title, xlabel, ylabel, ylim)
    if ax.get_legend():
        ax.get_legend().set_title('')
    plt.tight_layout()
    fig.savefig(f'{output_name} {fig_name}.png', dpi=300)
    plt.close(fig)
    print(f'Figure saved to {output_name} {fig_name}.png')

def create_dual_subplot_figure(data, output_name, fig_name, y_cols, titles, xlabels, ylabels, ylims):
    fig, axs = plt.subplots(1, 2, figsize=(12, 3))
    create_seaborn_plot(axs[0], data, 'Server', y_cols[0], 'defense', titles[0], xlabels[0], ylabels[0], ylims[0])
    create_seaborn_plot(axs[1], data, 'Server', y_cols[1], 'defense', titles[1], xlabels[1], ylabels[1], ylims[1])
    for ax in axs.flat:
        if ax.get_legend():
            ax.get_legend().set_title('')
    plt.tight_layout()
    fig.savefig(f'{output_name} {fig_name}.png', dpi=300)
    plt.close(fig)
    print(f'Figure saved to "{output_name} {fig_name}.png"')

def calculate_overhead(data, daita_version):
    # Byt namn på kolumner
    data = data.rename(columns={
        "Average Duration (s)": "duration (sec)",
        "Average Bandwidth (MiB)": "bandwidth (MiB)",
        "Average Sent Bandwidth (MiB)": "bandwidth sent (MiB)",
        "Average Received Bandwidth (MiB)": "bandwidth recv (MiB)",
        "DF Accuracy": "df (accuracy)",
        "RF Accuracy": "rf (accuracy)",
        "Defense": "defense",
        "Average Number Sent": "number sent",
        "Average Number Received": "number received"
    })

    server_impact = data.copy()

    # Lägg till kolumn för Daita-version (filnamnet)
    server_impact['daita_version'] = daita_version

    #   print(f"\nDebugging: Bandwidth Overhead Sent (x) för {daita_version}:")     #DEBUG
    for server in server_impact['Server'].unique():
        #print(f"\nServer: {server}")   #DEBUG
        undefended = server_impact[(server_impact['Server'] == server) & (server_impact['defense'] == 'Undefended')]
        daita = server_impact[(server_impact['Server'] == server) & (server_impact['defense'] == 'Daita')]

        if not undefended.empty:
            baseline_bw = undefended['bandwidth (MiB)'].iloc[0]
            baseline_sent = undefended['bandwidth sent (MiB)'].iloc[0]
            baseline_recv = undefended['bandwidth recv (MiB)'].iloc[0]
            baseline_duration = undefended['duration (sec)'].iloc[0]
            baseline_sent_packets = undefended['number sent'].iloc[0]
            baseline_recv_packets = undefended['number received'].iloc[0]

            #print(f"  Undefended:")                                            #DEBUG
            #print(f"    Baseline bandwidth sent (MiB): {baseline_sent}")
            #print(f"    Bandwidth overhead sent (x): 0")

            # Sätt overhead till 0 för Undefended
            undefended_mask = (server_impact['Server'] == server) & (server_impact['defense'] == 'Undefended')
            server_impact.loc[undefended_mask, 'bandwidth overhead (x)'] = 0
            server_impact.loc[undefended_mask, 'bandwidth overhead sent (x)'] = 0
            server_impact.loc[undefended_mask, 'bandwidth overhead recv (x)'] = 0
            server_impact.loc[undefended_mask, 'oh latency (x)'] = 0
            server_impact.loc[undefended_mask, 'number sent overhead (x)'] = 0
            server_impact.loc[undefended_mask, 'number received overhead (x)'] = 0

            if not daita.empty:
                daita_mask = (server_impact['Server'] == server) & (server_impact['defense'] == 'Daita')
                daita_sent = server_impact.loc[daita_mask, 'bandwidth sent (MiB)'].iloc[0]
                overhead_sent = server_impact.loc[daita_mask, 'bandwidth sent (MiB)'] / baseline_sent if baseline_sent != 0 else float('inf')
                
                #print(f"  Daita:")                                                         #DEBUG
                #print(f"    Bandwidth sent (MiB): {daita_sent}")
                #print(f"    Bandwidth overhead sent (x): {overhead_sent.iloc[0]}")

                server_impact.loc[daita_mask, 'bandwidth overhead (x)'] = (
                    (server_impact.loc[daita_mask, 'bandwidth (MiB)'] / baseline_bw if baseline_bw != 0 else float('inf')) - 1
                )
                server_impact.loc[daita_mask, 'bandwidth overhead sent (x)'] = (
                    (server_impact.loc[daita_mask, 'bandwidth sent (MiB)'] / baseline_sent if baseline_sent != 0 else float('inf')) - 1
                )
                server_impact.loc[daita_mask, 'bandwidth overhead recv (x)'] = (
                    (server_impact.loc[daita_mask, 'bandwidth recv (MiB)'] / baseline_recv if baseline_recv != 0 else float('inf')) - 1
                )
                server_impact.loc[daita_mask, 'oh latency (x)'] = (
                    (server_impact.loc[daita_mask, 'duration (sec)'] / baseline_duration if baseline_duration != 0 else float('inf')) - 1
                )
                server_impact.loc[daita_mask, 'number sent overhead (x)'] = (
                    (server_impact.loc[daita_mask, 'number sent'] / baseline_sent_packets if baseline_sent_packets != 0 else float('inf')) - 1
                )
                server_impact.loc[daita_mask, 'number received overhead (x)'] = (
                    (server_impact.loc[daita_mask, 'number received'] / baseline_recv_packets if baseline_recv_packets != 0 else float('inf')) - 1
                )
            else:
                print("  Ingen Daita-data")
        else:
            print("  Ingen Undefended-data")

    # Byt namn på "Daita" till "DAITA"
    server_impact['defense'] = server_impact['defense'].apply(lambda x: x.upper() if x.lower() == 'daita' else x)
    return server_impact

def main(file1, file2, ouput_name, split):
    # Extrahera filnamn utan .csv
    daita_version1 = os.path.splitext(os.path.basename(file1))[0]
    daita_version2 = os.path.splitext(os.path.basename(file2))[0]

    # Läs CSV-filerna
    data1 = pd.read_csv(file1)
    data2 = pd.read_csv(file2)
    #print("Kolumner i första CSV-filen:", data1.columns.tolist())      #DEBUG
    #print("Kolumner i andra CSV-filen:", data2.columns.tolist())

    server_impact1 = calculate_overhead(data1, daita_version1)
    server_impact2 = calculate_overhead(data2, daita_version2)

    common_servers = set(server_impact1['Server']).intersection(set(server_impact2['Server']))
    if not common_servers:
        print("Inga gemensamma servrar hittades mellan filerna.")
        return

    #print("\nGemensamma servrar:", common_servers)     #DEBUG

    # Filtrera data till gemensamma servrar och Daita
    plot_data1 = server_impact1[server_impact1['Server'].isin(common_servers) & (server_impact1['defense'] == 'DAITA')]
    plot_data2 = server_impact2[server_impact2['Server'].isin(common_servers) & (server_impact2['defense'] == 'DAITA')]

    # Kombinera data för plottning
    plot_data = pd.concat([
    plot_data1[['Server', 'daita_version', 'bandwidth overhead (x)', 'bandwidth overhead sent (x)', 
                'bandwidth overhead recv (x)', 'oh latency (x)', 'number sent overhead (x)', 
                'number received overhead (x)']],
    plot_data2[['Server', 'daita_version', 'bandwidth overhead (x)', 'bandwidth overhead sent (x)', 
                'bandwidth overhead recv (x)', 'oh latency (x)', 'number sent overhead (x)', 
                'number received overhead (x)']]
    ])

    sns.set_theme(style="darkgrid")
    if split != 'split':
        # Skapa subplots
        fig, axs = plt.subplots(3, 2, figsize=(12, 10))

        # Plot: Bandwidth Overhead
        create_seaborn_plot(axs[0, 0], plot_data, 'Server', 'bandwidth overhead (x)', 'daita_version',
                            'Defense Overhead: Bandwidth', 'Server', 'Bandwidth Overhead (x)', (0, None))

        # Plot: Bandwidth Overhead Sent
        create_seaborn_plot(axs[0, 1], plot_data, 'Server', 'bandwidth overhead sent (x)', 'daita_version',
                            'Defense Overhead: Bandwidth Sent', 'Server', 'Bandwidth Overhead Sent (x)', (0, None))

        # Plot: Bandwidth Overhead Received
        create_seaborn_plot(axs[1, 0], plot_data, 'Server', 'bandwidth overhead recv (x)', 'daita_version',
                            'Defense Overhead: Bandwidth Received', 'Server', 'Bandwidth Overhead Received (x)', (0, None))

        # Plot: Duration Overhead
        create_seaborn_plot(axs[1, 1], plot_data, 'Server', 'oh latency (x)', 'daita_version',
                            'Defense Overhead: Visit Duration', 'Server', 'Duration Overhead (x)', (None, None))
        
        create_seaborn_plot(axs[2, 0], plot_data, 'Server', 'number sent overhead (x)', 'daita_version',
                        'Defense Overhead: Number of Packets Sent', 'Server', 'Number sent overhead (x)', (None, None))

        create_seaborn_plot(axs[2, 1], plot_data, 'Server', 'number received overhead (x)', 'daita_version',
                        'Defense Overhead: Number of Packets Received', 'Server', 'Number received overhead (x)', (None, None))


        # Remove legend titles
        for ax in axs.flat:
            if ax.get_legend():
                ax.get_legend().set_title('')

        plt.tight_layout()
        plt.savefig(f'{ouput_name}.png')
        #plt.show()
        print(f'Graph saved as "{ouput_name}"')
    else:
        # Plot: Bandwidth Overhead
        create_single_subplot_figure(
            data=plot_data,
            output_name=ouput_name,
            fig_name='Bandwidth_Overhead',
            y_col='bandwidth overhead (x)',
            title='Defense Overhead: Bandwidth',
            xlabel='Server',
            ylabel='Bandwidth Overhead (x)',
            ylim=(0, 10.0)
        )

        # Plot: Bandwidth Overhead Sent
        create_single_subplot_figure(
            data=plot_data,
            output_name=ouput_name,
            fig_name='Bandwidth_Sent_Overhead',
            y_col='bandwidth overhead sent (x)',
            title='Defense Overhead: Bandwidth Sent',
            xlabel='Server',
            ylabel='Bandwidth Overhead Sent (x)',
            ylim=(0, None)
        )

        # Plot: Bandwidth Overhead Received
        create_single_subplot_figure(
            data=plot_data,
            output_name=ouput_name,
            fig_name='Bandwidth_Received_Overhead',
            y_col='bandwidth overhead recv (x)',
            title='Defense Overhead: Bandwidth Received',
            xlabel='Server',
            ylabel='Bandwidth Overhead Received (x)',
            ylim=(0, 3)
        )

        # Plot: Latency Overhead
        create_single_subplot_figure(
            data=plot_data,
            output_name=ouput_name,
            fig_name='Duration_Overhead',
            y_col='oh latency (x)',
            title='Defense Overhead: Visit Duration',
            xlabel='Server',
            ylabel='Duration Overhead (x)',
            ylim=(None, None)
        )

        # Plot: Number Sent Overhead
        create_single_subplot_figure(
            data=plot_data,
            output_name=ouput_name,
            fig_name='Number_Sent_Overhead',
            y_col='number sent overhead (x)',
            title='Defense Overhead: Number of Packets Sent',
            xlabel='Server',
            ylabel='Number sent overhead (x)',
            ylim=None
        )

        # Plot: Number Received Overhead
        create_single_subplot_figure(
            data=plot_data,
            output_name=ouput_name,
            fig_name='Number_Received_Overhead',
            y_col='number received overhead (x)',
            title='Defense Overhead: Number of Packets Received',
            xlabel='Server',
            ylabel='Number received overhead (x)',
            ylim=None
        )

if __name__ == "__main__":
    if len(sys.argv) == 5:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    elif len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3], 'Combined graph')
    elif len(sys.argv) < 4:
        print("Usage: python script.py <csv_file1> <csv_file2> <Optional: 'split'>")
    