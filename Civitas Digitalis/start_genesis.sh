#!/bin/bash

# Cores para o terminal
GREEN='\033[0;32m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${CYAN}=== INICIALIZADOR PROJETO GENESIS (Linux/Manjaro) ===${NC}"

# 1. Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERRO] Python 3 não encontrado. Instale-o com 'sudo pacman -S python'.${NC}"
    exit 1
fi

# 2. Criar Ambiente Virtual (Recomendado para não poluir o sistema)
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Criando ambiente virtual Python (venv)...${NC}"
    python3 -m venv venv
fi

# 3. Ativar Ambiente Virtual
source venv/bin/activate

# 4. Instalar biblioteca Ollama (se necessário)
if ! pip show ollama &> /dev/null; then
    echo -e "${GREEN}Instalando biblioteca 'ollama' via pip...${NC}"
    pip install ollama
else
    echo -e "${GREEN}Biblioteca 'ollama' já instalada.${NC}"
fi

# 5. Verificar se o script Python existe (Nome atualizado para v2)
if [ ! -f "genesis_v2.py" ]; then
    echo -e "${RED}[ERRO] O arquivo 'genesis_v2.py' não foi encontrado nesta pasta.${NC}"
    echo "Por favor, certifique-se de que o arquivo Python do projeto esteja nomeado como 'genesis_v2.py'."
    exit 1
fi

# 6. Rodar o Sistema
echo -e "${CYAN}Iniciando a Sociedade Bio-Digital (Fase 7: Gerações)...${NC}"
echo -e "Pressione CTRL+C para encerrar."
echo "---------------------------------------------------"

python3 genesis_society_generations.py

# Desativar venv ao sair
deactivate
