#!/bin/bash
# Script d'initialisation du repository GitHub
# À exécuter APRÈS avoir téléchargé tous les fichiers

echo "🚀 Initialisation du repository Parolie Calculator"
echo ""

# Vérifier qu'on est dans le bon dossier
if [ ! -f "calculator.py" ]; then
    echo "❌ ERREUR: calculator.py introuvable"
    echo "Assurez-vous d'être dans le dossier parolie-calculator"
    exit 1
fi

echo "✅ Fichiers trouvés"
echo ""

# Initialiser Git si pas déjà fait
if [ ! -d ".git" ]; then
    echo "📦 Initialisation Git..."
    git init
    git branch -M main
fi

# Ajouter remote si pas déjà fait
if ! git remote | grep -q "origin"; then
    echo "🔗 Ajout du remote GitHub..."
    git remote add origin https://github.com/didierlamothe85-hash/parolie-calculator.git
fi

# Ajouter tous les fichiers
echo "➕ Ajout des fichiers..."
git add .

# Commit initial
echo "💾 Création du commit initial..."
git commit -m "Initial commit - v3.9.3-PRO-UNLIMITED

✨ Features:
- Sessions illimitées (plus de limite S10)
- Mode 18N et 24N
- Gestion bankroll complète
- Statistiques détaillées
- Historique avec filtres
- Simulateur 365 jours

🐛 Fixes:
- Popup mode 24N
- Erreurs canvas Tkinter
- Extension dynamique sessions

📝 Documentation:
- README complet
- CHANGELOG détaillé
- .gitignore Python
- requirements.txt"

# Push vers GitHub
echo "🚀 Push vers GitHub..."
echo ""
echo "⚠️  Vous allez être invité à vous connecter à GitHub"
echo ""

git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS! Le code est maintenant sur GitHub!"
    echo ""
    echo "🌐 Repository: https://github.com/didierlamothe85-hash/parolie-calculator"
    echo ""
    echo "📝 Prochaines étapes:"
    echo "  1. Visitez le repo sur GitHub"
    echo "  2. Vérifiez que tout est là"
    echo "  3. Pour les prochaines modifications:"
    echo "     git pull           # Récupérer les changements"
    echo "     git add .          # Ajouter vos modifications"
    echo "     git commit -m '...' # Décrire les changements"
    echo "     git push           # Envoyer sur GitHub"
else
    echo ""
    echo "❌ ERREUR lors du push"
    echo ""
    echo "Solutions possibles:"
    echo "  1. Vérifiez votre connexion internet"
    echo "  2. Vérifiez vos identifiants GitHub"
    echo "  3. Si le repo existe déjà avec du contenu:"
    echo "     git pull origin main --rebase"
    echo "     git push -u origin main"
fi
