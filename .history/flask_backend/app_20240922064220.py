from flask import Flask, jsonify, request, make_response
import pdfextractor
from LLM import knowledge_graph
from LLM import vector_store
from LLM import agents
import threading

app = Flask(__name__)

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