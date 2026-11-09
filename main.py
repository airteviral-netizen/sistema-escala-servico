"""Sistema de escala de serviço com calendário mensal e exportação em PDF."""
import calendar
import datetime as dt
import sqlite3
from tkinter import messagebox, filedialog

import customtkinter as ctk

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from xml.sax.saxutils import escape
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
        self.geometry("1500x900")
        self.minsize(1150, 720)
        hoje = dt.date.today()
        self.ano, self.mes = hoje.year, hoje.month
        self.pessoas = []
        self.criar_interface()
        self.carregar_pessoas()
        self.montar_grade()

    def criar_interface(self):
        topo = ctk.CTkFrame(self)
        topo.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(topo, text="ESCALA DE SERVIÇO", font=("Segoe UI", 22, "bold")).pack(
            side="left", padx=15, pady=12
        )
        self.lbl_mes = ctk.CTkLabel(topo, text="", font=("Segoe UI", 18, "bold"))
        self.lbl_mes.pack(side="left", padx=15)

        ctk.CTkButton(topo, text="◀", width=40, command=lambda: self.mudar_mes(-1)).pack(side="left")
        ctk.CTkButton(topo, text="▶", width=40, command=lambda: self.mudar_mes(1)).pack(side="left", padx=(5, 15))
        ctk.CTkButton(topo, text="CADASTRO", command=self.abrir_cadastro).pack(side="right", padx=5)
        ctk.CTkButton(topo, text="PDF", fg_color="#7c3aed", hover_color="#6d28d9",
                      command=self.gerar_pdf).pack(side="right", padx=5)
        ctk.CTkButton(topo, text="GERAR ESCALA", fg_color="#059669", hover_color="#047857",
                      command=self.gerar_escala).pack(side="right", padx=5)

        ctk.CTkLabel(
            self,
            text=("SEG–SEX: EXPEDIENTE (com folga compensatória após o serviço)  |  "
                  "FIM DE SEMANA: 2 por turno em apenas UM dia; no próximo fim de semana entra o outro par"),
            font=("Segoe UI", 12, "bold"), text_color="#fbbf24", wraplength=1400,
        ).pack(pady=(0, 8))

        self.grade = ctk.CTkFrame(self)
        self.grade.pack(fill="both", expand=True, padx=15, pady=(0, 15))

    def carregar_pessoas(self):
        self.pessoas = db.listar_militares()

    def contar_turnos(self):
        return (
            sum(p["turno"] == "DIURNO" for p in self.pessoas),
            sum(p["turno"] == "NOTURNO" for p in self.pessoas),
        )

    def abrir_cadastro(self):
        janela = ctk.CTkToplevel(self)
        janela.title("Cadastro de pessoas")
        janela.geometry("850x650")
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
            for widget in lista.winfo_children():
                widget.destroy()
            for pessoa in self.pessoas:
                linha = ctk.CTkFrame(lista)
                linha.pack(fill="x", pady=4)
                ctk.CTkLabel(
                    linha,
                    text=f"{pessoa['nome']} | {pessoa['matricula'] or 'Sem matrícula'} | {pessoa['turno']}",
                ).pack(side="left", padx=10, pady=10)
                ctk.CTkButton(
                    linha, text="Excluir", width=75, fg_color="#991b1b", hover_color="#7f1d1d",
                    command=lambda pid=pessoa["id"]: self.excluir_pessoa(pid, atualizar),
                ).pack(side="right", padx=8)

        ctk.CTkButton(
            janela, text="+ CADASTRAR PESSOA", command=lambda: self.formulario(janela, atualizar)
        ).pack(pady=5)
        atualizar()

    def excluir_pessoa(self, pessoa_id, atualizar):
        if messagebox.askyesno("Confirmar", "Deseja excluir esta pessoa e os registros vinculados?"):
            db.excluir_militar(pessoa_id)
            atualizar()
            self.montar_grade()

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
            nome_valor = nome.get().strip()
            turno_valor = turno.get().strip()
            if not nome_valor:
                messagebox.showerror("Erro", "Informe o nome.", parent=janela)
                return
            if turno_valor not in funcoes.TURNOS:
                messagebox.showerror("Erro", "Selecione um turno válido.", parent=janela)
                return
            self.carregar_pessoas()
            quantidade = sum(p["turno"] == turno_valor for p in self.pessoas)
            if quantidade >= 4:
                messagebox.showwarning("Limite", f"O turno {turno_valor} já possui 4 pessoas.", parent=janela)
                return
            try:
                db.cadastrar_militar(nome_valor, matricula.get(), "Semana + Fim de Semana", turno_valor)
                janela.destroy()
                atualizar()
                self.montar_grade()
            except sqlite3.IntegrityError:
                messagebox.showerror("Cadastro", "Esta matrícula já está cadastrada.", parent=janela)
            except Exception as erro:
                messagebox.showerror("Erro", str(erro), parent=janela)

        ctk.CTkButton(
            janela, text="SALVAR", height=42, fg_color="#059669", hover_color="#047857",
            command=salvar,
        ).pack(fill="x", padx=30)

    def gerar_escala(self):
        self.carregar_pessoas()
        d, n = self.contar_turnos()
        if d != 4 or n != 4:
            messagebox.showwarning(
                "Cadastro incompleto",
                f"Cadastre exatamente 4 pessoas em cada turno. DIURNO: {d}/4 | NOTURNO: {n}/4",
            )
            return
        try:
            registros = funcoes.gerar_escala_automatica(self.pessoas, self.ano, self.mes)
            db.apagar_escala_mes(self.ano, self.mes)
            db.salvar_escala(registros)
            self.montar_grade()
            messagebox.showinfo(
                "Pronto", f"Escala de {MESES[self.mes]} de {self.ano} gerada corretamente."
            )
        except Exception as erro:
            messagebox.showerror("Erro ao gerar escala", str(erro))

    def montar_grade(self):
        for widget in self.grade.winfo_children():
            widget.destroy()
        dados = db.buscar_escala_mes(self.ano, self.mes)
        self.lbl_mes.configure(text=f"{MESES[self.mes]} / {self.ano}")

        for col, dia in enumerate(DIAS):
            self.grade.grid_columnconfigure(col, weight=1, uniform="dia")
            ctk.CTkLabel(
                self.grade, text=dia, font=("Segoe UI", 10, "bold"),
                text_color="#f87171" if col >= 5 else "#93c5fd",
            ).grid(row=0, column=col, sticky="nsew", padx=2, pady=3)

        semanas = calendar.Calendar(firstweekday=0).monthdatescalendar(self.ano, self.mes)
        for linha, semana in enumerate(semanas, start=1):
            self.grade.grid_rowconfigure(linha, weight=1)
            for col, data in enumerate(semana):
                fora = data.month != self.mes
                cor_fundo = "#0b0f16" if fora else ("#24191a" if col >= 5 else "#151a23")
                celula = ctk.CTkFrame(
                    self.grade, fg_color=cor_fundo, border_width=1, border_color="#303642"
                )
                celula.grid(row=linha, column=col, sticky="nsew", padx=2, pady=2)
                ctk.CTkLabel(
                    celula, text=str(data.day), font=("Segoe UI", 10, "bold"),
                    text_color="#64748b" if fora else "#ffffff",
                ).pack(anchor="nw", padx=5, pady=3)
                if fora:
                    continue
                for item in dados.get(data.isoformat(), []):
                    turno_sigla = "D" if item["turno"] == "DIURNO" else "N"
                    situacao = item["situacao"]
                    cor = {
                        "SERVIÇO": "#15803d",
                        "FOLGA COMP.": "#b45309",
                        "EXPEDIENTE": "#1e40af",
                        "FOLGA": "#475569",
                    }.get(situacao, "#475569")
                    ctk.CTkLabel(
                        celula,
                        text=f"{item['nome'][:12]} • {turno_sigla} • {situacao}",
                        font=("Segoe UI", 8), fg_color=cor, corner_radius=3,
                        anchor="w", height=18,
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
            messagebox.showerror("ReportLab", "Instale as bibliotecas com: pip install reportlab")
            return

        self.carregar_pessoas()
        dados = db.buscar_escala_mes(self.ano, self.mes)
        if not dados:
            messagebox.showwarning("Sem escala", "Gere a escala antes de criar o PDF.")
            return

        caminho = filedialog.asksaveasfilename(
            title="Salvar escala em PDF",
            initialfile=f"Escala_{self.ano}_{self.mes:02d}.pdf",
            defaultextension=".pdf",
            filetypes=[("Arquivo PDF", "*.pdf")],
        )
        if not caminho:
            return

        try:
            largura_pagina, _ = landscape(A4)
            margem = 12 * mm
            largura_util = largura_pagina - 2 * margem
            largura_nome = 34 * mm
            dias_mes = calendar.monthrange(self.ano, self.mes)[1]
            largura_dia = (largura_util - largura_nome) / dias_mes

            doc = SimpleDocTemplate(
                caminho,
                pagesize=landscape(A4),
                leftMargin=margem,
                rightMargin=margem,
                topMargin=12 * mm,
                bottomMargin=12 * mm,
                title=f"Escala de Serviço - {MESES[self.mes]} de {self.ano}",
                author="Sistema de Escala de Serviço",
            )

            estilos = getSampleStyleSheet()
            titulo = ParagraphStyle(
                "TituloEscala", parent=estilos["Title"], fontName="Helvetica-Bold",
                fontSize=14, leading=17, alignment=TA_CENTER, spaceAfter=4,
            )
            subtitulo = ParagraphStyle(
                "SubtituloEscala", parent=estilos["Normal"], fontSize=7,
                leading=9, alignment=TA_CENTER, spaceAfter=5,
            )
            cabecalho = ParagraphStyle(
                "CabecalhoDia", parent=estilos["Normal"], fontName="Helvetica-Bold",
                fontSize=5.8, leading=7, textColor=colors.white, alignment=TA_CENTER,
            )
            nome_style = ParagraphStyle(
                "NomePessoa", parent=estilos["Normal"], fontName="Helvetica-Bold",
                fontSize=6.2, leading=7.2, alignment=TA_LEFT,
            )
            celula_style = ParagraphStyle(
                "CelulaDia", parent=estilos["Normal"], fontName="Helvetica-Bold",
                fontSize=6.4, leading=7, alignment=TA_CENTER,
            )

            elementos = [
                Paragraph(f"ESCALA DE SERVIÇO — {MESES[self.mes].upper()} / {self.ano}", titulo),
                Paragraph(
                    "E = Expediente  |  S = Serviço  |  FC = Folga compensatória  |  F = Folga",
                    subtitulo,
                ),
                Spacer(1, 3 * mm),
            ]

            cabecalho_linha = [Paragraph("PESSOA / TURNO", cabecalho)]
            for dia in range(1, dias_mes + 1):
                data = dt.date(self.ano, self.mes, dia)
                cabecalho_linha.append(Paragraph(f"{dia:02d}<br/>{DIAS[data.weekday()]}", cabecalho))
            tabela = [cabecalho_linha]

            codigos_por_pessoa = {}
            for pessoa in self.pessoas:
                linha = [Paragraph(escape(f"{pessoa['nome']} / {pessoa['turno']}"), nome_style)]
                for dia in range(1, dias_mes + 1):
                    data_iso = dt.date(self.ano, self.mes, dia).isoformat()
                    item = next(
                        (registro for registro in dados.get(data_iso, [])
                         if registro["militar_id"] == pessoa["id"]),
                        None,
                    )
                    codigo = {
                        "SERVIÇO": "S",
                        "FOLGA": "F",
                        "FOLGA COMP.": "FC",
                        "EXPEDIENTE": "E",
                    }.get(item["situacao"], "–") if item else "–"
                    linha.append(Paragraph(codigo, celula_style))
                    codigos_por_pessoa[(len(tabela), dia)] = codigo
                tabela.append(linha)

            tabela_pdf = Table(
                tabela,
                colWidths=[largura_nome] + [largura_dia] * dias_mes,
                rowHeights=[9 * mm] + [7.5 * mm] * len(self.pessoas),
                repeatRows=1,
                hAlign="CENTER",
                splitByRow=0,
            )
            estilos_tabela = [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#9ca3af")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (1, 1), (-1, -1), "CENTER"),
                ("LEFTPADDING", (0, 0), (-1, -1), 2),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
            cores = {
                "S": colors.HexColor("#bbf7d0"),
                "FC": colors.HexColor("#fed7aa"),
                "F": colors.HexColor("#e5e7eb"),
                "E": colors.HexColor("#dbeafe"),
            }
            for (linha_idx, dia), codigo in codigos_por_pessoa.items():
                if codigo in cores:
                    estilos_tabela.append(("BACKGROUND", (dia, linha_idx), (dia, linha_idx), cores[codigo]))
            tabela_pdf.setStyle(TableStyle(estilos_tabela))
            elementos.append(tabela_pdf)
            elementos.append(Spacer(1, 4 * mm))
            elementos.append(Paragraph(
                "Regra: cada pessoa trabalha no máximo um dia do fim de semana. "
                "Quem trabalha recebe uma folga compensatória na semana seguinte "
                "e não entra no revezamento do fim de semana imediatamente posterior.",
                subtitulo,
            ))

            doc.build(elementos)
            messagebox.showinfo("PDF", f"PDF criado com sucesso:\n{caminho}")
        except Exception as erro:
            messagebox.showerror("Erro no PDF", str(erro))


if __name__ == "__main__":
    db.iniciar_banco()
    App().mainloop()
