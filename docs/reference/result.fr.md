# Result

`fptk.adt.result` fournit le type `Result` pour gérer les opérations qui peuvent réussir ou échouer. Au lieu de lever des exceptions, `Result` rend les erreurs explicites et composables.

## Concept : La Monade Either/Result

En programmation fonctionnelle, `Result` (aussi appelé `Either` en Haskell) représente un calcul qui peut réussir avec une valeur ou échouer avec une erreur. Elle a deux cas :

- **Ok(value)** : Le calcul a réussi
- **Err(error)** : Le calcul a échoué

Cela est important car :

- **Gestion explicite des erreurs** : La signature de type vous indique que quelque chose peut échouer
- **Chemins d'erreur composables** : Enchaîner des opérations et gérer toutes les erreurs à la fin
- **Pas de flux de contrôle caché** : Pas d'exceptions traversant votre pile d'appels
- **Programmation orientée railway** : Les chemins de succès et d'erreur s'exécutent sur des voies parallèles

### Le problème avec les exceptions

```python
def process(data):
    parsed = json.loads(data)        # Might raise JSONDecodeError
    validated = validate(parsed)      # Might raise ValidationError
    result = transform(validated)     # Might raise TransformError
    return result

# Caller has no idea what might be thrown
try:
    result = process(data)
except json.JSONDecodeError as e:
    # Handle parse error
except ValidationError as e:
    # Handle validation error
except TransformError as e:
    # Handle transform error
```

### La solution Result

```python
from fptk.adt.result import Ok, Err
from fptk.core.func import pipe

def process(data: str) -> Result[Output, str]:
    return pipe(
        data,
        parse_json,        # Returns Result[dict, str]
        lambda r: r.bind(validate),     # Result[Validated, str]
        lambda r: r.bind(transform),    # Result[Output, str]
    )

# Caller sees the Result type and handles it
result = process(data)
result.match(
    ok=lambda output: save(output),
    err=lambda error: log_error(error)
)
```

Le type d'erreur est visible. L'erreur de chaque étape fait partie de la chaîne. Un seul point de gestion à la fin.

## API

### Types

| Type | Description |
|------|-------------|
| `Result[T, E]` | Type de base : succès `T` ou erreur `E` |
| `Ok[T, E]` | Variante de succès contenant une valeur de type `T` |
| `Err[T, E]` | Variante d'échec contenant une erreur de type `E` |

### Constructeurs

```python
from fptk.adt.result import Ok, Err

success = Ok(42)
failure = Err("something went wrong")
```

### Méthodes

| Méthode | Signature | Description |
|---------|-----------|-------------|
| `is_ok()` | `() -> bool` | Retourne `True` si `Ok` |
| `is_err()` | `() -> bool` | Retourne `True` si `Err` |
| `map(f)` | `(T -> U) -> Result[U, E]` | Transformer la valeur de succès |
| `bind(f)` | `(T -> Result[U, E]) -> Result[U, E]` | Enchaîner des fonctions retournant Result |
| `and_then(f)` | `(T -> Result[U, E]) -> Result[U, E]` | Alias pour `bind` (nommage Rust) |
| `zip(other)` | `(Result[U, E]) -> Result[tuple[T, U], E]` | Combiner deux Results en tuple |
| `zip_with(other, f)` | `(Result[U, E], (T, U) -> R) -> Result[R, E]` | Combiner deux Results avec une fonction |
| `map_err(f)` | `(E -> F) -> Result[T, F]` | Transformer la valeur d'erreur |
| `unwrap_or(default)` | `(U) -> T | U` | Obtenir la valeur ou une valeur par défaut |
| `unwrap_or_else(f)` | `(E -> U) -> T | U` | Obtenir la valeur ou calculer depuis l'erreur |
| `match(ok, err)` | `(T -> U, E -> U) -> U` | Pattern matching sur les deux cas |
| `unwrap()` | `() -> T` | Obtenir la valeur ou lever ValueError |
| `expect(msg)` | `(str) -> T` | Obtenir la valeur ou lever avec un message |

### Méthodes asynchrones

| Méthode | Signature | Description |
|---------|-----------|-------------|
| `map_async(f)` | `async (T -> U) -> Result[U, E]` | Transformation asynchrone du succès |
| `bind_async(f)` | `async (T -> Result[U, E]) -> Result[U, E]` | Enchaînement asynchrone |

## Fonctionnement

### Structure de données

`Result` est implémenté comme un type scellé avec deux variantes :

```python
class Result[T, E]:
    """Base class - not instantiated directly."""
    pass

@dataclass(frozen=True, slots=True)
class Ok[T, E](Result[T, E]):
    value: T

@dataclass(frozen=True, slots=True)
class Err[T, E](Result[T, E]):
    error: E
```

### Le Functor : `map`

