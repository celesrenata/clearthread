#!/bin/bash
# Build .dmg package for ClearThread on macOS

set -e

PACKAGE_NAME="ClearThread"
VERSION="${1:-0.1.0}"
OUTPUT_DIR="./dist"

echo "Building ClearThread ${VERSION} for macOS..."

# Create DMG
APP_DIR="${OUTPUT_DIR}/${PACKAGE_NAME}.app"

# Create app structure if not exists
if [ ! -d "${APP_DIR}" ]; then
    mkdir -p "${APP_DIR}/Contents/Resources"
    mkdir -p "${APP_DIR}/Contents/MacOS"
fi

# Copy binary
cp "${OUTPUT_DIR}/${PACKAGE_NAME}" "${APP_DIR}/Contents/MacOS/"

# Create Info.plist
cat > "${APP_DIR}/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>${PACKAGE_NAME}</string>
    <key>CFBundleIdentifier</key>
    <string>com.celesrenata.clearthread</string>
    <key>CFBundleVersion</key>
    <string>${VERSION}</string>
    <key>CFBundleShortVersionString</key>
    <string>${VERSION}</string>
    <key>CFBundleExecutable</key>
    <string>${PACKAGE_NAME}</string>
    <key>CFBundleIconFile</key>
    <string>app-icon.icns</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

# Create DMG
hdiutil create -volname "${PACKAGE_NAME}" -srcfolder "${APP_DIR}" \
    -fs HFS+ -format UDZO "${OUTPUT_DIR}/${PACKAGE_NAME}_${VERSION}_macOS.dmg"

echo "Built: ${OUTPUT_DIR}/${PACKAGE_NAME}_${VERSION}_macOS.dmg"
