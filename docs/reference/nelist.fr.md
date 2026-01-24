# NonEmptyList

`fptk.adt.nelist` fournit `NonEmptyList`, une liste qui est garantie d'avoir au moins un élément par construction.

## Concept : Collections non vides

De nombreuses opérations sur les listes échouent ou produisent des résultats sans signification lorsque la liste est vide :

```python
max([])    # ValueError: max() arg is an empty sequence
min([])    # ValueError
head = xs[0]  # IndexError if empty
sum(xs) / len(xs)  # ZeroDivisionError if empty
```

Une `NonEmptyList` fait de la non-vacuité une garantie au niveau du type. Si vous avez une `NonEmptyList`, vous savez qu'elle a au moins un élément — aucune vérification à l'exécution n'est nécessaire.

### Le problème : Les vérifications de liste vide

```python
def average(xs: list[float]) -> float:
    if not xs:
        raise ValueError("Cannot compute average of empty list")
    return sum(xs) / len(xs)

def first(xs: list[T]) -> T:
    if not xs:
        raise ValueError("List is empty")
    return xs[0]

# Every function needs to validate, every caller needs to handle
```

### La solution NonEmptyList

```python
from fptk.adt.nelist import NonEmptyList

def average(xs: NonEmptyList[float]) -> float:
    # No check needed—xs is guaranteed non-empty
    return sum(xs) / len(list(xs))

def first(xs: NonEmptyList[T]) -> T:
    return xs.head  # Always safe

# Construct safely
result = NonEmptyList.from_iter(data)  # Option[NonEmptyList]
if result:
    avg = average(result)
else:
    # Handle empty case once, at the boundary
```

## API

### Types

| Type | Description |
|------|-------------|
| `NonEmptyList[E]` | Liste avec au moins un élément |

### Constructeur

```python
from fptk.adt.nelist import NonEmptyList

# Direct construction (always non-empty)
nel = NonEmptyList(1)                    # [1]
nel = NonEmptyList(1, (2, 3, 4))         # [1, 2, 3, 4]

# From iterable (might be empty)
result = NonEmptyList.from_iter([1, 2])  # NonEmptyList or None
result = NonEmptyList.from_iter([])      # None
```

### Propriétés

