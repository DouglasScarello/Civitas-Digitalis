import streamlit as st
import json
import pandas as pd
import time
import os

# ==============================================================================
# CONFIGURAÇÃO VISUAL (Estilo Sci-Fi)
# ==============================================================================
st.set_page_config(
    page_title="Genesis: Observatório Bio-Digital",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS Customizado para imersão (Dark Mode + Neon)
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e6e6e6; }
    .stProgress > div > div > div > div { background-color: #00ff41; }
    div[data-testid="metric-container"] {
        background-color: #1f2937;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #374151;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .agent-card {
        background-color: #262730;
        padding: 15px;
        border-radius: 8px;
        border-left: 6px solid #444;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    h1, h2, h3 { font-family: 'Courier New', monospace; font-weight: bold; }
    .status-dead { color: #ff4b4b; font-weight: bold; }
    .status-alive { color: #00ff41; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# Arquivos monitorados
DATA_FILE = "genesis_save.json"
BOOK_FILE = "genesis_book.md"
GRAVEYARD_FILE = "genesis_graveyard.json"

# ==============================================================================
# LEITURA DE DADOS
# ==============================================================================
def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r') as f: return json.load(f)
        except: pass
    return None

def load_text(filepath):
    if os.path.exists(filepath):
        with open(filepath, 'r') as f: return f.read()
    return ">> O Livro Sagrado ainda está em branco."

# ==============================================================================
# INTERFACE PRINCIPAL
# ==============================================================================
st.title("🧬 GENESIS: Observatório em Tempo Real")
st.markdown("Monitorando a evolução da sociedade bio-digital no terminal.")

placeholder = st.empty()

# Loop de atualização automática
while True:
    data = load_json(DATA_FILE)
    graveyard = load_json(GRAVEYARD_FILE) or []
    book_content = load_text(BOOK_FILE)
    
    with placeholder.container():
        if not data:
            st.info("📡 Aguardando sinal do Kernel (Inicie './start_genesis.sh' no terminal)...")
            time.sleep(2)
            continue

        # --- KPI's GERAIS ---
        cycle = data.get("cycle", 0)
        agents = data.get("agents", [])
        total_pop = len(agents)
        deaths = len(graveyard)
        
        # Cálculo de Médias
        avg_glic = sum(a['bio']['glicose'] for a in agents) / total_pop if total_pop else 0
        avg_cort = sum(a['bio']['cortisol'] for a in agents) / total_pop if total_pop else 0
        
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        kpi1.metric("Ciclo Atual", cycle)
        kpi2.metric("População Viva", total_pop, delta=f"{total_pop} ativos")
        kpi3.metric("Glicose Média", f"{avg_glic:.1f}%", delta=f"{avg_glic-50:.1f}")
        kpi4.metric("Nível de Estresse (Médio)", f"{avg_cort:.2f}", delta_color="inverse")

        st.markdown("---")

        # --- CARDS DOS AGENTES ---
        st.subheader(f"🦠 Organismos Ativos (Geração {max([a['bio'].get('generation', 1) for a in agents]) if agents else 1})")
        
        if agents:
            cols = st.columns(len(agents))
            for i, agent in enumerate(agents):
                bio = agent['bio']
                role = agent['role']
                
                # Cores por Arquétipo
                border_color = "#888"
                if role == "Sobrevivente": border_color = "#ff4b4b" # Vermelho
                elif role == "Criativo": border_color = "#00ff41"   # Verde
                elif role == "Filósofo": border_color = "#00aaff"   # Azul
                
                with cols[i]:
                    st.markdown(f"""
                    <div class="agent-card" style="border-left-color: {border_color}">
                        <h3>{agent['name']}</h3>
                        <p style="margin:0">🧬 <b>Linhagem:</b> {bio.get('generation', 1)}ª Geração</p>
                        <p style="margin:0">🛡️ <b>Classe:</b> {role}</p>
                        <p style="margin:0">⏳ <b>Idade:</b> {bio['age']} ciclos</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Barras de Vida
                    g_val = int(max(0, min(100, bio['glicose'])))
                    c_val = int(max(0, min(100, bio['cortisol'] * 100)))
                    
                    st.write(f"**Energia** ({g_val}%)")
                    st.progress(g_val)
                    
                    st.write(f"**Estresse** ({c_val}%)")
                    # Hack para mudar cor da barra de estresse (vermelho se alto)
                    if c_val > 70:
                        st.markdown(f"""<style>div[data-testid="stColumn"]:nth-child({i+1}) .stProgress > div > div > div > div {{ background-color: #ff4b4b; }}</style>""", unsafe_allow_html=True)
                    st.progress(c_val)
                    
                    with st.expander("🧠 Ver Estratégia Mental"):
                        st.caption(agent.get('evolved_strategy', 'Nenhuma estratégia formada.'))

        st.markdown("---")

        # --- HISTÓRICO E CULTURA ---
        c_book, c_grave = st.columns([1, 1])
        
        with c_book:
            st.subheader("📜 O Livro Sagrado")
            st.caption("Dogmas canonizados pela sociedade.")
            st.code(book_content, language="markdown")
            
        with c_grave:
            st.subheader("⚰️ Memorial (Cemitério)")
            if graveyard:
                # Converter para DataFrame para ficar bonito
                df = pd.DataFrame(graveyard)
                if not df.empty:
                    df = df[['name', 'role', 'age', 'cause', 'cycle_of_death']]
                    df.columns = ['Nome', 'Classe', 'Idade', 'Causa Mortis', 'Ciclo']
                    st.dataframe(df, hide_index=True, use_container_width=True)
            else:
                st.info("Nenhuma morte registrada até o momento.")

    time.sleep(1.5)
