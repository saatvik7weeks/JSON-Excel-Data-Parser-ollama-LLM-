import streamlit as st
import pandas as pd
import ollama
import plotly.express as px


ollama_client = ollama.Client()


st.title('Excel File Analyzer with Ollama')


uploaded_file = st.file_uploader("Upload an Excel file", type=['xlsx'])


data_str = ""

if uploaded_file:
  
    df = pd.read_excel(uploaded_file)
    st.write("Uploaded Data:")
    st.dataframe(df)

   
    if 'Status' in df.columns:
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        bar_chart = px.bar(status_counts, x='Status', y='Count', title='Pass/Fail Distribution')
        st.plotly_chart(bar_chart)
    
   
    if all(col in df.columns for col in ['S_No', 'Expected_Status', 'Actual_Status', 'URL']):
        line_chart = px.line(df, x='S_No', y=['Expected_Status', 'Actual_Status'], hover_data=['URL'], title='Line Chart of Test Results')
        st.plotly_chart(line_chart)

   
    ollama_data = df.to_dict(orient='records')
    data_str = "\n".join([str(record) for record in ollama_data])

   
    ollama_client.chat(
        model='llama3:latest',
        messages=[{"role": "user", "content": "Here is the test data:\n" + data_str}]
    )
    st.success("Data has been sent to Ollama and is ready for querying!")

   
    st.session_state['data_str'] = data_str


query = st.text_input("Ask something about your data:")
if query and 'data_str' in st.session_state:
    response = ollama_client.chat(
        model='llama3:latest',
        messages=[
            {"role": "user", "content": "Here is the test data:\n" + st.session_state['data_str']},
            {"role": "user", "content": query}
        ]
    )
    st.write("Ollama's Response:")
    st.text(response['message']['content'])
