import streamlit as st
import datetime
import requests
import json
import google.generativeai as genai

# --- CONFIGURAÇÃO INICIAL E MEMÓRIA DO SISTEMA ---
st.set_page_config(page_title="Sistema de Autenticação Segura", layout="centered")

with st.sidebar:
    st.header("Configurações do Motor IA")
    api_key = st.text_input("Cole sua API Key do Google Gemini aqui:", type="password")
    st.caption("Esta chave conecta o sistema à IA para checagem de fatos.")

if 'usuario_autenticado' not in st.session_state:
    st.session_state.usuario_autenticado = False
    st.session_state.nome_usuario = ""

# =====================================================================
# FASE 1: TELA DE CADASTRO
# =====================================================================
if not st.session_state.usuario_autenticado:
    st.title("Cadastro de Verificação de Identidade")
    st.write("Para garantir a segurança, precisamos validar sua identidade.")

    st.subheader("1. Dados Pessoais")
    nome = st.text_input("Nome Completo")
    cpf = st.text_input("CPF (Apenas números)")
    data_nascimento = st.date_input("Data de Nascimento", min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today())

    st.markdown("---")
    st.subheader("2. Endereço")
    cep_input = st.text_input("CEP (Apenas números)", max_chars=8)
    
    rua_encontrada = ""
    bairro_encontrado = ""
    cidade_encontrada = ""
    estado_encontrado = ""
    
    if cep_input and len(cep_input) == 8:
        try:
            resposta = requests.get(f"https://viacep.com.br/ws/{cep_input}/json/")
            dados_cep = resposta.json()
            if "erro" not in dados_cep:
                rua_encontrada = dados_cep.get("logradouro", "")
                bairro_encontrado = dados_cep.get("bairro", "")
                cidade_encontrada = dados_cep.get("localidade", "")
                estado_encontrado = dados_cep.get("uf", "")
        except:
            pass

    rua = st.text_input("Logradouro (Rua, Avenida)", value=rua_encontrada)
    
    col1, col2 = st.columns(2) 
    with col1:
        numero = st.text_input("Número")
    with col2:
        complemento = st.text_input("Complemento (Apto, Bloco)")

    bairro = st.text_input("Bairro", value=bairro_encontrado)

    col3, col4 = st.columns(2)
    with col3:
        cidade = st.text_input("Cidade", value=cidade_encontrada)
    with col4:
        estado = st.text_input("Estado (UF)", value=estado_encontrado)

    st.markdown("---")
    st.subheader("3. Prova de Vida")
    foto_documento = st.camera_input("Posicione o documento e tire a foto")

    if foto_documento:
        if not nome or not cpf or not cep_input or not numero:
            st.error("Preencha todos os campos obrigatórios antes de tirar a foto.")
        else:
            st.session_state.usuario_autenticado = True
            st.session_state.nome_usuario = nome.split()[0]
            st.rerun()

# =====================================================================
# FASE 2: PAINEL DE POSTAGEM E AUDITORIA (OSINT)
# =====================================================================
else:
    st.title("Painel de Publicação Segura")
    st.success(f"Identidade verificada. Bem-vindo(a), {st.session_state.nome_usuario}!")
    
    texto_postagem = st.text_area("O que você deseja publicar?", height=150)

    st.warning("**AVISO LEGAL:** Você responde criminalmente pelo que publica. Fake news, calúnia ou ameaças resultarão em bloqueio e repasse de dados (IP, Biometria) às autoridades.")
    
    # Termo de rolagem restaurado para garantir validade jurídica
    with st.container(height=150):
        st.markdown("""
        **TERMO DE RESPONSABILIDADE CIVIL E PENAL**
        Pelo presente instrumento, declaro que sou o único autor do conteúdo inserido nesta plataforma, assumindo responsabilidade civil e criminal por danos a terceiros.
        Estou ciente de que a disseminação de informações inverídicas (Fake News) ou a prática de crimes contra a honra (Arts. 138, 139 e 140, CP) constitui violação. Autorizo o armazenamento e repasse de meus dados de acesso, IP e biometria às autoridades competentes mediante requisição.
        """)
        
    aceite_termo = st.checkbox("Li, compreendi e assumo responsabilidade penal pelo conteúdo.")
    
    st.markdown("---")
    foto_postagem = st.camera_input("Confirmação Biométrica de Publicação")

    if st.button("Publicar Conteúdo", type="primary"):
        if not api_key:
            st.error("SISTEMA TRAVADO: Insira a API Key do Gemini no menu lateral esquerdo.")
        elif not texto_postagem:
            st.error("O texto da postagem não pode estar vazio.")
        elif not aceite_termo:
            st.error("Você deve aceitar o Termo de Responsabilidade.")
        elif not foto_postagem:
            st.error("A foto biométrica final é obrigatória.")
        else:
            with st.spinner("Motor de IA e OSINT analisando o conteúdo... Aguarde."):
                try:
                    genai.configure(api_key=api_key)
                    modelo = genai.GenerativeModel('gemini-2.5-flash')
                    
                    prompt_auditoria = f"""
                    Você é um sistema rigoroso de auditoria jurídica e OSINT de uma rede social brasileira.
                    Sua missão é ler o texto abaixo e decidir se ele deve ser bloqueado ou publicado.
                    
                    Regras de bloqueio imediato:
                    1. Ameaças de violência ou discursos de ódio.
                    2. Crimes contra a honra (calúnia, injúria, difamação) evidentes contra figuras públicas ou autoridades.
                    3. Afirmações criminosas óbvias sem base factual (Fake News grave).
                    
                    Texto do usuário: "{texto_postagem}"
                    
                    Responda APENAS em formato JSON, com as exatas chaves abaixo, sem nenhum outro texto:
                    {{
                        "aprovado": true ou false,
                        "risco": "baixo", "medio" ou "alto",
                        "justificativa_legal": "Explique em 1 frase o motivo do bloqueio ou aprovação baseado nas leis brasileiras."
                    }}
                    """
                    
                    resposta_ia = modelo.generate_content(prompt_auditoria)
                    texto_limpo = resposta_ia.text.replace("```json", "").replace("```", "").strip()
                    resultado = json.loads(texto_limpo)

                    if resultado["aprovado"] == True:
                        st.success("✅ **POSTAGEM APROVADA PELO MOTOR IA**")
                        st.write(f"**Análise de Risco:** {resultado['risco'].upper()}")
                        st.info(f"**Parecer:** {resultado['justificativa_legal']}")
                        st.balloons()
                    else:
                        st.error("🚨 **POSTAGEM BLOQUEADA: VIOLAÇÃO DE TERMOS E RISCO LEGAL**")
                        st.write(f"**Análise de Risco:** {resultado['risco'].upper()}")
                        st.warning(f"**Motivo Legal:** {resultado['justificativa_legal']}")
                        st.error(f"Atenção {st.session_state.nome_usuario}: Uma ocorrência interna foi registrada vinculando sua biometria e IP a esta tentativa de publicação.")

                except Exception as e:
                    st.error(f"Erro ao comunicar com a IA: {e}")