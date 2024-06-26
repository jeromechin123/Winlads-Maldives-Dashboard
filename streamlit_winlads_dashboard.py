import streamlit as st
import pandas as pd
import numpy as np
import os
from pymongo import MongoClient
import pprint
from datetime import datetime


# Test connection to database
try: 
       
    client = MongoClient(st.secrets["connection_url"])        
    client.admin.command('ping')
    print("Database connection established...")
except Exception as e:
    print(f"Database connection error!! {e}" )

# Connect to collection in database

database_name = "curated_data"
import_collection_name = "stripe1_charges_selected"

db = client[database_name]
collection = db[import_collection_name]

# Extract all data from collection 

chrarges1_data = list(collection.find())    

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

charges1_flatten_data['created'] = charges1_flatten_data['created'].apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))

# Clean name and emails to remove inconsistencies

charges1_flatten_data[['name', 'email']] = charges1_flatten_data[['name', 'email']].apply(lambda x: x.str.lower())
charges1_flatten_data['name'] = charges1_flatten_data['name'].str.title()

# Import data from stripe2_charges to clean

database_name = "curated_data"
import_collection_name = "stripe2_charges_selected"

db = client[database_name]
collection = db[import_collection_name]

# Extract all data from collection 

stripe2_charges_data = list(collection.find())    

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

charges2_flatten_data['created'] = charges2_flatten_data['created'].apply(lambda x: datetime.utcfromtimestamp(x).strftime('%Y-%m-%d %H:%M:%S'))


# Clean name and emails to remove inconsistencies

charges2_flatten_data[['name', 'email']] = charges2_flatten_data[['name', 'email']].apply(lambda x: x.str.lower())
charges2_flatten_data['name'] = charges2_flatten_data['name'].str.title()


# Streamlit dashboard starts here
# 
# 
# 


st.title('Winlads Maldives Campaign')

# Select owners name from exclude list
exclude_name_list = st.multiselect('Exclude Names', charges1_flatten_data['name'].unique())

# Ask for variable inputs for campaign spending
campaign_cost = st.number_input('Campaign Cost', min_value=0.0,value=10000.0)
ad_spend = st.number_input('Ad spend', min_value=0.0,value=5000.0)

# Get campaign start date
cutoffdate = st.date_input('Campaign Start Date', format = "DD/MM/YYYY")
cutoff_datetime = pd.to_datetime(cutoffdate)

st.divider()

# Convert created date to datetime
charges1_flatten_data['created'] = pd.to_datetime(charges1_flatten_data['created'])

# filter data based on criteria for stripe1 charges to get purchaser of one-offs

charges1_active_purchasers = charges1_flatten_data[(charges1_flatten_data['created'] >= cutoff_datetime) &
                                                   (charges1_flatten_data['paid'] == True) &
                                                   (charges1_flatten_data['description'] == 'Winlads Pty Ltd') &
                                                   (~charges1_flatten_data['name'].isin(exclude_name_list))
                                                  ]

col_1, col_2 =st.columns(2, gap="small", vertical_alignment="top")

with col_1:
    st.subheader('Stripe Admin@ One-offs')
    st.write(charges1_active_purchasers['id'].count())

with col_2:
    st.subheader('Stripe Admin Revenue@ One-offs')
    st.write("$"+"{:.2f}".format(charges1_active_purchasers['amount'].sum()))

if st.checkbox('Show Admin raw data'):
    st.subheader('Raw data')
    st.write(charges1_active_purchasers)

st.divider()

# Convert created date to datetime
charges2_flatten_data['created'] = pd.to_datetime(charges2_flatten_data['created'])

# filter data based on criteria for stripe1 charges to get purchaser of one-offs

charges2_active_purchasers = charges1_flatten_data[(charges1_flatten_data['created'] >= cutoff_datetime) &
                                          (charges1_flatten_data['paid'] == True) &
                                          (~charges1_flatten_data['name'].isin(exclude_name_list))
                                          ]


col1, col2 =st.columns(2, gap="small", vertical_alignment="top")

with col1: 
    st.subheader('Stripe Finance@ One-offs')
    st.write(charges2_active_purchasers['id'].count())

with col2:
    st.subheader('Stripe Finance Revenue@ One-offs')
    st.write("$"+"{:.2f}".format(charges2_active_purchasers['amount'].sum()))



if st.checkbox('Show Finance raw data'):
    st.subheader('Raw data')
    st.write(charges2_active_purchasers)

st.divider()

st.subheader('Total Revenue')
st.write("$"+"{:.2f}".format(charges1_active_purchasers['amount'].sum() + charges2_active_purchasers['amount'].sum()))

st.subheader('Total Revenue less campaign cost')
st.write("$"+"{:.2f}".format(charges1_active_purchasers['amount'].sum() + charges2_active_purchasers['amount'].sum() - campaign_cost))

st.subheader('Total Revenue less campaign cost and ad spend')
st.write("$"+"{:.2f}".format(charges1_active_purchasers['amount'].sum() + charges2_active_purchasers['amount'].sum() - campaign_cost - ad_spend))

st.subheader('Return on ad spend')
st.write("$"+"{:.2f}".format((charges1_active_purchasers['amount'].sum() + charges2_active_purchasers['amount'].sum())/ad_spend))



