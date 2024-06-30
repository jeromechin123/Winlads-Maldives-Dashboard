import streamlit as st
import pandas as pd
import numpy as np
import pymongo
import pprint
from datetime import datetime
from datetime import timedelta


# Test connection to database
try: 
       
    client = pymongo.MongoClient(st.secrets["connection_url"])        
    client.admin.command('ping')
    print("Database connection established...")
except Exception as e:
    print(f"Database connection error!! {e}" )

# Connect to collection in database


database_name = "curated_data"
import_collection_name = "stripe1_charges_selected"


# Uses st.cache_data to only rerun when the query changes or after 10 min.

def get_data(database_name, import_collection_name):
    db = client[database_name]
    collection = db[import_collection_name]
    return list(collection.find())

# Extract all data from collection 

chrarges1_data = get_data(database_name, import_collection_name) 

# Flatten data to get json fields in individual columns -- Use '_' as seperator

charges1_flatten_data = pd.json_normalize(chrarges1_data, sep='_')

# Drop '_id' column to prevent upserting errors

charges1_flatten_data.drop( columns = ['_id'],axis = 1 , inplace=True)

# Rename field columns

rename_columns = {"billing_details_address_postal_code":"postal_code","billing_details_name":"name","receipt_email":"email"}
charges1_flatten_data.rename(columns = rename_columns, inplace=True)

# Divide numbers by 100 

charges1_flatten_data[["amount","amount_captured"]] = charges1_flatten_data[["amount","amount_captured"]].div(100)

# Reformat date from UNIX epoch to datetime

# charges1_flatten_data['created'] = charges1_flatten_data['created'].apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))
charges1_flatten_data['created'] = charges1_flatten_data['created'].apply(lambda x: datetime.utcfromtimestamp(x))
charges1_flatten_data['created'] = (charges1_flatten_data['created']) + timedelta(hours=10)

# Clean name and emails to remove inconsistencies

charges1_flatten_data[['name', 'email']] = charges1_flatten_data[['name', 'email']].apply(lambda x: x.str.lower())
charges1_flatten_data['name'] = charges1_flatten_data['name'].str.title()

# Import data from stripe2_charges to clean

database_name = "curated_data"
import_collection_name = "stripe2_charges_selected"

# Extract all data from 2nd collection 

stripe2_charges_data = get_data(database_name, import_collection_name)


# Flatten data to get json fields in individual columns -- Use '_' as seperator

charges2_flatten_data = pd.json_normalize(stripe2_charges_data, sep='_')

# Drop '_id' column to prevent upserting errors

charges2_flatten_data.drop(columns = ['_id'],axis = 1 , inplace=True)

# Rename field columns

rename_columns = {"billing_details_address_postal_code":"postal_code",
                  "billing_details_name":"name",
                  "billing_details_email":"email"}

charges2_flatten_data.rename(columns = rename_columns, inplace=True)

# Divide numbers by 100 

charges2_flatten_data[["amount","amount_captured"]] = charges2_flatten_data[["amount","amount_captured"]].div(100)

# Reformat date from UNIX epoch to datetime

charges2_flatten_data['created'] = charges2_flatten_data['created'].apply(lambda x: datetime.utcfromtimestamp(x))
charges2_flatten_data['created'] = (charges2_flatten_data['created']) + timedelta(hours=10)

# Clean name and emails to remove inconsistencies

charges2_flatten_data[['name', 'email']] = charges2_flatten_data[['name', 'email']].apply(lambda x: x.str.lower())
charges2_flatten_data['name'] = charges2_flatten_data['name'].str.title()


# Streamlit dashboard starts here
# 
# 
# 


st.title('Winlads Maldives Campaign')
st.divider()

# create a sidebar for the inputs

st.sidebar.title('Campaign Details')

st.sidebar.divider()



# Ask for variable inputs for campaign spending
campaign_cost = st.sidebar.number_input('Campaign Cost', min_value=0.0,value=10000.0)
ad_spend = st.sidebar.number_input('Ad spend', min_value=0.0,value=3000.0)

# Get campaign start date and end date

