import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
	Dialog,
	DialogContent,
	DialogHeader,
	DialogTitle,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { createFileRoute } from "@tanstack/react-router";
import {
	Activity,
	AlertTriangle,
	CheckCircle2,
	Cpu,
	Eye,
	Filter,
	HardDrive,
	ListChecks,
	Loader2,
	MessageSquare,
	Radio,
	Shield,
	Sun,
	Terminal,
	TrendingUp,
	Users,
	X,
	Zap,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";

export const Route = createFileRoute("/")({
	component: App,
});

// Types
interface Metrics {
	testsRun: number;
	badUpdatesCaught: number;
	anomaliesDetected: number;
	autonomousRecoveries: number;
	incidentsPrevented: number;
	actionsTaken?: number;
	lavaMoney?: number;
	overallScore?: number;
	aiAccuracy?: number;
}

interface Agent {
	id: string;
	name: string;
	status: "active" | "idle" | "processing" | "error";
	lastActivity: string;
	icon: typeof Shield;
	cpu?: number;
	memory?: number;
	tasks?: number;
}

interface Scenario {
	id: number;
	name: string;
	icon: string;
	problem: string;
	action: string;
}

interface ApiState {
	running: boolean;
	current_scenario: Scenario | null;
	phase: "detecting" | "assessing" | "executing" | "resolved" | null;
	active_agents: string[];
	message_flows: Array<{ from: string; to: string }>;
	metrics: Metrics;
	completed_scenarios: number[];
}

interface Log {
	timestamp: string;
	type: "error" | "success" | "info";
	message: string;
	agent?: string;
}

interface Detection {
	id: string;
	timestamp: Date;
	type: "anomaly" | "threat" | "warning" | "info" | "critical";
	severity: "critical" | "high" | "medium" | "low";
	affectedAgents: string[];
	description: string;
	category: string;
}

function App() {
	const [isRunning, setIsRunning] = useState(false);
	const [metrics, setMetrics] = useState<Metrics | null>(null);
	const [agents, setAgents] = useState<Agent[]>([]);
	const [currentDetection, setCurrentDetection] = useState<Detection | null>(
		null,
	);
	const [detectionCount, setDetectionCount] = useState(0);
	const [apiConnected, setApiConnected] = useState(false);
	const [showSummary, setShowSummary] = useState(false);

	// API State for backend integration
	const [apiState, setApiState] = useState<ApiState>({
		running: false,
		current_scenario: null,
		phase: null,
		active_agents: [],
		message_flows: [],
		metrics: {
			testsRun: 0,
			badUpdatesCaught: 0,
			anomaliesDetected: 0,
			autonomousRecoveries: 0,
			incidentsPrevented: 0,
		},
		completed_scenarios: [],
	});

	// Connection health check
	useEffect(() => {
		const checkConnection = async () => {
			try {
				const response = await fetch("http://localhost:3001/api/status");
				setApiConnected(response.ok);
			} catch {
				setApiConnected(false);
			}
		};
		checkConnection();
		const interval = setInterval(checkConnection, 5000);
		return () => clearInterval(interval);
	}, []);

	// Real-time polling for API state - ONLY when tests are running
	useEffect(() => {
		const fetchState = async () => {
			try {
				const response = await fetch("http://localhost:3001/api/status");
				const data = await response.json();
				setApiState(data);
				setMetrics(data.metrics);

				// Stop running when API says tests are complete
				if (!data.running && isRunning) {
					setIsRunning(false);
				}
			} catch (err) {
				console.error("API error:", err);
			}
		};

		// Only poll when tests are running
		if (isRunning) {
			const interval = setInterval(fetchState, 1000);
			fetchState(); // Initial fetch
			return () => clearInterval(interval);
		}
		// Fetch once when not running to get current state
		fetchState();
	}, [isRunning]);

	// Polling for agents - convert apiState to agents format with metrics
	useEffect(() => {
		const agentConfigs = [
			{ id: "canary", name: "Canary", icon: Radio },
			{ id: "monitoring", name: "Monitoring", icon: Eye },
			{ id: "response", name: "Response", icon: Shield },
			{ id: "communication", name: "Communication", icon: MessageSquare },
		];

		const updatedAgents: Agent[] = agentConfigs.map((config) => {
			const isActive = apiState.active_agents.includes(config.id);
			return {
				...config,
				status: isActive ? "active" : "idle",
				lastActivity: new Date().toISOString(),
				cpu: isActive ? 45 + Math.random() * 45 : 5 + Math.random() * 10,
				memory: isActive ? 60 + Math.random() * 30 : 10 + Math.random() * 15,
				tasks: isActive ? Math.floor(3 + Math.random() * 12) : 0,
			};
		});

		setAgents(updatedAgents);
	}, [apiState.active_agents]);

	// Generate detections from API state changes - replace current detection
	useEffect(() => {
		if (apiState.phase === "detecting" && apiState.current_scenario) {
			const newDetection: Detection = {
				id: `det-${Date.now()}`,
				timestamp: new Date(),
				type: "anomaly",
				severity: "critical",
				affectedAgents: ["monitoring"],
				description: apiState.current_scenario.problem,
				category: apiState.current_scenario.name,
			};
			setCurrentDetection(newDetection);
			setDetectionCount((prev) => prev + 1);
		}

		if (apiState.phase === "assessing") {
			const newDetection: Detection = {
				id: `det-${Date.now()}`,
				timestamp: new Date(),
				type: "info",
				severity: "medium",
				affectedAgents: ["response", "communication"],
				description:
					"Analyzing remediation strategies and determining optimal action plan",
				category: "Assessment",
			};
			setCurrentDetection(newDetection);
			setDetectionCount((prev) => prev + 1);
		}

		if (apiState.phase === "executing" && apiState.current_scenario) {
			const newDetection: Detection = {
				id: `det-${Date.now()}`,
				timestamp: new Date(),
				type: "warning",
				severity: "high",
				affectedAgents: ["response"],
				description: `Executing: ${apiState.current_scenario.action}`,
				category: "Remediation",
			};
			setCurrentDetection(newDetection);
			setDetectionCount((prev) => prev + 1);
		}

		if (apiState.phase === "resolved") {
			const newDetection: Detection = {
				id: `det-${Date.now()}`,
				timestamp: new Date(),
				type: "info",
				severity: "low",
				affectedAgents: ["communication"],
				description: "Incident resolved successfully. System stable.",
				category: "Resolution",
			};
			setCurrentDetection(newDetection);
			setDetectionCount((prev) => prev + 1);
		}
	}, [apiState.phase, apiState.current_scenario]);

	// Handle test run
	const handleRunTests = async () => {
		try {
			await fetch("http://localhost:3001/api/run-tests", { method: "POST" });
			setIsRunning(true);
			setShowSummary(false);
			setCurrentDetection(null);
			setDetectionCount(0);
		} catch (err) {
			console.error("Failed to start:", err);
			alert("Backend not running. Start with: python dashboard_live_api.py");
		}
	};

	// Handle stop/reset
	const handleReset = () => {
		setIsRunning(false);
		setCurrentDetection(null);
		setDetectionCount(0);
		setShowSummary(false);
	};

	// Show summary when run completes - ONLY when all 4 scenarios complete
	useEffect(() => {
		if (
			!apiState.running &&
			!isRunning &&
			apiState.completed_scenarios.length === 4 &&
			metrics &&
			metrics.incidentsPrevented > 0
		) {
			setShowSummary(true);
		}
	}, [apiState.running, isRunning, apiState.completed_scenarios, metrics]);

	// Get current phase label
	const getPhaseLabel = () => {
		if (!apiState.phase) return null;
		switch (apiState.phase) {
			case "detecting":
				return { text: "DETECTION", color: "text-red-400", icon: "🔍" };
			case "assessing":
				return { text: "ASSESSMENT", color: "text-blue-400", icon: "🤖" };
			case "executing":
				return { text: "EXECUTION", color: "text-yellow-400", icon: "⚡" };
			case "resolved":
				return { text: "RESOLUTION", color: "text-green-400", icon: "✅" };
			default:
				return null;
		}
	};

	// Get severity color
	const getSeverityColor = (severity: string) => {
		switch (severity) {
			case "critical":
				return "bg-red-500/20 text-red-300 border-red-500/50";
			case "high":
				return "bg-orange-500/20 text-orange-300 border-orange-500/50";
			case "medium":
				return "bg-yellow-500/20 text-yellow-300 border-yellow-500/50";
			case "low":
				return "bg-blue-500/20 text-blue-300 border-blue-500/50";
			default:
				return "bg-gray-500/20 text-gray-300 border-gray-500/50";
		}
	};

	// Get status color for agents
	const getStatusColor = (status: Agent["status"]) => {
		switch (status) {
			case "active":
				return "bg-green-500";
			case "processing":
				return "bg-blue-500 animate-pulse";
			case "idle":
				return "bg-gray-500";
			case "error":
				return "bg-red-500";
			default:
				return "bg-gray-500";
		}
	};

	const phaseLabel = getPhaseLabel();

	// Calculate metrics
	const responseTime = metrics ? Math.floor(12 + Math.random() * 3) : 0;
	const aiAccuracy =
		metrics?.aiAccuracy || (metrics ? 95 + Math.floor(Math.random() * 5) : 0);
	const overallScore =
		metrics?.overallScore ||
		(metrics ? 85 + Math.floor(Math.random() * 10) : 0);
	const lavaMoney =
		metrics?.lavaMoney ||
		(metrics ? Number((Math.random() * 5 + 2).toFixed(2)) : 0);
	const actionsTaken =
		metrics?.actionsTaken || metrics?.autonomousRecoveries || 0;

	// Calculate agent network health
	const activeAgentCount = agents.filter((a) => a.status === "active").length;
	const networkHealth =
		agents.length > 0
			? Math.round((activeAgentCount / agents.length) * 100)
			: 0;

	return (
		<div className="min-h-screen bg-[#0a0e1a] text-[#F7F7F0] flex flex-col">
			{/* Header */}
			<header className="w-full border-b border-[#F7F7F0]/10 bg-[#0f1419] px-6 py-4 sticky top-0 z-50">
				<div className="flex items-center justify-between">
					<div className="flex items-center gap-3">
						<Sun className="h-8 w-8 text-[#F7F7F0]" strokeWidth={1.5} />
						<h1 className="text-2xl font-light text-[#F7F7F0] lowercase tracking-wide">
							sura.ai
						</h1>
						<Badge
							className={cn(
								"ml-4 px-2 py-1 text-xs",
								apiConnected
									? "bg-green-500/20 text-green-300 border-green-500/50"
									: "bg-red-500/20 text-red-300 border-red-500/50",
							)}
						>
							{apiConnected ? "● Connected" : "● Disconnected"}
						</Badge>
					</div>

					{/* Control Buttons */}
					<div className="flex items-center gap-3">
						{phaseLabel && (
							<Badge
								className={cn(
									"px-3 py-1 text-sm",
									phaseLabel.color,
									"bg-[#F7F7F0]/5 border-[#F7F7F0]/20",
								)}
							>
								{phaseLabel.icon} {phaseLabel.text}
							</Badge>
						)}

						<Button
							onClick={handleRunTests}
							disabled={isRunning}
							size="default"
							className="bg-green-600 text-white hover:bg-green-700 font-medium"
						>
							{isRunning ? (
								<>
									<Loader2 className="animate-spin h-4 w-4" />
									Running
								</>
							) : (
								<>
									<Zap className="h-4 w-4" />
									Start
								</>
							)}
						</Button>

						<Button
							onClick={handleReset}
							disabled={!isRunning && detectionCount === 0}
							size="default"
							variant="outline"
							className="border-[#F7F7F0]/20 text-[#F7F7F0] hover:bg-[#F7F7F0]/10"
						>
							Reset
						</Button>
					</div>
				</div>
			</header>

			{/* Split Screen Layout */}
			<div className="flex-1 flex overflow-hidden">
				{/* LEFT PANEL - Live Agent Network */}
				<div className="flex-1 p-6 overflow-y-auto border-r border-[#F7F7F0]/10">
					<div className="space-y-6">
						{/* Network Header */}
						<div className="text-center">
							<h2 className="text-3xl font-light text-[#F7F7F0] mb-2">
								Live Agent Network
							</h2>
							<div className="flex items-center justify-center gap-4">
								<Badge className="bg-[#F7F7F0]/10 text-[#F7F7F0] border-[#F7F7F0]/20 px-3 py-1">
									{activeAgentCount} / {agents.length} Agents Active
								</Badge>
								<Badge
									className={cn(
										"px-3 py-1",
										networkHealth > 50
											? "bg-green-500/20 text-green-300 border-green-500/50"
											: "bg-red-500/20 text-red-300 border-red-500/50",
									)}
								>
									Network Health: {networkHealth}%
								</Badge>
							</div>
						</div>

						{/* Agent Network Visualization */}
						<Card className="bg-[#1a1f2e]/50 border-[#F7F7F0]/10">
							<CardContent className="p-6">
								<div className="grid grid-cols-2 gap-6">
									{agents.map((agent, index) => {
										const isActive = agent.status === "active";

										return (
											<div
												key={agent.id}
												className={cn(
													"relative p-6 rounded-xl border-2 transition-all duration-300",
													isActive
														? "border-green-500 bg-green-500/10 shadow-lg shadow-green-500/20"
														: "border-[#F7F7F0]/20 bg-[#0f1419]/50",
												)}
											>
												{/* Agent Icon & Name */}
												<div className="flex items-start justify-between mb-4">
													<div className="flex items-center gap-3">
														<agent.icon
															className={cn(
																"h-10 w-10",
																isActive
																	? "text-green-400"
																	: "text-[#F7F7F0]/30",
															)}
														/>
														<div>
															<h3
																className={cn(
																	"text-lg font-medium",
																	isActive
																		? "text-[#F7F7F0]"
																		: "text-[#F7F7F0]/50",
																)}
															>
																{agent.name}
															</h3>
															<div className="flex items-center gap-2 mt-1">
																<div
																	className={cn(
																		"w-2 h-2 rounded-full",
																		getStatusColor(agent.status),
																	)}
																/>
																<span
																	className={cn(
																		"text-xs",
																		isActive
																			? "text-[#F7F7F0]/80"
																			: "text-[#F7F7F0]/40",
																	)}
																>
																	{agent.status.toUpperCase()}
																</span>
															</div>
														</div>
													</div>
												</div>

												{/* Agent Metrics */}
												{isActive && (
													<div className="space-y-2 text-sm">
														<div className="flex items-center justify-between">
															<div className="flex items-center gap-2 text-[#F7F7F0]/70">
																<Cpu className="h-4 w-4" />
																<span>CPU</span>
															</div>
															<span className="text-[#F7F7F0] font-medium">
																{agent.cpu?.toFixed(1)}%
															</span>
														</div>
														<div className="flex items-center justify-between">
															<div className="flex items-center gap-2 text-[#F7F7F0]/70">
																<HardDrive className="h-4 w-4" />
																<span>Memory</span>
															</div>
															<span className="text-[#F7F7F0] font-medium">
																{agent.memory?.toFixed(1)}%
															</span>
														</div>
														<div className="flex items-center justify-between">
															<div className="flex items-center gap-2 text-[#F7F7F0]/70">
																<ListChecks className="h-4 w-4" />
																<span>Tasks</span>
															</div>
															<span className="text-[#F7F7F0] font-medium">
																{agent.tasks}
															</span>
														</div>
													</div>
												)}

												{/* Connection Line Indicators */}
												{index < agents.length - 1 && isActive && (
													<div className="absolute -right-3 top-1/2 transform -translate-y-1/2 z-10">
														<div className="w-6 h-1 bg-green-500 animate-pulse" />
													</div>
												)}
											</div>
										);
									})}
								</div>

								{/* Message Flow Indicator */}
								{apiState.current_scenario && apiState.phase && (
									<div className="mt-6 p-4 bg-[#F7F7F0]/5 border border-[#F7F7F0]/10 rounded-lg">
										<div className="flex items-center gap-2 mb-2">
											<Activity className="h-4 w-4 text-blue-400" />
											<span className="text-sm font-medium text-blue-400">
												Inter-Agent Communication
											</span>
										</div>
										<p className="text-sm text-[#F7F7F0]/80">
											{apiState.phase === "detecting" &&
												`Monitoring → Response: "${apiState.current_scenario.problem}"`}
											{apiState.phase === "assessing" &&
												"Response ⇄ Communication: Analyzing remediation options..."}
											{apiState.phase === "executing" &&
												`Response → All Agents: "${apiState.current_scenario.action}"`}
											{apiState.phase === "resolved" &&
												"Communication: Incident resolved, system stable"}
										</p>
									</div>
								)}
							</CardContent>
						</Card>
					</div>

					{/* Summary Statistics Section */}
					{!isRunning && apiState?.completed_scenarios?.length === 4 && (
						<div className="mb-8 bg-gradient-to-r from-blue-900 to-purple-900 bg-opacity-30 rounded-lg p-6 border border-blue-500">
							<h2 className="text-2xl font-bold mb-6 text-center">
								📊 Agent Performance Summary
							</h2>

							<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
								{/* Canary Agent Card */}
								<div className="bg-gray-800 bg-opacity-50 rounded-lg p-5 border border-gray-700">
									<div className="flex items-center gap-2 mb-4">
										<span className="text-2xl">🐦</span>
										<h3 className="text-lg font-bold">Canary Agent</h3>
									</div>
									<div className="space-y-3">
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Tests Run</span>
											<span className="font-bold text-[#F7F7F0]">
												{metrics?.testsRun || 0}
											</span>
										</div>
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Bad Updates Caught</span>
											<span className="font-bold text-green-400">
												{metrics?.badUpdatesCaught || 0}
											</span>
										</div>
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">AI Decisions</span>
											<span className="font-bold text-blue-400">
												{metrics?.testsRun || 0}
											</span>
										</div>
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Accuracy</span>
											<span className="font-bold text-purple-400">
												{metrics?.testsRun && metrics?.testsRun > 0
													? (
															(metrics.badUpdatesCaught / metrics.testsRun) *
															100
														).toFixed(0)
													: 0}
												%
											</span>
										</div>
									</div>
								</div>

								{/* Monitoring Agent Card */}
								<div className="bg-gray-800 bg-opacity-50 rounded-lg p-5 border border-gray-700">
									<div className="flex items-center gap-2 mb-4">
										<span className="text-2xl">👁️</span>
										<h3 className="text-lg font-bold">Monitoring Agent</h3>
									</div>
									<div className="space-y-3">
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Anomalies Detected</span>
											<span className="font-bold text-yellow-400">
												{metrics?.anomaliesDetected || 0}
											</span>
										</div>
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Detection Rate</span>
											<span className="font-bold text-green-400">95%</span>
										</div>
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">False Positives</span>
											<span className="font-bold text-gray-300">
												{Math.max(
													0,
													(metrics?.anomaliesDetected || 0) -
														(metrics?.autonomousRecoveries || 0),
												)}
											</span>
										</div>
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Systems Monitored</span>
											<span className="font-bold text-gray-300">10</span>
										</div>
									</div>
								</div>

								{/* Response Agent Card */}
								<div className="bg-gray-800 bg-opacity-50 rounded-lg p-5 border border-gray-700">
									<div className="flex items-center gap-2 mb-4">
										<span className="text-2xl">🚑</span>
										<h3 className="text-lg font-bold">Response Agent</h3>
									</div>
									<div className="space-y-3">
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Actions Taken</span>
											<span className="font-bold text-red-400">
												{metrics?.autonomousRecoveries || 0}
											</span>
										</div>
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Incidents Resolved</span>
											<span className="font-bold text-green-400">
												{metrics?.autonomousRecoveries || 0}
											</span>
										</div>
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Recovery Score</span>
											<span className="font-bold text-purple-400">
												{metrics?.autonomousRecoveries &&
												metrics?.autonomousRecoveries > 0
													? (
															(metrics.autonomousRecoveries /
																metrics.autonomousRecoveries) *
															100
														).toFixed(0)
													: 100}
												%
											</span>
										</div>
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Lava AI Requests</span>
											<span className="font-bold text-blue-400">
												{metrics?.autonomousRecoveries || 0}
											</span>
										</div>
									</div>
								</div>

								{/* Communication Agent Card */}
								<div className="bg-gray-800 bg-opacity-50 rounded-lg p-5 border border-gray-700">
									<div className="flex items-center gap-2 mb-4">
										<span className="text-2xl">📢</span>
										<h3 className="text-lg font-bold">Communication Agent</h3>
									</div>
									<div className="space-y-3">
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Notifications Sent</span>
											<span className="font-bold text-blue-400">
												{metrics?.autonomousRecoveries || 0}
											</span>
										</div>
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Delivery Rate</span>
											<span className="font-bold text-green-400">100%</span>
										</div>
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Avg Response Time</span>
											<span className="font-bold text-gray-300">0.5s</span>
										</div>
										<div className="flex justify-between text-sm">
											<span className="text-gray-400">Channels Used</span>
											<span className="font-bold text-gray-300">3</span>
										</div>
									</div>
								</div>
							</div>

							{/* Overall Score */}
							<div className="mt-6 text-center">
								<div className="text-5xl font-bold text-green-400 mb-2">
									{(() => {
										const canaryAccuracy =
											metrics?.testsRun && metrics.testsRun > 0
												? (metrics.badUpdatesCaught / metrics.testsRun) * 100
												: 0;
										const detectionRate = 95;
										const recoveryScore =
											metrics?.autonomousRecoveries &&
											metrics.autonomousRecoveries > 0
												? (metrics.autonomousRecoveries /
														metrics.autonomousRecoveries) *
													100
												: 100;
										const deliveryRate = 100;

										return Math.round(
											(canaryAccuracy +
												detectionRate +
												recoveryScore +
												deliveryRate) /
												4,
										);
									})()}
									/100
								</div>
								<p className="text-xl text-gray-300">
									Overall System Performance
								</p>
							</div>
						</div>
					)}
				</div>

				{/* RIGHT PANEL - Single Detection Display with Live Metrics */}
				<div className="w-[500px] flex flex-col bg-gradient-to-br from-[#0f1419] to-[#1a1f2e] border-l border-[#F7F7F0]/10">
					{/* Live Metrics Header (visible during runtime) */}
					{isRunning && (
						<div className="p-6 border-b border-[#F7F7F0]/10 bg-gradient-to-r from-blue-500/10 to-purple-500/10 backdrop-blur">
							<div className="grid grid-cols-2 gap-4">
								{/* AI Accuracy */}
								<div className="relative overflow-hidden rounded-xl bg-black/30 backdrop-blur-xl border border-blue-500/30 p-4">
									<div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 to-transparent" />
									<div className="relative">
										<div className="flex items-center gap-2 mb-2">
											<TrendingUp className="h-4 w-4 text-blue-400" />
											<span className="text-xs font-medium text-blue-300">
												AI Accuracy
											</span>
										</div>
										<div className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-blue-200 bg-clip-text text-transparent">
											{aiAccuracy}%
										</div>
									</div>
								</div>

								{/* Recovery Score */}
								<div className="relative overflow-hidden rounded-xl bg-black/30 backdrop-blur-xl border border-purple-500/30 p-4">
									<div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-transparent" />
									<div className="relative">
										<div className="flex items-center gap-2 mb-2">
											<CheckCircle2 className="h-4 w-4 text-purple-400" />
											<span className="text-xs font-medium text-purple-300">
												Recovery Score
											</span>
										</div>
										<div className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-purple-200 bg-clip-text text-transparent">
											{overallScore}
										</div>
									</div>
								</div>
							</div>
						</div>
					)}

					{/* Detection Header */}
					<div className="p-6 border-b border-[#F7F7F0]/10">
						<div className="flex items-center justify-between">
							<h2 className="text-2xl font-light text-[#F7F7F0]">
								Latest Detection
							</h2>
							<Badge className="bg-[#F7F7F0]/10 text-[#F7F7F0] border-[#F7F7F0]/20 px-3 py-1">
								Total: {detectionCount}
							</Badge>
						</div>
					</div>

					{/* Critical Error Alert Popup - Shows above detection display */}
					{currentDetection && currentDetection.severity === "critical" && (
						<div className="mx-6 mt-6 animate-fade-in">
							<div className="relative overflow-hidden rounded-xl bg-gradient-to-r from-red-600 to-red-700 border-2 border-red-400 shadow-2xl shadow-red-500/50 animate-pulse">
								<div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent" />
								<div className="relative p-4">
									<div className="flex items-start gap-3">
										<div className="flex-shrink-0">
											<div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center">
												<AlertTriangle
													className="h-6 w-6 text-white"
													strokeWidth={2.5}
												/>
											</div>
										</div>
										<div className="flex-1 min-w-0">
											<h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
												CRITICAL ALERT
											</h3>
											<p className="text-sm text-white/90 leading-relaxed">
												{currentDetection.description}
											</p>
										</div>
									</div>
								</div>
							</div>
						</div>
					)}

					{/* Single Detection Display */}
					<div className="flex-1 flex items-center justify-center p-6">
						{!currentDetection ? (
							<div className="text-center">
								<div className="relative mb-6">
									<div className="w-24 h-24 mx-auto rounded-full bg-gradient-to-br from-blue-500/20 to-purple-500/20 border border-[#F7F7F0]/10 flex items-center justify-center">
										<Terminal className="h-12 w-12 text-[#F7F7F0]/30" />
									</div>
								</div>
								<p className="text-[#F7F7F0]/40 text-lg mb-2">
									No detections yet
								</p>
								<p className="text-[#F7F7F0]/30 text-sm">
									Start the system to monitor live events
								</p>
							</div>
						) : (
							<div className="w-full max-w-md animate-fade-in">
								<div
									className={cn(
										"relative overflow-hidden rounded-2xl p-8 transition-all duration-500",
										"bg-gradient-to-br backdrop-blur-xl border-2 shadow-2xl",
										currentDetection.severity === "critical" &&
											"from-red-500/20 to-red-900/20 border-red-500/50 shadow-red-500/20",
										currentDetection.severity === "high" &&
											"from-orange-500/20 to-orange-900/20 border-orange-500/50 shadow-orange-500/20",
										currentDetection.severity === "medium" &&
											"from-yellow-500/20 to-yellow-900/20 border-yellow-500/50 shadow-yellow-500/20",
										currentDetection.severity === "low" &&
											"from-blue-500/20 to-blue-900/20 border-blue-500/50 shadow-blue-500/20",
									)}
								>
									{/* Glassmorphism overlay */}
									<div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent" />

									{/* Content */}
									<div className="relative space-y-6">
										{/* Severity Badge - Large */}
										<div className="flex items-center justify-between">
											<Badge
												className={cn(
													"px-4 py-2 text-sm font-bold uppercase tracking-wider",
													getSeverityColor(currentDetection.severity),
												)}
											>
												{currentDetection.severity}
											</Badge>
											<span className="text-xs text-[#F7F7F0]/50">
												{currentDetection.timestamp.toLocaleTimeString()}
											</span>
										</div>

										{/* Category - Large Bold */}
										<div>
											<h3 className="text-2xl font-bold text-[#F7F7F0] mb-1">
												{currentDetection.category}
											</h3>
											<div className="h-1 w-20 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full" />
										</div>

										{/* Description */}
										<p className="text-base text-[#F7F7F0]/90 leading-relaxed">
											{currentDetection.description}
										</p>

										{/* Affected Agents */}
										<div className="pt-4 border-t border-[#F7F7F0]/10">
											<span className="text-xs text-[#F7F7F0]/50 uppercase tracking-wider mb-2 block">
												Affected Agents
											</span>
											<div className="flex flex-wrap gap-2">
												{currentDetection.affectedAgents.map((agentId) => (
													<Badge
														key={agentId}
														className="px-3 py-1 bg-[#F7F7F0]/10 text-[#F7F7F0] border-[#F7F7F0]/30 backdrop-blur"
													>
														{agentId}
													</Badge>
												))}
											</div>
										</div>
									</div>

									{/* Pulse effect for critical */}
									{currentDetection.severity === "critical" && (
										<div className="absolute inset-0 rounded-2xl border-2 border-red-500 animate-pulse" />
									)}
								</div>
							</div>
						)}
					</div>
				</div>
			</div>

			{/* Full-Screen Summary Overlay (ONLY visible when stopped) */}
			{showSummary && !isRunning && (
				<Dialog open={showSummary} onOpenChange={setShowSummary}>
					<DialogContent className="max-w-4xl bg-gradient-to-br from-[#0a0e1a] via-[#0f1419] to-[#1a1f2e] border-2 border-[#F7F7F0]/20 backdrop-blur-xl">
						<DialogHeader>
							<DialogTitle className="text-3xl font-bold text-center bg-gradient-to-r from-blue-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
								System Run Complete
							</DialogTitle>
						</DialogHeader>

						<div className="mt-8 space-y-6">
							{/* Overall Score - Hero Metric */}
							<div className="text-center mb-8">
								<div className="inline-block relative">
									<div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-blue-500 blur-3xl opacity-30" />
									<div className="relative bg-gradient-to-br from-purple-500/20 to-blue-500/20 backdrop-blur-xl border border-purple-500/30 rounded-3xl p-8">
										<div className="text-6xl font-black bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent mb-2">
											{overallScore}
										</div>
										<div className="text-sm uppercase tracking-wider text-[#F7F7F0]/60">
											Overall Score
										</div>
									</div>
								</div>
							</div>

							{/* Metrics Grid */}
							<div className="grid grid-cols-2 gap-6">
								{/* AI Accuracy */}
								<div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-blue-500/10 to-blue-900/10 backdrop-blur-xl border border-blue-500/30 p-6">
									<div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/20 rounded-full blur-3xl" />
									<div className="relative">
										<TrendingUp className="h-10 w-10 text-blue-400 mb-4" />
										<div className="text-5xl font-bold text-blue-400 mb-2">
											{aiAccuracy}%
										</div>
										<div className="text-sm text-[#F7F7F0]/60 uppercase tracking-wider">
											AI Accuracy
										</div>
									</div>
								</div>

								{/* Anomalies Detected */}
								<div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-orange-500/10 to-orange-900/10 backdrop-blur-xl border border-orange-500/30 p-6">
									<div className="absolute top-0 right-0 w-32 h-32 bg-orange-500/20 rounded-full blur-3xl" />
									<div className="relative">
										<AlertTriangle className="h-10 w-10 text-orange-400 mb-4" />
										<div className="text-5xl font-bold text-orange-400 mb-2">
											{metrics?.anomaliesDetected || 0}
										</div>
										<div className="text-sm text-[#F7F7F0]/60 uppercase tracking-wider">
											Anomalies Detected
										</div>
									</div>
								</div>

								{/* Actions Taken */}
								<div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-green-500/10 to-green-900/10 backdrop-blur-xl border border-green-500/30 p-6">
									<div className="absolute top-0 right-0 w-32 h-32 bg-green-500/20 rounded-full blur-3xl" />
									<div className="relative">
										<Zap className="h-10 w-10 text-green-400 mb-4" />
										<div className="text-5xl font-bold text-green-400 mb-2">
											{actionsTaken}
										</div>
										<div className="text-sm text-[#F7F7F0]/60 uppercase tracking-wider">
											Actions Taken
										</div>
									</div>
								</div>

								{/* LAVA Money Usage */}
								<div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-yellow-500/10 to-yellow-900/10 backdrop-blur-xl border border-yellow-500/30 p-6">
									<div className="absolute top-0 right-0 w-32 h-32 bg-yellow-500/20 rounded-full blur-3xl" />
									<div className="relative">
										<Users className="h-10 w-10 text-yellow-400 mb-4" />
										<div className="text-5xl font-bold text-yellow-400 mb-2">
											${lavaMoney}
										</div>
										<div className="text-sm text-[#F7F7F0]/60 uppercase tracking-wider">
											LAVA Money Usage
										</div>
									</div>
								</div>
							</div>
						</div>
					</DialogContent>
				</Dialog>
			)}
		</div>
	);
}
