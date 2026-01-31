import pandas as pd

df = pd.read_excel('data/planning_cours_brevet_2025-2027.xlsx')
df['Date'] = pd.to_datetime(df['Date'])

print("=== VÉRIFICATION DU CALENDRIER ===\n")
print(f"Première session extraite: {df['Date'].min().strftime('%d.%m.%Y')}")
print(f"Dernière session extraite: {df['Date'].max().strftime('%d.%m.%Y')}")

print("\n=== SESSIONS PAR MOIS 2025 ===")
df_2025 = df[df['Date'].dt.year == 2025]
for month in sorted(df_2025['Date'].dt.month.unique()):
    count = len(df_2025[df_2025['Date'].dt.month == month])
    month_name = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'][month-1]
    print(f"{month_name} 2025: {count} sessions")

print("\n=== COMPARAISON AVEC CALENDRIER FOURNI ===")
print("Attendu: Bloc 1 (07-11 oct), Bloc 2 (11-15 nov), Bloc 3 (02-06 déc)")
print(f"Extrait: {len(df_2025)} sessions en 2025")

df_oct = df_2025[df_2025['Date'].dt.month == 10]
df_nov = df_2025[df_2025['Date'].dt.month == 11]
df_dec = df_2025[df_2025['Date'].dt.month == 12]
df_jan = df_2025[df_2025['Date'].dt.month == 1]

print(f"\nOctobre 2025: {len(df_oct)} sessions {('✅' if len(df_oct) > 0 else '❌')}")
print(f"Novembre 2025: {len(df_nov)} sessions {('✅' if len(df_nov) > 0 else '❌')}")
print(f"Décembre 2025: {len(df_dec)} sessions {('✅' if len(df_dec) > 0 else '❌')}")
print(f"Janvier 2025: {len(df_jan)} sessions {('❌ NE DEVRAIT PAS EXISTER' if len(df_jan) > 0 else '✅')}")

if len(df_jan) > 0:
    print("\n⚠️ PROBLÈME: Sessions en janvier 2025 détectées:")
    print(df_jan[['Date', 'Periode', 'Module']].head(10).to_string(index=False))
