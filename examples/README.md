# 📂 Sample data

`pages/` holds **made-up** saved pages for the keyword "crm for small business":

| File | Role | Format |
|---|---|---|
| `your_page.html` | you | article |
| `pipelinehq.html`, `salesdeck.html`, `crmguide.html` | competitors | list posts |
| `closeflow.html` | competitor | how-to guide |

`competitors.txt` lists the four competitor files. All sites and text are fictional.

```bash
competitor-onpage-benchmark examples/pages/your_page.html --urls examples/competitors.txt -k "crm for small business"
```
