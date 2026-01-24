# Référence de l'API

Cette section documente chaque module, fonction et type constituant fptk. Chaque page détaille les concepts de programmation fonctionnelle sous-jacents, le fonctionnement technique de l'implémentation et fournit des exemples d'utilisation concrets.

## Aperçu des modules

### Fonctions de base

[`fptk.core.func`](core.md) — Combinateurs essentiels pour l'assemblage et la transformation de fonctions.

| Fonction | Objectif |
| :--- | :--- |
| `pipe` | Orchestre le passage d'une valeur à travers une séquence de fonctions (gauche à droite). |
| `compose` | Assemble des fonctions selon la notation mathématique (droite à gauche). |
| `curry` | Transforme une fonction multi-arguments en une chaîne de fonctions à argument unique. |
| `flip` | Permute l'ordre des deux premiers arguments d'une fonction. |
| `tap` | Déclenche des effets de bord sans interrompre ni modifier le flux de données. |
| `thunk` | Définit un calcul paresseux (lazy) dont le résultat est mis en cache (mémoïsé). |
| `identity` | Renvoie simplement l'entrée telle quelle. |
| `const` | Ignore ses arguments pour renvoyer systématiquement la même valeur fixe. |
| `once` | Garantit qu'une fonction ne s'exécute qu'une seule fois au maximum. |
| `try_catch` | Convertit les fonctions levant des exceptions en fonctions retournant des valeurs `Result`. |

### Types de données algébriques (ADT)

Ces types modélisent des schémas courants de manière sûre, robuste et composable.

| Type | Module | Objectif |
| :--- | :--- | :--- |
| [`Option`](option.md) | `fptk.adt.option` | Gestion explicite de l'absence de valeur (remplace avantageusement les tests sur `None`). |
| [`Result`](result.md) | `fptk.adt.result` | Gestion typée des erreurs (alternative robuste aux exceptions). |
| [`Reader`](reader.md) | `fptk.adt.reader` | Injection de dépendances via la circulation transparente d'un environnement. |
| [`State`](state.md) | `fptk.adt.state` | Modélisation pure de calculs impliquant des changements d'état. |
| [`Writer`](writer.md) | `fptk.adt.writer` | Accumulation de journaux (logs) ou de métriques parallèlement au calcul principal. |
| [`NonEmptyList`](nelist.md) | `fptk.adt.nelist` | Type de liste garantissant la présence d'au moins un élément. |

### Opérations sur les collections

| Module | Objectif |
| :--- | :--- |
| [`traverse`](traverse.md) | Fonctions `sequence` et `traverse` pour manipuler des collections d'`Option` ou de `Result`. |
| [`validate`](validate.md) | Validation de style applicatif permettant d'accumuler l'ensemble des erreurs. |
| [`lazy`](lazy.md) | Opérations sur itérateurs paresseux pour un traitement de données économe en mémoire. |
| [`async`](async.md) | Utilitaires asynchrones pour orchestrer des opérations concurrentes basées sur `Result`. |

## Comment consulter cette documentation ?

Chaque page de référence adopte une structure constante pour faciliter votre lecture :

1.  **Concept** — L'idée fondamentale issue de la programmation fonctionnelle et son intérêt pratique.
2.  **API** — Détail des types, des fonctions et de leurs signatures respectives.
3.  **Fonctionnement** — Précisions sur l'implémentation et les choix de conception.
4.  **Exemples** — Extraits de code illustrant les cas d'utilisation les plus fréquents.
5.  **Quand l'utiliser ?** — Conseils pour choisir l'outil le plus adapté à votre besoin.

## Accès rapide par besoin

**« Je veux gérer l'absence de valeur sans multiplier les tests sur None »**
→ Consulter [`Option`](option.md)

**« Je préfère utiliser des erreurs typées plutôt que des exceptions »**
→ Consulter [`Result`](result.md)

**« Je souhaite enchaîner mes transformations de manière fluide et lisible »**
→ Consulter [`pipe` et `compose`](core.md)

**« Je veux injecter des dépendances sans polluer tous mes paramètres de fonction »**
→ Consulter [`Reader`](reader.md)

**« Je dois suivre des changements d'état de façon pure et prévisible »**
→ Consulter [`State`](state.md)

**« Je veux collecter des logs ou des métriques pendant un calcul »**
→ Consulter [`Writer`](writer.md)

**« Je souhaite valider des données et obtenir la liste complète des erreurs »**
→ Consulter [`validate_all`](validate.md)

**« Je dois traiter des volumes de données importants sans saturer la mémoire »**
→ Consulter les [itérateurs paresseux (lazy iterators)](lazy.md)

**« Je veux lancer des opérations asynchrones et combiner leurs résultats »**
→ Consulter les [outils async](async.md)