# Traverse

Le module `fptk.adt.traverse` propose des opérations pour manipuler des collections de valeurs `Option` ou `Result`, permettant de « retourner » la structure du conteneur tout en assurant une gestion des erreurs robuste.

## Concept : Traverse et Sequence

Face à une liste de calculs susceptibles d'échouer, deux besoins majeurs apparaissent :

1.  **Sequence** : transformer une `list[Option[T]]` en `Option[list[T]]`.
2.  **Traverse** : appliquer une fonction à une liste d'éléments simples, puis regrouper les résultats faillibles en un seul conteneur.

Ces opérations inversent littéralement l'imbrication des conteneurs :

```
list[Option[T]]    →  Option[list[T]]
list[Result[T, E]]  →  Result[list[T], E]
```

C'est une approche indispensable pour :

-   **Une sémantique d'arrêt immédiat (fail-fast)** : stopper le traitement au premier `Nothing` ou `Err` rencontré.
-   **Des résultats « tout ou rien »** : soit vous obtenez la liste complète des succès, soit vous recevez le signal du premier échec.
-   **Des pipelines fluides** : manipulez des collections d'opérations faillibles comme s'il s'agissait d'une opération unique.

### Le problème : l'accumulation manuelle laborieuse

```python
def recuperer_tous_utilisateurs(ids: list[int]) -> list[User]:
    resultats = []
    for id in ids:
        utilisateur = fetch_user(id)  # Renvoie Option[User]
        if utilisateur.is_none():
            return []  # Que faire si un seul échoue ? Tout abandonner ?
        resultats.append(utilisateur.unwrap())
    return resultats

# Ce code est verbeux, propice aux erreurs et peu lisible.
```

### La solution avec `Traverse`

```python
from fptk.adt.traverse import traverse_option

def recuperer_tous_utilisateurs(ids: list[int]) -> Option[list[User]]:
    return traverse_option(ids, fetch_user)
    # Renvoie Some([users...]) si TOUS ont réussi.
    # Renvoie NOTHING si au moins UN a échoué.
```

Le code devient concis, sa sémantique est explicite et il s'intègre parfaitement au reste de l'écosystème fptk.

## API

### Fonctions Sequence

| Fonction | Signature | Description |
| :--- | :--- | :--- |
| `sequence_option(xs)` | `Iterable[Option[A]] -> Option[list[A]]` | Collecte les valeurs `Some` si elles sont toutes présentes. |
| `sequence_result(xs)` | `Iterable[Result[A, E]] -> Result[list[A], E]` | Collecte les valeurs `Ok` si elles ont toutes réussi. |

### Fonctions Traverse

| Fonction | Signature | Description |
| :--- | :--- | :--- |
| `traverse_option(xs, f)` | `(Iterable[A], A -> Option[B]) -> Option[list[B]]` | Applique `f` et collecte les succès. |
| `traverse_result(xs, f)` | `(Iterable[A], A -> Result[B, E]) -> Result[list[B], E]` | Applique `f` et collecte les succès. |

### Variantes asynchrones (Async)

| Fonction | Mode d'exécution | Description |
| :--- | :--- | :--- |
| `traverse_*_async` | Séquentiel | Applique et collecte un par un. |
| `traverse_*_parallel` | Parallèle | Applique et collecte tout de front. |

**Quand choisir quelle variante ?**

-   **Séquentiel (`*_async`)** : idéal pour les API avec limitation de débit (rate limiting) ou les opérations interdépendantes.
-   **Parallèle (`*_parallel`)** : à privilégier pour les tâches indépendantes afin d'obtenir un débit maximal.

## Fonctionnement technique

### Comportement Fail-Fast

Toutes ces opérations adoptent une stratégie d'**arrêt immédiat (fail-fast)**. Dès qu'un échec survient :

-   Le traitement s'interrompt (économie de ressources).
-   Seule la première erreur rencontrée est renvoyée.
-   Pour collecter *toutes* les erreurs, utilisez plutôt [`validate_all`](validate.md).

## Exemples d'utilisation

### Analyse d'une liste de saisies

```python
from fptk.adt.traverse import traverse_option
from fptk.adt.option import Some, NOTHING

def analyser_entier(s: str) -> Option[int]:
    try:
        return Some(int(s))
    except ValueError:
        return NOTHING

# Analyse tout... ou rien
resultat = traverse_option(["1", "2", "3"], analyser_entier)
# Some([1, 2, 3])

resultat = traverse_option(["1", "erreur", "3"], analyser_entier)
# NOTHING (le traitement s'est arrêté à "erreur")
```

### Parcours asynchrone

```python
async def recuperer_users_parallele(ids: list[int]) -> Result[list[User], str]:
    # Déclenche toutes les requêtes simultanément
    return await traverse_result_parallel(ids, fetch_user_async)

async def recuperer_users_sequentiel(ids: list[int]) -> Result[list[User], str]:
    # Interroge la base un par un (plus prudent pour les gros volumes)
    return await traverse_result_async(ids, fetch_user_async)
```

## Traverse vs validate_all : le match

| Opération | Stratégie | Usage recommandé |
| :--- | :--- | :--- |
| **`traverse_result`** | Arrêt immédiat (fail-fast). | Logique interne, pipelines techniques. |
| **`validate_all`** | Accumulation complète. | Saisie utilisateur, formulaires web. |

## Quand utiliser Traverse ?

**Privilégiez Traverse lorsque :**

-   Vous traitez une collection de données de façon uniforme.
-   Chaque étape du traitement est susceptible d'échouer.
-   Vous exigez que la totalité de la collection soit valide pour continuer.
-   Seule la première erreur survenue vous intéresse.

**Privilégiez `*_parallel` lorsque :**

-   Les tâches sont totalement indépendantes les unes des autres.
-   Vous visez la meilleure performance brute possible.

## Voir aussi

-   [`Option`](option.md) — Le type de base pour les valeurs facultatives.
-   [`Result`](result.md) — Le type de base pour les calculs faillibles.
-   [`validate_all`](validate.md) — Pour accumuler l'ensemble des erreurs de validation.
-   [`gather_results`](async.md) — Pour orchestrer des opérations asynchrones parallèles.