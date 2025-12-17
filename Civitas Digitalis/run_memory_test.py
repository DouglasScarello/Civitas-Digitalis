from memory_core import MemoryCore
import time

def test_memory():
    print("🧠 Inicializando Cortex de Teste...")
    brain = MemoryCore("Test_Subject_01")
    
    # 1. Limpar memórias antigas (opcional, para teste limpo)
    # brain.client.delete_collection(brain.collection.name)
    # Vamos usar o método clear_memory que adicionei para facilitar
    # brain.clear_memory() 
    
    # 2. Inserir memórias falsas com contextos variados
    print("💾 Inserindo memórias...")
    brain.store_experience("Eu odeio quando falta glicose, sinto tremores.", type="trauma")
    brain.store_experience("A luz azul me acalma e me faz pensar melhor.", type="preference")
    brain.store_experience("Kael tentou me enganar no último ciclo.", type="social_conflict")
    
    # 3. Testar busca semântica (RAG)
    print("\n🔍 Teste 1: Buscando por 'fome' (Semântica de Glicose)...")
    memories = brain.recall_relevant("Estou com muita fome")
    print(f"   Recuperado: {memories}")
    
    print("\n🔍 Teste 2: Buscando por 'confiança' (Semântica Social)...")
    memories = brain.recall_relevant("Posso confiar nos outros?")
    print(f"   Recuperado: {memories}")

if __name__ == "__main__":
    test_memory()
