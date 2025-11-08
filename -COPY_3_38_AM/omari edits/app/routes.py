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
from flask import Flask, request, render_template
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

app = Flask(__name__)

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

# --- Flask routes ---
@app.route("/ask", methods=["GET", "POST"])
def ask():
    # Get some example questions from the dataset for the dropdown
    example_questions = [
        reasonmed["train"][i]["question"] 
        for i in range(min(5, len(reasonmed["train"])))
    ]
    
    if request.method == "POST":
        # Get question from form
        question = request.form.get("question", "").strip()
        if not question:
            # Try to get from example questions dropdown
            question = request.form.get("example_question", "").strip()
        
        if not question:
            question = example_question  # final fallback
            
        # Generate answer
        try:
            answer = ask_question(question)
            # Check if this is an AJAX request
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return render_template("answer.html", question=question, answer=answer)
            return render_template("answer.html", question=question, answer=answer)
        except Exception as e:
            # Handle errors appropriately
            error_msg = "Sorry, there was an error processing your question. Please try again."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return error_msg, 500
            return render_template("ask.html", error=error_msg, example_questions=example_questions)
    
    # GET request - show the form
    return render_template("ask.html", example_questions=example_questions)

@app.route("/")
def index():
    return render_template("index.html")

# --- Error handlers ---
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

# --- Run app ---
if __name__ == "__main__":
    app.run(debug=True)
