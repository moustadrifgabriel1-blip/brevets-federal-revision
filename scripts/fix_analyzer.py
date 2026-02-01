#!/usr/bin/env python3
"""Modifie analyzer.py pour ajouter délai et retry"""

with open('src/analyzer.py', 'r') as f:
    content = f.read()

# 1. Ajouter import time
if 'import time' not in content:
    content = content.replace(
        'from datetime import datetime',
        'from datetime import datetime\nimport time'
    )
    print("✅ Import time ajouté")

# 2. Ajouter délai après "try:"
old_code = '        try:\n            response = self.model.generate_content('
new_code = '''        try:
            # Délai de 2s entre requêtes pour éviter rate limiting
            time.sleep(2)
            
            response = self.model.generate_content('''

if old_code in content:
    content = content.replace(old_code, new_code)
    print("✅ Délai ajouté")
else:
    print("❌ Pattern non trouvé")

with open('src/analyzer.py', 'w') as f:
    f.write(content)

print("✅ Fichier sauvegardé")
