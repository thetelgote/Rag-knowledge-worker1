# import gradio as gr
# from dotenv import load_dotenv
# from implementation.answer import answer_question
# from ingestion.ingest import run_ingest
# import shutil
# import os

# load_dotenv(override=True)

# UPLOAD_DIR = "knowledge-base/uploads"
# os.makedirs(UPLOAD_DIR, exist_ok=True)


# def save_file(file):
#     if file is None:
#         return "❌ No file uploaded"

#     file_path = os.path.join(UPLOAD_DIR, file.name)
#     shutil.copy(file.name, file_path)

#     # 🔥 Auto re-index after upload
#     run_ingest()

#     return f"✅ File uploaded & indexed: {file.name}"


# def format_context(context):
#     text = "### Retrieved Context\n\n"

#     for doc in context:
#         source = doc.metadata.get("source", "unknown")
#         text += f"**Source:** {source}\n\n"
#         text += doc.page_content + "\n\n---\n\n"

#     return text


# def chat(message, history):
#     if history is None:
#         history = []

#     answer, context = answer_question(message, history)

#     history.append((message, answer))

#     return history, format_context(context)


# def main():
#     with gr.Blocks() as ui:

#         gr.Markdown("# 🤖 RAG Knowledge Worker (Multi-file Support)")

#         # 🔥 Upload section
#         file_upload = gr.File(label="Upload PDF / DOCX / TXT / MD")
#         upload_status = gr.Textbox(label="Upload Status")

#         upload_btn = gr.Button("Upload & Index")

#         upload_btn.click(
#             save_file,
#             inputs=file_upload,
#             outputs=upload_status
#         )

#         chatbot = gr.Chatbot(height=400)
#         context_box = gr.Markdown("Context will appear here")

#         msg = gr.Textbox(
#             placeholder="Ask a question from knowledge base",
#             scale=7
#         )

#         msg.submit(
#             chat,
#             inputs=[msg, chatbot],
#             outputs=[chatbot, context_box]
#         ).then(
#             lambda: "",
#             None,
#             msg,
#             queue=False
#         )

#     ui.launch(share=True, inbrowser=True)


# if __name__ == "__main__":
#     main()







import gradio as gr
from dotenv import load_dotenv
from implementation.answer import answer_question
from ingestion.ingest import run_ingest
import shutil, os, sqlite3, hashlib

load_dotenv(override=True)

# ---------------- DB ----------------
DB = "users.db"

def create_user_table():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    conn.commit()
    conn.close()

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def signup(u, p):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users VALUES (NULL, ?, ?)",
                       (u, hash_password(p)))
        conn.commit()
        return "✅ Registered successfully"
    except:
        return "❌ Username already exists"
    finally:
        conn.close()

def login(u, p):
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username=? AND password=?",
                   (u, hash_password(p)))
    user = cursor.fetchone()
    conn.close()
    return user is not None

create_user_table()

# ---------------- FILE ----------------
UPLOAD_DIR = "knowledge-base/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ FIXED FUNCTION
def save_file(file):
    if file is None:
        return "❌ Upload file first"

    filename = os.path.basename(file.name)   # 🔥 fix
    path = os.path.join(UPLOAD_DIR, filename)

    try:
        if not os.path.exists(path):         # 🔥 avoid SameFileError
            shutil.copy(file.name, path)
    except Exception as e:
        return f"❌ Error: {str(e)}"

    run_ingest()
    return f"✅ Indexed: {filename}"

# ---------------- CHAT ----------------
def chat(msg, history):
    history = history or []
    ans, _ = answer_question(msg, history)
    history.append((msg, ans))
    return history

# ---------------- NAVIGATION ----------------
def show_login():
    return gr.update(visible=True), gr.update(visible=False)

def show_register():
    return gr.update(visible=False), gr.update(visible=True)

def handle_login(u, p):
    if login(u, p):
        return (
            "✅ Login successful",
            True,
            gr.update(visible=False),
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False)
        )
    return (
        "❌ Invalid credentials",
        False,
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update(),
        gr.update()
    )

def handle_register(u, p):
    return signup(u, p)

# ---------------- UI ----------------
def main():
    with gr.Blocks(
        theme=gr.themes.Soft(),
        css="""
        body {background: linear-gradient(135deg,#e0c3fc,#8ec5fc);}

        .navbar {
            display:flex;
            justify-content:space-between;
            padding:15px;
        }

        .card {
            width:400px;
            margin:auto;
            margin-top:80px;
            padding:30px;
            border-radius:15px;
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
        }
        """
    ) as ui:

        login_state = gr.State(False)

        # -------- NAVBAR --------
        with gr.Row(elem_classes="navbar"):
            gr.Markdown("### 🤖 AI App")

            with gr.Row():
                nav_login = gr.Button("Login")
                nav_register = gr.Button("Register")

        # -------- LOGIN PAGE --------
        login_page = gr.Column(elem_classes="card")

        with login_page:
            gr.Markdown("## 🔐 Login")
            l_user = gr.Textbox(placeholder="Username")
            l_pass = gr.Textbox(type="password", placeholder="Password")
            l_btn = gr.Button("Login")
            l_status = gr.Markdown()

            go_register = gr.Button("Go to Register")

        # -------- REGISTER PAGE --------
        register_page = gr.Column(visible=False, elem_classes="card")

        with register_page:
            gr.Markdown("## 🆕 Register")
            r_user = gr.Textbox(placeholder="Username")
            r_pass = gr.Textbox(type="password", placeholder="Password")
            r_btn = gr.Button("Register")
            r_status = gr.Markdown()

            go_login = gr.Button("Back to Login")

        # -------- CHAT PAGE --------
        chat_page = gr.Column(visible=False)

        with chat_page:
            gr.Markdown("## 💬 Chatbot")

            chatbot = gr.Chatbot(height=400)

            with gr.Row():
                msg = gr.Textbox(placeholder="Type message...", scale=8)
                send = gr.Button("➤")

            file = gr.File(label="Upload file")
            upload_btn = gr.Button("Upload & Index")
            upload_msg = gr.Markdown()

        # -------- EVENTS --------

        nav_login.click(show_login, None, [login_page, register_page])
        nav_register.click(show_register, None, [login_page, register_page])

        go_register.click(show_register, None, [login_page, register_page])
        go_login.click(show_login, None, [login_page, register_page])

        l_btn.click(
            handle_login,
            [l_user, l_pass],
            [
                l_status,
                login_state,
                login_page,
                register_page,
                chat_page,
                nav_login,
                nav_register
            ]
        )

        r_btn.click(handle_register, [r_user, r_pass], r_status)

        send.click(chat, [msg, chatbot], chatbot)
        msg.submit(chat, [msg, chatbot], chatbot)

        upload_btn.click(save_file, file, upload_msg)

    ui.launch(
    server_name="0.0.0.0",
    server_port=int(os.environ.get("PORT", 7860)),
    share=False
)

# ---------------- RUN ----------------
if __name__ == "__main__":
    main()
