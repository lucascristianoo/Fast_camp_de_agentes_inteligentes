#Abaixo temos a classe FastAPI da biblioteca fastapi, a qual é um framework para APIs REST, já o BaseModel da biblioteca pydantic é responsável por ajudar a criar modelos de dados (validação e parsing de dados JSON). Além disso também temos que destacar as classes do crew ai Crew, Process, Agent, Task, LLM sendo importadas respectivamente para coordenar a equipe, definir como ela deve operar, construção de agentes,construção de tasks e usar modelos alternativos ao padrão da OpenAi, assim como também temos a SerperDevTool do crewai_tools para realizar buscas na web e load_dotenv de dotenv para carregar as variáveis ambientes.

import os
from fastapi import FastAPI
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process, LLM
from crewai_tools import SerperDevTool
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()
gemini_api_key = os.getenv('GOOGLE_API_KEY')
llm = LLM(model='gemini/gemini-1.5-flash',
api_key=gemini_api_key)
serper_api_key = os.getenv('SERPER_DEV_API_KEY')

#Abaixo temos a classe obRequirements, que define um atributo obrigatório chamado job_requirements que deve ser uma string, logo quando enviar um JSON para a API deve ser no formato de string

class JobRequirements(BaseModel):
    job_requirements: str

# Abaixo temos a variável search_tool que usa a classe SeperDevTool para realizar buscas na web, essa tool é usada pelo agente researcher, variável essa que que t6em como objetivo é encontrar os melhores profissionais com base nos requisitos da vaga, orientando todo o seu comportamento. Vale ressaltar que podemos ver seus pensamentos pois verbose está como true e ele é capaz de armazenar informações, pois memory também está como true.

search_tool = SerperDevTool()
researcher = Agent(
    role='Recrutador Senior de Dados',
    goal='Encontrar os melhores perfis de dados para trabalhar baseado nos requisitos da vaga',
    verbose=True,
    memory=True,
    backstory=(
        'Experiência na área de dados e formação acadêmica em Recursos Humanos e '
        'especialista em LinkedIn, tem domínio das principais táticas de busca de profissionais.'
    ),
    tools=[search_tool],
    llm=llm
)

#Abaixo temos a criação de uma rota de API com @app.post("/research_candidates"), o qual é do tipo post para requisições, a qual como podemos ver pelo req: recebe um json com a string JobRequirements, a qual é uma variável que faz parte da descrição da tarefa em si, a qual é realizda pelo researcher usando a search_tool. A saída esperada da tarefa é é uma lista com os 5 principais candidatos potenciais. Após esse trecho temos a variável crew que executa a tarefa sequencial com nosso único agente e tarefa atribuida para ele.
@app.post("/research_candidates")
async def research_candidates(req: JobRequirements):
    research_task = Task(
        description=(
            f'Realizar pesquisas completas para encontrar candidatos em potencial para o cargo especificado'
            f'Utilize vários recursos e bancos de dados online para reunir uma lista abrangente de candidatos em potencial.'
            f'Garanta que o candidato atenda os requisitos da vaga. Requisitos da vaga: {req.job_requirements}'
        ),
        expected_output="""Uma lista com top 5 candidatos potenciais separada por Bullet points, cada candidato deve
                        conter informações de contato e breve descrição do perfil destacando a sua qualificação para a vaga.
                        Trazer junto a url para encontrar o perfil do candidato.""",
        tools=[search_tool],
        agent=researcher
    )

    crew = Crew(
        agents=[researcher],
        tasks=[research_task],
        process=Process.sequential
    )
    result = crew.kickoff(inputs={'job_requirements': req.job_requirements})
    return {'result': result}
#Já essa última parte serve para inicializar o servidor da API com o Uvicorn
if __name__ == "__main__":
    import uvicorn
    print('>>>>>>>>>>>>>>>>>>> version V0.0.1')
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    server.run()