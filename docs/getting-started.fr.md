# Commencer

Ce guide presente les idees fondamentales de la programmation fonctionnelle a travers fptk. Nous nous concentrerons sur la comprehension du *pourquoi* ces patrons existent, pas seulement sur comment les utiliser.

## Installation

```bash
pip install fptk
```

## Penser en transformations

Le plus grand changement en programmation fonctionnelle est de penser au code comme des **transformations de donnees** plutot que des **instructions a executer**.

Considerez ce code imperatif :

```python
def process_order(order):
    validated = validate_order(order)
    if not validated:
        return None

    total = calculate_total(validated)
    tax = apply_tax(total)

    result = save_order(tax)
    if not result:
        return None

    send_confirmation(result)
    return result
```

Ce code dit a l'ordinateur *quoi faire* etape par etape. Il est rempli de variables intermediaires, de verifications de None et de flux de controle implicite.

Maintenant, pensez-y comme un pipeline de transformation :

```
order → validate → calculate_total → apply_tax → save → send_confirmation → result
```

Chaque etape transforme les donnees en une nouvelle forme. C'est ce que `pipe` exprime :

```python
from fptk.core.func import pipe

def process_order(order):
    return pipe(
        order,
        validate_order,
        calculate_total,
        apply_tax,
        save_order,
        send_confirmation
    )
```

Le code se lit maintenant comme la transformation qu'il represente. Ajouter, supprimer ou reorganiser les etapes est trivial.

## Fonctions pures : le fondement

Une **fonction pure** a deux proprietes :

1. **Meme entree → meme sortie** : `add(2, 3)` retourne toujours `5`
2. **Pas d'effets de bord** : Elle ne modifie rien en dehors d'elle-meme

Pourquoi est-ce important ? Parce que les fonctions pures sont :

- **Testables** : Pas besoin de mocks, juste affirmer que `f(input) == expected_output`
- **Memorisables** : Si `f(x)` retourne toujours la meme chose, vous pouvez la mettre en cache
- **Parallelisables** : Pas d'etat partage signifie pas de conditions de course
- **Composables** : Vous pouvez les combiner librement sans surprises

La plupart des bugs viennent de l'etat mutable partage. Les fonctions pures eliminent toute cette categorie de bugs.

```python
# Impure: modifies external state
total = 0
def add_to_total(x):
    global total
    total += x  # Side effect!
    return total

# Pure: no side effects
def add(a, b):
    return a + b
```

fptk vous aide a ecrire des fonctions pures en fournissant des outils pour gerer les choses qui necessitent habituellement de l'impurete : erreurs, valeurs manquantes, etat et effets.

## Option : rendre l'absence explicite

Dans la plupart des langages, n'importe quelle valeur peut etre `null` ou `None`. Cela mene a de la programmation defensive :

```python
if user is not None:
    if user.profile is not None:
        if user.profile.name is not None:
            print(user.profile.name)
```

Le probleme n'est pas None en soi — c'est que None est *implicite*. N'importe quelle fonction peut retourner None, et le systeme de types ne vous avertit pas.

**Option** rend l'absence explicite. Une valeur est soit `Some(value)` soit `Nothing` :

```python
from fptk.adt.option import Some, NOTHING, from_nullable

# Explicit: this might be absent
maybe_name: Option[str] = from_nullable(get_name())

# You must handle both cases
name = maybe_name.unwrap_or("Anonymous")
```

La puissance vient du **chainage**. Au lieu de verifications de None imbriquees :

```python
# Without Option
if user and user.get("profile") and user.get("profile").get("email"):
    email = user["profile"]["email"].lower()
else:
    email = None
```

Vous composez des transformations qui gerent automatiquement l'absence :

```python
# With Option
email = (
    from_nullable(user)
    .bind(lambda u: from_nullable(u.get("profile")))
    .bind(lambda p: from_nullable(p.get("email")))
    .map(str.lower)
)
```

Si une etape retourne `Nothing`, le reste de la chaine est ignore. Pas besoin de verifications de None.

### Idee cle : map vs bind

- `map(f)` transforme la valeur a l'interieur : `Some(5).map(lambda x: x * 2)` → `Some(10)`
- `bind(f)` chaine des calculs qui peuvent echouer : quand `f` elle-meme retourne une Option

