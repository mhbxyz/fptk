# Traitement de donnees

Ce guide montre comment utiliser fptk pour les taches de traitement de donnees : pipelines ETL, validation, traitement par lots et transformations.

## Pourquoi des patterns fonctionnels pour le traitement de donnees ?

Le code de traitement de donnees souffre souvent de :

- **Pipelines fragiles** : Un mauvais enregistrement casse tout
- **Echecs silencieux** : Erreurs avalees ou enregistrees mais non gerees
- **Problemes de memoire** : Chargement de jeux de donnees entiers quand ce n'est pas necessaire
- **Difficile a deboguer** : Manque de clarte sur l'emplacement des transformations

Les patterns fonctionnels aident en :

- Rendant chaque transformation explicite et testable
- Gerant les erreurs comme des valeurs qui circulent dans le pipeline
- Utilisant l'evaluation paresseuse pour traiter les donnees efficacement
- Separant validation, transformation et E/S

## Pipeline ETL

Un pipeline classique Extract-Transform-Load s'adapte parfaitement a `pipe` :

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all
from fptk.iter.lazy import map_iter
import csv

def process_users_csv(file_path: str):
    """ETL pipeline: Extract → Transform → Load"""
    return pipe(
        file_path,
        read_csv,                    # Extract
        lambda r: r.map(transform_rows),  # Transform
        lambda r: r.bind(load_to_db)      # Load
    )

# --- Extract ---

def read_csv(path: str):
    """Read CSV file, returning Result."""
    try:
        with open(path) as f:
            return Ok(list(csv.DictReader(f)))
    except FileNotFoundError:
        return Err(f"File not found: {path}")
    except Exception as e:
        return Err(f"Read error: {e}")

# --- Transform ---

def transform_rows(rows):
    """Transform each row, collecting valid results."""
    results = [transform_row(row) for row in rows]
    valid = [r.unwrap() for r in results if r.is_ok()]
    errors = [r.unwrap_err() for r in results if r.is_err()]
    return {'users': valid, 'errors': errors}

def transform_row(row: dict):
    """Validate and normalize a single row."""
    return pipe(
        row,
        validate_row,
        lambda r: r.map(normalize),
        lambda r: r.map(enrich)
    )

def validate_row(row: dict):
    return validate_all([
        lambda r: Ok(r) if r.get('email') else Err("Missing email"),
        lambda r: Ok(r) if '@' in r.get('email', '') else Err("Invalid email"),
        lambda r: Ok(r) if r.get('name') else Err("Missing name"),
    ], row)

def normalize(row: dict):
    """Normalize data formats."""
    return {
        'email': row['email'].lower().strip(),
        'name': row['name'].strip(),
        'age': int(row['age']) if row.get('age', '').isdigit() else None
    }

def enrich(row: dict):
    """Add computed fields."""
    return {
        **row,
        'domain': row['email'].split('@')[1],
        'is_adult': row['age'] and row['age'] >= 18
    }

# --- Load ---

def load_to_db(data):
    """Save to database."""
    try:
        # db.users.insert_many(data['users'])
        return Ok({
            'saved': len(data['users']),
            'errors': len(data['errors'])
        })
    except Exception as e:
        return Err(f"Database error: {e}")
```

## Traitement paresseux avec les iterateurs

Pour les grands jeux de donnees, utilisez des iterateurs paresseux pour eviter de tout charger en memoire :

```python
from fptk.iter.lazy import map_iter, filter_iter, chunk

def process_large_file(path: str):
    """Process file lazily, line by line."""
    with open(path) as f:
        # Nothing is loaded yet - all lazy
        lines = map_iter(str.strip, f)
        non_empty = filter_iter(bool, lines)
        parsed = map_iter(parse_line, non_empty)
        valid = filter_iter(lambda r: r.is_ok(), parsed)
        values = map_iter(lambda r: r.unwrap(), valid)

        # Only now do we consume the iterator
        for batch in chunk(values, 1000):
            save_batch(batch)
```

### Decoupage pour les operations par lots

```python
from fptk.iter.lazy import chunk

