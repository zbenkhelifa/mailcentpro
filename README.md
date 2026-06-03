# MailCent Pro

Application bureau Python/PySide6 pour envoyer des emails personnalisés (identifiants, documents, liens) à une liste de destinataires CSV, avec pièces jointes PDF individuelles et design HTML personnalisable.

## Fonctionnalités

- Thème **dark / clair** commutable à la volée
- Éditeur de design email (couleur header, message texte ou HTML, boutons, footer)
- Aperçu HTML en un clic
- Envoi SMTP avec délai anti-spam configurable
- Pièces jointes PDF automatiques (correspondance par prénom/nom ou email)
- Log d'envoi coloré, exportable
- Système de licences (vérification en ligne via Supabase)

## Stack

| Couche | Technologie |
|---|---|
| App bureau | Python 3.11 + PySide6 |
| Backend licences | Supabase (PostgreSQL + Edge Functions Deno) |
| Paiement | Stripe abonnements |
| Livraison licence | Brevo API |

## Structure

```
mailsentpro/
├── mailcentpro.py             ← Application principale
├── mailcentpro.spec           ← Spec PyInstaller (Windows / Mac / Linux)
├── build_windows.bat          ← Build local Windows
├── build_linux.sh             ← Build local Linux
├── build_mac.sh               ← Build local macOS
├── .github/workflows/
│   └── build-release.yml      ← CI GitHub Actions (3 plateformes)
├── data/
│   └── eleves_exemple.csv
└── supabase/
    ├── functions/
    │   ├── verifier-licence/  ← Vérifie la clé au démarrage
    │   └── stripe-webhook/    ← Reçoit les paiements Stripe
    └── generer_licence.py     ← Gestion manuelle des licences
```

## Lancement en développement

```bash
pip install PySide6
python mailcentpro.py
```

## Build local

```bash
# Linux
bash build_linux.sh        # → MailCentPro-Linux.zip

# macOS
bash build_mac.sh          # → MailCentPro-Mac.zip

# Windows
build_windows.bat          # → MailCentPro-Windows.zip
```

## Release GitHub Actions

Déclencher manuellement depuis l'onglet **Actions** :

```
Actions → Build & Release MailCentPro → Run workflow → tag: v2.x
```

Produit trois assets attachés à la release :
- `MailCentPro-Windows.zip`
- `MailCentPro-Mac.zip`
- `MailCentPro-Linux.zip`

## Format CSV

```
nom,prenom,email,mot_de_passe
Dupont,Marie,marie.dupont@lycee.fr,Xk9#mP2q
Martin,Lucas,lucas.martin@lycee.fr,Ht7$nR4w
```

**Encodage :** UTF-8 · **Séparateur :** virgule

## Configuration SMTP

| Serveur | Hôte | Port |
|---|---|---|
| monlycee.net | `smtp.monlycee.net` | 587 |
| Gmail | `smtp.gmail.com` | 587 |
| Brevo | `smtp-relay.brevo.com` | 587 |

Délai anti-spam recommandé : **3–5 secondes** entre chaque envoi.

## Commandes Supabase

```bash
# Déployer les Edge Functions
supabase functions deploy verifier-licence --project-ref tcexvmzfesnbhfjcgrnz --no-verify-jwt
supabase functions deploy stripe-webhook   --project-ref tcexvmzfesnbhfjcgrnz --no-verify-jwt

# Tester les webhooks
stripe listen --forward-to https://tcexvmzfesnbhfjcgrnz.supabase.co/functions/v1/stripe-webhook

# Générer une licence manuellement
python supabase/generer_licence.py
python supabase/generer_licence.py --list
```
