# DreamEcho - Transform Dreams into 3D Art

![DreamEcho Banner](static/images/dreamecho_logo.png)

**DreamEcho** is an innovative AI-driven platform dedicated to transforming people's dream creativity into exquisite 3D models, featuring support for NFT trading.

🔗 **Live Demo / Project Page**: [https://wujiajunhahah.github.io/Texttodream/](https://wujiajunhahah.github.io/Texttodream/)
📦 **GitHub Repository**: [https://github.com/wujiajunhahah/Texttodream](https://github.com/wujiajunhahah/Texttodream)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)](https://flask.palletsprojects.com/)

## ✨ Features

- **🎨 Dream to 3D**: Transform text descriptions into precise 3D models using advanced AI technology (DeepSeek & Tripo3D).
- **💎 NFT Marketplace**: Support for minting models as NFTs and trading on multiple blockchains (Ethereum, Polygon, BSC).
- **🌍 Internationalization**: Built-in support for English and Chinese (Simplified) with easy switching.
- **🌈 Immersive Experience**: Unique particle animation backgrounds and a modern, dark-themed UI.
- **📱 Responsive Design**: Perfectly optimized for various devices, from desktop to mobile.

## 🛠 Tech Stack

- **Frontend**: HTML5, CSS3 (Tailwind CSS), JavaScript (Particles.js, Three.js)
- **Backend**: Python Flask
- **Database**: SQLite (Development) / SQLAlchemy ORM
- **AI Integration**: DeepSeek API (Analysis), Tripo API (3D Generation)
- **Blockchain**: Simulated integration for Ethereum, Polygon, BSC

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/wujiajunhahah/Texttodream.git
   cd Texttodream
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuration**
   Copy the example environment file and configure your API keys.
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your API keys:
   ```ini
   DEEPSEEK_API_KEY=your_key_here
   TRIPO_API_KEY=your_key_here
   SECRET_KEY=your_secure_secret_key
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Visit the website**
   Open your browser and navigate to `http://localhost:5001`

## 📦 Project Structure

```
Texttodream/
├── app.py              # Main Flask Application
├── config.py           # Configuration
├── services.py         # AI Service Integration (DeepSeek & Tripo)
├── requirements.txt    # Dependencies
├── static/             # Static Assets
│   ├── css/
│   ├── js/
│   ├── images/
│   └── models/         # Generated 3D Models
├── templates/          # HTML Templates (Modern & Responsive)
├── translations/       # i18n Translation Files
├── docs/               # Project Documentation & Landing Page
└── logs/               # Application Logs
```

## 🔑 Environment Variables

Ensure your `.env` file contains the following keys for full functionality:

| Variable | Description |
|----------|-------------|
| `FLASK_APP` | Set to `app.py` |
| `FLASK_ENV` | `development` or `production` |
| `SECRET_KEY` | Flask session security key |
| `DEEPSEEK_API_KEY` | API key for dream text analysis |
| `TRIPO_API_KEY` | API key for 3D model generation |

## 📄 API Documentation

This project includes a comprehensive API documentation page accessible at `/api_docs` after starting the server. It covers endpoints for user management, dream creation, and model retrieval.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Jiajun Wu**

- Website: [https://www.wujiajun.space](https://www.wujiajun.space)
- Email: epwujiajun@icloud.com
- GitHub: [@wujiajunhahah](https://github.com/wujiajunhahah)

---
*Note: This project is a demonstration of AI-driven creative tools and is open for educational and development purposes.*
