**Turn any website into clean, AI-ready data.**

A Model Context Protocol (MCP) server that exposes Firecrawl's API for scraping, crawling, mapping, searching, parsing documents, browser automation, and academic research.


## Overview

The Firecrawl MCP Server provides powerful web data extraction and research capabilities:

- Scrape individual pages or crawl entire websites into markdown, HTML, JSON, and more
- Search the web, map site structures, and run autonomous agent-based data extraction
- Automate browsers with code or natural language, parse documents, and search academic papers and GitHub

Perfect for:

- AI assistants that need to fetch and process live web content
- Automating structured data extraction and research pipelines
- Building competitive intelligence, literature review, and site auditing workflows


## Tools

### Scrape

<details>
<summary><code>scrape_url</code> — Scrape a single URL</summary>

Scrapes a single URL and returns content in one or more formats. Supports JavaScript rendering, mobile emulation, proxy selection, and HTML tag filtering.

**Inputs:**
```
- `url` (string, required) — Full URL to scrape, including https://
- `formats` (list[string], optional) — Output formats: markdown, html, rawHtml, screenshot, links, images, summary (default: ["markdown"])
- `only_main_content` (bool, optional) — Strip navigation, headers, footers, and ads (default: true)
- `wait_for` (int, optional) — Milliseconds to wait for JS rendering before capture (0–30000, default: 0)
- `timeout_ms` (int, optional) — Total request timeout in milliseconds (1000–300000, default: 30000)
- `mobile` (bool, optional) — Emulate a mobile viewport (default: false)
- `proxy` (string, optional) — Proxy type: basic, enhanced, or auto (default: auto)
- `block_ads` (bool, optional) — Block ads and cookie consent banners (default: true)
- `include_tags` (list[string], optional) — HTML tags to include in output
- `exclude_tags` (list[string], optional) — HTML tags to exclude from output
- `remove_base64_images` (bool, optional) — Drop inline base64 images to reduce response size (default: true)
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "markdown": "# Page Title\n...",
    "summary": null,
    "html": null,
    "rawHtml": null,
    "screenshot": null,
    "links": null,
    "metadata": {
      "title": "Page Title",
      "description": "Page description",
      "language": "en",
      "sourceURL": "https://example.com",
      "url": "https://example.com",
      "keywords": null,
      "statusCode": 200,
      "contentType": "text/html",
      "error": null,
      "scrapeId": "abc123"
    },
    "warning": null
  }
}

// Error
{
  "success": false,
  "statusCode": 400,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "VALIDATION_ERROR", "message": "url cannot be empty", "details": {} },
  "data": null
}
```

> Rate-limited errors return `"retriable": true` and `"retry_after_seconds": 60`.

</details>


<details>
<summary><code>batch_scrape_urls</code> — Start a batch scrape job</summary>

Starts an async job to scrape multiple URLs in parallel. Returns a job ID — poll with `get_batch_scrape_status`.

**Inputs:**
```
- `urls` (list[string], required) — List of URLs to scrape (minimum 1)
- `formats` (list[string], optional) — Output formats (default: ["markdown"])
- `only_main_content` (bool, optional) — Strip navigation and ads (default: true)
- `proxy` (string, optional) — Proxy type: basic, enhanced, or auto (default: auto)
- `block_ads` (bool, optional) — Block ads and cookie banners (default: true)
- `remove_base64_images` (bool, optional) — Drop base64 images (default: true)
- `ignore_invalid_urls` (bool, optional) — Skip invalid URLs instead of failing (default: false)
- `max_concurrency` (int, optional) — Maximum simultaneous scrapes (Firecrawl default if omitted)
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "id": "batch-job-uuid",
    "url": null,
    "invalidURLs": []
  }
}

// Error
{
  "success": false,
  "statusCode": 400,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "VALIDATION_ERROR", "message": "urls cannot be empty", "details": {} },
  "data": null
}
```

