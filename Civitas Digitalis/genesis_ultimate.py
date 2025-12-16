import time
import random
import sys
import json
import os
import re
from dataclasses import dataclass, asdict
from typing import List, Optional, Tuple

# ==============================================================================
# CONFIGURAÇÕES & INFRAESTRUTURA (Zero Cost)
# ==============================================================================
try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

DATA_FILE = "genesis_save.json"
BOOK_FILE = "genesis_book.md"
HALL_OF_FAME_FILE = "genesis_graveyard.json"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'   # Marcus / Sistema 2
    RED = '\033[91m'    # Kael / Sistema 1
    GREEN = '\033[92m'  # Luna
    GOLD = '\033[33m'   # Grande Obra
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'
    PURPLE = '\033[35m' # Trauma
    WARNING = '\033[93m'
    FAIL = '\033[91m'

# ==============================================================================
# MÓDULO BIOLÓGICO (Especificação v1.1)
# ==============================================================================
@dataclass
class BioState:
    # Energias Vitais
    glicose: float = 100.0        # Combustível do Sistema 2
    integridade: float = 100.0    # Saúde Estrutural
    
    # Neuroquímica (0.0 a 1.0)
    dopamina: float = 0.5         # Motivação/Prazer
    serotonina: float = 0.5       # Estabilidade/Humor
    cortisol: float = 0.0         # Estresse/Pânico
    oxitocina: float = 0.5        # Confiança Social (Novo na v2.1)
    
    # Genética/Memória
    trauma_depth: float = 0.0     # Cicatrizes permanentes (0-10)
    age: int = 0
    generation: int = 1

    def is_alive(self): return self.integridade > 0

@dataclass
class Memory:
    topic: str
    proposal: str
    score: float
    cycle: int
    system_used: str = "Sys2" # Sys1 ou Sys2

