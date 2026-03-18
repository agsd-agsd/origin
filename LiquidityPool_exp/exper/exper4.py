import matplotlib.pyplot as plt
import numpy as np
import json
import os
import sys
import pandas as pd
import seaborn as sns
from matplotlib.ticker import FuncFormatter, MultipleLocator

def plot_participation_vs_mer_boxplot(results_path, output_folder):
    """
    Create a box plot showing relationship between management fee rate and investor participation rate
    """
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Load JSON data
    with open(results_path, 'r') as f:
        results = json.load(f)
    
    # Initialize data storage
    data = []
    
    # Set BrokerHub colors
    brokerhub_colors = {'BrokerHub1': '#00cc44', 'BrokerHub2': '#ff3333'}
    
    # Collect data from all epochs and all brokerhubs
    for state in results:
        epoch = int(state['epoch'])
        # Only use data after stabilization (e.g., epoch > 50)
        if epoch > 50:
            for bh in state['brokerhubs']:
                # Management fee rate (MER)
                mer = float(bh['tax_rate']) * 100
                
                # Calculate participation rate
                total_volunteers = len(state['volunteers'])
                participation_rate = (len(bh['users'])) / total_volunteers * 100
                
                # Add data point to list
                data.append({
                    'MER': mer,
                    'Participation_Rate': participation_rate,
                    'Epoch': epoch,
                    'BrokerHub_ID': bh['id']
                })
    
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    # Define MER values for x-axis ticks - starting from 5 with step size 5
    mer_values = [10, 20, 30, 40, 50, 60, 70, 80, 90]
    
    # Create corresponding intervals
    bins = [0] + mer_values + [100]
    labels = [f'{bins[i]}-{bins[i+1]}' for i in range(len(bins)-1)]
    
    # Add MER group column
    df['MER_Group'] = pd.cut(df['MER'], bins=bins, labels=labels, right=False)
    
    # Create figure
    plt.figure(figsize=(14, 10))
    
    # Create box plot grouped by BrokerHub_ID
    ax = sns.boxplot(x='MER_Group', y='Participation_Rate', hue='BrokerHub_ID', 
                     data=df, 
                     palette=brokerhub_colors,
                     showfliers=True,  # Show outliers
                     boxprops=dict(alpha=0.8),  # Semi-transparent boxes
                     width=0.7,  # Box width
                     fliersize=5)  # Outlier point size
    
    # Add strip plot to show raw data points
    sns.stripplot(x='MER_Group', y='Participation_Rate', hue='BrokerHub_ID', 
                 data=df, dodge=True, size=4, 
                 palette={k: 'black' for k in brokerhub_colors.keys()}, 
                 alpha=0.3, jitter=True)
    
    # Remove duplicate legend entries
    handles, labels = ax.get_legend_handles_labels()
    # Keep only box plot legend (first two)
    plt.legend(handles[:2], labels[:2], fontsize=12)  # Removed title
    
    # Set title and labels
    plt.title('Investor Participation Rate vs Management Fee Rate', fontsize=20)
    plt.xlabel('Management Fee Rate (MER)', fontsize=16)
    plt.ylabel('Participation Rate (%)', fontsize=16)
    
    # Format Y-axis as percentage
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _: f'{y:.0f}%'))
    
    # Add grid lines
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Adjust x-axis ticks and labels
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)
    
    # Adjust y-axis tick interval
    ax.yaxis.set_major_locator(MultipleLocator(10))  # One tick every 10%
    
    # Save figure
    output_path = os.path.join(output_folder, 'participation_vs_mer_boxplot.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    
    # Also save PDF version
    pdf_output_path = os.path.join(output_folder, 'participation_vs_mer_boxplot.pdf')
    plt.savefig(pdf_output_path, dpi=300, bbox_inches='tight')
    
    plt.close()
    
    print(f"Box plot generated! Saved at {output_path} and {pdf_output_path}")
    
    # Output statistics by MER_Group and BrokerHub_ID
    stats = df.groupby(['MER_Group', 'BrokerHub_ID'])['Participation_Rate'].describe()
    print("\nParticipation rate statistics by MER group and BrokerHub:")
    print(stats)
    
    return stats

if __name__ == "__main__":
    # =========================== Parameter Settings ===========================
    # Experiment parameters
    experiment_name = "trump_20w_300_diff_final_balance2"  # Experiment name, same as your original code
    
    # File path parameters
    results_filename = f"simulation_results_{experiment_name}.json"  # Results file name
    input_folder = "../result/output"  # Input folder (relative to current script path)
    output_folder = "./exper4"  # Output folder base path - changed to exper4
    
    # =================================================================
    
    # Build complete paths
    results_path = os.path.join(os.path.dirname(__file__), input_folder, results_filename)
    
    # Check if input file exists
    if not os.path.exists(results_path):
        print(f"Error: Input file {results_path} not found")
        print(f"Please ensure the file exists and check path settings")
        sys.exit(1)
    
    # Draw the chart
    print(f"Starting to generate chart...")
    print(f"Input file: {results_path}")
    print(f"Output folder: {output_folder}")
    
    # Draw boxplot and get statistics
    stats = plot_participation_vs_mer_boxplot(results_path, output_folder)