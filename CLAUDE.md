# Projet Capsule BPALC

## Contexte

Capsule interactive pour la BPALC, remplaçant Genially. Client : **La Faabrick Cherdet** (conseil droit social).

## Structure du projet

```
BPALC/
├── prototype/
│   ├── index.html          # Template engine (HTML + CSS + JS, fichier unique)
│   ├── server.py            # Serveur local Python (save + upload images)
│   └── bpalc/
│       ├── capsule.md       # Contenu de la capsule (markdown + front matter YAML)
│       └── images/          # Images de la capsule (Midjourney, logos, thumbnails sommaire)
├── reference/genially/      # Captures PDF du Genially original
├── propositions/             # Contenu source
│   └── PROPOSITIONS_CAPSULE_BPALC_v2.md  # (~117 pages)
├── *.jpg                     # Captures de référence Genially (couverture, sommaire, slides)
└── CLAUDE.md
```

## Architecture technique

### Template engine (`index.html`)

Fichier unique : charge un `.md`, parse le YAML, découpe les pages sur `---`, rend chaque page avec son layout, auto-ajuste le texte.

**Header persistant** : `initHeader()` charge le logo une fois, `updateHeader()` ne modifie que le titre et la nav. Seul `#capsule-body` est remplacé à chaque navigation.

**Parsing** : `extractPopups()` → `detectTitlesAndSection()` → `transformContent()`. Les popups sont extraits **avant** la détection des `##`/`###`.

**Reveal sans saut** : Le body est masqué (`opacity: 0`) avant le changement de contenu. `waitForImagesAndReveal()` attend que **toutes les images** du slide soient chargées, puis appelle `autoFitText()` et révèle le body d'un coup. Timeout de sécurité 400ms.

### Front matter

```yaml
---
banque: BPALC
nom_complet: Banque Populaire Alsace Lorraine Champagne
couleur: "#1a5fa6"
logo: logo_banquepop.jpg    # Logo unique (CFTC + BP), utilisé dans header et couverture
date_maj: 2026-02-12
---
```

Le champ `logo_client` a été supprimé (même image que `logo`).

### Conventions markdown

| Syntaxe | Rôle |
|---------|------|
| `##` | Section (header + sommaire) |
| `###` | Titre de page (H1 visible dans le rendu) |
| `---` | Séparateur de pages |
| `:::popup Label\n...\n:::` | Popup. Label `+` = rond bleu, autre = bouton classique |
| `:::popup Label\nnavigate: Titre\n:::` | Bouton de navigation (pas de modale) |
| `:::popup _label\n...\n:::` | Popup caché (pas de bouton visible, placement manuel via `data-popup`) |
| `<!-- layout/image/thumbnail: xxx -->` | Métadonnées de page |
| `<!-- subsection: Nom -->` | Sous-section (header affiche "Section / Sous-section") |
| `<!-- title: Nom -->` | Titre de navigation uniquement (sidebar), **pas de H1 visible** |
| `##` seul (sans `###`) | Page section-only (pas de H1, déjà dans le bandeau) |

### Sections et sous-sections

- `## Nom` crée une **section** → apparaît dans le header et le sommaire
- `<!-- subsection: Nom -->` crée une **sous-section** → header affiche "Section / Sous-section", pas d'entrée sommaire
- La sous-section se propage aux pages suivantes (comme la section)
- Un nouveau `##` reset la sous-section
- Les sous-sections apparaissent dans la **sidebar** (burger menu) comme labels en bleu entre les pages

### Titre de page (`<!-- title: -->` vs `###`)

- `### Titre` → titre visible (H1 sur le slide) + titre sidebar
- `<!-- title: Titre -->` → titre sidebar uniquement, **pas de H1** sur le slide. Utile pour les pages composites avec HTML custom (ex: "Heures majorées", "Primes diverses")
- `<!-- title: -->` override `###` s'ils sont tous les deux présents

### Layouts

| Layout | Description |
|--------|-------------|
| `cover` | Couverture : fond blanc, logo en haut à gauche, titre, bouton centré, image plein bord |
| `sommaire` | Grille 4 colonnes de vignettes cliquables, panneau gauche avec titre |
| `image-right-square` / `left` | ~50/50 (ratio ~1:1) |
| `image-right-medium` / `left` | ~60/40 (ratio ~2:3) |
| `image-right-portrait` / `left` | ~75/25 (ratio portrait) |
| `image-right` / `left` | Auto-détection (fallback) |
| `text-only` | Texte seul (max 1000px) |
| `section-intro` | Auto-assigné quand `##` sans `###` ni `<!-- layout: -->` |

### Pattern : couverture

Layout `cover` : fond blanc (`#capsule.layout-cover { background: #ffffff }`), header masqué. Logo CFTC/BP en haut à gauche (80px de large), titre en H1 (38px), texte descriptif, bouton "Commencer la capsule" centré et poussé en bas (`margin-top:auto; align-self:center`). Image plein bord à droite.

