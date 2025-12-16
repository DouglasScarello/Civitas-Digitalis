import time
import random
import sys
import json
import os
import re
from dataclasses import dataclass, asdict
from typing import List, Optional

# ==============================================================================
# CONFIGURAÇÕES
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
    BLUE = '\033[94m'   # Marcus Lineage
    RED = '\033[91m'    # Kael Lineage
    GREEN = '\033[92m'  # Luna Lineage
    GOLD = '\033[33m'   # Sacred
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'
    PURPLE = '\033[35m'
    FAIL = '\033[91m'
    WARNING = '\033[93m'

# ==============================================================================
# ESTRUTURAS
# ==============================================================================
@dataclass
class BioState:
    glicose: float = 100.0
    integridade: float = 100.0
    dopamina: float = 0.5
    cortisol: float = 0.0
    serotonina: float = 0.5
    age: int = 0
    generation: int = 1  # Geração da linhagem (I, II, III...)

    def is_alive(self): return self.integridade > 0

@dataclass
class Memory:
    topic: str
    proposal: str
    score: float
    cycle: int

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
            self._apply_genetics()
            # Ao nascer, lê o livro para formar personalidade
            self.life_motto = self.read_scripture()
            
        self.memories = []
        if memories:
            for m in memories: 
                # Compatibilidade com saves antigos que podem não ter a chave 'cycle'
                if isinstance(m, dict):
                     # Se faltar keys, preenche default
                     if 'cycle' not in m: m['cycle'] = 0
                     if 'topic' not in m: m['topic'] = "Unknown"
                     if 'proposal' not in m: m['proposal'] = "..."
                     if 'score' not in m: m['score'] = 0.0
                     self.memories.append(Memory(m['topic'], m['proposal'], m['score'], m['cycle']))

    def _apply_genetics(self):
        # Mutações leves a cada geração
        mutation = random.uniform(-0.1, 0.1)
        if self.role == "Sobrevivente": self.bio.cortisol = 0.4 + mutation
        if self.role == "Criativo": self.bio.dopamina = 0.8 + mutation
        if self.role == "Filósofo": self.bio.serotonina = 0.8 + mutation

    def __str__(self):
        status = "💀" if not self.bio.is_alive() else "❤"
        gen = self._roman_numeral(self.bio.generation)
        return (f"{self.color}[{self.name} {gen} {status}]{Colors.RESET} "
                f"Glic:{self.bio.glicose:.0f} | Cort:{self.bio.cortisol:.2f} | Idade:{self.bio.age}")

    def get_full_prompt(self):
        motto_str = f"LEMA DE VIDA (Do Livro Sagrado): '{self.life_motto}'" if hasattr(self, 'life_motto') else ""
        return (f"Você é {self.name} {self._roman_numeral(self.bio.generation)}, um {self.role}. {self.base_prompt}\n"
                f"{motto_str}\n"
                f"ESTRATÉGIA APRENDIDA: {self.evolved_strategy}")

    def _roman_numeral(self, num):
        return "I" if num == 1 else "II" if num == 2 else "III" if num == 3 else "IV" if num == 4 else str(num)

    def read_scripture(self):
        if not os.path.exists(BOOK_FILE): return ""
        with open(BOOK_FILE, 'r') as f: lines = f.readlines()
        if not lines: return ""
        # Escolhe um verso aleatório para guiar a vida
        return random.choice(lines).strip()

    def propose_verse(self):
        self.bio.glicose -= 15.0 # Escrever custa muito caro agora
        previous_wisdom = self.read_scripture()
        prompt = (f"{self.get_full_prompt()}\n"
                  f"Sabedoria Anterior: '{previous_wisdom}'\n"
                  f"Tarefa: Escreva um NOVO VERSO SAGRADO (máx 15 palavras) para guiar as futuras gerações.")
        
        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
                return res['message']['content'].strip().replace('"', '')
            except: return "A entropia vence no final."
        return "Simulação de verso."

    def think(self, topic):
        self.bio.glicose -= 3.0
        prompt = (f"{self.get_full_prompt()}\n"
                  f"Contexto: Debate sobre '{topic}'.\n"
                  f"Gere uma opinião curta (máx 20 palavras) e persuasiva.")
        
        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
                return res['message']['content'].strip().replace('"', '')
            except: return f"Opinião sobre {topic}."
        return "Simulação."

    def judge(self, speaker_name, proposal):
        # Se cortisol explodir, rejeita tudo
        if self.bio.cortisol > 0.9: return 0.0, "COLAPSO NERVOSO (Medo extremo)."
        
        prompt = (f"{self.get_full_prompt()}\n"
                  f"O agente {speaker_name} disse: '{proposal}'\n"
                  f"Nota 0-10 e Motivo.")
        
        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
                content = res['message']['content']
                match = re.search(r'(\d+[\.,]?\d*)', content)
                score = float(match.group(1).replace(',', '.')) if match else 5.0
                return min(10.0, max(0.0, score)), content[:60]
            except: return 5.0, "Neutro."
        return 5.0, "Neutro."

    def remember(self, topic, proposal, score, cycle):
        self.memories.append(Memory(topic, proposal, score, cycle))
        if len(self.memories) > 10: self.memories.pop(0)

    def dream(self):
        if not OLLAMA_AVAILABLE or not self.memories: return "Sono sem sonhos."
        failures = [m for m in self.memories if m.score < 4.5]
        if not failures: return "Sinto-me confiante."

        prompt = (f"Você é o subconsciente de {self.name}.\n"
                  f"Falhas recentes: {[f.proposal for f in failures]}\n"
                  f"Defina uma NOVA ESTRATÉGIA (1 frase) para sobreviver amanhã.")

        try:
            res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
            self.evolved_strategy = res['message']['content'].strip()
            self.bio.cortisol = max(0.0, self.bio.cortisol - 0.3)
            return f"Evolução: {self.evolved_strategy[:50]}..."
        except: return "Pesadelo."

    def apply_entropy(self):
        self.bio.age += 1
        # Velhice custa caro: metabolismo desacelera (gasta menos) mas corpo quebra mais
        base_cost = 1.0
        if self.bio.age > 100: self.bio.integridade -= 0.1 # Envelhecimento natural
        
        self.bio.glicose -= base_cost
        
        if self.bio.glicose < 20: 
            self.bio.cortisol += 0.05
            self.bio.integridade -= 1.5 # Dano por fome aumentado
        else:
            self.bio.integridade = min(100, self.bio.integridade + 0.1) # Regeneração leve se alimentado

