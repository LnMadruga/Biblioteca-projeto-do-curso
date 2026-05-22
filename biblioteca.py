import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import re
import os

def conectar():
    caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), "banco.db")
    return sqlite3.connect(caminho)

def criar_tabelas():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS autor (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT    NOT NULL,
            pais TEXT    NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS livro (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo    TEXT    NOT NULL,
            ano       TEXT    NOT NULL,
            autor_id  INTEGER NOT NULL,
            FOREIGN KEY (autor_id) REFERENCES autor(id)
        )
    """)
    con.commit()
    con.close()

def limpar_banco():
    con = conectar()
    con.execute("DELETE FROM livro")
    con.execute("DELETE FROM autor")
    con.execute("DELETE FROM sqlite_sequence")
    con.commit()
    con.close()

def validar_ano(ano_str):
    s = ano_str.strip()
    if not s:
        return False, "O campo Ano não pode estar vazio."
    padrao = re.fullmatch(r"-?\d[\d.]*(\s*(a\.?c\.?|A\.?C\.?))?", s, re.IGNORECASE)
    if not padrao:
        return False, (
            "Formato de ano inválido.\n\n"
            "Exemplos aceitos:\n"
            "  1984\n"
            "  1.500\n"
            "  300 A.C.\n"
            "  -500"
        )
    return True, s

def salvar_autor(nome, pais):
    if not nome or not pais:
        messagebox.showwarning("Atenção", "Preencha todos os campos do autor.")
        return False
    con = conectar()
    con.execute("INSERT INTO autor (nome, pais) VALUES (?, ?)", (nome, pais))
    con.commit()
    con.close()
    return True

def listar_autores():
    con = conectar()
    rows = con.execute("SELECT id, nome, pais FROM autor ORDER BY nome").fetchall()
    con.close()
    return rows

def excluir_autor(autor_id):
    con = conectar()
    qtd = con.execute("SELECT COUNT(*) FROM livro WHERE autor_id=?", (autor_id,)).fetchone()[0]
    if qtd > 0:
        con.close()
        messagebox.showerror("Erro", "Não é possível excluir: autor possui livros cadastrados.")
        return False
    con.execute("DELETE FROM autor WHERE id=?", (autor_id,))
    con.commit()
    con.close()
    return True

def salvar_livro(titulo, ano, autor_id):
    if not titulo or not autor_id:
        messagebox.showwarning("Atenção", "Preencha todos os campos do livro.")
        return False
    ok, resultado = validar_ano(ano)
    if not ok:
        messagebox.showerror("Ano inválido", resultado)
        return False
    con = conectar()
    con.execute("INSERT INTO livro (titulo, ano, autor_id) VALUES (?, ?, ?)",
                (titulo, resultado, autor_id))
    con.commit()
    con.close()
    return True

def listar_livros():
    con = conectar()
    rows = con.execute("""
        SELECT l.id, l.titulo, l.ano, a.nome
        FROM livro l
        JOIN autor a ON a.id = l.autor_id
        ORDER BY l.titulo
    """).fetchall()
    con.close()
    return rows

def excluir_livro(livro_id):
    con = conectar()
    con.execute("DELETE FROM livro WHERE id=?", (livro_id,))
    con.commit()
    con.close()
    return True

def pesquisar_livros(filtro_autor="", filtro_ano="", filtro_titulo=""):
    """
    Retorna livros filtrando por nome do autor, ano e/ou título do livro.
    Todos os filtros usam LIKE (busca parcial, sem diferenciar maiúsc/minúsc).
    """
    con = conectar()
    query = """
        SELECT l.id, l.titulo, l.ano, a.nome
        FROM livro l
        JOIN autor a ON a.id = l.autor_id
        WHERE a.nome   LIKE ?
          AND l.ano    LIKE ?
          AND l.titulo LIKE ?
        ORDER BY l.titulo
    """
    autor_param  = f"%{filtro_autor}%"
    ano_param    = f"%{filtro_ano}%"
    titulo_param = f"%{filtro_titulo}%"
    rows = con.execute(query, (autor_param, ano_param, titulo_param)).fetchall()
    con.close()
    return rows

STYLE_LABEL = {"bg": "white", "fg": "black", "font": ("Segoe UI", 10)}
STYLE_ENTRY = {"bg": "white", "fg": "black", "insertbackground": "black",
               "relief": "solid", "bd": 1, "font": ("Segoe UI", 10)}
STYLE_BTN_P = {"bg": "#2563EB", "fg": "white", "relief": "flat",
               "font": ("Segoe UI", 9, "bold"), "padx": 14, "pady": 6,
               "cursor": "hand2"}
STYLE_BTN_D = {"bg": "#DC2626", "fg": "white", "relief": "flat",
               "font": ("Segoe UI", 9, "bold"), "padx": 14, "pady": 6,
               "cursor": "hand2"}
STYLE_BTN_S = {"bg": "#059669", "fg": "white", "relief": "flat",
               "font": ("Segoe UI", 9, "bold"), "padx": 14, "pady": 6,
               "cursor": "hand2"}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Biblioteca")
        self.geometry("820x560")
        self.resizable(False, False)
        self.configure(bg="white")

        criar_tabelas()
        self._build_menu()

        self.container = tk.Frame(self, bg="white")
        self.container.pack(fill="both", expand=True, padx=12, pady=10)

        self.mostrar_tela_autores()

    def _build_menu(self):
        barra = tk.Menu(self)

        menu_nav = tk.Menu(barra, tearoff=0)
        menu_nav.add_command(label="👤  Autores",   command=self.mostrar_tela_autores)
        menu_nav.add_command(label="📚  Livros",    command=self.mostrar_tela_livros)
        menu_nav.add_command(label="🔍  Pesquisa",  command=self.mostrar_tela_pesquisa)
        menu_nav.add_separator()
        menu_nav.add_command(label="🗑  Limpar banco de dados",
                             command=self._limpar_banco_confirmacao)
        menu_nav.add_separator()
        menu_nav.add_command(label="Sair", command=self.quit)
        barra.add_cascade(label="Menu", menu=menu_nav)

        menu_ajuda = tk.Menu(barra, tearoff=0)
        menu_ajuda.add_command(label="Sobre / Créditos", command=self.mostrar_creditos)
        barra.add_cascade(label="Ajuda", menu=menu_ajuda)

        self.config(menu=barra)

    def _limpar_container(self):
        for w in self.container.winfo_children():
            w.destroy()

    def mostrar_tela_autores(self):
        self._limpar_container()
        TelaAutores(self.container, self)

    def mostrar_tela_livros(self):
        self._limpar_container()
        TelaLivros(self.container, self)

    def mostrar_tela_pesquisa(self):
        self._limpar_container()
        TelaPesquisa(self.container, self)

    # ── LIMPAR BANCO ───────────────────────────
    def _limpar_banco_confirmacao(self):
        if messagebox.askyesno("Atenção",
                               "Isso vai apagar TODOS os dados do banco.\nTem certeza?"):
            limpar_banco()
            self.mostrar_tela_autores()
            messagebox.showinfo("Pronto", "Banco de dados limpo!\nOs IDs foram resetados.")

    def mostrar_creditos(self):
        win = tk.Toplevel(self)
        win.title("Sobre")
        win.geometry("360x260")
        win.resizable(False, False)
        win.configure(bg="white")

        tk.Label(win, text="📖  Sistema de Biblioteca",
                 font=("Segoe UI", 14, "bold"),
                 bg="white", fg="black").pack(pady=(20, 4))

        tk.Label(win,
                 text="Aplicação gráfica desenvolvida com\nTkinter e banco de dados SQLite.",
                 font=("Segoe UI", 10),
                 bg="white", fg="#444444", justify="center").pack()

        tk.Frame(win, bg="#dddddd", height=1).pack(fill="x", padx=20, pady=10)

        tk.Label(win, text="Integrantes do Grupo",
                 font=("Segoe UI", 10, "bold"),
                 bg="white", fg="black").pack()

        membros = [
            "Leonardo N. Madruga – Matrícula: 202403933951",
        ]
        for m in membros:
            tk.Label(win, text=m, font=("Segoe UI", 9),
                     bg="white", fg="#333333").pack()

        tk.Button(win, text="Fechar", command=win.destroy,
                  bg="#2563EB", fg="white",
                  font=("Segoe UI", 9, "bold"),
                  relief="flat", padx=16, pady=5,
                  cursor="hand2").pack(pady=16)

class TelaAutores(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.pack(fill="both", expand=True)
        self.app = app

        tk.Label(self, text="👤  Cadastro de Autores",
                 font=("Segoe UI", 13, "bold"),
                 bg="white", fg="black").grid(
                 row=0, column=0, columnspan=4, pady=(0, 12), sticky="w")

        tk.Label(self, text="Nome:", **STYLE_LABEL).grid(row=1, column=0, sticky="e", padx=4)
        self.ent_nome = tk.Entry(self, width=28, **STYLE_ENTRY)
        self.ent_nome.grid(row=1, column=1, padx=4, pady=4)

        tk.Label(self, text="País:", **STYLE_LABEL).grid(row=1, column=2, sticky="e", padx=4)
        self.ent_pais = tk.Entry(self, width=18, **STYLE_ENTRY)
        self.ent_pais.grid(row=1, column=3, padx=4, pady=4)

        tk.Button(self, text="💾  Salvar", command=self.salvar, **STYLE_BTN_P).grid(
            row=2, column=1, pady=8, sticky="w")
        tk.Button(self, text="🗑  Excluir", command=self.excluir, **STYLE_BTN_D).grid(
            row=2, column=3, pady=8, sticky="w")

        cols = ("ID", "Nome", "País")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.column("ID",   width=50,  anchor="center")
        self.tree.column("Nome", width=300)
        self.tree.column("País", width=150)
        self.tree.grid(row=3, column=0, columnspan=4, padx=4, pady=8, sticky="nsew")

        self._estilo_tabela()
        self.carregar()

    def _estilo_tabela(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background="white", foreground="black",
                        fieldbackground="white", rowheight=24,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background="#f0f0f0", foreground="black",
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#BFDBFE")])

    def carregar(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in listar_autores():
            self.tree.insert("", "end", values=row)

    def salvar(self):
        if salvar_autor(self.ent_nome.get().strip(), self.ent_pais.get().strip()):
            self.ent_nome.delete(0, "end")
            self.ent_pais.delete(0, "end")
            self.carregar()
            messagebox.showinfo("Sucesso", "Autor cadastrado com sucesso!")

    def excluir(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um autor na tabela.")
            return
        autor_id = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar", "Deseja excluir este autor?"):
            if excluir_autor(autor_id):
                self.carregar()

class TelaLivros(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.pack(fill="both", expand=True)
        self.app = app
        self._autores = []

        tk.Label(self, text="📚  Cadastro de Livros",
                 font=("Segoe UI", 13, "bold"),
                 bg="white", fg="black").grid(
                 row=0, column=0, columnspan=6, pady=(0, 12), sticky="w")

        tk.Label(self, text="Título:", **STYLE_LABEL).grid(row=1, column=0, sticky="e", padx=4)
        self.ent_titulo = tk.Entry(self, width=28, **STYLE_ENTRY)
        self.ent_titulo.grid(row=1, column=1, padx=4, pady=4)

        # Campo Ano
        frame_ano = tk.Frame(self, bg="white")
        frame_ano.grid(row=1, column=2, columnspan=2, sticky="w", padx=4)
        tk.Label(frame_ano, text="Ano:", **STYLE_LABEL).pack(side="left", padx=(0, 4))
        vcmd = (self.register(self._validar_char_ano), "%P")
        self.ent_ano = tk.Entry(frame_ano, width=12,
                                validate="key", validatecommand=vcmd,
                                **STYLE_ENTRY)
        self.ent_ano.pack(side="left")

        tk.Label(self, text="Ex: 1984 · 1.500 · 300 A.C. · -500",
                 bg="white", fg="#888888",
                 font=("Segoe UI", 8)).grid(row=2, column=2, columnspan=2,
                                             sticky="w", padx=4)

        tk.Label(self, text="Autor:", **STYLE_LABEL).grid(row=1, column=4, sticky="e", padx=4)
        self.combo_autor = ttk.Combobox(self, width=20, state="readonly",
                                        font=("Segoe UI", 10))
        self.combo_autor.grid(row=1, column=5, padx=4, pady=4)

        tk.Button(self, text="💾  Salvar", command=self.salvar, **STYLE_BTN_P).grid(
            row=3, column=1, pady=8, sticky="w")
        tk.Button(self, text="🗑  Excluir", command=self.excluir, **STYLE_BTN_D).grid(
            row=3, column=3, pady=8, sticky="w")

        cols = ("ID", "Título", "Ano", "Autor")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=13)
        self.tree.heading("ID",     text="ID");     self.tree.column("ID",     width=50,  anchor="center")
        self.tree.heading("Título", text="Título"); self.tree.column("Título", width=260)
        self.tree.heading("Ano",    text="Ano");    self.tree.column("Ano",    width=100, anchor="center")
        self.tree.heading("Autor",  text="Autor");  self.tree.column("Autor",  width=200)
        self.tree.grid(row=4, column=0, columnspan=6, padx=4, pady=8, sticky="nsew")

        self._estilo_tabela()
        self.carregar_autores()
        self.carregar()

    def _validar_char_ano(self, novo_valor):
        return re.fullmatch(r"[-.\d AaCc\.]*", novo_valor) is not None

    def _estilo_tabela(self):
        style = ttk.Style()
        style.configure("Treeview",
                        background="white", foreground="black",
                        fieldbackground="white", rowheight=24,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background="#f0f0f0", foreground="black",
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#BFDBFE")])

    def carregar_autores(self):
        self._autores = listar_autores()
        nomes = [a[1] for a in self._autores]
        self.combo_autor["values"] = nomes
        if nomes:
            self.combo_autor.current(0)

    def carregar(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in listar_livros():
            self.tree.insert("", "end", values=row)

    def salvar(self):
        idx = self.combo_autor.current()
        if idx < 0 or not self._autores:
            messagebox.showwarning("Atenção", "Cadastre pelo menos um autor primeiro.")
            return
        autor_id = self._autores[idx][0]
        if salvar_livro(self.ent_titulo.get().strip(),
                        self.ent_ano.get().strip(),
                        autor_id):
            self.ent_titulo.delete(0, "end")
            self.ent_ano.delete(0, "end")
            self.carregar()
            messagebox.showinfo("Sucesso", "Livro cadastrado com sucesso!")

    def excluir(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um livro na tabela.")
            return
        livro_id = self.tree.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar", "Deseja excluir este livro?"):
            excluir_livro(livro_id)
            self.carregar()

class TelaPesquisa(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="white")
        self.pack(fill="both", expand=True)
        self.app = app

        # ── Título ──
        tk.Label(self, text="🔍  Pesquisa de Livros",
                 font=("Segoe UI", 13, "bold"),
                 bg="white", fg="black").grid(
                 row=0, column=0, columnspan=6, pady=(0, 10), sticky="w")

        # ── Linha separadora ──
        tk.Frame(self, bg="#dddddd", height=1).grid(
            row=1, column=0, columnspan=6, sticky="ew", pady=(0, 10))

        # ── Filtros – linha 1: Título e Autor ──
        tk.Label(self, text="Filtrar por Título:",
                 **STYLE_LABEL).grid(row=2, column=0, sticky="e", padx=4)
        self.ent_titulo = tk.Entry(self, width=24, **STYLE_ENTRY)
        self.ent_titulo.grid(row=2, column=1, padx=4, pady=4, sticky="w")

        tk.Label(self, text="Filtrar por Autor:",
                 **STYLE_LABEL).grid(row=2, column=2, sticky="e", padx=(16, 4))
        self.ent_autor = tk.Entry(self, width=24, **STYLE_ENTRY)
        self.ent_autor.grid(row=2, column=3, padx=4, pady=4, sticky="w")

        # ── Filtros – linha 2: Ano e Botões ──
        tk.Label(self, text="Filtrar por Ano:",
                 **STYLE_LABEL).grid(row=3, column=0, sticky="e", padx=4)
        self.ent_ano = tk.Entry(self, width=14, **STYLE_ENTRY)
        self.ent_ano.grid(row=3, column=1, padx=4, pady=4, sticky="w")

        # ── Botões ──
        tk.Button(self, text="🔍  Pesquisar",
                  command=self.pesquisar, **STYLE_BTN_S).grid(
                  row=3, column=2, padx=(16, 4), pady=4, sticky="w")
        tk.Button(self, text="✖  Limpar",
                  command=self.limpar_filtros, **STYLE_BTN_D).grid(
                  row=3, column=3, padx=4, pady=4, sticky="w")

        # Dica
        tk.Label(self,
                 text="Deixe um campo em branco para ignorar esse filtro. "
                      "A busca é parcial — \"Mach\" encontra \"Machado de Assis\".",
                 bg="white", fg="#888888",
                 font=("Segoe UI", 8)).grid(
                 row=4, column=0, columnspan=6, sticky="w", padx=4, pady=(0, 6))

        # ── Contador de resultados ──
        self.lbl_count = tk.Label(self, text="", bg="white", fg="#555555",
                                  font=("Segoe UI", 9, "italic"))
        self.lbl_count.grid(row=5, column=0, columnspan=6, sticky="w", padx=4)

        # ── Tabela de resultados ──
        cols = ("ID", "Título", "Ano", "Autor")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=14)
        self.tree.heading("ID",     text="ID");     self.tree.column("ID",     width=50,  anchor="center")
        self.tree.heading("Título", text="Título"); self.tree.column("Título", width=260)
        self.tree.heading("Ano",    text="Ano");    self.tree.column("Ano",    width=100, anchor="center")
        self.tree.heading("Autor",  text="Autor");  self.tree.column("Autor",  width=250)
        self.tree.grid(row=6, column=0, columnspan=6, padx=4, pady=6, sticky="nsew")

        self._estilo_tabela()

        # Pesquisa automática ao digitar em qualquer campo
        self.ent_titulo.bind("<KeyRelease>", lambda e: self.pesquisar())
        self.ent_autor.bind("<KeyRelease>",  lambda e: self.pesquisar())
        self.ent_ano.bind("<KeyRelease>",    lambda e: self.pesquisar())

        # Carrega todos os livros ao abrir
        self.pesquisar()

    def _estilo_tabela(self):
        style = ttk.Style()
        style.configure("Treeview",
                        background="white", foreground="black",
                        fieldbackground="white", rowheight=24,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background="#f0f0f0", foreground="black",
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", "#BFDBFE")])

    def pesquisar(self):
        filtro_titulo = self.ent_titulo.get().strip()
        filtro_autor  = self.ent_autor.get().strip()
        filtro_ano    = self.ent_ano.get().strip()
        resultados    = pesquisar_livros(filtro_autor, filtro_ano, filtro_titulo)

        for row in self.tree.get_children():
            self.tree.delete(row)
        for row in resultados:
            self.tree.insert("", "end", values=row)

        total = len(resultados)
        if total == 0:
            self.lbl_count.config(text="Nenhum resultado encontrado.", fg="#DC2626")
        elif total == 1:
            self.lbl_count.config(text="1 livro encontrado.", fg="#059669")
        else:
            self.lbl_count.config(text=f"{total} livros encontrados.", fg="#059669")

    def limpar_filtros(self):
        self.ent_titulo.delete(0, "end")
        self.ent_autor.delete(0, "end")
        self.ent_ano.delete(0, "end")
        self.pesquisar()

if __name__ == "__main__":
    app = App()
    app.mainloop()
