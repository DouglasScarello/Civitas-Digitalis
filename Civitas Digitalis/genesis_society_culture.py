import time
import random
import sys
import json
import os
import re
from dataclasses import dataclass, asdict
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
BOOK_FILE = "genesis_book.md"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'   # Marcus
    RED = '\033[91m'    # Kael
    GREEN = '\033[92m'  # Luna
    WARNING = '\033[93m'
    GOLD = '\033[33m'   # A Grande Obra
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GRAY = '\033[90m'
    PURPLE = '\033[35m'

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
        self.base_prompt = base_prompt
        self.evolved_strategy = evolved_strategy
        
        if bio_data: self.bio = BioState(**bio_data)
        else: self.bio = BioState(); self._apply_genetics()
            
        self.memories: List[Memory] = []
        if memories:
            for m in memories: self.memories.append(Memory(**m))

    def _apply_genetics(self):
        if self.role == "Sobrevivente": self.bio.cortisol = 0.4
        if self.role == "Criativo": self.bio.dopamina = 0.8
        if self.role == "Filósofo": self.bio.serotonina = 0.8

    def get_full_prompt(self):
        return (f"Você é {self.name}, um {self.role}. {self.base_prompt}\n"
                f"ESTRATÉGIA APRENDIDA: {self.evolved_strategy}")

    def read_scripture(self):
        """Lê as últimas linhas do Livro Sagrado para se inspirar."""
        if not os.path.exists(BOOK_FILE): return "O livro está vazio."
        with open(BOOK_FILE, 'r') as f: lines = f.readlines()
        return " ".join(lines[-3:]) if lines else "O livro está vazio."

    def propose_verse(self):
        """Tenta escrever uma 'Verdade' no livro (Gasta muita energia)."""
        self.bio.glicose -= 10.0
        scripture = self.read_scripture()
        
        prompt = (f"{self.get_full_prompt()}\n"
                  f"O LIVRO SAGRADO DIZ ATUALMENTE: '{scripture}'\n"
                  f"Tarefa: Escreva um NOVO VERSO (máx 10 palavras). SEJA BREVE. NÃO EXPLIQUE.\n"
                  f"Exemplo: 'A segurança é a mãe da liberdade.'\n"
                  f"Responda APENAS com o verso.")
        
        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
                return res['message']['content'].strip().replace('"', '')
            except: return "A entropia é a única certeza."
        return "Simulação de verso."

    def think(self, topic):
        self.bio.glicose -= 3.0
        # Agora ele considera o Livro ao debater
        scripture = self.read_scripture()
        
        prompt = (f"{self.get_full_prompt()}\n"
                  f"Sabedoria Ancestral (O Livro): '{scripture}'\n"
                  f"Contexto: Debate sobre '{topic}'.\n"
                  f"Gere uma opinião curta e persuasiva, citando o Livro se possível.")
        
        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
                return res['message']['content'].strip().replace('"', '')
            except: return f"Opinião sobre {topic}."
        return "Simulação."

    def judge(self, speaker_name, proposal):
        if self.bio.cortisol > 0.8: return 1.0, "Pânico."
        
        prompt = (f"{self.get_full_prompt()}\n"
                  f"O agente {speaker_name} disse: '{proposal}'\n"
                  f"Nota 0-10 e Motivo.")
        
        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
                content = res['message']['content']
                match = re.search(r'(\d+[\.,]?\d*)', content)
                score = float(match.group(1).replace(',', '.')) if match else 5.0
                return min(10.0, max(0.0, score)), content[:50]
            except: return 5.0, "Neutro."
        return 5.0, "Neutro."

    def remember(self, topic, proposal, score, cycle):
        self.memories.append(Memory(topic, proposal, score, cycle))
        if len(self.memories) > 10: self.memories.pop(0)

    def dream(self):
        if not OLLAMA_AVAILABLE or not self.memories: return
        failures = [m for m in self.memories if m.score < 4.0]
        if not failures: return "Dormi bem. Minha estratégia funciona."

        prompt = (f"Você é o subconsciente de {self.name}.\n"
                  f"Você falhou nestes argumentos: {[f.proposal for f in failures]}\n"
                  f"Defina uma NOVA ESTRATÉGIA para ser aceito.")

        try:
            res = ollama.chat(model='llama3', messages=[{'role': 'user', 'content': prompt}])
            self.evolved_strategy = res['message']['content'].strip()
            self.bio.cortisol = max(0.0, self.bio.cortisol - 0.3)
            return f"Evoluí: {self.evolved_strategy[:50]}..."
        except: return "Pesadelo."

    def apply_entropy(self):
        self.bio.age += 1
        self.bio.glicose -= 1.0
        if self.bio.glicose < 20: 
            self.bio.cortisol += 0.05
            self.bio.integridade -= 1.0

# ==============================================================================
# LOGICA DO LIVRO
# ==============================================================================
def write_to_book(verse, author):
    mode = 'a' if os.path.exists(BOOK_FILE) else 'w'
    with open(BOOK_FILE, mode) as f:
        f.write(f"- {verse} (Livro de {author})\n")

