import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sys
import os

def create_seaborn_plot(ax, data, x_col, y_col, hue_col, title, xlabel, ylabel, ylim=None):
    daita_name = data[hue_col].unique()[data[hue_col].unique() != 'Undefended'][0] if len(data[hue_col].unique()) > 1 else 'Daita'
    palette = {
        'Undefended': 'C1',  # Orange Undefended
        daita_name: 'C0'     # Blå DAITA
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

def create_dual_subplot_figure(data, output_name, fig_name, y_cols, titles, xlabels, ylabels, ylims):
    fig, axs = plt.subplots(1, 2, figsize=(12, 6))
    create_seaborn_plot(axs[0], data, 'Server', y_cols[0], 'defense', titles[0], xlabels[0], ylabels[0], ylims[0])
    create_seaborn_plot(axs[1], data, 'Server', y_cols[1], 'defense', titles[1], xlabels[1], ylabels[1], ylims[1])
    for ax in axs.flat:
        if ax.get_legend():
            ax.get_legend().set_title('')
    plt.tight_layout()
    fig.savefig(f'{output_name} {fig_name}.png', dpi=300)
    plt.close(fig)
    print(f'Figure saved to "{output_name} {fig_name}.png"')

def main(fname, output_name, split):
    daita_name = os.path.splitext(os.path.basename(fname))[0]

    data = pd.read_csv(fname)
    # Byt namn på kolumner för att matcha grafer
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


    # Beräkna overhead för Daita relativt Undefended
    server_impact = data.copy()

    for server in server_impact['Server'].unique():

        undefended = server_impact[(server_impact['Server'] == server) & (server_impact['defense'] == 'Undefended')]
        if not undefended.empty:
            baseline_bw = undefended['bandwidth (MiB)'].iloc[0]
            baseline_sent = undefended['bandwidth sent (MiB)'].iloc[0]
            baseline_recv = undefended['bandwidth recv (MiB)'].iloc[0]
            baseline_duration = undefended['duration (sec)'].iloc[0]
            baseline_sent_packets = undefended['number sent'].iloc[0]
            baseline_recv_packets = undefended['number received'].iloc[0]
            
            # Beräkna overhead för Daita
            daita_mask = (server_impact['Server'] == server) & (server_impact['defense'].str.lower() == 'daita')
            if not server_impact[daita_mask].empty:
                #overhead_sent = server_impact.loc[daita_mask, 'bandwidth sent (MiB)'] / baseline_sent if baseline_sent != 0 else float('inf')                  #DEBUG
                #print(f"Server: {server}, Daita ({daita_name}) Bandwidth Overhead Sent (x): {overhead_sent.iloc[0] if not overhead_sent.empty else 'N/A'}")

                server_impact.loc[daita_mask, 'bandwidth overhead (x)'] = (
                    ((server_impact.loc[daita_mask, 'bandwidth (MiB)'] / baseline_bw if baseline_bw != 0 else float('inf')) - 1)
                )
                server_impact.loc[daita_mask, 'bandwidth overhead sent (x)'] = (
                    ((server_impact.loc[daita_mask, 'bandwidth sent (MiB)'] / baseline_sent if baseline_sent != 0 else float('inf')) - 1)
                )
                server_impact.loc[daita_mask, 'bandwidth overhead recv (x)'] = (
                    ((server_impact.loc[daita_mask, 'bandwidth recv (MiB)'] / baseline_recv if baseline_recv != 0 else float('inf')) - 1)
                )
                server_impact.loc[daita_mask, 'oh latency (x)'] = (
                    ((server_impact.loc[daita_mask, 'duration (sec)'] / baseline_duration if baseline_duration != 0 else float('inf')) - 1)
                )
                server_impact.loc[daita_mask, 'number sent overhead (x)'] = (
                    ((server_impact.loc[daita_mask, 'number sent'] / baseline_sent_packets if baseline_sent_packets != 0 else float('inf')) - 1)
                )
                server_impact.loc[daita_mask, 'number received overhead (x)'] = (
                    ((server_impact.loc[daita_mask, 'number received'] / baseline_recv_packets if baseline_recv_packets != 0 else float('inf')) - 1)
                )
            else:
                print(f"Server: {server}, Ingen Daita-data")

    # Sätt overhead till 0 för Undefended
    undefended_mask = server_impact['defense'] == 'Undefended'
    server_impact.loc[undefended_mask, 'bandwidth overhead (x)'] = 0
    server_impact.loc[undefended_mask, 'bandwidth overhead sent (x)'] = 0
    server_impact.loc[undefended_mask, 'bandwidth overhead recv (x)'] = 0
    server_impact.loc[undefended_mask, 'oh latency (x)'] = 0
    server_impact.loc[undefended_mask, 'number sent overhead (x)'] = 0
    server_impact.loc[undefended_mask, 'number received overhead (x)'] = 0

    # Byt namn på "Daita" till filnamnet
    server_impact['defense'] = server_impact['defense'].apply(
        lambda x: daita_name if x.lower() == 'daita' else x
    )

    sns.set_theme(style="darkgrid")

    if split != 'split':
        fig, axs = plt.subplots(7, 2, figsize=(12, 25))

        create_seaborn_plot(axs[0, 0], server_impact, 'Server', 'df (accuracy)', 'defense',
                            'Deep Fingerprinting attack accuracy', 'server', 'accuracy', (0.0, 1.0))

        create_seaborn_plot(axs[0, 1], server_impact, 'Server', 'rf (accuracy)', 'defense',
                            'Robust Fingerprinting attack accuracy', 'server', 'accuracy', (0.0, 1.0))

        create_seaborn_plot(axs[1, 0], server_impact, 'Server', 'bandwidth overhead (x)', 'defense',
                            'Defense Overhead: Bandwidth', 'server', 'bandwidth overhead (X)', (None, None))

        create_seaborn_plot(axs[1, 1], server_impact, 'Server', 'bandwidth (MiB)', 'defense',
                            'Total Bandwidth Per Visit', 'server', 'bandwidth used (MiB)', (None, None))

        create_seaborn_plot(axs[2, 0], server_impact, 'Server', 'oh latency (x)', 'defense',
                            'Defense Overhead: Duration', 'server', 'duration overhead (X)', (None, None))

        create_seaborn_plot(axs[2, 1], server_impact, 'Server', 'duration (sec)', 'defense',
                            'Total Duration Per Visit', 'server', 'duration (sec)', (None, None))

        create_seaborn_plot(axs[3, 0], server_impact, 'Server', 'bandwidth overhead sent (x)', 'defense',
                            'Defense Overhead: Bandwidth Sent', 'server', 'bw overhead sent (X)', (None, None))
        
        create_seaborn_plot(axs[3, 1], server_impact, 'Server', 'bandwidth sent (MiB)', 'defense',
                            'Total Bandwidth Sent Per Visit', 'server', 'bandwidth sent (MiB)', (None, None))

        create_seaborn_plot(axs[4, 0], server_impact, 'Server', 'bandwidth overhead recv (x)', 'defense',
                            'Defense Overhead: Bandwidth Received', 'server', 'bw overhead received (X)', (None, None))

        create_seaborn_plot(axs[4, 1], server_impact, 'Server', 'bandwidth recv (MiB)', 'defense',
                            'Total Bandwidth Received Per Visit', 'server', 'bandwidth received (MiB)', (None, None))

        create_seaborn_plot(axs[5, 0], server_impact, 'Server', 'number sent overhead (x)', 'defense',
                            'Defense Overhead: Number of Packets Sent', 'server', 'packets sent overhead (X)', (None, None))
        
        create_seaborn_plot(axs[5, 1], server_impact, 'Server', 'number sent', 'defense',
                            'Total Number of Packets Per Visit', 'server', 'packets sent', (None, None))

        create_seaborn_plot(axs[6, 0], server_impact, 'Server', 'number received overhead (x)', 'defense',
                            'Defense Overhead: Number of Packets Received', 'server', 'packets received overhead (X)', (None, None))

        create_seaborn_plot(axs[6, 1], server_impact, 'Server', 'number received', 'defense',
                            'Total Number of Packets Received Per Visit', 'server', 'packets received', (None, None))

        # Remove legend titles
        for ax in axs.flat:
            if ax.get_legend():
                ax.get_legend().set_title('')

        plt.tight_layout()
        plt.savefig(f'{output_name}.png')
        print(f'Figure saved to {output_name}')
    else:
        create_dual_subplot_figure(
            data=server_impact,
            output_name=output_name,
            fig_name='Fingerprinting Accuracy',
            y_cols=['df (accuracy)', 'rf (accuracy)'],
            titles=['Deep Fingerprinting Attack Accuracy', 'Robust Fingerprinting Attack Accuracy'],
            xlabels=['server', 'server'],
            ylabels=['accuracy', 'accuracy'],
            ylims=[(0.0, 1.0), (0.0, 1.0)]
        )

        create_dual_subplot_figure(
            data=server_impact,
            output_name=output_name,
            fig_name='Total Bandwidth',
            y_cols=['bandwidth overhead (x)', 'bandwidth (MiB)'],
            titles=['Defense Overhead: Bandwidth', 'Total Bandwidth Per Visit'],
            xlabels=['server', 'server'],
            ylabels=['bandwidth overhead (X)', 'bandwidth used (MiB)'],
            ylims=[(-0.1, None), (0, None)]
        )
        
        create_dual_subplot_figure(
            data=server_impact,
            output_name=output_name,
            fig_name='Duration',
            y_cols=['oh latency (x)', 'duration (sec)'],    # oh latency = duration overhead
            titles=['Defense Overhead: Duration', 'Total Duration Per Visit'],
            xlabels=['server', 'server'],
            ylabels=['duration overhead (X)', 'duration (sec)'],
            ylims=[(None, None), (-0.1, None)]
        )
        
        create_dual_subplot_figure(
            data=server_impact,
            output_name=output_name,
            fig_name='Bandwidth Sent',
            y_cols=['bandwidth overhead sent (x)', 'bandwidth sent (MiB)'],
            titles=['Defense Overhead: Bandwidth Sent', 'Total Bandwidth Per Visit'],
            xlabels=['server', 'server'],
            ylabels=['bandwidth overhead sent (X)', 'bandwidth sent (MiB)'],
            ylims=[(None, None), (0, None)]
        )

        
        create_dual_subplot_figure(
            data=server_impact,
            output_name=output_name,
            fig_name='Bandwidth Received',
            y_cols=['bandwidth overhead recv (x)', 'bandwidth recv (MiB)'],
            titles=['Defense Overhead: Bandwidth Received', 'Total Bandwidth Received Per Visit'],
            xlabels=['server', 'server'],
            ylabels=['bandwidth overhead received (X)', 'bandwidth received (MiB)'],
            ylims=[(-0.1, None), (0, None)]
        )

        create_dual_subplot_figure(
            data=server_impact,
            output_name=output_name,
            fig_name='Number Sent',
            y_cols=['number sent overhead (x)', 'number sent'],
            titles=['Defense Overhead: Number of Packets Sent', 'Total Number of Packets Sent Per Visit'],
            xlabels=['server', 'server'],
            ylabels=['packets sent overhead (X)', 'packets sent'],
            ylims=[(-0.1, None), (0, None)]
        )

        create_dual_subplot_figure(
            data=server_impact,
            output_name=output_name,
            fig_name='Number Received',
            y_cols=['number received overhead (x)', 'number received'],
            titles=['Defense Overhead: Number of Packets Received', 'Total Number of Packets Received Per Visit'],
            xlabels=['server', 'server'],
            ylabels=['packets recived overhead (X)', 'packets received'],
            ylims=[(-0.1, None), (0, None)]
        )

if __name__ == "__main__":
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2], 'Combined graph')
    elif len(sys.argv) == 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
    elif len(sys.argv) < 3:
        print("Usage: python script.py <csv_filename> <output_name> <Optional: 'split'>")