# Fonctions de base

Le module `fptk.core.func` propose un ensemble de combinateurs de fonctions : de petits utilitaires conçus pour vous aider à assembler, transformer et orchestrer vos fonctions. Ils constituent le socle de la programmation fonctionnelle en Python avec fptk.

## Concept : Les combinateurs de fonctions

En programmation fonctionnelle, les fonctions sont traitées comme des valeurs à part entière. Tout comme vous manipulez des entiers, vous pouvez transmettre des fonctions à d'autres fonctions ou en produire de nouvelles dynamiquement. Les **combinateurs** sont des fonctions d'ordre supérieur dédiées à cette manipulation.

Leur usage permet de favoriser :

-   **La composition plutôt que l'héritage** : bâtissez des comportements riches en assemblant des briques simples.
-   **Le style « point-free »** : exprimez vos transformations sans avoir à nommer explicitement chaque donnée intermédiaire.
-   **La réutilisabilité** : vos petites fonctions deviennent des composants versatiles pour de multiples pipelines.

---

## `pipe`

Cette fonction fait circuler une valeur à travers une suite de fonctions, en suivant l'ordre de lecture (de gauche à droite).

```python
from fptk.core.func import pipe

def pipe(x, *funcs):
    """Fait transiter une valeur à travers une série de fonctions unaires."""
```

### Pourquoi utiliser `pipe` ?

Les appels de fonctions imbriqués sont notoirement difficiles à lire car ils se déchiffrent de l'intérieur vers l'extérieur :

```python
# Ordre d'exécution réel : f -> g -> h
resultat = h(g(f(x)))
```

`pipe` rétablit un flux de données linéaire et intuitif :

```python
# Flux limpide : analyse -> validation -> formatage
resultat = pipe(donnees_brutes, analyse, validation, formatage)
```

### Exemples d'utilisation

```python
from fptk.core.func import pipe

# Chaîne de transformation classique
resultat = pipe(
    "  bonjour le monde  ",
    str.strip,
    str.upper,
    lambda s: s.replace(" ", "_")
)
# resultat = "BONJOUR_LE_MONDE"

# Avec Option pour un chaînage sécurisé
from fptk.adt.option import from_nullable

nom = pipe(
    dictionnaire_utilisateur,
    lambda d: from_nullable(d.get("profile")),
    lambda opt: opt.bind(lambda p: from_nullable(p.get("name"))),
    lambda opt: opt.map(str.upper),
    lambda opt: opt.unwrap_or("Anonyme")
)
```

---

## `compose`

Cette fonction assemble deux fonctions pour en créer une nouvelle : `(f ∘ g)(x) = f(g(x))`.

```python
from fptk.core.func import compose

def compose(f, g):
    """Compose deux fonctions unaires : f(g(x))."""
```

### Pourquoi utiliser `compose` ?

Contrairement à `pipe` qui s'applique immédiatement à une valeur, `compose` définit un pipeline réutilisable sous la forme d'une nouvelle fonction.

```python
# Création d'une transformation réutilisable
normaliser = compose(str.upper, str.strip)

# Application ultérieure
normaliser("  bonjour  ")  # "BONJOUR"
normaliser("  monde  ")    # "MONDE"
```

Note : l'ordre d'application est l'inverse de celui de `pipe` (application de `g` puis de `f`).

---

## `curry`

Cette fonction transforme une fonction acceptant N arguments en une suite de N fonctions acceptant chacune un seul argument.

```python
from fptk.core.func import curry

def curry(fn):
    """Applique la curryfication à une fonction de N arguments positionnels."""
```

### Pourquoi utiliser `curry` ?

La curryfication facilite l'**application partielle**, vous permettant de fournir certains paramètres immédiatement et de différer les autres.

```python
# Sans curryfication : usage obligatoire d'une lambda
list(map(lambda x: ajouter(1, x), [1, 2, 3]))

# Avec curryfication : syntaxe épurée
ajouter = curry(lambda a, b: a + b)
list(map(ajouter(1), [1, 2, 3]))  # [2, 3, 4]
```

---

## `flip`

Permute l'ordre des deux premiers arguments d'une fonction binaire.

```python
from fptk.core.func import flip

def flip(fn):
    """Échange les deux premiers arguments."""
```

