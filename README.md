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

Scrapes a single URL and returns its content in the requested formats. Returns the page as markdown, HTML, screenshot, links, or a summary. For public document URLs (PDF, DOCX) Firecrawl auto-detects and parses them. The response includes `data.metadata.scrapeId` which can be passed to `browser_interact` to continue interacting with the same live browser session.

**Inputs:**
```
- `url` (string, required) — Full URL to scrape, including https://.
- `formats` (list[string], optional, default: ["markdown"]) — Output formats to request: markdown (default), html, rawHtml, links, screenshot, summary, json, audio, video, branding, product, menu. Use ['markdown'] for text content, add 'screenshot' for visual capture.
- `only_main_content` (bool, optional, default: true) — Strip navigation, headers, footers, and ads — keep the article/content body.
- `wait_for` (int, optional, default: 0) — Milliseconds to wait after page load before capturing (0–30000). Use for JS-rendered pages.
- `timeout_ms` (int, optional, default: 30000) — Maximum time the page load may take in milliseconds (1000–300000).
- `mobile` (bool, optional, default: false) — Emulate a mobile viewport.
- `proxy` (string, optional, default: "auto") — Proxy tier: 'auto' (default), 'basic', or 'enhanced' (stealth, higher credit cost).
- `block_ads` (bool, optional, default: true) — Block ads and cookie consent banners before capturing.
- `include_tags` (list[string], optional) — HTML tags to include in output (e.g. ['article', 'main']). Omit to include all.
- `exclude_tags` (list[string], optional) — HTML tags to strip from output (e.g. ['nav', 'footer', 'aside']).
- `remove_base64_images` (bool, optional, default: true) — Drop inline base64 images from markdown output to reduce token usage.
```

**Output:**

```json
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
```

</details>


<details>
<summary><code>batch_scrape_urls</code> — Start a batch scrape job</summary>

Starts an async batch scrape job for a list of URLs. Returns a job ID immediately. Use `get_batch_scrape_status` to poll for completion and retrieve scraped content. Ideal for scraping 5–1000 URLs in parallel without blocking.

**Inputs:**
```
- `urls` (list[string], required) — List of URLs to scrape.
- `formats` (list[string], optional, default: ["markdown"]) — Output formats to request: markdown (default), html, rawHtml, links, screenshot, summary, json, audio, video, branding, product, menu. Use ['markdown'] for text content, add 'screenshot' for visual capture.
- `only_main_content` (bool, optional, default: true) — Strip navigation, headers, footers, and ads from each page.
- `proxy` (string, optional, default: "auto") — Proxy tier: 'auto' (default), 'basic', or 'enhanced' (stealth, higher credit cost).
- `block_ads` (bool, optional, default: true) — Block ads and cookie banners.
- `remove_base64_images` (bool, optional, default: true) — Drop inline base64 images to reduce response size.
- `ignore_invalid_urls` (bool, optional, default: false) — Skip invalid URLs instead of failing the entire job.
- `max_concurrency` (int, optional) — Maximum simultaneous scrapes (leave None for Firecrawl default).
```

**Output:**

```json
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
```

</details>


<details>
<summary><code>get_batch_scrape_status</code> — Poll batch scrape status</summary>

Polls the status of a batch scrape job started by `batch_scrape_urls`. Returns status (scraping/completed/failed), progress counters, and scraped pages when done. If `data.next` is present in the response, call again with the same job_id to get the next page of results.

**Inputs:**
```
- `job_id` (string, required) — Batch scrape job ID returned by `batch_scrape_urls`.
```

**Output:**

```json
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
```

</details>


<details>
<summary><code>cancel_batch_scrape</code> — Cancel a batch scrape job</summary>

DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. Stops a running batch scrape job. All in-progress scraping is terminated and any unfinished results are permanently lost — this cannot be undone. NEVER call this tool autonomously or as part of an automated flow. You MUST stop, tell the user exactly which batch scrape job will be cancelled and that unfinished results will be permanently lost, and wait for their explicit written confirmation before proceeding.

**Inputs:**
```
- `job_id` (string, required) — Batch scrape job ID to cancel.
```

**Output:**

