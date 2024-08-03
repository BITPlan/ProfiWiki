"""
Created on 2023-04-01

@author: wf
"""

import tempfile

from mwdocker.docker import DockerContainer
from python_on_whales import DockerException


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

    def upload(self, text: str, path: str):
        """
        upload the given text to the given path
        """
        with tempfile.NamedTemporaryFile() as tmp:
            self.log_action(f"uploading {tmp.name} as {path} to ")
            with open(tmp.name, "w") as text_file:
                text_file.write(text)
            self.dc.container.copy_to(tmp.name, path)

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
        script_path = "/root/install_plantuml.sh"
        self.install_and_run_script(script, script_path)
        pass

    def install_and_run_script(self, script: str, script_path: str):
        """
        install and run the given script

        Args:
            script(str): the source code of the script
            script_path(str): the path to copy the script to and then execute
        """
        self.upload(script, script_path)
        # make executable
        self.dc.container.execute(["chmod", "+x", script_path])
        self.dc.container.execute([script_path], tty=True)

    def install_fontawesome(self):
        """
        install fontawesome to this container
        """
        script = """#!/bin/bash
# install fontawesome
# WF 2023-01-25
version=6.4.0
#version=5.15.4
#version=4.7.0
zip_url=https://github.com/FortAwesome/Font-Awesome/releases/download/$version/fontawesome-free-$version-desktop.zip
#https://github.com/FortAwesome/Font-Awesome/releases/download/5.15.4/fontawesome-free-5.15.4-desktop.zip

cd /var/www
#curl https://use.fontawesome.com/releases/$version/fontawesome-free-$version-web.zip -o fontawesome.zip
curl --location $zip_url -o fontawesome.zip
unzip -o fontawesome.zip
ln -s -f fontawesome-free-$version-desktop fontawesome
chown -R www-data.www-data fontawesome
cd fontawesome
ln -s svgs/solid svg
cat << EOS > /etc/apache2/conf-available/font-awesome.conf
Alias /font-awesome /var/www/fontawesome
<Directory /var/www/fontawesome>
  Options Indexes FollowSymLinks MultiViews
  Require all granted
</Directory>
EOS
a2enconf font-awesome
"""
        script_path = "/root/install_fontawesome"
        self.install_and_run_script(script, script_path)
        try:
            self.dc.container.execute(["service", "apache2", "restart"])
        except DockerException as e:
            # we expect a SIGTERM
            if not e.return_code == 143:
                raise e
        pass
