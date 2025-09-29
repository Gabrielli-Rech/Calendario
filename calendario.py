import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os
import datetime
from plyer import notification

ARQUIVO_DE_EVENTOS = "eventos.json"

def carregar_eventos():
    """Carrega os eventos do arquivo JSON."""
    if not os.path.exists(ARQUIVO_DE_EVENTOS):
        return []
    with open(ARQUIVO_DE_EVENTOS, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def salvar_eventos(eventos):
    """Salva a lista de eventos no arquivo JSON."""
    with open(ARQUIVO_DE_EVENTOS, 'w', encoding='utf-8') as f:
        json.dump(eventos, f, indent=4, ensure_ascii=False)

class CalendarioApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Configurações da Janela e Tema ---
        self.title("Gerenciador de Eventos Moderno")
        self.geometry("600x650")
        self.resizable(False, False)

        # Define o tema (outras opções: "light", "system")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.eventos = carregar_eventos()
        self.eventos_notificados_hoje = []

        # --- Frame Principal ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(fill="both", expand=True, padx=15, pady=15)

        # --- Lista de Eventos (usando CTkScrollableFrame) ---
        self.frame_lista = ctk.CTkScrollableFrame(self.main_frame, label_text="Meus Eventos", label_font=("Arial", 14, "bold"))
        self.frame_lista.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Frame de Adicionar Evento ---
        self.frame_adicionar = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.frame_adicionar.pack(fill="x", padx=10, pady=(0, 10))

        # --- Layout do Formulário de Adição ---
        self.frame_adicionar.grid_columnconfigure(1, weight=1) # Faz a coluna 1 expandir

        # Nome
        self.label_nome = ctk.CTkLabel(self.frame_adicionar, text="Nome:", font=("Arial", 12))
        self.label_nome.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.entry_nome = ctk.CTkEntry(self.frame_adicionar, placeholder_text="Nome do evento")
        self.entry_nome.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        # Tipo
        self.label_tipo = ctk.CTkLabel(self.frame_adicionar, text="Tipo:", font=("Arial", 12))
        self.label_tipo.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.tipo_evento_var = tk.StringVar(self, "Aniversário")
        self.combobox_tipo = ctk.CTkComboBox(
            self.frame_adicionar,
            values=["Aniversário", "Feriado", "Reunião", "Reunião Semanal"],
            variable=self.tipo_evento_var,
            state="readonly",
            command=self.ao_selecionar_tipo_evento
        )
        self.combobox_tipo.grid(row=1, column=1, sticky="w", padx=10, pady=5)

        # Container para os campos de data
        self.frame_datas = ctk.CTkFrame(self.frame_adicionar, fg_color="transparent")
        self.frame_datas.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.label_dia = ctk.CTkLabel(self.frame_datas, text="Dia:")
        self.entry_dia = ctk.CTkEntry(self.frame_datas, width=60)

        self.label_mes = ctk.CTkLabel(self.frame_datas, text="Mês:")
        self.entry_mes = ctk.CTkEntry(self.frame_datas, width=60)

        self.label_ano = ctk.CTkLabel(self.frame_datas, text="Ano:")
        self.entry_ano = ctk.CTkEntry(self.frame_datas, width=80)

        self.label_dia_semana = ctk.CTkLabel(self.frame_datas, text="Dia da Semana:")
        self.dia_semana_var = tk.StringVar(self, "0-Segunda-feira")
        self.combobox_dia_semana = ctk.CTkComboBox(
            self.frame_datas, variable=self.dia_semana_var,
            values=["0-Segunda-feira", "1-Terça-feira", "2-Quarta-feira", "3-Quinta-feira", "4-Sexta-feira", "5-Sábado", "6-Domingo"],
            state="readonly"
        )

        # Botão Adicionar
        self.btn_adicionar = ctk.CTkButton(self.frame_adicionar, text="Adicionar Evento", command=self.adicionar_evento, font=("Arial", 12, "bold"))
        self.btn_adicionar.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.atualizar_lista_eventos()
        self.ao_selecionar_tipo_evento()

        print("Iniciando verificação de notificações em segundo plano...")
        self.agendar_verificacao_notificacoes()

    def ao_selecionar_tipo_evento(self, choice=None):
        tipo_selecionado = self.tipo_evento_var.get()

        # Oculta todos os widgets de data
        for widget in [self.label_dia, self.entry_dia, self.label_mes, self.entry_mes, self.label_ano, self.entry_ano, self.label_dia_semana, self.combobox_dia_semana]:
            widget.pack_forget()

        if tipo_selecionado in ["Aniversário", "Feriado", "Reunião"]:
            self.label_dia.pack(side="left", padx=(10,0))
            self.entry_dia.pack(side="left", padx=(0,10))
            self.label_mes.pack(side="left", padx=(10,0))
            self.entry_mes.pack(side="left", padx=(0,10))
            if tipo_selecionado == "Reunião":
                self.label_ano.pack(side="left", padx=(10,0))
                self.entry_ano.pack(side="left", padx=(0,10))
        elif tipo_selecionado == "Reunião Semanal":
            self.label_dia_semana.pack(side="left", padx=(10,0))
            self.combobox_dia_semana.pack(side="left", padx=(0,10))

    def atualizar_lista_eventos(self):

        for widget in self.frame_lista.winfo_children():
            widget.destroy()

        dias_semana = {0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"}

        if not self.eventos:
            ctk.CTkLabel(self.frame_lista, text="Nenhum evento cadastrado.", text_color="gray").pack(pady=10)
            return

        for index, evento in enumerate(self.eventos):
            tipo = evento.get("tipo", "")
            nome = evento.get("nome", "Sem nome")
            texto_exibicao = f"{nome} ({tipo})"

            if tipo in ["Aniversário", "Feriado"]:
                data_str = f"{evento.get('dia', '?'):02d}/{evento.get('mes', '?'):02d}"
                texto_exibicao = f"{nome} - {data_str} ({tipo})"
            elif tipo == "Reunião":
                data_str = f"{evento.get('dia', '?'):02d}/{evento.get('mes', '?'):02d}/{evento.get('ano', '?')}"
                texto_exibicao = f"{nome} - {data_str} ({tipo})"
            elif tipo == "Reunião Semanal":
                dia_semana_num = evento.get('dia', -1)
                nome_dia = dias_semana.get(dia_semana_num, "Dia inválido")
                texto_exibicao = f"{nome} - Toda {nome_dia}"

            item_frame = ctk.CTkFrame(self.frame_lista, corner_radius=5)
            item_frame.pack(fill="x", padx=5, pady=5)

            item_label = ctk.CTkLabel(item_frame, text=texto_exibicao, anchor="w")
            item_label.pack(side="left", fill="x", expand=True, padx=10, pady=5)

            delete_button = ctk.CTkButton(item_frame, text="🗑️", width=30, command=lambda idx=index: self.deletar_evento(idx))
            delete_button.pack(side="right", padx=10)

    def deletar_evento(self, indice):
        try:
            evento_selecionado_texto = self.eventos[indice].get("nome", "")
            confirmar = messagebox.askyesno("Confirmar Deleção", f"Você tem certeza que deseja deletar o evento?\n\n'{evento_selecionado_texto}'")
            if confirmar:
                self.eventos.pop(indice)
                salvar_eventos(self.eventos)
                self.atualizar_lista_eventos()
        except IndexError:
            messagebox.showerror("Erro", "Não foi possível deletar o evento selecionado.")

    def adicionar_evento(self):
        nome = self.entry_nome.get().strip()
        tipo = self.tipo_evento_var.get()

        novo_evento = None
        try:
            if tipo in ["Aniversário", "Feriado"]:
                dia = int(self.entry_dia.get().strip())
                mes = int(self.entry_mes.get().strip())
                if not nome: raise ValueError("Nome é obrigatório")
                novo_evento = {"nome": nome, "dia": dia, "mes": mes, "tipo": tipo}
            elif tipo == "Reunião":
                dia = int(self.entry_dia.get().strip())
                mes = int(self.entry_mes.get().strip())
                ano = int(self.entry_ano.get().strip())
                if not nome: raise ValueError("Nome é obrigatório")
                novo_evento = {"nome": nome, "dia": dia, "mes": mes, "ano": ano, "tipo": tipo}
            elif tipo == "Reunião Semanal":
                dia_semana_num = int(self.dia_semana_var.get().split('-')[0])
                if not nome: raise ValueError("Nome é obrigatório")
                novo_evento = {"nome": nome, "dia": dia_semana_num, "tipo": tipo}
        except ValueError as e:
            messagebox.showerror("Erro de Validação", f"Dados inválidos ou faltando. Por favor, verifique os campos.\n({e})")
            return

        if novo_evento:
            self.eventos.append(novo_evento)
            salvar_eventos(self.eventos)

            for entry in [self.entry_nome, self.entry_dia, self.entry_mes, self.entry_ano]:
                entry.delete(0, "end")

            self.atualizar_lista_eventos()
            messagebox.showinfo("Sucesso", f"{tipo} adicionado com sucesso!")

    def agendar_verificacao_notificacoes(self):
        self.verificar_eventos_e_notificar()
        intervalo_ms = 3600 * 1000 
        self.after(intervalo_ms, self.agendar_verificacao_notificacoes)

    def verificar_eventos_e_notificar(self):
        hoje = datetime.date.today()
        if hoje.day != getattr(self, "_ultimo_dia_verificado", 0):
            self.eventos_notificados_hoje = []
            self._ultimo_dia_verificado = hoje.day
        for evento in self.eventos:
            nome_evento = evento.get("nome")
            if nome_evento in self.eventos_notificados_hoje:
                continue
            notificar = False
            titulo = evento.get("tipo", "Evento")
            mensagem = ""
            if evento.get('tipo') in ['Aniversário', 'Feriado']:
                if evento.get('mes') == hoje.month and evento.get('dia') == hoje.day:
                    mensagem = f"Hoje é {evento['tipo'].lower()} de: {nome_evento}! 🎉"
                    notificar = True
            elif evento.get('tipo') == 'Reunião':
                if 'ano' in evento and evento.get('ano') == hoje.year and evento.get('mes') == hoje.month and evento.get('dia') == hoje.day:
                    mensagem = f"Lembrete de evento: {nome_evento}."
                    notificar = True
            elif evento.get('tipo') == 'Reunião Semanal':
                if evento.get('dia') == hoje.weekday():
                    mensagem = f"Lembrete de reunião semanal: {nome_evento}."
                    notificar = True
            if notificar:
                try:
                    notification.notify(title=titulo, message=mensagem, app_name='Calendário de Eventos', timeout=15)
                except Exception as e:
                    print(f"Erro ao enviar notificação: {e}")
                self.eventos_notificados_hoje.append(nome_evento)

if __name__ == "__main__":
    app = CalendarioApp()
    app.mainloop()