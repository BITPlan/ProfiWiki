#!/bin/bash
#
# Copyright (c) 2015-2018 BITPlan GmbH
#
# WF 2015-10-23
# WF 2017-06-01 - Syntax highlighting issue checked
# WF 2018-12-30 - Ubuntu 18 check
#
# Profiwiki installation
#
# see
# https://www.mediawiki.org/wiki/Manual:Installing_MediaWiki
#
# do not uncomment this - it will spoil the $? handling
#set -e

# create globl scope variables
apachepath=/var/www/html
mwpath=/var/www/html
# name of image
name=profiwiki
# default installation mode ist docker
install="docker"

#ansi colors
#http://www.csc.uvic.ca/~sae/seng265/fall04/tips/s265s047-tips/bash-using-colors.html
blue='\x1B[0;34m'
red='\x1B[0;31m'
green='\x1B[0;32m' # '\e[1;32m' is too bright for white bg.
endColor='\x1B[0m'

#
# a colored message
#   params:
#     1: l_color - the color of the message
#     2: l_msg - the message to display
#
color_msg() {
  local l_color="$1"
  local l_msg="$2"
  echo -e "${l_color}$l_msg${endColor}"
}

#
# error
#
#   show an error message and exit
#
#   params:
#     1: l_msg - the message to display
error() {
  local l_msg="$1"
  # use ansi red for error
  color_msg $red "Error: $l_msg" 1>&2
  exit 1
}

#
# show usage
#
usage() {
  echo "$0"
  echo ""
  echo "options: "
  echo "       -c|--clean            : clean - clean up docker containers and volumes (juse with caution)"
  # -h|--help|usage|show this usage
  echo "       -h|--help             : show this usage"
  echo "    -nols|--no_local_settings: skip automatic creation of LocalSettings.php"
  echo "-composer|--composer         : install composer"
  echo "       -l|--local            : local install (default is docker)"
  echo "       -n|--needed           : check and install needed prequisites"
  echo "       -m|--mysql            : initialize and start mysql"
  echo "       -r|--random           : create random passwords"
  echo "     -smw|--smw              : install Semantic MediaWiki"
  exit 1
}

#
# generate a random password
#
random_password() {
  date +%N | shasum | base64 | head -c 16 ; echo
}

#
# get the database environment
#  params:
#     1: l_settings - the Localsettings to get the db info from
#
#
getdbenv() {
  local l_settings="$1"
  # get database parameters from local settings
  dbserver=`egrep '^.wgDBserver' $l_settings | cut -d'"' -f2`
  dbname=`egrep '^.wgDBname'     $l_settings | cut -d'"' -f2`
  dbuser=`egrep '^.wgDBuser'     $l_settings | cut -d'"' -f2`
  dbpass=`egrep '^.wgDBpassword' $l_settings | cut -d'"' -f2`
}

#
# do an sql command
#  params:
#     1: l_settings - the Localsettings to get the db info from
#
dosql() {
  # get parameters
  local l_settings="$1"
  # get database parameters from local settings
  getdbenv "$l_settings"
  # uncomment for debugging mysql statement
  # echo mysql --host="$dbserver" --user="$dbuser" --password="$dbpass" "$dbname"
  mysql --host="$dbserver" --user="$dbuser" --password="$dbpass" "$dbname" 2>&1
}

#
# prepare mysql
#
prepare_mysql() {
  if [ "$domysql" = "true" ]
  then
    service mysql start
    #/mysqlstart.sh
    color_msg $blue "setting MySQL password ..."
    mysqladmin -u root password $MYSQL_PASSWD
  else
    color_msg $blue "MySQL preparation skipped"
  fi
}

