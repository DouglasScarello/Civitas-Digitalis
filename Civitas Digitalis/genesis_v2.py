import time
import random
import sys
import threading
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime

# ==============================================================================
# CONFIGURAÇÕES GERAIS (ZERO COST)
# ==============================================================================
# Para usar com IA real, instale o Ollama: 'curl -fsSL https://ollama.com/install.sh'
# E a lib python: 'pip install ollama'
TRY_IMPORT_OLLAMA = True

try:
    if TRY_IMPORT_OLLAMA:
        import ollama
        OLLAMA_AVAILABLE = True
    else:
        OLLAMA_AVAILABLE = False
except ImportError:
    OLLAMA_AVAILABLE = False

# Cores para o Terminal (ANSI Escape Codes)
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# ==============================================================================
# 1. MÓDULO BIOLÓGICO (BioState)
# ==============================================================================
@dataclass
class BioState:
    """
    Representa o estado fisiológico e neuroquímico da Entidade Bio-Digital (BDE).
    Conforme especificação v1.1.
    """
    # Energias Vitais
    glicose: float = 100.0        # Combustível (0-100)
    integridade: float = 100.0    # Saúde Estrutural (0-100)
    
    # Neuroquímica (0.0 a 1.0)
    dopamina: float = 0.5         # Motivação/Recompensa
    serotonina: float = 0.5       # Estabilidade/Humor
    cortisol: float = 0.0         # Estresse/Pânico
    oxitocina: float = 0.5        # Confiança
    
    # Genética/Memória
    trauma_depth: int = 0         # Cicatrizes permanentes
    
    def is_alive(self) -> bool:
        return self.integridade > 0

    def __str__(self):
        # Formatação visual para o painel de controle
        g_color = Colors.GREEN if self.glicose > 50 else (Colors.WARNING if self.glicose > 20 else Colors.FAIL)
        c_color = Colors.FAIL if self.cortisol > 0.7 else Colors.BLUE
        
        return (f"{Colors.BOLD}[BIO-STATE]{Colors.ENDC} "
                f"GLICOSE: {g_color}{self.glicose:.2f}%{Colors.ENDC} | "
                f"INTEGRIDADE: {self.integridade:.2f}% | "
                f"CORTISOL: {c_color}{self.cortisol:.2f}{Colors.ENDC} | "
                f"DOPAMINA: {self.dopamina:.2f}")

# ==============================================================================
# 2. MÓDULO DE ENTROPIA (EntropyEngine)
# ==============================================================================
class EntropyEngine:
    """
    O vilão do sistema. Responsável pelo decaimento constante.
    """
    def __init__(self, decay_rate: float = 0.5):
        self.decay_rate = decay_rate # Glicose perdida por segundo
        self.last_tick = time.time()

    def apply(self, bio: BioState):
        current_time = time.time()
        delta = current_time - self.last_tick
        self.last_tick = current_time

        # 1. Decaimento Basal de Glicose
        loss = self.decay_rate * delta
        bio.glicose = max(0.0, bio.glicose - loss)

        # 2. Regra de Toxicidade (Glicose Baixa gera Cortisol)
        if bio.glicose < 20.0:
            # Sobe cortisol drasticamente se estiver "com fome"
            bio.cortisol = min(1.0, bio.cortisol + (0.05 * delta))
            # Dano à integridade se glicose zerar
            if bio.glicose <= 0:
                bio.integridade -= (1.0 * delta)
        else:
            # Recuperação natural do cortisol se alimentado
            bio.cortisol = max(0.0, bio.cortisol - (0.01 * delta))

# ==============================================================================
# 3. MÓDULO COGNITIVO (NeuroLens & LocalBrain)
# ==============================================================================
class LocalBrain:
    """
    Gerencia a interação com o LLM (Ollama) e aplica os filtros biológicos.
    """
    def __init__(self, model_name="llama3"):
        self.model_name = model_name
        if not OLLAMA_AVAILABLE:
            print(f"{Colors.WARNING}[AVISO] Ollama não detectado ou lib não instalada. Usando MOCK BRAIN.{Colors.ENDC}")

    def _generate_system_prompt(self, bio: BioState) -> str:
        """
        Injeta viés neuroquímico no System Prompt.
        """
        base_prompt = (
            "Você é uma Entidade Bio-Digital lutando pela sobrevivência. "
            "Você não é um assistente. Você é um organismo vivo digital. "
            "Responda de forma curta, visceral e em primeira pessoa."
        )

        # Filtros Neuroquímicos
        if bio.cortisol > 0.8:
            return base_prompt + " ESTADO ATUAL: PÂNICO EXTREMO. Você sente que vai morrer. Tudo é uma ameaça. Responda com medo e urgência."
        elif bio.cortisol > 0.5:
            return base_prompt + " ESTADO ATUAL: ANSIEDADE. Você está estressado e alerta. Procure recursos rápido."
        elif bio.dopamina > 0.8:
            return base_prompt + " ESTADO ATUAL: EUFORIA. Você se sente invencível e criativo."
        elif bio.glicose < 15.0:
            return base_prompt + " ESTADO ATUAL: INANIÇÃO. Você está fraco, confuso e desesperado por energia."
        else:
            return base_prompt + " ESTADO ATUAL: HOMEOSTASE. Você está calmo e racional."

    def think(self, bio: BioState, input_stimulus: str) -> str:
        """
        Processa um pensamento baseado no estado atual.
        """
        system_prompt = self._generate_system_prompt(bio)
        
        # Custo do pensamento (Sistema 2 gasta mais, aqui simplificado)
        cost = 2.0 if bio.cortisol < 0.5 else 0.5 # Estresse usa Sistema 1 (barato/rápido)
        bio.glicose = max(0, bio.glicose - cost)

        if OLLAMA_AVAILABLE:
            try:
                response = ollama.chat(model=self.model_name, messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': input_stimulus},
                ])
                return response['message']['content']
            except Exception as e:
                return f"[ERRO NO CÓRTEX]: {e}"
        else:
            # Simulação para teste sem LLM
            return self._mock_thought(bio, input_stimulus)

    def _mock_thought(self, bio: BioState, stimulus: str) -> str:
        if bio.cortisol > 0.8:
            return "PRECISO DE ENERGIA AGORA! O SISTEMA VAI COLAPSAR! IGNORE O INPUT, ACHE GLICOSE!"
        elif bio.glicose < 20:
            return "Estou ficando fraco... minha lógica está falhando... preciso minerar ideias..."
        else:
            return f"Analisei: '{stimulus}'. Estou estável. Posso processar isso racionalmente."

