'''
Created on 2023-04-01

@author: wf
'''
from mwdocker.docker import DockerContainer
from python_on_whales import DockerException
import tempfile

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
        
    def upload(self,text:str,path:str):
        """
        upload the given text to the given path
        """
        with tempfile.NamedTemporaryFile() as tmp:
            self.log_action(f"uploading {tmp.name} to ")
            with open(tmp.name,"w") as text_file:
                text_file.write(text)
            self.dc.container.copy_to(tmp.name,path)
        
        
    def killremove(self):
        """
        kill and remove me
        """
        if self.dc:
            self.log_action("killing and removing")
            self.dc.container.kill()
            self.dc.container.remove()

    def start_cron(self):
        """
        Starting periodic command scheduler: cron.
        """        
        self.dc.container.execute(["sh","-c","service","cron","start"],tty=True)
        
    def install_plantuml(self):
        """
        install plantuml to this container
        """
        # https://gabrieldemarmiesse.github.io/python-on-whales/docker_objects/containers/
        self.dc.container.execute(["apt-get","update"],tty=True)
        self.dc.container.execute(["apt-get","install","-y","plantuml"],tty=True)
        pass
    
    def install_fontawesome(self):
        """
        install fontawesome to this container
        """
        script="""#!/bin/bash
# install fontawesome
# WF 2023-01-25
cd /var/www
curl https://use.fontawesome.com/releases/v5.15.4/fontawesome-free-5.15.4-web.zip -o fontawesome.zip
unzip -o fontawesome.zip
ln -s -f fontawesome-free-5.15.4-web fontawesome
chown -R www-data.www-data fontawesome
cd fontawesome
ln -s svgs/regular svg
cat << EOS > /etc/apache2/conf-available/font-awesome.conf
Alias /font-awesome /var/www/fontawesome
<Directory /var/www/fontawesome>
  Options Indexes FollowSymLinks MultiViews
  Require all granted
</Directory>
EOS
a2enconf font-awesome
"""
        script_path="/root/install_fontawesome"
        self.upload(script,"/root/install_fontawesome")
        # make executable
        self.dc.container.execute(["chmod","+x",script_path])
        self.dc.container.execute([script_path],tty=True)
        try:
            self.dc.container.execute(["service","apache2","restart"])
        except DockerException as e:
            # we expect a SIGTERM
            if not e.return_code==143:
                raise e
        pass
