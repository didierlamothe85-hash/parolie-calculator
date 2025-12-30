# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [3.9.3-PRO-UNLIMITED] - 2024-12-30

### 🚀 Ajouté
- **SESSIONS ILLIMITÉES** : Plus de limite à S10, sessions dynamiques à l'infini
- Extension automatique des listes `all_sessions` et `all_session_impacts`
- Gestion dynamique de la mémoire pour sessions illimitées

### 🐛 Corrigé
- **Fix popup mode 24N** : Le popup de fin de session s'affiche maintenant correctement quand l'objectif est atteint en mode 24N
- **Fix erreurs Tkinter** : Correction des erreurs `TclError` après fermeture de la fenêtre historique
- Gestion propre des événements mousewheel avec bind/unbind
- Protocol `WM_DELETE_WINDOW` implémenté correctement

### 🔧 Modifié
- Limite S10 supprimée : changé de `< 10` à `< 999` (puis logique illimitée)
- Version mise à jour : `3.9.3-PRO-UNLIMITED`

---

## [3.9.2-PRO-FINAL] - 2024-12-07

### ✨ Ajouté
- Bouton **S** (Stats) dans la fenêtre historique
- Affichage des moyennes temps et impact sur les en-têtes de jours
- Affichage de l'objectif (OBJ) en temps réel AVANT de cliquer sur GO

### 🔧 Modifié
- Taille de la corbeille réduite (12pt → 10pt)
- Hauteur fenêtre historique bloquée (= hauteur calculatrice complète)

### 🐛 Corrigé
- Fix "Oui" pour démarrer nouvelle session immédiatement après fin de session
- Bouton "Oui" lance maintenant `on_go()` correctement

---

## [3.9.1] - 2024-11-XX

### ✨ Ajouté
- Mode 24N (2 douzaines)
- Système de division des pertes par paliers (-2%, -4%, -6%...)
- Fenêtre historique interactive avec filtres
- Export des sessions

### 🔧 Modifié
- Interface utilisateur améliorée
- Gestion bankroll optimisée

---

## [3.9.0] - 2024-10-XX

### ✨ Ajouté
- Première version avec sessions S1-S10
- Mode 18N (simple chance)
- Calculatrice intégrée
- Statistiques de base
- Sauvegarde JSON

---

## [3.0.0] - 2024-XX-XX

### ✨ Ajouté
- Version initiale
- Calculs de base
- Interface Tkinter

---

## À venir (Roadmap)

### Version 4.0.0 (Planifiée)
- [ ] Multi-devises (EUR, USD, CAD, CHF)
- [ ] Graphiques de progression
- [ ] Export Excel/CSV
- [ ] Mode sombre/clair
- [ ] Backup automatique cloud
- [ ] Multi-langue (FR/EN)

### Version 3.9.4 (Prochaine)
- [ ] Optimisation performance avec 100+ sessions
- [ ] Raccourcis clavier personnalisables
- [ ] Templates de casinos
- [ ] Import/Export profils

---

**Légende** :
- 🚀 Ajouté : Nouvelles fonctionnalités
- 🔧 Modifié : Changements de fonctionnalités existantes
- 🐛 Corrigé : Corrections de bugs
- ⚠️ Déprécié : Fonctionnalités bientôt supprimées
- ❌ Supprimé : Fonctionnalités supprimées
- 🔒 Sécurité : Corrections de sécurité
