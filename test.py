import streamlit as st
import pandas as pd

# Inject custom CSS to increase container width
st.markdown(
    """
    <style>
        .block-container {
            max-width: 1500px;
            padding: 1rem;
            padding-top: 30px;
        }
        .stLineChart>div>div>div>iframe {
            width: 100% !important;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Sidebar for file upload
st.sidebar.title("File Upload")
file = st.sidebar.file_uploader("Upload an Excel file", type=["xlsx"])

def plotGraph(df, timeframe):
    # Determine the time range based on the selected timeframe
    amt = ''
    if timeframe == "1M":
        amt = 'Daily'
        df_monthly = df.resample('D').agg({
            'Invoice Amount': 'sum',
            'Invoice #': 'count'
        })
        filtered_data = df_monthly.tail(30)
    elif timeframe == "3M":
        amt = 'Weekly'
        df_monthly = df.resample('W').agg({
            'Invoice Amount': 'sum',
            'Invoice #': 'count'
        })
        filtered_data = df_monthly.tail(12)
    elif timeframe == "1Y":
        amt = 'Bi-Weekly'
        df_monthly = df.resample('2W').agg({
            'Invoice Amount': 'sum',
            'Invoice #': 'count'
        })
        filtered_data = df_monthly.tail(27)
    else:  # All Time
        amt = 'Monthly'
        df_monthly = df.resample('ME').agg({
            'Invoice Amount': 'sum',
            'Invoice #': 'count'
        })
        filtered_data = df_monthly

    # Display metrics for the selected timeframe
    total_volume = filtered_data['Invoice #'].sum()
    total_amt = filtered_data['Invoice Amount'].sum()

    col1, col2 = st.columns(2)
    col1.metric("Invoice Volume", total_volume)
    col2.metric("Invoice Amount", f"${total_amt:,.2f}")

    # Plot the data for the selected timeframe
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(amt + " Invoice Volume")
        st.line_chart(filtered_data['Invoice #'])

    with col2:
        st.subheader(amt + " Invoice Amount")
        st.line_chart(filtered_data['Invoice Amount'])


# Main content
if file is not None:
    pd.set_option('display.max_columns', None)
    df = pd.read_excel(file, engine="openpyxl")

    st.header("Data Overview and Analysis")
    st.markdown("---")

    # Add buttons for selecting timeframe
    timeframe = st.radio("Select Timeframe", options=["1M", "3M", "1Y", "All Time"], horizontal=True)

    # Convert 'Issue Date' to datetime
    df['Issue Date'] = pd.to_datetime(df['Issue Date'], errors='coerce')

    # Clean and convert 'Invoice Amount' to numeric
    df['Invoice Amount'] = df['Invoice Amount'].replace({'\$': '', ',': ''}, regex=True)
    df['Invoice Amount'] = pd.to_numeric(df['Invoice Amount'], errors='coerce')

    # Set 'Issue Date' as the index
    df.set_index('Issue Date', inplace=True)


    plotGraph(df, timeframe)