# ==============================================================================
# GESTÃO DE VIDA E MORTE
# ==============================================================================
def record_death(agent, cycle, cause):
    entry = {
        "name": f"{agent.name} {agent._roman_numeral(agent.bio.generation)}",
        "role": agent.role,
        "age": agent.bio.age,
        "cycle_of_death": cycle,
        "cause": cause,
        "legacy_strategy": agent.evolved_strategy
    }
    
    graveyard = []
    if os.path.exists(HALL_OF_FAME_FILE):
        with open(HALL_OF_FAME_FILE, 'r') as f: graveyard = json.load(f)
    
    graveyard.append(entry)
    with open(HALL_OF_FAME_FILE, 'w') as f: json.dump(graveyard, f, indent=4)
    print(f"\n{Colors.FAIL}††† {entry['name']} faleceu aos {entry['age']} ciclos. Causa: {cause} †††{Colors.RESET}")

def spawn_descendant(dead_agent):
    new_gen = dead_agent.bio.generation + 1
    print(f"{Colors.GOLD}*** Um novo discípulo surge: {dead_agent.name} {('I' if new_gen==1 else 'II' if new_gen==2 else str(new_gen))} ***{Colors.RESET}")
    # O novo agente herda o nome, cor, role e prompt base, mas reseta a biologia
    return Agent(dead_agent.name, dead_agent.role, dead_agent.color, dead_agent.base_prompt, generation=new_gen)

def write_to_book(verse, author):
    mode = 'a' if os.path.exists(BOOK_FILE) else 'w'
    with open(BOOK_FILE, mode) as f:
        f.write(f"- {verse} ({author})\n")

def save_society(agents, cycle):
    data = {
        "cycle": cycle,
        "agents": [{"name": a.name, "role": a.role, "bio": asdict(a.bio), "memories": [{"topic":m.topic,"proposal":m.proposal,"score":m.score,"cycle":m.cycle} for m in a.memories], "evolved_strategy": a.evolved_strategy} for a in agents]
    }
    with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)

def load_society():
    if not os.path.exists(DATA_FILE): return None, 0
    try:
        with open(DATA_FILE, 'r') as f: data = json.load(f)
        print(f"{Colors.GREEN}>> Save Carregado: Ciclo {data['cycle']}{Colors.RESET}")
        return data, data['cycle']
    except Exception as e: 
        print(f"Erro ao carregar save: {e}")
        return None, 0