### Pattern : sommaire

Layout `sommaire` : panneau gauche (240px) avec titre "Sommaire" + description (sans logo), grille 4 colonnes à droite. Vignettes avec image (aspect-ratio 16/9) et label (hauteur fixe 3em, centré verticalement, overflow hidden). Fichiers thumbnails nommés `sommaire_xxx.jpg/.png`.

### Pattern : page intro section

Layout `text-only` avec HTML inline flex. **2 colonnes** (gap 150px, max-width 550px) ou **3 colonnes** (gap 40px, max-width 380px). Images max-width 300px. Boutons alignés en bas via `margin-top:auto;padding-top:24px`. Voir "Temps de travail" (2 col) et "Salaire et rémunération" (3 col) dans capsule.md.

### Pattern : page composite (text-only + HTML custom)

Pour les slides mixtes (ex: "Travail de nuit / dimanche"), utiliser `<!-- layout: text-only -->` avec du HTML inline structuré. Combiner :
- Popups classiques (`:::popup Label`) pour les boutons normaux
- Popups cachés (`:::popup _label`) pour le contenu accessible via markers manuels
- HTML avec classes `.marker-rows` / `.marker-row` / `.marker-row-text` / `.marker-row-btn` pour reproduire le système de colonnes localement

### Pattern : marker-rows (boutons en 2e colonne)

Quand une page contient `:::popup +`, le moteur active les **marker-rows** : chaque paragraphe = ligne flex avec bouton optionnel en 2e colonne.

**Pipeline** : `extractPopups()` remplace par `%%POPUP:idx:label%%` → `marked.parse()` → `transformContent()` restaure en `<div class="marker-placeholder">` → `buildMarkerGrid()` crée les flex rows.

**Comportement** : les boutons (courts ou longs) restent dans la colonne marker de la ligne. Si plusieurs boutons se suivent, le moteur crée des lignes dédiées.

**IMPORTANT** : Sur les pages avec markers, TOUJOURS utiliser `:::popup` pour les boutons, jamais du HTML inline `<button>`. Les pages SANS markers utilisent des boutons inline classiques.

### Pattern : bouton centré sur ligne dédiée (marker-rows)

Quand on veut un bouton popup **centré** (sans texte dans la colonne 1) sur une page en marker-rows, insérer une ligne vide dédiée avant le popup :

```html
<div class="marker-center"></div>
```

Puis ajouter le popup juste après :

```md
:::popup Mon bouton long
Contenu...
:::
```

Le CSS cible `.marker-center` pour masquer la colonne texte et centrer le bouton sur la ligne.

### Popup navigation

`:::popup Label\nnavigate: Titre slide\n:::` → clic navigue au lieu d'ouvrir une modale.

**Important** : conserver le contenu texte dans les popups `navigate:` même si la page cible existe. Ce contenu sert de **fallback pour les futures capsules** où la page pourrait ne pas encore être créée. Ne jamais supprimer ce contenu sous prétexte qu'il est "mort".

### Popups cachés (placement manuel)

`:::popup _label\nContenu\n:::` → le `_` empêche la génération d'un bouton visible. Le popup est stocké dans `page.popups[idx]` et accessible via un bouton manuel en HTML : `<button class="marker-btn" data-popup="idx">+</button>`. Utilisé pour les pages composites et les boutons positionnés précisément dans du HTML custom.

### Serveur (`server.py`)

`python prototype/server.py` → port 8000. Mode admin : `?admin=true`.

## Conventions de code

- **Police** : Raleway. **Couleur** : `--primary` (front matter). **Fond** : `#f5f6f8`
- **Couverture** : fond blanc `#ffffff` (override via `#capsule.layout-cover`)
- **Titres H1** : 38px, font-weight 800 (identique sur cover et pages normales)
- **Header** : persistant, 66px. **Texte** : justifié, `hyphens: none`
- **Modal** : max-width 900px
- **Constantes** : `AUTOFIT`, `IMAGE_RATIO`, `DEBOUNCE`. **Helpers** : `imgSrc()`, `imgError()`
- **Windows** : toujours normaliser `\r\n` → `\n`. **Accents** : toujours corrects
- **Pas de sources** : ne jamais citer les sources (accords, articles, CC) dans le contenu. Le public cible = salariés, pas juristes
- **Popup-btn centré** : `p:has(> .popup-btn:only-child)` centre auto les boutons seuls
- **Titres dans les popups** : toujours en `###` (jamais en gras `**...**`)
- **Sommaire labels** : hauteur fixe `3em`, centré verticalement, `overflow: hidden`

## Pièges connus