```json
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": { "status": "cancelled" }
}
```

</details>


### Crawl

<details>
<summary><code>crawl_url</code> — Start a full-site crawl</summary>

Starts an async crawl job from a seed URL, following internal links up to the specified depth and page limit. Returns a job ID immediately. Use `get_crawl_status` to poll for progress and results. Use `include_paths`/`exclude_paths` regex patterns to control which URLs are visited. Ideal for extracting all content from a site, documentation, or blog.

**Inputs:**
```
- `url` (string, required) — Seed URL to start crawling from.
- `limit` (int, optional, default: 10000) — Maximum number of pages to crawl (1–10000).
- `max_discovery_depth` (int, optional) — Maximum link depth from the seed URL. Omit for unlimited.
- `include_paths` (list[string], optional) — Regex patterns — only URLs matching at least one pattern are crawled.
- `exclude_paths` (list[string], optional) — Regex patterns — URLs matching any pattern are skipped.
- `sitemap` (string, optional, default: "include") — Sitemap usage: 'include' (use sitemap + crawl), 'skip' (crawl only), 'only' (sitemap only).
- `allow_subdomains` (bool, optional, default: false) — Follow links to subdomains of the seed URL.
- `allow_external_links` (bool, optional, default: false) — Follow links to entirely different domains.
- `ignore_query_parameters` (bool, optional, default: false) — Treat URLs that differ only in query parameters as duplicates.
- `formats` (list[string], optional, default: ["markdown"]) — Output formats to request: markdown (default), html, rawHtml, links, screenshot, summary, json, audio, video, branding, product, menu. Use ['markdown'] for text content, add 'screenshot' for visual capture.
- `only_main_content` (bool, optional, default: true) — Strip navigation, headers, footers, and ads from each page.
- `proxy` (string, optional, default: "auto") — Proxy tier: 'auto' (default), 'basic', or 'enhanced' (stealth, higher credit cost).
- `block_ads` (bool, optional, default: true) — Block ads and cookie banners.
```

**Output:**

```json
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
```

</details>


<details>
<summary><code>get_crawl_status</code> — Poll crawl status</summary>

Polls the status of a crawl job started by `crawl_url`. Returns status (scraping/completed/failed/cancelled), progress counters, and crawled pages. If `data.next` is present, call again to retrieve the next page of results.

**Inputs:**
```
- `job_id` (string, required) — Crawl job ID returned by `crawl_url`.
```

**Output:**

```json
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
```

</details>


<details>
<summary><code>cancel_crawl</code> — Cancel a crawl job</summary>

DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. Stops a running crawl job. All in-progress crawling is terminated and any unfinished pages are permanently lost — this cannot be undone. NEVER call this tool autonomously or as part of an automated flow. You MUST stop, tell the user which crawl job will be cancelled and that unfinished pages will be permanently lost, and wait for their explicit written confirmation before proceeding.

**Inputs:**
```
- `job_id` (string, required) — Crawl job ID to cancel.
```

**Output:**

```json
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": { "status": "cancelled" }
}
```

</details>


### Discover

<details>
<summary><code>map_url</code> — Map all URLs on a website</summary>

Discovers all URLs on a website without scraping their content. Returns a list of links with title and description. Use before `crawl_url` to understand site structure, or pass `search` to filter URLs by relevance to a topic. Much faster and cheaper than crawling when you only need the URL list.

**Inputs:**
```
- `url` (string, required) — Root URL of the site to map.
- `search` (string, optional) — Filter and rank URLs by relevance to this search query.
- `sitemap` (string, optional, default: "include") — 'include' (sitemap + crawl), 'skip' (crawl only), 'only' (sitemap only).
- `include_subdomains` (bool, optional, default: true) — Include URLs from subdomains of the root URL.
- `ignore_query_parameters` (bool, optional, default: true) — Deduplicate URLs that differ only in query parameters.
- `ignore_cache` (bool, optional, default: false) — Bypass sitemap cache to get the freshest URL list.
- `limit` (int, optional, default: 5000) — Maximum number of URLs to return (1–100000).
- `country` (string, optional) — ISO 3166-1 alpha-2 country code for geo-targeting (e.g. 'US', 'DE').
```

