import json
import os
import time
import streamlit as st
from google import genai

DB_FILE = "database.json"

# --- DATABASE FUNCTIONS ---
def load_data():
    if not os.path.exists(DB_FILE):
        return {"users": {}, "questions": []}
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"users": {}, "questions": []}

def save_data(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# --- APP CONFIGURATION & STYLING ---
st.set_page_config(page_title="AI-Powered Pro Quiz Application", page_icon="🤖", layout="centered")

st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        border: none;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #5a6fd6 0%, #684190 100%);
        color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize Session State
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None

# --- AUTHENTICATION & REGISTRATION ---
def auth_page():
    st.title("🎯 AI-Powered Pro Quiz Platform")
    st.info("💡 **Demo Accounts:** Admin -> `admin` / `adminpassword` | Student -> `student1` / `password123`")
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.subheader("Login to your account")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login Now"):
            data = load_data()
            if username in data.get("users", {}) and data["users"][username]["password"] == password:
                st.session_state.user = username
                st.session_state.role = data["users"][username]["role"]
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        st.subheader("Create a new Student account")
        new_user = st.text_input("Choose Username", key="reg_user")
        new_pass = st.text_input("Choose Password", type="password", key="reg_pass")
        if st.button("Register Account"):
            data = load_data()
            if not new_user or not new_pass:
                st.warning("Please fill in all fields.")
            elif "users" in data and new_user in data["users"]:
                st.error("Username already exists!")
            else:
                if "users" not in data:
                    data["users"] = {}
                data["users"][new_user] = {"password": new_pass, "role": "student"}
                save_data(data)
                st.success("Registration successful! Please switch to the Login tab.")

# --- ADMIN PANEL WITH AI QUESTION GENERATOR ---
def admin_panel():
    st.title("👨‍💼 Admin Dashboard (AI Enhanced)")
    st.write(f"Logged in as: **{st.session_state.user}**")
    
    data = load_data()
    menu = st.sidebar.selectbox("Admin Menu", ["Manage Questions", "Add Question", "🤖 AI Question Generator"])

    if menu == "Manage Questions":
        st.subheader("Existing Questions")
        questions = data.get("questions", [])
        if not questions:
            st.info("No questions available.")
        for idx, q in enumerate(questions):
            with st.expander(f"Q{idx+1}: {q['question']} (Cat: {q['category']})"):
                st.write(f"**Options:** {', '.join(q['options'])}")
                st.write(f"**Answer:** {q['answer']}")
                if st.button(f"Delete Question {q['id']}", key=f"del_{q['id']}"):
                    data["questions"] = [item for item in questions if item["id"] != q["id"]]
                    save_data(data)
                    st.success("Question deleted successfully!")
                    st.rerun()

    elif menu == "Add Question":
        st.subheader("Add a New Question manually")
        cat = st.text_input("Category (e.g., Python, Java, DSA)")
        q_text = st.text_area("Question Text")
        opt1 = st.text_input("Option 1")
        opt2 = st.text_input("Option 2")
        opt3 = st.text_input("Option 3")
        opt4 = st.text_input("Option 4")
        ans = st.selectbox("Correct Answer", [opt1, opt2, opt3, opt4] if opt1 and opt2 else [])

        if st.button("Save Question"):
            if not cat or not q_text or not opt1 or not opt2:
                st.warning("Please fill out all mandatory fields.")
            else:
                current_data = load_data()
                questions = current_data.get("questions", [])
                new_id = max([q["id"] for q in questions], default=0) + 1
                new_q = {
                    "id": new_id,
                    "category": cat,
                    "question": q_text,
                    "options": [opt1, opt2, opt3, opt4],
                    "answer": ans
                }
                questions.append(new_q)
                current_data["questions"] = questions
                save_data(current_data)
                st.success("Question added successfully!")

    elif menu == "🤖 AI Question Generator":
        st.subheader("Generate Questions using Gemini AI")
        api_key_input = st.text_input("Enter your Google Gemini API Key", type="password")
        ai_topic = st.text_input("Enter Topic/Subject (e.g., Advanced Python, ReactJS, Networking)")
        num_q = st.slider("Number of Questions", 1, 5, 3)

        if st.button("Generate & Save via AI"):
            if not api_key_input or not ai_topic:
                st.warning("Please provide both API Key and Topic.")
            else:
                try:
                    client = genai.Client(api_key=api_key_input)
                    prompt = f"""
                    Generate {num_q} multiple choice questions about {ai_topic}. 
                    Return ONLY a valid JSON array of objects. Do not include any markdown formatting like ```json ... ```.
                    Each object must have these exact keys:
                    "question": string,
                    "options": array of 4 strings,
                    "answer": string (must match one of the options exactly)
                    """
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt,
                    )
                    
                    raw_text = response.text.strip()
                    if raw_text.startswith("```"):
                        raw_text = raw_text.split("```")[1]
                        if raw_text.startswith("json"):
                            raw_text = raw_text[4:].strip()
                    
                    ai_questions = json.loads(raw_text)
                    current_data = load_data()
                    questions = current_data.get("questions", [])
                    
                    for aq in ai_questions:
                        new_id = max([q["id"] for q in questions], default=0) + 1
                        formatted_q = {
                            "id": new_id,
                            "category": ai_topic,
                            "question": aq["question"],
                            "options": aq["options"],
                            "answer": aq["answer"]
                        }
                        questions.append(formatted_q)
                    
                    current_data["questions"] = questions
                    save_data(current_data)
                    st.success(f"Successfully generated and added {len(ai_questions)} questions under category '{ai_topic}'!")
                except Exception as e:
                    st.error(f"Error generating questions via AI: {e}")

    if st.button("Logout"):
        st.session_state.user = None
        st.session_state.role = None
        st.rerun()

