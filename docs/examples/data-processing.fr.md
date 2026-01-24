# Traitement de données

Ce guide démontre l'utilisation de fptk pour les tâches courantes de traitement de données : pipelines ETL, validation, traitement par lots (batch processing) et transformations.

## Pourquoi adopter des patrons fonctionnels pour le traitement de données ?

Le code de traitement de données se heurte souvent à plusieurs obstacles :

-   **Des pipelines fragiles** : un seul enregistrement corrompu peut bloquer tout le processus.
-   **Des échecs silencieux** : des erreurs ignorées ou enregistrées dans des logs mais jamais traitées.
-   **Une surconsommation de mémoire** : le chargement inutile de jeux de données massifs en RAM.
-   **Une difficulté de débogage** : un manque de clarté sur l'endroit précis où s'opèrent les transformations.

Les patrons fonctionnels apportent des solutions concrètes en :

-   Rendant chaque transformation explicite et testable isolément.
-   Traitant les erreurs comme des valeurs circulant dans le pipeline.
-   Exploitant l'évaluation paresseuse (lazy evaluation) pour un traitement efficace.
-   Dissociant clairement les étapes de validation, de transformation et d'E/S.

## Pipeline ETL

Un pipeline classique Extract-Transform-Load (Extraction-Transformation-Chargement) s'accorde parfaitement avec `pipe` :

```python
from fptk.core.func import pipe
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all
from fptk.iter.lazy import map_iter
import csv

def process_users_csv(file_path: str):
    """Pipeline ETL : Extraction → Transformation → Chargement"""
    return pipe(
        file_path,
        read_csv,                    # Extraction
        lambda r: r.map(transform_rows),  # Transformation
        lambda r: r.bind(load_to_db)      # Chargement
    )

# --- Extraction ---

def read_csv(path: str):
    """Lit un fichier CSV et renvoie un Result."""
    try:
        with open(path) as f:
            return Ok(list(csv.DictReader(f)))
    except FileNotFoundError:
        return Err(f"Fichier introuvable : {path}")
    except Exception as e:
        return Err(f"Erreur de lecture : {e}")

# --- Transformation ---

def transform_rows(rows):
    """Transforme chaque ligne et collecte les résultats valides."""
    results = [transform_row(row) for row in rows]
    valid = [r.unwrap() for r in results if r.is_ok()]
    errors = [r.unwrap_err() for r in results if r.is_err()]
    return {'users': valid, 'errors': errors}

def transform_row(row: dict):
    """Valide et normalise une ligne unique."""
    return pipe(
        row,
        validate_row,
        lambda r: r.map(normalize),
        lambda r: r.map(enrich)
    )

def validate_row(row: dict):
    return validate_all([
        lambda r: Ok(r) if r.get('email') else Err("Email manquant"),
        lambda r: Ok(r) if '@' in r.get('email', '') else Err("Email invalide"),
        lambda r: Ok(r) if r.get('name') else Err("Nom manquant"),
    ], row)

def normalize(row: dict):
    """Normalise les formats de données."""
    return {
        'email': row['email'].lower().strip(),
        'name': row['name'].strip(),
        'age': int(row['age']) if row.get('age', '').isdigit() else None
    }

def enrich(row: dict):
    """Ajoute des champs calculés."""
    return {
        **row,
        'domain': row['email'].split('@')[1],
        'is_adult': row['age'] and row['age'] >= 18
    }

# --- Chargement ---

def load_to_db(data):
    """Sauvegarde les données en base de données."""
    try:
        # db.users.insert_many(data['users'])
        return Ok({
            'saved': len(data['users']),
            'errors': len(data['errors'])
        })
    except Exception as e:
        return Err(f"Erreur de base de données : {e}")
```

## Traitement paresseux avec les itérateurs

Pour les jeux de données volumineux, utilisez des itérateurs paresseux (lazy iterators) afin d'éviter de saturer la mémoire :

```python
from fptk.iter.lazy import map_iter, filter_iter, chunk

def process_large_file(path: str):
    """Traite un fichier de manière paresseuse, ligne par ligne."""
    with open(path) as f:
        # Rien n'est chargé à ce stade - tout est paresseux
        lines = map_iter(str.strip, f)
        non_empty = filter_iter(bool, lines)
        parsed = map_iter(parse_line, non_empty)
        valid = filter_iter(lambda r: r.is_ok(), parsed)
        values = map_iter(lambda r: r.unwrap(), valid)

        # La consommation effective de l'itérateur commence seulement ici
        for batch in chunk(values, 1000):
            save_batch(batch)
```

