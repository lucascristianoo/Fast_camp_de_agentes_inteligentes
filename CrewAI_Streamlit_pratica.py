# A ideia para essa aplicação é pegar como base o código da aula "How to Implement a Simple UI for CrewAI applications"
# e produzir um fluxo de agentes que planeje um mapa de estudo de qualquer tema.
# O fluxo tem como objetivo um agente pesquisar sobre determinado tema e um segundo agente produzir um cronograma.
# A priori, para fins de teste, vou elaborar um cronograma para estudar matemática para o ENEM.
# Além disso, acho que é conveniente criar uma função que mostre a data de hoje para que ele possa usar como base 
# para dar uma estimativa de dias até o dia da prova.

# Abaixo temos as classes do CrewAI: Crew, Process, Agent, Task e LLM sendo importadas respectivamente para:
# coordenar a equipe, definir como ela deve operar, construção de agentes, construção de tasks e usar modelos alternativos ao padrão da OpenAI.
# Já sobre langchain_core temos BaseCallbackHandler, que é uma classe base para criar callbacks personalizadas.
# E por fim em typing temos TYPE_CHECKING (para evitar importações em tempo de execução), Any (tipo genérico), 
# Dict (dicionário tipado) e Optional (valor que pode ou não existir).

import streamlit as st
from crewai import Crew, Process, Agent, Task, LLM
from langchain_core.callbacks import BaseCallbackHandler
from crewai_tools import SerperDevTool
from dotenv import load_dotenv
from datetime import datetime
from typing import Any, Dict
import os

# Carrega variáveis de ambiente
load_dotenv()
gemini_api_key = os.getenv('GOOGLE_API_KEY')
serper_key = os.getenv('SERPER_DEV_API_KEY')

llm = LLM(model='gemini/gemini-1.5-flash', api_key=gemini_api_key)
search_tool = SerperDevTool()

# Abaixo temos a variável avatars que define os ícones que serão exibidos no Streamlit para cada agente.
# Logo em seguida temos a classe MyCustomHandler que é um callback personalizado onde:
# - exibe "Thinking..." quando o fluxo começa a responder (on_chain_start)
# - exibe a resposta formatada com nome e avatar do agente ao finalizar (on_chain_end)
avatars = {
    "Pesquisador": "https://cdn-icons-png.flaticon.com/512/3208/3208723.png",  
    "Planejador": "https://cdn-icons-png.flaticon.com/512/3094/3094880.png"   
}

class MyCustomHandler(BaseCallbackHandler):
    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name

    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        st.session_state.messages.append({"role": "assistant", "content": inputs['input']})
        st.chat_message("assistant").write(inputs['input'])

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        st.session_state.messages.append({"role": self.agent_name, "content": outputs['output']})
        st.chat_message(self.agent_name, avatar=avatars[self.agent_name]).write(outputs['output'])

# Abaixo temos o agente Pesquisador, o qual pesquisa os tópicos mais importantes para o tema da prova.
# Ele pode usar sua ferramenta de busca para procurar essas informações.
# Já o Planejador monta o cronograma com base nos tópicos e no tempo disponível até a data da prova.
# Ambos os agentes usam callbacks personalizados para exibir as mensagens com "Thinking..." e respostas com avatar.

pesquisador = Agent(
    role='Pesquisador de Conteúdo',
    backstory="Você é especialista em vestibulares. Seu papel é identificar os conteúdos mais importantes para a prova {prova}.",
    goal="Pesquisar os tópicos principais sobre o tema {tema} e indicar boas referências.",
    llm=llm,
    tools=[search_tool],
    callbacks=[
        MyCustomHandler("Pesquisador").on_chain_end,
        MyCustomHandler("Pesquisador").on_chain_start
    ]
)

planejador = Agent(
    role='Planejador de Cronograma',
    backstory="Você cria cronogramas de estudo eficientes com base nos tópicos sugeridos e nos dias disponíveis até {data_final}.",
    goal="Montar um plano diário de estudos claro, equilibrado e motivador.",
    llm=llm,
    callbacks=[MyCustomHandler("Planejador").on_chain_end]
)


# Exibe o título do app e estiliza com HTML e CSS
st.title("📚 Cronograma de Estudos com Agentes Inteligentes")
st.markdown("""
<style>
.chat-bubble {
    border-radius: 12px;
    padding: 12px;
    margin: 8px 0;
}
.pesquisador-msg {
    background-color: #e3f2fd;
    border-left: 5px solid #2196f3;
}
.planejador-msg {
    background-color: #f1f8e9;
    border-left: 5px solid #8bc34a;
}
</style>
""", unsafe_allow_html=True)

# Exibe o título do app e garante que a lista de mensagens exista.
# Se for o primeiro uso, exibe uma mensagem de boas-vindas.
if "messages" not in st.session_state:
    st.session_state["messages"] = [{
        "role": "assistant",
        "content": "Digite o tema de estudo e a data final para o cronograma que deseja receber!"
    }]

# Exibe o histórico de mensagens
for msg in st.session_state.messages:
    estilo = ""
    if msg["role"] == "Pesquisador":
        estilo = "pesquisador-msg"
    elif msg["role"] == "Planejador":
        estilo = "planejador-msg"
    st.markdown(f'<div class="chat-bubble {estilo}">{msg["content"]}</div>', unsafe_allow_html=True)

# Formulário onde o usuário informa o tema de estudo, data final e nome da prova
with st.form("formulario"):
    tema = st.text_input("Tema de estudo", value="Física") # O retângulo vêm autopreenchido com Física
    data_final = st.date_input("Data final do estudo")
    prova = st.text_input("Nome da prova", value="ENEM")  # O retângulo vêm autopreenchido com ENEM
    enviar = st.form_submit_button("Criar Cronograma")

# Ao enviar o formulário, calcula-se os dias restantes
if enviar and tema and data_final:
    hoje = datetime.now().date()
    dias_restantes = (data_final - hoje).days

    if dias_restantes <= 0:
        st.error("⚠️ A data final precisa ser no futuro!")
    else:
        st.session_state.messages.append({
            "role": "user",
            "content": f"Quero estudar {tema} para o {prova} até {data_final}."
        })
        st.chat_message("user").write(
            f"📘 Tema: **{tema}**\n📅 Prova: **{prova}**\n⏳ Dias disponíveis: **{dias_restantes}**"
        )

        # As tasks são criadas dinamicamente com base nas entradas do usuário sobre o tema, dias_restante e a data final da prova
        task1 = Task(
            description=f"""Liste os principais tópicos de estudo sobre: {tema}. Use provas anteriores, editais e fontes confiáveis.""",
            agent=pesquisador,
            expected_output="Lista detalhada dos tópicos + referências úteis."
        )

        task2 = Task(
            description=f"""Com base nos tópicos listados e considerando {dias_restantes} dias até {data_final}, monte um cronograma de estudos diário equilibrado para o tema: {tema}.""",
            agent=planejador,
            expected_output="Cronograma de estudos em formato diário."
        )

        crew = Crew(
            agents=[pesquisador, planejador],
            tasks=[task1, task2],
            process=Process.sequential,
            manager_llm=llm
        )

        resultado = crew.kickoff(inputs={
            "tema": tema,
            "prova": prova,
            "data_final": str(data_final)
        })

        resposta_final = f"## 🧠 Cronograma Gerado\n\n{resultado}"
        st.session_state.messages.append({"role": "assistant", "content": resposta_final})
        st.chat_message("assistant").write(resposta_final)