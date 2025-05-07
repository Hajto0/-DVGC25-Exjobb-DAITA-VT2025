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
    # Explicitly set ticks to unique values in x_col
    unique_x = data[x_col].unique()
    ax.set_xticks(range(len(unique_x)))  # Set ticks based on the number of unique values
    ax.set_xticklabels(unique_x, rotation=45, ha='right')  # Set labels for those ticks
    if ylim:
        ax.set_ylim(ylim)

def main(fname):
    # Load the CSV file
    data = pd.read_csv(fname)

    # Rename relevant columns
    data = data.rename(columns={"oh total (x)": "bandwidth overhead (x)"})
    data = data.rename(columns={"oh sent (x)": "bandwidth overhead sent (x)"})
    data = data.rename(columns={"oh recv (x)": "bandwidth overhead received (x)"})

    # Group by 'server' and 'defense' to analyze the impact across different server locations
    server_impact = data.groupby(['server', 'defense']).mean().reset_index()

    # rename "daita" to "DAITA", but keep the rest of the names as they are
    server_impact['defense'] = server_impact['defense'].apply(lambda x: x.upper() if x == 'daita' else x)

    # Set a paper-friendly theme
    sns.set_theme(style="darkgrid")
    #sns.set_context("poster", font_scale = 0.45, rc={"grid.linewidth": 1})

    # Create subplots for better presentation
    fig, axs = plt.subplots(5, 2, figsize=(12, 18))

    # Deep Fingerprinting Accuracy
    create_seaborn_plot(axs[0, 0], server_impact, 'server', 'df (accuracy)', 'defense', 
                                                     'Deep Fingerprinting attack accuracy', 'server', 'accuracy', (0.0, 1.0))

    # Robust Fingerprinting Accuracy
    create_seaborn_plot(axs[0, 1], server_impact, 'server', 'rf (accuracy)', 'defense', 
                                                     'Robust Fingerprinting attack accuracy', 'server', 'accuracy', (0.0, 1.0))

    # Bandwidth Overhead
    create_seaborn_plot(axs[1, 0], server_impact, 'server', 'bandwidth overhead (x)', 'defense', 
                                                     'defense bandwidth overhead', 'server', 'bandwidth overhead (x)', (-0.1, 3.0))

    # Bandwidth (starting from 0)
    create_seaborn_plot(axs[1, 1], server_impact, 'server', 'bandwidth (MiB)', 'defense', 
                                                     'total bandwidth used for website visit', 'server', 'bandwidth used (MiB)', (0, None))

    # Delay Overhead
    create_seaborn_plot(axs[2, 0], server_impact, 'server', 'oh latency (x)', 'defense', 
                                                     'defense delay overhead', 'server', 'delay overhead (x)', (-0.1, 3.0))

    # Duration (starting from 0)
    create_seaborn_plot(axs[2, 1], server_impact, 'server', 'duration (sec)', 'defense', 
                                                     'total duration for website visit', 'server', 'duration (sec)', (0, None))

    # Bandwidth Overhead Sent
    create_seaborn_plot(axs[3, 0], server_impact, 'server', 'bandwidth overhead sent (x)', 'defense', 
                                                     'defense bandwidth overhead sent', 'server', 'bw overhead sent (x)', (-0.1, 3.0))

    # Bandwidth Overhead Received
    create_seaborn_plot(axs[3, 1], server_impact, 'server', 'bandwidth overhead received (x)', 'defense', 
                                                     'defense bandwidth overhead received', 'server', 'bw overhead received (x)', (-0.1, 3.0))

    # Bandwidth Sent (starting from 0)
    create_seaborn_plot(axs[4, 0], server_impact, 'server', 'bandwidth sent (MiB)', 'defense', 
                                                     'total bandwidth sent during website visit', 'server', 'bandwidth sent (MiB)', (0, None))
    
    # Bandwidth Received (starting from 0)
    create_seaborn_plot(axs[4, 1], server_impact, 'server', 'bandwidth recv (MiB)', 'defense', 
                                                     'total bandwidth received during website visit', 'server', 'bandwidth received (MiB)', (0, None))

    # remove the heading from each legend
    for ax in axs.flat:
        ax.get_legend().set_title('')

    plt.tight_layout()
    # save to pdf
    plt.savefig('results.pdf')
    #plt.show()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script.py <csv_filename>")
    else:
        main(sys.argv[1])