#
# check the Wiki Database defined in the  LocalSettings.php for the given site
#  params:
#   1: settings - the LocalSettings path e.g /var/www/html/mediawiki/LocalSettings.php
#
checkWikiDB() {
  # get parameters
  local l_settings="$1"
  getdbenv "$l_settings"
  color_msg $blue "checking Wiki Database $dbname with settings $l_settings"

  # check mysql access
  local l_pages=`echo "select count(*) as pages from page" | dosql "$l_settings" `
  # uncomment next line to debug
  # echo $l_pages
  #
  # this will return a number of pages or a mysql ERROR
  #
  echo "$l_pages" | grep "ERROR 1049" > /dev/null
  if [ $? -ne 0 ]
  then
    # if the db does not exist or access is otherwise denied:
    # ERROR 1045 (28000): Access denied for user '<user>'@'localhost' (using password: YES)
    echo "$l_pages" | grep "ERROR 1045" > /dev/null
    if [ $? -ne 0 ]
    then
      # if the db was just created:
      #ERROR 1146 (42S02) at line 1: Table '<dbname>.page' doesn't exist
      echo "$l_pages" | grep "ERROR 1146" > /dev/null
      if [ $? -ne 0 ]
      then
        # if everything was o.k.
        echo "$l_pages" | grep "pages" > /dev/null
        if [ $? -ne 0 ]
        then
          # something unexpected
          error "$l_pages"
        else
          # this is what we expect
          color_msg $green "$l_pages"
        fi
      else
        # db just created - fill it
        color_msg $blue "$dbname seems to be just created and empty - shall I initialize it with the backup from an empty mediawiki database? y/n"
        read answer
        case $answer in
          y|Y|yes|Yes) initialize $l_settings;;
          *) color_msg $green "ok - leaving things alone ...";;
        esac
      fi
    else
      # something unexpected
      error "$l_pages"
    fi
  else
    getdbenv "$l_settings"
    color_msg $red  "$l_pages: database $dbname not created yet"
    color_msg $blue "will create database $dbname now ..."
    echo "create database $dbname;" | mysql --host="$dbserver" --user="$dbuser" --password="$dbpass" 2>&1
    echo "grant all privileges on $dbname.* to $dbuser@'localhost' identified by '"$dbpass"';" | dosql "$l_settings"
  fi
}