> Rate-limited errors return `"retriable": true` and `"retry_after_seconds": 60`.

</details>


<details>
<summary><code>get_batch_scrape_status</code> — Poll batch scrape status</summary>

Returns the current status and completed results of a batch scrape job.

**Inputs:**
```
- `job_id` (string, required) — Batch scrape job ID returned by `batch_scrape_urls`
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "status": "completed",
    "total": 5,
    "completed": 5,
    "creditsUsed": 5,
    "expiresAt": "2024-12-15T00:00:00Z",
    "next": null,
    "data": [
      {
        "markdown": "# Page Title\n...",
        "summary": null,
        "html": null,
        "rawHtml": null,
        "screenshot": null,
        "links": null,
        "metadata": { "title": "...", "url": "...", "statusCode": 200 },
        "warning": null
      }
    ]
  }
}

// Error
{
  "success": false,
  "statusCode": 404,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "NOT_FOUND", "message": "job not found", "details": {} },
  "data": null
}
```

> `status` values: `scraping`, `completed`, `failed`, `cancelled`

</details>


<details>
<summary><code>cancel_batch_scrape</code> — Cancel a batch scrape job</summary>

DESTRUCTIVE — cancels a running batch scrape job. Completed pages are not returned after cancellation.

**Inputs:**
```
- `job_id` (string, required) — Batch scrape job ID to cancel
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": { "status": "cancelled" }
}

// Error
{
  "success": false,
  "statusCode": 404,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "NOT_FOUND", "message": "job not found", "details": {} },
  "data": null
}
```

</details>


### Crawl

<details>
<summary><code>crawl_url</code> — Start a full-site crawl</summary>

Starts an async crawl from a seed URL, following links and scraping discovered pages. Returns a job ID — poll with `get_crawl_status`.

**Inputs:**
```
- `url` (string, required) — Seed URL to start crawling from
- `limit` (int, optional) — Maximum pages to crawl (1–10000, default: 10000)
- `max_discovery_depth` (int, optional) — Maximum link depth from seed URL (unlimited if omitted)
- `include_paths` (list[string], optional) — Regex patterns — only matching URLs are crawled
- `exclude_paths` (list[string], optional) — Regex patterns — matching URLs are skipped
- `sitemap` (string, optional) — Sitemap mode: skip, include, or only (default: include)
- `allow_subdomains` (bool, optional) — Follow links to subdomains (default: false)
- `allow_external_links` (bool, optional) — Follow links to external domains (default: false)
- `ignore_query_parameters` (bool, optional) — Treat URLs differing only in query params as duplicates (default: false)
- `formats` (list[string], optional) — Output formats (default: ["markdown"])
- `only_main_content` (bool, optional) — Strip navigation and ads (default: true)
- `proxy` (string, optional) — Proxy type: basic, enhanced, or auto (default: auto)
- `block_ads` (bool, optional) — Block ads and cookie banners (default: true)
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "id": "crawl-job-uuid",
    "url": "https://api.firecrawl.dev/v2/crawl/crawl-job-uuid"
  }
}

// Error
{
  "success": false,
  "statusCode": 400,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "VALIDATION_ERROR", "message": "url cannot be empty", "details": {} },
  "data": null
}
```

> Rate-limited errors return `"retriable": true` and `"retry_after_seconds": 60`.

</details>


<details>
<summary><code>get_crawl_status</code> — Poll crawl status</summary>

Returns the current status, progress, and completed page data for a crawl job.

**Inputs:**
```
- `job_id` (string, required) — Crawl job ID returned by `crawl_url`
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "status": "completed",
    "total": 42,
    "completed": 42,
    "creditsUsed": 42,
    "expiresAt": "2024-12-15T00:00:00Z",
    "createdAt": "2024-12-14T00:00:00Z",
    "completedAt": "2024-12-14T01:00:00Z",
    "duration": 3600,
    "next": null,
    "data": [
      {
        "markdown": "# Page Title\n...",
        "summary": null,
        "html": null,
        "rawHtml": null,
        "screenshot": null,
        "links": null,
        "metadata": { "title": "...", "url": "...", "statusCode": 200 },
        "warning": null
      }
    ]
  }
}

// Error
{
  "success": false,
  "statusCode": 404,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "NOT_FOUND", "message": "job not found", "details": {} },
  "data": null
}
```

