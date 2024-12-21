import streamlit as st
import pandas as pd

# inject custom CSS to increase container width
st.markdown(
    """
    <style>
        /* Increase container width */
        .block-container {
            max-width: 1500px;  /* Set the maximum width of the container */
            padding: 1rem;      /* Optional padding adjustment */
            padding-top: 30px;  /* Adds space at the top to move everything down */
        }

        /* Increase width of the charts */
        .stLineChart>div>div>div>iframe {
            width: 100% !important;  /* Ensure that the charts are full width */
        }

    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar for file upload
st.sidebar.title("File Upload")
file = st.sidebar.file_uploader("Upload an Excel file", type=["xlsx"])

if file is not None:
    
    pd.set_option('display.max_columns', None)
    df = pd.read_excel(file, engine="openpyxl")


    
    st.header("Data Overview and Analysis (Last 3 Months)")
    col1, col2, col3 = st.columns(3)
    st.markdown("---")


    # Convert 'Issue Date' to datetime
    df['Issue Date'] = pd.to_datetime(df['Issue Date'], errors='coerce')

    # Clean and convert 'Invoice Amount' to numeric
    df['Invoice Amount'] = df['Invoice Amount'].replace({'\$': '', ',': ''}, regex=True)  # Remove $ and commas
    df['Invoice Amount'] = pd.to_numeric(df['Invoice Amount'], errors='coerce')  # Convert to numeric

    # Set 'Issue Date' as the index
    df.set_index('Issue Date', inplace=True)

    # Group data by month and calculate total invoice amount and invoice volume (count invoices)
    df_monthly = df.resample('ME').agg({
        'Invoice Amount': 'sum',   # Sum the invoice amounts for each month
        'Invoice #': 'count'       # Count the total number of invoices for each month
    })


    # Calculate totals for the last 3 months and the previous 3 months
    last_three_months = df_monthly.tail(3)
    prev_three_months = df_monthly.iloc[-6:-3]

    # Calculate the total invoice amount and number of invoices for the last and previous 3 months
    last_three_total_volume = last_three_months['Invoice #'].sum()
    prev_three_total_volume = prev_three_months['Invoice #'].sum()

    last_three_total_amt = last_three_months['Invoice Amount'].sum()
    prev_three_total_amt = prev_three_months['Invoice Amount'].sum()


    growth_rate_volume = ((last_three_total_volume - prev_three_total_volume) / prev_three_total_volume) * 100
    col1.metric("Invoice Volume", last_three_total_volume, f"{growth_rate_volume:.2f}%", border=True)

    growth_rate_amt = ((last_three_total_amt - prev_three_total_amt) / prev_three_total_amt) * 100
    col2.metric("Invoice Amount", f"${last_three_total_amt:,.2f}", f"{growth_rate_amt:.2f}%", border=True)



    #test commit
    # Assuming 'Customer' and 'Issue Date' columnddds exist in your DataFrame

    # Define theweeeeee previous period (2023)
    previous_period = df[df.index.year == 2023]  # Filter data for year 2023

    # Define the current period (2024)
    current_period = df[df.index.year == 2024]  # Filter data for year 2024

    # Get unique customers from each period
    previous_customers = previous_period['Customer'].unique()
    current_customers = current_period['Customer'].unique()

    # Find repeat customers (intersection of both periods)
    repeat_customers = set(previous_customers) & set(current_customers)

    # Calculate retention rate
    retention_rate = (len(repeat_customers) / len(previous_customers)) * 100

    # Display retention in the metrics
    col3.metric("Customer Retention", f"{len(repeat_customers)} Repeat Customers", f"{retention_rate:.2f}% Retention", border=True)




    
    # Plot the data
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Monthly Invoice Amount")
        st.line_chart(df_monthly['Invoice Amount'])
    with col2:
        st.subheader("Monthly Invoice Volume")
        st.line_chart(df_monthly['Invoice #'])