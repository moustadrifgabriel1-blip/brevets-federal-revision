import pandas as pd

df = pd.read_excel('data/planning_cours_brevet_2025-2027.xlsx')
df['Date'] = pd.to_datetime(df['Date'])

print("=" * 60)
print("   PLANNING COURS BREVET FÉDÉRAL 2025-2027")
print("=" * 60)
print(f"\n✅ Extraction complète : {len(df)} sessions de cours")
print(f"📅 Période : {df['Date'].min().strftime('%d.%m.%Y')} → {df['Date'].max().strftime('%d.%m.%Y')}")
print(f"📝 Examen : 22-26 mars 2027")

print("\n" + "=" * 60)
print("   RÉPARTITION PAR ANNÉE")
print("=" * 60)
print(f"2025 : {len(df[df['Date'].dt.year == 2025]):2d} sessions (Blocs 1-3)")
print(f"2026 : {len(df[df['Date'].dt.year == 2026]):2d} sessions (Blocs 4-15)")
print(f"2027 : {len(df[df['Date'].dt.year == 2027]):2d} sessions (Bloc 16)")

print("\n" + "=" * 60)
print("   MODULES ENSEIGNÉS")
print("=" * 60)
modules = df['Module'].value_counts().sort_index()
print(f"Total : {len(modules)} modules différents")
for module, count in modules.items():
    print(f"  {module} : {count:2d} sessions")

print("\n" + "=" * 60)
print("   STATUT AU 31 JANVIER 2026")
print("=" * 60)
df_passed = df[df['Date'] <= pd.Timestamp('2026-01-31')]
print(f"✅ Sessions passées : {len(df_passed)}/{len(df)} ({len(df_passed)*100//len(df)}%)")
print(f"📚 Sessions à venir : {len(df) - len(df_passed)}")
print(f"📖 Blocs terminés : Blocs 1-5")
print(f"🎯 Prochain bloc : Bloc 6 (10-14 février 2026)")

print("\n" + "=" * 60)
print("   ✅ DONNÉES PRÊTES POUR STREAMLIT")
print("=" * 60)
print(f"📁 Fichier : data/planning_cours_brevet_2025-2027.xlsx")
print(f"💡 Action : Importer dans Streamlit → 📅 Planning Cours")
