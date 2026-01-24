# Démarrage rapide

Ce guide vous initie aux concepts clés de la programmation fonctionnelle avec fptk. L'accent est mis sur le *pourquoi* de ces patrons, au-delà du simple *comment* les utiliser.

## Installation

```bash
pip install fptk
```

## Penser en transformations

Le principal changement de perspective en programmation fonctionnelle consiste à envisager le code comme une suite de **transformations de données**, plutôt que comme une liste d'**instructions à exécuter**.

Considérez ce code impératif :

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

Ce code dicte à l'ordinateur *quoi faire*, étape par étape. Il est truffé de variables intermédiaires, de vérifications de `None`, et de flux de contrôle implicites.

Maintenant, voyons-le comme un pipeline de transformation :

```
commande → validation → calcul_total → application_taxes → sauvegarde → envoi_confirmation → résultat
```

Chaque étape transforme les données en une nouvelle forme. C'est exactement ce que `pipe` exprime :

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

Le code reflète désormais la transformation qu'il représente. Ajouter, supprimer ou réorganiser des étapes devient un jeu d'enfant.

## Les fonctions pures : les fondations

Une **fonction pure** possède deux propriétés :

1.  **Même entrée → même sortie** : `add(2, 3)` renverra toujours `5`.
2.  **Absence d'effets de bord** : Elle ne modifie rien en dehors de son propre périmètre.

Pourquoi est-ce si important ? Parce que les fonctions pures sont :

-   **Testables** : Nul besoin de mocks, il suffit de vérifier que `f(input) == expected_output`.
-   **Mémorisables (cacheable)** : Si `f(x)` renvoie un résultat identique pour une même entrée, ce résultat peut être mis en cache.
-   **Parallélisables** : L'absence d'état partagé élimine les conditions de course.
-   **Composables** : Elles se combinent librement, sans effets inattendus.

La majorité des bugs provient d'états mutables partagés. Les fonctions pures éradiquent cette catégorie entière de problèmes.

```python
# Impure : modifie un état externe
total = 0
def add_to_total(x):
    global total
    total += x  # Effet de bord !
    return total

# Pure : aucun effet de bord
def add(a, b):
    return a + b
```

fptk vous aide à écrire du code pur en fournissant des outils pour gérer les aspects qui requièrent normalement de l'impureté, comme les erreurs, les valeurs absentes, l'état ou les effets de bord.

## Option : rendre l'absence de valeur explicite

Dans la plupart des langages, n'importe quelle valeur peut être `null` ou `None`, ce qui conduit à une programmation défensive :

```python
if user is not None:
    if user.profile is not None:
        if user.profile.name is not None:
            print(user.profile.name)
```

Le problème ne vient pas de `None` en soi, mais du fait que sa présence est *implicite*. N'importe quelle fonction peut renvoyer `None` sans que le système de types ne vous en alerte.

**Option** rend cette absence explicite. Une valeur est soit `Some(value)`, soit `Nothing` :

```python
from fptk.adt.option import Some, NOTHING, from_nullable

# Explicite : cette valeur pourrait être absente
maybe_name: Option[str] = from_nullable(get_name())

# Il faut donc gérer les deux cas
name = maybe_name.unwrap_or("Anonyme")
```

Toute sa puissance réside dans le **chaînage**. Au lieu de vérifications imbriquées pour `None` :

```python
# Sans Option
if user and user.get("profile") and user.get("profile").get("email"):
    email = user["profile"]["email"].lower()
else:
    email = None
```

Vous composez des transformations qui gèrent l'absence pour vous :

```python
# Avec Option
email = (
    from_nullable(user)
    .bind(lambda u: from_nullable(u.get("profile")))
    .bind(lambda p: from_nullable(p.get("email")))
    .map(str.lower)
)
```

Si une étape renvoie `Nothing`, le reste de la chaîne est simplement ignoré. Aucune vérification `None` n'est nécessaire.

### Point clé : map vs bind

-   `map(f)` transforme la valeur *contenue* dans l'Option : `Some(5).map(lambda x: x * 2)` → `Some(10)`.
-   `bind(f)` enchaîne des opérations qui peuvent échouer, c'est-à-dire quand la fonction `f` renvoie elle-même une `Option`.

```python
Some(5).map(lambda x: x * 2)           # Some(10) - f renvoie une valeur
Some(5).bind(lambda x: Some(x * 2))    # Some(10) - f renvoie une Option
Some(5).map(lambda x: Some(x * 2))     # Some(Some(10)) - incorrect !
```

## Result : les erreurs comme des valeurs

Le problème des exceptions, c'est qu'elles sont invisibles. En regardant la signature d'une fonction, impossible de dire si elle peut échouer :

