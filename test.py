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

# side bar
st.sidebar.markdown(
    """
    <h2 style="display: inline; font-weight: bold;">Upload Required Files</h2> <span style="font-size: 24px;">📁</span>
    """, unsafe_allow_html=True
)
st.sidebar.markdown("---")
    
st.sidebar.subheader("Invoice List")
st.sidebar.markdown("Upload the `invoice-list.xlsx` file containing the invoice data.")
invoice_list = st.sidebar.file_uploader("Choose Invoice List File", type=["xlsx"])

st.sidebar.markdown("---")

st.sidebar.subheader("Job List")
st.sidebar.markdown("Upload the `job-list.xlsx` file containing the job details.")
job_list = st.sidebar.file_uploader("Choose Job List File", type=["xlsx"])



def plotGraph(df, timeframe):
    # Determine the time range based on the selected timeframe
    amt = ''
    if timeframe == "1M":
        amt = 'Daily'
        df_data = df.resample('D').agg({
            'Invoice Amount': 'sum',
            'Invoice #': 'count'
        })
        filtered_data = df_data.tail(30)
        prev_data = df_data.iloc[-60:-30]
    elif timeframe == "3M":
        amt = 'Weekly'
        df_data = df.resample('W').agg({
            'Invoice Amount': 'sum',
            'Invoice #': 'count'
        })
        filtered_data = df_data.tail(12)
        prev_data = df_data.iloc[-24:-12]

    elif timeframe == "1Y":
        amt = 'Bi-Weekly'
        df_data = df.resample('2W').agg({
            'Invoice Amount': 'sum',
            'Invoice #': 'count'
        })
        filtered_data = df_data.tail(27)
        prev_data = df_data.iloc[-54:-27]
    else:  # All Time
        amt = 'Monthly'
        df_data = df.resample('ME').agg({
            'Invoice Amount': 'sum',
            'Invoice #': 'count'
        })
        filtered_data = df_data
        prev_data = df_data

    # Display metrics for the selected timeframe
    total_volume = filtered_data['Invoice #'].sum()
    total_amt = filtered_data['Invoice Amount'].sum()
    prev_volume = prev_data['Invoice #'].sum()
    prev_amt = prev_data['Invoice Amount'].sum()

    volume_change = ((total_volume - prev_volume) / prev_volume) * 100 if prev_volume != 0 else 0
    amt_change = ((total_amt - prev_amt) / prev_amt) * 100 if prev_amt != 0 else 0

    abs_volume_decrease = total_volume - prev_volume
    abs_amt_decrease = total_amt - prev_amt




    if timeframe != "All Time":
        col1, col2 = st.columns(2)
        col1.metric("Invoice Volume", total_volume, f"{abs_volume_decrease:+d} ({volume_change:.2f}%)", border=True)
        col2.metric("Invoice Amount",f"${total_amt:,.2f}", f"{abs_amt_decrease:,.2f} ({amt_change:.2f}%)", border=True)
    else:
        col1, col2 = st.columns(2)
        col1.metric("Invoice Volume", total_volume, border=True)
        col2.metric("Invoice Amount", f"${total_amt:,.2f}", border=True)



    # Plot the data for the selected timeframe
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(amt + " Invoice Volume")
        st.line_chart(filtered_data['Invoice #'])

    with col2:
        st.subheader(amt + " Invoice Amount")
        st.line_chart(filtered_data['Invoice Amount'])


# Main content
if invoice_list is not None:
    dfInvoice = pd.read_excel(invoice_list, engine="openpyxl")
    st.header("Invoice Overview and Analysis")

    # Add buttons for selecting timeframe
    timeframe = st.radio("Select Timeframe", options=["1M", "3M", "1Y", "All Time"], horizontal=True)

    # Convert 'Issue Date' to datetime
    dfInvoice['Issue Date'] = pd.to_datetime(dfInvoice['Issue Date'], errors='coerce')

    # Clean and convert 'Invoice Amount' to numeric
    dfInvoice['Invoice Amount'] = dfInvoice['Invoice Amount'].replace({'\$': '', ',': ''}, regex=True)
    dfInvoice['Invoice Amount'] = pd.to_numeric(dfInvoice['Invoice Amount'], errors='coerce')

    # Set 'Issue Date' as the index
    dfInvoice.set_index('Issue Date', inplace=True)

    plotGraph(dfInvoice, timeframe)
    st.markdown("---")

if job_list is not None:
    dfJob = pd.read_excel(job_list, engine="openpyxl")
    st.header("Job Insights")
    # dfJob['Location Address'] is the address for geocoding later :)