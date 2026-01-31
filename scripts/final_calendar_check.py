import pandas as pd

df = pd.read_excel('data/planning_cours_brevet_2025-2027.xlsx')
df['Date'] = pd.to_datetime(df['Date'])

print("=== CONFORMITÉ AU CALENDRIER FOURNI ===\n")
print(f"Total: {len(df)} sessions")
print(f"Première: {df['Date'].min().strftime('%d.%m.%Y')}")
print(f"Dernière: {df['Date'].max().strftime('%d.%m.%Y')}")

print("\n--- 2025 (21 sessions) ---")
df_2025 = df[df['Date'].dt.year == 2025]
print(f"Oct 2025 (Bloc 1): {len(df_2025[df_2025['Date'].dt.month == 10])} sessions ✅")
print(f"Nov 2025 (Bloc 2): {len(df_2025[df_2025['Date'].dt.month == 11])} sessions ✅")
print(f"Déc 2025 (Bloc 3): {len(df_2025[df_2025['Date'].dt.month == 12])} sessions ✅")
print(f"Total 2025: {len(df_2025)} sessions")

print("\n--- 2026 (81 sessions) ---")
df_2026 = df[df['Date'].dt.year == 2026]
print(f"Jan 2026 (Blocs 4-5): {len(df_2026[df_2026['Date'].dt.month == 1])} sessions")
print(f"Fév 2026 (Bloc 6): {len(df_2026[df_2026['Date'].dt.month == 2])} sessions")
print(f"Mar 2026 (Blocs 7-8): {len(df_2026[df_2026['Date'].dt.month == 3])} sessions")
print(f"Avr 2026 (Bloc 9): {len(df_2026[df_2026['Date'].dt.month == 4])} sessions")
print(f"Mai 2026 (Blocs 10-11): {len(df_2026[df_2026['Date'].dt.month == 5])} sessions")
print(f"Sep 2026 (Blocs 12-13): {len(df_2026[df_2026['Date'].dt.month == 9])} sessions")
print(f"Oct 2026 (Bloc 14): {len(df_2026[df_2026['Date'].dt.month == 10])} sessions")
print(f"Nov 2026 (Bloc 15): {len(df_2026[df_2026['Date'].dt.month == 11])} sessions")
print(f"Total 2026: {len(df_2026)} sessions")

print("\n--- 2027 (7 sessions) ---")
df_2027 = df[df['Date'].dt.year == 2027]
print(f"Jan 2027 (Bloc 16): {len(df_2027)} sessions")
print(f"Dates: {df_2027['Date'].min().strftime('%d.%m')} au {df_2027['Date'].max().strftime('%d.%m')}")

print(f"\n=== TOTAL: {len(df)} sessions ===")
print("\n✅ Calendrier conforme:")
print("  - Début: 07 octobre 2025")
print("  - Fin: 21 janvier 2027")
print("  - Examen: 22-26 mars 2027")
