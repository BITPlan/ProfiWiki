#!/bin/bash
#
# Copyright (c) 2015-2019 BITPlan GmbH
#
# WF 2015-10-23
# WF 2017-06-01 - Syntax highlighting issue checked
# WF 2018-12-30 - Ubuntu 18 check
# WF 2019-10-13 -
#
# Profiwiki installation
#
# see
# https://www.mediawiki.org/wiki/Manual:Installing_MediaWiki
#
# do not uncomment this - it will spoil the $? handling
#set -e

# create global scope variables
apachepath=/var/www/html
mwpath=/var/www/html
install_dir=$(dirname $0)

# name of image
IMAGE_PREFIX=mediawiki

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
  echo "       -i                    : use install.php to create LocalSettings.php"
  echo "    -ismw SMW_VERSION        : install semanticmediawiki with the given version using composer"
  echo "-composer|--composer         : install composer"
  echo "       -l|--local            : local install (default is docker)"
  echo "       -n|--needed           : check and install needed prequisites"
  echo "       -m|--mysql            : initialize and start mysql"
  echo "       -r|--random           : create random passwords"
  echo "     -smw|--smw              : install Semantic MediaWiki"
  exit 1
}

#
# get a time stamp
#
timestamp() {
  date "+%Y-%m-%d %H:%M:%S"
}

#
# generate a random password of the given length
# params
#  #1: l_len: wanted lenght of password
#
random_password_len() {
  local l_len="$1"
  python -c "import string;import random;print (''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + '!?+-%_/:()#$&' +string.digits) for x in range($l_len)))"
  # does not work on macos
  # date +%N | shasum | base64 | head -c $l_len ; echo
}

# generate a random password
# default is a 16 char password
random_password() {
  random_password_len 16
}

#
# get the database environment
# - if the LocalSettings already exists from the local l_settings
# other wise from wiki-config.sh and wiki-passwdconfig.sh
# param 1 - the path to the local settings
#
getdbenv() {
  local l_settings=$mwpath/LocalSettings.php
  if [ -f $l_settings ]
  then
    # get database parameters from local settings
    dbserver=`egrep '^.wgDBserver' $l_settings | cut -d'"' -f2`
    dbname=`egrep '^.wgDBname'     $l_settings | cut -d'"' -f2`
    dbuser=`egrep '^.wgDBuser'     $l_settings | cut -d'"' -f2`
    dbpass=`egrep '^.wgDBpassword' $l_settings | cut -d'"' -f2`
  else
    # get parameters from config scripts
    . $install_dir/wiki-config.sh
    . $install_dir/wiki-pwconfig.sh
    dbpass=$MYSQL_PASSWORD
  fi
}

#
# do an sql command
#
dosql() {
  # get database environment
  getdbenv
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
# check the Wiki Database
#
checkWikiDB() {
  getdbenv
  color_msg $blue "checking Wiki Database $dbname on server $dbserver with user $dbuser"

  # check mysql access
  local l_pages=$(echo "select count(*) as pages from page" | dosql)

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
        color_msg $blue "$dbname seems to be just created and empty"
        #read answer
        #case $answer in
        #  y|Y|yes|Yes) initialize $l_settings;;
        #  *) color_msg $green "ok - leaving things alone ...";;
        #esac
      fi
    else
      # something unexpected
      error "$l_pages"
    fi
  else
    getdbenv
    color_msg $red  "$l_pages: database $dbname not created yet"
    color_msg $blue "will create database $dbname now ..."
    echo "create database $dbname;" | mysql --host="$dbserver" --user="$dbuser" --password="$dbpass" 2>&1
    echo "grant all privileges on $dbname.* to $dbuser@'localhost' identified by '"$dbpass"';" | dosql
  fi
}

#
# patch settings
#
#  params:
#   1: l_settings - the LocalSettings path e.g /var/www/html/mediawiki/LocalSettings.php
#   2: l_name - the name of the value to modify or add to add a line/values
#   3: l_value - the value to set
#
patch_settings() {
  local l_settings="$1"
  local l_name="$2"
  local l_value="$3"
  # check that the value exists
  grep "\$$l_name[[:space:]]=" "$l_settings" > /dev/null
  if [ $? -eq 0 ]
  then
    color_msg $blue "patching $l_settings setting $l_name to ... $l_value"
    os=`uname`
    case $os in
      Darwin )
        sed -E -i "" "/\$$l_name[[:space:]]/s/=.*$/= $l_value;/" $l_settings
      ;;
      *)
        sed -E -i "/\$$l_name[[:space:]]/s/=.*$/= $l_value;/" $l_settings
    esac
  else
    # add
    echo "\$${l_name} = $l_value;" >> $l_settings
  fi
}

