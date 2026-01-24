# État (State)

Le module `fptk.adt.state` propose la monade `State`, dédiée à la modélisation de calculs impliquant un état de façon pure. Elle permet de concevoir du code capable de lire et de modifier un état sans jamais recourir à la mutation réelle de données.

## Concept : La Monade State

La monade State modélise des calculs qui propagent un état mutable à travers une série d'opérations, mais de manière pure. Chaque opération reçoit l'état courant et renvoie un couple composé d'une valeur et du nouvel état.

Voyez-la comme : **une fonction transformant un état tout en produisant une valeur.**

```python
State[S, A]  ≈  S -> (A, S)
```

Ainsi, un `State[Counter, int]` est un calcul qui, à partir d'un état `Counter`, produit un entier (`int`) et un nouvel état `Counter` mis à jour.

### Le problème : la complexité de l'état mutable

```python
class Analyseur:
    def __init__(self, texte):
        self.texte = texte
        self.pos = 0  # État mutable caché !

    def consommer(self, n: int) -> str:
        resultat = self.texte[self.pos:self.pos + n]
        self.pos += n  # Mutation directe
        return resultat

# Difficile à tester : l'état est interne et muable.
# Difficile à appréhender : quel est l'état exact à un instant T ?
# Difficile de revenir en arrière : nécessite de sauvegarder/restaurer 'pos' manuellement.
```

### La solution avec `State`

```python
from fptk.adt.state import State, get, put, modify

@dataclass(frozen=True)
class ParserState:
    texte: str
    pos: int

def consommer(n: int) -> State[ParserState, str]:
    return (
        get()
        .bind(lambda s:
            put(ParserState(s.texte, s.pos + n))
            .map(lambda _: s.texte[s.pos:s.pos + n])
        )
    )

# Pur, testable et composable.
# Retour en arrière immédiat : il suffit de conserver l'ancienne version de l'état.
initial = ParserState("bonjour", 0)
resultat, etat_final = consommer(3).run(initial)
# resultat = "bon", etat_final = ParserState("bonjour", 3)
```

## API

### Types

| Type | Description |
| :--- | :--- |
| `State[S, A]` | Un calcul impliquant un état de type `S` et produisant un résultat de type `A`. |

### Constructeurs

```python
from fptk.adt.state import State

# Création depuis une fonction S -> (A, S)
mon_etat = State(lambda s: (s * 2, s + 1))
```

### Méthodes principales

| Méthode | Signature | Description |
| :--- | :--- | :--- |
| `map(f)` | `(A -> B) -> State[S, B]` | Transforme la valeur de retour sans modifier la transition d'état. |
| `bind(f)` | `(A -> State[S, B]) -> State[S, B]` | Enchaîne deux calculs à état. |
| `run(initial)` | `(S) -> (A, S)` | Exécute le calcul à partir d'un état initial. |

### Fonctions utilitaires

| Fonction | Signature | Description |
| :--- | :--- | :--- |
| `get()` | `() -> State[S, S]` | Récupère l'état actuel. |
| `put(s)` | `(S) -> State[S, None]` | Remplace l'état actuel par un nouvel état. |
| `modify(f)` | `(S -> S) -> State[S, None]` | Applique une fonction de transformation à l'état. |
| `gets(f)` | `(S -> A) -> State[S, A]` | Récupère une version transformée de l'état. |

## Fonctionnement technique

### Structure de données

`State` encapsule une fonction opérant la transition d'un état vers un couple (valeur, nouvel état) :

```python
@dataclass(frozen=True, slots=True)
class State[S, A]:
    run_state: Callable[[S], tuple[A, S]]

    def run(self, initial_state: S) -> tuple[A, S]:
        return self.run_state(initial_state)
```

### La Monade : `bind`

`bind` permet de séquencer des calculs à état en transmettant l'état résultant du premier calcul comme entrée du second :

```python
def bind(self, f):
    def run(state):
        valeur, etat_intermediaire = self.run_state(state)
        return f(valeur).run_state(etat_intermediaire)
    return State(run)
```

Point clé : le second calcul ne s'exécute qu'une fois le premier terminé, avec l'état mis à jour par ce dernier.

## Exemples d'utilisation

### Gestion d'une pile (Stack)

```python
Stack = tuple[int, ...]

def push(x: int) -> State[Stack, None]:
    return modify(lambda pile: (x,) + pile)

def pop() -> State[Stack, int]:
    def run(pile: Stack) -> tuple[int, Stack]:
        return pile[0], pile[1:]
    return State(run)

# Composition d'opérations sur la pile
programme = (
    push(1)
    .bind(lambda _: push(2))
    .bind(lambda _: pop())
)

resultat, pile_finale = programme.run(())
# resultat = 2, pile_finale = (1,)
```

### Génération déterministe de nombres aléatoires

`State` est idéal pour modéliser des générateurs dont l'état interne (la graine ou « seed ») doit être propagé sans mutation :

```python
def prochain_entier() -> State[RNG, int]:
    def run(rng: RNG) -> tuple[int, RNG]:
        nouvelle_graine = (a * rng.seed + c) % m
        return nouvelle_graine, RNG(nouvelle_graine)
    return State(run)
```

## Quand utiliser State ?

**Privilégiez State lorsque :**

-   Vous devez faire circuler et mettre à jour un état au cours d'un calcul de façon pure.
-   Vous voulez des transformations d'état parfaitement testables et prévisibles.
-   Vous concevez des analyseurs syntaxiques (parsers), des interpréteurs ou des moteurs de jeux.
-   Vous avez besoin de fonctionnalités de retour en arrière (undo/backtrack).

**Évitez State lorsque :**

-   Des paramètres de fonction explicites suffisent pour des cas simples.
-   La performance est ultra-critique (chaque étape crée un nouveau couple).
-   L'état est véritablement global et ne nécessite jamais de retour en arrière.

## Voir aussi

-   [`Reader`](reader.md) — Lorsque vous avez besoin d'accéder à un environnement en lecture seule.
-   [`Writer`](writer.md) — Pour une journalisation (log) en ajout seul.
-   [`Result`](result.md) — Pour combiner la gestion d'état avec des calculs susceptibles d'échouer.