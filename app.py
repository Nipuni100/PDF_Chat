import streamlit as st
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.memory  import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from htmlTemplates import css, bot_template, user_template

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# load_dotenv()

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")






def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = CharacterTextSplitter(
        separator='\n',
        chunk_size=1000,
        chunk_overlap=200, #To protect the meaning of the sentences
        length_function=len
    )

    chunks = text_splitter.split_text(text)  # return a list of text chunks
    return chunks

def get_vectorstore(text_chunks):
    
    embeddings = GoogleGenerativeAIEmbeddings(model="model/embedding-001")
    vectorstore = FAISS.from_texts(texts=text_chunks,embedding=embeddings)

    return vectorstore

def get_conversation_chain(model , vectorstore):
    llm=model
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    conversation_chain =ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=vectorstore.as_retriever(),
        memory=memory
    )
    return conversation_chain  #take the history and return the next word

def handle_userinput(user_question):
    response=st.session_state.conversation({"question":user_question}) #contains all configurations
    st.write(response)

def main():


    model = ChatGoogleGenerativeAI(model="gemini-pro" , google_api_key = GOOGLE_API_KEY)
    




    st.set_page_config(page_title="Chat with multiple PDFs", page_icon=":books:")
    st.write(css,unsafe_allow_html=True)

    if "conversation" not in st.session_state:
        st.session_state.conversation = None

    st.header("Chat with multiple PDFs :books:")
    user_question=st.text_input("Ask a question about your documents:")

    if user_question:
        handle_userinput(user_question)

    st.write(user_template.replace("{{MSG}}","Hello robot"),unsafe_allow_html=True)
    st.write(bot_template.replace("{{MSG}}","Hello human"),unsafe_allow_html=True)

    with st.sidebar:
        st.subheader("Your documents")
        pdf_docs = st.file_uploader("Upload your PDFs here and click on 'Process'",accept_multiple_files=True)
        if st.button("Process"):
            with st.spinner("Processing"): #Program is not frozen , but still running
                # get pdf text
                raw_text = get_pdf_text(pdf_docs)
                # st.write(raw_text)

                # get text chunks
                text_chunks= get_text_chunks(raw_text)
                # st.write(text_chunks)

                # create vector store
                vectorstore = get_vectorstore(text_chunks)

                # create conversation chain
                # st.session_state.conversation = get_conversation_chain(vectorstore)
                st.session_state.conversation = get_conversation_chain(model, vectorstore)


if __name__ == '__main__' :
    main()