### Pourquoi utiliser `flip` ?

Il arrive que l'ordre des arguments d'une fonction existante ne soit pas adapté à votre besoin, notamment lors d'un `map` :

```python
# pow(base, exp) - on veut mapper sur les bases avec un exposant fixe
list(map(lambda x: pow(x, 2), [1, 2, 3]))

# Avec flip
au_carre = flip(pow)(2)  # flip transforme pow(base, exp) en pow(exp, base)
list(map(au_carre, [1, 2, 3]))  # [1, 4, 9]
```

---

## `tap`

Déclenche un effet de bord sur une valeur sans modifier celle-ci, en la retournant telle quelle.

```python
from fptk.core.func import tap

def tap(f):
    """Exécute un effet de bord et renvoie l'entrée inchangée."""
```

### Pourquoi utiliser `tap` ?

C'est l'outil idéal pour déboguer un pipeline sans en altérer le flux :

```python
resultat = pipe(
    donnees,
    analyse,
    tap(print),  # Inspecte les données analysées
    validation,
    tap(lambda x: logger.debug(f"Validé : {x}")),
    transformation
)
```

---

## `thunk`

Définit un calcul paresseux (lazy) dont le résultat est mis en cache (mémoïsé) lors de sa première exécution.

```python
from fptk.core.func import thunk

def thunk(f):
    """Fonction sans argument mémoïsée (valeur paresseuse)."""
```

### Pourquoi utiliser `thunk` ?

Pour différer un calcul coûteux jusqu'à ce qu'il soit réellement nécessaire, tout en s'assurant qu'il ne sera effectué qu'une seule fois.

```python
config_lourde = thunk(lambda: charger_config_du_disque())

# La configuration n'est pas encore chargée...

res1 = config_lourde()  # Chargement effectif ici
res2 = config_lourde()  # Récupère la valeur en cache
```

---

## `identity`

Renvoie simplement l'entrée qu'elle a reçue, sans aucune modification.

```python
from fptk.core.func import identity

def identity(x):
    """Renvoie x tel quel."""
```

### Pourquoi utiliser `identity` ?

Elle sert de fonction par défaut ou de substitut (placeholder) dans les contextes de fonctions d'ordre supérieur.

```python
# Transformation par défaut
transformation = obtenir_transfo() or identity

# Dans un Option.match
valeur = mon_option.match(
    some=identity,  # Renvoie directement la valeur contenue
    none=lambda: "valeur_par_defaut"
)
```

---

## `const`

Crée une fonction qui ignore systématiquement ses arguments pour renvoyer une valeur fixe prédéfinie.

```python
from fptk.core.func import const

def const(x):
    """Renvoie une fonction qui retourne toujours x."""
```

### Pourquoi utiliser `const` ?

Pratique lorsqu'une API exige une fonction alors que vous souhaitez simplement fournir une valeur constante.

```python
# Renvoie toujours 0 pour les clés manquantes
fabrique_par_defaut = const(0)

# Dans un Result.unwrap_or_else
resultat.unwrap_or_else(const("valeur_par_defaut"))
```

---

## `once`

Encapsule une fonction pour garantir qu'elle ne s'exécutera qu'une seule fois. Les appels ultérieurs renverront le résultat du premier appel.

```python
from fptk.core.func import once

def once(fn):
    """Exécute au plus une fois et mémoïse le premier résultat."""
```

### Pourquoi utiliser `once` ?

Pour sécuriser un code d'initialisation devant être unique :

```python
init_db = once(lambda: creer_connexion_db())

# Premier appel : connexion établie
init_db()

# Appels suivants : renvoie la même connexion existante
init_db()
```

---

## `try_catch`

Transforme une fonction susceptible de lever des exceptions en une fonction retournant un objet `Result`.

```python
from fptk.core.func import try_catch

def try_catch(fn):
    """Encapsule fn pour renvoyer Ok/Err au lieu de lever une exception."""
```

### Pourquoi utiliser `try_catch` ?

Pour faire le pont entre du code impératif classique (basé sur les exceptions) et des pipelines fonctionnels (basés sur `Result`).

```python
import json
# json.loads lève une exception sur un JSON invalide
# safe_parse renvoie un Result (Ok ou Err)
safe_parse = try_catch(json.loads)

safe_parse("invalide")  # Err(JSONDecodeError(...))
safe_parse('{"a": 1}')  # Ok({"a": 1})
```

