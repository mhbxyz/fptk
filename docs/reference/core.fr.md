# Fonctions de base

`fptk.core.func` fournit des combinateurs de fonctions — de petits utilitaires qui vous aident à composer, transformer et contrôler des fonctions. Ce sont les briques de base de la programmation fonctionnelle en Python.

## Concept : Combinateurs de fonctions

En programmation fonctionnelle, les fonctions sont des valeurs. Tout comme vous pouvez passer des entiers à des fonctions et les retourner, vous pouvez passer des fonctions à d'autres fonctions et retourner de nouvelles fonctions. Les **combinateurs de fonctions** sont des fonctions d'ordre supérieur qui combinent ou transforment des fonctions.

Cela est important car :

- **Composition plutôt qu'héritage** : Construire des comportements complexes en combinant des fonctions simples
- **Style point-free** : Exprimer des transformations sans nommer les valeurs intermédiaires
- **Réutilisabilité** : De petites fonctions se composent en de nombreux pipelines différents

## `pipe`

Faire passer une valeur à travers une séquence de fonctions, de gauche à droite.

```python
from fptk.core.func import pipe

def pipe(x, *funcs):
    """Thread a value through unary functions."""
```

### Pourquoi `pipe` ?

Les appels de fonctions imbriqués se lisent de l'intérieur vers l'extérieur :

```python
# Difficile à lire : l'ordre d'exécution est h(g(f(x)))
result = format_output(validate(parse_input(raw_data)))
```

`pipe` rend le flux de données linéaire et lisible :

```python
# Clair : parse → validate → format
result = pipe(raw_data, parse_input, validate, format_output)
```

### Fonctionnement

```python
def pipe(x, *funcs):
    for f in funcs:
        x = f(x)
    return x
```

Chaque fonction reçoit la sortie de la précédente. L'implémentation est un simple fold sur la liste de fonctions.

### Exemples

```python
from fptk.core.func import pipe

# Basic transformation chain
result = pipe(
    "  hello world  ",
    str.strip,
    str.upper,
    lambda s: s.replace(" ", "_")
)
# result = "HELLO_WORLD"

# With Option for safe chaining
from fptk.adt.option import from_nullable

name = pipe(
    user_dict,
    lambda d: from_nullable(d.get("profile")),
    lambda opt: opt.bind(lambda p: from_nullable(p.get("name"))),
    lambda opt: opt.map(str.upper),
    lambda opt: opt.unwrap_or("Anonymous")
)
```

---

## `compose`

Combiner deux fonctions en une seule : `(f ∘ g)(x) = f(g(x))`.

```python
from fptk.core.func import compose

def compose(f, g):
    """Compose two unary functions: f(g(x))."""
```

### Pourquoi `compose` ?

`compose` construit des pipelines de fonctions réutilisables. Contrairement à `pipe` qui s'applique immédiatement à une valeur, `compose` crée une nouvelle fonction que vous pouvez utiliser plus tard.

```python
# Create a reusable transformation
normalize = compose(str.upper, str.strip)

# Apply it anywhere
normalize("  hello  ")  # "HELLO"
normalize("  world  ")  # "WORLD"
```

### Fonctionnement

```python
def compose(f, g):
    def h(x):
        return f(g(x))
    return h
```

Composition mathématique de fonctions : appliquer `g` d'abord, puis `f`. C'est l'ordre inverse de `pipe`.

### Exemples

```python
from fptk.core.func import compose

# Build transformation pipelines
strip_and_lower = compose(str.lower, str.strip)
strip_and_lower("  HELLO  ")  # "hello"

# Compose multiple functions (nested)
process = compose(
    lambda s: s.replace(" ", "_"),
    compose(str.upper, str.strip)
)
process("  hello world  ")  # "HELLO_WORLD"

# Use with higher-order functions
users = [" Alice ", " Bob "]
list(map(strip_and_lower, users))  # ["alice", "bob"]
```

---

## `curry`

Transformer une fonction de N arguments en N fonctions imbriquées d'un argument.

```python
from fptk.core.func import curry

def curry(fn):
    """Curry a function of N positional args."""
```

### Pourquoi `curry` ?

La curryfication permet l'**application partielle** — fournir certains arguments maintenant et le reste plus tard.

```python
# Without currying: need lambda
list(map(lambda x: add(1, x), [1, 2, 3]))

# With currying: cleaner
add = curry(lambda a, b: a + b)
list(map(add(1), [1, 2, 3]))  # [2, 3, 4]
```

### Fonctionnement

```python
def curry(fn):
    def curried(*args, **kwargs):
        needed = fn.__code__.co_argcount
        if len(args) + len(kwargs) >= needed:
            return fn(*args, **kwargs)
        return lambda *a, **k: curried(*(args + a), **{**kwargs, **k})
    return curried
```

