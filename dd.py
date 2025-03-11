import streamlit as st
import xml.etree.ElementTree as ET
import requests
import plotly.express as px
import pandas as pd

# Gemini API setup
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateText"
API_KEY = "AIzaSyAsoKOKjoIbdoePvEY53fo_z6M3O6yPors"






# Parse test results from XML
def parse_test_results(xml_file, num_testcases=1000):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        total_tests = int(root.get("tests", 0))
        total_failures = int(root.get("failures", 0))

        test_data = []
        for testcase in root.findall("testcase")[:num_testcases]:
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

# Push data and graph summaries to Gemini
def push_to_gemini(data, graph_summary):
    try:
        payload = {
            "contents": [{"parts": [{"text": f"Test Results:\n{data}\nGraph Summary:\n{graph_summary}"}]}]
        }
        url = f"{GEMINI_API_URL}?key={API_KEY}"
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.success("Data and graph summaries pushed to Gemini successfully!")
        else:
            st.error(f"Failed to push data to Gemini: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {e}")

# Query Gemini
def query_gemini(question):
    try:
        payload = {
            "contents": [{"parts": [{"text": question}]}]
        }
        url = f"{GEMINI_API_URL}?key={API_KEY}"
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "No response received.")
        else:
            st.error(f"Failed to query Gemini: {response.text}")
    except requests.exceptions.RequestException as e:
        st.error(f"Request error: {e}")

# Visualization
def plot_graphs(results):
    test_cases = pd.DataFrame(results["Test Cases"])

    st.subheader("Test Case Summary")
    st.json({
        "Total Tests": results["Total Tests"],
        "Failed Tests": results["Failed Tests"],
        "Passed Tests": results["Passed Tests"]
    })

    # Bar graph
    fig = px.bar(test_cases, x="name", y="time", color="status", title="Test Execution Time by Test Case")
    st.plotly_chart(fig)

    # Pie chart
    fig = px.pie(names=["Passed", "Failed"], values=[results["Passed Tests"], results["Failed Tests"]], title="Test Case Summary")
    st.plotly_chart(fig)

# Streamlit UI
st.title("Gemini-Powered Test Result Analyzer")

uploaded_file = st.file_uploader("Upload XML Test Results", type="xml")
num_testcases = st.slider("Select number of test cases to display:", 0, 1000, 500)

if uploaded_file is not None:
    results = parse_test_results(uploaded_file, num_testcases)
    plot_graphs(results)

    graph_summary = f"Total Tests: {results['Total Tests']}, Passed: {results['Passed Tests']}, Failed: {results['Failed Tests']}"
    
    if st.button("Push to Gemini"):
        push_to_gemini(results, graph_summary)

st.subheader("Ask Questions About Test Results and Graphs:")
question = st.text_input("Enter your question:")
if st.button("Query Gemini"):
    if question:
        answer = query_gemini(question)
        st.text_area("Answer:", answer, height=200)
