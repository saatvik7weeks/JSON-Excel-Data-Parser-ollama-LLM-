import streamlit as st
import xml.etree.ElementTree as ET
import requests

OLLAMA_API_URL = "http://localhost:11434/api/generate"

# Parse test results from XML

def parse_test_results(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        total_tests = int(root.get("tests", 0))
        total_failures = int(root.get("failures", 0))

        results = "Test Case Details:\n"
        for testcase in root.findall("testcase"):
            name = testcase.get("name", "N/A")
            classname = testcase.get("classname", "N/A")
            time = testcase.get("time", "N/A")
            failure = testcase.find("failure")
            status = "FAILED" if failure is not None else "PASSED"
            results += f'<testcase name="{name}"\n          classname="{classname}"\n          time="{time}"\n          status="{status}" />\n'

        results += f"\nSummary:\nTotal Test Cases: {total_tests}\nFailed Test Cases: {total_failures}\nPassed Test Cases: {total_tests - total_failures}\n"

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
            "model": "tinyllama:1.1b",
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
st.title("Json Ollama parser")

uploaded_file = st.file_uploader("Upload XML Test Results", type="xml")

if uploaded_file is not None:
    results = parse_test_results(uploaded_file)
    st.text_area("Parsed Test Results:", results, height=300)
    if st.button("Push to Ollama"):
        push_to_ollama(results)

st.subheader("Ask Questions About the Test Results:")
question = st.text_input("Enter your question:")
if st.button("Query Ollama"):
    if question:
        answer = query_ollama(question)
        st.text_area("Answer:", answer, height=200)
