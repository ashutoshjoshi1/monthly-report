import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

st.set_page_config(page_title="Monthly & Daily Report - Pandora Alignments", layout="centered")
st.title("Pandora Alignments Report")

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
    
    if not data:
        st.error("No data found in the file.")
    else:
        # Detect file type by checking the number of columns
        if len(data[0]) == 8:
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
            df = pd.DataFrame(data, columns=column_names)
            
            # Convert numeric columns to numbers
            for col in column_names[2:]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        elif len(data[0]) == 12:
            column_names = [
                "UT date and time (ISO 8601)",
                "Alignment routine code",
                "True zenith angle (deg)",
                "True azimuth (deg)",
                "Apparent zenith angle (deg) for spec 1",
                "Apparent azimuth (deg) for spec 1",
                "RMS of field of view fitting for spec 1",
                "Weighting factor for spec 1",
                "Apparent zenith angle (deg) for spec 2",
                "Apparent azimuth (deg) for spec 2",
                "RMS of field of view fitting for spec 2",
                "Weighting factor for spec 2"
            ]
            df = pd.DataFrame(data, columns=column_names)
            
            # Convert numeric columns for both sets
            numeric_cols = column_names[2:]
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Create a new combined weighting factor as the average of the two weighting factors
            df["Weighting factor"] = (df["Weighting factor for spec 1"] + df["Weighting factor for spec 2"]) / 2
        
        else:
            st.error("File format not recognized. Expected 8 or 12 columns.")
            st.stop()
        
        # Parse date column
        df["UT date and time (ISO 8601)"] = pd.to_datetime(
            df["UT date and time (ISO 8601)"],
            errors='coerce'
        )
        
        # Calculate average weighting factor and flag "Good Scan" rows
        average_weighting_factor = df["Weighting factor"].mean()
        df["Good Scan"] = df["Weighting factor"] > average_weighting_factor
        
        # Extract Year and Month for aggregation
        df["Year"] = df["UT date and time (ISO 8601)"].dt.year
        df["Month"] = df["UT date and time (ISO 8601)"].dt.month
        
        # Group by Year and Month to compute percentage of Good Scans
        monthly_report = df.groupby(["Year", "Month"])["Good Scan"].mean() * 100
        monthly_report_df = monthly_report.reset_index()
        monthly_report_df.columns = ["Year", "Month", "Good Scan (%)"]
        
        # Let user pick threshold (default 21)
        threshold = st.number_input("Threshold for Good Scans (%)", value=21, min_value=0, max_value=100)
        
        # --- Monthly Chart ---
        st.subheader("Monthly Good Scan Report")
        fig, ax = plt.subplots(figsize=(12, 5))
        
        # Color bars based on threshold
        bar_colors = [
            "red" if pct < threshold else "green" 
            for pct in monthly_report_df["Good Scan (%)"]
        ]
        
        ax.bar(monthly_report_df.index, monthly_report_df["Good Scan (%)"], color=bar_colors)
        ax.set_xlabel("Year-Month")
        ax.set_ylabel("Percentage of Good Scans")
        ax.set_title("Monthly Report of Pandora Alignments")
        
        # Create x-axis labels like "YYYY-M" and rotate them
        x_labels = [f"{row.Year}-{row.Month}" for _, row in monthly_report_df.iterrows()]
        ax.set_xticks(monthly_report_df.index)
        ax.set_xticklabels(x_labels, rotation=45)
        ax.set_ylim(0, 100)
        
        # Draw threshold line
        ax.axhline(y=threshold, color='gray', linestyle='--', label="Threshold")
        ax.legend()
        plt.tight_layout()
        
        st.pyplot(fig)
        
        # --- Daily Chart with Date Range Filter ---
        st.subheader("Daily Good Scan Report (Date Range Filter)")
        
        # Determine min and max dates
        min_date = df["UT date and time (ISO 8601)"].min()
        max_date = df["UT date and time (ISO 8601)"].max()
        min_date = min_date.date() if pd.notnull(min_date) else None
        max_date = max_date.date() if pd.notnull(max_date) else None
        
        if min_date is None or max_date is None:
            st.warning("No valid dates found in the uploaded file.")
        else:
            # Allow user to select a date range
            start_date, end_date = st.slider(
                "Select date range",
                min_value=min_date,
                max_value=max_date,
                value=(min_date, max_date),
                format="YYYY-MM-DD"
            )
            
            # Filter DataFrame by the selected date range
            df_filtered = df[
                (df["UT date and time (ISO 8601)"].dt.date >= start_date) &
                (df["UT date and time (ISO 8601)"].dt.date <= end_date)
            ]
            
            if not df_filtered.empty:
                # Group by day and compute Good Scan percentage
                daily_report = df_filtered.groupby(df_filtered["UT date and time (ISO 8601)"].dt.date)["Good Scan"].mean() * 100
                daily_report_df = daily_report.reset_index()
                daily_report_df.columns = ["Date", "Good Scan (%)"]
                
                # Convert the "Date" column back to datetime for plotting
                daily_report_df["Date"] = pd.to_datetime(daily_report_df["Date"])
                
                fig2, ax2 = plt.subplots(figsize=(12, 5))
                
                # Color bars based on threshold
                bar_colors2 = ["red" if pct < threshold else "green" for pct in daily_report_df["Good Scan (%)"]]
                
                ax2.bar(daily_report_df["Date"], daily_report_df["Good Scan (%)"], color=bar_colors2, width=0.8)
                ax2.set_xlabel("Date")
                ax2.set_ylabel("Percentage of Good Scans")
                ax2.set_title("Daily Report of Pandora Alignments")
                ax2.set_ylim(0, 100)
                
                # Draw threshold line
                ax2.axhline(y=threshold, color='gray', linestyle='--', label="Threshold")
                ax2.legend()
                
                # Format the x-axis dates
                locator = mdates.AutoDateLocator(minticks=3, maxticks=10)
                formatter = mdates.ConciseDateFormatter(locator)
                ax2.xaxis.set_major_locator(locator)
                ax2.xaxis.set_major_formatter(formatter)
                
                plt.tight_layout()
                st.pyplot(fig2)
            else:
                st.info("No data found for the selected date range.")
else:
    st.write("Please upload a `.txt` file to generate the monthly and daily reports.")
