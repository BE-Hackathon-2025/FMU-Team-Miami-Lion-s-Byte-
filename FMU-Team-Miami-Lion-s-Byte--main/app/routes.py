#
# #Original Code REMOVED ---------------------------
#  from flask import Flask, request, render_template
# from transformers import AutoModelForCausalLM, AutoTokenizer

# app = Flask(__name__)

# tokenizer = AutoTokenizer.from_pretrained("dousery/medical-reasoning-gpt-oss-20b")
# model = AutoModelForCausalLM.from_pretrained("dousery/medical-reasoning-gpt-oss-20b", load_in_4bit=True, device_map="auto")

# @app.route("/ask", methods=["GET","POST"])
# def ask():
#     if request.method == "POST":
#         question = request.form["question"]
#         inputs = tokenizer(question, return_tensors="pt").to(model.device)
#         outputs = model.generate(**inputs, max_new_tokens=512, temperature=0.7)
#         answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
#         return render_template("answer.html", question=question, answer=answer)
#     return render_template("ask.html")


# NEW Code ADDED ---------------------------

# --- Authentication routes ---
from flask import request, render_template
from . import app
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

# --- Load dataset (ReasonMed) ---
reasonmed = load_dataset("lingshu-medical-mllm/ReasonMed")
# Pick first example as fallback
example_question = reasonmed["train"][0]["question"]

# --- Load model ---
MODEL_ID = "dousery/medical-reasoning-gpt-oss-20b"
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    load_in_4bit=True,
    device_map="auto"
)


# --- Helper function for inference ---
def ask_question(question: str) -> str:
    inputs = tokenizer(question, return_tensors="pt").to(model.device)
    outputs = model.generate(
        **inputs,
        max_new_tokens=512,
        temperature=0.7,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id
    )
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return answer


# --- Flask route ---
@app.route('/ask', methods=['GET', 'POST'])
def ask():
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if not question:
            question = example_question  # fallback if empty input
        answer = ask_question(question)
        return render_template('answer.html', question=question, answer=answer)
    return render_template('ask.html', example_questions=reasonmed['train']['question'])


@app.route('/')
def index():
    return render_template('index.html')


# Fallback: serve index for unknown GET routes (useful for SPA or defaulting to index)
@app.errorhandler(404)
def page_not_found(e):
    # If the client wants HTML, render the main index so the UI can handle routing.
    # Otherwise return the original 404 error.
    try:
        from flask import request
        if request.method == 'GET' and request.accept_mimetypes.accept_html:
            return render_template('index.html'), 200
    except Exception:
        pass
    return e, 404
