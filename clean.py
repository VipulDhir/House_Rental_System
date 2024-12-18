import pandas as pd

# Read the data from a CSV file
input_file = "Bengaluru_House_Data.csv"  # Replace with your CSV file name
output_file = "cleaned_file_2.csv"  # Output cleaned file

# Load the CSV into a DataFrame
df = pd.read_csv(input_file)

# Replace placeholders like '-' or 'nan' strings with NaN
df.replace(['-', 'nan',' '], pd.NA, inplace=True)

# Drop rows containing any NaN values
cleaned_df = df.dropna()

# Display cleaned data
print("Cleaned DataFrame:")
print(cleaned_df)

# Save the cleaned DataFrame to a new CSV file
cleaned_df.to_csv(output_file, index=False)

print(f"Cleaned data saved to {output_file}")
