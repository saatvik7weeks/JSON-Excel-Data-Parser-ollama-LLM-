import streamlit as st
import xml.etree.ElementTree as ET
import requests
import pandas as pd
import plotly.express as px

OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Parse test results from XML
def parse_test_results(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        total_tests = int(root.get("tests", 0))
        total_failures = int(root.get("failures", 0))

        test_data = []
        for testcase in root.findall("testcase")[:20]:
            name = testcase.get("name", "N/A")
            classname = testcase.get("classname", "N/A")
            time = float(testcase.get("time", 0))
            failure = testcase.find("failure")
            status = "FAILED" if failure is not None else "PASSED"
            test_data.append({"name": name, "classname": classname, "time": time, "status": status})

        results = {
            "Total Tests": total_tests,
            "Failed Tests": total_failures,
            "Passed Tests": total_tests - total_failures,
            "Test Cases": test_data
        }

        return results

    except ET.ParseError as e:
        st.error(f"Error parsing XML: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")

# Push data to Ollama
def push_to_ollama(data):
    try:
        payload = {
            "model": "llama3",
            "prompt": f"Index the following test results for semantic search:\n{data}",
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        if response.status_code == 200:
            st.success("Data pushed to Ollama successfully!")
        else:
            st.error(f"Failed to push data to Ollama: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {e}")

# Query Ollama
def query_ollama(question):
    try:
        payload = {
            "model": "llama3",
            "prompt": f"Based on the indexed test results, answer this question: {question}",
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        if response.status_code == 200:
            return response.json().get("response", "No response received.")
        else:
            st.error(f"Failed to query Ollama: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {e}")

# Visualization using Plotly
def plot_graphs(results):
    test_cases = pd.DataFrame(results["Test Cases"])
    
    st.subheader("Test Case Summary")
    st.json({
        "Total Tests": results["Total Tests"],
        "Failed Tests": results["Failed Tests"],
        "Passed Tests": results["Passed Tests"]
    })

    # Test execution time bar chart
    fig = px.bar(test_cases, x="name", y="time", color="status",
                 title="Test Execution Time by Test Case")
    st.plotly_chart(fig)

    
    test_counts = pd.DataFrame({
        "Status": ["Passed", "Failed"],
        "Count": [results["Passed Tests"], results["Failed Tests"]]
    })

    fig = px.pie(test_counts, names="Status", values="Count",
                 title="Test Case Summary")
    st.plotly_chart(fig)

# Streamlit UI
st.title("JSON Ollama Parser with Graphs")

uploaded_file = st.file_uploader("Upload XML Test Results", type="xml")

if uploaded_file is not None:
    results = parse_test_results(uploaded_file)
    plot_graphs(results)
    if st.button("Push to Ollama"):
        push_to_ollama(results)

st.subheader("Ask Questions About the Test Results:")
question = st.text_input("Enter your question:")
if st.button("Query Ollama"):
    if question:
        answer = query_ollama(question)
        st.text_area("Answer:", answer, height=200)
