#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║           📊 مُحلّل التريندات التقنية الاحترافي 📊            ║
║   Professional Tech Trend Analyzer                           ║
║                                                              ║
║   الميزات:                                                   ║
║     • تتبع ذكر الشركات (Company Tracker)                    ║
║     • تتبع المصطلحات التقنية (Tech Term Tracker)             ║
║     • اتجاه التريند: صاعد/ثابت/هابط (Trend Direction)        ║
║     • تحليل لكل مصدر (Per-Source Breakdown)                  ║
║     • تقرير Markdown احترافي                                 ║
╚══════════════════════════════════════════════════════════════╝

المؤلف: Tech News Bot
الإصدار: 2.0
التاريخ: 2026-07-01
"""

import sys
import io
import json
import glob
import re
import argparse
import logging
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

# إصلاح ترميز Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ─────────────────────────────────────────────────────────────
# إعداد التسجيل
# ─────────────────────────────────────────────────────────────

LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_DIR / "trend_analyzer.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("TrendAnalyzer")

# ─────────────────────────────────────────────────────────────
# الإعدادات
# ─────────────────────────────────────────────────────────────

OUTPUT_DIR = Path(__file__).parent / "news_output"
OUTPUT_DIR.mkdir(exist_ok=True)

# الكلمات الشائعة التي لا تحمل معنى ترند (Stop Words)
STOP_WORDS = {
    # English articles & prepositions
    "the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "of", "with",
    "by", "from", "is", "are", "was", "were", "it", "this", "that", "how", "what",
    "why", "who", "as", "you", "not", "can", "will", "do", "have", "out",
    "all", "its", "up", "about", "so", "if", "we", "be", "but", "your",
    "via", "using", "into", "their", "has", "over", "after", "some", "any", "no",
    "more", "than", "then", "them", "they", "his", "her", "she", "him",
    "been", "being", "am", "were", "had", "did", "does", "done",
    "which", "when", "where", "there", "here", "now", "also", "just",
    "like", "get", "got", "make", "made", "use", "used", "one", "two",
    "first", "last", "best", "top", "most", "very", "much", "many",
    # Common news words that aren't trends
    "new", "says", "said", "report", "reports", "according", "based",
    "could", "would", "should", "may", "might", "must", "shall",
    "week", "year", "day", "month", "time", "today", "yesterday",
    "news", "blog", "post", "article", "story", "read", "watch",
    "video", "image", "photo", "link", "url", "http", "https",
    "com", "org", "net", "www", "html", "php", "amp",
}

# ─────────────────────────────────────────────────────────────
# قاموس الشركات التقنية للتتبع
# ─────────────────────────────────────────────────────────────

COMPANIES = {
    # Big Tech
    "Google": ["google", "alphabet", "deepmind", "gemini", "bard"],
    "OpenAI": ["openai", "chatgpt", "gpt", "dall-e", "sora", "whisper"],
    "Microsoft": ["microsoft", "azure", "copilot", "bing", "windows", "office"],
    "Apple": ["apple", "iphone", "ipad", "macbook", "ios", "macos", "swift"],
    "Meta": ["meta", "facebook", "instagram", "whatsapp", "oculus", "quest", "llama"],
    "Amazon": ["amazon", "aws", "alexa", "ec2", "s3", "lambda", "bedrock"],
    "NVIDIA": ["nvidia", "cuda", "geforce", "rtx", "dgx", "tensorrt"],
    "Anthropic": ["anthropic", "claude", "sonnet", "opus", "haiku"],
    "Tesla": ["tesla", "elon", "musk", "spacex", "x.ai", "xai", "grok"],
    "Intel": ["intel", "xeon", "arc", "core"],
    "AMD": ["amd", "ryzen", "epyc", "radeon", "instinct"],
    "IBM": ["ibm", "watson", "red hat"],
    "GitHub": ["github", "copilot", "actions", "codespaces"],
    "Oracle": ["oracle", "java", "mysql"],
    "Samsung": ["samsung", "galaxy", "bixby"],
    "Cloudflare": ["cloudflare", "workers", "pages"],
    "Snowflake": ["snowflake"],
    "Databricks": ["databricks", "spark"],
    "Hugging Face": ["hugging face", "huggingface", "transformers"],
    "Stability AI": ["stability ai", "stabilityai", "stable diffusion"],
    "Mistral": ["mistral", "mixtral"],
    "Perplexity": ["perplexity"],
    "Vercel": ["vercel", "next.js", "nextjs"],
    "Stripe": ["stripe"],
    "Notion": ["notion"],
    "Figma": ["figma"],
    "Discord": ["discord"],
    "Slack": ["slack"],
    "Zoom": ["zoom"],
    "Uber": ["uber"],
    "TikTok": ["tiktok", "bytedance"],
    "LinkedIn": ["linkedin"],
    "X (Twitter)": ["twitter", "x.com", "tweet"],
}

# ─────────────────────────────────────────────────────────────
# قاموس المصطلحات التقنية للتتبع
# ─────────────────────────────────────────────────────────────

TECH_TERMS = {
    # AI / ML
    "AI": ["ai", "artificial intelligence", "a.i."],
    "Machine Learning": ["machine learning", "ml", "ml model"],
    "Deep Learning": ["deep learning", "neural network", "neural net"],
    "LLM": ["llm", "large language model", "language model"],
    "GPT": ["gpt", "gpt-4", "gpt-5", "chatgpt"],
    "RAG": ["rag", "retrieval augmented", "retrieval-augmented"],
    "Agent": ["agent", "agentic", "ai agent", "autonomous agent"],
    "Fine-tuning": ["fine-tuning", "fine tuning", "finetuning", "fine-tuned"],
    "Training": ["training", "train model", "model training"],
    "Inference": ["inference", "inference speed", "inference time"],
    "Embeddings": ["embedding", "embeddings", "vector embedding"],
    "Transformers": ["transformer", "transformers", "attention mechanism"],
    "Diffusion": ["diffusion", "stable diffusion", "diffusion model"],
    "Computer Vision": ["computer vision", "cv model", "image recognition"],
    "NLP": ["nlp", "natural language processing", "text processing"],
    "Generative AI": ["generative ai", "genai", "gen ai", "generative"],
    "Multimodal": ["multimodal", "multi-modal", "vision-language"],
    "RLHF": ["rlhf", "reinforcement learning", "human feedback"],
    "Quantization": ["quantization", "quantized", "quantize"],
    "Mixture of Experts": ["mixture of experts", "moe", "expert model"],

    # Programming
    "Python": ["python", "python3", "pytorch", "django", "flask", "fastapi"],
    "JavaScript": ["javascript", "js", "node", "node.js", "nodejs"],
    "TypeScript": ["typescript", "ts", "tsx"],
    "Rust": ["rust", "cargo", "rustlang"],
    "Go": ["golang", "go "],
    "Java": ["java", "jvm", "spring"],
    "C++": ["c++", "cpp"],
    "React": ["react", "reactjs", "react.js", "jsx"],
    "Vue": ["vue", "vuejs", "vue.js"],
    "Svelte": ["svelte", "sveltekit"],
    "Next.js": ["next.js", "nextjs", "next js"],
    "Docker": ["docker", "container", "containerize", "dockerfile"],
    "Kubernetes": ["kubernetes", "k8s", "kubectl"],
    "GraphQL": ["graphql", "gql"],
    "WebAssembly": ["webassembly", "wasm"],
    "Microservices": ["microservice", "microservices"],

    # Cloud / DevOps
    "Cloud": ["cloud", "cloud-native", "cloud native"],
    "Serverless": ["serverless", "lambda", "edge function"],
    "CI/CD": ["ci/cd", "cicd", "continuous integration", "continuous deployment"],
    "DevOps": ["devops", "devsecops"],
    "IaC": ["terraform", "infrastructure as code", "iac", "pulumi"],
    "Edge Computing": ["edge computing", "edge cloud", "edge ai"],

    # Data
    "Big Data": ["big data", "data pipeline", "data lake", "data warehouse"],
    "Data Science": ["data science", "data scientist", "data analysis"],
    "Pandas": ["pandas", "dataframe"],
    "Spark": ["apache spark", "pyspark"],
    "Vector DB": ["vector database", "vector db", "vector search", "pinecone", "weaviate", "milvus", "qdrant"],

    # Security
    "Cybersecurity": ["cybersecurity", "cyber security", "infosec"],
    "Zero Trust": ["zero trust", "zero-trust"],
    "Encryption": ["encryption", "encrypt", "decrypt", "cryptography"],
    "Vulnerability": ["vulnerability", "vulnerabilities", "cve", "exploit"],
    "Ransomware": ["ransomware", "malware", "ransom"],

    # Hardware
    "GPU": ["gpu", "gpus", "graphics processing"],
    "TPU": ["tpu", "tensor processing unit"],
    "Chip": ["chip", "semiconductor", "silicon", "foundry"],
    "Quantum": ["quantum", "quantum computing", "qubit"],

    # Web3 / Blockchain
    "Blockchain": ["blockchain", "blockchain technology"],
    "Crypto": ["crypto", "cryptocurrency", "bitcoin", "ethereum", "web3"],
    "NFT": ["nft", "nfts", "non-fungible"],

    # Mobile
    "iOS": ["ios", "iphone", "ipad", "swiftui"],
    "Android": ["android", "kotlin", "jetpack"],
    "Flutter": ["flutter", "dart"],

    # Other
    "API": ["api", "apis", "rest api", "api key"],
    "Open Source": ["open source", "opensource", "oss"],
    "SaaS": ["saas", "software as a service"],
    "Startup": ["startup", "startups", "funding", "series a", "seed round"],
    "IPO": ["ipo", "public offering", "going public"],
    "Acquisition": ["acquisition", "acquire", "acquired", "merger", "buyout"],
    "Beta": ["beta", "beta test", "beta version", "early access"],
    "Preview": ["preview", "early preview", "technical preview"],
    "Linux": ["linux", "ubuntu", "debian", "fedora"],
    "Windows": ["windows", "windows 11", "windows 12"],
    "macOS": ["macos", "mac os", "macbook", "mac"],
    "Browser": ["browser", "chrome", "firefox", "safari", "edge browser"],
    "5G": ["5g", "5g network"],
    "IoT": ["iot", "internet of things"],
    "AR/VR": ["ar/vr", "augmented reality", "virtual reality", "xr", "vision pro"],
    "Robotics": ["robotics", "robot", "robots", "humanoid"],
    "Autonomous": ["autonomous", "self-driving", "self driving", "autonomy"],
    "Sustainability": ["sustainability", "carbon", "green energy", "renewable"],
}

# ─────────────────────────────────────────────────────────────
# قاموس منتجات/أطر عمل الـ AI Agents المحددة
# ─────────────────────────────────────────────────────────────

AGENT_PRODUCTS = {
    # Big Tech Agent Products
    "GitHub Copilot Agent": ["copilot agent", "copilot agents", "github copilot agent"],
    "Amazon AgentCore": ["agentcore", "amazon agentcore", "aws agentcore"],
    "OpenAI Agent SDK": ["agent sdk", "openai agent", "openai agents", "agents sdk"],
    "OpenAI Swarm": ["swarm", "openai swarm", "swarm framework"],
    "Google Gemini Agent": ["gemini agent", "gemini agents", "gemini agentic"],
    "Google Computer Use": ["computer use", "computer-use", "gemini computer use"],
    "Anthropic Computer Use": ["claude computer use", "anthropic computer use"],
    "Microsoft Copilot Studio": ["copilot studio", "copilot agents", "microsoft agent"],
    "Meta Llama Agent": ["llama agent", "llama agentic"],
    "Apple Intelligence Agent": ["apple intelligence", "apple agent", "app intent"],

    # Agent Frameworks / Libraries
    "AutoGen": ["autogen", "auto-gen", "microsoft autogen"],
    "CrewAI": ["crewai", "crew ai", "crew-ai"],
    "LangGraph": ["langgraph", "lang-graph", "langchain agent"],
    "LangChain Agents": ["langchain agent", "langchain agents", "agent executor"],
    "AutoGPT": ["autogpt", "auto-gpt", "auto gpt"],
    "AgentGPT": ["agentgpt", "agent-gpt"],
    "SuperAGI": ["superagi", "super-agi"],
    "Devika": ["devika"],
    "Devin": ["devin agent", "devin ai", "cognition devin"],
    "OpenDevin": ["opendevin", "open-devin"],
    "SWE-agent": ["swe-agent", "swe agent", "swe-bench agent"],
    "Smolagents": ["smolagents", "smol-agent", "smol agent"],
    "CAMEL-AI": ["camel-ai", "camel ai", "camel agent"],
    "Phidata": ["phidata", "phi-data", "phi data agent"],
    "LlamaIndex Agents": ["llamaindex agent", "llama index agent"],
    "Haystack Agents": ["haystack agent", "haystack agents"],
    "Semantic Kernel": ["semantic kernel", "semantic-kernel"],

    # Agent Platforms / Tools
    "Browser Use": ["browser use", "browser-use", "browser agent"],
    "Multi-Agent": ["multi-agent", "multi agent", "multiagent"],
    "AgentOps": ["agentops", "agent-ops"],
    "LangSmith": ["langsmith", "lang smith"],
    "Inferable": ["inferable", "inferable agent"],
    "RestGPT": ["restgpt", "rest-gpt"],

    # Research / Academic Agents
    "Voyager": ["voyager agent", "voyager minecraft"],
    "Generative Agents": ["generative agent", "generative agents", "stanford agents"],
    "ReAct Agent": ["react agent", "reasoning acting", "reasoning-acting"],
    "Reflexion": ["reflexion agent", "reflexion"],
    "Toolformer": ["toolformer"],
    "Hermes Agent": ["hermes-agent", "hermes agent"],
}

# ─────────────────────────────────────────────────────────────
# أسماء المصادر بالعربية للعرض
# ─────────────────────────────────────────────────────────────

SOURCE_NAMES = {
    "hacker_news": "Hacker News",
    "reddit": "Reddit",
    "github": "GitHub",
    "devto": "Dev.to",
    "lobsters": "Lobsters",
    "product_hunt": "Product Hunt",
    "arxiv": "arXiv",
    "x": "X (Twitter)",
    "youtube": "YouTube",
    "medium": "Medium",
    "company_blogs": "Company Blogs",
    "tech_news": "Tech News",
    "google_news": "Google News",
}

# ─────────────────────────────────────────────────────────────
# دوال مساعدة
# ─────────────────────────────────────────────────────────────

def load_json_files(days: int | None = None) -> list[dict]:
    """تحميل جميع ملفات JSON المحفوظة، مع فلترة اختيارية بالتاريخ."""
    json_files = glob.glob(str(OUTPUT_DIR / "tech_news_raw_*.json"))

    if not json_files:
        return []

    # ترتيب الملفات حسب الاسم (الذي يحوي التاريخ)
    json_files.sort()

    cutoff_date = None
    if days is not None:
        cutoff_date = datetime.now() - timedelta(days=days)

    datasets = []
    for file_path in json_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # فلترة بالتاريخ
            if cutoff_date and "generated_at" in data:
                file_date = datetime.fromisoformat(data["generated_at"])
                if file_date < cutoff_date:
                    continue

            datasets.append(data)
        except Exception as e:
            logger.warning(f"تخطي ملف تالف: {file_path} - {e}")

    return datasets


def extract_all_text(story: dict) -> str:
    """استخراج كل النص من قصة للبحث داخله."""
    parts = [
        str(story.get("title", "")),
        str(story.get("description", "")),
        str(story.get("tagline", "")),
        str(story.get("snippet", "")),
    ]
    tags = story.get("tags", [])
    if isinstance(tags, list):
        parts.append(" ".join(str(t) for t in tags))
    categories = story.get("categories", [])
    if isinstance(categories, list):
        parts.append(" ".join(str(c) for c in categories))
    return " ".join(parts).lower()


def count_term_mentions(text: str, patterns: list[str]) -> int:
    """عدّ مرات ذكر مصطلح في نص (بأي من أنماطه)."""
    count = 0
    for pattern in patterns:
        # استخدام word boundary للكلمات القصيرة
        if len(pattern) <= 3:
            matches = re.findall(r'\b' + re.escape(pattern) + r'\b', text)
        else:
            matches = re.findall(re.escape(pattern), text)
        count += len(matches)
    return count


def trend_arrow(current: int, previous: int) -> str:
    """حساب اتجاه التريند: صاعد 📈 / ثابت ➡️ / هابط 📉 / جديد 🆕."""
    if previous == 0 and current > 0:
        return "🆕 جديد"
    if previous == 0 and current == 0:
        return "—"
    change_pct = ((current - previous) / previous) * 100 if previous > 0 else 0
    if change_pct > 20:
        return f"📈 +{change_pct:.0f}%"
    elif change_pct < -20:
        return f"📉 {change_pct:.0f}%"
    else:
        return f"➡️ {change_pct:+.0f}%"


def discover_agent_names(text: str, known_patterns: set[str]) -> list[str]:
    """
    اكتشاف تلقائي لأسماء منتجات/أطر عمل Agents جديدة من السياق.
    يبحث عن أنماط مثل:
      - "X Agent" (مثل: Copilot Agent, Hermes Agent)
      - "AgentX" / "AgentCore" (كلمة واحدة تبدأ بـ Agent)
      - "X-agent" (مثل: SWE-agent, hermes-agent)
    يتجاهل الأنماط المعروفة بالفعل.
    """
    discovered = []

    # نمط 1: "Word Agent" — كلمة قبل Agent
    for m in re.finditer(r'\b([A-Za-z][a-z]+)\s+agent[s]?\b', text):
        name = m.group(1).lower()
        full = f"{name} agent"
        if full not in known_patterns and name not in STOP_WORDS and len(name) >= 3:
            discovered.append(f"{name.title()} Agent")

    # نمط 2: "AgentWord" — كلمة تبدأ بـ Agent (مثل AgentCore, AgentGPT)
    for m in re.finditer(r'\bagent([A-Z][a-z]+)\b', text):
        suffix = m.group(1)
        full = f"agent{suffix}"
        if full.lower() not in known_patterns:
            discovered.append(f"Agent{suffix}")

    # نمط 3: "word-agent" — مفصول بشرطة (مثل swe-agent, hermes-agent)
    for m in re.finditer(r'\b([a-z]+)-agent[s]?\b', text):
        name = m.group(1)
        full = f"{name}-agent"
        if full not in known_patterns and name not in STOP_WORDS and len(name) >= 3:
            discovered.append(f"{name.title()}-agent")

    # نمط 4: "WordAgents" / "Word Agent" — للجمع
    for m in re.finditer(r'\b([A-Z][a-z]+)\s+[Aa]gents\b', text):
        name = m.group(1)
        full = f"{name.lower()} agents"
        if full not in known_patterns and name.lower() not in STOP_WORDS and len(name) >= 3:
            discovered.append(f"{name} Agents")

    return discovered


# ═════════════════════════════════════════════════════════════
# المحلل الرئيسي
# ═════════════════════════════════════════════════════════════

class TrendAnalyzer:
    """المحلل الاحترافي للتريندات التقنية."""

    def __init__(self, days: int = 7, top_n: int = 15):
        self.days = days
        self.top_n = top_n
        self.now = datetime.now()

        # النتائج
        self.company_mentions: dict[str, int] = {}
        self.tech_term_mentions: dict[str, int] = {}
        self.agent_product_mentions: dict[str, int] = {}
        self.discovered_agents: dict[str, int] = {}
        self.keyword_freq: Counter = Counter()
        self.source_breakdown: dict[str, dict[str, int]] = {}
        self.trend_directions: dict[str, dict] = {}

        # للاتجاه (مقارنة الفترة الحالية بالسابقة)
        self.current_company: dict[str, int] = {}
        self.previous_company: dict[str, int] = {}
        self.current_tech: dict[str, int] = {}
        self.previous_tech: dict[str, int] = {}
        self.current_agents: dict[str, int] = {}
        self.previous_agents: dict[str, int] = {}

    def analyze(self) -> None:
        """تشغيل التحليل الكامل."""
        logger.info("=" * 60)
        logger.info(f"📊 بدء تحليل التريندات (آخر {self.days} يوم)...")
        logger.info("=" * 60)

        # ── تحميل البيانات للفترة الحالية ──
        current_datasets = load_json_files(days=self.days)
        if not current_datasets:
            logger.error("❌ لا توجد بيانات للتحليل. شغّل المُجمّع أولاً.")
            return

        # ── تحميل البيانات للفترة السابقة (للمقارنة) ──
        # الفترة السابقة = الأيام من (days) إلى (days*2)
        all_datasets = load_json_files(days=self.days * 2)
        previous_datasets = []
        cutoff = self.now - timedelta(days=self.days)
        for ds in all_datasets:
            gen_date = ds.get("generated_at", "")
            if gen_date:
                try:
                    fdate = datetime.fromisoformat(gen_date)
                    if fdate < cutoff:
                        previous_datasets.append(ds)
                except Exception:
                    pass

        logger.info(f"  📁 ملفات الفترة الحالية: {len(current_datasets)}")
        logger.info(f"  📁 ملفات الفترة السابقة: {len(previous_datasets)}")

        # ── تحليل الفترة الحالية ──
        (self.current_company, self.current_tech, self.keyword_freq,
         self.source_breakdown, self.current_agents, self.discovered_agents) = \
            self._analyze_datasets(current_datasets)

        # ── تحليل الفترة السابقة ──
        if previous_datasets:
            (self.previous_company, self.previous_tech, _, _,
             self.previous_agents, _) = \
                self._analyze_datasets(previous_datasets)
        else:
            logger.info("  ℹ️ لا توجد بيانات سابقة للمقارنة — سيظهر كل ترند كـ 'جديد'")

        # دمج النتائج
        self.company_mentions = self.current_company
        self.tech_term_mentions = self.current_tech
        self.agent_product_mentions = self.current_agents

        # حساب اتجاهات التريند
        self._compute_trend_directions()

        total_stories = sum(
            len(stories) for ds in current_datasets
            for stories in ds.get("sources", {}).values()
        )
        logger.info(f"  📊 إجمالي القصص المحللة: {total_stories}")
        logger.info(f"  🏢 شركات مُكتشفة: {len(self.company_mentions)}")
        logger.info(f"  🔧 مصطلحات تقنية: {len(self.tech_term_mentions)}")
        logger.info(f"  🤖 منتجات AI Agents: {len(self.agent_product_mentions)}")
        logger.info(f"  ✨ Agents مُكتشفة تلقائياً: {len(self.discovered_agents)}")
        logger.info("=" * 60)

    def _analyze_datasets(self, datasets: list[dict]) -> tuple:
        """تحليل مجموعة ملفات بيانات وإرجاع الإحصائيات."""
        company_counts: dict[str, int] = defaultdict(int)
        tech_counts: dict[str, int] = defaultdict(int)
        agent_counts: dict[str, int] = defaultdict(int)
        discovered_agent_counts: dict[str, int] = defaultdict(int)
        all_words: list[str] = []
        source_breakdown: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # بناء set من كل الأنماط المعروفة لتجنب اكتشافها كـ "جديدة"
        known_agent_patterns = set()
        for patterns in AGENT_PRODUCTS.values():
            for p in patterns:
                known_agent_patterns.add(p.lower())

        for data in datasets:
            for source_key, stories in data.get("sources", {}).items():
                source_name = SOURCE_NAMES.get(source_key, source_key)

                for story in stories:
                    text = extract_all_text(story)

                    # تتبع الشركات
                    for company, patterns in COMPANIES.items():
                        count = count_term_mentions(text, patterns)
                        if count > 0:
                            company_counts[company] += count
                            source_breakdown[source_name][company] += count

                    # تتبع المصطلحات التقنية
                    for term, patterns in TECH_TERMS.items():
                        count = count_term_mentions(text, patterns)
                        if count > 0:
                            tech_counts[term] += count
                            source_breakdown[source_name][term] += count

                    # تتبع منتجات/أطر عمل الـ AI Agents المحددة
                    for agent_name, patterns in AGENT_PRODUCTS.items():
                        count = count_term_mentions(text, patterns)
                        if count > 0:
                            agent_counts[agent_name] += count
                            source_breakdown[source_name][agent_name] += count

                    # اكتشاف تلقائي لأسماء Agents جديدة من السياق
                    if "agent" in text:
                        discovered = discover_agent_names(text, known_agent_patterns)
                        for name in discovered:
                            discovered_agent_counts[name] += 1

                    # الكلمات المفتاحية العامة
                    title = str(story.get("title", "")).lower()
                    words = re.findall(r'\b[a-z]{3,}\b', title)
                    all_words.extend(words)

        # تصفية الكلمات الشائعة
        meaningful_words = [w for w in all_words if w not in STOP_WORDS]
        keyword_freq = Counter(meaningful_words)

        return (dict(company_counts), dict(tech_counts), keyword_freq,
                dict(source_breakdown), dict(agent_counts), dict(discovered_agent_counts))

    def _compute_trend_directions(self) -> None:
        """حساب اتجاهات التريند (صاعد/ثابت/هابط) لكل شركة ومصطلح."""
        trends = {}

        for company in set(list(self.current_company.keys()) + list(self.previous_company.keys())):
            curr = self.current_company.get(company, 0)
            prev = self.previous_company.get(company, 0)
            if curr > 0 or prev > 0:
                trends[company] = {
                    "current": curr,
                    "previous": prev,
                    "direction": trend_arrow(curr, prev),
                    "type": "company",
                }

        for term in set(list(self.current_tech.keys()) + list(self.previous_tech.keys())):
            curr = self.current_tech.get(term, 0)
            prev = self.previous_tech.get(term, 0)
            if curr > 0 or prev > 0:
                trends[term] = {
                    "current": curr,
                    "previous": prev,
                    "direction": trend_arrow(curr, prev),
                    "type": "tech",
                }

        # منتجات/أطر عمل الـ AI Agents
        for agent in set(list(self.current_agents.keys()) + list(self.previous_agents.keys())):
            curr = self.current_agents.get(agent, 0)
            prev = self.previous_agents.get(agent, 0)
            if curr > 0 or prev > 0:
                trends[agent] = {
                    "current": curr,
                    "previous": prev,
                    "direction": trend_arrow(curr, prev),
                    "type": "agent",
                }

        self.trend_directions = trends

    # ═════════════════════════════════════════════════════════
    # توليد تقرير Markdown
    # ═════════════════════════════════════════════════════════

    def generate_report(self) -> Path:
        """توليد تقرير Markdown احترافي."""
        sections: list[str] = []

        # ── الرأس ──
        date_str = self.now.strftime("%Y-%m-%d")
        time_str = self.now.strftime("%H:%M")
        period_end = self.now.strftime("%Y-%m-%d")
        period_start = (self.now - timedelta(days=self.days)).strftime("%Y-%m-%d")

        sections.append(f"""<div align="center">

