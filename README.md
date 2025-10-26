SuraAI: Autonomous Multi-Agentic Infrastructure Immune System
<img width="682" height="321" alt="image" src="https://github.com/user-attachments/assets/b6d14e91-1990-4c1e-9777-516c8a212280" />

SuraAI is an autonomous, AI-powered system designed to be the "immune system for your infrastructure". It uses four cooperating Fetch.ai uAgents to detect, diagnose, and auto-remediate production failures in real-time.

Inspiration
The project was inspired by the critical need to eliminate human-in-the-loop dependencies during major infrastructure outages. We aimed to build a system capable of handling complex, cascading failures—like the simulated "CrowdStrike-style faulty update" and "AWS-style availability zone failure" scenarios in our testing pipeline—by providing instantaneous, intelligent response. The core idea is to go beyond simple rule-based automation and leverage LLMs for high-quality root cause analysis.

What it does
SuraAI orchestrates four distinct, self-registering Fetch.ai uAgents that communicate via the Agentverse Mailbox:

Canary Agent: Tests new software updates on a small subset of systems (1% canary population) to detect potential flaws before wide deployment. It uses AI analysis to decide whether to DEPLOY or initiate an automatic ROLLBACK. The system successfully prevented a simulated faulty kernel update scenario.

Monitoring Agent: Continuously polls a mock infrastructure API for real-time metrics (CPU, Memory, Errors) and applies advanced baselining to identify anomalies. It generates AnomalyAlerts which trigger the autonomous response loop.

Response Agent: Receives alerts and immediately consults Claude Sonnet 3.5 via the Lava Gateway for a definitive diagnosis and action recommendation (e.g., SCALE_UP, RESTART, ROLLBACK). It then executes the appropriate automated runbook. The system demonstrated a highly effective 97.6% action success rate (41 incidents resolved out of 42 actions taken) and intelligent alert deduplication.

Communication Agent: Upon resolution, it publishes a real-time StatusUpdate to a status page file and sends notifications to stakeholders, ensuring everyone is informed instantly without human intervention.

How we built it

Agent Logic: We structured the system using Fetch.ai uAgents, implementing the core logic across four decoupled Python agents. All agents were configured to use the Agentverse Mailbox for robust, asynchronous message routing.

AI Integration: We leveraged the Lava Gateway (Lava Payments) to route requests to the Claude Sonnet 3.5 LLM. This enabled us to inject incident data into a tailored prompt, receiving structured JSON output for AI-driven root cause analysis and action recommendation within the Response Agent. 

Simulation Environment: A FastAPI application was developed as a mock production infrastructure, featuring 100 simulated systems with endpoints for metric polling, failure injection, and system recovery (rollback). This simulation is entirely managed and displayed via the creao.ai dashboard, which allows users to visualize the agents' lifecycle and a live demo of the test pipeline.

Testing and Validation: A comprehensive end-to-end testing pipeline was created to orchestrate all agents and the mock infrastructure through four disaster scenarios, validating the entire communication flow and autonomous recovery capabilities.


What’s next for sura.ai?

Real-world Observability Integration: Transition the Monitoring Agent from the mock API to real observability platforms like Prometheus or Datadog.

Preemptive Recovery: Integrate failure prediction logic into the Monitoring Agent to enable sura.ai to take preemptive actions (e.g., auto-scaling) before an incident becomes critical.

Decentralized Consensus: Extend the Response Agent to a cluster of competing agents operating across the Agentverse, where they reach a consensus on the optimal recovery action via a voting mechanism before execution.

Dynamic Runbooks: Allow the AI to dynamically generate and validate runbook steps based on the incident context and historical resolution data, rather than relying solely on a hardcoded set of responses.

Built with
Agent Framework: Fetch.ai uAgents
AI Gateway: Lava Gateway (Lava Payments)
LLM Model: Claude Sonnet 3.5
Dashboard/Demo: creao.ai
APIs & Web: FastAPI, aiohttp
Language: Python
Communication: Agentverse Mailbox

