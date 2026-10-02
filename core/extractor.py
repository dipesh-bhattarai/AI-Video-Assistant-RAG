#Actionableitems , decisions , question

from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
import os

def get_llm():
    return ChatGroq(
        model = "openai/gpt-oss-120b",
        groq_api_key = os.getenv("GROQ_API_KEY"),
        temperature=0.2
        )
def build_chain(system_prompt : str):
    llm = get_llm()
    return (
        RunnablePassthrough() | RunnableLambda(lambda x : {"text" : x}) | ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                ("human", "{text}")
            ]
        ) | llm | StrOutputParser()
    )

def extract_action_items(transcript : str) -> str:
    chain = build_chain(
        "You are an expert meeting analyst. xFrom the meeting transcript, "
        "extract all action items. For each provide:\n"
        "- Task description\n"
        "- Owner (who is responsible)\n"
        "- Deadline (if mentioned, else write 'Not specified' )\n\n"
        "Format as a numbered list. If none found say 'No action items found.'"
    )

    