# 📊 تقرير تحليل التريندات التقنية

### 📅 {date_str} | ⏰ {time_str} | 🔍 آخر {self.days} يوم ({period_start} → {period_end})

---

> **تحليل احترافي** للتريندات التقنية من الأخبار المُجمّعة
> تتبع الشركات • المصطلحات التقنية • اتجاهات التريند • تحليل المصادر

---

</div>
""")

        # ── 1. ملخص تنفيذي ──
        total_companies = len(self.company_mentions)
        total_tech = len(self.tech_term_mentions)
        rising = sum(1 for t in self.trend_directions.values()
                     if "📈" in t["direction"])
        falling = sum(1 for t in self.trend_directions.values()
                      if "📉" in t["direction"])
        new_trends = sum(1 for t in self.trend_directions.values()
                         if "🆕" in t["direction"])

        # أعلى شركة وأعلى مصطلح
        top_company = max(self.company_mentions, key=self.company_mentions.get) \
            if self.company_mentions else "—"
        top_company_count = self.company_mentions.get(top_company, 0)
        top_tech = max(self.tech_term_mentions, key=self.tech_term_mentions.get) \
            if self.tech_term_mentions else "—"
        top_tech_count = self.tech_term_mentions.get(top_tech, 0)

        total_agents = len(self.agent_product_mentions) + len(self.discovered_agents)
        top_agent = max(self.agent_product_mentions, key=self.agent_product_mentions.get) \
            if self.agent_product_mentions else "—"
        top_agent_count = self.agent_product_mentions.get(top_agent, 0)

        sections.append(f"""## 📋 الملخص التنفيذي

