# Traverse

`fptk.adt.traverse` fournit des operations pour travailler avec des collections de valeurs `Option` ou `Result`, en les "retournant" tout en gerant les echecs.

## Concept : Traverse et Sequence

Lorsque vous avez une liste de calculs susceptibles d'echouer, vous souhaitez souvent :

1. **Sequence** : Transformer `list[Option[T]]` en `Option[list[T]]`
2. **Traverse** : Appliquer une fonction sur une liste, puis sequencer les resultats

Ces operations "inversent" la structure des conteneurs :

```
list[Option[T]]  →  Option[list[T]]
list[Result[T, E]]  →  Result[list[T], E]
```

Cela est important car :

- **Semantique fail-fast** : Arret au premier `Nothing` ou `Err`
- **Resultats tout-ou-rien** : Soit tout reussit, soit vous obtenez le premier echec
- **Pipelines composables** : Travaillez avec des collections d'operations faillibles

### Le probleme : Boucles et verifications imbriquees

```python
def fetch_all_users(ids: list[int]) -> list[User]:
    results = []
    for id in ids:
        user = fetch_user(id)  # Returns Option[User]
        if user.is_none():
            return []  # What if one fails?
        results.append(user.unwrap())
    return results

# Messy, error-prone, hard to read
```

### La solution Traverse

```python
from fptk.adt.traverse import traverse_option

def fetch_all_users(ids: list[int]) -> Option[list[User]]:
    return traverse_option(ids, fetch_user)
    # Returns Some([users...]) if all succeed
    # Returns NOTHING if any fails
```

Une seule ligne, une semantique claire, composable avec d'autres operations Option.

## API

### Fonctions Sequence

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `sequence_option(xs)` | `Iterable[Option[A]] -> Option[list[A]]` | Collecte les valeurs Some |
| `sequence_result(xs)` | `Iterable[Result[A, E]] -> Result[list[A], E]` | Collecte les valeurs Ok |

### Fonctions Traverse

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `traverse_option(xs, f)` | `(Iterable[A], A -> Option[B]) -> Option[list[B]]` | Applique et collecte |
| `traverse_result(xs, f)` | `(Iterable[A], A -> Result[B, E]) -> Result[list[B], E]` | Applique et collecte |

### Variantes Async

| Fonction | Execution | Description |
|----------|-----------|-------------|
| `traverse_option_async(xs, f)` | Sequentielle | Applique et collecte async, un a la fois |
| `traverse_result_async(xs, f)` | Sequentielle | Applique et collecte async, un a la fois |
| `traverse_option_parallel(xs, f)` | Parallele | Applique et collecte async, tous en meme temps |
| `traverse_result_parallel(xs, f)` | Parallele | Applique et collecte async, tous en meme temps |

**Quand utiliser laquelle :**

| Variante | A utiliser quand |
|---------|----------|
| `*_async` (sequentielle) | APIs avec limitation de debit, operations dependantes, effets de bord ordonnes |
| `*_parallel` | Operations independantes, debit maximal |

## Fonctionnement

### Sequence

Sequence itere sur la collection en accumulant les valeurs. Au premier echec, elle court-circuite :

```python
def sequence_option(xs):
    out = []
    for x in xs:
        if isinstance(x, Some):
            out.append(x.value)
        else:
            return NOTHING  # Short-circuit
    return Some(out)
```

### Traverse

Traverse est sequence compose avec map - applique la fonction, puis sequence :

```python
def traverse_option(xs, f):
    out = []
    for x in xs:
        result = f(x)
        if isinstance(result, Some):
            out.append(result.value)
        else:
            return NOTHING  # Short-circuit
    return Some(out)
```

Conceptuellement : `traverse(xs, f) = sequence(map(f, xs))`, mais implemente de maniere plus efficace.

### Comportement Fail-Fast

Toutes les operations sont **fail-fast** : elles arretent le traitement des qu'elles rencontrent un echec. Cela signifie :

- Efficace : Pas de calcul gaspille apres un echec
- Premiere erreur uniquement : Vous obtenez le premier `Err`, pas tous
- Pour accumuler toutes les erreurs, utilisez [`validate_all`](validate.md)

## Exemples

### Analyser une liste d'entrees

```python
from fptk.adt.traverse import traverse_option
from fptk.adt.option import Some, NOTHING

def parse_int(s: str) -> Option[int]:
    try:
        return Some(int(s))
    except ValueError:
        return NOTHING

# Parse all or none
inputs = ["1", "2", "3"]
result = traverse_option(inputs, parse_int)
# Some([1, 2, 3])

inputs = ["1", "oops", "3"]
result = traverse_option(inputs, parse_int)
# NOTHING (stops at "oops")
```

### Recuperer plusieurs ressources