> `status` values: `crawling`, `completed`, `failed`, `cancelled`

</details>


<details>
<summary><code>cancel_crawl</code> — Cancel a crawl job</summary>

DESTRUCTIVE — cancels a running crawl job. Already-scraped pages are not returned after cancellation.

**Inputs:**
```
- `job_id` (string, required) — Crawl job ID to cancel
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": { "status": "cancelled" }
}

// Error
{
  "success": false,
  "statusCode": 404,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "NOT_FOUND", "message": "job not found", "details": {} },
  "data": null
}
```

</details>


### Discover

<details>
<summary><code>map_url</code> — Map all URLs on a website</summary>

Discovers and lists all URLs found on a website without scraping page content. Useful for site auditing and planning crawls.

**Inputs:**
```
- `url` (string, required) — Root URL of the site to map
- `search` (string, optional) — Filter and rank URLs by relevance to this query
- `sitemap` (string, optional) — Sitemap mode: skip, include, or only (default: include)
- `include_subdomains` (bool, optional) — Include URLs from subdomains (default: true)
- `ignore_query_parameters` (bool, optional) — Deduplicate URLs differing only in query params (default: true)
- `ignore_cache` (bool, optional) — Bypass sitemap cache for fresh results (default: false)
- `limit` (int, optional) — Maximum URLs to return (1–100000, default: 5000)
- `country` (string, optional) — ISO 3166-1 alpha-2 country code for geo-targeting (e.g. "US")
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "links": [
      { "url": "https://example.com/", "title": "Home", "description": null },
      { "url": "https://example.com/about", "title": null, "description": null }
    ]
  }
}

// Error
{
  "success": false,
  "statusCode": 400,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "VALIDATION_ERROR", "message": "url cannot be empty", "details": {} },
  "data": null
}
```

</details>


<details>
<summary><code>search_web</code> — Search the web</summary>

Searches the web and optionally scrapes the full content of result pages. Supports web, news, and image sources with geo-targeting and time filtering.

**Inputs:**
```
- `query` (string, required) — Search query (max 500 characters)
- `limit` (int, optional) — Number of results to return (1–100, default: 10)
- `sources` (list[string], optional) — Sources: web, news, images (default: ["web"])
- `categories` (list[string], optional) — Filters: github, research, pdf
- `country` (string, optional) — ISO country code for geo-targeting (default: US)
- `location` (string, optional) — Geographic location string (e.g. "San Francisco,California,United States")
- `tbs` (string, optional) — Time filter: qdr:h, qdr:d, qdr:w, qdr:m, qdr:y
- `include_domains` (list[string], optional) — Restrict results to these domains
- `exclude_domains` (list[string], optional) — Exclude results from these domains
- `scrape_formats` (list[string], optional) — Also scrape result pages in these formats
- `timeout_ms` (int, optional) — Request timeout in milliseconds (default: 60000)
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "results": {
      "web": [
        {
          "title": "Example Result",
          "description": "Page description...",
          "url": "https://example.com",
          "markdown": null,
          "html": null,
          "rawHtml": null,
          "category": null
        }
      ],
      "images": [
        {
          "title": "Image Title",
          "imageUrl": "https://example.com/image.jpg",
          "imageWidth": 1200,
          "imageHeight": 630,
          "url": "https://example.com",
          "position": 1
        }
      ],
      "news": [
        {
          "title": "News Headline",
          "snippet": "News excerpt...",
          "url": "https://news.example.com",
          "date": "2024-12-14",
          "imageUrl": null,
          "position": 1,
          "markdown": null
        }
      ]
    },
    "warning": null,
    "id": null,
    "creditsUsed": 5
  }
}

// Error
{
  "success": false,
  "statusCode": 400,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "VALIDATION_ERROR", "message": "query cannot be empty", "details": {} },
  "data": null
}
```

