# Validation

`fptk.validate` fournit une validation applicative - exécutant plusieurs vérifications et accumulant toutes les erreurs au lieu d'échouer rapidement.

## Concept : Validation applicative

La composition monadique standard (utilisant `bind`) est **fail-fast** : la première erreur arrête la chaîne. Mais pour la validation, vous souhaitez souvent **accumuler toutes les erreurs** pour montrer à l'utilisateur tout ce qui ne va pas en une seule fois.

```
Monadique (fail-fast) :     check1 → Err → stop
Applicatif (accumule) : check1 → Err, check2 → Err, check3 → Ok → Err([e1, e2])
```

Cela est important car :

- **Meilleure UX** : Afficher toutes les erreurs de validation en une fois, pas une à la fois
- **Retour complet** : Les utilisateurs peuvent tout corriger en une seule passe
- **Séparation des responsabilités** : La logique de validation reste indépendante et composable

### Le problème : Validation fail-fast

```python
def validate_user(data: dict) -> Result[User, str]:
    return (
        check_name(data)
        .bind(lambda _: check_email(data))
        .bind(lambda _: check_age(data))
        .map(lambda _: User(**data))
    )

# If name is invalid, we never see email/age errors
result = validate_user({"name": "", "email": "bad", "age": -5})
# Err("Name is required") — but email and age are also wrong!
```

### La solution applicative

```python
from fptk.validate import validate_all

def validate_user(data: dict) -> Result[User, NonEmptyList[str]]:
    return validate_all(
        [check_name, check_email, check_age],
        data
    ).map(lambda d: User(**d))

result = validate_user({"name": "", "email": "bad", "age": -5})
# Err(NonEmptyList("Name is required", "Invalid email", "Age must be positive"))
```

Toutes les vérifications s'exécutent, toutes les erreurs sont collectées.

## API

### Fonction

```python
from fptk.validate import validate_all

def validate_all(
    checks: Iterable[Callable[[T], Result[T, E]]],
    value: T
) -> Result[T, NonEmptyList[E]]
```

**Paramètres :**

- `checks` : Itérable de fonctions de validation, chacune prenant une valeur et retournant `Result[T, E]`
- `value` : La valeur à valider

**Retourne :**

- `Ok(value)` si toutes les vérifications passent
- `Err(NonEmptyList[E])` contenant toutes les erreurs si une vérification échoue

## Fonctionnement

### Implémentation

```python
def validate_all(checks, value):
    errors = None
    cur = value

    for check in checks:
        result = check(cur)
        if isinstance(result, Ok):
            cur = result.value  # Allow transformations
        elif isinstance(result, Err):
            err = result.error
            if errors is None:
                errors = NonEmptyList(err)
            else:
                errors = errors.append(err)

    return Ok(cur) if errors is None else Err(errors)
```

Points clés :

1. **Toutes les vérifications s'exécutent** : Contrairement à `bind`, nous ne nous arrêtons pas à la première erreur
2. **Les erreurs s'accumulent** : Collectées dans une `NonEmptyList`
3. **La valeur peut être transformée** : Si une vérification retourne `Ok(transformed)`, les vérifications suivantes utilisent cette valeur
4. **Garantie NonEmptyList** : Si nous retournons `Err`, il y a au moins une erreur

### Les validateurs comme fonctions

Chaque validateur est une fonction `T -> Result[T, E]` :

```python
def required(field: str) -> Callable[[dict], Result[dict, str]]:
    def check(data: dict) -> Result[dict, str]:
        if data.get(field):
            return Ok(data)
        return Err(f"{field} is required")
    return check
```

## Exemples

### Validation de formulaire

```python
from fptk.validate import validate_all
from fptk.adt.result import Ok, Err

# Define validators
def required(field: str):
    def check(data: dict):
        if data.get(field):
            return Ok(data)
        return Err(f"{field} is required")
    return check

def email_format(field: str):
    def check(data: dict):
        email = data.get(field, "")
        if "@" in email and "." in email:
            return Ok(data)
        return Err(f"{field} must be a valid email")
    return check

def min_length(field: str, n: int):
    def check(data: dict):
        value = data.get(field, "")
        if len(value) >= n:
            return Ok(data)
        return Err(f"{field} must be at least {n} characters")
    return check

def age_range(min_age: int, max_age: int):
    def check(data: dict):
        age = data.get("age")
        if age is None:
            return Ok(data)  # Optional field
        if not isinstance(age, int):
            return Err("age must be a number")
        if min_age <= age <= max_age:
            return Ok(data)
        return Err(f"age must be between {min_age} and {max_age}")
    return check

# Use validators
def validate_signup(form: dict) -> Result[dict, NonEmptyList[str]]:
    return validate_all([
        required("username"),
        required("email"),
        required("password"),
        email_format("email"),
        min_length("username", 3),
        min_length("password", 8),
        age_range(13, 120),
    ], form)

# Test it
bad_form = {
    "username": "ab",
    "email": "not-an-email",
    "password": "123",
    "age": 10,
}

result = validate_signup(bad_form)
# Err(NonEmptyList(
#   "email must be a valid email",
#   "username must be at least 3 characters",
#   "password must be at least 8 characters",
#   "age must be between 13 and 120"
# ))
```

### Validation de requête API

