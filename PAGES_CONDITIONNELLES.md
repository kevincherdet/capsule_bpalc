# Pages conditionnelles — Spécification

## Problématique

Les capsules sont construites à partir d'un **template commun** (mêmes sections, mêmes slides) décliné pour chaque banque. Or certains slides ne s'appliquent pas à toutes les banques.

**Exemple concret :** le forfait jours.

- La **convention collective de branche** (Banque Populaire) ne fixe pas de forfait jours spécifique, mais le Code du travail le permet.
- Certaines banques l'appliquent (ex : forfait de 209 jours).
- À la **BPALC**, l'accord ATT de 2015 a basculé tous les cadres au forfait jours vers le rythme 39h/5j avec 22 JRTT (depuis le 1er janvier 2016). Le forfait jours n'est donc plus en vigueur.

**Conséquence :** les deux slides "Le forfait annuel en jours" et "Obligations de votre employeur" existent dans le template mais ne doivent pas apparaître dans la capsule BPALC.

Aujourd'hui, la seule option est de supprimer ces slides du markdown BPALC, ce qui casse la logique de template réutilisable.

## Autres cas identifiés

| Slide / contenu | Banques concernées | Banques non concernées |
|---|---|---|
| Forfait jours (2 slides) | Banques sans accord ATT spécifique | BPALC |
| Temps partiel scolaire | Banques avec accord spécifique | BPALC |
| Astreintes (accord entreprise) | Banques avec accord astreintes | BPALC (applique la CCN) |
| Primes spécifiques | Variable selon les accords | Variable |

La liste s'allongera au fur et à mesure des capsules.

## Solution proposée

### Principe

Ajouter un système de **conditions** au niveau de chaque page, piloté par le front matter YAML de la capsule.

### Syntaxe markdown

Un commentaire `<!-- condition: nom_flag -->` sur une page rend son affichage conditionnel :

```markdown
---

### Le forfait annuel en jours
<!-- condition: forfait_jours -->
<!-- layout: image-left -->
<!-- image: forfait_jours.jpg -->

Contenu du slide...

---
```

### Front matter

Chaque capsule déclare les flags actifs :

```yaml
---
banque: BPALC
couleur: "#1a5fa6"
conditions:
  forfait_jours: false
  temps_partiel_scolaire: false
---
```

```yaml
---
banque: BRED
couleur: "#e4002b"
conditions:
  forfait_jours: true
  temps_partiel_scolaire: true
---
```

### Règles

1. Une page **sans** `<!-- condition: -->` s'affiche toujours (comportement par défaut, aucun impact sur l'existant).
2. Une page **avec** `<!-- condition: xxx -->` ne s'affiche que si `conditions.xxx` vaut `true` dans le front matter.
3. Si le flag n'existe pas dans le front matter, la page est **masquée** (sécurité : on n'affiche pas un contenu non validé).
4. Les pages masquées sont **ignorées** par le sommaire, la sidebar et la navigation (prev/next).
5. Les popups de navigation (`navigate: Titre du slide`) vers une page masquée sont aussi masqués.

### Impact technique

Modification limitée à `index.html`, fonction `parsePages()` :

- Extraire `<!-- condition: xxx -->` au même moment que les autres métadonnées
- Vérifier `config.conditions[xxx]` (issu du front matter)
- Exclure la page du tableau `pages[]` si la condition n'est pas remplie

Estimation : ~10 lignes de JS.
