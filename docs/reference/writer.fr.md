# Writer

`fptk.adt.writer` fournit la monade `Writer` pour des calculs qui produisent une valeur accompagnée d'un journal accumulé. Elle sépare les préoccupations "quoi calculer" de "quoi enregistrer".

## Concept : La monade Writer

La monade Writer représente des calculs qui produisent à la fois une valeur et un journal qui s'accumule à travers les opérations. Le journal peut être n'importe quel **monoïde** — un type avec un élément identité et une opération de combinaison associative.

Considérez-la comme : **un calcul qui maintient un journal courant**.

```python
Writer[W, A]  ≈  (A, W)  # where W is a Monoid
```

Un `Writer[list[str], int]` est un calcul qui produit un `int` tout en accumulant une liste de messages de journal.

### Le problème : La journalisation mêlée à la logique

```python
def process(data, logger):
    logger.info("Starting processing")
    validated = validate(data)
    logger.debug(f"Validated: {validated}")
    transformed = transform(validated)
    logger.debug(f"Transformed: {transformed}")
    logger.info("Processing complete")
    return transformed

# Problems:
# - Logger pollutes function signatures
# - Side effects interleaved with pure logic
# - Hard to test without mocking logger
```

### La solution Writer

```python
from fptk.adt.writer import Writer, tell, monoid_list

def process(data) -> Writer[list[str], Result]:
    return (
        Writer.unit(data, monoid_list)
        .bind(lambda d: tell(["Starting processing"]).map(lambda _: d))
        .bind(lambda d:
            tell([f"Validated: {validate(d)}"]).map(lambda _: validate(d))
        )
        .bind(lambda v:
            tell([f"Transformed: {transform(v)}"]).map(lambda _: transform(v))
        )
        .bind(lambda t:
            tell(["Processing complete"]).map(lambda _: t)
        )
    )

# Pure: no side effects until we extract
result, logs = process(data).run()
# Then write logs however we want
for log in logs:
    print(log)
```

Le calcul est pur. Les journaux sont collectés, pas écrits. Nous pouvons les inspecter, les filtrer ou les rediriger.

## Concept : Les Monoïdes

Un **Monoïde** est un type avec :

1. Un **élément identité** (valeur vide) : `e`
2. Une **opération de combinaison associative** : `combine(a, combine(b, c)) == combine(combine(a, b), c)`

Monoïdes courants :

| Type | Identité | Combinaison |
|------|----------|-------------|
| `list` | `[]` | `+` (concaténation) |
| `str` | `""` | `+` (concaténation) |
| `int` (somme) | `0` | `+` (addition) |
| `int` (produit) | `1` | `*` (multiplication) |

fptk fournit :

```python
from fptk.adt.writer import monoid_list, monoid_str

monoid_list  # identity=[], combine=lambda a, b: a + b
monoid_str   # identity="", combine=lambda a, b: a + b
```

## API

### Types

| Type | Description |
|------|-------------|
| `Writer[W, A]` | Calcul produisant `A` avec journal `W` |
| `Monoid[W]` | Protocole avec `identity` et `combine` |

### Constructeur

```python
from fptk.adt.writer import Writer, monoid_list

# Create with empty log
w = Writer.unit(42, monoid_list)

# Create with value and initial log
w = Writer(42, ["started"], monoid_list)
```

### Méthodes

| Méthode | Signature | Description |
|---------|-----------|-------------|
| `unit(value, monoid)` | `classmethod` | Crée avec un journal vide |
| `map(f)` | `(A -> B) -> Writer[W, B]` | Transforme la valeur |
| `bind(f)` | `(A -> Writer[W, B]) -> Writer[W, B]` | Chaîne, en combinant les journaux |
| `run()` | `() -> (A, W)` | Extrait la valeur et le journal |

### Fonctions

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `tell(log, monoid)` | `(W, Monoid[W]) -> Writer[W, None]` | Ajoute au journal |
| `listen(writer)` | `Writer[W, A] -> Writer[W, (A, W)]` | Obtient la valeur et le journal en paire |
| `censor(f, writer)` | `(W -> W, Writer[W, A]) -> Writer[W, A]` | Modifie le journal |

### Exigences du Monoïde

Certaines fonctions nécessitent un paramètre monoïde, d'autres non :

| Fonction | Nécessite Monoïde ? | Pourquoi |
|----------|-------------------|----------|
| `Writer(v, log, m)` | Oui | Crée un nouveau Writer |
| `Writer.unit(v, m)` | Oui | Crée un nouveau Writer |
| `tell(log, m)` | Oui | Crée un nouveau Writer |
| `listen(w)` | Non | Utilise le monoïde du Writer existant |
| `censor(f, w)` | Non | Utilise le monoïde du Writer existant |

Les fonctions qui **créent** un Writer ont besoin du monoïde pour savoir comment combiner les journaux plus tard. Les fonctions qui **opèrent sur** un Writer existant ont déjà accès à son monoïde.

