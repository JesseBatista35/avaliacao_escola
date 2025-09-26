from flask import Flask, render_template, request, redirect, url_for, session
import os
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = "uma_chave_secreta_aqui"

# Conexão com PostgreSQL via variáveis de ambiente (Render)
db = psycopg2.connect(
    host=os.environ.get("DB_HOST"),
    database=os.environ.get("DB_NAME"),
    user=os.environ.get("DB_USER"),
    password=os.environ.get("DB_PASSWORD"),
    port=os.environ.get("DB_PORT", 5432)
)

cursor = db.cursor(cursor_factory=RealDictCursor)

# -------------------------
# Página inicial
# -------------------------
@app.route("/")
def welcome():
    return render_template("welcome.html")

# -------------------------
# Quiz
# -------------------------
@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    classe = request.args.get("classe") or request.form.get("classe")
    if request.method == "POST":
        aluno_nome = request.form.get("aluno_nome")
        sugestao = request.form.get("sugestao")  # opcional

        for key in request.form:
            if key.startswith("pergunta"):
                parts = key.split("_")
                pergunta = parts[0]
                professor_id = parts[1]
                resposta = request.form.get(key)
                cursor.execute("""
                    INSERT INTO respostas (aluno_nome, professor_id, pergunta, resposta, sugestao)
                    VALUES (%s,%s,%s,%s,%s)
                """, (aluno_nome, professor_id, pergunta, resposta, sugestao))
        db.commit()
        return redirect(url_for("thankyou"))

    # Buscar todos os professores da classe selecionada
    cursor.execute("""
        SELECT p.* 
        FROM professores p
        JOIN professor_classes pc ON p.id = pc.professor_id
        WHERE pc.classe = %s
    """, (classe,))
    professores = cursor.fetchall()

    return render_template("quiz.html", classe=classe, professores=professores)

# -------------------------
# Página de agradecimento
# -------------------------
@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")

# -------------------------
# Login admin
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "1234":
            session["admin"] = True
            return redirect(url_for("admin"))
        else:
            error = "Usuário ou senha incorretos"
    return render_template("login.html", error=error)

# -------------------------
# Painel admin
# -------------------------
@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect(url_for("login"))

    # Médias por professor
    cursor.execute("""
        SELECT p.id, p.nome, AVG(CAST(r.resposta AS FLOAT)) as media
        FROM professores p
        LEFT JOIN respostas r ON p.id = r.professor_id
        GROUP BY p.id
    """)
    medias = cursor.fetchall()

    # Todas respostas detalhadas
    cursor.execute("""
        SELECT r.*, p.nome as professor_nome
        FROM respostas r
        JOIN professores p ON r.professor_id = p.id
    """)
    respostas = cursor.fetchall()

    return render_template("admin.html", medias=medias, respostas=respostas)

if __name__ == "__main__":
    app.run(debug=True)
