# Itérateurs Lazy

`fptk.iter.lazy` fournit des utilitaires d'itérateurs lazy pour un traitement des données efficace en mémoire.

## Concept : Évaluation lazy

L'évaluation lazy retarde le calcul jusqu'à ce que le résultat soit réellement nécessaire. Avec les itérateurs lazy, vous pouvez construire des pipelines de transformation qui traitent les données un élément à la fois, sans charger des collections entières en mémoire.

```python
# Eager: loads all 1M items, creates intermediate lists
doubled = [x * 2 for x in million_items]
filtered = [x for x in doubled if x > 100]
result = list(filtered)[:10]  # We only needed 10!

# Lazy: processes one at a time, stops after 10
from fptk.iter.lazy import map_iter, filter_iter
pipeline = filter_iter(
    lambda x: x > 100,
    map_iter(lambda x: x * 2, million_items)
)
result = list(islice(pipeline, 10))  # Only computes what's needed
```

Cela est important car :

- **Efficacité mémoire** : Traitez des jeux de données plus grands que la RAM
- **Arrêt anticipé** : Arrêtez le traitement quand vous avez assez de résultats
- **Pipelines composables** : Chaînez les transformations sans allocations intermédiaires

### Le problème : Évaluation eager

```python
# Each step creates a full list in memory
users = load_all_users()              # 1M users in memory
active = [u for u in users if u.active]  # Another list
emails = [u.email for u in active]        # Another list
domains = [e.split("@")[1] for e in emails]  # Another list

# Memory usage: O(4N)
```

### La solution lazy

```python
from fptk.iter.lazy import map_iter, filter_iter

# Nothing loads yet—just builds a pipeline
pipeline = map_iter(
    lambda u: u.email.split("@")[1],
    filter_iter(lambda u: u.active, load_users_iterator())
)

# Only now do we consume, one item at a time
for domain in pipeline:
    print(domain)

# Memory usage: O(1) per item
```

## API

### Fonctions

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `map_iter(f, xs)` | `(A -> B, Iterable[A]) -> Iterator[B]` | Map lazy |
| `filter_iter(pred, xs)` | `(A -> bool, Iterable[A]) -> Iterator[A]` | Filter lazy |
| `chunk(xs, n)` | `(Iterable[T], int) -> Iterator[tuple[T, ...]]` | Découpe en morceaux |
| `group_by_key(xs, key)` | `(Iterable[T], T -> K) -> Iterator[tuple[K, list[T]]]` | Groupe les éléments consécutifs |

## Fonctionnement

### `map_iter`

Applique paresseusement une fonction à chaque élément :

```python
def map_iter(f, xs):
    for x in xs:
        yield f(x)
```

Utilise un générateur - aucune liste n'est créée. Les valeurs sont calculées une à la fois lors de l'itération.

### `filter_iter`

Filtre paresseusement les éléments selon un prédicat :

```python
def filter_iter(pred, xs):
    for x in xs:
        if pred(x):
            yield x
```

Ne produit que les éléments qui passent le prédicat.

### `chunk`

Découpe un itérable en morceaux de taille fixe :

```python
def chunk(xs, size):
    it = iter(xs)
    while True:
        buf = tuple(islice(it, size))
        if not buf:
            return
        yield buf
```

Le dernier morceau peut être plus petit. Utile pour le traitement par lots.

### `group_by_key`

Groupe les éléments consécutifs selon une fonction clé :

```python
def group_by_key(xs, key):
    for k, grp in groupby(xs, key=key):
        yield k, list(grp)
```

**Important** : L'entrée doit être pré-triée selon la clé pour des résultats corrects.

## Exemples

### Pipeline lazy basique

```python
from fptk.iter.lazy import map_iter, filter_iter

# Build a lazy pipeline
numbers = range(1000000)  # Lazy range
doubled = map_iter(lambda x: x * 2, numbers)
big = filter_iter(lambda x: x > 100000, doubled)

# Nothing computed yet!

# Take only what we need
from itertools import islice
first_10 = list(islice(big, 10))
# Only computed ~50000 items to get 10 results
```

### Traitement de gros fichiers

```python
from fptk.iter.lazy import map_iter, filter_iter

def process_large_csv(path: str):
    with open(path) as f:
        # Skip header
        next(f)

        # Lazy pipeline
        lines = map_iter(str.strip, f)
        non_empty = filter_iter(bool, lines)
        rows = map_iter(lambda l: l.split(","), non_empty)
        valid = filter_iter(lambda r: len(r) == 3, rows)

        # Process one at a time
        for row in valid:
            yield process_row(row)
```

### Insertions en base de données par lots

```python
from fptk.iter.lazy import chunk

def batch_insert(records, batch_size=1000):
    """Insert records in batches to avoid memory issues."""
    for batch in chunk(records, batch_size):
        db.insert_many(batch)
        print(f"Inserted {len(batch)} records")
```

