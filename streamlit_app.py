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

    # Sidebar de Configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Mode d'analyse
    mode_analyse = st.sidebar.radio(
        "Mode d'analyse", 
        ["Analyse Unique 🔍", "Comparaison Globale 🌍"], 
        index=0
    )
    
    # --- LOGIQUE : ANALYSE UNIQUE ---
    if mode_analyse == "Analyse Unique 🔍":
        st.sidebar.header("🎯 Filtres")
        muscle = st.sidebar.selectbox("Groupe Musculaire", sorted(df['Muscle'].unique()))
        exercices_dispo = sorted(df[df['Muscle'] == muscle]['Exercice'].unique())
        exercice = st.sidebar.selectbox("Exercice", exercices_dispo)

        # Filtre et tri
        df_plot = df[df['Exercice'] == exercice].sort_values('Date')
        
        # Options Visualisation (Unique)
        st.sidebar.markdown("---")
        st.sidebar.header("👁️ Visualisation")
        connect_all = st.sidebar.checkbox("Relier les séances", value=False, help="Ligne continue chronologique")
        
        # Dictionnaire des Vues (Corrigé pour logique GAUCHE->DROITE / BAS->HAUT)
        # Poids vs Reps : Poids (X visu) / Reps (Y visu). Dans le plot 3D: X=Date, Y=Reps, Z=Poids.
        # On veut Z horizontal et Y vertical.
        # Vue de Coté (Side): Eye sur l'axe X. Up = Y pour avoir Y vertical.
        view_options = {
            "Défaut 🔄": None,
            "Poids / Reps (Profil) 🏋️": dict(eye=dict(x=2.5, y=0, z=0), up=dict(x=0, y=1, z=0)), # Regarde le plan Y-Z. Up=Y (Reps vert), donc Z (Poids) horizontal.
            "Poids / Date (Face) 📅": dict(eye=dict(x=0, y=-2.5, z=0), up=dict(x=0, y=0, z=1)), # Regarde le plan X-Z. Up=Z (Poids vert), donc X (Date) horizontal.
            "Reps / Date (Dessus) 🔁": dict(eye=dict(x=0, y=0, z=2.5), up=dict(x=0, y=1, z=0))  # Regarde le plan X-Y. Up=Y (Reps vert), donc X (Date) horizontal.
        }
        selected_view = st.sidebar.radio("Angle de vue", list(view_options.keys()))

        # Titre et Métriques
        st.title(f"🚀 Progression : {exercice}")
        if not df_plot.empty:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Max Poids", f"{df_plot['Poids'].max()} kg", f"{df_plot['Poids'].iloc[-1] - df_plot['Poids'].iloc[0]:.1f} kg")
            with col2:
                st.metric("Max Reps", f"{df_plot['Reps'].max()}", f"{int(df_plot['Reps'].iloc[-1] - df_plot['Reps'].iloc[0])}")
            with col3:
                st.metric("Volume Total", f"{(df_plot['Poids'] * df_plot['Reps']).sum() / 1000:.1f} T")

        # Plot 3D Principal
        fig = go.Figure()
        # Scale de couleurs pour différencier les séries si non reliées
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']

        if connect_all:
            fig.add_trace(go.Scatter3d(
                x=df_plot['Date'],
                y=df_plot['Reps'],
                z=df_plot['Poids'],
                mode='lines+markers',
                name='Progression',
                line=dict(color='#ff7f0e', width=6),
                marker=dict(size=5, color=df_plot['Poids'], colorscale='Viridis', showscale=True),
                hovertemplate="<b>Date</b>: %{x|%d/%m/%Y}<br><b>Reps</b>: %{y}<br><b>Poids</b>: %{z} kg<extra></extra>"
            ))
        else:
            for i, s in enumerate(sorted(df_plot['Série'].unique())):
                subset = df_plot[df_plot['Série'] == s]
                fig.add_trace(go.Scatter3d(
                    x=subset['Date'],
                    y=subset['Reps'],
                    z=subset['Poids'],
                    mode='lines+markers',
                    name=f'Série {s}',
                    line=dict(color=colors[i % len(colors)], width=4),
                    marker=dict(size=4),
                    hovertemplate="<b>Date</b>: %{x|%d/%m/%Y}<br><b>Reps</b>: %{y}<br><b>Poids</b>: %{z} kg<extra></extra>"
                ))

        # Layout Update
        layout_args = dict(
            scene=dict(
                xaxis_title='Date 📅', yaxis_title='Reps 🔄', zaxis_title='Poids (kg) 🏋️',
                xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True, tickformat='%d/%m\n%y', nticks=6),
                yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
                zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
            ),
            margin=dict(l=0, r=0, b=0, t=0), height=700,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
        )
        if view_options[selected_view]:
            layout_args['scene']['camera'] = view_options[selected_view]
            
        fig.update_layout(**layout_args)
        st.plotly_chart(fig, use_container_width=True)
        
        # --- PANNEAU DE PROJECTION 2D (Tableau Plat) ---
        st.markdown("### 📊 Analyse Détaillée (Projections 2D)")
        c1, c2, c3 = st.columns(3)
        
        # 1. Date vs Poids
        with c1:
            fig2d_1 = go.Figure()
            fig2d_1.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['Poids'], mode='markers', marker=dict(color='#ff7f0e', size=8)))
            fig2d_1.update_layout(title="Poids vs Date", xaxis_title="Date", yaxis_title="Poids (kg)", height=300, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig2d_1, use_container_width=True)
            
        # 2. Date vs Reps  
        with c2:
            fig2d_2 = go.Figure()
            fig2d_2.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['Reps'], mode='markers', marker=dict(color='#1f77b4', size=8)))
            fig2d_2.update_layout(title="Reps vs Date", xaxis_title="Date", yaxis_title="Reps", height=300, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig2d_2, use_container_width=True)

        # 3. Poids vs Reps
        with c3:
            fig2d_3 = go.Figure()
            fig2d_3.add_trace(go.Scatter(x=df_plot['Poids'], y=df_plot['Reps'], mode='markers', marker=dict(color='#2ca02c', size=8)))
            fig2d_3.update_layout(title="Reps vs Poids", xaxis_title="Poids (kg)", yaxis_title="Reps", height=300, margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig2d_3, use_container_width=True)

    # --- LOGIQUE : COMPARAISON GLOBALE ---
    else:
        st.sidebar.header("🎯 Filtres Globaux")
        muscles_sel = st.sidebar.multiselect("Groupes Musculaires", sorted(df['Muscle'].unique()), default=sorted(df['Muscle'].unique()))
        
        # Filtrer exercices par muscles sélectionnés
        exos_filtered = sorted(df[df['Muscle'].isin(muscles_sel)]['Exercice'].unique())
        exercices_sel = st.sidebar.multiselect("Exercices", exos_filtered, default=exos_filtered[:3] if len(exos_filtered)>3 else exos_filtered)
        
        df_glob = df[df['Exercice'].isin(exercices_sel)].sort_values('Date')
        
        st.title("🌍 Comparaison Multi-Exercices")
        
        fig = go.Figure()
        
        # Palette de couleurs discrète pour distinguir les exercices
        import plotly.express as px
        palette = px.colors.qualitative.Bold
        
        for idx, exo in enumerate(exercices_sel):
            subset = df_glob[df_glob['Exercice'] == exo]
            color = palette[idx % len(palette)]
            
            fig.add_trace(go.Scatter3d(
                x=subset['Date'],
                y=subset['Reps'],
                z=subset['Poids'],
                mode='markers', # Juste markers pour éviter le chaos des lignes
                name=exo,
                marker=dict(size=5, color=color),
                hovertemplate=f"<b>{exo}</b><br>Date: %{{x|%d/%m/%Y}}<br>Reps: %{{y}}<br>Poids: %{{z}} kg<extra></extra>"
            ))
            
        fig.update_layout(
            scene=dict(
                xaxis_title='Date 📅', yaxis_title='Reps 🔄', zaxis_title='Poids (kg) 🏋️',
                xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True, tickformat='%d/%m\n%y'),
                yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
                zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
            ),
            margin=dict(l=0, r=0, b=0, t=0), height=800,
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01, bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
        )
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Erreur de connexion : {e}")