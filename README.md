**Turn any website into clean, AI-ready data.**

A Model Context Protocol (MCP) server that exposes Firecrawl's API for scraping, crawling, mapping, searching, and extracting structured data from websites.


## Overview

The Firecrawl MCP Server provides powerful web data extraction capabilities:

- Scrape individual pages or crawl entire websites into markdown, HTML, JSON, and more
- Search the web and extract structured data using LLMs with async job management
- Map website URL structures and run autonomous agent-based data extraction

Perfect for:

- AI assistants that need to fetch and process live web content
- Automating structured data extraction from multiple websites
- Building research and competitive intelligence pipelines


## Tools

<details>
<summary><code>health_check</code> — Check server readiness</summary>

Verifies the server is operational. No authentication required.

**Inputs:**
```
None
```

**Output:**

```json
{
  "success": true,
  "status": "ok",
  "server": "CL Firecrawl MCP Server",
  "version": "0.1.0"
}
```

</details>


<details>
<summary><code>scrape</code> — Scrape a single URL</summary>

Scrapes a single URL and returns the content in one or more formats. Supports JavaScript rendering, mobile emulation, and HTML tag filtering.

**Inputs:**
```
- `url` (string, required) — The URL to scrape
- `formats` (string, optional) — Comma-separated output formats: markdown, html, rawHtml, json, screenshot, links, images, summary, audio, branding, changeTracking (default: markdown)
- `only_main_content` (bool, optional) — Extract only main content, excluding headers/footers/navs (default: true)
- `include_tags` (string, optional) — Comma-separated HTML tags to include in output
- `exclude_tags` (string, optional) — Comma-separated HTML tags to exclude from output
- `wait_for_selector` (string, optional) — CSS selector to wait for before scraping
- `timeout_ms` (int, optional) — Request timeout in milliseconds (1000–300000, default: 30000)
- `mobile` (bool, optional) — Emulate mobile device (default: false)
- `skip_tls_verification` (bool, optional) — Skip TLS certificate verification (default: true)
- `proxy` (string, optional) — Proxy type: basic, enhanced, or auto (default: auto)
- `block_ads` (bool, optional) — Block ads and cookie popups (default: true)
- `remove_base64_images` (bool, optional) — Remove base64 encoded images from output (default: true)
```

**Output:**

```json
{
  "success": true,
  "data": {
    "markdown": "# Page Title\n...",
    "metadata": { "title": "...", "url": "..." }
  }
}
```

</details>


<details>
<summary><code>crawl</code> — Crawl an entire website</summary>

Starts a crawl job from a base URL, following links and scraping all discovered pages. Returns a job ID for async processing.

**Inputs:**
```
- `url` (string, required) — Base URL to start crawling from
- `prompt` (string, optional) — Natural language prompt to generate crawler options
- `exclude_paths` (string, optional) — Comma-separated regex patterns for URLs to exclude
- `include_paths` (string, optional) — Comma-separated regex patterns for URLs to include
- `max_discovery_depth` (int, optional) — Maximum crawl depth from the start URL
- `sitemap` (string, optional) — Sitemap mode: skip, include, or only (default: include)
- `ignore_query_parameters` (bool, optional) — Don't re-scrape same path with different query params (default: false)
- `limit` (int, optional) — Maximum number of pages to crawl (default: 10000)
- `crawl_entire_domain` (bool, optional) — Follow sibling and parent URLs (default: false)
- `allow_external_links` (bool, optional) — Follow links to external domains (default: false)
- `allow_subdomains` (bool, optional) — Follow links to subdomains (default: false)
- `delay` (float, optional) — Delay in seconds between requests
- `max_concurrency` (int, optional) — Maximum concurrent scrapes
- `formats` (string, optional) — Output formats, comma-separated (default: markdown)
- `only_main_content` (bool, optional) — Extract main content only (default: true)
- `zero_data_retention` (bool, optional) — Enable zero data retention (default: false)
```

