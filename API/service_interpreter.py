import flask
from flask import Flask, request, jsonify
from INTERPRETER.mainV2 import main_api
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/", methods=["GET"])
def home():
    return "Bem-vindo à API de Detecção de Smells!"

@app.route("/api/process", methods=["POST"])
def process():
    data = request.json
    smelldsl_content = data.get("smelldsl")
    limites_content = data.get("limites")
    dados_content = data.get("dados")

    if not smelldsl_content or not limites_content or not dados_content:
        return jsonify({"error": "Conteúdo ausente."}), 400

    logs = main_api(smelldsl_content, limites_content, dados_content)
    return jsonify(logs)

if __name__ == "__main__":
    app.run(debug=True)
