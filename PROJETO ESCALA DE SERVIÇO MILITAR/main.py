# ============================================================
# SISTEMA DE ESCALA DE SERVIÇO
# ============================================================
# Cadastro simples:
# - Nome
# - Matrícula (opcional)
# - Turno
#
# São cadastradas 4 pessoas no DIURNO e 4 no NOTURNO.
#
# ESCALA AUTOMÁTICA:
# - Segunda a sexta: 2 das 4 pessoas trabalham por dia.
# - Sábado e domingo: 2 das 4 pessoas fazem o rodízio do fim de semana.
# - O rodízio do fim de semana é separado dos dias úteis.
# - PDF disponível quando a escala estiver gerada.
# ============================================================

import calendar
import datetime as dt
import tkinter as tk
from tkinter import messagebox, filedialog

import customtkinter as ctk

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    PDF_OK = True
except ImportError:
    PDF_OK = False

import database as db
import funcoes

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

MESES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
         "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
DIAS = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Escala de Serviço")
        self.geometry("1450x850")
        self.minsize(1100, 700)
        hoje = dt.date.today()
        self.ano, self.mes = hoje.year, hoje.month
        self.pessoas = []
        self.criar_interface()
        self.carregar_pessoas()
        self.montar_grade()

    def criar_interface(self):
        topo = ctk.CTkFrame(self)
        topo.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(topo, text="ESCALA DE SERVIÇO", font=("Segoe UI", 22, "bold")).pack(side="left", padx=15, pady=12)
        self.lbl_mes = ctk.CTkLabel(topo, text="", font=("Segoe UI", 18, "bold"))
        self.lbl_mes.pack(side="left", padx=15)

        ctk.CTkButton(topo, text="◀", width=40, command=lambda: self.mudar_mes(-1)).pack(side="left")
        ctk.CTkButton(topo, text="▶", width=40, command=lambda: self.mudar_mes(1)).pack(side="left", padx=(5, 15))
        ctk.CTkButton(topo, text="CADASTRO", command=self.abrir_cadastro).pack(side="right", padx=5)
        ctk.CTkButton(topo, text="PDF", fg_color="#7c3aed", hover_color="#6d28d9", command=self.gerar_pdf).pack(side="right", padx=5)
        ctk.CTkButton(topo, text="GERAR ESCALA", fg_color="#059669", hover_color="#047857", command=self.gerar_escala).pack(side="right", padx=5)

        legenda = ctk.CTkLabel(
            self, text="DIAS ÚTEIS: 2 de 4 trabalhando  |  FIM DE SEMANA: 2 de 4 em rodízio",
            font=("Segoe UI", 12, "bold"), text_color="#fbbf24"
        )
        legenda.pack(pady=(0, 8))

        self.grade = ctk.CTkFrame(self)
        self.grade.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def carregar_pessoas(self):
        self.pessoas = db.listar_militares()

    def contar_turnos(self):
        return (
            sum(1 for p in self.pessoas if p["turno"] == "DIURNO"),
            sum(1 for p in self.pessoas if p["turno"] == "NOTURNO")
        )

    def abrir_cadastro(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Cadastro - 4 pessoas por turno")
        janela.geometry("900x680")
        janela.grab_set()

        ctk.CTkLabel(janela, text="CADASTRO", font=("Segoe UI", 20, "bold")).pack(pady=(20, 5))
        contagem = ctk.CTkLabel(janela, text="", font=("Segoe UI", 14, "bold"), text_color="#fbbf24")
        contagem.pack(pady=5)

        lista = ctk.CTkScrollableFrame(janela)
        lista.pack(fill="both", expand=True, padx=20, pady=15)

        def atualizar():
            self.carregar_pessoas()
            d, n = self.contar_turnos()
            contagem.configure(text=f"DIURNO: {d}/4     |     NOTURNO: {n}/4")
            for w in lista.winfo_children():
                w.destroy()
            for pessoa in self.pessoas:
                linha = ctk.CTkFrame(lista)
                linha.pack(fill="x", pady=4)
                ctk.CTkLabel(
                    linha,
                    text=f"{pessoa['nome']} | {pessoa['matricula'] or 'Sem matrícula'} | {pessoa['turno']}",
                    font=("Segoe UI", 11, "bold")
                ).pack(side="left", padx=10, pady=10)
                ctk.CTkButton(
                    linha, text="Excluir", width=70, fg_color="#991b1b", hover_color="#7f1d1d",
                    command=lambda pid=pessoa["id"]: (db.excluir_militar(pid), atualizar(), self.montar_grade())
                ).pack(side="right", padx=8)

        ctk.CTkButton(janela, text="+ CADASTRAR PESSOA", command=lambda: self.formulario(janela, atualizar)).pack(pady=5)
        atualizar()

    def formulario(self, pai, atualizar):
        janela = ctk.CTkToplevel(pai)
        janela.title("Nova pessoa")
        janela.geometry("430x390")
        janela.grab_set()

        ctk.CTkLabel(janela, text="NOVA PESSOA", font=("Segoe UI", 18, "bold")).pack(pady=20)

        ctk.CTkLabel(janela, text="Nome *").pack(anchor="w", padx=30)
        nome = ctk.CTkEntry(janela, height=35)
        nome.pack(fill="x", padx=30, pady=(2, 12))

        ctk.CTkLabel(janela, text="Matrícula (opcional)").pack(anchor="w", padx=30)
        matricula = ctk.CTkEntry(janela, height=35)
        matricula.pack(fill="x", padx=30, pady=(2, 12))

        ctk.CTkLabel(janela, text="Turno").pack(anchor="w", padx=30)
        turno = ctk.CTkComboBox(janela, values=funcoes.TURNOS, height=35)
        turno.pack(fill="x", padx=30, pady=(2, 20))
        turno.set("DIURNO")

        def salvar():
            self.carregar_pessoas()
            nome_valor = nome.get().strip()
            turno_valor = turno.get()
            if not nome_valor:
                messagebox.showerror("Erro", "Informe o nome.", parent=janela)
                return
            quantidade = sum(1 for p in self.pessoas if p["turno"] == turno_valor)
            if quantidade >= 4:
                messagebox.showwarning("Limite", f"O turno {turno_valor} já possui 4 pessoas.", parent=janela)
                return
            try:
                # O campo escala fica fixo no banco para manter compatibilidade.
                db.cadastrar_militar(nome_valor, matricula.get(), "Semana + Fim de Semana", turno_valor)
                janela.destroy()
                atualizar()
                self.montar_grade()
            except Exception as e:
                messagebox.showerror("Erro", str(e), parent=janela)

        ctk.CTkButton(janela, text="SALVAR", height=42, fg_color="#059669", hover_color="#047857", command=salvar).pack(fill="x", padx=30)

    def gerar_escala(self):
        self.carregar_pessoas()
        d, n = self.contar_turnos()
        if d != 4 or n != 4:
            messagebox.showwarning("Cadastro incompleto", f"Cadastre exatamente 4 pessoas em cada turno.\n\nDIURNO: {d}/4\nNOTURNO: {n}/4")
            return
        try:
            registros = funcoes.gerar_escala_automatica(self.pessoas, self.ano, self.mes)
            db.apagar_escala_mes(self.ano, self.mes)
            db.salvar_escala(registros)
            self.montar_grade()
            messagebox.showinfo("Pronto", f"Escala de {MESES[self.mes]} de {self.ano} gerada.")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def montar_grade(self):
        for w in self.grade.winfo_children():
            w.destroy()
        dados = db.buscar_escala_mes(self.ano, self.mes)
        self.lbl_mes.configure(text=f"{MESES[self.mes]} / {self.ano}")

        for col, dia in enumerate(DIAS):
            self.grade.grid_columnconfigure(col, weight=1, uniform="dia")
            ctk.CTkLabel(self.grade, text=dia, font=("Segoe UI", 10, "bold"), text_color="#f87171" if col >= 5 else "#93c5fd").grid(row=0, column=col, sticky="nsew", padx=2, pady=3)

        semanas = calendar.Calendar(firstweekday=0).monthdatescalendar(self.ano, self.mes)
        for linha, semana in enumerate(semanas, start=1):
            self.grade.grid_rowconfigure(linha, weight=1)
            for col, data in enumerate(semana):
                fora = data.month != self.mes
                celula = ctk.CTkFrame(self.grade, fg_color="#0b0f16" if fora else ("#24191a" if col >= 5 else "#151a23"), border_width=1, border_color="#303642")
                celula.grid(row=linha, column=col, sticky="nsew", padx=2, pady=2)
                ctk.CTkLabel(celula, text=str(data.day), font=("Segoe UI", 10, "bold"), text_color="#64748b" if fora else "#ffffff").pack(anchor="nw", padx=5, pady=3)
                if fora:
                    continue
                for item in dados.get(data.isoformat(), []):
                    inicial_turno = "D" if item["turno"] == "DIURNO" else "N"
                    servico = item["situacao"] == "SERVIÇO"
                    ctk.CTkLabel(
                        celula,
                        text=f"{item['nome'][:12]} • {inicial_turno} • {'S' if servico else 'F'}",
                        font=("Segoe UI", 8), fg_color="#15803d" if servico else "#475569", corner_radius=3, anchor="w"
                    ).pack(fill="x", padx=3, pady=1)

    def mudar_mes(self, delta):
        self.mes += delta
        if self.mes > 12:
            self.mes, self.ano = 1, self.ano + 1
        elif self.mes < 1:
            self.mes, self.ano = 12, self.ano - 1
        self.montar_grade()

    def gerar_pdf(self):
        if not PDF_OK:
            messagebox.showerror("ReportLab", "Instale com: python -m pip install reportlab")
            return
        dados = db.buscar_escala_mes(self.ano, self.mes)
        if not dados:
            messagebox.showwarning("Sem escala", "Gere a escala antes de criar o PDF.")
            return
        caminho = filedialog.asksaveasfilename(title="Salvar PDF", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")])
        if not caminho:
            return
        try:
            doc = SimpleDocTemplate(caminho, pagesize=landscape(A4), rightMargin=18, leftMargin=18, topMargin=18, bottomMargin=18)
            estilos = getSampleStyleSheet()
            elementos = [
                Paragraph(f"ESCALA DE SERVIÇO - {MESES[self.mes].upper()} / {self.ano}", estilos["Title"]),
                Paragraph("S = Serviço | F = Folga | Dias úteis: 2 de 4 | Fim de semana: rodízio separado", estilos["Normal"]),
                Spacer(1, 10)
            ]
            dias_mes = calendar.monthrange(self.ano, self.mes)[1]
            tabela = [["PESSOA / TURNO"] + [f"{d:02d}\n{DIAS[dt.date(self.ano,self.mes,d).weekday()]}" for d in range(1, dias_mes + 1)]]
            for pessoa in self.pessoas:
                linha = [f"{pessoa['nome']}\n{pessoa['turno']}"]
                for d in range(1, dias_mes + 1):
                    data = dt.date(self.ano, self.mes, d).isoformat()
                    item = next((x for x in dados.get(data, []) if x["militar_id"] == pessoa["id"]), None)
                    linha.append("S" if item and item["situacao"] == "SERVIÇO" else "F" if item else "-")
                tabela.append(linha)
            t = Table(tabela, repeatRows=1, hAlign="CENTER")
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#1e3a8a")),
                ("TEXTCOLOR", (0,0), (-1,0), colors.white),
                ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
                ("GRID", (0,0), (-1,-1), .4, colors.grey),
                ("ALIGN", (1,1), (-1,-1), "CENTER"),
                ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ("FONTSIZE", (0,0), (-1,-1), 6),
            ]))
            elementos.append(t)
            doc.build(elementos)
            messagebox.showinfo("PDF", "PDF criado com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro no PDF", str(e))


if __name__ == "__main__":
    db.iniciar_banco()
    App().mainloop()
