import streamlit as st
import pandas as pd
import os
import openai
import io

# --- Page Config ---
st.set_page_config(page_title="AI Competitive Intelligence 2022-2025", layout="wide")

# --- Header Section ---
st.title("📊 Strategic Competitive Report Generator")

col_header1, col_header2 = st.columns([2, 1])

with col_header1:
    st.markdown("### Report Parameters")
    # Updated Year Range for 2022-2025
    year_options = ["2022-2023", "2023-2024", "2024-2025", "Full Range (2022-2025)"]
    selected_years = st.selectbox("Select Report Fiscal Period:", year_options)

with col_header2:
    st.markdown("### API Configuration")
    api_key = st.text_input("Enter OpenAI API Key:", type="password")
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        openai.api_key = api_key

st.divider()

# --- Main UI: Inputs ---
st.subheader(f"Head-to-Head Comparison: {selected_years}")
col1, col2, col3 = st.columns(3)
with col1:
    comp_1 = st.text_input("Enter Company 1:", value="Apple")
with col2:
    comp_2 = st.text_input("Enter Company 2:", value="Google")
with col3:
    comp_3 = st.text_input("Enter Company 3:", value="Microsoft")

# --- Logic Processing ---
if st.button("Generate Strategy CSV"):
    if not api_key:
        st.error("Please enter an API Key in the header first.")
    else:
        with st.spinner(f"Analyzing {comp_1}, {comp_2}, and {comp_3} for {selected_years}..."):
            try:
                # Dynamic prompt injected with the user-selected year range
                prompt = f"""
                Act as a senior business analyst. Create a competitive report for {comp_1}, {comp_2}, and {comp_3} 
                specifically for the period {selected_years}.
                
                Format the output as a valid CSV with these columns:
                "Company Name", "Product Description", "Marketing Strategy", "Financial Summary"
                
                Data Requirements:
                1. Product Description: Detail key products and tech shifts during {selected_years}.
                2. Marketing Strategy: Describe brand messaging and competitive pivots in {selected_years}.
                3. Financial Summary: Provide revenue and profitability snapshots for the {selected_years} cycle.
                
                Return ONLY the CSV data.
                """

                client = openai.OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                st.write("AI Response Received. Processing CSV...")
                st.write(response.choices[0].message.content)
                csv_data = response.choices[0].message.content.strip().replace("```csv", "").replace("```", "").strip()

                # Convert to DataFrame
                df = pd.read_csv(io.StringIO(csv_data))

                # UI Results
                st.success(f"Report for {selected_years} ready.")
                st.dataframe(df, use_container_width=True)

                # Export
                csv_buffer = io.StringIO()
                df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label=f"📥 Download {selected_years} Report",
                    data=csv_buffer.getvalue(),
                    file_name=f"report_{selected_years.replace(' ', '_')}.csv",
                    mime="text/csv"
                )

            except Exception as e:
                st.error(f"Error: {e}")