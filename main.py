import streamlit as st
from google.cloud import storage
from PIL import Image
from io import BytesIO
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# ================= CONFIGURAÇÃO DA PÁGINA =================
st.set_page_config(
    page_title="Dashboard Copa do Mundo",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
        .main { 
            background-color: #f7f9fc; 
        }
        h1 { 
            color: #0d5c3a; 
            font-family: 'Arial Black', sans-serif;
        }
        h2, h3 { 
            color: #1e3d59; 
        }
        .stMetric {
            background-color: #ffffff;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-left: 5px solid #f3c220;
        }
    </style>
""", unsafe_allow_html=True)

# Título Principal
st.title("🏆 Analise de Dados Copa do Mundo")
st.markdown("---")

# ================= AUTENTICAÇÃO E DADOS =================

HEADERS = {"Authorization": st.secrets["api"]["API_KEY"]}

client = storage.Client.from_service_account_info(
    st.secrets["gcp_service_account"]
)

bucket_nome = "projeto-copa-aclara"
bucket = client.bucket(bucket_nome)

fifa_ranking_2026 = pd.read_csv('dataset/fifa_ranking_2026-06-08.csv')
fifa_ranking_2022 = pd.read_csv('dataset/fifa_ranking_2022-10-06.csv')

fifa_ranking = pd.merge(
    fifa_ranking_2026[['team','points']],
    fifa_ranking_2022[['team','points']],
    on='team',
    suffixes=('_2026','_2022')
)

partidas = pd.read_csv('dataset/matches_1930_2022.csv')
anos = sorted(partidas['Year'].unique().tolist(), reverse=True)
copas = pd.read_csv('dataset/world_cup.csv')
times = pd.read_csv('dataset/jogadores_com_imagens.csv')
times = times[['team_name', 'team_id']]

# Filtrar apenas partidas do Brasil
partidas_brasil = partidas[
    (partidas["home_team"] == "Brazil") | 
    (partidas["away_team"] == "Brazil")
]

# ================= FILTROS =================
st.sidebar.title("🔍 Filtros de Pesquisa")

oponente_selecionado = st.sidebar.selectbox(
    "Escolha o Oponente:",
    ["Todos"] + list(times['team_name'].unique())
)
ano_selecionado = st.sidebar.selectbox(
    "Escolha o Ano:",
    ["Todos"] + [int(a) for a in anos]
)

# APLICAR FILTROS ANTES DOS GRÁFICOS
if oponente_selecionado == "Todos":
    partidas_filtradas = partidas_brasil
else:
    partidas_filtradas = partidas_brasil[
        ((partidas_brasil["home_team"] == "oponente_selecionado") | (partidas_brasil["away_team"] == oponente_selecionado)) &
        ((partidas_brasil["home_team"] == "Brazil") | (partidas_brasil["away_team"] == "Brazil"))
    ]
    partidas_filtradas = partidas_brasil[
        ((partidas_brasil["home_team"] == "Brazil") & (partidas_brasil["away_team"] == oponente_selecionado)) |
        (partidas_brasil["home_team"] == oponente_selecionado) & (partidas_brasil["away_team"] == "Brazil")
    ]

    fifa_ranking = fifa_ranking[(fifa_ranking['team'] == oponente_selecionado)]

if ano_selecionado != "Todos":
    partidas_filtradas = partidas_filtradas[(partidas_filtradas["Year"] == int(ano_selecionado))]

# Contar resultados
vitorias_brasil = 0
vitorias_oponente = 0
empates = 0

for _, row in partidas_filtradas.iterrows():
    if row["home_team"] == "Brazil":
        if row["home_score"] > row["away_score"]: vitorias_brasil += 1
        elif row["home_score"] < row["away_score"]: vitorias_oponente += 1
        else: empates += 1
    else:
        if row["away_score"] > row["home_score"]: vitorias_brasil += 1
        elif row["away_score"] < row["home_score"]: vitorias_oponente += 1
        else: empates += 1


# ================= VISUALIZAÇÕES =================

# 1. Seção de Cards/Métricas Rápidas para o Brasil
st.subheader("📊 Desempenho do Brasil")
col1, col2, col3, col4 = st.columns(4)

col1.metric(label="Total de Partidas", value=len(partidas_filtradas))
col2.metric(label="Vitórias do Brasil", value=vitorias_brasil)
col3.metric(label="Empates", value=empates)
col4.metric(label="Derrotas", value=vitorias_oponente)

st.markdown("---")

#========= VITORIAS DO BRASIL POR COPA ==============
st.subheader("Vitórias do Brasil por copa")
vitorias_por_copa = partidas_brasil.groupby('Year').apply(
    lambda x: sum(
        ((x['home_team'] == 'Brazil') & (x['home_score'] > x['away_score'])) |
        ((x['away_team'] == 'Brazil') & (x['away_score'] > x['home_score']))
    )
).reset_index()

vitorias_por_copa.columns = ['Ano', 'Vitórias']

fig = px.line(
    vitorias_por_copa,
    x='Ano',
    y='Vitórias',
    markers=True,
    line_shape="linear"
)

fig.update_traces(line=dict(color="#009c3b", width=3), marker=dict(size=10))
fig.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")

st.plotly_chart(fig, use_container_width=True)

# 2. Gráficos em Colunas lado a lado
linha1_col1, linha1_col2 = st.columns(2)

#========= RANKING CAMPEÕES ==============
with linha1_col1:
    st.subheader("🥇 Ranking de Campeões")
    
    titulos = copas["Champion"].value_counts().reset_index()
    titulos.columns = ["Champion", "titulos"]

    fig1 = px.bar(
        titulos,
        x="titulos",
        y="Champion",
        orientation="h",
        color="titulos",
        color_continuous_scale="Viridis",
        text="titulos",
    )
    fig1.update_traces(textposition="outside", cliponaxis=False)
    fig1.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis_title="Copas Conquistadas",
        yaxis_title="País",
        coloraxis_showscale=False,
        margin=dict(t=20, b=20, l=20, r=20)
    )
    st.plotly_chart(fig1, use_container_width=True)

#========= JOGOS BRASIL X OPONENTE ==============
with linha1_col2:
    if oponente_selecionado == "Todos":
        titulo_graf2 = "Histórico Geral do Brasil em Copas"
        nomes_barras = ["Vitórias do Brasil", "Derrotas do Brasil", "Empates"]
    else:
        titulo_graf2 = f"Confronto direto: Brasil x {oponente_selecionado}"
        nomes_barras = ["Brasil", oponente_selecionado, "Empates"]

    st.subheader(titulo_graf2)
    
    fig2 = go.Figure(data=[
        go.Bar(
            x=nomes_barras,
            y=[vitorias_brasil, vitorias_oponente, empates],
            marker=dict(
                color=["#009c3b", "#1e3d59", "#f3c220"],
                line=dict(color="#ffffff", width=2)
            ),
            text=[vitorias_brasil, vitorias_oponente, empates],
            textposition="outside"
        )
    ])

    fig2.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        yaxis_title="Número de partidas",
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20)
    )
    
    st.plotly_chart(fig2, use_container_width=True)

#========= FIFA RANKING ==============
st.subheader("Fifa Ranking 2022 x 2026")

df = fifa_ranking.set_index('team')

fifa_long = fifa_ranking.melt(
    id_vars='team',
    value_vars=['points_2026','points_2022'],
    var_name='year',
    value_name='points'
)

fig3 = px.bar(fifa_long, x="team", y="points", color="year", barmode="group")
fig3.update_xaxes(range=[-0.5, 9.5])
st.plotly_chart(fig3, width="stretch")

#========= MEDIA GOLS: ANFITRIAO X VISITANTE ==============
linha3_col1, linha3_col2 = st.columns(2)
with linha3_col1:
    st.subheader("Média de gols: Anfitrião x Visitante")

    anfitriao_casa = partidas[partidas["home_team"] == partidas["Host"]]
    anfitriao_fora = partidas[partidas["away_team"] == partidas["Host"]]

    gols_anfitriao = pd.concat([
        anfitriao_casa["home_score"],
        anfitriao_fora["away_score"]
    ])

    gols_visitante = pd.concat([
        anfitriao_casa["away_score"],
        anfitriao_fora["home_score"]
    ])

    dados_grafico = pd.DataFrame({
        "Time": ["Anfitrião", "Visitante"],
        "Média de gols": [gols_anfitriao.mean(), gols_visitante.mean()]
    })

    fig4 = go.Figure(data=[
        go.Bar(
            x=dados_grafico["Time"],
            y=dados_grafico["Média de gols"],
            marker=dict(
                color=["#009c3b", "#1e3d59"],
                line=dict(color="#ffffff", width=2)
            ),
            text=dados_grafico["Média de gols"].round(2),
            textposition="outside"
        )
    ])

    fig4.update_layout(
        yaxis_title="Média de gols por jogo",
        showlegend=False,
        margin=dict(t=40, b=20, l=20, r=20)
    )

    st.plotly_chart(fig4, use_container_width=True)

#========= COPAS: ANFITRIAO X VISITANTE ==============
with linha3_col2:
    st.subheader("Vencedores de copa: Anfitrião x Visitante")

    copas_raw = pd.read_csv('dataset/world_cup.csv')

    copas_raw["Vencedor"] = copas_raw.apply(
        lambda row: "Anfitrião" if row["Champion"] == row["Host"] else "Visitante",
        axis=1
    )

    vitorias_anfitriao = copas_raw["Vencedor"].value_counts().reset_index()
    vitorias_anfitriao.columns = ["Vencedor", "Quantidade"]

    fig5 = px.pie(
        vitorias_anfitriao,
        names="Vencedor",
        values="Quantidade",
        color="Vencedor",
        color_discrete_map={
            "Anfitrião": "#009c3b",
            "Visitante": "#1e3d59"
        },
    )

    fig5.update_traces(textinfo="percent+label")
    fig5.update_layout(
        margin=dict(t=40, b=20, l=20, r=20)
    )

    st.plotly_chart(fig5, use_container_width=True)

#========= JOGADORES SELEÇÃO ==============

def redimensionar_imagem(imagem_bytes, tamanho=(250, 300)):
    """Redimensiona imagem para tamanho fixo"""
    img = Image.open(BytesIO(imagem_bytes))
    img = img.resize(tamanho, Image.Resampling.LANCZOS)
    return img


if oponente_selecionado == 'Todos':
    time_id = 2192 #Brasil
    titulo_graf = "Seleção Brasileira"
else:
    time_id = times.loc[times["team_name"] == oponente_selecionado, 'team_id'].values[0]
    titulo_graf = f"Seleção {oponente_selecionado}"

url_jogadores = f"https://footballdata.io/api/v1/players?team_id={time_id}"
resp = requests.get(url_jogadores, headers=HEADERS)
jogadores = resp.json()["data"]

st.title(titulo_graf)
cols = st.columns(4)

for idx, jogador in enumerate(jogadores):
    player_id = jogador["player_id"]
    caminho = f"imagens_jogadores/{player_id}.png"
    blob = bucket.blob(caminho)

    if blob.exists():
        imagem_bytes = blob.download_as_bytes()
        
        imagem = redimensionar_imagem(imagem_bytes, tamanho=(250, 300))

        with cols[idx % 4]:
            with st.container(border=True):
                st.image(imagem, use_container_width=True)
                st.markdown(f"##### {jogador['first_name']}")
                st.markdown(f"""
                **Posição:** {jogador['position']}  
                **Idade:** {jogador['age']}  
                **Altura:** {jogador['height_cm']} cm  
                **Peso:** {jogador['weight_kg']} kg
                """)