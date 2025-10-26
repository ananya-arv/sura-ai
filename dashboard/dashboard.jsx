import React, { useState, useEffect } from 'react';
import { Activity, Zap, Shield, Bell, CheckCircle, AlertTriangle, TrendingUp } from 'lucide-react';

const API_BASE = 'http://localhost:3001/api';

export default function SuraAIDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [status, setStatus] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 1000);
    return () => clearInterval(interval);
  }, []);

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/status`);
      if (!response.ok) throw new Error('API not available');
      const data = await response.json();
      setStatus(data);
      setIsRunning(data.running);
      setError(null);
      
      // Add to logs if there's a new phase
      if (data.phase && data.current_scenario) {
        addLog(`${data.current_scenario.icon} ${data.current_scenario.name}: ${data.phase}`);
      }
    } catch (err) {
      setError('Dashboard API not responding. Start it with: python dashboard/dashboard_api.py');
    }
  };

  const fetchMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE}/metrics`);
      if (response.ok) {
        const data = await response.json();
        setMetrics(data);
      }
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
    }
  };

  const runTests = async () => {
    try {
      const response = await fetch(`${API_BASE}/run-tests`, { method: 'POST' });
      if (response.ok) {
        setIsRunning(true);
        setLogs([]);
        addLog('🚀 Starting SuraAI test pipeline...');
      }
    } catch (err) {
      setError('Failed to start tests');
    }
  };

  const addLog = (message) => {
    setLogs(prev => [...prev.slice(-49), {
      timestamp: new Date().toLocaleTimeString(),
      message
    }]);
  };

  useEffect(() => {
    if (!isRunning && status?.completed_scenarios?.length > 0) {
      fetchMetrics();
    }
  }, [isRunning, status?.completed_scenarios]);

  const getAgentStatus = (agentName) => {
    if (!status) return 'idle';
    return status.active_agents?.includes(agentName) ? 'active' : 'idle';
  };

  const AgentCard = ({ name, icon, status, description }) => {
    const isActive = status === 'active';
    
    return (
      <div className={`relative p-6 rounded-xl border-2 transition-all duration-300 ${
        isActive 
          ? 'border-green-500 bg-green-500/10 shadow-lg shadow-green-500/20' 
          : 'border-gray-700 bg-gray-800/50'
      }`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-3">
            <span className="text-3xl">{icon}</span>
            <div>
              <h3 className="font-bold text-white">{name}</h3>
              <p className="text-xs text-gray-400">{description}</p>
            </div>
          </div>
          <div className={`w-3 h-3 rounded-full ${
            isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-600'
          }`} />
        </div>
        {isActive && (
          <div className="mt-3 text-xs font-semibold text-green-400 flex items-center gap-2">
            <Activity className="w-4 h-4" />
            PROCESSING
          </div>
        )}
      </div>
    );
  };

  const MetricCard = ({ title, value, subtitle, icon: Icon, color }) => (
    <div className={`p-6 rounded-xl bg-gradient-to-br ${color} border border-white/10`}>
      <div className="flex items-center justify-between mb-2">
        <Icon className="w-8 h-8 text-white/90" />
        <span className="text-4xl font-bold text-white">{value}</span>
      </div>
      <div className="text-sm font-semibold text-white/90">{title}</div>
      {subtitle && <div className="text-xs text-white/60 mt-1">{subtitle}</div>}
    </div>
  );

  const ScenarioProgress = () => {
    if (!status?.current_scenario) return null;
    
    const phases = ['detecting', 'assessing', 'executing', 'notifying', 'resolved'];
    const currentIndex = phases.indexOf(status.phase);
    
    return (
      <div className="p-6 rounded-xl bg-gradient-to-r from-purple-900/50 to-blue-900/50 border-2 border-purple-500">
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-4xl">{status.current_scenario.icon}</span>
              <h3 className="text-2xl font-bold text-white">
                Scenario {status.current_scenario.id}: {status.current_scenario.name}
              </h3>
            </div>
            <p className="text-purple-200">{status.current_scenario.problem}</p>
          </div>
          <div className="text-right">
            <div className="text-sm text-purple-300">Phase</div>
            <div className="text-2xl font-bold text-white capitalize">{status.phase}</div>
          </div>
        </div>
        
        <div className="flex gap-2 mt-4">
          {phases.map((phase, index) => (
            <div key={phase} className="flex-1">
              <div className={`h-2 rounded-full transition-all ${
                index <= currentIndex ? 'bg-green-500' : 'bg-gray-700'
              }`} />
              <div className="text-xs text-center mt-1 text-gray-400 capitalize">
                {phase}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const MessageFlow = () => {
    if (!status?.message_flows?.length) return null;
    
    return (
      <div className="flex items-center justify-center gap-4 py-4">
        {status.message_flows.map((flow, index) => (
          <div key={index} className="flex items-center gap-2">
            <div className="px-4 py-2 bg-blue-500/20 border border-blue-500 rounded-lg text-blue-300 font-medium">
              {flow.from}
            </div>
            <div className="flex items-center gap-1">
              <Zap className="w-5 h-5 text-yellow-400 animate-pulse" />
              <div className="w-12 h-0.5 bg-yellow-400" />
              <Zap className="w-5 h-5 text-yellow-400 animate-pulse" />
            </div>
            <div className="px-4 py-2 bg-green-500/20 border border-green-500 rounded-lg text-green-300 font-medium">
              {flow.to}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900 text-white p-8">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center text-2xl font-bold">
            ⚡
          </div>
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
              SuraAI
            </h1>
            <p className="text-gray-400">Autonomous Infrastructure Immune System</p>
          </div>
        </div>
        <button
          onClick={runTests}
          disabled={isRunning || !!error}
          className={`px-8 py-4 rounded-xl font-bold text-lg transition-all transform hover:scale-105 ${
            isRunning || error
              ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
              : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-lg'
          }`}
        >
          {isRunning ? '⏳ Tests Running...' : '🚀 Run Test Pipeline'}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/20 border border-red-500 rounded-lg text-red-200">
          ⚠️ {error}
        </div>
      )}

      {/* Real-time Metrics */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <MetricCard
            title="AI Accuracy"
            value={`${metrics.metrics?.ai_accuracy?.toFixed(1) || 0}%`}
            subtitle="Canary decisions"
            icon={TrendingUp}
            color="from-blue-600 to-blue-800"
          />
          <MetricCard
            title="Recovery Score"
            value={`${metrics.metrics?.recovery_score?.toFixed(1) || 0}%`}
            subtitle="Successful resolutions"
            icon={CheckCircle}
            color="from-green-600 to-green-800"
          />
          <MetricCard
            title="Anomalies Detected"
            value={metrics.metrics?.anomalies_detected || 0}
            subtitle="System issues found"
            icon={AlertTriangle}
            color="from-yellow-600 to-orange-700"
          />
          <MetricCard
            title="Actions Taken"
            value={metrics.metrics?.actions_taken || 0}
            subtitle={`$${(metrics.metrics?.lava_cost || 0).toFixed(2)} AI cost`}
            icon={Zap}
            color="from-purple-600 to-purple-800"
          />
        </div>
      )}

      {/* Current Scenario */}
      {isRunning && status?.current_scenario && (
        <div className="mb-8">
          <ScenarioProgress />
        </div>
      )}

      {/* Message Flows */}
      {isRunning && status?.message_flows?.length > 0 && (
        <div className="mb-8">
          <MessageFlow />
        </div>
      )}

      {/* Agent Network */}
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Shield className="w-6 h-6" />
          Live Agent Network
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <AgentCard
            name="Canary Agent"
            icon="🐦"
            description="Pre-deployment testing"
            status={getAgentStatus('canary')}
          />
          <AgentCard
            name="Monitoring Agent"
            icon="👁️"
            description="Real-time anomaly detection"
            status={getAgentStatus('monitoring')}
          />
          <AgentCard
            name="Response Agent"
            icon="🚑"
            description="AI-powered recovery"
            status={getAgentStatus('response')}
          />
          <AgentCard
            name="Communication Agent"
            icon="📢"
            description="Stakeholder notifications"
            status={getAgentStatus('communication')}
          />
        </div>
      </div>

      {/* Latest Detection */}
      {metrics?.latest_detection && (
        <div className="mb-8 p-6 rounded-xl bg-gradient-to-r from-red-900/30 to-orange-900/30 border border-red-500/50">
          <h3 className="text-xl font-bold mb-3 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-red-400" />
            Latest Detection
          </h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-sm text-gray-400">Incident</div>
              <div className="font-semibold text-white">{metrics.latest_detection.title}</div>
            </div>
            <div>
              <div className="text-sm text-gray-400">Status</div>
              <div className={`font-semibold ${
                metrics.latest_detection.status === 'RESOLVED' 
                  ? 'text-green-400' 
                  : 'text-yellow-400'
              }`}>
                {metrics.latest_detection.status}
              </div>
            </div>
          </div>
          <p className="mt-2 text-sm text-gray-300">{metrics.latest_detection.description}</p>
        </div>
      )}

      {/* Live Logs */}
      <div>
        <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
          <Bell className="w-6 h-6" />
          Live Activity Log
        </h2>
        <div className="bg-gray-900/80 rounded-xl p-6 font-mono text-sm h-80 overflow-y-auto border border-gray-700">
          {logs.length === 0 ? (
            <div className="text-gray-500 text-center py-8">
              Waiting for test execution...
            </div>
          ) : (
            logs.map((log, index) => (
              <div key={index} className="mb-1 text-gray-300">
                <span className="text-gray-500">[{log.timestamp}]</span> {log.message}
              </div>
            ))
          )}
        </div>
      </div>

      {/* System Status */}
      {status && !error && (
        <div className="mt-6 p-4 bg-gray-800/50 rounded-lg border border-gray-700">
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-6">
              <div>
                <span className="text-gray-400">Tests Run:</span>{' '}
                <span className="font-semibold text-white">{status.metrics?.testsRun || 0}</span>
              </div>
              <div>
                <span className="text-gray-400">Scenarios Completed:</span>{' '}
                <span className="font-semibold text-white">{status.completed_scenarios?.length || 0}/4</span>
              </div>
              <div>
                <span className="text-gray-400">Status:</span>{' '}
                <span className={`font-semibold ${
                  isRunning ? 'text-green-400' : 'text-gray-400'
                }`}>
                  {isRunning ? 'Running' : 'Idle'}
                </span>
              </div>
            </div>
            <div className="text-gray-500">
              Connected to Dashboard API
            </div>
          </div>
        </div>
      )}
    </div>
  );
}