```python
from fptk.adt.writer import Writer, tell, listen, censor, monoid_list

# Creating Writers - need monoid
w1 = Writer.unit(5, monoid_list)
w2 = tell(["log entry"], monoid_list)

# Operating on existing Writers - monoid comes from the Writer
w3 = listen(w1)                          # Uses w1's monoid
w4 = censor(lambda logs: logs[-1:], w1)  # Uses w1's monoid
```

### Monoïdes intégrés

| Monoïde | Description |
|--------|-------------|
| `monoid_list` | Concaténation de listes |
| `monoid_str` | Concaténation de chaînes |

## Fonctionnement

### Structure de données

Writer stocke une valeur, un journal et le monoïde pour combiner les journaux :

```python
@dataclass(frozen=True, slots=True)
class Monoid[W]:
    identity: W
    combine: Callable[[W, W], W]

@dataclass(frozen=True, slots=True)
class Writer[W, A]:
    value: A
    log: W
    monoid: Monoid[W]

    @classmethod
    def unit(cls, value, monoid):
        return cls(value, monoid.identity, monoid)

    def run(self):
        return (self.value, self.log)
```

### Le Functor : `map`

`map` transforme la valeur, en préservant le journal :

```python
def map(self, f):
    return Writer(f(self.value), self.log, self.monoid)
```

### La Monade : `bind`

`bind` séquence les calculs et combine leurs journaux :

```python
def bind(self, f):
    wb = f(self.value)
    return Writer(
        wb.value,
        self.monoid.combine(self.log, wb.log),  # Combine logs!
        self.monoid
    )
```

Point clé : les journaux des deux calculs sont combinés en utilisant l'opération `combine` du monoïde.

### Opérations Writer

```python
def tell(log, monoid):
    """Add to log, return None as value."""
    return Writer(None, log, monoid)

def listen(writer):
    """Get value and log as a pair."""
    return Writer((writer.value, writer.log), writer.log, writer.monoid)

def censor(f, writer):
    """Apply f to modify the log."""
    return Writer(writer.value, f(writer.log), writer.monoid)
```

## Exemples

### Journalisation simple

```python
from fptk.adt.writer import Writer, tell, monoid_list

def double(x: int) -> Writer[list[str], int]:
    result = x * 2
    return tell([f"Doubled {x} to {result}"], monoid_list).map(lambda _: result)

def add_ten(x: int) -> Writer[list[str], int]:
    result = x + 10
    return tell([f"Added 10 to {x}, got {result}"], monoid_list).map(lambda _: result)

# Chain operations
result = (
    Writer.unit(5, monoid_list)
    .bind(double)
    .bind(add_ten)
)

value, logs = result.run()
# value = 20
# logs = ["Doubled 5 to 10", "Added 10 to 10, got 20"]
```

### Collecte de métriques

```python
from dataclasses import dataclass

@dataclass
class Metrics:
    db_queries: int = 0
    cache_hits: int = 0
    api_calls: int = 0

    def __add__(self, other):
        return Metrics(
            self.db_queries + other.db_queries,
            self.cache_hits + other.cache_hits,
            self.api_calls + other.api_calls
        )

monoid_metrics = Monoid(
    identity=Metrics(),
    combine=lambda a, b: a + b
)

def record_db_query() -> Writer[Metrics, None]:
    return tell(Metrics(db_queries=1), monoid_metrics)

def record_cache_hit() -> Writer[Metrics, None]:
    return tell(Metrics(cache_hits=1), monoid_metrics)

def fetch_user(id: int) -> Writer[Metrics, User]:
    # Check cache first
    cached = cache.get(id)
    if cached:
        return record_cache_hit().map(lambda _: cached)

    # Query database
    user = db.query(id)
    return record_db_query().map(lambda _: user)

# Collect metrics across operations
result = (
    fetch_user(1)
    .bind(lambda u1: fetch_user(2).map(lambda u2: [u1, u2]))
    .bind(lambda users: fetch_user(3).map(lambda u3: users + [u3]))
)

users, metrics = result.run()
# metrics.db_queries = 2, metrics.cache_hits = 1, etc.
```

### Piste d'audit

```python
from datetime import datetime

@dataclass
class AuditEntry:
    timestamp: datetime
    action: str
    user: str

def audit(action: str, user: str) -> Writer[list[AuditEntry], None]:
    entry = AuditEntry(datetime.now(), action, user)
    return tell([entry], monoid_list)

def transfer_funds(from_acc: str, to_acc: str, amount: float, user: str):
    return (
        audit(f"Started transfer of ${amount}", user)
        .bind(lambda _: debit(from_acc, amount))
        .bind(lambda _: audit(f"Debited {from_acc}", user))
        .bind(lambda _: credit(to_acc, amount))
        .bind(lambda _: audit(f"Credited {to_acc}", user))
        .bind(lambda _: audit("Transfer complete", user))
    )

_, audit_trail = transfer_funds("A", "B", 100, "alice").run()
# audit_trail contains all entries in order
```

