#!/bin/bash
# Font Awesome installer for Docker environment
# WF 2025-05-19
BASE_DIR="/var/www/font-awesome"
CONF="font-awesome-all"
APACHE_CONF="/etc/apache2/conf-available/$CONF.conf"

# Start fresh configuration
cat << EOF > "$APACHE_CONF"
# Font Awesome configurations
# Generated: $(date)
# Version: 1.0
# Author: WF
# Description:
#    This configuration provides aliases for three Font Awesome versions
#    4.5.0, 5.15.4, 6.4.0
# with version 4.5.0 being the default "official" version.
EOF
VERSIONS=("4.5.0" "5.15.4" "6.4.0")
mkdir -p "$BASE_DIR"
cd "$BASE_DIR" || exit 1

for version in "${VERSIONS[@]}"; do
  major="${version%%.*}"

  # Map version directly to the correct directory name
  case "$major" in
    4)
      zip_url="https://download.bitplan.com/font-awesome-4.5.0.zip"
      zip_file="font-awesome-$version.zip"
      dir_name="font-awesome"
      ;;
    *)
      zip_url="https://github.com/FortAwesome/Font-Awesome/releases/download/$version/fontawesome-free-$version-desktop.zip"
      zip_file="fontawesome-$version.zip"
      dir_name="fontawesome-free-$version-desktop"
      ;;
  esac

  echo "Installing Font Awesome $version..."

  # Download and extract only if directory doesn't exist
  if [ ! -d "$dir_name" ]; then
    echo "Directory $dir_name not found, downloading and extracting..."
    curl --silent --fail -L "$zip_url" -o "$zip_file"
    unzip -q -o "$zip_file"
    rm -f "$zip_file"

    # Set ownership
    chown -R www-data:www-data "$dir_name"
  else
    echo "Directory $dir_name already exists, skipping download"
  fi

  # Create compatibility symlink if needed
  if [ ! -e "$dir_name/svg" ] && [ -d "$dir_name/svgs" ]; then
    echo "Creating compatibility symlink for $dir_name"
    ln -sf svgs/solid "$dir_name/svg"
  fi

  # Create aliases pointing to the correct directories
  echo "Alias /fontawesome$major $BASE_DIR/$dir_name" >> "$APACHE_CONF"
  echo "Alias /fa$major $BASE_DIR/$dir_name" >> "$APACHE_CONF"
  # version 4 is our "official" fontawesome
  case "$major" in
    4)
      echo "Alias /font-awesome $BASE_DIR/$dir_name" >> "$APACHE_CONF"
      ;;
  esac
done

# Add the directory access configuration
cat <<EOS >> "$APACHE_CONF"
<Directory $BASE_DIR>
  Options Indexes FollowSymLinks MultiViews
  Require all granted
</Directory>
EOS

# Enable the new configuration
a2enconf $CONF > /dev/null
apache2ctl -k graceful
echo "Font Awesome installation complete."
echo "Access via: /fontawesome4, /fontawesome5, /fontawesome6"
echo "or shorthand: /fa4, /fa5, /fa6"
