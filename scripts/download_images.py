import os
import sys
import time
import random
import pandas as pd
import requests
from urllib.parse import urlparse

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
]

def baixar_imagem(url, caminho_arquivo):
    try:
        headers = {"User-Agent": random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=30, stream=True)
        
        if response.status_code == 200:
            with open(caminho_arquivo, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return True
        return False
    except Exception as e:
        print(f"Erro: {e}")
        return False


def baixar_imagens(csv_path, pasta_destino):
    os.makedirs(pasta_destino, exist_ok=True)
    df = pd.read_csv(csv_path)
    
    # Filtrar apenas com imagem
    df = df[df['player_image'].notna()].copy()
    
    print(f"📷 Baixando {len(df)} imagens para: {pasta_destino}\n")
    
    sucesso = 0
    erro = 0
    
    for i, row in df.iterrows():
        url = str(row["player_image"]).strip()
        player_id = row["player_id"]
        
        # Extensão
        extensao = os.path.splitext(urlparse(url).path)[1] or ".jpg"
        nome_arquivo = f"{player_id}{extensao}"
        caminho = os.path.join(pasta_destino, nome_arquivo)
        
        print(f"[{i+1}/{len(df)}] {nome_arquivo}...", end=" ")
        
        if baixar_imagem(url, caminho):
            print("✅")
            sucesso += 1
        else:
            print("❌")
            erro += 1
        
        time.sleep(random.uniform(1, 2))
    
    print(f"\n✅ Sucesso: {sucesso} | ❌ Erros: {erro}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("python download_images.py jogadores_com_imagens.csv pasta_destino")
        sys.exit(1)
    
    baixar_imagens(sys.argv[1], sys.argv[2])