**Output:**

```json
{
  "success": true,
  "id": "crawl-job-uuid",
  "url": "https://api.firecrawl.dev/v2/crawl/crawl-job-uuid"
}
```

</details>


<details>
<summary><code>map</code> — Map all URLs on a website</summary>

Discovers and lists all URLs found on a website. Useful for site auditing and understanding site structure before crawling.

**Inputs:**
```
- `url` (string, required) — Base URL to start mapping from
- `search` (string, optional) — Filter and rank results by relevance to this query
- `sitemap` (string, optional) — Sitemap mode: skip, include, or only (default: include)
- `include_subdomains` (bool, optional) — Include subdomains (default: true)
- `ignore_query_parameters` (bool, optional) — Exclude URLs with query parameters (default: true)
- `ignore_cache` (bool, optional) — Bypass sitemap cache for fresh results (default: false)
- `limit` (int, optional) — Maximum URLs to return (max: 100000, default: 5000)
- `timeout_ms` (int, optional) — Timeout in milliseconds
- `country` (string, optional) — ISO 3166-1 alpha-2 country code (e.g., US, DE)
- `languages` (string, optional) — Comma-separated preferred languages (e.g., en-US,de-DE)
```

**Output:**

```json
{
  "success": true,
  "links": ["https://example.com/", "https://example.com/about", "..."]
}
```

</details>


<details>
<summary><code>search</code> — Search the web and scrape results</summary>

Searches the web using a query and optionally scrapes the full content of result pages.

**Inputs:**
```
- `query` (string, required) — Search query (max 500 characters)
- `limit` (int, optional) — Number of results to return (1–100, default: 5)
- `sources` (string, optional) — Comma-separated sources: web, images, news (default: web)
- `categories` (string, optional) — Comma-separated filters: github, research, pdf
- `tbs` (string, optional) — Time filter: qdr:d (day), qdr:w (week), qdr:m (month)
- `location` (string, optional) — Geographic location (e.g., San Francisco,California,United States)
- `country` (string, optional) — ISO country code for geo-targeting (default: US)
- `timeout` (int, optional) — Timeout in milliseconds (1000–300000, default: 60000)
- `ignore_invalid_urls` (bool, optional) — Exclude invalid URLs from results (default: false)
- `formats` (string, optional) — Scrape output formats, comma-separated (default: markdown)
- `mobile` (bool, optional) — Emulate mobile device when scraping (default: false)
- `proxy` (string, optional) — Proxy type: basic, enhanced, or auto (default: auto)
- `block_ads` (bool, optional) — Block ads and cookie popups (default: true)
```

**Output:**

```json
{
  "success": true,
  "data": [
    { "url": "https://...", "markdown": "...", "metadata": { "title": "..." } }
  ]
}
```

</details>


<details>
<summary><code>agent</code> — Autonomous website navigation and data extraction</summary>

Starts an autonomous agent that navigates websites and extracts data based on a natural language prompt. Returns a job ID — poll with `agent_status` for results.

**Inputs:**
```
- `prompt` (string, required) — Natural language description of what data to extract (max 10000 characters)
- `urls` (string, optional) — Comma-separated URLs to constrain the agent to
- `schema` (string, optional) — JSON schema string to structure extracted data
- `max_credits` (float, optional) — Maximum credits to spend (default: 2500)
- `strict_constrain_to_urls` (bool, optional) — Only visit URLs listed in the urls param (default: false)
- `model` (string, optional) — Model to use: spark-1-mini (default, cheaper) or spark-1-pro (higher accuracy)
```

**Output:**

```json
{
  "success": true,
  "jobId": "agent-job-uuid"
}
```

</details>


<details>
<summary><code>agent_status</code> — Check agent job status</summary>

Polls the status of an agent job started by `agent`. Poll every 15–30 seconds for up to 2–3 minutes.

