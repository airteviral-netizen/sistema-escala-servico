# Sistema de Escala de Serviço

Aplicação desktop em Python para cadastrar integrantes por turno, gerar automaticamente a escala mensal e exportar a escala em PDF.

## Funcionalidades

- Cadastro de até quatro pessoas por turno: **DIURNO** e **NOTURNO**.
- Visualização da escala mensal em uma grade de calendário.
- Geração automática da escala para o mês selecionado.
- Exportação da escala mensal para PDF.
- Armazenamento local dos cadastros e das escalas usando SQLite.

## Regras atuais da escala

- De segunda a sexta-feira, todos ficam em **EXPEDIENTE**, exceto quem estiver em **FOLGA COMP.**.
- Em cada fim de semana, o serviço ocorre em apenas um dos dias: **sábado OU domingo**.
- No dia escolhido, trabalham duas pessoas de cada turno; as demais ficam de folga.
- O par que trabalhou fica fora do revezamento do fim de semana imediatamente seguinte.
- Cada pessoa que trabalhou recebe uma folga compensatória na semana útil seguinte. As folgas do par são distribuídas em dias diferentes: segunda e terça-feira.
- A rotação usa uma data de referência fixa para manter a sequência entre meses e anos.

## Requisitos

- Python 3.10 ou superior.
- Windows com Python instalado e disponível no terminal como `python`.

As bibliotecas externas necessárias estão listadas em `requirements.txt`. O SQLite e o módulo Tkinter normalmente acompanham a instalação padrão do Python para Windows.

## Instalação e execução

Abra o terminal do VS Code na pasta do projeto e execute:

```powershell
python -m pip install -r requirements.txt
python main.py
```

Também é possível iniciar pelo arquivo `INICIAR.bat`, caso ele esteja presente na pasta do projeto.

## Estrutura do projeto

```text
PROJETO ESCALA DE SERVIÇO/
├── main.py             # Interface gráfica e funções principais
├── database.py         # Criação e operações do banco SQLite
├── funcoes.py          # Regras de geração automática da escala
├── requirements.txt    # Dependências Python
├── INICIAR.bat         # Inicialização pelo Windows (opcional)
├── README.md           # Este documento
└── .gitignore          # Arquivos que não devem ser enviados ao Git
```

## Banco de dados e privacidade

O arquivo `escalas.db` é criado localmente pelo sistema quando necessário e contém os cadastros e as escalas. Ele está listado no `.gitignore` de propósito, para evitar publicar nomes, matrículas ou outros dados pessoais no GitHub.

Faça cópias de segurança do banco local. O GitHub guardará o código-fonte, não os dados cadastrados no computador.

## Publicar no GitHub

Depois de criar um repositório vazio no GitHub, configure o endereço remoto e envie o projeto. Os comandos completos estão disponíveis nas instruções de publicação fornecidas junto com este projeto.
