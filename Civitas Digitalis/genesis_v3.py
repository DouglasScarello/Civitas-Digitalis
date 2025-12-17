import time
import random
import sys
import json
import os
import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional

# Importando o Cérebro Real
try:
    from memory_core import MemoryCore
    MEMORY_AVAILABLE = True
except ImportError:
    print("ERRO CRÍTICO: memory_core.py não encontrado.")
    sys.exit(1)

# Configurações de IA
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Arquivos
DATA_FILE = "genesis_save.json"
BOOK_FILE = "genesis_book.md"
GRAVEYARD_FILE = "genesis_graveyard.json"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    GOLD = '\033[33m'
    RESET = '\033[0m'
    GRAY = '\033[90m'

# ==============================================================================
# BIOLOGIA SISTÊMICA v3.0
# ==============================================================================
@dataclass
class BioState:
    glicose: float = 100.0
    integridade: float = 100.0
    dopamina: float = 0.5
    cortisol: float = 0.0
    oxitocina: float = 0.5
    age: int = 0
    generation: int = 1
    
    # Novo na V3: Taxa Metabólica (Quão rápido ele queima energia)
    metabolic_rate: float = 1.0 

    def is_alive(self): return self.integridade > 0

# ==============================================================================
# AGENTE COGNITIVO (RAG ENABLED)
# ==============================================================================
class Agent:
    def __init__(self, name, role, color, base_prompt, generation=1, bio_data=None, evolved_strategy=""):
        self.name = name
        self.role = role
        self.color = color
        self.base_prompt = base_prompt
        self.evolved_strategy = evolved_strategy
        
        # Carrega biologia
        if bio_data:
            # Filtra chaves que não existem no BioState atual para evitar erros de versão
            valid_keys = BioState.__annotations__.keys()
            filtered_bio = {k: v for k, v in bio_data.items() if k in valid_keys}
            self.bio = BioState(**filtered_bio)
        else: 
            self.bio = BioState(generation=generation)
            self._apply_archetype()

        # --- O CÉREBRO REAL ---
        # Conecta ao ChromaDB específico deste agente
        print(f"🔌 Conectando córtex de {self.name}...")
        self.cortex = MemoryCore(self.name)
        
        # Memória de curto prazo (RAM) apenas para fluxo imediato
        self.short_term_buffer = [] 

    def _apply_archetype(self):
        if self.role == "Sobrevivente": 
            self.bio.cortisol = 0.4
            self.bio.metabolic_rate = 1.2 # Ansioso queima mais
        if self.role == "Criativo": 
            self.bio.dopamina = 0.8
        if self.role == "Filósofo": 
            self.bio.metabolic_rate = 0.8 # Calmo gasta menos

    def _roman(self, n):
        return "I" if n==1 else "II" if n==2 else str(n)

    def __str__(self):
        status = "💀" if not self.bio.is_alive() else "❤"
        return (f"{self.color}[{self.name} {self._roman(self.bio.generation)} {status}]{Colors.RESET} "
                f"Glic:{self.bio.glicose:.0f} | Cort:{self.bio.cortisol:.2f} | Meta:{self.bio.metabolic_rate:.1f}")

    def recall_context(self, topic):
        """
        Consulta o ChromaDB para encontrar memórias relevantes sobre o tópico.
        """
        # Custo energético de lembrar (acessar neurônios custa glicose)
        self.bio.glicose -= 0.5
        
        memories = self.cortex.recall_relevant(topic, n_results=3)
        if not memories:
            return "Nenhuma memória relevante encontrada."
        
        context_str = "\n".join([f"- {m}" for m in memories])
        return context_str

    def think(self, topic):
        """
        Processo Cognitivo V3: Recall -> Contextualize -> Generate
        """
        # 1. Recuperação (RAG)
        context = self.recall_context(topic)
        
        # 2. Avaliação de Estado
        sys_mode = "Rápido/Instintivo" if self.bio.glicose < 20 or self.bio.cortisol > 0.7 else "Analítico/Profundo"
        
        # 3. Montagem do Prompt Rico
        full_prompt = (
            f"IDENTIDADE: Você é {self.name}, um {self.role}.\n"
            f"ESTADO BIOLÓGICO: Glicose {self.bio.glicose}%, Cortisol {self.bio.cortisol}%. Modo: {sys_mode}.\n"
            f"MEMÓRIA DE LONGO PRAZO (Contexto relevante):\n{context}\n"
            f"ESTRATÉGIA APRENDIDA: {self.evolved_strategy}\n"
            f"MISSÃO ATUAL: Debater sobre '{topic}'.\n"
            f"Instrução: Use suas memórias passadas para formular sua opinião. Seja coerente com seu histórico."
        )

        # Custo do pensamento (Varia conforme o modo)
        cost = 2.0 if "Rápido" in sys_mode else 5.0
        self.bio.glicose -= cost
        self.bio.metabolic_rate += 0.1 # Pensar aumenta o metabolismo temporariamente

        response = "..."
        if OLLAMA_AVAILABLE:
            try:
                # Temperatura dinâmica: Estresse alto = mais aleatório
                temp = 0.8 if self.bio.cortisol > 0.6 else 0.3
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': full_prompt}], options={'temperature': temp})
                response = res['message']['content'].strip()
            except Exception as e:
                response = f"[Erro Cognitivo]: {e}"

        # 4. Consolidação (Gravar o próprio pensamento no banco)
        self.cortex.store_experience(
            f"Minha opinião sobre {topic}: {response}", 
            type="self_thought", 
            sentiment="neutral",
            cycle=0 # Idealmente passar o ciclo atual aqui
        )
        
        return response, context

    def apply_entropy(self):
        # Entropia baseada na Taxa Metabólica (Feedback Loop)
        decay = 1.0 * self.bio.metabolic_rate
        self.bio.glicose -= decay
        self.bio.age += 1
        
        # Recuperação natural da taxa metabólica (acalmar)
        if self.bio.metabolic_rate > 1.0:
            self.bio.metabolic_rate -= 0.05

        # Crise
        if self.bio.glicose < 15:
            self.bio.cortisol += 0.1
            self.bio.integridade -= 1.5
            self.bio.metabolic_rate += 0.2 # Pânico acelera o coração