```python
def parse_config(path: str) -> dict:  # Peut lever FileNotFoundError, JSONDecodeError...
    ...
```

Vous finissez par envelopper votre code de blocs `try/except` ou par découvrir les erreurs au moment de l'exécution.

**Result** rend les erreurs explicites. Une opération retourne soit `Ok(value)` en cas de succès, soit `Err(error)` en cas d'échec :

```python
from fptk.adt.result import Ok, Err, Result

def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"'{s}' n'est pas un entier valide")
```

Le type de retour `Result[int, str]` vous informe que la fonction renvoie un `int`, mais qu'elle peut échouer avec une erreur de type `str`.

Comme `Option`, `Result` supporte le chaînage :

```python
def process_input(raw: str) -> Result[int, str]:
    return (
        parse_int(raw)
        .map(lambda x: x * 2)
        .bind(validate_positive)
        .map(lambda x: x + 10)
    )
```

Si une étape échoue, l'erreur se propage automatiquement dans la chaîne. Fini les `try/except` imbriqués.

### Programmation orientée chemin de fer (Railway Oriented Programming)

Imaginez `Result` comme une voie ferrée à deux pistes :

```
         ┌─ Ok ──→ map ──→ bind ──→ Résultat Ok
Entrée ───┤
         └─ Err ─────────────────→ Résultat Err
```

Une fois sur la piste d'erreur, on y reste. C'est ce qu'on nomme la 'programmation orientée chemin de fer' (Railway Oriented Programming), un principe qui rend la gestion d'erreurs composable.

## Validation : accumuler les erreurs

Une gestion d'erreurs classique s'arrête à la première défaillance (fail-fast).

```python
def validate(data):
    if not data.get("email"):
        return Err("Email requis")  # S'arrête ici
    if not data.get("name"):
        return Err("Nom requis")   # Jamais atteint
    ...
```

Cependant, lors de la validation de données utilisateur, il est préférable d'afficher *toutes* les erreurs en une seule fois. `validate_all` se charge de les accumuler :

```python
from fptk.validate import validate_all
from fptk.adt.result import Ok, Err

result = validate_all([
    lambda d: Ok(d) if d.get("email") else Err("Email requis"),
    lambda d: Ok(d) if d.get("name") else Err("Nom requis"),
    lambda d: Ok(d) if len(d.get("password", "")) >= 8 else Err("Mot de passe trop court"),
], data)

# Err(NonEmptyList("Email requis", "Nom requis", "Mot de passe trop court"))
```

Il s'agit d'un exemple de style **applicatif**, où des calculs indépendants peuvent être combinés. Ce style se distingue du style **monadique** (`bind`), dans lequel chaque étape dépend du succès de la précédente.

## Composition : construire le complexe à partir du simple

L'objectif de la programmation fonctionnelle est de construire des comportements complexes en assemblant des briques de base simples et robustes.

**compose** assemble des fonctions :

```python
from fptk.core.func import compose

# f(g(x))
inc_then_double = compose(lambda x: x * 2, lambda x: x + 1)
inc_then_double(5)  # 12
```

**curry** vous permet de spécialiser des fonctions en appliquant partiellement leurs arguments :

```python
from fptk.core.func import curry

@curry
def send_email(to, subject, body):
    ...

# Créer des fonctions spécialisées
send_alert = send_email("alerts@company.com")("ALERTE")
send_alert("Le serveur est hors service !")
```

Ces outils vous permettent de construire votre application à partir de petites briques logicielles, réutilisables et testables.

## Quand utiliser fptk

**Idéal pour :**

- Pipelines de traitement de données
- Validation et parsing
- Gestion d'erreurs explicite et prévisible
- Code exigeant une haute testabilité
- Pour les équipes qui découvrent la programmation fonctionnelle

**Démarrez en douceur :**

Nul besoin de réécrire tout votre code. Commencez par :

1.  Essayez `pipe` sur une fonction complexe.
2.  Utilisez `Result` pour une opération qui peut échouer.
3.  Utilisez `Option` pour gérer une série d'accès pouvant retourner `None`.

Chacun de ces patrons apporte une valeur ajoutée immédiate et indépendante.

## Prochaines étapes

-   [Concepts fondamentaux](guide/core-concepts.md) — Un guide détaillé pour chaque patron
-   [Effets de bord](guide/side-effects.md) — Structurer une application autour d'un noyau pur
-   [Guide de migration](guide/migration.md) — Adopter progressivement fptk dans un code impératif
-   [Référence de l'API](reference/index.md) — Documentation complète avec les bases théoriques et des exemples