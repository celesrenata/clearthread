/**
 * SettingsPanel component for Tauri frontend.
 * Displays and allows editing of application settings.
 */

import React, { useState, useEffect } from 'react';
import { invoke } from '@tauri-apps/api/core';

export function SettingsPanel() {
  const [settings, setSettings] = useState<Settings>({
    gpu_backend: 'cpu',
    model_provider: 'ollama',
    encryption_enabled: false,
    auto_lock: false,
    auto_lock_timeout: 300,
    theme: 'light',
    language: 'en',
  });

  interface Settings {
    gpu_backend: string;
    model_provider: string;
    encryption_enabled: boolean;
    auto_lock: boolean;
    auto_lock_timeout: number;
    theme: string;
    language: string;
  }

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const loaded = await invoke<Settings>('get_settings');
      setSettings(loaded);
    } catch (error) {
      console.error('Failed to load settings:', error);
    }
  };

  const updateSetting = async <K extends keyof Settings>(key: K, value: Settings[K]) => {
    const updated = { ...settings, [key]: value };
    setSettings(updated);
    await invoke('update_settings', { settings: updated });
  };

  return (
    <div className="view-container settings-panel">
      <h2>Settings</h2>

      <div className="settings-grid">
        <div className="settings-section">
          <h3>AI Models</h3>
          <div className="setting-row">
            <label>Model Provider</label>
            <select
              value={settings.model_provider}
              onChange={(e) => updateSetting('model_provider', e.target.value)}
            >
              <option value="ollama">Ollama</option>
              <option value="llamacpp">llama.cpp</option>
              <option value="mlx">MLX</option>
            </select>
          </div>
          <div className="setting-row">
            <label>GPU Backend</label>
            <select
              value={settings.gpu_backend}
              onChange={(e) => updateSetting('gpu_backend', e.target.value)}
            >
              <option value="cpu">CPU</option>
              <option value="cuda">CUDA</option>
              <option value="rocm">ROCm</option>
              <option value="metal">Metal</option>
            </select>
          </div>
        </div>

        <div className="settings-section">
          <h3>Security</h3>
          <div className="setting-row">
            <label>Encryption</label>
            <input
              type="checkbox"
              checked={settings.encryption_enabled}
              onChange={(e) => updateSetting('encryption_enabled', e.target.checked)}
            />
          </div>
          <div className="setting-row">
            <label>Auto-lock</label>
            <input
              type="checkbox"
              checked={settings.auto_lock}
              onChange={(e) => updateSetting('auto_lock', e.target.checked)}
            />
          </div>
          <div className="setting-row">
            <label>Auto-lock Timeout (seconds)</label>
            <input
              type="number"
              value={settings.auto_lock_timeout}
              onChange={(e) => updateSetting('auto_lock_timeout', Number(e.target.value))}
            />
          </div>
        </div>

        <div className="settings-section">
          <h3>Appearance</h3>
          <div className="setting-row">
            <label>Theme</label>
            <select
              value={settings.theme}
              onChange={(e) => updateSetting('theme', e.target.value)}
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </div>
          <div className="setting-row">
            <label>Language</label>
            <select
              value={settings.language}
              onChange={(e) => updateSetting('language', e.target.value)}
            >
              <option value="en">English</option>
              <option value="es">Spanish</option>
              <option value="fr">French</option>
            </select>
          </div>
        </div>
      </div>
    </div>
  );
}