```python
Some(5).map(lambda x: x * 2)           # Some(10) - f returns a value
Some(5).bind(lambda x: Some(x * 2))    # Some(10) - f returns an Option
Some(5).map(lambda x: Some(x * 2))     # Some(Some(10)) - wrong!
```

## Result : les erreurs comme valeurs

Les exceptions ont un probleme : elles sont invisibles. En regardant la signature d'une fonction, vous ne pouvez pas dire si elle peut echouer :

```python
def parse_config(path: str) -> dict:  # Might raise FileNotFoundError, JSONDecodeError, ...
    ...
```

Vous enveloppez tout dans des try/except ou vous decouvrez les erreurs a l'execution.

**Result** rend les erreurs explicites. Un calcul reussit avec `Ok(value)` ou echoue avec `Err(error)` :

```python
from fptk.adt.result import Ok, Err, Result

def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"'{s}' is not a valid integer")
```

Le type de retour `Result[int, str]` vous dit : cela retourne un int, mais peut echouer avec une erreur de type string.

Comme Option, Result supporte le chainage :

```python
def process_input(raw: str) -> Result[int, str]:
    return (
        parse_int(raw)
        .map(lambda x: x * 2)
        .bind(validate_positive)
        .map(lambda x: x + 10)
    )
```

Si une etape echoue, l'erreur se propage automatiquement. Pas d'imbrication de try/except.

### Programmation orientee railway

Pensez a Result comme un chemin de fer avec deux voies :

```
         ┌─ Ok ──→ map ──→ bind ──→ Ok result
Input ───┤
         └─ Err ─────────────────→ Err result
```

Une fois sur la voie d'erreur, vous y restez. C'est ce qu'on appelle la "programmation orientee railway" et cela rend la gestion des erreurs composable.

## Validation : accumuler les erreurs

La gestion d'erreurs normale est fail-fast : la premiere erreur arrete tout.

```python
def validate(data):
    if not data.get("email"):
        return Err("Email required")  # Stops here
    if not data.get("name"):
        return Err("Name required")   # Never reached
    ...
```

Pour la validation destinee aux utilisateurs, vous voulez montrer *toutes* les erreurs en une fois. `validate_all` les accumule :

```python
from fptk.validate import validate_all
from fptk.adt.result import Ok, Err

result = validate_all([
    lambda d: Ok(d) if d.get("email") else Err("Email required"),
    lambda d: Ok(d) if d.get("name") else Err("Name required"),
    lambda d: Ok(d) if len(d.get("password", "")) >= 8 else Err("Password too short"),
], data)

# Err(NonEmptyList("Email required", "Name required", "Password too short"))
```

C'est un exemple de style **applicatif**, ou des calculs independants peuvent etre combines. C'est different du style **monadique** (`bind`), ou chaque etape depend de la precedente.

## Composition : construire le complexe a partir du simple

L'objectif de la programmation fonctionnelle est de construire un comportement complexe en composant des pieces simples.

**compose** combine des fonctions :

```python
from fptk.core.func import compose

# f(g(x))
inc_then_double = compose(lambda x: x * 2, lambda x: x + 1)
inc_then_double(5)  # 12
```

**curry** vous permet d'appliquer partiellement des fonctions :

```python
from fptk.core.func import curry

@curry
def send_email(to, subject, body):
    ...

# Create specialized functions
send_alert = send_email("alerts@company.com")("ALERT")
send_alert("Server is down!")
```

Ces outils vous permettent de construire une application a partir de petites pieces reutilisables et testables.

## Quand utiliser fptk

**Bon choix :**

- Pipelines de transformation de donnees
- Validation et parsing
- Gestion d'erreurs qui doit etre explicite
- Code qui doit etre hautement testable
- Equipes apprenant la programmation fonctionnelle

**Commencez petit :**

Vous n'avez pas besoin de reecrire votre base de code. Commencez par :

1. Utilisez `pipe` pour une fonction complexe
2. Utilisez `Result` pour une operation sujette aux erreurs
3. Utilisez `Option` pour une chaine nullable

Chaque patron apporte une valeur immediate par lui-meme.

## Prochaines etapes

- [Concepts fondamentaux](guide/core-concepts.md) — Guide detaille de chaque patron
- [Effets de bord](guide/side-effects.md) — Comment structurer les applications avec des coeurs purs
- [Guide de migration](guide/migration.md) — Adoption etape par etape depuis le code imperatif
- [Reference](reference/index.md) — Documentation complete avec theorie et exemples