#
# get local settings lines for the extra_Permissions
#  params:
#    #1: l_createaccount
#    #2: l_edit
#    #3: l_read
#
extra_Permissions() {
  local l_createaccount="$1"
  local l_edit="$2"
  local l_read="$3"
  cat << EOF
  # The following permissions were set based on your choice in the installer
  \$wgGroupPermissions['*']['createaccount'] = $l_createaccount;
  \$wgGroupPermissions['*']['edit'] = $l_edit;
  \$wgGroupPermissions['*']['read'] = $l_read;
EOF
}

#
# get extra local settings
#  parameters
#   #1: l_version
#
extra_LocalSettings() {
  local l_version="$1"
  cat << EOF

# Enabled extensions. Most of the extensions are enabled by adding
# wfLoadExtensions('ExtensionName');
# to LocalSettings.php. Check specific extension documentation for more details.
# The following extensions were automatically enabled:
wfLoadExtension( 'ImageMap' );
wfLoadExtension( 'Nuke' );
wfLoadExtension( 'ParserFunctions' );
wfLoadExtension( 'PdfHandler' );
wfLoadExtension( 'Renameuser' );
wfLoadExtension( 'SyntaxHighlight_GeSHi' );
wfLoadExtension( 'WikiEditor' );
EOF
case $l_version in
  1.31*)
cat << EOF
# MW 1.31 only
wfLoadExtension( 'CategoryTree' );
wfLoadExtension( 'OATHAuth' );
wfLoadExtension( 'ReplaceText' );
EOF
;;
esac
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
  local l_apachepath=$(apache_path)
  local l_mwpath=$l_apachepath
  # set the Path to the Mediawiki installation (influenced by MEDIAWIKI ENV variable)

  # check for a preinstalled MediaWiki
  # e.g. in digitialocean droplet / a docker container
  if [ ! -d $l_mwpath/extensions ]
  then
    l_mwpath=$l_apachepath/$MEDIAWIKI
  fi
  # create a symbolic link
  #if [ ! -L $l_apachepath/mediawiki ]
  #then
  #    $sudo ln -s $mwpath $l_apachepath/mediawiki
  #fi
  echo $l_mwpath
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
  if [ ! -d $l_mwpath/extensions ]
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
# install media wiki
# paramams
#   #1: l_option
#   #2: l_mwpath
#
install_mediawiki() {
  local l_option="$1"
  local l_settings="$mwpath/LocalSettings.php"
  if [ -f "$l_settings" ]
  then
    color_msg $green "$l_settings already exists"
  else
    install_mediawiki_withscript "$1"
    if [ ! -f $l_settings ]
    then
      error "$l_settings not created"
    else
      color_msg $green "$l_settings where created"
    fi
    ## To enable image uploads, make sure the 'images' directory
    ## is writable, then set this to true:
    # https://www.mediawiki.org/wiki/Manual:$wgEnableUploads
    patch_settings "$l_settings" wgEnableUploads true
    # https://www.mediawiki.org/wiki/Manual:$wgFileExtensions
    patch_settings "$l_settings" wgFileExtensions "array_merge(\$wgFileExtensions, array('doc', 'docx', 'docxm','jpg','htm','html','pdf','png','ppt','pptx', 'pptxm','svg','xls','xml','xlsx','xlsm','zip'))"
    # InstantCommons allows wiki to use images from http://commons.wikimedia.org
    patch_settings "$l_settings" wgUseInstantCommons true
    # MediaWiki's big brother flag
    # https://www.mediawiki.org/wiki/Manual:$wgPingback
    patch_settings "$l_settings" wgPingBack false
    # add extra setting
    color_msg $blue "adding extra settings to $l_settings"
    # create=false edit=false read=true
    extra_Permissions false false true >> $l_settings
    extra_LocalSettings $MEDIAWIKI_VERSION  >> $l_settings
  fi
}

