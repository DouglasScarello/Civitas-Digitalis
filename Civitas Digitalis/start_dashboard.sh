#!/bin/bash

# Cores
CYAN='\033[0;36m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${CYAN}=== GENESIS: INICIANDO OBSERVATÓRIO ===${NC}"

# 1. Verificar/Criar Ambiente Virtual
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

# 2. Instalar Dependências (Usando pip do venv diretamente)
echo -e "${GREEN}Verificando dependências visuais...${NC}"
./venv/bin/pip install streamlit pandas

# 3. Verificar se o código Python existe
if [ ! -f "genesis_dashboard.py" ]; then
    echo "ERRO: genesis_dashboard.py não encontrado."
    exit 1
fi

# 4. Lançar o Dashboard (Usando streamlit do venv diretamente)
echo -e "${CYAN}Abrindo o portal visual... (Pressione CTRL+C para sair)${NC}"
./venv/bin/streamlit run genesis_dashboard.py
