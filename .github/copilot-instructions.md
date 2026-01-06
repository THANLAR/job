# Copilot Instructions

## Project Overview

GitHub Actions cron job to keep Hugging Face Space alive by pinging it every 3 hours.

**Target Space**: https://huggingface.co/spaces/aungyezaw/thanlar

## Architecture

```
job/
├── .github/
│   ├── workflows/
│   │   └── keep-alive.yml    # Cron job (every 3 hours)
│   └── copilot-instructions.md
├── .gitignore
├── LICENSE
└── README.md
```

## Secrets

| Secret Name | Purpose |
|-------------|---------|
| `HUGGING_FACE_JOB` | Hugging Face access token for API authentication |

## Workflow Details

- **Schedule**: `0 */3 * * *` (every 3 hours at minute 0)
- **Manual trigger**: Supported via `workflow_dispatch`
- **Action**: Clones the HF Space repo, updates `README_HF.md` with timestamp and count, then pushes to trigger rebuild

## How It Works

1. Clones `https://huggingface.co/spaces/aungyezaw/thanlar`
2. Updates `README_HF.md` with:
   - Current UTC timestamp
   - Incremental keep-alive count
3. Commits and pushes changes to Hugging Face
4. The push triggers a Space rebuild, keeping it active

## Modifying the Cron Schedule

Edit `.github/workflows/keep-alive.yml` cron expression:
- `0 */3 * * *` = every 3 hours
- `0 */6 * * *` = every 6 hours
- `0 0 * * *` = once daily at midnight UTC
