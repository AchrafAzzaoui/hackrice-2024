from flask import Blueprint, jsonify, request

main_routes = Blueprint('main', __name__)

@main_routes.route('/api/submitPDF', methods=['POST'])
def submit_pdf():
    data = request.json
    if 'filepath' not in data:
        return jsonify({"error": "No filepath provided"}), 400
   
    filepath = data['filepath']
    # Here you would typically process the PDF file
    # For this example, we'll just print the filepath
    print(f"Processing PDF at: {filepath}")
   
    return jsonify({"message": "Filepath received and processing initiated", "filepath": filepath}), 200

    