> Rate-limited errors return `"retriable": true` and `"retry_after_seconds": 60`.

</details>


### Parse

<details>
<summary><code>parse_document</code> — Parse a document file</summary>

Parses a document (PDF, DOCX, etc.) provided as base64-encoded bytes and returns the content as markdown or HTML.

**Inputs:**
```
- `file_content_b64` (string, required) — Base64-encoded file bytes
- `file_name` (string, required) — File name including extension (e.g. "report.pdf") — used to infer file type
- `formats` (list[string], optional) — Output formats: markdown, html (default: ["markdown"])
- `only_main_content` (bool, optional) — Strip headers, footers, and decorative content (default: true)
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "markdown": "# Document Title\n...",
    "summary": null,
    "html": null,
    "rawHtml": null,
    "links": ["https://reference.com"],
    "metadata": {
      "title": "Document Title",
      "description": null,
      "language": null,
      "sourceURL": null,
      "url": null,
      "keywords": null,
      "statusCode": null,
      "contentType": "application/pdf",
      "error": null,
      "scrapeId": null
    },
    "warning": null
  }
}

// Error
{
  "success": false,
  "statusCode": 400,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "VALIDATION_ERROR", "message": "file_content_b64 cannot be empty", "details": {} },
  "data": null
}
```

</details>


### Agent

<details>
<summary><code>run_agent</code> — Start an autonomous data extraction agent</summary>

Starts an async agent that navigates websites and extracts data based on a natural language prompt. Returns a job ID — poll with `get_agent_status` every 15–30 seconds.

**Inputs:**
```
- `prompt` (string, required) — Natural language description of what data to extract (max 10000 characters)
- `urls` (list[string], optional) — URLs to constrain the agent to
- `schema` (string, optional) — JSON schema string to structure the extracted data
- `model` (string, optional) — spark-1-mini (default, cheaper) or spark-1-pro (higher accuracy)
- `max_credits` (int, optional) — Maximum credits to spend (Firecrawl default if omitted)
```

**Output:**

```json
// Success — job started
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "id": "agent-job-uuid",
    "status": "processing",
    "data": null,
    "expiresAt": null,
    "creditsUsed": null
  }
}

// Error
{
  "success": false,
  "statusCode": 400,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "VALIDATION_ERROR", "message": "prompt cannot be empty", "details": {} },
  "data": null
}
```

> Rate-limited errors return `"retriable": true` and `"retry_after_seconds": 60`.

</details>


<details>
<summary><code>get_agent_status</code> — Poll agent job status</summary>

Returns the current status and results of an agent job. Poll every 15–30 seconds until status is `completed`, `failed`, or `cancelled`.

**Inputs:**
```
- `job_id` (string, required) — Agent job ID returned by `run_agent`
```

**Output:**

```json
// Success — job completed
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "id": "agent-job-uuid",
    "status": "completed",
    "data": { "your_field": "extracted value" },
    "expiresAt": "2024-12-15T00:00:00Z",
    "creditsUsed": 120
  }
}

// Error
{
  "success": false,
  "statusCode": 404,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "NOT_FOUND", "message": "job not found", "details": {} },
  "data": null
}
```

> `status` values: `processing`, `completed`, `failed`, `cancelled`. `data.data` shape matches the schema passed to `run_agent`.

</details>


<details>
<summary><code>cancel_agent</code> — Cancel an agent job</summary>

DESTRUCTIVE — cancels a running agent job. Partial results are not returned after cancellation.

**Inputs:**
```
- `job_id` (string, required) — Agent job ID to cancel
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": { "status": "cancelled" }
}

// Error
{
  "success": false,
  "statusCode": 404,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "NOT_FOUND", "message": "job not found", "details": {} },
  "data": null
}
```