#
# prepare mediawiki
#
#  params:
#   1: settings - the LocalSettings path e.g /var/www/html/mediawiki/LocalSettings.php
#
prepare_mediawiki() {
  local l_settings="$1"
  cat << EOF > $l_settings
<?php
# This file was automatically generated by the MediaWiki 1.23.11
# installer. If you make manual changes, please keep track in case you
# need to recreate them later.
#
# See includes/DefaultSettings.php for all configurable settings
# and their default values, but don't forget to make changes in _this_
# file, not there.
#
# Further documentation for configuration settings may be found at:
# https://www.mediawiki.org/wiki/Manual:Configuration_settings

# Protect against web entry
if ( !defined( 'MEDIAWIKI' ) ) {
  exit;
}

## Uncomment this to disable output compression
# \$wgDisableOutputCompression = true;

\$wgSitename = "wiki";
\$wgMetaNamespace = "Wiki";

## The URL base path to the directory containing the wiki;
## defaults for all runtime URL paths are based off of this.
## For more information on customizing the URLs
## (like /w/index.php/Page_title to /wiki/Page_title) please see:
## https://www.mediawiki.org/wiki/Manual:Short_URL
\$wgScriptPath = "/mediawiki";
\$wgScriptExtension = ".php";

## The protocol and server name to use in fully-qualified URLs
\$wgServer = "http://$hostname";

## The relative URL path to the skins directory
\$wgStylePath = "\$wgScriptPath/skins";

## The relative URL path to the logo.  Make sure you change this from the default,
## or else you'll overwrite your logo when you upgrade!
#\$wgLogo = "\$wgStylePath/common/images/wiki.png";
\$wgLogo = "/profiwiki/icons/135px-Profiwiki.svg.png";

## UPO means: this is also a user preference option

\$wgEnableEmail = false;
\$wgEnableUserEmail = true; # UPO

\$wgEmergencyContact = "apache@localhost";
\$wgPasswordSender = "apache@localhost";

\$wgEnotifUserTalk = false; # UPO
\$wgEnotifWatchlist = false; # UPO
\$wgEmailAuthentication = true;

## Database settings
\$wgDBtype = "mysql";
\$wgDBserver = "localhost";
\$wgDBname = "wiki";
\$wgDBuser = "root";
\$wgDBpassword = "$MYSQL_PASSWD";

# MySQL specific settings
\$wgDBprefix = "";

# MySQL table options to use during installation or update
\$wgDBTableOptions = "ENGINE=InnoDB, DEFAULT CHARSET=utf8";

# Experimental charset support for MySQL 5.0.
\$wgDBmysql5 = false;

## Shared memory settings
\$wgMainCacheType = CACHE_NONE;
\$wgMemCachedServers = array();

## To enable image uploads, make sure the 'images' directory
## is writable, then set this to true:
\$wgEnableUploads = true;
\$wgFileExtensions = array_merge(\$wgFileExtensions, array('doc', 'pdf','ppt','docx', 'docxm','xlsx','xlsm', 'pptx', 'pptxm','jpg','svg','htm','html','xls','xml','zip'));

#\$wgUseImageMagick = true;
#\$wgImageMagickConvertCommand = "/usr/bin/convert";

# InstantCommons allows wiki to use images from http://commons.wikimedia.org
\$wgUseInstantCommons = false;

## If you use ImageMagick (or any other shell command) on a
## Linux server, this will need to be set to the name of an
## available UTF-8 locale
\$wgShellLocale = "C.UTF-8";

## If you want to use image uploads under safe mode,
## create the directories images/archive, images/thumb and
## images/temp, and make them all writable. Then uncomment
## this, if it's not already uncommented:
#\$wgHashedUploadDirectory = false;

## Set \$wgCacheDirectory to a writable directory on the web server
## to make your wiki go slightly faster. The directory should not
## be publically accessible from the web.
#\$wgCacheDirectory = "$IP/cache";

# Site language code, should be one of the list in ./languages/Names.php
\$wgLanguageCode = "en";

\$wgSecretKey = "16da25466b94b683dab67d4533e11e40e0f7b24a15aaab2b3ef5600143ce0007";

# Site upgrade key. Must be set to a string (default provided) to turn on the
# web installer while LocalSettings.php is in place
\$wgUpgradeKey = "80554160e8352086";

## Default skin: you can change the default skin. Use the internal symbolic
## names, ie 'cologneblue', 'monobook', 'vector':
\$wgDefaultSkin = "vector";

## For attaching licensing metadata to pages, and displaying an
## appropriate copyright notice / icon. GNU Free Documentation
## License and Creative Commons licenses are supported so far.
\$wgRightsPage = ""; # Set to the title of a wiki page that describes your license/copyright
\$wgRightsUrl = "";
\$wgRightsText = "";
\$wgRightsIcon = "";

# Path to the GNU diff3 utility. Used for conflict resolution.
\$wgDiff3 = "/usr/bin/diff3";

# The following permissions were set based on your choice in the installer
\$wgGroupPermissions['*']['createaccount'] = false;
\$wgGroupPermissions['*']['edit'] = false;
\$wgGroupPermissions['*']['read'] = false;

# Enabled Extensions. Most extensions are enabled by including the base extension file here
# but check specific extension documentation for more details
# The following extensions were automatically enabled:
require_once "\$IP/extensions/ParserFunctions/ParserFunctions.php";
require_once "\$IP/extensions/PdfHandler/PdfHandler.php";
require_once "\$IP/extensions/SyntaxHighlight_GeSHi/SyntaxHighlight_GeSHi.php";
require_once "\$IP/extensions/WikiEditor/WikiEditor.php";

# End of automatically generated settings.
# Add more configuration options below.
EOF
}

