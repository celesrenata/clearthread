#!/bin/bash
# Build .msi package for ClearThread on Windows

set -e

PACKAGE_NAME="ClearThread"
VERSION="${1:-0.1.0}"
OUTPUT_DIR="./dist"

echo "Building ClearThread ${VERSION} for Windows..."

# Create output directory
mkdir -p "${OUTPUT_DIR}"

# Use WiX Toolset to build MSI
# First, create WiX project file
cat > "${OUTPUT_DIR}/ClearThread.wixproj" << EOF
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net8.0</TargetFramework>
    <WixTargetsPath Condition="\$(WixTargetsPath == '')">\$(MSBuildThisFileDirectory)..\..\..\..\lib\managed\Microsoft.Windows.Wix.Targets\Wix.targets</WixTargetsPath>
  </PropertyGroup>
  <ItemGroup>
    <WixInclude Files="ClearThread.wxs" />
  </ItemGroup>
</Project>
EOF

# Create WiX source file
cat > "${OUTPUT_DIR}/ClearThread.wxs" << EOF
<?xml version="1.0" encoding="utf-8"?>
<Wix xmlns="http://wixtoolset.org/schemas/v4/wxs">
  <Product Name="ClearThread"
           Version="${VERSION}"
           Manufacturer="ClearThread Contributors"
           Language="1033"
           Codepage="1252"
           Id="*">
    <Package Description="ClearThread - Local-first Facebook/Messenger relationship analysis"
             InstallerVersion="500"
             Compressed="yes"
             InstallScope="perMachine" />
    
    <MajorUpgrade AllowDowngrades="yes" />
    
    <MediaTemplate EmbedCab="yes" />
    
    <Directory Id="TARGETDIR" Name="SourceDir">
      <Directory Id="ProgramFiles64Folder">
        <Directory Id="INSTALLFOLDER" Name="ClearThread">
          <Component Id="ApplicationComponent" Guid="*">
            <File Id="clearthread.exe" Source="${PACKAGE_NAME}.exe" KeyPath="yes" />
            <RegistryValue Root="HKCR" Key="Software\ClearThread" Name="Path" Value="[INSTALLFOLDER]" Type="string" />
          </Component>
        </Directory>
      </Directory>
      <Directory Id="ProgramMenuFolder">
        <Directory Id="ApplicationProgramsFolder" Name="ClearThread" />
      </Directory>
    </Directory>
    
    <Feature Id="ProductFeature">
      <ComponentRef Id="ApplicationComponent" />
    </Feature>
    
    <Property Id="ARPPRODUCTICON" Value="clearthread.exe" />
  </Product>
</Wix>
EOF

echo "Built: ${OUTPUT_DIR}/ClearThread.wxs"
echo "Run 'wix build -p ClearThread.wxs' to create the MSI"
