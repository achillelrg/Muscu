import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials

# Configuration de la page
st.set_page_config(page_title="Sport Analytics 3D", layout="wide")

# Connexion via les secrets de Streamlit
def get_data():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # On récupère les credentials depuis les secrets de Streamlit
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], 
        scopes=scope
    )
    client = gspread.authorize(creds)
    
    # Remplace par le NOM exact de ton fichier Google Sheets
    sheet = client.open("MUSCU").worksheet("DATA")
    
    # 2. Récupère uniquement les colonnes A à F (pour éviter les colonnes vides à droite)
    # head=2 car tes titres (Date, Exercice...) sont sur la ligne 2
    data = sheet.get_all_records(head=2, default_blank=None)
    
    # 3. On transforme en DataFrame
    df = pd.DataFrame(data)
    
    # 4. On s'assure de ne garder que les colonnes qui ont un nom
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    # On filtre les lignes où l'exercice est vide (au cas où il y aurait des résidus)
    df = df[df['Exercice'] != ""]
    return df

try:
    df = get_data()
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)

    # Sidebar pour les filtres
    st.sidebar.header("Filtres")
    muscle = st.sidebar.selectbox("Groupe Musculaire", df['Muscle'].unique())
    exercices_dispo = df[df['Muscle'] == muscle]['Exercice'].unique()
    exercice = st.sidebar.selectbox("Exercice", exercices_dispo)

    # Filtrage des données
    df_plot = df[df['Exercice'] == exercice].sort_values('Date')

    st.title(f"Progression : {exercice}")

    # Génération du graphique 3D
    fig = go.Figure()

    # Définition des couleurs (dégradés)
    colors = ['#1f77b4', '#63aaff', '#a5d8ff', '#003366'] 

    for i, s in enumerate(sorted(df_plot['Série'].unique())):
        subset = df_plot[df_plot['Série'] == s]
        fig.add_trace(go.Scatter3d(
            x=subset['Date'],
            y=subset['Reps'],
            z=subset['Poids'],
            mode='lines+markers',
            name=f'Série {s}',
            line=dict(color=colors[i % len(colors)], width=4),
            marker=dict(size=4)
        ))

    fig.update_layout(
        scene=dict(
            xaxis_title='Date',
            yaxis_title='Reps',
            zaxis_title='Poids (kg)'
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=700
    )

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Erreur de connexion : {e}")