</details>


### Browser

<details>
<summary><code>browser_interact</code> — Interact with a browser session</summary>

Runs JavaScript code or a natural language prompt against an active browser session opened by a previous `scrape_url` call. Use `data.metadata.scrapeId` from the scrape response as `scrape_id`. Provide either `code` or `prompt_text`, not both.

**Inputs:**
```
- `scrape_id` (string, required) — Scrape job ID from `data.metadata.scrapeId` in a `scrape_url` response
- `code` (string, optional) — JavaScript code to execute in the browser page context
- `prompt_text` (string, optional) — Natural language instruction for the browser to execute
- `language` (string, optional) — Code language: javascript or python (default: javascript)
- `timeout` (int, optional) — Execution timeout in seconds (1–300, default: 30)
```

**Output:**

```json
// Success — code execution
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "cdpUrl": "wss://browser.firecrawl.dev/...",
    "liveViewUrl": null,
    "interactiveLiveViewUrl": null,
    "output": null,
    "stdout": "",
    "result": "{\"title\": \"Example\"}",
    "stderr": null,
    "exitCode": 0,
    "killed": false
  }
}

// Success — prompt execution
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "cdpUrl": "wss://browser.firecrawl.dev/...",
    "liveViewUrl": null,
    "interactiveLiveViewUrl": null,
    "output": "Clicked the submit button successfully.",
    "stdout": null,
    "result": null,
    "stderr": null,
    "exitCode": null,
    "killed": null
  }
}

// Error
{
  "success": false,
  "statusCode": 400,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "VALIDATION_ERROR", "message": "scrape_id cannot be empty", "details": {} },
  "data": null
}
```

</details>


<details>
<summary><code>browser_close</code> — Close a browser session</summary>

DESTRUCTIVE — closes and releases a browser session. Call this when browser interaction is complete to free resources.

**Inputs:**
```
- `scrape_id` (string, required) — Scrape job ID whose browser session to close
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": { "status": "closed" }
}

// Error
{
  "success": false,
  "statusCode": 404,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "NOT_FOUND", "message": "scrape session not found", "details": {} },
  "data": null
}
```

</details>


### Research

<details>
<summary><code>search_papers</code> — Search academic research papers</summary>

Searches Firecrawl's academic research index by topic, method, benchmark, or author. Returns ranked papers with IDs for use in `get_paper` and `find_related_papers`.

**Inputs:**
```
- `query` (string, required) — Natural language search query (e.g. "diffusion models image synthesis")
- `k` (int, optional) — Maximum number of papers to return (1–500, default: 40)
- `authors` (string, optional) — Filter by author name substring (e.g. "LeCun"). Comma-separate for multiple
- `categories` (string, optional) — Filter by arXiv category (e.g. "cs.LG", "cs.CV"). Comma-separate for multiple
- `from_date` (string, optional) — Inclusive start date in YYYY-MM-DD format
- `to_date` (string, optional) — Inclusive end date in YYYY-MM-DD format
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "results": [
      {
        "paperId": "2014215642691656232",
        "primaryId": "arxiv:2105.05233",
        "ids": { "arxiv": ["2105.05233"] },
        "title": "Diffusion Models Beat GANs on Image Synthesis",
        "abstract": "We show that diffusion models can achieve...",
        "score": 0.016
      }
    ]
  }
}

// Error
{
  "success": false,
  "statusCode": 400,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "VALIDATION_ERROR", "message": "query cannot be empty", "details": {} },
  "data": null
}
```

</details>


<details>
<summary><code>get_paper</code> — Get full details for a research paper</summary>

Retrieves title, abstract, authors, categories, and dates for a specific paper by its ID.