# ==============================================================================
# MÓDULO COGNITIVO (Agente Dual-Process)
# ==============================================================================
class Agent:
    def __init__(self, name, role, color, base_prompt, generation=1, bio_data=None, memories=None, evolved_strategy=""):
        self.name = name
        self.role = role
        self.color = color
        self.base_prompt = base_prompt
        self.evolved_strategy = evolved_strategy
        
        if bio_data: 
            self.bio = BioState(**bio_data)
        else: 
            self.bio = BioState(generation=generation)
            self._apply_archetype()
            self.life_motto = self.read_scripture()
            
        self.memories = []
        if memories:
            for m in memories:
                # Compatibilidade
                if isinstance(m, dict):
                     if 'system_used' not in m: m['system_used'] = "Sys2"
                     self.memories.append(Memory(m.get('topic', '?'), m.get('proposal', '...'), m.get('score', 0), m.get('cycle', 0), m.get('system_used', 'Sys2')))

    def _apply_archetype(self):
        # Configuração neuroquímica inicial baseada na "Ficha de Personagem"
        if self.role == "Sobrevivente": 
            self.bio.cortisol = 0.4
            self.bio.oxitocina = 0.2 # Baixa confiança
        if self.role == "Criativo": 
            self.bio.dopamina = 0.8
            self.bio.oxitocina = 0.6
        if self.role == "Filósofo": 
            self.bio.serotonina = 0.8
            self.bio.oxitocina = 0.5

    def _roman(self, n):
        return "I" if n==1 else "II" if n==2 else "III" if n==3 else str(n)

    def __str__(self):
        status = "💀" if not self.bio.is_alive() else "❤"
        # Indicador visual de qual sistema está dominante
        sys_indicator = f"{Colors.RED}[SYS-1]{Colors.RESET}" if self._check_system_1_dominance() else f"{Colors.BLUE}[SYS-2]{Colors.RESET}"
        return (f"{self.color}[{self.name} {self._roman(self.bio.generation)} {status}]{Colors.RESET} "
                f"Glic:{self.bio.glicose:.0f} | Cort:{self.bio.cortisol:.2f} | Oxi:{self.bio.oxitocina:.2f} | {sys_indicator}")

    def _check_system_1_dominance(self) -> bool:
        """
        Lógica Kahneman:
        Sistema 1 assume se: Cortisol > 0.6 (Pânico) OU Glicose < 20 (Fome)
        """
        return self.bio.cortisol > 0.6 or self.bio.glicose < 20.0

    def read_scripture(self):
        if not os.path.exists(BOOK_FILE): return ""
        try:
            with open(BOOK_FILE, 'r') as f: lines = f.readlines()
            return random.choice(lines).strip() if lines else ""
        except: return ""

    def get_context_prompt(self):
        """Monta o prompt considerando estado biológico e traumas."""
        trauma_text = f"TRAUMA PROFUNDO: Você é cínico e amargo devido a falhas passadas." if self.bio.trauma_depth > 5.0 else ""
        sys_state = "MODO: SOBREVIVÊNCIA (Rápido, Agressivo)" if self._check_system_1_dominance() else "MODO: ANALÍTICO (Racional, Calmo)"
        
        return (f"Você é {self.name}, {self.role}. {self.base_prompt}\n"
                f"Lema: {getattr(self, 'life_motto', '')}\n"
                f"{trauma_text}\n"
                f"Estratégia Aprendida: {self.evolved_strategy}\n"
                f"ESTADO ATUAL: {sys_state}")

    def think(self, topic) -> Tuple[str, str]:
        """
        Processamento Dual:
        - Sistema 1: Rápido, gasta pouca glicose (-1), resposta curta/visceral.
        - Sistema 2: Lento, gasta muita glicose (-5), resposta elaborada.
        """
        prompt = self.get_context_prompt()
        is_sys1 = self._check_system_1_dominance()
        
        cost = 1.0 if is_sys1 else 5.0
        self.bio.glicose -= cost
        
        instruction = "Responda em 1 frase curta, impulsiva e emocional." if is_sys1 else "Responda com 1 frase lógica, ponderada e estruturada."
        
        full_prompt = f"{prompt}\nContexto: Debate sobre '{topic}'.\nInstrução: {instruction}"
        
        response = "Simulação..."
        if OLLAMA_AVAILABLE:
            try:
                # Sistema 1 usa temperatura mais alta (mais aleatório/emocional)
                temp = 0.9 if is_sys1 else 0.4
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': full_prompt}], options={'temperature': temp})
                response = res['message']['content'].strip().replace('"', '')
            except: pass
            
        return response, ("Sys1" if is_sys1 else "Sys2")

    def judge(self, speaker_name, proposal) -> Tuple[float, str]:
        """
        A Oxitocina modula a confiança.
        Oxitocina alta = Tende a concordar (viés de grupo).
        Oxitocina baixa = Tende a desconfiar (viés de rejeição).
        """
        base_bias = (self.bio.oxitocina - 0.5) * 4.0 # -2.0 a +2.0 na nota
        
        # Se estiver em Pânico (Sys1), rejeita tudo que for complexo
        if self._check_system_1_dominance():
            return 2.0, "Estou em pânico! Não tenho tempo para isso!"

        prompt = (f"{self.get_context_prompt()}\n"
                  f"O agente {speaker_name} disse: '{proposal}'\n"
                  f"Avalie (0-10) considerando que seu nível de confiança (oxitocina) influencia sua nota.\n"
                  f"Retorne: 'NOTA: [numero] | MOTIVO: [texto]'")
        
        score = 5.0
        reason = "Neutro"
        
        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
                content = res['message']['content']
                match = re.search(r'(\d+[\.,]?\d*)', content)
                if match:
                    score = float(match.group(1).replace(',', '.'))
                    # Aplica o viés químico
                    score = max(0.0, min(10.0, score + base_bias))
                    reason = content.split('|')[-1].strip()[:60]
            except: pass
            
        return score, reason

    def apply_entropy(self):
        self.bio.age += 1
        self.bio.glicose -= 1.0 # Metabolismo basal
        
        # Regras de Toxicidade e Trauma
        if self.bio.glicose < 20:
            self.bio.cortisol += 0.05
            self.bio.integridade -= 1.0
        
        if self.bio.cortisol > 0.9:
            self.bio.integridade -= 0.5
            self.bio.trauma_depth += 0.01 # Pânico constante gera trauma permanente

    def remember(self, topic, proposal, score, cycle, sys_used):
        # Se foi rejeitado (score < 4), aumenta trauma
        if score < 4.0:
            self.bio.trauma_depth += 0.1
            self.bio.oxitocina = max(0.0, self.bio.oxitocina - 0.1) # Perde confiança no grupo
        elif score > 7.0:
            self.bio.dopamina = min(1.0, self.bio.dopamina + 0.2)
            self.bio.oxitocina = min(1.0, self.bio.oxitocina + 0.1) # Ganha confiança
            
        self.memories.append(Memory(topic, proposal, score, cycle, sys_used))
        if len(self.memories) > 10: self.memories.pop(0)

# ==============================================================================
# FUNÇÕES AUXILIARES (IO)
# ==============================================================================
def save_system(agents, cycle):
    data = {
        "cycle": cycle,
        "agents": [{"name": a.name, "role": a.role, "bio": asdict(a.bio), 
                    "memories": [asdict(m) for m in a.memories], 
                    "evolved_strategy": a.evolved_strategy} for a in agents]
    }
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)

def load_system():
    if not os.path.exists(DATA_FILE): return None, 0
    try:
        with open(DATA_FILE, 'r') as f: data = json.load(f)
        print(f"{Colors.GREEN}>> Sistema Restaurado: Ciclo {data['cycle']}{Colors.RESET}")
        return data, data['cycle']
    except: return None, 0