### Découpage (chunking) pour les opérations par lots

```python
from fptk.iter.lazy import chunk

def batch_insert(items, batch_size=100):
    """Insère des éléments par lots pour préserver la mémoire."""
    for batch in chunk(items, batch_size):
        db.insert_many(batch)
        print(f"{len(batch)} éléments insérés")
```

### Groupement

```python
from fptk.iter.lazy import group_by_key

def process_by_category(items):
    """Traite des éléments regroupés par catégorie."""
    # Attention : les éléments doivent être préalablement triés par clé !
    sorted_items = sorted(items, key=lambda x: x['category'])

    for category, group in group_by_key(sorted_items, lambda x: x['category']):
        process_category(category, list(group))
```

## Pipelines de validation

Pour valider des données de formulaires ou des entrées d'API, accumulez systématiquement toutes les erreurs :

```python
from fptk.adt.result import Ok, Err
from fptk.validate import validate_all

def validate_user_input(data: dict):
    """Valide les entrées et collecte toutes les erreurs détectées."""
    return validate_all([
        # Champs obligatoires
        required('name'),
        required('email'),

        # Validation de format
        email_format('email'),
        min_length('name', 2),

        # Règles métier
        age_range('age', 13, 120),
    ], data)

# Validateurs réutilisables

def required(field):
    return lambda d: Ok(d) if d.get(field) else Err(f"Le champ {field} est requis")

def email_format(field):
    return lambda d: Ok(d) if '@' in d.get(field, '') else Err(f"{field} doit être un email valide")

def min_length(field, n):
    return lambda d: Ok(d) if len(d.get(field, '')) >= n else Err(f"{field} doit comporter au moins {n} caractères")

def age_range(field, min_age, max_age):
    def check(d):
        age = d.get(field)
        if age is None:
            return Ok(d)
        if not isinstance(age, int):
            return Err(f"{field} doit être un nombre entier")
        if not (min_age <= age <= max_age):
            return Err(f"{field} doit être compris entre {min_age} et {max_age}")
        return Ok(d)
    return check
```

## Traitement par lots asynchrone

Pour accélérer les traitements limités par les E/S, utilisez l'asynchronisme :

```python
from fptk.async_tools import gather_results, gather_results_accumulate
import asyncio

async def process_urls(urls: list[str]):
    """Récupère plusieurs URL de manière concurrente."""
    tasks = [fetch_url(url) for url in urls]

    # Mode fail-fast : s'arrête à la première erreur
    result = await gather_results(tasks)

    # Ou mode accumulation : collecte toutes les erreurs
    # result = await gather_results_accumulate(tasks)

    return result

async def fetch_url(url: str):
    """Récupère une URL unique et renvoie un Result."""
    try:
        async with aiohttp.get(url) as response:
            data = await response.json()
            return Ok(data)
    except Exception as e:
        return Err(f"Échec de récupération pour {url} : {e}")
```

## Transformations composables

Bâtissez votre logique à partir de fonctions de transformation réutilisables :

```python
from fptk.core.func import compose, pipe

# Définition de transformations atomiques
strip_strings = lambda d: {k: v.strip() if isinstance(v, str) else v for k, v in d.items()}
lowercase_email = lambda d: {**d, 'email': d['email'].lower()} if 'email' in d else d
add_timestamp = lambda d: {**d, 'processed_at': datetime.now()}

# Assemblage dans un pipeline
normalize_user = compose(add_timestamp, lowercase_email, strip_strings)

# Utilisation dans un processus global
def process_user(raw_data):
    return pipe(
        raw_data,
        normalize_user,
        validate_user_input,
        lambda r: r.bind(save_user)
    )
```

## Rapports d'erreurs

Collectez les erreurs rencontrées sans interrompre le pipeline global :

```python
def process_with_report(items):
    """Traite tous les éléments et produit un rapport des succès et échecs."""
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

## Points clés à retenir

1.  **Utilisez `pipe` pour vos étapes de transformation** : cela rend le flux de données parfaitement explicite.
2.  **Adoptez les itérateurs paresseux pour les volumes massifs** : avec `map_iter`, `filter_iter` et `chunk`.
3.  **Privilégiez `validate_all` pour vos entrées** : afin de collecter l'ensemble des erreurs en une passe.
4.  **Utilisez `Result` systématiquement** : pour en finir avec les échecs silencieux.
5.  **Composez de petites transformations** : bâtissez des pipelines complexes à partir de briques élémentaires simples.
6.  **Séparez Extraction, Transformation et Chargement (ETL)** : chaque étape devient ainsi testable individuellement.