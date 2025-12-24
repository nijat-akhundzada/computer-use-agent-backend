from dataclasses import dataclass

import docker
from app.core.config import settings


@dataclass
class VmInfo:
    container_id: str
    vnc_host: str
    vnc_port: int
    novnc_url: str


class DockerSessionManager:
    """
    Creates one computer-use-demo container per session.
    Uses Docker Engine via /var/run/docker.sock.
    """

    def __init__(self):
        self.client = docker.from_env()

    def start(self, session_id: str) -> VmInfo:
        image = settings.COMPUTER_USE_IMAGE

        # Map container ports to random host ports (None => docker assigns)
        ports = {
            "5900/tcp": None,  # VNC
            "6080/tcp": None,  # noVNC
        }

        # Minimal env; you can add WIDTH/HEIGHT if you want
        env = {
            # demo container expects key for agent loop UI, but we’ll still pass it
            # (even before full agent integration)
            "ANTHROPIC_API_KEY": "",  # optional here; you can wire it later safely
        }

        container = self.client.containers.run(
            image=image,
            detach=True,
            name=f"computeruse-session-{session_id}",
            ports=ports,
            environment=env,
            shm_size="1g",
            labels={
                "app": "computer-use-backend",
                "session_id": session_id,
            },
        )

        container.reload()
        portmap = container.attrs["NetworkSettings"]["Ports"]

        vnc_port = int(portmap["5900/tcp"][0]["HostPort"])
        novnc_port = int(portmap["6080/tcp"][0]["HostPort"])

        # For browsers on host machine, use PUBLIC_HOST
        vnc_host = settings.PUBLIC_HOST
        novnc_url = f"http://{settings.PUBLIC_HOST}:{novnc_port}/"

        return VmInfo(
            container_id=container.id,
            vnc_host=vnc_host,
            vnc_port=vnc_port,
            novnc_url=novnc_url,
        )

    def stop(self, container_id: str) -> None:
        c = self.client.containers.get(container_id)
        try:
            c.stop(timeout=5)
        finally:
            # remove container to avoid buildup
            try:
                c.remove(force=True)
            except Exception:
                pass
