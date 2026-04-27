# 🎮 Manjaro Gaming Control

**Manjaro Gaming Control** is an exclusive, all-in-one optimization and hardware control utility designed specifically for Manjaro Linux gamers. It provides a clean GUI to manage your system's performance, clean junk, and monitor hardware without touching the terminal.

## ✨ Features

* **🚀 Game Optimization:** 
  * Toggle CPU Performance Mode (MAX FPS).
  * Enable low-latency network tweaks for competitive games.
  * Easy integration with Feral GameMode and MangoHud.
  * Boost Discord CPU priority to prevent voice lag.
* **🧹 Smart System Cleaner:** 
  * Safely clear package cache (Pamac), system error logs, and drop RAM/Swap caches.
  * Find and delete orphan Steam prefixes (compatdata) from uninstalled games.
* **🌡️ Overheat Protection:** 
  * Live temperature graphing for CPU and GPU.
  * Custom sound alarms when hardware reaches critical temperatures.
* **🔧 Hardware & Drivers:** 
  * Instantly check current and available Nvidia driver versions.
  * Safely rollback Nvidia drivers from your local cache.

## 📦 Installation

### Arch User Repository (AUR)
You can easily install the app using your favorite AUR helper:
yay -S manjaro-gaming-control-bin


Or using Pamac:
pamac build manjaro-gaming-control-bin

### Manual Binary Download
1. Go to the [Releases](../../releases) tab.
2. Download the latest `ManjaroGamingControl` binary.
3. Make it executable and run:
\`\`\`bash
chmod +x ManjaroGamingControl
./ManjaroGamingControl
\`\`\`

## 🛠 Dependencies
To get the most out of this application, ensure you have the following installed:
* `polkit` (for applying performance tweaks safely)
* `gamemode` (for Feral GameMode integration)
* `mangohud` (for OSD features)
* `nvidia-utils` (for GPU detection and rollback features)

## 🤝 Support
If you like this project and it helped you get more FPS or save your PC from overheating, consider supporting the development!
* [Buy Me a Coffee](https://buymeacoffee.com/serhiidev)

---
*Created by Serhii K. | 100% Free and Open-Source*
