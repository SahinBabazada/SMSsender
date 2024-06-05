import streamlit as st
import pandas as pd
import requests
from datetime import date, datetime
import json

# Initialize session_state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'password' not in st.session_state:
    st.session_state.password = ""

def format_message(row, message_template, format_options):
    """Formats a message based on template and formatting options."""
    try:
        for key, format_type in format_options.items():
            if key in row:
                if format_type == 'date':
                    row[key] = pd.to_datetime(row[key]).strftime('%Y-%m-%d')
                elif format_type.startswith('round'):
                    digits = int(format_type.split('-')[1])
                    row[key] = round(float(row[key]), digits)
        formatted_message = message_template.format(**row)
    except Exception as e:
        formatted_message = f"Error formatting message: {e}"
    return formatted_message

# Replace with your actual API endpoints
SEND_SMS_URL_1_N = "https://www.poctgoyercini.com/api_json/v1/Sms/Send_1_N"
SEND_SMS_URL_N_N = "https://www.poctgoyercini.com/api_json/v1/Sms/Send_N_N"
CHECK_STATUS_URL = "https://www.poctgoyercini.com/api_json/v1/Sms/Status"
EXCEL_FILE = 'sms_requests.xlsx'

# Format SendDate and ExpireDate in the 'yyyyMMdd HH' format or use null
def format_date(date, time):
    if date is not None and time is not None:
        return datetime.combine(date, time).strftime('%Y%m%d %H')
    else:
        return None

# Function to send 1-N SMS
def send_sms_1_n(username, password, message, receivers, send_date, expire_date):
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "Message": message,
        "Receivers": receivers,
        "SendDate": send_date,
        "ExpireDate": expire_date,
        "Username": username,
        "Password": password
    }
    response = requests.post(SEND_SMS_URL_1_N, headers=headers, json=payload)
    return response.json()

# Function to send N-N SMS
def send_sms_n_n(username, password, messages, send_date, expire_date):
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "Messages": messages,
        "SendDate": send_date,
        "ExpireDate": expire_date,
        "Username": username,
        "Password": password
    }
    response = requests.post(SEND_SMS_URL_N_N, headers=headers, json=payload)
    return response.json()

# Function to check SMS status
def get_status(username, password, message_ids):
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "MessageIds": message_ids,
        "Username": username,
        "Password": password
    }
    response = requests.post(CHECK_STATUS_URL, headers=headers, json=payload)
    return response.json()

# Function to divide a list into chunks
def chunk_list(data, chunk_size):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

# Show login form if not logged in
if not st.session_state.logged_in:
    st.title("Login to SMS Service")
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

        if login_button:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.session_state.password = password
            st.rerun()

