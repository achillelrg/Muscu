import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

def get_data():
    """
    Connects to Google Sheets and returns the cleaned DataFrame.
    Uses Streamlit secrets for authentication.
    """
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # Retrieve credentials from Streamlit secrets
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], 
        scopes=scope
    )
    client = gspread.authorize(creds)
    
    # Open the specific sheet
    sheet = client.open("MUSCU").worksheet("DATA")
    
    # Get all records, skipping header rows if needed
    data = sheet.get_all_records(head=2, default_blank=None)
    
    df = pd.DataFrame(data)
    
    # Cleanup
    # Ensure we only keep named columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    # Filter rows with empty Exercise
    df = df[df['Exercice'] != ""]
    
    # Date conversion
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
    
    return df
