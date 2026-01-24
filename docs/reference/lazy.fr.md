# Itérateurs paresseux (Lazy)

Le module `fptk.iter.lazy` propose des utilitaires d'itérateurs paresseux (lazy iterators) pour un traitement des données optimal, particulièrement économe en mémoire.

## Concept : L'évaluation paresseuse

L'évaluation paresseuse (lazy evaluation) consiste à différer un calcul jusqu'à ce que son résultat soit réellement indispensable. En utilisant des itérateurs paresseux, vous bâtissez des pipelines de transformation qui traitent les données élément par élément, sans jamais avoir à charger des collections massives en mémoire.

```python
# Mode immédiat (eager) : charge 1 million d'éléments et crée des listes intermédiaires
doubles = [x * 2 for x in million_elements]
filtres = [x for x in doubles if x > 100]
resultat = list(filtres)[:10]  # On n'en voulait que 10 !

# Mode paresseux (lazy) : traite un élément à la fois, s'arrête dès que le compte est bon
from fptk.iter.lazy import map_iter, filter_iter
pipeline = filter_iter(
    lambda x: x > 100,
    map_iter(lambda x: x * 2, million_elements)
)
resultat = list(islice(pipeline, 10))  # Calcule uniquement le strict nécessaire
```

Cette approche est capitale pour :

-   **L'efficacité mémoire** : traitez des jeux de données dont la taille dépasse celle de votre RAM.
-   **L'arrêt précoce** : interrompez le traitement dès que vous avez obtenu suffisamment de résultats.
-   **La composabilité** : enchaînez vos transformations sans générer d'allocations mémoire intermédiaires coûteuses.

### Le problème : l'évaluation immédiate (eager)

```python
# Chaque étape génère une liste complète en mémoire
utilisateurs = charger_utilisateurs()      # 1M d'utilisateurs en RAM
actifs = [u for u in utilisateurs if u.active] # Une deuxième liste
emails = [u.email for u in actifs]             # Une troisième...
domaines = [e.split("@")[1] for e in emails]   # Une quatrième !

# Occupation mémoire : O(4N)
```

### La solution : le pipeline paresseux

```python
from fptk.iter.lazy import map_iter, filter_iter

# Rien n'est chargé pour l'instant : on ne fait que définir le pipeline
pipeline = map_iter(
    lambda u: u.email.split("@")[1],
    filter_iter(lambda u: u.active, iter_utilisateurs())
)

# La consommation se fait ici, un par un
for domaine in pipeline:
    print(domaine)

# Occupation mémoire : O(1) par élément traité
```

## API

### Fonctions

| Fonction | Signature | Description |
| :--- | :--- | :--- |
| `map_iter(f, xs)` | `(A -> B, Iterable[A]) -> Iterator[B]` | Application paresseuse d'une fonction. |
| `filter_iter(pred, xs)` | `(A -> bool, Iterable[A]) -> Iterator[A]` | Filtrage paresseux selon un prédicat. |
| `chunk(xs, n)` | `(Iterable[T], int) -> Iterator[tuple[T, ...]]` | Découpage en morceaux (lots) de taille fixe. |
| `group_by_key(xs, key)` | `(Iterable[T], T -> K) -> Iterator[tuple[K, list[T]]]` | Groupement des éléments consécutifs par clé. |

## Fonctionnement technique

### `map_iter`

Elle applique une fonction à chaque élément au moment du passage de l'itérateur :

```python
def map_iter(f, xs):
    for x in xs:
        yield f(x)
```

Grâce à l'usage d'un générateur (`yield`), aucune liste n'est créée. Les valeurs sont calculées à la volée.

### `filter_iter`

Elle ne produit que les éléments satisfaisant le prédicat :

```python
def filter_iter(pred, xs):
    for x in xs:
        if pred(x):
            yield x
```

### `chunk`

Elle scinde un itérable en morceaux de taille fixe. Le dernier morceau peut être plus petit si nécessaire. C'est l'outil idéal pour le traitement par lots (batching).

