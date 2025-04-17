# Importação de streamlit para criar a interface da aplicação web de forma interativa, importação de requests para enviar requisições HTTP para a API que vai buscar os candidatos, time para medir o tempo de execução da busca dos candidatos e send_email usada para enviar o e-mail com os resultados.

import streamlit as st
import requests
import time
from sendmail import send_email  

# Abaixo temos uma função que realiza uma requisição POST para um servidor local (http://127.0.0.1/research_candidates) com os requisitos do job passados como argumento e se for bem sucedida retorna 200.

def search_jobs(requirements):
    url = 'http://127.0.0.1/research_candidates'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }
    data = {
        'job_requirements': f'{requirements}'
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()
    else:
        return None


# Abaixo temos a configuração do streamlit, onde há inicialmente o título da página como "Pesquisa de Jobs", em seguida cria-se um campo de entrada de texto onde o usuário pode inserir os requisitos do job, abaixo temos button1_clicked para buscar e button2_clicked para atuar , logo  em seguida um botão busca definido que quando apertado chama search_jobs
def main():
    st.title("Pesquisa de Jobs")
    requirements = st.text_input("Digite os requisitos do job:")

    # Inicializa estados da sessão
    if 'button1_clicked' not in st.session_state:
        st.session_state.button1_clicked = False
    if 'button2_clicked' not in st.session_state:
        st.session_state.button2_clicked = False
    if 'results' not in st.session_state:
        st.session_state.results = None

    # Botão de busca
    if st.button('Buscar'):
        st.session_state.button1_clicked = True
        st.session_state.button2_clicked = False
        st.session_state.results = None  # Reseta resultados antes de nova busca

    if st.session_state.button1_clicked:
        start_time = time.time()
        with st.spinner("Buscando os melhores candidatos..."):
            gif_placeholder = st.empty()
            gif_placeholder.text("Carregando...")
            results = search_jobs(requirements)
            st.session_state.results = results  # Armazena resultados no session_state
            end_time = time.time()  
            elapsed_time = end_time - start_time  

            if results:
                gif_placeholder.empty()  
                st.markdown("<h3 style='color:green;'>Busca Finalizada!</h3>", unsafe_allow_html=True)
                st.write("Top 5 Candidatos:")
                st.write(f"{results['result']['raw']}")

                st.write(f"Tokens Usados: {results['result']['token_usage']['total_tokens']}")
                st.write(f"Total de requisições: {results['result']['token_usage']['successful_requests']}")
                st.write(f"Tempo de execução: {elapsed_time:.2f} segundos")
            else:
                st.error("Não foi possível obter resultados.")
    
    # Campo de entrada de email e botão de envio
    email_input = st.text_input("Digite o email do destinatário:", key="email")
    if st.button('Enviar Email'):
        st.session_state.button2_clicked = True
        st.session_state.button1_clicked = False

    if st.session_state.button2_clicked:
        if email_input:
            if st.session_state.results and 'result' in st.session_state.results and 'raw' in st.session_state.results['result']:
                send_email(email_input, st.session_state.results['result']['raw'])
                st.markdown("<h3 style='color:green;'>Email enviado!</h3>", unsafe_allow_html=True)
            else:
                st.error("Erro: Nenhum resultado disponível para enviar. Realize uma busca primeiro.")

if __name__ == '__main__':
    main()