La fonction curryfiée vérifie si suffisamment d'arguments ont été fournis. Si oui, elle appelle la fonction originale. Si non, elle retourne une nouvelle fonction qui attend plus d'arguments.

### Exemples

```python
from fptk.core.func import curry

# Basic currying
add = curry(lambda a, b: a + b)
add_one = add(1)
add_one(5)  # 6

# Three-argument function
format_name = curry(lambda first, middle, last: f"{first} {middle} {last}")
format_smith = format_name("John")("Q")
format_smith("Smith")  # "John Q Smith"

# Use with map/filter
multiply = curry(lambda a, b: a * b)
list(map(multiply(2), [1, 2, 3]))  # [2, 4, 6]
```

---

## `flip`

Permuter les deux premiers arguments d'une fonction binaire.

```python
from fptk.core.func import flip

def flip(fn):
    """Flip the first two arguments."""
```

### Pourquoi `flip` ?

Parfois une fonction a ses arguments dans le mauvais ordre pour votre cas d'utilisation :

```python
# pow(base, exp) - but we want to map over bases with fixed exponent
list(map(lambda x: pow(x, 2), [1, 2, 3]))

# With flip
square = flip(pow)(2)  # flip makes it pow(exp, base)
list(map(square, [1, 2, 3]))  # [1, 4, 9]
```

### Fonctionnement

```python
def flip(fn):
    def flipped(b, a):
        return fn(a, b)
    return flipped
```

Inverse simplement les deux premiers arguments.

### Exemples

```python
from fptk.core.func import flip

# Flip division
div = lambda a, b: a / b
div(10, 2)  # 5.0

half_of = flip(div)(2)  # flipped: (2, x) -> x / 2
half_of(10)  # 5.0

# Flip string methods
append_to = flip(lambda s, suffix: s + suffix)
add_exclaim = append_to("!")
add_exclaim("hello")  # "hello!"
```

---

## `tap`

Exécuter un effet de bord sur une valeur et retourner la valeur originale inchangée.

```python
from fptk.core.func import tap

def tap(f):
    """Run side effect, return input."""
```

### Pourquoi `tap` ?

Déboguer des pipelines est délicat — vous voulez inspecter des valeurs sans les modifier :

```python
result = pipe(
    data,
    parse,
    tap(print),  # See parsed data
    validate,
    tap(lambda x: logger.debug(f"Validated: {x}")),
    transform
)
```

### Fonctionnement

```python
def tap(f):
    def inner(x):
        f(x)
        return x
    return inner
```

Appelle `f` pour son effet de bord, ignore sa valeur de retour, retourne l'entrée originale.

### Exemples

```python
from fptk.core.func import tap, pipe

# Debug a pipeline
result = pipe(
    [1, 2, 3],
    lambda xs: [x * 2 for x in xs],
    tap(lambda xs: print(f"After doubling: {xs}")),
    sum
)
# Prints: After doubling: [2, 4, 6]
# result = 12

# Log without breaking flow
def log(msg):
    def logger(x):
        print(f"{msg}: {x}")
    return tap(logger)

pipe("hello", str.upper, log("uppercased"), str.title)
# Prints: uppercased: HELLO
# Returns: "Hello"
```

---

## `thunk`

Créer un calcul paresseux et mémoïsé. La fonction s'exécute une seule fois, au premier appel.

```python
from fptk.core.func import thunk

def thunk(f):
    """Memoized nullary function (lazy value)."""
```

### Pourquoi `thunk` ?

Retarder les calculs coûteux jusqu'à ce qu'ils soient nécessaires, et mettre en cache le résultat :

```python
expensive_config = thunk(lambda: load_config_from_disk())

# Config isn't loaded yet...

result = expensive_config()  # Loads now
result2 = expensive_config()  # Returns cached value
```

### Fonctionnement

```python
def thunk(f):
    evaluated = False
    value = None

    def wrapper():
        nonlocal evaluated, value
        if not evaluated:
            value = f()
            evaluated = True
        return value

    return wrapper
```

Patron classique de mémoïsation : suivre si le calcul a été effectué, stocker le résultat, retourner la valeur en cache lors des appels suivants.

### Exemples

```python
from fptk.core.func import thunk

# Lazy configuration
config = thunk(lambda: {
    "db_url": os.getenv("DATABASE_URL"),
    "api_key": os.getenv("API_KEY")
})

# Expensive computation
fib_100 = thunk(lambda: compute_fibonacci(100))
# Not computed until first call
print(fib_100())  # Computes
print(fib_100())  # Returns cached
```

---

## `identity`

