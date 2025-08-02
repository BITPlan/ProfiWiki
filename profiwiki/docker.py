"""
Created on 2023-04-01

@author: wf
"""

import os
import tempfile
import time

from mwdocker.docker import DockerContainer
from python_on_whales import DockerException
from python_on_whales import docker as pow_docker

class ProfiWikiContainer:
    """
    a profiwiki docker container wrapper
    """

    def __init__(self, dc: DockerContainer):
        """
        Args:
            dc(DockerContainer): the to wrap
        """
        self.dc = dc

    def log_action(self, action: str):
        """
        log the given action

        Args:
            action(str): the d
        """
        if self.dc:
            print(f"{action} {self.dc.kind} {self.dc.name}", flush=True)
        else:
            print(f"{action}", flush=True)

    def wait_ready(self, timeout=5, check_interval=0.1, verbose=True):
        """
        Wait until the container is fully ready to accept commands

        Args:
            timeout (int): Maximum time to wait in seconds
            check_interval (float): Time between checks in seconds
            verbose (bool): If True, print status messages during waiting

        Raises:
            TimeoutError: If the container is not ready after the timeout period
        """
        start_time = time.time()
        tries = 0

        while time.time() - start_time < timeout:
            tries += 1
            if verbose:
                print(f"Checking if container is ready (try {tries})...")

            try:
                # Try a simple command to check if container is ready
                self.dc.container.execute(["test", "-e", "/bin"], tty=True)
                if verbose:
                    print(f"Container ready after {tries} tries")
                return True
            except Exception as e:
                # If still not ready, wait and try again
                if verbose:
                    print(f"Container not ready on try {tries}: {e}")
                time.sleep(check_interval)

        # If we've reached this point, the timeout has expired
        error_msg = f"Container not ready after {tries} tries and {timeout} seconds"
        if verbose:
            print(error_msg)
        raise TimeoutError(error_msg)

    def upload(self, text: str, path: str, with_wait: bool = True):
        """
        upload the given text to the given path
        """
        with tempfile.NamedTemporaryFile() as tmp:
            self.log_action(f"uploading {tmp.name} as {path} to ")
            with open(tmp.name, "w") as text_file:
                text_file.write(text)
            self.dc.container.copy_to(tmp.name, path)
        if with_wait:
            self.wait_ready()

    def killremove(self, volumes: bool = False):
        """
        kill and remove me

        Args:
            volumes(bool): if True remove anonymous volumes associated with the container, default=True (to avoid e.g. passwords to get remembered / stuck
        """
        if self.dc:
            self.log_action("killing and removing")
            self.dc.container.kill()
            self.dc.container.remove(volumes=volumes)

    def start_cron(self):
        """
        Starting periodic command scheduler: cron.
        """
        self.dc.container.execute(["/usr/sbin/service", "cron", "start"], tty=True)

    def install_plantuml(self):
        """
        install plantuml to this container
        """
        script = """#!/bin/bash
# install plantuml
# WF 2023-05-01
apt-get update
apt-get install -y plantuml
"""
        # https://gabrieldemarmiesse.github.io/python-on-whales/docker_objects/containers/
        script_path = "/scripts/install_plantuml.sh"
        self.install_and_run_script(script, script_path)
        pass

    def run_script_in_container(self, script_to_execute: str, sudo: bool = False, use_tty: bool = False):
        """
        Make the script executable and run it in the container.

        Args:
            script_to_execute: absolute path to the script inside the container
            sudo: whether to run with sudo
            use_tty: whether to allocate a pseudo-TTY
        """
        self.dc.container.execute(["sudo", "chmod", "755", script_to_execute], tty=use_tty)
        cmd = ["sudo", "bash", script_to_execute] if sudo else ["bash", script_to_execute]
        self.dc.container.execute(cmd, tty=use_tty)


    def install_and_run_script_from_file(self, local_script_path: str, script_to_execute: str, sudo: bool = False):
        """
        Copy a local shell script into the container and execute it.

        Args:
            local_script_path: path to the local shell script file
            script_to_execute: absolute path inside the container where the script will be placed and executed
            sudo: whether to use sudo inside the container
        """
        pow_docker.copy(local_script_path, (self.dc.container.name, script_to_execute))
        self.run_script_in_container(script_to_execute, sudo=sudo)


    def install_and_run_script(self, script_content: str, script_to_execute: str, sudo: bool = False):
        """
        Upload a script string into the container and execute it.

        Args:
            script_content: the shell script contents
            script_to_execute: absolute path inside the container where the script will be saved and executed
            sudo: whether to use sudo inside the container
        """
        self.upload(script_content, script_to_execute)
        self.run_script_in_container(script_to_execute, sudo=sudo, use_tty=True)


    def install_fontawesome(self):
        """
        install fontawesome to this container
        """
        local_script = os.path.join(os.path.dirname(__file__), "resources", "install_fontawesome.sh")

        script_path = "/scripts/install_fontawesome"
        self.install_and_run_script_from_file(local_script, script_path,sudo=True)
        try:
            self.dc.container.execute(["service", "apache2", "restart"])
        except DockerException as e:
            # we expect a SIGTERM
            if not e.return_code == 143:
                raise e
        pass