**Inputs:**
```
- `paper_id` (string, required) — Paper ID — canonical paperId or source-prefixed ID (e.g. "arxiv:2105.05233")
- `k` (int, optional) — Number of related papers to include alongside the paper details
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "paper": {
      "paperId": "2014215642691656232",
      "primaryId": "arxiv:2105.05233",
      "ids": { "arxiv": ["2105.05233"] },
      "title": "Diffusion Models Beat GANs on Image Synthesis",
      "abstract": "We show that diffusion models can achieve...",
      "authors": "Dhariwal, Nichol",
      "categories": ["cs.LG", "cs.CV"],
      "createdDate": "Wed, 11 May 2021 18:01:01 GMT",
      "updateDate": "Wed, 11 May 2021 18:01:01 GMT"
    }
  }
}

// Error
{
  "success": false,
  "statusCode": 404,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "NOT_FOUND", "message": "paper not found", "details": {} },
  "data": null
}
```

</details>


<details>
<summary><code>find_related_papers</code> — Find papers related to a seed paper</summary>

Finds papers related to a seed paper ranked by semantic relevance to an intent. Ideal for literature review workflows: `search_papers` → `find_related_papers` → `get_paper`.

**Inputs:**
```
- `paper_id` (string, required) — Seed paper ID (canonical paperId or "arxiv:XXXX.XXXXX")
- `intent` (string, required) — Natural language ranking intent (e.g. "applications in medical imaging")
- `mode` (string, optional) — Expansion strategy: similar, citers, or references (default: similar)
- `k` (int, optional) — Maximum related papers to return (1–500, default: 40)
- `rerank` (bool, optional) — Apply an additional reranking pass over results (default: false)
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "results": [
      {
        "paperId": "2006114239201234567",
        "primaryId": "arxiv:2006.11239",
        "title": "Denoising Diffusion Probabilistic Models",
        "abstract": "We present high quality image synthesis...",
        "score": 0.032
      }
    ],
    "poolSize": 40,
    "truncated": false
  }
}

// Error
{
  "success": false,
  "statusCode": 404,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "NOT_FOUND", "message": "paper not found", "details": {} },
  "data": null
}
```

</details>


<details>
<summary><code>search_github</code> — Search GitHub issues, PRs, and repos</summary>

Searches GitHub issue history, pull requests, discussions, and repository READMEs using natural language. Useful for researching how a bug was fixed or what library maintainers have said.

**Inputs:**
```
- `query` (string, required) — Natural language query (e.g. "race condition in worker shutdown firecrawl")
- `k` (int, optional) — Maximum results to return (1–100, default: 20)
```

**Output:**

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": {
    "results": [
      {
        "resultType": "issue",
        "repo": "mendableai/firecrawl",
        "url": "https://github.com/mendableai/firecrawl/issues/123",
        "pageType": null,
        "number": 123,
        "title": "Worker shutdown race condition",
        "snippet": "Queue worker shutdown can lose in-flight jobs...",
        "contentMd": null
      }
    ]
  }
}

