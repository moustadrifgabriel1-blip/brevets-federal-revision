import pandas as pd
from datetime import datetime

df = pd.read_excel('data/planning_cours_brevet_2025-2027.xlsx')
df['Date'] = pd.to_datetime(df['Date'])

# Calendrier attendu selon le document fourni
calendrier = {
    'B01': ('07.10.2025', '11.10.2025'),
    'B02': ('11.11.2025', '15.11.2025'),
    'B03': ('02.12.2025', '06.12.2025'),
    'B04': ('13.01.2026', '17.01.2026'),
    'B05': ('27.01.2026', '31.01.2026'),
    'B06': ('10.02.2026', '14.02.2026'),
    'B07': ('03.03.2026', '07.03.2026'),
    'B08': ('24.03.2026', '28.03.2026'),
    'B09': ('21.04.2026', '25.04.2026'),
    'B10': ('05.05.2026', '09.05.2026'),
    'B11': ('19.05.2026', '23.05.2026'),
    'B12': ('08.09.2026', '12.09.2026'),
    'B13': ('29.09.2026', '03.10.2026'),
    'B14': ('27.10.2026', '31.10.2026'),
    'B15': ('24.11.2026', '28.11.2026'),
    'B16': ('12.01.2027', '22.01.2027'),  # Attention: 10 jours!
}

print("=== VÉRIFICATION DÉTAILLÉE DES BLOCS ===\n")

for bloc, (debut_str, fin_str) in calendrier.items():
    debut = datetime.strptime(debut_str, '%d.%m.%Y')
    fin = datetime.strptime(fin_str, '%d.%m.%Y')
    
    sessions = df[(df['Date'] >= debut) & (df['Date'] <= fin)]
    nb_sessions = len(sessions)
    
    if nb_sessions > 0:
        date_min = sessions['Date'].min().strftime('%d.%m')
        date_max = sessions['Date'].max().strftime('%d.%m')
        print(f"{bloc}: {nb_sessions:2d} sessions | {date_min} au {date_max} ✅")
    else:
        print(f"{bloc}: {nb_sessions:2d} sessions | {debut_str} au {fin_str} ❌ VIDE!")

print(f"\n=== SESSIONS HORS BLOCS ===")
# Vérifier s'il y a des sessions en dehors des périodes de blocs
all_dates_in_blocs = []
for debut_str, fin_str in calendrier.values():
    debut = datetime.strptime(debut_str, '%d.%m.%Y')
    fin = datetime.strptime(fin_str, '%d.%m.%Y')
    all_dates_in_blocs.extend(pd.date_range(debut, fin))

hors_blocs = df[~df['Date'].isin(all_dates_in_blocs)]
if len(hors_blocs) > 0:
    print(f"⚠️ {len(hors_blocs)} sessions hors des périodes de blocs:")
    for idx, row in hors_blocs.iterrows():
        print(f"  {row['Date'].strftime('%d.%m.%Y')} - {row['Module']}")
else:
    print("✅ Toutes les sessions sont dans les périodes de blocs")
