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
    st.sidebar.header("🎯 Filtres")
    muscle = st.sidebar.selectbox("Groupe Musculaire", df['Muscle'].unique())
    exercices_dispo = df[df['Muscle'] == muscle]['Exercice'].unique()
    exercice = st.sidebar.selectbox("Exercice", exercices_dispo)

    # Sidebar pour la visualisation
    st.sidebar.markdown("---")
    st.sidebar.header("⚙️ Visualisation")
    
    # Option pour relier tous les points
    connect_all = st.sidebar.checkbox("Relier les séances (Chronologique)", value=False, help="Relie tous les points par ordre chronologique, indépendamment des séries.")
    
    # Option pour l'angle de vue
    view_options = {
        "Défaut 🔄": None,
        "Poids / Reps (Profil) 🏋️": dict(eye=dict(x=2.5, y=0, z=0)),
        "Poids / Date (Face) 📅": dict(eye=dict(x=0, y=2.5, z=0)),
        "Reps / Date (Dessus) 🔁": dict(eye=dict(x=0, y=0, z=2.5))
    }
    selected_view = st.sidebar.radio("Angle de vue Caméra", list(view_options.keys()))

    # Filtrage des données
    df_plot = df[df['Exercice'] == exercice].sort_values('Date')
    
    # Métriques clés en haut de page
    st.title(f"🚀 Progression : {exercice}")
    
    if not df_plot.empty:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Max Poids", f"{df_plot['Poids'].max()} kg", f"{df_plot['Poids'].iloc[-1] - df_plot['Poids'].iloc[0]:.1f} kg")
        with col2:
            st.metric("Max Reps", f"{df_plot['Reps'].max()}", f"{int(df_plot['Reps'].iloc[-1] - df_plot['Reps'].iloc[0])}")
        with col3:
            st.metric("Volume Total (Tonne)", f"{(df_plot['Poids'] * df_plot['Reps']).sum() / 1000:.1f} T")

    # Génération du graphique 3D
    fig = go.Figure()

    # Définition des couleurs (dégradés)
    colors = ['#1f77b4', '#63aaff', '#a5d8ff', '#003366', '#d62728', '#ff7f0e'] 

    if connect_all:
        # Trace unique reliant tous les points par ordre chronologique
        # On peut colorer par série ou simplement uniformément
        fig.add_trace(go.Scatter3d(
            x=df_plot['Date'],
            y=df_plot['Reps'],
            z=df_plot['Poids'],
            mode='lines+markers',
            name='Progression Globale',
            line=dict(color='#ff7f0e', width=6),
            marker=dict(size=5, color=df_plot['Poids'], colorscale='Viridis', showscale=True, colorbar=dict(title="Poids"))
        ))
    else:
        # Comportement par défaut : traces par série
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

    # Mise à jour du layout et de la caméra
    layout_args = dict(
        scene=dict(
            xaxis_title='Date 📅',
            yaxis_title='Reps 🔄',
            zaxis_title='Poids (kg) 🏋️',
            xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
            yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
            zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        height=700,
        paper_bgcolor="rgba(0,0,0,0)", # Fond transparent pour s'intégrer au thème
        plot_bgcolor="rgba(0,0,0,0)"
    )

    # Appliquer la caméra si une vue spécifique est sélectionnée
    if view_options[selected_view]:
        layout_args['scene']['camera'] = view_options[selected_view]

    fig.update_layout(**layout_args)

    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Erreur de connexion : {e}")