#
# install media wiki
# paramams
#   #1: l_option
#
install_mediawiki_withscript() {
  local l_option="$1"

  # use the one created by this script instead
  if [ "$l_option" == "-nols" ]
  then
    color_msg $blue "You choose to skip automatic creation of LocalSettings.php"
    color_msg $blue "you can now install MediaWiki with the url http://localhost:$MEDIAWIKI_PORT"
  else
    checkWikiDB

    # get the database environment variables
    getdbenv

    # run the Mediawiki install script
    color_msg $blue "running MediaWiki installation for $dbname on server $dbserver with user $dbuser"
    color_msg $blue "wiki name is $wikiname"
    color_msg $blue "setting language to $wikilang and admin to $wikiuser"
    php $mwpath/maintenance/install.php \
      --dbname $dbname \
      --dbpass $dbpass \
      --dbserver $dbserver \
      --dbtype mysql \
      --dbuser $dbuser \
      --installdbpass $dbpass \
      --installdbuser $dbuser \
      --lang $wikilang \
      --pass $SYSOP_PASSWD \
      --server http://localhost:$MEDIAWIKI_PORT \
      --scriptpath "" \
      $wikiname \
      $wikiuser

    # fix the realname of the Sysop
    #    the installscript can't do that
    #    see https://doc.wikimedia.org/mediawiki-core/master/php/install_8php_source.html)
    echo "update user set user_real_name='Sysop' where user_name='Sysop'" | dosql
    color_msg $blue "Mediawiki has been installed with users:"
    echo "select user_name,user_real_name from user" | dosql
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
  else
    color_msg $green "composer is already available"
  fi
  # update composer
  php composer.phar update --no-dev
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
  which usermod
  if [ $? -eq 0 ]
  then
    sudo usermod -aG docker $(id -un)
  fi
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
# install semantic mediawiki
#
install_smw() {
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
      color_msg $blue "installing semantic mediawiki Version $SMW_VERSION"
      cd $mwpath
      local l_settings="$mwpath/LocalSettings.php"
      cat << EOF >> $l_settings
  # see https://www.semantic-mediawiki.org/wiki/Help:Installation/Using_Composer_with_MediaWiki_1.25%2B
  enableSemantics();
EOF

      # see https://semantic-mediawiki.org/wiki/Help:Installation/Using_Composer_with_MediaWiki_1.22_-_1.24
      php composer.phar require mediawiki/semantic-media-wiki "$SMW_VERSION"
      php maintenance/update.php --skip-external-dependencies
      php extensions/SemanticMediaWiki/maintenance/rebuildData.php -d 50 -v
      color_msg $blue "finished installation of semantic mediawiki Version $SMW_VERSION"
    fi

    color_msg $blue "you can now login to MediaWiki with the url http://localhost:$MEDIAWIKI_PORT"
    color_msg $blue "    User: Sysop"
    color_msg $blue "Password: $SYSOP_PASSWD"
  fi
}


#
# local install
#
install_locally() {
  # check the needed installs
  check_needed
  # install mediawiki with the given options
  mediawiki_install "$option"
  install_smw

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
	--yesno "Really abort ProfiWiki installation?" 6 30
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
# and save them in the given shell file
# paramams
#  1: l_pwconfig - the file for the password configuration
#
get_passwords() {
  local l_pwconfig="$1"
  if [ -f $l_pwconfig ]
  then
    # get the sysop password
    export SYSOP_PASSWD=$(cat $l_pwconfig  | grep SYSOP_PASSWD | cut -f2 -d'"')
    export MYSQL_PASSWORD=$(cat $l_pwconfig  | grep MYSQL_PASSWORD | cut -f2 -d'"')
  else
    if [ "$random_passwords" = "true" ]
    then
      # create a random SYSOP passsword
      export SYSOP_PASSWD=$(random_password)
      export MYSQL_PASSWORD=$(random_password)
    else
      password_dialog "ProfiWiki Setup" "Please specify passwords"
   fi
   local l_now=$(timestamp)
   cat << EOF > $l_pwconfig
#!/bin/bash
# generated by $0 at $l_now
export SYSOP_PASSWD="$SYSOP_PASSWD"
export MYSQL_PASSWORD="$MYSQL_PASSWORD"
EOF
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
      install_mediawiki $option
      install="none"
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

    -ismw)
     installed="true"
     composer="true"
     smw=true
     shift
     if [ $# -lt 1 ]
     then
       usage
     fi
     export SMW_VERSION="$1"
     get_passwords /root/wiki-pwconfig.sh
     install_smw
     install="none"
     ;;

    -smw|--smw)
      composer="true"
      smw=true
      ;;

    *)
      params="$params $1"
  esac
  shift
done

# depending on install mode we use
# docker or install locally
case $install in
  docker)
    docker_autoinstall
    color_msg $blue "installing ${IMAGE_PREFIX} using docker on $(hostname) os $(uname)"
    name=$(echo ${IMAGE_PREFIX}${MEDIAWIKI_VERSION} | sed 's/\.//g')
    color_msg $blue "creating ${name} docker compose"
    if [ ! -d $name ]
    then
      mkdir $name
    fi
    get_passwords $name/wiki-pwconfig.sh
		# get the configuration values
    getdbenv
    ./gencompose $name
    # make sure this script is in the context of the docker-compose environment
    l_script=$(basename $0)
    # redundant copy of this script...
    cp -p $0 $name/$l_script
    cp -p $install_dir/wiki-config.sh $name
    docker_restart $name
    ;;
  local)
    color_msg $blue "installing $name locally on $(hostname) os $(uname)"
    sudo="sudo"
    install_locally
    ;;
  none)
    color_msg $blue "no further installation asked for"
    ;;
esac