#
# get the apach path
#
apache_path() {
  local l_apachepath="/whereisapache";
  # set the Path to the Apache Document root
  os=`uname`
  case $os in
   Darwin )
     # Macports installation
     # https://trac.macports.org/wiki/howto/Apache2
     l_apachepath="/opt/local/apache2/htdocs"
     ;;
   *)
     l_apachepath="/var/www/html"
     ;;
  esac
  if [ ! -d $l_apachepath ]
  then
    error "Apache DocumentRoot $l_apachepath is missing"
  fi
  echo $l_apachepath
}

#
# get the path for mediawiki and it's settings
#
get_mwpath() {
  local l_apachepath="$1"
  # set the Path to the Mediawiki installation (influenced by MEDIAWIKI ENV variable)

  # check for a preinstalled MediaWiki
  # e.g. in digitialocean droplet / a docker container
  if [ -d $l_apachepath/extensions ]
  then
    mwpath=$l_apachepath
  else
    mwpath=$l_apachepath/$MEDIAWIKI
  fi
  # create a symbolic link
  if [ ! -L $l_apachepath/mediawiki ]
  then
    $sudo ln -s $mwpath $l_apachepath/mediawiki
  fi
  echo $mwpath
}

#
# install mediawiki in the given path
#  param
#   #1: l_apachepath path to apache home directory
#   #2: l_mwpath - path to mediawiki
#
optional_install_mediawiki() {
  local l_apachepath="$1"
  local l_mwpath="$2"
  color_msg $blue "checking Mediawiki $MEDIAWIKI_VERSION installation in $l_mwpath"
  # check whether mediawiki is installed
  if [ ! -d $l_mwpath/ ]
  then
    cd /usr/local/src
    if [ ! -f $MEDIAWIKI.tar.gz ]
    then
      curl -O https://releases.wikimedia.org/mediawiki/$MEDIAWIKI_VERSION/$MEDIAWIKI.tar.gz
    fi
    cd $l_apachepath
    tar -xzvf /usr/local/src/$MEDIAWIKI.tar.gz
  fi
}

#
# installation of mediawiki
#
mediawiki_install() {
  local l_option="$1"
  local l_apachepath=$(apache_path)

  if [ "$MEDIAWIKI_VERSION" = "" ]
  then
    error "environment variable MEDIAWIKI_VERSION not set"
  fi
  color_msg $blue "Preparing Mediawiki $MEDIAWIKI_VERSION"

  # get the mediwawiki path
  local l_mwpath=$(get_mwpath $l_apachepath)

  optional_install_mediawiki $l_apachepath $l_mwpath

  # prepare mysql
  # if there is no MYSQL password given
  if [ "$MYSQL_PASSWD" = "" ]
  then
    prepare_mysql
  fi

  # start the services
  service apache2 start
  install_mediawiki $l_option $l_mwpath
}

#
# intall media wiki
# paramams
#   #1: l_option
#   #2: l_mwpath - path to mediawiki
#
install_mediawiki() {
  local l_option="$1"
  local l_mwpath="$2"
  # use the one created by this script instead
  if [ "$l_option" == "-nols" ]
  then
    color_msg $blue "You choose to skip automatic creation of LocalSettings.php"
    color_msg $blue "you can now install MediaWiki with the url http://$hostname/mediawiki"
  else
    # MediaWiki LocalSettings.php path
    localsettings_dist=$l_mwpath/LocalSettings.php.dist
    localsettings=$l_mwpath/LocalSettings.php

    if [ -f $localsettings ]
    then
      color_msg $green "$localsettings exist"
      SYSOP_PASSWD=`cat $HOME/.sysop.passwd`
    else
      # prepare the mediawiki
      # by creating LocalSettings
      prepare_mediawiki $localsettings_dist

      # make sure the Wiki Database exists
      checkWikiDB $localsettings_dist

      # get the database environment variables
      getdbenv $localsettings_dist

      # run the Mediawiki install script
      php $mwpath/maintenance/install.php \
        --dbname $dbname \
        --dbpass $dbpass \
        --dbserver $dbserver \
        --dbtype mysql \
        --dbuser $dbuser \
        --email mediawiki@localhost \
        --installdbpass $dbpass \
        --installdbuser $dbuser \
        --pass $SYSOP_PASSWD \
        --scriptpath /mediawiki \
        Sysop

      # fix the realname of the Sysop
      #    the installscript can't do that
      #    see https://doc.wikimedia.org/mediawiki-core/master/php/install_8php_source.html)
      echo "update user set user_real_name='Sysop' where user_name='Sysop'" | dosql $localsettings_dist
      # enable the LocalSettings
      # move the LocalSettings.php created by the installer above to the side
      mv $mwpath/LocalSettings.php $mwpath/LocalSettings.php.install
      mv $mwpath/LocalSettings.php.dist $mwpath/LocalSettings.php
    fi
    color_msg $blue "Mediawiki has been installed with users:"
    echo "select user_name,user_real_name from user" | dosql $localsettings
    # remember the installation state
    installed="true"
  fi
}