1. **Line endings** : normaliser `\r\n` → `\n` avant tout parsing regex
2. **Live editor** : utiliser `rebuildRawMarkdown()`, jamais indexOf/replace
3. **Ordre d'extraction** : popups avant détection `##`/`###`
4. **CSS overrides** : layouts spécifiques écrasent les règles générales. Pour la couverture, utiliser `#capsule.layout-cover` (spécificité ID+classe) sinon `#capsule { background }` gagne
5. **autoFitText** : appelé UNE SEULE FOIS par `waitForImagesAndReveal()` après chargement de toutes les images + détection layout. Ne plus appeler manuellement
6. **Header** : ne jamais recréer via innerHTML, utiliser `updateHeader()`
7. **Marker placeholders** : `%%POPUP:idx:label%%` avant `marked.parse()`, restaurés après
8. **Spacers dans markers** : `buildMarkerGrid()` et CSS ignorent les spacers
9. **Markers et HTML inline** : sur pages avec `+`, ne jamais mettre de `<button>` HTML — utiliser `:::popup`
10. **Popups cachés** : les `_label` ne génèrent pas de bouton visible. Le bouton manuel doit référencer le bon `data-popup="idx"` (index dans `page.popups[]`)
11. **`<!-- title: -->` vs `###`** : `title` ne génère PAS de H1 visible (`_hiddenTitle = true`). Utiliser `###` si le titre doit apparaître sur le slide
12. **Thumbnails sommaire** : nommage `sommaire_xxx.jpg` (underscores, pas de tirets). Vérifier l'extension (`.jpg` ou `.png`) avec Glob avant référencement
13. **Marker-center** : n'utiliser `<div class="marker-center"></div>` que sur les pages en marker-rows (présence d'au moins un `:::popup +`)

## État actuel (février 2026)

### Sections de la capsule (12 sections)

| # | Section | Pages | Statut |
|---|---------|-------|--------|
| 1 | Qui est concerné par cette capsule ? | Champ d'application | Complet |
| 2 | Classifications | Principe, Grille techniciens, Grille cadres | Complet |
| 3 | Temps de travail | Droit commun, Heures sup, Astreintes, Forfait jours, Obligations forfait, Temps partiel, Heures complémentaires | Complet |
| 4 | Salaire et rémunération | Intro, Salaire minimum, Heures majorées, Travail nuit/dimanche, Primes diverses | Complet |
| 5 | Contrat de travail | Intro, Mentions obligatoires (CDI), Clause de non-concurrence, Validité et levée | Contenu OK, images manquantes |
| 6 | Rupture du contrat de travail | Intro, Préavis, Indemnité licenciement, Départ retraite, Retraite progressive, Aménagement fin de carrière, Fiscalité indemnité | Complet |
| 7 | Télétravail | Éligibilité, Organisation | Complet |
| 8 | Indemnisation maladie | Intro, Indemnisation | Complet |
| 9 | Complémentaire santé, prévoyance et retraite supplémentaire | Intro prévoyance, Prévoyance, Complémentaire santé, Sur-complémentaire, Intro retraite, Retraite supplémentaire | Complet |
| 10 | Congés payés et congés exceptionnels | Intro, Congés payés, Acquisition/maladie, Enfant malade, Proche aidant, Congés spéciaux, Maternité, Congés exceptionnels | Complet |
| 11 | Épargne salariale | Intro, Intéressement, Calcul intéressement, Participation, Calcul participation, PEE, PERCOL-I | Complet |
| 12 | Compte épargne temps | Intro, Alimentation, Utilisation, Indemnisation et rupture | Complet |

### Fait
- Template engine complet, header persistant, marker-rows, sous-sections
- Mode admin, sauvegarde serveur, upload images, navigation, popups, sommaire
- Couverture : fond blanc, logo 80px, titre 38px, bouton centré
- Sommaire : 12 sections, vignettes avec thumbnails (hauteur label fixe)
- Popup navigation (`navigate:` prefix), popups cachés (`_label`)
- Titre de navigation (`<!-- title: -->`) sans affichage H1
- Sous-sections dans la sidebar (burger menu)
- Reveal anti-saut (`waitForImagesAndReveal` + opacity hide/show)
- **12 sections complètes** — tout le contenu de la capsule est rédigé
- Contenu vérifié contre les accords : CET (accord + 4 avenants), PEE, PERCOL-I (accord abondements), intéressement, participation
- Titres popup convertis globalement en `###` (H3)
- Layout `image-right-dual` ratio ajusté (texte 1 / images 1.1)

### À faire
- Images manquantes : `mentions_obligatoires.jpg`, `validite_clause.jpg`, `CET_utilisation.jpg`
- Relecture globale de la capsule (cohérence, formulations, vérification juridique)
- Contenu des popups à valider avec le client
- Responsive : les éléments internes (px fixes) ne scalent pas sur grand écran. À revisiter.
