import plotly.graph_objects as go
import plotly.express as px
from .utils import adjust_lightness

# --- Camera Views Configuration ---
CAMERA_VIEWS = {
    "Défaut 🔄": None,
    "Poids / Reps (Profil) 🏋️": dict(eye=dict(x=2.5, y=0, z=0), up=dict(x=0, y=1, z=0)),
    "Poids / Date (Face) 📅": dict(eye=dict(x=0, y=-2.5, z=0), up=dict(x=0, y=0, z=1)),
    "Reps / Date (Dessus) 🔁": dict(eye=dict(x=0, y=0, z=2.5), up=dict(x=0, y=1, z=0))
}

def create_3d_plot_unique(df_plot, exercice, connect_all=False, selected_view="Défaut 🔄"):
    """
    Creates the 3D plot for Single Analysis mode.
    """
    fig = go.Figure()
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

    update_layout_common(fig, selected_view)
    return fig

def create_3d_plot_global(df_glob, exercices_sel):
    """
    Creates the 3D plot for Global Comparison mode.
    """
    fig = go.Figure()
    palette = px.colors.qualitative.Bold
    
    for idx_exo, exo in enumerate(exercices_sel):
        subset_exo = df_glob[df_glob['Exercice'] == exo]
        base_color = palette[idx_exo % len(palette)]
        
        series = sorted(subset_exo['Série'].unique())
        for idx_ser, ser in enumerate(series):
            subset_serie = subset_exo[subset_exo['Série'] == ser]
            
            # Use utility for lightness
            # Start very bright (1.6) and darken significantly (+0.4) per series
            lightness_factor = 1.6 - (idx_ser * 0.4) 
            final_color = adjust_lightness(base_color, lightness_factor)
            
            fig.add_trace(go.Scatter3d(
                x=subset_serie['Date'],
                y=subset_serie['Reps'],
                z=subset_serie['Poids'],
                mode='lines+markers', 
                name=f"{exo} - S{ser}",
                line=dict(color=final_color, width=4),
                marker=dict(size=4, color=final_color),
                legendgroup=exo,
                legendgrouptitle_text=exo,
                hovertemplate=f"<b>{exo} S{ser}</b><br>Date: %{{x|%d/%m/%Y}}<br>Reps: %{{y}}<br>Poids: %{{z}} kg<extra></extra>"
            ))
            
    update_layout_common(fig, "Défaut 🔄") # Global view uses default camera usually
    return fig

def create_2d_panels(df_plot):
    """
    Creates the three 2D figures (Date/Poids, Date/Reps, Poids/Reps).
    Returns a tuple of 3 figures.
    """
    # 1. Date vs Poids
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['Poids'], mode='markers', marker=dict(color='#ff7f0e', size=8)))
    fig1.update_layout(title="Poids vs Date", xaxis_title="Date", yaxis_title="Poids (kg)", height=300, margin=dict(l=20, r=20, t=40, b=20))
    
    # 2. Date vs Reps
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_plot['Date'], y=df_plot['Reps'], mode='markers', marker=dict(color='#1f77b4', size=8)))
    fig2.update_layout(title="Reps vs Date", xaxis_title="Date", yaxis_title="Reps", height=300, margin=dict(l=20, r=20, t=40, b=20))
    
    # 3. Poids vs Reps
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=df_plot['Poids'], y=df_plot['Reps'], mode='markers', marker=dict(color='#2ca02c', size=8)))
    fig3.update_layout(title="Reps vs Poids", xaxis_title="Poids (kg)", yaxis_title="Reps", height=300, margin=dict(l=20, r=20, t=40, b=20))
    
    return fig1, fig2, fig3

def update_layout_common(fig, selected_view):
    """
    Applies common layout settings and camera view.
    """
    layout_args = dict(
        scene=dict(
            xaxis_title='Date 📅', yaxis_title='Reps 🔄', zaxis_title='Poids (kg) 🏋️',
            xaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True, tickformat='%d/%m\n%y', nticks=6),
            yaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
            zaxis=dict(backgroundcolor="rgba(0,0,0,0)", gridcolor="gray", showbackground=True),
        ),
        margin=dict(l=0, r=0, b=0, t=0), height=700,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        legend=dict(
            yanchor="top", y=0.99, xanchor="left", x=0.01, 
            bgcolor="rgba(0,0,0,0)", font=dict(color="white"),
            groupclick="toggleitem"
        )
    )
    
    if selected_view and CAMERA_VIEWS.get(selected_view):
        layout_args['scene']['camera'] = CAMERA_VIEWS[selected_view]
        
    fig.update_layout(**layout_args)