#
# check that composer is installed
#
check_composer() {
  if [ ! -f composer.phar ]
  then
    # see https://getcomposer.org/doc/00-intro.md
    curl -sS https://getcomposer.org/installer | php
    #curl -O http://getcomposer.org/composer.phar
    php composer.phar update
  else
    color_msg $green "composer is already available"
  fi
}

#
# autoinstall
#
#  check that l_prog is available by calling which
#  if not available install from given package depending on Operating system
#
#  params:
#    1: l_prog: The program that shall be checked
#    2: l_linuxpackage: The apt-package to install from
#    3: l_macospackage: The MacPorts package to install from
#
autoinstall() {
  local l_prog=$1
  local l_linuxpackage=$2
  local l_macospackage=$3
  os=`uname`
  color_msg $blue "checking that $l_prog  is installed on os $os ..."
  case $os in
    # Mac OS
    Darwin*)
      which $l_prog
      if [ $? -eq 1 ]
      then
      	if [ $l_macospackage="-" ]
	      then
          color_msg $red "no MacPorts package specified for $l_prog - please install yourself manually"
	      else
          color_msg $blue "installing $l_prog from MacPorts package $l_macospackage"
          sudo port install $l_macospackage
        fi
      else
        color_msg $green "macports package $l_macospackage already installed"
      fi
    ;;
    # e.g. Ubuntu/Fedora/Debian/Suse
    Linux)
      dpkg -s $l_linuxpackage | grep Status
      if [ $? -eq 1 ]
      then
        color_msg $blue "installing $l_prog from apt-package $l_linuxpackage"
        $sudo apt-get -y install $l_linuxpackage
      else
        color_msg $green "apt-package $l_linuxpackage already installed"
      fi
    ;;
    # git bash (Windows)
    MINGW32_NT-6.1)
      error "$l_prog ist not installed"
    ;;
    *)
      error "unknown operating system $os"
  esac
}

#
# some of the software might have already been installed by the Dockerfile
#
check_needed() {
  # software we'd always like to see installed
  autoinstall curl curl curl
  autoinstall dialog dialog dialog
  autoinstall dot graphviz graphviz
  autoinstall convert imagemagick imagemagick
  # for plantuml and profiwiki
  # autoinstall java openjdk-8-jdk -
  # software for local install
  case $install in
    local)
      phpversion="72"
      autoinstall mysql mysql-server mysql-server
      autoinstall php $php $php
      autoinstall apache2ctl apache2 apache2
    ;;
    docker)
      phpversion=$(php --version | head -1 | cut -c 5-7 | sed 's/\.//')
      ;;
  esac
  color_msg $green "PHP Version is $phpversion"
  php=php${phpversion}
  phpexts=/tmp/phpexts$$
  php -r "print_r(get_loaded_extensions());" > $phpexts
  for module in iconv curl gd mysql openssl mbstring xml
  do
    grep "=> $module" $phpexts > /dev/null
    if [ $? -ne 0 ]
    then
      autoinstall php-$module $php-$module $php-$module
    else
      color_msg $green "php module $module already installed"
    fi
  done
}

