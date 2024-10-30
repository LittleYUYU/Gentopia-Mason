import platform
import re
import subprocess
from typing import AnyStr, List, Union
from uuid import uuid4
from gentopia.tools.basetool import *

# Define a function to load `pexpect` lazily only on Unix/Linux systems
def _lazy_import_pexpect() -> 'pexpect':
    """Import pexpect only when needed on Unix/Linux."""
    if platform.system() == "Windows":
        raise ValueError("Persistent bash processes are not yet supported on Windows.")
    try:
        import pexpect
    except ImportError:
        raise ImportError(
            "pexpect required for persistent bash processes."
            " To install, run `pip install pexpect`."
        )
    return pexpect


# Define a cross-platform `run_command` function for non-persistent command execution
def run_command(command: str) -> str:
    """Run a command using subprocess for Windows compatibility."""
    try:
        output = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ).stdout.decode()
    except subprocess.CalledProcessError as error:
        return error.output.decode() if error.output else str(error)
    return output


class BashProcess:
    """Executes bash commands and returns the output, supporting persistent processes on Unix/Linux only."""

    def __init__(
            self,
            strip_newlines: bool = False,
            return_err_output: bool = False,
            persistent: bool = False,
    ):
        """Initialize with stripping newlines."""
        self.strip_newlines = strip_newlines
        self.return_err_output = return_err_output
        self.prompt = ""
        self.process = None

        # Only initialize persistent mode on Unix/Linux
        if persistent:
            if platform.system() == "Windows":
                raise ValueError("Persistent bash processes are not supported on Windows.")
            self.prompt = str(uuid4())
            self.process = self._initialize_persistent_process(self.prompt)

    @staticmethod
    def _initialize_persistent_process(prompt: str) -> 'pexpect.spawn':
        pexpect = _lazy_import_pexpect()
        process = pexpect.spawn(
            "env", ["-i", "bash", "--norc", "--noprofile"], encoding="utf-8"
        )
        process.sendline("PS1=" + prompt)
        process.expect_exact(prompt, timeout=10)
        return process

    def run(self, commands: Union[str, List[str]]) -> str:
        """Run commands and return final output."""
        if isinstance(commands, str):
            commands = [commands]
        commands = ";".join(commands)

        if self.process is not None:
            # Run in persistent mode for Unix/Linux
            return self._run_persistent(commands)
        else:
            # Run in non-persistent mode using `run_command` for both Windows and Unix/Linux
            return self._run(commands)

    def _run(self, command: str) -> str:
        """Run a single command and return final output using subprocess (cross-platform)."""
        output = run_command(command)
        if self.strip_newlines:
            output = output.strip()
        return output

    def process_output(self, output: str, command: str) -> str:
        """Remove the command from the output using a regular expression."""
        pattern = re.escape(command) + r"\s*\n"
        output = re.sub(pattern, "", output, count=1)
        return output.strip()

    def _run_persistent(self, command: str) -> str:
        """Run commands and return final output in persistent mode (Unix/Linux only)."""
        pexpect = _lazy_import_pexpect()
        if self.process is None:
            raise ValueError("Process not initialized")

        self.process.sendline(command)
        self.process.expect(self.prompt, timeout=10)
        self.process.sendline("")  # Clear the output with an empty string

        try:
            self.process.expect([self.prompt, pexpect.EOF], timeout=10)
        except pexpect.TIMEOUT:
            return f"Timeout error while executing command {command}"

        if self.process.after == pexpect.EOF:
            return f"Exited with error status: {self.process.exitstatus}"

        output = self.process.before
        output = self.process_output(output, command)
        if self.strip_newlines:
            return output.strip()
        return output


def get_platform() -> str:
    """Get platform."""
    system = platform.system()
    if system == "Darwin":
        return "MacOS"
    return system


def get_default_bash_process() -> BashProcess:
    """Initialize BashProcess based on the operating system."""
    return BashProcess(return_err_output=True)


class RunShellArgs(BaseModel):
    bash_commands: str = Field(..., description="a sequence of shell commands")


class RunShell(BaseTool):
    name = "bash_shell"
    description = (f"A tool to run shell commands on this {get_platform()} machine. "
                   "It returns output as a real command line interface. ")
    args_schema: Optional[Type[BaseModel]] = RunShellArgs
    process: BashProcess = get_default_bash_process()

    def _run(self, commands: AnyStr) -> Any:
        """Run commands and return final output."""
        return self.process.run(commands)

    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError


if __name__ == "__main__":
    # Example usage to test the RunShell class
    ans = RunShell()._run("mkdir test/hello")
    print(ans)
