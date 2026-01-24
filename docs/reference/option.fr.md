# Option

`fptk.adt.option` fournit le type `Option` pour gérer les valeurs qui pourraient être absentes. Au lieu d'utiliser `None` et de le vérifier partout, `Option` rend l'absence explicite et composable.

## Concept : La Monade Maybe/Option

En programmation fonctionnelle, `Option` (aussi appelé `Maybe` en Haskell) représente une valeur qui pourrait ne pas exister. Elle a deux cas :

- **Some(value)** : La valeur est présente
- **Nothing** : La valeur est absente

Cela est important car :

- **Pas d'exceptions de pointeur nul** : Vous ne pouvez pas accidentellement appeler des méthodes sur `None`
- **Absence explicite** : La signature de type vous indique qu'une valeur pourrait être manquante
- **Transformations composables** : Enchaîner des opérations qui gèrent gracieusement les valeurs manquantes

### Le problème avec `None`

```python
user = get_user(id)
name = user.get("profile").get("name").upper()  # AttributeError if any is None!

# Defensive coding everywhere
if user and user.get("profile") and user.get("profile").get("name"):
    name = user["profile"]["name"].upper()
else:
    name = "Anonymous"
```

### La solution Option

```python
from fptk.adt.option import from_nullable, Some, NOTHING

name = (
    from_nullable(get_user(id))
    .bind(lambda u: from_nullable(u.get("profile")))
    .bind(lambda p: from_nullable(p.get("name")))
    .map(str.upper)
    .unwrap_or("Anonymous")
)
```

Chaque `.bind()` court-circuite vers `NOTHING` si l'étape précédente était absente. Pas d'exceptions, pas de conditionnels imbriqués.

## API

### Types

| Type | Description |
|------|-------------|
| `Option[T]` | Type de base représentant une valeur optionnelle |
| `Some[T]` | Variante contenant une valeur présente |
| `Nothing` | Variante représentant l'absence (classe singleton) |
| `NOTHING` | L'instance singleton de `Nothing` |

### Constructeurs

```python
from fptk.adt.option import Some, NOTHING, from_nullable

# Directly construct
present = Some(42)
absent = NOTHING

# From nullable value
from_nullable(some_value)  # Some(x) if x is not None, else NOTHING
```

### Méthodes

| Méthode | Signature | Description |
|---------|-----------|-------------|
| `is_some()` | `() -> bool` | Retourne `True` si `Some` |
| `is_none()` | `() -> bool` | Retourne `True` si `Nothing` |
| `map(f)` | `(T -> U) -> Option[U]` | Transformer la valeur si présente |
| `bind(f)` | `(T -> Option[U]) -> Option[U]` | Enchaîner des fonctions retournant Option |
| `and_then(f)` | `(T -> Option[U]) -> Option[U]` | Alias pour `bind` (nommage Rust) |
| `zip(other)` | `(Option[U]) -> Option[tuple[T, U]]` | Combiner deux Options en tuple |
| `zip_with(other, f)` | `(Option[U], (T, U) -> R) -> Option[R]` | Combiner deux Options avec une fonction |
| `unwrap_or(default)` | `(U) -> T | U` | Obtenir la valeur ou une valeur par défaut |
| `or_else(alt)` | `(Option[T] | () -> Option[T]) -> Option[T]` | Alternative si absent |
| `to_result(err)` | `(E) -> Result[T, E]` | Convertir en Result |
| `match(some, none)` | `(T -> U, () -> U) -> U` | Pattern matching |
| `unwrap()` | `() -> T` | Obtenir la valeur ou lever ValueError |
| `expect(msg)` | `(str) -> T` | Obtenir la valeur ou lever avec un message |

### Méthodes asynchrones

| Méthode | Signature | Description |
|---------|-----------|-------------|
| `map_async(f)` | `async (T -> U) -> Option[U]` | Transformation asynchrone |
| `bind_async(f)` | `async (T -> Option[U]) -> Option[U]` | Enchaînement asynchrone |

### or_else : Eager vs Lazy

`or_else` accepte à la fois une valeur `Option` directe et un callable retournant `Option` :

```python
from fptk.adt.option import Some, NOTHING

# Eager: value is always evaluated
result = NOTHING.or_else(Some(42))  # Some(42)

# Lazy: callable only invoked if needed
result = NOTHING.or_else(lambda: Some(expensive_computation()))
```

**Quand utiliser lequel :**

| Patron | Syntaxe | Utiliser quand |
|--------|---------|----------------|
| Eager | `.or_else(Some(x))` | La valeur par défaut est peu coûteuse/déjà calculée |
| Lazy | `.or_else(lambda: ...)` | La valeur par défaut est coûteuse ou a des effets de bord |

```python
# Fallback chain with lazy evaluation
config_value = (
    from_nullable(os.getenv("MY_VAR"))
    .or_else(lambda: from_nullable(config_file.get("my_var")))  # Only if env missing
    .or_else(Some("default"))  # Cheap, can be eager
)
```