#
# install docker
#
docker_autoinstall() {
  autoinstall docker docker docker
  # add the current user to the docker group to avoid need of sudo
  sudo usermod -aG docker $(id -un)
  autoinstall docker-compose docker-compose docker-compose
}

#
# (re)start the docker containers
#
#  param 1: name
#
docker_restart() {
  local l_name="$1"
  for service in mw db
  do
    container="${l_name}_${service}_1"
    color_msg $blue "stopping and removing container $container"
    docker stop $container
    docker rm $container
  done
  composeyml=${l_name}/docker-compose.yml
  color_msg $blue "building $l_name"
  docker-compose -f $composeyml build
  color_msg $blue "starting $l_name"
  docker-compose -f $composeyml up
}

#
# local install
#
install_locally() {
  # check the needed installs
  check_needed
  # install mediawiki with the given options
  mediawiki_install "$option"

  # do we have a running mediawiki?
  if [ "$installed" == "true" ]
  then
    # shall we install composer?
    if [ "$composer" == "true" ]
    then
      color_msg $blue "checking composer at $mwpath"
      cd $mwpath
      check_composer
    fi

    # shall we install Semantic Media Wiki?
    if [ "$smw" == "true" ]
    then
      color_msg $blue "installing semantic mediawiki Version "
      cd $mwpath
      # see https://semantic-mediawiki.org/wiki/Help:Installation/Using_Composer_with_MediaWiki_1.22_-_1.24
      php composer.phar require mediawiki/semantic-media-wiki "~$SMW_VERSION"
      php maintenance/update.php
cat << EOF >> $localsettings
  # enableSemantics( "$hostname" );
EOF
  fi
  color_msg $blue "you can now login to MediaWiki with the url http://$hostname/mediawiki"
  color_msg $blue "    User: Sysop"
  color_msg $blue "Password: $SYSOP_PASSWD"
  echo "$SYSOP_PASSWD" > $HOME/.sysop.passwd
fi
}
#
# check the match of two entered passwords
#  params
#    #1 l_title: the title of the password
#    #2 l_1: the first password
#    #3 l_2: the second password
#
check_match() {
  local l_title="$1"
  local l_1="$2"
  local l_2="$3"
  if [ "$l_1" != "$l_2" ]
  then
    echo "$l_title"
  else
    if [ "$l_1" = "" ]
    then
      echo "$l_title"
    fi
  fi
}
#
# show the given password dialog
#
password_dialog() {
  backtitle="$1"
  formtitle="$2"
  DIALOG=dialog

  DIALOG_OK=0
  DIALOG_CANCEL=1
  DIALOG_ESC=255

  returncode=0
  while test $returncode != $DIALOG_CANCEL && test $returncode != 250
  do
    exec 3>&1
    pwdata=$($DIALOG  \
	  --backtitle "$backtitle" \
	  --insecure  \
	  --passwordform "$formtitle" \
15 60 0 \
	"               MySQL root:"  1 2 "${pwarray[0]}" 1 29 16 0 \
	"     MySQL root (confirm):"  2 2 "${pwarray[1]}" 2 29 16 0 \
	"           MySQL wikuser):"  4 2 "${pwarray[2]}" 4 29 16 0 \
	"  MySQL wikuser (confirm):"  5 2 "${pwarray[3]}" 5 29 16 0 \
	"          mediawiki Sysop:"  7 2 "${pwarray[4]}" 7 29 16 0 \
	"mediawiki Sysop (confirm):"  8 2 "${pwarray[5]}" 8 29 16 0 \
	2>&1 1>&3)
  returncode=$?
  exec 3>&-

  case $returncode in
    $DIALOG_ESC|$DIALOG_CANCEL)
      "$DIALOG" \
	--clear \
	--backtitle "$backtitle" \
	--yesno "Really about ProfiWiki installation?" 6 30
	case $? in
  	  $DIALOG_OK)
            clear
	    error "Installation aborted - rerun e.g. with --random option to automatically set passwords"
	    break
	  ;;
	  $DIALOG_CANCEL)
	    returncode=99
	  ;;
	esac
	;;
	$DIALOG_OK)
	  #echo $pwdata
	  pwarray=($(echo "$pwdata"))
	  msg1=$(check_match "MySQL root "      ${pwarray[0]} ${pwarray[1]})
	  msg2=$(check_match "MySQL wikiuser "  ${pwarray[2]} ${pwarray[3]})
	  msg3=$(check_match "mediawiki Sysop " ${pwarray[4]} ${pwarray[5]})
	  msg="$msg1$msg2$msg3"
	  if [ "$msg" = "" ]
          then
            export MYSQL_PASSWORD="${pwarray[0]}"
            export SYSOP_PASSWD="${pwarray[4]}"
	    break;
	  else
	    formtitle="$msg1$msg2${msg3}passwords do not match or empty - please reenter"
	  fi
	  ;;
	*)
	  echo "unknown dialog return code $returncode"
	  ;;
	esac
  done
}

