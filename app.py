import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import plotly.express as px
import requests
import json

# Remplacez cette URL par votre propre URL de Webhook Slack
slack_webhook_url = 'https://hooks.slack.com/services/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'

# CSS pour le style et les animations
st.markdown(
    """
    <style>
    h1 {
        color: #F63366;
        transition: all 0.3s ease;
    }
    h1:hover {
        color: #FF69B4;
    }
    .alert {
        background-color: #F9F9F9;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
        box-shadow: 0 1px 5px rgba(0,0,0,0.1);
    }
    .section-title {
        color: #F63366;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Titre de l'application
st.markdown("<h1>🔧 Analyse des Résultats de Maintenance</h1>", unsafe_allow_html=True)

# Choix de la langue
language = st.selectbox('Choisissez une langue', ['Français', 'English', 'Español'])

# Traductions
translations = {
    'Français': {
        "seuil": "Définissez un seuil pour le RUL",
        "urgence": "🚨 Urgence : {rul_superieur} moteurs ont un RUL supérieur au seuil.",
        "attention": "⚠️ Attention : {rul_approche} moteurs approchent du seuil.",
        "info": "ℹ️ Info : {rul_inferieur} moteurs ont un RUL inférieur au seuil - 10.",
        "success": "Rapport exporté avec succès.",
        "slack_sent": "Notification envoyée à Slack."
    },
    'English': {
        "seuil": "Set a threshold for RUL",
        "urgence": "🚨 Emergency: {rul_superieur} engines have a RUL higher than the threshold.",
        "attention": "⚠️ Warning: {rul_approche} engines are approaching the threshold.",
        "info": "ℹ️ Info: {rul_inferieur} engines have a RUL lower than threshold - 10.",
        "success": "Report successfully exported.",
        "slack_sent": "Notification sent to Slack."
    },
    'Español': {
        "seuil": "Defina un umbral para el RUL",
        "urgence": "🚨 Urgencia: {rul_superieur} motores tienen un RUL superior al umbral.",
        "attention": "⚠️ Advertencia: {rul_approche} motores se acercan al umbral.",
        "info": "ℹ️ Info: {rul_inferieur} motores tienen un RUL inferior al umbral - 10.",
        "success": "Informe exportado con éxito.",
        "slack_sent": "Notificación enviada a Slack."
    }
}

# Ajout d'un espacement
st.markdown("<br>", unsafe_allow_html=True)

# Téléchargement du fichier RUL prédit
st.header("📥 Téléchargez vos données")
uploaded_file = st.file_uploader("Choisissez un fichier CSV pour les valeurs RUL prédites et réelles", type="csv")

def send_slack_message(message):
    payload = {
        "text": message
    }
    response = requests.post(slack_webhook_url, data=json.dumps(payload), headers={'Content-Type': 'application/json'})
    if response.status_code != 200:
        raise ValueError(f'Erreur {response.status_code}: {response.text}')

if uploaded_file is not None:
    df_rul = pd.read_csv(uploaded_file)

    if 'RUL_Prédit' in df_rul.columns and 'RUL_Réel' in df_rul.columns:
        seuil = st.slider(translations[language]["seuil"], 0, 300, value=50)
        total_moteurs = df_rul.shape[0]

        # Calcul des moteurs en fonction du seuil
        rul_superieur = df_rul[df_rul['RUL_Prédit'] > seuil].shape[0]
        rul_inferieur = df_rul[df_rul['RUL_Prédit'] < seuil - 10].shape[0]
        rul_approche = df_rul[(df_rul['RUL_Prédit'] >= seuil - 10) & (df_rul['RUL_Prédit'] <= seuil)].shape[0]

        st.markdown("<h3 class='section-title'>Alertes de Maintenance</h3>", unsafe_allow_html=True)
        
        # Affichage des alertes avec barres de progression dans un encadré
        st.markdown("<div class='alert'>", unsafe_allow_html=True)
        st.markdown(translations[language]["urgence"].format(rul_superieur=rul_superieur))
        st.progress(rul_superieur / total_moteurs)
        
        st.markdown(translations[language]["attention"].format(rul_approche=rul_approche))
        st.progress(rul_approche / total_moteurs)
        
        st.markdown(translations[language]["info"].format(rul_inferieur=rul_inferieur))
        st.progress(rul_inferieur / total_moteurs)
        st.markdown("</div>", unsafe_allow_html=True)

        # Créer le dataframe df_alertes
        df_alertes = pd.DataFrame({
            'Moteur': df_rul.index,  
            'RUL Prédit': df_rul['RUL_Prédit'],
            'RUL Réel': df_rul['RUL_Réel'],
            'Statut': ['Urgence' if x > seuil else 'Approche' if seuil-10 <= x <= seuil else 'OK' for x in df_rul['RUL_Prédit']]
        })

        # Graphique de répartition des alertes
        fig = px.pie(df_alertes, names='Statut', title='Répartition des alertes RUL',
                     color_discrete_sequence=["#636EFA", "#EF553B", "#00CC96"])  # Personnalisez les couleurs ici
        st.plotly_chart(fig)

        # Envoyer une notification Slack
        if st.button("Envoyer une notification Slack"):
            message = f"Alertes de maintenance : Urgence : {rul_superieur}, Attention : {rul_approche}, Info : {rul_inferieur}"
            try:
                send_slack_message(message)
                st.success(translations[language]["slack_sent"])
            except Exception as e:
                st.error(f"Erreur lors de l'envoi de la notification Slack : {e}")

        # Ajout d'un espacement
        st.markdown("<br>", unsafe_allow_html=True)

        # Planification de maintenance
        if 'RUL_Prédit' in df_rul.columns:
            df_rul['Moteur_ID'] = df_rul.index  
            df_rul['Date de maintenance'] = pd.to_datetime('today') + pd.to_timedelta(df_rul['RUL_Prédit'], unit='D')

            df_maintenance_plan = df_rul[['Moteur_ID', 'Date de maintenance']]
            st.markdown("<h3 class='section-title'>Plan de Maintenance</h3>", unsafe_allow_html=True)
            st.dataframe(df_maintenance_plan)

            csv = df_maintenance_plan.to_csv(index=False).encode('utf-8')
            st.download_button(label="Télécharger le plan de maintenance",
                               data=csv,
                               file_name='plan_maintenance.csv',
                               mime='text/csv')

# Ajout d'un espacement
st.markdown("<br>", unsafe_allow_html=True)
