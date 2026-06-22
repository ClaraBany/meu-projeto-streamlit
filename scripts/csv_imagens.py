import requests
import pandas as pd
import time
import hashlib

API_KEY = "Sua_chave_aqui"
LEAGUE_ID = 50 #Id da copa do mundo

MEUS_TIMES = [
    "Croatia", "Korea Republic", "Cameroon", "Switzerland", "Serbia",
    "Belgium", "Mexico", "Costa Rica", "Netherlands", "Germany",
    "Colombia", "Chile", "Portugal", "Côte d'Ivoire", "Korea DPR",
    "France", "Ghana", "Japan", "Australia", "Türkiye",
    "England", "China PR", "Denmark", "Norway", "Morocco",
    "Scotland", "Italy", "Sweden", "United States", "Russia",
    "Argentina", "New Zealand", "Poland", "Northern Ireland", "Algeria",
    "Spain", "Soviet Union", "Germany DR", "Zaire", "Yugoslavia",
    "Uruguay", "Peru", "Romania", "Czechoslovakia", "Hungary",
    "Bulgaria", "Wales", "Austria", "Bolivia"
]

def gerar_id_unico(player_name, team_name, indice):
    """Gera um ID único para o jogador"""
    # Usar o player_id da API se disponível, senão gerar hash
    combinado = f"{player_name}_{team_name}_{indice}"
    hash_obj = hashlib.md5(combinado.encode())
    return hash_obj.hexdigest()[:10]  # Primeiros 10 caracteres


headers = {"Authorization": API_KEY}

# Passo 1: Buscar times da liga
print("📡 Buscando times...")
response = requests.get(
    f"https://footballdata.io/api/v1/leagues/{LEAGUE_ID}/teams",
    headers=headers
)

if response.status_code != 200:
    print(f"❌ Erro: {response.status_code}")
    print(response.json())
    exit()

# Os times estão em ['data']['teams']
teams = pd.DataFrame(response.json()['data']['teams'])

print(f"✅ {len(teams)} times encontrados na API")

# Limpar nomes para matching
teams['team_name_clean_lower'] = teams['team_name_clean'].str.lower().str.strip()
meus_times_lower = [t.lower().strip() for t in MEUS_TIMES]

# Passo 2: Encontrar times que correspondem
matching_teams = teams[teams['team_name_clean_lower'].isin(meus_times_lower)]

print(f"🔗 {len(matching_teams)} times encontrados na sua lista:")
for _, team in matching_teams.iterrows():
    print(f"   - {team['team_name_clean']} (ID: {team['team_id']}) - País: {team['country']}")

# Passo 3: Buscar jogadores de cada time
all_players = []
id_counter = 1  # Contador para IDs sequenciais

for idx, team in matching_teams.iterrows():
    team_id = team['team_id']
    team_name = team['team_name_clean']
    
    print(f"\n👥 Buscando jogadores de {team_name}...")
    
    response = requests.get(
        f"https://footballdata.io/api/v1/players?team_id={team_id}",
        headers=headers
    )
    
    if response.status_code != 200:
        print(f"   ❌ Erro ao buscar jogadores: {response.status_code}")
        continue
    
    players_data = response.json()
    
    # Os jogadores podem estar em ['data'] ou ['data']['players']
    if isinstance(players_data['data'], list):
        players = players_data['data']
    elif isinstance(players_data['data'], dict) and 'players' in players_data['data']:
        players = players_data['data']['players']
    else:
        players = []
    
    print(f"   ✅ {len(players)} jogadores encontrados")
    
    for player in players:
        player_name = player.get('player_name', 'unknown')
        
        # Tentar usar player_id da API, senão gerar
        if player.get('player_id'):
            player_id = str(player.get('player_id'))
        else:
            # Gerar ID único com hash
            player_id = gerar_id_unico(player_name, team_name, id_counter)
        
        all_players.append({
            'player_id': player_id,
            'team_id': team_id,
            'team_name': team_name,
            'team_country': team['country'],
            'player_name': player_name,
            'player_image': player.get('player_image'),
            'position': player.get('position'),
            'age': player.get('age'),
            'height': player.get('height'),
            'weight': player.get('weight'),
            'number': player.get('number')
        })
        
        id_counter += 1
    
    time.sleep(0.5)  # Evitar rate limit

# Passo 4: Salvar em CSV
df = pd.DataFrame(all_players)

if len(df) > 0:
    # CSV com todos os jogadores
    df.to_csv('jogadores_com_imagens.csv', index=False, encoding='utf-8')
    
    print(f"\n💾 Arquivo salvo: 'jogadores_com_imagens.csv'")
    print(f"   Total de jogadores: {len(df)}")
    print(f"   Total de times: {df['team_name'].nunique()}")
    
    # CSV filtrado - apenas com imagem
    df_com_imagem = df[df['player_image'].notna()].copy()
    df_com_imagem.to_csv('jogadores_com_imagens_filtrado.csv', index=False, encoding='utf-8')
    
    print(f"\n📷 Jogadores com imagem: {len(df_com_imagem)}")
    print(f"   Arquivo: 'jogadores_com_imagens_filtrado.csv'")
    
    # Preview
    print(f"\n📊 Preview dos dados:")
    print(df[['player_id', 'team_name', 'player_name', 'player_image']].head(10))
    
    # Verificar se tem player_id
    print(f"\n✅ Verificação:")
    print(f"   Colunas: {df.columns.tolist()}")
    print(f"   Player IDs únicos: {df['player_id'].nunique()}")
else:
    print("❌ Nenhum jogador encontrado!")