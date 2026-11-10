# flixtrain-mcp 🚆

mcp-name: io.github.mohammad-abbasi-sh/flixtrain-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **[global.api.flixbus.com (FlixBus shop search API)](https://shop.flixbus.com)** — زمان‌بندی و قیمت فلیکس‌ترین از API جست‌وجوی فروشگاه فلیکس‌بوس (رایگان، بدون کلید): فقط سفرهای قطار بین شهرهای آلمان، با ایستگاه‌ها، مدت سفر، قیمت و صندلی‌های موجود. بدون کلید، بدون ورود.

> ساختهٔ محمد عباسی، بخشی از «کارخانهٔ MCP آلمان». وابسته به global.api.flixbus.com (FlixBus shop search API) نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی MCP کلاینت اضافه کنید (stdio):

```json
{
  "mcpServers": {
    "flixtrain": {
      "command": "uvx",
      "args": ["flixtrain-mcp==0.1.0"]
    }
  }
}
```

یا به‌صورت محلی اجرا کنید: `python -m flixtrain_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `flixtrain_search_trains` | جست‌وجوی سفرهای فلیکس‌ترین بین دو شهر |
| `flixtrain_search_cities` | یافتن شهرها بر اساس نام |
| `flixtrain_health` | بررسی دسترس‌پذیری (ok / blocked / error) — یک درخواست مؤدبانه |

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## لایسنس

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
