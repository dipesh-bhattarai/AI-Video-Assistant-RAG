from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

import os

def get_llm():
    return ChatGroq(
        model = "openai/gpt-oss-120b",
        groq_api_key = os.getenv("GROQ_API_KEY"),
        temperature=0.3
        )

def split_transcript(transcript : str) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 3000,
        chunk_overlap = 200,

    )

    return splitter.split_text(transcript)

def summarize(transcript : str)-> str:
    