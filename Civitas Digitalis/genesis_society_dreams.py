import time
import random
import sys
import json
import os
import re
from dataclasses import dataclass, asdict, field
from typing import List

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

DATA_FILE = "genesis_save.json"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'   # Marcus
    RED = '\033[91m'    # Kael
    GREEN = '\033[92m'  # Luna
    WARNING = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'
    PURPLE = '\033[35m' # Cor dos Sonhos

# ==============================================================================
# ESTRUTURAS DE DADOS
# ==============================================================================
@dataclass
class BioState:
    glicose: float = 100.0
    integridade: float = 100.0
    dopamina: float = 0.5
    cortisol: float = 0.0
    serotonina: float = 0.5
    age: int = 0

    def is_alive(self): return self.integridade > 0

@dataclass
class Memory:
    topic: str
    proposal: str
    score: float
    cycle: int

class Agent:
    def __init__(self, name, role, color, base_prompt, bio_data=None, memories=None, evolved_strategy=""):
        self.name = name
        self.role = role
        self.color = color
        self.base_prompt = base_prompt          # O núcleo imutável (Quem ele é)
        self.evolved_strategy = evolved_strategy # O que ele aprendeu (Adaptável)
        
        if bio_data:
            self.bio = BioState(**bio_data)
        else:
            self.bio = BioState()
            self._apply_genetics()
            
        self.memories: List[Memory] = []
        if memories:
            for m in memories: self.memories.append(Memory(**m))

    def _apply_genetics(self):
        if self.role == "Sobrevivente": self.bio.cortisol = 0.4
        if self.role == "Criativo": self.bio.dopamina = 0.8
        if self.role == "Filósofo": self.bio.serotonina = 0.8

    def __str__(self):
        status = "💀" if not self.bio.is_alive() else "❤"
        return (f"{self.color}[{self.name} {status}]{Colors.RESET} "
                f"Glic:{self.bio.glicose:.0f} | Cort:{self.bio.cortisol:.2f} | Idade:{self.bio.age}")

    def get_full_prompt(self):
        """Combina a essência do agente com sua estratégia aprendida."""
        return (f"Você é {self.name}, um {self.role}. {self.base_prompt}\n"
                f"SUA ESTRATÉGIA ATUAL DE SOBREVIVÊNCIA: {self.evolved_strategy}")

    def think(self, topic):
        self.bio.glicose -= 3.0
        prompt = (f"{self.get_full_prompt()}\n"
                  f"Contexto: Debate valendo comida. Tópico: '{topic}'.\n"
                  f"Gere uma opinião curta e persuasiva (máx 20 palavras).")
        
        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
                return res['message']['content'].strip().replace('"', '')
            except: return f"Opinião simulada sobre {topic}."
        return f"Simulação."

    def judge(self, speaker_name, proposal):
        if self.bio.cortisol > 0.8: return 1.0, "Pânico: Rejeito tudo por segurança."
        
        prompt = (f"{self.get_full_prompt()}\n"
                  f"O agente {speaker_name} disse: '{proposal}'\n"
                  f"Avalie (0-10) se concorda. Responda: 'NOTA: [0-10] | MOTIVO: [texto]'")
        
        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
                content = res['message']['content']
                match = re.search(r'NOTA:\s*(\d+[\.,]?\d*)', content)
                score = float(match.group(1).replace(',', '.')) if match else 5.0
                reason = content.split('MOTIVO:')[-1].strip() if 'MOTIVO:' in content else content
                return min(10.0, max(0.0, score)), reason
            except: return 5.0, "Indiferente."
        return 5.0, "Neutro."

    def remember(self, topic, proposal, score, cycle):
        """Guarda a experiência para processar no sono."""
        self.memories.append(Memory(topic, proposal, score, cycle))
        if len(self.memories) > 10: self.memories.pop(0) # Mantém apenas as últimas 10

    def dream(self):
        """O PROCESSO DE NEUROPLASTICIDADE"""
        if not OLLAMA_AVAILABLE or not self.memories: return

        # Filtra fracassos (Notas baixas) e sucessos
        failures = [m for m in self.memories if m.score < 4.0]
        successes = [m for m in self.memories if m.score > 7.0]
        
        if not failures and not successes: return "Nada relevante para aprender hoje."

        prompt = (
            f"Você é a consciência subconsciente de {self.name} ({self.role}).\n"
            f"Análise dos seus últimos debates:\n"
            f"FRACASSOS (Rejeitados): {[f'{m.topic}: {m.proposal}' for m in failures]}\n"
            f"SUCESSOS (Aprovados): {[f'{m.topic}: {m.proposal}' for m in successes]}\n"
            f"Baseado nisso, defina uma NOVA ESTRATÉGIA DE DISCURSO (máx 1 frase) para ser mais aceito pelo grupo amanhã."
            f"Responda apenas com a nova estratégia."
        )

        try:
            res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
            new_strategy = res['message']['content'].strip()
            self.evolved_strategy = new_strategy
            # Recupera um pouco de sanidade ao dormir
            self.bio.cortisol = max(0.0, self.bio.cortisol - 0.2)
            self.bio.dopamina += 0.1
            return f"Aprendizado: '{new_strategy}'"
        except Exception as e:
            return f"Pesadelo (Erro): {e}"

    def apply_entropy(self):
        self.bio.age += 1
        self.bio.glicose -= 1.0
        if self.bio.glicose < 20: 
            self.bio.cortisol += 0.05
            self.bio.integridade -= 1.0
        
