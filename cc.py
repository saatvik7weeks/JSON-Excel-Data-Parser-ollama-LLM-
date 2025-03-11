import streamlit as st
import xml.etree.ElementTree as ET
import requests
import plotly.express as px
import pandas as pd

OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Parse test results from XML
def parse_test_results(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        total_tests = int(root.get("tests", 0))
        total_failures = int(root.get("failures", 0))

        test_data = []
        for testcase in root.findall("testcase"):
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

# Graph customization
def plot_graphs(results, num_tests, graph_type):
    test_cases = pd.DataFrame(results["Test Cases"])[:num_tests]

    st.subheader("Test Case Summary")
    st.json({
        "Total Tests": results["Total Tests"],
        "Failed Tests": results["Failed Tests"],
        "Passed Tests": results["Passed Tests"]
    })

    if graph_type == "Bar Graph":
        fig = px.bar(test_cases, x="name", y="time", color="status", title="Test Execution Time by Test Case")
    elif graph_type == "Pie Chart":
        counts = test_cases["status"].value_counts()
        fig = px.pie(names=counts.index, values=counts.values, title="Test Case Summary")
    elif graph_type == "Line Graph":
        fig = px.line(test_cases, x="name", y="time", color="status", title="Execution Time Trends")
    
    st.plotly_chart(fig)

# Push to Ollama
def push_to_ollama(data):
    try:
        payload = {
            "model": "llama3",
            "prompt": f"Index the following selected test data for semantic search:\n{data}",
            "stream": False
        }
        response = requests.post(OLLAMA_API_URL, json=payload)
        if response.status_code == 200:
            st.success("Selected test data pushed to Ollama successfully!")
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

# Streamlit UI
st.title("JSON parser")

uploaded_file = st.file_uploader("Upload XML Test Results", type="xml")

if uploaded_file is not None:
    results = parse_test_results(uploaded_file)
    
    # Number of test cases selection
    st.subheader("Select Number of Test Cases to Display:")
    num_tests = st.slider("Number of test cases:", 0, 1000, 100)

    # Graph customization
    st.subheader("Choose Graph Type:")
    graph_type = st.selectbox("Select graph type:", ["Bar Graph", "Pie Chart", "Line Graph"])

    # Plot graphs based on selection
    plot_graphs(results, num_tests, graph_type)

    # Push selected data to Ollama
    if st.button("Push Test Data to Ollama"):
        selected_data = results["Test Cases"][:num_tests]
        push_to_ollama(selected_data)

st.subheader("Ask Ollama About Test Results:")
question = st.text_input("Enter your question:")
if st.button("Query Ollama"):
    if question:
        answer = query_ollama(question)
        st.text_area("Answer:", answer, height=200)