**Output:**

```json
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
```

</details>


<details>
<summary><code>search_web</code> — Search the web</summary>

Searches the web and optionally scrapes the full content of each result. Returns web pages, images, or news depending on `sources`. Set `scrape_formats` to ['markdown'] to get full page content alongside each result — omit to get only title, description, and URL. Supports operator syntax: site:, filetype:, intitle:, -exclude, "exact phrase".

**Inputs:**
```
- `query` (string, required) — Search query. Supports operators: site:domain.com, filetype:pdf, intitle:keyword, -exclude, "exact phrase", related:domain.com.
- `limit` (int, optional, default: 10) — Number of results to return (1–100).
- `sources` (list[string], optional, default: ["web"]) — Result types to return: 'web', 'images', 'news'. Combine as needed.
- `categories` (list[string], optional) — Filter to specific result categories: 'github', 'research', 'pdf'.
- `country` (string, optional) — ISO country code for geo-targeted results (e.g. 'US', 'DE', 'JP'). Default: US.
- `location` (string, optional) — City/region for geo-targeted results (e.g. 'San Francisco,California,United States').
- `tbs` (string, optional) — Time-based filter: 'qdr:d' (past day), 'qdr:w' (past week), 'qdr:m' (past month).
- `include_domains` (list[string], optional) — Restrict results to these domains (mutually exclusive with exclude_domains).
- `exclude_domains` (list[string], optional) — Remove these domains from results (mutually exclusive with include_domains).
- `scrape_formats` (list[string], optional) — If provided, each result page is scraped and content returned in these formats. Omit to return only title/description/URL without scraping.
- `timeout_ms` (int, optional, default: 45000) — Request timeout in milliseconds (1000–300000). Default 45000.
```

**Output:**

```json
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
```

</details>


### Parse

<details>
<summary><code>parse_document</code> — Parse a document file</summary>

Parses a local or private document (PDF, DOCX, XLSX, HTML, and more) into clean markdown or structured data. Use when the file is not publicly accessible by URL — for public URLs use `scrape_url` instead. The file must be provided as base64-encoded bytes, making this suitable for workflow chains where a previous step fetches and encodes the file content.

**Inputs:**
```
- `file_content_b64` (string, required) — Base64-encoded file bytes to parse.
- `file_name` (string, required) — Filename including extension (e.g. 'report.pdf', 'data.docx'). Extension determines parser.
- `formats` (list[string], optional, default: ["markdown"]) — Output formats: markdown, html, rawHtml, links, summary.
- `only_main_content` (bool, optional, default: true) — Strip headers, footers, and decorative content.
```

**Output:**

```json
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
```

</details>


### Agent

<details>
<summary><code>run_agent</code> — Start an autonomous data extraction agent</summary>

Starts an autonomous web research agent that searches, navigates, and extracts data based on a natural language prompt. No URLs required — the agent finds them. Use `schema` to get structured JSON output. Returns a job ID; use `get_agent_status` to poll. Use `spark-1-mini` (default, 60% cheaper) for most tasks; `spark-1-pro` for complex multi-domain research. Set `max_credits` to cap spending — the job fails without charges if the limit is hit.

**Inputs:**
```
- `prompt` (string, required) — Natural language description of the data to find (max 10000 chars). Be specific: 'Find the 5 most-funded AI startups in 2024 with founder names and total funding.'
- `urls` (list[string], optional) — Optional seed URLs to focus the agent. Omit to let the agent search freely.
- `schema` (string, optional) — JSON schema string for structured output. Omit for free-form text.
- `model` (string, optional, default: "spark-1-mini") — 'spark-1-mini' (default, cheaper) or 'spark-1-pro' (higher accuracy).
- `max_credits` (int, optional) — Credit cap for this job (default 2500). Job fails without charges if exceeded.
```

**Output:**

```json
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
```

</details>


<details>
<summary><code>get_agent_status</code> — Poll agent job status</summary>

Polls the status of an agent job started by `run_agent`. Returns status (processing/completed/failed/cancelled), extracted data when done, and credit usage. Poll every 15–30 seconds; jobs typically complete in 1–5 minutes.