**Inputs:**
```
- `job_id` (string, required) — Agent job ID returned by the agent tool (UUID format)
```

**Output:**

```json
{
  "success": true,
  "status": "completed",
  "data": { "extracted": "..." }
}
```

</details>


<details>
<summary><code>extract</code> — Async structured data extraction using LLMs</summary>

Starts an async job to extract structured data from one or more URLs using LLMs and an optional schema. Returns a job ID — poll with `extract_status`.

**Inputs:**
```
- `urls` (string, required) — Comma-separated URLs to extract from (glob format supported)
- `prompt` (string, optional) — Custom prompt to guide the extraction
- `schema` (string, optional) — JSON schema string for structured output
- `enable_web_search` (bool, optional) — Use web search for additional context (default: false)
- `ignore_sitemap` (bool, optional) — Ignore sitemap.xml files (default: false)
- `include_subdomains` (bool, optional) — Include subdomains in scanning (default: true)
- `show_sources` (bool, optional) — Include extraction sources in response (default: false)
- `ignore_invalid_urls` (bool, optional) — Skip invalid URLs instead of failing (default: true)
- `formats` (string, optional) — Scrape output formats, comma-separated (default: markdown)
- `only_main_content` (bool, optional) — Extract main content only (default: true)
- `mobile` (bool, optional) — Emulate mobile device (default: false)
- `proxy` (string, optional) — Proxy type: basic, enhanced, or auto (default: auto)
- `block_ads` (bool, optional) — Block ads and cookie popups (default: true)
```

**Output:**

```json
{
  "success": true,
  "id": "extract-job-uuid"
}
```

</details>


<details>
<summary><code>extract_status</code> — Check extraction job status</summary>

Polls the status of an extraction job started by `extract`.

**Inputs:**
```
- `job_id` (string, required) — Extraction job ID returned by the extract tool (UUID format)
```

**Output:**

```json
{
  "success": true,
  "status": "completed",
  "data": { "field": "extracted value" }
}
```

</details>


## API Parameters Reference

<details>
<summary><strong>Output Formats</strong></summary>

All scraping tools accept a comma-separated `formats` parameter:

- `markdown` — Clean markdown (default)
- `html` — Cleaned HTML
- `rawHtml` — Raw page HTML
- `json` — Structured JSON extraction
- `screenshot` — Page screenshot
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

Tools `crawl`, `agent`, and `extract` are asynchronous:

1. Call the tool → receive a `job_id`
2. Poll `agent_status` or `extract_status` with the `job_id`
3. Keep polling until `status` is `completed`, `failed`, or `cancelled`

**Recommended polling interval:** every 15–30 seconds for at least 2–3 minutes before considering a job failed.

</details>

<details>
<summary><strong>Time-Based Search Filters (tbs)</strong></summary>

Use the `tbs` parameter in `search` to filter results by recency:

```
qdr:h  — Past hour
qdr:d  — Past day
qdr:w  — Past week
qdr:m  — Past month
qdr:y  — Past year
```

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
  2. Use correct server name from documentation
  3. Check available servers in your Curious Layer account

</details>

<details>
<summary><strong>Firecrawl API Error</strong></summary>

- **Cause:** Upstream Firecrawl API returned an error
- **Solution:**
  1. Check Firecrawl service status at [Firecrawl Status](https://www.firecrawl.dev)
  2. Verify your API key has sufficient credits for the operation
  3. Review the error message returned in the response for specific details

</details>

---

### Resources

- **[Firecrawl Documentation](https://docs.firecrawl.dev)** — Official API reference
- **[Firecrawl API Reference](https://docs.firecrawl.dev/api-reference)** — Complete endpoint reference
- **[FastMCP Docs](https://gofastmcp.com/v2/getting-started/welcome)** — FastMCP specification
- **[FastMCP Credentials](https://pypi.org/project/fastmcp-credentials/)** — FastMCP Credentials package for credential handling