`map` transforme la valeur de succès, laissant les erreurs inchangées :

```python
def map(self, f):
    if isinstance(self, Ok):
        return Ok(f(self.value))
    return self  # Err passes through
```

### La Monade : `bind`

`bind` enchaîne des opérations qui retournent des `Result` :

```python
def bind(self, f):
    if isinstance(self, Ok):
        return f(self.value)  # f returns Result[U, E]
    return self  # Err passes through
```

### Le Bifuncteur : `map_err`

Contrairement à `Option`, `Result` peut aussi transformer son erreur :

```python
def map_err(self, f):
    if isinstance(self, Err):
        return Err(f(self.error))
    return self  # Ok passes through
```

### Programmation orientée railway

Pensez à `Result` comme une voie ferrée avec deux rails :

```
     Ok path  ─────┬─────┬─────┬─────> Success
                   │     │     │
     Err path ─────┴─────┴─────┴─────> Failure
               parse  validate transform
```

Chaque fonction continue soit sur le rail Ok soit bascule sur le rail Err. Une fois sur le rail Err, vous y restez (les erreurs se propagent automatiquement).

## Exemples

### Encapsuler les exceptions

```python
from fptk.core.func import try_catch
from fptk.adt.result import Ok, Err

# Automatic wrapping
safe_parse = try_catch(json.loads)
safe_parse('{"a": 1}')  # Ok({"a": 1})
safe_parse('invalid')    # Err(JSONDecodeError(...))

# Manual wrapping
def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"'{s}' is not a valid integer")
```

### Enchaîner des opérations

```python
def validate_age(data: dict) -> Result[dict, str]:
    age = data.get("age")
    if age is None:
        return Err("age is required")
    if not isinstance(age, int):
        return Err("age must be an integer")
    if age < 0 or age > 150:
        return Err("age must be between 0 and 150")
    return Ok(data)

def validate_email(data: dict) -> Result[dict, str]:
    email = data.get("email")
    if not email or "@" not in email:
        return Err("valid email is required")
    return Ok(data)

def process_user(raw: str) -> Result[User, str]:
    return (
        try_catch(json.loads)(raw)
        .map_err(lambda e: f"Invalid JSON: {e}")
        .bind(validate_age)
        .bind(validate_email)
        .map(lambda d: User(**d))
    )
```

### Transformation des erreurs

```python
# Convert detailed errors to user-friendly messages
def user_friendly_error(e: Exception) -> str:
    if isinstance(e, json.JSONDecodeError):
        return "The data format is invalid"
    if isinstance(e, ValidationError):
        return f"Please check your input: {e.field}"
    return "An unexpected error occurred"

result = (
    process_data(raw)
    .map_err(user_friendly_error)
)
```

### Pattern Matching

```python
def respond(result: Result[User, str]) -> Response:
    return result.match(
        ok=lambda user: Response(200, {"user": user.to_dict()}),
        err=lambda error: Response(400, {"error": error})
    )
```

### Valeurs de repli

```python
# Simple default
value = parse_int(input).unwrap_or(0)

# Computed default (only runs on error)
value = parse_int(input).unwrap_or_else(
    lambda err: log_and_return_default(err)
)
```

### Combinaison avec Option

```python
from fptk.adt.option import from_nullable

def get_user_email(user_id: int) -> Result[str, str]:
    return (
        from_nullable(db.get(user_id))
        .to_result(f"User {user_id} not found")
        .bind(lambda user:
            from_nullable(user.get("email"))
            .to_result("User has no email")
        )
    )
```

## Quand utiliser Result

**Utilisez Result quand :**

- Une opération peut échouer et vous voulez gérer l'erreur
- Vous voulez des erreurs typées au lieu d'exceptions textuelles
- Vous construisez un pipeline où les erreurs doivent se propager
- Vous voulez forcer les appelants à reconnaître les échecs potentiels

**N'utilisez pas Result quand :**

- L'échec est vraiment exceptionnel (bugs de programmation, mémoire épuisée)
- Vous êtes dans une boucle critique et la performance compte
- L'erreur ne contient pas d'informations utiles → considérez `Option`

## Comparaison avec Option

| Aspect | Option | Result |
|--------|--------|--------|
| Cas | `Some(T)`, `Nothing` | `Ok(T)`, `Err(E)` |
| Info sur l'absence | Non | Oui (type d'erreur) |
| Cas d'utilisation | La valeur peut ne pas exister | L'opération peut échouer |
| Convertir vers | `.to_result(err)` | N/A |

## Voir aussi

- [`Option`](option.md) — Quand l'absence n'a pas besoin d'informations d'erreur
- [`try_catch`](core.md#try_catch) — Convertir les exceptions en Result
- [`validate_all`](validate.md) — Accumuler plusieurs erreurs
- [`traverse_result`](traverse.md) — Collecter plusieurs Results en un seul