# ==============================================================================
# SISTEMA DE ARQUIVOS
# ==============================================================================
def save_system(agents, cycle):
    # Serialização simplificada para o JSON (o cérebro pesado fica no ChromaDB)
    data = {
        "cycle": cycle,
        "agents": [{"name": a.name, "role": a.role, "bio": asdict(a.bio), "evolved_strategy": a.evolved_strategy} for a in agents]
    }
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)

def load_system():
    if not os.path.exists(DATA_FILE): return None, 0
    try:
        with open(DATA_FILE, 'r') as f: data = json.load(f)
        return data, data['cycle']
    except: return None, 0

# ==============================================================================
# ENGINE PRINCIPAL
# ==============================================================================
def main():
    print(f"{Colors.HEADER}=== CIVITAS KERNEL V3.0 (CÓRTEX VETORIAL ATIVO) ==={Colors.RESET}")
    print("Inicializando bancos de dados neurais...")
    
    saved, cycle = load_system()
    
    # Definição dos Agentes
    archetypes = [
        ("Marcus", "Filósofo", Colors.BLUE, "Lógica e Ética."),
        ("Kael", "Sobrevivente", Colors.RED, "Segurança e Cautela."),
        ("Luna", "Criativo", Colors.GREEN, "Arte e Caos.")
    ]

    agents = []
    if saved:
        print("Recuperando bio-estados...")
        for d in saved["agents"]:
            arch = next((a for a in archetypes if a[0] == d["name"]), None)
            if arch: 
                # Note que não carregamos "memories" do JSON, pois elas estão no ChromaDB agora
                ag = Agent(arch[0], arch[1], arch[2], arch[3], 
                           generation=d["bio"].get("generation", 1), 
                           bio_data=d["bio"], 
                           evolved_strategy=d.get("evolved_strategy", ""))
                agents.append(ag)
    else:
        print("Gênese inicial...")
        for a in archetypes: agents.append(Agent(a[0], a[1], a[2], a[3]))

    try:
        while True:
            cycle += 1
            print(f"\n{Colors.HEADER}--- CICLO {cycle} ---{Colors.RESET}")
            
            # 1. Entropia
            active = []
            for ag in agents:
                ag.apply_entropy()
                print(ag)
                if ag.bio.is_alive(): active.append(ag)
                else: print(f"{Colors.RED}† {ag.name} cessou funções.{Colors.RESET}")
            
            if len(active) < 2:
                print("Civilização colapsou. Reiniciando matriz...")
                break

            # 2. Debate com Memória Real
            hungry = sorted([a for a in active if a.bio.glicose < 60], key=lambda x: x.bio.glicose)
            
            if hungry:
                speaker = hungry[0]
                topic = random.choice(["O Medo", "A Confiança", "O Passado", "A Escassez"])
                
                print(f"\n{Colors.GOLD}>> DEBATE: '{topic}'{Colors.RESET}")
                print(f"{Colors.GRAY}Processando contexto neural...{Colors.RESET}")
                
                # O Pensamento (Agora com RAG)
                thought, context_used = speaker.think(topic)
                
                print(f"{speaker.color}{speaker.name}:{Colors.RESET} \"{thought}\"")
                print(f"{Colors.GRAY}[Memória Usada]:\n{context_used}{Colors.RESET}")
                
                # Recompensa simples por enquanto (Foco no cérebro)
                speaker.bio.glicose += 30
                print(f"{Colors.GREEN}>> Energia restaurada (+30){Colors.RESET}")
            
            else:
                print("Silêncio reflexivo.")

            if cycle % 5 == 0: save_system(agents, cycle)
            time.sleep(2)

    except KeyboardInterrupt:
        save_system(agents, cycle)
        print("\nSistema salvo.")

if __name__ == "__main__":
    main()
