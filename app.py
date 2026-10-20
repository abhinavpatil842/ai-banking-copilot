import streamlit as st
import pandas as pd
import requests
from google import genai

st.set_page_config(page_title="AI Banking Copilot", page_icon="🏦")

st.title("🏦 AI Banking Copilot")
st.subheader("Payments Operations Dashboard")

st.write("Monitor payment transactions and identify exceptions.")

payments = pd.DataFrame([
    {"Payment ID": "PAY1001", "Rail": "PESONet", "Amount (PHP)": 25000, "Status": "Completed", "Reason": "None"},
    {"Payment ID": "PAY1002", "Rail": "InstaPay", "Amount (PHP)": 1500, "Status": "Failed", "Reason": "Invalid beneficiary account"},
    {"Payment ID": "PAY1003", "Rail": "PESONet", "Amount (PHP)": 18000, "Status": "Pending", "Reason": "Awaiting confirmation"},
    {"Payment ID": "PAY1004", "Rail": "InstaPay", "Amount (PHP)": 3200, "Status": "Completed", "Reason": "None"},
])

rail_filter = st.selectbox(
    "Filter by Payment Rail",
    ["All", "PESONet", "InstaPay"]
)
status_filter = st.selectbox(
    "Filter by Payment Status",
    ["All", "Completed", "Failed", "Pending"]
)

filtered_payments = payments.copy()

if status_filter != "All":
    filtered_payments = filtered_payments[
        filtered_payments["Status"] == status_filter
    ]

if rail_filter != "All":
    filtered_payments = filtered_payments[
        filtered_payments["Rail"] == rail_filter
    ]

st.dataframe(filtered_payments, use_container_width=True)
st.download_button(
    label="Download Payment Report",
    data=filtered_payments.to_csv(index=False),
    file_name="payment_report.csv",
    mime="text/csv"
)

st.metric("Total Payments", len(payments))
st.metric("Failed Payments", len(payments[payments["Status"] == "Failed"]))
st.subheader("Payment Volume by Status")

volume = payments.groupby("Status")["Amount (PHP)"].sum()

st.bar_chart(volume)
st.subheader("Payment Count by Rail")

rail_counts = payments["Rail"].value_counts()

st.bar_chart(rail_counts)
st.subheader("Payment Exception Analysis")

failed_payments = payments[payments["Status"] == "Failed"]

if not failed_payments.empty:
    for _, payment in failed_payments.iterrows():
        st.warning(f"Payment {payment['Payment ID']} has failed.")
        reason = payment["Reason"]

        if reason == "Invalid beneficiary account":
            st.write("Suggested action: Verify beneficiary account details.")
        elif reason == "Awaiting confirmation":
            st.write("Suggested action: Check downstream payment status before taking further action.")
        else:
            st.write("Suggested action: Review the payment status and exception details.")
else:
    st.success("No failed payments found.")
st.subheader("Investigate a Payment")


payment_id = st.selectbox(
    "Select Payment ID",
    payments["Payment ID"]
)

selected_payment = payments[
    payments["Payment ID"] == payment_id
].iloc[0]

st.write("Payment Rail:", selected_payment["Rail"])
st.write("Amount:", selected_payment["Amount (PHP)"], "PHP")
st.write("Status:", selected_payment["Status"])
st.write("Reason:", selected_payment["Reason"])
if selected_payment["Status"] == "Failed":
    st.error("Action Required: Investigate failed payment")
elif selected_payment["Status"] == "Pending":
    st.warning("Monitor: Payment processing is pending")
else:
    st.success("No failure indicated in the payment record")


st.subheader("AI-Powered Investigation")

if st.button("Analyse Selected Payment"):
    status = selected_payment["Status"]

    if status == "Completed":
        st.success("Payment record shows Completed.")
        st.info(
            "Settlement and reconciliation are not confirmed "
            "by this status alone."
        )

    else:
        api_key = st.secrets.get("GEMINI_API_KEY")

        if not api_key:
            st.error("Gemini API key is not configured.")
        else:
            
            
            payment_details = selected_payment.to_dict()
            prompt = f"""
            You are a bank payments operations analyst.
            Analyse this payment record: {payment_details}

            Respond in no more than 120 words using these headings:
            1. Status: Explain what the status means.
            2. Likely cause: State the recorded reason and one
               plausible explanation. Clearly label uncertainty.
            3. Next action: Give up to 3 practical investigation steps.

            Be concise and operational. Do not invent facts,
            message codes, settlement outcomes, or reversal status.
            Do not recommend retrying until the failure is verified.
            """



            
            
            
            try:
                client = genai.Client(api_key=api_key)

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt,
                    config={
                        "max_output_tokens": 250
                    },
                )

                st.markdown(response.text)

            except Exception as e:
                st.error(f"AI analysis failed: {e}")