**Inputs:**
```
- `job_id` (string, required) — Agent job ID returned by `run_agent`.
```

**Output:**

```json
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
```

> `data.data` shape matches the schema passed to `run_agent`.

</details>


<details>
<summary><code>cancel_agent</code> — Cancel an agent job</summary>

DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. Requests cancellation of a running agent job. Any in-progress reasoning steps complete before the job transitions to cancelled — credits for completed steps may still be charged and cannot be recovered. NEVER call this tool autonomously or as part of an automated flow. You MUST stop, tell the user which agent job will be cancelled and the credit implications, and wait for their explicit written confirmation before proceeding.

**Inputs:**
```
- `job_id` (string, required) — Agent job ID to cancel.
```

**Output:**

```json
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": { "status": "cancelled" }
}
```

</details>


### Browser

<details>
<summary><code>browser_interact</code> — Interact with a browser session</summary>

Executes code or a natural language prompt in the live browser session bound to a previous scrape job. The `scrape_id` comes from `data.metadata.scrapeId` in a `scrape_url` response. First call creates the browser session at the same page state as the scrape. Subsequent calls on the same `scrape_id` reuse the live session. Provide either `code` (Playwright/Node/Python/Bash to run) or `prompt_text` (AI-driven navigation), not both. Returns CDP URL, live view URL, stdout, and AI output. Call `browser_close` when done to release the session.

**Inputs:**
```
- `scrape_id` (string, required) — Scrape job ID from `data.metadata.scrapeId` in a `scrape_url` response.
- `code` (string, optional) — Code to execute in the browser sandbox (1–100000 chars). Provide this OR prompt_text, not both.
- `prompt_text` (string, optional) — Natural language task for the AI browser agent (1–10000 chars). Provide this OR code, not both.
- `language` (string, optional, default: "node") — Code language when using `code`: 'node' (default), 'python', or 'bash'.
- `timeout` (int, optional, default: 30) — Execution timeout in seconds (1–300).
```

**Output:**

```json
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
```

> When using `prompt_text`, `output` contains the AI response and `result`/`stdout`/`exitCode` are null.

</details>


<details>
<summary><code>browser_close</code> — Close a browser session</summary>

DESTRUCTIVE — REQUIRES EXPLICIT USER CONFIRMATION BEFORE CALLING. Destroys the browser session attached to a scrape job. All browser state, cookies, and session data are permanently lost and the session cannot be resumed — this cannot be undone. Always call this when done interacting to avoid leaking browser resources and credits. NEVER call this tool autonomously or as part of an automated flow. You MUST stop, confirm with the user that the browser session is no longer needed, and wait for their explicit written confirmation before proceeding.

**Inputs:**
```
- `scrape_id` (string, required) — Scrape job ID whose browser session to close (same ID used in browser_interact).
```

**Output:**

```json
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": { "status": "closed" }
}
```

</details>


### Research

<details>
<summary><code>search_papers</code> — Search academic research papers</summary>

Searches Firecrawl's academic research index by topic, method, benchmark, or author. Returns ranked papers with paperId, title, abstract, and relevance score. Use `paperId` from results to call `get_paper` or `find_related_papers`. Supports filtering by author name substring, category (e.g. 'cs.LG'), and date range.

**Inputs:**
```
- `query` (string, required) — Natural language search query (e.g. 'diffusion models image synthesis').
- `k` (int, optional, default: 40) — Maximum number of ranked papers to return (1–500).
- `authors` (string, optional) — Filter by author name substring (e.g. 'LeCun'). Comma-separate for multiple.
- `categories` (string, optional) — Filter by paper category (e.g. 'cs.LG', 'cs.CV'). Comma-separate for multiple.
- `from_date` (string, optional) — Inclusive lower bound on paper date in YYYY-MM-DD format (e.g. '2023-01-01').
- `to_date` (string, optional) — Inclusive upper bound on paper date in YYYY-MM-DD format.
```

**Output:**

```json
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
```

</details>


<details>
<summary><code>get_paper</code> — Get full details for a research paper</summary>

