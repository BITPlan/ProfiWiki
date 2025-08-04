"""
Created on 2023-04-01

@author: wf
"""

import os

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
            dc(DockerContainer): the container to wrap
        """
        self.dc = dc

    @staticmethod
    def get_image(image_name:str):
        image=None
        try:
            image=pow_docker.image.inspect(image_name)
        except Exception as ex:
            # FIXME filter exceptions that need to be handled
            if "-something we would like to handle -" in str(ex):
                pass
            pass
        return image

    def commit(self, tag: str):
        """
        Commit the current state of this container to a new image.

        Args:
            tag(str): the target image tag e.g. 'ProfiWiki-1.39.13'
        """
        self.log_action(f"committing to image {tag}")
        pow_docker.commit(container=self.dc.container,tag=tag)

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


    def run_script_in_container(self, script_to_execute: str, sudo: bool = False):
        """
        Make the script executable and run it in the container.

        Args:
            script_to_execute: absolute path to the script inside the container
            sudo: whether to run with sudo
            use_tty: whether to allocate a pseudo-TTY
        """
        self.dc.execute("sudo", "chmod", "755", script_to_execute)
        cmd = ["sudo"] if sudo else []
        cmd += ["bash", script_to_execute]
        self.dc.execute(*cmd)


    def install_and_run_script_from_file(self, script_name: str, sudo: bool = False):
        """
        Copy a local shell script into the container and execute it.

        Args:
            local_script_path: path to the local shell script file
            sudo: whether to use sudo inside the container
        """
        local_script_path = self.get_local_script(script_name)
        script_to_execute=f"/scripts/{script_name}"
        pow_docker.copy(local_script_path, (self.dc.container.name, script_to_execute))
        self.run_script_in_container(script_to_execute, sudo=sudo)

    def get_local_script(self,name:str)->str:
        script_path=os.path.join(os.path.dirname(__file__), "resources", name)
        return script_path

    def install_plantuml(self):
        """
        install plantuml to this container
        """
        self.install_and_run_script_from_file("install_plantuml.sh",sudo=True)
        pass

    def install_fontawesome(self):
        """
        install fontawesome to this container
        """
        script_name="install_fontawesome.sh"
        self.install_and_run_script_from_file(script_name,sudo=True)
        try:
            self.dc.container.execute(["service", "apache2", "restart"])
        except DockerException as e:
            # we expect a SIGTERM
            if not e.return_code == 143:
                raise e
        pass
