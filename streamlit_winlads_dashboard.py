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

def get_data(database_name, import_collection_name):
    db = client[database_name]
    collection = db[import_collection_name]
    return list(collection.find())



# Extract all data from collection 

charges1_data = get_data(database_name, import_collection_name)


# Flatten data to get json fields in individual columns -- Use '_' as seperator

charges1_flatten_data = pd.json_normalize(charges1_data, sep='_')

# Drop '_id' column to prevent upserting errors

charges1_flatten_data.drop( columns = ['_id'],axis = 1 , inplace=True)

# Rename field columns

rename_columns = {"billing_details_address_postal_code":"postal_code","billing_details_name":"name","receipt_email":"email"}
charges1_flatten_data.rename(columns = rename_columns, inplace=True)

# Divide numbers by 100 

charges1_flatten_data[["amount","amount_captured"]] = charges1_flatten_data[["amount","amount_captured"]].div(100)

# Reformat date from UNIX epoch to datetime

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

# Import data from stripe1_subscriptions_clean collection

database_name = "curated_data"  
import_collection_name = "stripe1_subscriptions_cleaned"

# Extract all data from collection  

stripe1_subscriptions_data = get_data(database_name, import_collection_name)

subscriptions_flatten_data = pd.json_normalize(stripe1_subscriptions_data, sep='_')

subscriptions_flatten_data.drop(columns = ['_id'],axis = 1 , inplace=True)


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
campaign_cost = st.sidebar.number_input('Giveaway Prize Cost', min_value=0.0,value=9499.0)
ad_spend = st.sidebar.number_input('Ad spend', min_value=0.0,value=5690.12)

# Get campaign start date and end date


campaign_start_date = pd.to_datetime (st.sidebar.date_input("Campaign Start Date", value = datetime(2024, 6, 9), format = "DD/MM/YYYY"))
campaign_end_date = pd.to_datetime (st.sidebar.date_input("Campaign End Date", value = datetime(2024, 6, 30), format = "DD/MM/YYYY", min_value= (campaign_start_date))) + timedelta(days=1)

reporting_period_start = pd.to_datetime (st.sidebar.date_input("Reporting Period Start Date", value = datetime(2024, 6, 1), format = "DD/MM/YYYY"))
reporting_period_end = pd.to_datetime (st.sidebar.date_input("Reporting Period End Date", value = datetime(2024, 6, 30), format = "DD/MM/YYYY", min_value= (reporting_period_start))) + timedelta(days=1)

# Select owners name from exclude list

exclude_name_list = ["Shehan Tenabadu","Shehan Thenabadu","Shehan Thenabadu`","Shehan P Thenabdu","Shehan P Thenabadu",
                          "S", "Shehsn P Thenabadu", "Winlads Pty Ltt","Winlads Pty Ltd"]

if st.sidebar.checkbox('Add admin transactions'):
    st.sidebar.write('Admin transactions added')
    exclude_name_list = []

   


# filter data based on criteria for stripe1 charges to get purchaser of one-offs