# ==============================================================================
# MAIN LOOP
# ==============================================================================
def main():
    print(f"{Colors.HEADER}=== GENESIS: FASE 7 (GERAÇÕES E LEGADO) ==={Colors.RESET}")
    
    saved_data, start_cycle = load_society()
    
    archetypes = [
        ("Marcus", "Filósofo", Colors.BLUE, "Valorize lógica e ética."),
        ("Kael", "Sobrevivente", Colors.RED, "Valorize segurança e cautela."),
        ("Luna", "Criativo", Colors.GREEN, "Valorize a arte e o novo.")
    ]

    agents = []
    if saved_data:
        for ag_data in saved_data["agents"]:
            arch = next((a for a in archetypes if a[0] == ag_data["name"]), None)
            if arch:
                # Recupera generation do save ou define 1
                gen = ag_data["bio"].get("generation", 1)
                ag = Agent(arch[0], arch[1], arch[2], arch[3], generation=gen, bio_data=ag_data["bio"], memories=ag_data.get("memories"), evolved_strategy=ag_data.get("evolved_strategy", ""))
                agents.append(ag)
    else:
        for a in archetypes: agents.append(Agent(a[0], a[1], a[2], a[3]))

    cycle = start_cycle
    
    try:
        while True:
            cycle += 1
            
            # --- NOITE (SONHO) ---
            if cycle % 10 == 0:
                print(f"\n{Colors.PURPLE}=== NOITE (Neuroplasticidade) ==={Colors.RESET}")
                for ag in agents:
                    if ag.bio.is_alive(): print(f"{ag.name} sonha: {ag.dream()}")
                time.sleep(2)
                save_society(agents, cycle)
                continue

            # --- DIA ---
            print(f"\n{Colors.HEADER}--- CICLO {cycle} ---{Colors.RESET}")
            
            # 1. Aplicar Entropia e Verificar Mortes
            active_agents = []
            for i, ag in enumerate(agents):
                ag.apply_entropy()
                print(ag)
                
                if not ag.bio.is_alive():
                    # MORTE
                    cause = "Inanição (Fome)" if ag.bio.glicose <= 0 else "Colapso Sistêmico (Velhice/Dano)"
                    record_death(ag, cycle, cause)
                    # SUCESSÃO
                    new_agent = spawn_descendant(ag)
                    agents[i] = new_agent # Substitui o morto pelo filho na lista
                    active_agents.append(new_agent)
                else:
                    active_agents.append(ag)
            
            # 2. Grande Obra (Se houver iluminados)
            inspired = [a for a in active_agents if a.bio.glicose > 90 and a.bio.dopamina > 0.7]
            if inspired:
                prophet = random.choice(inspired)
                print(f"\n{Colors.GOLD}>> REVELAÇÃO: {prophet.name} escreve no Livro... <<{Colors.RESET}")
                verse = prophet.propose_verse()
                print(f"Verso: \"{verse}\"")
                
                votes = [v.judge(prophet.name, verse)[0] for v in active_agents if v != prophet]
                if votes and (sum(votes)/len(votes) >= 6.0):
                    write_to_book(verse, f"{prophet.name} {prophet._roman_numeral(prophet.bio.generation)}")
                    print(f"{Colors.GOLD}>> CANONIZADO!{Colors.RESET}")
                else:
                    print(f"{Colors.GRAY}>> Rejeitado.{Colors.RESET}")
                    prophet.bio.dopamina -= 0.3

            # 3. Debate (Se houver famintos)
            else:
                hungry = sorted([a for a in active_agents if a.bio.glicose < 50], key=lambda x: x.bio.glicose)
                if hungry:
                    speaker = hungry[0]
                    topic = random.choice(["O Medo", "O Legado", "A Morte", "O Livro"])
                    print(f"\n{Colors.WARNING}>> DEBATE: '{topic}'{Colors.RESET}")
                    
                    speech = speaker.think(topic)
                    print(f"{speaker.color}{speaker.name}:{Colors.RESET} \"{speech}\"")
                    
                    votes = []
                    for v in active_agents:
                        if v != speaker:
                            s, r = v.judge(speaker.name, speech)
                            votes.append(s)
                            print(f" > {v.name}: {s:.1f} | {r}")
                    
                    avg = sum(votes)/len(votes) if votes else 0
                    if avg >= 5.0:
                        print(f"{Colors.GREEN}>> Aprovado (+35 Glicose){Colors.RESET}")
                        speaker.bio.glicose += 35
                        speaker.remember(topic, speech, avg, cycle)
                    else:
                        print(f"{Colors.FAIL}>> Rejeitado (Cortisol Sobe){Colors.RESET}")
                        speaker.bio.cortisol += 0.4
                        speaker.remember(topic, speech, avg, cycle)

            time.sleep(1)

    except KeyboardInterrupt:
        save_society(agents, cycle)
        print("\nSociedade salva. Até logo.")

if __name__ == "__main__":
    main()
