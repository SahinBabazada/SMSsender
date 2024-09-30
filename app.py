import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from streamlit_date_picker import date_picker, PickerType
import json

# Initialize session_state variables
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'password' not in st.session_state:
    st.session_state.password = ""

# Replace with your actual API endpoints
SEND_SMS_URL_1_N = "https://www.poctgoyercini.com/api_json/v1/Sms/Send_1_N"
SEND_SMS_URL_N_N = "https://www.poctgoyercini.com/api_json/v1/Sms/Send_N_N"
CHECK_STATUS_URL = "https://www.poctgoyercini.com/api_json/v1/Sms/Status"
BALANCE_CHECK_URL = "https://www.poctgoyercini.com/api_json/v1/Sms/CreditBalance"

# Function to format datetime for API
def format_date(date_time):
    if date_time is not None:
        date_time = datetime.strptime(date_time, '%Y-%m-%d %H:%M:%S')
        date_time = date_time.strftime('%Y%m%d %H:%M')
        return date_time
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

# Function to check SMS balance
def check_sms_balance(username, password):
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "Username": username,
        "Password": password
    }
    response = requests.post(BALANCE_CHECK_URL, headers=headers, json=payload)
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

    # Display logged-in username
    st.sidebar.write(f"Logged in as: **{username}**")

    st.title("SMS Service")

    # Section for checking SMS balance
    with st.expander("Check SMS Balance"):
        if st.button("Check Balance"):
            balance_response = check_sms_balance(username, password)
            if balance_response.get("StatusCode") == 200:
                st.success(f"Balance: {balance_response['Result']['Balance']}")
            else:
                st.error(f"Error: {balance_response.get('StatusDescription')}")

    # Tabs for 1-to-N and N-to-N SMS
    tab1, tab2 = st.tabs(["1-to-N SMS", "N-to-N SMS"])

    # Tab 1: 1-to-N SMS
    with tab1:
        with st.form("form_1_to_n"):
            message_1_n = st.text_area("Message", height=100)
            receivers_1_n = st.text_area("Receiver List", height=100)

            # Columns to align date picker and checkbox
            col1, col2 = st.columns([2, 1])

            with col1:
                st.write("Send Date & Time")
                send_date_time_1_n = date_picker(picker_type=PickerType.time, value=datetime.now(), key='send_date_time_1_n')
             
            with col2:
                send_now_1_n = st.checkbox("Send Now", value=True)

            # Expire Date & Time with aligned checkbox
            col1_exp, col2_exp = st.columns([2, 1])

            with col1_exp:
                st.write("Expire Date & Time")
                expire_date_time_1_n = date_picker(picker_type=PickerType.time, value=datetime.now(), key='expire_date_time_1_n')
            
            with col2_exp:
                expire_never_1_n = st.checkbox("Never Expire", value=True)

            submit_button_1_n = st.form_submit_button("Send 1-to-N SMS")

            if submit_button_1_n:
                formatted_send_date_1_n = None if send_now_1_n else format_date(send_date_time_1_n)
                formatted_expire_date_1_n = None if expire_never_1_n else format_date(expire_date_time_1_n)
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
                col1_n, col2_n = st.columns([3, 1])

                with col1_n:
                    st.write("Send Date & Time")
                    send_date_n_n = date_picker(picker_type=PickerType.time, value=datetime.now(), key='send_date_n_n')

                with col2_n:
                    send_now_n_n = st.checkbox("Send Now", value=True)

                col1_exp_n, col2_exp_n = st.columns([3, 1])

                with col1_exp_n:
                    st.write("Expire Date & Time")
                    expire_date_n_n = date_picker(picker_type=PickerType.time, value=datetime.now(), key='expire_date_n_n')

                with col2_exp_n:
                    expire_never_n_n = st.checkbox("Never Expire", value=True)

                submit_button_n_n = st.form_submit_button("Send N-to-N SMS")

                if submit_button_n_n:
                    formatted_send_date_n_n = None if send_now_n_n else format_date(send_date_n_n)
                    formatted_expire_date_n_n = None if expire_never_n_n else format_date(expire_date_n_n)

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
                    scss_count = 0
                    for response in responses:
                        if response.get('StatusCode') == 200:
                            success_count += len(response.get('Result', []))
                            scss_count += 1
                        else:
                            failure_count += 1

                    if failure_count == 0:
                        st.success(f"All N-to-N SMS messages sent successfully to {success_count} recipients.")
                    if failure_count > 0:
                        st.error(f"Failed to send N-to-N SMS to some recipients. {failure_count} chunks failed.")
                    
                    st.success(f"{scss_count} chunks successed.")
