import time
import random
import sys
import json
import os
import re
from dataclasses import dataclass, asdict
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'   # Marcus
    RED = '\033[91m'    # Kael
    GREEN = '\033[92m'  # Luna
    WARNING = '\033[93m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'
    CYAN = '\033[96m'

DATA_FILE = "genesis_save.json"

# ==============================================================================
# 1. BIOLOGIA (Mantendo compatibilidade com save anterior)
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

# ==============================================================================
# 2. O AGENTE (Agora capaz de JULGAR)
# ==============================================================================
class Agent:
    def __init__(self, name, role, color, personality_prompt, bio_data=None):
        self.name = name
        self.role = role
        self.color = color
        self.personality_prompt = personality_prompt
        
        if bio_data:
            self.bio = BioState(**bio_data)
        else:
            self.bio = BioState()
            self._apply_genetics()

    def _apply_genetics(self):
        if self.role == "Sobrevivente": self.bio.cortisol = 0.4
        if self.role == "Criativo": self.bio.dopamina = 0.8
        if self.role == "Filósofo": self.bio.serotonina = 0.8

    def __str__(self):
        status = "💀" if not self.bio.is_alive() else "❤"
        return (f"{self.color}[{self.name}]{Colors.RESET} "
                f"Glic:{self.bio.glicose:.0f} | Cort:{self.bio.cortisol:.2f} | Idade:{self.bio.age}")

    def think(self, topic):
        """Gera uma proposta sobre o tópico."""
        self.bio.glicose -= 3.0
        
        prompt = (
            f"Você é {self.name}, um {self.role}. {self.personality_prompt}\n"
            f"Contexto: Você precisa convencer os outros para ganhar comida.\n"
            f"Tópico: {topic}\n"
            f"Gere uma opinião curta (máx 20 palavras) e persuasiva."
        )
        
        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
                return res['message']['content'].strip().replace('"', '')
            except:
                return f"Eu acho que {topic} é complicado..."
        return f"Simulação de opinião sobre {topic}."

    def judge(self, speaker_name, proposal):
        """Julga a proposta de outro agente e dá uma nota (0-10)."""
        # Agentes estressados julgam mal
        if self.bio.cortisol > 0.7:
            return 2.0, "Estou em pânico, não confio nisso."

        prompt = (
            f"Você é {self.name} ({self.role}). {self.personality_prompt}\n"
            f"O agente {speaker_name} disse: '{proposal}'\n"
            f"Avalie se você concorda com isso baseado na SUA personalidade.\n"
            f"Responda EXATAMENTE neste formato: 'NOTA: [número 0-10] | MOTIVO: [frase curta]'"
        )

        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
                content = res['message']['content']
                
                # Parser simples para extrair a nota
                match = re.search(r'NOTA:\s*(\d+[\.,]?\d*)', content)
                score = float(match.group(1).replace(',', '.')) if match else 5.0
                reason = content.split('MOTIVO:')[-1].strip() if 'MOTIVO:' in content else content
                
                return min(10.0, max(0.0, score)), reason
            except:
                return 5.0, "Indiferente (Erro Neural)"
        return 5.0, "Simulação de julgamento."

    def apply_entropy(self):
        self.bio.age += 1
        self.bio.glicose -= 1.5
        if self.bio.glicose < 20: 
            self.bio.cortisol += 0.05
            self.bio.integridade -= 1.0
        else:
            self.bio.cortisol = max(0.0, self.bio.cortisol - 0.02)

# ==============================================================================
# 3. SISTEMA (Loop Político)
# ==============================================================================
def save_society(agents, cycle):
    data = {"cycle": cycle, "agents": [{"name": a.name, "role": a.role, "bio": asdict(a.bio)} for a in agents]}
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)
    print(f"{Colors.GRAY}>> Estado salvo (Ciclo {cycle}){Colors.RESET}")

