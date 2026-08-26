import socket
from sys import stderr

import paramiko

from svt_core.logger import Logger


class SSHTimeoutError(Exception):
    pass


class DUTConnectionLostError(SSHTimeoutError):
    """Raised when the remote host drops the connection (e.g. DUT crash/reboot)."""
    pass


class SSHClient:
    def __init__(
        self,
        logger: Logger,
        host: str,
        username: str,
        password: str,
        port: int = 22,
        timeout: int = 300,
        keepalive: int = 30,
    ) -> None:
        self.logger = logger
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.keepalive = keepalive
        self._client: paramiko.SSHClient | None = None

    def _connect(self) -> paramiko.SSHClient:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            timeout=self.timeout,
        )
        # Send keepalives so sshd doesn't kill long-running stress sessions
        transport = client.get_transport()
        if transport:
            transport.set_keepalive(self.keepalive)
        return client

    def _get_client(self) -> paramiko.SSHClient:
        if (
            self._client is None
            or not self._client.get_transport()
            or not self._client.get_transport().is_active()
        ):
            self._client = self._connect()
        return self._client

    def close(self) -> None:
        if self._client:
            self._client.close()
            self._client = None

    def file_exists(self, path: str) -> bool:
        try:
            self.run(f"test -f {path}", to_log=False)
            return True
        except RuntimeError:
            return False

    def run(
        self,
        command: str,
        timeout=300,
        to_log=True,
        to_print=False,
        allowed_exit_codes: tuple[int, ...] = (),
        encoding_errors: str = "strict",
    ) -> str:
        if to_log:
            self.logger.info(f"# Command: {command}")
        if to_print:
            print(f"# Command: {command}")

        try:
            client = self._get_client()
            stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
            exit_status = stdout.channel.recv_exit_status()
            stdin.close()

            output = stdout.read().decode('utf-8', encoding_errors).strip()
            error = stderr.read().decode('utf-8', encoding_errors).strip()

            if exit_status != 0 and exit_status not in allowed_exit_codes:
                raise RuntimeError(
                    error or f"Command failed with exit code {exit_status}"
                )

            if "\n" in output:
                output = "\n" + output

            if to_log:
                self.logger.info(output)

            if to_print:
                print(output)

            return output

        except KeyboardInterrupt:
            # Clean up the transport before propagating — prevents the
            # secondary ConnectionResetError from the dirty channel state.
            self._client = None
            self.logger.warning(f"KeyboardInterrupt during SSH command on {self.host}, closing connection.")
            raise

        except (ConnectionResetError, EOFError) as e:
            # DUT likely crashed or rebooted (e.g. during DDR stress)
            self._client = None
            self.logger.exception(f"Connection lost to {self.host} (DUT may have crashed): {e}")
            raise DUTConnectionLostError(f"Connection lost to {self.host}: {e}") from e

        except (socket.timeout, socket.error) as se:
            self._client = None
            self.logger.exception(f"SSH connection error on {self.host}: {se}")
            raise SSHTimeoutError(f"SSH connection error on {self.host}: {se}") from se

        except paramiko.AuthenticationException as ae:
            self._client = None
            self.logger.exception(
                f"Authentication failed for {self.username}@{self.host}: {ae}"
            )
            raise

        except paramiko.SSHException as se:
            self._client = None
            self.logger.exception(f"SSH error for {self.host}: {se}")
            raise

        except RuntimeError as re:
            self.logger.error(f"Command execution failed on {self.host}: {re}")
            raise

        except Exception as e:
            self._client = None
            self.logger.exception(f"Unexpected error with {self.host}: {e}")
            raise
