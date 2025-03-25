import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Column names for the data file
column_names = [
    "UT date and time (ISO 8601)",
    "Alignment routine code",
    "True zenith angle (deg)",
    "True azimuth (deg)",
    "Apparent zenith angle (deg)",
    "Apparent azimuth (deg)",
    "RMS of field of view fitting",
    "Weighting factor"
]

st.set_page_config(page_title="Monthly Report - Pandora Alignments", layout="centered")
st.title("Monthly Report of Pandora Alignments")

uploaded_file = st.file_uploader("Upload your Pandora alignment .txt file", type=["txt"])

if uploaded_file is not None:
    # Read lines from the uploaded file
    lines = uploaded_file.read().decode("utf-8").splitlines()
    
    separator_count = 0
    data_lines = []
    
    for line in lines:
        if "----------------" in line:
            separator_count += 1
            continue
        # Only start collecting lines after the second separator
        if separator_count == 2:
            data_lines.append(line.strip())
    
    # Split each line by whitespace into columns
    data = [line.split() for line in data_lines if line]
    
    # Create a DataFrame
    df = pd.DataFrame(data, columns=column_names)
    
    # Convert numeric columns to numeric dtypes
    for col in column_names[2:]:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Parse date column (adjust format if necessary)
    df["UT date and time (ISO 8601)"] = pd.to_datetime(
        df["UT date and time (ISO 8601)"], 
        errors='coerce'
    )
    
    # Calculate average weighting factor
    average_weighting_factor = df["Weighting factor"].mean()
    
    # Flag "Good Scan" rows (True if above average weighting factor)
    df["Good Scan"] = df["Weighting factor"] > average_weighting_factor
    
    # Extract Year and Month
    df["Year"] = df["UT date and time (ISO 8601)"].dt.year
    df["Month"] = df["UT date and time (ISO 8601)"].dt.month
    
    # Group by Year and Month to compute percentage of Good Scans
    monthly_report = df.groupby(["Year", "Month"])["Good Scan"].mean() * 100
    monthly_report_df = monthly_report.reset_index()
    monthly_report_df.columns = ["Year", "Month", "Good Scan (%)"]
    
    # Let user pick threshold (default 21)
    threshold = st.number_input("Threshold for Good Scans (%)", value=21, min_value=0, max_value=100)
    
    # Plot with matplotlib
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Color bars based on threshold
    bar_colors = [
        "red" if pct < threshold else "green" 
        for pct in monthly_report_df["Good Scan (%)"]
    ]
    
    ax.bar(monthly_report_df.index, monthly_report_df["Good Scan (%)"], color=bar_colors)
    
    ax.set_xlabel("Year-Month")
    ax.set_ylabel("Percentage of Good Scans")
    ax.set_title("Monthly Report of Pandora Alignments")
    
    # Create x-axis labels like "YYYY-M" and rotate
    x_labels = [f"{row.Year}-{row.Month}" for _, row in monthly_report_df.iterrows()]
    ax.set_xticks(monthly_report_df.index)
    ax.set_xticklabels(x_labels, rotation=45)
    
    ax.set_ylim(0, 100)
    
    # Threshold line
    ax.axhline(y=threshold, color='gray', linestyle='--', label="Threshold")
    ax.legend()
    
    plt.tight_layout()
    
    # Display the plot
    st.pyplot(fig)
    
    # Display the monthly report table
    st.subheader("Monthly Report Data")
    st.dataframe(monthly_report_df)
else:
    st.write("Please upload a `.txt` file to generate the monthly report and chart.")
