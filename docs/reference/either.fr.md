# Either

Le module `fptk.adt.either` fournit `Either[L, R]`, un type somme symétrique représentant l'une de deux valeurs possibles. Contrairement à `Result` qui a une sémantique succès/erreur, `Either` est neutre — `Left` et `Right` sont des alternatives également valides.

## Concept : Alternatives symétriques

Alors que `Result[T, E]` implique « succès ou échec », `Either[L, R]` signifie simplement « l'un ou l'autre ». Utilisez `Either` quand les deux possibilités sont des résultats valides, pas des erreurs.

```python
Either[L, R] = Left[L] | Right[R]
```

### Quand utiliser Either vs Result

| Type | Utilisation |
|------|-------------|
| `Result[T, E]` | Un chemin est un « succès », l'autre un « échec » |
| `Either[L, R]` | Les deux chemins sont des alternatives valides |

### Exemple : Parsing avec deux résultats valides

```python
from fptk.adt.either import Either, Left, Right

def parse_id(s: str) -> Either[int, str]:
    """Parse en ID entier, ou garde en nom texte."""
    if s.isdigit():
        return Left(int(s))
    return Right(s)

# Les deux résultats sont valides
parse_id("123")   # Left(123) - ID numérique
parse_id("alice") # Right("alice") - nom textuel
```

## API

### Types

| Type | Description |
|------|-------------|
| `Either[L, R]` | Type somme : soit `Left[L]` soit `Right[R]` |
| `Left[L, R]` | Variante gauche contenant une valeur de type `L` |
| `Right[L, R]` | Variante droite contenant une valeur de type `R` |

### Constructeurs

```python
from fptk.adt.either import Left, Right

valeur_gauche = Left(42)        # Left[int, ???]
valeur_droite = Right("hello")  # Right[???, str]
```

### Méthodes

| Méthode | Signature | Description |
|---------|-----------|-------------|
| `is_left()` | `() -> bool` | True si Left |
| `is_right()` | `() -> bool` | True si Right |
| `map_left(f)` | `(L -> L2) -> Either[L2, R]` | Transforme la valeur Left |
| `map_right(f)` | `(R -> R2) -> Either[L, R2]` | Transforme la valeur Right |
| `bimap(f, g)` | `(L -> L2, R -> R2) -> Either[L2, R2]` | Transforme les deux côtés |
| `fold(on_left, on_right)` | `(L -> T, R -> T) -> T` | Pattern match vers une valeur unique |
| `swap()` | `() -> Either[R, L]` | Échange Left ↔ Right |

## Exemples

### Utilisation de base

```python
from fptk.adt.either import Either, Left, Right

# Créer des valeurs
gauche: Either[int, str] = Left(42)
droite: Either[int, str] = Right("hello")

# Vérifier la variante
gauche.is_left()   # True
droite.is_right()  # True
```

### Transformer les valeurs

```python
# map_left transforme Left, laisse passer Right
Left(5).map_left(lambda x: x * 2)     # Left(10)
Right("hi").map_left(lambda x: x * 2) # Right("hi")

# map_right transforme Right, laisse passer Left
Right("hi").map_right(str.upper)     # Right("HI")
Left(5).map_right(str.upper)         # Left(5)

# bimap transforme le côté présent
Left(2).bimap(lambda x: x + 1, str.upper)    # Left(3)
Right("a").bimap(lambda x: x + 1, str.upper) # Right("A")
```

### Pattern matching avec fold

```python
def decrire(e: Either[int, str]) -> str:
    return e.fold(
        on_left=lambda n: f"Nombre obtenu : {n}",
        on_right=lambda s: f"Chaîne obtenue : {s}"
    )

decrire(Left(42))       # "Nombre obtenu : 42"
decrire(Right("hello")) # "Chaîne obtenue : hello"
```

### Échanger les côtés

```python
Left(1).swap()    # Right(1)
Right("a").swap() # Left("a")

# Double swap revient à l'original
e = Left(5)
e.swap().swap() == e  # True
```

### Chaîner les transformations

```python
resultat = (
    Left(5)
    .map_left(lambda x: x * 2)   # Left(10)
    .map_left(lambda x: x + 1)   # Left(11)
    .map_right(str.upper)        # Toujours Left(11)
)

resultat2 = (
    Right("hello")
    .map_left(lambda x: x * 2)    # Toujours Right("hello")
    .map_right(str.upper)         # Right("HELLO")
    .map_right(lambda s: s + "!") # Right("HELLO!")
)
```

## Either vs Result

```python
from fptk.adt.either import Left, Right
from fptk.adt.result import Ok, Err

# Result : sémantique succès/échec
def diviser(a: int, b: int) -> Result[float, str]:
    if b == 0:
        return Err("division par zéro")  # C'est une erreur
    return Ok(a / b)                      # C'est un succès

# Either : deux alternatives valides
def classifier(n: int) -> Either[int, int]:
    if n % 2 == 0:
        return Left(n)   # Nombres pairs
    return Right(n)      # Nombres impairs
    # Aucun n'est « faux » — ce sont juste des catégories différentes
```

## Voir aussi

- [`Result`](result.md) — Succès/échec avec erreurs typées
- [`Option`](option.md) — Valeurs optionnelles