def batch_insert(items, batch_size=100):
    """Insert items in batches to avoid memory issues."""
    for batch in chunk(items, batch_size):
        db.insert_many(batch)
        print(f"Inserted {len(batch)} items")
```

### Regroupement

```python
from fptk.iter.lazy import group_by_key

def process_by_category(items):
    """Process items grouped by category."""
    # Items must be sorted by key first!
    sorted_items = sorted(items, key=lambda x: x['category'])

    for category, group in group_by_key(sorted_items, lambda x: x['category']):
        process_category(category, list(group))
```

## Pipelines de validation

Pour les donnees de formulaire ou les entrees API, accumulez toutes les erreurs de validation :

```python
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all

def validate_user_input(data: dict):
    """Validate with all errors collected."""
    return validate_all([
        # Required fields
        required('name'),
        required('email'),

        # Format validation
        email_format('email'),
        min_length('name', 2),

        # Business rules
        age_range('age', 13, 120),
    ], data)

# Reusable validators

def required(field):
    return lambda d: Ok(d) if d.get(field) else Err(f"{field} is required")

def email_format(field):
    return lambda d: Ok(d) if '@' in d.get(field, '') else Err(f"{field} must be valid email")

def min_length(field, n):
    return lambda d: Ok(d) if len(d.get(field, '')) >= n else Err(f"{field} must be at least {n} chars")

def age_range(field, min_age, max_age):
    def check(d):
        age = d.get(field)
        if age is None:
            return Ok(d)
        if not isinstance(age, int):
            return Err(f"{field} must be integer")
        if not (min_age <= age <= max_age):
            return Err(f"{field} must be between {min_age} and {max_age}")
        return Ok(d)
    return check
```

## Traitement par lots asynchrone

Pour le traitement limite par les E/S, utilisez async pour paralleliser :

```python
from fptk.async_tools import gather_results, gather_results_accumulate
import asyncio

async def process_urls(urls: list[str]):
    """Fetch multiple URLs concurrently."""
    tasks = [fetch_url(url) for url in urls]

    # Fail-fast: stop on first error
    result = await gather_results(tasks)

    # Or accumulate all errors
    # result = await gather_results_accumulate(tasks)

    return result

async def fetch_url(url: str):
    """Fetch single URL, returning Result."""
    try:
        async with aiohttp.get(url) as response:
            data = await response.json()
            return Ok(data)
    except Exception as e:
        return Err(f"Failed to fetch {url}: {e}")
```

## Transformations composables

Construisez des fonctions de transformation reutilisables :

```python
from fptk.core.func import compose, pipe

# Define atomic transformations
strip_strings = lambda d: {k: v.strip() if isinstance(v, str) else v for k, v in d.items()}
lowercase_email = lambda d: {**d, 'email': d['email'].lower()} if 'email' in d else d
add_timestamp = lambda d: {**d, 'processed_at': datetime.now()}

# Compose into pipelines
normalize_user = compose(add_timestamp, lowercase_email, strip_strings)

# Use in processing
def process_user(raw_data):
    return pipe(
        raw_data,
        normalize_user,
        validate_user_input,
        lambda r: r.bind(save_user)
    )
```

## Rapports d'erreurs

Collectez les erreurs sans arreter le pipeline :

```python
def process_with_report(items):
    """Process all items, collecting successes and failures."""
    results = [process_item(item) for item in items]

    successes = [r.unwrap() for r in results if r.is_ok()]
    failures = [(i, r.unwrap_err()) for i, r in enumerate(results) if r.is_err()]

    return {
        'processed': len(successes),
        'failed': len(failures),
        'errors': failures,
        'data': successes
    }
```

## Points cles a retenir

1. **Utilisez `pipe` pour les etapes de transformation** : Rend le flux de donnees explicite
2. **Utilisez les iterateurs paresseux pour les grandes donnees** : `map_iter`, `filter_iter`, `chunk`
3. **Utilisez `validate_all` pour la validation des entrees** : Collecte toutes les erreurs
4. **Utilisez `Result` partout** : Pas d'echecs silencieux
5. **Composez de petites transformations** : Construisez des pipelines complexes a partir de fonctions simples
6. **Separez Extract/Transform/Load** : Chaque etape est testable independamment