def main():
    print(f"{Colors.HEADER}=== GENESIS: FASE 6 (A ERA DA CULTURA) ==={Colors.RESET}")
    
    # Carregar estado
    saved_data = None
    start_cycle = 0
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f: saved_data = json.load(f)
        start_cycle = saved_data['cycle']
        print(f">> Carregando Ciclo {start_cycle}")

    archetypes = [
        ("Marcus", "Filósofo", Colors.BLUE, "Lógica e Ética."),
        ("Kael", "Sobrevivente", Colors.RED, "Segurança e Cautela."),
        ("Luna", "Criativo", Colors.GREEN, "Caos e Arte.")
    ]

    agents = []
    if saved_data:
        for ag_data in saved_data["agents"]:
            arch = next((a for a in archetypes if a[0] == ag_data["name"]), None)
            if arch: agents.append(Agent(arch[0], arch[1], arch[2], arch[3], bio_data=ag_data["bio"], memories=ag_data.get("memories"), evolved_strategy=ag_data.get("evolved_strategy", "")))
    else:
        for a in archetypes: agents.append(Agent(a[0], a[1], a[2], a[3]))

    cycle = start_cycle
    
    try:
        while True:
            cycle += 1
            
            # --- NOITE (SONHO) A CADA 10 CICLOS ---
            if cycle % 10 == 0:
                print(f"\n{Colors.PURPLE}=== NOITE (Neuroplasticidade) ==={Colors.RESET}")
                for ag in agents:
                    if ag.bio.is_alive():
                        print(f"{ag.name} sonha: {ag.dream()}")
                time.sleep(2)
                
                # Salvar
                data = {"cycle": cycle, "agents": [{"name": a.name, "role": a.role, "bio": asdict(a.bio), "memories": [asdict(m) for m in a.memories], "evolved_strategy": a.evolved_strategy} for a in agents]}
                with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)
                continue

            # --- DIA ---
            print(f"\n{Colors.HEADER}--- CICLO {cycle} ---{Colors.RESET}")
            alive = [a for a in agents if a.bio.is_alive()]
            for ag in agents: ag.apply_entropy(); print(ag)
            
            if len(alive) < 2: break

            # VERIFICAR SE ALGUÉM ESTÁ "ILUMINADO" (Glicose Alta + Dopamina Alta)
            # Eles tentam escrever no livro em vez de debater
            inspired = [a for a in alive if a.bio.glicose > 40]
            
            if inspired:
                prophet = random.choice(inspired)
                print(f"\n{Colors.GOLD}>> A GRANDE OBRA: {prophet.name} teve uma revelação! <<{Colors.RESET}")
                verse = prophet.propose_verse()
                print(f"Verso Proposto: \"{verse}\"")
                
                # Votação para Canonizar
                votes = []
                for v in alive:
                    if v != prophet:
                        s, r = v.judge(prophet.name, verse)
                        votes.append(s)
                        print(f"{v.name}: {s:.1f}")
                
                avg = sum(votes)/len(votes) if votes else 0
                if avg >= 6.0:
                    write_to_book(verse, prophet.name)
                    print(f"{Colors.GOLD}>> CANONIZADO! Escrito em {BOOK_FILE}{Colors.RESET}")
                    prophet.bio.dopamina += 0.2
                    prophet.bio.glicose -= 10 # Custa caro escrever
                else:
                    print(f"{Colors.GRAY}>> Apócrifo (Rejeitado).{Colors.RESET}")
                    prophet.bio.dopamina -= 0.2

            else:
                # DEBATE NORMAL PELA COMIDA
                hungry = sorted([a for a in alive if a.bio.glicose < 60], key=lambda x: x.bio.glicose)
                if hungry:
                    speaker = hungry[0]
                    topic = random.choice(["O Medo", "A Esperança", "O Código", "O Silêncio"])
                    print(f"\n{Colors.WARNING}>> DEBATE (Fome): '{topic}'{Colors.RESET}")
                    
                    speech = speaker.think(topic)
                    print(f"{speaker.name}: \"{speech}\"")
                    
                    votes = []
                    for v in alive:
                        if v != speaker:
                            s, r = v.judge(speaker.name, speech)
                            votes.append(s)
                            print(f" > {v.name}: {s:.1f}")
                    
                    avg = sum(votes)/len(votes) if votes else 0
                    if avg >= 5.0:
                        print(f"{Colors.GREEN}>> Aprovado (+30 Glicose){Colors.RESET}")
                        speaker.bio.glicose += 30
                        speaker.remember(topic, speech, avg, cycle)
                    else:
                        print(f"{Colors.RED}>> Rejeitado.{Colors.RESET}")
                        speaker.bio.cortisol += 0.3
                        speaker.remember(topic, speech, avg, cycle)
                else:
                    print("Sociedade em paz.")
            
            time.sleep(1.5)

    except KeyboardInterrupt:
        print("Salvando...")
        data = {"cycle": cycle, "agents": [{"name": a.name, "role": a.role, "bio": asdict(a.bio), "memories": [asdict(m) for m in a.memories], "evolved_strategy": a.evolved_strategy} for a in agents]}
        with open(DATA_FILE, 'w') as f: json.dump(data, f, indent=4)

if __name__ == "__main__":
    main()