campaign_period = st.sidebar.slider(
    "Campaign Period",
    value = (datetime(2024, 6, 9), datetime.now()),
    min_value = datetime(2024, 1, 1),
    max_value = datetime(2025, 1, 1)
    )

# # Select owners name from exclude list

# unique_names = set(charges1_flatten_data['name'].unique()) | set(charges2_flatten_data['name'].unique())
# exclude_name_list = st.sidebar.multiselect('Exclude Names', unique_names)
# st.write(exclude_name_list)

exclude_name_list = []

if st.sidebar.checkbox('Remove admin transactions'):
    st.sidebar.write('Admin transactions removed')
    exclude_name_list = ["Shehan Tenabadu","Shehan Thenabadu","Shehan Thenabadu`","Shehan P Thenabdu","Shehan P Thenabadu",
                          "S", "Shehsn P Thenabadu", "Winlads Pty Ltt","Winlads Pty Ltd"]
else:
    exclude_name_list = []



# Convert created date to datetime
charges1_flatten_data['created'] = pd.to_datetime(charges1_flatten_data['created'])

# filter data based on criteria for stripe1 charges to get purchaser of one-offs

charges1_active_purchasers = charges1_flatten_data[(charges1_flatten_data['created'] >= campaign_period[0]) &
                                                   (charges1_flatten_data['created'] <= campaign_period[1]) &
                                                   (charges1_flatten_data['paid'] == True) &
                                                   (~charges1_flatten_data['description'].str.contains('Subscription', na=False)) &
                                                   (~charges1_flatten_data['name'].isin(exclude_name_list))
                                                  ]

col_1, col_2 =st.columns(2, gap="small", vertical_alignment="top")


with col_1:
    st.subheader('Stripe Admin@ One-offs')
    st.header(f":orange[{charges1_active_purchasers['id'].count()}]")

with col_2:
    st.subheader('Stripe Admin Revenue@ One-offs')
    st.header(f":orange[${charges1_active_purchasers['amount'].sum():.2f}]")

if st.checkbox('Show Stripe admin table'):
    st.subheader('Admin Data')
    st.write(charges1_active_purchasers)

st.divider()

# Convert created date to datetime
charges2_flatten_data['created'] = pd.to_datetime(charges2_flatten_data['created'])

# filter data based on criteria for stripe1 charges to get purchaser of one-offs

charges2_active_purchasers = charges2_flatten_data[(charges2_flatten_data['created'] >= campaign_period[0]) &
                                                   (charges2_flatten_data['created'] <= campaign_period[1]) &
                                                   (charges2_flatten_data['paid'] == True) &
                                                   (~charges2_flatten_data['name'].isin(exclude_name_list))
                                                  ]


col1, col2 =st.columns(2, gap="small", vertical_alignment="top")

with col1: 
    st.subheader('Stripe Finance@ One-offs')
    st.header(f":orange[{charges2_active_purchasers['id'].count()}]")

with col2:
    st.subheader('Stripe Finance Revenue@ One-offs')
    st.header(f":orange[${charges2_active_purchasers['amount'].sum():.2f}]")



if st.checkbox('Show Stripe finance table'):
    st.subheader('Finance data')
    st.write(charges2_active_purchasers)

st.divider()

st.subheader('Once off Campaign Revenue')
st.header(f":orange[${charges1_active_purchasers['amount'].sum() + charges2_active_purchasers['amount'].sum():.2f}]")

# st.write("")
st.divider()


st.subheader('Campaign Revenue less Ad Spend  ')
st.header(f":orange[${(charges1_active_purchasers['amount'].sum() + charges2_active_purchasers['amount'].sum() - ad_spend):.2f}]")
st.divider()

st.subheader('Campaign Revenue Less Campaign cost and Ad Spend')
st.header(f":orange[${(charges1_active_purchasers['amount'].sum() + charges2_active_purchasers['amount'].sum() - campaign_cost - ad_spend):.2f}]")
st.divider()

st.subheader('Campaign Profit/Loss per $1 Ad Spent')
st.header(f":orange[${(((charges1_active_purchasers['amount'].sum() + charges2_active_purchasers['amount'].sum())/ad_spend)-1):.2f}]")


st.button("Rerun")