| المؤشر | القيمة |
|--------|--------|
| 📅 فترة التحليل | آخر **{self.days}** يوم |
| 🏢 عدد الشركات المُتتبَّعة | **{total_companies}** |
| 🔧 عدد المصطلحات التقنية | **{total_tech}** |
| 🤖 منتجات AI Agents | **{total_agents}** |
| 📈 تريندات صاعدة | **{rising}** |
| 📉 تريندات هابطة | **{falling}** |
| 🆕 تريندات جديدة | **{new_trends}** |
| 🏆 الشركة الأكثر ذكراً | **{top_company}** ({top_company_count} ذكر) |
| 🔥 المصطلح الأكثر تداولاً | **{top_tech}** ({top_tech_count} ذكر) |
| 🤖 المنتج الأكثر ذكراً | **{top_agent}** ({top_agent_count} ذكر) |

---
""")

        # ── 2. تتبع الشركات ──
        sections.append(self._section_companies())

        # ── 3. المصطلحات التقنية ──
        sections.append(self._section_tech_terms())

        # ── 4. منتجات/أطر عمل الـ AI Agents ──
        sections.append(self._section_agent_products())

        # ── 5. اتجاهات التريند (صاعد/هابط) ──
        sections.append(self._section_trend_directions())

        # ── 6. الكلمات المفتاحية الأكثر تداولاً ──
        sections.append(self._section_keywords())

        # ── 6. تحليل لكل مصدر ──
        sections.append(self._section_per_source())

        # ── 7. التذييل ──
        sections.append(self._section_footer())

        # ── حفظ ──
        filename = f"trend_report_{self.now.strftime('%Y-%m-%d_%H%M')}.md"
        filepath = OUTPUT_DIR / filename
        filepath.write_text("\n".join(sections), encoding="utf-8")
        logger.info(f"📄 تم حفظ تقرير التريند: {filepath}")
        return filepath

    def _section_companies(self) -> str:
        """قسم تتبع الشركات."""
        if not self.company_mentions:
            return "## 🏢 تتبع الشركات\n\n> ⚠️ لم يتم العثور على ذكر للشركات\n\n---\n"

        sorted_companies = sorted(self.company_mentions.items(),
                                  key=lambda x: x[1], reverse=True)[:self.top_n]

        section = f"""