## Fonctionnement

### Structure de données

`Option` est implémenté comme un type scellé avec deux variantes :

```python
class Option[T]:
    """Base class - not instantiated directly."""
    pass

@dataclass(frozen=True, slots=True)
class Some[T](Option[T]):
    value: T

@dataclass(frozen=True, slots=True)
class Nothing(Option[None]):
    pass

NOTHING = Nothing()  # Singleton
```

Le `@dataclass(frozen=True, slots=True)` rend les instances immuables et économes en mémoire.

### Le Functor : `map`

`map` applique une fonction à la valeur à l'intérieur de `Some`, ou ne fait rien pour `Nothing` :

```python
def map(self, f):
    if isinstance(self, Some):
        return Some(f(self.value))
    return NOTHING
```

C'est l'opération **Functor** : élever une fonction `A -> B` pour qu'elle fonctionne sur `Option[A] -> Option[B]`.

### La Monade : `bind`

`bind` (aussi appelé `flatMap` ou `>>=`) enchaîne des opérations qui retournent elles-mêmes des `Option` :

```python
def bind(self, f):
    if isinstance(self, Some):
        return f(self.value)  # f returns Option[U]
    return NOTHING
```

C'est l'opération **Monade**. Elle évite les `Option[Option[T]]` imbriqués en "aplatissant" le résultat.

### Pourquoi `bind` vs `map` ?

- Utilisez `map` quand votre fonction retourne une valeur simple : `lambda x: x + 1`
- Utilisez `bind` quand votre fonction retourne un `Option` : `lambda x: from_nullable(lookup(x))`

```python
# map: str -> str (plain value)
Some("hello").map(str.upper)  # Some("HELLO")

# bind: str -> Option[int] (returns Option)
Some("42").bind(lambda s: from_nullable(safe_parse(s)))  # Some(42) or NOTHING
```

## Exemples

### Accès sûr aux dictionnaires

```python
from fptk.adt.option import from_nullable

config = {"database": {"host": "localhost", "port": 5432}}

# Chain lookups safely
port = (
    from_nullable(config.get("database"))
    .bind(lambda db: from_nullable(db.get("port")))
    .map(str)
    .unwrap_or("5432")
)
```

### Analyse de l'entrée utilisateur

```python
def parse_int(s: str) -> Option[int]:
    try:
        return Some(int(s))
    except ValueError:
        return NOTHING

def parse_positive(s: str) -> Option[int]:
    return parse_int(s).bind(
        lambda n: Some(n) if n > 0 else NOTHING
    )

parse_positive("42")   # Some(42)
parse_positive("-1")   # NOTHING
parse_positive("abc")  # NOTHING
```

### Première valeur disponible

```python
from fptk.adt.option import from_nullable, NOTHING

def get_config_value(key: str) -> Option[str]:
    """Try environment, then file, then default."""
    return (
        from_nullable(os.getenv(key))
        .or_else(lambda: from_nullable(config_file.get(key)))
        .or_else(lambda: from_nullable(defaults.get(key)))
    )
```

### Pattern Matching

```python
def describe(opt: Option[int]) -> str:
    return opt.match(
        some=lambda n: f"Got number: {n}",
        none=lambda: "No value"
    )

describe(Some(42))  # "Got number: 42"
describe(NOTHING)   # "No value"
```

### Conversion en Result

```python
from fptk.adt.option import from_nullable

def find_user(id: int) -> Option[User]:
    return from_nullable(db.get(id))

# Convert to Result for error handling
result = find_user(42).to_result(f"User {id} not found")
# Ok(user) or Err("User 42 not found")
```

### Itération

```python
from fptk.adt.option import Some, NOTHING

# Option implements __iter__ for zero-or-one elements
for value in Some(42):
    print(value)  # Prints 42

for value in NOTHING:
    print(value)  # Never executes
```

## Quand utiliser Option

**Utilisez Option quand :**

- Une valeur peut légitimement être absente (pas une condition d'erreur)
- Vous voulez enchaîner des transformations qui peuvent échouer
- Vous analysez ou recherchez des valeurs qui pourraient ne pas exister
- Vous voulez éviter les vérifications de `None` dispersées dans votre code

**N'utilisez pas Option quand :**

- L'absence représente une erreur qui devrait être signalée → utilisez `Result`
- Vous avez besoin de savoir pourquoi une valeur est manquante → utilisez `Result` avec des informations d'erreur
- La performance est critique dans des boucles serrées → Option a un certain overhead

## Voir aussi

- [`Result`](result.md) — Quand l'absence est une erreur avec des informations
- [`from_nullable`](#constructeurs) — Pont du `None` de Python vers `Option`
- [`traverse_option`](traverse.md) — Collecter plusieurs Options en une seule