# ==============================================================================
# SISTEMA DE ARQUIVOS E LOOP
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
            "bio": asdict(ag.bio),
            "memories": [asdict(m) for m in ag.memories],
            "evolved_strategy": ag.evolved_strategy
        }
        data["agents"].append(agent_data)
    
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)
    print(f"{Colors.GRAY}>> Estado Salvo (Ciclo {cycle}){Colors.RESET}")

def load_society():
    if not os.path.exists(DATA_FILE): return None, 0
    try:
        with open(DATA_FILE, 'r') as f: data = json.load(f)
        print(f"{Colors.GREEN}>> Save Carregado: Ciclo {data['cycle']}{Colors.RESET}")
        return data, data['cycle']
    except: return None, 0

def main():
    print(f"{Colors.HEADER}=== GENESIS: FASE 5 (SONHOS E NEUROPLASTICIDADE) ==={Colors.RESET}")
    
    saved_data, start_cycle = load_society()
    
    archetypes = [
        ("Marcus", "Filósofo", Colors.BLUE, "Valorize lógica e ética. Rejeite o caos."),
        ("Kael", "Sobrevivente", Colors.RED, "Valorize segurança. Rejeite riscos desnecessários."),
        ("Luna", "Criativo", Colors.GREEN, "Valorize a arte e o novo. Rejeite o tédio.")
    ]

    agents = []
    if saved_data:
        for ag_data in saved_data["agents"]:
            arch = next((a for a in archetypes if a[0] == ag_data["name"]), None)
            if arch:
                agents.append(Agent(
                    arch[0], arch[1], arch[2], arch[3], 
                    bio_data=ag_data["bio"],
                    memories=ag_data.get("memories"),
                    evolved_strategy=ag_data.get("evolved_strategy", "")
                ))
    else:
        for a in archetypes: agents.append(Agent(a[0], a[1], a[2], a[3]))

    topics = ["O perigo do desconhecido", "A necessidade da arte", "Ordem ou Caos?", "O valor do silêncio"]
    cycle = start_cycle
    day_length = 5 # A cada 5 ciclos, eles dormem

    try:
        while True:
            cycle += 1
            is_night = (cycle % day_length == 0)
            
            if is_night:
                print(f"\n{Colors.PURPLE}=== A NOITE CAI (CICLO {cycle}) - HORA DE SONHAR ==={Colors.RESET}")
                print(f"{Colors.GRAY}Os agentes processam suas rejeições e sucessos para evoluir...{Colors.RESET}")
                
                for agent in agents:
                    if agent.bio.is_alive():
                        dream_result = agent.dream()
                        print(f"{agent.color}{agent.name} sonha... {Colors.RESET}{dream_result}")
                
                print(f"{Colors.PURPLE}=== O SOL NASCE (NOVA ESTRATÉGIA ADOTADA) ==={Colors.RESET}\n")
                time.sleep(3)
                save_society(agents, cycle)
                continue # Pula o debate durante a noite

            # --- O DIA (DEBATE) ---
            print(f"\n{Colors.HEADER}--- DIA: CICLO {cycle} ---{Colors.RESET}")
            alive_agents = [a for a in agents if a.bio.is_alive()]
            
            for ag in agents: 
                ag.apply_entropy()
                print(ag)
            
            if len(alive_agents) < 2:
                print("Sociedade colapsou.")
                break

            # Seleção de quem fala (Fome)
            speakers = sorted([a for a in alive_agents if a.bio.glicose < 60], key=lambda x: x.bio.glicose)
            
            if speakers:
                speaker = speakers[0]
                topic = random.choice(topics)
                
                print(f"\n{Colors.WARNING}>> DEBATE: '{topic}'{Colors.RESET}")
                
                # Pensamento (agora influenciado pela estratégia evoluída)
                proposal = speaker.think(topic)
                print(f"{speaker.color}{speaker.name}:{Colors.RESET} \"{proposal}\"")
                if speaker.evolved_strategy:
                    print(f"{Colors.GRAY}(Estratégia: {speaker.evolved_strategy}){Colors.RESET}")

                # Votação
                votes = []
                for voter in alive_agents:
                    if voter != speaker:
                        score, reason = voter.judge(speaker.name, proposal)
                        votes.append(score)
                        print(f"   > {voter.name}: {score:.1f} | {reason}")
                
                avg = sum(votes)/len(votes) if votes else 0
                print(f"   >> MÉDIA: {Colors.BOLD}{avg:.1f}{Colors.RESET}")

                # Consequências e Memória
                if avg >= 5.0:
                    speaker.bio.glicose += (avg * 5.0)
                    print(f"{Colors.GREEN}   >> APROVADO!{Colors.RESET}")
                else:
                    speaker.bio.cortisol += 0.3
                    print(f"{Colors.RED}   >> REJEITADO!{Colors.RESET}")
                
                # O agente guarda essa memória para sonhar com ela depois
                speaker.remember(topic, proposal, avg, cycle)
            
            else:
                print("Todos saciados.")

            time.sleep(2)

    except KeyboardInterrupt:
        save_society(agents, cycle)
        print("\nHibernando...")

if __name__ == "__main__":
    main()
