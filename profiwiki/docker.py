'''
Created on 2023-04-01

@author: wf
'''
from mwdocker.docker import DockerContainer

class ProfiWikiContainer():
    """
    a profiwiki docker container wrapper
    """
    def __init__(self,dc:DockerContainer):
        """
        Args:
            dc: the Docc
        """
        self.dc=dc
    
    def log_action(self,action:str):
        print(f"{action} {self.dc.kind} {self.dc.name}",flush=True)
        
    def killremove(self):
        """
        kill and remove me
        """
        if self.dc:
            self.log_action("killing and removing")
            self.dc.container.kill()
            self.dc.container.remove()
        
    def install_plantuml(self):
        """
        install plantuml to this container
        """
        # https://gabrieldemarmiesse.github.io/python-on-whales/docker_objects/containers/
        self.dc.container.execute(["apt-get","update"],tty=True)
        self.dc.container.execute(["apt-get","install","-y","plantuml"],tty=True)
        pass
