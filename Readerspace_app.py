import streamlit as st
import json
import os
from datetime import datetime
from twilio.rest import Client

FILENAME = "library_users.json"
MONTHLY_FEE = 500  # 💰 change as per your library fee

# Load Data
def load_data():
    if os.path.exists(FILENAME):
        with open(FILENAME, "r") as f:
            return json.load(f)
    return {}

# Save Data
def save_data(data):
    with open(FILENAME, "w") as f:
        json.dump(data, f, indent=4)

# Twilio SMS Sender
def send_sms(contact, message):
    try:
        account_sid = st.secrets["TWILIO_ACCOUNT_SID"]
        auth_token = st.secrets["TWILIO_AUTH_TOKEN"]
        twilio_number = st.secrets["TWILIO_PHONE_NUMBER"]

        client = Client(account_sid, auth_token)
        client.messages.create(
            body=message,
            from_=twilio_number,
            to=contact
        )
        st.success(f"📩 Message sent to {contact}")
    except Exception as e:
        st.error(f"❌ SMS sending failed: {e}")

# Main App
st.title("📚 ReaderSpace Library Management System")

data = load_data()

menu = ["New User Registration", "Existing User Login", "Check Pending Payments", "Record Payment"]
choice = st.sidebar.selectbox("Menu", menu)

# ---------------- New User ----------------
if choice == "New User Registration":
    st.subheader("🆕 Register New User")
    name = st.text_input("Full Name")
    father_name = st.text_input("Father's Name")
    address = st.text_area("Address")
    email = st.text_input("Email")
    contact = st.text_input("Contact Number (with +91)")
    seatno = st.text_input("Seat Number")
    library_code = "L" + str(len(data) + 2025001)
    admission_date = datetime.now().strftime("%Y-%m-%d")

    if st.button("Register"):
        data[library_code] = {
            "name": name,
            "father_name": father_name,
            "address": address,
            "email": email,
            "contact": contact,
            "seatno": seatno,
            "admission_date": admission_date,
            "last_payment": admission_date,
            "payments": [
                {"date": admission_date, "amount": MONTHLY_FEE}
            ]
        }
        save_data(data)
        st.success(f"✅ User registered successfully! Library Code: {library_code}")
        send_sms(contact, f"Welcome {name}! Your Library Code is {library_code}. Admission Date: {admission_date}. First payment of ₹{MONTHLY_FEE} received.")

# ---------------- Existing User ----------------
elif choice == "Existing User Login":
    st.subheader("🔑 Login Existing User")
    library_code = st.text_input("Enter Library Code")
    if st.button("Login"):
        if library_code in data:
            user = data[library_code]
            st.json(user)
            st.success("✅ Login Successful")
        else:
            st.error("❌ Invalid Library Code")

# ---------------- Check Pending Payments ----------------
elif choice == "Check Pending Payments":
    st.subheader("💰 Pending Payment Status")
    today = datetime.now()
    for code, user in data.items():
        last_payment = datetime.strptime(user["last_payment"], "%Y-%m-%d")
        months_due = (today.year - last_payment.year) * 12 + today.month - last_payment.month

        if months_due > 0:
            due_amount = months_due * MONTHLY_FEE
            st.warning(f"⚠ {user['name']} (Code: {code}) has {months_due} month(s) due = ₹{due_amount}")
            send_sms(user["contact"], f"Dear {user['name']}, you have {months_due} month(s) pending. Total Due: ₹{due_amount}. Please pay soon.")
        else:
            st.info(f"✅ {user['name']} (Code: {code}) is up to date")

# ---------------- Record Payment ----------------
elif choice == "Record Payment":
    st.subheader("💵 Record Monthly Payment")
    library_code = st.text_input("Enter Library Code")
    if st.button("Fetch User"):
        if library_code in data:
            user = data[library_code]
            st.write(f"👤 {user['name']} ({library_code})")
            months_due = (datetime.now().year - datetime.strptime(user["last_payment"], "%Y-%m-%d").year) * 12 + \
                         (datetime.now().month - datetime.strptime(user["last_payment"], "%Y-%m-%d").month)
            st.write(f"📅 Months Due: {months_due}")

            payment_months = st.number_input("Months Paying For", min_value=1, value=1)
            total_amount = payment_months * MONTHLY_FEE
            st.write(f"💰 Payment Amount: ₹{total_amount}")

            if st.button("Confirm Payment"):
                new_payment_date = datetime.now().strftime("%Y-%m-%d")
                user["last_payment"] = new_payment_date
                user["payments"].append({"date": new_payment_date, "amount": total_amount})
                save_data(data)
                st.success(f"✅ Payment of ₹{total_amount} recorded for {user['name']}")
                send_sms(user["contact"], f"Payment received: ₹{total_amount}. Thank you {user['name']}! Your next due will be next month.")
        else:
            st.error("❌ Invalid Library Code")
