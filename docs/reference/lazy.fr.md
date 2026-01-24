# Iterateurs Lazy

`fptk.iter.lazy` fournit des utilitaires d'iterateurs lazy pour un traitement des donnees efficace en memoire.

## Concept : Evaluation lazy

L'evaluation lazy retarde le calcul jusqu'a ce que le resultat soit reellement necessaire. Avec les iterateurs lazy, vous pouvez construire des pipelines de transformation qui traitent les donnees un element a la fois, sans charger des collections entieres en memoire.

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

- **Efficacite memoire** : Traitez des jeux de donnees plus grands que la RAM
- **Arret anticipe** : Arretez le traitement quand vous avez assez de resultats
- **Pipelines composables** : Chainez les transformations sans allocations intermediaires

### Le probleme : Evaluation eager

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
| `chunk(xs, n)` | `(Iterable[T], int) -> Iterator[tuple[T, ...]]` | Decoupe en morceaux |
| `group_by_key(xs, key)` | `(Iterable[T], T -> K) -> Iterator[tuple[K, list[T]]]` | Groupe les elements consecutifs |

## Fonctionnement

### `map_iter`

Applique paresseusement une fonction a chaque element :

```python
def map_iter(f, xs):
    for x in xs:
        yield f(x)
```

Utilise un generateur - aucune liste n'est creee. Les valeurs sont calculees une a la fois lors de l'iteration.

### `filter_iter`

Filtre paresseusement les elements selon un predicat :

```python
def filter_iter(pred, xs):
    for x in xs:
        if pred(x):
            yield x
```

Ne produit que les elements qui passent le predicat.

### `chunk`

Decoupe un iterable en morceaux de taille fixe :

```python
def chunk(xs, size):
    it = iter(xs)
    while True:
        buf = tuple(islice(it, size))
        if not buf:
            return
        yield buf
```

Le dernier morceau peut etre plus petit. Utile pour le traitement par lots.

### `group_by_key`

Groupe les elements consecutifs selon une fonction cle :

```python
def group_by_key(xs, key):
    for k, grp in groupby(xs, key=key):
        yield k, list(grp)
```

**Important** : L'entree doit etre pre-triee selon la cle pour des resultats corrects.

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

### Insertions en base de donnees par lots

```python
from fptk.iter.lazy import chunk

def batch_insert(records, batch_size=1000):
    """Insert records in batches to avoid memory issues."""
    for batch in chunk(records, batch_size):
        db.insert_many(batch)
        print(f"Inserted {len(batch)} records")
```

### Appels API pagines

```python
from fptk.iter.lazy import chunk

def fetch_with_pagination(ids: list[int], page_size=100):
    """Fetch resources in pages."""
    for page in chunk(ids, page_size):
        response = api.fetch_batch(list(page))
        yield from response["items"]
```

### Groupement d'entrees de logs

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

### Combiner plusieurs iterateurs

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

### Agregation efficace en memoire

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
| Memoire | O(1) par element | O(n) tout a la fois |
| Temps de demarrage | Instantane | Doit tout traiter d'abord |
| Passages multiples | Doit recreer | Peut iterer a nouveau |
| Acces aleatoire | Non | Oui |
| Debogage | Plus difficile (consomme) | Plus facile (peut inspecter) |

## Quand utiliser les iterateurs lazy

**Utilisez les iterateurs lazy quand :**

- Vous traitez de grands jeux de donnees qui ne tiennent pas en memoire
- Vous n'avez peut-etre pas besoin de tous les resultats (arret anticipe)
- Vous construisez des pipelines de transformations
- Vous lisez depuis des fichiers ou des flux
- L'efficacite memoire est importante

**Utilisez les listes eager quand :**

- Vous avez besoin d'un acces aleatoire
- Vous devez iterer plusieurs fois
- Le jeu de donnees est petit
- Vous devez connaitre la longueur a l'avance
- Le debogage est une priorite

## Alternatives Python natives

Les fonctions lazy de fptk encapsulent les builtins Python avec un typage explicite :

| fptk | Builtin Python |
|------|---------------|
| `map_iter(f, xs)` | `map(f, xs)` |
| `filter_iter(p, xs)` | `filter(p, xs)` |
| `chunk(xs, n)` | `itertools.batched(xs, n)` (3.12+) |
| `group_by_key(xs, k)` | `itertools.groupby(xs, k)` |

Les versions fptk fournissent de meilleurs indices de type et un style d'API coherent.

## Voir aussi

- [Recette traitement de donnees](../recipes/data-processing.md) - Traitement lazy dans les pipelines ETL
- [`traverse`](traverse.md) - Pour travailler avec des collections de Option/Result
- [`async_tools`](async.md) - Pour le traitement par lots async