# --- STUDENT QUIZ PLATFORM WITH AI HINTS & ANALYSIS ---
def student_panel():
    st.title("📚 Student Quiz Portal")
    st.write(f"Welcome, **{st.session_state.user}**!")
    
    data = load_data()
    questions = data.get("questions", [])

    if not questions:
        st.warning("No quizzes available right now. Check back later!")
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.role = None
            st.rerun()
        return

    categories = list(set([q["category"] for q in questions]))
    selected_cat = st.selectbox("Select Quiz Category", categories)

    filtered_questions = [q for q in questions if q["category"] == selected_cat]

    if st.button("🚀 Start Quiz"):
        st.session_state.active_quiz = filtered_questions
        st.session_state.current_q_index = 0
        st.session_state.user_answers = {}
        st.session_state.quiz_submitted = False
        st.session_state.quiz_start_time = time.time()
        st.session_state.time_limit = 120  # 2 minutes timer
        st.rerun()

    if "active_quiz" in st.session_state and st.session_state.active_quiz:
        q_list = st.session_state.active_quiz
        idx = st.session_state.current_q_index

        elapsed_time = int(time.time() - st.session_state.quiz_start_time)
        time_left = st.session_state.time_limit - elapsed_time

        if time_left <= 0 and not st.session_state.quiz_submitted:
            st.warning("⏰ Time's up! Your quiz has been auto-submitted.")
            st.session_state.quiz_submitted = True
            st.rerun()

        if not st.session_state.quiz_submitted:
            col_q, col_timer = st.columns([3, 1])
            with col_q:
                st.markdown(f"### Question {idx + 1} of {len(q_list)}")
            with col_timer:
                st.markdown(f"**⏱️ Time Left:** `{max(0, time_left)}s`")

            current_q = q_list[idx]
            st.write(f"**{current_q['question']}**")

            options = current_q["options"]
            current_ans = st.session_state.user_answers.get(current_q["id"], None)
            display_options = ["-- Select an option --"] + options
            
            if current_ans in options:
                default_index = options.index(current_ans) + 1
            else:
                default_index = 0

            selected_choice = st.radio("Choose an option:", display_options, index=default_index, key=f"q_{current_q['id']}")

            if selected_choice != "-- Select an option --":
                st.session_state.user_answers[current_q["id"]] = selected_choice
            else:
                if current_q["id"] in st.session_state.user_answers:
                    del st.session_state.user_answers[current_q["id"]]

            # AI Hint Section Option
            with st.expander("💡 Need an AI Hint?"):
                gemini_key_student = st.text_input("Enter Gemini API Key for Hint", type="password", key=f"hint_key_{idx}")
                if st.button("Get Hint", key=f"hint_btn_{idx}"):
                    if not gemini_key_student:
                        st.warning("Please enter your Gemini API Key.")
                    else:
                        try:
                            client = genai.Client(api_key=gemini_key_student)
                            prompt = f"Give a subtle, helpful hint (without directly revealing the correct answer) for this question: '{current_q['question']}' with options: {current_q['options']}"
                            res = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
                            st.info(res.text)
                        except Exception as e:
                            st.error(f"Could not fetch hint: {e}")

            col1, col2 = st.columns(2)
            with col1:
                if idx > 0 and st.button("⬅️ Previous"):
                    st.session_state.current_q_index -= 1
                    st.rerun()
            with col2:
                if idx < len(q_list) - 1:
                    if st.button("Next ➡️"):
                        st.session_state.current_q_index += 1
                        st.rerun()
                else:
                    if st.button("✅ Submit Quiz"):
                        st.session_state.quiz_submitted = True
                        st.rerun()
        else:
            # --- RESULT PAGE & AI PERFORMANCE FEEDBACK ---
            st.subheader("📊 Quiz Performance & AI Insights")
            score = 0
            total = len(q_list)
            incorrect_questions = []

            for q in q_list:
                user_ans = st.session_state.user_answers.get(q["id"])
                if user_ans == q["answer"]:
                    score += 1
                else:
                    incorrect_questions.append({
                        "question": q["question"],
                        "your_answer": user_ans if user_ans else "Not Answered",
                        "correct_answer": q["answer"]
                    })

            percentage = (score / total) * 100

            col_a, col_b = st.columns(2)
            with col_a:
                st.metric(label="Final Score", value=f"{score} / {total}")
            with col_b:
                st.metric(label="Percentage", value=f"{percentage:.2f}%")

            if percentage >= 50:
                st.success("🎉 Outstanding! You passed the quiz successfully.")
            else:
                st.error("❌ Don't worry! Review the material and try again.")

            # AI Analysis Section
            st.markdown("---")
            st.subheader("🤖 AI Performance Tutor Analysis")
            ai_analysis_key = st.text_input("Enter Gemini API Key for Feedback", type="password", key="analysis_key")
            if st.button("Generate AI Feedback"):
                if not ai_analysis_key:
                    st.warning("Please enter your API Key for detailed feedback.")
                else:
                    try:
                        client = genai.Client(api_key=ai_analysis_key)
                        feedback_prompt = f"The student scored {score} out of {total} ({percentage}%) in category {selected_cat}. Here are the questions they got wrong: {incorrect_questions}. Provide a short, motivating tutor-like feedback explaining how they can improve."
                        feedback_res = client.models.generate_content(model='gemini-2.5-flash', contents=feedback_prompt)
                        st.write(feedback_res.text)
                    except Exception as e:
                        st.error(f"Error generating feedback: {e}")

            if st.button("🔄 Restart / Attempt Another Quiz"):
                del st.session_state.active_quiz
                del st.session_state.current_q_index
                del st.session_state.user_answers
                del st.session_state.quiz_submitted
                st.rerun()

    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()

# --- MAIN ROUTER ---
if st.session_state.user is None:
    auth_page()
elif st.session_state.role == "admin":
    admin_panel()
else:
    student_panel()