---

## `async_pipe`

Version asynchrone de `pipe`, capable de gérer indifféremment des fonctions synchrones et asynchrones.

```python
from fptk.core.func import async_pipe

async def async_pipe(x, *funcs):
    """Fait circuler une valeur à travers des fonctions potentiellement asynchrones."""
```

Elle vérifie si le résultat de chaque étape est « awaitable » et, si c'est le cas, l'attend (`await`) avant de passer à la fonction suivante.

---

## `foldl`

Repli à gauche (left fold) : réduit une collection de gauche à droite avec un accumulateur.

```python
from fptk.core.func import foldl

def foldl(f, init, xs):
    """Repli à gauche : f(f(f(init, x1), x2), x3)"""
```

### Pourquoi utiliser `foldl` ?

`foldl` est l'opération fondamentale pour réduire des collections. De nombreuses opérations courantes (somme, produit, max, min) sont des replis :

```python
# La somme est un repli
foldl(lambda acc, x: acc + x, 0, [1, 2, 3])  # 6

# Le produit est un repli
foldl(lambda acc, x: acc * x, 1, [1, 2, 3])  # 6
```

### Exemples

```python
from fptk.core.func import foldl

# Somme
foldl(lambda acc, x: acc + x, 0, [1, 2, 3])  # 6

# Soustraction (associative à gauche) : ((10-1)-2)-3 = 4
foldl(lambda acc, x: acc - x, 10, [1, 2, 3])  # 4

# Construction de chaîne de gauche à droite
foldl(lambda acc, x: f"{acc}-{x}", "debut", ["a", "b", "c"])
# "debut-a-b-c"

# Aplatir des listes imbriquées
foldl(lambda acc, x: acc + x, [], [[1, 2], [3], [4, 5]])
# [1, 2, 3, 4, 5]
```

---

## `foldr`

Repli à droite (right fold) : réduit une collection de droite à gauche avec un accumulateur.

```python
from fptk.core.func import foldr

def foldr(f, init, xs):
    """Repli à droite : f(x1, f(x2, f(x3, init)))"""
```

### Pourquoi utiliser `foldr` ?

Certaines opérations sont naturellement associatives à droite. `foldr` préserve cette structure :

```python
# Construction d'une liste chaînée (de droite à gauche)
foldr(lambda x, acc: (x, acc), None, [1, 2, 3])
# (1, (2, (3, None)))
```

### Exemples

```python
from fptk.core.func import foldr

# Construction de chaîne de droite à gauche
foldr(lambda x, acc: f"{x}-{acc}", "fin", ["a", "b", "c"])
# "a-b-c-fin"

# Construction de structure imbriquée
foldr(lambda x, acc: {"valeur": x, "suivant": acc}, None, [1, 2, 3])
# {"valeur": 1, "suivant": {"valeur": 2, "suivant": {"valeur": 3, "suivant": None}}}
```

---

## `reduce`

Réduction sans valeur initiale, retournant un `Option`.

```python
from fptk.core.func import reduce

def reduce(f, xs):
    """Réduit sans init, retourne Option."""
```

### Pourquoi utiliser `reduce` ?

Parfois la valeur initiale devrait provenir de la collection elle-même. Le `functools.reduce` de Python lève une exception sur les collections vides. Le `reduce` de fptk retourne un `Option` pour plus de sécurité :

```python
from fptk.core.func import reduce

reduce(max, [1, 5, 3])  # Some(5)
reduce(max, [])          # NOTHING (pas d'exception !)
```

### Exemples

```python
from fptk.core.func import reduce
from fptk.adt.option import NOTHING

# Trouver le maximum
reduce(max, [1, 5, 3])  # Some(5)

# Somme
reduce(lambda a, b: a + b, [1, 2, 3])  # Some(6)

# Collection vide
reduce(max, [])  # NOTHING

# Un seul élément
reduce(max, [42])  # Some(42)

# Extraction sécurisée
resultat = reduce(max, scores_utilisateurs)
if resultat.is_some():
    print(f"Score le plus élevé : {resultat.unwrap()}")
else:
    print("Aucun score enregistré")
```