import os

import streamlit as st
from langchain import Cohere, OpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from openai.error import OpenAIError
from streamlit_chat import message

from utils import (
    embed_docs,
    get_answer,
    get_sources,
    parse_csv,
    parse_docx,
    parse_pdf,
    parse_txt,
    search_docs,
    text_to_docs,
    wrap_text_in_html,
)


def clear_submit():
    st.session_state["submit"] = False


def set_openai_api_key(api_key: str):
    st.session_state["OPENAI_API_KEY"] = api_key


if "summary" not in st.session_state:
    st.session_state["summary"] = ""

st.markdown("<h1>Pdf GPT 🤖<small></h1>", unsafe_allow_html=True)

# Sidebar
index = None
doc = None
with st.sidebar:
    st.write("To obtain an OpenAI API Key follow this link: https://openai.com/api/")
    user_secret = st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="Paste your OpenAI API key here (sk-...)",
        help="You can get your API key from https://platform.openai.com/account/api-keys.",
        value=st.session_state.get("OPENAI_API_KEY", ""),
    )
    if user_secret:
        set_openai_api_key(user_secret)

    st.write("<h3>Choose a file(s) to upload:</h3>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "Upload a pdf, docx, or txt file",
        type=["pdf", "docx", "txt", "csv"],
        help="Scanned documents are not supported yet!",
        accept_multiple_files=True,
        on_change=clear_submit,
    )

    if len(uploaded_files) > 0:
        all_docs = {}
        for uploaded_file in uploaded_files:
            if uploaded_file.name.endswith(".pdf"):
                doc = parse_pdf(uploaded_file)
            elif uploaded_file.name.endswith(".docx"):
                doc = parse_docx(uploaded_file)
            elif uploaded_file.name.endswith(".csv"):
                doc = parse_csv(uploaded_file)
            elif uploaded_file.name.endswith(".txt"):
                doc = parse_txt(uploaded_file)
            else:
                st.error("File type not supported")
                doc = None
            if doc:
                file_name_ = os.path.splitext(uploaded_file.name)[0]
                i = 1
                file_name = file_name_
                while file_name in all_docs:
                    file_name = file_name_ + "_{i}"
                    i += 1
                all_docs[file_name] = doc
        text = text_to_docs(all_docs)
        llm = OpenAI(
            temperature=0,
            max_tokens=512,
            openai_api_key=st.session_state.get("OPENAI_API_KEY"),
        )
        summary_chain = load_summarize_chain(llm, chain_type="map_reduce")
        st.session_state["summary"] = summary_chain.run(text)
        try:
            with st.spinner("Indexing document... This may take a while⏳"):
                index = embed_docs(text)
                st.session_state["api_key_configured"] = True
        except OpenAIError as e:
            st.error(e._message)


if "generated" not in st.session_state:
    st.session_state["generated"] = []

if "history" not in st.session_state:
    st.session_state["history"] = []

if "past" not in st.session_state:
    st.session_state["past"] = []


st.write(st.session_state["summary"])


def get_text():
    if user_secret:
        st.header("Ask me something about the document:")
        input_text = st.text_area("You:", on_change=clear_submit)
        return input_text


user_input = get_text()

button = st.button("Submit")
if button or st.session_state.get("submit"):
    tab1, tab2 = st.tabs(["Chat", "Sources"])
    if not user_input:
        st.error("Please enter a question!")
    else:
        st.session_state["submit"] = True
        sources = search_docs(index, user_input)
        try:
            if len(st.session_state.history) > 0:
                history = "\n".join(st.session_state.history)
                history = Document(page_content=history)
                history.metadata["source"] = "History"
                sources.append(history)
            answer = get_answer(sources, user_input)
            sources = get_sources(answer, sources)
            st.session_state.past.append(user_input)
            st.session_state.generated.append(answer["output_text"])
            st.session_state.history.append(answer["output_text"].split("SOURCES: ")[0])
        except OpenAIError as e:
            st.error(e._message)
        if st.session_state["generated"]:
            with tab1:
                for i in range(len(st.session_state["generated"]) - 1, -1, -1):
                    with st.container():
                        st.markdown(
                            f"<div class='bot'>🤖: {st.session_state['generated'][i]}</div>",
                            unsafe_allow_html=True,
                        )
                    st.markdown("\n\n")
                    with st.container():
                        st.markdown(
                            f"<div class='user'>🤓: {st.session_state['past'][i]}</div>",
                            unsafe_allow_html=True,
                        )
            with tab2:
                if sources:
                    for source in sources:
                        with st.container():
                            st.markdown(f"### {source.metadata['source']}")
                            st.markdown(
                                f"<div class='bot'>{wrap_text_in_html(source.page_content)}</div>",
                                unsafe_allow_html=True,
                            )
                else:
                    st.write("No sources found for this question.")


# Define CSS styles for chatbot1 and chatbot2
st.markdown(
    """
    <style>
    .user {
        background-color: #E0E0E0;
        padding: 5px;
        border-radius: 5px;
        text-align: right;
    }
    .bot {
        background-color: #FAFAFA;
        padding: 5px;
        border-radius: 5px;
        text-align: left;
    }
    </style>
""",
    unsafe_allow_html=True,
)
