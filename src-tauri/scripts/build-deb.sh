#!/bin/bash
# Build .deb package for ClearThread on Linux

set -e

PACKAGE_NAME="clearthread"
VERSION="${1:-0.1.0}"
ARCH="amd64"
OUTPUT_DIR="./dist"

echo "Building ClearThread ${VERSION} for Linux (${ARCH})..."

# Create package structure
PACKAGE_DIR="${OUTPUT_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}"
mkdir -p "${PACKAGE_DIR}/opt/${PACKAGE_NAME}"
mkdir -p "${PACKAGE_DIR}/usr/bin"
mkdir -p "${PACKAGE_DIR}/usr/share/applications"
mkdir -p "${PACKAGE_DIR}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${PACKAGE_DIR}/DEBIAN"

# Copy binary
cp "${OUTPUT_DIR}/${PACKAGE_NAME}" "${PACKAGE_DIR}/opt/${PACKAGE_NAME}/"
ln -sf "/opt/${PACKAGE_NAME}/${PACKAGE_NAME}" "/usr/bin/${PACKAGE_NAME}"

# Copy desktop file
cp "src-tauri/clearthread.desktop" "${PACKAGE_DIR}/usr/share/applications/"

# Copy icons
cp "src-tauri/icons/128x128.png" "${PACKAGE_DIR}/usr/share/icons/hicolor/128x128/apps/${PACKAGE_NAME}.png"

# Create control file
cat > "${PACKAGE_DIR}/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: utils
Priority: optional
Architecture: ${ARCH}
Depends: libwebkit2gtk-4.1, libayatana-appindicator3-1, libssl3, libxdo3, libgtk-3-0
Installed-Size: 100000
Maintainer: ClearThread Contributors
Description: Local-first Facebook/Messenger relationship analysis
 ClearThread helps you analyze your Facebook and Messenger data exports
 to reconstruct relationship histories and generate insights.
EOF

# Build .deb
cd "${OUTPUT_DIR}"
dpkg-deb --build --root-owner-group "${PACKAGE_NAME}_${VERSION}_${ARCH}" "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo "Built: ${OUTPUT_DIR}/${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
