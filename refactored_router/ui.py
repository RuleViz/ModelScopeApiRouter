import asyncio
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich import box
from .settings import config
from .stats import stats_service
from .schema import CallRecord

class Dashboard:
    def __init__(self):
        self.console = Console()
        # auto_refresh=False: 我们手动控制刷新
        # vertical_overflow="visible": 允许表格被挤到底部
        self.live = Live(self.console, auto_refresh=False, vertical_overflow="visible")
        self.running = False

    def start(self):
        self.running = True
        self.live.start()
        # 初始显示
        self.live.update(self._generate_table(), refresh=True)
        asyncio.create_task(self._updater())

    def stop(self):
        self.running = False
        self.live.stop()

    def _print(self, renderable):
        """核心修改：直接向 Live 的 console 打印，这会显示在表格上方"""
        if self.running:
            self.live.console.print(renderable)
        else:
            self.console.print(renderable)

    def log_request(self, model_id: str, is_stream: bool):
        self._print(f"\n[bold magenta]📨 Request[/bold magenta]: {model_id} (Stream: {is_stream})")

    def log_attempt(self, model_name: str):
        self._print(f"👉 Trying: [cyan]{model_name}[/cyan]...")

    def log_result(self, record: CallRecord):
        snapshot = stats_service.get_snapshot()
        limits = snapshot['limits']
        stats_data = snapshot['stats']
        
        limit = limits.get(record.model_name, 50)
        calls = stats_data.get(record.model_name, {}).get('calls', 0)

        if record.success:
            status = "[bold green]SUCCESS[/bold green]"
            msg = f"Time: {record.response_time:.2f}s"
        else:
            status = "[bold red]FAILED [/bold red]"
            msg = f"[red]{record.error_message}[/red]"

        self._print(
            f"  ↳ {status} [cyan]{record.model_name}[/cyan] | "
            f"Use: [bold yellow]{calls}/{limit}[/bold yellow] | {msg}"
        )
        # 结果产生时顺便刷新一下表格
        self.refresh()

    def log_error(self, msg: str):
        self._print(f"[bold red]❌ {msg}[/bold red]")

    def refresh(self):
        """只更新表格"""
        if self.running:
            self.live.update(self._generate_table(), refresh=True)

    async def _updater(self):
        while self.running:
            self.refresh()
            await asyncio.sleep(0.5)

    def _generate_table(self) -> Table:
        table = Table(
            title="🤖 ModelScope Router",
            box=box.ROUNDED,
            caption=f"Port: {config.PORT} | Status: Running",
            expand=True,
            border_style="bright_black"
        )
        table.add_column("Model Name", style="cyan", no_wrap=True)
        table.add_column("Usage", justify="center")
        table.add_column("Success Rate", justify="center")
        table.add_column("Status", justify="center")

        snapshot = stats_service.get_snapshot()
        stats_data = snapshot['stats']
        limits = snapshot['limits']

        for model in config.MODELS:
            name = model['name']
            st = stats_data.get(name, {})
            calls = st.get('calls', 0)
            success = st.get('success_calls', 0)
            limit = limits.get(name, 50)
            is_limited = st.get('is_limited', False)
            
            if calls >= limit:
                usage_style = "red"
            elif calls >= limit * 0.8:
                usage_style = "yellow"
            else:
                usage_style = "green"
                
            rate = (success / calls * 100) if calls > 0 else 0
            
            if is_limited:
                status = "🔴 LIMITED"
                status_style = "bold red"
            else:
                status = "🟢 Active"
                status_style = "green"

            table.add_row(
                name,
                f"[{usage_style}]{calls}/{limit}[/{usage_style}]",
                f"{rate:.1f}%",
                f"[{status_style}]{status}[/{status_style}]"
            )
        return table

# 全局 UI 实例
dashboard = Dashboard()