## 🏢 تتبع الشركات التقنية

> أكثر الشركات ذكراً في الأخبار التقنية (آخر {self.days} يوم)

| # | الشركة | 🔢 الذكر | 📊 الاتجاه |
|---|---------|-----------|-----------|
"""
        for i, (company, count) in enumerate(sorted_companies, 1):
            trend = self.trend_directions.get(company, {})
            direction = trend.get("direction", "—")
            section += f"| {i} | **{company}** | {count} | {direction} |\n"

        section += "\n---\n"
        return section

    def _section_tech_terms(self) -> str:
        """قسم المصطلحات التقنية."""
        if not self.tech_term_mentions:
            return "## 🔧 المصطلحات التقنية\n\n> ⚠️ لم يتم العثور على مصطلحات تقنية\n\n---\n"

        sorted_terms = sorted(self.tech_term_mentions.items(),
                              key=lambda x: x[1], reverse=True)[:self.top_n]

        section = f"""
## 🔧 المصطلحات التقنية الرائجة

> أكثر المصطلحات التقنية تداولاً (آخر {self.days} يوم)

| # | المصطلح | 🔢 الذكر | 📊 الاتجاه |
|---|---------|-----------|-----------|
"""
        for i, (term, count) in enumerate(sorted_terms, 1):
            trend = self.trend_directions.get(term, {})
            direction = trend.get("direction", "—")
            section += f"| {i} | **{term}** | {count} | {direction} |\n"

        section += "\n---\n"
        return section

    def _section_agent_products(self) -> str:
        """قسم منتجات/أطر عمل الـ AI Agents المحددة."""
        # دمج المنتجات المعروفة مع المُكتشفة تلقائياً
        all_agents = dict(self.agent_product_mentions)
        for name, count in self.discovered_agents.items():
            if name not in all_agents:
                all_agents[name] = count

        if not all_agents:
            return "## 🤖 منتجات وأطر عمل AI Agents\n\n> ⚠️ لم يتم العثور على منتجات Agents محددة\n\n---\n"

        sorted_agents = sorted(all_agents.items(), key=lambda x: x[1], reverse=True)

        # فصل المعروفة عن المُكتشفة
        known = [(n, c) for n, c in sorted_agents if n in self.agent_product_mentions]
        discovered = [(n, c) for n, c in sorted_agents if n not in self.agent_product_mentions]

        section = f"""
