import streamlit as st
try:
    from src.data import get_data
    from src.plots import create_3d_plot_unique, create_3d_plot_global, create_2d_panels, CAMERA_VIEWS
except ImportError:
    # Fallback to local import if run from root without module structure yet (debugging)
    pass

# --- Configuration ---
# Force reload
st.set_page_config(page_title="Sport Analytics 3D", layout="wide")

try:
    # 1. Load Data
    df = get_data()

    # --- Sidebar Configuration ---
    st.sidebar.header("⚙️ Configuration")
    
    # Mode d'analyse
    mode_analyse = st.sidebar.radio(
        "Mode d'analyse", 
        ["Analyse Unique 🔍", "Comparaison Globale 🌍"], 
        index=0
    )
    
    # --- LOGIC: SINGLE ANALYSIS ---
    if mode_analyse == "Analyse Unique 🔍":
        st.sidebar.header("🎯 Filtres")
        if not df.empty:
            muscle = st.sidebar.selectbox("Groupe Musculaire", sorted(df['Muscle'].unique()))
            exercices_dispo = sorted(df[df['Muscle'] == muscle]['Exercice'].unique())
            exercice = st.sidebar.selectbox("Exercice", exercices_dispo)

            # Filter and sort
            df_plot = df[df['Exercice'] == exercice].sort_values('Date')
            
            # Visualization Options
            st.sidebar.markdown("---")
            st.sidebar.header("👁️ Visualisation")
            connect_all = st.sidebar.checkbox("Relier les séances", value=False, help="Ligne continue chronologique")
            
            selected_view = st.sidebar.radio("Angle de vue", list(CAMERA_VIEWS.keys()))

            # Title & Metrics
            st.title(f"🚀 Progression : {exercice}")
            if not df_plot.empty:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Max Poids", f"{df_plot['Poids'].max()} kg", f"{df_plot['Poids'].iloc[-1] - df_plot['Poids'].iloc[0]:.1f} kg")
                with col2:
                    st.metric("Max Reps", f"{df_plot['Reps'].max()}", f"{int(df_plot['Reps'].iloc[-1] - df_plot['Reps'].iloc[0])}")
                with col3:
                    st.metric("Volume Total", f"{(df_plot['Poids'] * df_plot['Reps']).sum() / 1000:.1f} T")

                # Main 3D Plot
                fig = create_3d_plot_unique(df_plot, exercice, connect_all, selected_view)
                st.plotly_chart(fig, use_container_width=True)
                
                # 2D Panels
                st.markdown("### 📊 Analyse Détaillée (Projections 2D)")
                fig1, fig2, fig3 = create_2d_panels(df_plot)
                c1, c2, c3 = st.columns(3)
                with c1: st.plotly_chart(fig1, use_container_width=True)
                with c2: st.plotly_chart(fig2, use_container_width=True)
                with c3: st.plotly_chart(fig3, use_container_width=True)
            else:
                st.warning("Aucune donnée trouvée pour cet exercice.")
    
    # --- LOGIC: GLOBAL COMPARISON ---
    else:
        st.sidebar.header("🎯 Filtres Globaux")
        if not df.empty:
            muscles_sel = st.sidebar.multiselect("Groupes Musculaires", sorted(df['Muscle'].unique()), default=sorted(df['Muscle'].unique()))
            
            exos_filtered = sorted(df[df['Muscle'].isin(muscles_sel)]['Exercice'].unique())
            exercices_sel = st.sidebar.multiselect("Exercices", exos_filtered, default=exos_filtered[:3] if len(exos_filtered)>3 else exos_filtered)
            
            df_glob = df[df['Exercice'].isin(exercices_sel)].sort_values(['Date', 'Série'])
            
            st.title("🌍 Comparaison Multi-Exercices")
            
            if not df_glob.empty:
                fig = create_3d_plot_global(df_glob, exercices_sel)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Sélectionnez des exercices pour voir la comparaison.")

except Exception as e:
    st.error(f"Une erreur est survenue : {e}")
    # Optional: Print traceback to console for debugging
    import traceback
    traceback.print_exc()