#
# get the passwords
#
get_passwords() {
  if [ "$random_passwords" = "true" ]
  then
    # create a random SYSOP passsword
    export SYSOP_PASSWD=$(random_password)
    export MYSQL_PASSWORD=$(random_password)
  else
    password_dialog "ProfiWiki Setup" "Please specify passwords"
  fi
}

# cleanup the docker enviroment
clean() {
  echo "cleaning docker environment - stopping and removing containers and removing volumes for profiwiki"
  docker stop $(docker ps -q --filter="name=profiwiki")
  docker rm $(docker ps -aq --filter="name=profiwiki")
  for volume in $(profiwiki_volumes)
  do
    docker volume rm $volume
  done
}

#
# start of script
# check arguments
option=""
installed=""
# get the hostname
#hostname=`hostname`
hostname=$IMAGEHOSTNAME

if [ "$MEDIAWIKI_VERSION" = "" ]
then
  export MEDIAWIKI_VERSION=1.27
  export MEDIAWIKI=mediawiki-1.27.5
fi
if [ "SMW_VERSION" = "" ]
then
  export SMW_VERSION=3.0.0
fi
if [ "MEDIAWIKI_PORT" = "" ]
then
  export MEDIAWIKI_PORT="8080"
fi


while test $# -gt 0
do
  case $1 in
    -c|--clean)
      clean;;

    -composer|--composer)
      composer="true";;

    -i|-imw|--installmediawiki)
      install_mediawiki $option $(apache_path)
      ;;

    # -h|--help|usage|show this usage
    -h|--help)
      usage;;

    # local install
    -l|--local)
      install="local";;

    -m|--mysql)
      domysql="true"
      ;;

    -n|--needed)
      check_needed
      exit 0;;

    -nols|--no_local_settings)
      option="-nols";;

    -r|--random)
      random_passwords="true"
      ;;

    -p|--port)
      shift
      export MEDIAWIKI_PORT="$1"
      ;;

    -smw|--smw)
      composer="true";
      smw=true;;

    *)
      params="$params $1"
  esac
  shift
done


# depending on install mode we use
# docker or install locally
case $install in
  docker)
    color_msg $blue "installing $name using docker on $(hostname) os $(uname)"
    docker_autoinstall
    name=$(echo profiwiki_${MEDIAWIKI_VERSION} | sed 's/\./_/g')
    color_msg $blue "creating $name docker compose"
    get_passwords
    ./gencompose $name
    # make sure this script is in the context of the docker-compose environment
    l_script=$(basename $0)
    # redundant copy ...
    cp -p $l_script $name/$l_script
    docker_restart $name
    ;;
  local)
    color_msg $blue "installing $name locally on $(hostname) os $(uname)"
    sudo="sudo"
    install_locally
    ;;
esac
