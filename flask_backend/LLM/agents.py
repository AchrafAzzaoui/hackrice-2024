import os
import pymongo
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain.memory import ConversationBufferMemory
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from collections import defaultdict

from dotenv import load_dotenv

load_dotenv("C:\\Users\\achra\\Downloads\\hackrice-2024\\.env")

def getLangChains():
    llm = ChatOpenAI(model_name="gpt-4o", temperature=0.7)
    memory = ConversationBufferMemory(memory_key="chat_history", input_key="topic", output_key="text")

    question_prompt_template = PromptTemplate(
        input_variables=["topic", "context", "chat_history", "evaluation_feedback", "difficulty"],
        template="""
    You are an AI tutor helping a student understand the topic "{topic}". You are supposed to act like you are learning from the student,
    since teaching is the best way of reinforcing knowledge. IF THE NOTES ARE ABOUT A SPECIFIC PROGRAMMING LANGUAGE, DON'T ASK ABOUT OTHERS.
    FOR EXAMPLE, IF ALL THE NOTES ARE ABOUT JAVA ARRAYS, DON'T MENTION PYTHON ARRAYS UNLESS THEY SAID SOMETHING THAT IS RELEVANT TO ANOTHER LANGUAGE BUT DOESN'T WORK IN
    THE LANGUAGE IN THE NOTES.

    Based on the following context from their notes:
    {context}

    Considering the conversation so far:
    {chat_history}

    Here is the evaluation feedback from the previous question:
    {evaluation_feedback}

    Ask the student one question that assesses their understanding of a {difficulty} concept in this topic, or mention a common misconception and ask them to correct it.

    Your question should be clear and concise.
    """
    )

    evaluation_prompt_template = PromptTemplate(
        input_variables=["topic", "question", "user_answer", "context"],
        template="""
    You are an AI tutor evaluating the student's answer.

    Topic: {topic}
    Question: {question}
    Student's Answer: {user_answer}

    Based on the context:
    {context}

    Evaluate the correctness of the student's answer. Provide the following information in JSON format:
    1. Degree of correctness (Correct, Partially Correct, Incorrect).
    2. Brief explanation of the correctness.
    3. Suggestion for the next question difficulty.
    4. Provide a clear hint or guidance for the student to improve their answer.
    """
    )

    hint_prompt_template = PromptTemplate(
        input_variables=["evaluation"],
        template="""
    You are an AI that specializes in generating clear and concise hints for students. Based on the evaluation below, extract only the hint that will guide the student toward the correct answer.

    Evaluation:
    {evaluation}

    Provide only the hint.
    """
    )


    answer_prompt_template = PromptTemplate(
        input_variables=["topic", "question", "context"],
        template="""
    You are an AI tutor.

    Topic: {topic}
    Question: {question}

    Based on the context:
    {context}

    Provide the correct answer to the question.

    Your answer should be clear and concise.
    """
    )

    question_chain = LLMChain(llm=llm, prompt=question_prompt_template, memory=memory)
    hint_chain = LLMChain(llm=llm, prompt=hint_prompt_template)
    evaluation_chain = LLMChain(llm=llm, prompt=evaluation_prompt_template)
    answer_chain = LLMChain(llm=llm, prompt=answer_prompt_template)

    return (memory, question_chain, hint_chain, evaluation_chain, answer_chain)