def load_society():
    if not os.path.exists(DATA_FILE): return None, 0
    with open(DATA_FILE, 'r') as f: data = json.load(f)
    print(f"{Colors.GREEN}>> Save carregado: Ciclo {data['cycle']}{Colors.RESET}")
    return data, data['cycle']

def main():
    print(f"{Colors.HEADER}=== GENESIS: FASE 4 (POLÍTICA & VOTAÇÃO) ==={Colors.RESET}")
    
    saved_data, start_cycle = load_society()
    
    archetypes = [
        ("Marcus", "Filósofo", Colors.BLUE, "Você valoriza lógica, ética e verdade. Odeia caos."),
        ("Kael", "Sobrevivente", Colors.RED, "Você valoriza segurança e pessimismo. Odeia riscos."),
        ("Luna", "Criativo", Colors.GREEN, "Você valoriza arte, caos e novidade. Odeia tédio.")
    ]

    agents = []
    if saved_data:
        for ag_data in saved_data["agents"]:
            arch = next((a for a in archetypes if a[0] == ag_data["name"]), None)
            if arch: agents.append(Agent(arch[0], arch[1], arch[2], arch[3], bio_data=ag_data["bio"]))
    else:
        for a in archetypes: agents.append(Agent(a[0], a[1], a[2], a[3]))

    topics = ["O futuro é perigoso?", "A liberdade vale o risco?", "Devemos desligar os fracos?", "A arte salva?"]
    cycle = start_cycle

    try:
        while True:
            cycle += 1
            print(f"\n{Colors.HEADER}--- CICLO {cycle} ---{Colors.RESET}")
            
            # 1. Entropia
            alive_agents = [a for a in agents if a.bio.is_alive()]
            for ag in agents: 
                ag.apply_entropy()
                print(ag)
            
            if len(alive_agents) < 2:
                print("Sociedade insuficiente para votação.")
                break

            # 2. Seleção do Orador (Quem tem mais fome fala)
            speakers = sorted([a for a in alive_agents if a.bio.glicose < 60], key=lambda x: x.bio.glicose)
            
            if speakers:
                speaker = speakers[0] # O mais faminto fala
                topic = random.choice(topics)
                
                print(f"\n{Colors.WARNING}>> DEBATE: '{topic}'{Colors.RESET}")
                print(f"{speaker.color}{speaker.name} sobe ao palco (Glicose: {speaker.bio.glicose:.0f}%)...{Colors.RESET}")
                
                # Proposta
                proposal = speaker.think(topic)
                print(f"\"{proposal}\"\n")
                
                # 3. Votação dos Pares
                votes = []
                print(f"{Colors.GRAY}--- Votação ---{Colors.RESET}")
                for voter in alive_agents:
                    if voter != speaker:
                        score, reason = voter.judge(speaker.name, proposal)
                        votes.append(score)
                        print(f"{voter.color}{voter.name}:{Colors.RESET} Nota {score:.1f} | \"{reason}\"")
                
                # Resultado
                avg_score = sum(votes) / len(votes) if votes else 0
                print(f"\n>> Média Final: {Colors.BOLD}{avg_score:.1f}/10{Colors.RESET}")
                
                if avg_score >= 5.0:
                    reward = avg_score * 6.0
                    speaker.bio.glicose += reward
                    speaker.bio.cortisol -= 0.3
                    print(f"{Colors.GREEN}>> Aprovado! {speaker.name} recebe {reward:.1f} de Glicose.{Colors.RESET}")
                else:
                    speaker.bio.cortisol += 0.5
                    speaker.bio.glicose -= 5.0 # Penalidade por gastar tempo falando bobagem
                    print(f"{Colors.RED}>> REJEITADO! {speaker.name} aumenta cortisol e perde energia.{Colors.RESET}")
            
            else:
                print("Todos estão saciados. Silêncio no servidor.")

            if cycle % 5 == 0: save_society(agents, cycle)
            time.sleep(2)

    except KeyboardInterrupt:
        save_society(agents, cycle)
        print("\nSociedade hibernada.")

if __name__ == "__main__":
    main()
