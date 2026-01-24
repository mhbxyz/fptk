<p align="center">
  <img src="../assets/fptk-logo.svg" alt="fptk — Functional Programming Toolkit" width="450">
</p>

<p align="center">
  <strong>Une approche pragmatique de la programmation fonctionnelle en Python 3.13+</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/fptk/">PyPI</a> ·
  <a href="https://github.com/mhbxyz/fptk">GitHub</a> ·
  <a href="getting-started.fr.md">Démarrage Rapide</a>
</p>

---

## Qu'est-ce que la programmation fonctionnelle ?

La programmation fonctionnelle est un paradigme qui consiste à construire des programmes en assemblant des **fonctions pures**. C'est-à-dire des fonctions qui, pour une même entrée, produisent toujours la même sortie, sans modifier d'état extérieur (effets de bord).

Bien que cela puisse paraître abstrait, cette approche résout des problèmes très concrets :

-   **Les bugs liés à l'état partagé** : Lorsque plusieurs parties de votre code modifient les mêmes données, la recherche de bugs peut virer au cauchemar. Les fonctions pures n'ayant pas d'effets de bord, ce problème est éliminé à la racine.
-   **La difficulté à tester le code** : Les fonctions avec des effets de bord (appels à une base de données, requêtes API, entrées/sorties de fichiers) exigent des mocks complexes pour leurs tests. À l'inverse, les fonctions pures se contentent d'entrées et de sorties attendues.
-   **La complexité du code** : Quand une fonction peut potentiellement tout faire (modifier des variables globales, appeler des API, écrire dans des fichiers), il faut lire toute son implémentation pour comprendre son comportement. Les fonctions pures sont, par nature, prévisibles.

La programmation fonctionnelle ne se résume pas à l'utilisation d'abstractions complexes. Il s'agit avant tout d'écrire du code plus simple à comprendre, à tester et à maintenir.

## Pourquoi fptk ?

Python est un langage formidable, mais il présente quelques points faibles que les patrons fonctionnels corrigent avec élégance :

### Le problème de `None`

```python
user = get_user(id)
name = user.get("profile").get("name").upper()  # AttributeError
```

`None` a tendance à se propager silencieusement dans le code jusqu'à ce qu'une erreur survienne. On se retrouve alors à écrire du code défensif à tout bout de champ :

```python
user = get_user(id)
if user and user.get("profile") and user.get("profile").get("name"):
    name = user["profile"]["name"].upper()
else:
    name = "Anonymous"
```

L'`Option` de fptk rend l'absence de valeur à la fois explicite et composable :

```python
name = (
    from_nullable(get_user(id))
    .bind(lambda u: from_nullable(u.get("profile")))
    .bind(lambda p: from_nullable(p.get("name")))
    .map(str.upper)
    .unwrap_or("Anonymous")
)
```

### Le problème des exceptions

Les exceptions sont invisibles. Rien dans la signature d'une fonction ne les indique. Lorsque vous appelez `parse_json(data)`, rien ne vous dit qu'elle peut lever `JSONDecodeError`, `UnicodeDecodeError` ou `MemoryError`. Vous finissez par envelopper vos appels dans des blocs `try/except`, ou par croiser les doigts.

`Result` de fptk intègre la possibilité d'échec directement dans le type de retour :

```python
def parse_json(data: str) -> Result[dict, str]:
    ...

# Le type de retour vous alerte : cette fonction peut échouer, gérez-le.
```

### Le problème des appels de fonctions imbriqués

Dans la pratique, le code ressemble souvent à ceci :

```python
send_email(format_message(validate(parse(request))))
```

Il se lit de l'intérieur vers l'extérieur, et ajouter une étape oblige à trouver le bon niveau d'imbrication. `pipe` de fptk linéarise le flux de données :

```python
pipe(request, parse, validate, format_message, send_email)
```

## L'état d'esprit fonctionnel

La programmation fonctionnelle vous invite à penser différemment :

| Pensée impérative | Pensée fonctionnelle |
|-------------------|----------------------|
| "Fais ceci, puis fais cela" | "Transforme ces données en cela" |
| Modifier des données existantes | Créer de nouvelles données à partir des anciennes |
| Gérer les erreurs avec `try/catch` | Intégrer l'échec au type de retour |
| Tester la présence de `None` partout | Rendre l'absence de valeur explicite avec `Option` |
| Des fonctions qui peuvent tout faire | Des fonctions qui ne font que calculer une sortie à partir d'une entrée |

Ce changement de perspective demande de la pratique, mais les bénéfices — un code plus prévisible, testable et composable — en valent la peine.

## Ce que fptk fournit

| Fonctionnalité | Ce qu'elle résout |
|----------------|-------------------|
| `pipe`, `compose` | Appels de fonctions imbriqués et flux de données peu lisible |
| `Option` | Erreurs liées à `None` (`AttributeError`) et code défensif |
| `Result` | Exceptions implicites et gestion d'erreurs éparpillée |
| `validate_all` | Validation qui s'arrête à la première erreur et retours utilisateurs peu informatifs |
| `Reader` | Injection de dépendances et transmission de configuration |
| `State` | Gestion de l'état mutable et code difficile à tester |
| `Writer` | Journalisation (logging) mêlée à la logique métier |

## Installation

```bash
pip install fptk
```

## Prochaines étapes

-   [Démarrage Rapide](getting-started.fr.md) — Comprendre les concepts et commencer à utiliser fptk
-   **Guide**
    -   [Concepts fondamentaux](guide/core-concepts.md) — Une plongée détaillée dans chaque patron
    -   [Effets de bord](guide/side-effects.md) — Structurer son application autour d'un noyau pur
    -   [Migration](guide/migration.md) — Adopter progressivement fptk dans un code impératif
-   **Exemples**
    -   [Développement d'API](examples/api-development.md) — Construire des API web robustes
    -   [Traitement de données](examples/data-processing.md) — Pipelines ETL et transformations de données
-   [Référence de l'API](reference/index.md) — Documentation complète avec les bases théoriques et des exemples