## 🤖 منتجات وأطر عمل AI Agents

> تتبع منتجات/أطر عمل الـ AI Agents المحددة (وليس الكلمة العامة "agent")

### 🏷️ منتجات/أطر معروفة

| # | المنتج/الإطار | 🔢 الذكر | 📊 الاتجاه |
|---|---------------|-----------|-----------|
"""
        if known:
            for i, (name, count) in enumerate(known[:self.top_n], 1):
                trend = self.trend_directions.get(name, {})
                direction = trend.get("direction", "—")
                section += f"| {i} | **{name}** | {count} | {direction} |\n"
        else:
            section += "| — | لا توجد منتجات معروفة في هذه الفترة | — | — |\n"

        if discovered:
            section += f"""
### ✨ Agents مُكتشفة تلقائياً (جديدة/غير موجودة في القاموس)

> تم اكتشافها من تحليل السياق حول كلمة "agent" — قد تكون منتجات جديدة

| # | الاسم المُكتشف | 🔢 الذكر |
|---|---------------|-----------|
"""
            for i, (name, count) in enumerate(discovered[:self.top_n], 1):
                section += f"| {i} | `{name}` | {count} |\n"
        else:
            section += "\n> ℹ️ لم يتم اكتشاف أسماء Agents جديدة تلقائياً\n"

        section += "\n---\n"
        return section

    def _section_trend_directions(self) -> str:
        """قسم اتجاهات التريند — الصاعدة والهابطة."""
        if not self.trend_directions:
            return "## 📈📉 اتجاهات التريند\n\n> ⚠️ لا توجد بيانات كافية لتحديد الاتجاهات\n\n---\n"

        # تصنيف التريندات
        rising = []
        falling = []
        new_trends = []

        for name, data in self.trend_directions.items():
            direction = data["direction"]
            entry = (name, data["current"], data["previous"], direction, data["type"])

            if "📈" in direction:
                rising.append(entry)
            elif "📉" in direction:
                falling.append(entry)
            elif "🆕" in direction:
                new_trends.append(entry)

        # ترتيب
        rising.sort(key=lambda x: x[1], reverse=True)
        falling.sort(key=lambda x: x[2], reverse=True)
        new_trends.sort(key=lambda x: x[1], reverse=True)

        section = f"""
