// Mock data store for RedArky

export const mockMissions = [
    {
      id: "m1",
      title: "SaaS Gap Finder – DevTools",
      goal: "Monitor Reddit, Hacker News, and GitHub Trending to identify recurring pain points in the developer tooling space. Find underserved niches where solutions are either non-existent or poorly executed.",
      goalType: "SaaS Discovery",
      status: "Running",
      dataSource: "scrape",
      sources: ["Reddit", "Hacker News"],
      apifyScraperId: null,
      agents: ["collector", "analyzer", "worker"],
      createdAt: "2026-05-20T08:00:00Z",
      lastRun: "2026-05-23T07:00:00Z",
      nextRun: "2026-05-24T07:00:00Z",
      stats: { gapsFound: 14, specsGenerated: 6, postsAnalyzed: 2340, pendingApprovals: 3 }
    },
    {
      id: "m2",
      title: "AI Productivity Sentiment",
      goal: "Track community sentiment around AI productivity tools across Reddit communities. Identify what features users love and hate.",
      goalType: "Opinion Analysis",
      status: "Scheduled",
      dataSource: "scrape",
      sources: ["Reddit"],
      apifyScraperId: null,
      agents: ["collector", "analyzer"],
      createdAt: "2026-05-18T10:00:00Z",
      lastRun: "2026-05-22T07:00:00Z",
      nextRun: "2026-05-23T19:00:00Z",
      stats: { gapsFound: 7, specsGenerated: 2, postsAnalyzed: 980, pendingApprovals: 0 }
    },
    {
      id: "m3",
      title: "B2B SaaS Pricing Research",
      goal: "Collect discussions about SaaS pricing models and frustrations. Find common complaints about pricing tiers and billing transparency.",
      goalType: "SaaS Discovery",
      status: "Idle",
      dataSource: "provide",
      sources: [],
      apifyScraperId: null,
      agents: ["collector"],
      createdAt: "2026-05-15T14:00:00Z",
      lastRun: "2026-05-20T07:00:00Z",
      nextRun: null,
      stats: { gapsFound: 3, specsGenerated: 0, postsAnalyzed: 450, pendingApprovals: 0 }
    },
    {
      id: "m4",
      title: "No-Code Tool Trends",
      goal: "Find emerging no-code and low-code tool ideas from Product Hunt, Hacker News, and Reddit.",
      goalType: "Custom",
      status: "Completed",
      dataSource: "scrape",
      sources: ["Hacker News", "Reddit"],
      apifyScraperId: "apify/product-hunt-scraper",
      agents: ["collector", "analyzer", "worker"],
      createdAt: "2026-05-10T09:00:00Z",
      lastRun: "2026-05-18T07:00:00Z",
      nextRun: null,
      stats: { gapsFound: 22, specsGenerated: 9, postsAnalyzed: 4120, pendingApprovals: 0 }
    }
  ];
  
  export const mockAgents = {
    m1: [
      {
        id: "a1-col",
        missionId: "m1",
        type: "collector",
        status: "Running",
        prompt: "Prioritize posts mentioning developer tooling pain points. Keywords: CI/CD, deployment, monitoring, observability, developer experience, devex, slow builds, flaky tests. Focus on posts with high engagement (>10 comments).",
        schedule: "0 6 * * *",
        scheduleLabel: "Daily at 6:00 AM",
        lastRun: "2026-05-23T06:00:00Z",
        nextRun: "2026-05-24T06:00:00Z",
        stats: { postsScraped: 2340, filtered: 890, stored: 654 }
      },
      {
        id: "a1-ana",
        missionId: "m1",
        type: "analyzer",
        status: "Running",
        prompt: "Analyze collected posts to identify recurring pain points and unmet needs. Look for: explicit complaints about existing tools, feature requests that have high upvote ratios, questions that reveal missing solutions. Categorize by severity and frequency. Confidence score threshold: 0.7.",
        schedule: "0 7 * * *",
        scheduleLabel: "Daily at 7:00 AM",
        lastRun: "2026-05-23T07:00:00Z",
        nextRun: "2026-05-24T07:00:00Z",
        stats: { analyzed: 654, gapsFound: 14, specsGenerated: 6 }
      },
      {
        id: "a1-wor",
        missionId: "m1",
        type: "worker",
        status: "Idle",
        prompt: "For each identified market gap with confidence >0.8, generate a detailed mini-spec. Draft Reddit comment replies to relevant threads asking about solutions — hold for human approval before posting.",
        schedule: "0 8 * * *",
        scheduleLabel: "Daily at 8:00 AM",
        metadata: [
          { key: "storage_bucket", value: "s3://redarky-specs/devtools" },
          { key: "notify_email", value: "user@example.com" }
        ],
        lastRun: "2026-05-23T08:00:00Z",
        nextRun: "2026-05-24T08:00:00Z",
        stats: { tasksExecuted: 12, actionsApproved: 9, actionsPending: 3 }
      }
    ],
    m2: [
      {
        id: "a2-col",
        missionId: "m2",
        type: "collector",
        status: "Scheduled",
        prompt: "Collect posts and comments from r/productivity, r/AItools, r/artificial, r/ChatGPT mentioning AI productivity apps. Keywords: ChatGPT, Claude, Copilot, Notion AI, workflow, automation. Filter: min 5 comments.",
        schedule: "0 18 * * *",
        scheduleLabel: "Daily at 6:00 PM",
        lastRun: "2026-05-22T18:00:00Z",
        nextRun: "2026-05-23T18:00:00Z",
        stats: { postsScraped: 980, filtered: 432, stored: 312 }
      },
      {
        id: "a2-ana",
        missionId: "m2",
        type: "analyzer",
        status: "Scheduled",
        prompt: "Run sentiment analysis on collected posts. Categorize sentiment per tool mentioned. Track sentiment trends over time. Identify feature requests and negative experiences. Output structured sentiment scores per tool.",
        schedule: "0 19 * * *",
        scheduleLabel: "Daily at 7:00 PM",
        lastRun: "2026-05-22T19:00:00Z",
        nextRun: "2026-05-23T19:00:00Z",
        stats: { analyzed: 312, gapsFound: 7, specsGenerated: 2 }
      }
    ]
  };
  
  export const mockLogs = {
    "a1-col": [
      { id: 1, ts: "2026-05-23T06:00:01Z", level: "info", message: "Collector agent initialized. Mission: SaaS Gap Finder – DevTools" },
      { id: 2, ts: "2026-05-23T06:00:03Z", level: "info", message: "Connecting to Reddit API... OK" },
      { id: 3, ts: "2026-05-23T06:00:05Z", level: "info", message: "Fetching r/devops — found 142 posts" },
      { id: 4, ts: "2026-05-23T06:00:08Z", level: "info", message: "Fetching r/programming — found 89 posts" },
      { id: 5, ts: "2026-05-23T06:00:11Z", level: "info", message: "Fetching r/SoftwareEngineering — found 76 posts" },
      { id: 6, ts: "2026-05-23T06:00:13Z", level: "info", message: "Connecting to Hacker News API... OK" },
      { id: 7, ts: "2026-05-23T06:00:15Z", level: "info", message: "Fetching HN Ask/Show posts — found 234 items" },
      { id: 8, ts: "2026-05-23T06:00:19Z", level: "success", message: "Keyword filter applied. 890/2340 posts pass threshold" },
      { id: 9, ts: "2026-05-23T06:00:22Z", level: "info", message: "Running AI relevance scoring on 890 posts..." },
      { id: 10, ts: "2026-05-23T06:00:45Z", level: "success", message: "AI scoring complete. 654 posts exceed relevance threshold 0.6" },
      { id: 11, ts: "2026-05-23T06:00:47Z", level: "info", message: "Uploading 654 posts to S3 bucket: redarky-data/devtools/2026-05-23" },
      { id: 12, ts: "2026-05-23T06:00:52Z", level: "success", message: "Data stored successfully. Pipeline stage complete." },
      { id: 13, ts: "2026-05-23T06:00:52Z", level: "info", message: "Triggering downstream Analyzer agent... handoff complete." },
    ],
    "a1-ana": [
      { id: 1, ts: "2026-05-23T07:00:01Z", level: "info", message: "Analyzer agent initialized. Loading 654 posts from S3." },
      { id: 2, ts: "2026-05-23T07:00:04Z", level: "info", message: "Chunking data for LLM processing (batch size: 50)..." },
      { id: 3, ts: "2026-05-23T07:00:06Z", level: "info", message: "Processing batch 1/14 — analyzing pain points..." },
      { id: 4, ts: "2026-05-23T07:00:18Z", level: "info", message: "Processing batch 2/14..." },
      { id: 5, ts: "2026-05-23T07:00:31Z", level: "success", message: "Gap detected: 'No affordable observability tool for solo devs' — confidence: 0.91" },
      { id: 6, ts: "2026-05-23T07:00:33Z", level: "success", message: "Gap detected: 'CI/CD pipeline debugging is opaque' — confidence: 0.87" },
      { id: 7, ts: "2026-05-23T07:00:35Z", level: "info", message: "Processing batch 5/14..." },
      { id: 8, ts: "2026-05-23T07:00:58Z", level: "success", message: "Gap detected: 'Flaky test management tooling missing' — confidence: 0.83" },
      { id: 9, ts: "2026-05-23T07:01:22Z", level: "warning", message: "Batch 9/14: Low signal posts detected. Skipping 12 items." },
      { id: 10, ts: "2026-05-23T07:01:45Z", level: "success", message: "Analysis complete. 14 market gaps identified across 654 posts." },
      { id: 11, ts: "2026-05-23T07:01:47Z", level: "info", message: "Generating 6 mini-specs for high-confidence gaps (>0.80)..." },
      { id: 12, ts: "2026-05-23T07:01:58Z", level: "success", message: "Mini-specs generated. Saving to digest queue." },
      { id: 13, ts: "2026-05-23T07:02:00Z", level: "info", message: "Handing off to Worker agent." },
    ],
    "a1-wor": [
      { id: 1, ts: "2026-05-23T08:00:01Z", level: "info", message: "Worker agent initialized. Loading 6 specs from Analyzer output." },
      { id: 2, ts: "2026-05-23T08:00:03Z", level: "info", message: "Task: Store specs to S3 — executing..." },
      { id: 3, ts: "2026-05-23T08:00:05Z", level: "success", message: "Specs uploaded to s3://redarky-specs/devtools/2026-05-23" },
      { id: 4, ts: "2026-05-23T08:00:07Z", level: "info", message: "Task: Send digest email to user@example.com — executing..." },
      { id: 5, ts: "2026-05-23T08:00:09Z", level: "success", message: "Email notification sent successfully." },
      { id: 6, ts: "2026-05-23T08:00:11Z", level: "info", message: "Task: Draft Reddit replies for 3 relevant threads — pending approval..." },
      { id: 7, ts: "2026-05-23T08:00:12Z", level: "warning", message: "External action requires human approval. Adding to Engagement Queue." },
      { id: 8, ts: "2026-05-23T08:00:13Z", level: "info", message: "3 actions queued for approval. Worker agent complete." },
    ]
  };
  
  export const mockMarketGaps = [
    {
      id: "g1",
      missionId: "m1",
      title: "Affordable Observability for Solo Developers",
      problem: "Solo developers and small teams are priced out of modern observability tools like Datadog and New Relic ($100+/mo). Open source alternatives (Prometheus, Grafana) require significant DevOps expertise to self-host and maintain. There's a clear gap for a simple, affordable, managed observability solution.",
      existingSolutions: ["Datadog (expensive)", "New Relic (complex pricing)", "Prometheus + Grafana (self-hosted complexity)", "Better Uptime (limited)"],
      confidenceScore: 91,
      evidenceCount: 47,
      supportingLinks: [
        { label: "r/devops: 'Why is observability so expensive?'", url: "#" },
        { label: "HN: Ask HN: Affordable monitoring for indie hackers", url: "#" },
        { label: "r/SRE: Grafana vs Datadog cost breakdown", url: "#" }
      ],
      sentiment: "negative",
      category: "DevOps",
      detectedAt: "2026-05-23T07:00:35Z"
    },
    {
      id: "g2",
      missionId: "m1",
      title: "CI/CD Pipeline Debugging Visibility",
      problem: "When CI/CD pipelines fail, engineers spend 30-60 minutes just understanding what went wrong and why. Existing tools show what failed but not why. There's demand for a tool that provides intelligent root cause analysis for pipeline failures with actionable fixes.",
      existingSolutions: ["GitHub Actions (basic logs)", "CircleCI (verbose but not intelligent)", "BuildPulse (flaky test only)"],
      confidenceScore: 87,
      evidenceCount: 38,
      supportingLinks: [
        { label: "r/programming: 'CI debugging is a nightmare'", url: "#" },
        { label: "HN: Show HN: Spent 3 days debugging a pipeline fail", url: "#" }
      ],
      sentiment: "negative",
      category: "DevTools",
      detectedAt: "2026-05-23T07:00:33Z"
    },
    {
      id: "g3",
      missionId: "m1",
      title: "Flaky Test Management Platform",
      problem: "Flaky tests are one of the top complaints from engineering teams of all sizes. Tests that sometimes pass and sometimes fail erode trust in CI, slow down deployments, and waste significant engineering time. No tool specifically focuses on tracking, quarantining, and fixing flaky tests intelligently.",
      existingSolutions: ["BuildPulse (partial)", "Manual tracking in spreadsheets", "Jest/Pytest plugins (limited)"],
      confidenceScore: 83,
      evidenceCount: 29,
      supportingLinks: [
        { label: "r/programming: The flaky test problem thread", url: "#" },
        { label: "HN: Flaky tests costing teams hours per week", url: "#" },
        { label: "r/devops: How do you handle flaky tests?", url: "#" }
      ],
      sentiment: "frustrated",
      category: "Testing",
      detectedAt: "2026-05-23T07:00:58Z"
    }
  ];
  
  export const mockMiniSpec = {
    id: "spec-g1",
    gapId: "g1",
    title: "ObservaLite — Affordable Observability SaaS",
    version: "0.1.0",
    generatedAt: "2026-05-23T07:01:52Z",
    spec: {
      productName: "ObservaLite",
      tagline: "Production observability for indie developers. No DevOps PhD required.",
      targetUser: "Solo developers, indie hackers, small engineering teams (1–5 engineers)",
      coreFeatures: [
        "One-line SDK install for Node.js, Python, Go",
        "Auto-instrumented error tracking and performance metrics",
        "Intelligent alerting with noise reduction",
        "Pre-built dashboards for common stacks (Next.js, FastAPI, Rails)",
        "Log aggregation with full-text search"
      ],
      pricing: {
        free: "1 service, 7-day retention, 10k events/day",
        pro: "$19/mo — 5 services, 30-day retention, unlimited events",
        team: "$49/mo — 20 services, 90-day retention, team seats"
      },
      techStack: {
        frontend: "Next.js + Recharts",
        backend: "Go (data ingestion), Python (alerting)",
        storage: "ClickHouse (time-series), PostgreSQL (metadata)",
        infra: "AWS ECS + S3"
      },
      marketSize: "~$2.1B TAM (observability tools), targeting $200M SAM",
      differentiator: "Price and simplicity. 10x cheaper than Datadog, 10x simpler than self-hosted Grafana stack.",
      risks: ["Competing with free tiers of large players", "Data retention costs at scale"],
      nextSteps: ["Validate pricing with 10 indie dev interviews", "Build MVP in 4–6 weeks", "Launch on Product Hunt"]
    }
  };
  
  export const mockSentimentData = [
    { date: "May 17", positive: 42, neutral: 35, negative: 23 },
    { date: "May 18", positive: 38, neutral: 40, negative: 22 },
    { date: "May 19", positive: 45, neutral: 32, negative: 23 },
    { date: "May 20", positive: 51, neutral: 28, negative: 21 },
    { date: "May 21", positive: 48, neutral: 31, negative: 21 },
    { date: "May 22", positive: 55, neutral: 27, negative: 18 },
    { date: "May 23", positive: 59, neutral: 26, negative: 15 },
  ];
  
  export const mockApprovalQueue = [
    {
      id: "aq1",
      missionId: "m1",
      agentType: "worker",
      actionType: "Reddit Reply",
      createdAt: "2026-05-23T08:00:12Z",
      subreddit: "r/devops",
      originalPost: {
        title: "Is there any affordable alternative to Datadog for a solo project?",
        author: "u/indie_dev_22",
        content: "I'm building a side project and want to add some basic observability but Datadog costs more than my entire hosting budget. I tried setting up Prometheus + Grafana but it took me 2 days and still doesn't feel right. Any alternatives people have had success with?",
        upvotes: 234,
        comments: 67,
        url: "#"
      },
      draftedResponse: "Hey! I've been in the same boat. A few options worth checking out: **Better Stack** (formerly Logtail) has a generous free tier for small projects. **Highlight.io** is open-source and can be self-hosted for free, or their cloud is quite affordable. If you're on Node.js/Python, **OpenTelemetry** with a cheap Grafana Cloud account can get you 90% of Datadog's value for about $10/mo. Good luck with the project!",
      confidence: 0.89
    },
    {
      id: "aq2",
      missionId: "m1",
      agentType: "worker",
      actionType: "Reddit Reply",
      createdAt: "2026-05-23T08:00:12Z",
      subreddit: "r/SoftwareEngineering",
      originalPost: {
        title: "How does your team handle flaky tests in CI?",
        author: "u/buildkite_fan",
        content: "We have about 40% of our CI failures being flaky tests and it's killing our deploy frequency. Currently we just re-run the pipeline and hope for the best. Has anyone found a systematic approach?",
        upvotes: 156,
        comments: 43,
        url: "#"
      },
      draftedResponse: "Flaky tests are genuinely one of the most underrated engineering productivity drains. A few approaches that have worked well: 1) **Quarantine** known flaky tests immediately into a separate suite that runs nightly, 2) Use **test retry logic** (pytest-rerunfailures, jest.retryTimes) as a band-aid while fixing root causes, 3) **Track flakiness rates** per test over time — tests failing >5% of the time get prioritized for fixing. Tools like BuildPulse specifically track this.",
      confidence: 0.84
    },
    {
      id: "aq3",
      missionId: "m1",
      agentType: "worker",
      actionType: "Reddit Reply",
      createdAt: "2026-05-23T08:00:13Z",
      subreddit: "r/programming",
      originalPost: {
        title: "Why is debugging CI/CD pipelines so painful in 2026?",
        author: "u/frustrated_engineer",
        content: "Spent 4 hours yesterday debugging a pipeline failure that turned out to be a timing issue in a Docker layer cache. The error message was completely useless. Modern CI tools have barely improved in terms of debuggability. Am I missing something or is this still just a dark art?",
        upvotes: 891,
        comments: 142,
        url: "#"
      },
      draftedResponse: "You're not missing anything — CI debugging is genuinely still terrible in most tools. A few things that help: **Act** (run GitHub Actions locally) is a game changer for fast iteration. For actual root cause analysis, some teams use **Honeycomb** traces in their pipelines. The honest answer is most CI tools optimize for *running* pipelines, not *understanding* why they fail. This is genuinely an unsolved problem that could use a good product.",
      confidence: 0.92
    }
  ];
  
  export const mockCollectedData = [
    {
      id: "cd1",
      missionId: "m1",
      source: "Reddit",
      subreddit: "r/devops",
      title: "Is there any affordable alternative to Datadog for a solo project?",
      author: "u/indie_dev_22",
      upvotes: 234,
      comments: 67,
      relevanceScore: 0.94,
      sentiment: "negative",
      keywords: ["datadog", "observability", "affordable", "alternative"],
      collectedAt: "2026-05-23T06:00:05Z",
      url: "#"
    },
    {
      id: "cd2",
      missionId: "m1",
      source: "Hacker News",
      subreddit: null,
      title: "Ask HN: What observability tools do you use for small teams?",
      author: "throwerr",
      upvotes: 178,
      comments: 89,
      relevanceScore: 0.91,
      sentiment: "neutral",
      keywords: ["observability", "monitoring", "small team", "cost"],
      collectedAt: "2026-05-23T06:00:13Z",
      url: "#"
    },
    {
      id: "cd3",
      missionId: "m1",
      source: "Reddit",
      subreddit: "r/SoftwareEngineering",
      title: "How does your team handle flaky tests in CI?",
      author: "u/buildkite_fan",
      upvotes: 156,
      comments: 43,
      relevanceScore: 0.88,
      sentiment: "frustrated",
      keywords: ["flaky tests", "CI/CD", "pipeline", "testing"],
      collectedAt: "2026-05-23T06:00:08Z",
      url: "#"
    },
    {
      id: "cd4",
      missionId: "m1",
      source: "Reddit",
      subreddit: "r/programming",
      title: "Why is debugging CI/CD pipelines so painful in 2026?",
      author: "u/frustrated_engineer",
      upvotes: 891,
      comments: 142,
      relevanceScore: 0.96,
      sentiment: "negative",
      keywords: ["CI/CD", "debugging", "pipeline", "devtools"],
      collectedAt: "2026-05-23T06:00:11Z",
      url: "#"
    },
    {
      id: "cd5",
      missionId: "m1",
      source: "Hacker News",
      subreddit: null,
      title: "Show HN: I built a CI debugging tool and it saved our team 5 hours/week",
      author: "devbuilder99",
      upvotes: 312,
      comments: 54,
      relevanceScore: 0.89,
      sentiment: "positive",
      keywords: ["CI", "debugging", "devtools", "show hn"],
      collectedAt: "2026-05-23T06:00:15Z",
      url: "#"
    }
  ];
  
  export const mockActivityFeed = [
    { id: 1, type: "agent_complete", agent: "collector", mission: "SaaS Gap Finder – DevTools", detail: "Scraped 2,340 posts from Reddit & HN", ts: "2026-05-23T06:01:00Z" },
    { id: 2, type: "gap_found", agent: "analyzer", mission: "SaaS Gap Finder – DevTools", detail: "14 market gaps identified", ts: "2026-05-23T07:02:00Z" },
    { id: 3, type: "approval_needed", agent: "worker", mission: "SaaS Gap Finder – DevTools", detail: "3 Reddit replies awaiting approval", ts: "2026-05-23T08:00:12Z" },
    { id: 4, type: "agent_complete", agent: "collector", mission: "AI Productivity Sentiment", detail: "Scraped 980 posts from Reddit", ts: "2026-05-22T18:01:00Z" },
    { id: 5, type: "spec_generated", agent: "analyzer", mission: "SaaS Gap Finder – DevTools", detail: "6 mini-specs generated", ts: "2026-05-23T07:02:00Z" },
    { id: 6, type: "scheduled", agent: "system", mission: "AI Productivity Sentiment", detail: "Pipeline scheduled for 7:00 PM", ts: "2026-05-23T00:00:00Z" },
    { id: 7, type: "agent_complete", agent: "worker", mission: "No-Code Tool Trends", detail: "9 specs stored, digest email sent", ts: "2026-05-18T08:05:00Z" },
  ];