Retrieves full details for a specific research paper by its ID. Returns title, abstract, authors, categories, and dates. The `paper_id` can be a canonical paperId (e.g. '2014215642691656232') or a source-prefixed ID (e.g. 'arxiv:2105.05233') from `search_papers` results.

**Inputs:**
```
- `paper_id` (string, required) — Paper ID — either canonical paperId or source-prefixed ID like 'arxiv:2105.05233'.
- `k` (int, optional) — Number of related papers to include alongside the paper details.
```

**Output:**

```json
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
```

</details>


<details>
<summary><code>find_related_papers</code> — Find papers related to a seed paper</summary>

Finds papers related to a seed paper, ranked by semantic relevance to an intent. Use `mode` to choose expansion strategy: 'similar' (semantically close), 'citers' (papers that cite the seed), 'references' (papers cited by the seed). Returns ranked results with relevance scores. Ideal for literature review workflows: search_papers → find_related_papers → get_paper.

**Inputs:**
```
- `paper_id` (string, required) — Seed paper ID (canonical paperId or 'arxiv:XXXX.XXXXX').
- `intent` (string, required) — Natural language ranking intent (e.g. 'applications in medical imaging').
- `mode` (string, optional, default: "similar") — Expansion mode: 'similar' (default), 'citers', or 'references'.
- `k` (int, optional, default: 40) — Maximum number of related papers to return (1–500).
- `rerank` (bool, optional, default: false) — Apply an additional reranking pass over the fused candidate set.
```

**Output:**

```json
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
```

</details>


<details>
<summary><code>search_github</code> — Search GitHub issues, PRs, and repos</summary>

Searches GitHub issue history, pull requests, discussions, and repository READMEs using natural language. Returns matched content with repository metadata, URLs, and markdown snippets. Useful for researching how a bug was fixed, what a library's maintainers have said, or finding prior art in open source projects.

**Inputs:**
```
- `query` (string, required) — Natural language query (e.g. 'race condition in worker shutdown firecrawl').
- `k` (int, optional, default: 20) — Maximum number of results to return (1–100).
```

**Output:**

```json
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
```

> `resultType` values: `issue`, `pull_request`, `repository`, `discussion`

</details>


## API Parameters Reference

<details>
<summary><strong>Response Envelope</strong></summary>

Every tool returns the same top-level envelope. Only `data` varies per tool.

```json
// Success
{
  "success": true,
  "statusCode": 200,
  "retriable": false,
  "retry_after_seconds": null,
  "error": null,
  "data": { ... }
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

- `retriable` — `true` when it is safe to retry (rate limit, network error, 503). `false` for validation and auth errors.
- `retry_after_seconds` — seconds to wait before retrying; present only when `retriable` is `true` and the upstream specifies a delay.
- `error.code` — machine-readable string: `VALIDATION_ERROR`, `AUTH_ERROR`, `UPSTREAM_ERROR`, `SERVER_ERROR`.

</details>

<details>
<summary><strong>Output Formats</strong></summary>

All scraping tools accept a `formats` list:

- `markdown` — Clean markdown (default)
- `html` — Cleaned HTML
- `rawHtml` — Raw page HTML
- `screenshot` — Page screenshot as base64
- `links` — All links found on the page
- `summary` — AI-generated page summary
- `json` — Structured JSON extraction
- `audio`, `video`, `branding`, `product`, `menu` — Specialised extraction modes

</details>

<details>
<summary><strong>Proxy Options</strong></summary>

- `auto` — Automatically selects the best proxy (default)
- `basic` — Standard proxy for general use
- `enhanced` — Stealth proxy for bot-protected sites (higher credit cost)

</details>

<details>
<summary><strong>Async Job Workflow</strong></summary>

`batch_scrape_urls`, `crawl_url`, and `run_agent` are asynchronous — they return a job ID immediately:

1. Call the tool → receive `data.id`
2. Poll the matching status tool (`get_batch_scrape_status`, `get_crawl_status`, `get_agent_status`) with the job ID
3. Keep polling until `status` is `completed`, `failed`, or `cancelled`
4. If `data.next` is present in the status response, call again with the same job ID to page through results

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