charges1_active_purchasers = charges1_flatten_data[(charges1_flatten_data['created'] >=   campaign_start_date) &
                                                   (charges1_flatten_data['created'] <=  campaign_end_date ) &
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


# filter data based on criteria for stripe2 charges to get purchaser of one-offs

charges2_active_purchasers = charges2_flatten_data[(charges2_flatten_data['created'] >= campaign_start_date) &
                                                   (charges2_flatten_data['created'] <= campaign_end_date) &
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

col_1, col_2 =st.columns(2, gap="small", vertical_alignment="top")

total_one_off_revenue = charges1_active_purchasers['amount'].sum() + charges2_active_purchasers['amount'].sum()
with col_1:
    
    st.subheader('Total Once-off Revenue')
    st.header(f":orange[${charges1_active_purchasers['amount'].sum() + charges2_active_purchasers['amount'].sum():.2f}]")

    st.subheader('Campaign Profit/Loss')
    st.header(f":orange[${(charges1_active_purchasers['amount'].sum() + charges2_active_purchasers['amount'].sum() - ad_spend):.2f}]")



with col_2:
    st.subheader('Return on Ad Spend')
    st.header(f":orange[{((total_one_off_revenue - ad_spend)/ad_spend*100):.2f}%]")

    st.subheader('Total Once-off Transactions')
    st.header(f":orange[{(charges1_active_purchasers['id'].count() + charges2_active_purchasers['id'].count())}]")

st.divider()

# # filter data based on criteria for active subscribers
# st.write(subscriptions_flatten_data)                                                


# active_subscribers = subscriptions_flatten_data[
#                                                 (subscriptions_flatten_data['current_period_start'] <= campaign_end_date) &
#                                                 (subscriptions_flatten_data['current_period_end'] >= campaign_end_date) &
#                                                 (subscriptions_flatten_data['created'] <= campaign_end_date) &
#                                                 (~subscriptions_flatten_data['status'].str.contains('incomplete_expired|past_due')) &
#                                                 (~subscriptions_flatten_data['name'].isin(exclude_name_list))
#                                                 ]
# st.write(active_subscribers)                                                

# col_1, col_2 =st.columns(2, gap="small", vertical_alignment="top")

# with col_1:
#     st.subheader('Active Subscribers')
#     st.header(f":orange[{active_subscribers['id'].count()}]")

# with col_2:
#     st.subheader('Active Subscribers Revenue')
#     st.header(f":orange[${active_subscribers['monthly_amount'].sum():.2f}]")

# if st.checkbox('Show Data for Active Subscribers'):
#     st.subheader('Active Subscribers Data')
#     st.write(active_subscribers)


# Subscriber information for campaign period only

charges1_new_subscribers = charges1_flatten_data[(charges1_flatten_data['created'] >=  campaign_start_date) &
                                                    (charges1_flatten_data['created'] <=  campaign_end_date ) &
                                                    (charges1_flatten_data['paid'] == True) &
                                                    (charges1_flatten_data['description'].str.contains('Subscription creation', na=False)) &
                                                    (~charges1_flatten_data['name'].isin(exclude_name_list))
                                                    ]

charges1_new_renewals = charges1_flatten_data[(charges1_flatten_data['created'] >=   campaign_start_date) &
                                                    (charges1_flatten_data['created'] <=   campaign_end_date ) &
                                                    (charges1_flatten_data['paid'] == True) &
                                                    (charges1_flatten_data['description'].str.contains('Subscription update', na=False)) &
                                                    (~charges1_flatten_data['name'].isin(exclude_name_list))
                                                    ]

total_subscription_revenue_campaign_period = charges1_new_subscribers['amount'].sum() + charges1_new_renewals['amount'].sum()

if st.checkbox('Show info on subscribers movement during campaign period'):

    # filter data based on criteria for new subscribers



    col_1, col_2 =st.columns(2, gap="small", vertical_alignment="top")

    with col_1:
        st.subheader('New Subscribers')
        st.header(f":orange[{charges1_new_subscribers['id'].count()}]")

    with col_2:
        st.subheader('New Subscribers Revenue')
        st.header(f":orange[${charges1_new_subscribers['amount'].sum():.2f}]")

    if st.checkbox('Show Data for New Subscribers'):
        st.subheader('New Subscribers Data')
        st.write(charges1_new_subscribers)

    # filter data based on criteria for renewing subscribers

 
    col_1, col_2 =st.columns(2, gap="small", vertical_alignment="top")

    with col_1:
        st.subheader('Subscription Renewal')
        st.header(f":orange[{charges1_new_renewals['id'].count()}]")

    with col_2:
        st.subheader('Renewal Revenue')
        st.header(f":orange[${charges1_new_renewals['amount'].sum():.2f}]")

    if st.checkbox('Show Data for Renewals'):
        st.subheader('Renewals Data')
        st.write(charges1_new_renewals )
    
    st.subheader('Total Subscription Revenue for Campaign Period')
    st.header(f":orange[${total_subscription_revenue_campaign_period:.2f}]")
    

st.divider()

# Subsription information for reporting period only

new_subscribers_reporting_period = charges1_flatten_data[(charges1_flatten_data['created'] >=  reporting_period_start) &
                                                    (charges1_flatten_data['created'] <=   reporting_period_end ) &
                                                    (charges1_flatten_data['paid'] == True) &
                                                    (charges1_flatten_data['description'].str.contains('Subscription creation', na=False)) &
                                                    (~charges1_flatten_data['name'].isin(exclude_name_list))
                                                    ]

subscriber_renewals_reporting_period = charges1_flatten_data[(charges1_flatten_data['created'] >=   reporting_period_start) &
                                                    (charges1_flatten_data['created'] <=   reporting_period_end ) &
                                                    (charges1_flatten_data['paid'] == True) &
                                                    (charges1_flatten_data['description'].str.contains('Subscription update', na=False)) &
                                                    (~charges1_flatten_data['name'].isin(exclude_name_list))
                                                    ]


col_1, col_2 =st.columns(2, gap="small", vertical_alignment="top")

with col_1:
    st.subheader('New Subscribers for Reporting Period')
    st.header(f":orange[{new_subscribers_reporting_period['id'].count()}]")

with col_2:
    st.subheader('New Subscribers Revenue for Reporting Period')
    st.header(f":orange[${new_subscribers_reporting_period['amount'].sum():.2f}]")

if st.checkbox('Show Data for New Subscribers during Reporting Period'):
    st.subheader('New Subscribers Data')
    st.write(new_subscribers_reporting_period)

# filter data based on criteria for renewing subscribers


col_1, col_2 =st.columns(2, gap="small", vertical_alignment="top")

with col_1:
    st.subheader('Subscription Renewal for Reporting Period')
    st.header(f":orange[{subscriber_renewals_reporting_period['id'].count()}]")

with col_2:
    st.subheader('Renewal Revenue for Reporting Period')
    st.header(f":orange[${subscriber_renewals_reporting_period['amount'].sum():.2f}]")

if st.checkbox('Show Data for Renewals during Reporting Period'):
    st.subheader('Renewals Data')
    st.write(subscriber_renewals_reporting_period )
st.divider()

# Total Subscription revenue and  once off revenue

total_subscription_revenue_reporting_period = subscriber_renewals_reporting_period['amount'].sum() + new_subscribers_reporting_period['amount'].sum()

col_1, col_2 =st.columns(2, gap="small", vertical_alignment="top")  

with col_1:
    st.subheader('Total Subscription Revenue for Reporting Period')
    st.header(f":orange[${total_subscription_revenue_reporting_period:.2f}]")        

with col_2:
    st.subheader('Total Revenue for Once-offs for Reporting Period')
    st.header(f":orange[${(total_one_off_revenue):.2f}]")

st.divider()

st.subheader('Total Revenue for Reporting Period')

revenue = (charges1_active_purchasers['amount'].sum() + 
           charges2_active_purchasers['amount'].sum() + 
           subscriber_renewals_reporting_period['amount'].sum() +
           new_subscribers_reporting_period['amount'].sum())

st.header(f":orange[${(revenue):.2f}]")


st.subheader('Total Profit/Loss for Reporting Period')

profit = (revenue - campaign_cost - ad_spend)

st.header(f":red[${(profit):.2f}]")

st.divider()

# Bar chart for one-off revenue over campaign period

st.subheader('One-off Revenue over Campaign Period')
oneoffrevenuechart = pd.concat([charges1_active_purchasers[['created', 'amount']], charges2_active_purchasers[['created', 'amount']]])

oneoffrevenuechart['created'] = oneoffrevenuechart['created'].dt.date
aggreated_oneoffrevenue = oneoffrevenuechart.groupby('created').sum().reset_index()

st.bar_chart(data = aggreated_oneoffrevenue, x = 'created', y = 'amount', x_label = "Date", y_label= "Revenue ($)", height = 400)

st.divider()