## 📈📉 اتجاهات التريند — الصاعد والهابط

> مقارنة الفترة الحالية (آخر {self.days} يوم) بالفترة السابقة

### 📈 تريندات صاعدة

| # | الاسم | 🔢 الحالي | 🔢 السابق | 📊 التغيّر | 🏷️ النوع |
|---|-------|-----------|-----------|-----------|-----------|
"""
        if rising:
            for i, (name, curr, prev, direction, typ) in enumerate(rising[:10], 1):
                type_icon = "🏢" if typ == "company" else "🔧"
                section += f"| {i} | **{name}** | {curr} | {prev} | {direction} | {type_icon} |\n"
        else:
            section += "| — | لا توجد تريندات صاعدة | — | — | — | — |\n"

        section += f"""
### 📉 تريندات هابطة

| # | الاسم | 🔢 الحالي | 🔢 السابق | 📊 التغيّر | 🏷️ النوع |
|---|-------|-----------|-----------|-----------|-----------|
"""
        if falling:
            for i, (name, curr, prev, direction, typ) in enumerate(falling[:10], 1):
                type_icon = "🏢" if typ == "company" else "🔧"
                section += f"| {i} | **{name}** | {curr} | {prev} | {direction} | {type_icon} |\n"
        else:
            section += "| — | لا توجد تريندات هابطة | — | — | — | — |\n"

        section += f"""
