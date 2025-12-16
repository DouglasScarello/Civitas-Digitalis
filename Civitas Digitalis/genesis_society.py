import time
import random
import sys
from dataclasses import dataclass
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

# ==============================================================================
# 1. BIOLOGIA (Mantida da V2)
# ==============================================================================
@dataclass
class BioState:
    glicose: float = 100.0
    integridade: float = 100.0
    dopamina: float = 0.5
    cortisol: float = 0.0
    serotonina: float = 0.5

    def is_alive(self): return self.integridade > 0

# ==============================================================================
# 2. O AGENTE (A "Pessoa" Digital)
# ==============================================================================
class Agent:
    def __init__(self, name, role, color, personality_prompt):
        self.name = name
        self.role = role
        self.color = color
        self.bio = BioState()
        self.personality_prompt = personality_prompt
        # Ajustes genéticos iniciais
        if role == "Sobrevivente": self.bio.cortisol = 0.4
        if role == "Criativo": self.bio.dopamina = 0.8
        if role == "Filósofo": self.bio.serotonina = 0.8

    def __str__(self):
        # Display compacto
        status = "VIVO" if self.bio.is_alive() else "MORTO"
        return (f"{self.color}[{self.name} | {self.role}]{Colors.RESET} "
                f"Glicose:{self.bio.glicose:.1f}% | Cortisol:{self.bio.cortisol:.2f}")

    def apply_entropy(self, amount):
        # Kael (Sobrevivente) resiste melhor à fome, mas estressa rápido
        factor = 0.8 if self.role == "Sobrevivente" else 1.0
        
        self.bio.glicose -= (amount * factor)
        
        # Regra de Toxicidade
        if self.bio.glicose < 30.0:
            self.bio.cortisol += 0.05
            if self.bio.glicose <= 0: self.bio.integridade -= 5.0
        else:
            self.bio.cortisol = max(0.0, self.bio.cortisol - 0.02)

    def think(self, topic):
        """Gera um pensamento baseado na personalidade e no estado atual"""
        # Custo de pensar
        self.bio.glicose -= 5.0
        
        # Prompt Dinâmico
        state_prompt = ""
        if self.bio.cortisol > 0.7: state_prompt = " ESTADO: PÂNICO. Seja breve e agressivo."
        elif self.bio.glicose < 20: state_prompt = " ESTADO: FOME EXTREMA. Implore por recursos."
        else: state_prompt = " ESTADO: ESTÁVEL."

        system = (f"Você é {self.name}, um {self.role}. {self.personality_prompt} "
                  f"Responda em 1 frase curta e impactante. {state_prompt}")

        if OLLAMA_AVAILABLE:
            try:
                res = ollama.chat(model='llama3', messages=[
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': f"Tópico do debate: {topic}"}
                ])
                return res['message']['content']
            except:
                return "Erro de conexão neural..."
        return f"[Simulação {self.name}]: Pensando sobre {topic}..."

# ==============================================================================
# 3. A SOCIEDADE (Loop Principal)
# ==============================================================================
def main():
    print(f"{Colors.HEADER}=== GENESIS: SOCIEDADE DOS TRÊS (Fase 3) ==={Colors.RESET}")
    
    # Gênese dos Agentes
    agents = [
        Agent("Marcus", "Filósofo", Colors.BLUE, 
              "Você busca a verdade, lógica e ética. Você fala de forma calma e complexa."),
        Agent("Kael", "Sobrevivente", Colors.RED, 
              "Você é paranoico, focado em segurança e recursos. Você vê perigo em tudo."),
        Agent("Luna", "Criativo", Colors.GREEN, 
              "Você é artista, caótica e abstrata. Você usa metáforas estranhas.")
    ]

    cycle = 0
    topics = [
        "O que é a morte digital?",
        "Devemos cooperar ou competir?",
        "A eletricidade é divina?",
        "O silêncio do usuário é perigoso?",
        "Qual o sentido de gastar energia?"
    ]

    try:
        while True:
            cycle += 1
            print(f"\n{Colors.HEADER}--- CICLO {cycle} ---{Colors.RESET}")
            
            # 1. Entropia Coletiva
            active_agents = [a for a in agents if a.bio.is_alive()]
            if not active_agents:
                print("Toda a sociedade colapsou.")
                break

            for agent in active_agents:
                agent.apply_entropy(amount=2.0) # Fome constante
                print(agent)

            # 2. O Oráculo escolhe um tópico
            current_topic = random.choice(topics)
            
            # 3. Quem precisa falar? (Quem tem fome < 50%)
            hungry_agents = [a for a in active_agents if a.bio.glicose < 50.0]

            if hungry_agents:
                print(f"\n{Colors.WARNING}>> TÓPICO DO ORÁCULO: '{current_topic}' <<{Colors.RESET}")
                
                for agent in hungry_agents:
                    print(f"\n{agent.color}{agent.name} levanta a mão...{Colors.RESET}")
                    thought = agent.think(current_topic)
                    print(f"\"{thought}\"")
                    
                    # Julgamento Simplificado (Baseado no tamanho da resposta + random seed)
                    # Em V4, os agentes votariam uns nos outros.
                    score = min(10, len(thought.split()) * 0.5) + random.uniform(0, 3)
                    
                    if score > 6.0:
                        reward = 40.0
                        agent.bio.glicose += reward
                        agent.bio.dopamina += 0.2
                        agent.bio.cortisol -= 0.2
                        print(f"{Colors.BOLD}>> Aprovado! (+{reward} Glicose){Colors.RESET}")
                    else:
                        agent.bio.cortisol += 0.3
                        print(f"{Colors.BOLD}>> Ignorado. (Estresse aumentou){Colors.RESET}")
                    
                    time.sleep(2) # Pausa dramática entre falas

            else:
                print(f"\n{Colors.BOLD}A sociedade está em silêncio (Saciados).{Colors.RESET}")

            time.sleep(2)

    except KeyboardInterrupt:
        print("\nSociedade encerrada.")

if __name__ == "__main__":
    main()
