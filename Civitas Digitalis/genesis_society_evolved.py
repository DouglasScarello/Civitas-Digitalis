import time
import random
import sys
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÕES & IMPORTAÇÕES
# ==============================================================================
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

# Cores ANSI
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'   # Marcus
    RED = '\033[91m'    # Kael
    GREEN = '\033[92m'  # Luna
    WARNING = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'

DATA_FILE = "genesis_save.json"

# ==============================================================================
# 1. BIOLOGIA (Serializável)
# ==============================================================================
@dataclass
class BioState:
    glicose: float = 100.0
    integridade: float = 100.0
    dopamina: float = 0.5
    cortisol: float = 0.0
    serotonina: float = 0.5
    age: int = 0  # Ciclos vividos

    def is_alive(self): return self.integridade > 0

# ==============================================================================
# 2. O AGENTE (Com Memória)
# ==============================================================================
class Agent:
    def __init__(self, name, role, color, personality_prompt, bio_data=None):
        self.name = name
        self.role = role
        self.color = color
        self.personality_prompt = personality_prompt
        
        # Carregar biologia salva ou criar nova
        if bio_data:
            self.bio = BioState(**bio_data)
        else:
            self.bio = BioState()
            self._apply_archetype_genetics()

        self.short_term_memory = [] # Últimas 3 falas ouvidas

    def _apply_archetype_genetics(self):
        if self.role == "Sobrevivente": self.bio.cortisol = 0.4
        if self.role == "Criativo": self.bio.dopamina = 0.8
        if self.role == "Filósofo": self.bio.serotonina = 0.8

    def __str__(self):
        status = "💀" if not self.bio.is_alive() else "❤"
        return (f"{self.color}[{self.name} {status}]{Colors.RESET} "
                f"Glic:{self.bio.glicose:.0f}% | Cort:{self.bio.cortisol:.2f} | Idade:{self.bio.age}")

    def listen(self, speaker_name, content):
        """Ouve o que outro agente disse e guarda na memória recente."""
        memory_bit = f"{speaker_name} disse: '{content}'"
        self.short_term_memory.append(memory_bit)
        if len(self.short_term_memory) > 2:
            self.short_term_memory.pop(0)

    def think(self, topic):
        """Gera pensamento considerando o tópico E o que ouviu recentemente."""
        self.bio.glicose -= 4.0 # Pensar cansa
        
        # Contexto do que os outros disseram
        context = ""
        if self.short_term_memory:
            context = "CONTEXTO RECENTE (O que os outros disseram):\n" + "\n".join(self.short_term_memory)

        # Estado Emocional no Prompt
        state_prompt = "ESTADO: CALMO."
        if self.bio.cortisol > 0.6: state_prompt = "ESTADO: MEDO/PARANOIA. Seja defensivo."
        elif self.bio.glicose < 30: state_prompt = "ESTADO: FOME. Você está desesperado."
        elif self.bio.dopamina > 0.7: state_prompt = "ESTADO: EXCITADO. Você está empolgado."

        system_msg = (
            f"Você é {self.name}, um {self.role}. {self.personality_prompt}\n"
            f"{state_prompt}\n"
            f"Responda ao TÓPICO ou rebata o CONTEXTO RECENTE. Seja breve (máx 2 frases)."
        )
        
        user_msg = f"TÓPICO: {topic}\n{context}"

        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[
                    {'role': 'system', 'content': system_msg},
                    {'role': 'user', 'content': user_msg}
                ])
                return res['message']['content']
            except Exception as e:
                return f"Erro neural: {e}"
        return f"Refletindo sobre {topic}..."

    def apply_entropy(self):
        self.bio.age += 1
        loss = 1.5
        
        # Personalidades lidam diferente com estresse
        if self.role == "Filósofo": loss = 1.2 # Gasta menos energia
        
        self.bio.glicose -= loss
        
        # Toxicidade
        if self.bio.glicose < 25.0:
            self.bio.cortisol += 0.04
            self.bio.integridade -= 0.5
        else:
            self.bio.cortisol = max(0.0, self.bio.cortisol - 0.01)

