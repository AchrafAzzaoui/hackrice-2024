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

def getVectorStore(topics: list, split_texts: str):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

    documents = []
    user_id = "Wyatt Bellinger"
    session = 609

    for text_chunk in split_texts:
        embedding = embeddings.embed_query(text_chunk)
        document = {
            'embedding': embedding,
            'text': text_chunk,
            'topics': topics,
            'user_id': user_id,
            'session': session
        }
        documents.append(document)

    client = pymongo.MongoClient("mongodb+srv://aa270:Achraf2004**@hackrice-trial-db.v9ye8.mongodb.net/?retryWrites=true&w=majority&appName=Hackrice-Trial-DB")
    db = client["test"]
    collection = db["pdf_embeddings"]
    # collection.delete_many({})

    vector_store = MongoDBAtlasVectorSearch(collection=collection, embedding=embeddings, index_name='pdf_embeddings')

    texts = [doc['text'] for doc in documents]
    metadatas = [{'topics': doc['topics'], 'user_id': doc['user_id'], 'session': doc['session']} for doc in documents]
    embeddings_list = [doc['embedding'] for doc in documents]

    vector_store.add_texts(texts=texts, metadatas=metadatas, embeddings=embeddings_list)

    print(f"Added {len(documents)} documents to the vector store.")

    return vector_store
