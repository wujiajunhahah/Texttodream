# DreamEcho - Transform Dreams into 3D Art

![DreamEcho Banner](static/images/dreamecho_logo.png)

**DreamEcho** is an innovative AI-driven platform dedicated to transforming people's dream creativity into exquisite 3D models. It uses advanced Large Language Models (LLM) to interpret dream meanings and AI 3D generation technology to visualize them.

🔗 **Live Demo / Project Page**: [https://wujiajunhahah.github.io/Texttodream/](https://wujiajunhahah.github.io/Texttodream/)
📦 **GitHub Repository**: [https://github.com/wujiajunhahah/Texttodream](https://github.com/wujiajunhahah/Texttodream)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green)](https://flask.palletsprojects.com/)

## ✨ Features

- **🎨 Dream to 3D**: Transform text descriptions into precise 3D models using advanced AI technology (DeepSeek & Tripo3D).
- **🧠 Deep Analysis**: Automatically analyze dream symbolism, emotions, and psychological meanings.
- **🌍 Internationalization**: Built-in support for English and Chinese (Simplified) with easy switching.
- **🌈 Immersive Experience**: Unique particle animation backgrounds and a modern, dark-themed UI.
- **📱 Responsive Design**: Perfectly optimized for various devices, from desktop to mobile.

## 🛠 Tech Stack

- **Frontend**: HTML5, CSS3 (Tailwind CSS), JavaScript (Particles.js, Three.js, Model-Viewer)
- **Backend**: Python Flask
- **Database**: SQLite (Development) / SQLAlchemy ORM
- **AI Integration**:
  - **DeepSeek API**: Used for semantic analysis of dreams, keyword extraction, and psychological interpretation.
  - **Tripo API**: Used for generating high-quality 3D models from text prompts.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- pip
- **API Keys**: You need to obtain API keys from the following services:
  - **DeepSeek**: [https://www.deepseek.com/](https://www.deepseek.com/) (For text analysis)
  - **Tripo AI**: [https://www.tripo3d.ai/](https://www.tripo3d.ai/) (For 3D model generation)

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
   Open `.env` file and fill in your API keys:
   ```ini
   # Required for Dream Analysis
   DEEPSEEK_API_KEY=your_deepseek_key_here
   
   # Required for 3D Generation
   TRIPO_API_KEY=your_tripo_key_here
   
   # Flask Security
   SECRET_KEY=generate_a_random_secure_key
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Start Creating**
   Open your browser and navigate to `http://localhost:5001`.
   - Enter your dream description.
   - Wait for the AI to analyze and generate the model (approx. 2-4 minutes).
   - View the interpretation and download your 3D model (.glb).

## 📦 Project Structure

```
Texttodream/
├── app.py              # Main Flask Application & Routes
├── config.py           # Configuration Settings
├── services.py         # AI Service Integration (DeepSeek & Tripo Logic)
├── requirements.txt    # Python Dependencies
├── static/             # Static Assets
│   ├── css/            # Stylesheets
│   ├── js/             # JavaScript files
│   ├── images/         # Images
│   └── models/         # Generated 3D Models Storage
├── templates/          # HTML Templates (Jinja2)
├── translations/       # i18n Translation Files
├── docs/               # Project Documentation & GitHub Pages
└── logs/               # Application Logs
```

## 🔑 Environment Variables

Ensure your `.env` file contains the following keys for full functionality:

| Variable | Description | Required |
|----------|-------------|----------|
| `DEEPSEEK_API_KEY` | API key for dream text analysis | **Yes** |
| `TRIPO_API_KEY` | API key for 3D model generation | **Yes** |
| `SECRET_KEY` | Flask session security key | **Yes** |
| `FLASK_APP` | Set to `app.py` | No (auto-detected) |
| `FLASK_ENV` | `development` or `production` | No |

## 📄 API Documentation

This project includes a comprehensive API documentation page accessible at `/api_docs` after starting the server. It covers endpoints for dream creation and model retrieval.

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
*Note: This project is a demonstration of AI-driven creative tools. The accuracy of dream interpretation and the quality of 3D models depend on the respective AI services.*