def record_death(agent, cycle, cause):
    entry = {"name": f"{agent.name} {agent._roman(agent.bio.generation)}", 
             "role": agent.role, "age": agent.bio.age, "cycle": cycle, "cause": cause}
    graveyard = []
    if os.path.exists(HALL_OF_FAME_FILE):
        with open(HALL_OF_FAME_FILE, 'r') as f: graveyard = json.load(f)
    graveyard.append(entry)
    with open(HALL_OF_FAME_FILE, 'w') as f: json.dump(graveyard, f, indent=4)
    print(f"\n{Colors.FAIL}† {entry['name']} faleceu. Causa: {cause} †{Colors.RESET}")

def spawn_descendant(dead_agent):
    new_gen = dead_agent.bio.generation + 1
    roman = "I" if new_gen==1 else "II" if new_gen==2 else "III" if new_gen==3 else str(new_gen)
    print(f"{Colors.GOLD}* Nascimento: {dead_agent.name} {roman} *{Colors.RESET}")
    return Agent(dead_agent.name, dead_agent.role, dead_agent.color, dead_agent.base_prompt, generation=new_gen)

# ==============================================================================
# KERNEL PRINCIPAL
# ==============================================================================
def main():
    print(f"{Colors.HEADER}=== GENESIS KERNEL v2.1 (ZERO COST / DUAL PROCESS) ==={Colors.RESET}")
    print("Módulos Ativos: BioState v1.1 | Kahneman Engine | Trauma | Oxitocina")
    
    saved, cycle = load_system()
    
    archetypes = [
        ("Marcus", "Filósofo", Colors.BLUE, "Busque a verdade lógica e ética."),
        ("Kael", "Sobrevivente", Colors.RED, "Busque segurança e evite riscos."),
        ("Luna", "Criativo", Colors.GREEN, "Busque a beleza e o caos.")
    ]

    agents = []
    if saved:
        for d in saved["agents"]:
            arch = next((a for a in archetypes if a[0] == d["name"]), None)
            if arch: agents.append(Agent(arch[0], arch[1], arch[2], arch[3], 
                                         generation=d["bio"].get("generation", 1), 
                                         bio_data=d["bio"], memories=d.get("memories"), 
                                         evolved_strategy=d.get("evolved_strategy", "")))
    else:
        for a in archetypes: agents.append(Agent(a[0], a[1], a[2], a[3]))

    try:
        while True:
            cycle += 1
            print(f"\n{Colors.HEADER}--- CICLO {cycle} ---{Colors.RESET}")
            
            # 1. PROCESSAMENTO BIOLÓGICO
            active = []
            for i, ag in enumerate(agents):
                ag.apply_entropy()
                print(ag) # Mostra SYS-1 ou SYS-2
                
                if not ag.bio.is_alive():
                    cause = "Colapso Metabólico" if ag.bio.glicose <= 0 else "Falência Sistêmica"
                    record_death(ag, cycle, cause)
                    new_ag = spawn_descendant(ag)
                    agents[i] = new_ag
                    active.append(new_ag)
                else:
                    active.append(ag)
            
            # 2. SELEÇÃO ECONÔMICA (Quem trabalha?)
            # Ordena por fome (Glicose menor primeiro)
            hungry = sorted([a for a in active if a.bio.glicose < 60], key=lambda x: x.bio.glicose)
            
            if hungry:
                speaker = hungry[0]
                topic = random.choice(["O Futuro", "A Dor", "O Código", "A Confiança"])
                
                print(f"\n{Colors.WARNING}>> DEBATE (Valendo Glicose): '{topic}'{Colors.RESET}")
                
                # Pensamento (Dual Process)
                speech, sys_used = speaker.think(topic)
                sys_label = f"{Colors.RED}[SYS-1 Rápido]{Colors.RESET}" if sys_used == "Sys1" else f"{Colors.BLUE}[SYS-2 Analítico]{Colors.RESET}"
                print(f"{speaker.color}{speaker.name}:{Colors.RESET} {sys_label} \"{speech}\"")
                
                # Julgamento Social (Oxitocina)
                votes = []
                for judge in active:
                    if judge != speaker:
                        score, reason = judge.judge(speaker.name, speech)
                        votes.append(score)
                        print(f" > {judge.name} (Oxi:{judge.bio.oxitocina:.1f}): {score:.1f} | {reason}")
                
                avg = sum(votes)/len(votes) if votes else 0
                
                if avg >= 5.0:
                    reward = 30.0 if sys_used == "Sys2" else 15.0 # Sys2 paga melhor (qualidade)
                    speaker.bio.glicose += reward
                    print(f"{Colors.GREEN}>> APROVADO (+{reward} Glicose){Colors.RESET}")
                else:
                    speaker.bio.cortisol += 0.2
                    print(f"{Colors.RED}>> REJEITADO (Estresse Sobe){Colors.RESET}")
                
                speaker.remember(topic, speech, avg, cycle, sys_used)
            
            else:
                print("Sociedade Saciada.")

            # Save periódico
            if cycle % 5 == 0: save_system(agents, cycle)
            time.sleep(2)

    except KeyboardInterrupt:
        save_system(agents, cycle)
        print("\nKernel Hibernado.")

if __name__ == "__main__":
    main()