### Appels API paginés

```python
from fptk.iter.lazy import chunk

def fetch_with_pagination(ids: list[int], page_size=100):
    """Fetch resources in pages."""
    for page in chunk(ids, page_size):
        response = api.fetch_batch(list(page))
        yield from response["items"]
```

### Groupement d'entrées de logs

```python
from fptk.iter.lazy import group_by_key

def process_logs_by_hour(log_entries):
    """Process logs grouped by hour."""
    # Sort by timestamp first (required for group_by_key)
    sorted_logs = sorted(log_entries, key=lambda e: e.timestamp)

    for hour, entries in group_by_key(sorted_logs, lambda e: e.timestamp.hour):
        print(f"Hour {hour}: {len(entries)} entries")
        process_hour_batch(entries)
```

### Combinaison avec Result

```python
from fptk.iter.lazy import map_iter, filter_iter
from fptk.adt.result import Ok, Err

def parse_line(line: str) -> Result[Record, str]:
    try:
        return Ok(Record.parse(line))
    except ValueError as e:
        return Err(str(e))

def process_file(path: str):
    with open(path) as f:
        # Parse each line
        results = map_iter(parse_line, f)

        # Filter to successful parses
        valid = filter_iter(lambda r: r.is_ok(), results)

        # Extract values
        records = map_iter(lambda r: r.unwrap(), valid)

        for record in records:
            process(record)
```

### Pipeline ETL lazy

```python
from fptk.iter.lazy import map_iter, filter_iter, chunk

def etl_pipeline(source_path: str, dest_db):
    """Extract-Transform-Load with lazy processing."""

    # Extract: read file lazily
    with open(source_path) as f:
        raw_lines = map_iter(str.strip, f)

        # Transform: parse and validate
        parsed = map_iter(parse_json, raw_lines)
        valid = filter_iter(lambda r: r.is_ok(), parsed)
        records = map_iter(lambda r: r.unwrap(), valid)
        transformed = map_iter(transform_record, records)

        # Load: batch inserts
        for batch in chunk(transformed, 500):
            dest_db.insert_many(batch)
```

### Combiner plusieurs itérateurs

```python
from fptk.iter.lazy import map_iter, filter_iter
from itertools import chain

# Combine multiple sources lazily
source1 = load_csv("file1.csv")
source2 = load_csv("file2.csv")
source3 = load_csv("file3.csv")

# chain is lazy too
all_records = chain(source1, source2, source3)

# Apply common processing
processed = map_iter(normalize, filter_iter(is_valid, all_records))
```

### Agrégation efficace en mémoire

```python
from fptk.iter.lazy import map_iter

def streaming_average(numbers):
    """Compute average without storing all numbers."""
    total = 0
    count = 0
    for n in numbers:
        total += n
        count += 1
    return total / count if count > 0 else 0

# Process billions of numbers with O(1) memory
avg = streaming_average(map_iter(float, huge_file))
```

## Lazy vs Eager

| Aspect | Lazy (Iterator) | Eager (List) |
|--------|-----------------|--------------|
| Mémoire | O(1) par élément | O(n) tout à la fois |
| Temps de démarrage | Instantané | Doit tout traiter d'abord |
| Passages multiples | Doit recréer | Peut itérer à nouveau |
| Accès aléatoire | Non | Oui |
| Débogage | Plus difficile (consomme) | Plus facile (peut inspecter) |

## Quand utiliser les itérateurs lazy

**Utilisez les itérateurs lazy quand :**

- Vous traitez de grands jeux de données qui ne tiennent pas en mémoire
- Vous n'avez peut-être pas besoin de tous les résultats (arrêt anticipé)
- Vous construisez des pipelines de transformations
- Vous lisez depuis des fichiers ou des flux
- L'efficacité mémoire est importante

**Utilisez les listes eager quand :**

- Vous avez besoin d'un accès aléatoire
- Vous devez itérer plusieurs fois
- Le jeu de données est petit
- Vous devez connaître la longueur à l'avance
- Le débogage est une priorité

## Alternatives Python natives

Les fonctions lazy de fptk encapsulent les builtins Python avec un typage explicite :

| fptk | Builtin Python |
|------|---------------|
| `map_iter(f, xs)` | `map(f, xs)` |
| `filter_iter(p, xs)` | `filter(p, xs)` |
| `chunk(xs, n)` | `itertools.batched(xs, n)` (3.12+) |
| `group_by_key(xs, k)` | `itertools.groupby(xs, k)` |

Les versions fptk fournissent de meilleurs indices de type et un style d'API cohérent.

## Voir aussi

- [Recette traitement de données](../recipes/data-processing.md) - Traitement lazy dans les pipelines ETL
- [`traverse`](traverse.md) - Pour travailler avec des collections de Option/Result
- [`async_tools`](async.md) - Pour le traitement par lots async
