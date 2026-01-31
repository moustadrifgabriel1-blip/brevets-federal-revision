# 📝 Formules Essentielles - Brevet Fédéral Réseaux Énergétiques

## ⚡ Électrotechnique Fondamentale

### Loi d'Ohm
```
U = R × I

U = Tension (Volts)
R = Résistance (Ohms)
I = Courant (Ampères)
```

### Puissance électrique

**Courant continu (DC) :**
```
P = U × I
P = R × I²
P = U² / R
```

**Courant alternatif monophasé (AC) :**
```
P (active) = U × I × cos(φ)           [W]
Q (réactive) = U × I × sin(φ)         [VAr]
S (apparente) = U × I                  [VA]
S = √(P² + Q²)
```

**Courant alternatif triphasé :**
```
P = √3 × U × I × cos(φ)
Q = √3 × U × I × sin(φ)
S = √3 × U × I
```

### Facteur de puissance
```
cos(φ) = P / S

φ = angle de déphasage entre tension et courant
```

### Énergie électrique
```
W = P × t

W = Énergie (Wh ou kWh)
P = Puissance (W ou kW)
t = Temps (h)
```

---

## 🔌 Résistances et Impédances

### Résistance d'un conducteur
```
R = ρ × L / A

ρ = Résistivité (Ω·mm²/m)
L = Longueur (m)
A = Section (mm²)
```

**Résistivité des métaux (à 20°C) :**
| Matériau | ρ (Ω·mm²/m) |
|----------|-------------|
| Cuivre   | 0.0175      |
| Aluminium| 0.028       |

### Résistances en série
```
R_total = R1 + R2 + R3 + ...
```

### Résistances en parallèle
```
1/R_total = 1/R1 + 1/R2 + 1/R3 + ...

Pour 2 résistances :
R_total = (R1 × R2) / (R1 + R2)
```

### Impédance (AC)
```
Z = √(R² + X²)

X = Réactance (XL - XC)
XL = 2πfL (inductive)
XC = 1/(2πfC) (capacitive)
```

---

## 📉 Chute de tension

### Monophasé
```
ΔU = 2 × I × L × (R × cos(φ) + X × sin(φ))

Simplifié (cosφ ≈ 1) :
ΔU = 2 × ρ × L × I / A
```

### Triphasé
```
ΔU = √3 × I × L × (R × cos(φ) + X × sin(φ))

Simplifié :
ΔU = √3 × ρ × L × I / A
```

### Chute de tension en pourcentage
```
ΔU% = (ΔU / Un) × 100

Limites NIBT :
- Éclairage : 3% max
- Autres usages : 5% max
```

---

## ⚡ Courant de court-circuit

### Courant de court-circuit triphasé
```
Icc3 = Un / (√3 × Zcc)

Un = Tension nominale
Zcc = Impédance de court-circuit
```

### Courant de court-circuit monophasé
```
Icc1 = U0 / Zs

U0 = Tension phase-neutre
Zs = Impédance de boucle de défaut
```

### Pouvoir de coupure
```
Le disjoncteur doit avoir :
Icu ≥ Icc présumé au point d'installation
```

---

## 🔒 Protection des personnes

### Condition de protection (schéma TN)
```
Ia × Zs ≤ U0

Ia = Courant de déclenchement du dispositif
Zs = Impédance de boucle de défaut
U0 = Tension phase-neutre (230V)
```

### Temps de coupure maximum
| Tension (V) | Temps max (s) |
|-------------|---------------|
| 120V        | 0.8s          |
| 230V        | 0.4s          |
| 400V        | 0.2s          |
| > 400V      | 0.1s          |

### Résistance de terre (schéma TT)
```
RA × IΔn ≤ UL

RA = Résistance de la prise de terre
IΔn = Courant différentiel nominal
UL = Tension limite (50V ou 25V)
```

---

## 🔧 Dimensionnement des câbles

### Courant admissible (Iz)
```
Iz ≥ IB

IB = Courant d'emploi
Iz = Courant admissible du câble

Avec facteurs de correction :
I'z = Iz × k1 × k2 × k3

k1 = facteur de température
k2 = facteur de groupement
k3 = facteur de mode de pose
```