# ==============================================================================
# 3. GERENCIAMENTO DE ESTADO (JSON)
# ==============================================================================
def save_society(agents, cycle):
    data = {
        "cycle": cycle,
        "agents": []
    }
    for ag in agents:
        agent_data = {
            "name": ag.name,
            "role": ag.role,
            "bio": asdict(ag.bio)
        }
        data["agents"].append(agent_data)
    
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"{Colors.GRAY}>> Estado da sociedade salvo em {DATA_FILE}{Colors.RESET}")

def load_society():
    if not os.path.exists(DATA_FILE):
        return None, 0
    
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
        print(f"{Colors.GREEN}>> Save encontrado! Carregando Ciclo {data['cycle']}...{Colors.RESET}")
        return data, data['cycle']
    except:
        return None, 0

# ==============================================================================
# 4. LOOP PRINCIPAL
# ==============================================================================
def main():
    print(f"{Colors.HEADER}=== GENESIS: EVOLUÇÃO (Memória & Debate) ==={Colors.RESET}")
    
    # Tenta carregar save
    saved_data, start_cycle = load_society()
    
    # Definição dos Arquétipos
    archetypes = [
        ("Marcus", "Filósofo", Colors.BLUE, "Busque a verdade lógica."),
        ("Kael", "Sobrevivente", Colors.RED, "Foque em riscos e segurança."),
        ("Luna", "Criativo", Colors.GREEN, "Seja abstrata e artística.")
    ]

    agents = []
    
    # Reconstrói agentes (do save ou do zero)
    if saved_data:
        for ag_data in saved_data["agents"]:
            # Acha a cor e prompt baseados no nome
            arch = next((a for a in archetypes if a[0] == ag_data["name"]), None)
            if arch:
                agents.append(Agent(arch[0], arch[1], arch[2], arch[3], bio_data=ag_data["bio"]))
    else:
        print(f"{Colors.WARNING}>> Criando nova sociedade do zero...{Colors.RESET}")
        for name, role, color, prompt in archetypes:
            agents.append(Agent(name, role, color, prompt))

    cycle = start_cycle
    topics = [
        "A dor é necessária?", "O caos é melhor que a ordem?", 
        "A memória define a identidade?", "Devemos confiar no Oráculo?"
    ]

    try:
        while True:
            cycle += 1
            print(f"\n{Colors.HEADER}--- CICLO {cycle} ---{Colors.RESET}")
            
            # 1. Entropia
            for agent in agents:
                agent.apply_entropy()
                print(agent)
            
            # 2. Oráculo define Tópico
            current_topic = random.choice(topics)
            
            # 3. Debate Dinâmico
            # Quem tem energia < 60% quer falar para ganhar tokens
            speakers = [a for a in agents if a.bio.is_alive() and a.bio.glicose < 60.0]
            
            if speakers:
                print(f"\n{Colors.WARNING}>> ORÁCULO: '{current_topic}'{Colors.RESET}")
                
                # Embaralha para ver quem fala primeiro
                random.shuffle(speakers)
                
                for speaker in speakers:
                    # O agente pensa (considerando o que ouviu antes)
                    print(f"\n{speaker.color}{speaker.name} ({speaker.role}) diz:{Colors.RESET}")
                    thought = speaker.think(current_topic)
                    print(f"\"{thought}\"")
                    
                    # Outros ouvem
                    for other in agents:
                        if other != speaker:
                            other.listen(speaker.name, thought)
                    
                    # Julgamento
                    score = min(10, len(thought.split()) * 0.6) + random.uniform(0, 2)
                    
                    if score > 6.0:
                        reward = 35.0
                        speaker.bio.glicose += reward
                        speaker.bio.cortisol -= 0.2
                        print(f"{Colors.BOLD}>> Aprovado (+{reward} Glicose){Colors.RESET}")
                    else:
                        speaker.bio.cortisol += 0.4
                        print(f"{Colors.RED}>> Ignorado (Estresse sobe){Colors.RESET}")
                    
                    time.sleep(2)
                    
            else:
                print(f"{Colors.GRAY}Sociedade em silêncio...{Colors.RESET}")

            # Salvar a cada 5 ciclos
            if cycle % 5 == 0:
                save_society(agents, cycle)

            time.sleep(1.5)

    except KeyboardInterrupt:
        print("\n\nEncerrando e salvando estado...")
        save_society(agents, cycle)
        print("Até logo.")

if __name__ == "__main__":
    main()