### 🆕 تريندات جديدة (لم تظهر في الفترة السابقة)

| # | الاسم | 🔢 الحالي | 🏷️ النوع |
|---|-------|-----------|-----------|
"""
        if new_trends:
            for i, (name, curr, prev, direction, typ) in enumerate(new_trends[:10], 1):
                type_icon = "🏢" if typ == "company" else "🔧"
                section += f"| {i} | **{name}** | {curr} | {type_icon} |\n"
        else:
            section += "| — | لا توجد تريندات جديدة | — | — |\n"

        section += "\n---\n"
        return section

    def _section_keywords(self) -> str:
        """قسم الكلمات المفتاحية الأكثر تداولاً."""
        if not self.keyword_freq:
            return "## 🔤 الكلمات المفتاحية\n\n> ⚠️ لا توجد كلمات مفتاحية\n\n---\n"

        top_keywords = self.keyword_freq.most_common(self.top_n)

        section = f"""
## 🔤 الكلمات المفتاحية الأكثر تداولاً

> استخراج تلقائي من عناوين الأخبار (بعد تصفية الكلمات الشائعة)

| # | الكلمة | 🔢 التكرار |
|---|--------|-----------|
"""
        for i, (word, count) in enumerate(top_keywords, 1):
            section += f"| {i} | `{word}` | **{count}** |\n"

        section += "\n---\n"
        return section

    def _section_per_source(self) -> str:
        """قسم التحليل لكل مصدر."""
        if not self.source_breakdown:
            return "## 📡 تحليل المصادر\n\n> ⚠️ لا توجد بيانات للمصادر\n\n---\n"

        section = f"""
