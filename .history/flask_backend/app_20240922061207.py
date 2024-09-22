from flask import Flask, jsonify, request, make_response
import pdfextractor
from flask_socketio import SocketIO, emit
from LLM import knowledge_graph
from LLM import vector_store
from LLM import agents
import threading

app = Flask(__name__)

socketio = SocketIO(app, cors_allowed_origins="*")

global client

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
            user_id, session, vector_embeddings = vector_store.getVectorStore(ordered_topics, split_texts)
            memory, question_chain, hint_chain, evaluation_chain, answer_chain = agents.getLangChains()

           # Start the learning session in a background task
            socketio.start_background_task(learning_session, user_id, session, ordered_topics, vector_embeddings, memory, question_chain, hint_chain, evaluation_chain, answer_chain)

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
        
async def learning_session(user_id, session, topics, vector_embeddings, memory, question_chain, hint_chain, evaluation_chain, answer_chain):
    for current_topic in topics:
        retriever = vector_embeddings.as_retriever(
            search_kwargs={
                "k": 25,
                "pre_filter": {
                    "$and": [
                        {"topics": {"$in": [current_topic]}},
                        {"user_id": user_id},
                        {"session": session}
                    ]
                }
            }
        )

        relevant_docs = await retriever.aget_relevant_documents(current_topic)
        context = "\n".join([doc.page_content for doc in relevant_docs])

        memory.clear()

        await socketio.emit('question', f"Explain {current_topic} to me.")
        user_explanation = await socketio.call('user_input', timeout=360)
        print(user_explanation)

        memory.save_context({"topic": current_topic}, {"text": user_explanation})

        difficulty = 'easy'
        evaluation_feedback = "None"

        for question_num in range(1, 3):
            question = await question_chain.arun(
                topic=current_topic,
                context=context,
                chat_history=memory.load_memory_variables({})["chat_history"],
                evaluation_feedback=evaluation_feedback,
                difficulty=difficulty
            )
            question = question.strip()

            await socketio.emit('question', question)
            user_answer = await socketio.call('user_input', timeout=360)

            memory.save_context({"topic": current_topic}, {"text": question})
            memory.save_context({"topic": current_topic}, {"text": user_answer})

            evaluation = await evaluation_chain.arun(
                topic=current_topic,
                question=question,
                user_answer=user_answer,
                context=context
            )
            evaluation = evaluation.strip()

            await socketio.emit('feedback', evaluation)

            evaluation_feedback = evaluation

            if 'Incorrect' in evaluation or 'Partially Correct' in evaluation:
                await socketio.emit('choice', "Would you like to try again with a hint, or see the correct answer?")
                choice = await socketio.call('user_input', timeout=360)

                if choice == '1':
                    hint = await hint_chain.arun(evaluation=evaluation)
                    hint = hint.strip()
                    await socketio.emit('hint', hint)
                    user_answer_2 = await socketio.call('user_input', timeout=360)

                    memory.save_context({"topic": current_topic}, {"text": user_answer_2})

                    evaluation_2 = await evaluation_chain.arun(
                        topic=current_topic,
                        question=question,
                        user_answer=user_answer_2,
                        context=context
                    )
                    evaluation_2 = evaluation_2.strip()

                    await socketio.emit('feedback', evaluation_2)

                    difficulty = 'harder' if 'Correct' in evaluation_2 else 'easier'
                    evaluation_feedback = evaluation_2
                else:
                    correct_answer = await answer_chain.arun(
                        topic=current_topic,
                        question=question,
                        context=context
                    )
                    correct_answer = correct_answer.strip()
                    await socketio.emit('correct_answer', correct_answer)

                    difficulty = 'easier'
            else:
                difficulty = 'harder' if 'Correct' in evaluation else 'same'

        await socketio.emit('topic_finished', f"Finished topic: {current_topic}")

@socketio.on('user_input')
def handle_user_input(data):
    print('inside handle')
    print(data)
    return data

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")



if __name__ == '__main__':
    app.run(port=5000)