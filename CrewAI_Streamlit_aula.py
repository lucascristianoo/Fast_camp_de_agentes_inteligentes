#How to Implement a Simple UI for CrewAI applications

#Abaixo temos as classes do crew ai Crew, Process, Agent, Task, LLM sendo importadas respectivamente para coordenar a equipe, definir como ela deve operar, construção de agentes,construção de tasks e usar modelos alternativos ao padrão da OpenAi. Já sobre langchain_core temos BaseCallbackHandler que é uma classe base para criar callbacks personalizadas e por fim em typing temos TYPE_CHECKING, o qual é usado para evitar importações em tempo de execução e só carregar módulos para type hints, Any que aceita qualquer tipo de dado, Dict que é um dicionário com chave e valor tipados e Optional que é um valor que pode ser do tipo especificado

import streamlit as st
from crewai import Crew, Process, Agent, Task, LLM
from langchain_core.callbacks import BaseCallbackHandler
from typing import TYPE_CHECKING, Any, Dict, Optional
from dotenv import load_dotenv
import os

load_dotenv()
gemini_api_key = os.getenv('GOOGLE_API_KEY')
llm = LLM(model='gemini/gemini-1.5-flash',
api_key=gemini_api_key)

#Abaixo temos a variável avators que define os icones que serão exibidos no streamlit para cada agente. Logo em seguida temos a classe MyCustomHandler que é um callback personalizado onde exibe "Thinking..." quando o fluxo começa a responder em def on_chain_start e em def on_chain_end busca o nome do agente que respondeu, usa um avatar para ele e gera o texto em markdown para ser exibido

avators = {"Writer":"https://cdn-icons-png.flaticon.com/512/320/320336.png",
            "Reviewer":"https://cdn-icons-png.freepik.com/512/9408/9408201.png"}

class MyCustomHandler(BaseCallbackHandler):


    def __init__(self, agent_name: str) -> None:
        self.agent_name = agent_name

    def on_chain_start(
        self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any
    ) -> None:
        """Print out that we are entering a chain."""
        st.session_state.messages.append({"role": "assistant", "content": inputs['input']})
        st.chat_message("assistant").write(inputs['input'])

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Print out that we finished a chain."""
        st.session_state.messages.append({"role": self.agent_name, "content": outputs['output']})
        st.chat_message(self.agent_name, avatar=avators[self.agent_name]).write(outputs['output'])

#Abaixo temos o agente writer que têm como objetivo avaliar o conteúdo escrito e sugerir melhorias. Sobre o agente esse possui uma especialização em blog de viagens e executa o callback  MyCustomHandler que é um callback personalizado onde exibe "Thinking..., ou seja, vai exibir isso antes de sair a resposta.

writer = Agent(
    role='Blog Post Writer',
    backstory='''You are a blog post writer who is capable of writing a travel blog.
                      You generate one iteration of an article once at a time.
                      You never provide review comments.
                      You are open to reviewer's comments and willing to iterate its article based on these comments.
                      ''',
    goal="Write and iterate a decent blog post.",
    # tools=[]  # This can be optionally specified; defaults to an empty list
    llm=llm,
    callbacks=[MyCustomHandler("Writer").on_chain_end,MyCustomHandler("Writer").on_chain_start],
)

#Abaixo temos o reviewer que tem como objetivo avaliar o conteúdo escrito e sugerir melhorias. Onde também há o uso similar de  MyCustomHandler para exibir "Thinking...

reviewer = Agent(
    role='Blog Post Reviewer',
    backstory='''You are a professional article reviewer and very helpful for improving articles.
                 You review articles and give change recommendations to make the article more aligned with user requests.
                 You will give review comments upon reading entire article, so you will not generate anything when the article is not completely delivered.
                  You never generate blogs by itself.''',
    goal="list builtins about what need to be improved of a specific blog post. Do not give comments on a summary or abstract of an article",
    # tools=[]  # Optionally specify tools; defaults to an empty list
    llm=llm,
    # Provide the on_chain_end method as the callback
    callbacks=[MyCustomHandler("Reviewer").on_chain_end],
)

#Abaixo temos a criação de um título para o app em st.title("💬 CrewAI Writing Studio") e após isso temos a garantia de que a lista de mensagens existe em if "messages" not in st.session_state: e além disso há no inicio uma saudação se for o primeiro uso. Também vale ressaltar a exibição de mensagens passadas como um histórico em for msg in st.session_state.messages:.

st.title("💬 CrewAI Writing Studio")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "What blog post do you want us to write?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

#Por fim temos a captura do input do usuário em if prompt := st.chat_input(): e a criação das tasks onde a primeira atribui para o writter que ele deve escrever um artigo de no máximo 300 palavras e a segunda que o reviewer deve sugerir melhorias no texto anterior para torná-lo viral. Vale um destaque também para o trecho result = f"## Here is the Final Result \n\n {final}"st .. onde temos o resultado final para o usuário e adiciona ao histórico.

if prompt := st.chat_input():

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    task1 = Task(
      description=f"""Write a blog post of {prompt}. """,
      agent=writer,
      expected_output="an article under 300 words."
    )

    task2 = Task(
      description="""list review comments for improvement from the entire content of blog post to make it more viral on social media""",
      agent=reviewer,
      expected_output="Builtin points about where need to be improved."
    )
    # Establishing the crew with a hierarchical process
    project_crew = Crew(
        tasks=[task1, task2],  # Tasks to be delegated and executed under the manager's supervision
        agents=[writer, reviewer],
        process=Process.hierarchical,
        manager_llm=llm
    )
    final = project_crew.kickoff()

    result = f"## Here is the Final Result \n\n {final}"
    st.session_state.messages.append({"role": "assistant", "content": result})
    st.chat_message("assistant").write(result)