// Error
{
  "success": false,
  "statusCode": 400,
  "retriable": false,
  "retry_after_seconds": null,
  "error": { "code": "VALIDATION_ERROR", "message": "query cannot be empty", "details": {} },
  "data": null
}
```

> `resultType` values: `issue`, `pull_request`, `repository`, `discussion`

</details>


## API Parameters Reference

<details>
<summary><strong>Output Formats</strong></summary>

All scraping tools accept a `formats` list:

- `markdown` — Clean markdown (default)
- `html` — Cleaned HTML
- `rawHtml` — Raw page HTML
- `screenshot` — Page screenshot as base64
- `links` — All links found on the page
- `images` — All image URLs
- `summary` — AI-generated page summary

</details>

<details>
<summary><strong>Proxy Options</strong></summary>

- `basic` — Standard proxy for general use
- `enhanced` — Advanced proxy for bot-protected sites
- `auto` — Automatically selects the best proxy (default)

</details>

<details>
<summary><strong>Async Job Workflow</strong></summary>

`batch_scrape_urls`, `crawl_url`, and `run_agent` are asynchronous — they return a job ID immediately:

1. Call the tool → receive `data.id`
2. Poll the matching status tool (`get_batch_scrape_status`, `get_crawl_status`, `get_agent_status`) with the job ID
3. Keep polling until `status` is `completed`, `failed`, or `cancelled`

**Recommended polling interval:** every 15–30 seconds. Allow at least 2–3 minutes for crawl and agent jobs.

</details>

<details>
<summary><strong>Time-Based Search Filters (tbs)</strong></summary>

Use the `tbs` parameter in `search_web` to filter results by recency:

```
qdr:h  — Past hour
qdr:d  — Past day
qdr:w  — Past week
qdr:m  — Past month
qdr:y  — Past year
```

</details>

<details>
<summary><strong>Research Paper IDs</strong></summary>

`get_paper` and `find_related_papers` accept two ID formats:

```
Canonical:        2014215642691656232
Source-prefixed:  arxiv:2105.05233
```

Use `paperId` or `primaryId` from `search_papers` results.

</details>


## Getting Your Firecrawl API Key

<details>
<summary><strong>Steps</strong></summary>

1. Go to [Firecrawl](https://www.firecrawl.dev) and sign in or create an account
2. Navigate to **API Keys** in your dashboard
3. Click **Create API Key**
4. Copy the generated key — you will only see it once

</details>


## Troubleshooting

<details>
<summary><strong>Missing or Invalid Headers</strong></summary>

- **Cause:** API key not provided in request headers or incorrect format
- **Solution:**
  1. Verify `Authorization: Bearer YOUR_API_KEY` and `X-Mewcp-Credential-Id: CREDENTIAL-ID` headers are present
  2. Check API key is active in your MewCP account

</details>

<details>
<summary><strong>Insufficient Credits</strong></summary>

- **Cause:** API calls have exceeded your request limits
- **Solution:**
  1. Check credit usage in your Curious Layer dashboard
  2. Upgrade to a paid plan or add credits for higher limits
  3. Contact support for credit adjustments

</details>

<details>
<summary><strong>Credential Not Connected</strong></summary>

- **Cause:** No Firecrawl credential linked to your account
- **Solution:**
  1. Go to **Credentials** in your MewCP dashboard
  2. Add your Firecrawl API key
  3. Retry the request with the correct `X-Mewcp-Credential-Id` header

</details>

<details>
<summary><strong>Malformed Request Payload</strong></summary>

- **Cause:** JSON payload is invalid or missing required fields
- **Solution:**
  1. Validate JSON syntax before sending
  2. Ensure all required tool parameters are included
  3. Check parameter types match expected values (e.g. `timeout_ms` must be 1000–300000)

</details>

<details>
<summary><strong>Server Not Found</strong></summary>

- **Cause:** Incorrect server name in the API endpoint
- **Solution:**
  1. Verify endpoint format: `{server-name}/mcp/{tool-name}`
  2. Use the correct server name from documentation
  3. Check available servers in your Curious Layer account

</details>

<details>
<summary><strong>Firecrawl API Error</strong></summary>

- **Cause:** Upstream Firecrawl API returned an error
- **Solution:**
  1. Check Firecrawl service status at [Firecrawl Status](https://www.firecrawl.dev)
  2. Verify your API key has sufficient credits for the operation
  3. Review the error message in the response for specific details

</details>

---

<details>
<summary><strong>Resources</strong></summary>

- **[Firecrawl Documentation](https://docs.firecrawl.dev)** — Official API reference
- **[Firecrawl API Reference](https://docs.firecrawl.dev/api-reference)** — Complete endpoint reference
- **[FastMCP Docs](https://gofastmcp.com/v2/getting-started/welcome)** — FastMCP specification
- **[FastMCP Credentials](https://pypi.org/project/fastmcp-credentials/)** — FastMCP Credentials package for credential handling

</details>
