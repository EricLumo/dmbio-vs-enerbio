import streamlit as st
import pandas as pd

# Seiten-Konfiguration
st.set_page_config(page_title="dmBio vs. enerBiO Preisvergleich", page_icon="🌱", layout="wide")

st.title("🌱 dmBio vs. enerBiO – Coupon-Preisvergleich")
st.markdown("Vergleiche Bio-Eigenmarken von **dm** und **Rossmann** inklusive aktueller App-Coupons und auf den Grundpreis normiert.")

# --- SEITENLEISTE: COUPON-EINSTELLUNGEN ---
st.sidebar.header("🎟️ Deine aktuellen Coupons")

dm_rabatt = st.sidebar.slider("dm Rabatt (%)", min_value=0, max_value=30, value=10, step=5)
st.sidebar.markdown("---")
rossmann_alles = st.sidebar.slider("Rossmann 'Auf alles' (%)", min_value=0, max_value=20, value=10, step=5)
rossmann_ernaehrung = st.sidebar.slider("Rossmann 'Ernährung' (%)", min_value=0, max_value=30, value=20, step=5)
rossmann_kombinierbar = st.sidebar.checkbox("Rossmann Coupons kombinierbar (10% + 20% = 28%)", value=True)

if rossmann_kombinierbar:
    rossmann_faktor = (1 - rossmann_alles / 100) * (1 - rossmann_ernaehrung / 100)
else:
    rossmann_faktor = 1 - max(rossmann_alles, rossmann_ernaehrung) / 100

dm_faktor = 1 - (dm_rabatt / 100)

st.sidebar.info(f"**Effektiver Rabatt:**\n- dm: **{dm_rabatt}%**\n- Rossmann: **{(1 - rossmann_faktor)*100:.1f}%**")

# --- DATEN AUS CSV LADEN ---
@st.cache_data(ttl=300)
def lade_daten():
    return pd.read_csv("produkte.csv", sep=";")

try:
    df = lade_daten()
except Exception as e:
    st.error(f"Fehler beim Laden der produktliste: {e}")
    st.stop()

# --- BERECHNUNGEN ---
def berechne_vergleich(row):
    dm_eff = row["dm_Preis"] * dm_faktor if pd.notnull(row["dm_Preis"]) else None
    ross_eff = row["ross_Preis"] * rossmann_faktor if pd.notnull(row["ross_Preis"]) else None
    
    dm_gp = (dm_eff / row["dm_Menge_g"] * 100) if dm_eff else None
    ross_gp = (ross_eff / row["ross_Menge_g"] * 100) if ross_eff else None
    
    if dm_gp and ross_gp:
        if dm_gp < ross_gp:
            diff = ((ross_gp - dm_gp) / ross_gp) * 100
            sieger = f"dm (-{diff:.0f}%)"
        elif ross_gp < dm_gp:
            diff = ((dm_gp - ross_gp) / dm_gp) * 100
            sieger = f"Rossmann (-{diff:.0f}%)"
        else:
            sieger = "Gleichstand"
    elif dm_gp:
        sieger = "Nur bei dm"
    elif ross_gp:
        sieger = "Nur bei Rossmann"
    else:
        sieger = "-"
        
    return pd.Series([dm_eff, ross_eff, dm_gp, ross_gp, sieger])

df[["dm (Rabatt)", "Rossmann (Rabatt)", "dm (pro 100g/ml)", "Rossmann (pro 100g/ml)", "Günstiger"]] = df.apply(berechne_vergleich, axis=1)

# --- FILTER & SUCHE ---
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    suche = st.text_input("🔍 Produkt suchen...", "")
with col2:
    kategorie = st.selectbox("Kategorie", ["Alle"] + sorted(list(df["Kategorie"].dropna().unique())))
with col3:
    nur_beide = st.checkbox("Nur bei beiden verfügbar", value=False)

if suche:
    df = df[df["Produkt"].str.contains(suche, case=False, na=False)]
if kategorie != "Alle":
    df = df[df["Kategorie"] == kategorie]
if nur_beide:
    df = df[df["dm_Preis"].notnull() & df["ross_Preis"].notnull()]

# --- ANZEIGE DER TABELLE ---
anzeige_df = df[[
    "Produkt", "Kategorie", 
    "dm_Preis", "dm (Rabatt)", "dm (pro 100g/ml)",
    "ross_Preis", "Rossmann (Rabatt)", "Rossmann (pro 100g/ml)",
    "Günstiger"
]].rename(columns={
    "dm_Preis": "dm Normal (€)",
    "ross_Preis": "Rossmann Normal (€)"
})

st.dataframe(
    anzeige_df.style.format({
        "dm Normal (€)": "{:.2f} €",
        "dm (Rabatt)": "{:.2f} €",
        "dm (pro 100g/ml)": "{:.2f} €",
        "Rossmann Normal (€)": "{:.2f} €",
        "Rossmann (Rabatt)": "{:.2f} €",
        "Rossmann (pro 100g/ml)": "{:.2f} €",
    }, na_rep="-"),
    use_container_width=True,
    hide_index=True
)

st.markdown("---")
st.markdown("💡 **Fehlt ein Produkt oder stimmt ein Preis nicht?** Du kannst die Produktliste direkt auf [GitHub bearbeiten](https://github.com/EricLumo/dmbio-vs-enerbio/blob/main/produkte.csv)!")
