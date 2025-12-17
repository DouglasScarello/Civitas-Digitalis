#!/bin/bash

CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=== CIVITAS DIGITALIS V3.0 (RAG/CHROMA) ===${NC}"

# Verifica ambiente virtual
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Ambiente não encontrado. Execute os passos anteriores."
    exit 1
fi

# Instala dependências se necessário (garantia)
pip install chromadb sentence-transformers ollama > /dev/null 2>&1

if [ ! -f "genesis_v3.py" ]; then
    echo "Erro: genesis_v3.py não encontrado."
    exit 1
fi

python3 genesis_v3.py