Retourner l'entrée inchangée.

```python
from fptk.core.func import identity

def identity(x):
    """Return x unchanged."""
```

### Pourquoi `identity` ?

Utile comme fonction par défaut ou placeholder dans des contextes d'ordre supérieur :

```python
# Default transformation
transform = get_transform() or identity

# In Option.match
value = some_option.match(
    some=identity,  # Just return the value
    none=lambda: "default"
)
```

### Fonctionnement

```python
def identity(x):
    return x
```

La fonction la plus simple possible.

---

## `const`

Créer une fonction qui ignore ses arguments et retourne toujours une valeur fixe.

```python
from fptk.core.func import const

def const(x):
    """Return a function that always returns x."""
```

### Pourquoi `const` ?

Utile quand une API attend une fonction mais vous voulez une valeur fixe :

```python
# Always return 0 for missing keys
default_factory = const(0)

# In Result.unwrap_or_else
result.unwrap_or_else(const("default"))
```

### Fonctionnement

```python
def const(x):
    def inner(*_, **__):
        return x
    return inner
```

Capture `x` dans une closure, ignore tous les arguments.

### Exemples

```python
from fptk.core.func import const

always_zero = const(0)
always_zero(1, 2, 3)  # 0
always_zero("anything")  # 0

# Use in callbacks
list(map(const(1), [1, 2, 3]))  # [1, 1, 1]
```

---

## `once`

Envelopper une fonction pour qu'elle ne s'exécute qu'une seule fois. Les appels suivants retournent le premier résultat.

```python
from fptk.core.func import once

def once(fn):
    """Run at most once, memoize first result."""
```

### Pourquoi `once` ?

S'assurer que le code d'initialisation ne s'exécute qu'une seule fois :

```python
init_database = once(lambda: create_db_connection())

# First call: connects
init_database()

# Subsequent calls: returns same connection
init_database()
```

### Fonctionnement

```python
def once(fn):
    called = False
    result = None

    def wrapper(*args, **kwargs):
        nonlocal called, result
        if not called:
            result = fn(*args, **kwargs)
            called = True
        return result

    return wrapper
```

Comme `thunk`, mais accepte des arguments (qui sont ignorés après le premier appel).

---

## `try_catch`

Convertir des fonctions qui lèvent des exceptions en fonctions qui retournent des `Result`.

```python
from fptk.core.func import try_catch

def try_catch(fn):
    """Wrap fn to return Ok/Err instead of raising."""
```

### Pourquoi `try_catch` ?

Faire le pont entre le code basé sur les exceptions et les pipelines basés sur `Result` :

```python
# Standard library raises on invalid JSON
import json
json.loads("invalid")  # JSONDecodeError!

# Wrap to get Result
safe_parse = try_catch(json.loads)
safe_parse("invalid")  # Err(JSONDecodeError(...))
safe_parse('{"a": 1}')  # Ok({"a": 1})
```

### Fonctionnement

```python
def try_catch(fn):
    def wrapper(*args, **kwargs):
        try:
            return Ok(fn(*args, **kwargs))
        except Exception as e:
            return Err(e)
    return wrapper
```

Capture `Exception` (pas `BaseException`, pour éviter de capturer `KeyboardInterrupt`/`SystemExit`).

### Exemples

```python
from fptk.core.func import try_catch, pipe
from fptk.adt.result import Ok, Err

# Safe integer parsing
safe_int = try_catch(int)
safe_int("42")  # Ok(42)
safe_int("abc")  # Err(ValueError(...))

# In a pipeline
def process_input(raw: str):
    return pipe(
        raw,
        try_catch(json.loads),
        lambda r: r.map(extract_data),
        lambda r: r.bind(validate),
    )
```

---

## `async_pipe`

Version asynchrone de `pipe` qui gère à la fois les fonctions synchrones et asynchrones.

```python
from fptk.core.func import async_pipe

async def async_pipe(x, *funcs):
    """Thread value through possibly-async functions."""
```

### Fonctionnement

```python
async def async_pipe(x, *funcs):
    for f in funcs:
        x = f(x)
        if inspect.isawaitable(x):
            x = await x
    return x
```

Vérifie si chaque résultat est awaitable et l'attend si c'est le cas. Cela permet de mélanger des fonctions synchrones et asynchrones dans le même pipeline.

### Exemples

```python
from fptk.core.func import async_pipe

async def fetch_user(id):
    return await db.get_user(id)

def format_name(user):
    return user["name"].upper()

async def send_notification(name):
    await notifications.send(f"Hello, {name}")

# Mix sync and async
await async_pipe(
    user_id,
    fetch_user,      # async
    format_name,     # sync
    send_notification # async
)
```
