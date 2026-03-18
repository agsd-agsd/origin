def filter_data(input_file, output_file, line_number=4):
    """
    Filter data from a specific line in a text file
    Keeps only data entries where Fee <= value
    
    Args:
        input_file (str): Path to input file
        output_file (str): Path to output file
        line_number (int): Line number to process (1-based indexing)
    """
    # Read all lines from the input file
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    # Make sure the requested line exists
    if line_number > len(lines):
        print(f"Error: File only has {len(lines)} lines, but line {line_number} was requested")
        return
    
    # Get the line to process (adjusting for 0-based indexing)
    line = lines[line_number - 1]
    
    # Process the data
    filtered_data = []
    data_entries = line.strip().split(' ')
    
    for entry in data_entries:
        # Remove parentheses and split by comma
        clean_entry = entry.strip('()')
        if not clean_entry:  # Skip empty entries
            continue
            
        parts = clean_entry.split(',')
        if len(parts) < 2:  # Skip invalid entries
            continue
            
        try:
            fee = int(parts[0])
            value = int(parts[1])
            
            # Only keep entries where Fee <= value
            if fee <= value:
                filtered_data.append(entry)
        except ValueError:
            print(f"Warning: Could not parse numbers in entry: {entry}")
    
    # Replace the line with filtered data
    lines[line_number - 1] = ' '.join(filtered_data) + '\n'
    
    # Write all lines to the output file
    with open(output_file, 'w') as f:
        f.writelines(lines)
    
    print(f"Filtered data written to {output_file}")
    print(f"Kept {len(filtered_data)} entries out of {len(data_entries)} where Fee <= Value")

# Example usage
if __name__ == "__main__":
    filter_data("./item0/data1.txt", "./item0/filtered_data.txt", 4)