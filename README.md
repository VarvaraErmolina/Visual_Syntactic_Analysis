This repository is an appendix to the thesis "A Tool for Visual Analysis of Syntactic Structure Based on Corpus Data".

It contains:

* code for the tool for working with a corpus of syntactically annotated Russian texts (`Backend` and `Frontend` folders);
* JSON files used to build the charts discussed in the analytical chapter of the thesis, as well as a Jupyter notebook reproducing them in an interactive format (`Analysis` folder).

## Running the tool

In the project root, create a `.env` file with:

```env
DATABASE_URL=postgresql+psycopg://USERNAME:PASSWORD@HOST:5432/russian_authors
DB_SCHEMA=corpus
```

To run the project, open a terminal in the project root, where `docker-compose.yml` is located, and execute:

```bash
docker compose up --build
```

To stop the containers, run:

```bash
docker compose down
```
