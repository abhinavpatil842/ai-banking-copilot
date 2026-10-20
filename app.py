import streamlit as st
import pandas as pd
import requests

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
            "No failure is indicated by this record. "
            "Settlement and reconciliation are not confirmed."
        )

    else:
        prompt = f"""
You are a banking payments operations assistant.

Payment details:
ID: {selected_payment['Payment ID']}
Rail: {selected_payment['Rail']}
Amount: PHP {selected_payment['Amount (PHP)']}
Status: {status}
Reason: {selected_payment['Reason']}

If Status is Failed:
- State that the payment has FAILED.
- Explain the recorded reason.
- Recommend relevant investigation steps.
- Do not recommend retry or reversal without sufficient evidence.

If Status is Pending:
- State that the payment is PENDING.
- Recommend checking the latest processing status and applicable SLA.
- Do not recommend retry or reversal without sufficient evidence.

Use only the supplied information.
Do not invent bank policies or payment-network rules.
Keep the response under 120 words.
"""

        with st.spinner("AI is analysing the payment..."):
            try:
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": "llama3.2:3b",
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=180
                )
                response.raise_for_status()
                result = response.json()["response"]

                st.write("Payment ID:", selected_payment["Payment ID"])
                st.write("Payment Rail:", selected_payment["Rail"])
                st.write("Transaction Status:", status)
                st.markdown(result)

            except requests.RequestException as error:
                st.error(f"Could not connect to Ollama: {error}")
