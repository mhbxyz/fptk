# Référence

Cette référence documente chaque module, fonction et type de fptk. Chaque page explique les concepts de programmation fonctionnelle sous-jacents, le fonctionnement de l'implémentation et fournit des exemples pratiques.

## Aperçu des modules

### Fonctions de base

[`fptk.core.func`](core.md) — Combinateurs de fonctions pour composer et transformer des fonctions.

| Fonction | Objectif |
|----------|----------|
| `pipe` | Faire passer une valeur à travers des fonctions de gauche à droite |
| `compose` | Combiner des fonctions de droite à gauche (notation mathématique) |
| `curry` | Transformer des fonctions à plusieurs arguments en chaînes de fonctions à un argument |
| `flip` | Permuter les deux premiers arguments d'une fonction |
| `tap` | Exécuter des effets de bord sans interrompre le flux de données |
| `thunk` | Calcul paresseux et mémoïsé |
| `identity` | Retourner l'entrée inchangée |
| `const` | Ignorer les arguments, toujours retourner la même valeur |
| `once` | Exécuter une fonction au plus une fois |
| `try_catch` | Convertir les exceptions en valeurs Result |

### Types de données algébriques

Ces types modélisent des patrons courants de manière sûre et composable.

| Type | Module | Objectif |
|------|--------|----------|
| [`Option`](option.md) | `fptk.adt.option` | Gestion explicite de l'absence (remplace les vérifications de `None`) |
| [`Result`](result.md) | `fptk.adt.result` | Gestion typée des erreurs (remplace les exceptions) |
| [`Reader`](reader.md) | `fptk.adt.reader` | Injection de dépendances via le passage d'environnement |
| [`State`](state.md) | `fptk.adt.state` | Calculs avec état purs |
| [`Writer`](writer.md) | `fptk.adt.writer` | Accumulation de logs parallèlement au calcul |
| [`NonEmptyList`](nelist.md) | `fptk.adt.nelist` | Listes garanties d'avoir au moins un élément |

### Opérations sur les collections

| Module | Objectif |
|--------|----------|
| [`traverse`](traverse.md) | Séquence et traverse pour les collections Option/Result |
| [`validate`](validate.md) | Validation applicative (accumule toutes les erreurs) |
| [`lazy`](lazy.md) | Opérations d'itérateurs paresseux économes en mémoire |
| [`async`](async.md) | Utilitaires asynchrones pour les opérations Result concurrentes |

## Comment lire ces pages

Chaque page de référence suit une structure cohérente :

1. **Concept** — Quelle idée de programmation fonctionnelle cela implémente et pourquoi c'est important
2. **API** — Types, fonctions et leurs signatures
3. **Fonctionnement** — Détails d'implémentation et décisions de conception
4. **Exemples** — Code pratique montrant les patrons d'utilisation courants
5. **Quand utiliser** — Conseils sur les cas d'utilisation appropriés

## Liens rapides par cas d'utilisation

**"Je veux gérer les valeurs manquantes sans vérifications de None"**
→ [`Option`](option.md)

**"Je veux des erreurs typées au lieu d'exceptions"**
→ [`Result`](result.md)

**"Je veux enchaîner des transformations proprement"**
→ [`pipe`, `compose`](core.md)

**"Je veux l'injection de dépendances sans passer la configuration partout"**
→ [`Reader`](reader.md)

**"Je veux suivre les changements d'état de manière pure"**
→ [`State`](state.md)

**"Je veux accumuler des logs pendant le calcul"**
→ [`Writer`](writer.md)

**"Je veux valider et collecter toutes les erreurs"**
→ [`validate_all`](validate.md)

**"Je veux traiter de grandes quantités de données sans tout charger en mémoire"**
→ [`lazy iterators`](lazy.md)

**"Je veux exécuter des opérations asynchrones et combiner leurs résultats"**
→ [`async tools`](async.md)