### Utiliser `censor` pour filtrer les journaux

```python
def verbose_computation() -> Writer[list[str], int]:
    return (
        Writer.unit(0, monoid_list)
        .bind(lambda x: tell(["DEBUG: starting"], monoid_list).map(lambda _: x))
        .bind(lambda x: tell(["INFO: processing"], monoid_list).map(lambda _: x + 1))
        .bind(lambda x: tell(["DEBUG: intermediate"], monoid_list).map(lambda _: x))
        .bind(lambda x: tell(["INFO: done"], monoid_list).map(lambda _: x + 1))
    )

# Filter to only INFO level
def only_info(logs):
    return [l for l in logs if l.startswith("INFO")]

result = censor(only_info, verbose_computation())
value, logs = result.run()
# logs = ["INFO: processing", "INFO: done"]
```

### Utiliser `listen` pour inspecter les journaux

```python
def computation_with_summary() -> Writer[list[str], str]:
    return (
        listen(verbose_computation())
        .map(lambda pair:
            f"Computed {pair[0]} with {len(pair[1])} log entries"
        )
    )

summary, logs = computation_with_summary().run()
# summary = "Computed 2 with 4 log entries"
# logs still contains all entries
```

### Monoïdes personnalisés

Vous pouvez créer des monoïdes personnalisés pour tout type avec un élément identité et une opération de combinaison associative.

#### Monoïde de somme

Suivre des valeurs cumulatives comme les coûts, les comptages ou les tailles :

```python
monoid_sum = Monoid(identity=0, combine=lambda a, b: a + b)

def process_with_cost(data: list) -> Writer[int, list]:
    return tell(len(data), monoid_sum).map(lambda _: [x * 2 for x in data])

result = (
    Writer.unit([1, 2, 3], monoid_sum)
    .bind(process_with_cost)  # cost: 3
    .bind(process_with_cost)  # cost: 3
)

value, total_cost = result.run()
# value = [4, 8, 12], total_cost = 6
```

#### Monoïde de maximum

Suivre les valeurs de pointe comme l'utilisation maximale de mémoire ou la latence la plus élevée :

```python
monoid_max = Monoid(identity=float('-inf'), combine=max)

def track_max(value: float) -> Writer[float, float]:
    return tell(value, monoid_max).map(lambda _: value)

result = (
    track_max(5.0)
    .bind(lambda _: track_max(10.0))
    .bind(lambda _: track_max(3.0))
)

_, max_seen = result.run()
# max_seen = 10.0
```

#### Monoïde d'union d'ensembles

Collecter des éléments uniques comme des tags, des catégories ou des noeuds visités :

```python
monoid_set = Monoid(identity=frozenset(), combine=lambda a, b: a | b)

def tag(labels: set[str]) -> Writer[frozenset[str], None]:
    return tell(frozenset(labels), monoid_set)

result = (
    tag({"python", "fp"})
    .bind(lambda _: tag({"fp", "monad"}))
    .bind(lambda _: tag({"tutorial"}))
)

_, all_tags = result.run()
# all_tags = frozenset({"python", "fp", "monad", "tutorial"})
```

#### Monoïde de produit

Calculer des probabilités combinées ou des facteurs d'échelle :

```python
monoid_product = Monoid(identity=1.0, combine=lambda a, b: a * b)

def scale(factor: float) -> Writer[float, float]:
    return tell(factor, monoid_product).map(lambda _: factor)

result = (
    scale(0.9)
    .bind(lambda _: scale(0.8))
    .bind(lambda _: scale(0.95))
)

_, combined_factor = result.run()
# combined_factor = 0.684 (0.9 * 0.8 * 0.95)
```

## Quand utiliser Writer

**Utilisez Writer lorsque :**

- Vous voulez accumuler des journaux/métriques aux côtés des calculs
- Vous avez besoin de pistes d'audit ou de traçage
- Vous voulez séparer les préoccupations de journalisation de la logique métier
- Vous avez besoin d'une journalisation pure et testable

**N'utilisez pas Writer lorsque :**

- Les journaux doivent être écrits immédiatement (utilisez des systèmes d'effets)
- Le journal pourrait croître indéfiniment (problèmes de mémoire)
- Des cas simples où une journalisation explicite est plus claire

## Writer vs autres patterns

| Pattern | Quand l'utiliser |
|---------|------------------|
| Monade Writer | Accumulation de journal pure, composable |
| Injection de logger | Lorsque vous avez besoin d'E/S immédiates |
| Logger global | Applications simples (éviter pour la testabilité) |
| Monade State | Lorsque vous devez lire/modifier le journal |

Writer est particulièrement utile pour le traçage, l'audit et la collecte de métriques de manière pure et composable.

## Voir aussi

- [`Reader`](reader.md) — Accès à l'environnement en lecture seule
- [`State`](state.md) — Lire et écrire l'état
- [Effets de bord](../guide/side-effects.md) — Coeurs purs avec effets aux frontières
