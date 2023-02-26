# PdfGPT

You want to review a topic, use this to read pdfs and get a summary of the topic. You can ask questions about the topic and get answers. You can also ask questions about the pdfs and get answers.

## Running Locally

1. Clone the repository

```bash
git clone https://github.com/davila7/file-gpt
cd file-gpt
```
2. Install dependencies

These dependencies are required to install with the requirements.txt file:

* openai
* pypdf
* scikit-learn
* numpy
* tiktoken
* docx2txt
* langchain
* pydantic
* typing
* faiss-cpu
* streamlit_chat

```bash
pip install -r requirements.txt
```
3. Run the Streamlit server

```bash
streamlit run app.py
```