```python
from fptk.adt.traverse import traverse_result
from fptk.adt.result import Ok, Err

def fetch_user(id: int) -> Result[User, str]:
    user = db.get(id)
    if user:
        return Ok(user)
    return Err(f"User {id} not found")

# Fetch all users
ids = [1, 2, 3]
result = traverse_result(ids, fetch_user)
# Ok([User(1), User(2), User(3)]) or Err("User X not found")
```

### Valider une configuration

```python
from fptk.adt.traverse import sequence_result

def validate_field(name: str, value: str) -> Result[str, str]:
    if not value:
        return Err(f"{name} is required")
    return Ok(value)

# Validate multiple fields
validations = [
    validate_field("name", config.get("name", "")),
    validate_field("email", config.get("email", "")),
    validate_field("password", config.get("password", "")),
]

result = sequence_result(validations)
# Ok(["Alice", "alice@example.com", "secret"]) or Err("email is required")
```

### Combiner avec les methodes Option

```python
from fptk.adt.traverse import traverse_option
from fptk.adt.option import from_nullable

def get_user_names(data: list[dict]) -> Option[list[str]]:
    return traverse_option(
        data,
        lambda d: from_nullable(d.get("name"))
    )

users = [{"name": "Alice"}, {"name": "Bob"}]
get_user_names(users)  # Some(["Alice", "Bob"])

users = [{"name": "Alice"}, {"age": 30}]
get_user_names(users)  # NOTHING (second has no name)
```

### Traversal async

```python
from fptk.adt.traverse import traverse_result_async, traverse_result_parallel

async def fetch_user_async(id: int) -> Result[User, str]:
    try:
        user = await db.async_get(id)
        return Ok(user) if user else Err(f"User {id} not found")
    except Exception as e:
        return Err(str(e))

# Sequential - respects rate limits, executes one at a time
async def fetch_users_sequential(ids: list[int]) -> Result[list[User], str]:
    return await traverse_result_async(ids, fetch_user_async)

# Parallel - maximum throughput, all requests at once
async def fetch_users_parallel(ids: list[int]) -> Result[list[User], str]:
    return await traverse_result_parallel(ids, fetch_user_async)

# 100 users, 100ms each:
# - Sequential: ~10 seconds
# - Parallel: ~100ms
```

### Chainer les traversals

```python
from fptk.adt.traverse import traverse_result
from fptk.core.func import pipe

def process_batch(ids: list[int]) -> Result[list[ProcessedItem], str]:
    return pipe(
        ids,
        lambda xs: traverse_result(xs, fetch_item),       # Fetch all
        lambda r: r.bind(lambda items:
            traverse_result(items, validate_item)          # Validate all
        ),
        lambda r: r.bind(lambda items:
            traverse_result(items, transform_item)         # Transform all
        ),
    )
```

### De Sequence a Traverse

```python
from fptk.adt.traverse import sequence_option, traverse_option

# These are equivalent:
# 1. Manual map + sequence
options = [parse_int(s) for s in strings]  # list[Option[int]]
result = sequence_option(options)           # Option[list[int]]

# 2. Traverse (more efficient, no intermediate list)
result = traverse_option(strings, parse_int)
```

## Traverse vs validate_all

| Operation | Comportement | A utiliser quand |
|-----------|----------|----------|
| `traverse_result` | Fail-fast, retourne la premiere erreur | Vous n'avez besoin que d'une erreur |
| `validate_all` | Accumule toutes les erreurs | Vous voulez afficher tous les problemes |

```python
# Fail-fast: stops at first error
traverse_result(["bad1", "bad2"], parse_positive)
# Err("'bad1' is not positive")

# Accumulate: collects all errors
validate_all([check_positive, check_even], -3)
# Err(NonEmptyList("not positive", "not even"))
```

## Quand utiliser Traverse

**Utilisez traverse quand :**

- Vous avez une collection de valeurs a traiter de maniere uniforme
- Chaque etape de traitement peut echouer
- Vous voulez une semantique tout-ou-rien
- Vous voulez la premiere erreur, pas toutes les erreurs

**Utilisez validate_all quand :**

- Vous voulez collecter toutes les erreurs
- Vous validez une saisie utilisateur
- Afficher tous les problemes en une fois ameliore l'experience utilisateur

**Utilisez `*_parallel` quand :**

- Vous avez besoin d'une execution async parallele
- Chaque tache est independante
- Vous voulez un debit maximal

## Voir aussi

- [`Option`](option.md) - Le type optionnel sous-jacent
- [`Result`](result.md) - Le type resultat sous-jacent
- [`validate_all`](validate.md) - Pour accumuler toutes les erreurs
- [`gather_results`](async.md) - Pour les operations async paralleles