### Protection par disjoncteur
```
IB ≤ In ≤ Iz
I2 ≤ 1.45 × Iz

IB = Courant d'emploi
In = Courant nominal du disjoncteur
Iz = Courant admissible du câble
I2 = Courant de déclenchement thermique
```

### Section minimale
```
A ≥ (2 × ρ × L × I) / ΔU_max

A = Section (mm²)
L = Longueur (m)
I = Courant (A)
ΔU_max = Chute de tension maximale (V)
```

---

## ☀️ Installations Photovoltaïques

### Puissance crête
```
Pc = E × A × η

Pc = Puissance crête (Wc)
E = Ensoleillement (1000 W/m² conditions STC)
A = Surface des panneaux (m²)
η = Rendement des panneaux (%)
```

### Production annuelle estimée
```
E_an = Pc × HSP × PR

E_an = Énergie annuelle (kWh)
Pc = Puissance crête installée (kWc)
HSP = Heures solaires de pointe par an (≈1000h en Suisse)
PR = Performance Ratio (0.75-0.85)
```

### Dimensionnement onduleur
```
Ratio DC/AC recommandé : 1.0 à 1.2

P_onduleur = P_crête / 1.1 (typique)
```

### Tension chaîne (string)
```
U_string = n × Umpp

n = nombre de panneaux en série
Umpp = tension au point de puissance max
```

---

## 🔋 Stockage d'énergie

### Capacité batterie
```
C = E / U

C = Capacité (Ah)
E = Énergie (Wh)
U = Tension (V)
```

### Autonomie
```
t = C × U × DoD / P

t = Temps d'autonomie (h)
C = Capacité (Ah)
U = Tension (V)
DoD = Profondeur de décharge (%)
P = Puissance consommée (W)
```

---

## 🔌 Bornes de recharge VE

### Puissance de charge
```
AC monophasé : P = U × I (max 7.4 kW à 32A)
AC triphasé : P = √3 × U × I (max 22 kW à 32A)
DC : P = U × I (jusqu'à 350 kW)
```

### Temps de charge
```
t = E_batterie / P_charge

t = Temps (h)
E_batterie = Capacité de la batterie (kWh)
P_charge = Puissance de charge (kW)
```

---

## 🌡️ Transformateurs

### Rapport de transformation
```
m = N1/N2 = U1/U2 = I2/I1

N = nombre de spires
U = tension
I = courant
```

### Puissance apparente
```
S = √3 × Un × In

S = Puissance apparente (VA)
Un = Tension nominale
In = Courant nominal
```

### Pertes fer (à vide)
```
Approximation : 0.2-0.5% de Sn
```

### Pertes cuivre (en charge)
```
Pcu = R × I²
Approximation : 1-2% de Sn à pleine charge
```

---

## 📊 Tableaux de référence

### Sections normalisées (mm²)
```
1.5 - 2.5 - 4 - 6 - 10 - 16 - 25 - 35 - 50 - 70 - 95 - 120 - 150 - 185 - 240 - 300
```

### Calibres disjoncteurs (A)
```
6 - 10 - 16 - 20 - 25 - 32 - 40 - 50 - 63 - 80 - 100 - 125
```

### Sensibilités différentiels (mA)
```
10 - 30 (protection des personnes)
100 - 300 (protection incendie)
500 - 1000 (protection des installations)
```

---

## 💡 Mnémotechniques

### Pour retenir les formules de puissance :
```
"PUI" comme "oui" mais en électricien !
P = U × I
```

### Triangle de puissance :
```
        S (VA)
       /|
      / |
     /  | Q (VAr)
    /   |
   /φ   |
  /_____|
    P (W)

cos(φ) = P/S (adjacent/hypoténuse)
sin(φ) = Q/S (opposé/hypoténuse)
```

### Couleurs des fils (Suisse) :
```
L1 = Brun
L2 = Noir  
L3 = Gris
N = Bleu
PE = Vert-Jaune
```

---

*Ces formules sont essentielles pour votre examen. Révisez-les régulièrement avec la répétition espacée !*
