#!/bin/bash

CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}=== GENESIS KERNEL v2.1 (DEFINITIVE EDITION) ===${NC}"
echo "Carregando Especificações do Documento Zero Cost v2.0..."

if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Configurando ambiente..."
    python3 -m venv venv
    source venv/bin/activate
    pip install ollama
fi

if [ ! -f "genesis_ultimate.py" ]; then
    echo "Erro: genesis_ultimate.py não encontrado."
    exit 1
fi

python3 genesis_ultimate.py