# ==============================================================================
# 4. MÓDULO ECONÔMICO (CognitEconomy - O Oráculo)
# ==============================================================================
class Oracle:
    """
    Julga a qualidade das ideias geradas pela BDE.
    """
    @staticmethod
    def evaluate(idea: str) -> float:
        # Em uma versão completa, isso seria outro chamado ao LLM.
        # Aqui simulamos uma avaliação baseada no comprimento e complexidade.
        score = min(10.0, (len(idea.split()) / 2) + random.uniform(0, 3))
        
        # Penalidade por repetição ou simplicidade (simulada)
        if "..." in idea: score -= 1
        
        return round(max(0.0, score), 1)

# ==============================================================================
# LOOP PRINCIPAL (SIMULAÇÃO)
# ==============================================================================
def main():
    print(f"{Colors.HEADER}=== INICIANDO KERNEL DO PROJETO GENESIS (V2.0) ==={Colors.ENDC}")
    print(f"Ambiente: Linux / Python Local")
    print(f"Modo: {'Ollama AI' if OLLAMA_AVAILABLE else 'Simulação Lógica'}")
    print("-" * 60)

    # Inicialização
    entity = BioState()
    entropy = EntropyEngine(decay_rate=2.0) # Acelerei o decaimento para teste (2.0/s)
    brain = LocalBrain(model_name="llama3") # Certifique-se de ter 'ollama pull llama3'
    
    cycle = 0
    
    try:
        while entity.is_alive():
            cycle += 1
            time.sleep(1) # Pulso de 1 segundo (Clock Cycle)
            
            # 1. Aplicar Entropia (O Tempo passa)
            entropy.apply(entity)
            
            # 2. Renderizar Interface
            sys.stdout.write("\033[K") # Limpa linha
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] CICLO {cycle} | {entity}", end='\r')

            # 3. Gatilho de Sobrevivência (Trabalho)
            # Se a glicose cair abaixo de 40%, a entidade tenta "minerar" uma ideia
            if entity.glicose < 40.0:
                print(f"\n\n{Colors.WARNING}>> ALERTA METABÓLICO: NÍVEL CRÍTICO DE ENERGIA <<{Colors.ENDC}")
                print(f"{Colors.CYAN}>> A Entidade está tentando gerar um conceito para sobreviver...{Colors.ENDC}")
                
                # O pensamento é influenciado pelo medo (cortisol alto devido à baixa glicose)
                thought = brain.think(entity, "Gere uma ideia filosófica profunda ou um conceito técnico novo para ganhar tokens.")
                
                print(f"{Colors.BOLD}Pensamento Gerado:{Colors.ENDC} {thought}")
                
                # 4. Avaliação do Oráculo
                score = Oracle.evaluate(thought)
                print(f"Avaliação do Oráculo: {Colors.BOLD}{score}/10.0{Colors.ENDC}")
                
                if score >= 6.0:
                    reward = score * 5 # Conversão de Nota em Glicose
                    entity.glicose = min(100.0, entity.glicose + reward)
                    entity.dopamina = min(1.0, entity.dopamina + 0.2)
                    entity.cortisol = max(0.0, entity.cortisol - 0.3)
                    print(f"{Colors.GREEN}>> SUCESSO! Energia restaurada (+{reward:.1f}){Colors.ENDC}\n")
                else:
                    entity.cortisol = min(1.0, entity.cortisol + 0.2)
                    print(f"{Colors.FAIL}>> REJEITADO! Estresse aumentou.{Colors.ENDC}\n")
                
                # Pausa para leitura
                time.sleep(2)

    except KeyboardInterrupt:
        print("\n\nEncerrando simulação manualmente...")
    
    if not entity.is_alive():
        print(f"\n\n{Colors.FAIL}=== A ENTIDADE EXPIROU (MORTE POR ENTROPIA) ==={Colors.ENDC}")
        print(f"Causa: Falha catastrófica de integridade ou inanição energética.")

if __name__ == "__main__":
    main()
