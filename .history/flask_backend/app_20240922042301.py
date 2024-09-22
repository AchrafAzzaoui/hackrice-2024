from flask import Flask, jsonify, request, make_response
import pdfextractor
from flask_socketio import SocketIO, emit
from LLM import knowledge_graph
from LLM import vector_store
from LLM import agents
import threading

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

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/submitPDF", methods=['POST', 'OPTIONS'])
def submit_PDF():

    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Content-Type'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, access-control-allow-origin, Access-Control-Allow-Origin'
        return response
    elif request.method == 'POST':
        # body = request.get_json()
        # filename = body.get('filename')
        # print(filename) 
        
        # combined_text = pdfextractor.run(filename)
        # print(combined_text)
        
        # return response
        try:
            body = request.get_json()
            if not body:
                return jsonify({"error": "No JSON data received"}), 400

            filename = body.get('filename')
            if not filename:
                return jsonify({"error": "No filename provided"}), 400
            print(f"Received filename: {filename}")

            topics = body.get('topics')
            print(topics)

            combined_text = pdfextractor.run(filename)
            print(f"Extracted text (first 100 characters): {combined_text[:100]}...")

            ordered_topics, split_texts = knowledge_graph.getKnowledgeGraph(topics, combined_text)
            print(ordered_topics)
            vector_embeddings = vector_store.getVectorStore(ordered_topics, split_texts)
            memory, question_chain, hint_chain, evaluation_chain, answer_chain = agents.getLangChains()

            # Start the learning session in a background thread
            threading.Thread(target=learning_session, args=(ordered_topics, vector_embeddings, memory, question_chain, hint_chain, evaluation_chain, answer_chain)).start()

            # Create a JSON response with the combined text
            response_data = jsonify({"text": combined_text})
            
            # Set the Content-Type header to application/json
            response_data.headers['Content-Type'] = 'application/json'
            
            # Copy over the CORS headers
            response_data.headers['Access-Control-Allow-Origin'] = '*'
            response_data.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response_data.headers['Content-Type'] = '*'
            response_data.headers['Access-Control-Allow-Headers'] = 'Content-Type, access-control-allow-origin, Access-Control-Allow-Origin'

            return response_data

        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return jsonify({"error": str(e)}), 500
        
def learning_session(topics, vector_embeddings, memory, question_chain, hint_chain, evaluation_chain, answer_chain):
    for current_topic in topics:
        retriever = vector_embeddings.as_retriever(
            search_kwargs={
                "k": 25,
                "pre_filter": {
                    "$and": [
                        {"topics": {"$in": [current_topic]}},
                        # Add other filters if needed
                    ]
                }
            }
        )

        relevant_docs = retriever.get_relevant_documents(current_topic)
        context = "\n".join([doc.page_content for doc in relevant_docs])

        memory.clear()

        socketio.emit('question', f"Explain {current_topic} to me.")
        user_explanation = socketio.call('user_input')

        memory.save_context({"topic": current_topic}, {"text": user_explanation})

        difficulty = 'easy'
        evaluation_feedback = "None"

        for question_num in range(1, 3):
            question = question_chain.run(
                topic=current_topic,
                context=context,
                chat_history=memory.load_memory_variables({})["chat_history"],
                evaluation_feedback=evaluation_feedback,
                difficulty=difficulty
            ).strip()

            socketio.emit('question', question)
            user_answer = socketio.call('user_input')

            memory.save_context({"topic": current_topic}, {"text": question})
            memory.save_context({"topic": current_topic}, {"text": user_answer})

            evaluation = evaluation_chain.run(
                topic=current_topic,
                question=question,
                user_answer=user_answer,
                context=context
            ).strip()

            socketio.emit('feedback', evaluation)

            evaluation_feedback = evaluation

            if 'Incorrect' in evaluation or 'Partially Correct' in evaluation:
                socketio.emit('choice', "Would you like to try again with a hint, or see the correct answer?")
                choice = socketio.call('user_input')

                if choice == '1':
                    hint = hint_chain.run(evaluation=evaluation).strip()
                    socketio.emit('hint', hint)
                    user_answer_2 = socketio.call('user_input')

                    memory.save_context({"topic": current_topic}, {"text": user_answer_2})

                    evaluation_2 = evaluation_chain.run(
                        topic=current_topic,
                        question=question,
                        user_answer=user_answer_2,
                        context=context
                    ).strip()

                    socketio.emit('feedback', evaluation_2)

                    difficulty = 'harder' if 'Correct' in evaluation_2 else 'easier'
                    evaluation_feedback = evaluation_2
                else:
                    correct_answer = answer_chain.run(
                        topic=current_topic,
                        question=question,
                        context=context
                    ).strip()
                    socketio.emit('correct_answer', correct_answer)

                    difficulty = 'easier'
            else:
                difficulty = 'harder' if 'Correct' in evaluation else 'same'

        socketio.emit('topic_finished', f"Finished topic: {current_topic}")

@socketio.on('user_input')
def handle_user_input(data):
    return data


if __name__ == '__main__':
    app.run(port=5000)