### `group_by_key`

Elle regroupe les éléments consécutifs partageant la même clé de tri.
**Important** : pour obtenir un résultat correct, l'entrée doit être préalablement triée selon cette clé.

## Exemples d'utilisation

### Pipeline paresseux simple

```python
from fptk.iter.lazy import map_iter, filter_iter

# Définition d'un pipeline sans exécution immédiate
nombres = range(1000000)
doubles = map_iter(lambda x: x * 2, nombres)
grands = filter_iter(lambda x: x > 100000, doubles)

# On ne récupère que ce dont on a besoin
from itertools import islice
premiers_10 = list(islice(grands, 10))
# Seuls les ~50 000 premiers éléments ont été calculés pour obtenir 10 résultats.
```

### Traitement de fichiers volumineux

```python
from fptk.iter.lazy import map_iter, filter_iter

def traiter_gros_csv(chemin: str):
    with open(chemin) as f:
        next(f) # Ignore l'en-tête

        # Pipeline de traitement ligne à ligne
        lignes = map_iter(str.strip, f)
        non_vides = filter_iter(bool, lignes)
        donnees = map_iter(lambda l: l.split(","), non_vides)
        valides = filter_iter(lambda r: len(r) == 3, donnees)

        for ligne in valides:
            yield traiter_ligne(ligne)
```

### Insertion en base de données par lots

```python
from fptk.iter.lazy import chunk

def insertion_par_lots(enregistrements, taille_lot=1000):
    """Insère des données par blocs pour ménager la base de données et la RAM."""
    for lot in chunk(enregistrements, taille_lot):
        db.insert_many(lot)
        print(f"{len(lot)} enregistrements insérés")
```

### Combinaison avec Result

```python
from fptk.iter.lazy import map_iter, filter_iter
from fptk.adt.result import Ok, Err

def analyser_ligne(ligne: str) -> Result[Record, str]:
    try:
        return Ok(Record.parse(ligne))
    except ValueError as e:
        return Err(str(e))

def traiter_fichier(chemin: str):
    with open(chemin) as f:
        # Analyse de chaque ligne
        resultats = map_iter(analyser_ligne, f)

        # On ne garde que les analyses réussies
        valides = filter_iter(lambda r: r.is_ok(), resultats)

        # Extraction des valeurs
        enregistrements = map_iter(lambda r: r.unwrap(), valides)

        for rec in enregistrements:
            traiter(rec)
```

## Lazy vs Eager : le match

| Caractéristique | Paresseux (Iterator) | Immédiat (List) |
| :--- | :--- | :--- |
| **Mémoire** | O(1) par élément. | O(n) pour la totalité. |
| **Réactivité** | Démarrage instantané. | Doit tout traiter avant de commencer. |
| **Passages multiples** | Doit être recréé. | Peut être parcouru plusieurs fois. |
| **Accès aléatoire** | Impossible. | Possible (par index). |
| **Débogage** | Plus complexe (consomme l'itérateur). | Plus simple (inspection directe). |

## Quand utiliser les itérateurs paresseux ?

**Privilégiez les itérateurs paresseux lorsque :**

-   Vous manipulez des volumes de données qui risquent de saturer la RAM.
-   Vous n'avez pas nécessairement besoin de traiter la totalité des éléments (arrêt précoce).
-   Vous construisez des pipelines de transformation successives.
-   Vous lisez des données provenant de flux (streams) ou de fichiers.

**Privilégiez les listes classiques lorsque :**

-   Vous avez besoin d'accéder aux éléments de façon aléatoire.
-   Vous devez parcourir la collection plusieurs fois.
-   Le jeu de données est de petite taille.
-   Vous devez connaître la longueur totale de la collection à l'avance.

## Voir aussi

-   [Exemple : Traitement de données](../examples/data-processing.md) — Usage intensif dans les pipelines ETL.
-   [`traverse`](traverse.md) — Pour manipuler des collections d'`Option` ou de `Result`.
-   [`async_tools`](async.md) — Pour le traitement par lots asynchrone.