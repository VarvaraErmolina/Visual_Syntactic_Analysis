This repository is an Appendix to the thesis "A tool for visual analysis of syntactic structure based on corpus data".

It contains:
- code for the tool for working with a corpus of syntactically annotated Russian texts (folders *Backend* and *Frontend*)
- JSON files used to build the charts discussed in the analytical chapter of the thesis and the Jupyter notebook notebook reproducing them in an interactive format (folder *Analysis*)

**Implementing the tool**
In the project root, create `.env` with:

```DATABASE_URL=postgresql+psycopg://postgres:YOUR_PASSWORD@YOUR_SERVER_IP:5432/russian_authors```

In the `Frontend` folder, create `.env` with:

```VITE_API_BASE_URL=http://YOUR_SERVER_IP:8000```

To run the project, open a terminal in the project root (where `docker-compose.yml` is located) and execute:

```docker compose up --build```

To stop the containers, run:

```docker compose down```
