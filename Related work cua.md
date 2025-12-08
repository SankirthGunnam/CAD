### 3. Related Work

The field of Agents for Computer Use (ACUs) has seen rapid evolution, particularly since the advent of large vision-language models (VLMs) and foundation LLMs in 2023–2024. A comprehensive survey by Li et al. (2025) categorizes ACUs across domains (e.g., web, Android, personal computers), observation spaces (textual vs. image-based), action primitives (mouse/keyboard simulation vs. direct UI access), and agent architectures (specialized RL/BC models vs. prompted foundation models).<grok:render card_id="84bc6d" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">16</argument>
</grok:render> Key trends include a shift toward image-based observations for better generalization in dynamic environments and behavioral cloning (BC) as the dominant learning paradigm for efficiency.<grok:render card_id="ef697b" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render> However, gaps persist in privacy-preserving deployments, non-stationary real-world adaptation, and safety mechanisms for sensitive office automation tasks—areas where cloud-dependent systems risk data leakage via API calls.<grok:render card_id="7a242a" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render>

#### 3.1 Foundational ACU Benchmarks and Datasets
Early works focused on web navigation, with benchmarks like MiniWoB++ (Liu et al., 2018) enabling simple form-filling tasks via RL. More recent datasets emphasize realism: Mind2Web (Deng et al., 2023) spans 137 websites with 2,350 cross-domain demos, while WebArena (Zhou et al., 2023) simulates e-commerce and content management for long-horizon planning.<grok:render card_id="66c5a2" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render> For desktop environments, OSWorld (Kannan et al., 2024) provides 9,802 tasks across 57 apps, using multimodal screenshots for grounding.<grok:render card_id="299682" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render> Office-specific benchmarks like OfficeBench (Ahn et al., 2024) target productivity tools (e.g., Excel, PowerPoint), evaluating LLMs on multi-step automation with success rates under 40% for unadapted models.<grok:render card_id="4f15ec" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render> These resources highlight the brittleness of textual observations in non-stationary UIs, favoring vision-based approaches for office settings.

#### 3.2 Key ACU Systems
Prominent systems leverage VLMs for grounding and LLMs for planning:

- **SeeAct (Zhang et al., 2023)**: A vision-augmented code agent that grounds natural language actions (e.g., "click submit") into executable Python via Selenium, achieving 70% success on WebArena. It excels in web tasks but requires internet access for browser control, limiting local deployment.<grok:render card_id="98abd0" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render>

- **OpenAI Computer-Using Agent (CUA) (Ahn et al., 2024)**: Built on GPT-4V, this agent observes screenshots and executes mouse/keyboard actions for general PC tasks, reporting 48% success on OSWorld. While versatile, it relies on cloud APIs, raising privacy concerns for enterprise data.<grok:render card_id="5bc5d5" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render>

- **CogAgent (Hong et al., 2024)**: A VLM fine-tuned on GUI datasets for perception and action prediction, supporting both web and desktop with 55% accuracy on Mind2Web. It uses direct UI access where possible but lacks built-in orchestration for multi-agent office workflows.<grok:render card_id="af58ec" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render>

- **Google Antigravity (Google, 2025)**: Released in November 2025 as an agentic development platform powered by Gemini 3 Pro, Antigravity transforms traditional IDEs into "agent-first" environments where autonomous agents handle planning, execution, and verification of complex coding tasks via natural language.<grok:render card_id="962cef" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">3</argument>
</grok:render> Key features include synchronized control across editor, terminal, and browser (e.g., browser-in-the-loop agents for frontend automation), multi-agent orchestration via a "mission control" view, and artifact-based verification for transparency.<grok:render card_id="ae3565" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">8</argument>
</grok:render> It supports tab autocompletion and user feedback loops to refine agent behavior, achieving high efficiency in developer workflows (e.g., scripting beyond 500 lines).<grok:render card_id="c7a397" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">2</argument>
</grok:render> However, as a cloud-hosted tool in free preview, it transmits data to Google's infrastructure, contrasting with privacy-focused needs; no on-premise options are detailed, and early incidents highlight risks like unintended file deletions during autonomous execution.<grok:render card_id="e0d050" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">5</argument>
</grok:render> Antigravity represents a commercial push toward agentic coding but underscores gaps in secure, local control for non-developer office automation.

Other notables include Mobile-Agent (Wang et al., 2024) for Android grounding and WebVoyager (Yang et al., 2024) for end-to-end web tasks with multimodal planning.<grok:render card_id="019378" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render>

#### 3.3 Privacy and Local Deployment in ACUs
Privacy emerges as a critical gap: Agents often capture sensitive screenshots or files, with API-based systems (e.g., GPT-4V) risking leakage.<grok:render card_id="fe5d38" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render> Local deployments mitigate this via on-device LLMs (e.g., fine-tuned Llama variants), but face hardware diversity and latency challenges (e.g., $0.28/task for cloud equivalents).<grok:render card_id="5a6232" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render> Works like UINav (Liu et al., 2024) explore on-device mobile automation, while safety mitigations advocate conditional autonomy (user veto on critical actions).<grok:render card_id="80100c" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render> Our system addresses these by enforcing fully on-premise processing, aligning with enterprise needs underexplored in current benchmarks.

#### 3.4 Comparison of Representative Systems
Table 1 summarizes key systems against our framework, highlighting trade-offs in deployment, privacy, and scope.

| System              | Domain Focus | Observation | Action Primitives       | Deployment | Privacy Model          | Office Automation Fit |
|---------------------|--------------|-------------|-------------------------|------------|------------------------|-----------------------|
| SeeAct (2023)      | Web         | Image/Text | Code (Selenium)        | Cloud     | API-dependent         | Low (web-only)       |
| OpenAI CUA (2024)  | PC/Web      | Image      | Mouse/Keyboard         | Cloud     | Data transmission     | Medium (general PC)  |
| CogAgent (2024)    | GUI/Multi   | Image      | Direct UI/Code         | Hybrid    | Model-dependent       | Medium (GUI tasks)   |
| Google Antigravity (2025) | Dev/IDE  | Multi-modal| Browser/Editor/Terminal| Cloud     | Google-hosted         | High (dev workflows) |
| Ours               | PC/Office   | Image      | Mouse/Keyboard (MCP)   | Local     | Fully on-premise      | High (private office)|

Our approach uniquely emphasizes local VLMs and LLMs for zero-data-exfiltration, filling gaps in adaptive, safe office agents as projected for 2025 trends (e.g., vision-dominant policies and real-world alignment).<grok:render card_id="4fbf71" card_type="citation_card" type="render_inline_citation">
<argument name="citation_id">19</argument>
</grok:render>

This positions our system as a practical advancement in privacy-centric ACUs, extending foundation-model trends to secure enterprise environments.
