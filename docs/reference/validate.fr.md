# Validation

Le module `fptk.validate` propose une approche de validation dite « applicative » : elle permet d'exécuter plusieurs vérifications successives et d'accumuler l'ensemble des erreurs rencontrées, au lieu de s'interrompre dès le premier échec.

## Concept : La validation applicative

Contrairement à la composition monadique classique (via `bind`) qui s'arrête à la première erreur (stratégie **fail-fast**), la validation applicative vise à **collecter l'intégralité des anomalies**. C'est une méthode particulièrement adaptée aux interfaces utilisateurs, car elle permet de signaler tout ce qui ne va pas en une seule fois.

```
Monadique (fail-fast)  : test1 → Échec → Fin du traitement.
Applicatif (accumulation) : test1 → Échec, test2 → Échec, test3 → Succès → Erreur([e1, e2]).
```

Cette approche est capitale pour :

-   **Une meilleure expérience utilisateur (UX)** : affichez toutes les erreurs de validation simultanément.
-   **Un retour complet** : permettez aux utilisateurs de corriger l'ensemble des problèmes en un seul passage.
-   **Une séparation nette** : chaque règle de validation demeure indépendante, testable et réutilisable.

### Le problème : la validation « fail-fast » frustrante

```python
def valider_utilisateur(data: dict) -> Result[User, str]:
    return (
        verifier_nom(data)
        .bind(lambda _: verifier_email(data))
        .bind(lambda _: verifier_age(data))
        .map(lambda _: User(**data))
    )

# Si le nom est invalide, l'utilisateur ne verra jamais les erreurs sur l'email ou l'âge.
resultat = valider_utilisateur({"nom": "", "email": "erroné", "age": -5})
# Err("Le nom est obligatoire") — mais l'email et l'âge sont aussi incorrects !
```

### La solution : `validate_all`

```python
from fptk.validate import validate_all

def valider_utilisateur(data: dict) -> Result[User, NonEmptyList[str]]:
    return validate_all(
        [verifier_nom, verifier_email, verifier_age],
        data
    ).map(lambda d: User(**d))

resultat = valider_utilisateur({"nom": "", "email": "erroné", "age": -5})
# Err(NonEmptyList("Le nom est obligatoire", "Email invalide", "L'âge doit être positif"))
```

Tous les tests sont effectués, et toutes les erreurs sont dûment collectées.

## API

### Fonction principale

```python
from fptk.validate import validate_all

def validate_all(
    checks: Iterable[Callable[[T], Result[T, E]]],
    value: T
) -> Result[T, NonEmptyList[E]]
```

**Paramètres :**

-   `checks` : un itérable de fonctions de validation. Chaque fonction prend la valeur en entrée et renvoie un `Result[T, E]`.
-   `value` : la donnée à valider.

**Valeur de retour :**

-   `Ok(value)` si l'ensemble des vérifications a réussi.
-   `Err(NonEmptyList[E])` contenant la liste exhaustive des erreurs en cas d'échec.

## Fonctionnement technique

### Principes clés

1.  **Exécution exhaustive** : contrairement à `bind`, nous ne nous arrêtons pas avant d'avoir parcouru l'intégralité des tests.
2.  **Accumulation structurée** : les erreurs sont regroupées dans une [`NonEmptyList`](nelist.md).
3.  **Transformation au fil de l'eau** : si un test renvoie une version transformée de la donnée (ex: `Ok(email_normalise)`), les tests suivants travailleront sur cette nouvelle version.
4.  **Garantie de non-vacuité** : si la fonction renvoie un `Err`, celui-ci contient obligatoirement au moins une erreur.

## Exemples d'utilisation

### Validation complète d'un formulaire

```python
# Définition des validateurs
def est_requis(champ: str):
    return lambda d: Ok(d) if d.get(champ) else Err(f"Le champ {champ} est obligatoire")

def format_email(champ: str):
    def test(d):
        email = d.get(champ, "")
        return Ok(d) if "@" in email else Err(f"Format d'email invalide pour {champ}")
    return test

# Utilisation combinée
def valider_inscription(formulaire: dict):
    return validate_all([
        est_requis("pseudo"),
        est_requis("email"),
        format_email("email"),
        lambda d: Ok(d) if len(d.get("pseudo", "")) >= 3 else Err("Pseudo trop court")
    ], formulaire)
```

### Transformation lors de la validation

Les validateurs peuvent également nettoyer les données avant qu'elles n'atteignent les tests suivants :

```python
def normaliser_email(data: dict) -> Result[dict, str]:
    """Passe l'email en minuscules et retire les espaces superflus."""
    if "email" in data:
        data["email"] = data["email"].lower().strip()
    return Ok(data)

resultat = validate_all([
    normaliser_email,  # La donnée est nettoyée d'abord
    est_requis("email"),
    format_email("email") # Le test s'effectue sur l'email nettoyé
], mon_formulaire)
```

## `validate_all` vs `traverse_result` : que choisir ?

| Caractéristique | `traverse_result` | `validate_all` |
| :--- | :--- | :--- |
| **Comportement** | S'arrête dès la première erreur (fail-fast). | Parcourt tout et accumule (accumulate). |
| **Type de retour** | `Result[list[T], E]` | `Result[T, NonEmptyList[E]]` |
| **Cas d'usage** | Logique technique interne. | Saisie de données par un utilisateur. |

## Voir aussi

-   [`Result`](result.md) — Le type de base gérant les succès et les échecs.
-   [`NonEmptyList`](nelist.md) — La structure utilisée pour regrouper les erreurs.
-   [`traverse_result`](traverse.md) — Pour un traitement de collection avec arrêt immédiat.
-   [Développement d'API](../recipes/api-development.md) — Exemples concrets dans des points d'entrée web.