```python
from fptk.validate import validate_all
from fptk.core.func import pipe

def validate_request(request: dict) -> Result[dict, NonEmptyList[str]]:
    return validate_all([
        # Required fields
        required("method"),
        required("path"),

        # Method validation
        lambda r: (
            Ok(r) if r.get("method") in ["GET", "POST", "PUT", "DELETE"]
            else Err("Invalid HTTP method")
        ),

        # Path validation
        lambda r: (
            Ok(r) if r.get("path", "").startswith("/")
            else Err("Path must start with /")
        ),

        # Body validation for POST/PUT
        lambda r: (
            Ok(r) if r.get("method") not in ["POST", "PUT"] or r.get("body")
            else Err("Body required for POST/PUT")
        ),
    ], request)

# Handle the result
def process_request(request: dict):
    return validate_request(request).match(
        ok=lambda r: handle_valid_request(r),
        err=lambda errors: {
            "status": 400,
            "errors": list(errors)
        }
    )
```

### Bibliothèque de validateurs réutilisables

```python
from fptk.validate import validate_all
from fptk.adt.result import Ok, Err
import re

# Generic validators
def is_string(field: str):
    return lambda d: (
        Ok(d) if isinstance(d.get(field), str)
        else Err(f"{field} must be a string")
    )

def is_int(field: str):
    return lambda d: (
        Ok(d) if isinstance(d.get(field), int)
        else Err(f"{field} must be an integer")
    )

def matches(field: str, pattern: str, message: str):
    regex = re.compile(pattern)
    return lambda d: (
        Ok(d) if regex.match(d.get(field, ""))
        else Err(message)
    )

def one_of(field: str, options: list):
    return lambda d: (
        Ok(d) if d.get(field) in options
        else Err(f"{field} must be one of: {', '.join(map(str, options))}")
    )

def depends_on(field: str, condition_field: str, condition_value):
    """field is required when condition_field == condition_value"""
    return lambda d: (
        Ok(d) if d.get(condition_field) != condition_value or d.get(field)
        else Err(f"{field} is required when {condition_field} is {condition_value}")
    )

# Compose validators
user_validators = [
    required("name"),
    is_string("name"),
    min_length("name", 2),

    required("email"),
    matches("email", r"^[\w.-]+@[\w.-]+\.\w+$", "Invalid email format"),

    one_of("role", ["admin", "user", "guest"]),

    depends_on("department", "role", "admin"),
]
```

### Transformation pendant la validation

Les validateurs peuvent transformer les données :

```python
def normalize_email(data: dict) -> Result[dict, str]:
    """Lowercase and strip the email."""
    if "email" in data:
        normalized = {**data, "email": data["email"].lower().strip()}
        return Ok(normalized)
    return Ok(data)

def trim_strings(data: dict) -> Result[dict, str]:
    """Strip whitespace from all string fields."""
    return Ok({
        k: v.strip() if isinstance(v, str) else v
        for k, v in data.items()
    })

result = validate_all([
    trim_strings,      # Transform first
    normalize_email,
    required("email"),
    email_format("email"),
], form)
# The validation runs on normalized data
```

### Validation imbriquée

```python
def validate_address(data: dict) -> Result[dict, NonEmptyList[str]]:
    return validate_all([
        required("street"),
        required("city"),
        required("country"),
        lambda d: (
            Ok(d) if len(d.get("postal_code", "")) >= 5
            else Err("Postal code must be at least 5 characters")
        ),
    ], data)

def validate_user_with_address(data: dict) -> Result[dict, NonEmptyList[str]]:
    # Validate user fields
    user_result = validate_all([
        required("name"),
        required("email"),
    ], data)

    # Validate nested address
    address_result = validate_address(data.get("address", {}))

    # Combine results
    match (user_result, address_result):
        case (Ok(_), Ok(_)):
            return Ok(data)
        case (Err(e1), Ok(_)):
            return Err(e1)
        case (Ok(_), Err(e2)):
            return Err(e2)
        case (Err(e1), Err(e2)):
            # Combine error lists
            combined = e1
            for e in e2:
                combined = combined.append(f"address.{e}")
            return Err(combined)
```

## Quand utiliser validate_all

**Utilisez validate_all quand :**

- Vous voulez afficher toutes les erreurs de validation en une fois
- Vous validez une saisie utilisateur (formulaires, requêtes API)
- Chaque validation est indépendante
- Une meilleure UX est importante

**Utilisez une chaîne de bind quand :**

- Les validations dépendent les unes des autres
- Vous n'avez besoin que de la première erreur
- Le comportement court-circuit est souhaité

## validate_all vs traverse_result

| Fonction | Comportement des erreurs | Type de retour |
|----------|---------------|-------------|
| `traverse_result` | Fail-fast (première erreur) | `Result[list[T], E]` |
| `validate_all` | Accumule toutes les erreurs | `Result[T, NonEmptyList[E]]` |

```python
# traverse_result: stop at first error
traverse_result(["bad1", "bad2"], parse)
# Err("bad1 is invalid")

# validate_all: collect all errors
validate_all([check1, check2, check3], value)
# Err(NonEmptyList("error1", "error2"))
```

## Voir aussi

- [`Result`](result.md) - Le type Result sous-jacent
- [`NonEmptyList`](nelist.md) - Le type de collection d'erreurs
- [`traverse_result`](traverse.md) - Pour le traitement fail-fast de collections
- [Recette développement API](../recipes/api-development.md) - Validation dans les APIs web
