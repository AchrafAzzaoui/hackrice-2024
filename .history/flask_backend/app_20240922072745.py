from flask import Flask, jsonify, request, make_response
import pdfextractor
from LLM import knowledge_graph, vector_store, agents
import threading

app = Flask(__name__)

# Global variables to store session data
user_id = None
session = None
vector_embeddings = None
memory = None
question_chain = None
hint_chain = None
evaluation_chain = None
answer_chain = None


@app.route("/submit-explanation", methods=['POST', 'OPTIONS'])
def submit_explanation():
    global memory, question_chain, evaluation_chain

    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Content-Type'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, access-control-allow-origin, Access-Control-Allow-Origin'
        return response
    elif request.method == 'POST':
        data = request.json
        topic = data['topic']
        explanation = data['explanation']

        memory.save_context({"topic": topic}, {"text": explanation})

        retriever = vector_store.as_retriever(
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

    relevant_docs = retriever.get_relevant_documents(current_topic)
    context = "\n".join([doc.page_content for doc in relevant_docs])

        question = question_chain.run(
            topic=topic,
            context=vector_embeddings.get(topic, ""),
            chat_history=memory.load_memory_variables({})["chat_history"],
            evaluation_feedback="None",
            difficulty='easy'
        ).strip()

        response_data = jsonify({
            "feedback": "Great explanation! Let's test your understanding.",
            "question": question
        })

        # Set the Content-Type header to application/json
        response_data.headers['Content-Type'] = 'application/json'
        
        # Copy over the CORS headers
        response_data.headers['Access-Control-Allow-Origin'] = '*'
        response_data.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response_data.headers['Content-Type'] = '*'
        response_data.headers['Access-Control-Allow-Headers'] = 'Content-Type, access-control-allow-origin, Access-Control-Allow-Origin'

        return response_data

@app.route("/submit-answer", methods=['POST', 'OPTIONS'])
def submit_answer():
    global memory, evaluation_chain, hint_chain, answer_chain

    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Content-Type'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, access-control-allow-origin, Access-Control-Allow-Origin'
        return response
    elif request.method == 'POST':
        data = request.json
        topic = data['topic']
        question = data['question']
        answer = data['answer']

        memory.save_context({"topic": topic}, {"text": question})
        memory.save_context({"topic": topic}, {"text": answer})

        evaluation = evaluation_chain.run(
            topic=topic,
            question=question,
            user_answer=answer,
            context=vector_embeddings.get(topic, "")
        ).strip()

        if 'Incorrect' in evaluation or 'Partially Correct' in evaluation:
            hint = hint_chain.run(evaluation=evaluation).strip()
            next_question = question  # Ask the same question again
        else:
            hint = None
            next_question = None  # Move to the next topic

        response_data = jsonify({
            "feedback": evaluation,
            "hint": hint,
            "nextQuestion": next_question
        })

        # Set the Content-Type header to application/json
        response_data.headers['Content-Type'] = 'application/json'
        
        # Copy over the CORS headers
        response_data.headers['Access-Control-Allow-Origin'] = '*'
        response_data.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response_data.headers['Content-Type'] = '*'
        response_data.headers['Access-Control-Allow-Headers'] = 'Content-Type, access-control-allow-origin, Access-Control-Allow-Origin'

        return response_data


@app.route("/submitPDF", methods=['POST', 'OPTIONS'])
def submit_PDF():

    global user_id, session, vector_embeddings, memory, question_chain, hint_chain, evaluation_chain, answer_chain

    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Content-Type'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, access-control-allow-origin, Access-Control-Allow-Origin'
        return response
    elif request.method == 'POST':
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
        



if __name__ == '__main__':
    app.run(port=5000)