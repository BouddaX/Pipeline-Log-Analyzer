# Pipeline Log Analyzer

## Présentation

Ce projet lit des journaux d’authentification SSH, extrait les tentatives de connexion, enregistre les résultats dans PostgreSQL et affiche trois indicateurs dans un dashboard :

- le nombre de tentatives échouées par pays ;
- le nombre de tentatives réussies par utilisateur ;
- le nombre de tentatives échouées avec un utilisateur invalide.

Le code est organisé en modules afin de séparer la lecture, l’extraction, le stockage et l’affichage.

## Technologies utilisées

- Python 3.14 ou plus récent ;
- PostgreSQL ;
- `psycopg2-binary` pour la connexion Python à PostgreSQL ;
- `matplotlib` pour générer les graphiques ;
- `re` de la bibliothèque standard Python pour reconnaître les lignes SSH.

## Organisation du projet

```text
.
├── data/                         # Journaux SSH à analyser
├── ingestion/read.py             # Lecture des fichiers texte et gzip
├── processing/extract_transform.py # Extraction des tentatives avec re
├── storage.py                    # Connexion, insertion et requêtes PostgreSQL
├── schema.sql                    # Tables et index PostgreSQL
├── dashboard.py                  # Graphiques PNG du dashboard
├── main.py                       # Lancement du pipeline
└── reports/                      # Dashboard généré
```

## Préparation de PostgreSQL

1. Démarrer le serveur PostgreSQL.
2. Créer la base :

   ```sh
   createdb log_analysis
   ```

   Si `createdb` n’est pas disponible, créer une base nommée `log_analysis` avec l’outil PostgreSQL installé dans votre cours.

3. Définir les paramètres de connexion dans le terminal. Les valeurs par défaut sont `localhost`, port `5432`, base `log_analysis`, utilisateur `boudda` et mot de passe vide. Si votre rôle a un mot de passe, renseignez `PGPASSWORD`.

   ```sh
   export PGHOST=localhost
   export PGPORT=5432
   export PGDATABASE=log_analysis
   export PGUSER=postgres
   export PGPASSWORD='votre_mot_de_passe'
   ```

   Vous pouvez aussi fournir une chaîne de connexion complète dans `LOG_DATABASE_URL`. Ne mettez pas de vrai mot de passe dans Git.

4. Le programme exécute `schema.sql` au démarrage et crée les tables si elles n’existent pas.

## Pays associés aux adresses IP

Les journaux SSH contiennent l’adresse IP, mais pas le pays. Le projet utilise donc la table `ip_country_map` dans PostgreSQL. Ajoutez les correspondances connues avant l’analyse, par exemple :

```sql
INSERT INTO ip_country_map (ip_address, country)
VALUES ('203.0.113.10', 'France')
ON CONFLICT (ip_address) DO UPDATE SET country = EXCLUDED.country;
```

Remplacez l’adresse d’exemple par une adresse réelle de vos données. Les IP sans correspondance sont comptées dans le pays `Unknown`. Les données des plages réservées ou privées n’ont généralement pas de pays public.

## Installation et exécution

Depuis la racine du projet, installer les dépendances déclarées :

```sh
uv sync
```

Placer les fichiers de journaux SSH (texte ou `.gz`) dans `data/`, configurer les variables PostgreSQL, puis lancer :

```sh
python main.py
```

Le programme lit les fichiers, reconnaît les lignes d’authentification SSH, enregistre les tentatives dans PostgreSQL et affiche les agrégations. Les lignes répétées identiques ne créent pas de doublons. Si vous ajoutez ensuite une correspondance IP/pays, relancez le programme pour actualiser le pays de ces tentatives.

Le dashboard est créé dans `reports/dashboard.png`. Ouvrir l’image dans un navigateur ou un visionneur d’images.

## Données enregistrées

`authentication_attempts` contient la date partielle du journal, l’heure, l’utilisateur, l’adresse IP, le pays, le statut (`Accepted` ou `Failed`), la méthode, l’indicateur d’utilisateur invalide et le nombre d’occurrences. `event_key` évite de réinsérer une ligne identique à chaque lancement.

Les dates SSH syslog n’incluent pas toujours l’année ; le projet stocke donc le mois, le jour et l’heure disponibles au lieu d’inventer une année.

## Erreurs et journaux de l’application

Les erreurs d’ingestion, d’extraction, d’accès PostgreSQL et de création du dashboard sont journalisées dans `app.log` avec la date, le niveau et le nom du module. En cas d’échec du pipeline, consulter ce fichier ainsi que le message affiché dans le terminal.

## Limites

- Le pays dépend des correspondances présentes dans `ip_country_map` ; aucune géolocalisation externe n’est appelée.
- Les lignes qui ne correspondent pas au format SSH reconnu sont ignorées.
- Les journaux sont traités depuis le dossier `data/` à la racine du projet.
