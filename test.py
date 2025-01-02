import streamlit as st
import pandas as pd
import requests
import time
import re
import plotly.express as px


import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

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
            'Invoice #': 'count',
            'Customer': lambda x: list(x)
        })
        filtered_data = df_data.tail(30)
        prev_data = df_data.iloc[-60:-30]
    elif timeframe == "3M":
        amt = 'Weekly'
        df_data = df.resample('W').agg({
            'Invoice Amount': 'sum',
            'Invoice #': 'count',
            'Customer': lambda x: list(x)
        })
        filtered_data = df_data.tail(12)
        prev_data = df_data.iloc[-24:-12]
    elif timeframe == "1Y":
        amt = 'Bi-Weekly'
        df_data = df.resample('2W').agg({
            'Invoice Amount': 'sum',
            'Invoice #': 'count',
            'Customer': lambda x: list(x)
        })
        filtered_data = df_data.tail(27)
        prev_data = df_data.iloc[-54:-27]
    else:  # All Time
        amt = 'Monthly'
        df_data = df.resample('ME').agg({
            'Invoice Amount': 'sum',
            'Invoice #': 'count',
            'Customer': lambda x: list(x)
        })
        filtered_data = df_data
        prev_data = df_data

    unique_customers = filtered_data['Customer'].explode().drop_duplicates()
    unique_prev_customers = prev_data['Customer'].explode().drop_duplicates()

    # Calculate customer retention
    retained_customers = len(unique_customers[unique_customers.isin(unique_prev_customers)])
    customer_retention = (retained_customers / len(unique_prev_customers)) * 100
    
    
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
        col1, col2, col3 = st.columns(3)
        col1.metric("Invoice Volume", total_volume, f"{abs_volume_decrease:+d} ({volume_change:.2f}%)", border=True)
        col2.metric("Customer Retention", f"{customer_retention:.2f}%", border=True)
        col3.metric("Invoice Amount", f"${total_amt:,.2f}", f"{abs_amt_decrease:,.2f} ({amt_change:.2f}%)", border=True)
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Invoice Volume", total_volume, border=True)
        col2.metric("Customer Retention", None, border=True)
        col3.metric("Invoice Amount", f"${total_amt:,.2f}", border=True)





    # Plot the data for the selected timeframe
    col1, col2 = st.columns(2)

    with col1:
        st.subheader(amt + " Invoice Volume")
        st.line_chart(filtered_data['Invoice #'])

    with col2:
        st.subheader(amt + " Invoice Amount")
        st.line_chart(filtered_data['Invoice Amount'])

def geocode(addresses):
    # API call to get the geocodes
    URL = 'https://api.geoapify.com/v1/batch/geocode/search?apiKey=b4c75e67dae1497492698c563da01626'
    response = requests.post(URL, json=addresses, headers={
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    })


    if response.status_code == 202:
        status_url = response.json()['url']

        while True:
            status_response = requests.get(status_url, headers={
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            })
            
            if status_response.status_code == 202:
                time.sleep(5)
                continue
            elif status_response.status_code == 200:
                geocode_data = status_response.json()
                break
            else:                    
                st.write("Something went wrong, rip. just message Nick or something lol.")
                break

        if geocode_data:
            coordinates = []
            for result in geocode_data:
                lat = result['lat']
                lon = result['lon']
                coordinates.append((lat, lon))
            return coordinates
    else:
        st.write("Something went wrong, rip. just message Nick or something lol.")

@st.cache_data
def get_geocoding_results(addresses):
    return geocode(addresses)

def categorize_job_name(job_name):

    category_patterns = {
    'toilet-related': r'toilet',
    'water heater': r'water\s*heater|w/h|wh',
    'multiple jobs': r'multiple|mulitiple',
    'leak-related': r'leak',
    'shower-related': r'shower',
    'faucet-related': r'faucet',
    'pipe-related': r'pipe',
    'kitchen-related': r'kitchen',
    'bathtub-related': r'tub',
    'clog-related': r'clog',
    'bathroom-related': r'bathroom',
    'drain-related': r'drain',
    'sink-related': r'sink',
    'valve-related': r'valve',
    }

    if not isinstance(job_name, str) or not job_name.strip():
        return None 

    job_name = job_name.lower()

    for category, pattern in category_patterns.items():
        if re.search(pattern, job_name, re.IGNORECASE):
            return category

    return job_name


# Main content
if invoice_list is not None:
    dfInvoice = pd.read_excel(invoice_list, engine="openpyxl")
    st.header("Invoice Overview and Analysis")

    # add buttons for selecting timeframe
    timeframe = st.radio("Select Timeframe", options=["1M", "3M", "1Y", "All Time"], horizontal=True)

    # convert 'Issue Date' to datetime
    dfInvoice['Issue Date'] = pd.to_datetime(dfInvoice['Issue Date'], errors='coerce')

    # clean and convert 'Invoice Amount' to numeric
    dfInvoice['Invoice Amount'] = dfInvoice['Invoice Amount'].replace({'\$': '', ',': ''}, regex=True)
    dfInvoice['Invoice Amount'] = pd.to_numeric(dfInvoice['Invoice Amount'], errors='coerce')

    # set 'Issue Date' as the index
    dfInvoice.set_index('Issue Date', inplace=True)

    plotGraph(dfInvoice, timeframe)
    st.markdown("---")


if job_list is None:
    st.cache_data.clear()
else:
    st.header("Job Insights")
    col1, col2 = st.columns(2)
    dfJob = pd.read_excel(job_list, engine="openpyxl")

    # Geocode the addresses directly
    addresses = dfJob['Location Address'][:200].tolist()
    cords = get_geocoding_results(addresses)
    df_coords = pd.DataFrame(cords, columns=['lat', 'lon'])

    # Create a heatmap with the geocoded coordinates
    m = folium.Map(location=[df_coords['lat'].mean(), df_coords['lon'].mean()], zoom_start=10, tiles='CartoDB positron')
    HeatMap(data=cords, radius=10, blur=15, opacity=0.5).add_to(m)

    with col1:
        st.subheader("Invoice Heatmap of the last 100 Jobs")
        st_folium(m, width=700, height=500)

    # Categorize job names and prepare data for the pie chart
    dfJob['Job Name'] = dfJob['Job Name'].apply(categorize_job_name)

    # Filter out any less than 50 jobs
    job_counts = dfJob['Job Name'].value_counts()
    other_count = job_counts[job_counts < 50].sum()
    job_counts = job_counts[job_counts >= 50]
    job_counts = pd.concat([job_counts, pd.Series({'Other': other_count})])

    job_counts_df = job_counts.reset_index()
    job_counts_df.columns = ['Job Name', 'Count']

    fig = px.pie(job_counts_df, names='Job Name', values='Count', 
                hover_data={'Count': True},
                labels={'Job Name': 'Job Category'})

    # Update the layout to make the chart look nicer and larger
    fig.update_traces(textinfo='percent+label', pull=[0.1]*len(job_counts_df))  # Adds percentage and label

    # Set the width and height of the figure
    fig.update_layout(
        showlegend=False,
        width=700,
        height=700,
    )

    # Display the pie chart in Streamlit
    with col2:
        st.subheader("Job Category Distribution")
        st.plotly_chart(fig)
