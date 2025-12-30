# 🎰 Calculatrice Casino - Parolie Calculator

**Version 3.9.3-PRO-UNLIMITED** - Gestion professionnelle de sessions casino avec bankroll tracking

## 📋 Description

Application Python/Tkinter pour gérer des sessions de casino avec :
- Gestion de bankroll en temps réel
- Calcul automatique des objectifs (% configurable)
- Système de sessions illimitées (S1, S2, S3... S∞)
- Modes 18N (simple chance) et 24N (2 douzaines)
- Division automatique des pertes
- Statistiques détaillées par casino
- Historique complet avec filtres
- Export des données
- Simulateur 365 jours

## ✨ Nouveautés v3.9.3

- ✅ **SESSIONS ILLIMITÉES** - Plus de limite à S10
- ✅ **Fix popup mode 24N** - Affichage correct quand objectif atteint
- ✅ **Fix canvas Tkinter** - Correction erreurs après fermeture historique

## 🚀 Installation

### Prérequis
- Python 3.7 ou supérieur
- Tkinter (inclus avec Python sur Windows/Mac)

### Installation

```bash
# Cloner le repository
git clone https://github.com/didierlamothe85-hash/parolie-calculator.git
cd parolie-calculator

# Lancer l'application
python calculator.py
```

## 📖 Utilisation

### Démarrage rapide

1. **Sélectionner un casino** dans la liste déroulante
2. **Entrer votre bankroll** (ex: 100)
3. **Configurer l'objectif %** (ex: 2.0%)
4. **Cliquer sur GO** pour démarrer la session

### Raccourcis clavier

- `G` - Gain (coup gagné)
- `P` - Perte (coup perdu)
- `O` - GO (démarrer session)
- `R` - RESET
- `K` - Verrouiller/Déverrouiller clavier
- `Z` - UNDO (annuler dernière action)
- `S` - Statistiques
- `C` - Mode Compact

### Modes de jeu

**Mode 18N (Simple chance)** :
- Paiement 1:1
- Mise sur Rouge/Noir, Pair/Impair, etc.

**Mode 24N (2 Douzaines)** :
- 2 douzaines simultanées
- Mise affichée = mise PAR douzaine
- Mise réelle = 2× mise affichée

### Système de sessions

- **S1, S2, S3** : Sessions initiales (affichées par défaut)
- **S4-S∞** : Sessions supplémentaires créées automatiquement
- **Division des pertes** : À chaque palier (-2%, -4%, -6%...), les pertes sont divisées sur 4 sessions

## 📊 Fonctionnalités avancées

### Historique
- Filtre par casino
- Filtre par période (7/30/90 jours)
- Recherche textuelle
- Affichage par jour (repliable)
- Détail des impacts par session
- Suppression sélective

### Statistiques
- Temps moyen par session
- Impact moyen bankroll %
- Impact min/max
- Gain moyen à l'heure ($/H)

### Simulateur 365 jours
- Projection annuelle
- Calendrier visuel
- Calcul automatique des objectifs quotidiens
- Visualisation de la progression

## 🗂️ Structure des données

Les données sont sauvegardées dans `calc_stats_data.json` :

```json
{
  "casinos": [
    {
      "name": "Casino Example",
      "sessions": [
        {
          "start_ts": 1234567890,
          "end_ts": 1234567900,
          "duration": 600,
          "profit": 20.0,
          "impact_pct": -5.2,
          "impacts_detail": [-5.2, -3.1, 0.0],
          "num_mode": 18,
          "num_sessions": 3
        }
      ]
    }
  ],
  "obj_pct": 2.0
}
```

## 🐛 Bugs connus résolus

### v3.9.3
- ✅ Sessions bloquées à S10 (maintenant illimitées)
- ✅ Popup manquant en mode 24N
- ✅ Erreurs Tkinter canvas après fermeture historique

### v3.9.2
- ✅ Problème "Oui" nouvelle session
- ✅ Affichage OBJ avant GO

## 🔧 Développement

### Architecture

```
calculator.py           # Application principale
├── Calculator         # Classe principale
├── HistoryWindow      # Fenêtre historique
├── StatsWindow        # Fenêtre statistiques
├── CasinoListWindow   # Gestion casinos
└── SimulatorWindow    # Simulateur 365j
```

### Workflow Git

```bash
# Récupérer dernières modifications
git pull

# Après modifications
git add .
git commit -m "Description des changements"
git push
```

## 📝 Changelog

### v3.9.3-PRO-UNLIMITED (30/12/2024)
- SESSIONS ILLIMITÉES (plus de limite S10)
- Fix popup mode 24N quand objectif atteint
- Fix erreurs canvas après fermeture fenêtre
- Extension dynamique des listes de sessions

### v3.9.2-PRO-FINAL
- Bouton Stats dans historique
- Moyennes sur en-têtes de jours
- Fix hauteur fenêtre historique
- Affichage OBJ en temps réel

## 🤝 Contribution

Ce projet est privé. Pour contribuer :
1. Créer une issue pour discuter du changement
2. Fork le repository
3. Créer une branche (`git checkout -b feature/AmazingFeature`)
4. Commit (`git commit -m 'Add AmazingFeature'`)
5. Push (`git push origin feature/AmazingFeature`)
6. Ouvrir une Pull Request

## 📄 Licence

Tous droits réservés © 2024

## 👤 Auteur

**Didier Lamothe**
- GitHub: [@didierlamothe85-hash](https://github.com/didierlamothe85-hash)

## 🙏 Support

Pour toute question ou bug :
- Ouvrir une issue sur GitHub
- Consulter la documentation dans le code

---

**Bon jeu responsable ! 🎲**