## 📡 تحليل المصادر — ماذا يتحدث كل مصدر؟

> أكثر الشركات والمصطلحات ذكراً في كل مصدر

"""
        for source_name, terms in sorted(self.source_breakdown.items()):
            if not terms:
                continue
            # أعلى 5 لكل مصدر
            top_for_source = sorted(terms.items(), key=lambda x: x[1], reverse=True)[:5]
            if not top_for_source:
                continue

            top_items = " • ".join([f"`{name}` ({count})" for name, count in top_for_source])
            section += f"### 📡 {source_name}\n\n> {top_items}\n\n"

        section += "---\n"
        return section

    def _section_footer(self) -> str:
        """تذييل التقرير."""
        return f"""
<div align="center">

---

> 🤖 تم إنشاء هذا التقرير بواسطة **مُحلّل التريندات التقنية v2.0**
>
> ⏰ آخر تحديث: {self.now.strftime('%Y-%m-%d %H:%M:%S')}
>
> 📊 فترة التحليل: آخر **{self.days}** يوم

</div>
"""

    # ═════════════════════════════════════════════════════════
    # ملخص سريع للطباعة في الكونسول
    # ═════════════════════════════════════════════════════════

    def print_summary(self) -> None:
        """طباعة ملخص سريع في الكونسول."""
        print("\n" + "=" * 60)
        print(f"📊 ملخص التريندات (آخر {self.days} يوم)")
        print("=" * 60)

        # الشركات
        if self.company_mentions:
            print(f"\n🏢 أعلى {min(5, len(self.company_mentions))} شركات:")
            for i, (company, count) in enumerate(
                sorted(self.company_mentions.items(), key=lambda x: x[1], reverse=True)[:5], 1
            ):
                direction = self.trend_directions.get(company, {}).get("direction", "")
                print(f"  {i}. {company:<20s} ({count:>3d} ذكر)  {direction}")

        # المصطلحات
        if self.tech_term_mentions:
            print(f"\n🔧 أعلى {min(5, len(self.tech_term_mentions))} مصطلحات تقنية:")
            for i, (term, count) in enumerate(
                sorted(self.tech_term_mentions.items(), key=lambda x: x[1], reverse=True)[:5], 1
            ):
                direction = self.trend_directions.get(term, {}).get("direction", "")
                print(f"  {i}. {term:<20s} ({count:>3d} ذكر)  {direction}")

        # منتجات AI Agents
        all_agents = dict(self.agent_product_mentions)
        for name, count in self.discovered_agents.items():
            if name not in all_agents:
                all_agents[name] = count
        if all_agents:
            print(f"\n🤖 منتجات/أطر AI Agents ({len(all_agents)}):")
            for i, (name, count) in enumerate(
                sorted(all_agents.items(), key=lambda x: x[1], reverse=True)[:5], 1
            ):
                tag = "✨" if name not in self.agent_product_mentions else "🏷️"
                print(f"  {i}. {tag} {name:<25s} ({count:>3d} ذكر)")

        # التريندات الصاعدة
        rising = [(n, d) for n, d in self.trend_directions.items() if "📈" in d["direction"]]
        if rising:
            print(f"\n📈 تريندات صاعدة ({len(rising)}):")
            for name, data in sorted(rising, key=lambda x: x[1]["current"], reverse=True)[:5]:
                print(f"  🔥 {name:<20s} {data['direction']}")

        # التريندات الجديدة
        new_trends = [(n, d) for n, d in self.trend_directions.items() if "🆕" in d["direction"]]
        if new_trends:
            print(f"\n🆕 تريندات جديدة ({len(new_trends)}):")
            for name, data in sorted(new_trends, key=lambda x: x[1]["current"], reverse=True)[:5]:
                print(f"  ✨ {name:<20s} ({data['current']} ذكر)")

        print("\n" + "=" * 60)


# ═════════════════════════════════════════════════════════════
# نقطة الدخول
# ═════════════════════════════════════════════════════════════

def main():
    """الدالة الرئيسية."""
    parser = argparse.ArgumentParser(
        description="📊 مُحلّل التريندات التقنية الاحترافي"
    )
    parser.add_argument(
        "--days", "-d", type=int, default=7,
        help="عدد الأيام السابقة للتحليل (افتراضي: 7)"
    )
    parser.add_argument(
        "--top", "-t", type=int, default=15,
        help="عدد النتائج الأعلى لعرضها في كل قسم (افتراضي: 15)"
    )
    args = parser.parse_args()

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║       📊 مُحلّل التريندات التقنية الاحترافي 📊           ║
    ║       Professional Tech Trend Analyzer v2.0              ║
    ╠══════════════════════════════════════════════════════════╣
    ║  📡 الميزات:                                             ║
    ║    🏢 تتبع الشركات   🔧 تتبع المصطلحات التقنية          ║
    ║    📈📉 اتجاه التريند  📡 تحليل لكل مصدر                 ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    analyzer = TrendAnalyzer(days=args.days, top_n=args.top)
    analyzer.analyze()

    if analyzer.company_mentions or analyzer.tech_term_mentions:
        analyzer.print_summary()
        report_path = analyzer.generate_report()

        print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║  ✅ اكتمل التحليل بنجاح!                                 ║
    ╠══════════════════════════════════════════════════════════╣
    ║  📄 تقرير التريند: {str(report_path):<42s} ║
    ╚══════════════════════════════════════════════════════════╝
        """)
    else:
        print("❌ لا توجد بيانات كافية للتحليل. شغّل المُجمّع أولاً:")
        print("   python tech_news_aggregator.py")


if __name__ == "__main__":
    main()