| Propriété | Type | Description |
|-----------|------|-------------|
| `head` | `E` | Premier élément (garanti d'exister) |
| `tail` | `tuple[E, ...]` | Éléments restants (peut être vide) |

### Méthodes

| Méthode | Signature | Description |
|---------|-----------|-------------|
| `append(e)` | `(E) -> NonEmptyList[E]` | Ajoute un élément à la fin |
| `to_list()` | `() -> list[E]` | Convertit en liste standard |
| `from_iter(it)` | `staticmethod (Iterable[E]) -> NonEmptyList[E] | None` | Crée à partir d'un itérable |
| `__iter__()` | `() -> Iterator[E]` | Itère sur tous les éléments |

## Fonctionnement

### Structure de données

NonEmptyList stocke un `head` requis et un `tail` optionnel :

```python
@dataclass(frozen=True, slots=True)
class NonEmptyList[E]:
    head: E                      # First element (required)
    tail: tuple[E, ...] = ()     # Remaining elements (tuple for immutability)
```

Le champ `head` est requis, garantissant au moins un élément. Le `tail` est un tuple (immuable) qui peut être vide.

### Construction sûre

```python
@staticmethod
def from_iter(it: Iterable[E]) -> NonEmptyList[E] | None:
    iterator = iter(it)
    try:
        h = next(iterator)
    except StopIteration:
        return None  # Empty iterable
    return NonEmptyList(h, tuple(iterator))
```

`from_iter` retourne `None` pour les itérables vides — la seule façon d'obtenir une `NonEmptyList` est avec au moins un élément.

### Itération

```python
def __iter__(self):
    yield self.head
    yield from self.tail
```

Itère dans l'ordre : d'abord le head, puis les éléments du tail.

### Ajout

```python
def append(self, e: E) -> NonEmptyList[E]:
    return NonEmptyList(self.head, self.tail + (e,))
```

Retourne une nouvelle `NonEmptyList` avec l'élément ajouté à la fin (immuable).

## Exemples

### Accès sûr au head

```python
from fptk.adt.nelist import NonEmptyList

# Regular list: might fail
def unsafe_head(xs: list[int]) -> int:
    return xs[0]  # IndexError if empty!

# NonEmptyList: always safe
def safe_head(xs: NonEmptyList[int]) -> int:
    return xs.head  # Guaranteed to exist

# Construct at boundaries
data = get_data()  # list[int]
nel = NonEmptyList.from_iter(data)
if nel:
    print(safe_head(nel))
else:
    print("No data available")
```

### Calcul de statistiques

```python
from fptk.adt.nelist import NonEmptyList

def stats(xs: NonEmptyList[float]) -> dict:
    """Compute statistics. No empty-list checks needed."""
    values = list(xs)
    return {
        "count": len(values),
        "sum": sum(values),
        "mean": sum(values) / len(values),
        "min": min(values),  # Safe
        "max": max(values),  # Safe
        "first": xs.head,    # Safe
    }

# Safe construction
data = NonEmptyList.from_iter(measurements)
if data:
    result = stats(data)
```

### Construction de résultats

```python
from fptk.adt.nelist import NonEmptyList

def collect_errors(validations: list[Result]) -> NonEmptyList[str] | None:
    """Collect error messages, if any."""
    errors = [r.error for r in validations if r.is_err()]
    return NonEmptyList.from_iter(errors)

# Later
errors = collect_errors(results)
if errors:
    # We know there's at least one error
    print(f"First error: {errors.head}")
    print(f"Total errors: {len(list(errors))}")
```

### Avec la validation

```python
from fptk.validate import validate_all
from fptk.adt.nelist import NonEmptyList

# validate_all returns Result[T, NonEmptyList[E]]
# If validation fails, you're guaranteed at least one error

result = validate_all([check1, check2, check3], data)
result.match(
    ok=lambda d: process(d),
    err=lambda errors: print(f"Validation failed: {errors.head}")
    # errors is NonEmptyList[str], so .head is safe
)
```

### Chaînage d'opérations

```python
from fptk.adt.nelist import NonEmptyList

# Build up a list
nel = NonEmptyList(1)
nel = nel.append(2).append(3).append(4)

print(nel.head)       # 1
print(nel.tail)       # (2, 3, 4)
print(list(nel))      # [1, 2, 3, 4]
```

### Conversion de collections

```python
from fptk.adt.nelist import NonEmptyList

# From various iterables
from_list = NonEmptyList.from_iter([1, 2, 3])
from_set = NonEmptyList.from_iter({1, 2, 3})
from_gen = NonEmptyList.from_iter(x for x in range(5))

# To list
nel = NonEmptyList(1, (2, 3))
regular_list = nel.to_list()  # [1, 2, 3]
```

## Quand utiliser NonEmptyList

**Utilisez NonEmptyList lorsque :**

- Votre domaine nécessite au moins un élément
- Vous voulez éliminer les vérifications de liste vide dans le code en aval
- Vous accumulez des erreurs (validation)
- Vous calculez des agrégats qui nécessitent une entrée non vide (moyenne, max, etc.)

**N'utilisez pas NonEmptyList lorsque :**

- Les collections vides sont valides dans votre domaine
- Vous avez besoin d'accès aléatoire fréquent (utilisez list)
- Vous avez besoin d'ajouts efficaces (la concaténation de tuple est O(n))

## NonEmptyList vs Option[list]

| Type | Signification |
|------|---------------|
| `list[T]` | Zéro ou plusieurs éléments |
| `Option[list[T]]` | Peut-être une liste (mais la liste pourrait toujours être vide !) |
| `NonEmptyList[T]` | Un ou plusieurs éléments (garanti) |
| `Option[NonEmptyList[T]]` | Peut-être une liste non vide |

`NonEmptyList` est le bon choix lorsque vous devez garantir la non-vacuité au niveau du type.

## Voir aussi

- [`validate_all`](validate.md) — Utilise NonEmptyList pour l'accumulation d'erreurs
- [`Option`](option.md) — Pour les valeurs qui peuvent être absentes
- [`Result`](result.md) — Pour les calculs qui peuvent échouer
