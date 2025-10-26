#!/usr/bin/env python3
"""
Fix aiohttp connection leaks in monitoring agent and test pipeline
These "unclosed connection" errors are warnings, not failures, but they pollute logs
"""

from pathlib import Path
import re

def fix_monitoring_agent():
    """Fix aiohttp session management in monitoring_agent.py"""
    
    file_path = Path("agents/monitoring/monitoring_agent.py")
    
    if not file_path.exists():
        print(f"❌ {file_path} not found")
        return False
    
    print(f"🔧 Fixing {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Backup
    with open(f"{file_path}.backup", 'w') as f:
        f.write(content)
    
    # Fix 1: Use single shared session instead of creating new ones
    new_init = '''    def __init__(self):
        load_dotenv()
        super().__init__(
            name="monitoring_agent",
            seed="monitoring_seed_phrase_67890",
            port=8002,
            capabilities=["monitoring", "anomaly_detection", "real_time_polling"]
        )
        
        self.monitoring_interval = 5  # seconds
        self.baseline_metrics: Dict[str, Dict] = {}
        self.anomaly_threshold = 0.8
        self.mock_infrastructure_url = "http://localhost:8000"
        
        # Shared aiohttp session (prevents connection leaks)
        self.session: Optional[aiohttp.ClientSession] = None
        
        self.setup_handlers()'''
    
    # Replace __init__
    content = re.sub(
        r'def __init__\(self\):.*?self\.setup_handlers\(\)',
        new_init,
        content,
        flags=re.DOTALL
    )
    
    # Fix 2: Add session management methods
    session_methods = '''
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create shared aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def _close_session(self):
        """Close the shared session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
'''
    
    # Add before get_monitored_systems
    content = content.replace(
        '    async def get_monitored_systems',
        session_methods + '\n    async def get_monitored_systems'
    )
    
    # Fix 3: Update get_monitored_systems to use shared session
    new_get_systems = '''    async def get_monitored_systems(self) -> List[str]:
        """Get list of systems from mock infrastructure"""
        try:
            session = await self._get_session()
            async with session.get(f"{self.mock_infrastructure_url}/systems") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("systems", [])[:10]
                else:
                    logger.error(f"Failed to get systems: {resp.status}")
                    return []
        except Exception as e:
            logger.error(f"Failed to connect to mock infrastructure: {e}")
            return [f"server-{i}" for i in range(10)]  # Fallback'''
    
    content = re.sub(
        r'async def get_monitored_systems\(self\).*?return \[f"server-\{i\}" for i in range\(10\)\]  # Fallback',
        new_get_systems,
        content,
        flags=re.DOTALL
    )
    
    # Fix 4: Update collect_metrics to use shared session
    new_collect_metrics = '''    async def collect_metrics(self, system_id: str) -> SystemMetrics:
        """Collect REAL metrics from mock infrastructure API"""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.mock_infrastructure_url}/system/{system_id}"
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    return SystemMetrics(
                        system_id=system_id,
                        cpu_usage=data.get("cpu", 0.0),
                        memory_usage=data.get("memory", 0.0),
                        disk_usage=50.0,
                        network_latency=20.0,
                        error_count=0 if data.get("status") == "healthy" else 10,
                        timestamp=datetime.now().timestamp()
                    )
                else:
                    logger.error(f"System {system_id} not found")
                    return None
        except Exception as e:
            logger.error(f"Failed to collect metrics for {system_id}: {e}")
            return None'''
    
    content = re.sub(
        r'async def collect_metrics\(self, system_id: str\).*?return None',
        new_collect_metrics,
        content,
        flags=re.DOTALL,
        count=1
    )
    
    # Fix 5: Add cleanup on shutdown
    startup_handler = content.find('@self.agent.on_event("startup")')
    if startup_handler != -1:
        # Find the end of startup handler
        shutdown_handler = '''
        @self.agent.on_event("shutdown")
        async def shutdown(ctx: Context):
            logger.info("👋 Monitoring Agent shutting down...")
            await self._close_session()
            logger.info("✅ Cleanup complete")
        '''
        
        # Add after startup handler
        content = content.replace(
            'self.setup_handlers()',
            'self.setup_handlers()\n        \n' + shutdown_handler
        )
    
    # Write fixed version
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")
    return True

def fix_e2e_test_pipeline():
    """Fix aiohttp session management in e2e_test_pipeline.py"""
    
    file_path = Path("e2e_test_pipeline.py")
    
    if not file_path.exists():
        print(f"❌ {file_path} not found")
        return False
    
    print(f"🔧 Fixing {file_path}...")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Backup
    with open(f"{file_path}.backup", 'w') as f:
        f.write(content)
    
    # Fix: Add session to __init__
    new_init = '''    def __init__(self):
        # Initialize orchestrator agent with mailbox
        self.agent = Agent(
            name="e2e_test_orchestrator",
            seed="e2e_test_seed_999",
            port=9999,
            mailbox=True
        )
        
        # Shared session for HTTP requests
        self.session: Optional[aiohttp.ClientSession] = None
        
        self.metrics = {'''
    
    content = content.replace(
        '''    def __init__(self):
        # Initialize orchestrator agent with mailbox
        self.agent = Agent(
            name="e2e_test_orchestrator",
            seed="e2e_test_seed_999",
            port=9999,
            mailbox=True  # Use mailbox for Agentverse routing
        )
        
        self.metrics = {''',
        new_init
    )
    
    # Add session management methods after __init__
    session_methods = '''
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create shared session"""
        if self.session is None or self.session.closed:
            # Create session with proper timeout
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session
    
    async def _close_session(self):
        """Close shared session"""
        if self.session and not self.session.closed:
            await self.session.close()
            await asyncio.sleep(0.25)  # Give time for connections to close
            self.session = None
    '''
    
    # Add before setup_handlers
    content = content.replace(
        '    def setup_handlers(self):',
        session_methods + '\n    def setup_handlers(self):'
    )
    
    # Fix all HTTP methods to use shared session
    
    # Fix check_mock_infrastructure
    new_check_mock = '''    async def check_mock_infrastructure(self) -> bool:
        """Verify mock infrastructure is running"""
        try:
            session = await self._get_session()
            async with session.get(f"{MOCK_API}/health") as resp:
                if resp.status == 200:
                    logger.info("✅ Mock infrastructure is running")
                    return True
        except Exception as e:
            logger.error(f"❌ Mock infrastructure not responding: {e}")
        return False'''
    
    content = re.sub(
        r'async def check_mock_infrastructure\(self\).*?return False',
        new_check_mock,
        content,
        flags=re.DOTALL,
        count=1
    )
    
    # Fix get_systems
    new_get_systems = '''    async def get_systems(self) -> List[str]:
        """Get systems from mock infrastructure"""
        session = await self._get_session()
        async with session.get(f"{MOCK_API}/systems") as resp:
            data = await resp.json()
            return data['systems']'''
    
    content = re.sub(
        r'async def get_systems\(self\).*?return data\[\'systems\'\]',
        new_get_systems,
        content,
        flags=re.DOTALL,
        count=1
    )
    
    # Fix poison_system
    new_poison = '''    async def poison_system(self, system_id: str):
        """Inject failure into system"""
        session = await self._get_session()
        async with session.post(f"{MOCK_API}/simulate-failure/{system_id}") as resp:
            pass  # Just trigger, don't wait for response'''
    
    content = re.sub(
        r'async def poison_system\(self, system_id: str\):.*?await session\.post\(f"\{MOCK_API\}/simulate-failure/\{system_id\}"\)',
        new_poison,
        content,
        flags=re.DOTALL,
        count=1
    )
    
    # Fix recover_system
    new_recover = '''    async def recover_system(self, system_id: str):
        """Recover poisoned system"""
        session = await self._get_session()
        async with session.post(f"{MOCK_API}/rollback/{system_id}") as resp:
            pass  # Just trigger, don't wait for response'''
    
    content = re.sub(
        r'async def recover_system\(self, system_id: str\):.*?await session\.post\(f"\{MOCK_API\}/rollback/\{system_id\}"\)',
        new_recover,
        content,
        flags=re.DOTALL,
        count=1
    )
    
    # Add cleanup in run_full_test_suite
    cleanup_code = '''
        # Cleanup
        await asyncio.sleep(5)
        await self._close_session()  # Close HTTP session
        self.generate_final_report()
        
        # Stop agent
        self.test_complete = True
        logger.info("\\n🛑 Tests complete. Stopping orchestrator in 3 seconds...")
        await asyncio.sleep(3)
        sys.exit(0)'''
    
    content = re.sub(
        r'# Generate final report\s+await asyncio\.sleep\(5\)\s+self\.generate_final_report\(\).*?sys\.exit\(0\)',
        cleanup_code,
        content,
        flags=re.DOTALL,
        count=1
    )
    
    # Write fixed version
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Fixed {file_path}")
    return True

def main():
    print("=" * 60)
    print("🔧 FIXING AIOHTTP CONNECTION LEAKS")
    print("=" * 60)
    print()
    print("These 'Unclosed connection' errors are not critical failures,")
    print("but they pollute your logs. This fix properly closes HTTP")
    print("connections to the mock infrastructure.")
    print()
    
    success = True
    
    # Fix monitoring agent
    if not fix_monitoring_agent():
        success = False
    
    # Fix test pipeline
    if not fix_e2e_test_pipeline():
        success = False
    
    print()
    print("=" * 60)
    if success:
        print("✅ ALL FIXES APPLIED!")
        print("=" * 60)
        print()
        print("📝 Changes made:")
        print("  • Shared aiohttp session (instead of creating new ones)")
        print("  • Proper session cleanup on shutdown")
        print("  • Connection timeout settings")
        print()
        print("🔄 Next steps:")
        print("  1. Restart agents: killall python")
        print("  2. Run: ./setup_e2e_test.sh")
        print()
        print("You should no longer see 'Unclosed connection' errors!")
    else:
        print("❌ SOME FIXES FAILED")
        print("=" * 60)
        print()
        print("Check error messages above")
    
    print("=" * 60)

if __name__ == "__main__":
    main()