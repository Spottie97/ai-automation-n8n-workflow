# KB admin — user guide

This guide is for **operators** using the Streamlit **Knowledge base admin** app. Technical setup (install, `.env`, security) is in [kb-admin.md](kb-admin.md).

---

## What this app does

| Tab | Purpose |
|-----|---------|
| **Collections** | See all Qdrant collections, point counts, and vector size. |
| **Ingest** | Add or update knowledge for a **client** (one Qdrant collection per client). |
| **Search** | Try a question and see what chunks would be retrieved (same as the CLI search). |
| **Delete collection** | Remove an entire collection permanently. |

Ingest behavior matches **`scripts/ingest.py`**: text is chunked, sent to **Ollama** for embeddings, stored in **Qdrant**. The same **client id** must be used in **n8n** as `CLIENT_ID`.

---

## Before you start

1. **`.env`** in the project root must contain correct `OLLAMA_HOST`, `OLLAMA_EMBED_MODEL`, `QDRANT_URL`, and optional `QDRANT_API_KEY`.
2. Start the app from the repo root:

   ```bash
   source .venv/bin/activate
   streamlit run apps/kb_admin/app.py
   ```

3. If **KB_ADMIN_PASSWORD** is set in `.env`, the first screen asks for that password. Use a strong value if the app is reachable on a network.

4. Use **Test connections** in the sidebar to confirm Ollama, Qdrant, and llama-server (optional) respond.

---

## Client ID and collection names

- **Client ID** is what you type in the app (e.g. `demo_client`, `harborview`).
- Qdrant stores data in a **sanitized** name (lowercase, special characters → `_`). The app shows the **preview** collection name under the Client ID field.
- **n8n** should use the **same** logical client id in `CLIENT_ID` as you use here—not the n8n workflow name.

---

## Ingest tab: plain text (.txt or paste)

Best for:

- Pasting a FAQ or policy from Google Docs, Notion, or email (as ordinary text).
- Long markdown documents.

**Steps**

1. Enter **Client ID** (e.g. `demo_client`).
2. Choose **Payload source label** (`faq`, `website`, or `manual`)—stored on each chunk for your own filtering later.
3. Adjust **Chunk size** and **Chunk overlap** if needed (defaults match the CLI).
4. Either:
   - **Upload** a `.txt` file, or  
   - **Paste** UTF-8 text in the text area.
5. Click **Run ingest**.
6. Wait for the success message (number of points upserted). Large documents may take a minute.

**Note:** Re-ingesting the **same** client with **updated** content **reuses** stable point IDs where chunk text matches; content changes create new or updated points.

---

## Ingest tab: JSON (.json upload or paste)

JSON is useful when you have **structured** exports: CMS JSON, FAQ arrays, multiple small articles, or tools that emit one file with many entries.

The app **flattens** JSON into one long text document, then runs the **same** chunking and embedding pipeline as plain text. You can **upload** a `.json` file or **paste** JSON in the text area (must start with `[` or `{` to be detected as JSON).

### Supported shapes (examples)

**1. Single string**

```json
"Weekly hours: Mon–Fri 9–5."
```

**2. Array of strings** (each block separated before chunking)

```json
[
  "Section about returns…",
  "Section about shipping…"
]
```

**3. Array of FAQ objects** (`question` + `answer`, or `q` / `a`, or `title` + body-style fields)

```json
[
  {
    "question": "Do you allow dogs?",
    "answer": "Yes, on the patio on a leash."
  }
]
```

**4. Wrapper objects** — the app looks for these array keys (first match wins):

`chunks`, `items`, `documents`, `entries`, `faqs`, `pages`, `articles`

```json
{
  "faqs": [
    { "question": "Hours?", "answer": "7am–6pm weekdays." }
  ]
}
```

**5. Objects with text fields**

Per item, the app looks for: `text`, `content`, `body`, or `markdown`.

```json
[
  { "title": "Shipping", "body": "We ship within 3 days." }
]
```

If JSON is invalid or no text can be extracted, the app shows a clear error.

**When to prefer text vs JSON**

| Use plain text | Use JSON |
|----------------|----------|
| One continuous FAQ or policy | Multiple Q&A pairs or records from an export |
| Copy-paste from a doc | API/CMS gives you structured JSON |
| You are not typing brackets | You want one file per “catalog” of snippets |

---

## Search tab

1. Enter the **same Client ID** you ingested into.
2. Type a natural **Query** (what a customer might ask).
3. Set **Limit** (how many chunks to show).
4. Click **Search**.

Results show **scores** and chunk text—use this to check whether the KB answers common questions before turning on n8n auto-replies.

---

## Delete collection tab

1. Choose the **Collection** name from the list.
2. Type exactly **DELETE** (all caps) in the confirmation box.
3. Click **Delete collection**.

This cannot be undone. You will need to **re-ingest** to restore data.

---

## Troubleshooting (quick)

- **Empty list** on Collections: Qdrant URL wrong, or services down—use **Test connections** and [n8n-troubleshooting.md](n8n-troubleshooting.md).
- **Ingest errors** on embeddings: Ollama model name mismatch—check `OLLAMA_EMBED_MODEL` matches a model pulled on the server (`ollama pull …`).
- **Wrong answers in production**: fix the KB here first, then re-test **Search**; n8n uses the same collection.

---

## Related docs

- [kb-admin.md](kb-admin.md) — install, env vars, LAN security
- [n8n-runbook-import-test.md](n8n-runbook-import-test.md) — testing workflows after ingest
- [n8n-email-mvp-build.md](n8n-email-mvp-build.md) — automation overview