# If logged in, display the SMS service UI
if st.session_state.logged_in:    
    # Use st.session_state.username and st.session_state.password for SMS functions
    username = st.session_state.username
    password = st.session_state.password

    # Now you can directly proceed with the rest of your Streamlit application's functionality as before.
    # For example, defining the title, tabs, forms, etc.
    st.title("SMS Service")

    # Tabs for 1-to-N and N-to-N SMS
    tab1, tab2 = st.tabs(["1-to-N SMS", "N-to-N SMS"])

    # Tab 1: 1-to-N SMS
    with tab1:
        with st.form("form_1_to_n"):
            message_1_n = st.text_area("Message", height=100)
            receivers_1_n = st.text_area("Receiver List", height=100)
            send_date_1_n = st.date_input(
                "Send Date", min_value=datetime.today(), help="Leave blank for immediate send")
            send_time_1_n = st.time_input("Send Time")
            expire_date_1_n = st.date_input(
                "Expire Date", help="Leave blank if no expiry is needed")
            expire_time_1_n = st.time_input("Expire Time")
            send_now_1_n = st.checkbox("Send Now", value=True)
            expire_never_1_n = st.checkbox("Never Expire", value=True)
            submit_button_1_n = st.form_submit_button("Send 1-to-N SMS")

            if submit_button_1_n:
                # Assuming send_now_1_n handles the immediate sending logic
                formatted_send_date_1_n = None if send_now_1_n else format_date(
                    send_date_1_n, send_time_1_n)
                formatted_expire_date_1_n = None if expire_never_1_n else format_date(
                    expire_date_1_n, expire_time_1_n)
                receivers_list_1_n = [r.strip() for r in receivers_1_n.split("\n")]
                
                # Divide receivers into chunks
                receiver_chunks = list(chunk_list(receivers_list_1_n, 800))
                responses = []
                for chunk in receiver_chunks:
                    response_1_n = send_sms_1_n(
                        username,
                        password,
                        message_1_n,
                        chunk,
                        formatted_send_date_1_n,
                        formatted_expire_date_1_n
                    )
                    responses.append(response_1_n)

                # Handle responses
                success_count = 0
                failure_count = 0
                for response in responses:
                    if response.get('StatusCode') == 200:
                        success_count += len(response.get('Result', []))
                    else:
                        failure_count += 1

                if failure_count == 0:
                    st.success(f"SMS successfully sent to {success_count} recipients.")
                else:
                    st.error(f"Failed to send SMS to some recipients. {failure_count} chunks failed.")

    # Tab 2: N-to-N SMS
    with tab2:
        if 'receiver_message_pairs' not in st.session_state:
            st.session_state['receiver_message_pairs'] = []

        uploaded_file = st.file_uploader(
            "Upload a recipient list (Excel or CSV)", type=['xlsx', 'csv'])
        receiver_message_pairs = []
        if uploaded_file:
            # Read the file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.dataframe(df.head())

            # Enter message template
            message_template = st.text_area(
                "Enter your message template (use {column_name} for placeholders):", value="Salam {name}, Sizin  {date}.")
            receiver_column = st.selectbox(
                "Which column contains the phone numbers?", df.columns)

            # Generate message-receiver pairs
            if st.button("Generate Messages"):
                st.session_state['receiver_message_pairs'] = []  # Reinitialize to empty for each generation
                for index, row in df.iterrows():
                    try:
                        message = message_template.format(**row)
                        receiver = row[receiver_column]
                        st.session_state['receiver_message_pairs'].append({"Receiver": receiver, "Message": message})
                    except Exception as e:
                        st.error(f"Error in generating message for row {index + 1}: {e}")
                if st.session_state['receiver_message_pairs']:
                    st.write("Generated Messages:")
                    st.dataframe(pd.DataFrame(st.session_state['receiver_message_pairs']))
                else:
                    st.write("No messages generated. Please check your template and data.")

            with st.form("form_n_to_n"):
                send_date_n_n = st.date_input(
                    "Send Date", min_value=datetime.today(), help="Leave blank for immediate send")
                send_time_n_n = st.time_input("Send Time")
                expire_date_n_n = st.date_input(
                    "Expire Date", help="Leave blank if no expiry is needed")
                expire_time_n_n = st.time_input("Expire Time")
                send_now_n_n = st.checkbox("Send Now", value=True)
                expire_never_n_n = st.checkbox("Never Expire", value=True)
                submit_button_n_n = st.form_submit_button("Send N-to-N SMS")

                if submit_button_n_n:
                    formatted_send_date_n_n = None if send_now_n_n else format_date(send_date_n_n, send_time_n_n)
                    formatted_expire_date_n_n = None if expire_never_n_n else format_date(expire_date_n_n, expire_time_n_n)

                    # Divide message-receiver pairs into chunks
                    message_chunks = list(chunk_list(st.session_state['receiver_message_pairs'], 800))
                    responses = []
                    for chunk in message_chunks:
                        response_n_n = send_sms_n_n(
                            username,
                            password,
                            chunk,
                            formatted_send_date_n_n,
                            formatted_expire_date_n_n
                        )
                        responses.append(response_n_n)

                    # Handle responses
                    success_count = 0
                    failure_count = 0
                    for response in responses:
                        if response.get('StatusCode') == 200:
                            success_count += len(response.get('Result', []))
                        else:
                            failure_count += 1

                    if failure_count == 0:
                        st.success(f"All N-to-N SMS messages sent successfully to {success_count} recipients.")
                    else:
                        st.error(f"Failed to send N-to-N SMS to some recipients. {failure_count} chunks failed.")
