#get answers
import streamlit as st
import pandas as pd
import ollama
import altair as alt

st.title('Dynamic Excel Analysis with Ollama')


uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx", "xls"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)
    st.write("### Uploaded Data Preview")
    st.dataframe(df)

    
    if 'Status' in df.columns:
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']

        chart = alt.Chart(status_counts).mark_bar().encode(
            x='Status',
            y='Count',
            color='Status'
        ).properties(title='Test Results: Passed vs. Failed')
        
        st.altair_chart(chart, use_container_width=True)

      
        ollama_client = ollama.Client(host='http://localhost:11434')
        query = st.text_input("Ask Ollama about the data:")
        if st.button("Get Answer") and query:
            model = 'llama3:latest'
            response = ollama_client.chat(
                model=model,
                messages=[{"role": "user", "content": query + "\nData:\n" + df.to_string()}]
            )
            st.write("### Ollama's Response")
            st.text_area("Answer:", response['message']['content'], height=200)
    else:
        st.error("The uploaded file must have a 'Status' column with 'Passed' and 'Failed' values.")
